"""Registry contract tests for the qsv MCP server and data group."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.mcphub_registry_helpers import group_server_names

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "config" / "mcp-registry.json"
QSV_WRAPPER_ARG = "".join(
    ("$", "{", "REPO_ROOT", "}/scripts/mcphub/qsv-stdio.sh")
)


@pytest.fixture
def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_qsv_server_entry(registry: dict) -> None:
    server = registry["servers"]["qsv"]
    assert server["transport"] == "stdio"
    assert server["command"] == "bash"
    assert server["args"] == [QSV_WRAPPER_ARG]
    assert server["enabled"] is True
    assert server["tools"] == ["*"]
    assert server["tools_allow_all"] is True
    assert server["timeout_ms"] == 600000


def test_qsv_env_placeholders(registry: dict) -> None:
    env = registry["servers"]["qsv"]["env"]
    assert env["QSV_MCP_BIN_PATH"] == {"env_var": "QSV_MCP_BIN_PATH"}
    assert env["QSV_MCP_ALLOWED_DIRS"] == {"env_var": "QSV_MCP_ALLOWED_DIRS"}
    assert env["QSV_MCP_WORKING_DIR"] == {"env_var": "QSV_MCP_WORKING_DIR"}
    assert env["QSV_MCP_CHECK_UPDATES_ON_STARTUP"] == {"value": "false"}
    assert env["QSV_MCP_OPERATION_TIMEOUT_MS"] == {"value": "600000"}


def test_qsv_data_group_primary(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    assert "data" in groups
    assert groups["data"]["enabled"] is True
    assert "qsv" in group_server_names(groups["data"])


def test_qsv_opt_in_workflow_groups(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    for group_name in ("coding", "research"):
        assert "qsv" in group_server_names(groups[group_name]), group_name


def test_qsv_excluded_from_default_groups(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    for group_name in ("harness", "tunnel"):
        assert "qsv" not in group_server_names(groups[group_name]), group_name


def test_qsv_wrapper_script_exists() -> None:
    wrapper = REPO_ROOT / "scripts" / "mcphub" / "qsv-stdio.sh"
    assert wrapper.is_file()
    text = wrapper.read_text(encoding="utf-8")
    assert "qsv-agent-skills/dist/mcp-server.js" in text
    assert "HOME}/dev" in text or "${HOME}/dev" in text
