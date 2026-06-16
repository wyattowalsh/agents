"""Bootstrap imports from the portable skill-creator asset_toolkit."""

from __future__ import annotations

import sys
from pathlib import Path


def toolkit_scripts_path() -> Path:
    """Return the skill-creator scripts directory containing asset_toolkit."""
    return Path(__file__).resolve().parents[2] / "skills" / "skill-creator" / "scripts"


def ensure_toolkit_importable() -> None:
    """Add skill-creator/scripts to sys.path for asset_toolkit imports."""
    root = str(toolkit_scripts_path())
    if root not in sys.path:
        sys.path.insert(0, root)


def ensure_validate_importable() -> None:
    """Add scripts/validate and asset_toolkit to sys.path for collector imports."""
    validate_dir = str(Path(__file__).resolve().parent)
    if validate_dir not in sys.path:
        sys.path.insert(0, validate_dir)
    ensure_toolkit_importable()


def repo_root_from_validate() -> Path:
    """Return the repository root (parent of scripts/)."""
    return Path(__file__).resolve().parents[2]