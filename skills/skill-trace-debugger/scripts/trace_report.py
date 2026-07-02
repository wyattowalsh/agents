#!/usr/bin/env python3
"""Inspect eval and validator trace readiness for skills."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SLASH_RE = re.compile(r"^/\S+")


def _load_evals(skill_dir: Path) -> dict[str, Any] | None:
    eval_path = skill_dir / "evals" / "evals.json"
    if not eval_path.is_file():
        return None
    return json.loads(eval_path.read_text(encoding="utf-8"))


def _trace_report(skill_dir: Path) -> dict[str, Any]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return {"skill": skill_dir.name, "ok": False, "error": "missing SKILL.md"}

    eval_data = _load_evals(skill_dir)
    has_check = (skill_dir / "scripts" / "check.py").is_file()
    gaps: list[str] = []
    explicit_cases = 0

    if eval_data is None:
        gaps.append("missing evals/evals.json")
    else:
        for case in eval_data.get("evals", []):
            if not isinstance(case, dict):
                continue
            prompt = str(case.get("prompt", ""))
            if SLASH_RE.match(prompt.strip()) or skill_dir.name in prompt:
                explicit_cases += 1

    if not has_check:
        gaps.append("missing scripts/check.py")
    if eval_data is not None and explicit_cases == 0:
        gaps.append("no explicit-invocation eval case detected")

    return {
        "skill": skill_dir.name,
        "ok": True,
        "has_evals": eval_data is not None,
        "has_check": has_check,
        "explicit_invocation_cases": explicit_cases,
        "gaps": gaps,
        "trace_ready": not gaps,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Skill trace readiness report")
    parser.add_argument("name", nargs="?", default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    skills_dir = REPO_ROOT / "skills"
    if args.all or args.name in (None, "repo"):
        rows = [_trace_report(path) for path in sorted(skills_dir.iterdir()) if path.is_dir()]
        payload: dict[str, Any] = {"ok": True, "count": len(rows), "skills": rows}
    else:
        skill_dir = skills_dir / args.name
        if not skill_dir.is_dir():
            print(json.dumps({"ok": False, "error": f"unknown skill: {args.name}"}))
            return 1
        payload = _trace_report(skill_dir)

    if args.format == "json":
        print(json.dumps(payload, indent=2))
    elif "skills" in payload:
        for row in payload["skills"]:
            status = "ready" if row.get("trace_ready") else f"gaps: {', '.join(row.get('gaps', []))}"
            print(f"{row['skill']}: {status}")
    else:
        status = "ready" if payload.get("trace_ready") else f"gaps: {', '.join(payload.get('gaps', []))}"
        print(f"{payload['skill']}: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
