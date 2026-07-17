"""Tests for mcp/source-url-health/server.py.

All HTTP calls are mocked; no real network requests are made in this suite.
"""

from __future__ import annotations

import importlib
import socket
from typing import Protocol

import httpx
import pytest
from fastmcp import Client

from tests.mcp.conftest import load_server_module, run_async

server = load_server_module("source-url-health")
server_impl = importlib.import_module("mcp_source_url_health.server")


class _FakeResponse:
    def __init__(self, status_code: int, url: str) -> None:
        self.status_code = status_code
        self.url = url
        self.headers: dict[str, str] = {}

    def __str__(self) -> str:
        return self.url


class _FakeClientProtocol(Protocol):
    """Protocol shared by the test HTTP client fakes."""

    def __enter__(self) -> object: ...

    def __exit__(self, *exc_info: object) -> None: ...

    def head(
        self, url: str, timeout: float = 5.0, follow_redirects: bool = False, **_kwargs: object
    ) -> _FakeResponse: ...

    def get(
        self, url: str, timeout: float = 5.0, follow_redirects: bool = False, **_kwargs: object
    ) -> _FakeResponse: ...


class _FakeHttpClient:
    """Minimal stand-in for httpx.Client used by _check_one."""

    def __init__(self, *, head_status: int = 200, get_status: int | None = None, raise_error: bool = False) -> None:
        self.head_status = head_status
        self.get_status = get_status
        self.raise_error = raise_error
        self.head_calls: list[str] = []
        self.get_calls: list[str] = []
        self.pin_log: list[tuple[str, str, str]] = []

    def __enter__(self) -> _FakeHttpClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def head(self, url: str, timeout: float = 5.0, follow_redirects: bool = False, **_kwargs: object) -> _FakeResponse:
        assert follow_redirects is False
        self.head_calls.append(url)
        if self.raise_error:
            raise httpx.ConnectError("simulated connection failure")
        return _FakeResponse(self.head_status, url)

    def get(self, url: str, timeout: float = 5.0, follow_redirects: bool = False, **_kwargs: object) -> _FakeResponse:
        assert follow_redirects is False
        self.get_calls.append(url)
        status = self.get_status if self.get_status is not None else self.head_status
        return _FakeResponse(status, url)

    def request_pinned(
        self,
        method: str,
        url: str,
        *,
        pinned_ip: str,
        timeout: float = 5.0,
        follow_redirects: bool = False,
    ) -> _FakeResponse:
        """Used when tests inject a pin-aware client (not via PinnedHttpxClient wrap)."""
        assert follow_redirects is False
        self.pin_log.append((method.upper(), url, pinned_ip))
        if method.upper() == "HEAD":
            return self.head(url, timeout=timeout, follow_redirects=False)
        return self.get(url, timeout=timeout, follow_redirects=False)


def _patch_client(monkeypatch: pytest.MonkeyPatch, fake: _FakeClientProtocol) -> None:
    """Inject *fake* as the pin-aware client (bypass PinnedHttpxClient hostname rewrite)."""

    def _client(**_kwargs: object) -> object:
        # Return a pin-capable object that check_once will use via PinnedHttpxClient
        # if wrapped — prefer exposing request_pinned on the outer wrap.
        return fake

    # Replace PinnedHttpxClient so check_once receives the fake with request_pinned.
    monkeypatch.setattr(server_impl, "PinnedHttpxClient", lambda _raw: fake)
    monkeypatch.setattr(server_impl.httpx, "Client", lambda **_kwargs: fake)
    # Preserve literal-address classification while making hostname resolution
    # deterministic and network-free.
    ssrf_socket = server_impl.check_once.__globals__["socket"]
    monkeypatch.setattr(
        ssrf_socket,
        "getaddrinfo",
        lambda *_a, **_k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))],
    )


def test_registers_expected_tools() -> None:
    async def _list() -> list[str]:
        async with Client(server.mcp) as client:
            return [t.name for t in await client.list_tools()]

    names = set(run_async(_list()))
    assert {"check_url_health", "check_urls_health"} <= names


