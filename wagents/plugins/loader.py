"""Discover and load wagents command plugins via entry points."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import typer

COMMANDS_GROUP = "wagents.commands"


@dataclass(frozen=True)
class PluginLoadResult:
    name: str
    status: str
    summary: str


def _iter_command_entry_points():
    try:
        return entry_points(group=COMMANDS_GROUP)
    except TypeError:
        discovered = entry_points()
        if hasattr(discovered, "select"):
            return discovered.select(group=COMMANDS_GROUP)
        return discovered.get(COMMANDS_GROUP, [])


def _resolve_register(entry: Any) -> Any:
    target = entry.load()
    if hasattr(target, "register_commands"):
        return target.register_commands
    if callable(target):
        return target
    module_name, _, attr = str(entry.value).partition(":")
    module = importlib.import_module(module_name)
    return getattr(module, attr or "register_commands")


def load_command_plugins(app: typer.Typer) -> list[PluginLoadResult]:
    """Load all wagents.commands entry points onto *app*."""
    results: list[PluginLoadResult] = []
    for entry in sorted(_iter_command_entry_points(), key=lambda item: item.name):
        try:
            register = _resolve_register(entry)
            register(app)
            results.append(PluginLoadResult(entry.name, "ok", "Loaded"))
        except Exception as exc:
            results.append(PluginLoadResult(entry.name, "warn", f"Failed to load: {exc}"))
    return results
