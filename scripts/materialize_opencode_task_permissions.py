#!/usr/bin/env python3
"""Materialize OpenCode task allowlists from config/agent-delegation-policy.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "agent-delegation-policy.json"
OVERLAY_PATH = ROOT / "config" / "opencode-agents.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _task_block(allows: list[str]) -> dict[str, str]:
    block: dict[str, str] = {"*": "deny"}
    for name in sorted(allows, key=lambda value: (value not in {"general", "explore"}, value)):
        block[name] = "allow"
    return block


def _apply_policy(overlay: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    by_name = {entry["name"]: entry for entry in overlay["agents"]}
    for delegator, spec in policy["delegators"].items():
        if delegator not in by_name:
            raise KeyError(f"delegator {delegator!r} missing from {OVERLAY_PATH}")
        permission = by_name[delegator].setdefault("permission", {})
        permission["task"] = _task_block(spec["allow"])
    return overlay


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write updated task permissions to config/opencode-agents.json",
    )
    args = parser.parse_args()

    policy = _load_json(POLICY_PATH)
    current = _load_json(OVERLAY_PATH)
    updated = _apply_policy(json.loads(json.dumps(current)), policy)
    rendered = json.dumps(updated, indent=2) + "\n"
    existing = OVERLAY_PATH.read_text(encoding="utf-8")

    if rendered == existing:
        print("opencode task permissions already match agent-delegation-policy.json")
        return 0

    if not args.apply:
        print(
            "config/opencode-agents.json task permissions drift from "
            "config/agent-delegation-policy.json; re-run with --apply",
            file=sys.stderr,
        )
        return 1

    OVERLAY_PATH.write_text(rendered, encoding="utf-8")
    print(f"updated task permissions in {OVERLAY_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())