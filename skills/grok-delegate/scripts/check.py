#!/usr/bin/env python3
"""Validate grok-delegate skill assets."""

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


def _smoke_doctor() -> int:
    doctor = SKILL_DIR / "scripts" / "doctor.py"
    result = subprocess.run(
        [sys.executable, str(doctor), "--format", "json", "--cwd", str(SKILL_DIR.parent.parent)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode not in (0, 1):
        print(result.stdout or result.stderr, file=sys.stderr)
        return result.returncode
    try:
        import json

        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"doctor smoke: invalid JSON: {result.stdout!r}", file=sys.stderr)
        return 1
    required = {"ok", "summary", "checks"}
    if not required.issubset(payload):
        print(f"doctor smoke: missing keys: {payload!r}", file=sys.stderr)
        return 1
    if not payload["checks"] or payload["checks"][0]["name"] != "grok-binary":
        print(f"doctor smoke: unexpected checks: {payload['checks']!r}", file=sys.stderr)
        return 1
    return 0


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

    exit_code = _smoke_doctor()
    exit_code = _smoke_parse_grok_json() or exit_code
    for command in commands:
        exit_code = subprocess.run(command, check=False).returncode or exit_code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
