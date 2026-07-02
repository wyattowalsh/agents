"""MCP server: oauth-reference.

Read-only reference shape for OAuth-protected MCP servers. Documents expected
tool annotations and auth placeholders without performing OAuth flows or network I/O.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("OAuth Reference")

_READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


@mcp.tool(annotations=_READ_ONLY)
def oauth_reference_shape() -> dict[str, Any]:
    """Return the repo reference schema for OAuth MCP server configuration.

    Use this when authoring OAuth-backed MCP entries in `config/mcp-registry.json`.
    Values are placeholders — live credentials belong in user-owned env files only.
    """
    return {
        "auth": {
            "type": "oauth2",
            "authorizationUrl": "https://provider.example/oauth/authorize",
            "tokenUrl": "https://provider.example/oauth/token",
            "scopes": ["read"],
        },
        "env_placeholders": ["MCP_OAUTH_CLIENT_ID", "MCP_OAUTH_CLIENT_SECRET"],
        "notes": [
            "Never commit OAuth client secrets to tracked config.",
            "Prefer MCPHub bearer auth for local control-plane endpoints.",
            "Mark read-only tools with readOnlyHint annotations.",
        ],
    }


@mcp.tool(annotations=_READ_ONLY)
def list_reference_tools() -> list[dict[str, str]]:
    """List the reference tool ids shipped by this scaffold server."""
    return [
        {"name": "oauth_reference_shape", "purpose": "Document OAuth MCP config shape"},
        {"name": "list_reference_tools", "purpose": "Enumerate reference tool ids"},
    ]


if __name__ == "__main__":
    mcp.run()
