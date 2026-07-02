"""Tests for mcp/skill-catalog/server.py."""

from __future__ import annotations

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from tests.mcp.conftest import load_server_module, run_async

server = load_server_module("skill-catalog")


def test_registers_expected_tools() -> None:
    async def _list() -> list[str]:
        async with Client(server.mcp) as client:
            return [t.name for t in await client.list_tools()]

    names = set(run_async(_list()))
    assert {"list_skills", "get_skill", "skills_catalog_index", "skill_catalog_summary"} <= names


def test_list_skills_filters_by_query() -> None:
    async def _call() -> list[dict]:
        async with Client(server.mcp) as client:
            result = await client.call_tool("list_skills", {"query": "review"})
            return result.data

    rows = run_async(_call())
    assert any(row["id"] == "review" for row in rows)
    assert all("review" in f"{row['id']} {row['title']} {row['description']}".lower() for row in rows)


def test_list_skills_empty_query_returns_all() -> None:
    async def _call() -> list[dict]:
        async with Client(server.mcp) as client:
            result = await client.call_tool("list_skills", {})
            return result.data

    rows = run_async(_call())
    assert len(rows) > 10
    assert rows == sorted(rows, key=lambda r: r["id"])


def test_get_skill_returns_full_catalog_node() -> None:
    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("get_skill", {"skill_id": "review"})
            return result.data

    data = run_async(_call())
    assert data["kind"] == "skill"
    assert data["id"] == "review"
    assert "source_path" in data
    assert "metadata" in data


def test_get_skill_unknown_id_raises() -> None:
    async def _call() -> None:
        async with Client(server.mcp) as client:
            await client.call_tool("get_skill", {"skill_id": "definitely-not-a-real-skill"})

    with pytest.raises(ToolError):
        run_async(_call())


def test_skills_catalog_index_returns_dict_with_index_key() -> None:
    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("skills_catalog_index", {})
            return result.data

    data = run_async(_call())
    assert "allSkillIndex" in data
    assert isinstance(data["allSkillIndex"], list)


def test_skill_catalog_summary_counts_are_nonnegative() -> None:
    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("skill_catalog_summary", {})
            return result.data

    counts = run_async(_call())
    assert counts["skills"] > 0
    assert all(v >= 0 for v in counts.values())
