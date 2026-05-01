"""Gemini CLI / Antigravity adapter.

Placeholder — Gemini requires:
- ``~/.gemini/settings.json``  (MCP, hooks, model defaults, mirrors some Claude settings)
- ``~/.gemini/GEMINI.md``  (entrypoint)
- ``~/.gemini/antigravity/mcp_config.json``  (Antigravity MCP)
- ``~/.gemini/extensions/.../mcp_config.json``  (Extension MCP)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wagents.platforms.base import HOME, PlatformAdapter, SyncContext

GEMINI_SETTINGS_PATH = HOME / ".gemini" / "settings.json"


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
        """TODO: merge settings, MCP, hooks, and entrypoint."""
        pass
