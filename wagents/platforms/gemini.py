"""Gemini CLI / Antigravity adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from wagents.hooks.render import enabled_hooks_for_harness, render_hook_command
from wagents.platforms.base import HOME, REPO_ROOT, PlatformAdapter, SyncContext, load_json, merge_hook_groups

if TYPE_CHECKING:
    from pathlib import Path

GEMINI_SETTINGS_PATH = HOME / ".gemini" / "settings.json"
GEMINI_ENTRYPOINT_PATH = HOME / ".gemini" / "GEMINI.md"
GEMINI_GLOBAL_MD = REPO_ROOT / "instructions" / "gemini-cli-global.md"
GEMINI_REPO_SETTINGS_PATH = REPO_ROOT / ".gemini" / "settings.json"


class Adapter(PlatformAdapter):
    name = "gemini-cli"

    def home_config_paths(self) -> list[Path]:
        return [GEMINI_SETTINGS_PATH]

    def render_hooks(self, hook_registry: dict[str, Any], *, repo_relative: bool = False) -> dict[str, Any] | None:
        event_map = {
            "SessionStart": "sessionStart",
            "UserPromptSubmit": "BeforeAgent",
            "PreToolUse": "BeforeTool",
            "PostToolUse": "AfterTool",
            "SessionEnd": "sessionEnd",
            "Stop": "AfterAgent",
        }
        repo_root = "." if repo_relative else str(REPO_ROOT)
        rendered: dict[str, list[dict[str, Any]]] = {}
        for hook in enabled_hooks_for_harness(hook_registry, self.name):
            event = event_map.get(str(hook.get("logical_event")))
            if not event:
                continue
            config: dict[str, Any] = {
                "type": "command",
                "command": render_hook_command(hook, self.name, repo_root=repo_root),
                "name": hook["id"],
                "timeout": int(hook.get("timeout", 5)) * 1000,
                "description": hook.get("description", hook["id"]),
            }
            group: dict[str, Any] = {"hooks": [config], "sequential": True}
            if hook.get("matcher"):
                group["matcher"] = hook["matcher"]
            rendered.setdefault(event, []).append(group)
        return {"hooks": rendered} if rendered else None

    def sync_repo(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        hook_registry: dict[str, Any],
        policy: dict[str, Any],
    ) -> None:
        settings = load_json(GEMINI_REPO_SETTINGS_PATH) if GEMINI_REPO_SETTINGS_PATH.exists() else {}
        rendered = self.render_hooks(hook_registry, repo_relative=True)
        if rendered:
            settings["hooks"] = merge_hook_groups(settings.get("hooks", {}), rendered)
        ctx.write_json(GEMINI_REPO_SETTINGS_PATH, settings)

    def sync_home(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        policy: dict[str, Any],
        fallbacks: dict[str, str],
        hook_registry: dict[str, Any],
    ) -> None:
        from scripts.sync_agent_stack import ensure_symlink, merge_gemini_settings

        sync_ctx = cast("Any", ctx)
        ensure_symlink(sync_ctx, GEMINI_ENTRYPOINT_PATH, GEMINI_GLOBAL_MD)
        merge_gemini_settings(sync_ctx, registry, policy, fallbacks, hook_registry)
