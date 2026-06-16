"""MDX escaping and page renderers for skills, agents, and MCP servers."""

import json
import re
from pathlib import Path

import typer
import yaml

from wagents import CONTENT_DIR, GITHUB_BASE, ROOT
from wagents.catalog import RELATED_SKILLS, CatalogEdge, CatalogNode
from wagents.parsing import (
    FenceTracker,
    escape_attr,
    is_navigable_catalog_link_target,
    process_outside_fences,
    sanitize_catalog_links,
    shift_headings,
    truncate_sentence,
)
from wagents.site_model import (
    LOCAL_INSTALLED_SOURCE_LABEL,
    REPO_SOURCE,
    SUPPORTED_AGENT_IDS,
    build_install_command,
    resolve_trust_tier_for_node,
    trust_badge_for_tier,
)
from wagents.skill_docs import skill_detail_href
from wagents.skill_research import load_skill_research

# ---------------------------------------------------------------------------
# MDX escaper
# ---------------------------------------------------------------------------


def escape_mdx(body: str) -> str:
    """Escape markdown body for safe MDX embedding."""
    return process_outside_fences(body, escape_mdx_line)


def escape_mdx_line(line: str) -> str:
    """Escape a single MDX line, preserving inline code spans."""
    if line.startswith("import ") or line.startswith("export "):
        return "\\" + line

    # Normalize markdown-escaped angle brackets from upstream SKILL sources.
    line = re.sub(r"\\([<>])", r"\1", line)

    # Find all inline code span ranges
    code_ranges = []
    i = 0
    while i < len(line):
        if line[i] == "`":
            bt_start = i
            bt_count = 0
            while i < len(line) and line[i] == "`":
                bt_count += 1
                i += 1
            close_idx = line.find("`" * bt_count, i)
            if close_idx != -1:
                code_ranges.append((bt_start, close_idx + bt_count))
                i = close_idx + bt_count
        else:
            i += 1

    def in_code(pos):
        return any(s <= pos < e for s, e in code_ranges)

    out = []
    i = 0
    while i < len(line):
        if in_code(i):
            if line[i] == "|":
                out.append("\\|")
            elif line[i] == "<":
                out.append("&lt;")
            elif line[i] == ">":
                out.append("&gt;")
            else:
                out.append(line[i])
            i += 1
            continue
        if line[i : i + 4] == "<!--":
            end = line.find("-->", i + 4)
            if end != -1:
                content = line[i + 4 : end].strip()
                out.append("{/* " + content + " */}")
                i = end + 3
                continue
        if line[i] in "{}":
            out.append("\\" + line[i])
            i += 1
            continue
        if line[i] == "<":
            out.append("&lt;")
            i += 1
            continue
        if line[i] == ">":
            out.append("&gt;")
            i += 1
            continue
        out.append(line[i])
        i += 1

    return "".join(out)


# ---------------------------------------------------------------------------
# Page renderers
# ---------------------------------------------------------------------------


def render_tabs(tab_items: list[tuple[str, str]]) -> list[str]:
    """Render a list of (label, content) pairs as MDX Tabs or a single heading."""
    parts: list[str] = []
    if not tab_items:
        return parts
    if len(tab_items) == 1:
        label, content = tab_items[0]
        parts.append(f"### {label}")
        parts.append("")
        parts.append(content)
        parts.append("")
    else:
        parts.append("<Tabs>")
        for label, content in tab_items:
            parts.append(f'  <TabItem label="{label}">')
            parts.append(content)
            parts.append("  </TabItem>")
        parts.append("</Tabs>")
        parts.append("")
    return parts


def render_page(node: CatalogNode, edges: list[CatalogEdge], all_nodes: list[CatalogNode]) -> str:
    """Render a CatalogNode to MDX string."""
    if node.kind == "skill":
        return render_skill_page(node, edges, all_nodes)
    elif node.kind == "agent":
        return render_agent_page(node, edges, all_nodes)
    elif node.kind == "mcp":
        return render_mcp_page(node, edges, all_nodes)
    return ""


def scaffold_doc_page(node: CatalogNode) -> None:
    """Create a single docs page for a newly scaffolded asset."""
    if not CONTENT_DIR.exists():
        return
    if node.kind == "skill":
        page_dir = CONTENT_DIR / "skills" / "catalog"
    else:
        page_dir = CONTENT_DIR / (node.kind + "s" if node.kind != "mcp" else "mcp")
    page_dir.mkdir(parents=True, exist_ok=True)
    content = render_page(node, [], [node])
    (page_dir / f"{node.id}.mdx").write_text(content)
    rel = page_dir.relative_to(ROOT) / f"{node.id}.mdx"
    typer.echo(f"Created {rel}")


def safe_outer_fence(content: str) -> str:
    """Return a backtick fence longer than any fence inside *content*."""
    max_fence = 3
    for line in content.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fence_len = len(stripped) - len(stripped.lstrip(stripped[0]))
            max_fence = max(max_fence, fence_len)
    return "`" * (max_fence + 1)


def _resolve_raw_path(node: CatalogNode) -> Path:
    """Resolve the on-disk path for a catalog node's source file."""
    raw = Path(node.source_path)
    if node.source == "custom" or not raw.is_absolute():
        return ROOT / node.source_path
    return raw


