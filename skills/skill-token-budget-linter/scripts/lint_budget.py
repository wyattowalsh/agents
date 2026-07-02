#!/usr/bin/env python3
"""Lint skill token budgets for descriptions, bodies, and references."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]

LIMITS = {
    "description_soft": 200,
    "description_hard": 1024,
    "body_soft": 400,
    "body_hard": 500,
    "reference_soft": 300,
    "reference_hard": 500,
}

RUNTIME_FIELDS = frozenset({
    "user-invocable",
    "disable-model-invocation",
    "context",
    "agent",
    "hooks",
    "paths",
    "model",
    "argument-hint",
})


def _parse_skill_md(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    frontmatter = yaml.safe_load(text[4:end])
    if not isinstance(frontmatter, dict):
        frontmatter = {}
    return frontmatter, text[end + 5 :]


def lint_skill(skill_dir: Path, *, strict: bool) -> dict[str, object]:
    skill_md = skill_dir / "SKILL.md"
    findings: list[dict[str, object]] = []
    if not skill_md.is_file():
        return {"skill": skill_dir.name, "ok": False, "findings": [{"level": "error", "message": "missing SKILL.md"}]}

    text = skill_md.read_text(encoding="utf-8")
    frontmatter, body = _parse_skill_md(text)
    description = str(frontmatter.get("description", "")).strip()
    desc_len = len(description)
    body_lines = len(body.splitlines())

    def add(level: str, message: str, **extra: object) -> None:
        findings.append({"level": level, "message": message, **extra})

    if desc_len > LIMITS["description_hard"]:
        add("error", "description exceeds hard limit", chars=desc_len, limit=LIMITS["description_hard"])
    elif desc_len > LIMITS["description_soft"] and strict:
        add("error", "description exceeds strict soft limit", chars=desc_len, limit=LIMITS["description_soft"])
    elif desc_len > LIMITS["description_soft"]:
        add("warn", "description exceeds soft limit", chars=desc_len, limit=LIMITS["description_soft"])

    if body_lines > LIMITS["body_hard"]:
        add("error", "body exceeds hard line limit", lines=body_lines, limit=LIMITS["body_hard"])
    elif body_lines > LIMITS["body_soft"] and strict:
        add("error", "body exceeds strict soft line limit", lines=body_lines, limit=LIMITS["body_soft"])
    elif body_lines > LIMITS["body_soft"]:
        add("warn", "body exceeds soft line limit", lines=body_lines, limit=LIMITS["body_soft"])

    refs_dir = skill_dir / "references"
    if refs_dir.is_dir():
        for ref in sorted(refs_dir.glob("*.md")):
            ref_lines = len(ref.read_text(encoding="utf-8").splitlines())
            if ref_lines > LIMITS["reference_hard"]:
                add("error", "reference exceeds hard line limit", file=str(ref.relative_to(skill_dir)), lines=ref_lines)
            elif ref_lines > LIMITS["reference_soft"] and strict:
                add("error", "reference exceeds strict soft line limit", file=str(ref.relative_to(skill_dir)), lines=ref_lines)
            elif ref_lines > LIMITS["reference_soft"]:
                add("warn", "reference exceeds soft line limit", file=str(ref.relative_to(skill_dir)), lines=ref_lines)

    runtime_fields = sorted(
        key for key in frontmatter if isinstance(key, str) and key in RUNTIME_FIELDS
    )
    ok = not any(item["level"] == "error" for item in findings)
    return {
        "skill": skill_dir.name,
        "ok": ok,
        "description_chars": desc_len,
        "body_lines": body_lines,
        "runtime_fields": runtime_fields,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint skill token budgets")
    parser.add_argument("target", nargs="?", default="", help="Skill name or omit with --all")
    parser.add_argument("--all", action="store_true", help="Lint every skill")
    parser.add_argument("--strict", action="store_true", help="Treat soft limits as errors")
    args = parser.parse_args(argv)

    skills_root = REPO_ROOT / "skills"
    if args.all or not args.target:
        skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file())
    else:
        skill_dirs = [skills_root / args.target]

    reports = [lint_skill(skill_dir, strict=args.strict) for skill_dir in skill_dirs]
    payload = {"ok": all(report["ok"] for report in reports), "reports": reports}
    print(json.dumps(payload, indent=2))

    for report in reports:
        for finding in report["findings"]:
            print(f"{report['skill']}: {finding['level']}: {finding['message']}", file=sys.stderr)

    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
