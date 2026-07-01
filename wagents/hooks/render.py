"""Shared hook renderers and logical-event maps for harness projections.

The registry stores hooks with a ``logical_event`` (Claude-style PascalCase).
Each harness maps those logical events onto its native event names and emits a
harness-specific entry shape. This module centralizes the maps and the Cursor
flat-shape renderer so the Cursor adapter (``wagents.platforms.cursor``) and the
APM materializer (``wagents.apm``) produce byte-identical output.

Cursor hook shape (authoritative, https://cursor.com/docs/agent/hooks):

    {
      "version": 1,
      "hooks": {
        "preToolUse": [
          {"command": "...", "matcher": "Bash", "timeout": 5, "failClosed": true}
        ]
      }
    }

Entries are **flat** ``{command, matcher?, timeout?, failClosed?}`` objects — not
the nested Claude ``{"hooks": [{"type": "command", ...}]}`` group shape.
"""

from __future__ import annotations

import json
import shlex
from pathlib import Path
from typing import Any

from wagents.context import get_repo_root

# Logical event -> Cursor native event name.
# Cursor supports both the generic preToolUse/postToolUse surface and the
# fine-grained beforeShellExecution/afterFileEdit/etc. surface. The registry's
# logical events map onto the generic surface plus session/prompt/stop events.
CURSOR_EVENT_MAP: dict[str, str] = {
    "SessionStart": "sessionStart",
    "SessionEnd": "sessionEnd",
    "UserPromptSubmit": "beforeSubmitPrompt",
    "PreToolUse": "preToolUse",
    "PostToolUse": "postToolUse",
    "PostToolUseFailure": "postToolUseFailure",
    "SubagentStart": "subagentStart",
    "SubagentStop": "subagentStop",
    "BeforeShellExecution": "beforeShellExecution",
    "AfterShellExecution": "afterShellExecution",
    "BeforeMCPExecution": "beforeMCPExecution",
    "AfterMCPExecution": "afterMCPExecution",
    "BeforeReadFile": "beforeReadFile",
    "AfterFileEdit": "afterFileEdit",
    "PreCompact": "preCompact",
    "Stop": "stop",
}

# Cursor pre-execution events where a fail-closed enforce hook should block on
# crash/timeout/invalid-JSON instead of failing open.
CURSOR_FAIL_CLOSED_EVENTS: frozenset[str] = frozenset({
    "preToolUse",
    "beforeShellExecution",
    "beforeMCPExecution",
    "beforeReadFile",
})

# Logical event -> native event name for the nested-group harnesses. Codex and
# Claude keep PascalCase native names; Gemini uses its own surface.
CODEX_EVENT_MAP: dict[str, str] = {
    "SessionStart": "SessionStart",
    "UserPromptSubmit": "UserPromptSubmit",
    "PreToolUse": "PreToolUse",
    "PermissionRequest": "PermissionRequest",
    "PostToolUse": "PostToolUse",
    "PreCompact": "PreCompact",
    "PostCompact": "PostCompact",
    "SubagentStart": "SubagentStart",
    "SubagentStop": "SubagentStop",
    "Stop": "Stop",
}

CLAUDE_EVENT_MAP: dict[str, str] = {
    "SessionStart": "SessionStart",
    "UserPromptSubmit": "UserPromptSubmit",
    "PreToolUse": "PreToolUse",
    "PermissionRequest": "PermissionRequest",
    "PostToolUse": "PostToolUse",
    "SubagentStart": "SubagentStart",
    "SubagentStop": "SubagentStop",
    "Stop": "Stop",
}

GEMINI_EVENT_MAP: dict[str, str] = {
    "SessionStart": "sessionStart",
    "UserPromptSubmit": "BeforeAgent",
    "PreToolUse": "BeforeTool",
    "PostToolUse": "AfterTool",
    "SessionEnd": "sessionEnd",
    "Stop": "AfterAgent",
}

COPILOT_EVENT_MAP: dict[str, str] = {
    "SessionStart": "sessionStart",
    "UserPromptSubmit": "userPromptSubmitted",
    "PreToolUse": "preToolUse",
    "PostToolUse": "postToolUse",
    "SessionEnd": "sessionEnd",
}


def enabled_hooks_for_harness(hook_registry: dict[str, Any], harness: str) -> list[dict[str, Any]]:
    """Return registry hooks with a command that target ``harness``."""
    hooks = hook_registry.get("hooks", [])
    if not isinstance(hooks, list):
        return []
    return [
        hook
        for hook in hooks
        if isinstance(hook, dict) and hook.get("command") and harness in set(hook.get("harnesses", []))
    ]


