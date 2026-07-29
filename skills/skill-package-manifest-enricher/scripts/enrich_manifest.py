#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6,<7"]
# ///
"""Enrich a portable skill manifest from explicit, content-bound metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, cast

import yaml

CATALOG_RELATIVE_PATH = Path("docs/public/generated-registries/skills-catalog-index.json")
TARGET_KEYS = ("targetAgents", "target_agents", "target_harnesses", "harness_targets")
SYNC_ACTIVE_BUCKETS = ("missing", "already_present", "pin_blocked", "unresolved")


class EnrichmentError(ValueError):
    """Raised when enrichment input is malformed or ambiguous."""


@dataclass(frozen=True)
class TargetResolution:
    """Resolved harness targets and the portable evidence binding."""

    targets: tuple[str, ...]
    status: str
    source: str
    source_sha256: str


def _load_eval_count(skill_dir: Path) -> int:
    evals_file = skill_dir / "evals" / "evals.json"
    if not evals_file.is_file():
        return 0
    try:
        data = json.loads(evals_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    evals = data.get("evals") if isinstance(data, dict) else None
    return len(evals) if isinstance(evals, list) else 0


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse a `SKILL.md` frontmatter mapping with PyYAML safe semantics."""
    lines = text.splitlines()
    if not lines or lines[0].rstrip() != "---" or lines[0].startswith((" ", "\t")):
        raise EnrichmentError("SKILL.md is missing opening YAML frontmatter delimiter")
    try:
        closing_index = next(
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.rstrip() == "---" and not line.startswith((" ", "\t"))
        )
    except StopIteration as exc:
        raise EnrichmentError("SKILL.md is missing closing YAML frontmatter delimiter") from exc

    source = "\n".join(lines[1:closing_index])
    try:
        loaded = yaml.safe_load(source)
    except yaml.YAMLError as exc:
        raise EnrichmentError(f"invalid SKILL.md YAML frontmatter: {exc}") from exc
    if not isinstance(loaded, dict):
        raise EnrichmentError("SKILL.md YAML frontmatter must be a mapping")
    return loaded


def _required_string(frontmatter: dict[str, Any], key: str, *, fallback: str = "") -> str:
    value = frontmatter.get(key, fallback)
    if not isinstance(value, str) or not value.strip():
        raise EnrichmentError(f"SKILL.md frontmatter field {key!r} must be a non-empty string")
    return value


