"""Grok Build CLI adapter."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from wagents.platforms.base import (
    HOME,
    REPO_ROOT,
    PlatformAdapter,
    SyncContext,
    enabled_registry_servers,
    mcphub_bearer_env_var,
    mcphub_config,
    mcphub_enabled,
    mcphub_endpoint_specs,
    mcphub_projection_mode,
    render_env_value,
    render_mcphub_stdio_server,
)

GROK_CONFIG_PATH = HOME / ".grok" / "config.toml"
GROK_CONFIG_REPO_PATH = REPO_ROOT / ".grok" / "config.toml"
GROK_CONFIG_POLICY_PATH = REPO_ROOT / "config" / "grok-config.toml"
GROK_BINARY_PATH = HOME / ".grok" / "bin" / "grok"
GROK_AGENTS_HOME_DIR = HOME / ".grok" / "agents"
AGENTS_DIR = REPO_ROOT / "agents"

GROK_MCP_BEGIN = "# BEGIN MANAGED BY sync_agent_stack.py: MCP_SERVERS"
GROK_MCP_END = "# END MANAGED BY sync_agent_stack.py: MCP_SERVERS"
GROK_POLICY_BEGIN = "# BEGIN MANAGED BY sync_agent_stack.py: GROK_POLICY"
GROK_POLICY_END = "# END MANAGED BY sync_agent_stack.py: GROK_POLICY"

TOML_TABLE_RE = re.compile(r"^\[(?P<header>[^\]]+)\]\s*$")

GROK_REPLACE_OWNED_PREFIXES: tuple[str, ...] = (
    "models",
    "telemetry",
    "compat",
    "plugins",
    "mcp_servers",
)

GROK_BLEND_OWNED_PREFIXES: tuple[str, ...] = (
    "ui",
    "features",
    "session",
    "tools",
    "toolset",
    "subagents",
    "memory",
)

GROK_OWNED_TABLE_PREFIXES: tuple[str, ...] = GROK_REPLACE_OWNED_PREFIXES + GROK_BLEND_OWNED_PREFIXES


class GrokConfigDropError(RuntimeError):
    """Raised when a Grok sync would drop preserved user-owned TOML tables."""


def toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        items = ", ".join(f"{json.dumps(str(key))} = {toml_value(val)}" for key, val in value.items())
        return "{" + items + "}"
    raise TypeError(f"Unsupported TOML value: {value!r}")


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


def _header_matches_prefix(header: str, prefix: str) -> bool:
    return header == prefix or header.startswith(f"{prefix}.")


def is_grok_blend_header(header: str | None) -> bool:
    if header is None:
        return False
    return any(_header_matches_prefix(header, prefix) for prefix in GROK_BLEND_OWNED_PREFIXES)


def is_grok_owned_header(header: str | None) -> bool:
    if header is None:
        return False
    return any(_header_matches_prefix(header, prefix) for prefix in GROK_OWNED_TABLE_PREFIXES)


def parse_toml_table_kv(chunk: str) -> tuple[str | None, dict[str, str]]:
    """Parse a single TOML table chunk into header and top-level key/value lines."""
    header: str | None = None
    values: dict[str, str] = {}
    for line in chunk.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = TOML_TABLE_RE.match(stripped)
        if match:
            header = match.group("header")
            continue
        if "=" in stripped and not stripped.startswith("["):
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip()
    return header, values


def render_toml_table(header: str | None, values: dict[str, str]) -> str:
    lines: list[str] = []
    if header:
        lines.append(f"[{header}]")
    for key in sorted(values):
        lines.append(f"{key} = {values[key]}")
    return "\n".join(lines)


def blend_owned_table(policy_chunk: str, user_chunk: str) -> str:
    """Merge two table chunks; policy keys override, user-only keys are kept."""
    policy_header, policy_kv = parse_toml_table_kv(policy_chunk)
    user_header, user_kv = parse_toml_table_kv(user_chunk)
    header = policy_header or user_header
    merged = dict(user_kv)
    merged.update(policy_kv)
    return render_toml_table(header, merged)


def extract_blend_chunks(current: str) -> dict[str, str]:
    """Return blend-owned table chunks from current config (post managed/MCP strip)."""
    chunks: dict[str, str] = {}
    for header, chunk in chunk_toml_sections(current):
        if header and is_grok_blend_header(header):
            chunks[header] = chunk.strip()
    return chunks


def apply_blend_to_policy_body(body: str, user_blend: dict[str, str]) -> str:
    if not user_blend:
        return body
    parts: list[str] = []
    for header, chunk in chunk_toml_sections(body):
        if header and header in user_blend:
            parts.append(blend_owned_table(chunk, user_blend[header]))
        else:
            parts.append(chunk.strip())
    return "\n\n".join(part for part in parts if part) + ("\n" if parts else "")


def registry_mcp_server_names(registry: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    if mcphub_enabled(registry):
        for spec in mcphub_endpoint_specs(registry, "grok"):
            names.add(str(spec["name"]))
    else:
        names.update(enabled_registry_servers(registry, "grok").keys())
    return names


def strip_registry_mcp_tables(text: str, names: set[str]) -> str:
    if not names:
        return text
    kept: list[str] = []
    for header, chunk in chunk_toml_sections(text):
        if header and header.startswith("mcp_servers."):
            server_name = header.split(".", 1)[1]
            if server_name in names:
                continue
        kept.append(chunk.rstrip())
    return "\n\n".join(part for part in kept if part.strip()) + ("\n" if kept else "")


def strip_before_merge(text: str, registry: dict[str, Any] | None = None) -> str:
    stripped = remove_managed_grok_blocks(text)
    if registry is not None:
        stripped = strip_registry_mcp_tables(stripped, registry_mcp_server_names(registry))
    return stripped


def remove_managed_block(text: str, begin: str, end: str) -> str:
    start = text.find(begin)
    if start == -1:
        return text
    stop = text.find(end, start)
    if stop == -1:
        return text[:start]
    stop += len(end)
    while stop < len(text) and text[stop] == "\n":
        stop += 1
    prefix = text[:start].rstrip("\n")
    suffix = text[stop:].lstrip("\n")
    if prefix and suffix:
        return prefix + "\n\n" + suffix
    if prefix:
        return prefix + "\n"
    return suffix


def remove_managed_grok_blocks(text: str) -> str:
    text = remove_managed_block(text, GROK_POLICY_BEGIN, GROK_POLICY_END)
    return remove_managed_block(text, GROK_MCP_BEGIN, GROK_MCP_END)


def render_codex_args(entry: dict[str, Any]) -> list[Any]:
    args = list(entry.get("args", []))
    env_names = {value["env_var"] for value in entry.get("env", {}).values() if "env_var" in value}
    rendered: list[Any] = []
    for item in args:
        if isinstance(item, str) and item.startswith("${") and item.endswith("}"):
            env_name = item[2:-1]
            if env_name in env_names:
                rendered.append(item)
                continue
        rendered.append(item)
    return rendered


def render_grok_mcp_block(registry: dict[str, Any]) -> str:
    lines = [GROK_MCP_BEGIN]
    if mcphub_enabled(registry):
        mode = mcphub_projection_mode(registry, "grok", "http")
        token_env = mcphub_bearer_env_var(registry)
        auth_header = f"Bearer ${{{token_env}}}"
        for spec in mcphub_endpoint_specs(registry, "grok"):
            lines.append("")
            lines.append(f"[mcp_servers.{spec['name']}]")
            if mode == "http":
                lines.append(f"url = {toml_value(spec['url'])}")
                lines.append(f'headers = {{ "Authorization" = {toml_value(auth_header)} }}')
            else:
                entry = render_mcphub_stdio_server(registry, spec["url"], {}, enabled=bool(spec["enabled"]))
                lines.append(f"command = {toml_value(entry['command'])}")
                lines.append(f"args = {toml_value(entry['args'])}")
                lines.append(f"env = {toml_value(entry['env'])}")
            startup_timeout_sec = int(mcphub_config(registry).get("startup_timeout_sec", 20))
            tool_timeout_sec = int(mcphub_config(registry).get("tool_timeout_sec", 90))
            lines.append(f"startup_timeout_sec = {toml_value(startup_timeout_sec)}")
            lines.append(f"tool_timeout_sec = {toml_value(tool_timeout_sec)}")
            lines.append(f"enabled = {toml_value(bool(spec['enabled']))}")
        lines.append("")
        lines.append(GROK_MCP_END)
        return "\n".join(lines) + "\n"

    for name, entry in enabled_registry_servers(registry, "grok").items():
        lines.append("")
        lines.append(f"[mcp_servers.{name}]")
        lines.append(f"command = {toml_value(entry['command'])}")
        lines.append(f"args = {toml_value(render_codex_args(entry))}")
        lines.append(f"startup_timeout_sec = {toml_value(entry.get('startup_timeout_sec', 90))}")
        if entry.get("timeout_ms"):
            lines.append(f"tool_timeout_sec = {toml_value(max(1, int(entry['timeout_ms']) // 1000))}")
        if entry.get("env"):
            env_map = {key: render_env_value(value, {}, local_values=False) for key, value in entry["env"].items()}
            lines.append(f"env = {toml_value(env_map)}")
    lines.append("")
    lines.append(GROK_MCP_END)
    return "\n".join(lines) + "\n"


def apply_model_defaults(body: str, policy: dict[str, Any]) -> str:
    defaults = policy.get("model_defaults", {}).get("grok", {})
    if not defaults:
        return body
    lines = body.splitlines()
    out: list[str] = []
    in_models = False
    seen: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if stripped == "[models]":
            in_models = True
            out.append(line)
            continue
        if in_models and stripped.startswith("["):
            in_models = False
        if in_models and "=" in stripped and not stripped.startswith("#"):
            key = stripped.split("=", 1)[0].strip()
            seen.add(key)
            if key in defaults:
                out.append(f'{key} = {toml_value(defaults[key])}')
                continue
        out.append(line)
    if "models" not in {ln.strip().strip("[]") for ln in out if ln.strip().startswith("[")}:
        out.append("[models]")
    for key, value in defaults.items():
        if key not in seen:
            out.append(f"{key} = {toml_value(value)}")
    return "\n".join(out).rstrip() + "\n"


def load_policy_template() -> str:
    if GROK_CONFIG_POLICY_PATH.exists():
        return GROK_CONFIG_POLICY_PATH.read_text(encoding="utf-8").rstrip() + "\n"
    return ""


def render_grok_policy_block(
    *,
    current: str = "",
    repo_root: Path | None = None,
    policy: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
) -> str:
    user_blend = extract_blend_chunks(strip_before_merge(current, registry))
    body = apply_model_defaults(load_policy_template().strip(), policy or {})
    body = apply_blend_to_policy_body(body, user_blend)
    lines = [GROK_POLICY_BEGIN]
    if body:
        lines.append(body)
    if repo_root is not None:
        lines.append("")
        lines.append("[plugins]")
        lines.append(f"paths = [{toml_value(str(repo_root))}]")
    lines.append(GROK_POLICY_END)
    return "\n".join(lines).rstrip() + "\n"


def render_preserved_grok_config(current: str, registry: dict[str, Any] | None = None) -> str:
    stripped = strip_before_merge(current, registry)
    preserved_chunks: list[str] = []
    for header, chunk in chunk_toml_sections(stripped):
        if is_grok_owned_header(header):
            continue
        preserved_chunks.append(chunk.strip())
    return "\n\n".join(chunk for chunk in preserved_chunks if chunk)


def preserved_table_headers(text: str, registry: dict[str, Any] | None = None) -> set[str]:
    """Non-owned table headers that must survive merge (blend/replace owned tables excluded)."""
    headers: set[str] = set()
    for header, _ in chunk_toml_sections(strip_before_merge(text, registry)):
        if header and not is_grok_owned_header(header):
            headers.add(header)
    return headers


def assert_no_grok_config_drops(
    before: str,
    after: str,
    registry: dict[str, Any] | None = None,
) -> None:
    before_headers = preserved_table_headers(before, registry)
    after_headers = preserved_table_headers(after, registry)
    dropped = sorted(before_headers - after_headers)
    if not dropped:
        return
    preview = ", ".join(dropped[:10])
    if len(dropped) > 10:
        preview += f", ... (+{len(dropped) - 10} more)"
    raise GrokConfigDropError(
        f"Refusing to update Grok config: sync would remove user-owned tables: {preview}"
    )


def render_grok_config(
    current: str,
    registry: dict[str, Any],
    *,
    repo_only: bool,
    repo_root: Path | None = None,
    policy: dict[str, Any] | None = None,
) -> str:
    if repo_only:
        return render_grok_mcp_block(registry)

    preserved = render_preserved_grok_config(current, registry).rstrip()
    parts: list[str] = []
    if preserved:
        parts.append(preserved)
    parts.append(
        render_grok_policy_block(
            current=current,
            repo_root=repo_root,
            policy=policy or {},
            registry=registry,
        ).rstrip()
    )
    parts.append(render_grok_mcp_block(registry).rstrip())
    return "\n\n".join(part for part in parts if part) + "\n"


def sync_grok_agents(ctx: SyncContext) -> None:
    if not AGENTS_DIR.is_dir():
        return
    if ctx.apply:
        GROK_AGENTS_HOME_DIR.mkdir(parents=True, exist_ok=True)
    for agent_file in sorted(AGENTS_DIR.glob("*.md")):
        destination = GROK_AGENTS_HOME_DIR / agent_file.name
        if destination.is_symlink() and destination.resolve() == agent_file.resolve():
            continue
        if destination.exists() and not destination.is_symlink():
            continue
        ctx.note(f"symlink {agent_file} -> {destination}")
        if ctx.apply:
            if destination.exists() or destination.is_symlink():
                destination.unlink()
            destination.symlink_to(agent_file)


class Adapter(PlatformAdapter):
    name = "grok"

    def home_config_paths(self) -> list[Path]:
        return [GROK_CONFIG_PATH, GROK_CONFIG_REPO_PATH]

    def repo_config_paths(self) -> list[Path]:
        return [GROK_CONFIG_POLICY_PATH, GROK_CONFIG_REPO_PATH]

    def is_available(self) -> bool:
        return GROK_BINARY_PATH.exists() or GROK_CONFIG_PATH.exists()

    def sync_repo(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        hook_registry: dict[str, Any],
        policy: dict[str, Any],
    ) -> None:
        del hook_registry, policy
        ctx.write_text(GROK_CONFIG_REPO_PATH, render_grok_config("", registry, repo_only=True))

    def sync_home(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        policy: dict[str, Any],
        fallbacks: dict[str, str],
        hook_registry: dict[str, Any],
    ) -> None:
        del fallbacks, hook_registry
        current = GROK_CONFIG_PATH.read_text(encoding="utf-8") if GROK_CONFIG_PATH.exists() else ""
        rendered = render_grok_config(current, registry, repo_only=False, repo_root=REPO_ROOT, policy=policy)
        assert_no_grok_config_drops(current, rendered, registry)
        ctx.write_text(GROK_CONFIG_PATH, rendered)
        sync_grok_agents(ctx)
