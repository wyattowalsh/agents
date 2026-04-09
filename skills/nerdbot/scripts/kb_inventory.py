#!/usr/bin/env python3
"""Inspect a knowledge-base or repository root for nerdbot-style KB signals.

The script is read-only. It inventories default KB layers, classifies content
where possible, highlights risky paths, finds likely indexes/logs, and suggests
safe next actions.

Usage examples:
    python kb_inventory.py --root .
    python kb_inventory.py --root ./client-repo
    uv run python skills/nerdbot/scripts/kb_inventory.py --root .
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

DEFAULT_LAYER_PATHS: dict[str, str] = {
    "raw": "raw",
    "wiki": "wiki",
    "schema": "schema",
    "config": "config",
    "indexes": "indexes",
    "activity": "activity",
}

DEFAULT_LAYER_CHILDREN: dict[str, tuple[str, ...]] = {
    "raw": ("sources", "captures", "extracts"),
    "wiki": ("topics",),
    "schema": (),
    "config": (),
    "indexes": (),
    "activity": (),
}

DEFAULT_DIRECTORIES: tuple[str, ...] = (
    "raw",
    "raw/sources",
    "raw/captures",
    "raw/extracts",
    "wiki",
    "wiki/topics",
    "schema",
    "config",
    "indexes",
    "activity",
)

STARTER_FILES: dict[str, str] = {
    "wiki_index": "wiki/index.md",
    "coverage_index": "indexes/coverage.md",
    "source_map": "indexes/source-map.md",
    "activity_log": "activity/log.md",
}

LAYER_ALIAS_HINTS: dict[str, tuple[str, ...]] = {
    "raw": ("sources", "source", "evidence", "captures", "extracts", "materials"),
    "wiki": ("docs", "notes", "knowledge", "kb", "reference", "topics"),
    "schema": ("schemas", "contracts"),
    "config": ("configs", "settings"),
    "indexes": ("index", "maps", "catalog", "inventories"),
    "activity": ("logs", "journal", "history", "changelog"),
}

MARKDOWN_SUFFIXES = {".md", ".mdx"}
TEXT_SUFFIXES = MARKDOWN_SUFFIXES | {
    ".txt",
    ".rst",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".csv",
    ".tsv",
    ".log",
}
SKIP_WALK_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "site",
    "public",
    "out",
    "coverage",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}
DERIVED_DIR_MARKERS = {"dist", "build", "site", "public", "out", "export", "generated", "derived"}
RISK_REASON_BY_MARKER: dict[str, str] = {
    "archive": "archived material can be confused with canonical material",
    "archives": "archived material can be confused with canonical material",
    "backup": "backup content can drift from the active KB",
    "backups": "backup content can drift from the active KB",
    "old": "legacy content may be stale or superseded",
    "tmp": "temporary content is easy to lose or misclassify",
    "temp": "temporary content is easy to lose or misclassify",
    "draft": "draft content may not be traceable or review-ready",
    "scratch": "scratch content may not be canonical or traceable",
}
INDEX_ROLE_HINTS: dict[str, tuple[str, ...]] = {
    "wiki_index": ("wiki/index", "/index.md", "readme"),
    "coverage_index": ("coverage",),
    "source_map": ("source-map", "sourcemap", "source_map", "manifest"),
    "activity_log": ("activity/log", "log", "journal", "changelog", "history"),
    "inventory": ("inventory", "audit"),
}
PROVENANCE_TERMS = (
    "provenance",
    "sources",
    "source:",
    "canonical material",
    "derived from",
    "evidence",
    "source notes",
    "references",
)
HEADING_PATTERN = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*$", re.MULTILINE)
LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def warn(message: str) -> None:
    """Emit a human-readable warning to stderr."""
    print(f"warning: {message}", file=sys.stderr)


def normalize_requested_root(root_arg: str) -> Path:
    """Resolve a root path while rejecting symlinked roots or ancestors.

    Examples:
        >>> normalize_requested_root('.')  # doctest: +ELLIPSIS
        PosixPath('...')
    """
    supplied = Path(root_arg).expanduser()
    candidate = supplied if supplied.is_absolute() else Path.cwd() / supplied
    for ancestor in (candidate, *candidate.parents):
        if ancestor.exists() and ancestor.is_symlink():
            raise RuntimeError(f"Refusing to use symlinked root path: {ancestor}")
    return candidate.resolve()


def resolve_existing_root(root_arg: str) -> Path:
    """Resolve and validate an existing root directory.

    Examples:
        >>> resolve_existing_root(".")  # doctest: +ELLIPSIS
        PosixPath('...')
    """
    root = normalize_requested_root(root_arg)
    if not root.exists():
        raise FileNotFoundError(f"Root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Root is not a directory: {root}")
    return root


def relative_posix(root: Path, path: Path) -> str:
    """Return a stable POSIX-style path relative to the root.

    Examples:
        >>> root = Path("/repo")
        >>> relative_posix(root, Path("/repo/wiki/index.md"))
        'wiki/index.md'
    """
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def normalize_title(value: str) -> str:
    """Normalize a title or filename stem for duplicate detection.

    Examples:
        >>> normalize_title("Agentic Knowledge Bases")
        'agentic-knowledge-bases'
    """
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return slug.strip("-") or "untitled"


def normalize_anchor(value: str) -> str:
    """Normalize a heading into a GitHub-style markdown anchor.

    Examples:
        >>> normalize_anchor("Source Map")
        'source-map'
    """
    anchor = value.strip().lower()
    anchor = re.sub(r"[^a-z0-9\s-]", "", anchor)
    anchor = re.sub(r"\s+", "-", anchor)
    return re.sub(r"-+", "-", anchor).strip("-")


def should_prune_directory(name: str) -> bool:
    """Return True when a directory should not be traversed recursively."""
    lowered = name.lower()
    return lowered in SKIP_WALK_DIRS or (name.startswith(".") and lowered not in {".obsidian"})


def iter_repo_entries(root: Path) -> Iterator[tuple[Path, bool]]:
    """Yield repository entries with a flag indicating whether each entry is a directory.

    Examples:
        >>> any(is_dir for _, is_dir in iter_repo_entries(Path('.').resolve()))  # doctest: +SKIP
        True
    """
    for current_root, dirnames, filenames in os.walk(root):
        current = Path(current_root)
        for directory_name in list(dirnames):
            child = current / directory_name
            yield child, True
            if should_prune_directory(directory_name):
                dirnames.remove(directory_name)
        for filename in filenames:
            yield current / filename, False


def iter_repo_files(root: Path) -> Iterator[Path]:
    """Yield repository files while pruning bulky or hidden directories."""
    for path, is_dir in iter_repo_entries(root):
        if not is_dir and not path.is_symlink():
            yield path


def read_text_file(path: Path, *, max_bytes: int = 262_144) -> str | None:
    """Read a text file safely, returning None for likely-binary files.

    Examples:
        >>> read_text_file(Path(__file__), max_bytes=32) is not None
        True
    """
    suffix = path.suffix.lower()
    if suffix and suffix not in TEXT_SUFFIXES:
        return None
    try:
        with path.open("rb") as handle:
            data = handle.read(max_bytes + 1)
    except OSError as exc:
        warn(f"Could not read {path}: {exc}")
        return None
    if len(data) > max_bytes:
        warn(f"Truncated read of {path} after {max_bytes} bytes")
        data = data[:max_bytes]
    if b"\x00" in data:
        return None
    return data.decode("utf-8", errors="ignore")


def extract_headings(text: str) -> list[str]:
    """Extract markdown headings from a document.

    Examples:
        >>> extract_headings("# Title\n\n## Sources")
        ['Title', 'Sources']
    """
    headings: list[str] = []
    for match in HEADING_PATTERN.finditer(text):
        heading = match.group(1).strip().rstrip("#").strip()
        if heading:
            headings.append(heading)
    return headings


def extract_markdown_links(text: str) -> list[str]:
    """Extract inline markdown link targets.

    Examples:
        >>> extract_markdown_links("See [map](indexes/source-map.md).")
        ['indexes/source-map.md']
    """
    return [target.strip() for target in LINK_PATTERN.findall(text)]


def has_provenance_markers(text: str, links: list[str] | None = None) -> bool:
    """Detect whether a document exposes provenance or source markers.

    Examples:
        >>> has_provenance_markers("## Sources\n- [raw](../raw/sources/a.txt)")
        True
    """
    lowered = text.lower()
    if any(term in lowered for term in PROVENANCE_TERMS):
        return True
    for link in links or []:
        cleaned = link.lower().lstrip("./")
        if cleaned.startswith("raw/") or "/raw/" in cleaned or cleaned.startswith("../raw/"):
            return True
    return False


def emit_error_payload(script: str, root_arg: str) -> str:
    """Build a generic stdout-safe error payload.

    Examples:
        >>> emit_error_payload('kb_inventory', '.')
        '{"error": "kb_inventory failed", "root": ".", "details": "see stderr"}'
    """
    return json.dumps(
        {
            "error": f"{script} failed",
            "root": root_arg,
            "details": "see stderr",
        },
        ensure_ascii=False,
    )


def is_index_like_path(path: Path) -> bool:
    """Return True when a path looks like an index, map, or log page.

    Examples:
        >>> is_index_like_path(Path("wiki/index.md"))
        True
    """
    name = path.stem.lower()
    parts = [part.lower() for part in path.parts]
    if parts and parts[0] in {"indexes", "activity"}:
        return True
    return any(
        token in name
        for token in (
            "index",
            "coverage",
            "source-map",
            "sourcemap",
            "log",
            "journal",
            "manifest",
            "inventory",
            "audit",
        )
    )


def classify_content(root: Path, path: Path, text: str | None) -> tuple[str, list[str]]:
    """Classify a file and capture evidence used for the classification.

    Examples:
        >>> classify_content(Path('/repo'), Path('/repo/wiki/index.md'), '# KB')
        ('wiki_index', ['path:wiki'])
    """
    rel_path = relative_posix(root, path)
    parts = path.relative_to(root).parts
    lowered_parts = [part.lower() for part in parts]
    evidence: list[str] = []
    top = lowered_parts[0] if lowered_parts else ""
    if top == "raw":
        evidence.append("path:raw")
        if len(lowered_parts) > 1 and lowered_parts[1] == "extracts":
            return "raw_extract", evidence
        return "raw_source", evidence
    if top == "wiki":
        evidence.append("path:wiki")
        if path.name.lower() == "index.md" or is_index_like_path(Path(*lowered_parts)):
            return "wiki_index", evidence
        return "wiki_page", evidence
    if top == "indexes":
        evidence.append("path:indexes")
        return "kb_index", evidence
    if top == "activity":
        evidence.append("path:activity")
        kind = "activity_log" if "log" in path.stem.lower() or "journal" in path.stem.lower() else "activity_note"
        return kind, evidence
    if top == "schema":
        evidence.append("path:schema")
        return "schema_contract", evidence
    if top == "config":
        evidence.append("path:config")
        return "config_file", evidence
    if any(part in DERIVED_DIR_MARKERS for part in lowered_parts):
        evidence.append("path:derived")
        return "derived_output", evidence
    if path.suffix.lower() in MARKDOWN_SUFFIXES:
        if text and has_provenance_markers(text, extract_markdown_links(text)):
            evidence.append("content:provenance")
        kind = "unlayered_index" if is_index_like_path(Path(*lowered_parts)) else "unlayered_markdown"
        return kind, evidence
    if path.suffix.lower() in {".json", ".yaml", ".yml", ".toml", ".ini"}:
        evidence.append("content:structured-config")
        return "repo_config", evidence
    if rel_path.lower().endswith(".log"):
        evidence.append("content:log")
        return "log_file", evidence
    return "unknown", evidence


def infer_index_role(root: Path, path: Path, text: str | None) -> str | None:
    """Guess whether a file behaves like a KB index or log.

    Examples:
        >>> infer_index_role(Path('/repo'), Path('/repo/indexes/coverage.md'), '# Coverage')
        'coverage_index'
    """
    rel_path = relative_posix(root, path).lower()
    name = path.name.lower()
    if rel_path == STARTER_FILES["wiki_index"]:
        return "wiki_index"
    if any(hint in rel_path for hint in INDEX_ROLE_HINTS["coverage_index"]):
        return "coverage_index"
    if any(hint in rel_path for hint in INDEX_ROLE_HINTS["source_map"]):
        return "source_map"
    if any(hint in rel_path for hint in INDEX_ROLE_HINTS["activity_log"]):
        return "activity_log"
    if any(hint in rel_path for hint in INDEX_ROLE_HINTS["inventory"]):
        return "inventory"
    if rel_path.startswith("indexes/"):
        return "kb_index"
    if name == "readme.md" and rel_path.startswith("wiki/"):
        return "wiki_index"
    return None


def assess_risk(root: Path, path: Path, classification: str) -> dict[str, Any] | None:
    """Return a structured risk record when a path deserves extra review."""
    parts = [part.lower() for part in path.relative_to(root).parts]
    reasons: list[str] = []
    severity = "warning"
    if path.is_symlink():
        reasons.append("symlinked content can break repo-local provenance or portability")
    if classification == "unlayered_markdown":
        reasons.append("markdown exists outside the default KB layers")
    if classification == "derived_output":
        reasons.append("derived output can be mistaken for canonical material")
    if any(part.startswith(".") and part != ".git" for part in parts):
        reasons.append("hidden metadata or editor state may be easy to miss during review")
    for part in parts:
        if part in RISK_REASON_BY_MARKER:
            reasons.append(RISK_REASON_BY_MARKER[part])
    if path.is_file():
        suffix = path.suffix.lower()
        if suffix in {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".zip", ".sqlite"}:
            reasons.append("binary or packaged content often needs a raw summary stub or normalized extract")
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        if size > 5_000_000:
            reasons.append("large files can slow audits and provenance review")
    if not reasons:
        return None
    return {
        "path": relative_posix(root, path),
        "severity": severity,
        "reasons": sorted(set(reasons)),
    }


def detect_layers(root: Path) -> dict[str, dict[str, Any]]:
    """Detect default KB layers and likely aliases at the root level."""
    top_level_dirs = {
        entry.name.lower(): entry for entry in root.iterdir() if entry.is_dir() and not entry.is_symlink()
    }
    layers: dict[str, dict[str, Any]] = {}
    for layer, rel_path in DEFAULT_LAYER_PATHS.items():
        layer_path = root / rel_path
        symlinked = layer_path.is_symlink()
        present = layer_path.is_dir() and not symlinked
        aliases = [
            relative_posix(root, top_level_dirs[name])
            for name in LAYER_ALIAS_HINTS.get(layer, ())
            if name in top_level_dirs and top_level_dirs[name] != layer_path
        ]
        layers[layer] = {
            "expected_path": rel_path,
            "present": present,
            "symlinked": symlinked,
            "present_path": rel_path if present else None,
            "expected_children": list(DEFAULT_LAYER_CHILDREN.get(layer, ())),
            "present_children": sorted(child.name for child in layer_path.iterdir() if present and child.is_dir())
            if present
            else [],
            "alias_candidates": sorted(set(aliases)),
        }
    return layers


def build_inventory(root: Path, *, max_examples: int = 5) -> dict[str, Any]:
    """Build a structured inventory for a candidate KB root.

    Examples:
        >>> inventory = build_inventory(Path('.').resolve())  # doctest: +SKIP
        >>> 'layers' in inventory  # doctest: +SKIP
        True
    """
    layers = detect_layers(root)
    starter_files = {
        name: {
            "path": rel_path,
            "present": (root / rel_path).is_file() and not (root / rel_path).is_symlink(),
            "symlinked": (root / rel_path).is_symlink(),
        }
        for name, rel_path in STARTER_FILES.items()
    }
    classification_counts: Counter[str] = Counter()
    classification_examples: dict[str, list[str]] = defaultdict(list)
    layer_file_counts: Counter[str] = Counter()
    risky_paths: list[dict[str, Any]] = []
    likely_indexes_logs: list[dict[str, str]] = []
    canonical_candidates: list[dict[str, str]] = []
    seen_risky_paths: set[str] = set()
    seen_index_paths: set[str] = set()
    top_level_entries = []
    for entry in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        top_level_entries.append(
            {
                "path": relative_posix(root, entry),
                "kind": "directory" if entry.is_dir() else "file",
            }
        )
    directory_count = 0
    file_count = 0
    for path, is_dir in iter_repo_entries(root):
        if is_dir:
            directory_count += 1
            risk = assess_risk(root, path, "directory")
            if risk and risk["path"] not in seen_risky_paths:
                seen_risky_paths.add(risk["path"])
                risky_paths.append(risk)
            continue
        if path.is_symlink():
            risk = assess_risk(root, path, "symlinked_file")
            if risk and risk["path"] not in seen_risky_paths:
                seen_risky_paths.add(risk["path"])
                risky_paths.append(risk)
            continue
        file_count += 1
        text = read_text_file(path)
        classification, _evidence = classify_content(root, path, text)
        classification_counts[classification] += 1
        rel_path = relative_posix(root, path)
        top = path.relative_to(root).parts[0].lower()
        layer_file_counts[top] += 1
        if len(classification_examples[classification]) < max_examples:
            classification_examples[classification].append(rel_path)
        if (
            classification in {"wiki_page", "wiki_index", "unlayered_markdown", "unlayered_index"}
            and len(canonical_candidates) < max_examples * 2
        ):
            headings = extract_headings(text) if text else []
            canonical_candidates.append(
                {
                    "path": rel_path,
                    "classification": classification,
                    "title": headings[0] if headings else path.stem,
                }
            )
        role = infer_index_role(root, path, text)
        if role and rel_path not in seen_index_paths:
            seen_index_paths.add(rel_path)
            likely_indexes_logs.append({"path": rel_path, "role": role})
        risk = assess_risk(root, path, classification)
        if risk and risk["path"] not in seen_risky_paths:
            seen_risky_paths.add(risk["path"])
            risky_paths.append(risk)
    for layer_name, layer_info in layers.items():
        layer_info["file_count"] = layer_file_counts.get(layer_name, 0)
    present_layers = [name for name, info in layers.items() if info["present"]]
    missing_layers = [name for name, info in layers.items() if not info["present"]]
    kb_root_detected = len(present_layers) >= 2 or sum(1 for info in starter_files.values() if info["present"]) >= 2
    suggested_next_actions: list[str] = []
    if missing_layers:
        suggested_next_actions.append(
            "Run kb_bootstrap.py --root <path> to scaffold missing layers and starter files safely."
        )
    if classification_counts.get("unlayered_markdown"):
        suggested_next_actions.append(
            "Review unlayered markdown files as canonical material candidates "
            "before moving, rewriting, or deleting them."
        )
    if classification_counts.get("raw_source") and not classification_counts.get("wiki_page"):
        suggested_next_actions.append(
            "Create wiki summary stubs for raw sources before deeper synthesis or migration work."
        )
    if not any(item["role"] == "source_map" for item in likely_indexes_logs):
        suggested_next_actions.append("Add indexes/source-map.md to map raw evidence to wiki pages.")
    if not any(item["role"] == "activity_log" for item in likely_indexes_logs):
        suggested_next_actions.append("Add activity/log.md and append every mutating batch to it.")
    if risky_paths:
        suggested_next_actions.append("Inspect risky paths before any rename, cutover, or bulk rewrite.")
    if not suggested_next_actions:
        suggested_next_actions.append(
            "Layered KB signals look healthy; run kb_lint.py for deeper non-destructive checks."
        )
    return {
        "root": str(root),
        "kb_root_detected": kb_root_detected,
        "layers": layers,
        "starter_files": starter_files,
        "content_summary": {
            "total_files": file_count,
            "total_directories": directory_count,
            "by_classification": dict(sorted(classification_counts.items())),
            "examples": dict(sorted(classification_examples.items())),
        },
        "canonical_material_candidates": canonical_candidates,
        "canonical_material_candidates_sampled": len(canonical_candidates) >= max_examples * 2,
        "likely_indexes_logs": sorted(likely_indexes_logs, key=lambda item: item["path"]),
        "risky_paths": sorted(risky_paths, key=lambda item: (item["severity"], item["path"])),
        "top_level_entries": top_level_entries,
        "suggested_next_actions": suggested_next_actions,
    }


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the inventory command."""
    parser = argparse.ArgumentParser(
        description="Inspect a repository root for nerdbot KB structure and risks.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--root", default=".", help="KB or repository root to inspect")
    parser.add_argument("--max-examples", type=int, default=5, help="Maximum example paths per content class")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON instead of pretty-printed JSON")
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint for kb_inventory.py.

    Examples:
        python kb_inventory.py --root .
    """
    args = parse_args()
    try:
        root = resolve_existing_root(args.root)
        result = build_inventory(root, max_examples=max(1, args.max_examples))
    except Exception as exc:  # pragma: no cover - CLI safeguard
        warn(str(exc))
        print(emit_error_payload("kb_inventory", args.root))
        return 1
    indent = None if args.compact else 2
    print(json.dumps(result, indent=indent, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
