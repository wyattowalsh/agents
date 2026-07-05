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
from pathlib import Path
from typing import TYPE_CHECKING, Any

from wagents.context import REPO_ROOT_PROXY, get_repo_root
from wagents.hooks.merge import (  # re-exported for adapters that import from base
    HOOK_COMMAND_MARKERS as HOOK_COMMAND_MARKERS,
)
from wagents.hooks.merge import (
    merge_cursor_flat_hooks as merge_cursor_flat_hooks,
)
from wagents.hooks.merge import (
    merge_hook_groups as merge_hook_groups,
)
from wagents.hooks.merge import (
    strip_foreign_claude_hook_entries as strip_foreign_claude_hook_entries,
)
from wagents.hooks.merge import (
    strip_generated_hook_entries as strip_generated_hook_entries,
)
from wagents.mcphub.endpoints import (
    mcphub_bearer_env_var,
    mcphub_config,  # noqa: F401
    mcphub_enabled,
    mcphub_endpoint_specs,
    mcphub_projection_mode,
    mcphub_spec_enabled_for_harness,  # noqa: F401
)
from wagents.mcphub.endpoints import (
    render_mcphub_stdio_server as _render_mcphub_stdio_server,
)
from wagents.repo_paths import resolve_portable_path

if TYPE_CHECKING:
    from collections.abc import Callable

REPO_ROOT = REPO_ROOT_PROXY
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
    "package version": "package-version-check-mcp",
    "shannon problem solver": "shannon-thinking",
    "structured thinking": "structured-thinking",
}
REMOVED_MCP_SERVERS: set[str] = {
    "ableton",
    "apple-mail",
    "default",
    "desktop-commander",
    "playwright-headless",
    "serena",
    "web-search",
}

MANAGED_HEADER = "<!-- Managed by wagents. Do not edit directly. -->\n"


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

    def __init__(self, apply: bool = False, *, grok_plannotator_hooks: bool = True) -> None:
        self.apply = apply
        self.grok_plannotator_hooks = grok_plannotator_hooks
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


class ConfigDropError(RuntimeError):
    """Raised when a sync render would remove existing local config data."""


def _json_path(parent: str, segment: str | int) -> str:
    if isinstance(segment, int):
        return f"{parent}[{segment}]"
    if segment.isidentifier():
        return f"{parent}.{segment}"
    return f"{parent}[{json.dumps(segment, ensure_ascii=True)}]"


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def find_config_drops(current: Any, rendered: Any, path: str = "$") -> list[str]:
    """Return paths that exist in current config but are absent from rendered config."""
    if isinstance(current, dict):
        if not isinstance(rendered, dict):
            return [path]
        drops: list[str] = []
        for key, value in current.items():
            child_path = _json_path(path, str(key))
            if key not in rendered:
                drops.append(child_path)
                continue
            drops.extend(find_config_drops(value, rendered[key], child_path))
        return drops

    if isinstance(current, list):
        if not isinstance(rendered, list):
            return [path]
        rendered_counts: dict[str, int] = {}
        for item in rendered:
            rendered_key = _stable_json(item)
            rendered_counts[rendered_key] = rendered_counts.get(rendered_key, 0) + 1

        drops: list[str] = []
        for index, item in enumerate(current):
            item_key = _stable_json(item)
            remaining = rendered_counts.get(item_key, 0)
            if remaining > 0:
                rendered_counts[item_key] = remaining - 1
            else:
                drops.append(_json_path(path, index))
        return drops

    return []


def assert_no_config_drops(config_path: Path, current: Any, rendered: Any) -> None:
    drops = find_config_drops(current, rendered)
    if not drops:
        return
    preview = ", ".join(drops[:10])
    if len(drops) > 10:
        preview += f", ... (+{len(drops) - 10} more)"
    raise ConfigDropError(
        f"Refusing to update {config_path}: sync would remove local config entries: {preview}. "
        "Update the repo-managed source or remove the local entries explicitly."
    )


def normalize_existing_server_name(name: str, known_names: set[str]) -> str:
    normalized = normalize_name(name)
    lowered = normalized.lower()
    if lowered in known_names or lowered in REMOVED_MCP_SERVERS:
        return lowered
    return normalized


def merge_server_maps(
    rendered: dict[str, Any],
    existing: dict[str, Any],
    known_names: set[str] | None = None,
) -> dict[str, Any]:
    """Merge rendered MCP servers with existing ones, preserving unknown servers."""
    merged = dict(rendered)
    known_names = known_names or set(rendered)
    owns_mcphub_namespace = any(name.startswith("mcphub") for name in known_names)
    for name, entry in existing.items():
        normalized = normalize_existing_server_name(name, known_names)
        if (
            normalized in known_names
            or normalized in REMOVED_MCP_SERVERS
            or (owns_mcphub_namespace and normalized.startswith("mcphub"))
        ):
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
    if value.startswith(f"${REPO_ROOT}"):
        return resolve_portable_path(value, repo_root=get_repo_root(), home=HOME)
    if value == "~":
        return str(HOME.resolve())
    if value.startswith("~/"):
        return str((HOME / value[2:]).resolve())
    if value.startswith("/"):
        return str(Path(value).resolve())
    return resolve_portable_path(value, repo_root=get_repo_root(), home=HOME)


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


def render_mcphub_stdio_server(
    registry: dict[str, Any],
    url: str,
    fallbacks: dict[str, str],
    enabled: bool,
    *,
    local_values: bool = True,
) -> dict[str, Any]:
    return _render_mcphub_stdio_server(
        registry,
        url,
        enabled=enabled,
        fallbacks=fallbacks,
        local_values=local_values,
        render_env_value=render_env_value,
    )


def managed_registry_server_names(registry: dict[str, Any], harness: str | None = None) -> set[str]:
    names = set(enabled_registry_servers(registry, harness))
    if mcphub_enabled(registry):
        names.update(spec["name"] for spec in mcphub_endpoint_specs(registry, harness))
        names.update(spec["name"] for spec in mcphub_endpoint_specs(registry, None))
    names.update(normalize_name(name) for name in list(names))
    return names


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
        if mcphub_enabled(registry):
            mode = mcphub_projection_mode(registry, harness or self.name, "remote-stdio")
            token_env = mcphub_bearer_env_var(registry)
            return {
                "mcpServers": {
                    spec["name"]: (
                        {
                            "type": "http",
                            "url": spec["url"],
                            "enabled": bool(spec["enabled"]),
                            "headers": {"Authorization": f"Bearer ${{{token_env}}}"},
                        }
                        if mode == "http"
                        else render_mcphub_stdio_server(registry, spec["url"], fallbacks, bool(spec["enabled"]))
                    )
                    for spec in mcphub_endpoint_specs(registry, harness or self.name)
                }
            }

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
        *,
        repo_relative: bool = False,
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
            repo_root = "." if repo_relative else str(get_repo_root())
            config: dict[str, Any] = {
                "type": "command",
                "command": str(hook["command"]).format(
                    repo_root=repo_root,
                    hook_runner=f"{repo_root}/hooks/run-wagents-hook",
                    harness=self.name,
                ),
            }
            if hook.get("timeout"):
                config["timeout"] = int(hook["timeout"])
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
