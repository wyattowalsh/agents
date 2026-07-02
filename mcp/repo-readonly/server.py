"""MCP server: repo-readonly.

Generic read-only file access to an explicit allowlist of repo surfaces
(`wagents.mcp_shared.read_only_paths.DEFAULT_ALLOWED_PREFIXES`): skills/,
agents/, mcp/, selected docs/ trees, config/, openspec/, planning/manifests/,
kb/wiki/, README.md, AGENTS.md. No tool in this server writes, deletes, or
executes anything.
"""

from __future__ import annotations

from fastmcp import FastMCP

from wagents import ROOT
from wagents.mcp_shared.read_only_paths import (
    DEFAULT_ALLOWED_PREFIXES,
    PathNotAllowedError,
    is_read_only_path_allowed,
    read_text_within_allowlist,
)

mcp = FastMCP("Repo Read-Only")

_READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


@mcp.tool(annotations=_READ_ONLY)
def list_allowed_prefixes() -> list[str]:
    """Return the repo-root-relative path prefixes this server is allowed to read.

    Call this first to know which trees are in scope before calling
    `read_file` or `list_directory`.
    """
    return list(DEFAULT_ALLOWED_PREFIXES)


@mcp.tool(annotations=_READ_ONLY)
def path_allowed(relative_path: str) -> bool:
    """Return whether *relative_path* is inside the read-only allowlist.

    *relative_path* must be repo-root-relative (no leading "/", no ".."
    segments). Use this to pre-check a path before calling `read_file` when
    you want to avoid handling the raised error.
    """
    return is_read_only_path_allowed(relative_path)


@mcp.tool(annotations=_READ_ONLY)
def read_file(relative_path: str, max_bytes: int = 500_000) -> str:
    """Read a UTF-8 text file within the read-only allowlist.

    *relative_path* is repo-root-relative, e.g. "skills/review/SKILL.md" or
    "config/mcp-registry.json". Raises `ValueError` if the path is outside
    the allowlist, `FileNotFoundError` if it does not exist, or if it is a
    directory (use `list_directory` instead), and truncation errors if the
    file exceeds *max_bytes*.
    """
    try:
        return read_text_within_allowlist(relative_path, max_bytes=max_bytes)
    except PathNotAllowedError as exc:
        raise ValueError(str(exc)) from exc


@mcp.tool(annotations=_READ_ONLY)
def list_directory(relative_path: str) -> list[dict[str, str]]:
    """List immediate entries (name, kind) of an allowlisted repo directory.

    *relative_path* is repo-root-relative, e.g. "skills" or "mcp/mcphub".
    Raises `ValueError` if the path is outside the allowlist or is not a
    directory.
    """
    from wagents.mcp_shared.read_only_paths import resolve_read_only_path

    try:
        resolved = resolve_read_only_path(relative_path)
    except PathNotAllowedError as exc:
        raise ValueError(str(exc)) from exc
    if not resolved.is_dir():
        raise ValueError(f"Not a directory: {relative_path!r}")
    entries = []
    for child in sorted(resolved.iterdir(), key=lambda p: p.name):
        entries.append({
            "name": child.name,
            "kind": "directory" if child.is_dir() else "file",
            "relative_path": str(child.relative_to(ROOT)),
        })
    return entries


if __name__ == "__main__":
    mcp.run()