def render_hook_command(hook: dict[str, Any], harness: str, *, repo_root: str) -> str:
    """Render a hook command template with repo/harness placeholders resolved."""
    return str(hook["command"]).format(
        repo_root=repo_root,
        hook_runner=f"{repo_root}/hooks/run-wagents-hook",
        harness=harness,
    )


def _wagents_policy_id(hook: dict[str, Any]) -> str:
    command = str(hook.get("command") or "")
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    for index, part in enumerate(parts):
        if (
            part == "{hook_runner}" or part.endswith("/run-wagents-hook") or part.endswith("/wagents-hook.py")
        ) and index + 1 < len(parts):
            return parts[index + 1]
    return str(hook.get("logical_policy") or hook["id"])


def render_cursor_hook_command(hook: dict[str, Any], harness: str, *, repo_root: str) -> str:
    """Render Cursor wagents hooks through the shell-expanded project runner.

    Cursor currently passes hook command strings to the shell without expanding
    ``${workspaceFolder}``, while ``$CURSOR_PROJECT_DIR`` is available to the
    hook environment. Use the repo runner for all wagents policies so the
    trusted-Python lookup and script path resolution stay centralized.
    """
    policy_id = _wagents_policy_id(hook)
    return f'"{repo_root}/hooks/run-wagents-hook" {shlex.quote(policy_id)} --harness {shlex.quote(harness)}'


def _cursor_flat_entry(
    hook: dict[str, Any],
    event: str,
    *,
    harness: str,
    repo_root: str,
) -> dict[str, Any]:
    """Build one flat Cursor hook entry: ``{command, matcher?, timeout?, failClosed?}``."""
    matcher = str(hook.get("matcher") or "")
    entry: dict[str, Any] = {"command": render_cursor_hook_command(hook, harness, repo_root=repo_root)}
    if hook.get("matcher"):
        entry["matcher"] = hook["matcher"]
    if hook.get("timeout"):
        entry["timeout"] = int(hook["timeout"])
    if hook.get("mode") == "enforce" and event in CURSOR_FAIL_CLOSED_EVENTS:
        entry["failClosed"] = matcher != ".*"
    return entry


