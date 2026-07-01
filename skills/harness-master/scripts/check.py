#!/usr/bin/env python3
"""Validate this skill's SKILL.md and eval manifests."""

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


def _package_script(toolkit: Path) -> Path | None:
    bundled = toolkit / "package.py"
    if bundled.is_file():
        return bundled
    if _portable_ci():
        print("PORTABLE_CI requires bundled scripts/asset_toolkit/package.py", file=sys.stderr)
        raise SystemExit(1)
    repo_script = SKILL_DIR.parent / "skill-creator" / "scripts" / "package.py"
    return repo_script if repo_script.is_file() else None


def _audit_script() -> Path | None:
    if _portable_ci():
        return None
    audit_script = SKILL_DIR.parent / "skill-creator" / "scripts" / "audit.py"
    return audit_script if audit_script.is_file() else None


def _run(command: list[str]) -> int:
    return subprocess.run(command, check=False).returncode


def main() -> int:
    toolkit = _toolkit_path()
    commands: list[list[str]] = [
        [sys.executable, str(toolkit / "validate_skill.py"), str(SKILL_DIR)],
    ]
    if (SKILL_DIR / "evals").is_dir():
        commands.append([sys.executable, str(toolkit / "validate_evals.py"), str(SKILL_DIR)])

    package_script = _package_script(toolkit)
    if package_script is not None:
        commands.append([sys.executable, str(package_script), str(SKILL_DIR), "--dry-run"])

    audit_script = _audit_script()
    if audit_script is not None:
        commands.append([sys.executable, str(audit_script), str(SKILL_DIR)])

    # Run discovery parity (inventory + hook) as part of harness-master checks
    disc_parity = SKILL_DIR / "scripts" / "discovery" / "parity_check.py"
    if disc_parity.is_file():
        commands.append([sys.executable, str(disc_parity)])

    exit_code = 0
    for command in commands:
        exit_code = _run(command) or exit_code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
