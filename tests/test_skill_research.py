"""Tests for wagents.skill_research helpers."""

from wagents.catalog import CatalogNode
from wagents.skill_docs import SkillDocNode
from wagents.skill_research import (
    build_batch_prompt,
    build_repo_grounded_research_body,
    partition_skills_for_research,
    research_coverage,
    research_queries,
    seed_phase_a_research,
    validate_artifact,
    write_skill_research_artifact,
)


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


def test_build_repo_grounded_research_body_detects_scripts_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("wagents.skill_research.ROOT", tmp_path)
    skill_dir = tmp_path / "skills" / "alpha"
    (skill_dir / "scripts").mkdir(parents=True)
    doc = _doc_node("alpha")
    body = build_repo_grounded_research_body(doc)
    assert "portable skill scripts" in body


def test_build_repo_grounded_research_body_uses_description_and_not_for():
    doc = _doc_node("honest-review")
    doc.node.description = (
        "Review code with confidence-scored evidence. NOT for feature work (simplify)."
    )
    doc.node.body = "# Honest Review\n\nResearch-driven code review.\n"
    body = build_repo_grounded_research_body(doc)
    assert "Quick Answer" in body
    assert "`simplify`" in body
    assert "Research-driven code review." in body


def test_seed_phase_a_research_writes_custom_skills(tmp_path, monkeypatch):
    monkeypatch.setattr("wagents.skill_research.RESEARCH_DIR", tmp_path)
    monkeypatch.setattr("wagents.skill_research.MANIFEST_PATH", tmp_path / "manifest.mjs")
    nodes = [_doc_node("alpha"), _doc_node("beta", source_type="installed")]

    written = seed_phase_a_research(nodes)

    assert len(written) == 1
    assert (tmp_path / "alpha.md").exists()
    assert not (tmp_path / "beta.md").exists()


def test_research_coverage_counts_present_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr("wagents.skill_research.RESEARCH_DIR", tmp_path)
    write_skill_research_artifact(
        "alpha",
        source_type="custom",
        research_tier="quick",
        mean_confidence=0.8,
        body="## Summary\n\nAlpha.",
    )
    nodes = [_doc_node("alpha"), _doc_node("beta")]
    present, total = research_coverage(nodes, source_type="custom")
    assert present == 1
    assert total == 2


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