def render_cursor_hooks(
    hook_registry: dict[str, Any],
    *,
    harness: str = "cursor",
    repo_root: str = "$CURSOR_PROJECT_DIR",
    event_map: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """Render the Cursor flat hook shape, or ``None`` when nothing is enabled.

    ``harness`` selects which registry rows apply (defaults to ``cursor``);
    ``repo_root`` is the path prefix substituted into command templates
    (``$CURSOR_PROJECT_DIR`` for project hooks, ``~/.cursor`` style for home).
    """
    events = event_map or CURSOR_EVENT_MAP
    rendered: dict[str, list[dict[str, Any]]] = {}
    for hook in enabled_hooks_for_harness(hook_registry, harness):
        event = events.get(str(hook.get("logical_event")))
        if not event:
            continue
        rendered.setdefault(event, []).append(
            _cursor_flat_entry(hook, event, harness=harness, repo_root=repo_root)
        )
    if not rendered:
        return None
    return {"version": 1, "hooks": rendered}


CURSOR_GLOBAL_HOOKS_PATH = get_repo_root() / "config" / "cursor-global-hooks.json"
PLANNOTATOR_BIN_PLACEHOLDER = "__PLANNOTATOR_BIN__"


def resolve_plannotator_binary() -> Path:
    return Path.home() / ".local" / "bin" / "plannotator"


def _substitute_cursor_global_placeholders(payload: str) -> str:
    plannotator_bin = str(resolve_plannotator_binary())
    return payload.replace(PLANNOTATOR_BIN_PLACEHOLDER, plannotator_bin)


def render_cursor_global_hooks(*, template_path: Path | None = None) -> dict[str, Any] | None:
    """Render home-global Cursor hooks (for example Plannotator plan review) in flat shape."""
    path = template_path or CURSOR_GLOBAL_HOOKS_PATH
    if not path.is_file():
        return None
    try:
        data = json.loads(_substitute_cursor_global_placeholders(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError:
        return None
    hooks = data.get("hooks")
    if not isinstance(hooks, dict) or not hooks:
        return None
    rendered: dict[str, list[dict[str, Any]]] = {}
    for event, entries in hooks.items():
        if not isinstance(entries, list):
            continue
        flat_entries: list[dict[str, Any]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            command = entry.get("command")
            if not isinstance(command, str) or not command:
                continue
            flat: dict[str, Any] = {"command": command}
            if entry.get("matcher"):
                flat["matcher"] = entry["matcher"]
            if entry.get("timeout") is not None:
                flat["timeout"] = int(entry["timeout"])
            if entry.get("failClosed") is not None:
                flat["failClosed"] = bool(entry["failClosed"])
            flat_entries.append(flat)
        if flat_entries:
            rendered[str(event)] = flat_entries
    if not rendered:
        return None
    return {"version": int(data.get("version", 1)), "hooks": rendered}


def _codex_status_message(hook: dict[str, Any]) -> str:
    return str(hook.get("statusMessage") or hook.get("status_message") or hook.get("description") or hook["id"])


def render_codex_hooks(hook_registry: dict[str, Any], *, repo_root: str) -> dict[str, Any]:
    """Render Codex's nested-group hook shape (single source for sync + APM)."""
    rendered: dict[str, list[dict[str, Any]]] = {}
    for hook in enabled_hooks_for_harness(hook_registry, "codex"):
        event = CODEX_EVENT_MAP.get(str(hook.get("logical_event")))
        if not event:
            continue
        config: dict[str, Any] = {
            "type": "command",
            "command": render_hook_command(hook, "codex", repo_root=repo_root),
            "timeout": int(hook.get("timeout", 5)),
            "statusMessage": _codex_status_message(hook),
        }
        command_windows = hook.get("commandWindows") or hook.get("command_windows")
        if command_windows:
            config["commandWindows"] = str(command_windows).format(
                repo_root=repo_root,
                hook_runner=f"{repo_root}/hooks/run-wagents-hook",
                harness="codex",
            )
        group: dict[str, Any] = {"hooks": [config]}
        if hook.get("matcher"):
            group["matcher"] = hook["matcher"]
        rendered.setdefault(event, []).append(group)
    return {"hooks": rendered}


def render_claude_hooks(hook_registry: dict[str, Any], *, repo_root: str) -> dict[str, Any]:
    """Render Claude Code's nested-group hook shape (single source for sync + APM)."""
    rendered: dict[str, list[dict[str, Any]]] = {}
    for hook in enabled_hooks_for_harness(hook_registry, "claude-code"):
        event = CLAUDE_EVENT_MAP.get(str(hook.get("logical_event")))
        if not event:
            continue
        config: dict[str, Any] = {
            "type": "command",
            "command": render_hook_command(hook, "claude-code", repo_root=repo_root),
        }
        if hook.get("timeout"):
            config["timeout"] = int(hook["timeout"])
        group: dict[str, Any] = {"hooks": [config]}
        if hook.get("matcher"):
            group["matcher"] = hook["matcher"]
        rendered.setdefault(event, []).append(group)
    return {"hooks": rendered}


def render_gemini_hooks(hook_registry: dict[str, Any], *, repo_root: str) -> dict[str, Any]:
    """Render Gemini CLI's nested-group hook shape (single source for sync + APM)."""
    rendered: dict[str, list[dict[str, Any]]] = {}
    for hook in enabled_hooks_for_harness(hook_registry, "gemini-cli"):
        event = GEMINI_EVENT_MAP.get(str(hook.get("logical_event")))
        if not event:
            continue
        config: dict[str, Any] = {
            "type": "command",
            "command": render_hook_command(hook, "gemini-cli", repo_root=repo_root),
            "name": hook["id"],
            "timeout": int(hook.get("timeout", 5)) * 1000,
            "description": hook.get("description", hook["id"]),
        }
        group: dict[str, Any] = {"hooks": [config], "sequential": True}
        if hook.get("matcher"):
            group["matcher"] = hook["matcher"]
        rendered.setdefault(event, []).append(group)
    return {"hooks": rendered}


def render_copilot_hooks(hook_registry: dict[str, Any], *, repo_root: str) -> dict[str, Any]:
    """Render GitHub Copilot's flat ``bash`` hook shape (single source for sync + APM)."""
    rendered: dict[str, list[dict[str, Any]]] = {}
    for hook in enabled_hooks_for_harness(hook_registry, "github-copilot"):
        event = COPILOT_EVENT_MAP.get(str(hook.get("logical_event")))
        if not event:
            continue
        rendered.setdefault(event, []).append({
            "type": "command",
            "bash": render_hook_command(hook, "github-copilot", repo_root=repo_root),
            "cwd": ".",
            "timeoutSec": int(hook.get("timeout", 5)),
            "comment": hook.get("description", hook["id"]),
        })
    return {"version": int(hook_registry.get("version", 1)), "hooks": rendered}
