"""MCP server: source-url-health.

Checks the reachability of external source URLs (curated skill sources,
agent MCP references, docs links) over HTTP. Performs outbound network
requests only — never mutates the repository.
"""

from __future__ import annotations

import time
from typing import Any

import httpx
from fastmcp import FastMCP

mcp = FastMCP("Source URL Health")

_READ_ONLY_NETWORK = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}

_DEFAULT_TIMEOUT_SEC = 10.0
_MAX_BATCH = 25
_USER_AGENT = "agents-repo-source-url-health-mcp/1"


def _check_one(client: httpx.Client, url: str, timeout_sec: float) -> dict[str, Any]:
    started = time.monotonic()
    try:
        response = client.head(url, timeout=timeout_sec, follow_redirects=True)
        if response.status_code >= 405:
            response = client.get(url, timeout=timeout_sec, follow_redirects=True)
        elapsed_ms = round((time.monotonic() - started) * 1000, 1)
        return {
            "url": url,
            "ok": response.status_code < 400,
            "status_code": response.status_code,
            "final_url": str(response.url),
            "elapsed_ms": elapsed_ms,
            "error": None,
        }
    except httpx.HTTPError as exc:
        elapsed_ms = round((time.monotonic() - started) * 1000, 1)
        return {
            "url": url,
            "ok": False,
            "status_code": None,
            "final_url": None,
            "elapsed_ms": elapsed_ms,
            "error": f"{type(exc).__name__}: {exc}",
        }


@mcp.tool(annotations=_READ_ONLY_NETWORK)
def check_url_health(url: str, timeout_sec: float = _DEFAULT_TIMEOUT_SEC) -> dict[str, Any]:
    """Check whether a single URL is reachable (HEAD, falling back to GET on 405).

    Returns `{url, ok, status_code, final_url, elapsed_ms, error}`. `ok` is
    true only for 2xx/3xx-resolved responses (status_code < 400). Network
    failures (DNS, TLS, timeout, connection refused) are captured in `error`
    rather than raised, so batch callers never abort partway through.
    """
    with httpx.Client(headers={"User-Agent": _USER_AGENT}) as client:
        return _check_one(client, url, timeout_sec)


@mcp.tool(annotations=_READ_ONLY_NETWORK)
def check_urls_health(urls: list[str], timeout_sec: float = _DEFAULT_TIMEOUT_SEC) -> list[dict[str, Any]]:
    """Check reachability of multiple URLs sequentially (bounded to 25 per call).

    See `check_url_health` for the per-URL result shape. Raises `ValueError`
    if more than 25 URLs are supplied in one call — split larger batches
    across multiple calls to keep individual tool calls bounded.
    """
    if len(urls) > _MAX_BATCH:
        raise ValueError(f"Too many URLs ({len(urls)}); split into batches of {_MAX_BATCH} or fewer.")
    with httpx.Client(headers={"User-Agent": _USER_AGENT}) as client:
        return [_check_one(client, url, timeout_sec) for url in urls]


if __name__ == "__main__":
    mcp.run()
