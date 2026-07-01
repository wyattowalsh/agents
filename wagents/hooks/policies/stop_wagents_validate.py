"""Select repo asset paths that warrant a ``wagents validate`` pass on Stop.

This is the pure selection half of the ``stop-wagents-validate`` policy: given a
set of touched paths, return the subset that are validatable repo assets (skills,
agents, MCP servers, hook/config registries). The dispatcher runs validate only
when this returns a non-empty list, keeping the Stop gate cheap when no assets
changed.
"""

from __future__ import annotations

from pathlib import PurePosixPath

_ASSET_PREFIXES = ("skills/", "agents/", "mcp/")
_ASSET_FILES = {
    "config/hook-registry.json",
    "config/mcp-registry.json",
}


def _normalize(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def validate_asset_paths(paths: list[str]) -> list[str]:
    """Return the sorted, de-duplicated repo-asset paths from ``paths``."""
    selected: set[str] = set()
    for raw in paths:
        if not raw:
            continue
        norm = _normalize(raw)
        if norm in _ASSET_FILES:
            selected.add(norm)
            continue
        if any(norm.startswith(prefix) for prefix in _ASSET_PREFIXES):
            name = PurePosixPath(norm).name
            if name.endswith((".md", ".json", ".py", ".toml", ".yaml", ".yml")):
                selected.add(norm)
    return sorted(selected)
