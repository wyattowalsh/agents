"""Shared path helpers for discover-skills scripts (stdlib only)."""

from __future__ import annotations

from pathlib import Path


def skill_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    return skill_dir() / "data"


def find_repo_root(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for path in [current, *current.parents]:
        if (path / "skills").is_dir() and (path / "AGENTS.md").exists():
            return path
    return None


def default_repo_root() -> Path:
    found = find_repo_root()
    if found is not None:
        return found
    return Path(__file__).resolve().parents[3]