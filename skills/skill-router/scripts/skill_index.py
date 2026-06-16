#!/usr/bin/env python3
"""Index and search local AI agent skills."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from _parse import parse_frontmatter

TOKEN_RE = re.compile(r"[a-z0-9]+")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
MAX_BODY_CHARS = 120_000

OUTPUT_FORMATS = ("text", "json", "jsonl")
SKILL_SOURCES = (
    "all",
    "repo",
    "project",
    "codex",
    "global",
    "claude-code",
    "gemini-cli",
    "github-copilot",
    "opencode",
    "plugin",
)


@dataclass(frozen=True)
class SkillRoot:
    """A filesystem root that may contain skills."""

    path: Path
    source: str
    trust_tier: str


@dataclass
class SkillRecord:
    """A parsed skill plus source metadata."""

    name: str
    path: str
    source: str
    trust_tier: str
    description: str
    source_root: str
    title: str = ""
    aliases: list[str] | None = None
    warnings: list[str] | None = None
    body: str = ""

    def public_dict(self, *, include_body: bool = False) -> dict[str, object]:
        data = asdict(self)
        if not include_body:
            data.pop("body", None)
        data["aliases"] = data.get("aliases") or []
        data["warnings"] = data.get("warnings") or []
        return data


@dataclass
class SkillSearchResult:
    """A ranked skill search result."""

    record: SkillRecord
    score: float
    matched_fields: list[str]
    reason: str

    def public_dict(self, *, include_body: bool = False) -> dict[str, object]:
        data = self.record.public_dict(include_body=include_body)
        data.update(
            {
                "score": round(self.score, 3),
                "matched_fields": self.matched_fields,
                "reason": self.reason,
            }
        )
        return data


def find_repo_root(start: Path | None = None) -> Path | None:
    """Walk parents for a repo root containing skills/."""
    current = (start or Path.cwd()).resolve()
    for path in [current, *current.parents]:
        skills_dir = path / "skills"
        if skills_dir.is_dir():
            return path
    return None


def default_repo_root() -> Path:
    """Return the default repository root for skill discovery."""
    found = find_repo_root()
    if found is not None:
        return found
    return Path(__file__).resolve().parents[3]


def default_skill_roots(
    *,
    root: Path | None = None,
    home: Path | None = None,
    cwd: Path | None = None,
) -> list[SkillRoot]:
    """Return known local skill roots in precedence order."""
    repo_root = root or default_repo_root()
    home_dir = home or Path.home()
    cwd_path = cwd or Path.cwd()

    roots: list[SkillRoot] = [
        SkillRoot(repo_root / "skills", "repo", "repo"),
    ]

    for parent in [cwd_path, *cwd_path.parents]:
        project_root = parent / ".agents" / "skills"
        if project_root == repo_root / ".agents" / "skills":
            continue
        roots.append(SkillRoot(project_root, "project", "codex-user"))
        if parent == repo_root:
            break

    roots.extend(
        [
            SkillRoot(home_dir / ".codex" / "skills", "codex", "codex-user"),
            SkillRoot(home_dir / ".agents" / "skills", "global", "external-installed"),
            SkillRoot(home_dir / ".claude" / "skills", "claude-code", "external-installed"),
            SkillRoot(home_dir / ".gemini" / "skills", "gemini-cli", "external-installed"),
            SkillRoot(home_dir / ".copilot" / "skills", "github-copilot", "external-installed"),
            SkillRoot(home_dir / ".config" / "opencode" / "skills", "opencode", "external-installed"),
        ]
    )

    plugin_cache = home_dir / ".codex" / "plugins" / "cache"
    if plugin_cache.exists():
        for skills_root in sorted(plugin_cache.glob("*/*/skills")):
            trust_tier = "openai-plugin" if "openai-" in str(skills_root) else "plugin"
            roots.append(SkillRoot(skills_root, "plugin", trust_tier))

    return _dedupe_roots(roots)


def collect_skill_records(
    *,
    root: Path | None = None,
    home: Path | None = None,
    cwd: Path | None = None,
    source: str = "all",
    include_body: bool = False,
) -> list[SkillRecord]:
    """Collect parsed skill records from known roots."""
    roots = default_skill_roots(root=root, home=home, cwd=cwd)
    records: list[SkillRecord] = []
    seen_paths: set[str] = set()
    best_by_name: dict[str, SkillRecord] = {}

    for skill_root in roots:
        if not _source_matches(skill_root.source, source):
            continue
        for skill_file in _iter_skill_files(skill_root.path):
            real_path = _safe_realpath(skill_file)
            if real_path in seen_paths:
                continue
            seen_paths.add(real_path)
            record = _read_skill(skill_file, skill_root, include_body=include_body)
            existing = best_by_name.get(record.name)
            if existing is None or _trust_rank(record.trust_tier) < _trust_rank(existing.trust_tier):
                best_by_name[record.name] = record
            records.append(record)

    preferred_paths = {record.path for record in best_by_name.values()}
    records.sort(
        key=lambda record: (
            record.path not in preferred_paths,
            _trust_rank(record.trust_tier),
            record.name,
            record.path,
        )
    )
    return records


def search_skills(
    query: str,
    *,
    root: Path | None = None,
    home: Path | None = None,
    cwd: Path | None = None,
    source: str = "all",
    limit: int = 5,
) -> list[SkillSearchResult]:
    """Search local skills with deterministic lexical ranking."""
    normalized_query = query.strip()
    if not normalized_query:
        return []

    records = collect_skill_records(root=root, home=home, cwd=cwd, source=source, include_body=True)
    tokenized_records = [_tokenize_record(record) for record in records]
    doc_count = max(len(tokenized_records), 1)
    doc_freq: dict[str, int] = {}
    for token_set in ({token for tokens in item.values() for token in tokens} for item in tokenized_records):
        for token in token_set:
            doc_freq[token] = doc_freq.get(token, 0) + 1

    query_tokens = _tokens(normalized_query)
    results: list[SkillSearchResult] = []
    for record, field_tokens in zip(records, tokenized_records, strict=True):
        score, matched_fields = _score_record(record, field_tokens, query_tokens, doc_freq, doc_count)
        if score <= 0:
            continue
        reason = _build_reason(record, normalized_query, matched_fields)
        results.append(SkillSearchResult(record=record, score=score, matched_fields=matched_fields, reason=reason))

    results.sort(key=lambda result: (-result.score, _trust_rank(result.record.trust_tier), result.record.name))
    return results[: max(limit, 0)]


def read_skill(
    name_or_path: str,
    *,
    root: Path | None = None,
    home: Path | None = None,
    cwd: Path | None = None,
) -> SkillRecord:
    """Read a skill by exact path or exact skill name."""
    candidate = Path(name_or_path).expanduser()
    if candidate.exists():
        skill_file = candidate if candidate.name == "SKILL.md" else candidate / "SKILL.md"
        if not skill_file.exists():
            raise FileNotFoundError(f"No SKILL.md at {candidate}")
        skill_root = SkillRoot(skill_file.parent.parent, "explicit", "unknown")
        return _read_skill(skill_file, skill_root, include_body=True)

    records = collect_skill_records(root=root, home=home, cwd=cwd, include_body=True)
    exact = [record for record in records if record.name == name_or_path]
    if exact:
        exact.sort(key=lambda record: (_trust_rank(record.trust_tier), record.path))
        return exact[0]
    raise LookupError(f"No installed skill named '{name_or_path}'")


def doctor_report(*, root: Path | None = None, home: Path | None = None, cwd: Path | None = None) -> dict[str, object]:
    """Return a diagnostic summary for skill discovery."""
    roots = default_skill_roots(root=root, home=home, cwd=cwd)
    root_rows = []
    records = collect_skill_records(root=root, home=home, cwd=cwd, include_body=False)
    for skill_root in roots:
        files = list(_iter_skill_files(skill_root.path)) if skill_root.path.exists() else []
        root_rows.append(
            {
                "path": str(skill_root.path),
                "source": skill_root.source,
                "trust_tier": skill_root.trust_tier,
                "exists": skill_root.path.exists(),
                "skill_count": len(files),
            }
        )

    warning_count = sum(len(record.warnings or []) for record in records)
    return {
        "ok": True,
        "root_count": len(root_rows),
        "skill_count": len(records),
        "warning_count": warning_count,
        "roots": root_rows,
    }


def _dedupe_roots(roots: list[SkillRoot]) -> list[SkillRoot]:
    seen: set[str] = set()
    deduped: list[SkillRoot] = []
    for skill_root in roots:
        key = _safe_realpath(skill_root.path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(skill_root)
    return deduped


def _iter_skill_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    results: list[Path] = []
    visited_dirs: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
        real_dir = _safe_realpath(Path(dirpath))
        if real_dir in visited_dirs:
            dirnames[:] = []
            continue
        visited_dirs.add(real_dir)
        dirnames[:] = sorted(d for d in dirnames if d not in {".git", "node_modules", "__pycache__"})
        if "SKILL.md" in filenames:
            results.append(Path(dirpath) / "SKILL.md")
            dirnames[:] = []
    return sorted(results)


def _read_skill(skill_file: Path, skill_root: SkillRoot, *, include_body: bool) -> SkillRecord:
    warnings: list[str] = []
    raw_body = ""
    fm: dict[str, object] = {}
    try:
        content = skill_file.read_text(errors="replace")
        fm, raw_body = parse_frontmatter(content)
    except Exception as exc:
        warnings.append(f"parse_error: {exc}")

    name = str(fm.get("name") or skill_file.parent.name)
    description = str(fm.get("description") or "")
    if not description:
        warnings.append("missing description")
    if fm.get("name") and fm.get("name") != skill_file.parent.name:
        warnings.append("frontmatter name does not match directory")
    if fm.get("hooks"):
        warnings.append("declares hooks")
    if (skill_file.parent / "scripts").is_dir():
        warnings.append("has scripts")

    aliases = _extract_aliases(fm)
    body = raw_body[:MAX_BODY_CHARS] if include_body else ""
    return SkillRecord(
        name=name,
        path=str(skill_file),
        source=skill_root.source,
        trust_tier=skill_root.trust_tier,
        description=description,
        source_root=str(skill_root.path),
        title=str(fm.get("title") or name.replace("-", " ").title()),
        aliases=aliases,
        warnings=warnings,
        body=body,
    )


def _extract_aliases(fm: dict[str, object]) -> list[str]:
    metadata = fm.get("metadata")
    candidates: object = None
    if isinstance(metadata, dict):
        metadata_dict = cast(dict[object, object], metadata)
        candidates = metadata_dict.get("aliases") or metadata_dict.get("alias")
    if candidates is None:
        candidates = fm.get("aliases") or fm.get("alias")
    if isinstance(candidates, str):
        return [candidates]
    if isinstance(candidates, list):
        return [str(item) for item in candidates if str(item).strip()]
    return []


def _tokenize_record(record: SkillRecord) -> dict[str, list[str]]:
    headings = " ".join(HEADING_RE.findall(record.body or ""))
    aliases = " ".join(record.aliases or [])
    return {
        "name": _tokens(f"{record.name} {record.title} {aliases}"),
        "description": _tokens(record.description),
        "headings": _tokens(headings),
        "body": _tokens(record.body),
    }


def _score_record(
    record: SkillRecord,
    field_tokens: dict[str, list[str]],
    query_tokens: list[str],
    doc_freq: dict[str, int],
    doc_count: int,
) -> tuple[float, list[str]]:
    query_text = " ".join(query_tokens)
    name_text = record.name.lower()
    name_key = " ".join(_tokens(record.name))
    alias_texts = [alias.lower() for alias in record.aliases or []]
    alias_keys = [" ".join(_tokens(alias)) for alias in record.aliases or []]

    score = 0.0
    matched_fields: list[str] = []
    if query_text and (query_text in {name_text, name_key} or query_text in alias_texts or query_text in alias_keys):
        score += 120
        matched_fields.append("name")
    elif query_text and (
        name_text.startswith(query_text)
        or name_key.startswith(query_text)
        or any(alias.startswith(query_text) for alias in alias_texts)
        or any(alias.startswith(query_text) for alias in alias_keys)
    ):
        score += 60
        matched_fields.append("name")

    weights = {"name": 8.0, "description": 4.0, "headings": 2.0, "body": 1.0}
    for field, tokens in field_tokens.items():
        if not tokens:
            continue
        field_score = 0.0
        token_counts: dict[str, int] = {}
        for token in tokens:
            token_counts[token] = token_counts.get(token, 0) + 1
        for token in query_tokens:
            count = token_counts.get(token, 0)
            if count == 0:
                continue
            idf = math.log((doc_count + 1) / (doc_freq.get(token, 0) + 1)) + 1
            field_score += weights[field] * (1 + math.log(count)) * idf
        if field_score:
            score += field_score
            if field not in matched_fields:
                matched_fields.append(field)

    if record.trust_tier == "repo":
        score += 1.5
    elif record.trust_tier in {"codex-user", "openai-plugin"}:
        score += 0.5
    return score, matched_fields


def _build_reason(record: SkillRecord, query: str, matched_fields: list[str]) -> str:
    if not matched_fields:
        return "No lexical match"
    fields = ", ".join(matched_fields)
    return f"Matched {fields} for query '{query}' in {record.source} skill `{record.name}`."


def _tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def _source_matches(actual: str, requested: str) -> bool:
    requested = requested.lower()
    if requested == "all":
        return True
    if requested == "global":
        return actual in {"global", "claude-code", "gemini-cli", "github-copilot", "opencode"}
    return actual == requested


def _trust_rank(trust_tier: str) -> int:
    order = {
        "repo": 0,
        "codex-user": 1,
        "openai-plugin": 2,
        "external-installed": 3,
        "plugin": 4,
        "unknown": 5,
    }
    return order.get(trust_tier, 9)


def _safe_realpath(path: Path) -> str:
    try:
        return str(path.resolve())
    except OSError:
        return str(path.absolute())


def _normalize_output_format(format_: str) -> str:
    normalized = format_.lower()
    if normalized not in OUTPUT_FORMATS:
        print(
            f"Error: unsupported format '{format_}'. Use one of: {', '.join(OUTPUT_FORMATS)}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return normalized


def _normalize_skill_source(source: str) -> str:
    normalized = source.lower()
    if normalized not in SKILL_SOURCES:
        print(
            f"Error: unsupported source '{source}'. Use one of: {', '.join(SKILL_SOURCES)}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return normalized


def _format_skill_row(record: dict[str, object]) -> str:
    warnings = record.get("warnings")
    warning_count = len(warnings) if isinstance(warnings, list) else 0
    warning_text = f" warnings={warning_count}" if warning_count else ""
    description = str(record.get("description") or "").replace("\n", " ").strip()
    if len(description) > 120:
        description = description[:117].rstrip() + "..."
    return (
        f"{record['name']} [{record['source']}:{record['trust_tier']}]"
        f"{warning_text}\n  {record['path']}\n  {description}"
    )


def _emit_structured_output(
    format_: str,
    *,
    text_lines: list[str] | None = None,
    json_data: dict | list | None = None,
    jsonl_records: list[dict] | None = None,
) -> None:
    normalized = _normalize_output_format(format_)
    if normalized == "text":
        for line in text_lines or []:
            print(line)
        return
    if normalized == "json":
        print(json.dumps(json_data, indent=2))
        return
    for record in jsonl_records or []:
        print(json.dumps(record))


def _runtime_paths(args: argparse.Namespace) -> tuple[Path | None, Path | None, Path | None]:
    root = Path(args.repo_root).resolve() if args.repo_root else None
    home = Path(args.home).resolve() if args.home else None
    cwd = Path(args.cwd).resolve() if args.cwd else None
    return root, home, cwd


def _cmd_index(args: argparse.Namespace) -> int:
    root, home, cwd = _runtime_paths(args)
    source = _normalize_skill_source(args.source)
    records = [record.public_dict() for record in collect_skill_records(root=root, home=home, cwd=cwd, source=source)]
    text_lines = [f"{len(records)} skills found"]
    text_lines.extend(_format_skill_row(record) for record in records)
    _emit_structured_output(
        args.format,
        text_lines=text_lines,
        json_data={"count": len(records), "skills": records},
        jsonl_records=[{"type": "skill", **record} for record in records],
    )
    return 0


def _cmd_search(args: argparse.Namespace) -> int:
    root, home, cwd = _runtime_paths(args)
    source = _normalize_skill_source(args.source)
    results = [result.public_dict() for result in search_skills(args.query, root=root, home=home, cwd=cwd, source=source, limit=args.limit)]
    text_lines = [f"{len(results)} matches for {args.query!r}"]
    for result in results:
        matched_fields = result.get("matched_fields")
        fields_text = ",".join(str(field) for field in matched_fields) if isinstance(matched_fields, list) else ""
        text_lines.append(
            f"{result['name']} score={result['score']} fields={fields_text}\n"
            f"  {result['reason']}\n"
            f"  {result['path']}\n"
            f"  {result.get('description', '')}"
        )
    _emit_structured_output(
        args.format,
        text_lines=text_lines,
        json_data={"query": args.query, "count": len(results), "skills": results},
        jsonl_records=[{"type": "skill", "query": args.query, **result} for result in results],
    )
    return 0


def _cmd_read(args: argparse.Namespace) -> int:
    root, home, cwd = _runtime_paths(args)
    try:
        record = read_skill(args.name_or_path, root=root, home=home, cwd=cwd)
    except (FileNotFoundError, LookupError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    data = record.public_dict(include_body=True)
    text_lines = [
        f"{record.name} [{record.source}:{record.trust_tier}]",
        str(record.path),
        "",
        record.description,
        "",
        record.body,
    ]
    _emit_structured_output(
        args.format,
        text_lines=text_lines,
        json_data=data,
        jsonl_records=[{"type": "skill", **data}],
    )
    return 0


def _cmd_context(args: argparse.Namespace) -> int:
    root, home, cwd = _runtime_paths(args)
    source = _normalize_skill_source(args.source)
    results = search_skills(args.query, root=root, home=home, cwd=cwd, source=source, limit=args.limit)
    records: list[dict[str, object]] = []
    for result in results:
        try:
            record = read_skill(result.record.path, root=root, home=home, cwd=cwd)
        except (FileNotFoundError, LookupError):
            record = result.record
        data = result.public_dict()
        data["body"] = record.body
        records.append(data)

    text_lines = [f"Skill context for {args.query!r}", ""]
    for result in records:
        warnings = result.get("warnings")
        warning_text = ", ".join(str(warning) for warning in warnings) if isinstance(warnings, list) else ""
        text_lines.extend(
            [
                f"## {result['name']} score={result['score']} [{result['source']}:{result['trust_tier']}]",
                f"Path: {result['path']}",
                f"Reason: {result['reason']}",
            ]
        )
        if warning_text:
            text_lines.append(f"Warnings: {warning_text}")
        text_lines.extend(["", str(result.get("body") or ""), ""])

    _emit_structured_output(
        args.format,
        text_lines=text_lines,
        json_data={"query": args.query, "count": len(records), "skills": records},
        jsonl_records=[{"type": "skill_context", "query": args.query, **record} for record in records],
    )
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    root, home, cwd = _runtime_paths(args)
    report = doctor_report(root=root, home=home, cwd=cwd)
    roots = report.get("roots")
    root_rows: list[dict[str, object]] = []
    if isinstance(roots, list):
        root_rows = [cast(dict[str, object], row) for row in roots if isinstance(row, dict)]
    text_lines = [
        f"Skill roots: {report['root_count']}",
        f"Skills found: {report['skill_count']}",
        f"Warnings: {report['warning_count']}",
    ]
    for row in root_rows:
        status = "ok" if row.get("exists") else "missing"
        text_lines.append(f"{status} {row.get('source')} {row.get('skill_count')} {row.get('path')}")
    _emit_structured_output(
        args.format,
        text_lines=text_lines,
        json_data=report,
        jsonl_records=[{"type": "root", **row} for row in root_rows],
    )
    return 0


def _add_format_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", default="text", choices=OUTPUT_FORMATS, help="Output format: text, json, jsonl")


def _add_runtime_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", help="Repository root override for skill discovery")
    parser.add_argument("--home", help="Home directory override for installed skill roots")
    parser.add_argument("--cwd", help="Working directory override for project skill roots")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Index and search local skills")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Index locally available skills without loading full bodies")
    index_parser.add_argument("--source", default="all", help="Skill source: all, repo, codex, global, plugin, ...")
    _add_format_option(index_parser)
    _add_runtime_options(index_parser)
    index_parser.set_defaults(func=_cmd_index)

    search_parser = subparsers.add_parser("search", help="Search locally available skills")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--source", default="all", help="Skill source: all, repo, codex, global, plugin, ...")
    search_parser.add_argument("--limit", "-n", type=int, default=5, help="Maximum results")
    _add_format_option(search_parser)
    _add_runtime_options(search_parser)
    search_parser.set_defaults(func=_cmd_search)

    context_parser = subparsers.add_parser("context", help="Build a compact context packet for matching skills")
    context_parser.add_argument("query", help="Task or capability query")
    context_parser.add_argument("--source", default="all", help="Skill source: all, repo, codex, global, plugin, ...")
    context_parser.add_argument("--limit", "-n", type=int, default=3, help="Maximum skill bodies to include (max 5)")
    _add_format_option(context_parser)
    _add_runtime_options(context_parser)
    context_parser.set_defaults(func=_cmd_context)

    read_parser = subparsers.add_parser("read", help="Read one skill body by exact name or path")
    read_parser.add_argument("name_or_path", help="Skill name, directory path, or SKILL.md path")
    _add_format_option(read_parser)
    _add_runtime_options(read_parser)
    read_parser.set_defaults(func=_cmd_read)

    doctor_parser = subparsers.add_parser("doctor", help="Diagnose skill discovery roots and counts")
    _add_format_option(doctor_parser)
    _add_runtime_options(doctor_parser)
    doctor_parser.set_defaults(func=_cmd_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "context" and args.limit > 5:
        print("Error: --limit must be at most 5 for context", file=sys.stderr)
        return 1
    if args.command in {"search", "context"} and args.limit < 1:
        print("Error: --limit must be at least 1", file=sys.stderr)
        return 1
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())