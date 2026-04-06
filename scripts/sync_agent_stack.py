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
CLAUDE_COMPAT_MD = REPO_ROOT / "instructions" / "claude-code-global.md"
COPILOT_GLOBAL_MD = REPO_ROOT / "instructions" / "copilot-global.md"
MCP_REGISTRY_PATH = CONFIG_DIR / "mcp-registry.json"
TOOLING_POLICY_PATH = CONFIG_DIR / "tooling-policy.json"
SYNC_MANIFEST_PATH = CONFIG_DIR / "sync-manifest.json"
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
CLAUDE_ENTRYPOINT_PATH = HOME / ".claude" / "CLAUDE.md"
CODEX_ENTRYPOINT_PATH = HOME / ".codex" / "AGENTS.md"
CODEX_CONFIG_PATH = HOME / ".codex" / "config.toml"
CODEX_SKILLS_DIR = HOME / ".codex" / "skills"
COPILOT_ENTRYPOINT_PATH = HOME / ".copilot" / "copilot-instructions.md"
COPILOT_CONFIG_PATH = HOME / ".copilot" / "config.json"
COPILOT_MCP_PATH = HOME / ".copilot" / "mcp-config.json"
COPILOT_AGENTS_HOME_DIR = HOME / ".copilot" / "agents"
COPILOT_SKILLS_DIR = HOME / ".copilot" / "skills"
GEMINI_SETTINGS_PATH = HOME / ".gemini" / "settings.json"
GEMINI_ENTRYPOINT_PATH = HOME / ".gemini" / "GEMINI.md"
GEMINI_SKILLS_DIR = HOME / ".gemini" / "skills"

CODEX_MCP_BEGIN = "# BEGIN MANAGED BY sync_agent_stack.py: MCP_SERVERS"
CODEX_MCP_END = "# END MANAGED BY sync_agent_stack.py: MCP_SERVERS"
MANAGED_HEADER = "<!-- Managed by scripts/sync_agent_stack.py. Do not edit directly. -->\n"
TOML_TABLE_RE = re.compile(r"^\[(?P<header>[^\]]+)\]\s*$")

