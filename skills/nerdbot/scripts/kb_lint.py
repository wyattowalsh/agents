#!/usr/bin/env python3
"""Run non-destructive lint checks for a nerdbot-style layered KB.

The script checks for missing layers/files, missing provenance markers, orphan
wiki pages, duplicate or overlapping pages, broken local links, raw sources
without summary stubs where detectable, and index/activity coverage heuristics.

Usage examples:
    python kb_lint.py --root .
    uv run python skills/nerdbot/scripts/kb_lint.py --root ./knowledge-base
    uv run python skills/nerdbot/scripts/kb_lint.py --root ./client-repo --include-unlayered
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote

from kb_inventory import (
    DEFAULT_LAYER_PATHS,
    MARKDOWN_SUFFIXES,
    OBSIDIAN_VOLATILE_FILES,
    STARTER_FILES,
    build_inventory,
    emit_error_payload,
    extract_all_local_references,
    extract_frontmatter_aliases,
    extract_frontmatter_block,
    extract_frontmatter_keys,
    extract_headings,
    extract_markdown_links,
    extract_obsidian_references,
    is_index_like_path,
    iter_repo_files,
    normalize_anchor,
    normalize_title,
    read_text_file,
    relative_posix,
    resolve_existing_root,
    warn,
)

SEVERITY_ORDER = {"critical": 0, "warning": 1, "suggestion": 2}
LOG_ENTRY_PATTERN = re.compile(r"^\s*(?:[-*]\s+|\d+\.\s+|\d{4}-\d{2}-\d{2})", re.MULTILINE)
SCHEME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
EXPLICIT_PROVENANCE_HEADINGS = {"provenance", "sources", "evidence", "references", "canonical-material"}
ACTIVITY_ENTRY_HEADER_PATTERN = re.compile(r"^### \[\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2})?\] .+$", re.MULTILINE)
MARKDOWN_HEADING_PATTERN = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*$", re.MULTILINE)
INLINE_CODE_PATTERN = re.compile(r"`([^`\n]+)`")
BLOCK_ID_PATTERN = re.compile(r"(?:^|\s)\^([A-Za-z0-9-]+)\s*$", re.MULTILINE)
PATH_REFERENCE_PATTERN = re.compile(
    r"(?P<path>(?:\.\./|\.?/)?(?:[\w.-]+/)*[\w .-]+\.[a-z0-9]{1,8}(?:#[^\s`|)]+)?)",
    re.IGNORECASE,
)
PROVENANCE_FIELD_PATTERN = re.compile(
    r"^\s*(provenance|sources?|evidence|references|canonical material)\s*:\s*(.+)$",
    re.IGNORECASE | re.MULTILINE,
)
KB_SCAN_PREFIXES = tuple(f"{layer}/" for layer in DEFAULT_LAYER_PATHS)
KB_ROOT_LAYERS = frozenset(DEFAULT_LAYER_PATHS)
OVERVIEW_PROVENANCE_PATHS = frozenset(
    {
        STARTER_FILES["source_map"],
        STARTER_FILES["coverage_index"],
        STARTER_FILES["activity_log"],
    }
)
MIN_PAGE_WORDS = 5
MIN_INDEX_NARRATIVE_WORDS = 20


@dataclass(slots=True)
class MarkdownPage:
    """Structured view of a markdown file used by lint checks.

    Examples:
        >>> page = MarkdownPage(Path('wiki/index.md'), 'wiki/index.md', '# KB', 'KB', 'kb', set(), [], True, True, 'kb')
        >>> page.is_wiki
        True
    """

    path: Path
    relative_path: str
    text: str
    title: str
    normalized_title: str
    headings: set[str]
    links: list[str]
    is_wiki: bool
    is_index_like: bool
    plain_excerpt: str
    aliases: set[str] = None  # type: ignore[assignment]
    block_ids: set[str] = None  # type: ignore[assignment]
    frontmatter_keys: set[str] = None  # type: ignore[assignment]
    has_frontmatter: bool = False

    def __post_init__(self) -> None:
        if self.aliases is None:
            self.aliases = set()
        if self.block_ids is None:
            self.block_ids = set()
        if self.frontmatter_keys is None:
            self.frontmatter_keys = set()


def make_issue(
    rule: str,
    severity: str,
    path: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a normalized lint issue payload."""
    issue: dict[str, Any] = {
        "rule": rule,
        "severity": severity,
        "path": path,
        "message": message,
    }
    if details:
        issue["details"] = details
    return issue


def markdown_to_plain_text(text: str, *, max_words: int = 400) -> str:
    """Reduce markdown to a comparable text snippet.

    Examples:
        >>> markdown_to_plain_text('# Title\n\nSee [map](x.md).', max_words=5)
        'title see map'
    """
    without_frontmatter = text
    if text.startswith("---\n"):
        parts = text.split("\n---\n", 1)
        if len(parts) == 2:
            without_frontmatter = parts[1]
    without_code = re.sub(r"```.*?```", " ", without_frontmatter, flags=re.DOTALL)
    without_inline_code = re.sub(r"`[^`]+`", " ", without_code)
    without_links = re.sub(r"(?<!!)\[([^\]]+)\]\([^)]+\)", r"\1", without_inline_code)
    without_obsidian_links = re.sub(
        r"!?\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]",
        lambda match: (match.group(2) or Path(match.group(1)).stem),
        without_links,
    )
    normalized = re.sub(r"[^a-zA-Z0-9\s]+", " ", without_obsidian_links).lower()
    words = normalized.split()
    return " ".join(words[:max_words])


