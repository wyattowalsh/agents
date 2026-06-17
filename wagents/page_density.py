"""Page density modes for generated docs catalog pages."""

from __future__ import annotations

from typing import Literal

from wagents.catalog import CatalogNode

PageDensity = Literal["summary", "standard"]
DEFAULT_SKILL_DENSITY: PageDensity = "standard"
DEFAULT_AGENT_DENSITY: PageDensity = "standard"
DEFAULT_MCP_DENSITY: PageDensity = "standard"

AGENT_INLINE_PROMPT_MAX_LINES = 48
MCP_INLINE_SOURCE_MAX_LINES = 80
RESEARCH_SECTION_MAX_WORDS = 120


def resolve_density(node: CatalogNode, *, default: PageDensity = "standard") -> PageDensity:
    """Resolve density from node metadata frontmatter."""
    raw = node.metadata.get("docs-density") or node.metadata.get("density")
    if raw in ("summary", "standard"):
        return raw
    return default


def should_emit_word_count_badge(density: PageDensity) -> bool:
    return density == "standard"


def should_emit_works_with_prose(density: PageDensity) -> bool:
    return density == "standard"


def should_emit_source_aside(density: PageDensity) -> bool:
    return density == "standard"


def should_emit_resources_grid(density: PageDensity) -> bool:
    return density == "standard"


def should_render_body_sections(density: PageDensity, *, has_full_source_disclosure: bool) -> bool:
    """Inline extracted SKILL sections duplicate collapsed source in summary mode."""
    if density == "standard":
        return True
    return not has_full_source_disclosure


def should_render_what_it_does(
    density: PageDensity,
    *,
    description: str,
    what_it_does: str,
) -> bool:
    if not what_it_does.strip():
        return False
    if density == "standard":
        return True
    desc_norm = " ".join(description.split()).strip().lower()
    witd_norm = " ".join(what_it_does.split()).strip().lower()
    return witd_norm != desc_norm and len(what_it_does.split()) > 20


def should_emit_skill_source_disclosure(node: CatalogNode, *, is_stub: bool) -> bool:
    return not is_stub


def agent_prompt_disclosure_mode(body: str, density: PageDensity) -> Literal["inline", "details", "both"]:
    """Avoid duplicating agent prompt inline and in details."""
    if density == "standard":
        return "both"
    line_count = len(body.splitlines()) if body else 0
    if line_count <= AGENT_INLINE_PROMPT_MAX_LINES:
        return "inline"
    return "details"


def mcp_source_disclosure_mode(body: str, density: PageDensity) -> Literal["inline", "details"]:
    if density == "standard":
        return "inline"
    line_count = len(body.splitlines()) if body else 0
    if line_count <= MCP_INLINE_SOURCE_MAX_LINES:
        return "inline"
    return "details"


def collapse_metadata_tabs(density: PageDensity) -> bool:
    return density == "summary"


def truncate_research_prose(text: str, *, max_words: int = RESEARCH_SECTION_MAX_WORDS) -> tuple[str, bool]:
    """Return truncated prose and whether truncation occurred."""
    words = text.split()
    if len(words) <= max_words:
        return text, False
    truncated = " ".join(words[:max_words]).rstrip()
    if truncated and truncated[-1] not in ".!?":
        truncated += "…"
    return truncated, True
