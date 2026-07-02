"""Tests for mcp/agent-catalog/server.py."""

from __future__ import annotations

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from tests.mcp.conftest import load_server_module, run_async

server = load_server_module("agent-catalog")


def test_registers_expected_tools() -> None:
    async def _list() -> list[str]:
        async with Client(server.mcp) as client:
            return [t.name for t in await client.list_tools()]

    names = set(run_async(_list()))
    assert {"list_agents", "get_agent", "agent_skill_edges"} <= names


def test_list_agents_finds_orchestrator() -> None:
    async def _call() -> list[dict]:
        async with Client(server.mcp) as client:
            result = await client.call_tool("list_agents", {"query": "orchestrator"})
            return result.data

    rows = run_async(_call())
    assert any(row["id"] == "orchestrator" for row in rows)


def test_get_agent_returns_full_catalog_node() -> None:
    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("get_agent", {"agent_id": "orchestrator"})
            return result.data

    data = run_async(_call())
    assert data["kind"] == "agent"
    assert data["id"] == "orchestrator"
    assert data["body"]


def test_get_agent_unknown_id_raises() -> None:
    async def _call() -> None:
        async with Client(server.mcp) as client:
            await client.call_tool("get_agent", {"agent_id": "definitely-not-a-real-agent"})

    with pytest.raises(ToolError):
        run_async(_call())


def test_agent_skill_edges_returns_edge_shape() -> None:
    async def _call() -> list[dict]:
        async with Client(server.mcp) as client:
            result = await client.call_tool("agent_skill_edges", {})
            return result.data

    edges = run_async(_call())
    assert isinstance(edges, list)
    if edges:
        assert {"from_id", "to_id", "relation"} <= set(edges[0])


def test_agent_skill_edges_filters_by_agent_id() -> None:
    async def _all_edges() -> list[dict]:
        async with Client(server.mcp) as client:
            result = await client.call_tool("agent_skill_edges", {})
            return result.data

    all_edges = run_async(_all_edges())
    target_agent = next((e["from_id"].split(":", 1)[1] for e in all_edges if e["from_id"].startswith("agent:")), None)
    if target_agent is None:
        pytest.skip("No agent-sourced edges present in this checkout")

    async def _filtered() -> list[dict]:
        async with Client(server.mcp) as client:
            result = await client.call_tool("agent_skill_edges", {"agent_id": target_agent})
            return result.data

    filtered = run_async(_filtered())
    assert filtered
    assert all(e["from_id"] == f"agent:{target_agent}" for e in filtered)
