"""Tests for wagents.skill_research helpers."""

from typing import Literal

from wagents.catalog import CatalogNode
from wagents.external_skills import ExternalSkillEntry
from wagents.skill_docs import SkillDocNode
from wagents.skill_research import (
    CURATED_RESEARCH_SECTIONS,
    build_batch_prompt,
    build_curated_config_research_body,
    build_repo_grounded_research_body,
    partition_skills_by_source,
    partition_skills_for_research,
    research_coverage,
    research_queries,
    seed_curated_config_research,
    seed_phase_a_research,
    validate_artifact,
    write_skill_research_artifact,
)


def _doc_node(
    skill_id: str,
    source_type: Literal["custom", "installed", "curated-external"] = "custom",
    curated_status: str = "",
) -> SkillDocNode:
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
        source_type=source_type,
        curated_status=curated_status,
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
    doc = _doc_node("review")
    doc.node.description = "Review code with confidence-scored evidence. NOT for feature work (build)."
    doc.node.body = "# Review\n\nResearch-driven code review.\n"
    body = build_repo_grounded_research_body(doc)
    assert "Quick Answer" in body
    assert "`build`" in body
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


def _curated_entry(
    name: str,
    status: str = "install-now-after-trust-gate",
    *,
    trust_tier: str = "low",
    notes: str = "",
    risk_notes: str = "",
) -> ExternalSkillEntry:
    return ExternalSkillEntry(
        name=name,
        source="example/source",
        install_source="example/source",
        status=status,
        trust_tier=trust_tier,
        provenance_status="verified-install-command",
        install_command=f"npx skills add example/source --skill {name} -a claude-code opencode",
        target_agents=("claude-code", "opencode"),
        source_url="https://github.com/example/source",
        notes=notes or f"Purpose of curated skill {name}.",
        risk_notes=risk_notes or "Review hooks and dedupe.",
        promotion_policy="Install only after trust gate.",
        provenance_evidence="Curated in config/external-skills.md.",
    )


def test_curated_research_sections_constant():
    assert CURATED_RESEARCH_SECTIONS[0] == "Purpose"
    assert "Harness Coverage" in CURATED_RESEARCH_SECTIONS
    assert "Comparable Alternatives" in CURATED_RESEARCH_SECTIONS
    assert len(CURATED_RESEARCH_SECTIONS) == 6


def test_build_curated_config_research_body_structured_sections():
    entry = _curated_entry("demo-curated-skill", notes="Generate trust-gated workflow guidance.")
    body = build_curated_config_research_body(entry)
    for section in CURATED_RESEARCH_SECTIONS:
        assert f"## {section}" in body, f"missing section {section}"
    assert "demo-curated-skill" in body or "Purpose" in body
    assert "Target agents:" in body
    assert "trust_tier=low" in body
    assert "https://github.com/example/source" in body
    assert "Sourced from curated config/external-skills.md" in body


def _curated_doc_node(
    entry: ExternalSkillEntry,
) -> SkillDocNode:
    return SkillDocNode(
        node=CatalogNode(
            kind="skill",
            id=entry.name,
            title=entry.name,
            description=entry.notes,
            metadata={"_skills_install_source": entry.install_source},
            body="",
            source_path=entry.source_path,
            source="curated-external",
        ),
        source_type="curated-external",
        curated_status=entry.status,
    )


def test_seed_curated_config_research_writes_and_manifest(tmp_path, monkeypatch):
    entries = [
        _curated_entry("plannotator-review"),
        _curated_entry("inspect-me", status="inspect-then-install"),
    ]
    doc_nodes = [_curated_doc_node(entry) for entry in entries]
    monkeypatch.setattr("wagents.skill_research.read_external_skill_entries", lambda path=None: entries)
    monkeypatch.setattr("wagents.skill_research.collect_skill_doc_nodes", lambda **kwargs: doc_nodes)
    monkeypatch.setattr("wagents.skill_research.RESEARCH_DIR", tmp_path)
    monkeypatch.setattr("wagents.skill_research.MANIFEST_PATH", tmp_path / "manifest.mjs")
    written = seed_curated_config_research()
    assert len(written) == 2
    p1 = tmp_path / "plannotator-review.md"
    assert p1.exists()
    text = p1.read_text(encoding="utf-8")
    assert "source_type: curated-external" in text
    assert "## Purpose" in text
    assert "## Harness Coverage" in text
    # only the filtered one
    written2 = seed_curated_config_research(curated_status="install-now-after-trust-gate")
    assert len(written2) == 0  # already exist, no overwrite
    written3 = seed_curated_config_research(curated_status="install-now-after-trust-gate", overwrite=True)
    assert len(written3) == 1


