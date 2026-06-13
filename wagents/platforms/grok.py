"""Grok Build CLI adapter.

Grok reads MCP servers from ``~/.grok/config.toml`` and project-scoped
``.grok/config.toml``. Sync logic lives in ``scripts/sync_agent_stack.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wagents.platforms.base import HOME, PlatformAdapter, SyncContext

REPO_ROOT = Path(__file__).resolve().parents[2]
GROK_CONFIG_PATH = HOME / ".grok" / "config.toml"
GROK_CONFIG_REPO_PATH = REPO_ROOT / ".grok" / "config.toml"


class Adapter(PlatformAdapter):
    name = "grok"

    def home_config_paths(self) -> list[Path]:
        return [GROK_CONFIG_PATH, GROK_CONFIG_REPO_PATH]

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
        pass
