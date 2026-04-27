"""GitHub Copilot adapter.

Placeholder — Copilot requires:
- ``~/.copilot/settings.json``  (model defaults, trusted folders, allowed URLs)
- ``~/.copilot/mcp-config.json``  (MCP with tool allowlists)
- ``~/.copilot/hooks.json``  (custom event mapping)
- ``.github/copilot-instructions.md``  (generated from global.md)
- ``.github/instructions/``  (rules from Claude rules)
- ``.github/hooks/policy.json``  (hook policy)
- Subagent env file
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wagents.platforms.base import HOME, PlatformAdapter, SyncContext

COPILOT_SETTINGS_PATH = HOME / ".copilot" / "settings.json"
COPILOT_MCP_PATH = HOME / ".copilot" / "mcp-config.json"


class Adapter(PlatformAdapter):
    name = "github-copilot"

    def home_config_paths(self) -> list[Path]:
        return [COPILOT_SETTINGS_PATH, COPILOT_MCP_PATH]

    def sync_repo(self, ctx: SyncContext, registry: dict[str, Any], hook_registry: dict[str, Any], policy: dict[str, Any]) -> None:
        """TODO: generate repo instructions, rules, and hooks."""
        pass

    def sync_home(self, ctx: SyncContext, registry: dict[str, Any], policy: dict[str, Any], fallbacks: dict[str, str], hook_registry: dict[str, Any]) -> None:
        """TODO: merge settings, MCP, subagent env, and agent symlinks."""
        pass
