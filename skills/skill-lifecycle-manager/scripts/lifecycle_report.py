#!/usr/bin/env python3
"""Report skill lifecycle stage from repo signals."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
TODO_RE = re.compile(r"\bTODO\b", re.IGNORECASE)
DEPRECATED_RE = re.compile(r"\b(deprecat(ed|ion)|sunset)\b", re.IGNORECASE)


def _parse_frontmatter(skill_md: Path) -> dict[str, Any]:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    data = yaml.safe_load(text[4:end])
    return data if isinstance(data, dict) else {}


def _stage_for_skill(skill_dir: Path) -> dict[str, Any]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return {"skill": skill_dir.name, "ok": False, "error": "missing SKILL.md"}

    fm = _parse_frontmatter(skill_md)
    body = skill_md.read_text(encoding="utf-8").split("\n---\n", 2)[-1]
    description = str(fm.get("description", ""))
    internal = bool((fm.get("metadata") or {}).get("internal"))
    has_evals = (skill_dir / "evals" / "evals.json").is_file()
    has_check = (skill_dir / "scripts" / "check.py").is_file()
    signals: list[str] = []

    if internal:
        stage = "internal"
        signals.append("metadata.internal=true")
    elif DEPRECATED_RE.search(body) or DEPRECATED_RE.search(description):
        stage = "deprecated"
        signals.append("deprecation language detected")
    elif TODO_RE.search(description) or not description.strip():
        stage = "draft"
        signals.append("description incomplete")
    elif not has_evals or not has_check:
        stage = "draft"
        if not has_evals:
            signals.append("missing evals/evals.json")
        if not has_check:
            signals.append("missing scripts/check.py")
    else:
        stage = "active"
        signals.append("frontmatter, evals, and check contract present")

    return {
        "skill": skill_dir.name,
        "ok": True,
        "stage": stage,
        "signals": signals,
        "has_evals": has_evals,
        "has_check": has_check,
        "internal": internal,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Skill lifecycle report")
    parser.add_argument("name", nargs="?", default=None, help="Skill directory name")
    parser.add_argument("--all", action="store_true", help="Report all repo skills")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    skills_dir = REPO_ROOT / "skills"
    if args.all or args.name in (None, "repo"):
        rows = [_stage_for_skill(path) for path in sorted(skills_dir.iterdir()) if path.is_dir()]
        payload = {"ok": True, "count": len(rows), "skills": rows}
    else:
        skill_dir = skills_dir / args.name
        if not skill_dir.is_dir():
            print(json.dumps({"ok": False, "error": f"unknown skill: {args.name}"}))
            return 1
        payload = _stage_for_skill(skill_dir)

    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        if "skills" in payload:
            for row in payload["skills"]:
                print(f"{row.get('skill')}: {row.get('stage')} ({', '.join(row.get('signals', []))})")
        else:
            print(f"{payload.get('skill')}: {payload.get('stage')}")
    return 0 if payload.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