def read_raw_content(node: CatalogNode) -> str:
    """Read the raw file content for a CatalogNode from disk."""
    raw_path = _resolve_raw_path(node)
    try:
        return raw_path.read_text()
    except Exception:
        # Fallback: reconstruct from parsed data
        raw_lines = ["---"]
        for key, value in node.metadata.items():
            raw_lines.append(yaml.dump({key: value}, default_flow_style=False).strip())
        raw_lines.append("---")
        if node.body:
            raw_lines.append("")
            raw_lines.append(node.body)
        return "\n".join(raw_lines)


def _display_source_path(node: CatalogNode) -> str:
    """Format a source path for display in docs pages."""
    path = str(node.source_path)
    if node.source != "custom" and _is_local_path_like(path):
        return LOCAL_INSTALLED_SOURCE_LABEL
    home = str(Path.home())
    if path.startswith(home):
        return "~" + path[len(home) :]
    return path


def _is_local_path_like(value: str) -> bool:
    path = str(value or "").strip()
    if path.startswith(("http://", "https://", "github:")):
        return False
    if path.startswith(("~/", "$HOME/", "/Users/", "/home/", "/private/", "/tmp/")):
        return True
    return Path(path).is_absolute()


def _contains_local_path(value: str) -> bool:
    return any(marker in str(value or "") for marker in ("/Users/", "/home/", "/private/", "/tmp/", "~/"))


def _installed_install_command(node: CatalogNode) -> str:
    metadata = node.metadata if isinstance(node.metadata, dict) else {}
    command = str(metadata.get("_skills_install_command") or "").strip()
    if command and not _contains_local_path(command):
        return command
    source = str(metadata.get("_skills_install_source") or metadata.get("_skills_source") or "").strip()
    if not source or _is_local_path_like(source):
        return ""
    return f"npx skills add {source} --skill {node.id} -y -g"


def _skill_display_source(node: CatalogNode) -> str:
    if node.source == "custom":
        return REPO_SOURCE
    metadata = node.metadata if isinstance(node.metadata, dict) else {}
    source = str(metadata.get("_skills_source") or metadata.get("_skills_install_source") or node.source_path).strip()
    if not source or _is_local_path_like(source):
        return LOCAL_INSTALLED_SOURCE_LABEL
    return source


def _skill_source_kind(node: CatalogNode) -> str:
    source = _skill_display_source(node)
    if node.source == "custom" or source == REPO_SOURCE:
        return "repo"
    if source == LOCAL_INSTALLED_SOURCE_LABEL:
        return "local-inventory"
    if source.startswith("github:") or re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", source):
        return "github"
    if source.startswith(("http://", "https://")):
        return "url"
    return "external"


def _skill_public_metadata_rows(node: CatalogNode) -> list[str]:
    if node.source == "curated-external":
        source_type = "curated-external"
        display_source = _skill_display_source(node)
        install_command = _installed_install_command(node)
        install_state = "portable command" if install_command else "local inventory only"
        review_state = "curated"
        fm = node.metadata if isinstance(node.metadata, dict) else {}
        target_list = fm.get("_skills_target_agents") or []
        targets = ", ".join(f"`{agent}`" for agent in target_list) if target_list else ""
        trust_tier = resolve_trust_tier_for_node(node)
        rows = [
            f"| Source Type | `{source_type}` |",
            f"| Display Source | `{escape_mdx_line(display_source)}` |",
            f"| Source Kind | `{_skill_source_kind(node)}` |",
            f"| Installability | {install_state} |",
            f"| Review State | {review_state} |",
            f"| Trust Tier | `{trust_tier}` |",
        ]
        if targets:
            rows.append(f"| Target Agents | {targets} |")
        return rows

    source_type = "repo-owned" if node.source == "custom" else "installed-external"
    display_source = _skill_display_source(node)
    install_command = (
        build_install_command(skill=node.id) if node.source == "custom" else _installed_install_command(node)
    )
    install_state = "portable command" if install_command else "local inventory only"
    review_state = "reviewed" if node.source == "custom" else "local inventory"
    targets = ", ".join(f"`{agent}`" for agent in SUPPORTED_AGENT_IDS) if node.source == "custom" else ""
    rows = [
        f"| Source Type | `{source_type}` |",
        f"| Display Source | `{escape_mdx_line(display_source)}` |",
        f"| Source Kind | `{_skill_source_kind(node)}` |",
        f"| Installability | {install_state} |",
        f"| Review State | {review_state} |",
    ]
    if targets:
        rows.append(f"| Target Agents | {targets} |")
    return rows


def _sanitize_what_it_does(text: str) -> str:
    """Drop summary text that would break MDX when embedded as prose."""
    stripped = text.strip()
    if not stripped:
        return ""
    if "```" in stripped:
        return ""
    if "import {" in stripped:
        return ""
    if re.search(r"</?[A-Za-z][^>]*>", stripped):
        return ""
    if re.search(r"\]\(#", stripped):
        return ""
    if re.match(r"^#{1,6}\s", stripped):
        return ""
    if "## Contents" in stripped or stripped.lower().startswith("## contents"):
        return ""
    if stripped.count("|") >= 4:
        return ""
    return stripped


