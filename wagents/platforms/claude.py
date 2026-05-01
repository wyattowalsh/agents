"""Claude Code adapter.

Handles:
- ``~/.claude/settings.json``  (permissions + hooks merge)
- ``~/.claude/settings.local.json``  (enabledMcpjsonServers filter)
- ``~/.claude/CLAUDE.md``  (symlink to global instructions)
- ``~/Library/Application Support/Claude/claude_desktop_config.json``  (MCP)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wagents.platforms.base import (
    HOME,
    REPO_ROOT,
    PlatformAdapter,
    SyncContext,
    enabled_registry_servers,
    load_json,
    merge_hook_groups,
    merge_server_maps,
)

CLAUDE_SETTINGS_PATH = HOME / ".claude" / "settings.json"
CLAUDE_SETTINGS_LOCAL_PATH = HOME / ".claude" / "settings.local.json"
CLAUDE_DESKTOP_CONFIG_PATH = HOME / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
CLAUDE_ENTRYPOINT_PATH = HOME / ".claude" / "CLAUDE.md"
GLOBAL_MD = REPO_ROOT / "instructions" / "global.md"
HOOK_COMMAND_MARKER = "wagents-hook.py"


class Adapter(PlatformAdapter):
    name = "claude-code"

    def home_config_paths(self) -> list[Path]:
        return [CLAUDE_SETTINGS_PATH, CLAUDE_DESKTOP_CONFIG_PATH]

    def render_hooks(self, hook_registry: dict[str, Any]) -> dict[str, Any] | None:
        event_map = {
            "UserPromptSubmit": "UserPromptSubmit",
            "PreToolUse": "PreToolUse",
            "PostToolUse": "PostToolUse",
            "Stop": "Stop",
        }
        return self._render_standard_hooks(hook_registry, event_map)

    def sync_repo(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        hook_registry: dict[str, Any],
        policy: dict[str, Any],
    ) -> None:
        """Claude has no repo-local config files beyond the root entrypoint."""
        pass

    def sync_home(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        policy: dict[str, Any],
        fallbacks: dict[str, str],
        hook_registry: dict[str, Any],
    ) -> None:
        self._sync_entrypoint(ctx)
        self._merge_settings(ctx, policy, hook_registry)
        self._merge_settings_local(ctx, registry)
        self._merge_desktop_mcp(ctx, registry, fallbacks)

    # -- internal ------------------------------------------------------

    def _sync_entrypoint(self, ctx: SyncContext) -> None:
        if not ctx.apply:
            ctx.note(f"symlink {CLAUDE_ENTRYPOINT_PATH} -> {GLOBAL_MD}")
            return
        CLAUDE_ENTRYPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
        if CLAUDE_ENTRYPOINT_PATH.exists() or CLAUDE_ENTRYPOINT_PATH.is_symlink():
            CLAUDE_ENTRYPOINT_PATH.unlink()
        CLAUDE_ENTRYPOINT_PATH.symlink_to(GLOBAL_MD.resolve())

    def _merge_settings(self, ctx: SyncContext, policy: dict[str, Any], hook_registry: dict[str, Any]) -> None:
        if not CLAUDE_SETTINGS_PATH.exists():
            return
        settings = load_json(CLAUDE_SETTINGS_PATH)
        # Permissions
        allow = settings.setdefault("permissions", {}).setdefault("allow", [])
        for domain in policy.get("docs_domains", []):
            token = f"WebFetch(domain:{domain})"
            if token not in allow:
                allow.append(token)
        # Hooks
        rendered = self.render_hooks(hook_registry)
        if rendered:
            settings["hooks"] = merge_hook_groups(settings.get("hooks", {}), rendered)
            # Rewrite legacy .claude/hooks/ paths to repo hooks/
            for hook_groups in settings.get("hooks", {}).values():
                for group in hook_groups:
                    for hook in group.get("hooks", []):
                        command = hook.get("command")
                        if not isinstance(command, str) or ".claude/hooks/" not in command:
                            continue
                        hook_name = command.split(".claude/hooks/", 1)[1].split()[0]
                        suffix = command.split(hook_name, 1)[1]
                        hook["command"] = f"{REPO_ROOT / 'hooks' / hook_name}{suffix}"
        ctx.write_json(CLAUDE_SETTINGS_PATH, settings)

    def _merge_settings_local(self, ctx: SyncContext, registry: dict[str, Any]) -> None:
        if not CLAUDE_SETTINGS_LOCAL_PATH.exists():
            return
        settings = load_json(CLAUDE_SETTINGS_LOCAL_PATH)
        enabled = settings.get("enabledMcpjsonServers")
        if not isinstance(enabled, list):
            return
        valid = set(enabled_registry_servers(registry, "claude-code"))
        filtered = [name for name in enabled if isinstance(name, str) and name in valid]
        # Preserve order, dedupe
        seen: set[str] = set()
        deduped: list[str] = []
        for name in filtered:
            if name not in seen:
                seen.add(name)
                deduped.append(name)
        settings["enabledMcpjsonServers"] = deduped
        ctx.write_json(CLAUDE_SETTINGS_LOCAL_PATH, settings)

    def _merge_desktop_mcp(self, ctx: SyncContext, registry: dict[str, Any], fallbacks: dict[str, str]) -> None:
        if not CLAUDE_DESKTOP_CONFIG_PATH.exists():
            return
        rendered = self.render_mcp(registry, fallbacks, harness="claude-desktop")["mcpServers"]
        data = load_json(CLAUDE_DESKTOP_CONFIG_PATH)
        existing = data.get("mcpServers", {})
        data["mcpServers"] = merge_server_maps(rendered, existing)
        ctx.write_json(CLAUDE_DESKTOP_CONFIG_PATH, data)
