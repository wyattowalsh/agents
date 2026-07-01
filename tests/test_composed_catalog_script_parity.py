"""Composed catalog pages use portable script paths."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.skill_portability_ids import COMPOSED_CATALOG_PAGES
from wagents.parsing import FenceTracker

ROOT = Path(__file__).resolve().parent.parent
BAD_RE = re.compile(r"(?<![A-Za-z0-9_./-])(?:\./)?skills/[a-z0-9][a-z0-9-]*/scripts/")


def _bad_script_refs_outside_fences(text: str) -> list[tuple[int, str]]:
    fence = FenceTracker()
    issues: list[tuple[int, str]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        if fence.update(line) or fence.inside_fence:
            continue
        if BAD_RE.search(line):
            issues.append((line_no, line.strip()))
    return issues


def test_bad_script_refs_outside_fences_reports_prose() -> None:
    text = "Run uv run python skills/research/scripts/check.py"

    assert _bad_script_refs_outside_fences(text) == [(1, text)]


def test_bad_script_refs_outside_fences_ignores_source_disclosure() -> None:
    text = "\n".join([
        '````yaml title="skills/research/SKILL.md"',
        "uv run python skills/research/scripts/check.py",
        "````",
    ])

    assert _bad_script_refs_outside_fences(text) == []


def test_bad_script_refs_outside_fences_keeps_four_tick_fence_open_across_inner_triples() -> None:
    text = "\n".join([
        '````yaml title="skills/research/SKILL.md"',
        "```bash",
        "uv run python skills/research/scripts/check.py",
        "```",
        "uv run python skills/research/scripts/package.py",
        "````",
    ])

    assert _bad_script_refs_outside_fences(text) == []


@pytest.mark.parametrize("rel_path", COMPOSED_CATALOG_PAGES)
def test_catalog_page_portable_script_paths(rel_path: str) -> None:
    path = ROOT / rel_path
    if not path.is_file():
        pytest.skip(f"missing catalog page {rel_path}")
    text = path.read_text(encoding="utf-8")
    issues = _bad_script_refs_outside_fences(text)
    if issues:
        line_no, line = issues[0]
        pytest.fail(f"{rel_path}:{line_no}: {line}")
