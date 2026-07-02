#!/usr/bin/env python3
"""Report per-harness, per-event spawn counts from ``config/hook-registry.json``.

Baseline tool for the ``fleet-hooks-performance`` OpenSpec program (W1/G0).
Every enabled registry row that targets a harness is one process spawn under
the ``legacy`` performance tier (the default): this script counts those rows
grouped by ``(harness, logical_event)`` so later waves can measure the
before/after spawn-count reduction from bundling (G2) and dedupe (G4).

Usage:
    uv run python scripts/hooks/hook_perf_inventory.py [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from wagents.hooks.render import prepare_hooks_for_render

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "config" / "hook-registry.json"


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_dispatcher_backed(hook: dict[str, Any]) -> bool:
    command = str(hook.get("command") or "")
    return any(token in command for token in ("wagents-hook.py", "run-wagents-hook", "{hook_runner}"))


def spawn_inventory(registry: dict[str, Any]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Return ``{harness: {logical_event: [row summaries]}}`` for enabled hooks."""
    inventory: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for hook in registry.get("hooks", []):
        if not isinstance(hook, dict) or not hook.get("command"):
            continue
        event = str(hook.get("logical_event") or "unknown")
        for harness in hook.get("harnesses", []) or []:
            inventory[str(harness)][event].append({
                "id": hook.get("id"),
                "logical_policy": hook.get("logical_policy"),
                "mode": hook.get("mode"),
                "bundle_group": hook.get("bundle_group"),
                "dispatcher_backed": _is_dispatcher_backed(hook),
                "timeout": hook.get("timeout"),
            })
    return {harness: dict(events) for harness, events in inventory.items()}


def spawn_inventory_tier(
    registry: dict[str, Any],
    *,
    tier: str,
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    inventory: dict[str, dict[str, list[dict[str, Any]]]] = {}
    harnesses = sorted({h for row in registry.get("hooks", []) for h in row.get("harnesses", []) or []})
    for harness in harnesses:
        events: dict[str, list[dict[str, Any]]] = {}
        for hook in prepare_hooks_for_render(registry, harness, perf_tier=tier):
            event = str(hook.get("logical_event") or "unknown")
            events.setdefault(event, []).append({
                "id": hook.get("id"),
                "logical_policy": hook.get("logical_policy"),
                "mode": hook.get("mode"),
                "bundle_group": hook.get("bundle_group"),
                "dispatcher_backed": _is_dispatcher_backed(hook),
                "timeout": hook.get("timeout"),
            })
        inventory[harness] = events
    return inventory


def summarize(inventory: dict[str, dict[str, list[dict[str, Any]]]]) -> dict[str, Any]:
    total_spawns = 0
    per_harness: dict[str, Any] = {}
    for harness, events in inventory.items():
        harness_total = sum(len(rows) for rows in events.values())
        total_spawns += harness_total
        per_harness[harness] = {
            "total_spawns": harness_total,
            "events": {event: len(rows) for event, rows in sorted(events.items())},
            "max_spawns_single_event": max((len(rows) for rows in events.values()), default=0),
        }
    return {
        "total_spawns": total_spawns,
        "harness_count": len(inventory),
        "harnesses": dict(sorted(per_harness.items())),
    }


def render_text(summary: dict[str, Any]) -> str:
    lines = [f"Total enabled dispatcher rows (spawns under legacy tier): {summary['total_spawns']}", ""]
    for harness, data in summary["harnesses"].items():
        lines.append(f"{harness}: {data['total_spawns']} spawns across {len(data['events'])} logical events")
        for event, count in sorted(data["events"].items(), key=lambda item: -item[1]):
            lines.append(f"  - {event}: {count}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument("--tier", choices=["legacy", "g1", "bundle"], default="legacy")
    args = parser.parse_args(argv)

    registry = load_registry(args.registry)
    inventory = spawn_inventory(registry) if args.tier == "legacy" else spawn_inventory_tier(registry, tier=args.tier)
    summary = summarize(inventory)

    if args.json:
        json.dump({"summary": summary, "inventory": inventory}, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(render_text(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
