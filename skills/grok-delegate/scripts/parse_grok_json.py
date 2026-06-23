#!/usr/bin/env python3
"""Parse grok --output-format json stdout for shell pipelines."""

from __future__ import annotations

import json
import sys


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print("error: empty stdin", file=sys.stderr)
        return 1

    # Grok may log errors to stderr; stdin should be one JSON object.
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"error: invalid json: {exc}", file=sys.stderr)
        return 1

    for key in ("sessionId", "stopReason", "text"):
        value = payload.get(key, "")
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())