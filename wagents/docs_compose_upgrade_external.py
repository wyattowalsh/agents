"""External catalog page upgrades (wrangler-depth contract)."""

from __future__ import annotations

import re

import yaml

from wagents import ROOT
from wagents.catalog import RELATED_SKILLS, collect_edges
from wagents.docs_lint import HAND_MAINTAINED_SENTINEL
from pathlib import Path

from wagents.docs_compose_apply import compose_skill_mdx
from wagents.docs_compose_batch import UpgradeResult, run_upgrade_batch
from wagents.docs_mdx_safety import escape_composed_page_prose, strip_duplicate_details_headings
from wagents.rendering import escape_attr, truncate_sentence
from wagents.skill_docs import collect_all_doc_nodes, skill_detail_href

EXTERNAL_CATALOG = ROOT / "docs" / "src" / "content" / "docs" / "skills" / "catalog" / "external"
AUTHORING_DIR = ROOT / "docs" / "src" / "authoring" / "skills"
_CURATED_ASIDE = re.compile(
    r'<Aside type="note" title="Curated external \(hand-maintained\)">.*?</Aside>\s*',
    re.DOTALL,
)


def batch_composed_external_ids() -> list[str]:
    ids: list[str] = []
    for page in sorted(EXTERNAL_CATALOG.glob("*.mdx")):
        if page.name == "index.mdx":
            continue
        text = page.read_text(encoding="utf-8")
        if "composed: true" in text and HAND_MAINTAINED_SENTINEL in text:
            ids.append(page.stem)
    return ids


def _external_wave_for_skill(skill_id: str, batch_ids: list[str], batch_size: int = 25) -> str:
    try:
        index = batch_ids.index(skill_id)
    except ValueError:
        return "compose-external-wave-1"
    return f"compose-external-wave-{index // batch_size + 1}"


def _extract_section(page: str, heading: str) -> tuple[str, str]:
    marker = f"## {heading}\n"
    start = page.find(marker)
    if start < 0:
        return page, ""
    rest = page[start + len(marker) :]
    end = len(rest)
    for nxt in ("## ", "<Tabs>", "<details"):
        pos = rest.find(nxt)
        if pos >= 0:
            end = min(end, pos)
    block = marker + rest[:end].rstrip() + "\n\n"
    return page[:start] + rest[end:], block


def _reorder_what_it_does(page: str) -> str:
    if "## What It Does\n" not in page or "## Harness Coverage\n" not in page:
        return page
    if page.find("## What It Does\n") < page.find("## Harness Coverage\n"):
        return page
    page, what_block = _extract_section(page, "What It Does")
    insert_at = page.find("## Harness Coverage\n")
    if insert_at < 0 or not what_block:
        return page
    return page[:insert_at] + what_block + page[insert_at:]


def _related_skills_block(node, all_nodes) -> str:
    related = RELATED_SKILLS.get(node.id, [])
    if not related:
        return ""
    lines = ["## Related Skills", "", "<CardGrid>"]
    for rel_id in related:
        rel_node = next((n for n in all_nodes if n.kind == "skill" and n.id == rel_id), None)
        if rel_node:
            desc = escape_attr(truncate_sentence(rel_node.description, 160))
            href = skill_detail_href(rel_id, node=rel_node)
            lines.append(
                f'  <LinkCard title="{escape_attr(rel_id)}" href="{href}" description="{desc}" />'
            )
        else:
            lines.append(
                f'  <LinkCard title="{escape_attr(rel_id)}"'
                f' href="{skill_detail_href(rel_id, source="custom")}"'
                ' description="Related curated external skill." />'
            )
    lines.extend(["</CardGrid>", ""])
    return "\n".join(lines)


