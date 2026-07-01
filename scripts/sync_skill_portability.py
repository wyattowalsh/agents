#!/usr/bin/env python3
"""Sync bundled asset_toolkit into skill directories (portability wrapper)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _default_skill_ids() -> list[str]:
    import sys
    sys.path.insert(0, str(REPO_ROOT / 'tests'))
    from tests.skill_portability_ids import PLAN_SKILL_IDS
    return list(PLAN_SKILL_IDS)


SYNC = REPO_ROOT / "skills" / "skill-creator" / "scripts" / "sync_asset_toolkit.py"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync portable asset_toolkit into skills")
    parser.add_argument("--skill-ids", nargs="*", default=None)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    cmd = [sys.executable, str(SYNC)]
    skill_ids = args.skill_ids or (_default_skill_ids() if args.check else None)
    if skill_ids:
        cmd.extend(["--skill-ids", *skill_ids])
    if args.apply:
        cmd.append("--apply")
    if args.check:
        cmd.append("--check")
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
