"""OpenCode adapter.

Handles:
- ``~/.config/opencode/opencode.json``  (complex JSON merge: MCP, providers, instructions, skills)
- ``opencode.json`` in repo root  (project config)
- Plugin deployment to ``~/.config/opencode/plugins/``
"""

from __future__ import annotations

import copy
import os
from typing import TYPE_CHECKING, Any

from wagents.platforms.base import (
    HOME,
    REPO_ROOT,
    PlatformAdapter,
    SyncContext,
    assert_no_config_drops,
    enabled_registry_servers,
    load_json,
    managed_registry_server_names,
    mcphub_bearer_env_var,
    mcphub_enabled,
    mcphub_endpoint_specs,
    mcphub_projection_mode,
    mcphub_spec_enabled_for_harness,
    merge_server_maps,
    merge_unique_path_strings,
    render_env_value,
    render_home_path,
    render_mcphub_stdio_server,
    replace_arg_placeholders,
)

if TYPE_CHECKING:
    from pathlib import Path

OPENCODE_CONFIG_PATH = HOME / ".config" / "opencode" / "opencode.json"
OPENCODE_TUI_CONFIG_PATH = HOME / ".config" / "opencode" / "tui.json"
OPENCODE_TUI_PLUGINS_TEMPLATE_PATH = REPO_ROOT / "config" / "opencode-tui-plugins.json"
OPENCODE_DCP_CONFIG_PATH = HOME / ".config" / "opencode" / "dcp.jsonc"
OPENCODE_LARGE_IMAGE_OPTIMIZER_CONFIG_PATH = HOME / ".config" / "opencode" / "large-image-optimizer.json"
OPENCODE_DCP_TEMPLATE_PATH = REPO_ROOT / "config" / "opencode-dcp.jsonc"
OPENCODE_LARGE_IMAGE_OPTIMIZER_TEMPLATE_PATH = REPO_ROOT / "config" / "opencode-large-image-optimizer.json"
OPENCODE_QUOTA_TOAST_CONFIG_PATH = HOME / ".config" / "opencode" / "opencode-quota" / "quota-toast.json"
OPENCODE_QUOTA_TOAST_TEMPLATE_PATH = REPO_ROOT / "config" / "opencode-quota-toast.json"
OPENCODE_TOKEN_MONITOR_CONFIG_PATH = HOME / ".config" / "opencode" / "token-monitor.json"
OPENCODE_TOKEN_MONITOR_TEMPLATE_PATH = REPO_ROOT / "config" / "opencode-token-monitor.json"
OPENCODE_ENSEMBLE_CONFIG_PATH = HOME / ".config" / "opencode" / "ensemble.json"
OPENCODE_ENSEMBLE_TEMPLATE_PATH = REPO_ROOT / "config" / "opencode-ensemble.json"
OPENCODE_OCTTO_CONFIG_PATH = HOME / ".config" / "opencode" / "octto.json"
OPENCODE_OCTTO_TEMPLATE_PATH = REPO_ROOT / "config" / "opencode-octto.json"
OPENCODE_REPO_CONFIG_PATH = REPO_ROOT / "opencode.json"
OPENCODE_PLUGINS_DIR = HOME / ".config" / "opencode" / "plugins"
OPENCODE_GLOBAL_MD = REPO_ROOT / "instructions" / "opencode-global.md"
OPENCODE_AGENTS_OVERLAY_MD = REPO_ROOT / "instructions" / "opencode-agents-overlay.md"
GLOBAL_MD = REPO_ROOT / "instructions" / "global.md"
CHROME_DEVTOOLS_LAUNCHER = os.environ.get(
    "CHROME_DEVTOOLS_LAUNCHER",
    str(HOME / ".config/opencode/tools/chrome-devtools-launcher.sh"),
)
SKILLS_DIR = REPO_ROOT / "skills"
_LOCAL_PLUGIN_SPECS = [
    "./plugins/opencode-context-cache.mjs",
    "./plugins/octto-primary-inherit.mjs",
    "./plugins/opencode-incomplete-resume.mjs",
]
_TUI_ONLY_PLUGIN_KEYS = {
    "@ishaksebsib/opencode-tree",
    "@thiagos1lva/opencode-token-usage-chart",
    "opencode-subagent-statusline",
}
_DISABLED_TUI_PLUGIN_KEYS = {
    "@thiagos1lva/opencode-token-usage-chart",
    "opencode-subagent-statusline",
}
_DEPRECATED_RUNTIME_PLUGIN_KEYS = {
    "opencode-auto-resume",
}

