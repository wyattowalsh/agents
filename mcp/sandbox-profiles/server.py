"""MCP server: sandbox-profiles.

Later-tier stub exposing read-only sandbox profile placeholders for MCP servers.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("Sandbox Profiles")

_READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}

_PROFILES: list[dict[str, Any]] = [
    {
        "id": "read-only-repo",
        "description": "Allow read tools against repo allowlist prefixes only",
        "network": "deny",
        "filesystem": "allowlist",
    },
    {
        "id": "harness-safe-mcp",
        "description": "Attach MCPHub harness-safe group without full schema tax",
        "network": "localhost-only",
        "filesystem": "deny",
    },
]


@mcp.tool(annotations=_READ_ONLY)
def list_sandbox_profiles() -> list[dict[str, Any]]:
    """List reference sandbox profiles for future MCP server hardening."""
    return _PROFILES


@mcp.tool(annotations=_READ_ONLY)
def profile_status() -> dict[str, str]:
    """Report stub status for sandbox profile enforcement."""
    return {"status": "stub", "message": "Sandbox enforcement is planned (W13)."}


if __name__ == "__main__":
    mcp.run()
