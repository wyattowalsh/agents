"""VSCode / generic JSON MCP adapter.

VSCode uses the standard ``mcpServers`` JSON format both in the repo
(``.vscode/mcp.json``) and in user settings.  This is the simplest
possible adapter — it only writes repo-local MCP config.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wagents.context import get_repo_root
from wagents.platforms.base import (
    PlatformAdapter,
    SyncContext,
    enabled_registry_servers,
    mcphub_bearer_env_var,
    mcphub_enabled,
    mcphub_endpoint_specs,
    mcphub_projection_mode,
    render_env_value,
    render_mcphub_stdio_server,
    replace_arg_placeholders,
)


def vscode_mcp_path() -> Path:
    return get_repo_root() / ".vscode" / "mcp.json"


def repo_mcp_path() -> Path:
    return get_repo_root() / "mcp.json"


class Adapter(PlatformAdapter):
    name = "vscode"

    def repo_config_paths(self) -> list[Path]:
        return [repo_mcp_path(), vscode_mcp_path()]

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
        ctx.write_json(repo_mcp_path(), self.render_mcp(registry, fallbacks={}, harness="repo-mcp"))
        ctx.write_json(vscode_mcp_path(), self.render_mcp(registry, fallbacks={}, harness="vscode"))

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
        if mcphub_enabled(registry):
            mode = mcphub_projection_mode(registry, harness or self.name, "remote-stdio")
            token_env = mcphub_bearer_env_var(registry)
            return {
                "mcpServers": {
                    spec["name"]: (
                        {
                            "type": "http",
                            "url": spec["url"],
                            "enabled": bool(spec["enabled"]),
                            "headers": {"Authorization": f"Bearer ${{{token_env}}}"},
                        }
                        if mode == "http"
                        else render_mcphub_stdio_server(
                            registry,
                            spec["url"],
                            fallbacks,
                            bool(spec["enabled"]),
                            local_values=False,
                        )
                    )
                    for spec in mcphub_endpoint_specs(registry, harness or self.name)
                }
            }

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