_DCP_MODEL_LIMIT_KEYS = {"modelMaxLimits", "modelMinLimits"}
_OPENCODE_MODEL_KEYS = {"model", "small_model", "mode", "agent"}
_RUNTIME_DEFAULT_KEYS = {
    "model",
    "small_model",
    "agent",
    "autoupdate",
    "formatter",
    "lsp",
    "watcher",
    "tool_output",
    "experimental",
    "permission",
}
_MANAGED_PROVIDER_IDS = {"vercel", "opencode-go", "kimi-for-coding"}
_PYTHON_EXTENSIONS = [".py", ".pyi"]
_FORMATTER_DEFAULTS = {
    "biome": {
        "command": ["npx", "-y", "@biomejs/biome@latest", "format", "--write", "$FILE"],
        "extensions": [".js", ".jsx", ".ts", ".tsx", ".json", ".jsonc"],
    },
    "prettier": {
        "command": ["npx", "-y", "prettier@latest", "--write", "$FILE"],
        "extensions": [
            ".astro",
            ".css",
            ".graphql",
            ".gql",
            ".html",
            ".md",
            ".mdx",
            ".scss",
            ".svelte",
            ".vue",
            ".yaml",
            ".yml",
        ],
    },
    "ruff": {
        "command": ["ruff", "format", "$FILE"],
        "extensions": _PYTHON_EXTENSIONS,
    },
    "shell": {
        "command": [
            "npx",
            "-y",
            "-p",
            "prettier@latest",
            "-p",
            "prettier-plugin-sh@latest",
            "prettier",
            "--plugin",
            "prettier-plugin-sh",
            "--write",
            "$FILE",
        ],
        "extensions": [".bash", ".bats", ".env", ".sh", ".zsh"],
    },
    "toml": {
        "command": ["npx", "-y", "@taplo/cli@latest", "format", "$FILE"],
        "extensions": [".toml"],
    },
    "just": {
        "command": ["just", "--justfile", "$FILE", "--fmt"],
        "extensions": [".just", ".justfile", "Justfile", "justfile"],
    },
    "gofmt": {
        "command": ["gofmt", "-w", "$FILE"],
        "extensions": [".go"],
    },
    "rustfmt": {
        "command": ["rustfmt", "$FILE"],
        "extensions": [".rs"],
    },
}
_WATCHER_IGNORE_DEFAULTS = [
    ".git/**",
    ".mypy_cache/**",
    ".pytest_cache/**",
    ".ruff_cache/**",
    ".ty/**",
    ".venv/**",
    "dist/**",
    "docs/dist/**",
    "node_modules/**",
]


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


def _merge_enforced_defaults(defaults: Any, existing: Any) -> Any:
    if isinstance(defaults, dict) and isinstance(existing, dict):
        merged = copy.deepcopy(existing)
        for key, value in defaults.items():
            merged[key] = _merge_enforced_defaults(value, merged.get(key))
        return merged
    return copy.deepcopy(defaults)


