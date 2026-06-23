"""Shared batch runner for compose upgrade commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wagents.docs_mdx_safety import has_legacy_quick_start, parse_composed_by

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


@dataclass(frozen=True)
class UpgradeResult:
    written: int
    skipped: int
    paths: list[str]


def should_skip_upgrade(
    page_text: str,
    *,
    target_wave: str,
    force: bool,
    pending_markers: tuple[str, ...] = ("compose-batch-apply",),
) -> bool:
    if force:
        return False
    composed_by = parse_composed_by(page_text)
    if composed_by in pending_markers:
        return False
    if has_legacy_quick_start(page_text):
        return False
    if composed_by == target_wave:
        return True
    return bool(composed_by and composed_by.startswith("compose-"))


def run_upgrade_batch(
    *,
    target_ids: list[str],
    resolve_wave: Callable[[str], str],
    load_page: Callable[[str], Path | None],
    transform: Callable[[str, str], str | None],
    force: bool = False,
    dry_run: bool = False,
    pending_markers: tuple[str, ...] = ("compose-batch-apply",),
) -> UpgradeResult:
    written = 0
    skipped = 0
    paths: list[str] = []
    for asset_id in target_ids:
        page_path = load_page(asset_id)
        if page_path is None or not page_path.exists():
            skipped += 1
            continue
        existing = page_path.read_text(encoding="utf-8")
        wave_id = resolve_wave(asset_id)
        if should_skip_upgrade(
            existing,
            target_wave=wave_id,
            force=force,
            pending_markers=pending_markers,
        ):
            skipped += 1
            continue
        content = transform(asset_id, wave_id)
        if content is None:
            skipped += 1
            continue
        paths.append(str(page_path))
        if not dry_run:
            page_path.write_text(content, encoding="utf-8")
        written += 1
    return UpgradeResult(written=written, skipped=skipped, paths=paths)
