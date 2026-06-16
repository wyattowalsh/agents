#!/usr/bin/env python3
"""Scaffold a new skill SKILL.md from template."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPT_ROOT = Path(__file__).resolve().parent
if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))

from asset_toolkit.common import KEBAB_CASE_PATTERN, find_repo_root, to_title


def validate_name(name: str) -> None:
    if not KEBAB_CASE_PATTERN.match(name):
        raise ValueError(f"name must be kebab-case (got '{name}')")
    if len(name) > 64:
        raise ValueError("name exceeds 64 characters")


def scaffold_skill(repo_root: Path, name: str, *, dry_run: bool = False) -> Path:
    validate_name(name)
    skill_dir = repo_root / "skills" / name
    skill_file = skill_dir / "SKILL.md"
    if skill_file.exists():
        raise FileExistsError(f"{skill_file} already exists")

    title = to_title(name)
    content = f"""---
name: {name}
description: TODO — What this skill does and when to use it
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0.0"
---

# {title}

Skill instructions go here in markdown. Use imperative voice.

## When to Use

Describe when an AI agent should invoke this skill.

## Instructions

Step-by-step instructions for the agent.
"""

    if dry_run:
        print(content)
        return skill_file

    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file.write_text(content, encoding="utf-8")
    return skill_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new skill")
    parser.add_argument("name", help="kebab-case skill name")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    repo_root = find_repo_root()
    if repo_root is None:
        print("Could not find repo root", file=sys.stderr)
        return 1

    try:
        path = scaffold_skill(repo_root, args.name, dry_run=args.dry_run)
    except (ValueError, FileExistsError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not args.dry_run:
        print(f"Created {path.relative_to(repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())