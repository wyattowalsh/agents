#!/usr/bin/env python3
"""CRUD operations for discovery session journals in ~/.claude/discover-skills/.

Manages discovery journal files with YAML frontmatter and markdown body.
Tracks skill audits, gap analysis, candidate evaluation, and installation.

Usage:
  python journal-store.py init --focus "AI tooling"
  python journal-store.py save --target 1 --status "In Progress" --wave 2 --candidates '[...]'
  python journal-store.py load 1
  python journal-store.py list
  python journal-store.py list --filter active
  python journal-store.py resume
  python journal-store.py resume 1
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

JOURNAL_DIR = Path.home() / ".claude" / "discover-skills"


# --- YAML frontmatter parsing (stdlib only, no pyyaml) ---


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown text. Returns (metadata, body)."""
    if not text.startswith("---"):
        return {}, text

    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    yaml_block = text[4:end].strip()
    body = text[end + 4 :].lstrip("\n")
    meta = _parse_yaml_simple(yaml_block)
    return meta, body


def _parse_yaml_simple(text: str) -> dict[str, Any]:
    """Simple YAML parser for frontmatter (handles scalars, lists, numbers)."""
    result: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[str] | None = None

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # List item under current key
        if (
            stripped.startswith("- ")
            and current_key is not None
            and current_list is not None
        ):
            current_list.append(_parse_yaml_value(stripped[2:].strip()))
            result[current_key] = current_list
            continue

        # Key-value pair
        m = re.match(r"^([a-z_][a-z0-9_]*)\s*:\s*(.*)", stripped)
        if m:
            key, val_str = m.group(1), m.group(2).strip()
            current_key = key
            if not val_str:
                # Could be a list or empty
                current_list = []
                result[key] = current_list
            elif val_str.startswith("[") and val_str.endswith("]"):
                # Inline list
                inner = val_str[1:-1].strip()
                if not inner:
                    result[key] = []
                else:
                    items = [
                        _parse_yaml_value(s.strip()) for s in _split_yaml_list(inner)
                    ]
                    result[key] = items
                current_list = None
            else:
                result[key] = _parse_yaml_value(val_str)
                current_list = None
        else:
            current_list = None

    return result


def _split_yaml_list(text: str) -> list[str]:
    """Split a YAML inline list, respecting quotes."""
    items: list[str] = []
    current: list[str] = []
    in_quote: str | None = None
    for ch in text:
        if ch in ('"', "'") and in_quote is None:
            in_quote = ch
            current.append(ch)
        elif ch == in_quote:
            in_quote = None
            current.append(ch)
        elif ch == "," and in_quote is None:
            items.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        items.append("".join(current).strip())
    return items


def _parse_yaml_value(val: str) -> Any:
    """Parse a YAML scalar value."""
    if not val:
        return ""
    # Remove quotes
    if (val.startswith('"') and val.endswith('"')) or (
        val.startswith("'") and val.endswith("'")
    ):
        return val[1:-1]
    # Booleans
    if val.lower() in ("true", "yes"):
        return True
    if val.lower() in ("false", "no"):
        return False
    # None
    if val.lower() in ("null", "~"):
        return None
    # Numbers
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        pass
    return val


def serialize_frontmatter(meta: dict[str, Any]) -> str:
    """Serialize a dict to YAML frontmatter string."""
    lines = ["---"]
    for key, val in meta.items():
        if isinstance(val, list):
            if not val:
                lines.append(f"{key}: []")
            elif all(isinstance(v, str) and len(v) < 60 for v in val):
                items = ", ".join(_yaml_scalar(v) for v in val)
                lines.append(f"{key}: [{items}]")
            else:
                lines.append(f"{key}:")
                for item in val:
                    lines.append(f"  - {_yaml_scalar(item)}")
        elif isinstance(val, bool):
            lines.append(f"{key}: {'true' if val else 'false'}")
        elif val is None:
            lines.append(f"{key}: null")
        else:
            lines.append(f"{key}: {_yaml_scalar(val)}")
    lines.append("---")
    return "\n".join(lines)


