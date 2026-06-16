#!/usr/bin/env python3
"""Scan OpenCode and marketplace plugin entries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from _paths import default_repo_root
from schemas import write_json


def scan_plugins(*, repo_root: Path) -> dict[str, Any]:
    stale_latest: list[str] = []
    overlaps: list[str] = []
    plugins: list[str] = []

    opencode_path = repo_root / "opencode.json"
    if opencode_path.is_file():
        try:
            text = opencode_path.read_text(encoding="utf-8")
            payload = json.loads(text)
            for entry in payload.get("plugin", []):
                if isinstance(entry, str):
                    plugins.append(entry)
                    if entry.endswith("@latest"):
                        stale_latest.append(entry)
        except json.JSONDecodeError:
            overlaps.append("opencode.json:invalid-json")

    for manifest in (
        repo_root / ".claude-plugin" / "marketplace.json",
        repo_root / ".agents" / "plugins" / "marketplace.json",
    ):
        if manifest.is_file():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                plugins.extend(str(p) for p in data.get("plugins", []) if p)
            except json.JSONDecodeError:
                overlaps.append(f"{manifest.name}:invalid-json")

    return {
        "version": 1,
        "plugins": sorted(set(plugins)),
        "stale_latest": sorted(set(stale_latest)),
        "overlaps": overlaps,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan plugin surfaces")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args(argv)

    repo_root = args.repo_root or default_repo_root()
    result = scan_plugins(repo_root=repo_root)

    if args.output:
        write_json(args.output, result)
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())