"""Repo-local MCP directory policy helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

LOCAL_MCP_DIR_NAMES = frozenset({"archives", "cache", "notes", "secrets", "servers"})


def is_git_ignored(path: Path, repo_root: Path) -> bool:
    """Return whether path is ignored by this repo's git rules."""
    try:
        rel_path = path.relative_to(repo_root)
    except ValueError:
        return False
    candidates = [str(rel_path)]
    if path.is_dir():
        candidates.append(str(rel_path / "__wagents_check__"))
    for candidate in candidates:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_root), "check-ignore", "-q", candidate],
                capture_output=True,
                check=False,
            )
        except OSError:
            return False
        if result.returncode == 0:
            return True
    return False


def is_local_mcp_dir(path: Path, repo_root: Path) -> bool:
    """Return whether an MCP subdirectory is reserved for local machine assets."""
    return path.name in LOCAL_MCP_DIR_NAMES or is_git_ignored(path, repo_root)