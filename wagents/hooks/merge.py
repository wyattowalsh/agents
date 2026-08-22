"""Single-source hook merge helpers shared across projections.

``strip_generated_hook_entries`` and ``merge_hook_groups`` were previously
duplicated in ``wagents/platforms/base.py`` and ``scripts/sync_agent_stack.py``.
Both now import from here so generated-entry detection stays identical for every
harness (Claude nested groups and Cursor flat entries).
"""

from __future__ import annotations

from typing import Any

HOOK_COMMAND_MARKERS: tuple[str, ...] = ("wagents-hook.py", "run-wagents-hook")
CURSOR_PLANNOTATOR_MATCHER_TOKENS: tuple[str, ...] = (
    "exit_plan_mode",
    "ExitPlanMode",
    "enter_plan_mode",
    "EnterPlanMode",
    "CreatePlan",
    "SwitchMode",
    "create_plan",
)

# Claude Code native event names (PascalCase). Lowercase/camelCase rows are
# foreign projections that must not persist inside ``.claude/settings.json``.
CLAUDE_NATIVE_HOOK_EVENTS: frozenset[str] = frozenset({
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PermissionRequest",
    "PostToolUse",
    "PostToolUseFailure",
    "SubagentStart",
    "SubagentStop",
    "Stop",
})


def _entry_commands(entry: dict[str, Any]) -> list[str]:
    """Return command strings for an entry in either nested or flat shape.

    Nested (Claude/Codex): ``{"matcher"?, "hooks": [{"command"}]}``.
    Flat (Cursor): ``{"command"}`` directly on the entry.
    """
    raw_hooks = entry.get("hooks")
    hook_configs = raw_hooks if isinstance(raw_hooks, list) else [entry]
    return [
        str(config.get("command") or config.get("bash") or "") for config in hook_configs if isinstance(config, dict)
    ]


def _is_generated_entry(entry: dict[str, Any], managed_commands: frozenset[str]) -> bool:
    """Return True when an entry is wagents-managed and should be re-rendered.

    An entry is managed when any of its commands carries a wagents marker
    (``wagents-hook.py`` / ``run-wagents-hook``) *or* exactly matches a command
    in ``managed_commands`` (the set of freshly rendered commands). The second
    case is essential for registry hooks that shell out to plain scripts
    (e.g. ``./hooks/verify-before-stop.sh``) which carry no marker: without it,
    re-sync would treat them as user hooks, keep them, and append duplicate
    rendered copies on every run.
    """
    commands = _entry_commands(entry)
    if any(marker in command for marker in HOOK_COMMAND_MARKERS for command in commands):
        return True
    return any(command and command in managed_commands for command in commands)


def strip_generated_hook_entries(
    hooks: dict[str, Any],
    managed_commands: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    """Drop entries that are wagents-managed (marker or freshly-rendered command).

    Local, hand-authored hook entries are preserved so a re-sync never clobbers
    user-owned hooks; only previously generated entries are removed before the
    freshly rendered ones are merged back in.
    """
    if not isinstance(hooks, dict):
        return {}
    stripped: dict[str, list[Any]] = {}
    for event, entries in hooks.items():
        if not isinstance(entries, list):
            continue
        kept: list[Any] = []
        for entry in entries:
            if not isinstance(entry, dict):
                kept.append(entry)
                continue
            if _is_generated_entry(entry, managed_commands):
                continue
            kept.append(entry)
        if kept:
            stripped[event] = kept
    return stripped


def _managed_commands(generated: dict[str, Any]) -> frozenset[str]:
    commands: set[str] = set()
    for entries in generated.get("hooks", {}).values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict):
                commands.update(command for command in _entry_commands(entry) if command)
    return frozenset(commands)


def _is_foreign_claude_hook_entry(entry: dict[str, Any]) -> bool:
    """Return True when an entry does not belong in Claude nested-group settings."""
    if entry.get("bash") or entry.get("cwd") or entry.get("timeoutSec") or entry.get("comment"):
        return True
    nested = entry.get("hooks")
    if isinstance(nested, list) and nested:
        for config in nested:
            if not isinstance(config, dict):
                continue
            command = str(config.get("command") or config.get("bash") or "")
            if "${workspaceFolder}" in command:
                return True
            if "--harness cursor" in command:
                return True
        return False
    command = str(entry.get("command") or entry.get("bash") or "")
    return bool(command and not nested)


def strip_foreign_claude_hook_entries(hooks: dict[str, Any]) -> dict[str, Any]:
    """Drop foreign flat hook shapes that were merged into Claude settings."""
    if not isinstance(hooks, dict):
        return {}
    cleaned: dict[str, list[Any]] = {}
    for event, entries in hooks.items():
        if event not in CLAUDE_NATIVE_HOOK_EVENTS:
            continue
        if not isinstance(entries, list):
            continue
        kept = [entry for entry in entries if isinstance(entry, dict) and not _is_foreign_claude_hook_entry(entry)]
        if kept:
            cleaned[event] = kept
    return cleaned


# Codex nested-group native event names (PascalCase). CamelCase APM residue and
# Claude-only stop shells must not persist in project/home Codex hooks files.
CODEX_NATIVE_HOOK_EVENTS: frozenset[str] = frozenset({
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PermissionRequest",
    "PostToolUse",
    "PostToolUseFailure",
    "PreCompact",
    "PostCompact",
    "SubagentStart",
    "SubagentStop",
    "Stop",
})

