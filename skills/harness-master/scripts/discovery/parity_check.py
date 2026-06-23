#!/usr/bin/env python3
"""Compare inventory_scan vs skill-router index repo skill counts."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from _paths import default_repo_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Repo skill-count parity guard")
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)

    repo_root = args.repo_root or default_repo_root()
    scripts = [
        repo_root / "scripts" / "check_discovery_parity.py",
        repo_root / "scripts" / "check_hook_discovery_parity.py",
    ]
    for script in scripts:
        if not script.is_file():
            print(f"Error: parity script not found: {script}", file=sys.stderr)
            return 1

    for script in scripts:
        proc = subprocess.run(
            [sys.executable, str(script), "--repo-root", str(repo_root)],
            check=False,
        )
        if proc.returncode != 0:
            return int(proc.returncode or 1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
