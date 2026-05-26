"""MCPHub control-plane metadata MCP server."""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("MCPHub")

ROOT = Path(__file__).resolve().parents[2]
SETTINGS_PATH = ROOT / "mcp" / "mcphub" / "mcp_settings.json"


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def mcphub_status() -> dict[str, str | bool]:
    """Return local MCPHub scaffold status and config location.

    Use this tool when checking whether the repo-owned MCPHub scaffold is
    present and where its generated settings file lives. It does not start,
    stop, mutate, or validate the running MCPHub process. It returns static
    local paths and endpoint metadata that clients can use for follow-up checks.
    """
    return {
        "name": "mcphub",
        "description": "Local MCP control-plane configuration scaffold.",
        "settings_path": str(SETTINGS_PATH),
        "settings_exists": SETTINGS_PATH.exists(),
        "managed_url": "http://127.0.0.1:46683",
        "mcp_endpoint": "http://127.0.0.1:46683/mcp",
    }
