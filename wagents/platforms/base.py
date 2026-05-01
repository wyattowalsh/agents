"""Abstract base class and shared utilities for platform adapters.

The adapter interface is intentionally minimal: each platform implements
`sync_repo()` and `sync_home()` which perform all writes, while the base
class provides common helpers for JSON/TOML manipulation, server-map merging,
and env-placeholder resolution.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
HOME = Path.home()

# Normalized registry constants (mirrored from sync_agent_stack.py)
NAME_MAP: dict[str, str] = {
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
REMOVED_MCP_SERVERS: set[str] = {
    "ableton",
    "apple-mail",
    "default",
    "playwright-headless",
    "serena",
}

MANAGED_HEADER = "<!-- Managed by wagents. Do not edit directly. -->\n"
HOOK_COMMAND_MARKER = "wagents-hook.py"


def normalize_name(name: str) -> str:
    normalized = NAME_MAP.get(name)
    if normalized is not None:
        return normalized
    return NAME_MAP.get(name.lower(), name)


def env_placeholder(name: str) -> str:
    return "${" + name + "}"


def resolve_env_value(name: str, fallbacks: dict[str, str]) -> str:
    return os.environ.get(name) or fallbacks.get(name) or env_placeholder(name)


def render_env_value(value: dict[str, Any], fallbacks: dict[str, str], *, local_values: bool) -> str:
    if "value" in value:
        return str(value["value"])
    env_var = value["env_var"]
    return resolve_env_value(env_var, fallbacks) if local_values else env_placeholder(env_var)


def replace_arg_placeholders(args: list[Any], fallbacks: dict[str, str], *, local_values: bool) -> list[Any]:
    rendered: list[Any] = []
    for item in args:
        if isinstance(item, str) and item.startswith("${") and item.endswith("}"):
            env_name = item[2:-1]
            rendered.append(resolve_env_value(env_name, fallbacks) if local_values else item)
        else:
            rendered.append(item)
    return rendered


def load_json(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        without_line_comments = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("//"))
        return json.loads(without_line_comments)


def dump_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=True) + "\n"


class SyncContext:
    """Tracks pending changes and whether to apply them."""

    def __init__(self, apply: bool = False) -> None:
        self.apply = apply
        self.changes: list[str] = []

    def note(self, message: str) -> None:
        self.changes.append(message)

    def write_text(self, path: Path, content: str) -> None:
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == content:
            return
        self.note(f"update {path}")
        if not self.apply:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def write_json(self, path: Path, data: Any) -> None:
        self.write_text(path, dump_json(data))


def normalize_existing_server_name(name: str, known_names: set[str]) -> str:
    normalized = normalize_name(name)
    lowered = normalized.lower()
    if lowered in known_names or lowered in REMOVED_MCP_SERVERS:
        return lowered
    return normalized


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


def merge_server_maps(rendered: dict[str, Any], existing: dict[str, Any]) -> dict[str, Any]:
    """Merge rendered MCP servers with existing ones, preserving unknown servers."""
    merged = dict(rendered)
    known_names = set(rendered)
    for name, entry in existing.items():
        normalized = normalize_existing_server_name(name, known_names)
        if normalized in known_names or normalized in REMOVED_MCP_SERVERS:
            continue
        if name not in merged:
            merged[name] = entry
    return merged


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


def server_enabled_for_harness(entry: dict[str, Any], harness: str | None) -> bool:
    if entry.get("enabled") is False:
        return False
    return not (harness and harness in set(entry.get("exclude_from_harnesses", [])))


def enabled_registry_servers(registry: dict[str, Any], harness: str | None = None) -> dict[str, Any]:
    return {
        name: entry for name, entry in registry.get("servers", {}).items() if server_enabled_for_harness(entry, harness)
    }


class PlatformAdapter(ABC):
    """Abstract base for platform-specific asset generation.

    Subclasses must set `name` and implement `sync_repo()` / `sync_home()`.
    The base class provides shared utilities for JSON/TOML I/O, server-map
    merging, env resolution, and hook rendering.
    """

    name: str = ""

    # -- Availability --------------------------------------------------

    def is_available(self) -> bool:
        """Return True if the platform appears to be installed.

        Default heuristic: at least one home config path exists.
        Override for more precise detection.
        """
        return any(p.exists() for p in self.home_config_paths())

    # -- Path discovery ------------------------------------------------

    def repo_config_paths(self) -> list[Path]:
        """Paths for repo-local generated config (if any)."""
        return []

    def home_config_paths(self) -> list[Path]:
        """Paths for user home config files."""
        return []

    # -- Pure renderers ------------------------------------------------

    def render_mcp(
        self,
        registry: dict[str, Any],
        fallbacks: dict[str, str],
        harness: str | None = None,
    ) -> dict[str, Any]:
        """Render MCP server config in this platform's native format.

        Default returns a generic ``{mcpServers: {...}}`` structure.
        Platforms with special formatting (TOML, per-server files, etc.)
        should override.
        """
        servers: dict[str, Any] = {}
        for name, entry in enabled_registry_servers(registry, harness or self.name).items():
            server: dict[str, Any] = {
                "command": entry["command"],
                "args": replace_arg_placeholders(entry.get("args", []), fallbacks, local_values=True),
            }
            if entry.get("env"):
                server["env"] = {
                    key: render_env_value(value, fallbacks, local_values=True) for key, value in entry["env"].items()
                }
            servers[name] = server
        return {"mcpServers": servers}

    def render_hooks(self, hook_registry: dict[str, Any]) -> dict[str, Any] | None:
        """Render hook config for this platform, or None if unsupported.

        Default returns standard event-mapped command hooks.
        """
        event_map = {
            "UserPromptSubmit": "UserPromptSubmit",
            "PreToolUse": "PreToolUse",
            "PostToolUse": "PostToolUse",
            "Stop": "Stop",
        }
        return self._render_standard_hooks(hook_registry, event_map)

    # -- Impure sync entrypoints ---------------------------------------

    @abstractmethod
    def sync_repo(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        hook_registry: dict[str, Any],
        policy: dict[str, Any],
    ) -> None:
        """Sync repo-local generated targets for this platform."""
        raise NotImplementedError

    @abstractmethod
    def sync_home(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        policy: dict[str, Any],
        fallbacks: dict[str, str],
        hook_registry: dict[str, Any],
    ) -> None:
        """Sync user home targets for this platform."""
        raise NotImplementedError

    # -- Shared helpers ------------------------------------------------

    def _render_standard_hooks(
        self,
        hook_registry: dict[str, Any],
        event_map: dict[str, str],
    ) -> dict[str, Any] | None:
        """Render generic command hooks using a logical-event → platform-event map."""
        hooks = hook_registry.get("hooks", [])
        if not isinstance(hooks, list):
            return None
        rendered: dict[str, list[dict[str, Any]]] = {}
        for hook in hooks:
            if not isinstance(hook, dict) or not hook.get("command"):
                continue
            if self.name not in set(hook.get("harnesses", [])):
                continue
            event = event_map.get(str(hook.get("logical_event")))
            if not event:
                continue
            config: dict[str, Any] = {
                "type": "command",
                "command": str(hook["command"]).format(repo_root=str(REPO_ROOT), harness=self.name),
            }
            group: dict[str, Any] = {"hooks": [config]}
            if hook.get("matcher"):
                group["matcher"] = hook["matcher"]
            rendered.setdefault(event, []).append(group)
        return {"hooks": rendered} if rendered else None

    def _merge_json_config(self, ctx: SyncContext, path: Path, updater: Callable[[dict[str, Any]], None]) -> None:
        """Load JSON at *path*, apply *updater*(data), and write back."""
        if not path.exists():
            return
        data = load_json(path)
        updater(data)
        ctx.write_json(path, data)

    def _merge_server_root_config(self, ctx: SyncContext, path: Path, root_key: str, rendered: dict[str, Any]) -> None:
        """Replace *root_key* in a JSON file with merged server maps."""
        if not path.exists():
            return
        data = load_json(path)
        existing = data.get(root_key)
        if not isinstance(existing, dict):
            return
        data[root_key] = merge_server_maps(rendered, existing)
        ctx.write_json(path, data)
