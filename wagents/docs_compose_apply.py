"""Deterministic batch application of composed catalog page contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from wagents import ROOT
from wagents.catalog import collect_edges
from wagents.docs_compose import ComposeSurface, collect_compose_targets, is_composed_mdx
from wagents.docs_lint import HAND_MAINTAINED_SENTINEL
from wagents.page_frontmatter import render_catalog_frontmatter_lines
from wagents.rendering import render_agent_page, render_mcp_page, render_skill_page, safe_outer_fence
from wagents.skill_docs import collect_all_doc_nodes

AUTHORING_DIR = ROOT / "docs" / "src" / "authoring" / "skills"

_PROVENANCE_ASIDE = re.compile(
    r'<Aside type="note" title="Source & provenance">.*?</Aside>',
    re.DOTALL,
)
_SKILL_DETAILS = re.compile(r"<details>\s*<summary>View Full SKILL\.md</summary>.*?</details>", re.DOTALL)
_AGENT_DETAILS = re.compile(
    r"<details>\s*<summary>View Full Agent File</summary>.*?</details>",
    re.DOTALL,
)


@dataclass(frozen=True)
class ApplyResult:
    written: int
    skipped: int
    missing: int
    paths: list[str]


def _composed_frontmatter_block(node, *, wave_id: str) -> str:
    lines = render_catalog_frontmatter_lines(node, composed=True)
    lines.append(f'composed_by: "{wave_id}"')
    lines.append(f'composed_at: "{date.today().isoformat()}"')
    block = "---\n" + "\n".join(lines) + "\n---\n\n"
    return block + HAND_MAINTAINED_SENTINEL + "\n"


def _replace_frontmatter(text: str, frontmatter_block: str) -> str:
    return re.sub(r"^---\n.*?\n---\n", frontmatter_block, text, count=1, flags=re.DOTALL)


def _external_provenance_aside(skill_id: str, wave_id: str) -> str:
    return (
        '<Aside type="note" title="Curated external (hand-maintained)">\n'
        f"Composed {wave_id} using authoring SSOT "
        f"(`docs/src/authoring/skills/{skill_id}.mdx`) + research. "
        "Do not run `wagents docs generate` on this file (HAND-MAINTAINED sentinel). "
        "Run `/review source` before using in production or promoting.\n"
        "</Aside>"
    )


def _custom_provenance_aside(source_path: str, wave_id: str) -> str:
    return (
        '<Aside type="note" title="Repo skill (hand-maintained)">\n'
        f"Composed {wave_id} from `{source_path}`. "
        "Do not run `wagents docs generate` on this file (HAND-MAINTAINED sentinel).\n"
        "</Aside>"
    )


def _agent_provenance_aside(source_path: str, wave_id: str) -> str:
    return (
        '<Aside type="note" title="Repo agent (hand-maintained)">\n'
        f"Composed {wave_id} from `{source_path}`. "
        "Do not run `wagents docs generate` on this file (HAND-MAINTAINED sentinel).\n"
        "</Aside>"
    )


def _mcp_provenance_aside(server_id: str, wave_id: str) -> str:
    return (
        '<Aside type="note" title="Repo MCP server (hand-maintained)">\n'
        f"Composed {wave_id} from `mcp/{server_id}/`. "
        "Do not run `wagents docs generate` on this file (HAND-MAINTAINED sentinel).\n"
        "</Aside>"
    )


def _external_details_block(skill_id: str) -> str | None:
    authoring = AUTHORING_DIR / f"{skill_id}.mdx"
    if not authoring.exists():
        return None
    content = authoring.read_text(encoding="utf-8")
    fence = safe_outer_fence(content)
    return (
        '<details class="source-disclosure">\n'
        "<summary>Curated catalog entry</summary>\n\n"
        f'{fence}mdx title="docs/src/authoring/skills/{skill_id}.mdx (full SSOT excerpt)"\n'
        f"{content}\n"
        f"{fence}\n"
        "</details>"
    )


def compose_skill_mdx(node, edges, all_nodes, *, wave_id: str) -> str:
    body = render_skill_page(node, edges, all_nodes)
    body = _replace_frontmatter(body, _composed_frontmatter_block(node, wave_id=wave_id))

    if node.source == "curated-external":
        body = _PROVENANCE_ASIDE.sub(_external_provenance_aside(node.id, wave_id), body, count=1)
        if "## What It Does" not in body and "## Purpose\n" in body:
            body = body.replace("## Purpose\n", "## What It Does\n", 1)
        details = _external_details_block(node.id)
        if details:
            body = _SKILL_DETAILS.sub(details, body, count=1)
        else:
            body = body.replace("<details>", '<details class="source-disclosure">', 1)
            body = body.replace(
                "<summary>View Full SKILL.md</summary>",
                "<summary>Curated catalog entry</summary>",
                1,
            )
    else:
        source = node.source_path or f"skills/{node.id}/SKILL.md"
        body = _PROVENANCE_ASIDE.sub(_custom_provenance_aside(source, wave_id), body, count=1)
        body = body.replace("<details>", '<details class="source-disclosure">', 1)
        body = body.replace(
            "<summary>View Full SKILL.md</summary>",
            "<summary>Full SKILL.md</summary>",
            1,
        )

    trust_marker = "Entry maintained in `config/external-skills.md`"
    if trust_marker in body:
        body = body.replace(
            trust_marker,
            f"Entry maintained via authoring + research for {wave_id}",
            1,
        )
    return body


def compose_agent_mdx(node, edges, all_nodes, *, wave_id: str) -> str:
    body = render_agent_page(node, edges, all_nodes)
    body = _replace_frontmatter(body, _composed_frontmatter_block(node, wave_id=wave_id))
    source = node.source_path or f"agents/{node.id}.md"
    body = _PROVENANCE_ASIDE.sub(_agent_provenance_aside(source, wave_id), body, count=1)
    return _AGENT_DETAILS.sub(
        lambda match: (
            match
            .group(0)
            .replace("<details>", '<details class="source-disclosure">', 1)
            .replace("<summary>View Full Agent File</summary>", "<summary>Full agent file</summary>", 1)
        ),
        body,
        count=1,
    )


def compose_mcp_mdx(node, edges, all_nodes, *, wave_id: str) -> str:
    body = render_mcp_page(node, edges, all_nodes)
    body = _replace_frontmatter(body, _composed_frontmatter_block(node, wave_id=wave_id))
    return _PROVENANCE_ASIDE.sub(_mcp_provenance_aside(node.id, wave_id), body, count=1)


def _node_index(nodes) -> dict[tuple[str, str], object]:
    return {(node.kind, node.id): node for node in nodes}


def apply_compose_batch(
    *,
    surface: ComposeSurface = "all",
    wave_id: str = "compose-batch-apply",
    dry_run: bool = False,
) -> ApplyResult:
    targets = collect_compose_targets(surface=surface)
    nodes = collect_all_doc_nodes(include_installed=False, include_drafts=False)
    by_key = _node_index(nodes)
    edges = collect_edges(nodes)

    written = 0
    skipped = 0
    missing = 0
    paths: list[str] = []

    for target in targets:
        if target.surface in {"hooks", "configs"}:
            continue
        if not target.page_path.exists():
            missing += 1
            continue
        existing = target.page_path.read_text(encoding="utf-8")
        if is_composed_mdx(existing):
            skipped += 1
            continue

        if target.surface == "skills":
            node = by_key.get(("skill", target.asset_id))
        elif target.surface == "agents":
            node = by_key.get(("agent", target.asset_id))
        elif target.surface == "mcp":
            node = by_key.get(("mcp", target.asset_id))
        else:
            node = None

        if node is None:
            missing += 1
            continue

        if target.surface == "skills":
            content = compose_skill_mdx(node, edges, nodes, wave_id=wave_id)
        elif target.surface == "agents":
            content = compose_agent_mdx(node, edges, nodes, wave_id=wave_id)
        elif target.surface == "mcp":
            content = compose_mcp_mdx(node, edges, nodes, wave_id=wave_id)
        else:
            missing += 1
            continue

        rel = str(target.page_path.relative_to(ROOT))
        paths.append(rel)
        if not dry_run:
            target.page_path.write_text(content, encoding="utf-8")
        written += 1

    return ApplyResult(written=written, skipped=skipped, missing=missing, paths=paths)
