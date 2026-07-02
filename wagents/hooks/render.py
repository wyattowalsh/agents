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
from functools import lru_cache
from pathlib import Path
from typing import Any

from wagents.context import get_repo_root

HOOK_PERF_TIERS: tuple[str, ...] = ("legacy", "g1", "bundle", "worker")
BUNDLE_PERF_TIERS: frozenset[str] = frozenset({"bundle", "worker"})
DEFAULT_HARNESS_HOOK_TIMEOUT = 120
TOOLING_POLICY_PATH = get_repo_root() / "config" / "tooling-policy.json"
COPILOT_POST_EDIT_SHELL = "./hooks/post-edit-quality.sh"
CODEX_UNSUPPORTED_MATCHER_TOKENS: tuple[str, ...] = ("(?=", "(?!", "(?<=", "(?<!")

# When the same logical_policy would render on both events in a pair, drop the
# less-specific event (second element) only under bundle/worker tiers.
DEDUPE_EVENT_PAIRS: dict[str, tuple[tuple[str, str], ...]] = {
    "cursor": (
        ("PreToolUse", "BeforeShellExecution"),
        ("PostToolUse", "AfterFileEdit"),
    ),
}


@lru_cache(maxsize=1)
def _load_tooling_policy() -> dict[str, Any]:
    if not TOOLING_POLICY_PATH.is_file():
        return {}
    try:
        return json.loads(TOOLING_POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def resolve_hook_perf_tier(*, override: str | None = None) -> str:
    """Read staged hook perf tier from repo policy (default ``legacy``)."""
    if override is not None:
        return override if override in HOOK_PERF_TIERS else "legacy"
    policy = _load_tooling_policy()
    tier = str((policy.get("hook_perf") or {}).get("tier") or "legacy")
    return tier if tier in HOOK_PERF_TIERS else "legacy"


def _is_dispatcher_backed(hook: dict[str, Any]) -> bool:
    command = str(hook.get("command") or "")
    return any(token in command for token in ("wagents-hook.py", "run-wagents-hook", "{hook_runner}"))


def _bundle_timeout(members: list[dict[str, Any]]) -> int:
    return min(sum(int(member.get("timeout", 5)) for member in members), DEFAULT_HARNESS_HOOK_TIMEOUT)


def union_bundle_matchers(members: list[dict[str, Any]]) -> str | None:
    """Union every member's ``|``-delimited matcher into one deduped matcher string.

    Bundle-group members are not guaranteed to share an identical matcher: for
    example ``cursor-shell-file-guards`` groups a shell-only guard
    (``Bash|bash|run_shell_command|shell|terminal``) with a guard that also
    covers file-write tools (``Write|Edit|MultiEdit|...``). Collapsing them
    into one rendered entry using only the first member's matcher would
    silently narrow the surviving matcher and stop firing on tool calls the
    dropped member used to guard. Dedupe is case-sensitive and preserves
    first-seen order so the result stays deterministic across renders.
    """
    seen: dict[str, None] = {}
    for member in members:
        raw = str(member.get("matcher") or "")
        if not raw:
            continue
        for token in raw.split("|"):
            if token:
                seen.setdefault(token, None)
    return "|".join(seen) if seen else None


def _shell_bundle_command(members: list[dict[str, Any]]) -> str | None:
    commands = [str(member.get("command") or "") for member in members]
    if len(members) == 2 and all(cmd.endswith("auto-format.sh") or cmd.endswith("lint-check.sh") for cmd in commands):
        return COPILOT_POST_EDIT_SHELL
    if all(cmd.startswith("./hooks/") for cmd in commands):
        return commands[0]
    return None


def _synthetic_bundle_hook(members: list[dict[str, Any]], *, harness: str, perf_tier: str) -> dict[str, Any]:
    group = str(members[0].get("bundle_group") or members[0]["id"])
    policy_ids = [str(member["id"]) for member in members if _is_dispatcher_backed(member)]
    timeout = _bundle_timeout(members)
    bundle_mode = str(members[0].get("bundle_mode") or "enforce-chain")
    merged: dict[str, Any] = {
        "id": f"bundle-{group}",
        "logical_event": members[0]["logical_event"],
        "timeout": timeout,
        "harnesses": list(members[0].get("harnesses") or []),
        "bundle_group": members[0].get("bundle_group"),
        "logical_policy": members[0].get("logical_policy"),
        "mode": members[0].get("mode"),
        "description": members[0].get("description", group),
    }
    union_matcher = union_bundle_matchers(members)
    if union_matcher:
        merged["matcher"] = union_matcher
    if members[0].get("status_message"):
        merged["status_message"] = members[0]["status_message"]
    if len(policy_ids) == len(members):
        ids_csv = ",".join(policy_ids)
        if perf_tier == "worker":
            merged["command"] = (
                '{hook_runner} --worker-socket "${{WAGENTS_HOOK_WORKER_SOCKET:-}}" '
                f"--bundle {ids_csv} --harness {{harness}} "
                f"--bundle-mode {bundle_mode} --bundle-timeout {timeout}"
            )
        else:
            merged["command"] = (
                "{hook_runner} "
                f"--bundle {ids_csv} --harness {{harness}} "
                f"--bundle-mode {bundle_mode} --bundle-timeout {timeout}"
            )
        merged["_bundle_policy_ids"] = policy_ids
        return merged
    shell_command = _shell_bundle_command(members)
    if shell_command is not None:
        merged["command"] = shell_command
        return merged
    return dict(members[0])


def collapse_bundle_entries(
    hooks: list[dict[str, Any]],
    harness: str,
    *,
    perf_tier: str | None = None,
) -> list[dict[str, Any]]:
    """Collapse consecutive same-event ``bundle_group`` rows when tier is bundle/worker."""
    tier = perf_tier or resolve_hook_perf_tier()
    if tier not in BUNDLE_PERF_TIERS:
        return hooks

    collapsed: list[dict[str, Any]] = []
    index = 0
    while index < len(hooks):
        hook = hooks[index]
        group = hook.get("bundle_group")
        if not group:
            collapsed.append(hook)
            index += 1
            continue

        event = hook.get("logical_event")
        members = [hook]
        next_index = index + 1
        while next_index < len(hooks):
            candidate = hooks[next_index]
            if candidate.get("bundle_group") != group or candidate.get("logical_event") != event:
                break
            members.append(candidate)
            next_index += 1

        if len(members) == 1:
            collapsed.append(hook)
        else:
            collapsed.append(_synthetic_bundle_hook(members, harness=harness, perf_tier=tier))
        index = next_index
    return collapsed


def dedupe_logical_policy_across_events(
    hooks: list[dict[str, Any]],
    harness: str,
    *,
    perf_tier: str | None = None,
) -> list[dict[str, Any]]:
    """Drop duplicate ``logical_policy`` renders across overlapping native events."""
    tier = perf_tier or resolve_hook_perf_tier()
    if tier not in BUNDLE_PERF_TIERS:
        return hooks

    pairs = DEDUPE_EVENT_PAIRS.get(harness, ())
    if not pairs:
        return hooks

    policy_events: dict[str, set[str]] = {}
    for hook in hooks:
        logical_policy = str(hook.get("logical_policy") or hook.get("id"))
        event = str(hook.get("logical_event"))
        policy_events.setdefault(logical_policy, set()).add(event)

    drop_keys: set[tuple[str, str]] = set()
    for drop_event, keep_event in pairs:
        for logical_policy, events in policy_events.items():
            if drop_event in events and keep_event in events:
                drop_keys.add((logical_policy, drop_event))

    if not drop_keys:
        return hooks

    return [
        hook
        for hook in hooks
        if (str(hook.get("logical_policy") or hook.get("id")), str(hook.get("logical_event"))) not in drop_keys
    ]


def group_hooks_by_logical_event(hooks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Preserve registry order within each ``logical_event`` block.

    Bundle collapse only considers consecutive rows. Registry rows for different
    native events may interleave; regrouping keeps enforce chains collapsible
    without changing per-event relative order.
    """
    buckets: dict[str, list[dict[str, Any]]] = {}
    event_order: list[str] = []
    for hook in hooks:
        event = str(hook.get("logical_event") or "")
        if event not in buckets:
            buckets[event] = []
            event_order.append(event)
        buckets[event].append(hook)
    return [hook for event in event_order for hook in buckets[event]]


def prepare_hooks_for_render(
    hook_registry: dict[str, Any],
    harness: str,
    *,
    perf_tier: str | None = None,
) -> list[dict[str, Any]]:
    """Enabled harness hooks with optional dedupe + bundle collapse for render."""
    hooks = enabled_hooks_for_harness(hook_registry, harness)
    hooks = group_hooks_by_logical_event(hooks)
    hooks = dedupe_logical_policy_across_events(hooks, harness, perf_tier=perf_tier)
    return collapse_bundle_entries(hooks, harness, perf_tier=perf_tier)


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

# Hook ids that must stay fail-open on Cursor regardless of matcher shape. This
# was previously inferred from ``matcher == ".*"`` (a catch-all matcher implied
# "too disruptive to fail closed"), but G1 narrows some catch-all matchers for
# spawn-count wins without changing their intended fail-open crash behavior.
# Recorded explicitly so narrowing a matcher never silently flips failClosed.
CURSOR_FAIL_OPEN_HOOK_IDS: frozenset[str] = frozenset({"image-input-optimizer-guard"})

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
    runner = f'"{repo_root}/hooks/run-wagents-hook"'
    bundle_ids = hook.get("_bundle_policy_ids")
    if isinstance(bundle_ids, list) and bundle_ids:
        ids_csv = ",".join(str(policy_id) for policy_id in bundle_ids)
        bundle_mode = str(hook.get("bundle_mode") or "enforce-chain")
        timeout = int(hook.get("timeout", DEFAULT_HARNESS_HOOK_TIMEOUT))
        command = str(hook.get("command") or "")
        if "--worker-socket" in command or "wagents-hook-worker.py" in command:
            return (
                f'{runner} --worker-socket "${{WAGENTS_HOOK_WORKER_SOCKET:-}}" '
                f"--bundle {shlex.quote(ids_csv)} --harness {shlex.quote(harness)} "
                f"--bundle-mode {shlex.quote(bundle_mode)} --bundle-timeout {timeout}"
            )
        return (
            f"{runner} --bundle {shlex.quote(ids_csv)} --harness {shlex.quote(harness)} "
            f"--bundle-mode {shlex.quote(bundle_mode)} --bundle-timeout {timeout}"
        )
    policy_id = _wagents_policy_id(hook)
    # Single-policy worker tier is not rendered yet. When enabling --worker-socket here,
    # pass --forward-timeout from hook["timeout"] so socket forwards exceed policy budgets
    # (e.g. image-input-optimizer-guard 60s registry vs 5s client default).
    return f"{runner} {shlex.quote(policy_id)} --harness {shlex.quote(harness)}"


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
        stays_fail_open = str(hook.get("id") or "") in CURSOR_FAIL_OPEN_HOOK_IDS
        entry["failClosed"] = matcher != ".*" and not stays_fail_open
    return entry


def render_cursor_hooks(
    hook_registry: dict[str, Any],
    *,
    harness: str = "cursor",
    repo_root: str = "$CURSOR_PROJECT_DIR",
    event_map: dict[str, str] | None = None,
    perf_tier: str | None = None,
) -> dict[str, Any] | None:
    """Render the Cursor flat hook shape, or ``None`` when nothing is enabled.

    ``harness`` selects which registry rows apply (defaults to ``cursor``);
    ``repo_root`` is the path prefix substituted into command templates
    (``$CURSOR_PROJECT_DIR`` for project hooks, ``~/.cursor`` style for home).
    """
    events = event_map or CURSOR_EVENT_MAP
    rendered: dict[str, list[dict[str, Any]]] = {}
    for hook in prepare_hooks_for_render(hook_registry, harness, perf_tier=perf_tier):
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


def _codex_matcher(hook: dict[str, Any]) -> str | None:
    matcher = str(hook.get("matcher") or "")
    if not matcher:
        return None
    if any(token in matcher for token in CODEX_UNSUPPORTED_MATCHER_TOKENS):
        hook_id = str(hook.get("id") or "<unknown>")
        raise ValueError(f"Codex hook matcher for {hook_id!r} uses unsupported look-around syntax: {matcher}")
    return matcher


def render_codex_hooks(
    hook_registry: dict[str, Any],
    *,
    repo_root: str,
    perf_tier: str | None = None,
) -> dict[str, Any]:
    """Render Codex's nested-group hook shape (single source for sync + APM)."""
    rendered: dict[str, list[dict[str, Any]]] = {}
    for hook in prepare_hooks_for_render(hook_registry, "codex", perf_tier=perf_tier):
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
        matcher = _codex_matcher(hook)
        if matcher:
            group["matcher"] = matcher
        rendered.setdefault(event, []).append(group)
    return {"hooks": rendered}


def render_claude_hooks(
    hook_registry: dict[str, Any],
    *,
    repo_root: str,
    perf_tier: str | None = None,
) -> dict[str, Any]:
    """Render Claude Code's nested-group hook shape (single source for sync + APM)."""
    rendered: dict[str, list[dict[str, Any]]] = {}
    for hook in prepare_hooks_for_render(hook_registry, "claude-code", perf_tier=perf_tier):
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


def render_gemini_hooks(
    hook_registry: dict[str, Any],
    *,
    repo_root: str,
    perf_tier: str | None = None,
) -> dict[str, Any]:
    """Render Gemini CLI's nested-group hook shape (single source for sync + APM)."""
    rendered: dict[str, list[dict[str, Any]]] = {}
    for hook in prepare_hooks_for_render(hook_registry, "gemini-cli", perf_tier=perf_tier):
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


def render_copilot_hooks(
    hook_registry: dict[str, Any],
    *,
    repo_root: str,
    perf_tier: str | None = None,
) -> dict[str, Any]:
    """Render GitHub Copilot's flat ``bash`` hook shape (single source for sync + APM)."""
    rendered: dict[str, list[dict[str, Any]]] = {}
    for hook in prepare_hooks_for_render(hook_registry, "github-copilot", perf_tier=perf_tier):
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
