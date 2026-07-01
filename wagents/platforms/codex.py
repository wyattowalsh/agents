"""Codex adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from wagents.platforms.base import HOME, PlatformAdapter, SyncContext

CODEX_CONFIG_PATH = HOME / ".codex" / "config.toml"
CODEX_REPO_HOOKS_PATH = Path(__file__).resolve().parents[2] / ".codex" / "hooks.json"


class Adapter(PlatformAdapter):
    name = "codex"

    def home_config_paths(self) -> list[Path]:
        return [CODEX_CONFIG_PATH]

    def render_hooks(self, hook_registry: dict[str, Any], *, repo_relative: bool = False) -> dict[str, Any] | None:
        from scripts.sync_agent_stack import render_codex_hooks

        return render_codex_hooks(hook_registry, repo_relative=repo_relative)

    def sync_repo(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        hook_registry: dict[str, Any],
        policy: dict[str, Any],
    ) -> None:
        from scripts.sync_agent_stack import generate_codex_global_instructions, merge_codex_hooks

        sync_ctx = cast("Any", ctx)
        generate_codex_global_instructions(sync_ctx)
        # Codex may evaluate project hook commands without using the repository
        # root as cwd, so local project hooks need absolute command paths.
        merge_codex_hooks(sync_ctx, hook_registry, path=CODEX_REPO_HOOKS_PATH)

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
