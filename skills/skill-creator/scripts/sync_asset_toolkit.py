#!/usr/bin/env python3
"""Sync portable asset_toolkit modules into skill scripts/asset_toolkit/."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
SKILLS_DIR = REPO_ROOT / "skills"

MODULES = (
    "__init__.py",
    "_shared.py",
    "common.py",
    "package.py",
    "validate_skill.py",
    "validate_evals.py",
    "validate_hooks.py",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source(module: str) -> Path:
    if module in {"_shared.py", "package.py"}:
        return SCRIPT_DIR / module
    return SCRIPT_DIR / "asset_toolkit" / module


def _skill_dirs(skill_ids: list[str] | None) -> list[Path]:
    if skill_ids:
        return [SKILLS_DIR / sid for sid in skill_ids if (SKILLS_DIR / sid / "SKILL.md").is_file()]
    return sorted(p for p in SKILLS_DIR.iterdir() if (p / "SKILL.md").is_file())


def _mismatches(skill_dirs: list[Path]) -> list[str]:
    issues: list[str] = []
    for skill_dir in skill_dirs:
        dest_dir = skill_dir / "scripts" / "asset_toolkit"
        for module in MODULES:
            src = _source(module)
            dest = dest_dir / module
            if not src.is_file():
                issues.append(f"missing source module: {src}")
                continue
            if not dest.is_file():
                issues.append(f"{skill_dir.name}: missing scripts/asset_toolkit/{module}")
            elif _sha256(dest) != _sha256(src):
                issues.append(f"{skill_dir.name}: stale scripts/asset_toolkit/{module}")
    return issues


def sync_skill(skill_dir: Path) -> None:
    dest_dir = skill_dir / "scripts" / "asset_toolkit"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for module in MODULES:
        src = _source(module)
        dest = dest_dir / module
        if src.resolve() == dest.resolve():
            continue
        shutil.copy2(src, dest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync bundled asset_toolkit into skills")
    parser.add_argument("--skill-ids", nargs="*", default=None)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    skill_dirs = _skill_dirs(args.skill_ids)
    if args.check or not args.apply:
        mismatches = _mismatches(skill_dirs)
        if mismatches:
            for issue in mismatches:
                print(issue, file=sys.stderr)
            return 1
        print(f"OK: {len(skill_dirs)} skills toolkit-synced")
        return 0
    for skill_dir in skill_dirs:
        sync_skill(skill_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
