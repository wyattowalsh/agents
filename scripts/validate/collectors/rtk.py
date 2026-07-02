"""Collect RTK policy violations in shared instruction surfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from wagents.rtk import collect_shared_rtk_include_violations


def collect_rtk_instruction_errors(repo_root: Path) -> list[dict[str, str]]:
    return collect_shared_rtk_include_violations(repo_root)
