"""Cursor adapter for repo-local project surfaces and home MCP merges."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from wagents.context import get_repo_root
from wagents.hooks.merge import merge_cursor_flat_hooks
from wagents.hooks.registry import sync_hook_projection
from wagents.hooks.render import render_cursor_global_hooks, render_cursor_hooks, resolve_hook_perf_tier
from wagents.parsing import parse_frontmatter
from wagents.platforms.base import (
    HOME,
    PlatformAdapter,
    SyncContext,
    enabled_registry_servers,
    load_json,
    managed_registry_server_names,
    mcphub_bearer_env_var,
    mcphub_enabled,
    mcphub_endpoint_specs,
    merge_server_maps,
)

CURSOR_HOME_MCP_PATH = HOME / ".cursor" / "mcp.json"
CURSOR_HOME_HOOKS_PATH = HOME / ".cursor" / "hooks.json"
CURSOR_MANAGED_AGENT_MARKER = "<!-- Managed by wagents. Source: agents/"


def cursor_project_dir() -> Path:
    return get_repo_root() / ".cursor"


def cursor_mcp_path() -> Path:
    return cursor_project_dir() / "mcp.json"


def cursor_hooks_path() -> Path:
    return cursor_project_dir() / "hooks.json"


def cursor_permissions_path() -> Path:
    return cursor_project_dir() / "permissions.json"


def cursor_cli_path() -> Path:
    return cursor_project_dir() / "cli.json"


def cursor_bugbot_path() -> Path:
    return cursor_project_dir() / "BUGBOT.md"


def cursor_agents_dir() -> Path:
    return cursor_project_dir() / "agents"


def cursor_skills_repo_dir() -> Path:
    return cursor_project_dir() / "skills" / "repo"


def cursor_agents_config_path() -> Path:
    return get_repo_root() / "config" / "cursor-agents.json"


def _cursor_render_string(value: str) -> str:
    """Render repo/env placeholders in Cursor's project config syntax."""
    repo_root = get_repo_root()
    repo_str = str(repo_root)
    if value == "${REPO_ROOT}":
        return "${workspaceFolder}"
    if value.startswith("${REPO_ROOT}/"):
        return "${workspaceFolder}/" + value.removeprefix("${REPO_ROOT}/")
    if value == repo_str:
        return "${workspaceFolder}"
    if value.startswith(repo_str + "/"):
        return "${workspaceFolder}/" + value[len(repo_str) + 1 :]
    if value.startswith("${") and value.endswith("}") and ":" not in value[2:-1]:
        env_name = value[2:-1]
        return f"${{env:{env_name}}}"
    return value


def _cursor_render_env_value(value: dict[str, Any]) -> str:
    if "value" in value:
        return str(value["value"])
    return f"${{env:{value['env_var']}}}"


def _cursor_render_list(values: list[Any]) -> list[Any]:
    return [_cursor_render_string(item) if isinstance(item, str) else item for item in values]


def _format_frontmatter(data: dict[str, Any]) -> str:
    return "---\n" + yaml.safe_dump(data, sort_keys=False, allow_unicode=False) + "---\n\n"


def _load_cursor_agent_overlays() -> dict[str, dict[str, Any]]:
    config = load_json(cursor_agents_config_path())
    overlays = config.get("agents")
    if not isinstance(overlays, list):
        raise ValueError("config/cursor-agents.json must contain an agents list")
    by_name: dict[str, dict[str, Any]] = {}
    for entry in overlays:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise ValueError("every Cursor agent overlay must include a name")
        by_name[entry["name"]] = entry
    return by_name


def _portable_agent_files() -> list[Path]:
    return sorted(path for path in (get_repo_root() / "agents").glob("*.md") if path.name != "README.md")


def _render_cursor_agent(path: Path, overlay: dict[str, Any]) -> str:
    frontmatter, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    name = str(frontmatter.get("name") or path.stem)
    data: dict[str, Any] = {
        "name": name,
        "description": str(overlay.get("description") or frontmatter.get("description") or ""),
        "model": str(overlay.get("model", "inherit")),
        "readonly": bool(overlay["readonly"]),
    }
    if "is_background" in overlay:
        data["is_background"] = bool(overlay["is_background"])
    return _format_frontmatter(data) + f"{CURSOR_MANAGED_AGENT_MARKER}{path.name} -->\n\n" + body.rstrip() + "\n"


def _render_cursor_agents() -> dict[str, str]:
    overlays = _load_cursor_agent_overlays()
    agent_files = _portable_agent_files()
    names = {parse_frontmatter(path.read_text(encoding="utf-8"))[0].get("name", path.stem) for path in agent_files}
    overlay_names = set(overlays)
    missing = sorted(str(name) for name in names - overlay_names)
    extra = sorted(overlay_names - {str(name) for name in names})
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing overlays: {', '.join(missing)}")
        if extra:
            details.append(f"unknown overlays: {', '.join(extra)}")
        raise ValueError("config/cursor-agents.json does not match agents/*.md (" + "; ".join(details) + ")")

    rendered: dict[str, str] = {}
    for path in agent_files:
        frontmatter, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        name = str(frontmatter.get("name") or path.stem)
        rendered[f"{name}.md"] = _render_cursor_agent(path, overlays[name])
    return rendered


