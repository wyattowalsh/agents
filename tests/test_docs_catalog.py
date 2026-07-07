"""Tests for catalog discovery facet indexes (RV-023)."""

from __future__ import annotations

from wagents.docs_catalog import (
    _catalog_skill_entries,
    _collect_platform_index,
    _collect_tag_index,
    _skills_catalog_index,
    write_catalog_tags_index,
)


def test_catalog_skill_entries_reads_all_skill_index() -> None:
    index = _skills_catalog_index()
    entries = _catalog_skill_entries(index)
    assert len(entries) >= 600


def test_platform_index_populated_from_target_agents() -> None:
    index = _skills_catalog_index()
    by_platform = _collect_platform_index(index)
    assert "claude-code" in by_platform
    assert len(by_platform["claude-code"]) >= 100


def test_tag_index_derives_synthetic_facets() -> None:
    index = _skills_catalog_index()
    by_tag = _collect_tag_index(index)
    assert any(tag.startswith("source:") for tag in by_tag)
    assert any(tag.startswith("trust:") for tag in by_tag)


def test_write_catalog_tags_index_emits_tag_query_links() -> None:
    captured: list[str] = []

    def writer(_path, _frontmatter, body):
        captured.extend(body)

    skills_index = {
        "allSkillIndex": [
            {
                "name": "demo-skill",
                "sourceKind": "curated-external",
                "sourceType": "curated-external",
                "status": "inspect-then-install",
                "trustTier": "curated-trust-gated",
                "targetAgents": ["claude-code"],
            }
        ]
    }

    write_catalog_tags_index(skills_index, writer=writer)
    body = "\n".join(captured)

    assert 'href="/skills/catalog/external/?tag=source%3Acurated-external"' in body
    assert "external, 0 custom" in body