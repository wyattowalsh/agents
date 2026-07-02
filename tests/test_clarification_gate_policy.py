"""Parity tests for Clarification Gate depth routing policy."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GLOBAL_MD = REPO_ROOT / "instructions" / "global.md"

DEPTH_MARKERS = (
    "### Depth routing",
    "user-pivotal",
    "/grill-me",
    "codebase-resolvable",
    "independent-choice",
    "subtask-pivotal",
    "micro-reversible",
    "Scoped grill contract",
    "on re-entry",
)

MIRROR_PATHS = (
    REPO_ROOT / ".claude" / "rules" / "global.md",
    REPO_ROOT / ".cursor" / "rules" / "global.mdc",
    REPO_ROOT / ".github" / "instructions" / "global.instructions.md",
)


@pytest.mark.parametrize("marker", DEPTH_MARKERS)
def test_global_md_contains_depth_routing_markers(marker: str) -> None:
    text = GLOBAL_MD.read_text(encoding="utf-8")
    assert marker in text


def test_global_md_embeds_grill_me_protocol() -> None:
    text = GLOBAL_MD.read_text(encoding="utf-8")
    assert "Ask one at a time" in text
    assert "mattpocock/skills" in text


@pytest.mark.parametrize("path", MIRROR_PATHS)
def test_instruction_mirrors_include_depth_routing(path: Path) -> None:
    if not path.exists():
        pytest.skip(f"mirror not materialized: {path}")
    text = path.read_text(encoding="utf-8")
    assert "### Depth routing" in text
    assert "/grill-me" in text