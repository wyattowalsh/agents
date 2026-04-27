"""OpenCode adapter.

Handles:
- ``~/.config/opencode/opencode.json``  (complex JSON merge: MCP, providers, instructions, skills, model defaults)
- ``opencode.json`` in repo root  (project config)
- Plugin deployment to ``~/.config/opencode/plugins/``
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
    merge_server_maps,
    merge_unique_path_strings,
    render_home_path,
    replace_arg_placeholders,
    resolve_env_value,
)

OPENCODE_CONFIG_PATH = HOME / ".config" / "opencode" / "opencode.json"
OPENCODE_REPO_CONFIG_PATH = REPO_ROOT / "opencode.json"
OPENCODE_PLUGINS_DIR = HOME / ".config" / "opencode" / "plugins"
OPENCODE_GLOBAL_MD = REPO_ROOT / "instructions" / "opencode-global.md"
GLOBAL_MD = REPO_ROOT / "instructions" / "global.md"
SKILLS_DIR = REPO_ROOT / "skills"


class Adapter(PlatformAdapter):
    name = "opencode"

    def home_config_paths(self) -> list[Path]:
        return [OPENCODE_CONFIG_PATH]

    def render_mcp(self, registry: dict[str, Any], fallbacks: dict[str, str]) -> dict[str, Any]:
        """OpenCode uses ``type: local|remote`` with ``command`` arrays or ``url``."""
        servers: dict[str, Any] = {}
        for name, entry in enabled_registry_servers(registry).items():
            args = replace_arg_placeholders(entry.get("args", []), fallbacks, local_values=True)
            remote_url = self._extract_remote_url(entry["command"], args)
            server: dict[str, Any]
            if remote_url:
                server = {"type": "remote", "url": remote_url, "enabled": True}
            else:
                server = {"type": "local", "command": [entry["command"], *args], "enabled": True}
            if entry.get("env"):
                server["environment"] = {
                    key: resolve_env_value(value["env_var"], fallbacks)
                    for key, value in entry["env"].items()
                }
            servers[name] = server
        return servers  # note: OpenCode nests under "mcp", not "mcpServers"

    def sync_repo(self, ctx: SyncContext, registry: dict[str, Any], hook_registry: dict[str, Any], policy: dict[str, Any]) -> None:
        """Ensure repo ``opencode.json`` exists with base instructions and skills paths."""
        config: dict[str, Any] = {
            "$schema": "https://opencode.ai/config.json",
            "instructions": ["AGENTS.md", "instructions/opencode-global.md"],
            "skills": {"paths": ["skills"]},
        }
        if OPENCODE_REPO_CONFIG_PATH.exists():
            existing = load_json(OPENCODE_REPO_CONFIG_PATH)
            if isinstance(existing, dict):
                existing.setdefault("instructions", config["instructions"])
                existing.setdefault("skills", config["skills"])
                config = existing
        ctx.write_json(OPENCODE_REPO_CONFIG_PATH, config)

    def sync_home(self, ctx: SyncContext, registry: dict[str, Any], policy: dict[str, Any], fallbacks: dict[str, str], hook_registry: dict[str, Any]) -> None:
        if not OPENCODE_CONFIG_PATH.exists():
            return
        settings = load_json(OPENCODE_CONFIG_PATH)

        # -- MCP merge (OpenCode uses root key "mcp", not "mcpServers") --
        rendered_mcp = self.render_mcp(registry, fallbacks)
        existing_mcp = settings.get("mcp")
        settings["mcp"] = merge_server_maps(
            rendered_mcp, existing_mcp if isinstance(existing_mcp, dict) else {}
        )

        # -- Instructions paths --
        settings["instructions"] = merge_unique_path_strings(
            [render_home_path(GLOBAL_MD), render_home_path(OPENCODE_GLOBAL_MD)],
            settings.get("instructions"),
        )

        # -- Skills paths --
        skills = settings.get("skills")
        if not isinstance(skills, dict):
            skills = {}
            settings["skills"] = skills
        skills["paths"] = merge_unique_path_strings([render_home_path(SKILLS_DIR)], skills.get("paths"))

        # -- Model defaults --
        defaults = policy.get("model_defaults", {}).get("opencode", {})
        if "model" in defaults:
            settings["model"] = defaults["model"]
        if "small_model" in defaults:
            settings["small_model"] = defaults["small_model"]

        # -- Recursively update nested model refs in mode/agent configs --
        def _update_nested_model(obj: Any, model: str) -> None:
            if not isinstance(obj, dict):
                return
            for key, value in obj.items():
                if isinstance(value, dict):
                    if "model" in value:
                        value["model"] = model
                    if key in ("mode", "agent"):
                        _update_nested_model(value, model)

        if "model" in defaults:
            _update_nested_model(settings.get("mode"), defaults["model"])
            _update_nested_model(settings.get("agent"), defaults["model"])

        ctx.write_json(OPENCODE_CONFIG_PATH, settings)
        self._deploy_plugins(ctx)

    # -- internal helpers ----------------------------------------------

    @staticmethod
    def _extract_remote_url(command: str, args: list[Any]) -> str | None:
        if command != "npx":
            return None
        compact = [item for item in args if item != "-y"]
        if len(compact) == 2 and compact[0] == "mcp-remote" and isinstance(compact[1], str):
            return compact[1]
        return None

    def _deploy_plugins(self, ctx: SyncContext) -> None:
        """Copy repo plugins into OpenCode plugin directory."""
        source_dir = REPO_ROOT / "platforms" / "opencode" / "plugins"
        if not source_dir.exists():
            return
        OPENCODE_PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
        for plugin_file in source_dir.iterdir():
            if plugin_file.is_file():
                dest = OPENCODE_PLUGINS_DIR / plugin_file.name
                ctx.write_text(dest, plugin_file.read_text(encoding="utf-8"))
