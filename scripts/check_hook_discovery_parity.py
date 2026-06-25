#!/usr/bin/env python3
"""Parity guard: ensure every harness claiming 'hooks' in projection_surfaces
has corresponding entries in hook-surface-registry.json or a documented blind_spot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _tier_mismatches(
    harness_reg: dict,
    hook_map: dict[str, dict],
) -> list[str]:
    """Return failures when shared harness/hook ids disagree on support_tier."""
    harness_map = {
        str(h["id"]): h
        for h in harness_reg.get("harnesses", [])
        if isinstance(h, dict) and h.get("id")
    }
    failures: list[str] = []
    for hid, hook_entry in hook_map.items():
        harness_entry = harness_map.get(hid)
        if harness_entry is None:
            continue
        hook_tier = hook_entry.get("support_tier")
        harness_tier = harness_entry.get("support_tier")
        if hook_tier != harness_tier:
            failures.append(
                f"{hid}: hook-surface support_tier {hook_tier!r} != harness-surface {harness_tier!r}"
            )
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument(
        "--check-tiers",
        action="store_true",
        help="Also require matching support_tier for ids present in both registries",
    )
    args = parser.parse_args(argv)
    repo_root = args.repo_root or ROOT

    harness_path = repo_root / "config" / "harness-surface-registry.json"
    hook_path = repo_root / "config" / "hook-surface-registry.json"

    if not harness_path.is_file():
        print(f"Error: harness-surface-registry not found: {harness_path}", file=sys.stderr)
        return 1
    if not hook_path.is_file():
        print(f"Error: hook-surface-registry not found: {hook_path}", file=sys.stderr)
        return 1

    harness_reg = json.loads(harness_path.read_text(encoding="utf-8"))
    hook_reg = json.loads(hook_path.read_text(encoding="utf-8"))

    hook_map = {h["id"]: h for h in hook_reg.get("harnesses", []) if isinstance(h, dict) and "id" in h}

    failures: list[str] = []
    if args.check_tiers:
        failures.extend(_tier_mismatches(harness_reg, hook_map))

    for harness in harness_reg.get("harnesses", []):
        if not isinstance(harness, dict):
            continue
        proj = harness.get("projection_surfaces", [])
        if not isinstance(proj, list):
            proj = []
        if "hooks" not in proj:
            continue
        hid = str(harness.get("id", ""))
        entry = hook_map.get(hid)
        if not entry:
            failures.append(f"{hid}: no entry in hook-surface-registry")
            continue
        has_entries = bool(entry.get("hook_surfaces"))
        blind = entry.get("blind_spot")
        documented_blind = isinstance(blind, str) and blind.strip()
        if not has_entries and not documented_blind:
            failures.append(f"{hid}: no hook_surfaces entries and no documented blind_spot")
            continue

    if failures:
        for f in failures:
            print(f"hook discovery parity failure: {f}", file=sys.stderr)
        return 1

    checked = [h.get("id") for h in harness_reg.get("harnesses", []) if "hooks" in (h.get("projection_surfaces") or [])]
    print(json.dumps({"ok": True, "checked": checked}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
