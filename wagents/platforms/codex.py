"""Codex adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wagents.platforms.base import HOME, PlatformAdapter, SyncContext

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

        generate_codex_global_instructions(ctx)

    def sync_home(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        policy: dict[str, Any],
        fallbacks: dict[str, str],
        hook_registry: dict[str, Any],
    ) -> None:
        from scripts.sync_agent_stack import merge_codex_config, merge_codex_hooks, sync_codex_entrypoint

        sync_codex_entrypoint(ctx)
        merge_codex_config(ctx, registry, policy, fallbacks)
        merge_codex_hooks(ctx, hook_registry)

