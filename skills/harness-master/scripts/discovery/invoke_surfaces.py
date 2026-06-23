#!/usr/bin/env python3
"""Invoke harness-master discover_surfaces.py and merge summary."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from _paths import default_repo_root, harness_master_dir
from schemas import write_json

DEFAULT_HARNESSES = [
    "claude-code",
    "codex",
    "cursor",
    "gemini-cli",
    "github-copilot",
    "grok-build",
    "opencode",
    "antigravity",
]


def discover_surfaces_script() -> Path:
    return harness_master_dir() / "scripts" / "discover_surfaces.py"


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
            "hooks_surfaces": {"present": [], "missing": [], "blind_spots": []},
        }

    cmd = [
        sys.executable,
        str(script),
        "--repo-root",
        str(repo_root),
        "--level",
        level,
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
            "hooks_surfaces": {"present": [], "missing": [], "blind_spots": []},
        }

    payload = json.loads(proc.stdout)
    surfaces = payload.get("surfaces", [])
    blind_spots = [s.get("label", "") for s in surfaces if s.get("status") == "blind-spot"]
    missing = [s.get("label", "") for s in surfaces if s.get("status") == "missing"]
    # hooks_surfaces: filter surfaces where kind==hooks (embedded or dedicated) for present/missing/blind_spots
    hook_surfs = [s for s in surfaces if s.get("kind") == "hooks"]
    hook_present = [s.get("label", "") for s in hook_surfs if s.get("status") == "present"]
    hook_missing = [s.get("label", "") for s in hook_surfs if s.get("status") == "missing"]
    hook_blind = [s.get("label", "") for s in hook_surfs if s.get("status") == "blind-spot"]
    return {
        "version": 1,
        "summary": payload.get("summary", {}),
        "blind_spots": [b for b in blind_spots if b],
        "missing_surfaces": [m for m in missing if m],
        "surface_count": len(surfaces),
        "hooks_surfaces": {
            "present": [p for p in hook_present if p],
            "missing": [m for m in hook_missing if m],
            "blind_spots": [b for b in hook_blind if b],
        },
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
