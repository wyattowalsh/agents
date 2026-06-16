"""Collect hook validation errors."""

from __future__ import annotations

from pathlib import Path

from _toolkit import ensure_validate_importable

ensure_validate_importable()

from asset_toolkit.validate_hooks import validate_hooks


def collect_hook_errors(repo_root: Path) -> list[dict[str, str]]:
    """Return hook validation errors for the repository."""
    return validate_hooks(repo_root)