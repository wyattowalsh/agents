#!/usr/bin/env python3
"""Build a maintainer plan from skills sync dry-run JSON."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

PLAN_STEPS = [
    {"id": "validate", "action": "Run repo validate gate", "required": True},
    {"id": "dry-run", "action": "Run skills sync dry-run JSON report", "required": True},
    {"id": "review-gaps", "action": "Inspect missing, unresolved, and skipped rows per harness", "required": True},
    {
        "id": "optional-smoke",
        "command": "INSTALL_SMOKE=1 uv run python skills/cross-agent-install-smoke/scripts/local_smoke.py",
        "required": False,
        "gate": "INSTALL_SMOKE=1",
    },
    {"id": "apply-gate", "action": "Human approval required before wagents skills sync --apply", "required": False},
]


def _run_dry_run(harness: str | None) -> dict[str, Any]:
    command = ["uv", "run", "wagents", "skills", "sync", "--dry-run", "--format", "json"]
    if harness:
        command.extend(["--agent", harness])
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if result.returncode not in (0, 1):
        return {"ok": False, "error": result.stderr or result.stdout}
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"invalid JSON: {exc}"}
    return payload


def _summarize_agents(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in payload.get("agents", []):
        if not isinstance(row, dict):
            continue
        rows.append({
            "agent": row.get("agent"),
            "missing_count": len(row.get("missing") or []),
            "unresolved_count": len(row.get("unresolved") or []),
            "skipped_count": len(row.get("skipped") or []),
        })
    return rows


def build_plan(harness: str | None = None) -> dict[str, Any]:
    dry_run = _run_dry_run(harness)
    return {
        "ok": dry_run.get("ok", False) if isinstance(dry_run, dict) else False,
        "harness_filter": harness,
        "steps": PLAN_STEPS,
        "dry_run": {
            "mode": dry_run.get("mode") if isinstance(dry_run, dict) else None,
            "inventory_count": dry_run.get("inventory_count") if isinstance(dry_run, dict) else None,
            "agent_summary": _summarize_agents(dry_run) if isinstance(dry_run, dict) else [],
            "top_level_ok": dry_run.get("ok") if isinstance(dry_run, dict) else False,
        },
        "related": [
            "skills/cross-agent-install-smoke/SKILL.md",
            "docs/runbooks/install-smoke.md",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Skills sync dry-run planner")
    parser.add_argument("--harness", default=None, help="Filter dry-run to one harness adapter")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--self-test", action="store_true", help="Validate plan shape without wagents CLI")
    args = parser.parse_args(argv)

    if args.self_test:
        payload = {"ok": True, "steps": PLAN_STEPS, "self_test": True}
        print(json.dumps(payload, indent=2) if args.format == "json" else f"steps={len(PLAN_STEPS)}")
        return 0

    payload = build_plan(args.harness)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print("Skills sync dry-run plan:")
        for step in PLAN_STEPS:
            label = step.get("command") or step.get("action")
            print(f"  - {step['id']}: {label}")
        summary = payload.get("dry_run", {}).get("agent_summary", [])
        for row in summary:
            print(f"  {row.get('agent')}: missing={row.get('missing_count')} unresolved={row.get('unresolved_count')}")
    return 0 if payload.get("ok") or payload.get("dry_run", {}).get("top_level_ok") is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
