"""Registry contract tests for package-version-check-mcp."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "config" / "mcp-registry.json"
LAUNCHER = REPO_ROOT / "scripts/mcphub/package-version-check-mcp.sh"


def group_server_names(group: dict) -> list[str]:
    names: list[str] = []
    for server in group["servers"]:
        if isinstance(server, dict):
            names.append(server["name"])
        else:
            names.append(server)
    return names


def test_package_version_check_mcp_server_entry() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    server = registry["servers"]["package-version-check-mcp"]
    assert server["transport"] == "stdio"
    assert server["command"] == "bash"
    assert server["args"] == ["${REPO_ROOT}/scripts/mcphub/package-version-check-mcp.sh"]  # noqa: RUF027
    assert server["enabled"] is True
    assert server["tools"] == [
        "get_latest_package_versions",
        "get_github_action_versions_and_args",
        "get_supported_tools",
        "get_latest_tool_versions",
    ]
    assert LAUNCHER.is_file()


def test_package_version_check_mcp_in_harness_and_research() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    groups = registry["mcphub"]["groups"]
    for group_name in ("harness", "research", "tunnel", "daily"):
        assert "package-version-check-mcp" in group_server_names(groups[group_name]), group_name


def test_legacy_package_version_server_removed() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    assert "package-version" not in registry["servers"]
