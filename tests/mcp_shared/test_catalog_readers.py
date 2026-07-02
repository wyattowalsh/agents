"""Tests for wagents.mcp_shared.catalog_readers — read-only catalog wrappers for MCP servers."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from wagents.catalog import CatalogEdge, CatalogNode
from wagents.mcp_shared import catalog_readers

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def _skill_node(name: str = "review") -> CatalogNode:
    return CatalogNode(
        kind="skill",
        id=name,
        title=name.title(),
        description=f"{name} skill",
        metadata={},
        body="body",
        source_path=f"skills/{name}/SKILL.md",
    )


def _agent_node(name: str = "orchestrator") -> CatalogNode:
    return CatalogNode(
        kind="agent",
        id=name,
        title=name.title(),
        description=f"{name} agent",
        metadata={"skills": ["review"], "mcpServers": ["docs-index"]},
        body="body",
        source_path=f"agents/{name}.md",
    )


def test_node_to_dict_round_trips_fields() -> None:
    node = _skill_node()
    data = catalog_readers.node_to_dict(node)
    assert data["kind"] == "skill"
    assert data["id"] == "review"
    assert data["description"] == "review skill"


def test_edge_to_dict_round_trips_fields() -> None:
    edge = CatalogEdge(from_id="agent:orchestrator", to_id="skill:review", relation="uses-skill")
    data = catalog_readers.edge_to_dict(edge)
    assert data == {"from_id": "agent:orchestrator", "to_id": "skill:review", "relation": "uses-skill"}


def test_list_nodes_filters_by_kind(monkeypatch: pytest.MonkeyPatch) -> None:
    nodes = [_skill_node(), _agent_node()]
    monkeypatch.setattr(catalog_readers, "collect_nodes", lambda: nodes)
    assert catalog_readers.list_nodes() == nodes
    assert catalog_readers.list_nodes(kind="skill") == [nodes[0]]
    assert catalog_readers.list_nodes(kind="agent") == [nodes[1]]
    assert catalog_readers.list_nodes(kind="mcp") == []


def test_find_node_returns_match_or_none(monkeypatch: pytest.MonkeyPatch) -> None:
    nodes = [_skill_node(), _agent_node()]
    monkeypatch.setattr(catalog_readers, "collect_nodes", lambda: nodes)
    assert catalog_readers.find_node("skill", "review") is nodes[0]
    assert catalog_readers.find_node("skill", "missing") is None


def test_list_edges_derives_agent_cross_references(monkeypatch: pytest.MonkeyPatch) -> None:
    nodes = [_skill_node(), _agent_node()]
    monkeypatch.setattr(catalog_readers, "collect_nodes", lambda: nodes)
    edges = catalog_readers.list_edges()
    relations = {(e.from_id, e.to_id, e.relation) for e in edges}
    assert ("agent:orchestrator", "skill:review", "uses-skill") in relations
    assert ("agent:orchestrator", "mcp:docs-index", "uses-mcp") in relations


def test_load_skills_catalog_index_missing_file_returns_empty_shape(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(catalog_readers, "CATALOG_INDEX_PATH", tmp_path / "missing.json")
    assert catalog_readers.load_skills_catalog_index() == {
        "allSkillIndex": [],
        "customSkillIndex": [],
        "externalSkillIndex": [],
    }


def test_load_skills_catalog_index_reads_existing_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    payload = {"version": 1, "skills": [{"name": "review"}]}
    index_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(catalog_readers, "CATALOG_INDEX_PATH", index_path)
    assert catalog_readers.load_skills_catalog_index() == payload


def test_catalog_summary_counts_by_kind(monkeypatch: pytest.MonkeyPatch) -> None:
    nodes = [
        _skill_node("a"),
        _skill_node("b"),
        _agent_node(),
        CatalogNode(
            kind="mcp",
            id="docs-index",
            title="Docs Index",
            description="",
            metadata={},
            body="",
            source_path="mcp/docs-index/server.py",
        ),
    ]
    monkeypatch.setattr(catalog_readers, "collect_nodes", lambda: nodes)
    assert catalog_readers.catalog_summary() == {"skills": 2, "agents": 1, "mcp": 1}
