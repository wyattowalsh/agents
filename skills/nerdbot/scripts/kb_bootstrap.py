#!/usr/bin/env python3
"""Safely scaffold the default nerdbot layered KB structure.

By default this command creates only missing directories and starter files. Use
--force to overwrite the known starter files explicitly, except for the
append-only activity log.

Usage examples:
    python3 scripts/kb_bootstrap.py --root .
    python3 scripts/kb_bootstrap.py --root ./new-kb --dry-run
    python3 scripts/kb_bootstrap.py --root ./existing-kb --force
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Callable
from datetime import date
from functools import lru_cache
from pathlib import Path

from kb_inventory import (
    DEFAULT_DIRECTORIES,
    STARTER_FILES,
    emit_error_payload,
    normalize_requested_root,
    warn,
)

TemplateFactory = Callable[[Path], str]
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
KB_BOOTSTRAP_TEMPLATE_PATH = ASSETS_DIR / "kb-bootstrap-template.md"
ACTIVITY_LOG_TEMPLATE_PATH = ASSETS_DIR / "activity-log-template.md"
PATH_MARKER_PREFIX = "Path: `"
ACTIVITY_LOG_INITIAL_MARKER = "## Initial entry example"
PACKET_STARTER_FILES = tuple(STARTER_FILES.values())


def knowledge_base_title(root: Path) -> str:
    """Derive a human-friendly KB title from the target root path.

    Examples:
        >>> knowledge_base_title(Path('agent-kb'))
        'Agent Kb'
    """
    return root.name.replace("-", " ").replace("_", " ").strip().title() or "Knowledge Base"


def knowledge_base_slug(root: Path) -> str:
    """Derive a stable starter-page slug from the target root path."""
    return knowledge_base_title(root).lower().replace(" ", "-")


def read_asset_text(asset_path: Path) -> str:
    """Read a bundled starter-template asset."""
    try:
        return asset_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Could not read starter template asset: {asset_path}") from exc


def finalize_template_section(lines: list[str]) -> str:
    """Normalize a parsed template section for writing to disk."""
    return "\n".join(lines).strip() + "\n"


def parse_bootstrap_packet_sections(packet_text: str) -> dict[str, str]:
    """Extract file templates from the bootstrap packet asset."""
    sections: dict[str, str] = {}
    current_path: str | None = None
    current_lines: list[str] = []
    lines = packet_text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith(PATH_MARKER_PREFIX) and line.endswith("`"):
            if current_path is not None:
                sections[current_path] = finalize_template_section(current_lines)
            current_path = line.removeprefix(PATH_MARKER_PREFIX).removesuffix("`")
            current_lines = []
            index += 1
            while index < len(lines) and not lines[index]:
                index += 1
            continue
        if current_path is not None:
            if line == "---":
                next_index = index + 1
                while next_index < len(lines) and not lines[next_index]:
                    next_index += 1
                if next_index >= len(lines) or lines[next_index].startswith(PATH_MARKER_PREFIX):
                    sections[current_path] = finalize_template_section(current_lines)
                    current_path = None
                    index = next_index
                    continue
            current_lines.append(line)
        index += 1
    if current_path is not None:
        sections[current_path] = finalize_template_section(current_lines)
    return sections


@lru_cache(maxsize=1)
def load_bootstrap_packet_sections() -> dict[str, str]:
    """Load the starter-file packet sections from the bundled asset."""
    sections = parse_bootstrap_packet_sections(read_asset_text(KB_BOOTSTRAP_TEMPLATE_PATH))
    missing_sections = [rel_path for rel_path in PACKET_STARTER_FILES if rel_path not in sections]
    if missing_sections:
        missing_list = ", ".join(missing_sections)
        raise RuntimeError(f"Starter template sections missing from {KB_BOOTSTRAP_TEMPLATE_PATH}: {missing_list}")
    return sections


def load_bootstrap_packet_section(rel_path: str) -> str:
    """Return the bundled template for a specific starter file."""
    try:
        return load_bootstrap_packet_sections()[rel_path]
    except KeyError as exc:
        raise RuntimeError(f"Starter template for {rel_path} not found in {KB_BOOTSTRAP_TEMPLATE_PATH}") from exc


def strip_leading_comment_block(template: str, asset_path: Path) -> str:
    """Drop a leading HTML comment from an asset before writing the starter file."""
    lines = template.splitlines()
    index = 0
    while index < len(lines) and not lines[index]:
        index += 1
    if index < len(lines) and lines[index].lstrip().startswith("<!--"):
        while index < len(lines) and "-->" not in lines[index]:
            index += 1
        if index >= len(lines):
            raise RuntimeError(f"Unterminated leading comment in {asset_path}")
        index += 1
    while index < len(lines) and not lines[index]:
        index += 1
    return "\n".join(lines[index:]).rstrip() + "\n"


@lru_cache(maxsize=1)
def load_activity_log_sections() -> tuple[str, str]:
    """Load the activity-log prelude and initial example from the bundled asset."""
    template = strip_leading_comment_block(
        read_asset_text(ACTIVITY_LOG_TEMPLATE_PATH),
        ACTIVITY_LOG_TEMPLATE_PATH,
    )
    before, separator, after = template.partition(ACTIVITY_LOG_INITIAL_MARKER)
    if not separator:
        raise RuntimeError(f"Could not find '{ACTIVITY_LOG_INITIAL_MARKER}' in {ACTIVITY_LOG_TEMPLATE_PATH}")
    prelude = f"{before.rstrip()}\n\n{separator}\n\n"
    initial_example = after.lstrip()
    if not initial_example:
        raise RuntimeError(f"Initial activity-log example is empty in {ACTIVITY_LOG_TEMPLATE_PATH}")
    return prelude, initial_example.rstrip() + "\n"


def starter_placeholder_values(root: Path) -> dict[str, str]:
    """Return safe default substitutions for bundled starter templates."""
    title = knowledge_base_title(root)
    slug = knowledge_base_slug(root)
    today = date.today().isoformat()
    return {
        "[KB Title]": title,
        "[topic]": title,
        "[kb-root]": root.name or ".",
        "[overview-page]": slug,
        "[source-summary-page]": f"{slug}-source-summary",
        "[page]": slug,
        "[authoritative / pending review]": "pending review",
        "[notes]": "List user-authored files or pages that must remain authoritative.",
        "[import / capture / extract]": "import",
        "[no / yes]": "no",
        "[missing / partial / linked]": "missing",
        "[added / not yet needed]": "unchanged",
        "[none yet / listed in `wiki/index.md`]": "none yet",
        "[YYYY-MM-DD]": today,
        "[YYYY-MM-DD HH:MM]": f"{today} 00:00",
    }


def render_starter_template(template: str, root: Path) -> str:
    """Render a bundled starter template with safe repo-local defaults."""
    rendered = template
    for placeholder, value in starter_placeholder_values(root).items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def render_wiki_index(root: Path) -> str:
    """Render the default wiki index starter file from the bundled asset."""
    return render_starter_template(
        load_bootstrap_packet_section(STARTER_FILES["wiki_index"]),
        root,
    )


def render_coverage_index(root: Path) -> str:
    """Render the default coverage starter file from the bundled asset."""
    return render_starter_template(
        load_bootstrap_packet_section(STARTER_FILES["coverage_index"]),
        root,
    )


def render_source_map(root: Path) -> str:
    """Render the default source-map starter file from the bundled asset."""
    return render_starter_template(
        load_bootstrap_packet_section(STARTER_FILES["source_map"]),
        root,
    )


def render_activity_log(root: Path) -> str:
    """Render the default activity log starter file from the bundled asset."""
    prelude, initial_example = load_activity_log_sections()
    return prelude + render_starter_template(initial_example, root)


def render_packet_starter(root: Path, rel_path: str) -> str:
    """Render a packet-backed starter file with repo-local placeholder defaults."""
    return render_starter_template(load_bootstrap_packet_section(rel_path), root)


STARTER_TEMPLATES: dict[str, TemplateFactory] = {
    STARTER_FILES["wiki_index"]: render_wiki_index,
    STARTER_FILES["coverage_index"]: render_coverage_index,
    STARTER_FILES["source_map"]: render_source_map,
    STARTER_FILES["activity_log"]: render_activity_log,
    STARTER_FILES["vault_config"]: lambda root: render_packet_starter(root, STARTER_FILES["vault_config"]),
    STARTER_FILES["vault_wiki_template"]: lambda root: render_packet_starter(
        root, STARTER_FILES["vault_wiki_template"]
    ),
    STARTER_FILES["vault_source_template"]: lambda root: render_packet_starter(
        root, STARTER_FILES["vault_source_template"]
    ),
}
if set(STARTER_TEMPLATES) != set(STARTER_FILES.values()):
    raise RuntimeError("STARTER_TEMPLATES must define a renderer for every starter file")
# The activity log is append-only by contract, so bootstrap never overwrites it.
APPEND_ONLY_STARTER_FILES = {STARTER_FILES["activity_log"]}


def normalize_root(root_arg: str) -> Path:
    """Resolve a target root path without requiring it to exist first.

    Examples:
        >>> normalize_root('.')  # doctest: +ELLIPSIS
        PosixPath('...')
    """
    return normalize_requested_root(root_arg)


def ensure_safe_target(root: Path, target: Path) -> None:
    """Reject writes that would follow symlinks or escape the requested root.

    Examples:
        >>> ensure_safe_target(Path('/repo'), Path('/repo/wiki/index.md'))
    """
    try:
        relative = target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Target escapes requested root: {target}") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise RuntimeError(f"Refusing to follow symlinked path component: {current}")


def write_text_safely(path: Path, content: str, *, overwrite: bool) -> None:
    """Write text without following a symlink at the final path component.

    Examples:
        >>> # write_text_safely(Path('/repo/file.txt'), 'x', overwrite=False)  # doctest: +SKIP
        ... # doctest: +SKIP
    """
    flags = os.O_WRONLY | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    flags |= os.O_TRUNC if overwrite else os.O_EXCL
    fd = os.open(path, flags, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(content)


def preflight_validate_targets(root: Path, *, force: bool) -> None:
    """Validate all target paths before any filesystem mutation occurs.

    Examples:
        >>> preflight_validate_targets(Path('example-kb').resolve(), force=False)  # doctest: +SKIP
    """
    for rel_dir in DEFAULT_DIRECTORIES:
        target_dir = root / rel_dir
        ensure_safe_target(root, target_dir)
        if target_dir.exists():
            if target_dir.is_symlink():
                raise RuntimeError(f"Refusing to reuse symlinked directory: {target_dir}")
            if not target_dir.is_dir():
                raise NotADirectoryError(f"Expected directory but found file: {target_dir}")
    for rel_path in STARTER_TEMPLATES:
        target_file = root / rel_path
        ensure_safe_target(root, target_file)
        if target_file.is_symlink():
            raise RuntimeError(f"Refusing to write through symlinked file: {target_file}")
        if target_file.exists() and target_file.is_dir():
            raise IsADirectoryError(f"Expected file but found directory: {target_file}")
        if target_file.exists() and not force:
            continue


def scaffold(root: Path, *, force: bool, dry_run: bool) -> dict[str, object]:
    """Create the default KB directories and starter files safely.

    Examples:
        >>> result = scaffold(Path('example-kb').resolve(), force=False, dry_run=True)
        >>> result['dry_run']
        True
    """
    if root.exists() and not root.is_dir():
        raise NotADirectoryError(f"Root is not a directory: {root}")
    if not root.exists() and not root.parent.exists():
        raise FileNotFoundError(f"Parent directory does not exist: {root.parent}")
    preflight_validate_targets(root, force=force)
    created_directories: list[str] = []
    skipped_directories: list[str] = []
    created_files: list[str] = []
    overwritten_files: list[str] = []
    skipped_existing: list[str] = []
    root_created = False
    if not root.exists():
        root_created = True
        if not dry_run:
            root.mkdir(parents=True, exist_ok=True)
    for rel_dir in DEFAULT_DIRECTORIES:
        target_dir = root / rel_dir
        ensure_safe_target(root, target_dir)
        if target_dir.exists():
            if target_dir.is_symlink():
                raise RuntimeError(f"Refusing to reuse symlinked directory: {target_dir}")
            if not target_dir.is_dir():
                raise NotADirectoryError(f"Expected directory but found file: {target_dir}")
            skipped_directories.append(rel_dir)
            continue
        created_directories.append(rel_dir)
        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
    for rel_path, factory in STARTER_TEMPLATES.items():
        target_file = root / rel_path
        ensure_safe_target(root, target_file)
        content = factory(root)
        if target_file.is_symlink():
            raise RuntimeError(f"Refusing to write through symlinked file: {target_file}")
        if target_file.exists() and target_file.is_dir():
            raise IsADirectoryError(f"Expected file but found directory: {target_file}")
        if target_file.exists() and rel_path in APPEND_ONLY_STARTER_FILES:
            skipped_existing.append(rel_path)
            warn(f"Preserving append-only starter file: {target_file}")
            continue
        if target_file.exists() and not force:
            skipped_existing.append(rel_path)
            warn(f"Skipping existing file: {target_file}")
            continue
        if target_file.exists() and force:
            overwritten_files.append(rel_path)
            warn(f"Overwriting starter file due to --force: {target_file}")
        else:
            created_files.append(rel_path)
        if not dry_run:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            ensure_safe_target(root, target_file)
            write_text_safely(target_file, content, overwrite=force)
    next_actions = [
        "Add source captures under raw/sources/, raw/captures/, or raw/extracts/, and place local supporting assets under raw/assets/.",
        "Create synthesized pages under wiki/topics/ with explicit provenance back to raw evidence and Obsidian-native frontmatter.",
        "Refresh indexes/coverage.md, indexes/source-map.md, activity/log.md, and config/obsidian-vault.md in the same batch as content changes.",
    ]
    if skipped_existing and not force:
        next_actions.append("Re-run with --force only if you explicitly want to overwrite the known starter files.")
    return {
        "root": str(root),
        "root_created": root_created,
        "dry_run": dry_run,
        "force": force,
        "created_directories": created_directories,
        "skipped_directories": skipped_directories,
        "created_files": created_files,
        "overwritten_files": overwritten_files,
        "skipped_existing": skipped_existing,
        "suggested_next_actions": next_actions,
    }


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for kb_bootstrap.py."""
    parser = argparse.ArgumentParser(
        description="Safely scaffold the default nerdbot layered KB structure.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--root", default=".", help="KB root to create or update")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite known starter files except the append-only activity log",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON instead of pretty-printed JSON")
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint for kb_bootstrap.py.

    Examples:
        python kb_bootstrap.py --root . --dry-run
    """
    args = parse_args()
    try:
        root = normalize_root(args.root)
        result = scaffold(root, force=args.force, dry_run=args.dry_run)
    except Exception as exc:  # pragma: no cover - CLI safeguard
        warn(str(exc))
        print(emit_error_payload("kb_bootstrap", args.root))
        return 1
    indent = None if args.compact else 2
    print(json.dumps(result, indent=indent, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