def _extract_what_it_does(body: str) -> str:
    """Return the first prose paragraph after the H1, excluding subheadings and tables."""
    if not body:
        return ""

    lines = body.split("\n")
    past_h1 = False
    para_lines: list[str] = []
    fence = FenceTracker()

    for line in lines:
        fence.update(line)
        if fence.inside_fence:
            if para_lines:
                break
            continue

        stripped = line.strip()
        if not past_h1:
            if stripped.startswith("# ") and not stripped.startswith("## "):
                past_h1 = True
            continue

        if not stripped:
            if para_lines:
                break
            continue
        if re.match(r"^#{1,6}\s", stripped):
            if para_lines:
                break
            continue
        if stripped.startswith("|"):
            if para_lines:
                break
            continue

        para_lines.append(stripped)

    return _sanitize_what_it_does(" ".join(para_lines))


def _section_is_link_heavy(content: str) -> bool:
    """True when most markdown links in a section point at non-navigable relative paths."""
    links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
    if not links:
        return False
    relative = sum(1 for _, target in links if not is_navigable_catalog_link_target(target))
    return relative / len(links) > 0.5


def _catalog_prose(text: str) -> str:
    return sanitize_catalog_links(escape_mdx(text), fence_aware=True)


def _extract_body_sections(body: str) -> dict[str, str]:
    """Extract named sections from SKILL.md body.

    Returns a dict mapping section heading (lowercase) to section content
    (everything after the heading until the next ## heading or end of body).
    Skips the first H1 heading and the Dispatch section (handled separately).
    """
    sections: dict[str, str] = {}
    if not body:
        return sections

    lines = body.split("\n")
    current_heading = ""
    current_lines: list[str] = []
    fence = FenceTracker()

    for line in lines:
        fence.update(line)
        if fence.inside_fence:
            current_lines.append(line)
            continue
        stripped = line.strip()
        if stripped.startswith("## "):
            # Save previous section
            if current_heading:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = stripped[3:].strip().lower()
            current_lines = []
        elif stripped.startswith("# ") and not current_heading:
            # Skip the first H1 heading
            continue
        else:
            current_lines.append(line)

    # Save last section
    if current_heading:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


# Sections from SKILL.md body to render inline on docs pages.
# Excludes dispatch (handled separately), references, canonical vocabulary, and
# sections that are too implementation-specific for a docs audience.
_RENDERABLE_SECTIONS = {
    "tooling",
    "preferred libraries",
    "project structure",
    "package management",
    "tooling preferences",
    "conventions",
    "when to propose updates",
    "routing",
    "verification checklist",
    "critical rules",
    "skill development",
    "audit",
    "audit all",
    "audit and quality",
    "package",
    "core principles",
    "auto-detection heuristic",
    "quick start",
}

# Sections to skip entirely — they are redundant with the docs structure
_SKIP_SECTIONS = {
    "dispatch",
    "references",
    "reference file index",
    "canonical vocabulary",
    "hooks",
    "state management",
    "gallery (empty arguments)",
    "dashboard",
}


def _parse_research_sections(body: str) -> dict[str, str]:
    """Extract ##-headed sections from a research body for structured H2 rendering.

    Preserves original heading casing. Skips leading H1. Used for curated-external
    enrichment so research appears as native page sections (not a single Aside).
    """
    sections: dict[str, str] = {}
    if not body:
        return sections

    lines = body.split("\n")
    current_heading = ""
    current_lines: list[str] = []
    fence = FenceTracker()

    for line in lines:
        fence.update(line)
        if fence.inside_fence:
            current_lines.append(line)
            continue
        stripped = line.strip()
        if stripped.startswith("## "):
            if current_heading:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = stripped[3:].strip()
            current_lines = []
        elif stripped.startswith("# ") and not current_heading:
            # Skip the first H1 heading
            continue
        else:
            current_lines.append(line)

    if current_heading:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def _render_curated_harness_section(node: CatalogNode) -> list[str]:
    """Render a Harness Coverage H2 section for curated-external (stub) skills.

    Pulls verified target harnesses from _skills_target_agents metadata and the
    portable install command when present.
    """
    fm = node.metadata if isinstance(node.metadata, dict) else {}
    target_agents = fm.get("_skills_target_agents") or []
    install_cmd = _installed_install_command(node)
    parts: list[str] = []
    parts.append("## Harness Coverage")
    parts.append("")
    if target_agents:
        listed = ", ".join(f"`{a}`" for a in target_agents)
        parts.append(f"Targets verified harnesses: {listed}.")
    else:
        parts.append("Targets all supported agent harnesses via the install command below.")
    if install_cmd:
        parts.append("")
        parts.append("**Portable multi-harness install command:**")
        parts.append("```bash")
        parts.append(install_cmd)
        parts.append("```")
    parts.append("")
    return parts


