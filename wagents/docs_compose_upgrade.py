"""Upgrade batch-composed custom skill pages toward orchestrator-level depth."""

from __future__ import annotations

import re
from pathlib import Path

from wagents import ROOT
from wagents.catalog import collect_edges
from wagents.docs_compose_batch import UpgradeResult, run_upgrade_batch
from wagents.docs_lint import HAND_MAINTAINED_SENTINEL
from wagents.docs_mdx_safety import escape_composed_page_prose, strip_duplicate_details_headings
from wagents.page_frontmatter import render_composed_frontmatter_block
from wagents.rendering import (
    _catalog_prose,
    _extract_body_sections,
    escape_mdx,
    read_raw_content,
    render_skill_page,
    safe_outer_fence,
)
from wagents.skill_docs import collect_all_doc_nodes
from wagents.skill_research import load_skill_research

CUSTOM_CATALOG = ROOT / "docs" / "src" / "content" / "docs" / "skills" / "catalog" / "custom"
_SKIP_INLINE = {"references", "reference file index", "dispatch"}
_RESEARCH_ASIDE = re.compile(
    r'<Aside type="note" title="Research context \(evidence, not authority\)">.*?</Aside>\s*',
    re.DOTALL,
)
_OLD_DETAILS = re.compile(r"<details class=\"source-disclosure\">.*?</details>\s*", re.DOTALL)


def _wave_for_skill(skill_id: str, batch_ids: list[str], batch_size: int = 7) -> str:
    try:
        index = batch_ids.index(skill_id)
    except ValueError:
        return "compose-custom-wave-1"
    return f"compose-custom-wave-{index // batch_size + 1}"


RICH_HAND_CUSTOM = {
    "orchestrator",
    "honest-review",
    "wargame",
    "prompt-engineer",
    "host-panel",
    "add-badges",
    "python-conventions",
    "mcp-creator",
}


def batch_composed_custom_ids() -> list[str]:
    ids: list[str] = []
    for path in sorted(CUSTOM_CATALOG.glob("*.mdx")):
        if path.name == "index.mdx" or path.stem in RICH_HAND_CUSTOM:
            continue
        text = path.read_text(encoding="utf-8")
        if "composed: true" in text and HAND_MAINTAINED_SENTINEL in text:
            ids.append(path.stem)
    return ids


def _condensed_research_aside(skill_id: str) -> str:
    body = load_skill_research(skill_id)
    if not body:
        return ""
    bullets: list[str] = []
    for ln in body.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("**") and s.endswith("**") or s.startswith("**") and ":" in s:
            bullets.append(s)
        if len(bullets) >= 3:
            break
    if not bullets:
        return ""
    inner = "\n".join(bullets)
    return (
        '<Aside type="note" title="Research context (evidence, not authority)">\n'
        f"{escape_mdx(inner)}\n"
        "</Aside>\n\n"
    )


def _maybe_steps(content: str) -> str:
    lines = content.strip().splitlines()
    numbered = [ln for ln in lines if re.match(r"^\d+\.\s", ln.strip())]
    if len(numbered) < 3:
        return content
    steps = []
    for ln in lines:
        m = re.match(r"^(\d+)\.\s+(.*)$", ln.strip())
        if m:
            steps.append(f"{m.group(1)}. **Step** -- {m.group(2)}")
        elif ln.strip() and not steps:
            return content
    if len(steps) < 3:
        return content
    inner = "\n\n".join(steps)
    return f"<Steps>\n\n{inner}\n\n</Steps>"


def _insert_missing_sections(page: str, node) -> str:
    sections = _extract_body_sections(node.body or "")
    blocks: list[str] = []
    main = page.split("<details", 1)[0]
    for key, section_content in sections.items():
        if key in _SKIP_INLINE or not section_content.strip():
            continue
        heading = key.title()
        if f"## {heading}\n" in main:
            continue
        prose = _maybe_steps(_catalog_prose(section_content))
        blocks.append(f"## {heading}\n\n{prose}\n\n")
    if not blocks:
        return page
    for anchor in ("<Tabs>", "<details"):
        idx = page.find(anchor)
        if idx >= 0:
            return page[:idx] + "".join(blocks) + page[idx:]
    return page + "\n" + "".join(blocks)


def _details_block(node) -> str:
    raw = read_raw_content(node)
    fence = safe_outer_fence(raw)
    source = node.source_path or f"skills/{node.id}/SKILL.md"
    return (
        '<details class="source-disclosure">\n'
        "<summary>Full SKILL.md</summary>\n\n"
        f'{fence}yaml title="{source}"\n'
        f"{raw}\n"
        f"{fence}\n\n"
        f"[Download from GitHub](https://raw.githubusercontent.com/wyattowalsh/agents/main/{source})\n\n"
        "</details>\n\n"
    )


def _provenance_aside(source_path: str, wave_id: str) -> str:
    return (
        '<Aside type="note" title="Repo skill (hand-maintained)">\n'
        f"Composed {wave_id} from `{source_path}` with full SKILL disclosure. "
        "Do not run `wagents docs generate` on this file (HAND-MAINTAINED sentinel).\n"
        "</Aside>\n\n"
    )


def upgrade_custom_skill_mdx(node, edges, all_nodes, *, wave_id: str) -> str:
    page = render_skill_page(node, edges, all_nodes)
    page = re.sub(
        r"^---\n.*?\n---\n",
        render_composed_frontmatter_block(node, wave_id=wave_id),
        page,
        count=1,
        flags=re.DOTALL,
    )
    page = _RESEARCH_ASIDE.sub("", page, count=1)
    research_aside = _condensed_research_aside(node.id)
    if research_aside:
        for marker in ("/>\n\nWorks with", "</div>\n\nWorks with"):
            if marker in page:
                prefix = marker.split("\n\n", 1)[0]
                page = page.replace(marker, f"{prefix}\n\n{research_aside}Works with", 1)
                break
    page = re.sub(
        r'<Aside type="note" title="(?:Repo skill \(hand-maintained\)|Source & provenance)">.*?</Aside>\s*',
        _provenance_aside(node.source_path or f"skills/{node.id}/SKILL.md", wave_id),
        page,
        count=1,
        flags=re.DOTALL,
    )
    page = _insert_missing_sections(page, node)
    page = _OLD_DETAILS.sub(_details_block(node), page, count=1)
    page = escape_composed_page_prose(page)
    page = strip_duplicate_details_headings(page)
    return page


def upgrade_custom_batch(
    *,
    skill_ids: list[str] | None = None,
    wave_id: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> UpgradeResult:
    batch_ids = batch_composed_custom_ids()
    targets = skill_ids or batch_ids
    nodes = collect_all_doc_nodes(include_installed=False, include_drafts=False)
    by_id = {n.id: n for n in nodes if n.kind == "skill" and n.source == "custom"}
    edges = collect_edges(nodes)

    def resolve_wave(skill_id: str) -> str:
        return wave_id or _wave_for_skill(skill_id, batch_ids)

    def load_page(skill_id: str) -> Path | None:
        path = CUSTOM_CATALOG / f"{skill_id}.mdx"
        return path if path.exists() else None

    def transform(skill_id: str, resolved_wave: str) -> str | None:
        node = by_id.get(skill_id)
        if node is None:
            return None
        return upgrade_custom_skill_mdx(node, edges, nodes, wave_id=resolved_wave)

    return run_upgrade_batch(
        target_ids=targets,
        resolve_wave=resolve_wave,
        load_page=load_page,
        transform=transform,
        force=force,
        dry_run=dry_run,
    )
