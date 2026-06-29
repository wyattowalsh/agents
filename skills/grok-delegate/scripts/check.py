#!/usr/bin/env python3
"""Validate grok-delegate skill assets."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent


def _toolkit_path() -> Path:
    bundled = SKILL_DIR / "scripts" / "asset_toolkit" / "validate_skill.py"
    if bundled.is_file():
        return SKILL_DIR / "scripts" / "asset_toolkit"
    return SKILL_DIR.parent / "skill-creator" / "scripts" / "asset_toolkit"


def _smoke_parse_grok_json() -> int:
    parser = SKILL_DIR / "scripts" / "parse_grok_json.py"
    payload = '{"sessionId":"s1","stopReason":"EndTurn","text":"ok"}'
    result = subprocess.run(
        [sys.executable, str(parser)],
        input=payload,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        print(result.stderr or result.stdout, file=sys.stderr)
        return result.returncode
    expected = {"sessionId=s1", "stopReason=EndTurn", "text=ok"}
    lines = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    if not expected.issubset(lines):
        print(f"parse_grok_json smoke mismatch: {result.stdout!r}", file=sys.stderr)
        return 1
    return 0


def _smoke_doctor() -> int:
    doctor = SKILL_DIR / "scripts" / "doctor.py"
    result = subprocess.run(
        [sys.executable, str(doctor), "--format", "json"],
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
    if "grok-binary" not in names:
        print(f"doctor smoke missing grok-binary check: {names!r}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    toolkit = _toolkit_path()
    commands: list[list[str]] = [
        [sys.executable, str(toolkit / "validate_skill.py"), str(SKILL_DIR)],
    ]
    if (SKILL_DIR / "evals").is_dir():
        commands.append([sys.executable, str(toolkit / "validate_evals.py"), str(SKILL_DIR)])

    audit_script = SKILL_DIR.parent / "skill-creator" / "scripts" / "audit.py"
    if audit_script.is_file():
        commands.append([sys.executable, str(audit_script), str(SKILL_DIR)])

    exit_code = _smoke_parse_grok_json() or _smoke_doctor()
    for command in commands:
        exit_code = subprocess.run(command, check=False).returncode or exit_code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())