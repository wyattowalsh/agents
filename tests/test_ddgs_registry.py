"""Registry contract tests for the ddgs MCP server."""

from __future__ import annotations

import json
import os
import subprocess
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
    assert server["command"] == "bash"
    assert server["args"] == ["${REPO_ROOT}/scripts/mcphub/ddgs-stdio.sh"]  # noqa: RUF027
    assert server["auth_policy"] == "none"
    assert server["enabled"] is True


def test_ddgs_wrapper_uses_preinstalled_pinned_tool(tmp_path: Path) -> None:
    tool_root = tmp_path / "tools"
    tool_bin = tool_root / "ddgs" / "bin"
    tool_bin.mkdir(parents=True)
    python_bin = tool_bin / "python"
    ddgs_bin = tool_bin / "ddgs"
    python_bin.write_text("#!/bin/sh\nprintf '9.14.4 1.29.0\\n'\n", encoding="utf-8")
    ddgs_bin.write_text("#!/bin/sh\nprintf '%s\\n' \"$*\"\n", encoding="utf-8")
    python_bin.chmod(0o755)
    ddgs_bin.chmod(0o755)

    result = subprocess.run(
        [str(REPO_ROOT / "scripts" / "mcphub" / "ddgs-stdio.sh"), "--probe"],
        cwd=REPO_ROOT,
        env={**os.environ, "UV_TOOL_DIR": str(tool_root)},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "mcp --probe\n"


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