def _openai_provider_defaults() -> dict[str, Any]:
    effort_variants = {
        "none": {
            "include": ["reasoning.encrypted_content"],
            "reasoningEffort": "none",
            "reasoningSummary": None,
        },
        "low": {
            "include": ["reasoning.encrypted_content"],
            "reasoningEffort": "low",
            "reasoningSummary": None,
        },
        "medium": {
            "include": ["reasoning.encrypted_content"],
            "reasoningEffort": "medium",
            "reasoningSummary": None,
        },
        "high": {
            "include": ["reasoning.encrypted_content"],
            "reasoningEffort": "high",
            "reasoningSummary": None,
            "textVerbosity": "low",
        },
        "xhigh": {
            "include": ["reasoning.encrypted_content"],
            "reasoningEffort": "xhigh",
            "reasoningSummary": None,
            "textVerbosity": "low",
        },
    }
    return {
        "options": {
            "timeout": 600000,
            "chunkTimeout": 180000,
            "setCacheKey": True,
            "reasoningEffort": "xhigh",
            "websearch_cited": {"model": "gpt-5.5"},
        },
        "models": {
            "gpt-5.5": {"variants": copy.deepcopy(effort_variants)},
            "gpt-5.4-mini": {"variants": copy.deepcopy(effort_variants)},
            "gpt-5.3-codex-spark": {"variants": copy.deepcopy(effort_variants)},
        },
    }


def _runtime_defaults(policy: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": "openai/gpt-5.5",
        "small_model": "openai/gpt-5.4-mini",
        "provider": {"openai": _openai_provider_defaults(), "xai": {"options": {}}},
        "agent": {
            "build": {
                "model": "openai/gpt-5.5",
                "variant": "xhigh",
                "options": {"reasoningEffort": "xhigh"},
            },
            "plan": {
                "model": "openai/gpt-5.5",
                "variant": "xhigh",
                "options": {"reasoningEffort": "xhigh"},
            },
            "explore": {
                "model": "openai/gpt-5.5",
                "variant": "xhigh",
                "options": {"reasoningEffort": "xhigh"},
            },
            "general": {
                "model": "openai/gpt-5.5",
                "variant": "xhigh",
                "options": {"reasoningEffort": "xhigh"},
            },
        },
        "autoupdate": "notify",
        "formatter": _FORMATTER_DEFAULTS,
        "lsp": {
            "ruff": {
                "command": ["ruff", "server"],
                "extensions": _PYTHON_EXTENSIONS,
            },
            "ty": {
                "command": ["ty", "server"],
                "extensions": _PYTHON_EXTENSIONS,
            },
        },
        "watcher": {"ignore": _WATCHER_IGNORE_DEFAULTS},
        "tool_output": {"max_lines": 4000, "max_bytes": 120000},
        "experimental": {
            "disable_paste_summary": False,
            "batch_tool": True,
            "openTelemetry": True,
            "continue_loop_on_deny": True,
            "mcp_timeout": 120000,
        },
        "permission": {"lsp": "allow"},
    }


def _load_repo_runtime_defaults(policy: dict[str, Any]) -> dict[str, Any]:
    if not OPENCODE_REPO_CONFIG_PATH.exists():
        return _runtime_defaults(policy)
    repo_config = load_json(OPENCODE_REPO_CONFIG_PATH)
    if not isinstance(repo_config, dict):
        return _runtime_defaults(policy)
    repo_defaults = {key: copy.deepcopy(repo_config[key]) for key in _RUNTIME_DEFAULT_KEYS if key in repo_config}
    return _merge_enforced_defaults(_runtime_defaults(policy), repo_defaults)


def _drop_unmanaged_provider_models(settings: dict[str, Any], defaults: dict[str, Any]) -> None:
    providers = settings.get("provider")
    default_providers = defaults.get("provider")
    if not isinstance(providers, dict) or not isinstance(default_providers, dict):
        return
    for provider_id, provider_defaults in default_providers.items():
        provider = providers.get(provider_id)
        if not isinstance(provider, dict) or not isinstance(provider_defaults, dict):
            continue
        provider_default_models = provider_defaults.get("models")
        if "models" not in provider_defaults:
            provider.pop("models", None)
            continue
        provider_models = provider.get("models")
        if not isinstance(provider_default_models, dict) or not isinstance(provider_models, dict):
            continue
        provider["models"] = {
            model_id: copy.deepcopy(model_defaults)
            for model_id, model_defaults in provider_default_models.items()
            if isinstance(model_defaults, dict)
        }


