#!/usr/bin/env python3
"""Render compact report JSON for new-project templates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_json(path: str | None) -> dict:
    if not path or path == "-":
        return json.load(sys.stdin)
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize new-project report data.")
    parser.add_argument("--input", default="-", help="Input JSON path, or '-' for stdin")
    parser.add_argument("--kind", choices=["blueprint", "preferences", "audit"], default="blueprint")
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args()

    data = load_json(args.input)
    summary = {
        "ok": data.get("ok", True),
        "kind": args.kind,
        "title": f"new-project {args.kind} report",
        "items": data.get("capabilities") or data.get("gaps") or data.get("categories") or [],
        "risks": data.get("risks") or data.get("risk_flags") or [],
        "approvals": data.get("approval_required", []),
        "source": data,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
