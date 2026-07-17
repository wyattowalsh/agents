"""Unit tests for production PinnedHttpxClient (session-review RV-001/002)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

import httpx
import pytest

_SERVER_PATH = Path(__file__).resolve().parents[1] / "mcp" / "source-url-health" / "server.py"
# Import the namespaced production module from its workspace member.
sys.path.insert(0, str(_SERVER_PATH.parent))
server = importlib.import_module("mcp_source_url_health.server")


class _RecordingClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []

    def __enter__(self) -> _RecordingClient:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def build_request(self, method: str, url: str, **kwargs: object) -> object:
        self.calls.append((method.upper(), url, dict(kwargs)))
        return object()

    def send(self, request: object, **kwargs: object) -> object:
        assert request is not None
        assert kwargs == {"follow_redirects": False, "stream": True}
        _method, url, _request_kwargs = self.calls[-1]

        class _Resp:
            def __init__(self, response_url: str) -> None:
                self.status_code = 200
                self.headers: dict[str, str] = {}
                self.url = response_url

            def close(self) -> None:
                return None

        return _Resp(url)

    def head(self, *a: object, **k: object) -> object:
        raise AssertionError("PinnedHttpxClient must use client.request, not head")

    def get(self, *a: object, **k: object) -> object:
        raise AssertionError("PinnedHttpxClient must use client.request, not get")


def test_request_pinned_uses_ip_netloc_and_host_header() -> None:
    rec = _RecordingClient()
    client = server.PinnedHttpxClient(cast("httpx.Client", rec))
    client.request_pinned(
        "HEAD",
        "https://example.com/a",
        pinned_ip="93.184.216.34",
        timeout=5.0,
    )
    assert len(rec.calls) == 1
    method, url, kwargs = rec.calls[0]
    assert method == "HEAD"
    netloc = urlparse(url).netloc
    assert "93.184.216.34" in netloc
    assert "example.com" not in netloc
    headers = kwargs.get("headers") or {}
    assert headers.get("Host") == "example.com"
    assert "follow_redirects" not in kwargs


def test_request_pinned_https_sets_sni_extension() -> None:
    rec = _RecordingClient()
    client = server.PinnedHttpxClient(cast("httpx.Client", rec))
    client.request_pinned(
        "GET",
        "https://example.com/b",
        pinned_ip="1.2.3.4",
        timeout=3.0,
    )
    _method, _url, kwargs = rec.calls[0]
    extensions = kwargs.get("extensions") or {}
    assert extensions.get("sni_hostname") == "example.com"
    assert "verify" not in kwargs


def test_request_pinned_matches_real_httpx_signature_and_streams() -> None:
    class _GuardedStream(httpx.SyncByteStream):
        def __init__(self) -> None:
            self.iterated = False
            self.closed = False

        def __iter__(self):  # type: ignore[no-untyped-def]
            self.iterated = True
            raise AssertionError("probe fallback must not consume the response body")

        def close(self) -> None:
            self.closed = True

    guarded = _GuardedStream()
    seen: list[httpx.Request] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, request=request, stream=guarded)

    with httpx.Client(
        transport=httpx.MockTransport(_handler),
        verify=True,
        trust_env=False,
        follow_redirects=False,
    ) as raw:
        client = server.PinnedHttpxClient(raw)
        response = client.request_pinned(
            "GET",
            "https://example.com/large",
            pinned_ip="93.184.216.34",
            timeout=3.0,
        )
        assert response.status_code == 200
        assert guarded.iterated is False
        response.close()

    assert len(seen) == 1
    assert seen[0].url.host == "93.184.216.34"
    assert seen[0].headers["host"] == "example.com"
    assert seen[0].headers["range"] == "bytes=0-0"
    assert guarded.closed is True


def test_request_pinned_typeerror_fails_closed() -> None:
    class _Bad:
        def build_request(self, *a: object, **k: object) -> object:
            raise TypeError("unexpected keyword argument 'extensions'")

    client = server.PinnedHttpxClient(cast("httpx.Client", _Bad()))
    with pytest.raises(ValueError, match="rejected pin kwargs"):
        client.request_pinned(
            "HEAD",
            "https://example.com/",
            pinned_ip="1.2.3.4",
            timeout=1.0,
        )


def test_request_pinned_forbids_auto_redirects() -> None:
    client = server.PinnedHttpxClient(cast("httpx.Client", _RecordingClient()))
    with pytest.raises(ValueError, match="forbids auto redirects"):
        client.request_pinned(
            "HEAD",
            "https://example.com/",
            pinned_ip="1.2.3.4",
            timeout=1.0,
            follow_redirects=True,
        )


def test_request_pinned_forbids_mutating_methods() -> None:
    client = server.PinnedHttpxClient(cast("httpx.Client", _RecordingClient()))
    with pytest.raises(ValueError, match="forbids method: POST"):
        client.request_pinned(
            "POST",
            "https://example.com/",
            pinned_ip="1.2.3.4",
            timeout=1.0,
        )
