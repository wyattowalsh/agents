#!/usr/bin/env python3
"""Inspect a knowledge-base or repository root for nerdbot-style KB signals.

The script is read-only. It inventories default KB layers, classifies content
where possible, highlights risky paths, finds likely indexes/logs, and suggests
safe next actions.

Usage examples:
    python3 scripts/kb_inventory.py --root .
    python3 scripts/kb_inventory.py --root ./client-repo
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Iterator
from pathlib import Path, PurePosixPath
from typing import Any

from kb_path_policy import normalize_requested_root

DEFAULT_LAYER_PATHS: dict[str, str] = {
    "raw": "raw",
    "wiki": "wiki",
    "schema": "schema",
    "config": "config",
    "indexes": "indexes",
    "activity": "activity",
}

DEFAULT_LAYER_CHILDREN: dict[str, tuple[str, ...]] = {
    "raw": ("assets", "sources", "captures", "extracts"),
    "wiki": ("topics",),
    "schema": (),
    "config": (),
    "indexes": (),
    "activity": (),
}

DEFAULT_DIRECTORIES: tuple[str, ...] = (
    ".obsidian",
    ".obsidian/templates",
    ".obsidian/snippets",
    "raw",
    "raw/assets",
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
    "vault_config": "config/obsidian-vault.md",
    "vault_wiki_template": ".obsidian/templates/wiki-note-template.md",
    "vault_source_template": ".obsidian/templates/source-note-template.md",
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
OBSIDIAN_VOLATILE_FILES = {
    "app.json",
    "graph.json",
    "workspace.json",
    "workspace-mobile.json",
    "workspace",
}
OBSIDIAN_SHARED_DIRS = {"templates", "snippets"}
DATAVIEW_RECOMMENDED_FIELDS = {
    "title",
    "tags",
    "aliases",
    "kind",
    "status",
    "updated",
    "source_count",
    "cssclasses",
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
FRONTMATTER_PATTERN = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
FRONTMATTER_KEY_PATTERN = re.compile(r"^([A-Za-z0-9_-]+):", re.MULTILINE)
OBSIDIAN_REFERENCE_PATTERN = re.compile(r"(?P<embed>!)?\[\[([^\[\]\n]+)\]\]")


def warn(message: str) -> None:
    """Emit a human-readable warning to stderr."""
    print(f"warning: {message}", file=sys.stderr)


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
        >>> read_text_file(Path(__file__), max_bytes=32) is None
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
        >>> extract_headings("# Title\\n\\n## Sources")
        ['Title', 'Sources']
    """
    headings: list[str] = []
    for match in HEADING_PATTERN.finditer(text):
        heading = match.group(1).strip().rstrip("#").strip()
        if heading:
            headings.append(heading)
    return headings


def extract_frontmatter_block(text: str) -> str | None:
    """Return the frontmatter body without surrounding delimiters when present."""
    match = FRONTMATTER_PATTERN.match(text)
    return match.group(1) if match else None


def extract_frontmatter_keys(text: str) -> list[str]:
    """Return top-level frontmatter keys when present."""
    frontmatter = extract_frontmatter_block(text)
    if not frontmatter:
        return []
    return [match.group(1).strip() for match in FRONTMATTER_KEY_PATTERN.finditer(frontmatter)]


def _clean_frontmatter_scalar(value: str) -> str:
    return value.strip().strip('"').strip("'")


def extract_frontmatter_aliases(text: str) -> list[str]:
    """Extract alias values from simple YAML frontmatter patterns."""
    frontmatter = extract_frontmatter_block(text)
    if not frontmatter:
        return []
    aliases: list[str] = []
    lines = frontmatter.splitlines()
    in_aliases = False
    for line in lines:
        stripped = line.strip()
        if in_aliases:
            if stripped.startswith("- "):
                alias = _clean_frontmatter_scalar(stripped[2:])
                if alias:
                    aliases.append(alias)
                continue
            if not stripped or line.startswith((" ", "\t")):
                continue
            in_aliases = False
        if stripped.startswith(("aliases:", "alias:")):
            _, value = stripped.split(":", 1)
            value = value.strip()
            if not value:
                in_aliases = True
                continue
            if value.startswith("[") and value.endswith("]"):
                for part in value[1:-1].split(","):
                    alias = _clean_frontmatter_scalar(part)
                    if alias:
                        aliases.append(alias)
                continue
            alias = _clean_frontmatter_scalar(value)
            if alias:
                aliases.append(alias)
    return aliases