def _drop_unmanaged_provider_options(settings: dict[str, Any], defaults: dict[str, Any]) -> None:
    providers = settings.get("provider")
    default_providers = defaults.get("provider")
    if not isinstance(providers, dict) or not isinstance(default_providers, dict):
        return
    for provider_id, provider_defaults in default_providers.items():
        provider = providers.get(provider_id)
        if not isinstance(provider, dict) or not isinstance(provider_defaults, dict):
            continue
        provider_default_options = provider_defaults.get("options")
        if "options" not in provider_defaults:
            provider.pop("options", None)
            continue
        if isinstance(provider_default_options, dict):
            provider_options = provider.get("options")
            if not isinstance(provider_options, dict):
                provider_options = {}
            provider_options.update(copy.deepcopy(provider_default_options))
            provider["options"] = provider_options


def _remove_repo_managed_providers(settings: dict[str, Any]) -> None:
    providers = settings.get("provider")
    if not isinstance(providers, dict):
        return
    for provider_id in _MANAGED_PROVIDER_IDS:
        providers.pop(provider_id, None)
    # Aggressively keep only providers we explicitly manage or preserve: openai,
    # lmstudio, and a minimal xai picker-support block. Any others are stripped so
    # their options cannot inherit websearch_cited/setCacheKey/reasoning* etc. and
    # cause "invalid <provider> provider options".
    for pid in list(providers.keys()):
        if pid not in ("openai", "lmstudio", "xai"):
            providers.pop(pid, None)
    # Sanitize xai if present (from desktop auto-write or other) to keep options clean.
    # The clean xai block is now intentionally present in project and global configs to
    # support desktop model picker for grok 4.3 without invalid options errors.
    if "xai" in providers and isinstance(providers["xai"], dict):
        providers["xai"]["options"] = {}
    if not providers:
        settings.pop("provider", None)


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


def _plugin_package_name(plugin_spec: Any) -> str | None:
    if isinstance(plugin_spec, str):
        return plugin_spec
    if isinstance(plugin_spec, list) and plugin_spec and isinstance(plugin_spec[0], str):
        return plugin_spec[0]
    return None


def _plugin_package_key(plugin_spec: Any) -> str | None:
    package_name = _plugin_package_name(plugin_spec)
    if not package_name:
        return None
    version_index = package_name.rfind("@")
    if version_index > 0:
        return package_name[:version_index]
    return package_name


def _mcphub_bearer_auth_header(token_env: str) -> str:
    return "Bearer {file:~/.config/opencode/secrets/mcphub-bearer-token}"


def _sanitize_mcphub_auth_headers(mcp_servers: dict[str, Any], token_env: str) -> None:
    placeholder = _mcphub_bearer_auth_header(token_env)
    for name, server in mcp_servers.items():
        if not isinstance(name, str) or not name.startswith("mcphub") or not isinstance(server, dict):
            continue
        headers = server.get("headers")
        if isinstance(headers, dict) and "Authorization" in headers:
            headers["Authorization"] = placeholder


def _load_repo_plugin_specs() -> list[Any]:
    if not OPENCODE_REPO_CONFIG_PATH.exists():
        return []
    repo_config = load_json(OPENCODE_REPO_CONFIG_PATH)
    plugins = repo_config.get("plugin") if isinstance(repo_config, dict) else None
    return plugins if isinstance(plugins, list) else []


def _merge_plugin_specs(managed: list[Any], existing: Any, *, preserve_existing_options: bool = False) -> list[Any]:
    existing_specs = existing if isinstance(existing, list) else []
    existing_by_key = {
        key: plugin_spec for plugin_spec in existing_specs if (key := _plugin_package_key(plugin_spec)) is not None
    }

    merged: list[Any] = []
    seen: set[str] = set()

    for plugin_spec in managed:
        key = _plugin_package_key(plugin_spec)
        if key is None or key in seen:
            continue
        seen.add(key)
        existing_spec = existing_by_key.get(key)
        if (
            preserve_existing_options
            and isinstance(plugin_spec, str)
            and isinstance(existing_spec, list)
            and existing_spec
            and isinstance(existing_spec[0], str)
            and len(existing_spec) > 1
        ):
            merged.append([plugin_spec, *copy.deepcopy(existing_spec[1:])])
        else:
            merged.append(copy.deepcopy(plugin_spec))

    for plugin_spec in existing_specs:
        key = _plugin_package_key(plugin_spec)
        if key is None:
            merged.append(copy.deepcopy(plugin_spec))
            continue
        if key in seen:
            continue
        seen.add(key)
        merged.append(copy.deepcopy(plugin_spec))

    return merged


