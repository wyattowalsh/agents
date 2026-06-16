"""Gemini CLI / Antigravity adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wagents.platforms.base import HOME, REPO_ROOT, PlatformAdapter, SyncContext

GEMINI_SETTINGS_PATH = HOME / ".gemini" / "settings.json"
GEMINI_ENTRYPOINT_PATH = HOME / ".gemini" / "GEMINI.md"
GEMINI_GLOBAL_MD = REPO_ROOT / "instructions" / "gemini-cli-global.md"


class Adapter(PlatformAdapter):
    name = "gemini-cli"

    def home_config_paths(self) -> list[Path]:
        return [GEMINI_SETTINGS_PATH]

    def render_hooks(self, hook_registry: dict[str, Any]) -> dict[str, Any] | None:
        event_map = {
            "UserPromptSubmit": "BeforeAgent",
            "PreToolUse": "BeforeTool",
            "PostToolUse": "AfterTool",
            "Stop": "AfterAgent",
        }
        return self._render_standard_hooks(hook_registry, event_map)

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
        from scripts.sync_agent_stack import ensure_symlink, merge_gemini_settings

        ensure_symlink(ctx, GEMINI_ENTRYPOINT_PATH, GEMINI_GLOBAL_MD)
        merge_gemini_settings(ctx, registry, policy, fallbacks, hook_registry)

