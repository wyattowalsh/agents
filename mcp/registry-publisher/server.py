"""MCP server: registry-publisher.

Later-tier stub for publishing MCP registry artifacts. Read-only inventory only.
"""

from __future__ import annotations

import json
from typing import Any

from fastmcp import FastMCP

from wagents import ROOT

mcp = FastMCP("Registry Publisher")

_READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


@mcp.tool(annotations=_READ_ONLY)
def registry_snapshot() -> dict[str, Any]:
    """Return a read-only summary of `config/mcp-registry.json` server ids."""
    path = ROOT / "config" / "mcp-registry.json"
    if not path.is_file():
        return {"ok": False, "error": "missing config/mcp-registry.json"}
    data = json.loads(path.read_text(encoding="utf-8"))
    servers = data.get("servers") or data.get("mcpServers") or {}
    if isinstance(servers, dict):
        ids = sorted(servers.keys())
    elif isinstance(servers, list):
        ids = sorted(str(row.get("id", row.get("name", ""))) for row in servers if isinstance(row, dict))
    else:
        ids = []
    return {"ok": True, "server_count": len(ids), "server_ids": ids[:50], "truncated": len(ids) > 50}


@mcp.tool(annotations=_READ_ONLY)
def publish_status() -> dict[str, str]:
    """Report that live registry publishing is not implemented in this stub."""
    return {
        "status": "stub",
        "message": "Registry publishing is planned (W13). Use config/mcp-registry.json as SSOT.",
    }


if __name__ == "__main__":
    mcp.run()
