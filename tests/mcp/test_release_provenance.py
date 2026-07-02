"""Tests for mcp/release-provenance/server.py."""

from __future__ import annotations

from fastmcp import Client

from tests.mcp.conftest import load_server_module, run_async

server = load_server_module("release-provenance")


def test_registers_expected_tools() -> None:
    async def _list() -> list[str]:
        async with Client(server.mcp) as client:
            return [t.name for t in await client.list_tools()]

    names = set(run_async(_list()))
    assert {
        "list_provenance_manifests",
        "get_provenance_manifest",
        "list_release_workflows",
        "get_release_workflow_summary",
    } <= names


def test_list_release_workflows_includes_release_skills() -> None:
    async def _call() -> list[dict]:
        async with Client(server.mcp) as client:
            result = await client.call_tool("list_release_workflows", {})
            return result.data

    names = {row["name"] for row in run_async(_call())}
    assert "release-skills.yml" in names