# Legacy APM / shell paths that were superseded by wagents fleet projection.
CODEX_LEGACY_SHELL_BASENAMES: frozenset[str] = frozenset({
    "session-start.sh",
    "guard-destructive.sh",
    "protect-files.sh",
    "auto-format.sh",
    "lint-check.sh",
    "log-prompt.sh",
    "notify.sh",
    "post-edit-quality.sh",
})

# Claude-only stop/idle shells must not be re-projected onto Codex surfaces.
CODEX_CLAUDE_ONLY_SHELL_BASENAMES: frozenset[str] = frozenset({
    "verify-before-stop.sh",
    "task-completed-gate.sh",
    "teammate-idle-gate.sh",
})


def _command_basename(command: str) -> str:
    cleaned = command.strip().strip("'\"")
    if not cleaned:
        return ""
    # Handle both ``./hooks/foo.sh`` and absolute ``.../hooks/foo.sh``.
    name = cleaned.rsplit("/", 1)[-1]
    return name.split()[0] if name else ""


def _is_foreign_codex_hook_entry(entry: dict[str, Any]) -> bool:
    """Return True when an entry is stale APM residue or Claude-only on Codex."""
    # APM Copilot-shaped rows: top-level bash + timeoutSec + optional _apm_source.
    if entry.get("bash") or entry.get("timeoutSec") or entry.get("_apm_source"):
        return True
    if entry.get("cwd") and not entry.get("hooks"):
        return True

    commands = _entry_commands(entry)
    for command in commands:
        base = _command_basename(command)
        if base in CODEX_LEGACY_SHELL_BASENAMES:
            return True
        if base in CODEX_CLAUDE_ONLY_SHELL_BASENAMES:
            return True
        # Absolute or relative paths into legacy shell scripts.
        if "/hooks/" in command.replace("\\", "/"):
            path_base = command.replace("\\", "/").rsplit("/", 1)[-1].split()[0]
            if path_base in CODEX_LEGACY_SHELL_BASENAMES | CODEX_CLAUDE_ONLY_SHELL_BASENAMES:
                return True
    return False


def strip_foreign_codex_hook_entries(hooks: dict[str, Any]) -> dict[str, Any]:
    """Drop camelCase APM residue and Claude-only shells from Codex hook maps.

    Keeps only PascalCase Codex-native events and non-foreign entries so a
    re-sync cannot reintroduce dual-stack project contamination.
    """
    if not isinstance(hooks, dict):
        return {}
    cleaned: dict[str, list[Any]] = {}
    for event, entries in hooks.items():
        if event not in CODEX_NATIVE_HOOK_EVENTS:
            continue
        if not isinstance(entries, list):
            continue
        kept = [entry for entry in entries if isinstance(entry, dict) and not _is_foreign_codex_hook_entry(entry)]
        if kept:
            cleaned[event] = kept
    return cleaned


def _flat_entry_commands(entry: dict[str, Any]) -> list[str]:
    command = entry.get("command")
    return [str(command)] if isinstance(command, str) and command else []


def _is_managed_cursor_plannotator_entry(entry: dict[str, Any]) -> bool:
    """True for home Plannotator rows, including stale Claude/Grok matchers."""
    command = str(entry.get("command") or "")
    matcher = str(entry.get("matcher") or "")
    if "plannotator-plan-hook.py" in command:
        return True
    return "plannotator" in command and any(token in matcher for token in CURSOR_PLANNOTATOR_MATCHER_TOKENS)


def _is_managed_cursor_flat_entry(entry: dict[str, Any], managed_commands: frozenset[str]) -> bool:
    if "hooks" in entry:
        return True
    if _is_managed_cursor_plannotator_entry(entry):
        return True
    commands = _flat_entry_commands(entry)
    if any(marker in command for marker in HOOK_COMMAND_MARKERS for command in commands):
        return True
    return any(command in managed_commands for command in commands)


def strip_managed_cursor_flat_entries(
    hooks: dict[str, Any],
    managed_commands: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    """Drop wagents-managed or invalid nested entries from Cursor flat hook maps."""
    if not isinstance(hooks, dict):
        return {}
    stripped: dict[str, list[Any]] = {}
    for event, entries in hooks.items():
        if not isinstance(entries, list):
            continue
        kept: list[Any] = []
        for entry in entries:
            if not isinstance(entry, dict):
                kept.append(entry)
                continue
            if _is_managed_cursor_flat_entry(entry, managed_commands):
                continue
            kept.append(entry)
        if kept:
            stripped[event] = kept
    return stripped


def _managed_flat_commands(generated: dict[str, Any]) -> frozenset[str]:
    commands: set[str] = set()
    for entries in generated.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict):
                commands.update(command for command in _flat_entry_commands(entry) if command)
    return frozenset(commands)


def merge_cursor_flat_hooks(existing: dict[str, Any], generated: dict[str, Any]) -> dict[str, Any]:
    """Merge flat Cursor hook entries, stripping prior managed rows first."""
    managed = _managed_flat_commands(generated)
    merged = strip_managed_cursor_flat_entries(existing, managed)
    for event, entries in generated.items():
        if not isinstance(entries, list):
            continue
        merged.setdefault(event, [])
        merged[event].extend(entries)
    return merged


def merge_hook_groups(existing: dict[str, Any], generated: dict[str, Any]) -> dict[str, Any]:
    """Merge freshly rendered hook groups onto stripped existing hooks.

    Idempotent: existing entries that match a freshly rendered command are
    stripped first, so re-running the merge re-renders managed hooks in their
    canonical order instead of accumulating duplicates.
    """
    merged = strip_generated_hook_entries(existing, _managed_commands(generated))
    for event, entries in generated.get("hooks", {}).items():
        merged.setdefault(event, [])
        merged[event].extend(entries)
    return merged
