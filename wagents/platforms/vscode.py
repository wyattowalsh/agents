"""VSCode / generic JSON MCP adapter.

VSCode uses the standard ``mcpServers`` JSON format both in the repo
(``.vscode/mcp.json``) and in user settings.  This is the simplest
possible adapter — it only writes repo-local MCP config.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wagents.platforms.base import (
    PlatformAdapter,
    SyncContext,
    enabled_registry_servers,
    render_env_value,
    replace_arg_placeholders,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

VSCODE_MCP_PATH = REPO_ROOT / ".vscode" / "mcp.json"
REPO_MCP_PATH = REPO_ROOT / "mcp.json"


class Adapter(PlatformAdapter):
    name = "vscode"

    def repo_config_paths(self) -> list[Path]:
        return [REPO_MCP_PATH, VSCODE_MCP_PATH]

    def sync_repo(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        hook_registry: dict[str, Any],
        policy: dict[str, Any],
    ) -> None:
        """Write repo ``mcp.json`` and ``.vscode/mcp.json``."""
        # Repo configs use placeholder env vars, not resolved secrets. Keep
        # generic mcp.json complete while allowing .vscode to suppress servers
        # owned by native VS Code/Copilot plugins.
        ctx.write_json(REPO_MCP_PATH, self.render_mcp(registry, fallbacks={}, harness="repo-mcp"))
        ctx.write_json(VSCODE_MCP_PATH, self.render_mcp(registry, fallbacks={}, harness="vscode"))

    def sync_home(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        policy: dict[str, Any],
        fallbacks: dict[str, str],
        hook_registry: dict[str, Any],
    ) -> None:
        """VSCode has no home-target sync; user settings are managed manually."""
        pass

    def render_mcp(
        self,
        registry: dict[str, Any],
        fallbacks: dict[str, str],
        harness: str | None = None,
    ) -> dict[str, Any]:
        """Return standard mcpServers with env placeholders (no secret resolution)."""
        servers: dict[str, Any] = {}
        for name, entry in enabled_registry_servers(registry, harness or self.name).items():
            server: dict[str, Any] = {
                "command": entry["command"],
                "args": replace_arg_placeholders(entry.get("args", []), {}, local_values=False),
            }
            if entry.get("env"):
                server["env"] = {
                    key: render_env_value(value, {}, local_values=False) for key, value in entry["env"].items()
                }
            if entry.get("timeout_ms"):
                server["timeout"] = entry["timeout_ms"]
            servers[name] = server
        return {"mcpServers": servers}