def extract_block_ids(text: str) -> set[str]:
    """Extract Obsidian block IDs from note content."""
    return {match.group(1) for match in BLOCK_ID_PATTERN.finditer(text)}


def collect_markdown_pages(root: Path, *, include_unlayered: bool = False) -> dict[str, MarkdownPage]:
    """Collect markdown files under the root for lint analysis.

    Examples:
        >>> isinstance(collect_markdown_pages(Path('.').resolve()), dict)  # doctest: +SKIP
        True
    """
    pages: dict[str, MarkdownPage] = {}
    for path in iter_repo_files(root):
        if path.suffix.lower() not in MARKDOWN_SUFFIXES:
            continue
        text = read_text_file(path, max_bytes=1_048_576)
        if text is None:
            continue
        rel_path = relative_posix(root, path)
        if not include_unlayered and not rel_path.startswith(KB_SCAN_PREFIXES):
            continue
        headings = extract_headings(text)
        title = headings[0] if headings else path.stem.replace("-", " ").replace("_", " ").title()
        is_wiki = rel_path.startswith("wiki/")
        links = extract_all_local_references(text)
        pages[rel_path] = MarkdownPage(
            path=path,
            relative_path=rel_path,
            text=text,
            title=title,
            normalized_title=normalize_title(title),
            headings=build_heading_anchor_set(headings),
            links=links,
            is_wiki=is_wiki,
            is_index_like=is_index_like_path(Path(rel_path)),
            plain_excerpt=markdown_to_plain_text(text),
            aliases=set(extract_frontmatter_aliases(text)),
            block_ids=extract_block_ids(text),
            frontmatter_keys=set(key.lower() for key in extract_frontmatter_keys(text)),
            has_frontmatter=extract_frontmatter_block(text) is not None,
        )
    return pages


def build_heading_anchor_set(headings: list[str]) -> set[str]:
    """Build markdown anchors, including duplicate-heading suffixes.

    Examples:
        >>> sorted(build_heading_anchor_set(['Title', 'Title']))
        ['title', 'title-1']
    """
    anchors: set[str] = set()
    counts: Counter[str] = Counter()
    for heading in headings:
        base = normalize_anchor(heading)
        if not base:
            continue
        suffix = counts[base]
        anchor = base if suffix == 0 else f"{base}-{suffix}"
        anchors.add(anchor)
        counts[base] += 1
    return anchors


def extract_markdown_sections(text: str) -> list[tuple[str, str]]:
    """Extract heading-scoped markdown blocks, including nested content.

    Examples:
        >>> extract_markdown_sections("## Sources\\n- one\\n### Nested\\n- two\\n## End\\nDone")[0][0]
        'sources'
    """
    matches = list(MARKDOWN_HEADING_PATTERN.finditer(text))
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        heading = match.group(2).strip().rstrip("#").strip()
        normalized_heading = normalize_anchor(heading)
        if not normalized_heading:
            continue
        level = len(match.group(1))
        end = len(text)
        for next_match in matches[index + 1 :]:
            if len(next_match.group(1)) <= level:
                end = next_match.start()
                break
        sections.append((normalized_heading, text[match.start() : end].strip()))
    return sections


def extract_reference_candidates(text: str) -> set[str]:
    """Extract likely local provenance references from markdown text.

    Examples:
        >>> sorted(extract_reference_candidates("`raw/extracts/a.md#x` and [doc](../docs/spec.md)"))
        ['../docs/spec.md', 'raw/extracts/a.md#x']
    """
    candidates = set(extract_all_local_references(text))
    candidates.update(match.group(1).strip() for match in INLINE_CODE_PATTERN.finditer(text))
    candidates.update(match.group("path").strip() for match in PATH_REFERENCE_PATTERN.finditer(text))
    return {candidate for candidate in candidates if candidate}


def canonicalize_reference_path(page: MarkdownPage, candidate: str) -> str | None:
    """Normalize a local reference to a KB-root-relative path when possible.

    Examples:
        >>> page = MarkdownPage(Path('wiki/index.md'), 'wiki/index.md', '', 'KB', 'kb', set(), [], True, True, '')
        >>> canonicalize_reference_path(page, '../indexes/source-map.md')
        'indexes/source-map.md'
        >>> canonicalize_reference_path(page, 'raw/extracts/source.md#summary')
        'raw/extracts/source.md'
    """
    cleaned = unquote(candidate.strip().strip("`"))
    if not cleaned or cleaned.startswith("#") or SCHEME_PATTERN.match(cleaned):
        return None
    path_part = cleaned.split("?", 1)[0].split("#", 1)[0]
    if not path_part:
        return None
    pure_candidate = PurePosixPath(path_part)
    if not pure_candidate.parts:
        return None
    if pure_candidate.parts[0].lower() in KB_ROOT_LAYERS:
        return pure_candidate.as_posix()
    source_parent = PurePosixPath(page.relative_path).parent
    normalized_parts: list[str] = []
    for part in (*source_parent.parts, *pure_candidate.parts):
        if part in {"", "."}:
            continue
        if part == "..":
            if not normalized_parts:
                return None
            normalized_parts.pop()
            continue
        normalized_parts.append(part)
    if not normalized_parts:
        return None
    return PurePosixPath(*normalized_parts).as_posix()


def looks_like_local_path_reference(candidate: str) -> bool:
    """Return True when a candidate resembles a repo-local file reference."""
    cleaned = unquote(candidate.strip().strip("`"))
    if not cleaned or cleaned.startswith("#") or SCHEME_PATTERN.match(cleaned):
        return False
    path_part = cleaned.split("?", 1)[0].split("#", 1)[0]
    if not path_part:
        return False
    has_suffix = bool(Path(path_part).suffix)
    if path_part.startswith(("./", "../")) or "/" in path_part:
        return has_suffix or path_part.lower().lstrip("./").startswith("raw/")
    return has_suffix