def _yaml_scalar(val: Any) -> str:
    """Format a scalar value for YAML output."""
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    if val is None:
        return "null"
    s = str(val)
    _yaml_special = set(':#[]{},"&*?|-<>=!%@`')
    if any(ch in _yaml_special for ch in s) or not s:
        escaped = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return f'"{s}"'


# --- STATE block parsing ---

_STATE_PATTERN = re.compile(r"<!--\s*STATE\s*\n(.*?)\n\s*-->", re.DOTALL)


def parse_state_blocks(body: str) -> list[dict[str, Any]]:
    """Extract all STATE blocks from journal body."""
    blocks: list[dict[str, Any]] = []
    for m in _STATE_PATTERN.finditer(body):
        blocks.append(_parse_yaml_simple(m.group(1)))
    return blocks


# --- Slug generation ---

_SLUG_STOP = {
    "what",
    "how",
    "why",
    "when",
    "where",
    "which",
    "who",
    "is",
    "are",
    "does",
    "do",
    "the",
    "a",
    "an",
    "for",
    "to",
    "of",
    "in",
    "on",
    "and",
    "or",
    "but",
    "with",
    "from",
    "by",
    "at",
    "it",
    "this",
    "that",
    "be",
    "was",
    "were",
    "been",
    "has",
    "have",
    "had",
}


def make_slug(focus: str) -> str:
    """Generate a kebab-case slug from the focus string."""
    words = re.findall(r"[a-zA-Z0-9]+", focus.lower())
    meaningful = [w for w in words if w not in _SLUG_STOP and len(w) > 1]
    slug_words = meaningful[:5] if len(meaningful) >= 3 else words[:5]
    return "-".join(slug_words) if slug_words else "full-scan"


def make_filename(focus: str | None, base_dir: Path) -> str:
    """Generate journal filename: {YYYY-MM-DD}-discovery-{slug}.md"""
    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    slug = make_slug(focus) if focus else "full-scan"
    base = f"{date_str}-discovery-{slug}.md"

    # Handle collisions
    path = base_dir / base
    if not path.exists():
        return base

    version = 2
    while True:
        versioned = f"{date_str}-discovery-{slug}-v{version}.md"
        if not (base_dir / versioned).exists():
            return versioned
        version += 1


# --- Journal listing ---


def list_journals(
    base_dir: Path, filter_val: str | None = None
) -> list[dict[str, Any]]:
    """List journals with metadata, reverse chronological."""
    if not base_dir.exists():
        return []

    journals: list[dict[str, Any]] = []
    for f in sorted(base_dir.glob("*.md"), reverse=True):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        meta, _body = parse_frontmatter(text)
        if not meta:
            continue

        entry = {
            "path": str(f),
            "filename": f.name,
            **meta,
        }
        journals.append(entry)

    # Apply filter
    if filter_val:
        fl = filter_val.lower()
        if fl == "active":
            journals = [
                j
                for j in journals
                if str(j.get("status", "")).lower() in ("in progress", "in_progress")
            ]
        else:
            journals = [
                j
                for j in journals
                if fl in str(j.get("focus", "")).lower()
                or fl in j.get("filename", "").lower()
                or fl in str(j.get("session_type", "")).lower()
            ]

    return journals


# --- Helpers ---


