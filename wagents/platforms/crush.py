"""Crush CLI adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from wagents.platforms.base import HOME, PlatformAdapter, SyncContext

if TYPE_CHECKING:
    from pathlib import Path

CRUSH_CONFIG_PATH = HOME / ".config" / "crush" / "crush.json"
CRUSH_SKILLS_DIR = HOME / ".config" / "crush" / "skills"


class Adapter(PlatformAdapter):
    name = "crush"

    def home_config_paths(self) -> list[Path]:
        return [CRUSH_CONFIG_PATH]

    def sync_repo(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        hook_registry: dict[str, Any],
        policy: dict[str, Any],
    ) -> None:
        """Crush has no repo-local projection."""

    def sync_home(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        policy: dict[str, Any],
        fallbacks: dict[str, str],
        hook_registry: dict[str, Any],
    ) -> None:
        from scripts.sync_agent_stack import (
            managed_registry_server_names,
            merge_server_root_config,
            render_flat_mcp,
            sync_skill_entries,
        )

        sync_ctx = cast("Any", ctx)
        merge_server_root_config(
            sync_ctx,
            CRUSH_CONFIG_PATH,
            "mcp",
            render_flat_mcp(registry, fallbacks, harness="crush"),
            managed_registry_server_names(registry, "crush"),
            create=True,
        )
        sync_skill_entries(sync_ctx, CRUSH_SKILLS_DIR)
