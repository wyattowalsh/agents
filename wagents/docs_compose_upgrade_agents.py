"""Upgrade batch-composed agent pages to compose-agents-wave-1 depth."""

from __future__ import annotations

from typing import TYPE_CHECKING

from wagents import ROOT
from wagents.catalog import collect_edges
from wagents.docs_compose_apply import compose_agent_mdx
from wagents.docs_compose_batch import UpgradeResult, run_upgrade_batch
from wagents.docs_lint import HAND_MAINTAINED_SENTINEL
from wagents.docs_mdx_safety import escape_composed_page_prose, strip_duplicate_details_headings
from wagents.rendering import escape_mdx
from wagents.site_model import SUPPORTED_AGENT_IDS
from wagents.skill_docs import collect_all_doc_nodes

if TYPE_CHECKING:
    from pathlib import Path

AGENTS_DIR = ROOT / "docs" / "src" / "content" / "docs" / "agents"
AGENTS_WAVE_ID = "compose-agents-wave-1"
HARNESS_AGENTS = tuple(SUPPORTED_AGENT_IDS)
_PENDING_MARKERS = ("compose-batch-apply",)


def batch_composed_agent_ids() -> list[str]:
    ids: list[str] = []
    for path in sorted(AGENTS_DIR.glob("*.mdx")):
        if path.name == "index.mdx":
            continue
        text = path.read_text(encoding="utf-8")
        if "composed: true" in text and HAND_MAINTAINED_SENTINEL in text:
            ids.append(path.stem)
    return ids


def _harness_coverage_block() -> str:
    names = ", ".join(f"`{agent}`" for agent in HARNESS_AGENTS)
    return f"## Harness Coverage\n\nAgent definitions sync to project and home harness surfaces including {names}.\n\n"


def upgrade_agent_mdx(node, edges, all_nodes, *, wave_id: str = AGENTS_WAVE_ID) -> str:
    page = compose_agent_mdx(node, edges, all_nodes, wave_id=wave_id)
    if "## What It Does\n" not in page:
        what = f"## What It Does\n\n{escape_mdx(node.description)}\n\n"
        marker = "## System Prompt\n"
        page = page.replace(marker, what + marker, 1) if marker in page else page.rstrip() + "\n\n" + what
    if "## Harness Coverage\n" not in page:
        insert = _harness_coverage_block()
        marker = "## System Prompt\n"
        page = page.replace(marker, insert + marker, 1) if marker in page else page.rstrip() + "\n\n" + insert
    page = escape_composed_page_prose(page)
    return strip_duplicate_details_headings(page)


def upgrade_agents_batch(
    *,
    agent_ids: list[str] | None = None,
    wave_id: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> UpgradeResult:
    batch_ids = batch_composed_agent_ids()
    targets = agent_ids or batch_ids
    nodes = collect_all_doc_nodes(include_installed=False, include_drafts=False)
    by_id = {n.id: n for n in nodes if n.kind == "agent"}
    edges = collect_edges(nodes)
    resolved_wave = wave_id or AGENTS_WAVE_ID

    def resolve_wave(_agent_id: str) -> str:
        return resolved_wave

    def load_page(agent_id: str) -> Path | None:
        path = AGENTS_DIR / f"{agent_id}.mdx"
        return path if path.exists() else None

    def transform(agent_id: str, wave: str) -> str | None:
        node = by_id.get(agent_id)
        if node is None:
            return None
        return upgrade_agent_mdx(node, edges, nodes, wave_id=wave)

    return run_upgrade_batch(
        target_ids=targets,
        resolve_wave=resolve_wave,
        load_page=load_page,
        transform=transform,
        force=force,
        pending_markers=_PENDING_MARKERS,
        dry_run=dry_run,
    )