def _resolve_path(target: str) -> Path | None:
    """Resolve a journal target: path, number, or keyword."""
    result = None

    # Direct path -- force relative to JOURNAL_DIR unless already under it
    p = Path(target)
    if not p.is_absolute():
        p = JOURNAL_DIR / p
    if p.resolve().is_file():
        result = p.resolve()

    # Try as number
    if result is None:
        try:
            num = int(target)
            journals = list_journals(JOURNAL_DIR)
            if 1 <= num <= len(journals):
                result = Path(journals[num - 1]["path"]).resolve()
        except ValueError:
            pass

    # Try as keyword search
    if result is None:
        journals = list_journals(JOURNAL_DIR)
        target_lower = target.lower()
        for j in journals:
            if target_lower in str(j.get("focus", "")).lower() or target_lower in Path(
                j["path"]
            ).stem:
                result = Path(j["path"]).resolve()
                break

    # Containment check -- reject paths outside JOURNAL_DIR
    if result is not None:
        jail = JOURNAL_DIR.resolve()
        if not str(result).startswith(str(jail) + "/") and result != jail:
            print(
                f"Error: path outside discover-skills directory: {target}",
                file=sys.stderr,
            )
            sys.exit(1)
        if not result.is_file():
            return None

    return result


# --- Subcommands ---


def cmd_init(args: argparse.Namespace) -> None:
    """Create a new discovery journal."""
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")
    focus = args.focus or None

    meta: dict[str, Any] = {
        "session_type": "discovery",
        "focus": focus if focus else "",
        "status": "In Progress",
        "created": now,
        "updated": now,
        "total_skills_audited": 0,
        "gap_count": 0,
        "candidates_found": 0,
        "proposals_made": 0,
        "installed": [],
        "rejected": [],
    }

    # Build initial body
    title = f"Discovery: {focus}" if focus else "Discovery: Full Scan"
    body_lines = [f"# {title}", ""]

    filename = make_filename(focus, JOURNAL_DIR)
    path = JOURNAL_DIR / filename
    content = serialize_frontmatter(meta) + "\n\n" + "\n".join(body_lines) + "\n"
    try:
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        print(f"Error: could not write journal: {exc}", file=sys.stderr)
        sys.exit(1)

    result = {"action": "created", "path": str(path), "metadata": meta}
    json.dump(result, sys.stdout, indent=2)
    print()


def cmd_save(args: argparse.Namespace) -> None:
    """Update an existing discovery journal."""
    if not args.target:
        print("Error: --target is required.", file=sys.stderr)
        sys.exit(1)

    path = _resolve_path(args.target)
    if path is None:
        print(f"Error: journal not found: {args.target}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")
    meta["updated"] = now

    if args.status:
        meta["status"] = args.status
    if args.wave is not None:
        meta["last_wave"] = args.wave

    # Parse and merge candidates
    if args.candidates:
        try:
            candidates = json.loads(args.candidates)
            if isinstance(candidates, list):
                meta["candidates_found"] = len(candidates)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON in --candidates: {exc}", file=sys.stderr)
            sys.exit(1)

    # Parse and merge proposals
    if args.proposals:
        try:
            proposals = json.loads(args.proposals)
            if isinstance(proposals, list):
                meta["proposals_made"] = len(proposals)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON in --proposals: {exc}", file=sys.stderr)
            sys.exit(1)

    # Parse and merge installed
    if args.installed:
        try:
            installed = json.loads(args.installed)
            if isinstance(installed, list):
                meta["installed"] = installed
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON in --installed: {exc}", file=sys.stderr)
            sys.exit(1)

    # Build STATE block for this save
    state_lines = ["<!-- STATE"]
    state_lines.append(f"wave: {args.wave if args.wave is not None else 0}")
    state_lines.append(f"timestamp: {now}")
    if args.candidates:
        state_lines.append(f"candidates_found: {meta.get('candidates_found', 0)}")
    if args.proposals:
        state_lines.append(f"proposals_made: {meta.get('proposals_made', 0)}")
    if args.installed:
        installed_list = meta.get("installed", [])
        if installed_list:
            items = ", ".join(f'"{i}"' for i in installed_list)
            state_lines.append(f"installed: [{items}]")
        else:
            state_lines.append("installed: []")
    state_lines.append("-->")
    state_block = "\n".join(state_lines)

    # Append state block to body
    body = body.rstrip("\n") + "\n\n" + state_block + "\n"

    content = serialize_frontmatter(meta) + "\n\n" + body
    try:
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        print(f"Error: could not write journal: {exc}", file=sys.stderr)
        sys.exit(1)

    result = {"action": "updated", "path": str(path), "metadata": meta}
    json.dump(result, sys.stdout, indent=2)
    print()


