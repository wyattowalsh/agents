"""Tests for canonical MCPHub endpoint projection."""

from __future__ import annotations

import json
from pathlib import Path

from wagents.mcphub.endpoints import (
    mcphub_endpoint_specs,
    mcphub_smart_routing_enabled,
    render_mcphub_stdio_server,
)


def test_smart_routing_endpoints_omitted_when_disabled():
    repo_root = Path(__file__).resolve().parents[1]
    registry = json.loads((repo_root / "config" / "mcp-registry.json").read_text(encoding="utf-8"))

    assert mcphub_smart_routing_enabled(registry) is False
    specs = mcphub_endpoint_specs(registry, "codex")
    assert all(spec["kind"] != "smart" for spec in specs)


def test_codex_bounded_profile_includes_configured_groups_and_disabled_servers():
    repo_root = Path(__file__).resolve().parents[1]
    registry = json.loads((repo_root / "config" / "mcp-registry.json").read_text(encoding="utf-8"))
    specs = mcphub_endpoint_specs(registry, "codex")

    kinds = {spec["kind"] for spec in specs}
    assert kinds == {"group", "server"}

    group_names = {spec["group"] for spec in specs if spec["kind"] == "group"}
    assert group_names == {"harness", "candidate-corpus", "nlm", "things"}
    projectable_servers = {name for name, entry in registry["servers"].items() if entry.get("group_only") is not True}
    assert {spec["server"] for spec in specs if spec["kind"] == "server"} == projectable_servers
    assert all(spec["enabled"] is False for spec in specs if spec["kind"] == "server")

    things = next(spec for spec in specs if spec.get("group") == "things")
    assert things["url"] == "http://127.0.0.1:46683/mcp/things"
    assert things["enabled"] is False
    assert things["group_id"] == "3b94a096-b95f-586c-b2e7-e69ed177eb5a"
    assert things["approval_policy"] == {
        "default": "per-call",
        "read_only_risk": "never",
        "otherwise": "per-call",
    }


def test_remote_stdio_projection_uses_portable_path_without_token_env():
    repo_root = Path(__file__).resolve().parents[1]
    registry = json.loads((repo_root / "config" / "mcp-registry.json").read_text(encoding="utf-8"))

    rendered = render_mcphub_stdio_server(registry, "http://127.0.0.1:46683/mcp/harness")

    assert rendered["command"] == "${REPO_ROOT}/scripts/mcphub/remote-stdio.sh"
    assert not rendered["command"].startswith("$/")
    assert "env" not in rendered
