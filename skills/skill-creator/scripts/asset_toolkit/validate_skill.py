#!/usr/bin/env python3
"""Validate skill SKILL.md frontmatter and body."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPT_ROOT = Path(__file__).resolve().parent.parent
if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))

from asset_toolkit.common import KEBAB_CASE_PATTERN, find_repo_root, parse_frontmatter


def validate_skill_file(skill_file: Path) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []

    def add_error(message: str) -> None:
        errors.append({"source": str(skill_file), "message": message})

    try:
        content = skill_file.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(content)
        skill_dir = skill_file.parent

        if "name" not in frontmatter:
            add_error("missing required field 'name'")
        else:
            name = str(frontmatter["name"])
            if not KEBAB_CASE_PATTERN.match(name):
                add_error("name must be kebab-case")
            if len(name) > 64:
                add_error("name exceeds 64 characters")
            if name != skill_dir.name:
                add_error(f"name '{name}' doesn't match directory '{skill_dir.name}'")

        if "description" not in frontmatter:
            add_error("missing required field 'description'")
        else:
            description = str(frontmatter["description"]).strip()
            if not description:
                add_error("description cannot be empty")
            elif len(str(frontmatter["description"])) > 1024:
                add_error("description exceeds 1024 characters")

        if not body:
            add_error("body cannot be empty")
    except Exception as exc:
        add_error(str(exc))

    return errors


def validate_skills_root(skills_dir: Path) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if not skills_dir.is_dir():
        return [{"source": str(skills_dir), "message": "skills directory not found"}]

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if skill_file.is_file():
            errors.extend(validate_skill_file(skill_file))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate skill SKILL.md files")
    parser.add_argument(
        "path",
        nargs="?",
        default="",
        help="Skill directory or skills/ root (default: auto-detect repo skills/)",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    if args.path:
        target = Path(args.path).resolve()
        if (target / "SKILL.md").is_file():
            errors = validate_skill_file(target / "SKILL.md")
        elif target.name == "SKILL.md":
            errors = validate_skill_file(target)
        else:
            errors = validate_skills_root(target)
    else:
        repo_root = find_repo_root()
        if repo_root is None:
            print("Could not find repo skills/ directory", file=sys.stderr)
            return 1
        errors = validate_skills_root(repo_root / "skills")

    payload = {"ok": not errors, "error_count": len(errors), "errors": errors}
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    elif errors:
        for error in errors:
            print(f"{error['source']}: {error['message']}", file=sys.stderr)
    else:
        print("All skills valid")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