def _filter_runtime_plugin_specs(existing: Any) -> Any:
    if not isinstance(existing, list):
        return existing
    return [
        plugin_spec
        for plugin_spec in existing
        if _plugin_package_key(plugin_spec) not in _TUI_ONLY_PLUGIN_KEYS | _DEPRECATED_RUNTIME_PLUGIN_KEYS
    ]


def _filter_tui_plugin_specs(existing: Any) -> Any:
    if not isinstance(existing, list):
        return existing
    return [
        plugin_spec for plugin_spec in existing if _plugin_package_key(plugin_spec) not in _DISABLED_TUI_PLUGIN_KEYS
    ]


_TUI_KEYMAP_BINDING_NAMES = {
    "agent.list": "agent_list",
    "command.palette.show": "command_list",
    "docs.open": "docs_open",
    "messages.copy": "messages_copy",
    "model.list": "model_list",
    "opencode.status": "status_view",
    "plugin.dialog.install": "dialog.plugins.install",
    "plugins.list": "plugin_manager",
    "session.compact": "session_compact",
    "session.export": "session_export",
    "session.list": "session_list",
    "session.new": "session_new",
    "session.sidebar.toggle": "sidebar_toggle",
    "session.toggle.scrollbar": "scrollbar_toggle",
    "session.toggle.thinking": "display_thinking",
    "theme.switch": "theme_switch_mode",
    "variant.list": "variant_list",
}


def _normalize_tui_config(settings: dict[str, Any]) -> dict[str, Any]:
    keymap = settings.pop("keymap", None)
    if not isinstance(keymap, dict):
        return settings

    converted: dict[str, Any] = {}
    leader = keymap.get("leader")
    if leader is not None:
        converted["leader"] = copy.deepcopy(leader)
    if "leader_timeout" not in settings and keymap.get("leader_timeout") is not None:
        settings["leader_timeout"] = copy.deepcopy(keymap["leader_timeout"])

    sections = keymap.get("sections")
    if isinstance(sections, dict):
        for bindings in sections.values():
            if not isinstance(bindings, dict):
                continue
            for old_name, binding in bindings.items():
                new_name = _TUI_KEYMAP_BINDING_NAMES.get(str(old_name))
                if new_name:
                    converted[new_name] = copy.deepcopy(binding)

    existing_keybinds = settings.get("keybinds")
    if isinstance(existing_keybinds, dict):
        converted.update(existing_keybinds)
    if converted:
        settings["keybinds"] = converted

    plugin_enabled = settings.get("plugin_enabled")
    if isinstance(plugin_enabled, dict):
        settings["plugin_enabled"] = {
            name: enabled
            for name, enabled in plugin_enabled.items()
            if _plugin_package_key(name) not in _DISABLED_TUI_PLUGIN_KEYS
        }
    return settings


