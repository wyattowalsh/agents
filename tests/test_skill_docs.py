"""Tests for wagents.skill_docs unified catalog nodes."""

from wagents.catalog import CatalogNode
from wagents.skill_docs import (
    collect_skill_doc_nodes,
    merge_skill_doc_nodes,
    skill_detail_href,
    skill_detail_slug,
)


def _skill(id_suffix: str, *, source: str = "custom") -> CatalogNode:
    return CatalogNode(
        kind="skill",
        id=f"{id_suffix}-skill",
        title=f"Test {id_suffix}",
        description=f"Description for {id_suffix}",
        metadata={"name": f"{id_suffix}-skill"},
        body="# Body",
        source_path=f"skills/{id_suffix}-skill/SKILL.md",
        source=source,
    )


def test_skill_detail_paths():
    assert skill_detail_href("review", source="custom") == "/skills/catalog/custom/review/"
    assert skill_detail_slug("review", source="custom") == "skills/catalog/custom/review"
    assert skill_detail_href("demo-external", source="curated-external") == "/skills/catalog/external/demo-external/"


def test_merge_prefers_custom_over_installed():
    custom = _skill("alpha", source="custom")
    installed = _skill("alpha", source="installed")
    merged = merge_skill_doc_nodes([custom], [installed])
    assert len(merged) == 1
    assert merged[0].source == "custom"


def test_collect_skill_doc_nodes_marks_curated_stubs(monkeypatch):
    custom = _skill("repo", source="custom")

    monkeypatch.setattr("wagents.skill_docs.collect_repo_skill_nodes", lambda: [custom])
    monkeypatch.setattr("wagents.skill_docs.collect_installed_skill_nodes", lambda _ids: [])
    monkeypatch.setattr(
        "wagents.skill_docs.curated_entries_to_stub_nodes",
        lambda **kwargs: [
            CatalogNode(
                kind="skill",
                id="curated-skill",
                title="Curated",
                description="Curated external",
                metadata={"_is_stub": True, "_curated_status": "install-now-after-trust-gate"},
                body="",
                source_path="config/external-skills.md",
                source="curated-external",
            )
        ],
    )

    # Force the legacy stub path (no authoring mdx) for this test; real AUTHORING_SKILLS_DIR
    # now contains files post W3 sync/migrate, which would take the collect_authoring branch instead.
    from pathlib import Path

    monkeypatch.setattr(
        "wagents.skill_index.AUTHORING_SKILLS_DIR",
        Path("/nonexistent/forcing-legacy-stub-path-in-test"),
    )

    nodes = collect_skill_doc_nodes(include_installed=False, include_curated=True)
    by_id = {node.id: node for node in nodes}
    assert by_id["repo-skill"].source_type == "custom"
    assert by_id["curated-skill"].is_stub is True
    assert by_id["curated-skill"].source_type == "curated-external"
