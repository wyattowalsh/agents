#!/usr/bin/env python3
"""Invoke harness-master discover_surfaces.py and merge summary."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from _paths import default_repo_root, skill_dir
from schemas import write_json

DEFAULT_HARNESSES = [
    "claude-code",
    "codex",
    "cursor",
    "gemini-cli",
    "github-copilot",
    "opencode",
    "antigravity",
]


def discover_surfaces_script() -> Path:
    return skill_dir().parent / "harness-master" / "scripts" / "discover_surfaces.py"


def run_surfaces(
    *,
    repo_root: Path,
    harnesses: list[str],
    level: str,
) -> dict[str, Any]:
    script = discover_surfaces_script()
    if not script.is_file():
        return {
            "version": 1,
            "error": f"missing script: {script}",
            "blind_spots": ["harness-master-script-missing"],
            "missing_surfaces": [],
            "summary": {},
        }

    cmd = [
        sys.executable,
        str(script),
        "--repo-root",
        str(repo_root),
        "--level",
        level,
        "--format",
        "json",
    ]
    for harness in harnesses:
        cmd.extend(["--harness", harness])

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return {
            "version": 1,
            "error": proc.stderr.strip() or "discover_surfaces failed",
            "blind_spots": [],
            "missing_surfaces": [],
            "summary": {},
        }

    payload = json.loads(proc.stdout)
    surfaces = payload.get("surfaces", [])
    blind_spots = [s.get("label", "") for s in surfaces if s.get("status") == "blind-spot"]
    missing = [s.get("label", "") for s in surfaces if s.get("status") == "missing"]
    return {
        "version": 1,
        "summary": payload.get("summary", {}),
        "blind_spots": [b for b in blind_spots if b],
        "missing_surfaces": [m for m in missing if m],
        "surface_count": len(surfaces),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan harness surfaces")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--harness", action="append", default=[])
    parser.add_argument("--level", default="both", choices=("project", "global", "both"))
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args(argv)

    repo_root = args.repo_root or default_repo_root()
    harnesses = args.harness or DEFAULT_HARNESSES
    result = run_surfaces(repo_root=repo_root, harnesses=harnesses, level=args.level)

    if args.output:
        write_json(args.output, result)
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())