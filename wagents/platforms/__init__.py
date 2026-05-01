"""Platform adapter registry for unified agent asset generation.

Usage:
    from wagents.platforms import get_adapter, list_adapters
    from wagents.platforms.base import PlatformAdapter

    adapter = get_adapter("claude-code")
    adapter.sync_home(ctx, registry, policy, fallbacks, hook_registry)
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wagents.platforms.base import PlatformAdapter

# Platform identifier → adapter module name
_BUILT_IN_ADAPTERS: dict[str, str] = {
    "claude-code": "wagents.platforms.claude",
    "codex": "wagents.platforms.codex",
    "copilot": "wagents.platforms.copilot",
    "cursor": "wagents.platforms.cursor",
    "gemini-cli": "wagents.platforms.gemini",
    "github-copilot": "wagents.platforms.copilot",
    "opencode": "wagents.platforms.opencode",
    "vscode": "wagents.platforms.vscode",
}

_ADAPTERS: dict[str, PlatformAdapter] = {}


def _load_adapter(name: str) -> PlatformAdapter:
    module_name = _BUILT_IN_ADAPTERS[name]
    module = importlib.import_module(module_name)
    # Each adapter module exports an `Adapter` class inheriting from PlatformAdapter
    adapter_cls = module.Adapter
    return adapter_cls()


def get_adapter(name: str) -> PlatformAdapter:
    """Return a cached adapter instance by platform identifier."""
    normalized = name.lower().replace(" ", "-").replace("_", "-")
    if normalized not in _ADAPTERS:
        if normalized not in _BUILT_IN_ADAPTERS:
            raise KeyError(f"Unknown platform adapter: {name!r}")
        _ADAPTERS[normalized] = _load_adapter(normalized)
    return _ADAPTERS[normalized]


def list_adapters() -> list[str]:
    """List all registered platform identifiers."""
    return sorted(_BUILT_IN_ADAPTERS.keys())


def available_adapters() -> list[str]:
    """List adapters whose target platform appears to be installed."""
    return sorted(name for name in list_adapters() if get_adapter(name).is_available())
