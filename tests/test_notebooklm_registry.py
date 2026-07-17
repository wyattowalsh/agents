"""Registry contract tests for the notebooklm MCP server (teng-lin/notebooklm-py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.mcphub_registry_helpers import group_server_names

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "config" / "mcp-registry.json"

TARGET_CLIENTS = ("default", "codex", "grok", "opencode")


@pytest.fixture
def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_notebooklm_server_entry(registry: dict) -> None:
    server = registry["servers"]["notebooklm"]
    assert server["transport"] == "stdio"
    assert server["command"] == "uvx"
    assert server["args"] == [
        "--from",
        "notebooklm-py[mcp]==0.8.0b5",
        "notebooklm-mcp",
    ]
    assert server["enabled"] is True
    assert server.get("tools_allow_all") is True


def test_notebooklm_group_nlm_membership(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    assert "nlm" in groups
    assert groups["nlm"]["enabled"] is True
    assert group_server_names(groups["nlm"]) == ["notebooklm"]


def test_notebooklm_not_in_harness_or_tunnel(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    assert "notebooklm" not in group_server_names(groups["harness"])
    assert "notebooklm" not in group_server_names(groups["tunnel"])


def test_notebooklm_server_id_is_not_shadowed_by_a_group_id(registry: dict) -> None:
    assert "notebooklm" not in registry["mcphub"]["groups"]
    assert "nlm" not in registry["servers"]


def test_notebooklm_clients_enable_nlm_group(registry: dict) -> None:
    clients = registry["mcphub"]["clients"]
    for name in TARGET_CLIENTS:
        client = clients[name]
        assert client["included_groups"] == ["harness", "nlm"], name
        assert client["enabled_groups"] == ["harness", "nlm"], name
        assert "group" in client["enabled_endpoint_kinds"], name
    # optional clients (present only on some machines / registry revisions)
    if "lm-studio" in clients:
        assert "nlm" in clients["lm-studio"].get("included_groups", [])