def is_raw_reference(candidate: str) -> bool:
    """Return True when a provenance candidate points into the raw layer."""
    cleaned = unquote(candidate.strip().strip("`")).split("?", 1)[0]
    lowered = cleaned.lower().lstrip("./")
    lowered = lowered.split("#", 1)[0]
    return lowered.startswith("raw/") or "/raw/" in lowered


def is_navigation_reference(candidate: str) -> bool:
    """Return True when a candidate points to indexes or activity-log navigation."""
    cleaned = unquote(candidate.strip().strip("`")).split("?", 1)[0]
    lowered = cleaned.lower().lstrip("./")
    lowered = lowered.split("#", 1)[0]
    return lowered.startswith(("indexes/", "activity/")) or "/indexes/" in lowered or "/activity/" in lowered


def extract_explicit_provenance_blocks(page: MarkdownPage) -> list[str]:
    """Return blocks that explicitly declare provenance, sources, or canonical material.

    Examples:
        >>> page = MarkdownPage(
        ...     Path('wiki/a.md'),
        ...     'wiki/a.md',
        ...     '## Provenance\\n`raw/extracts/a.md#x`',
        ...     'A',
        ...     'a',
        ...     {'provenance'},
        ...     [],
        ...     True,
        ...     False,
        ...     'raw extracts',
        ... )
        >>> extract_explicit_provenance_blocks(page)
        ['## Provenance\\n`raw/extracts/a.md#x`']
    """
    blocks = [
        block for heading, block in extract_markdown_sections(page.text) if heading in EXPLICIT_PROVENANCE_HEADINGS
    ]
    blocks.extend(match.group(0).strip() for match in PROVENANCE_FIELD_PATTERN.finditer(page.text))
    return blocks


def count_narrative_words(text: str) -> int:
    """Count prose-like words while ignoring headings, tables, lists, and code blocks."""
    if text.startswith("---\n"):
        parts = text.split("\n---\n", 1)
        if len(parts) == 2:
            text = parts[1]
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    lines: list[str] = []
    in_code_block = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block or not line:
            continue
        if MARKDOWN_HEADING_PATTERN.match(raw_line):
            continue
        if line.startswith(("|", ">")):
            continue
        if re.match(r"^(?:[-*+]\s+|\d+\.\s+)", line):
            continue
        lines.append(line)
    normalized = re.sub(r"[^a-zA-Z0-9\s]+", " ", " ".join(lines))
    return len(normalized.split())


def requires_provenance_check(page: MarkdownPage) -> bool:
    """Return True when a wiki page is substantive enough to require provenance linting.

    Index-like pages are only checked when they contain meaningful narrative prose,
    which avoids flagging navigation-only maps and logs.
    """
    if not page.is_wiki:
        return False
    if page.is_index_like:
        return count_narrative_words(page.text) >= MIN_INDEX_NARRATIVE_WORDS
    return len(page.plain_excerpt.split()) >= MIN_PAGE_WORDS


def has_explicit_provenance(page: MarkdownPage) -> bool:
    """Return True when a page contains an explicit provenance section or field.

    Examples:
        >>> page = MarkdownPage(
        ...     Path('wiki/a.md'),
        ...     'wiki/a.md',
        ...     '## Provenance\\n'
        ...     '| Claim | Raw or canonical material |\\n'
        ...     '| --- | --- |\\n'
        ...     '| Summary | `raw/extracts/a.md#intro` |',
        ...     'A',
        ...     'a',
        ...     {'provenance'},
        ...     [],
        ...     True,
        ...     False,
        ...     'provenance raw',
        ... )
        >>> has_explicit_provenance(page)
        True
        >>> overview = MarkdownPage(
        ...     Path('wiki/index.md'),
        ...     'wiki/index.md',
        ...     '## Provenance\\n'
        ...     '| Section | Raw or canonical material |\\n'
        ...     '| --- | --- |\\n'
        ...     '| Summary | `../indexes/source-map.md` |\\n'
        ...     '| Coverage | `../indexes/coverage.md` |\\n'
        ...     '| Activity | `../activity/log.md` |',
        ...     'Overview',
        ...     'overview',
        ...     {'provenance'},
        ...     [],
        ...     True,
        ...     True,
        ...     'overview sources',
        ... )
        >>> has_explicit_provenance(overview)
        True
    """
    blocks = extract_explicit_provenance_blocks(page)
    if not blocks:
        return False
    block_references = {
        block: {
            reference for reference in extract_reference_candidates(block) if looks_like_local_path_reference(reference)
        }
        for block in blocks
    }
    block_reference_paths = {
        block: {
            normalized_path
            for reference in references
            if (normalized_path := canonicalize_reference_path(page, reference)) is not None
        }
        for block, references in block_references.items()
    }
    if any(is_raw_reference(reference) for references in block_references.values() for reference in references):
        return True
    has_canonical_material_reference = any(
        "canonical material" in block.lower()
        and any(
            not reference.startswith("raw/") and not reference.startswith(("indexes/", "activity/"))
            for reference in references
        )
        for block, references in block_reference_paths.items()
    )
    if has_canonical_material_reference:
        return True
    page_reference_paths = {
        normalized_path
        for reference in page.links
        if (normalized_path := canonicalize_reference_path(page, reference)) is not None
    }
    page_reference_paths.update(
        normalized_path
        for references in block_references.values()
        for reference in references
        if (normalized_path := canonicalize_reference_path(page, reference)) is not None
    )
    return page.is_index_like and OVERVIEW_PROVENANCE_PATHS.issubset(page_reference_paths)


