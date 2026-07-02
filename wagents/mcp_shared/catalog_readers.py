"""Thin read-only wrappers over `wagents.catalog` / `wagents.skill_index` for MCP servers.

Every repo-authored catalog-facing MCP server (`mcp/skill-catalog`,
`mcp/agent-catalog`, `mcp/docs-index`, `mcp/eval-results`, ...) should read
skills/agents/mcp metadata through this module instead of re-implementing
frontmatter parsing or catalog scanning, so behavior stays consistent with
`wagents docs generate` / `wagents catalog index`.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from wagents.catalog import CatalogEdge, CatalogNode, collect_edges, collect_nodes
from wagents.skill_index import CATALOG_INDEX_PATH


def node_to_dict(node: CatalogNode) -> dict[str, Any]:
    """Convert a `CatalogNode` dataclass into a JSON-serializable dict."""
    return asdict(node)


def edge_to_dict(edge: CatalogEdge) -> dict[str, Any]:
    """Convert a `CatalogEdge` dataclass into a JSON-serializable dict."""
    return asdict(edge)


def list_nodes(kind: str | None = None) -> list[CatalogNode]:
    """Return catalog nodes, optionally filtered to one kind ('skill' | 'agent' | 'mcp')."""
    nodes = collect_nodes()
    if kind is None:
        return nodes
    return [n for n in nodes if n.kind == kind]


def find_node(kind: str, node_id: str) -> CatalogNode | None:
    """Return the first catalog node matching *kind* and *node_id*, or None."""
    for node in collect_nodes():
        if node.kind == kind and node.id == node_id:
            return node
    return None


def list_edges() -> list[CatalogEdge]:
    """Return agent -> skill/mcp cross-reference edges derived from agent frontmatter."""
    return collect_edges(collect_nodes())


def load_skills_catalog_index() -> dict[str, Any]:
    """Load the generated public skills-catalog-index.json (machine SSOT for skills).

    Returns an empty index shape when the generated file has not been produced
    yet (e.g. before the first `wagents docs generate` run).
    """
    if not CATALOG_INDEX_PATH.exists():
        return {"allSkillIndex": [], "customSkillIndex": [], "externalSkillIndex": []}
    return json.loads(CATALOG_INDEX_PATH.read_text(encoding="utf-8"))


def catalog_summary() -> dict[str, int]:
    """Return coarse counts per catalog kind, useful for MCP resource listings."""
    nodes = collect_nodes()
    counts = {"skills": 0, "agents": 0, "mcp": 0}
    for node in nodes:
        key = "mcp" if node.kind == "mcp" else f"{node.kind}s"
        counts[key] = counts.get(key, 0) + 1
    return counts