NAME_MAP = {
    "apple_mail": "apple-mail",
}
CORE_INVENTORY = [
    "context7",
    "brave-search",
    "deepwiki",
    "fetch",
    "fetcher",
    "playwright",
    "chrome-devtools",
    "docling",
    "package-version",
    "structured-thinking",
    "cascade-thinking",
    "sequential-thinking",
    "tavily",
    "repomix",
    "trafilatura",
    "web-search",
]
NORMALIZED_BASES: dict[str, dict[str, Any]] = {
    "brave-search": {
        "command": "npx",
        "args": ["-y", "@brave/brave-search-mcp-server"],
    },
    "chrome-devtools": {
        "command": "npx",
        "args": ["-y", "chrome-devtools-mcp@latest", "--autoConnect"],
    },
    "context7": {
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp", "--api-key", "${CONTEXT7_API_KEY}"],
    },
    "default": {
        "command": "npx",
        "args": ["-y", "mcp-remote", "https://mcp.w4w.dev/mcp/default"],
        "enabled": False,
    },
    "docling": {
        "command": "uvx",
        "args": ["--from=docling-mcp", "docling-mcp-server"],
    },
    "playwright": {
        "command": "npx",
        "args": ["-y", "@playwright/mcp@latest", "--cdp-endpoint", "http://127.0.0.1:9222"],
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
    return NAME_MAP.get(name, name)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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


def ensure_symlink(ctx: SyncContext, path: Path, target: Path) -> None:
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
    path.symlink_to(target)


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


def resolve_env_value(name: str, fallbacks: dict[str, str]) -> str:
    return os.environ.get(name) or fallbacks.get(name) or env_placeholder(name)


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


def render_repo_mcp(registry: dict[str, Any]) -> dict[str, Any]:
    servers: dict[str, Any] = {}
    for name, entry in registry["servers"].items():
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
    for name, entry in registry["servers"].items():
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


def render_codex_mcp_block(registry: dict[str, Any], fallbacks: dict[str, str]) -> str:
    lines = [CODEX_MCP_BEGIN]
    for name, entry in registry["servers"].items():
        lines.append("")
        lines.append(f"[mcp_servers.{name}]")
        lines.append(
            f"args = {toml_value(replace_arg_placeholders(entry.get('args', []), fallbacks, local_values=True))}"
        )
        lines.append(f"command = {toml_value(entry['command'])}")
        lines.append(f"startup_timeout_sec = {toml_value(entry.get('startup_timeout_sec', 90))}")
        lines.append(f"type = {toml_value(entry.get('transport', 'stdio'))}")
        if entry.get("enabled") is False:
            lines.append("enabled = false")
        lines.append("")
        lines.append(f"[mcp_servers.{name}.env]")
        for env_name, env_meta in entry.get("env", {}).items():
            lines.append(f"{env_name} = {toml_value(resolve_env_value(env_meta['env_var'], fallbacks))}")
    lines.append("")
    lines.append(CODEX_MCP_END)
    return "\n".join(lines) + "\n"


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
    managed_names = set(registry["servers"])
    filtered_chunks: list[str] = []
    for header, chunk in chunk_toml_sections(remove_managed_codex_block(current)):
        server_name = codex_mcp_server_name(header)
        if server_name and server_name in managed_names:
            continue
        filtered_chunks.append(chunk)
    filtered = "".join(filtered_chunks).strip()
    model_defaults = policy.get("model_defaults", {}).get("codex", {})
    reasoning_effort = model_defaults.get("reasoning_effort", "xhigh")
    replacements = {
        "model = ": f'model = "{model_defaults.get("model", "gpt-5.4")}"',
        "model_reasoning_effort = ": f'model_reasoning_effort = "{reasoning_effort}"',
        "plan_mode_reasoning_effort = ": f'plan_mode_reasoning_effort = "{reasoning_effort}"',
        "personality = ": f'personality = "{model_defaults.get("personality", "pragmatic")}"',
    }
    filtered_lines = []
    for line in filtered.splitlines():
        replaced = False
        for prefix, value in replacements.items():
            if line.startswith(prefix):
                filtered_lines.append(value)
                replaced = True
                break
        if not replaced:
            filtered_lines.append(line)
    shared_root = '[projects."/Users/ww/dev/projects"]\ntrust_level = "trusted"'
    filtered_text = "\n".join(filtered_lines).rstrip() + "\n\n"
    if shared_root not in filtered_text:
        filtered_text += shared_root + "\n\n"
    rendered = filtered_text + render_codex_mcp_block(registry, fallbacks)
    write_text(ctx, CODEX_CONFIG_PATH, rendered)


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


def generate_copilot_hooks(ctx: SyncContext) -> None:
    hooks_config = {
        "version": 1,
        "hooks": {
            "sessionStart": [{"type": "command", "bash": "./hooks/session-start.sh", "cwd": ".", "timeoutSec": 15}],
            "userPromptSubmitted": [{"type": "command", "bash": "./hooks/log-prompt.sh", "cwd": ".", "timeoutSec": 5}],
            "preToolUse": [
                {"type": "command", "bash": "./hooks/guard-destructive.sh", "cwd": ".", "timeoutSec": 5},
                {"type": "command", "bash": "./hooks/protect-files.sh", "cwd": ".", "timeoutSec": 5},
            ],
            "postToolUse": [
                {"type": "command", "bash": "./hooks/auto-format.sh", "cwd": ".", "timeoutSec": 30},
                {"type": "command", "bash": "./hooks/lint-check.sh", "cwd": ".", "timeoutSec": 30},
            ],
        },
    }
    write_json(ctx, COPILOT_HOOKS_DIR / "policy.json", hooks_config)


def merge_claude_settings(ctx: SyncContext, policy: dict[str, Any]) -> None:
    settings = load_json(CLAUDE_SETTINGS_PATH)
    allow = settings.setdefault("permissions", {}).setdefault("allow", [])
    for domain in policy.get("docs_domains", []):
        token = f"WebFetch(domain:{domain})"
        if token not in allow:
            allow.append(token)
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
    config = load_json(COPILOT_CONFIG_PATH)
    defaults = policy.get("model_defaults", {}).get("copilot", {})
    config["model"] = defaults.get("model", config.get("model"))
    config["effortLevel"] = defaults.get("effort_level", config.get("effortLevel"))
    trusted = set(config.get("trusted_folders", []))
    trusted.update(policy.get("trusted_roots", []))
    config["trusted_folders"] = sorted(trusted)
    allowed = set(config.get("allowed_urls", []))
    for domain in policy.get("docs_domains", []):
        allowed.add(f"https://{domain}")
    config["allowed_urls"] = sorted(allowed)
    write_json(ctx, COPILOT_CONFIG_PATH, config)


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


def sync_repo_targets(ctx: SyncContext, registry: dict[str, Any]) -> None:
    write_json(ctx, MCP_REGISTRY_PATH, registry)
    write_json(ctx, REPO_MCP_PATH, render_repo_mcp(registry))
    write_json(ctx, VSCODE_MCP_PATH, render_repo_mcp(registry))
    generate_copilot_repo_instructions(ctx)
    generate_copilot_rule_instructions(ctx)
    generate_copilot_hooks(ctx)


def render_gemini_mcp(registry: dict[str, Any], fallbacks: dict[str, str]) -> dict[str, Any]:
    servers: dict[str, Any] = {}
    for name, entry in registry["servers"].items():
        if entry.get("enabled") is False:
            continue
        server: dict[str, Any] = {
            "type": entry.get("transport", "stdio"),
            "command": entry["command"],
            "args": replace_arg_placeholders(entry.get("args", []), fallbacks, local_values=True),
        }
        if entry.get("env"):
            server["env"] = {key: resolve_env_value(value["env_var"], fallbacks) for key, value in entry["env"].items()}
        servers[name] = server
    return servers

def merge_gemini_settings(
    ctx: SyncContext, registry: dict[str, Any], policy: dict[str, Any], fallbacks: dict[str, str]
) -> None:
    if not GEMINI_SETTINGS_PATH.exists():
        return
    settings = load_json(GEMINI_SETTINGS_PATH)
    settings["mcpServers"] = render_gemini_mcp(registry, fallbacks)
    
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

def sync_home_targets(
    ctx: SyncContext, registry: dict[str, Any], policy: dict[str, Any], fallbacks: dict[str, str]
) -> None:
    ensure_symlink(ctx, CODEX_ENTRYPOINT_PATH, GLOBAL_MD)
    ensure_symlink(ctx, CLAUDE_ENTRYPOINT_PATH, GLOBAL_MD)
    ensure_symlink(ctx, COPILOT_ENTRYPOINT_PATH, COPILOT_GLOBAL_MD)
    write_text(ctx, GEMINI_ENTRYPOINT_PATH, f"@{GLOBAL_MD}\n")
    write_text(
        ctx,
        CLAUDE_COMPAT_MD,
        (
            "@/Users/ww/dev/projects/agents/instructions/global.md\n\n"
            "Compatibility shim only. Active configs should point directly at `global.md`.\n"
        ),
    )
    merge_claude_settings(ctx, policy)
    merge_copilot_config(ctx, policy)
    merge_gemini_settings(ctx, registry, policy, fallbacks)
    write_json(ctx, COPILOT_MCP_PATH, render_copilot_mcp(registry, fallbacks))
    merge_codex_config(ctx, registry, policy, fallbacks)
    sync_skill_entries(ctx, CODEX_SKILLS_DIR)
    sync_skill_entries(ctx, COPILOT_SKILLS_DIR)
    sync_skill_entries(ctx, GEMINI_SKILLS_DIR)
    sync_copilot_agents(ctx)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync Codex, Claude, and Copilot config from repo-managed sources.")
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
    fallbacks = load_current_secret_fallbacks()
    targets = {item.strip() for item in args.targets.split(",")} if args.targets != "all" else {"repo", "home"}
    if "repo" in targets:
        sync_repo_targets(ctx, registry)
    if "home" in targets:
        sync_home_targets(ctx, registry, policy, fallbacks)
    if args.check:
        for change in ctx.changes:
            print(change)
        return 1 if ctx.changes else 0
    for change in ctx.changes:
        print(change)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
