"""Shared path helpers for harness-master discovery scripts (stdlib only)."""

from __future__ import annotations

from pathlib import Path


def harness_master_dir() -> Path:
    """Skill root: skills/harness-master/ (from scripts/discovery/ -> parent x3)."""
    return Path(__file__).resolve().parent.parent.parent


def discovery_dir() -> Path:
    """Location of discovery scripts: harness-master/scripts/discovery/."""
    return harness_master_dir() / "scripts" / "discovery"


def data_dir() -> Path:
    """Discovery data dir: harness-master/data/discovery/."""
    return harness_master_dir() / "data" / "discovery"


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
    # From discovery scripts: parents[0]=discovery, [1]=scripts, [2]=harness-master,
    # [3]=skills, [4]=repo root
    return Path(__file__).resolve().parents[4]


# Back-compat aliases for code that still references the pre-move discover-skills layout.
# After consolidation, "skill_dir" for discovery purposes is the harness-master root.
def skill_dir() -> Path:
    return harness_master_dir()
