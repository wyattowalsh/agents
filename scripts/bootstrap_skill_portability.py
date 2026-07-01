#!/usr/bin/env python3
"""Bootstrap skill portability artifacts for PLAN_SKILL_IDS."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap skill portability")
    parser.add_argument("--apply", action="store_true", help="Sync toolkit and regenerate standard checks")
    args = parser.parse_args(argv)
    if not args.apply:
        print("Dry run: would sync toolkit for PLAN_SKILL_IDS and run generate_check --upgrade-standard --apply")
        return 0

    sys.path.insert(0, str(REPO / "tests"))
    from tests.skill_portability_ids import PLAN_SKILL_IDS

    sync = REPO / "skills" / "skill-creator" / "scripts" / "sync_asset_toolkit.py"
    gen = REPO / "skills" / "skill-creator" / "scripts" / "generate_check.py"
    rc = subprocess.call(
        [sys.executable, str(sync), "--skill-ids", *PLAN_SKILL_IDS, "--apply"],
        cwd=REPO,
    )
    return subprocess.call([sys.executable, str(gen), "--upgrade-standard", "--apply"], cwd=REPO) or rc


if __name__ == "__main__":
    raise SystemExit(main())
