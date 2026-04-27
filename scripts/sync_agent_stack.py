#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tomllib
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"
GLOBAL_MD = REPO_ROOT / "instructions" / "global.md"
CODEX_GLOBAL_MD = REPO_ROOT / "instructions" / "codex-global.md"
CLAUDE_COMPAT_MD = REPO_ROOT / "instructions" / "claude-code-global.md"
COPILOT_GLOBAL_MD = REPO_ROOT / "instructions" / "copilot-global.md"
GEMINI_GLOBAL_MD = REPO_ROOT / "instructions" / "gemini-cli-global.md"
OPENCODE_GLOBAL_MD = REPO_ROOT / "instructions" / "opencode-global.md"
MCP_REGISTRY_PATH = CONFIG_DIR / "mcp-registry.json"
HOOK_REGISTRY_PATH = CONFIG_DIR / "hook-registry.json"
TOOLING_POLICY_PATH = CONFIG_DIR / "tooling-policy.json"
SYNC_MANIFEST_PATH = CONFIG_DIR / "sync-manifest.json"
CODEX_CONFIG_COPY_PATH = CONFIG_DIR / "codex-config.toml"
REPO_MCP_PATH = REPO_ROOT / "mcp.json"
VSCODE_MCP_PATH = REPO_ROOT / ".vscode" / "mcp.json"
COPILOT_REPO_INSTRUCTIONS_PATH = REPO_ROOT / ".github" / "copilot-instructions.md"
COPILOT_RULES_DIR = REPO_ROOT / ".github" / "instructions"
COPILOT_HOOKS_DIR = REPO_ROOT / ".github" / "hooks"
COPILOT_AGENTS_REPO_DIR = REPO_ROOT / "platforms" / "copilot" / "agents"
HOOKS_DIR = REPO_ROOT / "hooks"
CLAUDE_RULES_DIR = REPO_ROOT / ".claude" / "rules"
SKILLS_DIR = REPO_ROOT / "skills"

HOME = Path.home()
CLAUDE_SETTINGS_PATH = HOME / ".claude" / "settings.json"
CLAUDE_SETTINGS_LOCAL_PATH = HOME / ".claude" / "settings.local.json"
CLAUDE_DESKTOP_CONFIG_PATH = HOME / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
CHATGPT_MCP_PATH = HOME / "Library" / "Application Support" / "ChatGPT" / "mcp.json"
CLAUDE_ENTRYPOINT_PATH = HOME / ".claude" / "CLAUDE.md"
CODEX_ENTRYPOINT_PATH = HOME / ".codex" / "AGENTS.md"
CODEX_CONFIG_PATH = HOME / ".codex" / "config.toml"
CODEX_HOOKS_PATH = HOME / ".codex" / "hooks.json"
CODEX_SKILLS_DIR = HOME / ".codex" / "skills"
COPILOT_ENTRYPOINT_PATH = HOME / ".copilot" / "copilot-instructions.md"
COPILOT_MCP_PATH = HOME / ".copilot" / "mcp-config.json"
COPILOT_SHADOW_MCP_PATH = HOME / ".config" / ".copilot" / "mcp-config.json"
COPILOT_AGENTS_HOME_DIR = HOME / ".copilot" / "agents"
COPILOT_SKILLS_DIR = HOME / ".copilot" / "skills"
COPILOT_SETTINGS_PATH = HOME / ".copilot" / "settings.json"
COPILOT_SUBAGENTS_ENV_PATH = HOME / ".config" / "copilot-subagents.env"
CURSOR_MCP_PATH = HOME / ".cursor" / "mcp.json"
GEMINI_SETTINGS_PATH = HOME / ".gemini" / "settings.json"
GEMINI_ANTIGRAVITY_MCP_PATH = HOME / ".gemini" / "antigravity" / "mcp_config.json"
GEMINI_EXTENSION_MCP_PATH = (
    HOME / ".gemini" / "extensions" / "outline-driven-development" / "antigravity" / "mcp_config.json"
)
GEMINI_ENTRYPOINT_PATH = HOME / ".gemini" / "GEMINI.md"
GEMINI_SKILLS_DIR = HOME / ".gemini" / "skills"
OPENCODE_CONFIG_PATH = HOME / ".config" / "opencode" / "opencode.json"
OPENCODE_TUI_CONFIG_PATH = HOME / ".config" / "opencode" / "tui.json"
OPENCODE_REPO_CONFIG_PATH = REPO_ROOT / "opencode.json"
AITK_MCP_PATH = HOME / ".aitk" / "mcp.json"
CRUSH_CONFIG_PATH = HOME / ".config" / "crush" / "crush.json"
CHERRY_STUDIO_DIR = HOME / "Library" / "Application Support" / "CherryStudio"
CHERRY_STUDIO_IMPORT_DIR = CHERRY_STUDIO_DIR / "mcp-import"
CHERRY_STUDIO_MANAGED_IMPORT_DIR = CHERRY_STUDIO_IMPORT_DIR / "managed"

CODEX_MCP_BEGIN = "# BEGIN MANAGED BY sync_agent_stack.py: MCP_SERVERS"
CODEX_MCP_END = "# END MANAGED BY sync_agent_stack.py: MCP_SERVERS"
HOOK_COMMAND_MARKER = "wagents-hook.py"
MANAGED_HEADER = "<!-- Managed by scripts/sync_agent_stack.py. Do not edit directly. -->\n"
TOML_TABLE_RE = re.compile(r"^\[(?P<header>[^\]]+)\]\s*$")
CODEX_CONFIG_SCHEMA_COMMENT = "#:schema https://developers.openai.com/codex/config-schema.json"
CODEX_OWNED_TOP_LEVEL_KEYS = {
    "analytics",
    "approval_policy",
    "approvals_reviewer",
    "background_terminal_max_timeout",
    "check_for_update_on_startup",
    "default_permissions",
    "developer_instructions",
    "feedback",
    "file_opener",
    "model",
    "model_reasoning_effort",
    "model_reasoning_summary",
    "model_verbosity",
    "notify",
    "personality",
    "plan_mode_reasoning_effort",
    "project_doc_fallback_filenames",
    "project_doc_max_bytes",
    "sandbox_mode",
    "suppress_unstable_features_warning",
    "tool_output_token_limit",
    "web_search",
}
CODEX_OWNED_TABLES = {
    "agents",
    "analytics",
    "apps",
    "apps._default",
    "auto_review",
    "features",
    "features.multi_agent_v2",
    "feedback",
    "history",
    "memories",
    "model_providers.local-lmstudio",
    "model_providers.lmstudio",
    "profiles.deep",
    "profiles.fast",
    "profiles.full_access",
    "profiles.local-lmstudio",
    "profiles.lmstudio",
    "sandbox_workspace_write",
    "shell_environment_policy",
    "skills",
    "tools",
    "tools.web_search",
    "tools.web_search.location",
    "tui",
}
CODEX_AUTO_REVIEW_POLICY = "\n".join(
    [
        "Approve routine read-only inspection and bounded edits inside trusted workspaces.",
        "Reject or escalate destructive filesystem operations, credential exposure, global package manager mutations,",
        "privilege escalation, broad network side effects, and irreversible VCS operations unless explicitly",
        "requested.",
    ]
)
CODEX_MULTI_AGENT_USAGE_HINT = (
    "Use dynamic subagents for bounded parallel exploration, tests, and sidecar implementation. "
    "Do not hardcode static teams; keep the main thread responsible for integration and final judgment."
)

