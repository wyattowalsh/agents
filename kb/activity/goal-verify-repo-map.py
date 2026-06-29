#!/usr/bin/env python3
"""Repo-map primary-table sourcing check for goal-verify.sh."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


def main() -> int:
    tree = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    print(f"verification_tree: {tree}")

    repo_map = Path("kb/indexes/repo-map.md").read_text()
    paths: list[tuple[str, str]] = []
    in_primary = False
    for line in repo_map.splitlines():
        if line.startswith("| Path |"):
            in_primary = True
            continue
        if in_primary:
            if line.startswith("| `"):
                match = re.match(r"\| `([^`]+)` \|", line)
                if match:
                    paths.append(("repo", match.group(1)))
            elif line.startswith("| External upstream docs |"):
                paths.append(("external", "External upstream docs"))
            elif paths and not line.startswith("|"):
                break

    raw_text = "\n".join(p.read_text(errors="ignore") for p in Path("kb/raw").rglob("*.md"))
    missing: list[str] = []
    for kind, path in paths:
        if kind == "repo":
            if path not in raw_text and path != "kb/":
                missing.append(path)
        elif "external-primary-source-map" not in raw_text:
            missing.append(path)

    print(f"primary_table_rows: {len(paths)}")
    print(f"missing: {len(missing)}")
    for item in missing:
        print(f"  MISSING: {item}")
    print("PASS" if not missing else "FAIL")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())