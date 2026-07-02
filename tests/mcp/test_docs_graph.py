"""Tests for mcp/docs-graph/server.py."""

from __future__ import annotations

from fastmcp import Client

from tests.mcp.conftest import load_server_module, run_async

server = load_server_module("docs-graph")


def test_registers_expected_tools() -> None:
    async def _list() -> list[str]:
        async with Client(server.mcp) as client:
            return [t.name for t in await client.list_tools()]

    names = set(run_async(_list()))
    assert {"docs_graph_snapshot", "docs_graph_latest", "docs_graph_history"} <= names


def test_docs_graph_latest_has_metrics() -> None:
    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("docs_graph_latest", {})
            return result.data

    latest = run_async(_call())
    assert "total_pages" in latest
    assert "orphan_count" in latest
