"""Registry contract tests for the open-websearch MCP server."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.mcphub_registry_helpers import (
    group_server_entry,
    group_server_names,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "config" / "mcp-registry.json"


@pytest.fixture
def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_open_websearch_server_entry(registry: dict) -> None:
    server = registry["servers"]["open-websearch"]
    assert server["transport"] == "stdio"
    assert server["command"] == "bash"
    assert server["args"] == ["${REPO_ROOT}/scripts/mcphub/open-websearch-stdio.sh"]  # noqa: RUF027
    assert server["enabled"] is True
    assert server["tools_allow_all"] is True


def test_open_websearch_opt_in_groups(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    for group_name in ("web-search", "research", "experimental"):
        assert "open-websearch" in group_server_names(groups[group_name]), group_name


def test_open_websearch_excluded_from_default_groups(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    for group_name in ("harness", "tunnel"):
        assert "open-websearch" not in group_server_names(groups[group_name]), group_name


def test_open_websearch_bounded_subsets(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    web_read = group_server_entry(groups["web-read"], "open-websearch")
    shared_read = group_server_entry(groups["shared-read"], "open-websearch")
    assert isinstance(web_read, dict)
    assert isinstance(shared_read, dict)
    assert web_read["tools"] == ["fetchWebContent", "fetchGithubReadme"]
    assert shared_read["tools"] == ["search", "fetchWebContent"]
