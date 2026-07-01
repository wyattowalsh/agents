"""Single-source hook merge helpers shared across projections.

``strip_generated_hook_entries`` and ``merge_hook_groups`` were previously
duplicated in ``wagents/platforms/base.py`` and ``scripts/sync_agent_stack.py``.
Both now import from here so generated-entry detection stays identical for every
harness (Claude nested groups, Cursor flat entries, Copilot ``bash`` entries).
"""

from __future__ import annotations

from typing import Any

HOOK_COMMAND_MARKERS: tuple[str, ...] = ("wagents-hook.py", "run-wagents-hook")

# Claude Code native event names (PascalCase). Lowercase/camelCase rows are Copilot/Cursor
# projections that must not persist inside ``.claude/settings.json``.
CLAUDE_NATIVE_HOOK_EVENTS: frozenset[str] = frozenset({
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PermissionRequest",
    "PostToolUse",
    "SubagentStart",
    "SubagentStop",
    "Stop",
})

# Copilot-only native event keys that were accidentally merged into Claude settings.
COPILOT_NATIVE_HOOK_EVENTS: frozenset[str] = frozenset({
    "sessionStart",
    "userPromptSubmitted",
    "preToolUse",
    "postToolUse",
    "sessionEnd",
})


def _entry_commands(entry: dict[str, Any]) -> list[str]:
    """Return command strings for an entry in either nested or flat shape.

    Nested (Claude/Codex/Gemini): ``{"matcher"?, "hooks": [{"command"|"bash"}]}``.
    Flat (Cursor/Copilot): ``{"command"|"bash"}`` directly on the entry.
    """
    hook_configs = entry.get("hooks") if isinstance(entry.get("hooks"), list) else [entry]
    return [
        str(config.get("command") or config.get("bash") or "")
        for config in hook_configs
        if isinstance(config, dict)
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
            if "--harness cursor" in command or "--harness github-copilot" in command:
                return True
        return False
    command = str(entry.get("command") or entry.get("bash") or "")
    return bool(command and not nested)


def strip_foreign_claude_hook_entries(hooks: dict[str, Any]) -> dict[str, Any]:
    """Drop Copilot/Cursor hook shapes that were merged into Claude settings by mistake."""
    if not isinstance(hooks, dict):
        return {}
    cleaned: dict[str, list[Any]] = {}
    for event, entries in hooks.items():
        if event in COPILOT_NATIVE_HOOK_EVENTS:
            continue
        if event not in CLAUDE_NATIVE_HOOK_EVENTS:
            continue
        if not isinstance(entries, list):
            continue
        kept = [entry for entry in entries if isinstance(entry, dict) and not _is_foreign_claude_hook_entry(entry)]
        if kept:
            cleaned[event] = kept
    return cleaned


def _flat_entry_commands(entry: dict[str, Any]) -> list[str]:
    command = entry.get("command")
    return [str(command)] if isinstance(command, str) and command else []


def _is_managed_cursor_flat_entry(entry: dict[str, Any], managed_commands: frozenset[str]) -> bool:
    if "hooks" in entry:
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
