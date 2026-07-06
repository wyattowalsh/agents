"""Registry contract tests for the jupyter-mcp-server MCP server."""

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
JUPYTER_WRAPPER_ARG = "".join(
    ("$", "{", "REPO_ROOT", "}/scripts/mcphub/jupyter-mcp-server-stdio.sh")
)

JUPYTER_BOUNDED_TOOLS = [
    "list_files",
    "list_kernels",
    "list_notebooks",
    "read_notebook",
    "read_cell",
]


@pytest.fixture
def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_jupyter_server_entry(registry: dict) -> None:
    server = registry["servers"]["jupyter-mcp-server"]
    assert server["transport"] == "stdio"
    assert server["command"] == "bash"
    assert server["args"] == [JUPYTER_WRAPPER_ARG]
    assert server["enabled"] is True
    assert server["startup_timeout_sec"] == 120
    assert server["tools_allow_all"] is True


def test_jupyter_env_placeholders(registry: dict) -> None:
    env = registry["servers"]["jupyter-mcp-server"]["env"]
    assert env["JUPYTER_URL"] == {"env_var": "JUPYTER_URL"}
    assert env["JUPYTER_TOKEN"] == {"env_var": "JUPYTER_TOKEN"}
    assert env["ALLOW_IMG_OUTPUT"] == {"env_var": "ALLOW_IMG_OUTPUT"}
    assert env["JUPYTER_DOCUMENT_ID"] == {"env_var": "JUPYTER_DOCUMENT_ID"}


def test_jupyter_opt_in_groups(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    for group_name in (
        "notebooks",
        "coding",
        "heavy",
        "credentialed",
        "experimental",
    ):
        assert "jupyter-mcp-server" in group_server_names(groups[group_name]), group_name


def test_jupyter_excluded_from_default_groups(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    for group_name in ("harness", "tunnel", "shared-read"):
        assert "jupyter-mcp-server" not in group_server_names(
            groups[group_name]
        ), group_name


def test_jupyter_bounded_subsets(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    for group_name in ("research", "review"):
        entry = group_server_entry(groups[group_name], "jupyter-mcp-server")
        assert isinstance(entry, dict), group_name
        assert entry["tools"] == JUPYTER_BOUNDED_TOOLS