def test_check_url_health_constructs_isolated_verified_client(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    raw = _FakeHttpClient(head_status=200)

    def _client(**kwargs: object) -> _FakeHttpClient:
        captured.update(kwargs)
        return raw

    monkeypatch.setattr(server_impl.httpx, "Client", _client)
    monkeypatch.setattr(server_impl, "PinnedHttpxClient", lambda _raw: raw)
    monkeypatch.setattr(
        server_impl,
        "_check_one",
        lambda _client, url, _timeout: {"url": url, "ok": True},
    )

    assert server.check_url_health("https://example.com")["ok"] is True
    assert captured["verify"] is True
    assert captured["trust_env"] is False
    assert captured["follow_redirects"] is False
    limits = captured["limits"]
    assert isinstance(limits, httpx.Limits)
    assert limits.max_keepalive_connections == 0


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


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/admin",
        "http://localhost:8080/",
        "http://192.168.1.1/",
        "http://10.0.0.5/",
        "http://[::1]/",
        "file:///etc/passwd",
        "ftp://example.com/a",
        "https://169.254.169.254/latest/meta-data",
    ],
)
def test_check_url_health_blocks_ssrf_targets(monkeypatch: pytest.MonkeyPatch, url: str) -> None:
    fake = _FakeHttpClient(head_status=200)
    _patch_client(monkeypatch, fake)

    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("check_url_health", {"url": url})
            return result.data

    data = run_async(_call())
    assert data["ok"] is False
    assert data["error"]
    assert "ssrf_blocked" in data["error"]
    assert fake.head_calls == []


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
    assert fake.get_calls == ["https://example.com"] or (
        fake.pin_log and fake.pin_log[-1][0] == "GET" and fake.get_calls == ["https://example.com"]
    )


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
            # Host must resolve publicly; transport then raises ConnectError.
            result = await client.call_tool("check_url_health", {"url": "https://example.com/down"})
            return result.data

    data = run_async(_call())
    assert data["ok"] is False
    assert data["status_code"] is None
    assert "ConnectError" in data["error"]


def test_check_urls_health_batches_multiple_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_client(monkeypatch, _FakeHttpClient(head_status=200))
    # Use path variants on a resolvable public host (DNS fail-closed would block fake TLDs).
    urls = ["https://example.com/a", "https://example.com/b"]

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


class _RedirectFakeClient:
    """Scripted multi-hop client for tool-level redirect SSRF checks."""

    def __init__(self, routes: dict[str, list[tuple[int, str | None]]]) -> None:
        self._routes = {k: list(v) for k, v in routes.items()}
        self.head_calls: list[str] = []
        self.pin_log: list[tuple[str, str, str]] = []

    def __enter__(self) -> _RedirectFakeClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def head(self, url: str, timeout: float = 5.0, follow_redirects: bool = False, **_k: object) -> _FakeResponse:
        assert follow_redirects is False
        self.head_calls.append(url)
        queue = self._routes.get(url)
        if not queue:
            return _FakeResponse(200, url)
        status, location = queue.pop(0)
        resp = _FakeResponse(status, url)
        if location:
            resp.headers = {"location": location}
        return resp

    def get(self, url: str, timeout: float = 5.0, follow_redirects: bool = False, **_k: object) -> _FakeResponse:
        return self.head(url, timeout=timeout, follow_redirects=follow_redirects)

    def request_pinned(
        self,
        method: str,
        url: str,
        *,
        pinned_ip: str,
        timeout: float = 5.0,
        follow_redirects: bool = False,
    ) -> _FakeResponse:
        assert follow_redirects is False
        self.pin_log.append((method.upper(), url, pinned_ip))
        if method.upper() == "HEAD":
            return self.head(url, timeout=timeout, follow_redirects=False)
        return self.get(url, timeout=timeout, follow_redirects=False)


def test_tool_blocks_redirect_to_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    public = "https://example.com/start"
    fake = _RedirectFakeClient({public: [(302, "http://127.0.0.1/admin")]})
    _patch_client(monkeypatch, fake)

    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("check_url_health", {"url": public})
            return result.data

    data = run_async(_call())
    assert data["ok"] is False
    assert data["error"]
    assert "ssrf_blocked" in data["error"]
    assert fake.head_calls == [public]
    assert not any("127.0.0.1" in u for u in fake.head_calls)


def test_tool_405_fallback_without_auto_follow(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeHttpClient(head_status=405, get_status=200)
    _patch_client(monkeypatch, fake)

    async def _call() -> dict:
        async with Client(server.mcp) as client:
            result = await client.call_tool("check_url_health", {"url": "https://example.com"})
            return result.data

    data = run_async(_call())
    assert data["ok"] is True
    assert fake.get_calls == ["https://example.com"]
    assert any(m == "GET" for m, _u, _ip in fake.pin_log) or fake.get_calls


def test_tool_batch_propagates_ssrf_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeHttpClient(head_status=200)
    _patch_client(monkeypatch, fake)
    urls = ["https://example.com/ok", "http://127.0.0.1/bad"]

    async def _call() -> list[dict]:
        async with Client(server.mcp) as client:
            result = await client.call_tool("check_urls_health", {"urls": urls})
            return result.data

    results = run_async(_call())
    assert results[0]["ok"] is True
    assert results[1]["ok"] is False
    assert results[1]["error"]
    assert "ssrf_blocked" in results[1]["error"]