def _render_curated_trust_section(node: CatalogNode) -> list[str]:
    """Render a Trust / Audit H2 section for curated-external skills.

    Uses the shared resolve_trust_tier_for_node + trust_badge_for_tier so the
    rendered page matches the site index badges/rows.
    """
    trust_tier = resolve_trust_tier_for_node(node)
    badge_text, _ = trust_badge_for_tier(trust_tier)
    fm = node.metadata if isinstance(node.metadata, dict) else {}
    status = fm.get("_curated_status") or ""
    risk = fm.get("_risk_notes") or ""
    parts: list[str] = []
    parts.append("## Trust / Audit")
    parts.append("")
    parts.append(f"Trust tier: **{escape_mdx_line(badge_text)}** (`{trust_tier}`)")
    if status:
        parts.append("")
        parts.append(f"Curated status: `{escape_mdx_line(str(status))}`")
    if risk:
        parts.append("")
        parts.append(f"Risk notes: {escape_mdx_line(_sanitize_what_it_does(str(risk)))}")
    parts.append("")
    parts.append(
        "Entry maintained in `config/external-skills.md`; provenance and audit notes are "
        "authoritative there (research context is advisory)."
    )
    parts.append("")
    return parts


def render_skill_page(node: CatalogNode, edges: list[CatalogEdge], all_nodes: list[CatalogNode]) -> str:
    fm = node.metadata
    parts = []

    is_stub = bool(node.metadata.get("_is_stub"))
    raw_content = read_raw_content(node) if not is_stub else ""

    # Frontmatter
    parts.append("---")
    parts.append(f'title: "{node.id}"')
    parts.append(f'description: "{escape_attr(truncate_sentence(node.description, 200))}"')
    parts.append("---")
    parts.append("")

    # Imports
    parts.append(
        "import { Badge, Tabs, TabItem, Card, CardGrid, LinkCard, Aside, Steps } from '@astrojs/starlight/components';"
    )
    parts.append("")

    # === TIER 1: Human summary ===

    # Badge row — standardized: always show name + word count
    badges = []
    badges.append(f'<Badge text="{escape_attr(node.id)}" variant="note" />')
    word_count = len(node.body.split()) if node.body else 0
    badges.append(f'<Badge text="{word_count} words" variant="default" />')
    if fm.get("license"):
        badges.append(f'<Badge text="{escape_attr(fm["license"])}" variant="success" />')
    meta = fm.get("metadata", {})
    if isinstance(meta, dict):
        if meta.get("version"):
            badges.append(f'<Badge text="v{escape_attr(str(meta["version"]))}" variant="success" />')
        if meta.get("author"):
            badges.append(f'<Badge text="{escape_attr(meta["author"])}" variant="caution" />')
    if fm.get("model"):
        badges.append(f'<Badge text="{escape_attr(fm["model"])}" variant="tip" />')
    # Emit single trust badge from site_model mapping (replaces legacy Custom/Curated/Installed)
    trust_tier = resolve_trust_tier_for_node(node)
    trust_badge, trust_badge_variant = trust_badge_for_tier(trust_tier)
    badges.append(f'<Badge text="{escape_attr(trust_badge)}" variant="{trust_badge_variant}" />')
    if node.source == "curated-external":
        curated_status = str(node.metadata.get("_curated_status") or "")
        if curated_status:
            badges.append(f'<Badge text="{escape_attr(curated_status)}" variant="default" />')
    parts.append(" ".join(badges))
    parts.append("")

    # Description
    parts.append(f"> {escape_mdx(node.description)}")
    parts.append("")

    # Quick Start box
    parts.append('<div class="quick-start">')
    parts.append("")
    parts.append("### Quick Start")
    parts.append("")
    parts.append("**Install:**")
    if node.source == "custom":
        parts.append("```bash")
        parts.append(build_install_command(skill=node.id))
        parts.append("```")
    else:
        install_command = _installed_install_command(node)
        if install_command:
            parts.append("```bash")
            parts.append(install_command)
            parts.append("```")
        else:
            parts.append("Discovered from local installed inventory; no portable install command is recorded.")
    parts.append("")
    use_line = f"**Use:** `/{node.id}`"
    if fm.get("argument-hint"):
        use_line += f" `{fm['argument-hint']}`"
    parts.append(use_line)
    parts.append("")
    parts.append("</div>")
    parts.append("")
    parts.append(
        "Works with "
        "[Claude Code](https://docs.anthropic.com/en/docs/claude-code), "
        "[Gemini CLI](https://github.com/google-gemini/gemini-cli), "
        "[OpenCode](https://github.com/anomalyco/opencode), "
        "and other "
        "[agentskills.io](https://agentskills.io)-compatible agents."
    )
    parts.append("")

    research_body = load_skill_research(node.id)
    is_enriched_stub = bool(node.source == "curated-external" and node.metadata.get("_is_stub") and research_body)

    parts.append('<Aside type="note" title="Source & provenance">')
    if node.source == "custom":
        parts.append(
            "This page is generated from the repository file "
            f"`{escape_mdx_line(_display_source_path(node))}` by `wagents docs generate`."
        )
    elif node.source == "curated-external":
        parts.append(
            "This page is generated from curated config "
            f"(`{escape_mdx_line(_display_source_path(node))}`) and local inventory when installed."
        )
        if node.metadata.get("_is_stub"):
            if is_enriched_stub:
                parts.append(
                    " Enriched from research cache (stub); the upstream SKILL.md body is not present locally."
                    " Re-run `uv run wagents docs research --skill "
                    f"{node.id}` to refresh."
                )
            else:
                parts.append(
                    " SKILL.md is not available locally; install the skill or run "
                    f"`uv run wagents docs research --skill {node.id}` to refresh research context."
                )
    else:
        parts.append(f"This page is generated from `{escape_mdx_line(_display_source_path(node))}`.")
    parts.append("</Aside>")
    parts.append("")

    if node.source == "curated-external":
        # For curated-external show dedicated harness + trust/audit sections plus
        # structured research H2s (never collapse research into a single Aside).
        parts.extend(_render_curated_harness_section(node))
        parts.extend(_render_curated_trust_section(node))
        if research_body:
            research_sections = _parse_research_sections(research_body)
            skip_headings = {"Harness Coverage", "Trust And Risks", "Trust / Audit"}
            for heading, content in research_sections.items():
                if heading in skip_headings or not content or not content.strip():
                    continue
                parts.append(f"## {heading}")
                parts.append("")
                parts.append(_catalog_prose(content))
                parts.append("")
    elif research_body:
        parts.append('<Aside type="note" title="Research context (evidence, not authority)">')
        parts.append(_catalog_prose(research_body))
        parts.append("</Aside>")
        parts.append("")

    # Guide cross-link — check if a hand-maintained guide page exists
    guide_path = CONTENT_DIR / "guides" / f"{node.id}.mdx"
    if guide_path.exists():
        desc = "Architecture, research sources, framework catalog, design decisions, and roadmap."
        parts.append(f'<LinkCard title="Full Guide: {node.id}" href="/guides/{node.id}/" description="{desc}" />')
        parts.append("")

    what_it_does = _extract_what_it_does(node.body) if node.body else ""
    if what_it_does:
        parts.append("## What It Does")
        parts.append("")
        parts.append(_catalog_prose(what_it_does))
        parts.append("")

    # Auto-invoke aside for convention skills
    is_auto_invoke = fm.get("user-invocable") is False
    if is_auto_invoke:
        parts.append('<Aside type="note">')
        parts.append(
            "This is an **auto-invoke** skill -- it activates automatically "
            "when the agent detects relevant context. "
            "It is not visible in the `/` slash command menu."
        )
        parts.append("</Aside>")
        parts.append("")

    # Extract dispatch table if present
    dispatch_table = ""
    if node.body:
        body_lines = node.body.split("\n")
        table_lines = []
        in_table = False
        for bl in body_lines:
            if "|" in bl and ("$ARGUMENTS" in bl or "\\$ARGUMENTS" in bl):
                in_table = True
            if in_table:
                if bl.strip().startswith("|"):
                    table_lines.append(bl)
                elif bl.strip() == "":
                    if table_lines:
                        break
                else:
                    if table_lines:
                        break
        # Include the header row before the $ARGUMENTS row
        if table_lines:
            for i, bl in enumerate(body_lines):
                if bl == table_lines[0]:
                    header_idx = i - 2 if i >= 2 and body_lines[i - 1].strip().startswith("|") else i - 1
                    if header_idx >= 0 and body_lines[header_idx].strip().startswith("|"):
                        prefix = []
                        for j in range(header_idx, i):
                            if body_lines[j].strip().startswith("|"):
                                prefix.append(body_lines[j])
                        table_lines = prefix + table_lines
                    break
            dispatch_table = "\n".join(table_lines)

    if dispatch_table:
        parts.append("## Modes")
        parts.append("")
        parts.append(_catalog_prose(dispatch_table))
        parts.append("")

    # Extract and render additional body sections for richer docs pages
    body_sections = _extract_body_sections(node.body) if node.body else {}
    for section_key, section_content in body_sections.items():
        if (
            section_key in _SKIP_SECTIONS
            or section_key not in _RENDERABLE_SECTIONS
            or not section_content.strip()
        ):
            continue
        if (
            node.source != "custom"
            and section_key == "routing"
            and _section_is_link_heavy(section_content)
        ):
            continue
        # Use the original casing from the body for the heading
        heading = section_key.title()
        parts.append(f"## {heading}")
        parts.append("")
        parts.append(_catalog_prose(section_content))
        parts.append("")

    # Tabbed metadata (with single-tab fix)
    tab_items = []

    # Public metadata tab
    tab_items.append(
        (
            "Public Metadata",
            "| Field | Value |\n| ----- | ----- |\n" + "\n".join(_skill_public_metadata_rows(node)),
        )
    )

    # General tab
    general_rows = []
    if fm.get("name"):
        general_rows.append(f"| Name | `{fm['name']}` |")
    if fm.get("license"):
        general_rows.append(f"| License | {fm['license']} |")
    if isinstance(meta, dict) and meta.get("version"):
        general_rows.append(f"| Version | {meta['version']} |")
    if isinstance(meta, dict) and meta.get("author"):
        general_rows.append(f"| Author | {meta['author']} |")
    if general_rows:
        tab_items.append(
            (
                "General",
                "| Field | Value |\n| ----- | ----- |\n" + "\n".join(general_rows),
            )
        )

    # Claude Code tab
    cc_rows = []
    if fm.get("model"):
        cc_rows.append(f"| Model | `{fm['model']}` |")
    if fm.get("context"):
        cc_rows.append(f"| Context | `{fm['context']}` |")
    if fm.get("agent"):
        cc_rows.append(f"| Agent | `{fm['agent']}` |")
    if fm.get("argument-hint"):
        # Replace angle brackets — MDX parses <word> as JSX inside TabItem
        _hint = fm["argument-hint"].replace("<", "[").replace(">", "]")
        cc_rows.append(f"| Argument Hint | `{_hint}` |")
    if fm.get("user-invocable") is False:
        cc_rows.append("| User Invocable | No |")
    if fm.get("disable-model-invocation"):
        cc_rows.append("| Disable Model Invocation | Yes |")
    if cc_rows:
        tab_items.append(
            (
                "Claude Code",
                "| Field | Value |\n| ----- | ----- |\n" + "\n".join(cc_rows),
            )
        )

    # Compatibility tab
    compat_rows = []
    if fm.get("compatibility"):
        compat_rows.append(f"| Compatibility | {fm['compatibility']} |")
    if fm.get("allowed-tools"):
        compat_rows.append(f"| Allowed Tools | `{fm['allowed-tools']}` |")
    if compat_rows:
        tab_items.append(
            (
                "Compatibility",
                "| Field | Value |\n| ----- | ----- |\n" + "\n".join(compat_rows),
            )
        )

    parts.extend(render_tabs(tab_items))

    # Cross-links (Used By)
    related_edges = [e for e in edges if e.to_id == f"skill:{node.id}"]
    if related_edges:
        parts.append("## Used By")
        parts.append("")
        parts.append("<CardGrid>")
        for edge in related_edges:
            agent_id = edge.from_id.split(":")[1]
            agent_node = next((n for n in all_nodes if n.kind == "agent" and n.id == agent_id), None)
            if agent_node:
                desc = escape_attr(truncate_sentence(agent_node.description, 160))
                parts.append(
                    f'  <LinkCard title="{escape_attr(agent_id)}" href="/agents/{agent_id}/" description="{desc}" />'
                )
        parts.append("</CardGrid>")
        parts.append("")

    # Related Skills
    related = RELATED_SKILLS.get(node.id, [])
    if related:
        parts.append("## Related Skills")
        parts.append("")
        parts.append("<CardGrid>")
        for rel_id in related:
            rel_node = next((n for n in all_nodes if n.kind == "skill" and n.id == rel_id), None)
            if rel_node:
                desc = escape_attr(truncate_sentence(rel_node.description, 160))
                href = skill_detail_href(rel_id)
                title = escape_attr(rel_id)
                parts.append(
                    f'  <LinkCard title="{title}" href="{href}" description="{desc}" />'
                )
        parts.append("</CardGrid>")
        parts.append("")

    # === TIER 2: Copyable asset preview ===
    # Skills show raw SKILL.md behind a disclosure widget (install-and-use artifacts).
    # Agents show system prompts inline (read-to-understand artifacts). This is intentional.
    if not is_stub:
        outer_fence = safe_outer_fence(raw_content)
        parts.append("<details>")
        parts.append("<summary>View Full SKILL.md</summary>")
        parts.append("")
        parts.append(f'{outer_fence}yaml title="SKILL.md"')
        parts.append(raw_content)
        parts.append(outer_fence)
        parts.append("")
        if node.source == "custom":
            parts.append(
                f"[Download from GitHub](https://raw.githubusercontent.com/wyattowalsh/agents/main/{node.source_path})"
            )
            parts.append("")
        parts.append("</details>")
        parts.append("")

    # Resources
    parts.append("## Resources")
    parts.append("")
    parts.append("<CardGrid>")
    parts.append('  <LinkCard title="All Skills" href="/skills/" description="Browse the full skill catalog." />')
    parts.append('  <LinkCard title="CLI Reference" href="/cli/" description="Install and manage skills." />')
    if node.source == "custom":
        parts.append(
            '  <LinkCard title="agentskills.io"'
            ' href="https://agentskills.io"'
            ' description="The open ecosystem for'
            ' cross-agent skills." />'
        )
    parts.append("</CardGrid>")
    parts.append("")

    # Source link (only for custom skills)
    if node.source == "custom":
        parts.append("---")
        parts.append(f"[View source on GitHub]({GITHUB_BASE}/{node.source_path})")
        parts.append("")

    return "\n".join(parts)