def _sync_generated_text_directory(ctx: SyncContext, directory: Path, rendered: dict[str, str]) -> None:
    if ctx.apply:
        directory.mkdir(parents=True, exist_ok=True)
    for name, content in sorted(rendered.items()):
        ctx.write_text(directory / name, content)
    if not directory.exists():
        return
    for path in sorted(directory.glob("*.md")):
        if path.name in rendered:
            continue
        try:
            current = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if not current.startswith("---\n") or CURSOR_MANAGED_AGENT_MARKER not in current:
            continue
        ctx.note(f"remove stale generated Cursor agent {path}")
        if ctx.apply:
            path.unlink()


def _sync_skill_symlinks(ctx: SyncContext) -> None:
    source_root = get_repo_root() / "skills"
    target_root = cursor_skills_repo_dir()
    skills = sorted(path for path in source_root.iterdir() if path.is_dir() and (path / "SKILL.md").exists())
    if ctx.apply:
        target_root.mkdir(parents=True, exist_ok=True)
    for skill in skills:
        target = target_root / skill.name
        desired = Path("../..") / ".." / "skills" / skill.name
        if target.is_symlink() and Path(target.readlink()) == desired:
            continue
        if target.exists() or target.is_symlink():
            if target.is_symlink():
                ctx.note(f"update Cursor skill symlink {target} -> {desired}")
                if ctx.apply:
                    target.unlink()
                    target.symlink_to(desired, target_is_directory=True)
                continue
            ctx.note(f"skip Cursor skill symlink {target}: path exists and is not a symlink")
            continue
        ctx.note(f"create Cursor skill symlink {target} -> {desired}")
        if ctx.apply:
            target.symlink_to(desired, target_is_directory=True)
    if not target_root.exists():
        return
    expected = {skill.name for skill in skills}
    for target in sorted(target_root.iterdir()):
        if target.name in expected or not target.is_symlink():
            continue
        ctx.note(f"remove stale Cursor skill symlink {target}")
        if ctx.apply:
            target.unlink()


