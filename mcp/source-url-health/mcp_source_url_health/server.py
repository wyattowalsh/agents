"""MCP server: source-url-health.

Checks the reachability of external source URLs (curated skill sources,
agent MCP references, docs links) over HTTP. Performs outbound network
requests only — never mutates the repository.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

import httpx
from fastmcp import FastMCP

if TYPE_CHECKING:
    from types import TracebackType

from .ssrf import (
    check_once,
    url_for_pinned_connect,
    validate_url_for_probe,
)

mcp = FastMCP("Source URL Health")

_READ_ONLY_NETWORK = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}

_DEFAULT_TIMEOUT_SEC = 10.0
_MAX_TIMEOUT_SEC = 30.0
_MAX_BATCH = 25
_USER_AGENT = "agents-repo-source-url-health-mcp/1"

__all__ = [
    "PinnedHttpxClient",
    "check_url_health",
    "check_urls_health",
    "mcp",
    "validate_url_for_probe",
]


class PinnedHttpxClient:
    """httpx wrapper that dials validated public IPs while preserving Host/SNI."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def __enter__(self) -> PinnedHttpxClient:
        self._client.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._client.__exit__(exc_type, exc_value, traceback)

    def head(self, url: str, *, timeout: float, follow_redirects: bool = False, **kwargs: Any) -> httpx.Response:
        return self._client.head(url, timeout=timeout, follow_redirects=follow_redirects, **kwargs)

    def get(self, url: str, *, timeout: float, follow_redirects: bool = False, **kwargs: Any) -> httpx.Response:
        return self._client.get(url, timeout=timeout, follow_redirects=follow_redirects, **kwargs)

    def request_pinned(
        self,
        method: str,
        url: str,
        *,
        pinned_ip: str,
        timeout: float,
        follow_redirects: bool = False,
    ) -> httpx.Response:
        """Dial *pinned_ip* while presenting original hostname as Host/SNI.

        Build and stream one request through the supported HTTPX 0.28 client
        surface. TLS verification belongs to client construction, never this
        per-request call.
        """
        if follow_redirects:
            raise ValueError("PinnedHttpxClient forbids auto redirects")
        pinned_url, hostname = url_for_pinned_connect(url, pinned_ip)
        parsed = urlsplit(url)
        display_host = f"[{hostname}]" if ":" in hostname else hostname
        host_header = f"{display_host}:{parsed.port}" if parsed.port else display_host
        headers = {"Host": host_header, "User-Agent": _USER_AGENT}
        method_u = method.upper()
        if method_u not in {"HEAD", "GET"}:
            raise ValueError(f"PinnedHttpxClient forbids method: {method_u}")
        if method_u == "GET":
            headers["Range"] = "bytes=0-0"
        extensions = {"sni_hostname": hostname} if parsed.scheme.lower() == "https" else None
        try:
            request = self._client.build_request(
                method_u,
                pinned_url,
                headers=headers,
                timeout=timeout,
                extensions=extensions,
            )
            return self._client.send(
                request,
                follow_redirects=False,
                stream=True,
            )
        except TypeError as exc:
            raise ValueError(f"httpx client rejected pin kwargs (Host/SNI required): {exc}") from exc


def _clamp_timeout(timeout_sec: float) -> float:
    try:
        value = float(timeout_sec)
    except (TypeError, ValueError):
        return _DEFAULT_TIMEOUT_SEC
    if value <= 0:
        return _DEFAULT_TIMEOUT_SEC
    return min(value, _MAX_TIMEOUT_SEC)


def _check_one(client: Any, url: str, timeout_sec: float) -> dict[str, Any]:
    return check_once(client, url, timeout_sec)


@mcp.tool(annotations=_READ_ONLY_NETWORK)
def check_url_health(url: str, timeout_sec: float = _DEFAULT_TIMEOUT_SEC) -> dict[str, Any]:
    """Check whether a single URL is reachable (HEAD, falling back to GET on 405).

    Returns `{url, ok, status_code, final_url, elapsed_ms, error, pinned_addresses?}`.
    Redirects are followed hop-by-hop with SSRF validation and connect-to-pinned-IP
    before each request (never auto-follow into private networks). ``timeout_sec``
    is a best-effort per-URL budget shared across redirects and pin attempts.
    Synchronous system DNS cannot be interrupted, and HTTPX applies phase
    timeouts, so elapsed wall time can exceed that budget.
    """
    timeout = _clamp_timeout(timeout_sec)
    with httpx.Client(
        headers={"User-Agent": _USER_AGENT},
        verify=True,
        trust_env=False,
        follow_redirects=False,
        limits=httpx.Limits(max_keepalive_connections=0),
    ) as raw:
        return _check_one(PinnedHttpxClient(raw), url, timeout)


@mcp.tool(annotations=_READ_ONLY_NETWORK)
def check_urls_health(urls: list[str], timeout_sec: float = _DEFAULT_TIMEOUT_SEC) -> list[dict[str, Any]]:
    """Check up to 25 URLs sequentially with a best-effort budget per URL.

    The budget is shared across redirects and pin attempts for one URL, not the
    whole batch. Synchronous system DNS cannot be interrupted, so an individual
    result and therefore the sequential batch can exceed the requested budget.
    """
    if len(urls) > _MAX_BATCH:
        raise ValueError(f"Too many URLs ({len(urls)}); split into batches of {_MAX_BATCH} or fewer.")
    timeout = _clamp_timeout(timeout_sec)
    with httpx.Client(
        headers={"User-Agent": _USER_AGENT},
        verify=True,
        trust_env=False,
        follow_redirects=False,
        limits=httpx.Limits(max_keepalive_connections=0),
    ) as raw:
        pinned = PinnedHttpxClient(raw)
        return [_check_one(pinned, url, timeout) for url in urls]


if __name__ == "__main__":
    mcp.run()
