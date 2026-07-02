"""Tests for mcp/workflow-status/server.py."""

from __future__ import annotations

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from tests.mcp.conftest import load_server_module, run_async

server = load_server_module("workflow-status")


def test_registers_expected_tools() -> None:
    async def _list() -> list[str]:
        async with Client(server.mcp) as client:
            return [t.name for t in await client.list_tools()]

    names = set(run_async(_list()))
    assert {"list_workflows", "get_workflow_summary", "read_workflow", "workflows_overview"} <= names


def test_get_workflow_summary_ci() -> None:
    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("get_workflow_summary", {"filename": "ci.yml"})
            return result.data

    summary = run_async(_call())
    assert summary["filename"] == "ci.yml"
    assert summary["job_count"] > 0
    assert "lint" in {job["name"] for job in summary["jobs"]}


def test_read_workflow_rejects_traversal() -> None:
    async def _call() -> None:
        async with Client(server.mcp) as client:
            await client.call_tool("read_workflow", {"filename": "../../etc/passwd"})

    with pytest.raises(ToolError):
        run_async(_call())