def render_agent_page(node: CatalogNode, edges: list[CatalogEdge], all_nodes: list[CatalogNode]) -> str:
    fm = node.metadata
    parts = []
    raw_content = read_raw_content(node)

    # Frontmatter
    parts.append("---")
    parts.append(f'title: "{node.id}"')
    parts.append(f'description: "{escape_attr(truncate_sentence(node.description, 200))}"')
    parts.append("---")
    parts.append("")

    # Imports
    parts.append(
        "import { Badge, Tabs, TabItem, Card, CardGrid, LinkCard, Aside } from '@astrojs/starlight/components';"
    )
    parts.append("")

    # Badge row
    badges = []
    badges.append('<Badge text="Agent Config" variant="note" />')
    if fm.get("model") and fm["model"] != "inherit":
        badges.append(f'<Badge text="{escape_attr(fm["model"])}" variant="tip" />')
    if fm.get("permissionMode") and fm["permissionMode"] != "default":
        badges.append(f'<Badge text="{escape_attr(fm["permissionMode"])}" variant="caution" />')
    if isinstance(fm.get("skills"), list):
        badges.append(f'<Badge text="{len(fm.get("skills", []))} skills" variant="default" />')
    if isinstance(fm.get("mcpServers"), list):
        badges.append(f'<Badge text="{len(fm.get("mcpServers", []))} MCP servers" variant="default" />')
    if badges:
        parts.append(" ".join(badges))
        parts.append("")

    # Description
    parts.append(f"> {escape_mdx(node.description)}")
    parts.append("")

    parts.append('<Aside type="note" title="Source & provenance">')
    parts.append(
        "This page is generated from the repository agent file "
        f"`{escape_mdx_line(_display_source_path(node))}` by `wagents docs generate`."
    )
    parts.append("</Aside>")
    parts.append("")

    # Tools as pill badges
    if fm.get("tools"):
        parts.append('<div class="tool-pills">')
        pills = " ".join(f'<Badge text="{escape_attr(t.strip())}" variant="note" />' for t in fm["tools"].split(","))
        parts.append(pills)
        parts.append("</div>")
        parts.append("")

    # Tabbed config (with single-tab fix)
    tab_items = []

    # Identity tab
    id_rows = [f"| Name | `{fm.get('name', node.id)}` |"]
    if fm.get("model"):
        id_rows.append(f"| Model | `{fm['model']}` |")
    if fm.get("permissionMode"):
        id_rows.append(f"| Permission Mode | `{fm['permissionMode']}` |")
    if fm.get("maxTurns"):
        id_rows.append(f"| Max Turns | {fm['maxTurns']} |")
    if fm.get("memory"):
        id_rows.append(f"| Memory | `{fm['memory']}` |")
    tab_items.append(("Identity", "| Field | Value |\n| ----- | ----- |\n" + "\n".join(id_rows)))

    # Tools tab
    tools_rows = []
    if fm.get("tools"):
        tools_rows.append(f"| Allowed | `{fm['tools']}` |")
    if fm.get("disallowedTools"):
        tools_rows.append(f"| Disallowed | `{fm['disallowedTools']}` |")
    if tools_rows:
        tab_items.append(("Tools", "| Field | Value |\n| ----- | ----- |\n" + "\n".join(tools_rows)))

    # Integrations tab
    int_rows = []
    if fm.get("skills"):
        skills_list = ", ".join(f"`{s}`" for s in fm["skills"])
        int_rows.append(f"| Skills | {skills_list} |")
    if fm.get("mcpServers"):
        mcp_list = ", ".join(f"`{m}`" for m in fm["mcpServers"])
        int_rows.append(f"| MCP Servers | {mcp_list} |")
    if int_rows:
        tab_items.append(
            (
                "Integrations",
                "| Field | Value |\n| ----- | ----- |\n" + "\n".join(int_rows),
            )
        )

    parts.extend(render_tabs(tab_items))

    # Skills as LinkCard grid (from frontmatter; includes missing-node fallback)
    if fm.get("skills") and isinstance(fm["skills"], list):
        parts.append("## Skills")
        parts.append("")
        parts.append("<CardGrid>")
        for skill_name in fm["skills"]:
            skill_node = next((n for n in all_nodes if n.kind == "skill" and n.id == skill_name), None)
            if skill_node:
                desc = escape_attr(truncate_sentence(skill_node.description, 160))
                parts.append(
                    f'  <LinkCard title="{escape_attr(skill_name)}"'
                    f' href="{skill_detail_href(skill_name)}" description="{desc}" />'
                )
            else:
                parts.append(
                    f'  <LinkCard title="{escape_attr(skill_name)}" href="{skill_detail_href(skill_name)}" />'
                )
        parts.append("</CardGrid>")
        parts.append("")

    # MCP Servers as LinkCard grid
    if fm.get("mcpServers") and isinstance(fm["mcpServers"], list):
        parts.append("## MCP Servers")
        parts.append("")
        parts.append("<CardGrid>")
        for mcp_name in fm["mcpServers"]:
            mcp_node = next((n for n in all_nodes if n.kind == "mcp" and n.id == mcp_name), None)
            if mcp_node:
                desc = escape_attr(truncate_sentence(mcp_node.description, 160))
                parts.append(
                    f'  <LinkCard title="{escape_attr(mcp_name)}" href="/mcp/{mcp_name}/" description="{desc}" />'
                )
            else:
                parts.append(f'  <LinkCard title="{escape_attr(mcp_name)}" href="/mcp/{mcp_name}/" />')
        parts.append("</CardGrid>")
        parts.append("")

    # System prompt body (shift headings)
    if node.body:
        parts.append("## System Prompt")
        parts.append("")
        parts.append(_catalog_prose(shift_headings(node.body, 1)))
        parts.append("")

    outer_fence = safe_outer_fence(raw_content)
    parts.append("<details>")
    parts.append("<summary>View Full Agent File</summary>")
    parts.append("")
    parts.append(f'{outer_fence}yaml title="{node.id}.md"')
    parts.append(raw_content)
    parts.append(outer_fence)
    parts.append("")
    parts.append("</details>")
    parts.append("")

    parts.append("## Resources")
    parts.append("")
    parts.append("<CardGrid>")
    parts.append('  <LinkCard title="All Agents" href="/agents/" description="Browse agent configurations." />')
    parts.append(
        '  <LinkCard title="CLI Reference" href="/cli/" description="Create and manage agent files with wagents." />'
    )
    parts.append("</CardGrid>")
    parts.append("")

    # Source link
    parts.append("---")
    parts.append(f"[View source on GitHub]({GITHUB_BASE}/{node.source_path})")
    parts.append("")

    return "\n".join(parts)


