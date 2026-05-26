#!/usr/bin/env python3
"""Read-only scaffold health summary for existing projects."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]


def run_preflight(path: str) -> dict:
    script = BASE_DIR / "scripts" / "preflight.py"
    result = subprocess.run(
        [sys.executable, str(script), "--path", path, "--format", "json"],
        check=False,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run read-only project doctor checks.")
    parser.add_argument("--path", default=".")
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args()

    preflight = run_preflight(args.path)
    checks = {
        "has_readme": Path(args.path, "README.md").exists(),
        "has_agents_md": Path(args.path, "AGENTS.md").exists(),
        "has_ci": Path(args.path, ".github", "workflows").exists(),
        "has_quality_runner": Path(args.path, "justfile").exists() or Path(args.path, "Makefile").exists(),
    }
    gaps = [name for name, ok in checks.items() if not ok]
    print(json.dumps({"ok": True, "preflight": preflight, "checks": checks, "gaps": gaps}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