def split_obsidian_reference(value: str) -> str:
    """Remove display text or width suffixes from an Obsidian reference."""
    target, *_rest = value.split("|", 1)
    return target.strip()


def extract_obsidian_references(text: str) -> tuple[list[str], list[str]]:
    """Extract Obsidian wikilink and embed targets."""
    links: list[str] = []
    embeds: list[str] = []
    for match in OBSIDIAN_REFERENCE_PATTERN.finditer(text):
        target = split_obsidian_reference(match.group(2))
        if not target:
            continue
        if match.group("embed"):
            embeds.append(target)
        else:
            links.append(target)
    return links, embeds


def extract_markdown_links(text: str) -> list[str]:
    """Extract inline markdown link targets.

    Examples:
        >>> extract_markdown_links("See [map](indexes/source-map.md).")
        ['indexes/source-map.md']
    """
    return [target.strip() for target in LINK_PATTERN.findall(text)]


def extract_all_local_references(text: str) -> list[str]:
    """Extract markdown links, wikilinks, and embeds as a combined list."""
    obsidian_links, obsidian_embeds = extract_obsidian_references(text)
    combined = [*extract_markdown_links(text), *obsidian_links, *obsidian_embeds]
    return list(dict.fromkeys(reference for reference in combined if reference.strip()))


