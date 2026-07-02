"""Tests for mcp/template-smoke/server.py."""

from __future__ import annotations

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from tests.mcp.conftest import load_server_module, run_async

server = load_server_module("template-smoke")


def test_registers_expected_tools() -> None:
    async def _list() -> list[str]:
        async with Client(server.mcp) as client:
            return [t.name for t in await client.list_tools()]

    names = set(run_async(_list()))
    assert {
        "mcp_layout_validate",
        "list_mcp_servers",
        "scaffold_dry_run",
        "scaffold_name_check",
    } <= names


def test_mcp_layout_validate_returns_ok_flag() -> None:
    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("mcp_layout_validate", {})
            return result.data

    payload = run_async(_call())
    assert "ok" in payload
    assert isinstance(payload["errors"], list)


def test_list_mcp_servers_includes_skill_catalog() -> None:
    async def _call() -> list[dict]:
        async with Client(server.mcp) as client:
            result = await client.call_tool("list_mcp_servers", {})
            return result.data

    rows = run_async(_call())
    names = {row["name"] for row in rows}
    assert "skill-catalog" in names
    skill_row = next(row for row in rows if row["name"] == "skill-catalog")
    assert skill_row["has_server_py"] is True
    assert skill_row["has_fastmcp_json"] is True


def test_scaffold_dry_run_valid_name() -> None:
    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("scaffold_dry_run", {"name": "example-server"})
            return result.data

    payload = run_async(_call())
    assert payload["name"] == "example-server"
    assert payload["already_exists"] is False
    assert payload["would_create"] == ["server.py", "pyproject.toml", "fastmcp.json"]


def test_scaffold_name_check_rejects_invalid_name() -> None:
    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("scaffold_name_check", {"name": "Bad_Name"})
            return result.data

    payload = run_async(_call())
    assert payload["valid"] is False


def test_scaffold_dry_run_invalid_name_raises() -> None:
    async def _call() -> None:
        async with Client(server.mcp) as client:
            await client.call_tool("scaffold_dry_run", {"name": "Bad_Name"})

    with pytest.raises(ToolError):
        run_async(_call())
