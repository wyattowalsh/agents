"""MDX escaping and page renderers for skills, agents, and MCP servers."""

import json
from pathlib import Path

import typer
import yaml

from wagents import CONTENT_DIR, GITHUB_BASE, ROOT
from wagents.catalog import RELATED_SKILLS, CatalogEdge, CatalogNode
from wagents.parsing import (
    FenceTracker,
    escape_attr,
    shift_headings,
    strip_relative_md_links,
    truncate_sentence,
)

# ---------------------------------------------------------------------------
# MDX escaper
# ---------------------------------------------------------------------------


def escape_mdx(body: str) -> str:
    """Escape markdown body for safe MDX embedding."""
    lines = body.split("\n")
    result = []
    fence = FenceTracker()

    for line in lines:
        if fence.update(line) or fence.inside_fence:
            result.append(line)
        else:
            result.append(escape_mdx_line(line))

    return "\n".join(result)


def escape_mdx_line(line: str) -> str:
    """Escape a single MDX line, preserving inline code spans."""
    if line.startswith("import ") or line.startswith("export "):
        return "\\" + line

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
            out.append("\\<")
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


def read_raw_content(node: CatalogNode) -> str:
    """Read the raw file content for a CatalogNode from disk."""
    raw_path = ROOT / node.source_path if node.source == "custom" else Path(node.source_path)
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
    home = str(Path.home())
    if path.startswith(home):
        return "~" + path[len(home) :]
    return path


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


def render_skill_page(node: CatalogNode, edges: list[CatalogEdge], all_nodes: list[CatalogNode]) -> str:
    fm = node.metadata
    parts = []

    # Read raw content from disk for the copyable code block
    raw_content = read_raw_content(node)

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
    if node.source == "custom":
        badges.append('<Badge text="Custom" variant="tip" />')
    else:
        badges.append('<Badge text="Installed" variant="caution" />')
    parts.append(" ".join(badges))
    parts.append("")

    # Description
    parts.append(f"> {node.description}")
    parts.append("")

    # Quick Start box
    parts.append('<div class="quick-start">')
    parts.append("")
    parts.append("### Quick Start")
    parts.append("")
    parts.append("**Install:**")
    parts.append("```bash")
    if node.source == "custom":
        parts.append(f"npx skills add wyattowalsh/agents/skills/{node.id} -g")
    else:
        parts.append(f"npx skills add {node.id} -g")
    parts.append("```")
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
        "and other "
        "[agentskills.io](https://agentskills.io)-compatible agents."
    )
    parts.append("")

    parts.append('<Aside type="note" title="Source & provenance">')
    if node.source == "custom":
        parts.append(
            "This page is generated from the repository file "
            f"`{escape_mdx_line(_display_source_path(node))}` by `wagents docs generate`."
        )
    else:
        parts.append(
            "This page is generated from an installed skill on disk at "
            f"`{escape_mdx_line(_display_source_path(node))}`."
        )
    parts.append("</Aside>")
    parts.append("")

    # Guide cross-link — check if a hand-maintained guide page exists
    guide_path = CONTENT_DIR / "guides" / f"{node.id}.mdx"
    if guide_path.exists():
        desc = "Architecture, research sources, framework catalog, design decisions, and roadmap."
        parts.append(f'<LinkCard title="Full Guide: {node.id}" href="/guides/{node.id}/" description="{desc}" />')
        parts.append("")

    # "What it does" section — first paragraph after first heading
    what_it_does = ""
    if node.body:
        body_lines = node.body.split("\n")
        found_heading = False
        para_lines = []
        for bl in body_lines:
            if not found_heading:
                if bl.strip().startswith("#"):
                    found_heading = True
                continue
            if bl.strip() == "":
                if para_lines:
                    break
                continue
            para_lines.append(bl.strip())
        if para_lines:
            what_it_does = " ".join(para_lines)

    if what_it_does:
        parts.append("## What It Does")
        parts.append("")
        parts.append(strip_relative_md_links(escape_mdx(what_it_does)))
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
        parts.append(strip_relative_md_links(escape_mdx(dispatch_table)))
        parts.append("")

    # Extract and render additional body sections for richer docs pages
    body_sections = _extract_body_sections(node.body) if node.body else {}
    for section_key, section_content in body_sections.items():
        if section_key in _SKIP_SECTIONS:
            continue
        if section_key not in _RENDERABLE_SECTIONS:
            continue
        if not section_content.strip():
            continue
        # Use the original casing from the body for the heading
        heading = section_key.title()
        parts.append(f"## {heading}")
        parts.append("")
        parts.append(strip_relative_md_links(escape_mdx(section_content)))
        parts.append("")

    # Tabbed metadata (with single-tab fix)
    tab_items = []

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
        cc_rows.append(f"| Argument Hint | `{fm['argument-hint']}` |")
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
                parts.append(
                    f'  <LinkCard title="{escape_attr(rel_id)}" href="/skills/{rel_id}/" description="{desc}" />'
                )
        parts.append("</CardGrid>")
        parts.append("")

    # === TIER 2: Copyable asset preview ===
    # Skills show raw SKILL.md behind a disclosure widget (install-and-use artifacts).
    # Agents show system prompts inline (read-to-understand artifacts). This is intentional.
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
    parts.append(f"> {node.description}")
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
                    f' href="/skills/{skill_name}/" description="{desc}" />'
                )
            else:
                parts.append(f'  <LinkCard title="{escape_attr(skill_name)}" href="/skills/{skill_name}/" />')
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
        parts.append(strip_relative_md_links(escape_mdx(shift_headings(node.body, 1))))
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
        '  <LinkCard title="CLI Reference" href="/cli/"'
        ' description="Create and manage agent files with wagents." />'
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
        parts.append(f"> {node.description}")
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
        '  <LinkCard title="MCP Overview" href="/mcp/"'
        ' description="Browse all MCP documentation in this site." />'
    )
    parts.append(
        '  <LinkCard title="CLI Reference" href="/cli/"'
        ' description="Scaffold new MCP servers with wagents." />'
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