def render_mcp_page(node: CatalogNode, edges: list[CatalogEdge], all_nodes: list[CatalogNode]) -> str:
    fm = node.metadata
    proj = fm.get("project", {})
    parts = []

    # Frontmatter
    parts.append("---")
    parts.append(f'title: "{node.id}"')
    desc = node.description or f"MCP server: {node.id}"
    parts.append(f'description: "{escape_attr(truncate_sentence(desc, 200))}"')
    parts.append("---")
    parts.append("")

    # Imports
    parts.append(
        "import { Badge, Tabs, TabItem, Aside, Code, CardGrid, LinkCard } from '@astrojs/starlight/components';"
    )
    parts.append("")

    # Badges
    deps = proj.get("dependencies", [])
    badge_parts = ['<Badge text="MCP" variant="note" />', '<Badge text="FastMCP" variant="success" />']
    if deps:
        badge_parts.append(f'<Badge text="{len(deps)} deps" variant="default" />')
    parts.append(" ".join(badge_parts))
    parts.append("")

    # Description
    if node.description:
        parts.append(f"> {escape_mdx(node.description)}")
        parts.append("")

    parts.append('<Aside type="note" title="Source & provenance">')
    parts.append(
        "This page is generated from the repository MCP server directory "
        f"`mcp/{node.id}/` (source file `{escape_mdx_line(_display_source_path(node))}`)."
    )
    parts.append("</Aside>")
    parts.append("")

    # Usage aside
    parts.append('<Aside type="tip" title="Usage">')
    parts.append("Add to your `claude_desktop_config.json`:")
    parts.append("```json")
    mcp_config = {
        "mcpServers": {
            node.id: {
                "command": "uv",
                "args": ["run", "--directory", f"mcp/{node.id}", "python", "server.py"],
            }
        }
    }
    parts.append(json.dumps(mcp_config, indent=2))
    parts.append("```")
    parts.append("</Aside>")
    parts.append("")

    # Tabbed config (with single-tab fix)
    tab_items = []

    # Package info tab
    pkg_rows = []
    if proj.get("name"):
        pkg_rows.append(f"| Name | `{proj['name']}` |")
    if proj.get("version"):
        pkg_rows.append(f"| Version | {proj['version']} |")
    if proj.get("requires-python"):
        pkg_rows.append(f"| Python | `{proj['requires-python']}` |")
    if pkg_rows:
        tab_items.append(("Package", "| Field | Value |\n| ----- | ----- |\n" + "\n".join(pkg_rows)))

    # Dependencies as badges
    if deps:
        dep_badges = " ".join(f'<Badge text="{escape_attr(d)}" variant="note" />' for d in deps)
        tab_items.append(("Dependencies", dep_badges))

    # FastMCP config tab
    fastmcp_config = fm.get("fastmcp_config", {})
    if fastmcp_config:
        tab_items.append(
            (
                "FastMCP Config",
                "```json\n" + json.dumps(fastmcp_config, indent=2) + "\n```",
            )
        )

    parts.extend(render_tabs(tab_items))

    # Server source
    if node.body:
        parts.append("## Server Source")
        parts.append("")
        parts.append('<div class="server-source">')
        parts.append("")
        parts.append(f'```python title="mcp/{node.id}/server.py"')
        parts.append(node.body)
        parts.append("```")
        parts.append("")
        parts.append("</div>")
        parts.append("")

    parts.append("## Resources")
    parts.append("")
    parts.append("<CardGrid>")
    parts.append(
        '  <LinkCard title="MCP Overview" href="/mcp/" description="Browse all MCP documentation in this site." />'
    )
    parts.append(
        '  <LinkCard title="CLI Reference" href="/cli/" description="Scaffold new MCP servers with wagents." />'
    )
    parts.append("</CardGrid>")
    parts.append("")

    # Cross-links (agents that use this MCP)
    related_edges = [e for e in edges if e.to_id == f"mcp:{node.id}"]
    if related_edges:
        parts.append("## Used By")
        parts.append("")
        parts.append("<CardGrid>")
        for edge in related_edges:
            agent_id = edge.from_id.split(":")[1]
            agent_node = next((n for n in all_nodes if n.kind == "agent" and n.id == agent_id), None)
            if agent_node:
                desc = escape_attr(truncate_sentence(agent_node.description, 160))
                parts.append(
                    f'  <LinkCard title="{escape_attr(agent_id)}" href="/agents/{agent_id}/" description="{desc}" />'
                )
        parts.append("</CardGrid>")
        parts.append("")

    # Source link
    parts.append("---")
    parts.append(f"[View source on GitHub]({GITHUB_BASE}/{node.source_path})")
    parts.append("")

    return "\n".join(parts)