def has_provenance_markers(text: str, links: list[str] | None = None) -> bool:
    """Detect whether a document exposes provenance or source markers.

    Examples:
        >>> has_provenance_markers("## Sources\\n- [raw](../raw/sources/a.txt)")
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
    if top == ".obsidian":
        evidence.append("path:obsidian")
        return "obsidian_config", evidence
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
        if text and has_provenance_markers(text, extract_all_local_references(text)):
            evidence.append("content:provenance")
        if text:
            obsidian_links, obsidian_embeds = extract_obsidian_references(text)
            if obsidian_links:
                evidence.append("content:wikilinks")
            if obsidian_embeds:
                evidence.append("content:embeds")
            if extract_frontmatter_block(text):
                evidence.append("content:frontmatter")
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
    if parts and parts[0] == ".obsidian":
        if len(parts) > 1 and parts[1] in OBSIDIAN_SHARED_DIRS:
            reasons.append("shared Obsidian config should stay project-safe and reviewable")
        elif path.is_file() and path.name.lower() in OBSIDIAN_VOLATILE_FILES:
            reasons.append("volatile Obsidian workspace state should not be treated as canonical config")
        elif len(parts) > 1 and parts[1] == "plugins":
            reasons.append("community plugin config should be preserved carefully during vault migration")
    elif any(part.startswith(".") and part != ".git" for part in parts):
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


def detect_vault_surface(root: Path) -> dict[str, Any]:
    """Detect Obsidian vault signals and shared-surface state."""
    obsidian_root = root / ".obsidian"
    shared_config_paths: list[str] = []
    volatile_paths: list[str] = []
    plugin_paths: list[str] = []
    if obsidian_root.is_dir() and not obsidian_root.is_symlink():
        for child in sorted(obsidian_root.rglob("*")):
            if child.is_symlink():
                continue
            rel_path = relative_posix(root, child)
            if child.is_dir() and child.parent == obsidian_root and child.name in OBSIDIAN_SHARED_DIRS:
                shared_config_paths.append(rel_path)
            elif child.is_file() and child.name.lower() in OBSIDIAN_VOLATILE_FILES:
                volatile_paths.append(rel_path)
            elif (
                len(child.parts) >= len(obsidian_root.parts) + 1 and child.parts[len(obsidian_root.parts)] == "plugins"
            ):
                plugin_paths.append(rel_path)
    return {
        "obsidian_config_present": obsidian_root.is_dir() and not obsidian_root.is_symlink(),
        "shared_config_paths": sorted(set(shared_config_paths)),
        "volatile_paths": sorted(set(volatile_paths)),
        "plugin_paths": sorted(set(plugin_paths)),
    }


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
    dataview_field_counts: Counter[str] = Counter()
    risky_paths: list[dict[str, Any]] = []
    likely_indexes_logs: list[dict[str, str]] = []
    canonical_candidates: list[dict[str, str]] = []
    attachment_directories: set[str] = set()
    seen_risky_paths: set[str] = set()
    seen_index_paths: set[str] = set()
    obsidian_link_count = 0
    obsidian_embed_count = 0
    markdown_link_count = 0
    files_with_frontmatter = 0
    alias_count = 0
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
        if text and path.suffix.lower() in MARKDOWN_SUFFIXES:
            markdown_links = extract_markdown_links(text)
            obsidian_links, obsidian_embeds = extract_obsidian_references(text)
            frontmatter_keys = extract_frontmatter_keys(text)
            aliases = extract_frontmatter_aliases(text)
            markdown_link_count += len(markdown_links)
            obsidian_link_count += len(obsidian_links)
            obsidian_embed_count += len(obsidian_embeds)
            if frontmatter_keys:
                files_with_frontmatter += 1
            alias_count += len(aliases)
            for key in frontmatter_keys:
                lowered = key.lower()
                if lowered in DATAVIEW_RECOMMENDED_FIELDS:
                    dataview_field_counts[lowered] += 1
            for embed in obsidian_embeds:
                if "." not in Path(embed.split("#", 1)[0]).name:
                    continue
                embed_path = embed.split("#", 1)[0]
                if "/" in embed_path:
                    attachment_directories.add(str(PurePosixPath(embed_path).parent))
                else:
                    attachment_directories.add(".")
        if (
            classification in {"wiki_page", "wiki_index", "unlayered_markdown", "unlayered_index"}
            and len(canonical_candidates) < max_examples * 2
        ):
            headings = extract_headings(text) if text else []
            aliases = extract_frontmatter_aliases(text) if text else []
            canonical_candidates.append(
                {
                    "path": rel_path,
                    "classification": classification,
                    "title": headings[0] if headings else path.stem,
                    "aliases": aliases[:3],
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
    vault_surface = detect_vault_surface(root)
    vault_detected = bool(
        vault_surface["obsidian_config_present"]
        or obsidian_link_count
        or obsidian_embed_count
        or files_with_frontmatter
    )
    if vault_surface["obsidian_config_present"] and obsidian_link_count and markdown_link_count == 0:
        vault_mode = "obsidian_native_vault"
    elif vault_surface["obsidian_config_present"] and (
        obsidian_link_count or obsidian_embed_count or files_with_frontmatter
    ):
        vault_mode = "mixed_vault" if markdown_link_count else "obsidian_native_vault"
    elif vault_detected:
        vault_mode = "legacy_markdown_repo"
    else:
        vault_mode = "legacy_markdown_repo"
    suggested_next_actions: list[str] = []
    if missing_layers:
        suggested_next_actions.append(
            "Run kb_bootstrap.py --root <path> to scaffold missing layers and starter files safely."
        )
    if vault_mode == "legacy_markdown_repo" and (
        classification_counts.get("unlayered_markdown") or classification_counts.get("wiki_page")
    ):
        suggested_next_actions.append(
            "Plan an Obsidian-native overhaul before expansion or refinement: normalize frontmatter, "
            "note names, aliases, and link style first."
        )
    if vault_mode == "mixed_vault":
        suggested_next_actions.append(
            "Normalize shared `.obsidian/` surfaces, note metadata, and link style before deeper synthesis "
            "or migration work."
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
    if vault_detected and not vault_surface["shared_config_paths"]:
        suggested_next_actions.append(
            "Add `.obsidian/templates/` and `.obsidian/snippets/` or document why the vault intentionally "
            "omits shared surfaces."
        )
    if vault_surface["volatile_paths"]:
        suggested_next_actions.append(
            "Review tracked volatile `.obsidian` files and keep only project-safe shared config under version control."
        )
    if obsidian_embed_count and "raw/assets" not in attachment_directories:
        suggested_next_actions.append(
            "Standardize local supporting assets under `raw/assets/` unless the repo already has an approved "
            "attachment convention."
        )
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
        "vault": {
            "detected": vault_detected,
            "mode": vault_mode,
            "shared_config_paths": vault_surface["shared_config_paths"],
            "volatile_paths": vault_surface["volatile_paths"],
            "plugin_paths": vault_surface["plugin_paths"],
            "attachment_directories": sorted(attachment_directories),
            "link_summary": {
                "markdown_links": markdown_link_count,
                "obsidian_links": obsidian_link_count,
                "obsidian_embeds": obsidian_embed_count,
            },
            "frontmatter_summary": {
                "files_with_frontmatter": files_with_frontmatter,
                "alias_count": alias_count,
                "dataview_field_counts": dict(sorted(dataview_field_counts.items())),
            },
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