def build_note_lookup(pages: dict[str, MarkdownPage]) -> dict[str, list[MarkdownPage]]:
    """Build a lookup of note names and aliases to markdown pages."""
    lookup: dict[str, list[MarkdownPage]] = defaultdict(list)
    for page in pages.values():
        note_names = {
            page.path.stem,
            page.relative_path.removesuffix(page.path.suffix),
            page.relative_path,
        }
        note_names.update(page.aliases)
        for note_name in note_names:
            key = normalize_title(note_name.removesuffix(".md"))
            if page not in lookup[key]:
                lookup[key].append(page)
    return lookup


def resolve_path_like_target(
    source_page: MarkdownPage,
    target: str,
    *,
    root: Path | None = None,
) -> tuple[Path | None, str | None]:
    """Resolve a path-like local reference relative to a source page."""
    target = unquote(target.strip())
    if not target or target.startswith("#"):
        return source_page.path, target[1:] if target.startswith("#") else None
    if SCHEME_PATTERN.match(target):
        return None, None
    if target.startswith("mailto:") or target.startswith("tel:"):
        return None, None
    link_target = target.split("?", 1)[0]
    if "#" in link_target:
        path_part, anchor = link_target.split("#", 1)
    else:
        path_part, anchor = link_target, None
    if root is not None:
        candidate = (root / path_part).resolve()
    else:
        candidate = (source_page.path.parent / path_part).resolve()
    candidates = []
    if candidate.suffix:
        candidates.append(candidate)
    else:
        candidates.extend([candidate, candidate.with_suffix(".md"), candidate / "index.md", candidate / "README.md"])
    for option in candidates:
        if option.exists():
            if option.is_dir():
                continue
            return option, anchor
    return candidate, anchor


def resolve_obsidian_target(
    source_page: MarkdownPage,
    target: str,
    note_lookup: dict[str, list[MarkdownPage]],
    root: Path,
) -> tuple[Path | None, str | None, list[str]]:
    """Resolve an Obsidian note reference using names, aliases, or paths."""
    cleaned = unquote(target.strip())
    if not cleaned:
        return None, None, []
    if cleaned.startswith("#"):
        return source_page.path, cleaned[1:], []
    link_target = cleaned.split("?", 1)[0]
    if "#" in link_target:
        note_part, anchor = link_target.split("#", 1)
    else:
        note_part, anchor = link_target, None
    note_part = note_part.strip()
    if not note_part:
        return source_page.path, anchor, []
    path_like = note_part.startswith(("./", "../")) or Path(note_part).suffix.lower() in MARKDOWN_SUFFIXES
    if path_like:
        root_relative = not note_part.startswith(("./", "../"))
        resolved_path, resolved_anchor = resolve_path_like_target(
            source_page,
            link_target,
            root=root if root_relative else None,
        )
        return resolved_path, resolved_anchor, []
    matches = note_lookup.get(normalize_title(note_part.removesuffix(".md")), [])
    if len(matches) == 1:
        return matches[0].path, anchor, []
    if len(matches) > 1:
        return None, anchor, sorted(match.relative_path for match in matches)
    return None, anchor, []


def resolve_link_target(
    source_page: MarkdownPage,
    target: str,
    note_lookup: dict[str, list[MarkdownPage]],
    root: Path,
) -> tuple[Path | None, str | None, list[str]]:
    """Resolve a local link target relative to a source page."""
    normalized_target = unquote(target.strip())
    if not normalized_target:
        return None, None, []
    if normalized_target.startswith(("./", "../", "/")) or Path(normalized_target.split("#", 1)[0]).suffix:
        path_part = normalized_target.split("#", 1)[0]
        first_part = PurePosixPath(path_part).parts[0] if PurePosixPath(path_part).parts else ""
        root_relative = first_part in (*KB_ROOT_LAYERS, ".obsidian") and not normalized_target.startswith(
            ("./", "../", "/")
        )
        resolved_path, anchor = resolve_path_like_target(
            source_page, normalized_target, root=root if root_relative else None
        )
        return resolved_path, anchor, []
    return resolve_obsidian_target(source_page, normalized_target, note_lookup, root)


def lint_structure(root: Path, inventory: dict[str, Any]) -> list[dict[str, Any]]:
    """Check for missing layers and default starter files."""
    issues: list[dict[str, Any]] = []
    total_content = inventory["content_summary"]["total_files"]
    layers = inventory["layers"]
    for layer_name, layer_path in DEFAULT_LAYER_PATHS.items():
        if layers[layer_name]["present"]:
            continue
        alias_candidates = layers[layer_name]["alias_candidates"]
        severity = "critical" if layer_name in {"raw", "wiki"} and total_content else "warning"
        if alias_candidates:
            severity = "suggestion"
        issues.append(
            make_issue(
                "missing_layer",
                severity,
                layer_path,
                f"Missing default layer '{layer_name}' at {layer_path}.",
                {"layer": layer_name, "alias_candidates": alias_candidates},
            )
        )
    role_by_starter = {
        "wiki_index": "wiki_index",
        "coverage_index": "coverage_index",
        "source_map": "source_map",
        "activity_log": "activity_log",
        "vault_config": "vault_config",
        "vault_wiki_template": "vault_wiki_template",
        "vault_source_template": "vault_source_template",
    }
    for starter_name, rel_path in STARTER_FILES.items():
        if inventory["starter_files"][starter_name]["present"]:
            continue
        severity = "warning" if total_content else "suggestion"
        alternative_paths = [
            item["path"]
            for item in inventory["likely_indexes_logs"]
            if item["role"] == role_by_starter[starter_name] and item["path"] != rel_path
        ]
        if alternative_paths:
            severity = "suggestion"
        issues.append(
            make_issue(
                "missing_starter_file",
                severity,
                rel_path,
                f"Missing starter file {rel_path}.",
                {"starter": starter_name, "alternative_paths": alternative_paths},
            )
        )
    return issues


