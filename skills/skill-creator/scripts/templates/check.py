#!/usr/bin/env python3
"""Validate this skill's SKILL.md and eval manifests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TOOLKIT = SKILL_DIR / "scripts" / "asset_toolkit"
PACKAGE = SKILL_DIR / "scripts" / "package.py"
AUDIT = SKILL_DIR.parent / "skill-creator" / "scripts" / "audit.py"


def _run(command: list[str]) -> int:
    result = subprocess.run(command, check=False)
    return result.returncode


def main() -> int:
    commands: list[list[str]] = [
        [sys.executable, str(TOOLKIT / "validate_skill.py"), str(SKILL_DIR)],
    ]
    if (SKILL_DIR / "evals").is_dir():
        commands.append([sys.executable, str(TOOLKIT / "validate_evals.py"), str(SKILL_DIR)])

    if PACKAGE.is_file():
        commands.append([sys.executable, str(PACKAGE), str(SKILL_DIR), "--dry-run"])

    if AUDIT.is_file():
        commands.append([sys.executable, str(AUDIT), str(SKILL_DIR)])

    exit_code = 0
    for command in commands:
        exit_code = _run(command) or exit_code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