def _optional_string(frontmatter: dict[str, Any], key: str) -> str:
    value = frontmatter.get(key, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise EnrichmentError(f"SKILL.md frontmatter field {key!r} must be a string")
    return value


def _read_json_object(path: Path, *, kind: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise EnrichmentError(f"cannot read {kind} metadata: {path.name}: {exc}") from exc
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EnrichmentError(f"invalid {kind} metadata JSON: {path.name}: {exc}") from exc
    if not isinstance(payload, dict):
        raise EnrichmentError(f"{kind} metadata must contain a top-level JSON object")
    return payload, raw


def _normalize_targets(value: object, *, source: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise EnrichmentError(f"{source} target set must be a JSON array")
    targets: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise EnrichmentError(f"{source} target entries must be non-empty strings")
        normalized = item.strip()
        if normalized not in seen:
            targets.append(normalized)
            seen.add(normalized)
    return tuple(targets)


def _rows_from_container(container: object) -> list[dict[str, Any]]:
    if isinstance(container, list):
        return [cast("dict[str, Any]", item) for item in container if isinstance(item, dict)]
    if isinstance(container, dict):
        rows: list[dict[str, Any]] = []
        for name, value in container.items():
            if isinstance(value, dict):
                row = dict(value)
                row.setdefault("name", name)
                rows.append(row)
        return rows
    return []


def _targets_from_named_rows(payload: dict[str, Any], skill_name: str, *, keys: tuple[str, ...]) -> tuple[str, ...] | None:
    matches: list[tuple[str, ...]] = []
    for key in keys:
        for row in _rows_from_container(payload.get(key)):
            if row.get("name") != skill_name:
                continue
            target_key = next((candidate for candidate in TARGET_KEYS if candidate in row), None)
            if target_key is None:
                continue
            matches.append(_normalize_targets(row[target_key], source=f"{key}.{skill_name}.{target_key}"))

    if not matches:
        return None
    first = matches[0]
    if any(match != first for match in matches[1:]):
        raise EnrichmentError(f"metadata contains conflicting target sets for skill {skill_name!r}")
    return first


def _sync_item_name(item: object) -> str:
    if isinstance(item, dict):
        value = item.get("name")
        return value.strip() if isinstance(value, str) else ""
    if isinstance(item, str):
        return item.partition(" [")[0].strip()
    return ""


def _targets_from_sync_report(payload: dict[str, Any], skill_name: str) -> tuple[str, ...] | None:
    agents = payload.get("agents")
    if not isinstance(agents, list):
        return None
    targets: list[str] = []
    found = False
    for report in agents:
        if not isinstance(report, dict):
            continue
        agent = report.get("agent")
        if not isinstance(agent, str) or not agent.strip():
            continue
        for bucket in SYNC_ACTIVE_BUCKETS:
            rows = report.get(bucket)
            if not isinstance(rows, list):
                continue
            if any(_sync_item_name(item) == skill_name for item in rows):
                found = True
                targets.append(agent.strip())
                break
    return _normalize_targets(targets, source=f"sync report for {skill_name}") if found else None


def _catalog_targets(payload: dict[str, Any], skill_name: str) -> tuple[str, ...] | None:
    return _targets_from_named_rows(
        payload,
        skill_name,
        keys=("customSkillIndex", "externalSkillIndex", "allSkillIndex", "skills"),
    )


def _sync_targets(payload: dict[str, Any], skill_name: str) -> tuple[str, ...] | None:
    row_targets = _targets_from_named_rows(payload, skill_name, keys=("skills", "desired", "rows"))
    return row_targets if row_targets is not None else _targets_from_sync_report(payload, skill_name)


def _portable_source_label(label: str | None, path: Path, *, kind: str, default: str | None = None) -> str:
    candidate = label or default or f"{kind}/{path.name}"
    posix = PurePosixPath(candidate)
    windows = PureWindowsPath(candidate)
    if (
        not candidate
        or posix.is_absolute()
        or windows.is_absolute()
        or bool(windows.drive)
        or candidate.startswith("~")
        or "://" in candidate
        or ".." in posix.parts
    ):
        raise EnrichmentError(f"{kind} source label must be a portable relative path")
    return posix.as_posix()


def _default_catalog(skill_dir: Path) -> tuple[Path, str] | None:
    """Use the repo catalog only when `skill_dir` is visibly under that repo's skills root."""
    if skill_dir.parent.name != "skills":
        return None
    repo_root = skill_dir.parent.parent
    catalog = repo_root / CATALOG_RELATIVE_PATH
    if catalog.is_file():
        return catalog, CATALOG_RELATIVE_PATH.as_posix()
    return None


def _resolution_from_source(
    path: Path,
    *,
    label: str | None,
    default_label: str | None,
    kind: str,
    skill_name: str,
) -> TargetResolution | None:
    payload, raw = _read_json_object(path, kind=kind)
    targets = _catalog_targets(payload, skill_name) if kind == "catalog" else _sync_targets(payload, skill_name)
    if targets is None:
        return None
    return TargetResolution(
        targets=targets,
        status=kind,
        source=_portable_source_label(label, path, kind=kind, default=default_label),
        source_sha256=hashlib.sha256(raw).hexdigest(),
    )


def _resolve_targets(
    skill_dir: Path,
    skill_name: str,
    *,
    catalog_metadata: Path | None,
    sync_metadata: Path | None,
    catalog_source_label: str | None,
    sync_source_label: str | None,
) -> TargetResolution:
    catalog_path = catalog_metadata
    catalog_default_label: str | None = None
    if catalog_path is None and sync_metadata is None:
        default_catalog = _default_catalog(skill_dir)
        if default_catalog is not None:
            catalog_path, catalog_default_label = default_catalog

    if catalog_path is not None:
        catalog_resolution = _resolution_from_source(
            catalog_path,
            label=catalog_source_label,
            default_label=catalog_default_label,
            kind="catalog",
            skill_name=skill_name,
        )
        if catalog_resolution is not None:
            return catalog_resolution

    if sync_metadata is not None:
        sync_resolution = _resolution_from_source(
            sync_metadata,
            label=sync_source_label,
            default_label=None,
            kind="sync",
            skill_name=skill_name,
        )
        if sync_resolution is not None:
            return sync_resolution

    return TargetResolution(targets=(), status="unavailable", source="unavailable", source_sha256="")


def _load_upstream_manifest(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    payload, _ = _read_json_object(path, kind="upstream manifest")
    return payload


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary_path.replace(path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def enrich_manifest(
    skill_dir: Path,
    *,
    apply: bool,
    catalog_metadata: Path | None = None,
    sync_metadata: Path | None = None,
    catalog_source_label: str | None = None,
    sync_source_label: str | None = None,
    upstream_manifest: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, object]:
    """Build an additive manifest and write it only when `apply` is true."""
    skill_dir = skill_dir.resolve()
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise EnrichmentError(f"missing SKILL.md under {skill_dir}")

    frontmatter = _parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    skill_name = _required_string(frontmatter, "name", fallback=skill_dir.name)
    description = _required_string(frontmatter, "description")
    compatibility = _optional_string(frontmatter, "compatibility")
    resolution = _resolve_targets(
        skill_dir,
        skill_name,
        catalog_metadata=catalog_metadata,
        sync_metadata=sync_metadata,
        catalog_source_label=catalog_source_label,
        sync_source_label=sync_source_label,
    )

    out = (output_path or skill_dir / "manifest.enriched.json").resolve()
    base_path = upstream_manifest.resolve() if upstream_manifest is not None else (out if out.is_file() else None)
    manifest = _load_upstream_manifest(base_path)
    manifest.update(
        {
            "name": skill_name,
            "description": description,
            "compatibility_notes": compatibility,
            "eval_case_count": _load_eval_count(skill_dir),
            "harness_targets": list(resolution.targets),
            "harness_targets_status": resolution.status,
            "harness_targets_source": resolution.source,
            "harness_targets_source_sha256": resolution.source_sha256,
        }
    )
    if apply:
        manifest["packaged_at"] = datetime.now(UTC).isoformat()
        _write_json_atomic(out, manifest)
    return {"ok": True, "path": str(out), "manifest": manifest, "applied": apply}


def _repo_named_skill(name: str) -> Path:
    if not name or name in {".", ".."} or Path(name).name != name or "\\" in name:
        raise EnrichmentError(f"invalid repo skill name {name!r}; pass --skill-dir explicitly")
    source_skill = Path(__file__).resolve().parent.parent
    if source_skill.parent.name == "skills":
        candidate = source_skill.parent / name
        if candidate.is_dir():
            return candidate
    raise EnrichmentError(f"cannot resolve skill {name!r}; pass --skill-dir explicitly")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Enrich a portable skill package manifest")
    parser.add_argument("name", nargs="?", help="Repo skill name; use --skill-dir outside the source repository")
    parser.add_argument("--skill-dir", type=Path, help="Explicit portable skill directory")
    parser.add_argument("--manifest", type=Path, help="Existing upstream manifest JSON to preserve")
    parser.add_argument("--output", type=Path, help="Output sidecar path (default: <skill-dir>/manifest.enriched.json)")
    parser.add_argument("--catalog-metadata", type=Path, help="Portable catalog index JSON (preferred)")
    parser.add_argument("--sync-metadata", type=Path, help="Portable skill sync JSON (fallback)")
    parser.add_argument("--catalog-source-label", help="Portable relative label recorded for catalog metadata")
    parser.add_argument("--sync-source-label", help="Portable relative label recorded for sync metadata")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Write the enriched sidecar")
    mode.add_argument("--dry-run", action="store_true", help="Preview only (the default)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if bool(args.name) == bool(args.skill_dir):
        parser.error("provide exactly one of NAME or --skill-dir")

    try:
        skill_dir = args.skill_dir if args.skill_dir is not None else _repo_named_skill(args.name)
        payload = enrich_manifest(
            skill_dir,
            apply=args.apply,
            catalog_metadata=args.catalog_metadata,
            sync_metadata=args.sync_metadata,
            catalog_source_label=args.catalog_source_label,
            sync_source_label=args.sync_source_label,
            upstream_manifest=args.manifest,
            output_path=args.output,
        )
    except (EnrichmentError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
