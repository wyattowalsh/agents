"""Compatibility bridge for path safety helpers used by legacy scripts."""

# ruff: noqa: E402, I001

from __future__ import annotations

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if SRC_DIR.is_dir() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from nerdbot.safety import (  # noqa: E402
    ensure_descendant,
    ensure_safe_target,
    fsync_parent_directory,
    is_windows_reparse_point,
    normalize_requested_root,
    open_text_no_follow,
    read_text_no_follow,
    reject_hardlinked_overwrite,
    reject_indirect_path_component as reject_symlinked_existing_components,
    write_bytes_atomic_no_follow,
)

__all__ = [
    "ensure_descendant",
    "ensure_safe_target",
    "fsync_parent_directory",
    "is_windows_reparse_point",
    "normalize_requested_root",
    "open_text_no_follow",
    "read_text_no_follow",
    "reject_hardlinked_overwrite",
    "reject_symlinked_existing_components",
    "write_bytes_atomic_no_follow",
]
