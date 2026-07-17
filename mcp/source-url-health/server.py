"""Compatibility launcher for the namespaced source URL health MCP package."""

from __future__ import annotations

import sys
from pathlib import Path

from fastmcp import FastMCP

# Path-based MCP loaders do not add this file's directory to ``sys.path``.
# Add only the project root, then import through the collision-safe package.
_PROJECT_DIR = Path(__file__).resolve().parent
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

from mcp_source_url_health.server import (  # noqa: E402
    PinnedHttpxClient,
    check_url_health,
    check_urls_health,
    mcp,
    validate_url_for_probe,
)

if not isinstance(mcp, FastMCP):
    raise TypeError("source URL health package did not export a FastMCP server")

__all__ = [
    "PinnedHttpxClient",
    "check_url_health",
    "check_urls_health",
    "mcp",
    "validate_url_for_probe",
]

if __name__ == "__main__":
    mcp.run()