class Adapter(PlatformAdapter):
    name = "cursor"

    def repo_config_paths(self) -> list[Path]:
        return [
            cursor_mcp_path(),
            cursor_hooks_path(),
            cursor_permissions_path(),
            cursor_cli_path(),
            cursor_bugbot_path(),
            cursor_agents_dir(),
            cursor_skills_repo_dir(),
        ]

    def home_config_paths(self) -> list[Path]:
        return [CURSOR_HOME_MCP_PATH, CURSOR_HOME_HOOKS_PATH]

    def sync_repo(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        hook_registry: dict[str, Any],
        policy: dict[str, Any],
    ) -> None:
        ctx.write_json(cursor_mcp_path(), self.render_mcp(registry, {}, harness="cursor"))
        perf_tier = resolve_hook_perf_tier()
        sync_hook_projection(
            ctx.write_json,
            harness="cursor",
            dest_path=cursor_hooks_path(),
            render_fn=lambda: self.render_hooks(
                hook_registry,
                repo_root="$CURSOR_PROJECT_DIR",
                perf_tier=perf_tier,
            ),
            perf_tier=perf_tier,
            apply=ctx.apply,
        )
        ctx.write_json(cursor_permissions_path(), self.render_permissions(policy))
        ctx.write_json(cursor_cli_path(), self.render_cli_config(policy))
        ctx.write_text(cursor_bugbot_path(), self.render_bugbot(policy))
        _sync_generated_text_directory(ctx, cursor_agents_dir(), _render_cursor_agents())
        _sync_skill_symlinks(ctx)

    def sync_home(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        policy: dict[str, Any],
        fallbacks: dict[str, str],
        hook_registry: dict[str, Any],
    ) -> None:
        if CURSOR_HOME_MCP_PATH.exists():
            data = load_json(CURSOR_HOME_MCP_PATH)
            rendered = self.render_mcp(registry, fallbacks)["mcpServers"]
            existing = data.get("mcpServers")
            data["mcpServers"] = merge_server_maps(
                rendered,
                existing if isinstance(existing, dict) else {},
                managed_registry_server_names(registry, self.name),
            )
            ctx.write_json(CURSOR_HOME_MCP_PATH, data)

        rendered_global = render_cursor_global_hooks()
        if rendered_global is None:
            return
        existing_hooks: dict[str, Any] = {}
        if CURSOR_HOME_HOOKS_PATH.exists():
            existing_payload = load_json(CURSOR_HOME_HOOKS_PATH)
            raw_hooks = existing_payload.get("hooks")
            if isinstance(raw_hooks, dict):
                existing_hooks = raw_hooks
        merged_hooks = merge_cursor_flat_hooks(existing_hooks, rendered_global.get("hooks", {}))
        ctx.write_json(
            CURSOR_HOME_HOOKS_PATH,
            {"version": int(rendered_global.get("version", 1)), "hooks": merged_hooks},
        )

    def render_mcp(
        self,
        registry: dict[str, Any],
        fallbacks: dict[str, str],
        harness: str | None = None,
    ) -> dict[str, Any]:
        if mcphub_enabled(registry):
            token_env = mcphub_bearer_env_var(registry)
            servers: dict[str, Any] = {}
            for spec in mcphub_endpoint_specs(registry, harness or self.name):
                if not spec.get("enabled"):
                    continue
                servers[str(spec["name"])] = {
                    "type": "http",
                    "url": spec["url"],
                    "headers": {"Authorization": f"Bearer ${{env:{token_env}}}"},
                }
            return {"mcpServers": servers}

        servers: dict[str, Any] = {}
        for name, entry in enabled_registry_servers(registry, harness or self.name).items():
            transport = str(entry.get("transport", "stdio"))
            server: dict[str, Any] = {"type": transport}
            if transport == "stdio":
                server["command"] = _cursor_render_string(str(entry["command"]))
                server["args"] = _cursor_render_list(entry.get("args", []))
                if entry.get("env"):
                    server["env"] = {key: _cursor_render_env_value(value) for key, value in entry["env"].items()}
                if entry.get("envFile"):
                    server["envFile"] = _cursor_render_string(str(entry["envFile"]))
            else:
                if entry.get("url"):
                    server["url"] = _cursor_render_string(str(entry["url"]))
                if entry.get("headers"):
                    server["headers"] = {
                        key: _cursor_render_string(str(value)) for key, value in entry["headers"].items()
                    }
            if entry.get("timeout_ms"):
                server["timeout"] = entry["timeout_ms"]
            servers[name] = server
        return {"mcpServers": servers}

    def render_hooks(
        self,
        hook_registry: dict[str, Any],
        *,
        repo_root: str = "$CURSOR_PROJECT_DIR",
        perf_tier: str | None = None,
    ) -> dict[str, Any] | None:
        """Render Cursor's flat hook shape: ``{event: [{command, matcher?, timeout?, failClosed?}]}``.

        Cursor expects flat per-event entries, *not* the nested Claude-style
        ``{"hooks": [{"type": "command", ...}]}`` group shape. See
        ``wagents.hooks.render.render_cursor_hooks`` for the authoritative shape.
        """
        return render_cursor_hooks(hook_registry, harness=self.name, repo_root=repo_root, perf_tier=perf_tier)

    def render_permissions(self, policy: dict[str, Any]) -> dict[str, Any]:
        return {
            "autoRun": {
                "block_instructions": [
                    (
                        "Ask before deleting files, rewriting git history, force-pushing, "
                        "or running destructive shell commands."
                    ),
                    "Ask before reading .env files, credentials, private keys, service-account files, or token stores.",
                    "Ask before running migrations, deployments, or commands that change external services.",
                    "Ask before installing packages or executing unreviewed scripts from the network.",
                ]
            }
        }

    def render_cli_config(self, policy: dict[str, Any]) -> dict[str, Any]:
        return {
            "permissions": {
                "allow": [
                    "Read(AGENTS.md)",
                    "Read(instructions/**)",
                    "Read(config/**)",
                    "Read(agents/**)",
                    "Read(skills/**)",
                    "Shell(git:status*)",
                    "Shell(git:diff*)",
                    "Shell(rg:*)",
                    "Shell(ls:*)",
                    "Shell(uv:run wagents validate*)",
                    "Shell(uv:run wagents openspec validate*)",
                    "WebFetch(cursor.com)",
                ],
                "deny": [
                    "Read(.env*)",
                    "Read(**/.env*)",
                    "Read(**/*secret*)",
                    "Read(**/*token*)",
                    "Write(.env*)",
                    "Write(**/.env*)",
                    "Write(**/*.key)",
                    "Shell(git:reset*)",
                    "Shell(git:clean*)",
                    "Shell(git:push*)",
                    "Shell(rm)",
                    "Shell(sudo)",
                    "Shell(curl:*)",
                    "Shell(wget:*)",
                ],
            }
        }

    def render_bugbot(self, policy: dict[str, Any]) -> str:
        return """# Bugbot Project Rules

Review this repository as a cross-platform agent asset bundle. Treat `AGENTS.md`,
`instructions/global.md`, `config/*`, `agents/*.md`, `skills/*/SKILL.md`, and
`scripts/sync_agent_stack.py` as source-of-truth surfaces.

- Flag edits that mutate generated outputs without updating the source and
  rerunning the relevant generator.
- Flag new or changed Cursor support that mutates `~/.cursor`, dashboard/team
  settings, Cloud Agent settings, Bugbot Admin API state, OAuth state, or live
  installs without explicit maintainer approval.
- Flag `.cursor/permissions.json` changes that add `mcpAllowlist` or
  `terminalAllowlist` without a source config that explicitly opts into
  overriding Cursor UI allowlists.
- Flag `.cursor/cli.json` changes that include global-only CLI fields instead
  of project-level `permissions`.
- Flag Cursor MCP entries that expose secrets directly instead of using
  `${env:NAME}`, or repo paths that do not use `${workspaceFolder}`.
- Require focused tests for sync, adapter rendering, hooks, permissions, and
  schema/registry coverage after Cursor support changes.
"""