def test_seed_curated_config_research_uses_catalog_install_source_for_duplicates(tmp_path, monkeypatch):
    entries = [
        ExternalSkillEntry(
            name="vitest",
            source="antfu/skills",
            install_source="antfu/skills",
            status="install-now-after-trust-gate",
            trust_tier="low",
            provenance_status="verified-install-command",
            install_command="npx skills add antfu/skills --skill vitest -y -g",
            target_agents=("claude-code",),
            source_url="https://github.com/antfu/skills",
            notes="antfu vitest",
        ),
        ExternalSkillEntry(
            name="vitest",
            source="PaulRBerg/agent-skills",
            install_source="PaulRBerg/agent-skills@abc",
            status="install-now-after-trust-gate",
            trust_tier="low",
            provenance_status="verified-install-command",
            install_command="npx skills add PaulRBerg/agent-skills@abc --skill vitest -y -g",
            target_agents=("claude-code",),
            source_url="https://github.com/PaulRBerg/agent-skills",
            notes="paul vitest",
        ),
    ]
    doc_nodes = [_curated_doc_node(entries[0])]
    monkeypatch.setattr("wagents.skill_research.read_external_skill_entries", lambda path=None: entries)
    monkeypatch.setattr("wagents.skill_research.collect_skill_doc_nodes", lambda **kwargs: doc_nodes)
    monkeypatch.setattr("wagents.skill_research.RESEARCH_DIR", tmp_path)
    monkeypatch.setattr("wagents.skill_research.MANIFEST_PATH", tmp_path / "manifest.mjs")
    written = seed_curated_config_research(overwrite=True)
    assert len(written) == 1
    body = (tmp_path / "vitest.md").read_text(encoding="utf-8")
    assert "antfu vitest" in body
    assert "paul vitest" not in body


def test_seed_curated_config_research_skips_when_no_overwrite(tmp_path, monkeypatch):
    entry = _curated_entry("existing-one")
    monkeypatch.setattr("wagents.skill_research.read_external_skill_entries", lambda path=None: [entry])
    monkeypatch.setattr(
        "wagents.skill_research.collect_skill_doc_nodes",
        lambda **kwargs: [_curated_doc_node(entry)],
    )
    monkeypatch.setattr("wagents.skill_research.RESEARCH_DIR", tmp_path)
    monkeypatch.setattr("wagents.skill_research.MANIFEST_PATH", tmp_path / "manifest.mjs")
    # pre-create
    (tmp_path / "existing-one.md").write_text(
        "---\nskill: existing-one\nsource_type: curated-external\n---\n\n## Purpose\n\nx", encoding="utf-8"
    )
    written = seed_curated_config_research(overwrite=False)
    assert written == []


def test_partition_skills_by_source_with_filter(monkeypatch):
    nodes = [
        _doc_node("alpha", "curated-external", "install-now-after-trust-gate"),
        _doc_node("beta", "curated-external", "install-now-after-trust-gate"),
        _doc_node("gamma", "curated-external", "inspect-then-install"),
        _doc_node("delta", "custom"),
    ]
    monkeypatch.setattr("wagents.skill_research.collect_skill_doc_nodes", lambda **kwargs: nodes)
    batches = partition_skills_by_source(batch_max=2)
    assert len(batches) >= 2
    batches_filtered = partition_skills_by_source(batch_max=10, curated_status="install-now-after-trust-gate")
    assert len(batches_filtered) == 1
    assert len(batches_filtered[0]) == 2
    ids = {n.id for n in batches_filtered[0]}
    assert ids == {"alpha", "beta"}


def test_validate_artifact_curated_external_requires_headers(tmp_path, monkeypatch):
    monkeypatch.setattr("wagents.skill_research.RESEARCH_DIR", tmp_path)
    # missing headers
    bad_path = write_skill_research_artifact(
        "cur-bad",
        source_type="curated-external",
        research_tier="standard",
        mean_confidence=0.6,
        body="Just some freeform text without the required sections.",
    )
    errs = validate_artifact(bad_path)
    assert any("missing curated-external header: ## Purpose" in e for e in errs)
    assert any("## Harness Coverage" in e for e in errs)
    # good body
    good_body = "\n\n".join(f"## {sec}\n\nContent for {sec}." for sec in CURATED_RESEARCH_SECTIONS)
    good_path = write_skill_research_artifact(
        "cur-good",
        source_type="curated-external",
        research_tier="standard",
        mean_confidence=0.7,
        body=good_body,
    )
    errs_good = validate_artifact(good_path)
    assert not any("missing curated-external header" in e for e in errs_good)
    assert errs_good == []
