"""Codex adapter.

Placeholder — Codex requires complex TOML merging with section preservation.
Full implementation should handle:
- ``~/.codex/config.toml``  (base config + preserved user tables + managed MCP block)
- ``~/.codex/AGENTS.md``  (symlink)
- ``~/.codex/hooks.json``  (hook merge)
- ``config/codex-config.toml``  (sanitized repo copy)
"""

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
        """TODO: generate ``instructions/codex-global.md`` and repo config copy."""
        pass

    def sync_home(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        policy: dict[str, Any],
        fallbacks: dict[str, str],
        hook_registry: dict[str, Any],
    ) -> None:
        """TODO: merge TOML config with preserved user sections and managed MCP block."""
        pass
