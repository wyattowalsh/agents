"""OpenCode adapter.

Handles:
- ``~/.config/opencode/opencode.json``  (complex JSON merge: MCP, providers, instructions, skills)
- ``opencode.json`` in repo root  (project config)
- Plugin deployment to ``~/.config/opencode/plugins/``
"""

from __future__ import annotations

import os
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
    render_env_value,
    render_home_path,
    replace_arg_placeholders,
)

OPENCODE_CONFIG_PATH = HOME / ".config" / "opencode" / "opencode.json"
OPENCODE_DCP_CONFIG_PATH = HOME / ".config" / "opencode" / "dcp.jsonc"
OPENCODE_DCP_TEMPLATE_PATH = REPO_ROOT / "config" / "opencode-dcp.jsonc"
OPENCODE_REPO_CONFIG_PATH = REPO_ROOT / "opencode.json"
OPENCODE_PLUGINS_DIR = HOME / ".config" / "opencode" / "plugins"
OPENCODE_GLOBAL_MD = REPO_ROOT / "instructions" / "opencode-global.md"
GLOBAL_MD = REPO_ROOT / "instructions" / "global.md"
CHROME_DEVTOOLS_LAUNCHER = "/Users/ww/.config/opencode/tools/chrome-devtools-launcher.sh"
SKILLS_DIR = REPO_ROOT / "skills"

_DCP_MODEL_LIMIT_KEYS = {"modelMaxLimits", "modelMinLimits"}
_OPENCODE_MODEL_KEYS = {"model", "small_model", "mode", "agent"}


def _local_llm_provider(policy: dict[str, Any], provider: str) -> dict[str, Any] | None:
    providers = policy.get("local_llm_providers")
    if not isinstance(providers, dict):
        return None
    config = providers.get(provider)
    return config if isinstance(config, dict) else None


def _resolve_local_llm_base_url(provider_config: dict[str, Any], fallbacks: dict[str, str]) -> str:
    env_names = [provider_config.get("base_url_env")]
    aliases = provider_config.get("base_url_env_aliases", [])
    if isinstance(aliases, list):
        env_names.extend(aliases)
    for env_name in env_names:
        if not isinstance(env_name, str):
            continue
        value = os.environ.get(env_name) or fallbacks.get(env_name)
        if value:
            return value
    default = provider_config.get("default_base_url")
    return str(default or "")


def _render_lmstudio_provider(policy: dict[str, Any], fallbacks: dict[str, str]) -> dict[str, Any] | None:
    provider = _local_llm_provider(policy, "lmstudio")
    if not provider:
        return None
    opencode_raw = provider.get("opencode")
    opencode: dict[str, Any] = opencode_raw if isinstance(opencode_raw, dict) else {}
    models_raw = opencode.get("models")
    models: dict[str, Any] = models_raw if isinstance(models_raw, dict) else {}
    return {
        "npm": opencode.get("npm", "@ai-sdk/openai-compatible"),
        "name": provider.get("name", "LM Studio (local)"),
        "options": {
            "baseURL": _resolve_local_llm_base_url(provider, fallbacks),
        },
        "models": models or {str(provider.get("default_model", "local-model")): {"name": "LM Studio Local Model"}},
    }


