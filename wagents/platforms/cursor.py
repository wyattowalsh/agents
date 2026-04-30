"""Cursor adapter.

Cursor uses the standard client MCP JSON format (same as Claude Desktop).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wagents.platforms.base import HOME, PlatformAdapter, SyncContext, load_json, merge_server_maps

CURSOR_MCP_PATH = HOME / ".cursor" / "mcp.json"


class Adapter(PlatformAdapter):
    name = "cursor"

    def home_config_paths(self) -> list[Path]:
        return [CURSOR_MCP_PATH]

    def sync_repo(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        hook_registry: dict[str, Any],
        policy: dict[str, Any],
    ) -> None:
        pass

    def sync_home(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        policy: dict[str, Any],
        fallbacks: dict[str, str],
        hook_registry: dict[str, Any],
    ) -> None:
        if not CURSOR_MCP_PATH.exists():
            return
        data = load_json(CURSOR_MCP_PATH)
        rendered = self.render_mcp(registry, fallbacks)["mcpServers"]
        existing = data.get("mcpServers")
        data["mcpServers"] = merge_server_maps(rendered, existing if isinstance(existing, dict) else {})
        ctx.write_json(CURSOR_MCP_PATH, data)