NAME_MAP = {
    "atom of thoughts": "atom-of-thoughts",
    "apple_mail": "apple-mail",
    "apple mail": "apple-mail",
    "deep lucid 3d": "deep-lucid-3d",
    "defaulttools": "default",
    "duck duck go search": "duckduckgo",
    "duckduckgo-search": "duckduckgo",
    "package version": "package-version",
    "shannon problem solver": "shannon-thinking",
    "structured thinking": "structured-thinking",
}
REMOVED_MCP_SERVERS = {
    "ableton",
    "apple-mail",
    "default",
    "playwright-headless",
    "serena",
}
CORE_INVENTORY = [
    "context7",
    "brave-search",
    "deepwiki",
    "fetch",
    "fetcher",
    "chrome-devtools",
    "docling",
    "package-version",
    "structured-thinking",
    "cascade-thinking",
    "sequential-thinking",
    "tavily",
    "repomix",
    "trafilatura",
]
NORMALIZED_BASES: dict[str, dict[str, Any]] = {
    "brave-search": {
        "command": "npx",
        "args": ["-y", "@brave/brave-search-mcp-server"],
    },
    "chrome-devtools": {
        "command": "npx",
        "args": ["-y", "chrome-devtools-mcp@latest", "--chrome-arg", "--disable-blink-features=AutomationControlled"],
    },
    "context7": {
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp", "--api-key", "${CONTEXT7_API_KEY}"],
    },
    "docling": {
        "command": "uvx",
        "args": ["--from", "docling-mcp", "docling-mcp-server", "--transport", "stdio"],
    },
    "repomix": {
        "command": "npx",
        "args": ["-y", "repomix", "--mcp"],
    },
    "tavily": {
        "command": "npx",
        "args": ["-y", "tavily-mcp"],
    },
}
COPILOT_TOOLS_OVERRIDES = {
    "package-version": [
        "check_docker_tags",
        "check_github_actions",
        "check_go_versions",
        "check_npm_versions",
        "check_pyproject_versions",
        "check_python_versions",
    ]
}


class SyncContext:
    def __init__(self, apply: bool) -> None:
        self.apply = apply
        self.changes: list[str] = []

    def note(self, message: str) -> None:
        self.changes.append(message)


def normalize_name(name: str) -> str:
    normalized = NAME_MAP.get(name)
    if normalized is not None:
        return normalized
    return NAME_MAP.get(name.lower(), name)


def normalize_existing_server_name(name: str, known_names: set[str]) -> str:
    normalized = normalize_name(name)
    lowered = normalized.lower()
    if lowered in known_names or lowered in REMOVED_MCP_SERVERS:
        return lowered
    return normalized


def load_json(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        without_line_comments = "\n".join(
            line for line in text.splitlines() if not line.lstrip().startswith("//")
        )
        return json.loads(without_line_comments)


def dump_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=True) + "\n"


def write_text(ctx: SyncContext, path: Path, content: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == content:
        return
    ctx.note(f"update {path}")
    if not ctx.apply:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(ctx: SyncContext, path: Path, data: Any) -> None:
    write_text(ctx, path, dump_json(data))


def sync_generated_json_directory(ctx: SyncContext, path: Path, files: dict[str, Any]) -> None:
    existing: set[str] = set()
    if path.exists() and path.is_dir():
        existing = {child.name for child in path.iterdir() if child.is_file() and child.suffix == ".json"}

    for file_name, data in files.items():
        write_json(ctx, path / file_name, data)

    for stale_name in sorted(existing - set(files)):
        stale_path = path / stale_name
        ctx.note(f"remove {stale_path}")
        if not ctx.apply:
            continue
        stale_path.unlink()


def ensure_symlink(ctx: SyncContext, path: Path, target: Path) -> None:
    try:
        target_str = os.path.relpath(target, start=path.parent)
    except ValueError:
        target_str = str(target)
    if path.is_symlink() and os.readlink(path) == target_str:
        return
    ctx.note(f"symlink {path} -> {target}")
    if not ctx.apply:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        if path.is_dir() and not path.is_symlink():
            backup = path.with_name(f"{path.name}.bak")
            if backup.exists():
                shutil.rmtree(backup)
            shutil.move(str(path), str(backup))
        else:
            path.unlink()
    path.symlink_to(target_str)


def portable_skill_dirs() -> list[Path]:
    return sorted(path for path in SKILLS_DIR.iterdir() if (path / "SKILL.md").exists())


def sync_skill_entries(ctx: SyncContext, target_dir: Path) -> None:
    for skill_dir in portable_skill_dirs():
        target = target_dir / skill_dir.name
        ensure_symlink(ctx, target, skill_dir)


def load_codex_config() -> dict[str, Any]:
    with CODEX_CONFIG_PATH.open("rb") as handle:
        return tomllib.load(handle)


def load_current_secret_fallbacks() -> dict[str, str]:
    fallbacks: dict[str, str] = {}
    if GEMINI_SETTINGS_PATH.exists():
        for server in load_json(GEMINI_SETTINGS_PATH).get("mcpServers", {}).values():
            for key, value in server.get("env", {}).items():
                if isinstance(value, str) and value and not value.startswith("${"):
                    fallbacks.setdefault(key, value)
    if COPILOT_MCP_PATH.exists():
        for server in load_json(COPILOT_MCP_PATH).get("mcpServers", {}).values():
            for key, value in server.get("env", {}).items():
                if isinstance(value, str) and value and not value.startswith("${"):
                    fallbacks.setdefault(key, value)
    for server in load_codex_config().get("mcp_servers", {}).values():
        for key, value in server.get("env", {}).items():
            if isinstance(value, str) and value and not value.startswith("${"):
                fallbacks.setdefault(key, value)
    if "CONTEXT7_API_KEY" not in fallbacks:
        backup_root = HOME / ".codex"
        for backup_path in sorted(backup_root.glob("config.toml.bak*"), reverse=True):
            match = re.search(
                r'@upstash/context7-mcp", "--api-key", "([^"]+)"', backup_path.read_text(encoding="utf-8")
            )
            if match:
                fallbacks["CONTEXT7_API_KEY"] = match.group(1)
                break
    return fallbacks


def env_placeholder(name: str) -> str:
    return "${" + name + "}"


def render_home_path(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(HOME.resolve())
    except ValueError:
        return str(path)
    return f"~/{relative.as_posix()}"


def normalize_path_value(value: str) -> str:
    if value == "~":
        return str(HOME.resolve())
    if value.startswith("~/"):
        return str((HOME / value[2:]).resolve())
    if value.startswith("/"):
        return str(Path(value).resolve())
    return value


def merge_unique_path_strings(managed: list[str], existing: Any) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()

    for item in managed:
        key = normalize_path_value(item)
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)

    if isinstance(existing, list):
        for item in existing:
            if not isinstance(item, str):
                continue
            key = normalize_path_value(item)
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)

    return merged


def resolve_env_value(name: str, fallbacks: dict[str, str]) -> str:
    return os.environ.get(name) or fallbacks.get(name) or env_placeholder(name)


def local_llm_provider(policy: dict[str, Any], provider: str) -> dict[str, Any] | None:
    providers = policy.get("local_llm_providers")
    if not isinstance(providers, dict):
        return None
    config = providers.get(provider)
    return config if isinstance(config, dict) else None


def resolve_local_llm_base_url(
    provider_config: dict[str, Any],
    fallbacks: dict[str, str] | None,
    *,
    local_values: bool,
) -> str:
    env_names = [provider_config.get("base_url_env")]
    aliases = provider_config.get("base_url_env_aliases", [])
    if isinstance(aliases, list):
        env_names.extend(aliases)
    if local_values:
        for env_name in env_names:
            if not isinstance(env_name, str):
                continue
            value = os.environ.get(env_name) or (fallbacks or {}).get(env_name)
            if value:
                return value
    default = provider_config.get("default_base_url")
    return str(default or "")