class Adapter(PlatformAdapter):
    name = "opencode"

    def home_config_paths(self) -> list[Path]:
        return [
            OPENCODE_CONFIG_PATH,
            OPENCODE_TUI_CONFIG_PATH,
            OPENCODE_DCP_CONFIG_PATH,
            OPENCODE_LARGE_IMAGE_OPTIMIZER_CONFIG_PATH,
            OPENCODE_QUOTA_TOAST_CONFIG_PATH,
            OPENCODE_TOKEN_MONITOR_CONFIG_PATH,
            OPENCODE_ENSEMBLE_CONFIG_PATH,
            OPENCODE_OCTTO_CONFIG_PATH,
        ]

    def render_mcp(
        self,
        registry: dict[str, Any],
        fallbacks: dict[str, str],
        harness: str | None = None,
    ) -> dict[str, Any]:
        """OpenCode uses ``type: local|remote`` with ``command`` arrays or ``url``."""
        if mcphub_enabled(registry):
            mode = mcphub_projection_mode(registry, harness or self.name, "http")
            token_env = mcphub_bearer_env_var(registry)
            auth_header = _mcphub_bearer_auth_header(token_env)
            servers: dict[str, Any] = {}
            for spec in mcphub_endpoint_specs(registry, harness or self.name):
                enabled = mcphub_spec_enabled_for_harness(registry, harness or self.name, spec)
                if mode == "http":
                    servers[spec["name"]] = {
                        "type": "remote",
                        "url": spec["url"],
                        "enabled": enabled,
                        "oauth": False,
                        "headers": {"Authorization": auth_header},
                    }
                else:
                    entry = render_mcphub_stdio_server(registry, spec["url"], fallbacks, enabled)
                    servers[spec["name"]] = {
                        "type": "local",
                        "command": [entry["command"], *entry["args"]],
                        "enabled": enabled,
                        "environment": {
                            token_env: render_env_value({"env_var": token_env}, fallbacks, local_values=True)
                        },
                    }
            return servers

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
            "instructions": ["AGENTS.md", "instructions/opencode-global.md", "instructions/opencode-agents-overlay.md"],
            "skills": {"paths": ["skills"]},
        }
        if OPENCODE_REPO_CONFIG_PATH.exists():
            existing = load_json(OPENCODE_REPO_CONFIG_PATH)
            if isinstance(existing, dict):
                existing["instructions"] = merge_unique_path_strings(
                    config["instructions"], existing.get("instructions")
                )
                existing.setdefault("skills", config["skills"])
                config = existing
        defaults = _runtime_defaults(policy)
        config = _merge_enforced_defaults(defaults, config)
        _drop_unmanaged_provider_options(config, defaults)
        _drop_unmanaged_provider_models(config, defaults)
        _remove_repo_managed_providers(config)
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
        self._sync_large_image_optimizer_config(ctx)
        self._sync_json_template(ctx, OPENCODE_QUOTA_TOAST_TEMPLATE_PATH, OPENCODE_QUOTA_TOAST_CONFIG_PATH)
        self._sync_json_template(ctx, OPENCODE_TOKEN_MONITOR_TEMPLATE_PATH, OPENCODE_TOKEN_MONITOR_CONFIG_PATH)
        self._sync_json_template(ctx, OPENCODE_ENSEMBLE_TEMPLATE_PATH, OPENCODE_ENSEMBLE_CONFIG_PATH)
        self._sync_json_template(ctx, OPENCODE_OCTTO_TEMPLATE_PATH, OPENCODE_OCTTO_CONFIG_PATH)
        self._sync_tui_config(ctx)

        if not OPENCODE_CONFIG_PATH.exists():
            return
        settings = load_json(OPENCODE_CONFIG_PATH)
        defaults = _load_repo_runtime_defaults(policy)
        settings = _merge_enforced_defaults(defaults, settings)
        _drop_unmanaged_provider_options(settings, defaults)
        _drop_unmanaged_provider_models(settings, defaults)
        _remove_repo_managed_providers(settings)

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
        if isinstance(existing_mcp, dict) and mcphub_enabled(registry):
            _sanitize_mcphub_auth_headers(existing_mcp, mcphub_bearer_env_var(registry))
            existing_mcp = self._strip_managed_mcphub_entries(existing_mcp)
        if isinstance(existing_mcp, dict) and not mcphub_enabled(registry):
            self._preserve_chrome_devtools_wrapper(rendered_mcp, existing_mcp)
        settings["mcp"] = merge_server_maps(
            rendered_mcp,
            existing_mcp if isinstance(existing_mcp, dict) else {},
            managed_registry_server_names(registry, self.name),
        )

        # -- Instructions paths --
        settings["instructions"] = merge_unique_path_strings(
            [
                render_home_path(GLOBAL_MD),
                render_home_path(OPENCODE_GLOBAL_MD),
                render_home_path(OPENCODE_AGENTS_OVERLAY_MD),
            ],
            settings.get("instructions"),
        )

        # -- Skills paths --
        skills = settings.get("skills")
        if not isinstance(skills, dict):
            skills = {}
            settings["skills"] = skills
        skills["paths"] = merge_unique_path_strings([render_home_path(SKILLS_DIR)], skills.get("paths"))

        # -- Runtime plugins --
        settings["plugin"] = _merge_plugin_specs(
            _load_repo_plugin_specs() + _LOCAL_PLUGIN_SPECS,
            _filter_runtime_plugin_specs(settings.get("plugin")),
        )

        self._write_local_json_config(ctx, OPENCODE_CONFIG_PATH, settings)
        self._deploy_plugins(ctx)

    # -- internal helpers ----------------------------------------------

    def _sync_dcp_config(self, ctx: SyncContext) -> None:
        existing: dict[str, Any] = {}
        if OPENCODE_DCP_CONFIG_PATH.exists():
            loaded = load_json(OPENCODE_DCP_CONFIG_PATH)
            if isinstance(loaded, dict):
                existing = loaded
        rendered = _render_dcp_config(existing)
        self._write_local_json_config(ctx, OPENCODE_DCP_CONFIG_PATH, rendered, current=existing)

    def _sync_large_image_optimizer_config(self, ctx: SyncContext) -> None:
        if not OPENCODE_LARGE_IMAGE_OPTIMIZER_TEMPLATE_PATH.exists():
            return
        self._write_local_json_config(
            ctx,
            OPENCODE_LARGE_IMAGE_OPTIMIZER_CONFIG_PATH,
            load_json(OPENCODE_LARGE_IMAGE_OPTIMIZER_TEMPLATE_PATH),
        )

    @staticmethod
    def _sync_json_template(ctx: SyncContext, template_path: Path, target_path: Path) -> None:
        if not template_path.exists():
            return
        Adapter._write_local_json_config(ctx, target_path, load_json(template_path))

    @staticmethod
    def _sync_tui_config(ctx: SyncContext) -> None:
        if not OPENCODE_TUI_CONFIG_PATH.exists() or not OPENCODE_TUI_PLUGINS_TEMPLATE_PATH.exists():
            return
        settings = load_json(OPENCODE_TUI_CONFIG_PATH)
        managed_plugins = load_json(OPENCODE_TUI_PLUGINS_TEMPLATE_PATH)
        if not isinstance(settings, dict) or not isinstance(managed_plugins, list):
            return
        settings["plugin"] = _merge_plugin_specs(
            managed_plugins,
            _filter_tui_plugin_specs(settings.get("plugin")),
            preserve_existing_options=True,
        )
        _normalize_tui_config(settings)
        Adapter._write_local_json_config(ctx, OPENCODE_TUI_CONFIG_PATH, settings)

    @staticmethod
    def _write_local_json_config(
        ctx: SyncContext,
        path: Path,
        data: Any,
        *,
        current: Any | None = None,
    ) -> None:
        if current is None and path.exists():
            current = load_json(path)
        if current is not None:
            assert_no_config_drops(path, current, data)
        ctx.write_json(path, data)

    @staticmethod
    def _preserve_chrome_devtools_wrapper(rendered: dict[str, Any], existing: dict[str, Any]) -> None:
        current = existing.get("chrome-devtools")
        if not isinstance(current, dict):
            return
        command = current.get("command")
        if isinstance(command, list) and CHROME_DEVTOOLS_LAUNCHER in command:
            rendered["chrome-devtools"] = current

    @staticmethod
    def _strip_managed_mcphub_entries(existing: dict[str, Any]) -> dict[str, Any]:
        return {name: entry for name, entry in existing.items() if not str(name).startswith("mcphub")}

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
