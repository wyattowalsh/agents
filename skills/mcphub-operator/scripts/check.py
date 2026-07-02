#!/usr/bin/env python3
"""Validate mcphub-operator skill assets."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_DIR.parent.parent


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


def _smoke_doctor() -> int:
    doctor = SKILL_DIR / "scripts" / "doctor.py"
    result = subprocess.run(
        [sys.executable, str(doctor), "--format", "json", "--cwd", str(REPO_ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        print(result.stderr or result.stdout, file=sys.stderr)
        return result.returncode or 1
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"doctor smoke invalid JSON: {result.stdout!r}", file=sys.stderr)
        return 1
    if "ok" not in payload or "checks" not in payload:
        print(f"doctor smoke missing keys: {payload!r}", file=sys.stderr)
        return 1
    names = {check.get("name") for check in payload["checks"] if isinstance(check, dict)}
    required = {
        "repo-root",
        "mcphub-enabled",
        "smart-routing-off",
        "settings-parity",
        "chatgpt-tunnel-only",
    }
    missing = required - names
    if missing:
        print(f"doctor smoke missing checks: {sorted(missing)!r}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    toolkit = _toolkit_path()
    commands: list[list[str]] = [
        [sys.executable, str(toolkit / "validate_skill.py"), str(SKILL_DIR)],
    ]
    if (SKILL_DIR / "evals").is_dir():
        commands.append([sys.executable, str(toolkit / "validate_evals.py"), str(SKILL_DIR)])

    exit_code = _smoke_doctor()
    for command in commands:
        exit_code = _run(command) or exit_code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())