def render_codex_lmstudio_blocks(
    policy: dict[str, Any],
    fallbacks: dict[str, str] | None,
    *,
    local_values: bool,
) -> list[list[str]]:
    provider = local_llm_provider(policy, "lmstudio")
    if not provider:
        return []
    codex = provider.get("codex") if isinstance(provider.get("codex"), dict) else {}
    provider_id = str(codex.get("provider_id", "local-lmstudio"))
    profile = str(codex.get("profile", provider_id))
    return [
        render_toml_block(
            f"model_providers.{provider_id}",
            {
                "name": provider.get("name", "LM Studio (local)"),
                "base_url": resolve_local_llm_base_url(provider, fallbacks, local_values=local_values),
                "wire_api": codex.get("wire_api", "responses"),
            },
        ),
        render_toml_block(
            f"profiles.{profile}",
            {
                "model": provider.get("default_model", "local-model"),
                "model_provider": provider_id,
            },
        ),
    ]


def replace_arg_placeholders(args: list[Any], fallbacks: dict[str, str], local_values: bool) -> list[Any]:
    rendered: list[Any] = []
    for item in args:
        if isinstance(item, str) and item.startswith("${") and item.endswith("}"):
            env_name = item[2:-1]
            rendered.append(resolve_env_value(env_name, fallbacks) if local_values else item)
        else:
            rendered.append(item)
    return rendered


def parse_codex_servers() -> dict[str, dict[str, Any]]:
    servers = load_codex_config().get("mcp_servers", {})
    return {normalize_name(name): value for name, value in servers.items()}


