"""Registry contract tests for the llms-txt-explorer MCP server."""

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


def test_llms_txt_explorer_server_entry(registry: dict) -> None:
    server = registry["servers"]["llms-txt-explorer"]
    assert server["transport"] == "stdio"
    assert server["command"] == "bash"
    assert server["args"] == ["${REPO_ROOT}/scripts/mcphub/llms-txt-explorer-stdio.sh"]  # noqa: RUF027
    assert server["enabled"] is True
    assert server["tools_allow_all"] is True


def test_llms_txt_explorer_harness_bounded_subset(registry: dict) -> None:
    harness = group_server_entry(registry["mcphub"]["groups"]["harness"], "llms-txt-explorer")
    assert isinstance(harness, dict)
    assert harness["tools"] == ["list_websites"]


def test_llms_txt_explorer_excluded_from_tunnel(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    assert "llms-txt-explorer" not in group_server_names(groups["tunnel"])


def test_llms_txt_explorer_workflow_groups(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    for group_name in (
        "daily",
        "docs",
        "research",
        "web-read",
        "coding",
        "review",
        "shared-read",
    ):
        assert "llms-txt-explorer" in group_server_names(groups[group_name]), group_name
        entry = group_server_entry(groups[group_name], "llms-txt-explorer")
        assert entry == "llms-txt-explorer", group_name
