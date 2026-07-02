"""Tests for mcp/repo-readonly/server.py."""

from __future__ import annotations

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from tests.mcp.conftest import load_server_module, run_async

server = load_server_module("repo-readonly")


def test_registers_expected_tools() -> None:
    async def _list() -> list[str]:
        async with Client(server.mcp) as client:
            return [t.name for t in await client.list_tools()]

    names = set(run_async(_list()))
    assert {"list_allowed_prefixes", "path_allowed", "read_file", "list_directory"} <= names


def test_list_allowed_prefixes_includes_skills_and_agents() -> None:
    async def _call() -> list[str]:
        async with Client(server.mcp) as client:
            result = await client.call_tool("list_allowed_prefixes", {})
            return result.data

    prefixes = run_async(_call())
    assert "skills" in prefixes
    assert "agents" in prefixes
    assert "AGENTS.md" in prefixes


def test_path_allowed_true_for_allowlisted_file() -> None:
    async def _call() -> bool:
        async with Client(server.mcp) as client:
            result = await client.call_tool("path_allowed", {"relative_path": "AGENTS.md"})
            return result.data

    assert run_async(_call()) is True


def test_path_allowed_false_for_disallowed_file() -> None:
    async def _call() -> bool:
        async with Client(server.mcp) as client:
            result = await client.call_tool("path_allowed", {"relative_path": ".env"})
            return result.data

    assert run_async(_call()) is False


def test_read_file_returns_contents_for_allowlisted_path() -> None:
    async def _call() -> str:
        async with Client(server.mcp) as client:
            result = await client.call_tool("read_file", {"relative_path": "AGENTS.md"})
            return result.data

    text = run_async(_call())
    assert "AGENTS.md" in text or len(text) > 0


def test_read_file_rejects_traversal() -> None:
    async def _call() -> None:
        async with Client(server.mcp) as client:
            await client.call_tool("read_file", {"relative_path": "../outside.txt"})

    with pytest.raises(ToolError):
        run_async(_call())


def test_read_file_rejects_absolute_path() -> None:
    async def _call() -> None:
        async with Client(server.mcp) as client:
            await client.call_tool("read_file", {"relative_path": "/etc/passwd"})

    with pytest.raises(ToolError):
        run_async(_call())


def test_list_directory_returns_entries_for_skills() -> None:
    async def _call() -> list[dict]:
        async with Client(server.mcp) as client:
            result = await client.call_tool("list_directory", {"relative_path": "skills"})
            return result.data

    entries = run_async(_call())
    assert any(e["name"] == "review" and e["kind"] == "directory" for e in entries)


def test_list_directory_rejects_non_directory() -> None:
    async def _call() -> None:
        async with Client(server.mcp) as client:
            await client.call_tool("list_directory", {"relative_path": "AGENTS.md"})

    with pytest.raises(ToolError):
        run_async(_call())
