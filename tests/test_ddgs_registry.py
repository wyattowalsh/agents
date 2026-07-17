"""Registry contract tests for the ddgs MCP server."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.mcphub_registry_helpers import group_server_names

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "config" / "mcp-registry.json"


@pytest.fixture
def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_ddgs_server_entry(registry: dict) -> None:
    server = registry["servers"]["ddgs"]
    assert server["transport"] == "stdio"
    assert server["command"] == "uvx"
    assert server["args"] == ["--from", "ddgs[mcp]", "ddgs", "mcp"]
    assert server["auth_policy"] == "none"
    assert server["enabled"] is True


def test_ddgs_follows_duckduckgo_in_harness(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    harness = group_server_names(groups["harness"])
    assert "ddgs" in harness
    assert "duckduckgo-search" in harness
    assert harness.index("ddgs") == harness.index("duckduckgo-search") + 1


def test_ddgs_excluded_from_tunnel(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    assert "ddgs" not in group_server_names(groups["tunnel"])


def test_ddgs_server_id_is_not_shadowed_by_a_group_id(registry: dict) -> None:
    assert "ddgs" not in registry["mcphub"]["groups"]
