"""Tests for mcp/ci-artifacts/server.py."""

from __future__ import annotations

from fastmcp import Client

from tests.mcp.conftest import load_server_module, run_async

server = load_server_module("ci-artifacts")


def test_registers_expected_tools() -> None:
    async def _list() -> list[str]:
        async with Client(server.mcp) as client:
            return [t.name for t in await client.list_tools()]

    names = set(run_async(_list()))
    assert {
        "list_ci_artifacts",
        "get_ci_artifact",
        "ci_artifact_registry",
        "ci_artifact_summary",
    } <= names


def test_list_ci_artifacts_includes_docs_graph_snapshot() -> None:
    async def _call() -> list[dict]:
        async with Client(server.mcp) as client:
            result = await client.call_tool("list_ci_artifacts", {})
            return result.data

    names = {row["name"] for row in run_async(_call())}
    assert "docs-graph-snapshot" in names


def test_get_ci_artifact_returns_payload() -> None:
    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("get_ci_artifact", {"name": "docs-graph-snapshot"})
            return result.data

    payload = run_async(_call())
    assert "latest" in payload or "history" in payload