def lint_provenance(pages: dict[str, MarkdownPage]) -> list[dict[str, Any]]:
    """Check wiki pages for provenance or source markers."""
    issues: list[dict[str, Any]] = []
    for page in pages.values():
        if not requires_provenance_check(page):
            continue
        if has_explicit_provenance(page):
            continue
        issues.append(
            make_issue(
                "missing_provenance_marker",
                "warning",
                page.relative_path,
                "Wiki page lacks an explicit provenance section or clearly labeled source marker.",
                {"title": page.title},
            )
        )
    return issues


def lint_links(root: Path, pages: dict[str, MarkdownPage]) -> tuple[list[dict[str, Any]], dict[str, set[str]]]:
    """Check local links and return inbound-link map for wiki orphan detection."""
    issues: list[dict[str, Any]] = []
    inbound_links: dict[str, set[str]] = defaultdict(set)
    note_lookup = build_note_lookup(pages)
    for page in pages.values():
        for raw_target in page.links:
            resolved_path, anchor, collisions = resolve_link_target(page, raw_target, note_lookup, root)
            if collisions:
                issues.append(
                    make_issue(
                        "ambiguous_obsidian_link",
                        "warning",
                        page.relative_path,
                        f"Obsidian link target is ambiguous: {raw_target}",
                        {"target": raw_target, "matches": collisions},
                    )
                )
                continue
            if resolved_path is None:
                if not SCHEME_PATTERN.match(raw_target):
                    issues.append(
                        make_issue(
                            "broken_local_link",
                            "critical",
                            page.relative_path,
                            f"Broken local link target: {raw_target}",
                            {"target": raw_target},
                        )
                    )
                continue
            rel_target = relative_posix(root, resolved_path)
            if not resolved_path.is_relative_to(root):
                issues.append(
                    make_issue(
                        "out_of_root_local_link",
                        "warning",
                        page.relative_path,
                        f"Local markdown link escapes the KB root: {raw_target}",
                        {"target": raw_target},
                    )
                )
                continue
            if not resolved_path.exists():
                issues.append(
                    make_issue(
                        "broken_local_link",
                        "critical",
                        page.relative_path,
                        f"Broken local link target: {raw_target}",
                        {"target": raw_target},
                    )
                )
                continue
            if rel_target in pages and rel_target != page.relative_path:
                inbound_links[rel_target].add(page.relative_path)
            if anchor and rel_target in pages:
                target_page = pages[rel_target]
                if anchor.startswith("^"):
                    block_id = anchor[1:]
                    if block_id and block_id not in target_page.block_ids:
                        issues.append(
                            make_issue(
                                "broken_obsidian_block_ref",
                                "critical",
                                page.relative_path,
                                f"Broken Obsidian block reference '{anchor}' in link target {raw_target}.",
                                {"target": raw_target, "resolved_target": rel_target},
                            )
                        )
                    continue
                normalized_anchor = normalize_anchor(anchor)
                if normalized_anchor and normalized_anchor not in target_page.headings:
                    issues.append(
                        make_issue(
                            "broken_local_anchor",
                            "critical",
                            page.relative_path,
                            f"Broken markdown anchor '{anchor}' in link target {raw_target}.",
                            {"target": raw_target, "resolved_target": rel_target},
                        )
                    )
    return issues, inbound_links


def lint_orphans(pages: dict[str, MarkdownPage], inbound_links: dict[str, set[str]]) -> list[dict[str, Any]]:
    """Detect wiki pages that have no inbound links."""
    issues: list[dict[str, Any]] = []
    for page in pages.values():
        if not page.is_wiki or page.is_index_like or page.relative_path == STARTER_FILES["wiki_index"]:
            continue
        if inbound_links.get(page.relative_path):
            continue
        issues.append(
            make_issue(
                "orphan_wiki_page",
                "warning",
                page.relative_path,
                "Wiki page has no inbound links from other markdown pages under the KB root.",
                {"title": page.title},
            )
        )
    return issues


