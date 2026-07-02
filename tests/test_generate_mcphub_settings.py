"""Tests for MCPHub settings generation."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_mcphub_settings import generate_settings, serialize_settings
from scripts.mcphub.validate_settings import validate_settings


def test_generate_settings_matches_registry_servers_and_groups():
    repo_root = Path(__file__).resolve().parents[1]
    registry = json.loads((repo_root / "config" / "mcp-registry.json").read_text(encoding="utf-8"))
    settings = json.loads((repo_root / "mcp" / "mcphub" / "mcp_settings.json").read_text(encoding="utf-8"))

    generated = generate_settings(registry)

    assert set(generated["mcpServers"]) == set(registry["servers"])
    assert generated["systemConfig"]["smartRouting"]["enabled"] is False
    assert generated["systemConfig"]["toolResultCompression"] == {
        "enabled": False,
        "minTokens": 2000,
        "maxOutputTokens": 1200,
        "strategy": "auto",
    }

    registry_groups = registry["mcphub"]["groups"]
    assert set(generated["groups"]) == {
        name for name, group in registry_groups.items() if group.get("enabled") is not False
    }
    for group_name, group in generated["groups"].items():
        registry_servers = [
            server
            for server in registry_groups[group_name]["servers"]
            if server in generated["mcpServers"]
        ]
        assert group["servers"] == registry_servers

    assert validate_settings(generated, registry) == []
    assert validate_settings(settings, registry) == []


def test_serialize_settings_is_stable_json():
    repo_root = Path(__file__).resolve().parents[1]
    registry = json.loads((repo_root / "config" / "mcp-registry.json").read_text(encoding="utf-8"))
    generated = generate_settings(registry)
    assert serialize_settings(generated).endswith("\n")