#!/usr/bin/env python3
"""CRUD operations for research journals stored in ~/.claude/research/.

Manages research journal files with YAML frontmatter and markdown body.
Supports save, load, list, diff, archive, and delete operations.

Usage:
  python journal-store.py save --query "What is X?" --tier standard --mode investigate --findings '[...]'
  python journal-store.py load 1
  python journal-store.py load ~/.claude/research/2026-02-27-tech-llm-agents.md
  python journal-store.py list
  python journal-store.py list --filter active
  python journal-store.py list --filter technology
  python journal-store.py diff journal1.md journal2.md
  python journal-store.py archive --days 90
  python journal-store.py delete 1 --force
"""
import argparse
import json
import re
import shutil
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

JOURNAL_DIR = Path.home() / ".claude" / "research"
ARCHIVE_DIR = JOURNAL_DIR / "archive"

# --- YAML frontmatter parsing (stdlib only, no pyyaml) ---

def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown text. Returns (metadata, body)."""
    if not text.startswith("---"):
        return {}, text

    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    yaml_block = text[4:end].strip()
    body = text[end + 4:].lstrip("\n")
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
        if stripped.startswith("- ") and current_key is not None and current_list is not None:
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
                    items = [_parse_yaml_value(s.strip()) for s in _split_yaml_list(inner)]
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
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
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

_SLUG_STOP = {"what", "how", "why", "when", "where", "which", "who", "is", "are",
              "does", "do", "the", "a", "an", "for", "to", "of", "in", "on",
              "and", "or", "but", "with", "from", "by", "at", "it", "this",
              "that", "be", "was", "were", "been", "has", "have", "had"}

_MODE_TO_DOMAIN: dict[str, str] = {
    "factcheck": "factcheck",
    "compare": "compare",
    "survey": "survey",
    "track": "track",
}


def make_slug(query: str) -> str:
    """Generate a 3-5 word kebab-case slug from the query."""
    words = re.findall(r"[a-zA-Z0-9]+", query.lower())
    meaningful = [w for w in words if w not in _SLUG_STOP and len(w) > 1]
    slug_words = meaningful[:5] if len(meaningful) >= 3 else words[:5]
    return "-".join(slug_words) if slug_words else "research"


def detect_domain_tag(query: str, mode: str) -> str:
    """Detect the domain tag for the journal filename."""
    if mode in _MODE_TO_DOMAIN:
        return _MODE_TO_DOMAIN[mode]

    ql = query.lower()
    domain_keywords = {
        "tech": ["api", "framework", "library", "software", "code", "programming",
                 "llm", "ai", "machine learning", "database", "cloud"],
        "academic": ["paper", "study", "evidence", "research", "journal", "peer-reviewed"],
        "market": ["market", "competitor", "revenue", "pricing", "business"],
        "policy": ["law", "regulation", "policy", "legislation", "compliance"],
    }
    for domain, keywords in domain_keywords.items():
        for kw in keywords:
            if kw in ql:
                return domain
    return "general"


def make_filename(query: str, mode: str, base_dir: Path) -> str:
    """Generate journal filename: {YYYY-MM-DD}-{domain}-{slug}.md"""
    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    domain = detect_domain_tag(query, mode)
    slug = make_slug(query)
    base = f"{date_str}-{domain}-{slug}.md"

    # Handle collisions
    path = base_dir / base
    if not path.exists():
        return base

    version = 2
    while True:
        versioned = f"{date_str}-{domain}-{slug}-v{version}.md"
        if not (base_dir / versioned).exists():
            return versioned
        version += 1


# --- Journal listing ---

def list_journals(base_dir: Path, filter_val: str | None = None) -> list[dict[str, Any]]:
    """List journals with metadata, reverse chronological."""
    if not base_dir.exists():
        return []

    journals: list[dict[str, Any]] = []
    for f in sorted(base_dir.glob("*.md"), reverse=True):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        meta, body = parse_frontmatter(text)
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
            journals = [j for j in journals if str(j.get("status", "")).lower() in ("in progress", "in_progress")]
        else:
            journals = [
                j for j in journals
                if fl in str(j.get("domain_tags", [])).lower()
                or fl in str(j.get("tier", "")).lower()
                or fl in str(j.get("mode", "")).lower()
                or fl in j.get("filename", "").lower()
            ]

    return journals


# --- Subcommands ---

def cmd_save(args: argparse.Namespace) -> None:
    """Create or update a research journal."""
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")
    findings_data: list[dict] = []
    if args.findings:
        try:
            findings_data = json.loads(args.findings)
            if isinstance(findings_data, dict):
                findings_data = [findings_data]
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON in --findings: {exc}", file=sys.stderr)
            sys.exit(1)

    # Check if updating existing
    if args.update:
        path = _resolve_path(args.update)
        if path is None:
            print(f"Error: journal not found: {args.update}", file=sys.stderr)
            sys.exit(1)
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        meta["updated"] = now
        if args.status:
            meta["status"] = args.status
        meta["findings_count"] = len(findings_data)
        if findings_data:
            confidences = [
                f.get("confidence", 0) for f in findings_data
                if isinstance(f.get("confidence"), (int, float))
            ]
            if confidences:
                meta["confidence_mean"] = round(sum(confidences) / len(confidences), 2)
            else:
                meta["confidence_mean"] = 0
        content = serialize_frontmatter(meta) + "\n\n" + body
        try:
            path.write_text(content, encoding="utf-8")
        except OSError as exc:
            print(f"Error: could not write journal: {exc}", file=sys.stderr)
            sys.exit(1)
        result = {"action": "updated", "path": str(path), "metadata": meta}
        json.dump(result, sys.stdout, indent=2)
        print()
        return

    if not args.update and not args.query:
        print("Error: --query is required when creating a new journal.", file=sys.stderr)
        sys.exit(1)

    # New journal
    mode = args.mode or "investigate"
    query = args.query or ""
    tier = args.tier or "standard"
    status = args.status or "In Progress"
    domain = detect_domain_tag(query, mode)

    confidences = [f.get("confidence", 0) for f in findings_data if isinstance(f.get("confidence"), (int, float))]
    confidence_mean = round(sum(confidences) / len(confidences), 2) if confidences else 0

    meta: dict[str, Any] = {
        "query": query,
        "mode": mode,
        "tier": tier,
        "status": status,
        "created": now,
        "updated": now,
        "sub_questions": [],
        "domain_tags": [domain],
        "sources_consulted": 0,
        "findings_count": len(findings_data),
        "confidence_mean": confidence_mean,
        "tools_used": [],
    }

    # Build body
    body_lines = [f"# Research: {query}", ""]
    if findings_data:
        body_lines.append("## Findings")
        body_lines.append("")
        for f in findings_data:
            body_lines.append(f"- **{f.get('claim', 'N/A')}** (confidence: {f.get('confidence', 'N/A')})")
        body_lines.append("")

    filename = make_filename(query, mode, JOURNAL_DIR)
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


def cmd_diff(args: argparse.Namespace) -> None:
    """Compare two journals and output added/removed/changed findings."""
    path1 = _resolve_path(args.path1)
    path2 = _resolve_path(args.path2)
    if path1 is None:
        print(f"Error: journal not found: {args.path1}", file=sys.stderr)
        sys.exit(1)
    if path2 is None:
        print(f"Error: journal not found: {args.path2}", file=sys.stderr)
        sys.exit(1)

    text1 = path1.read_text(encoding="utf-8")
    text2 = path2.read_text(encoding="utf-8")
    meta1, _ = parse_frontmatter(text1)
    meta2, _ = parse_frontmatter(text2)

    result = {
        "journal_1": {"path": str(path1), "metadata": meta1},
        "journal_2": {"path": str(path2), "metadata": meta2},
        "changes": {
            "findings_count_delta": (meta2.get("findings_count", 0) or 0) - (meta1.get("findings_count", 0) or 0),
            "confidence_mean_delta": round(
                (meta2.get("confidence_mean", 0) or 0) - (meta1.get("confidence_mean", 0) or 0), 2
            ),
            "sources_consulted_delta": (
                (meta2.get("sources_consulted", 0) or 0)
                - (meta1.get("sources_consulted", 0) or 0)
            ),
            "status_changed": meta1.get("status") != meta2.get("status"),
            "status_from": meta1.get("status"),
            "status_to": meta2.get("status"),
        },
    }
    json.dump(result, sys.stdout, indent=2)
    print()


def cmd_archive(args: argparse.Namespace) -> None:
    """Move journals older than N days to archive/ subdirectory."""
    if not JOURNAL_DIR.exists():
        json.dump({"archived": 0, "files": []}, sys.stdout, indent=2)
        print()
        return

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now(UTC) - timedelta(days=args.days)
    archived: list[str] = []

    for f in JOURNAL_DIR.glob("*.md"):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        meta, _ = parse_frontmatter(text)
        created = meta.get("created", "")
        if not created:
            continue
        try:
            dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
        except (ValueError, TypeError):
            continue
        if dt < cutoff:
            dest = ARCHIVE_DIR / f.name
            if dest.exists():
                stem, suffix, v = dest.stem, dest.suffix, 2
                while dest.exists():
                    dest = ARCHIVE_DIR / f"{stem}-v{v}{suffix}"
                    v += 1
            try:
                shutil.move(str(f), str(dest))
            except OSError as exc:
                print(f"Error: could not archive {f.name}: {exc}", file=sys.stderr)
                continue
            archived.append(str(dest))

    json.dump({"archived": len(archived), "files": archived}, sys.stdout, indent=2)
    print()


def cmd_delete(args: argparse.Namespace) -> None:
    """Delete a journal with confirmation."""
    path = _resolve_path(args.target)
    if path is None:
        print(f"Error: journal not found: {args.target}", file=sys.stderr)
        sys.exit(1)

    if not args.force:
        print(f"Delete {path.name}? Type 'yes' to confirm: ", file=sys.stderr, end="", flush=True)
        try:
            answer = input()
        except EOFError:
            answer = ""
        if answer.strip().lower() != "yes":
            print("Aborted.", file=sys.stderr)
            sys.exit(1)

    path.unlink()
    json.dump({"action": "deleted", "path": str(path)}, sys.stdout, indent=2)
    print()


# --- Helpers ---

def _resolve_path(target: str) -> Path | None:
    """Resolve a journal target: path, number, or keyword."""
    result = None

    # Direct path — force relative to JOURNAL_DIR unless already under it
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
            if target_lower in j.get("query", "").lower() or target_lower in Path(j["path"]).stem:
                result = Path(j["path"]).resolve()
                break

    # Containment check — reject paths outside JOURNAL_DIR
    if result is not None:
        jail = JOURNAL_DIR.resolve()
        if not str(result).startswith(str(jail) + "/") and result != jail:
            print(f"Error: path outside research directory: {target}", file=sys.stderr)
            sys.exit(1)
        if not result.is_file():
            return None

    return result


def main() -> None:
    ap = argparse.ArgumentParser(
        description="CRUD operations for research journals in ~/.claude/research/.",
    )
    sub = ap.add_subparsers(dest="command", required=True)

    # save
    sp_save = sub.add_parser("save", help="Create or update a research journal.")
    sp_save.add_argument("--query", required=False, default=None, help="Research query text.")
    sp_save.add_argument("--tier", choices=["quick", "standard", "deep", "exhaustive"], default="standard")
    sp_save.add_argument(
        "--mode",
        choices=["investigate", "factcheck", "compare", "survey", "track"],
        default="investigate",
    )
    sp_save.add_argument("--status", default="In Progress", help="Journal status.")
    sp_save.add_argument("--findings", default=None, help="JSON string of findings array.")
    sp_save.add_argument("--update", default=None, help="Path or number of existing journal to update.")

    # load
    sp_load = sub.add_parser("load", help="Load a journal and output as JSON.")
    sp_load.add_argument("target", help="Journal path, number, or keyword.")

    # list
    sp_list = sub.add_parser("list", help="List journals with metadata.")
    sp_list.add_argument("--filter", default=None, help="Filter: 'active', domain name, or tier.")

    # diff
    sp_diff = sub.add_parser("diff", help="Compare two journals.")
    sp_diff.add_argument("path1", help="First journal path or number.")
    sp_diff.add_argument("path2", help="Second journal path or number.")

    # archive
    sp_archive = sub.add_parser("archive", help="Archive old journals.")
    sp_archive.add_argument("--days", type=int, default=90, help="Archive journals older than N days.")

    # delete
    sp_delete = sub.add_parser("delete", help="Delete a journal.")
    sp_delete.add_argument("target", help="Journal path or number.")
    sp_delete.add_argument("--force", action="store_true", help="Skip confirmation prompt.")

    args = ap.parse_args()

    dispatch = {
        "save": cmd_save,
        "load": cmd_load,
        "list": cmd_list,
        "diff": cmd_diff,
        "archive": cmd_archive,
        "delete": cmd_delete,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
