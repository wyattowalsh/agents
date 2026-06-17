"""Tests for wagents.page_density summary-mode helpers."""

from wagents.catalog import CatalogNode
from wagents.page_density import (
    agent_prompt_disclosure_mode,
    resolve_density,
    should_render_body_sections,
    should_render_what_it_does,
    truncate_research_prose,
)


def _node(**meta) -> CatalogNode:
    return CatalogNode(
        kind="skill",
        id="demo",
        title="Demo",
        description="Short description for tests.",
        metadata=meta or {"name": "demo", "description": "Short description for tests."},
        body="",
        source_path="skills/demo/SKILL.md",
        source="custom",
    )


def test_resolve_density_defaults_to_standard() -> None:
    assert resolve_density(_node()) == "standard"


def test_resolve_density_honors_frontmatter() -> None:
    assert resolve_density(_node(density="standard")) == "standard"


def test_summary_skips_body_sections_when_source_disclosed() -> None:
    assert should_render_body_sections("summary", has_full_source_disclosure=True) is False


def test_summary_skips_redundant_what_it_does() -> None:
    assert (
        should_render_what_it_does(
            "summary",
            description="Same text here.",
            what_it_does="Same text here.",
        )
        is False
    )


def test_agent_small_body_uses_inline_only() -> None:
    body = "\n".join(["line"] * 10)
    assert agent_prompt_disclosure_mode(body, "summary") == "inline"


def test_agent_large_body_uses_details_only() -> None:
    body = "\n".join(["line"] * 80)
    assert agent_prompt_disclosure_mode(body, "summary") == "details"


def test_truncate_research_prose() -> None:
    text = " ".join(["word"] * 200)
    capped, truncated = truncate_research_prose(text, max_words=120)
    assert truncated is True
    assert len(capped.split()) == 120
