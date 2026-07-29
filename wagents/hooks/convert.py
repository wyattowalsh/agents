"""Convert rendered hook documents between harness projection shapes.

The registry (``config/hook-registry.json``) is the single source of truth, and
``wagents.hooks.render`` projects it to each harness. This module performs the
inverse + cross projection: given an *already rendered* hook document for one
harness, normalize it to a list of :class:`HookSpec` and re-emit it in another
harness's shape. Unlike the registry renderers, the converters preserve the
existing command string verbatim (they never re-resolve a runner path), so a
``claude-code`` -> ``cursor`` -> ``claude-code`` round-trip keeps logical
events, matchers, and commands stable.

Two projection families:

* nested groups: ``codex``, ``claude-code``
  ``{event: [{matcher?, hooks: [{type, command, ...}]}]}``
* flat permission entries: ``cursor``
  ``{event: [{command, matcher?, timeout?, failClosed?}]}``

**Lossy cross-projection:** Cursor-only logical events from
``wagents.hooks.render.CURSOR_EVENT_MAP`` — including ``BeforeReadFile``,
``BeforeShellExecution``, ``BeforeMCPExecution``, ``AfterFileEdit``, and
``SubagentStart`` — are omitted when converting to ``claude-code``, ``codex``,
``codex`` or ``claude-code`` because those harnesses have no native equivalent
in their event maps. Use the registry + ``render_*`` helpers for
authoritative multi-harness projection instead of convert for those events.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from wagents.hooks.render import (
    CLAUDE_EVENT_MAP,
    CODEX_EVENT_MAP,
    CURSOR_EVENT_MAP,
    CURSOR_FAIL_CLOSED_EVENTS,
)

SUPPORTED_HARNESSES: frozenset[str] = frozenset({
    "codex",
    "claude-code",
    "cursor",
})

_EVENT_MAPS: dict[str, dict[str, str]] = {
    "codex": CODEX_EVENT_MAP,
    "claude-code": CLAUDE_EVENT_MAP,
    "cursor": CURSOR_EVENT_MAP,
}

# Harnesses whose entries nest a ``hooks`` command group.
_NESTED_HARNESSES = frozenset({"codex", "claude-code"})


@dataclass
class HookSpec:
    """Harness-neutral hook description with timeouts normalized to seconds."""

    logical_event: str
    command: str
    matcher: str | None = None
    timeout: int | None = None
    description: str | None = None
    fail_closed: bool | None = None


def _reverse_event_map(harness: str) -> dict[str, str]:
    return {native: logical for logical, native in _EVENT_MAPS[harness].items()}


def _entry_command(config: dict[str, Any]) -> str:
    return str(config.get("command") or config.get("bash") or "")


def normalize_from(doc: dict[str, Any], source: str) -> list[HookSpec]:
    """Parse a rendered hook document into harness-neutral :class:`HookSpec`s."""
    if source not in SUPPORTED_HARNESSES:
        raise ValueError(f"unsupported source harness {source!r}")
    reverse = _reverse_event_map(source)
    hooks = doc.get("hooks")
    if not isinstance(hooks, dict):
        return []
    specs: list[HookSpec] = []
    for native_event, entries in hooks.items():
        logical = reverse.get(str(native_event))
        if not logical or not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            specs.extend(_specs_from_entry(entry, logical, source))
    return specs


def _specs_from_entry(entry: dict[str, Any], logical: str, source: str) -> list[HookSpec]:
    matcher = entry.get("matcher")
    matcher_str = str(matcher) if matcher else None
    if source in _NESTED_HARNESSES:
        configs = entry.get("hooks")
        configs = configs if isinstance(configs, list) else []
        specs: list[HookSpec] = []
        for config in configs:
            if not isinstance(config, dict):
                continue
            command = _entry_command(config)
            if not command:
                continue
            timeout = config.get("timeout")
            seconds = int(timeout) if timeout else None
            specs.append(
                HookSpec(
                    logical_event=logical,
                    command=command,
                    matcher=matcher_str,
                    timeout=seconds,
                    description=config.get("description"),
                )
            )
        return specs
    # Cursor uses a flat command entry.
    command = _entry_command(entry)
    if not command:
        return []
    timeout = entry.get("timeout")
    fail_closed = entry.get("failClosed")
    return [
        HookSpec(
            logical_event=logical,
            command=command,
            matcher=matcher_str,
            timeout=int(timeout) if timeout else None,
            fail_closed=bool(fail_closed) if fail_closed is not None else None,
        )
    ]


def _emit_nested(specs: list[HookSpec], target: str) -> dict[str, Any]:
    event_map = _EVENT_MAPS[target]
    rendered: dict[str, list[dict[str, Any]]] = {}
    for spec in specs:
        native = event_map.get(spec.logical_event)
        if not native:
            continue
        config: dict[str, Any] = {"type": "command", "command": spec.command}
        if target == "codex":
            config["timeout"] = spec.timeout if spec.timeout else 5
            config["statusMessage"] = spec.description or spec.command
        elif spec.timeout:
            config["timeout"] = spec.timeout
        group: dict[str, Any] = {"hooks": [config]}
        if spec.matcher:
            group["matcher"] = spec.matcher
        rendered.setdefault(native, []).append(group)
    return {"hooks": rendered}


def _emit_cursor(specs: list[HookSpec]) -> dict[str, Any]:
    rendered: dict[str, list[dict[str, Any]]] = {}
    for spec in specs:
        native = CURSOR_EVENT_MAP.get(spec.logical_event)
        if not native:
            continue
        entry: dict[str, Any] = {"command": spec.command}
        if spec.matcher:
            entry["matcher"] = spec.matcher
        if spec.timeout:
            entry["timeout"] = spec.timeout
        if spec.fail_closed is not None and native in CURSOR_FAIL_CLOSED_EVENTS:
            entry["failClosed"] = spec.fail_closed
        rendered.setdefault(native, []).append(entry)
    return {"version": 1, "hooks": rendered}


def render_to(specs: list[HookSpec], target: str) -> dict[str, Any]:
    """Render harness-neutral specs into ``target``'s hook-document shape."""
    if target not in SUPPORTED_HARNESSES:
        raise ValueError(f"unsupported target harness {target!r}")
    if target == "cursor":
        return _emit_cursor(specs)
    return _emit_nested(specs, target)


def convert_hooks(doc: dict[str, Any], *, source: str, target: str) -> dict[str, Any]:
    """Convert a rendered hook document from ``source`` shape to ``target`` shape."""
    return render_to(normalize_from(doc, source), target)
