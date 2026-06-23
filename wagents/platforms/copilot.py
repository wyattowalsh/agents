"""GitHub Copilot adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from wagents.platforms.base import HOME, PlatformAdapter, SyncContext

if TYPE_CHECKING:
    from pathlib import Path

COPILOT_SETTINGS_PATH = HOME / ".copilot" / "settings.json"
COPILOT_MCP_PATH = HOME / ".copilot" / "mcp-config.json"


class Adapter(PlatformAdapter):
    name = "github-copilot"

    def home_config_paths(self) -> list[Path]:
        return [COPILOT_SETTINGS_PATH, COPILOT_MCP_PATH]

    def sync_repo(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        hook_registry: dict[str, Any],
        policy: dict[str, Any],
    ) -> None:
        from scripts.sync_agent_stack import (
            generate_copilot_hooks,
            generate_copilot_repo_instructions,
            generate_copilot_rule_instructions,
        )

        sync_ctx = cast("Any", ctx)
        generate_copilot_repo_instructions(sync_ctx)
        generate_copilot_rule_instructions(sync_ctx)
        generate_copilot_hooks(sync_ctx, hook_registry)

    def sync_home(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        policy: dict[str, Any],
        fallbacks: dict[str, str],
        hook_registry: dict[str, Any],
    ) -> None:
        from scripts.sync_agent_stack import (
            merge_copilot_config,
            render_copilot_mcp,
            sync_copilot_agents,
            sync_copilot_subagent_env,
        )

        sync_ctx = cast("Any", ctx)
        merge_copilot_config(sync_ctx, policy)
        sync_copilot_subagent_env(sync_ctx, policy)
        ctx.write_json(COPILOT_MCP_PATH, render_copilot_mcp(registry, fallbacks, "github-copilot-cli"))
        sync_copilot_agents(sync_ctx)
