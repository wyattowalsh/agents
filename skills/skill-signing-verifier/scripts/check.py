#!/usr/bin/env python3
"""Portable validator for skill-signing-verifier scaffold."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent


def _toolkit_path() -> Path:
    return SKILL_DIR.parent / "skill-creator" / "scripts" / "asset_toolkit"


def main() -> int:
    toolkit = _toolkit_path()
    exit_code = subprocess.run(
        [sys.executable, str(toolkit / "validate_skill.py"), str(SKILL_DIR)],
        check=False,
    ).returncode
    if (SKILL_DIR / "evals").is_dir():
        exit_code = subprocess.run(
            [sys.executable, str(toolkit / "validate_evals.py"), str(SKILL_DIR)],
            check=False,
        ).returncode or exit_code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
