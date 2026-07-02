#!/usr/bin/env python3
"""Portable validator for cross-agent-install-smoke."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent


def _portable_ci() -> bool:
    return os.environ.get("SKILL_PORTABLE_CI") == "1" or os.environ.get("PORTABLE_CI") == "1"


def _toolkit_path() -> Path:
    bundled = SKILL_DIR / "scripts" / "asset_toolkit" / "validate_skill.py"
    if bundled.is_file():
        return SKILL_DIR / "scripts" / "asset_toolkit"
    if _portable_ci():
        print("PORTABLE_CI requires bundled scripts/asset_toolkit", file=sys.stderr)
        raise SystemExit(1)
    return SKILL_DIR.parent / "skill-creator" / "scripts" / "asset_toolkit"


def _run(command: list[str]) -> int:
    return subprocess.run(command, check=False).returncode


def main() -> int:
    toolkit = _toolkit_path()
    exit_code = _run([sys.executable, str(toolkit / "validate_skill.py"), str(SKILL_DIR)])

    if (SKILL_DIR / "evals").is_dir():
        exit_code = _run([sys.executable, str(toolkit / "validate_evals.py"), str(SKILL_DIR)]) or exit_code

    exit_code = _run([sys.executable, str(SKILL_DIR / "scripts" / "dry_run.py"), "--agent", "codex"]) or exit_code

    if os.environ.get("INSTALL_SMOKE") == "1":
        exit_code = _run([sys.executable, str(SKILL_DIR / "scripts" / "local_smoke.py")]) or exit_code

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