def cmd_load(args: argparse.Namespace) -> None:
    """Load a journal and output as JSON."""
    path = _resolve_path(args.target)
    if path is None:
        print(f"Error: journal not found: {args.target}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    state_blocks = parse_state_blocks(body)

    result = {
        "path": str(path),
        "metadata": meta,
        "state_blocks": state_blocks,
        "body": body,
    }
    json.dump(result, sys.stdout, indent=2)
    print()


def cmd_list(args: argparse.Namespace) -> None:
    """List journals with metadata as JSON array."""
    journals = list_journals(JOURNAL_DIR, args.filter)

    # Add index numbers for easy reference
    for i, j in enumerate(journals, 1):
        j["number"] = i

    json.dump(journals, sys.stdout, indent=2)
    print()


def cmd_resume(args: argparse.Namespace) -> None:
    """Find the most recent in-progress journal, or resolve a specific target."""
    if args.target:
        path = _resolve_path(args.target)
        if path is None:
            print(f"Error: journal not found: {args.target}", file=sys.stderr)
            sys.exit(1)
    else:
        # Find most recent in-progress journal
        journals = list_journals(JOURNAL_DIR, "active")
        if not journals:
            json.dump(
                {"error": "no_active_journals", "message": "No in-progress journals found."},
                sys.stdout,
                indent=2,
            )
            print()
            return
        path = Path(journals[0]["path"]).resolve()

    text = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    state_blocks = parse_state_blocks(body)

    result = {
        "path": str(path),
        "metadata": meta,
        "state_blocks": state_blocks,
        "body": body,
    }
    json.dump(result, sys.stdout, indent=2)
    print()


# --- Main ---


def main() -> None:
    ap = argparse.ArgumentParser(
        description="CRUD operations for discovery journals in ~/.claude/discover-skills/.",
    )
    sub = ap.add_subparsers(dest="command", required=True)

    # init
    sp_init = sub.add_parser("init", help="Create a new discovery journal.")
    sp_init.add_argument(
        "--focus", default=None, help="Optional domain focus for this discovery session."
    )

    # save
    sp_save = sub.add_parser("save", help="Update an existing discovery journal.")
    sp_save.add_argument(
        "--target", required=True, help="Path or number of existing journal to update."
    )
    sp_save.add_argument("--status", default=None, help="Journal status.")
    sp_save.add_argument(
        "--wave", type=int, default=None, help="Last completed wave number."
    )
    sp_save.add_argument(
        "--candidates", default=None, help="JSON string of candidates array."
    )
    sp_save.add_argument(
        "--proposals", default=None, help="JSON string of proposals array."
    )
    sp_save.add_argument(
        "--installed", default=None, help="JSON string of installed skills array."
    )

    # load
    sp_load = sub.add_parser("load", help="Load a journal and output as JSON.")
    sp_load.add_argument("target", help="Journal path, number, or keyword.")

    # list
    sp_list = sub.add_parser("list", help="List journals with metadata.")
    sp_list.add_argument(
        "--filter", default=None, help="Filter: 'active', keyword, or focus domain."
    )

    # resume
    sp_resume = sub.add_parser(
        "resume", help="Find the most recent in-progress journal."
    )
    sp_resume.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Optional: number or keyword to resume a specific journal.",
    )

    args = ap.parse_args()

    dispatch: dict[str, Any] = {
        "init": cmd_init,
        "save": cmd_save,
        "load": cmd_load,
        "list": cmd_list,
        "resume": cmd_resume,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
