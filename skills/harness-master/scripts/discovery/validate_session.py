#!/usr/bin/env python3
"""Validate discovery session artifacts against JSON contracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from schemas import (
    validate_gap_report,
    validate_hook_scan,
    validate_scout_artifact,
    validate_wave_manifest,
)


def validate_file(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid json: {exc}"]

    if "domains" in data and "generated_at" in data:
        return validate_gap_report(data)
    if "expected_count" in data and "tasks" in data:
        return validate_wave_manifest(data)
    if "task_id" in data and "role" in data:
        return validate_scout_artifact(data)
    if "version" in data and "registry" in data:
        return validate_hook_scan(data)
    return [f"unknown artifact shape: {path}"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate discovery session JSON")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args(argv)

    had_errors = False
    for path in args.paths:
        errors = validate_file(path)
        if errors:
            had_errors = True
            print(json.dumps({"path": str(path), "errors": errors}, indent=2), file=sys.stderr)
        else:
            print(json.dumps({"path": str(path), "ok": True}))

    return 1 if had_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
