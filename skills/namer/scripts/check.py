#!/usr/bin/env python3
"""Platform availability checker for name candidates.

Makes async HTTP requests to check domain, dev registry, and social
platform availability. Outputs JSON to stdout, warnings to stderr.

Usage:
    uv run python skills/namer/scripts/check.py check-domain neon flux
    uv run python skills/namer/scripts/check.py check-dev neon flux
    uv run python skills/namer/scripts/check.py check-social neon flux
    uv run python skills/namer/scripts/check.py check-all neon flux
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from typing import Annotated

import httpx
import typer
from loguru import logger

# ---------------------------------------------------------------------------
# Loguru: warnings/errors to stderr only
# ---------------------------------------------------------------------------
logger.remove()
logger.add(sys.stderr, level="WARNING", format="{level}: {message}")

app = typer.Typer(help="Check name availability across domains, dev registries, and social platforms.")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USER_AGENT = "namer-skill/1.0"
REQUEST_TIMEOUT = 10.0
MAX_CONCURRENT = 8

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _client(*, follow_redirects: bool = False) -> httpx.AsyncClient:
    """Create an async HTTP client."""
    return httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=follow_redirects,
    )


async def _check_url(
    client: httpx.AsyncClient,
    url: str,
    *,
    available_on_404: bool = True,
) -> dict:
    """GET a URL. Return availability result dict.

    When available_on_404=True, a 404 response means the resource is available.
    """
    try:
        resp = await client.get(url)
        if resp.status_code == 404:
            return {"available": available_on_404, "method": "api", "confidence": "high", "status": 404}
        if 200 <= resp.status_code < 300:
            return {
                "available": not available_on_404, "method": "api", "confidence": "high", "status": resp.status_code,
            }
        if resp.status_code == 429:
            logger.warning(f"Rate limited on {url}")
            return {"available": None, "method": "api", "confidence": "none", "error": "rate_limited"}
        return {"available": None, "method": "api", "confidence": "none", "error": f"http_{resp.status_code}"}
    except httpx.TimeoutException:
        logger.warning(f"Timeout checking {url}")
        return {"available": None, "method": "api", "confidence": "none", "error": "timeout"}
    except httpx.HTTPError as exc:
        logger.warning(f"HTTP error checking {url}: {exc}")
        return {"available": None, "method": "api", "confidence": "none", "error": str(exc)}


# ---------------------------------------------------------------------------
# Domain checks (RDAP)
# ---------------------------------------------------------------------------


async def _check_domain_rdap(client: httpx.AsyncClient, name: str, tld: str) -> dict:
    """Check domain availability via RDAP."""
    rdap_base = {
        "com": "https://rdap.verisign.com/com/v1/domain",
        "net": "https://rdap.verisign.com/net/v1/domain",
        "dev": "https://rdap.nic.google/domain",
    }
    base = rdap_base.get(tld)
    if not base:
        return {"available": None, "method": "rdap", "confidence": "none", "error": f"unsupported_tld_{tld}"}

    url = f"{base}/{name}.{tld}"
    try:
        resp = await client.get(url, follow_redirects=True)
        if resp.status_code == 404:
            return {"available": True, "method": "rdap", "confidence": "high"}
        if 200 <= resp.status_code < 300:
            return {"available": False, "method": "rdap", "confidence": "high"}
        return {"available": None, "method": "rdap", "confidence": "none", "error": f"http_{resp.status_code}"}
    except httpx.TimeoutException:
        logger.warning(f"Timeout checking RDAP for {name}.{tld}")
        return {"available": None, "method": "rdap", "confidence": "none", "error": "timeout"}
    except httpx.HTTPError as exc:
        logger.warning(f"HTTP error checking RDAP for {name}.{tld}: {exc}")
        return {"available": None, "method": "rdap", "confidence": "none", "error": str(exc)}


async def _check_domains(client: httpx.AsyncClient, name: str) -> dict:
    """Check .com, .net, and .dev domain availability in parallel."""
    com, net, dev = await asyncio.gather(
        _check_domain_rdap(client, name, "com"),
        _check_domain_rdap(client, name, "net"),
        _check_domain_rdap(client, name, "dev"),
    )
    return {"domain_com": com, "domain_net": net, "domain_dev": dev}


# ---------------------------------------------------------------------------
# Dev registry checks
# ---------------------------------------------------------------------------


async def _check_github(client: httpx.AsyncClient, name: str) -> dict:
    """Check GitHub username/org availability. 404 = available."""
    return await _check_url(client, f"https://api.github.com/users/{name}", available_on_404=True)


async def _check_npm(client: httpx.AsyncClient, name: str) -> dict:
    """Check npm package availability. 404 = available."""
    return await _check_url(client, f"https://registry.npmjs.org/{name}", available_on_404=True)


async def _check_pypi(client: httpx.AsyncClient, name: str) -> dict:
    """Check PyPI package availability. 404 = available."""
    return await _check_url(client, f"https://pypi.org/pypi/{name}/json", available_on_404=True)


async def _check_crates(client: httpx.AsyncClient, name: str) -> dict:
    """Check crates.io crate availability. 404 = available."""
    return await _check_url(client, f"https://crates.io/api/v1/crates/{name}", available_on_404=True)


async def _check_dev_registries(client: httpx.AsyncClient, name: str) -> dict:
    """Check all dev registries for a name."""
    github, npm, pypi, crates = await asyncio.gather(
        _check_github(client, name),
        _check_npm(client, name),
        _check_pypi(client, name),
        _check_crates(client, name),
    )
    return {
        "github": github,
        "npm": npm,
        "pypi": pypi,
        "crates": crates,
    }


# ---------------------------------------------------------------------------
# Social platform checks
# ---------------------------------------------------------------------------


async def _check_reddit(client: httpx.AsyncClient, name: str) -> dict:
    """Check Reddit username availability via their API."""
    url = f"https://www.reddit.com/api/username_available.json?user={name}"
    try:
        resp = await client.get(url)
        if resp.status_code == 200:
            body = resp.text.strip().lower()
            if body == "true":
                return {"available": True, "method": "api", "confidence": "high"}
            if body == "false":
                return {"available": False, "method": "api", "confidence": "high"}
            return {"available": None, "method": "api", "confidence": "low", "error": f"unexpected_body: {body[:50]}"}
        if resp.status_code == 429:
            logger.warning("Rate limited on Reddit API")
            return {"available": None, "method": "api", "confidence": "none", "error": "rate_limited"}
        return {"available": None, "method": "api", "confidence": "none", "error": f"http_{resp.status_code}"}
    except httpx.TimeoutException:
        logger.warning(f"Timeout checking Reddit for {name}")
        return {"available": None, "method": "api", "confidence": "none", "error": "timeout"}
    except httpx.HTTPError as exc:
        logger.warning(f"HTTP error checking Reddit for {name}: {exc}")
        return {"available": None, "method": "api", "confidence": "none", "error": str(exc)}


async def _check_bluesky(client: httpx.AsyncClient, name: str) -> dict:
    """Check Bluesky handle availability via AT Protocol.

    A 400 response with a handle-resolution error means the handle is available.
    Other 400 responses (malformed request) are treated as unknown.
    """
    url = f"https://bsky.social/xrpc/com.atproto.identity.resolveHandle?handle={name}.bsky.social"
    try:
        resp = await client.get(url)
        if 200 <= resp.status_code < 300:
            return {"available": False, "method": "api", "confidence": "high"}
        if resp.status_code == 400:
            # Parse body to distinguish "handle not found" from "malformed request"
            try:
                body = resp.json()
                error_msg = body.get("message", "").lower()
                if "unable to resolve" in error_msg or "not found" in error_msg or "handle" in error_msg:
                    return {"available": True, "method": "api", "confidence": "high"}
            except (ValueError, KeyError):
                pass
            # Could not confirm handle-not-found — treat as medium confidence
            return {"available": True, "method": "api", "confidence": "medium"}
        if resp.status_code == 429:
            logger.warning("Rate limited on Bluesky API")
            return {"available": None, "method": "api", "confidence": "none", "error": "rate_limited"}
        return {"available": None, "method": "api", "confidence": "none", "error": f"http_{resp.status_code}"}
    except httpx.TimeoutException:
        logger.warning(f"Timeout checking Bluesky for {name}")
        return {"available": None, "method": "api", "confidence": "none", "error": "timeout"}
    except httpx.HTTPError as exc:
        logger.warning(f"HTTP error checking Bluesky for {name}: {exc}")
        return {"available": None, "method": "api", "confidence": "none", "error": str(exc)}


async def _check_social(client: httpx.AsyncClient, name: str) -> dict:
    """Check all social platforms for a name."""
    reddit, bluesky = await asyncio.gather(
        _check_reddit(client, name),
        _check_bluesky(client, name),
    )
    return {
        "reddit": reddit,
        "bluesky": bluesky,
    }


# ---------------------------------------------------------------------------
# Combined check
# ---------------------------------------------------------------------------


async def _check_all_for_name(client: httpx.AsyncClient, name: str) -> dict:
    """Run all checks (domain + dev + social) for a single name."""
    domains, dev, social = await asyncio.gather(
        _check_domains(client, name),
        _check_dev_registries(client, name),
        _check_social(client, name),
    )
    combined = {}
    combined.update(domains)
    combined.update(dev)
    combined.update(social)
    return combined


async def _run_checks(names: list[str], checker) -> dict:
    """Run a checker coroutine for each name with concurrency control."""
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    errors: list[str] = []
    results: dict[str, dict] = {}

    async with _client() as shared_client:
        async def _bounded(name: str):
            async with semaphore:
                try:
                    results[name] = await checker(shared_client, name)
                except Exception as exc:
                    logger.warning(f"Unexpected error checking {name}: {exc}")
                    errors.append(f"{name}: {exc}")
                    results[name] = {"check_failed": True, "error": str(exc)}

        await asyncio.gather(*[_bounded(n) for n in names])

    return {
        "results": results,
        "checked_at": datetime.now(UTC).isoformat(),
        "errors": errors,
    }


def _output(data: dict) -> None:
    """Write JSON result to stdout."""
    json.dump(data, sys.stdout, indent=2)
    sys.stdout.write("\n")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command("check-domain")
def check_domain(
    names: Annotated[list[str], typer.Argument(help="Names to check domain availability for.")],
) -> None:
    """Check .com, .net, and .dev domain availability via RDAP."""
    if not names:
        logger.error("Provide at least one name to check.")
        raise typer.Exit(code=1)
    data = asyncio.run(_run_checks(names, _check_domains))
    _output(data)


@app.command("check-dev")
def check_dev(
    names: Annotated[list[str], typer.Argument(help="Names to check on dev registries.")],
) -> None:
    """Check GitHub, npm, PyPI, and Crates.io availability."""
    if not names:
        logger.error("Provide at least one name to check.")
        raise typer.Exit(code=1)
    data = asyncio.run(_run_checks(names, _check_dev_registries))
    _output(data)


@app.command("check-social")
def check_social(
    names: Annotated[list[str], typer.Argument(help="Names to check on social platforms.")],
) -> None:
    """Check Reddit and Bluesky handle availability."""
    if not names:
        logger.error("Provide at least one name to check.")
        raise typer.Exit(code=1)
    data = asyncio.run(_run_checks(names, _check_social))
    _output(data)


@app.command("check-all")
def check_all(
    names: Annotated[list[str], typer.Argument(help="Names to check across all platforms.")],
) -> None:
    """Run all availability checks: domains, dev registries, and social platforms."""
    if not names:
        logger.error("Provide at least one name to check.")
        raise typer.Exit(code=1)
    data = asyncio.run(_run_checks(names, _check_all_for_name))
    _output(data)


if __name__ == "__main__":
    app()
