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
    script = repo_root / "scripts" / "check_discovery_parity.py"
    if not script.is_file():
        print(f"Error: parity script not found: {script}", file=sys.stderr)
        return 1

    proc = subprocess.run(
        [sys.executable, str(script), "--repo-root", str(repo_root)],
        check=False,
    )
    return int(proc.returncode or 0)


if __name__ == "__main__":
    raise SystemExit(main())