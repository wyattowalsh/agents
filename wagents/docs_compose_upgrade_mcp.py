"""Upgrade batch-composed MCP catalog pages."""

from __future__ import annotations

from pathlib import Path

from wagents import ROOT
from wagents.catalog import collect_edges
from wagents.docs_compose_apply import compose_mcp_mdx
from wagents.docs_compose_batch import UpgradeResult, run_upgrade_batch
from wagents.docs_mdx_safety import escape_composed_page_prose
from wagents.skill_docs import collect_all_doc_nodes

MCP_DIR = ROOT / "docs" / "src" / "content" / "docs" / "mcp"
MCP_WAVE_ID = "compose-mcp-wave-1"
_PENDING_MARKERS = ("compose-batch-apply",)


def batch_composed_mcp_ids() -> list[str]:
    ids: list[str] = []
    for path in sorted(MCP_DIR.glob("*.mdx")):
        if path.name == "index.mdx":
            continue
        text = path.read_text(encoding="utf-8")
        if "composed: true" in text and 'composed_by: "compose-batch-apply"' in text:
            ids.append(path.stem)
    return ids


def upgrade_mcp_mdx(node, edges, all_nodes, *, wave_id: str = MCP_WAVE_ID) -> str:
    page = compose_mcp_mdx(node, edges, all_nodes, wave_id=wave_id)
    return escape_composed_page_prose(page)


def upgrade_mcp_batch(
    *,
    mcp_ids: list[str] | None = None,
    wave_id: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> UpgradeResult:
    batch_ids = batch_composed_mcp_ids()
    targets = mcp_ids or batch_ids
    nodes = collect_all_doc_nodes(include_installed=False, include_drafts=False)
    by_id = {n.id: n for n in nodes if n.kind == "mcp"}
    edges = collect_edges(nodes)
    resolved_wave = wave_id or MCP_WAVE_ID

    def resolve_wave(_mcp_id: str) -> str:
        return resolved_wave

    def load_page(mcp_id: str) -> Path | None:
        path = MCP_DIR / f"{mcp_id}.mdx"
        return path if path.exists() else None

    def transform(mcp_id: str, wave: str) -> str | None:
        node = by_id.get(mcp_id)
        if node is None:
            return None
        return upgrade_mcp_mdx(node, edges, nodes, wave_id=wave)

    return run_upgrade_batch(
        target_ids=targets,
        resolve_wave=resolve_wave,
        load_page=load_page,
        transform=transform,
        force=force,
        pending_markers=_PENDING_MARKERS,
        dry_run=dry_run,
    )