def _merge_provider_entry(existing: Any, rendered: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(existing, dict):
        existing = {}
    merged = dict(existing)
    merged["npm"] = rendered["npm"]
    merged["name"] = rendered["name"]
    existing_options_raw = existing.get("options")
    existing_options: dict[str, Any] = existing_options_raw if isinstance(existing_options_raw, dict) else {}
    merged["options"] = {**existing_options, **rendered["options"]}
    existing_models_raw = existing.get("models")
    existing_models: dict[str, Any] = existing_models_raw if isinstance(existing_models_raw, dict) else {}
    merged["models"] = {**rendered["models"], **existing_models}
    return merged


def _merge_dict_defaults(defaults: dict[str, Any], existing: dict[str, Any]) -> dict[str, Any]:
    merged = dict(defaults)
    for key, value in existing.items():
        default_value = merged.get(key)
        if isinstance(default_value, dict) and isinstance(value, dict):
            merged[key] = _merge_dict_defaults(default_value, value)
        else:
            merged[key] = value
    return merged


def _load_dcp_template() -> dict[str, Any]:
    if not OPENCODE_DCP_TEMPLATE_PATH.exists():
        return {}
    template = load_json(OPENCODE_DCP_TEMPLATE_PATH)
    return template if isinstance(template, dict) else {}


def _render_dcp_config(existing: dict[str, Any]) -> dict[str, Any]:
    config = _merge_dict_defaults(_load_dcp_template(), existing)
    for key in _OPENCODE_MODEL_KEYS:
        config.pop(key, None)
    compress = config.get("compress")
    if isinstance(compress, dict):
        for key in _DCP_MODEL_LIMIT_KEYS:
            compress.pop(key, None)
    return config


class Adapter(PlatformAdapter):
    name = "opencode"

    def home_config_paths(self) -> list[Path]:
        return [OPENCODE_CONFIG_PATH, OPENCODE_DCP_CONFIG_PATH]

    def render_mcp(
        self,
        registry: dict[str, Any],
        fallbacks: dict[str, str],
        harness: str | None = None,
    ) -> dict[str, Any]:
        """OpenCode uses ``type: local|remote`` with ``command`` arrays or ``url``."""
        servers: dict[str, Any] = {}
        for name, entry in enabled_registry_servers(registry, harness or self.name).items():
            args = replace_arg_placeholders(entry.get("args", []), fallbacks, local_values=True)
            remote_url = self._extract_remote_url(entry["command"], args)
            server: dict[str, Any]
            if remote_url:
                server = {"type": "remote", "url": remote_url, "enabled": True}
            else:
                server = {"type": "local", "command": [entry["command"], *args], "enabled": True}
            if entry.get("env"):
                server["environment"] = {
                    key: render_env_value(value, fallbacks, local_values=True) for key, value in entry["env"].items()
                }
            servers[name] = server
        return servers  # note: OpenCode nests under "mcp", not "mcpServers"

    def sync_repo(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        hook_registry: dict[str, Any],
        policy: dict[str, Any],
    ) -> None:
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

    def sync_home(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        policy: dict[str, Any],
        fallbacks: dict[str, str],
        hook_registry: dict[str, Any],
    ) -> None:
        self._sync_dcp_config(ctx)

        if not OPENCODE_CONFIG_PATH.exists():
            return
        settings = load_json(OPENCODE_CONFIG_PATH)

        lmstudio_provider = _render_lmstudio_provider(policy, fallbacks)
        if lmstudio_provider:
            providers = settings.get("provider")
            if not isinstance(providers, dict):
                providers = {}
                settings["provider"] = providers
            providers["lmstudio"] = _merge_provider_entry(providers.get("lmstudio"), lmstudio_provider)

        # -- MCP merge (OpenCode uses root key "mcp", not "mcpServers") --
        existing_mcp = settings.get("mcp")
        rendered_mcp = self.render_mcp(registry, fallbacks)
        if isinstance(existing_mcp, dict):
            self._preserve_chrome_devtools_wrapper(rendered_mcp, existing_mcp)
        settings["mcp"] = merge_server_maps(rendered_mcp, existing_mcp if isinstance(existing_mcp, dict) else {})

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

        ctx.write_json(OPENCODE_CONFIG_PATH, settings)
        self._deploy_plugins(ctx)

    # -- internal helpers ----------------------------------------------

    def _sync_dcp_config(self, ctx: SyncContext) -> None:
        existing: dict[str, Any] = {}
        if OPENCODE_DCP_CONFIG_PATH.exists():
            loaded = load_json(OPENCODE_DCP_CONFIG_PATH)
            if isinstance(loaded, dict):
                existing = loaded
        ctx.write_json(OPENCODE_DCP_CONFIG_PATH, _render_dcp_config(existing))

    @staticmethod
    def _preserve_chrome_devtools_wrapper(rendered: dict[str, Any], existing: dict[str, Any]) -> None:
        current = existing.get("chrome-devtools")
        if not isinstance(current, dict):
            return
        command = current.get("command")
        if isinstance(command, list) and CHROME_DEVTOOLS_LAUNCHER in command:
            rendered["chrome-devtools"] = current

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
