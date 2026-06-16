#!/usr/bin/env python3
"""Scan MCP registry and repo mcp/ packages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from _paths import default_repo_root
from schemas import write_json


def scan_mcp(*, repo_root: Path) -> dict[str, Any]:
    present: list[str] = []
    gaps: list[str] = []

    registry_path = repo_root / "config" / "mcp-registry.json"
    if registry_path.is_file():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        servers = registry.get("servers", {})
        if isinstance(servers, dict):
            for name, spec in servers.items():
                if not isinstance(spec, dict) or not spec.get("enabled", True):
                    continue
                present.append(str(name))
                if not spec.get("command") and not spec.get("args") and not spec.get("url"):
                    gaps.append(str(name))

    mcp_dir = repo_root / "mcp"
    if mcp_dir.is_dir():
        for child in sorted(mcp_dir.iterdir()):
            if child.is_dir() and (child / "server.py").is_file() and child.name not in present:
                present.append(child.name)

    return {
        "version": 1,
        "present": sorted(set(present)),
        "gaps": gaps,
        "blind_spots": ["ui-only-mcp-connectors"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan MCP surfaces")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args(argv)

    repo_root = args.repo_root or default_repo_root()
    result = scan_mcp(repo_root=repo_root)

    if args.output:
        write_json(args.output, result)
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())