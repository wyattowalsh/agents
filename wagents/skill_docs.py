"""Unified skill document nodes for generated docs pages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from wagents.catalog import CatalogNode, collect_installed_skills, collect_nodes
from wagents.external_skills import ExternalSkillEntry, read_external_skill_entries
from wagents.parsing import to_title

SKILL_DETAIL_SLUG_PREFIX = "skills/catalog"

SourceType = Literal["custom", "installed", "curated-external"]

_SOURCE_PRIORITY: dict[str, int] = {
    "custom": 3,
    "installed": 2,
    "curated-external": 1,
}


@dataclass(frozen=True)
class SkillDocNode:
    """Skill row used by docs generate and research batching."""

    node: CatalogNode
    source_type: SourceType
    is_stub: bool = False
    curated_status: str = ""

    @property
    def id(self) -> str:
        return self.node.id

    @property
    def description(self) -> str:
        return self.node.description


def skill_detail_href(skill_id: str) -> str:
    """Return the canonical docs URL for a skill detail page."""
    return f"/{SKILL_DETAIL_SLUG_PREFIX}/{skill_id}/"


def skill_detail_slug(skill_id: str) -> str:
    """Return the Starlight content slug for a skill detail page."""
    return f"{SKILL_DETAIL_SLUG_PREFIX}/{skill_id}"


def collect_repo_skill_nodes() -> list[CatalogNode]:
    """Return repo-owned skills from ``skills/*/SKILL.md``."""
    return [node for node in collect_nodes() if node.kind == "skill" and node.source == "custom"]


def collect_installed_skill_nodes(existing_ids: set[str]) -> list[CatalogNode]:
    """Return installed harness skills not already present as repo-owned."""
    return collect_installed_skills(existing_ids)


def curated_entry_to_node(entry: ExternalSkillEntry) -> CatalogNode:
    """Build a stub catalog node from a curated external-skills.md entry."""
    description = entry.notes.strip() or f"Curated external skill: {entry.name}"
    if len(description) > 1024:
        description = description[:1021] + "..."
    metadata: dict[str, object] = {
        "name": entry.name,
        "description": description,
        "_skills_install_command": entry.install_command,
        "_skills_provenance_status": entry.provenance_status,
        "_skills_trust_tier": entry.trust_tier,
        "_skills_target_agents": list(entry.target_agents),
        "_skills_source": entry.source,
        "_skills_install_source": entry.install_source,
        "_curated_status": entry.status,
        "_is_stub": True,
    }
    if entry.risk_notes:
        metadata["_risk_notes"] = entry.risk_notes
    return CatalogNode(
        kind="skill",
        id=entry.name,
        title=to_title(entry.name),
        description=description,
        metadata=metadata,
        body="",
        source_path=entry.source_path,
        source="curated-external",
    )


def curated_entries_to_stub_nodes(
    entries: list[ExternalSkillEntry] | None = None,
    *,
    sections: str = "all",
) -> list[CatalogNode]:
    """Convert curated external entries into stub skill nodes."""
    rows = entries if entries is not None else read_external_skill_entries()
    nodes: list[CatalogNode] = []
    for entry in rows:
        if sections == "install-now" and entry.status != "install-now-after-trust-gate":
            continue
        nodes.append(curated_entry_to_node(entry))
    return nodes


def merge_skill_doc_nodes(*node_groups: list[CatalogNode]) -> list[CatalogNode]:
    """Merge skill nodes by name; higher-priority ``source`` wins."""
    merged: dict[str, CatalogNode] = {}
    for group in node_groups:
        for node in group:
            if node.kind != "skill":
                continue
            existing = merged.get(node.id)
            if existing is None:
                merged[node.id] = node
                continue
            if _SOURCE_PRIORITY.get(node.source, 0) > _SOURCE_PRIORITY.get(existing.source, 0):
                merged[node.id] = node
    return sorted(merged.values(), key=lambda item: item.id)


def collect_skill_doc_nodes(
    *,
    include_installed: bool = True,
    include_curated: bool = True,
    curated_sections: str = "all",
) -> list[SkillDocNode]:
    """Collect unified skill nodes for docs generation and research."""
    repo_nodes = collect_repo_skill_nodes()
    repo_ids = {node.id for node in repo_nodes}
    groups: list[list[CatalogNode]] = [repo_nodes]

    if include_installed:
        groups.append(collect_installed_skill_nodes(repo_ids))

    if include_curated:
        groups.append(curated_entries_to_stub_nodes(sections=curated_sections))

    merged = merge_skill_doc_nodes(*groups)
    doc_nodes: list[SkillDocNode] = []
    for node in merged:
        if node.source == "custom":
            source_type: SourceType = "custom"
        elif node.source == "installed":
            source_type = "installed"
        else:
            source_type = "curated-external"
        is_stub = bool(node.metadata.get("_is_stub")) or (
            source_type == "curated-external" and not node.body.strip()
        )
        curated_status = str(node.metadata.get("_curated_status") or "")
        doc_nodes.append(
            SkillDocNode(
                node=node,
                source_type=source_type,
                is_stub=is_stub,
                curated_status=curated_status,
            )
        )
    return doc_nodes


def collect_all_doc_nodes(
    *,
    include_installed: bool = True,
    include_drafts: bool = False,
    include_curated: bool = True,
) -> list[CatalogNode]:
    """Collect agents, MCP servers, and unified skill nodes for docs generate."""
    non_skills = [node for node in collect_nodes() if node.kind != "skill"]
    skills = [
        doc.node
        for doc in collect_skill_doc_nodes(include_installed=include_installed, include_curated=include_curated)
    ]
    if not include_drafts:
        skills = [node for node in skills if not node.description.strip().upper().startswith("TODO")]
    return non_skills + skills
