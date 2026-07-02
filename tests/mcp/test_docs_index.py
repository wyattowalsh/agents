"""Tests for mcp/docs-index/server.py."""

from __future__ import annotations

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from tests.mcp.conftest import load_server_module, run_async

server = load_server_module("docs-index")


def test_registers_expected_tools() -> None:
    async def _list() -> list[str]:
        async with Client(server.mcp) as client:
            return [t.name for t in await client.list_tools()]

    names = set(run_async(_list()))
    assert {"list_reports", "get_report", "list_content_pages", "read_content_page"} <= names


def test_list_reports_returns_known_slugs() -> None:
    async def _call() -> list[dict]:
        async with Client(server.mcp) as client:
            result = await client.call_tool("list_reports", {})
            return result.data

    slugs = {row["slug"] for row in run_async(_call())}
    assert {
        "docs-dependency-drift",
        "llms-txt-coverage",
        "site-graph-insights",
        "docs-link-check",
        "docs-graph-snapshot",
    } <= slugs


def test_get_report_unknown_slug_raises() -> None:
    async def _call() -> None:
        async with Client(server.mcp) as client:
            await client.call_tool("get_report", {"slug": "not-a-real-report"})

    with pytest.raises(ToolError):
        run_async(_call())


def test_get_report_known_slug_returns_generated_payload(tmp_path, monkeypatch) -> None:
    payload = {"hello": "world"}
    report_path = tmp_path / "docs-dependency-drift.json"
    report_path.write_text('{"hello": "world"}', encoding="utf-8")
    monkeypatch.setattr(server, "REPORTS_JSON_DIR", tmp_path)

    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("get_report", {"slug": "docs-dependency-drift"})
            return result.data

    assert run_async(_call()) == payload


def test_get_report_missing_file_raises(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(server, "REPORTS_JSON_DIR", tmp_path)

    async def _call() -> None:
        async with Client(server.mcp) as client:
            await client.call_tool("get_report", {"slug": "docs-link-check"})

    with pytest.raises(ToolError):
        run_async(_call())


def test_list_content_pages_filters_by_query() -> None:
    async def _call() -> list[dict]:
        async with Client(server.mcp) as client:
            result = await client.call_tool("list_content_pages", {"query": "cli"})
            return result.data

    rows = run_async(_call())
    assert any(row["path"] == "cli.mdx" for row in rows)


def test_read_content_page_rejects_disallowed_path() -> None:
    async def _call() -> None:
        async with Client(server.mcp) as client:
            await client.call_tool("read_content_page", {"relative_path": "../../etc/passwd"})

    with pytest.raises(ToolError):
        run_async(_call())
