#!/usr/bin/env python3
"""Validate this skill's SKILL.md and eval manifests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent


def _toolkit_path() -> Path:
    bundled = SKILL_DIR / "scripts" / "asset_toolkit" / "validate_skill.py"
    if bundled.is_file():
        return SKILL_DIR / "scripts" / "asset_toolkit"
    repo_toolkit = SKILL_DIR.parent / "skill-creator" / "scripts" / "asset_toolkit"
    return repo_toolkit


def _run(command: list[str]) -> int:
    return subprocess.run(command, check=False).returncode


def main() -> int:
    toolkit = _toolkit_path()
    commands: list[list[str]] = [
        [sys.executable, str(toolkit / "validate_skill.py"), str(SKILL_DIR)],
    ]
    if (SKILL_DIR / "evals").is_dir():
        commands.append([sys.executable, str(toolkit / "validate_evals.py"), str(SKILL_DIR)])

    package_script = SKILL_DIR / "scripts" / "package.py"
    if not package_script.is_file():
        package_script = SKILL_DIR.parent / "skill-creator" / "scripts" / "package.py"
    if package_script.is_file():
        commands.append([sys.executable, str(package_script), str(SKILL_DIR), "--dry-run"])

    audit_script = SKILL_DIR.parent / "skill-creator" / "scripts" / "audit.py"
    if audit_script.is_file():
        commands.append([sys.executable, str(audit_script), str(SKILL_DIR)])

    scripts_dir = SKILL_DIR / "scripts"
    commands.extend(
        [
            [sys.executable, str(scripts_dir / "validate_catalog.py"), "--format", "json"],
            [sys.executable, str(scripts_dir / "preferences.py"), "validate", "--format", "json"],
        ]
    )
    openspec_cli = scripts_dir / "openspec_cli.py"
    if (SKILL_DIR.parents[1] / "openspec").is_dir() and openspec_cli.is_file():
        commands.append([sys.executable, str(openspec_cli), "validate"])

    exit_code = 0
    for command in commands:
        exit_code = _run(command) or exit_code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
