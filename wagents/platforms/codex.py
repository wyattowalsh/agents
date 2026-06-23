"""Codex adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from wagents.platforms.base import HOME, PlatformAdapter, SyncContext

if TYPE_CHECKING:
    from pathlib import Path

CODEX_CONFIG_PATH = HOME / ".codex" / "config.toml"


class Adapter(PlatformAdapter):
    name = "codex"

    def home_config_paths(self) -> list[Path]:
        return [CODEX_CONFIG_PATH]

    def sync_repo(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        hook_registry: dict[str, Any],
        policy: dict[str, Any],
    ) -> None:
        from scripts.sync_agent_stack import generate_codex_global_instructions

        sync_ctx = cast("Any", ctx)
        generate_codex_global_instructions(sync_ctx)

    def sync_home(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        policy: dict[str, Any],
        fallbacks: dict[str, str],
        hook_registry: dict[str, Any],
    ) -> None:
        from scripts.sync_agent_stack import merge_codex_config, merge_codex_hooks, sync_codex_entrypoint

        sync_ctx = cast("Any", ctx)
        sync_codex_entrypoint(sync_ctx)
        merge_codex_config(sync_ctx, registry, policy, fallbacks)
        merge_codex_hooks(sync_ctx, hook_registry)
