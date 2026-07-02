#!/usr/bin/env python3
"""Portable validator for skill-package-manifest-enricher."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent


def _toolkit_path() -> Path:
    bundled = SKILL_DIR / "scripts" / "asset_toolkit" / "validate_skill.py"
    if bundled.is_file():
        return SKILL_DIR / "scripts" / "asset_toolkit"
    return SKILL_DIR.parent / "skill-creator" / "scripts" / "asset_toolkit"


def _run(command: list[str]) -> int:
    return subprocess.run(command, check=False).returncode


def main() -> int:
    toolkit = _toolkit_path()
    exit_code = _run([sys.executable, str(toolkit / "validate_skill.py"), str(SKILL_DIR)])
    if (SKILL_DIR / "evals").is_dir():
        exit_code = _run([sys.executable, str(toolkit / "validate_evals.py"), str(SKILL_DIR)]) or exit_code
    return (
        _run(
            [
                sys.executable,
                str(SKILL_DIR / "scripts" / "enrich_manifest.py"),
                SKILL_DIR.name,
                "--dry-run",
            ]
        )
        or exit_code
    )


if __name__ == "__main__":
    raise SystemExit(main())