def lint_duplicates_and_overlap(pages: dict[str, MarkdownPage]) -> list[dict[str, Any]]:
    """Detect duplicate titles and overlapping wiki pages."""
    issues: list[dict[str, Any]] = []
    wiki_pages = [page for page in pages.values() if page.is_wiki and not page.is_index_like]
    title_map: dict[str, list[MarkdownPage]] = defaultdict(list)
    for page in wiki_pages:
        title_map[page.normalized_title].append(page)
    for title, grouped_pages in sorted(title_map.items()):
        if len(grouped_pages) < 2:
            continue
        issues.append(
            make_issue(
                "duplicate_wiki_title",
                "warning",
                grouped_pages[0].relative_path,
                f"Multiple wiki pages normalize to the same title '{title}'.",
                {"paths": sorted(page.relative_path for page in grouped_pages)},
            )
        )
    alias_map: dict[str, list[MarkdownPage]] = defaultdict(list)
    for page in wiki_pages:
        for alias in page.aliases:
            alias_map[normalize_title(alias)].append(page)
    for alias, grouped_pages in sorted(alias_map.items()):
        if len(grouped_pages) < 2:
            continue
        issues.append(
            make_issue(
                "duplicate_obsidian_alias",
                "warning",
                grouped_pages[0].relative_path,
                f"Multiple wiki pages share the same normalized alias '{alias}'.",
                {"paths": sorted(page.relative_path for page in grouped_pages)},
            )
        )
    overlap_candidates: list[tuple[float, MarkdownPage, MarkdownPage]] = []
    for index, page in enumerate(wiki_pages):
        for other in wiki_pages[index + 1 :]:
            if page.normalized_title == other.normalized_title:
                continue
            title_tokens_a = set(page.normalized_title.split("-"))
            title_tokens_b = set(other.normalized_title.split("-"))
            union = title_tokens_a | title_tokens_b
            title_overlap = len(title_tokens_a & title_tokens_b) / len(union) if union else 0.0
            if (
                title_overlap < 0.34
                and page.normalized_title not in other.normalized_title
                and other.normalized_title not in page.normalized_title
            ):
                continue
            similarity = SequenceMatcher(None, page.plain_excerpt[:1500], other.plain_excerpt[:1500]).ratio()
            if similarity >= 0.76:
                overlap_candidates.append((similarity, page, other))
    for similarity, page, other in sorted(overlap_candidates, key=lambda item: item[0], reverse=True)[:20]:
        issues.append(
            make_issue(
                "overlapping_wiki_pages",
                "suggestion",
                page.relative_path,
                "Wiki pages appear to overlap significantly and may need consolidation or clearer scoping.",
                {
                    "other_path": other.relative_path,
                    "similarity": round(similarity, 3),
                    "titles": [page.title, other.title],
                },
            )
        )
    return issues


def lint_raw_summary_stubs(root: Path, pages: dict[str, MarkdownPage]) -> list[dict[str, Any]]:
    """Detect raw sources without obvious wiki summary stubs or source-map entries."""
    issues: list[dict[str, Any]] = []
    wiki_pages = [page for page in pages.values() if page.is_wiki]
    wiki_titles = {page.normalized_title for page in wiki_pages}
    source_map_text = pages.get(STARTER_FILES["source_map"])
    source_map_blob = source_map_text.text.lower() if source_map_text else ""
    wiki_texts = [page.text.lower() for page in wiki_pages]
    for path in iter_repo_files(root):
        rel_path = relative_posix(root, path)
        if not rel_path.startswith(("raw/sources/", "raw/captures/", "raw/extracts/")):
            continue
        if path.name.startswith("."):
            continue
        normalized_stem = normalize_title(path.stem)
        mentioned = rel_path.lower() in source_map_blob or path.name.lower() in source_map_blob
        if not mentioned:
            mentioned = any(rel_path.lower() in text or path.name.lower() in text for text in wiki_texts)
        if normalized_stem in wiki_titles or mentioned:
            continue
        issues.append(
            make_issue(
                "raw_source_missing_summary_stub",
                "warning",
                rel_path,
                "Raw source has no detectable wiki summary stub, wiki mention, or source-map entry.",
                {"normalized_stem": normalized_stem},
            )
        )
    return issues


def lint_schema_config_drift(root: Path, pages: dict[str, MarkdownPage]) -> list[dict[str, Any]]:
    """Flag empty or weakly populated schema/config layers when KB content exists."""
    issues: list[dict[str, Any]] = []
    wiki_pages = [page for page in pages.values() if page.is_wiki and not page.is_index_like]
    raw_sources = [
        path
        for path in iter_repo_files(root)
        if relative_posix(root, path).startswith(("raw/sources/", "raw/captures/", "raw/extracts/"))
    ]
    schema_files = [path for path in iter_repo_files(root) if relative_posix(root, path).startswith("schema/")]
    config_files = [path for path in iter_repo_files(root) if relative_posix(root, path).startswith("config/")]
    if (wiki_pages or raw_sources) and not schema_files and (root / "schema").is_dir():
        issues.append(
            make_issue(
                "empty_schema_layer",
                "suggestion",
                "schema/",
                "Schema layer exists but has no files to describe page shapes, contracts, or taxonomies.",
            )
        )
    if (wiki_pages or raw_sources) and not config_files and (root / "config").is_dir():
        issues.append(
            make_issue(
                "empty_config_layer",
                "suggestion",
                "config/",
                "Config layer exists but has no files to capture KB-specific operational settings.",
            )
        )
    return issues


def lint_obsidian_vault(root: Path, pages: dict[str, MarkdownPage]) -> list[dict[str, Any]]:
    """Check Obsidian-native surfaces, shared config, and metadata hygiene."""
    issues: list[dict[str, Any]] = []
    obsidian_root = root / ".obsidian"
    wiki_pages = [page for page in pages.values() if page.is_wiki and not page.is_index_like]
    obsidian_signal_pages = [
        page
        for page in pages.values()
        if page.has_frontmatter or "[[" in page.text or "![[" in page.text or page.aliases
    ]
    if obsidian_signal_pages and not obsidian_root.is_dir():
        issues.append(
            make_issue(
                "missing_obsidian_root",
                "suggestion",
                ".obsidian/",
                "Vault-like note syntax or metadata exists, but the repository has no shared `.obsidian/` root.",
            )
        )
    if obsidian_root.is_dir():
        for shared_dir in ("templates", "snippets"):
            shared_path = obsidian_root / shared_dir
            if not shared_path.is_dir():
                issues.append(
                    make_issue(
                        "missing_shared_obsidian_surface",
                        "suggestion",
                        relative_posix(root, shared_path),
                        f"Missing shared Obsidian surface: {relative_posix(root, shared_path)}.",
                    )
                )
        for volatile_name in OBSIDIAN_VOLATILE_FILES:
            volatile_path = obsidian_root / volatile_name
            if volatile_path.is_file():
                issues.append(
                    make_issue(
                        "tracked_volatile_obsidian_state",
                        "warning",
                        relative_posix(root, volatile_path),
                        "Tracked volatile Obsidian workspace state should not be treated as required shared config.",
                    )
                )
    if wiki_pages and any(page.has_frontmatter for page in obsidian_signal_pages):
        missing_frontmatter = [page.relative_path for page in wiki_pages if not page.has_frontmatter]
        for rel_path in missing_frontmatter[:10]:
            issues.append(
                make_issue(
                    "missing_vault_frontmatter",
                    "suggestion",
                    rel_path,
                    "Wiki page is missing frontmatter even though the repo is using Obsidian-native metadata elsewhere.",
                )
            )
    return issues


