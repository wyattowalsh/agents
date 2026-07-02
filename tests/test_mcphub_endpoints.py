"""Tests for canonical MCPHub endpoint projection."""

from __future__ import annotations

import json
from pathlib import Path

from wagents.mcphub.endpoints import mcphub_endpoint_specs, mcphub_smart_routing_enabled


def test_smart_routing_endpoints_omitted_when_disabled():
    repo_root = Path(__file__).resolve().parents[1]
    registry = json.loads((repo_root / "config" / "mcp-registry.json").read_text(encoding="utf-8"))

    assert mcphub_smart_routing_enabled(registry) is False
    specs = mcphub_endpoint_specs(registry, "codex")
    assert all(spec["kind"] != "smart" for spec in specs)


def test_codex_bounded_profile_includes_harness_and_disabled_servers():
    repo_root = Path(__file__).resolve().parents[1]
    registry = json.loads((repo_root / "config" / "mcp-registry.json").read_text(encoding="utf-8"))
    specs = mcphub_endpoint_specs(registry, "codex")

    kinds = {spec["kind"] for spec in specs}
    assert kinds == {"group", "server"}

    group_names = {spec["group"] for spec in specs if spec["kind"] == "group"}
    assert group_names == {"harness"}
    assert {spec["server"] for spec in specs if spec["kind"] == "server"} == set(registry["servers"])
    assert all(spec["enabled"] is False for spec in specs if spec["kind"] == "server")
