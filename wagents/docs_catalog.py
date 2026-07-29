"""Unified catalog discovery pages (/catalog/*) and architecture docs (W5).

Generates maintainer-facing discovery IA under `docs/src/content/docs/catalog/`:
- `/catalog/` landing
- `/catalog/agents/` — agent discovery (links to `/agents/<id>/`)
- `/catalog/mcp/` — MCP discovery with empty-state when no servers
- `/catalog/tags/`, `/catalog/platforms/`, `/catalog/tooling/` — facet indexes

Also emits architecture explainers:
- `/architecture/progressive-disclosure/`
- `/architecture/instruction-loading/`
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

if TYPE_CHECKING:
    from pathlib import Path

from wagents import CONTENT_DIR, ROOT
from wagents.catalog import CatalogNode, collect_nodes
from wagents.parsing import escape_attr, truncate_sentence
from wagents.skill_index import entry_catalog_tags, entry_platforms, read_catalog_index

CATALOG_CONTENT_DIR = CONTENT_DIR / "catalog"
ARCHITECTURE_CONTENT_DIR = CONTENT_DIR / "architecture"
MdxWriter = Callable[["Path", dict[str, str], list[str]], None]

# Harness ids surfaced on platform index pages (from harness-surface-registry when present).
_DEFAULT_PLATFORMS = (
    "claude-code",
    "cursor",
    "codex",
    "opencode",
    "grok",
)


def _load_harness_labels() -> dict[str, str]:
    path = ROOT / "config" / "harness-surface-registry.json"
    if not path.is_file():
        return {h: h.replace("-", " ").title() for h in _DEFAULT_PLATFORMS}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {h: h.replace("-", " ").title() for h in _DEFAULT_PLATFORMS}
    labels: dict[str, str] = {}
    for record in data.get("harnesses", []):
        hid = str(record.get("id") or "")
        if hid:
            labels[hid] = str(record.get("label") or hid)
    return labels or {h: h.replace("-", " ").title() for h in _DEFAULT_PLATFORMS}


def _catalog_skill_entries(skills_index: dict[str, Any]) -> list[dict[str, Any]]:
    """Return skill rows from the generated catalog index bundle."""
    if not isinstance(skills_index, dict):
        return []
    for key in ("allSkillIndex", "skillIndex", "skills"):
        rows = skills_index.get(key)
        if isinstance(rows, list) and rows:
            return [entry for entry in rows if isinstance(entry, dict)]
    return []


def _skills_catalog_index() -> dict[str, Any]:
    index = read_catalog_index()
    return index if isinstance(index, dict) else {}


_TEACHING_TOPOLOGY_NAMES = (
    "orchestrator",
    "review",
    "python-conventions",
    "javascript-conventions",
    "agent-conventions",
    "shell-conventions",
    "learn",
    "research",
    "mcp-creator",
    "design",
    "docs-steward",
    "harness-master",
    "skill-creator",
    "security-scanner",
    "devops-engineer",
    "openspec-workflow",
)


def _skill_rows_for_topology() -> list[dict[str, str]]:
    """Prefer first-party teaching skills for architecture progressive-disclosure visuals."""
    index = _skills_catalog_index()
    by_name: dict[str, dict[str, str]] = {}
    custom_rows: list[dict[str, str]] = []
    for entry in _catalog_skill_entries(index):
        name = str(entry.get("name") or entry.get("id") or "")
        if not name:
            continue
        source_kind = str(entry.get("sourceKind") or entry.get("source_kind") or "custom")
        source_type = "curated-external" if source_kind == "curated-external" else "custom"
        row = {
            "name": name,
            "sourceType": source_type,
            "trustTier": str(entry.get("trustTier") or entry.get("trust_tier") or "unknown"),
        }
        by_name[name] = row
        if source_type == "custom":
            custom_rows.append(row)

    teaching: list[dict[str, str]] = []
    for name in _TEACHING_TOPOLOGY_NAMES:
        if name in by_name:
            teaching.append(by_name[name])
    if len(teaching) >= 8:
        return teaching

    # Fall back to sorted custom skills when teaching set is sparse.
    custom_rows.sort(key=lambda r: r["name"])
    return custom_rows[:48]


def _entry_source_type(entry: dict[str, Any]) -> str:
    source_kind = str(entry.get("sourceKind") or entry.get("source_kind") or "custom")
    return "curated-external" if source_kind == "curated-external" else "custom"


def _collect_tag_index(skills_index: dict[str, Any]) -> dict[str, list[str]]:
    by_tag: dict[str, list[str]] = defaultdict(list)
    for entry in _catalog_skill_entries(skills_index):
        name = str(entry.get("name") or "")
        if not name:
            continue
        for tag in entry_catalog_tags(entry):
            by_tag[tag].append(name)
    return dict(sorted(by_tag.items()))


def _collect_tag_index_counts(skills_index: dict[str, Any]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"external": 0, "custom": 0})
    for entry in _catalog_skill_entries(skills_index):
        name = str(entry.get("name") or "")
        if not name:
            continue
        bucket = "external" if _entry_source_type(entry) == "curated-external" else "custom"
        for tag in entry_catalog_tags(entry):
            counts[tag][bucket] += 1
    return dict(sorted(counts.items()))


def _collect_platform_index(skills_index: dict[str, Any]) -> dict[str, list[str]]:
    by_platform: dict[str, list[str]] = defaultdict(list)
    for entry in _catalog_skill_entries(skills_index):
        name = str(entry.get("name") or "")
        if not name:
            continue
        for platform in entry_platforms(entry):
            by_platform[platform].append(name)
    return dict(sorted(by_platform.items()))


def _collect_tooling_index(nodes: list[CatalogNode]) -> dict[str, list[str]]:
    """Group assets by coarse tooling lane (skill / agent / mcp)."""
    lanes: dict[str, list[str]] = {"skills": [], "agents": [], "mcp-servers": []}
    for node in nodes:
        if node.kind == "skill":
            lanes["skills"].append(node.id)
        elif node.kind == "agent":
            lanes["agents"].append(node.id)
        elif node.kind == "mcp":
            lanes["mcp-servers"].append(node.id)
    return {k: sorted(v) for k, v in lanes.items() if v}


def _render_mdx(frontmatter: dict[str, str], body_lines: list[str]) -> str:
    parts = ["---"]
    for key, value in frontmatter.items():
        parts.append(f"{key}: {value}")
    parts.extend(["---", ""])
    parts.extend(body_lines)
    if parts[-1] != "":
        parts.append("")
    return "\n".join(parts)


def _write_mdx(path: Path, frontmatter: dict[str, str], body_lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_render_mdx(frontmatter, body_lines), encoding="utf-8")


def write_catalog_landing(*, writer: MdxWriter = _write_mdx) -> None:
    """Write /catalog/ discovery hub."""
    body = [
        "import { CardGrid, LinkCard } from '@astrojs/starlight/components';",
        "",
        "Unified discovery for skills, agents, MCP servers, and maintainer tooling indexes.",
        "",
        "<CardGrid>",
        '  <LinkCard title="Skills" href="/skills/catalog/" description="Custom + curated external skill catalog." />',
        '  <LinkCard title="Agents" href="/catalog/agents/" description="Portable agent configurations." />',
        '  <LinkCard title="MCP Servers" href="/catalog/mcp/" description="First-party MCP servers in this repo." />',
        '  <LinkCard title="Tags" href="/catalog/tags/" description="Skill catalog grouped by tag." />',
        '  <LinkCard title="Platforms" href="/catalog/platforms/" description="Skills by target harness." />',
        '  <LinkCard title="Tooling" href="/catalog/tooling/" description="Skills, agents, and MCP tooling lanes." />',
        '  <LinkCard title="Architecture" href="/architecture/progressive-disclosure/" '
        'description="Progressive disclosure and instruction loading." />',
        "</CardGrid>",
    ]
    writer(
        CATALOG_CONTENT_DIR / "index.mdx",
        {
            "title": "Catalog",
            "description": "Unified discovery hub for skills, agents, MCP, and maintainer indexes",
        },
        body,
    )


def write_catalog_agents_index(agents: list[CatalogNode], *, writer: MdxWriter = _write_mdx) -> None:
    """Write /catalog/agents/ with links to detail pages under /agents/."""
    body = [
        "import { CardGrid, LinkCard } from '@astrojs/starlight/components';",
        "",
        "Portable agents from `agents/*.md`. Detail pages live under [`/agents/`](/agents/).",
        "",
        '<div class="stats-bar">',
        f'  <span class="stat stat-agent">{len(agents)} agents indexed</span>',
        "</div>",
        "",
        "<CardGrid>",
    ]
    for node in sorted(agents, key=lambda n: n.id):
        desc = escape_attr(truncate_sentence(node.description, 160))
        body.append(
            f'  <LinkCard title="{escape_attr(node.id)}" href="/agents/{node.id}/" description="{desc}" />'
        )
    body.extend(["</CardGrid>"])
    writer(
        CATALOG_CONTENT_DIR / "agents" / "index.mdx",
        {
            "title": "Agent Catalog",
            "description": "Browse portable agent configurations with links to detail pages",
        },
        body,
    )


def write_catalog_mcp_index(mcps: list[CatalogNode], *, writer: MdxWriter = _write_mdx) -> None:
    """Write /catalog/mcp/ with empty-state when no MCP packages exist."""
    body = [
        "import { Aside, CardGrid, LinkCard } from '@astrojs/starlight/components';",
        "",
        "First-party MCP servers authored under `mcp/<name>/`. Detail pages: [`/mcp/`](/mcp/).",
        "",
    ]
    if not mcps:
        body.extend([
            '<Aside type="note" title="No MCP servers yet">',
            "This repository has no first-party MCP packages indexed. Run `wagents new mcp <name>` "
            "to scaffold a server, then `wagents docs generate` to refresh this catalog.",
            "</Aside>",
        ])
    else:
        body.extend([
            '<div class="stats-bar">',
            f'  <span class="stat stat-mcp">{len(mcps)} MCP servers indexed</span>',
            "</div>",
            "",
            "<CardGrid>",
        ])
        for node in sorted(mcps, key=lambda n: n.id):
            desc = escape_attr(truncate_sentence(node.description, 160))
            body.append(
                f'  <LinkCard title="{escape_attr(node.id)}" href="/mcp/{node.id}/" description="{desc}" />'
            )
        body.append("</CardGrid>")
    writer(
        CATALOG_CONTENT_DIR / "mcp" / "index.mdx",
        {
            "title": "MCP Catalog",
            "description": "Browse first-party MCP servers with empty-state when none are registered",
        },
        body,
    )


def write_catalog_tags_index(skills_index: dict[str, Any], *, writer: MdxWriter = _write_mdx) -> None:
    by_tag = _collect_tag_index(skills_index)
    tag_counts = _collect_tag_index_counts(skills_index)
    custom_names = {
        str(e.get("name") or "")
        for e in _catalog_skill_entries(skills_index)
        if _entry_source_type(e) == "custom" and e.get("name")
    }
    body = [
        "import { CardGrid, LinkCard } from '@astrojs/starlight/components';",
        "",
        "Skills grouped by catalog tag from authoring frontmatter / generated index.",
        "",
    ]
    if not by_tag:
        body.append("_No tags indexed yet. Add `tags` to skill authoring MDX or catalog index entries._")
    else:
        body.append("<CardGrid>")
        for tag, skill_ids in by_tag.items():
            sample = ", ".join(skill_ids[:4])
            if len(skill_ids) > 4:
                sample += f", +{len(skill_ids) - 4} more"
            counts = tag_counts.get(tag, {"external": 0, "custom": 0})
            total = len(skill_ids)
            description = (
                f"{total} skills ({counts['external']} external, {counts['custom']} custom) — e.g. {sample}"
            )
            href = f"/skills/catalog/external/?tag={quote(tag, safe='')}"
            body.append(
                f'  <LinkCard title="{escape_attr(tag)}" href="{href}" '
                f'description="{escape_attr(description)}" />'
            )
        if custom_names:
            desc = f"{len(custom_names)} custom skills in the catalog (browse custom hub)"
            body.append(
                f'  <LinkCard title="Custom skills" href="/skills/catalog/custom/" '
                f'description="{escape_attr(desc)}" />'
            )
        body.append("</CardGrid>")
    writer(
        CATALOG_CONTENT_DIR / "tags" / "index.mdx",
        {"title": "Catalog Tags", "description": "Skill catalog grouped by tag"},
        body,
    )


def write_catalog_platforms_index(skills_index: dict[str, Any], *, writer: MdxWriter = _write_mdx) -> None:
    by_platform = _collect_platform_index(skills_index)
    harness_labels = _load_harness_labels()
    custom_names = {
        str(e.get("name") or "")
        for e in _catalog_skill_entries(skills_index)
        if _entry_source_type(e) == "custom" and e.get("name")
    }
    body = [
        "import { CardGrid, LinkCard } from '@astrojs/starlight/components';",
        "",
        "Skills grouped by `target_agents` / harness from the generated catalog index.",
        "",
        "<CardGrid>",
    ]
    if not by_platform:
        for _hid, label in sorted(harness_labels.items()):
            body.append(
                f'  <LinkCard title="{escape_attr(label)}" href="/harness-support/" '
                f'description="Harness support matrix — no indexed skills tagged yet." />'
            )
    else:
        for platform, skill_ids in by_platform.items():
            label = harness_labels.get(platform, platform)
            external_count = sum(
                1
                for entry in _catalog_skill_entries(skills_index)
                if str(entry.get("name") or "") in skill_ids
                and _entry_source_type(entry) == "curated-external"
                and platform in entry_platforms(entry)
            )
            custom_count = len(skill_ids) - external_count
            href = f"/skills/catalog/external/?platform={quote(platform, safe='')}"
            description = (
                f"{len(skill_ids)} skills ({external_count} external, {custom_count} custom) for {platform}"
            )
            body.append(
                f'  <LinkCard title="{escape_attr(label)}" href="{href}" '
                f'description="{escape_attr(description)}" />'
            )
    # Hub companion even when by_platform is empty (customs with no targetAgents).
    if custom_names:
        desc = f"{len(custom_names)} custom skills in the catalog (browse custom hub)"
        body.append(
            f'  <LinkCard title="Custom skills" href="/skills/catalog/custom/" '
            f'description="{escape_attr(desc)}" />'
        )
    body.append("</CardGrid>")
    writer(
        CATALOG_CONTENT_DIR / "platforms" / "index.mdx",
        {
            "title": "Catalog Platforms",
            "description": "Skills indexed by target agent harness",
        },
        body,
    )


def write_catalog_tooling_index(nodes: list[CatalogNode], *, writer: MdxWriter = _write_mdx) -> None:
    lanes = _collect_tooling_index(nodes)
    body = [
        "import { CardGrid, LinkCard } from '@astrojs/starlight/components';",
        "",
        "Coarse tooling lanes for maintainer navigation.",
        "",
        "<CardGrid>",
        f'  <LinkCard title="Skills ({len(lanes.get("skills", []))})" href="/skills/catalog/" '
        'description="Repo-owned + curated external skills." />',
        f'  <LinkCard title="Agents ({len(lanes.get("agents", []))})" href="/catalog/agents/" '
        'description="Portable agent definitions." />',
        f'  <LinkCard title="MCP ({len(lanes.get("mcp-servers", []))})" href="/catalog/mcp/" '
        'description="First-party MCP servers." />',
        '  <LinkCard title="Reports" href="/reports/" description="Generated maintainer observability." />',
        '  <LinkCard title="CLI" href="/cli/" description="wagents command reference." />',
        "</CardGrid>",
    ]
    writer(
        CATALOG_CONTENT_DIR / "tooling" / "index.mdx",
        {"title": "Tooling Index", "description": "Skills, agents, MCP, reports, and CLI lanes"},
        body,
    )


def write_architecture_pages(
    *,
    skill_topology_rows: list[dict[str, str]],
    writer: MdxWriter = _write_mdx,
) -> None:
    """Write progressive-disclosure and instruction-loading architecture pages."""
    topology_import = ""
    topology_block = ""
    if skill_topology_rows:
        topology_import = "import SkillTopology from '../../../components/SkillTopology.astro';"
        topology_block = (
            "<SkillTopology skills={"
            + json.dumps(skill_topology_rows[:96])
            + "} />"
        )

    pd_body = [
        "import { Aside } from '@astrojs/starlight/components';",
        topology_import,
        "",
        "This repository uses **progressive disclosure** so agents load the minimum standing context, "
        "then pull depth on demand via skills, scoped rules, and generated docs.",
        "",
        "## Layers",
        "",
        "| Layer | Owner | Loads when |",
        "| ----- | ----- | ---------- |",
        "| Bundle entry | `AGENTS.md` | Always (points at global + formats) |",
        "| Global instructions | `instructions/global.md` | Always (cross-harness) |",
        "| Platform overlays | `instructions/*-global.md` | Harness-specific bridge |",
        "| Skill descriptions | `skills/*/SKILL.md` frontmatter | Always (descriptions only) |",
        "| Scoped rules | `.claude/rules/`, `.cursor/rules/*.mdc` (independent sets) | Path match |",
        "| Generated mirrors | `.github/instructions/`, `.apm/instructions/`, Copilot home file | Sync / install |",
        "| Skill bodies | `skills/*/SKILL.md` body | Skill invoked |",
        "| Generated docs | `wagents docs generate` | Human browse / MCP docs-index |",
        "",
        "Cursor `.mdc` rules are **not** assumed parity with Claude `.claude/rules/`.",
        "Edit each surface when policy must match.",
        "",
        '<Aside type="tip" title="Token efficacy">',
        "See [Harness config — token efficacy](/harness-config/token-efficacy/) for one-tool-per-layer policy.",
        "</Aside>",
        "",
    ]
    if topology_block:
        pd_body.extend(
            [
                "## Skill topology (teaching sample)",
                "",
                "First-party progressive-disclosure examples (not the full catalog alphabet). "
                "Browse the full inventory in the [Skill Catalog](/skills/catalog/).",
                "",
                topology_block,
                "",
            ]
        )

    writer(
        ARCHITECTURE_CONTENT_DIR / "progressive-disclosure.mdx",
        {
            "title": "Progressive Disclosure",
            "description": "How standing context, skills, rules, and docs layers compose",
        },
        pd_body,
    )

    il_body = [
        "import { Aside } from '@astrojs/starlight/components';",
        "",
        "**Instruction loading** is harness-specific projection of the same canonical sources "
        "(see `AGENTS.md` section 5-6 for the full support matrix):",
        "",
        "| Harness | Entry | Bridge / generated source |",
        "| ------- | ----- | ------------------------ |",
        "| Claude Code | `CLAUDE.md` | `@AGENTS.md` → `@instructions/global.md` |",
        "| Codex | `AGENTS.md` | `@instructions/global.md`; overlay `instructions/codex-global.md` |",
        "| Crush | `AGENTS.md` | `@instructions/global.md` |",
        "| OpenCode | `AGENTS.md` | `@instructions/global.md`; overlay `instructions/opencode-global.md` |",
        "| Cursor | `AGENTS.md` | `@instructions/global.md` + `.cursor/rules/*.mdc` |",
        "| Grok Build | `AGENTS.md` | `@instructions/global.md`; bridge `instructions/grok-global.md` "
        "(config tomls are policy/MCP, not the instruction entry) |",
        "| Cherry Studio | MCP-only | MCPHub registry; no dedicated instruction bridge |",
        "| LM Studio | presets + optional skills | `instructions/lm-studio-global.md` + home MCP/presets |",
        "",
        "Platform overlays may add runtime guidance but must not weaken safety or secret-handling rules.",
        "",
        '<Aside type="caution" title="Generated vs hand-authored">',
        "Regenerate mirrors with `uv run python scripts/sync_agent_stack.py --apply --targets repo` "
        "after editing canonical instruction sources.",
        "</Aside>",
        "",
        "## Maintainer loop",
        "",
        "1. Edit `instructions/global.md` or platform overlay.",
        "2. Run stack sync for harness mirrors.",
        "3. Run `uv run wagents validate` and `uv run wagents docs generate --check`.",
    ]
    writer(
        ARCHITECTURE_CONTENT_DIR / "instruction-loading.mdx",
        {
            "title": "Instruction Loading",
            "description": "Harness entrypoints and sync for cross-platform instructions",
        },
        il_body,
    )


def write_catalog_pages(*, nodes: list[CatalogNode] | None = None, writer: MdxWriter = _write_mdx) -> None:
    """Generate all W5 catalog and architecture pages."""
    nodes = nodes if nodes is not None else collect_nodes()
    agents = [n for n in nodes if n.kind == "agent"]
    mcps = [n for n in nodes if n.kind == "mcp"]
    skills_index = _skills_catalog_index()
    topology_rows = _skill_rows_for_topology()

    write_catalog_landing(writer=writer)
    write_catalog_agents_index(agents, writer=writer)
    write_catalog_mcp_index(mcps, writer=writer)
    write_catalog_tags_index(skills_index, writer=writer)
    write_catalog_platforms_index(skills_index, writer=writer)
    write_catalog_tooling_index(nodes, writer=writer)
    write_architecture_pages(skill_topology_rows=topology_rows, writer=writer)


def render_catalog_page_artifacts(*, nodes: list[CatalogNode] | None = None) -> dict[Path, str]:
    """Return generated catalog/architecture page contents without writing files."""
    artifacts: dict[Path, str] = {}

    def capture(path: Path, frontmatter: dict[str, str], body_lines: list[str]) -> None:
        artifacts[path] = _render_mdx(frontmatter, body_lines)

    write_catalog_pages(nodes=nodes, writer=capture)
    return artifacts


def catalog_sidebar_entries() -> list[str]:
    """Return sidebar module lines for catalog + architecture groups."""
    lines = [
        "  {",
        "    label: 'Catalog',",
        "    collapsed: true,",
        "    items: [",
        "      { slug: 'catalog', label: 'Overview' },",
        "      { slug: 'catalog/agents', label: 'Agents' },",
        "      { slug: 'catalog/mcp', label: 'MCP' },",
        "      { slug: 'catalog/tags', label: 'Tags' },",
        "      { slug: 'catalog/platforms', label: 'Platforms' },",
        "      { slug: 'catalog/tooling', label: 'Tooling' },",
        "    ],",
        "  },",
        "  {",
        "    label: 'Architecture',",
        "    collapsed: true,",
        "    items: [",
        "      { slug: 'architecture/progressive-disclosure', label: 'Progressive disclosure' },",
        "      { slug: 'architecture/instruction-loading', label: 'Instruction loading' },",
        "    ],",
        "  },",
    ]
    return lines  # noqa: RET504 — sidebar fragment list built incrementally