def normalize_env_map(raw_env: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {key: {"env_var": key} for key in raw_env}


def normalize_args(name: str, args: list[Any]) -> list[Any]:
    args = list(args)
    if name == "context7" and "--api-key" in args:
        idx = args.index("--api-key")
        if idx + 1 < len(args):
            args[idx + 1] = env_placeholder("CONTEXT7_API_KEY")
    return args


def seed_registry_from_current_state() -> dict[str, Any]:
    repo_servers = (
        {normalize_name(name): value for name, value in load_json(REPO_MCP_PATH).get("mcpServers", {}).items()}
        if REPO_MCP_PATH.exists()
        else {}
    )
    vscode_servers = (
        {normalize_name(name): value for name, value in load_json(VSCODE_MCP_PATH).get("mcpServers", {}).items()}
        if VSCODE_MCP_PATH.exists()
        else {}
    )
    copilot_servers = (
        {normalize_name(name): value for name, value in load_json(COPILOT_MCP_PATH).get("mcpServers", {}).items()}
        if COPILOT_MCP_PATH.exists()
        else {}
    )
    gemini_servers = (
        {normalize_name(name): value for name, value in load_json(GEMINI_SETTINGS_PATH).get("mcpServers", {}).items()}
        if GEMINI_SETTINGS_PATH.exists()
        else {}
    )
    codex_servers = parse_codex_servers()
    names = sorted(
        {
            *repo_servers.keys(),
            *vscode_servers.keys(),
            *copilot_servers.keys(),
            *gemini_servers.keys(),
            *codex_servers.keys(),
        }
    )

    servers: dict[str, Any] = {}
    for name in names:
        base = (
            gemini_servers.get(name)
            or codex_servers.get(name)
            or repo_servers.get(name)
            or copilot_servers.get(name)
            or vscode_servers.get(name)
            or {}
        )
        entry = {
            "transport": base.get("type", "stdio"),
            "command": base.get("command"),
            "args": normalize_args(name, list(base.get("args", []))),
            "env": normalize_env_map(base.get("env", {})),
            "enabled": base.get("enabled", True),
            "startup_timeout_sec": int(base.get("startup_timeout_sec", 90)),
            "timeout_ms": int((repo_servers.get(name) or vscode_servers.get(name) or {}).get("timeout", 600000)),
            "tools": list((copilot_servers.get(name) or {}).get("tools", ["*"])),
            "tool_approvals": {},
            "platform_overrides": {},
        }
        for normalized_key, override in NORMALIZED_BASES.items():
            if name == normalized_key:
                entry.update(override)
        if name == "context7":
            entry["env"] = {"CONTEXT7_API_KEY": {"env_var": "CONTEXT7_API_KEY"}}
        if name in COPILOT_TOOLS_OVERRIDES:
            entry["tools"] = COPILOT_TOOLS_OVERRIDES[name]
        if not entry["command"]:
            continue
        servers[name] = entry

    ordered_servers = {
        name: servers[name] for name in sorted(servers, key=lambda item: (item not in CORE_INVENTORY, item))
    }
    return {
        "version": 1,
        "instruction_source": str(GLOBAL_MD),
        "servers": ordered_servers,
    }


def load_registry(ctx: SyncContext) -> dict[str, Any]:
    if MCP_REGISTRY_PATH.exists():
        return load_json(MCP_REGISTRY_PATH)
    registry = seed_registry_from_current_state()
    write_json(ctx, MCP_REGISTRY_PATH, registry)
    return registry


def load_hook_registry() -> dict[str, Any]:
    return load_json(HOOK_REGISTRY_PATH)


def enabled_registry_servers(registry: dict[str, Any]) -> dict[str, Any]:
    return {name: entry for name, entry in registry["servers"].items() if entry.get("enabled") is not False}


def render_repo_mcp(registry: dict[str, Any]) -> dict[str, Any]:
    servers: dict[str, Any] = {}
    for name, entry in enabled_registry_servers(registry).items():
        server: dict[str, Any] = {
            "command": entry["command"],
            "args": replace_arg_placeholders(entry.get("args", []), {}, local_values=False),
        }
        if entry.get("env"):
            server["env"] = {key: env_placeholder(value["env_var"]) for key, value in entry["env"].items()}
        if entry.get("timeout_ms"):
            server["timeout"] = entry["timeout_ms"]
        servers[name] = server
    return {"mcpServers": servers}


def render_copilot_mcp(registry: dict[str, Any], fallbacks: dict[str, str]) -> dict[str, Any]:
    servers: dict[str, Any] = {}
    for name, entry in enabled_registry_servers(registry).items():
        server: dict[str, Any] = {
            "tools": entry.get("tools", ["*"]),
            "type": entry.get("transport", "stdio"),
            "command": entry["command"],
            "args": replace_arg_placeholders(entry.get("args", []), fallbacks, local_values=True),
        }
        if entry.get("env"):
            server["env"] = {key: resolve_env_value(value["env_var"], fallbacks) for key, value in entry["env"].items()}
        servers[name] = server
    return {"mcpServers": servers}


def toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    raise TypeError(f"Unsupported TOML value: {value!r}")


def render_toml_block(header: str | None, values: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    if header is not None:
        lines.append(f"[{header}]")
    for key, value in values.items():
        if isinstance(value, str) and "\n" in value:
            lines.append(f'{key} = """{value}"""')
        else:
            lines.append(f"{key} = {toml_value(value)}")
    return lines


def render_codex_args(entry: dict[str, Any]) -> list[Any]:
    args = list(entry.get("args", []))
    env_names = {value["env_var"] for value in entry.get("env", {}).values()}
    rendered: list[Any] = []
    idx = 0
    while idx < len(args):
        arg = args[idx]
        next_arg = args[idx + 1] if idx + 1 < len(args) else None
        if (
            isinstance(arg, str)
            and arg.startswith("--")
            and isinstance(next_arg, str)
            and next_arg.startswith("${")
            and next_arg.endswith("}")
            and next_arg[2:-1] in env_names
        ):
            idx += 2
            continue
        if isinstance(arg, str) and arg.startswith("${") and arg.endswith("}") and arg[2:-1] in env_names:
            idx += 1
            continue
        rendered.append(arg)
        idx += 1
    return rendered


def render_codex_mcp_block(registry: dict[str, Any]) -> str:
    lines = [CODEX_MCP_BEGIN]
    for name, entry in enabled_registry_servers(registry).items():
        lines.append("")
        lines.append(f"[mcp_servers.{name}]")
        lines.append(f"args = {toml_value(render_codex_args(entry))}")
        lines.append(f"command = {toml_value(entry['command'])}")
        lines.append(f"startup_timeout_sec = {toml_value(entry.get('startup_timeout_sec', 90))}")
        if entry.get("timeout_ms"):
            lines.append(f"tool_timeout_sec = {toml_value(max(1, int(entry['timeout_ms']) // 1000))}")
        if entry.get("tools") and entry.get("tools") != ["*"]:
            lines.append(f"enabled_tools = {toml_value(entry['tools'])}")
        if entry.get("env"):
            env_vars = [value["env_var"] for value in entry["env"].values()]
            lines.append(f"env_vars = {toml_value(env_vars)}")
    lines.append("")
    lines.append(CODEX_MCP_END)
    return "\n".join(lines) + "\n"


def render_hook_command(entry: dict[str, Any], harness: str, *, repo_relative: bool) -> str:
    repo_root = "." if repo_relative else str(REPO_ROOT)
    return str(entry["command"]).format(repo_root=repo_root, harness=harness)


def enabled_hooks_for_harness(hook_registry: dict[str, Any], harness: str) -> list[dict[str, Any]]:
    hooks = hook_registry.get("hooks", [])
    if not isinstance(hooks, list):
        return []
    return [
        hook
        for hook in hooks
        if isinstance(hook, dict) and hook.get("command") and harness in set(hook.get("harnesses", []))
    ]


def render_copilot_hooks(hook_registry: dict[str, Any]) -> dict[str, Any]:
    event_map = {
        "SessionStart": "sessionStart",
        "UserPromptSubmit": "userPromptSubmitted",
        "PreToolUse": "preToolUse",
        "PostToolUse": "postToolUse",
        "SessionEnd": "sessionEnd",
    }
    rendered: dict[str, list[dict[str, Any]]] = {}
    for hook in enabled_hooks_for_harness(hook_registry, "github-copilot"):
        event = event_map.get(str(hook.get("logical_event")))
        if not event:
            continue
        rendered.setdefault(event, []).append(
            {
                "type": "command",
                "bash": render_hook_command(hook, "github-copilot", repo_relative=True),
                "cwd": ".",
                "timeoutSec": int(hook.get("timeout", 5)),
                "comment": hook.get("description", hook["id"]),
            }
        )
    return {"version": int(hook_registry.get("version", 1)), "hooks": rendered}


def render_standard_hooks(hook_registry: dict[str, Any], harness: str) -> dict[str, Any]:
    event_map = {
        "codex": {
            "UserPromptSubmit": "UserPromptSubmit",
            "PreToolUse": "PreToolUse",
            "PostToolUse": "PostToolUse",
            "Stop": "Stop",
        },
        "claude-code": {
            "UserPromptSubmit": "UserPromptSubmit",
            "PreToolUse": "PreToolUse",
            "PostToolUse": "PostToolUse",
            "Stop": "Stop",
        },
        "gemini-cli": {
            "UserPromptSubmit": "BeforeAgent",
            "PreToolUse": "BeforeTool",
            "PostToolUse": "AfterTool",
            "Stop": "AfterAgent",
        },
    }[harness]
    rendered: dict[str, list[dict[str, Any]]] = {}
    for hook in enabled_hooks_for_harness(hook_registry, harness):
        event = event_map.get(str(hook.get("logical_event")))
        if not event:
            continue
        config: dict[str, Any] = {
            "type": "command",
            "command": render_hook_command(hook, harness, repo_relative=False),
        }
        if harness == "gemini-cli":
            config.update(
                {
                    "name": hook["id"],
                    "timeout": int(hook.get("timeout", 5)) * 1000,
                    "description": hook.get("description", hook["id"]),
                }
            )
        group: dict[str, Any] = {"hooks": [config]}
        if hook.get("matcher"):
            group["matcher"] = hook["matcher"]
        if harness == "gemini-cli":
            group["sequential"] = True
        rendered.setdefault(event, []).append(group)
    return {"hooks": rendered}


def strip_generated_hook_entries(hooks: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(hooks, dict):
        return {}
    stripped: dict[str, list[Any]] = {}
    for event, entries in hooks.items():
        if not isinstance(entries, list):
            continue
        kept = []
        for entry in entries:
            if not isinstance(entry, dict):
                kept.append(entry)
                continue
            hook_configs = entry.get("hooks") if isinstance(entry.get("hooks"), list) else [entry]
            commands = [
                str(config.get("command") or config.get("bash") or "")
                for config in hook_configs
                if isinstance(config, dict)
            ]
            if any(HOOK_COMMAND_MARKER in command for command in commands):
                continue
            kept.append(entry)
        if kept:
            stripped[event] = kept
    return stripped


def merge_hook_groups(existing: dict[str, Any], generated: dict[str, Any]) -> dict[str, Any]:
    merged = strip_generated_hook_entries(existing)
    for event, entries in generated.get("hooks", {}).items():
        merged.setdefault(event, [])
        merged[event].extend(entries)
    return merged


def merge_codex_hooks(ctx: SyncContext, hook_registry: dict[str, Any]) -> None:
    existing: dict[str, Any] = {}
    if CODEX_HOOKS_PATH.exists():
        existing = load_json(CODEX_HOOKS_PATH)
    existing_hooks = existing.get("hooks") if isinstance(existing.get("hooks"), dict) else {}
    existing["hooks"] = merge_hook_groups(existing_hooks, render_standard_hooks(hook_registry, "codex"))
    write_json(ctx, CODEX_HOOKS_PATH, existing)


def render_codex_global_instructions() -> str:
    global_text = GLOBAL_MD.read_text(encoding="utf-8").rstrip("\n")
    codex_suffix = """

## Codex-Specific Instructions

- Treat `/Users/ww/dev/projects/agents/instructions/global.md` as the canonical shared instruction source.
- Keep Codex-specific config generation in `/Users/ww/dev/projects/agents/scripts/sync_agent_stack.py`.
- Keep `/Users/ww/.codex/config.toml` and the repo-owned sanitized config copy schema-valid.
- Codex disables automatic startup skill-list injection to avoid context-budget warnings; use
  `uv run wagents skills search|context|read|doctor ...` from `/Users/ww/dev/projects/agents`
  when a task needs a skill body or a missing/omitted skill must be recovered.
- Prefer dynamic subagent delegation over hardcoded static teams; keep local agent ceilings practical.
"""
    return global_text + codex_suffix


def generate_codex_global_instructions(ctx: SyncContext) -> None:
    write_text(ctx, CODEX_GLOBAL_MD, render_codex_global_instructions())


def sync_codex_entrypoint(ctx: SyncContext) -> None:
    ensure_symlink(ctx, CODEX_ENTRYPOINT_PATH, CODEX_GLOBAL_MD)


def render_codex_base_config(
    policy: dict[str, Any],
    current_data: dict[str, Any] | None = None,
    fallbacks: dict[str, str] | None = None,
    *,
    local_values: bool = False,
) -> str:
    model_defaults = policy.get("model_defaults", {}).get("codex", {})
    model = model_defaults.get("model", "gpt-5.5")
    reasoning_effort = model_defaults.get("reasoning_effort", "high")
    personality = model_defaults.get("personality", "pragmatic")
    top_level = {
        "approval_policy": "never",
        "approvals_reviewer": "user",
        "background_terminal_max_timeout": 300000,
        "check_for_update_on_startup": True,
        "file_opener": "vscode",
        "model": model,
        "model_reasoning_effort": reasoning_effort,
        "model_reasoning_summary": "detailed",
        "model_verbosity": "medium",
        "personality": personality,
        "plan_mode_reasoning_effort": reasoning_effort,
        "project_doc_fallback_filenames": ["TEAM_GUIDE.md", ".agents.md"],
        "project_doc_max_bytes": 131072,
        "sandbox_mode": "danger-full-access",
        "suppress_unstable_features_warning": False,
        "tool_output_token_limit": 20000,
        "web_search": "live",
    }
    if current_data and isinstance(current_data.get("notify"), list):
        top_level["notify"] = current_data["notify"]
    blocks: list[list[str]] = [
        [CODEX_CONFIG_SCHEMA_COMMENT],
        render_toml_block(None, top_level),
        render_toml_block("auto_review", {"policy": CODEX_AUTO_REVIEW_POLICY}),
        render_toml_block(
            "features",
            {
                "apps": True,
                "codex_hooks": True,
                "enable_request_compression": True,
                "fast_mode": True,
                "general_analytics": True,
                "guardian_approval": True,
                "image_generation": True,
                "memories": True,
                "multi_agent": True,
                "personality": True,
                "plugins": True,
                "prevent_idle_sleep": True,
                "shell_snapshot": True,
                "shell_tool": True,
                "skill_mcp_dependency_install": True,
                "tool_call_mcp_elicitation": True,
                "tool_search": True,
                "tool_suggest": True,
                "undo": True,
                "unified_exec": True,
                "workspace_dependencies": True,
            },
        ),
        render_toml_block(
            "features.multi_agent_v2",
            {
                "enabled": True,
                "usage_hint_enabled": True,
                "usage_hint_text": CODEX_MULTI_AGENT_USAGE_HINT,
            },
        ),
        render_toml_block(
            "profiles.deep",
            {
                "approval_policy": "on-request",
                "approvals_reviewer": "guardian_subagent",
                "model": model,
                "model_reasoning_effort": "xhigh",
                "model_reasoning_summary": "detailed",
                "model_verbosity": "medium",
                "plan_mode_reasoning_effort": "xhigh",
                "sandbox_mode": "workspace-write",
                "web_search": "live",
            },
        ),
        render_toml_block(
            "profiles.fast",
            {
                "approval_policy": "on-request",
                "approvals_reviewer": "guardian_subagent",
                "model": "gpt-5.4-mini",
                "model_reasoning_effort": "medium",
                "model_reasoning_summary": "concise",
                "model_verbosity": "medium",
                "plan_mode_reasoning_effort": "medium",
                "sandbox_mode": "workspace-write",
                "service_tier": "fast",
                "web_search": "live",
            },
        ),
        render_toml_block(
            "profiles.full_access",
            {
                "approval_policy": "never",
                "approvals_reviewer": "user",
                "model": model,
                "model_reasoning_effort": "high",
                "model_reasoning_summary": "detailed",
                "model_verbosity": "medium",
                "plan_mode_reasoning_effort": "high",
                "sandbox_mode": "danger-full-access",
                "web_search": "live",
            },
        ),
        *render_codex_lmstudio_blocks(policy, fallbacks, local_values=local_values),
        render_toml_block(
            "apps._default",
            {
                "enabled": True,
                "destructive_enabled": False,
                "open_world_enabled": True,
            },
        ),
        render_toml_block("tools", {"view_image": True}),
        render_toml_block("tools.web_search", {"context_size": "high"}),
        render_toml_block(
            "tools.web_search.location",
            {
                "country": "US",
                "region": "NY",
                "city": "New York",
                "timezone": "America/New_York",
            },
        ),
        render_toml_block(
            "history",
            {
                "persistence": "save-all",
                "max_bytes": 134217728,
            },
        ),
        render_toml_block("feedback", {"enabled": True}),
        render_toml_block("analytics", {"enabled": True}),
        render_toml_block(
            "memories",
            {
                "generate_memories": True,
                "use_memories": True,
                "disable_on_external_context": False,
                "max_raw_memories_for_consolidation": 1024,
                "max_unused_days": 90,
                "max_rollout_age_days": 45,
                "max_rollouts_per_startup": 32,
                "min_rollout_idle_hours": 6,
            },
        ),
        render_toml_block(
            "sandbox_workspace_write",
            {
                "network_access": True,
                "exclude_tmpdir_env_var": False,
                "exclude_slash_tmp": False,
            },
        ),
        render_toml_block("shell_environment_policy", {"inherit": "core"}),
        render_toml_block("skills", {"include_instructions": False}),
        render_toml_block(
            "tui",
            {
                "notifications": True,
                "notification_method": "auto",
                "notification_condition": "unfocused",
                "animations": True,
                "alternate_screen": "auto",
                "show_tooltips": True,
                "status_line": ["model-with-reasoning", "context-remaining", "current-dir"],
                "terminal_title": ["spinner", "project"],
            },
        ),
    ]
    return "\n\n".join("\n".join(block) for block in blocks) + "\n\n"


def filter_codex_top_level_chunk(chunk: str) -> str:
    lines: list[str] = []
    for line in chunk.splitlines():
        stripped = line.strip()
        if stripped == CODEX_CONFIG_SCHEMA_COMMENT:
            continue
        if not stripped or stripped.startswith("#"):
            lines.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in CODEX_OWNED_TOP_LEVEL_KEYS:
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def render_preserved_codex_config(current: str, *, include_local_extras: bool) -> str:
    if not include_local_extras:
        return ""
    preserved_chunks: list[str] = []
    for header, chunk in chunk_toml_sections(remove_managed_codex_block(current)):
        if header in CODEX_OWNED_TABLES:
            continue
        if header is None:
            filtered = filter_codex_top_level_chunk(chunk)
            if filtered:
                preserved_chunks.append(filtered)
            continue
        preserved_chunks.append(chunk.strip())
    return "\n\n".join(chunk for chunk in preserved_chunks if chunk)


def render_codex_config(
    current: str,
    registry: dict[str, Any],
    policy: dict[str, Any],
    *,
    include_local_extras: bool,
    fallbacks: dict[str, str] | None = None,
) -> str:
    current_data = tomllib.loads(current)
    preserved = render_preserved_codex_config(current, include_local_extras=include_local_extras)
    if include_local_extras:
        managed_names = set(registry["servers"])
        filtered_chunks: list[str] = []
        for header, chunk in chunk_toml_sections(preserved):
            server_name = codex_mcp_server_name(header)
            normalized_server_name = normalize_name(server_name) if server_name else None
            if normalized_server_name and normalized_server_name in managed_names:
                continue
            filtered_chunks.append(chunk.strip())
        preserved = "\n\n".join(chunk for chunk in filtered_chunks if chunk)
    parts = [
        render_codex_base_config(
            policy,
            current_data if include_local_extras else None,
            fallbacks,
            local_values=include_local_extras,
        ).rstrip()
    ]
    if preserved:
        parts.append(preserved)
    parts.append(render_codex_mcp_block(registry).rstrip())
    return "\n\n".join(parts) + "\n"


def remove_managed_codex_block(text: str) -> str:
    begin = text.find(CODEX_MCP_BEGIN)
    if begin == -1:
        return text
    end = text.find(CODEX_MCP_END, begin)
    if end == -1:
        return text[:begin]
    end += len(CODEX_MCP_END)
    while end < len(text) and text[end] == "\n":
        end += 1
    prefix = text[:begin].rstrip("\n")
    suffix = text[end:].lstrip("\n")
    if prefix and suffix:
        return prefix + "\n\n" + suffix
    if prefix:
        return prefix + "\n"
    return suffix


def chunk_toml_sections(text: str) -> list[tuple[str | None, str]]:
    chunks: list[tuple[str | None, str]] = []
    current_header: str | None = None
    current_lines: list[str] = []
    for line in text.splitlines(keepends=True):
        match = TOML_TABLE_RE.match(line.strip())
        if match:
            if current_lines:
                chunks.append((current_header, "".join(current_lines)))
            current_header = match.group("header")
            current_lines = [line]
            continue
        current_lines.append(line)
    if current_lines:
        chunks.append((current_header, "".join(current_lines)))
    return chunks


def codex_mcp_server_name(header: str | None) -> str | None:
    if not header or not header.startswith("mcp_servers."):
        return None
    suffix = header.removeprefix("mcp_servers.")
    return suffix.split(".", 1)[0]


def merge_codex_config(
    ctx: SyncContext, registry: dict[str, Any], policy: dict[str, Any], fallbacks: dict[str, str]
) -> None:
    current = CODEX_CONFIG_PATH.read_text(encoding="utf-8")
    write_text(
        ctx,
        CODEX_CONFIG_PATH,
        render_codex_config(current, registry, policy, include_local_extras=True, fallbacks=fallbacks),
    )
    write_text(
        ctx,
        CODEX_CONFIG_COPY_PATH,
        render_codex_config(current, registry, policy, include_local_extras=False, fallbacks=fallbacks),
    )


def generate_copilot_repo_instructions(ctx: SyncContext) -> None:
    copilot_text = COPILOT_GLOBAL_MD.read_text(encoding="utf-8")
    global_text = GLOBAL_MD.read_text(encoding="utf-8").rstrip("\n")
    content, replacements = re.subn(
        r"^@.*instructions/global\.md\s*$",
        global_text,
        copilot_text,
        count=1,
        flags=re.MULTILINE,
    )
    if replacements != 1:
        raise ValueError(f"Expected a single global.md import in {COPILOT_GLOBAL_MD}")
    content = MANAGED_HEADER + content
    write_text(ctx, COPILOT_REPO_INSTRUCTIONS_PATH, content)


def parse_claude_rule(path: Path) -> tuple[list[str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return [], text
    _, frontmatter, body = text.split("---\n", 2)
    patterns: list[str] = []
    for line in frontmatter.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            patterns.append(stripped[2:].strip().strip('"'))
    return patterns, body.lstrip()


def generate_copilot_rule_instructions(ctx: SyncContext) -> None:
    for rule_path in sorted(CLAUDE_RULES_DIR.glob("*.md")):
        patterns, body = parse_claude_rule(rule_path)
        apply_to = ",".join(patterns)
        rendered = f'---\napplyTo: "{apply_to}"\n---\n\n{MANAGED_HEADER}{body}'
        output_path = COPILOT_RULES_DIR / f"{rule_path.stem}.instructions.md"
        write_text(ctx, output_path, rendered)


def generate_copilot_hooks(ctx: SyncContext, hook_registry: dict[str, Any]) -> None:
    write_json(ctx, COPILOT_HOOKS_DIR / "policy.json", render_copilot_hooks(hook_registry))


def merge_claude_settings(ctx: SyncContext, policy: dict[str, Any], hook_registry: dict[str, Any]) -> None:
    settings = load_json(CLAUDE_SETTINGS_PATH)
    allow = settings.setdefault("permissions", {}).setdefault("allow", [])
    for domain in policy.get("docs_domains", []):
        token = f"WebFetch(domain:{domain})"
        if token not in allow:
            allow.append(token)
    settings["hooks"] = merge_hook_groups(
        settings.get("hooks", {}),
        render_standard_hooks(hook_registry, "claude-code"),
    )
    for hook_groups in settings.get("hooks", {}).values():
        for group in hook_groups:
            for hook in group.get("hooks", []):
                command = hook.get("command")
                if not isinstance(command, str) or ".claude/hooks/" not in command:
                    continue
                hook_name = command.split(".claude/hooks/", 1)[1].split()[0]
                suffix = command.split(hook_name, 1)[1]
                hook["command"] = f"{HOOKS_DIR / hook_name}{suffix}"
    write_json(ctx, CLAUDE_SETTINGS_PATH, settings)


def merge_copilot_config(ctx: SyncContext, policy: dict[str, Any]) -> None:
    config = load_json(COPILOT_SETTINGS_PATH)
    defaults = policy.get("model_defaults", {}).get("copilot", {})
    config["model"] = defaults.get("model", config.get("model"))
    config["effortLevel"] = defaults.get("effort_level", config.get("effortLevel"))
    if "continue_on_auto_mode" in defaults:
        config["continueOnAutoMode"] = defaults["continue_on_auto_mode"]
    trusted = set(config.get("trustedFolders", []))
    trusted.update(policy.get("trusted_roots", []))
    config["trustedFolders"] = sorted(trusted)
    allowed = set(config.get("allowedUrls", config.get("allowed_urls", [])))
    for domain in policy.get("docs_domains", []):
        allowed.add(f"https://{domain}")
    config.pop("allowed_urls", None)
    config["allowedUrls"] = sorted(allowed)
    write_json(ctx, COPILOT_SETTINGS_PATH, config)


def sync_copilot_subagent_env(ctx: SyncContext, policy: dict[str, Any]) -> None:
    defaults = policy.get("model_defaults", {}).get("copilot", {})
    limits = defaults.get("subagent_limits")
    if not limits:
        content = (
            "# Managed by /Users/ww/dev/projects/agents/scripts/sync_agent_stack.py.\n"
            "unset COPILOT_SUBAGENT_MAX_CONCURRENT\n"
            "unset COPILOT_SUBAGENT_MAX_DEPTH\n"
        )
        write_text(ctx, COPILOT_SUBAGENTS_ENV_PATH, content)
        return
    max_concurrent = int(limits["max_concurrent"])
    max_depth = int(limits["max_depth"])
    content = (
        "# Managed by /Users/ww/dev/projects/agents/scripts/sync_agent_stack.py.\n"
        f'export COPILOT_SUBAGENT_MAX_CONCURRENT="{max_concurrent}"\n'
        f'export COPILOT_SUBAGENT_MAX_DEPTH="{max_depth}"\n'
    )
    write_text(ctx, COPILOT_SUBAGENTS_ENV_PATH, content)


def sync_copilot_agents(ctx: SyncContext) -> None:
    if ctx.apply:
        COPILOT_AGENTS_REPO_DIR.mkdir(parents=True, exist_ok=True)
    if COPILOT_AGENTS_HOME_DIR.exists() and not COPILOT_AGENTS_HOME_DIR.is_symlink():
        for agent_file in sorted(COPILOT_AGENTS_HOME_DIR.glob("*.agent.md")):
            destination = COPILOT_AGENTS_REPO_DIR / agent_file.name
            if not destination.exists():
                ctx.note(f"copy {agent_file} -> {destination}")
                if ctx.apply:
                    shutil.copy2(agent_file, destination)
    ensure_symlink(ctx, COPILOT_AGENTS_HOME_DIR, COPILOT_AGENTS_REPO_DIR)


def sync_repo_targets(ctx: SyncContext, registry: dict[str, Any], hook_registry: dict[str, Any]) -> None:
    write_json(ctx, MCP_REGISTRY_PATH, registry)
    write_json(ctx, REPO_MCP_PATH, render_repo_mcp(registry))
    write_json(ctx, VSCODE_MCP_PATH, render_repo_mcp(registry))
    write_json(ctx, HOOK_REGISTRY_PATH, hook_registry)
    generate_codex_global_instructions(ctx)
    generate_copilot_repo_instructions(ctx)
    generate_copilot_rule_instructions(ctx)
    generate_copilot_hooks(ctx, hook_registry)
    generate_project_opencode_config(ctx)


def render_gemini_mcp(registry: dict[str, Any], fallbacks: dict[str, str]) -> dict[str, Any]:
    servers: dict[str, Any] = {}
    for name, entry in enabled_registry_servers(registry).items():
        server: dict[str, Any] = {
            "type": entry.get("transport", "stdio"),
            "command": entry["command"],
            "args": replace_arg_placeholders(entry.get("args", []), fallbacks, local_values=True),
        }
        if entry.get("env"):
            server["env"] = {key: resolve_env_value(value["env_var"], fallbacks) for key, value in entry["env"].items()}
        if entry.get("tools") and entry.get("tools") != ["*"]:
            server["includeTools"] = entry["tools"]
        servers[name] = server
    return servers


def render_client_mcp(registry: dict[str, Any], fallbacks: dict[str, str]) -> dict[str, Any]:
    servers: dict[str, Any] = {}
    for name, entry in enabled_registry_servers(registry).items():
        server: dict[str, Any] = {
            "command": entry["command"],
            "args": replace_arg_placeholders(entry.get("args", []), fallbacks, local_values=True),
        }
        if entry.get("env"):
            server["env"] = {key: resolve_env_value(value["env_var"], fallbacks) for key, value in entry["env"].items()}
        servers[name] = server
    return {"mcpServers": servers}


def merge_server_maps(rendered: dict[str, Any], existing: dict[str, Any]) -> dict[str, Any]:
    merged = dict(rendered)
    known_names = set(rendered)
    for name, entry in existing.items():
        normalized = normalize_existing_server_name(name, known_names)
        if normalized in known_names or normalized in REMOVED_MCP_SERVERS:
            continue
        if name not in merged:
            merged[name] = entry
    return merged


def merge_server_root_config(ctx: SyncContext, path: Path, root_key: str, rendered: dict[str, Any]) -> None:
    if not path.exists():
        return
    settings = load_json(path)
    existing = settings.get(root_key)
    if not isinstance(existing, dict):
        return
    settings[root_key] = merge_server_maps(rendered, existing)
    write_json(ctx, path, settings)


def render_shadow_copilot_mcp(registry: dict[str, Any], fallbacks: dict[str, str]) -> dict[str, Any]:
    servers = render_copilot_mcp(registry, fallbacks)["mcpServers"]
    for server in servers.values():
        server["source"] = "user"
    return servers


def extract_remote_url(command: str, args: list[Any]) -> str | None:
    if command != "npx":
        return None
    compact = [item for item in args if item != "-y"]
    if len(compact) == 2 and compact[0] == "mcp-remote" and isinstance(compact[1], str):
        return compact[1]
    return None


def render_opencode_mcp(registry: dict[str, Any], fallbacks: dict[str, str]) -> dict[str, Any]:
    servers: dict[str, Any] = {}
    for name, entry in enabled_registry_servers(registry).items():
        args = replace_arg_placeholders(entry.get("args", []), fallbacks, local_values=True)
        remote_url = extract_remote_url(entry["command"], args)
        server: dict[str, Any]
        if remote_url:
            server = {"type": "remote", "url": remote_url, "enabled": True}
        else:
            server = {"type": "local", "command": [entry["command"], *args], "enabled": True}
        if entry.get("env"):
            server["environment"] = {
                key: resolve_env_value(value["env_var"], fallbacks) for key, value in entry["env"].items()
            }
        servers[name] = server
    return servers


def render_opencode_lmstudio_provider(policy: dict[str, Any], fallbacks: dict[str, str]) -> dict[str, Any] | None:
    provider = local_llm_provider(policy, "lmstudio")
    if not provider:
        return None
    opencode = provider.get("opencode") if isinstance(provider.get("opencode"), dict) else {}
    models = opencode.get("models") if isinstance(opencode.get("models"), dict) else {}
    return {
        "npm": opencode.get("npm", "@ai-sdk/openai-compatible"),
        "name": provider.get("name", "LM Studio (local)"),
        "options": {
            "baseURL": resolve_local_llm_base_url(provider, fallbacks, local_values=True),
        },
        "models": models or {str(provider.get("default_model", "local-model")): {"name": "LM Studio Local Model"}},
    }


def merge_opencode_provider_entry(existing: Any, rendered: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(existing, dict):
        existing = {}
    merged = dict(existing)
    merged["npm"] = rendered["npm"]
    merged["name"] = rendered["name"]
    existing_options = existing.get("options") if isinstance(existing.get("options"), dict) else {}
    merged["options"] = {**existing_options, **rendered["options"]}
    existing_models = existing.get("models") if isinstance(existing.get("models"), dict) else {}
    merged["models"] = {**rendered["models"], **existing_models}
    return merged


def cherry_remote_transport(url: str) -> str:
    return "streamableHttp" if url.endswith("/mcp") else "sse"


def render_cherry_server(name: str, entry: dict[str, Any], fallbacks: dict[str, str]) -> dict[str, Any]:
    args = replace_arg_placeholders(entry.get("args", []), fallbacks, local_values=True)
    remote_url = extract_remote_url(entry["command"], args)

    if remote_url:
        server: dict[str, Any] = {
            "type": cherry_remote_transport(remote_url),
            "baseUrl": remote_url,
        }
    else:
        server = {
            "type": entry.get("transport", "stdio"),
            "command": entry["command"],
            "args": args,
        }

    if entry.get("env"):
        server["env"] = {key: resolve_env_value(value["env_var"], fallbacks) for key, value in entry["env"].items()}

    return server


def render_cherry_import_files(registry: dict[str, Any], fallbacks: dict[str, str]) -> dict[str, Any]:
    servers = {
        name: render_cherry_server(name, entry, fallbacks) for name, entry in enabled_registry_servers(registry).items()
    }
    files: dict[str, Any] = {"all.json": {"mcpServers": servers}}

    for name, server in servers.items():
        files[f"{name}.json"] = {"mcpServers": {name: server}}

    return files


def merge_opencode_config(
    ctx: SyncContext, registry: dict[str, Any], fallbacks: dict[str, str], policy: dict[str, Any] | None = None
) -> None:
    if not OPENCODE_CONFIG_PATH.exists():
        return

    settings = load_json(OPENCODE_CONFIG_PATH)
    lmstudio_provider = render_opencode_lmstudio_provider(policy or {}, fallbacks)
    if lmstudio_provider:
        providers = settings.get("provider")
        if not isinstance(providers, dict):
            providers = {}
            settings["provider"] = providers
        providers["lmstudio"] = merge_opencode_provider_entry(providers.get("lmstudio"), lmstudio_provider)

    existing_mcp = settings.get("mcp")
    settings["mcp"] = merge_server_maps(
        render_opencode_mcp(registry, fallbacks), existing_mcp if isinstance(existing_mcp, dict) else {}
    )
    settings["instructions"] = merge_unique_path_strings(
        [render_home_path(GLOBAL_MD), render_home_path(OPENCODE_GLOBAL_MD)],
        settings.get("instructions"),
    )

    skills = settings.get("skills")
    if not isinstance(skills, dict):
        skills = {}
        settings["skills"] = skills
    skills["paths"] = merge_unique_path_strings([render_home_path(SKILLS_DIR)], skills.get("paths"))

    defaults = (policy or {}).get("model_defaults", {}).get("opencode", {})
    if "model" in defaults:
        settings["model"] = defaults["model"]
    if "small_model" in defaults:
        settings["small_model"] = defaults["small_model"]

    def _update_nested_model(obj: Any, model: str) -> None:
        if not isinstance(obj, dict):
            return
        for key, value in obj.items():
            if isinstance(value, dict):
                if "model" in value:
                    value["model"] = model
                _update_nested_model(value, model)

    if "model" in defaults:
        _update_nested_model(settings.get("mode"), defaults["model"])
        _update_nested_model(settings.get("agent"), defaults["model"])

    write_json(ctx, OPENCODE_CONFIG_PATH, settings)


def merge_opencode_tui_config(ctx: SyncContext) -> None:
    settings: dict[str, Any] = {}
    if OPENCODE_TUI_CONFIG_PATH.exists():
        settings = load_json(OPENCODE_TUI_CONFIG_PATH)
    settings["notification_method"] = "auto"
    write_json(ctx, OPENCODE_TUI_CONFIG_PATH, settings)


def generate_project_opencode_config(ctx: SyncContext) -> None:
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
    write_json(ctx, OPENCODE_REPO_CONFIG_PATH, config)


def merge_cherry_studio_config(ctx: SyncContext) -> None:
    if not CHERRY_STUDIO_DIR.exists():
        return
    config_path = CHERRY_STUDIO_DIR / "config.json"
    settings: dict[str, Any] = {}
    if config_path.exists():
        settings = load_json(config_path)
    write_json(ctx, config_path, settings)


def merge_gemini_settings(
    ctx: SyncContext,
    registry: dict[str, Any],
    policy: dict[str, Any],
    fallbacks: dict[str, str],
    hook_registry: dict[str, Any],
) -> None:
    if not GEMINI_SETTINGS_PATH.exists():
        return
    settings = load_json(GEMINI_SETTINGS_PATH)
    settings["mcpServers"] = render_gemini_mcp(registry, fallbacks)

    if CLAUDE_SETTINGS_PATH.exists():
        claude_settings = load_json(CLAUDE_SETTINGS_PATH)
        for key in ["permissions", "enabledPlugins", "alwaysThinkingEnabled", "autoUpdatesChannel"]:
            if key in claude_settings:
                settings[key] = claude_settings[key]
    settings["hooks"] = merge_hook_groups(settings.get("hooks", {}), render_standard_hooks(hook_registry, "gemini-cli"))

    defaults = policy.get("model_defaults", {}).get("gemini", {})
    if "model" in defaults:
        settings["model"] = defaults["model"]
    if "effort_level" in defaults:
        settings["effortLevel"] = defaults["effort_level"]

    trusted = set(settings.get("trusted_folders", []))
    trusted.update(policy.get("trusted_roots", []))
    settings["trusted_folders"] = sorted(trusted)

    allowed = set(settings.get("allowed_urls", []))
    for domain in policy.get("docs_domains", []):
        allowed.add(f"https://{domain}")
    settings["allowed_urls"] = sorted(allowed)

    settings["experimental"] = True

    write_json(ctx, GEMINI_SETTINGS_PATH, settings)


def merge_client_mcp_config(ctx: SyncContext, path: Path, registry: dict[str, Any], fallbacks: dict[str, str]) -> None:
    if not path.exists():
        return
    settings = load_json(path)
    settings["mcpServers"] = render_client_mcp(registry, fallbacks)["mcpServers"]
    write_json(ctx, path, settings)


def merge_claude_settings_local(ctx: SyncContext, registry: dict[str, Any]) -> None:
    if not CLAUDE_SETTINGS_LOCAL_PATH.exists():
        return
    settings = load_json(CLAUDE_SETTINGS_LOCAL_PATH)
    enabled = settings.get("enabledMcpjsonServers")
    if not isinstance(enabled, list):
        return
    valid_names = set(enabled_registry_servers(registry))
    filtered: list[str] = []
    for name in enabled:
        if isinstance(name, str) and name in valid_names and name not in filtered:
            filtered.append(name)
    settings["enabledMcpjsonServers"] = filtered
    write_json(ctx, CLAUDE_SETTINGS_LOCAL_PATH, settings)


def sync_home_targets(
    ctx: SyncContext,
    registry: dict[str, Any],
    policy: dict[str, Any],
    fallbacks: dict[str, str],
    hook_registry: dict[str, Any],
) -> None:
    sync_codex_entrypoint(ctx)
    ensure_symlink(ctx, CLAUDE_ENTRYPOINT_PATH, GLOBAL_MD)
    ensure_symlink(ctx, COPILOT_ENTRYPOINT_PATH, COPILOT_GLOBAL_MD)
    write_text(ctx, GEMINI_ENTRYPOINT_PATH, f"@{REPO_ROOT / 'AGENTS.md'}\n@{GEMINI_GLOBAL_MD}\n")
    write_text(
        ctx,
        CLAUDE_COMPAT_MD,
        (
            "@/Users/ww/dev/projects/agents/instructions/global.md\n\n"
            "Compatibility shim only. Active configs should point directly at `global.md`.\n"
        ),
    )
    merge_claude_settings(ctx, policy, hook_registry)
    merge_claude_settings_local(ctx, registry)
    merge_client_mcp_config(ctx, CLAUDE_DESKTOP_CONFIG_PATH, registry, fallbacks)
    merge_client_mcp_config(ctx, CURSOR_MCP_PATH, registry, fallbacks)
    merge_copilot_config(ctx, policy)
    sync_copilot_subagent_env(ctx, policy)
    merge_gemini_settings(ctx, registry, policy, fallbacks, hook_registry)
    write_json(ctx, COPILOT_MCP_PATH, render_copilot_mcp(registry, fallbacks))
    merge_server_root_config(ctx, CHATGPT_MCP_PATH, "mcpServers", render_client_mcp(registry, fallbacks)["mcpServers"])
    merge_server_root_config(ctx, COPILOT_SHADOW_MCP_PATH, "mcpServers", render_shadow_copilot_mcp(registry, fallbacks))
    merge_server_root_config(
        ctx,
        GEMINI_ANTIGRAVITY_MCP_PATH,
        "mcpServers",
        render_client_mcp(registry, fallbacks)["mcpServers"],
    )
    merge_server_root_config(
        ctx,
        GEMINI_EXTENSION_MCP_PATH,
        "mcpServers",
        render_client_mcp(registry, fallbacks)["mcpServers"],
    )
    merge_opencode_config(ctx, registry, fallbacks, policy)
    merge_opencode_tui_config(ctx)
    merge_server_root_config(ctx, AITK_MCP_PATH, "servers", render_gemini_mcp(registry, fallbacks))
    merge_server_root_config(ctx, CRUSH_CONFIG_PATH, "mcp", render_gemini_mcp(registry, fallbacks))
    merge_codex_config(ctx, registry, policy, fallbacks)
    merge_codex_hooks(ctx, hook_registry)
    sync_generated_json_directory(
        ctx, CHERRY_STUDIO_MANAGED_IMPORT_DIR, render_cherry_import_files(registry, fallbacks)
    )
    merge_cherry_studio_config(ctx)
    sync_skill_entries(ctx, CODEX_SKILLS_DIR)
    sync_skill_entries(ctx, COPILOT_SKILLS_DIR)
    sync_skill_entries(ctx, GEMINI_SKILLS_DIR)
    sync_copilot_agents(ctx)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync repo-managed agent stack config into local harnesses.")
    parser.add_argument("--targets", default="all", help="Comma-separated list: repo,home,all")
    parser.add_argument("--apply", action="store_true", help="Apply changes")
    parser.add_argument("--check", action="store_true", help="Check drift without writing")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if not args.apply and not args.check:
        print("Pass --apply or --check.", file=sys.stderr)
        return 2
    ctx = SyncContext(apply=args.apply)
    policy = load_json(TOOLING_POLICY_PATH)
    registry = load_registry(ctx)
    hook_registry = load_hook_registry()
    fallbacks = load_current_secret_fallbacks()
    targets = {item.strip() for item in args.targets.split(",")} if args.targets != "all" else {"repo", "home"}
    if "repo" in targets:
        sync_repo_targets(ctx, registry, hook_registry)
    if "home" in targets:
        sync_home_targets(ctx, registry, policy, fallbacks, hook_registry)
    if args.check:
        for change in ctx.changes:
            print(change)
        return 1 if ctx.changes else 0
    for change in ctx.changes:
        print(change)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
