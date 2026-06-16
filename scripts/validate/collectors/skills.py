"""Collect skill frontmatter validation errors."""

from __future__ import annotations

from pathlib import Path

from _toolkit import ensure_validate_importable

ensure_validate_importable()

from asset_toolkit.validate_skill import validate_skills_root


def collect_skill_errors(repo_root: Path) -> list[dict[str, str]]:
    """Return skill validation errors for the repository."""
    return validate_skills_root(repo_root / "skills")