#!/usr/bin/env python3
"""Infer skill tags from names and descriptions."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]

TAG_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("conventions", re.compile(r"convention|standard|lint|style", re.I)),
    ("orchestration", re.compile(r"orchestr|delegat|ensemble|workflow|fleet", re.I)),
    ("security", re.compile(r"security|audit|scanner|quarantine|owasp", re.I)),
    ("docs", re.compile(r"docs|readme|steward|catalog|mdx", re.I)),
    ("mcp", re.compile(r"\bmcp\b|server|registry|fastmcp", re.I)),
    ("eval", re.compile(r"eval|scaffold|adequacy|behavior", re.I)),
    ("infra", re.compile(r"devops|ci/cd|pipeline|release|deploy", re.I)),
    ("research", re.compile(r"research|discover|source audit", re.I)),
]


def _frontmatter(skill_md: Path) -> dict[str, Any]:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    data = yaml.safe_load(text[4:end])
    return data if isinstance(data, dict) else {}


def _infer_tags(name: str, description: str) -> list[str]:
    haystack = f"{name} {description}"
    tags = [tag for tag, pattern in TAG_RULES if pattern.search(haystack)]
    if name.endswith("-conventions"):
        tags.append("conventions")
    return sorted(set(tags))


def _report(skill_dir: Path) -> dict[str, Any]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return {"skill": skill_dir.name, "ok": False, "error": "missing SKILL.md"}
    fm = _frontmatter(skill_md)
    description = str(fm.get("description", ""))
    tags = _infer_tags(skill_dir.name, description)
    authoring = REPO_ROOT / "docs" / "src" / "authoring" / "skills" / f"{skill_dir.name}.mdx"
    return {
        "skill": skill_dir.name,
        "ok": True,
        "inferred_tags": tags,
        "has_authoring_mdx": authoring.is_file(),
        "authoring_path": str(authoring.relative_to(REPO_ROOT)) if authoring.is_file() else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Skill tag inference report")
    parser.add_argument("name", nargs="?", default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    skills_dir = REPO_ROOT / "skills"
    if args.all or args.name in (None, "repo"):
        rows = [_report(path) for path in sorted(skills_dir.iterdir()) if path.is_dir()]
        payload: dict[str, Any] = {"ok": True, "count": len(rows), "skills": rows}
    else:
        skill_dir = skills_dir / args.name
        if not skill_dir.is_dir():
            print(json.dumps({"ok": False, "error": f"unknown skill: {args.name}"}))
            return 1
        payload = _report(skill_dir)

    if args.format == "json":
        print(json.dumps(payload, indent=2))
    elif "skills" in payload:
        for row in payload["skills"]:
            print(f"{row['skill']}: {', '.join(row.get('inferred_tags', [])) or '(none)'}")
    else:
        print(f"{payload['skill']}: {', '.join(payload.get('inferred_tags', [])) or '(none)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
