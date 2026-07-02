"""Tests for mcp/source-url-health/server.py.

All HTTP calls are mocked; no real network requests are made in this suite.
"""

from __future__ import annotations

import httpx
import pytest
from fastmcp import Client

from tests.mcp.conftest import load_server_module, run_async

server = load_server_module("source-url-health")


class _FakeResponse:
    def __init__(self, status_code: int, url: str) -> None:
        self.status_code = status_code
        self.url = url

    def __str__(self) -> str:
        return self.url


class _FakeHttpClient:
    """Minimal stand-in for httpx.Client used by _check_one."""

    def __init__(self, *, head_status: int = 200, get_status: int | None = None, raise_error: bool = False) -> None:
        self.head_status = head_status
        self.get_status = get_status
        self.raise_error = raise_error
        self.head_calls: list[str] = []
        self.get_calls: list[str] = []

    def __enter__(self) -> _FakeHttpClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def head(self, url: str, timeout: float, follow_redirects: bool) -> _FakeResponse:
        self.head_calls.append(url)
        if self.raise_error:
            raise httpx.ConnectError("simulated connection failure")
        return _FakeResponse(self.head_status, url)

    def get(self, url: str, timeout: float, follow_redirects: bool) -> _FakeResponse:
        self.get_calls.append(url)
        status = self.get_status if self.get_status is not None else self.head_status
        return _FakeResponse(status, url)


def _patch_client(monkeypatch: pytest.MonkeyPatch, fake: _FakeHttpClient) -> None:
    monkeypatch.setattr(server.httpx, "Client", lambda **_kwargs: fake)


def test_registers_expected_tools() -> None:
    async def _list() -> list[str]:
        async with Client(server.mcp) as client:
            return [t.name for t in await client.list_tools()]

    names = set(run_async(_list()))
    assert {"check_url_health", "check_urls_health"} <= names


def test_check_url_health_ok_on_2xx_head(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_client(monkeypatch, _FakeHttpClient(head_status=200))

    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("check_url_health", {"url": "https://example.com"})
            return result.data

    data = run_async(_call())
    assert data["ok"] is True
    assert data["status_code"] == 200
    assert data["error"] is None


def test_check_url_health_falls_back_to_get_on_405(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeHttpClient(head_status=405, get_status=200)
    _patch_client(monkeypatch, fake)

    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("check_url_health", {"url": "https://example.com"})
            return result.data

    data = run_async(_call())
    assert data["ok"] is True
    assert data["status_code"] == 200
    assert fake.get_calls == ["https://example.com"]


def test_check_url_health_reports_4xx_as_not_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_client(monkeypatch, _FakeHttpClient(head_status=404))

    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("check_url_health", {"url": "https://example.com/missing"})
            return result.data

    data = run_async(_call())
    assert data["ok"] is False
    assert data["status_code"] == 404


def test_check_url_health_captures_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_client(monkeypatch, _FakeHttpClient(raise_error=True))

    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("check_url_health", {"url": "https://unreachable.invalid"})
            return result.data

    data = run_async(_call())
    assert data["ok"] is False
    assert data["status_code"] is None
    assert "ConnectError" in data["error"]


def test_check_urls_health_batches_multiple_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_client(monkeypatch, _FakeHttpClient(head_status=200))
    urls = ["https://a.example.com", "https://b.example.com"]

    async def _call() -> list[dict]:
        async with Client(server.mcp) as client:
            result = await client.call_tool("check_urls_health", {"urls": urls})
            return result.data

    results = run_async(_call())
    assert [r["url"] for r in results] == urls
    assert all(r["ok"] for r in results)


def test_check_urls_health_rejects_oversized_batch() -> None:
    urls = [f"https://example.com/{i}" for i in range(26)]

    async def _call() -> None:
        async with Client(server.mcp) as client:
            await client.call_tool("check_urls_health", {"urls": urls})

    from fastmcp.exceptions import ToolError

    with pytest.raises(ToolError):
        run_async(_call())
