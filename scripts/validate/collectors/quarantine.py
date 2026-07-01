"""Collect external-skill quarantine policy violations."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def _quarantine_register_path(repo_root: Path) -> Path:
    return repo_root / "planning/manifests/security-quarantine-register.json"


def _load_quarantine_register(repo_root: Path) -> tuple[Path, dict | None, list[dict[str, str]]]:
    path = _quarantine_register_path(repo_root)
    if not path.is_file():
        return path, None, []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - exercised through integration tests
        return path, None, [{"source": str(path), "message": f"Invalid quarantine register JSON: {exc}"}]
    if not isinstance(payload, dict):
        return path, None, [{"source": str(path), "message": "Invalid quarantine register JSON: expected object"}]
    return path, payload, []


def _quarantined_repo_slugs(payload: dict) -> set[str]:
    slugs: set[str] = set()
    for record in payload.get("external_repo_records", []):
        if not isinstance(record, dict):
            continue
        if record.get("default_action") != "quarantine":
            continue
        repo = str(record.get("repo") or "").strip()
        if repo:
            slugs.add(repo)
    return {s.lower() for s in slugs}


def _register_policy_errors(path: Path, payload: dict) -> list[dict[str, str]]:
    triggers = {str(t).strip() for t in payload.get("quarantine_triggers", []) if str(t).strip()}
    errors: list[dict[str, str]] = []
    for record in payload.get("external_repo_records", []):
        if not isinstance(record, dict):
            continue
        trigger = str(record.get("trigger") or "").strip()
        record_id = str(record.get("id") or record.get("repo") or "?")
        if not trigger:
            errors.append({
                "source": str(path),
                "message": f"Quarantine record {record_id} is missing a trigger",
            })
        elif trigger not in triggers:
            errors.append({
                "source": str(path),
                "message": f"Quarantine record {record_id} uses undeclared trigger '{trigger}'",
            })
    return errors


def _slug_hits_value(slug: str, val: str) -> bool:
    return bool(slug and slug in val.lower())


def _scan_text_for_slugs(
    text: str,
    slugs: list[str],
    *,
    source: str,
    label: str,
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    lowered = text.lower()
    for slug in slugs:
        if _slug_hits_value(slug, lowered):
            errors.append({
                "source": source,
                "message": (
                    f"Hard-quarantined source '{slug}' must not appear in {label}"
                ),
            })
    return errors


def _scan_authoring_for_slugs(repo_root: Path, slugs: list[str]) -> list[dict[str, str]]:
    authoring_dir = repo_root / "docs" / "src" / "authoring" / "skills"
    if not authoring_dir.is_dir():
        return []

    from wagents.parsing import parse_frontmatter

    errors: list[dict[str, str]] = []
    for path in sorted(authoring_dir.glob("*.mdx")):
        try:
            frontmatter, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        fields = (
            str(frontmatter.get("source") or ""),
            str(frontmatter.get("install_source") or ""),
            str(frontmatter.get("install_command") or ""),
            str(frontmatter.get("source_url") or ""),
            body,
        )
        combined = " ".join(fields)
        errors.extend(
            _scan_text_for_slugs(
                combined,
                slugs,
                source=str(path),
                label=f"authoring entry {frontmatter.get('name') or path.stem}",
            )
        )
    return errors


def collect_quarantine_errors(repo_root: Path) -> list[dict[str, str]]:
    """Fail when curated external skill sources reference hard-quarantined repos."""
    register_path, payload, errors = _load_quarantine_register(repo_root)
    if payload is None:
        return errors

    errors.extend(_register_policy_errors(register_path, payload))
    slugs = sorted(_quarantined_repo_slugs(payload))
    if not slugs:
        return errors

    cat_index = repo_root / "docs" / "public" / "generated-registries" / "skills-catalog-index.json"
    if cat_index.is_file():
        try:
            data = json.loads(cat_index.read_text(encoding="utf-8"))
            for key in ("externalSkillIndex", "allSkillIndex", "customSkillIndex"):
                rows = data.get(key) or []
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    for fld in ("install_source", "source", "name", "installSource", "sourceRoot", "source_url"):
                        val = str(row.get(fld) or "").lower()
                        for slug in slugs:
                            if _slug_hits_value(slug, val):
                                name = row.get("name") or row.get("id") or "?"
                                errors.append({
                                    "source": str(cat_index),
                                    "message": (
                                        f"Hard-quarantined source '{slug}' must not appear in catalog index entry "
                                        f"{name} (field {fld})"
                                    ),
                                })
        except Exception as exc:
            errors.append({
                "source": str(cat_index),
                "message": f"Invalid catalog index JSON during quarantine scan: {exc}",
            })

    errors.extend(_scan_authoring_for_slugs(repo_root, slugs))

    # dedupe identical messages
    seen_msgs: set[str] = set()
    deduped: list[dict[str, str]] = []
    for e in errors:
        msg = e["message"]
        if msg not in seen_msgs:
            seen_msgs.add(msg)
            deduped.append(e)
    return deduped
