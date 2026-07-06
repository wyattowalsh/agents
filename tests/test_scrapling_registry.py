"""Registry contract tests for the scrapling MCP server."""

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


def test_scrapling_server_entry(registry: dict) -> None:
    server = registry["servers"]["scrapling"]
    assert server["transport"] == "stdio"
    assert server["command"] == "bash"
    assert server["args"] == ["${REPO_ROOT}/scripts/mcphub/scrapling-stdio.sh"]
    assert server["enabled"] is True
    assert server["startup_timeout_sec"] == 120
    assert server["timeout_ms"] == 600000
    assert server["tools_allow_all"] is True


def test_scrapling_opt_in_groups(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    for group_name in (
        "research",
        "media-work",
        "live-browser",
        "heavy",
        "experimental",
    ):
        assert "scrapling" in group_server_names(groups[group_name]), group_name


def test_scrapling_excluded_from_default_groups(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    for group_name in ("harness", "tunnel", "browser"):
        assert "scrapling" not in group_server_names(groups[group_name]), group_name


def test_scrapling_bounded_subsets(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    web_read = group_server_entry(groups["web-read"], "scrapling")
    shared_read = group_server_entry(groups["shared-read"], "scrapling")
    assert isinstance(web_read, dict)
    assert isinstance(shared_read, dict)
    assert web_read["tools"] == ["get", "bulk_get"]
    assert shared_read["tools"] == ["get"]