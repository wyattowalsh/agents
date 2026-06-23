#!/usr/bin/env python3
"""Grok PreToolUse wrapper for Plannotator plan review.

Runs the plannotator CLI, parses hook JSON output, and maps Claude/Codex
``block`` decisions to Grok ``deny``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any


def _plannotator_bin() -> str:
    return os.environ.get("PLANNOTATOR_BIN", os.path.expanduser("~/.local/bin/plannotator"))


def _map_decision(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return payload
    if payload.get("decision") != "block":
        return payload
    mapped = dict(payload)
    mapped["decision"] = "deny"
    return mapped


def main() -> int:
    plannotator = _plannotator_bin()
    if not os.access(plannotator, os.X_OK):
        print(f"plannotator binary not found at {plannotator}", file=sys.stderr)
        return 0

    result = subprocess.run(
        [plannotator],
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout or result.stderr or "").strip()
    if not output:
        return result.returncode

    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        sys.stdout.write(output)
        if not output.endswith("\n"):
            sys.stdout.write("\n")
        return result.returncode

    mapped = _map_decision(payload)
    json.dump(mapped, sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