def _authoring_provenance_table(skill_id: str) -> str:
    authoring = AUTHORING_DIR / f"{skill_id}.mdx"
    if not authoring.exists():
        return ""
    text = authoring.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end < 0:
        return ""
    data = yaml.safe_load(text[3:end]) or {}
    if not isinstance(data, dict):
        return ""

    def row(key: str, val: object) -> str:
        if val is None or val == "" or val == []:
            return ""
        if isinstance(val, list):
            val = ", ".join(str(v) for v in val)
        return f"| {key} | `{val}` |"

    rows = [
        row("install_command", data.get("install_command")),
        row("source", data.get("source") or data.get("install_source")),
        row("source_url", data.get("source_url")),
        row("trust_tier", data.get("trust_tier")),
        row("curated_status", data.get("status")),
        row("target_agents", data.get("target_agents")),
    ]
    rows = [r for r in rows if r]
    if not rows:
        return ""
    header = "**Install / provenance (from authoring frontmatter + research):**\n\n"
    table = "| Field | Value |\n|-------|-------|\n" + "\n".join(rows) + "\n"
    return f"\n{header}{table}"


def _append_provenance_table(page: str, skill_id: str) -> str:
    table = _authoring_provenance_table(skill_id)
    if not table or table in page:
        return page
    idx = page.rfind("</details>")
    if idx < 0:
        return page
    return page[:idx] + table + "\n" + page[idx:]


def _trim_research_sections(page: str) -> str:
    for heading in ("Purpose", "Comparable Alternatives", "Upstream Maintainer"):
        page, _ = _extract_section(page, heading)
    return page


def _curated_aside(skill_id: str, wave_id: str) -> str:
    return (
        '<Aside type="note" title="Curated external (hand-maintained)">\n'
        f"Composed {wave_id} using authoring SSOT "
        f"(`docs/src/authoring/skills/{skill_id}.mdx`) + research. "
        "Do not run `wagents docs generate` on this file (HAND-MAINTAINED sentinel). "
        "Run external-skill-auditor before using in production or promoting.\n"
        "</Aside>\n\n"
    )


def upgrade_external_skill_mdx(node, edges, all_nodes, *, wave_id: str) -> str:
    page = compose_skill_mdx(node, edges, all_nodes, wave_id=wave_id)
    page = _CURATED_ASIDE.sub(_curated_aside(node.id, wave_id), page, count=1)
    page = page.replace(
        "Entry maintained via authoring + research for compose-batch-apply",
        f"Entry maintained via authoring + research for {wave_id}",
    )
    page = _trim_research_sections(page)
    page = _reorder_what_it_does(page)
    main = page.split("<details", 1)[0]
    if "## Related Skills\n" not in main:
        rel = _related_skills_block(node, all_nodes)
        if rel:
            idx = page.find("<details")
            if idx >= 0:
                page = page[:idx] + rel + page[idx:]
    page = _append_provenance_table(page, node.id)
    page = escape_composed_page_prose(page)
    page = strip_duplicate_details_headings(page)
    return page


def upgrade_external_batch(
    *,
    skill_ids: list[str] | None = None,
    wave_id: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> UpgradeResult:
    batch_ids = batch_composed_external_ids()
    targets = skill_ids or batch_ids
    nodes = collect_all_doc_nodes(include_installed=False, include_drafts=False)
    by_id = {n.id: n for n in nodes if n.kind == "skill" and n.source == "curated-external"}
    edges = collect_edges(nodes)

    def resolve_wave(skill_id: str) -> str:
        return wave_id or _external_wave_for_skill(skill_id, batch_ids)

    def load_page(skill_id: str) -> Path | None:
        path = EXTERNAL_CATALOG / f"{skill_id}.mdx"
        return path if path.exists() else None

    def transform(skill_id: str, resolved_wave: str) -> str | None:
        node = by_id.get(skill_id)
        if node is None:
            return None
        return upgrade_external_skill_mdx(node, edges, nodes, wave_id=resolved_wave)

    return run_upgrade_batch(
        target_ids=targets,
        resolve_wave=resolve_wave,
        load_page=load_page,
        transform=transform,
        force=force,
        dry_run=dry_run,
    )
