#!/usr/bin/env python3
"""Scan local skill inventory via skill-router index subprocess."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from _paths import default_repo_root, skill_dir
from schemas import write_json


def skill_router_script() -> Path:
    return skill_dir().parent / "skill-router" / "scripts" / "skill_index.py"


def collect_inventory(
    *,
    repo_root: Path,
    home: Path | None = None,
    source: str = "all",
) -> dict[str, Any]:
    script = skill_router_script()
    if not script.is_file():
        msg = f"skill-router index not found: {script}"
        raise FileNotFoundError(msg)

    cmd = [
        sys.executable,
        str(script),
        "index",
        "--repo-root",
        str(repo_root),
        "--format",
        "json",
        "--source",
        source,
    ]
    if home is not None:
        cmd.extend(["--home", str(home)])

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        msg = proc.stderr.strip() or proc.stdout.strip() or "skill index failed"
        raise RuntimeError(msg)

    payload = json.loads(proc.stdout)
    skills = payload.get("skills", payload.get("records", []))
    if not isinstance(skills, list):
        skills = payload if isinstance(payload, list) else []

    repo_skills = [s for s in skills if isinstance(s, dict) and s.get("source") == "repo"]
    installed = [s for s in skills if isinstance(s, dict) and s.get("source") != "repo"]

    return {
        "version": 1,
        "repo_root": str(repo_root),
        "total": len(skills),
        "repo_count": len(repo_skills),
        "installed_count": len(installed),
        "skills": skills,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan local skill inventory")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--home", type=Path, default=None)
    parser.add_argument("--source", default="all")
    parser.add_argument("-o", "--output", type=Path, default=None)
    parser.add_argument("--format", choices=("json",), default="json")
    args = parser.parse_args(argv)

    repo_root = args.repo_root or default_repo_root()
    result = collect_inventory(repo_root=repo_root, home=args.home, source=args.source)

    if args.output:
        write_json(args.output, result)
    else:
        print(json.dumps(result, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
