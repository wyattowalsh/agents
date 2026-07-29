"""Registry contract tests for the reddit-mcp-buddy MCP server."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from tests.mcphub_registry_helpers import group_server_entry, group_server_names

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "config" / "mcp-registry.json"
SETTINGS_PATH = REPO_ROOT / "mcp" / "mcphub" / "mcp_settings.json"
WRAPPER_PATH = REPO_ROOT / "scripts" / "mcphub" / "reddit-mcp-buddy-stdio.sh"
REDDIT_WRAPPER_ARG = "".join(
    ("$", "{", "REPO_ROOT", "}/scripts/mcphub/reddit-mcp-buddy-stdio.sh")
)
OPT_IN_GROUPS = ("research", "shared-read", "experimental")
EXPECTED_TOOLS = [
    "browse_subreddit",
    "search_reddit",
    "get_post_details",
    "user_analysis",
    "reddit_explain",
]


@pytest.fixture
def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_reddit_mcp_buddy_server_entry(registry: dict) -> None:
    server = registry["servers"]["reddit-mcp-buddy"]
    assert server["transport"] == "stdio"
    assert server["command"] == "bash"
    assert server["args"] == [REDDIT_WRAPPER_ARG]
    assert server["enabled"] is True
    assert server["startup_timeout_sec"] == 90
    assert server["timeout_ms"] == 600000
    assert server["tools"] == EXPECTED_TOOLS
    assert "tools_allow_all" not in server
    assert server.get("env", {}) == {}


def test_reddit_mcp_buddy_wrapper_exists_and_executable() -> None:
    assert WRAPPER_PATH.is_file()
    assert os.access(WRAPPER_PATH, os.X_OK)
    text = WRAPPER_PATH.read_text(encoding="utf-8")
    assert "mcphub_load_env" in text
    assert "reddit-mcp-buddy@" in text
    assert "1.1.13" in text
    assert "MCPHUB_REDDIT_MCP_BUDDY_VERSION" not in text


def test_reddit_mcp_buddy_opt_in_groups(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    for group_name in OPT_IN_GROUPS:
        assert "reddit-mcp-buddy" in group_server_names(groups[group_name]), group_name
        assert group_server_entry(groups[group_name], "reddit-mcp-buddy") == {
            "name": "reddit-mcp-buddy",
            "tools": EXPECTED_TOOLS,
        }


def test_reddit_mcp_buddy_excluded_from_default_groups(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    for group_name in (
        "harness",
        "tunnel",
        "web-search",
        "web-read",
        "credentialed",
        "daily",
        "coding",
        "review",
    ):
        assert "reddit-mcp-buddy" not in group_server_names(
            groups[group_name]
        ), group_name


def test_reddit_mcp_buddy_generated_settings_parity() -> None:
    """Generated MCPHub settings project the server without tracked secrets."""
    assert SETTINGS_PATH.is_file()
    settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    servers = settings.get("mcpServers") or {}
    assert "reddit-mcp-buddy" in servers
    entry = servers["reddit-mcp-buddy"]
    assert entry.get("command") == "bash"
    assert any("reddit-mcp-buddy-stdio.sh" in str(a) for a in entry.get("args", []))
    # No env block or empty — never track REDDIT_* secrets in generated settings.
    env = entry.get("env")
    assert env in (None, {})
    if isinstance(env, dict):
        assert not any(k.upper().startswith("REDDIT") for k in env)

    groups = settings.get("groups") or []
    found: set[str] = set()
    if isinstance(groups, list):
        for g in groups:
            name = g.get("name") if isinstance(g, dict) else None
            servers_list = g.get("servers") if isinstance(g, dict) else None
            blob = json.dumps(servers_list or [])
            if "reddit-mcp-buddy" in blob and name:
                found.add(name)
    elif isinstance(groups, dict):
        for name, g in groups.items():
            blob = json.dumps(g)
            if "reddit-mcp-buddy" in blob:
                found.add(name)
    for group_name in OPT_IN_GROUPS:
        assert group_name in found, group_name
    for excluded in ("harness", "tunnel"):
        assert excluded not in found, excluded
