"""Tests for wagents.skill_research helpers."""

from pathlib import Path

from wagents.skill_research import (
    build_batch_prompt,
    partition_skills_for_research,
    research_queries,
    validate_artifact,
    write_skill_research_artifact,
)
from wagents.skill_docs import SkillDocNode
from wagents.catalog import CatalogNode


def _doc_node(skill_id: str, source_type: str = "custom") -> SkillDocNode:
    source = source_type if source_type != "curated-external" else "curated-external"
    return SkillDocNode(
        node=CatalogNode(
            kind="skill",
            id=skill_id,
            title=skill_id,
            description=f"Desc {skill_id}",
            metadata={},
            body="# Body",
            source_path=f"skills/{skill_id}/SKILL.md",
            source=source,
        ),
        source_type=source_type,  # type: ignore[arg-type]
    )


def test_research_queries_loads_yaml():
    data = research_queries()
    assert "custom" in data
    assert "prompt" in data["custom"]


def test_partition_skills_for_research_batches(monkeypatch):
    nodes = [_doc_node(f"skill-{i}") for i in range(3)]

    monkeypatch.setattr("wagents.skill_research.collect_skill_doc_nodes", lambda **kwargs: nodes)
    batches = partition_skills_for_research(batch_size=2)
    assert batches == [nodes[:2], nodes[2:]]


def test_build_batch_prompt_includes_skill_ids(monkeypatch):
    batch = [_doc_node("alpha"), _doc_node("beta")]
    monkeypatch.setattr("wagents.skill_research.research_queries", lambda: {"custom": {"prompt": "Research {name}"}})
    prompt = build_batch_prompt(batch)
    assert "alpha" in prompt
    assert "beta" in prompt


def test_write_and_validate_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr("wagents.skill_research.RESEARCH_DIR", tmp_path)
    path = write_skill_research_artifact(
        "demo",
        source_type="custom",
        research_tier="quick",
        mean_confidence=0.9,
        body="## Summary\n\nDemo research body.",
    )
    assert path.exists()
    errors = validate_artifact(path)
    assert errors == []