def resolve_git_root(root: Path) -> Path | None:
    """Return the git repository root that contains the lint target, if available."""
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    return Path(output).resolve() if output else None


def latest_git_change_epoch(repo_root: Path, paths: list[Path]) -> int | None:
    """Return the latest tracked commit timestamp across the provided paths."""
    relative_paths: list[str] = []
    for path in paths:
        try:
            relative_paths.append(path.resolve().relative_to(repo_root).as_posix())
        except ValueError:
            continue
    if not relative_paths:
        return None
    result = subprocess.run(
        ["git", "-C", str(repo_root), "log", "-1", "--format=%ct", "--", *relative_paths],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    if not output:
        return None
    try:
        return int(output.splitlines()[0])
    except ValueError:
        return None


def count_local_links(page: MarkdownPage, *, prefix: str) -> int:
    """Count local links from a page to a given path prefix."""
    count = 0
    for link in page.links:
        lowered = unquote(link).lower().lstrip("./")
        if lowered.startswith(prefix) or f"/{prefix}" in lowered:
            count += 1
    return count


def lint_index_activity_coverage(
    root: Path,
    pages: dict[str, MarkdownPage],
    inbound_links: dict[str, set[str]],
) -> list[dict[str, Any]]:
    """Apply heuristic checks for indexes, source maps, coverage pages, and activity logs."""
    issues: list[dict[str, Any]] = []
    wiki_pages = [page for page in pages.values() if page.is_wiki and not page.is_index_like]
    raw_sources = [
        path
        for path in iter_repo_files(root)
        if relative_posix(root, path).startswith(("raw/sources/", "raw/captures/", "raw/extracts/"))
        and not path.name.startswith(".")
    ]
    wiki_index = pages.get(STARTER_FILES["wiki_index"])
    if wiki_pages and wiki_index:
        linked_pages = sum(
            1
            for target in inbound_links
            if target.startswith("wiki/") and STARTER_FILES["wiki_index"] in inbound_links[target]
        )
        if linked_pages == 0:
            issues.append(
                make_issue(
                    "weak_wiki_index_coverage",
                    "warning",
                    STARTER_FILES["wiki_index"],
                    "wiki/index.md does not link to any other wiki pages under the current root.",
                )
            )
    coverage_page = pages.get(STARTER_FILES["coverage_index"])
    if wiki_pages and coverage_page:
        expected_links = max(1, math.ceil(len(wiki_pages) / 3))
        wiki_link_count = count_local_links(coverage_page, prefix="../wiki/") + count_local_links(
            coverage_page,
            prefix="wiki/",
        )
        mentioned_paths = sum(1 for page in wiki_pages if page.relative_path in coverage_page.text)
        if (
            wiki_link_count < expected_links
            and not any(token in coverage_page.text.lower() for token in ("todo", "gap", "planned"))
            and mentioned_paths < expected_links
        ):
            issues.append(
                make_issue(
                    "weak_coverage_index",
                    "suggestion",
                    STARTER_FILES["coverage_index"],
                    "Coverage index has weak linkage to existing wiki pages and no obvious gap-planning markers.",
                    {
                        "expected_min_links": expected_links,
                        "detected_links": wiki_link_count,
                        "mentioned_paths": mentioned_paths,
                    },
                )
            )
    source_map_page = pages.get(STARTER_FILES["source_map"])
    if raw_sources and source_map_page:
        raw_link_count = count_local_links(source_map_page, prefix="../raw/") + count_local_links(
            source_map_page,
            prefix="raw/",
        )
        if raw_link_count == 0 and not any(
            path.name.lower() in source_map_page.text.lower() for path in raw_sources[:10]
        ):
            issues.append(
                make_issue(
                    "weak_source_map",
                    "warning",
                    STARTER_FILES["source_map"],
                    "Source map does not appear to reference current raw sources.",
                    {"raw_sources_checked": min(len(raw_sources), 10)},
                )
            )
    activity_log = pages.get(STARTER_FILES["activity_log"])
    if activity_log:
        entry_count = len(ACTIVITY_ENTRY_HEADER_PATTERN.findall(activity_log.text))
        if (wiki_pages or raw_sources) and entry_count == 0:
            issues.append(
                make_issue(
                    "empty_activity_log",
                    "warning",
                    STARTER_FILES["activity_log"],
                    "Activity log exists but has no detectable log entries.",
                )
            )
        repo_root = resolve_git_root(root)
        if repo_root is not None:
            activity_change_epoch = latest_git_change_epoch(repo_root, [activity_log.path])
            latest_content_epoch = latest_git_change_epoch(
                repo_root,
                [page.path for page in wiki_pages] + raw_sources,
            )
            if (
                activity_change_epoch is not None
                and latest_content_epoch is not None
                and latest_content_epoch > activity_change_epoch
            ):
                issues.append(
                    make_issue(
                        "stale_activity_log",
                        "suggestion",
                        STARTER_FILES["activity_log"],
                        "Activity log may be stale relative to newer tracked wiki or raw content.",
                    )
                )
    return issues


def summarize_actions(issues: list[dict[str, Any]]) -> list[str]:
    """Convert lint findings into compact next-step recommendations."""
    rules = {issue["rule"] for issue in issues}
    actions: list[str] = []
    if {"missing_layer", "missing_starter_file"} & rules:
        actions.append(
            "Run kb_bootstrap.py --root <path> to add missing layers and starter files without destructive overwrites."
        )
    if {
        "broken_local_link",
        "broken_local_anchor",
        "broken_obsidian_block_ref",
        "ambiguous_obsidian_link",
        "out_of_root_local_link",
    } & rules:
        actions.append("Fix broken local links and anchors before relying on wiki or index navigation.")
    if "missing_provenance_marker" in rules:
        actions.append("Add Sources/Provenance sections or raw links to substantive wiki pages.")
    if {"orphan_wiki_page", "duplicate_wiki_title", "overlapping_wiki_pages"} & rules:
        actions.append("Review wiki topology: add inbound links, merge duplicates, or clarify page scopes.")
    if "raw_source_missing_summary_stub" in rules:
        actions.append("Create wiki summary stubs or source-map entries for unmapped raw sources.")
    if {"empty_schema_layer", "empty_config_layer"} & rules:
        actions.append(
            "Add lightweight schema/ and config/ files so page shapes and KB-specific settings stay explicit."
        )
    if {
        "missing_obsidian_root",
        "missing_shared_obsidian_surface",
        "tracked_volatile_obsidian_state",
        "missing_vault_frontmatter",
        "duplicate_obsidian_alias",
    } & rules:
        actions.append(
            "Normalize the Obsidian vault surface: keep shared `.obsidian/` config project-safe, add frontmatter where expected, and resolve alias collisions."
        )
    if {
        "weak_wiki_index_coverage",
        "weak_coverage_index",
        "weak_source_map",
        "empty_activity_log",
        "stale_activity_log",
    } & rules:
        actions.append(
            "Refresh wiki/index.md, indexes/coverage.md, indexes/source-map.md, "
            "and activity/log.md in the same batch as content changes."
        )
    if not actions:
        actions.append(
            "Lint checks passed; continue with additive KB maintenance and rerun lint after the next mutating batch."
        )
    return actions


def should_fail(issues: list[dict[str, Any]], fail_on: str) -> bool:
    """Return True when lint findings should trigger a non-zero exit code.

    Examples:
        >>> should_fail([{'severity': 'critical'}], 'critical')
        True
    """
    severities = {issue["severity"] for issue in issues}
    if fail_on == "none":
        return False
    if fail_on == "critical":
        return "critical" in severities
    if fail_on == "warning":
        return "critical" in severities or "warning" in severities
    raise ValueError(f"Unsupported fail-on level: {fail_on}")


def run_lint(root: Path, *, include_unlayered: bool = False) -> dict[str, Any]:
    """Run all lint checks and return a JSON-serializable result."""
    inventory = build_inventory(root)
    pages = collect_markdown_pages(root, include_unlayered=include_unlayered)
    issues = []
    issues.extend(lint_structure(root, inventory))
    issues.extend(lint_provenance(pages))
    link_issues, inbound_links = lint_links(root, pages)
    issues.extend(link_issues)
    issues.extend(lint_orphans(pages, inbound_links))
    issues.extend(lint_duplicates_and_overlap(pages))
    issues.extend(lint_raw_summary_stubs(root, pages))
    issues.extend(lint_schema_config_drift(root, pages))
    issues.extend(lint_obsidian_vault(root, pages))
    issues.extend(lint_index_activity_coverage(root, pages, inbound_links))
    issues.sort(key=lambda issue: (SEVERITY_ORDER.get(issue["severity"], 99), issue["path"], issue["rule"]))
    issues_by_severity: Counter[str] = Counter(issue["severity"] for issue in issues)
    present_layers = [name for name, info in inventory["layers"].items() if info["present"]]
    missing_layers = [name for name, info in inventory["layers"].items() if not info["present"]]
    return {
        "root": str(root),
        "summary": {
            "issue_count": len(issues),
            "issues_by_severity": dict(sorted(issues_by_severity.items())),
            "wiki_pages_checked": sum(1 for page in pages.values() if page.is_wiki),
            "markdown_files_checked": len(pages),
            "scan_mode": "kb_plus_unlayered" if include_unlayered else "kb_only",
            "present_layers": present_layers,
            "missing_layers": missing_layers,
        },
        "issues": issues,
        "suggested_next_actions": summarize_actions(issues),
    }


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for kb_lint.py."""
    parser = argparse.ArgumentParser(
        description="Run non-destructive nerdbot KB lint checks.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--root", default=".", help="KB or repository root to lint")
    parser.add_argument(
        "--fail-on",
        choices=("none", "critical", "warning"),
        default="warning",
        help="Return a non-zero exit code when findings reach this severity",
    )
    parser.add_argument(
        "--include-unlayered",
        action="store_true",
        help="Include markdown outside the default KB layers in link and coverage analysis",
    )
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON instead of pretty-printed JSON")
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint for kb_lint.py.

    Examples:
        python kb_lint.py --root .
    """
    args = parse_args()
    try:
        root = resolve_existing_root(args.root)
        result = run_lint(root, include_unlayered=args.include_unlayered)
    except Exception as exc:  # pragma: no cover - CLI safeguard
        warn(str(exc))
        print(emit_error_payload("kb_lint", args.root))
        return 1
    indent = None if args.compact else 2
    print(json.dumps(result, indent=indent, ensure_ascii=False))
    return 1 if should_fail(result["issues"], args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
