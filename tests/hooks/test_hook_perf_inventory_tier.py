from __future__ import annotations

import json
from pathlib import Path

from scripts.hooks import hook_perf_inventory as hpi

REPO = Path(__file__).resolve().parents[2]


def test_bundle_tier_inventory_not_above_legacy():
    registry = json.loads((REPO / "config/hook-registry.json").read_text(encoding="utf-8"))
    legacy = hpi.summarize(hpi.spawn_inventory(registry))
    bundle = hpi.summarize(hpi.spawn_inventory_tier(registry, tier="bundle"))
    assert bundle["total_spawns"] <= legacy["total_spawns"]
