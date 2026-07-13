"""Tests for catalog discovery facet indexes (RV-023 / RV-S-005)."""

from __future__ import annotations

from wagents.docs_catalog import (
    _catalog_skill_entries,
    _collect_platform_index,
    _collect_tag_index,
    _skills_catalog_index,
    write_catalog_platforms_index,
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
    assert 'title="Custom skills"' not in body
    assert "— custom skills" not in body


def test_write_catalog_tags_index_emits_single_custom_companion() -> None:
    captured: list[str] = []

    def writer(_path, _frontmatter, body):
        captured.extend(body)

    skills_index = {
        "allSkillIndex": [
            {
                "name": "custom-one",
                "sourceKind": "custom",
                "sourceType": "custom",
                "status": "repo-owned",
                "trustTier": "repo-owned",
                "targetAgents": ["claude-code"],
                "tags": ["demo-tag"],
            },
            {
                "name": "ext-one",
                "sourceKind": "curated-external",
                "sourceType": "curated-external",
                "status": "inspect-then-install",
                "trustTier": "curated-trust-gated",
                "targetAgents": ["claude-code"],
                "tags": ["demo-tag"],
            },
        ]
    }

    write_catalog_tags_index(skills_index, writer=writer)
    body = "\n".join(captured)
    assert body.count('title="Custom skills"') == 1
    assert 'href="/skills/catalog/custom/"' in body
    assert "— custom skills" not in body


def test_write_catalog_platforms_index_emits_single_custom_companion() -> None:
    captured: list[str] = []

    def writer(_path, _frontmatter, body):
        captured.extend(body)

    skills_index = {
        "allSkillIndex": [
            {
                "name": "custom-one",
                "sourceKind": "custom",
                "sourceType": "custom",
                "targetAgents": ["claude-code"],
            },
            {
                "name": "ext-one",
                "sourceKind": "curated-external",
                "sourceType": "curated-external",
                "targetAgents": ["claude-code"],
            },
        ]
    }

    write_catalog_platforms_index(skills_index, writer=writer)
    body = "\n".join(captured)
    assert 'href="/skills/catalog/external/?platform=claude-code"' in body
    assert body.count('title="Custom skills"') == 1
    assert "— custom skills" not in body


def test_write_catalog_tags_multi_tag_emits_exactly_one_companion() -> None:
    """RV-S-005 L21c: multi-tag custom facets must not duplicate hub companions."""
    captured: list[str] = []

    def writer(_path, _frontmatter, body):
        captured.extend(body)

    skills_index = {
        "allSkillIndex": [
            {
                "name": "c1",
                "sourceKind": "custom",
                "sourceType": "custom",
                "tags": ["alpha", "beta"],
                "targetAgents": ["claude-code"],
            },
            {
                "name": "c2",
                "sourceKind": "custom",
                "sourceType": "custom",
                "tags": ["beta"],
                "targetAgents": ["codex"],
            },
            {
                "name": "e1",
                "sourceKind": "curated-external",
                "sourceType": "curated-external",
                "tags": ["alpha"],
                "targetAgents": ["claude-code"],
            },
        ]
    }

    write_catalog_tags_index(skills_index, writer=writer)
    body = "\n".join(captured)
    assert body.count('title="Custom skills"') == 1


def test_write_catalog_platforms_multi_platform_emits_exactly_one_companion() -> None:
    captured: list[str] = []

    def writer(_path, _frontmatter, body):
        captured.extend(body)

    skills_index = {
        "allSkillIndex": [
            {
                "name": "c1",
                "sourceKind": "custom",
                "sourceType": "custom",
                "targetAgents": ["claude-code", "codex"],
            },
            {
                "name": "e1",
                "sourceKind": "curated-external",
                "sourceType": "curated-external",
                "targetAgents": ["claude-code", "opencode"],
            },
        ]
    }

    write_catalog_platforms_index(skills_index, writer=writer)
    body = "\n".join(captured)
    assert body.count('title="Custom skills"') == 1


def test_platforms_empty_map_still_emits_custom_companion() -> None:
    """RV-S-R-006: customs with no targetAgents still get a hub companion card."""
    captured: list[str] = []

    def writer(_path, _frontmatter, body):
        captured.extend(body)

    skills_index = {
        "allSkillIndex": [
            {
                "name": "c1",
                "sourceKind": "custom",
                "sourceType": "custom",
                "targetAgents": [],
            },
        ]
    }

    write_catalog_platforms_index(skills_index, writer=writer)
    body = "\n".join(captured)
    assert body.count('title="Custom skills"') == 1
