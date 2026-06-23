"""Collect skill frontmatter validation errors."""

from __future__ import annotations

from _toolkit import ensure_validate_importable

ensure_validate_importable()

from typing import TYPE_CHECKING

from asset_toolkit.validate_skill import validate_skills_root

if TYPE_CHECKING:
    from pathlib import Path


def collect_skill_errors(repo_root: Path) -> list[dict[str, str]]:
    """Return skill validation errors for the repository."""
    return validate_skills_root(repo_root / "skills")
