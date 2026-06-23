#!/usr/bin/env python3
"""Compare harness-master discovery inventory_scan vs skill-router index counts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()

    inv_script = args.repo_root / "skills" / "harness-master" / "scripts" / "discovery" / "inventory_scan.py"
    index_script = args.repo_root / "skills" / "skill-router" / "scripts" / "skill_index.py"

    inv_proc = subprocess.run(
        [sys.executable, str(inv_script), "--repo-root", str(args.repo_root), "--source", "repo"],
        capture_output=True,
        text=True,
        check=False,
    )
    idx_proc = subprocess.run(
        [
            sys.executable,
            str(index_script),
            "index",
            "--repo-root",
            str(args.repo_root),
            "--format",
            "json",
            "--source",
            "repo",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if inv_proc.returncode != 0 or idx_proc.returncode != 0:
        print(inv_proc.stderr or idx_proc.stderr, file=sys.stderr)
        return 1

    inv = json.loads(inv_proc.stdout)
    idx = json.loads(idx_proc.stdout)
    inv_count = int(inv.get("repo_count", inv.get("total", 0)))
    idx_count = int(idx.get("count", 0))
    if inv_count != idx_count:
        print(f"parity mismatch: inventory_scan={inv_count} skill_index={idx_count}", file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, "repo_count": inv_count}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
