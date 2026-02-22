"""Documentation site generation: indexes, sidebar, and docs subcommands."""

import shutil
import subprocess

import typer

from wagents import CONTENT_DIR, DOCS_DIR, ROOT
from wagents.catalog import collect_edges, collect_installed_skills, collect_nodes
from wagents.parsing import escape_attr, truncate_sentence
from wagents.rendering import (
    read_raw_content,
    render_page,
    safe_outer_fence,
)

# ---------------------------------------------------------------------------
# Index and CLI pages
# ---------------------------------------------------------------------------


def write_index_page(nodes: list) -> None:
    """Write the index.mdx splash page."""
    skills = [n for n in nodes if n.kind == "skill"]
    agents = [n for n in nodes if n.kind == "agent"]
    mcps = [n for n in nodes if n.kind == "mcp"]

    parts = []
    parts.append("---")
    parts.append("title: Agents")
    parts.append(
        "description: AI agent skills, tools, and MCP servers for Claude Code, Gemini CLI, Codex, Cursor, and more"
    )
    parts.append("template: splash")
    parts.append("hero:")
    parts.append("  tagline: Open-source skills, agents, and MCP servers — install in one command")
    parts.append("  image:")
    parts.append("    html: |")
    parts.append('      <div class="hero-terminal">')
    parts.append('        <div class="hero-terminal-header">')
    parts.append('          <span class="hero-terminal-dot red"></span>')
    parts.append('          <span class="hero-terminal-dot yellow"></span>')
    parts.append('          <span class="hero-terminal-dot green"></span>')
    parts.append('          <span class="hero-terminal-title">terminal</span>')
    parts.append("        </div>")
    parts.append('        <div class="hero-terminal-body">')
    parts.append('          <span class="hero-terminal-prompt">$</span>')
    parts.append('          <span class="hero-terminal-cmd">npx skills add wyattowalsh/agents --all -g</span>')
    parts.append('          <span class="hero-terminal-cursor">▋</span>')
    parts.append("        </div>")
    parts.append('        <div class="hero-agents-row">')
    parts.append('          <span class="hero-agent-badge">Claude</span>')
    parts.append('          <span class="hero-agent-badge">Gemini</span>')
    parts.append('          <span class="hero-agent-badge">Codex</span>')
    parts.append('          <span class="hero-agent-badge">Cursor</span>')
    parts.append('          <span class="hero-agent-badge">Copilot</span>')
    parts.append("        </div>")
    parts.append("      </div>")
    parts.append("  actions:")
    parts.append("    - text: Get Started")
    parts.append("      link: /skills/")
    parts.append("      icon: right-arrow")
    parts.append("    - text: GitHub")
    parts.append("      link: https://github.com/wyattowalsh/agents")
    parts.append("      variant: minimal")
    parts.append("      icon: external")
    parts.append("---")
    parts.append("")
    parts.append("import { Card, CardGrid, LinkCard } from '@astrojs/starlight/components';")
    parts.append("")

    # Stats bar — only show non-zero counts
    custom_skills = [n for n in skills if n.source == "custom"]
    installed_skills = [n for n in skills if n.source != "custom"]

    stat_items = []
    if custom_skills:
        stat_items.append(f'  <span class="stat stat-skill">{len(custom_skills)} Custom Skills</span>')
    if installed_skills:
        stat_items.append(f'  <span class="stat stat-installed">{len(installed_skills)} Installed Skills</span>')
    if agents:
        stat_items.append(f'  <span class="stat stat-agent">{len(agents)} Agents</span>')
    if mcps:
        stat_items.append(f'  <span class="stat stat-mcp">{len(mcps)} MCP Servers</span>')

    if stat_items:
        parts.append('<div class="stats-bar">')
        parts.extend(stat_items)
        parts.append("</div>")
        parts.append("")

    # Manually curated showcase — update when key skills change
    parts.append("## What Can You Do?")
    parts.append("")
    parts.append("<CardGrid>")
    parts.append(
        '  <LinkCard title="Enhance Code Reviews" href="/skills/honest-review/"'
        ' description="Research-driven code review at multiple abstraction levels'
        ' with AI code smell detection and severity calibration." />'
    )
    parts.append(
        '  <LinkCard title="Strategic Decision Analysis" href="/skills/wargame/"'
        ' description="Domain-agnostic wargaming with Monte Carlo exploration,'
        ' structured adjudication, and visual dashboards." />'
    )
    parts.append(
        '  <LinkCard title="Host Expert Panels" href="/skills/host-panel/"'
        ' description="Simulated panel discussions among AI experts in roundtable,'
        ' Oxford-style, and Socratic formats." />'
    )
    parts.append(
        '  <LinkCard title="Create MCP Servers" href="/skills/mcp-creator/"'
        ' description="Build production-ready MCP servers using FastMCP v3'
        ' with tool design, testing, and deployment guidance." />'
    )
    parts.append("</CardGrid>")
    parts.append("")

    # Install section
    parts.append('<div class="install-section">')
    parts.append("")
    parts.append("### Quick Install")
    parts.append("")
    parts.append("```bash")
    parts.append("npx skills add wyattowalsh/agents --all -g")
    parts.append("```")
    parts.append("")
    parts.append("</div>")
    parts.append("")

    # Skills section — show top 3 + link to full index
    if skills:
        parts.append("## Featured Skills")
        parts.append("")
        parts.append('<div class="catalog-skill">')
        parts.append("<CardGrid>")
        for n in skills[:3]:
            desc = escape_attr(truncate_sentence(n.description, 160))
            parts.append(f'  <LinkCard title="{escape_attr(n.id)}" href="/skills/{n.id}/" description="{desc}" />')
        parts.append("</CardGrid>")
        parts.append("</div>")
        parts.append("")
        if len(skills) > 3:
            parts.append(f"[View all {len(skills)} skills →](/skills/)")
            parts.append("")

    # Agents section
    if agents:
        parts.append("## Agents")
        parts.append("")
        parts.append('<div class="catalog-agent">')
        parts.append("<CardGrid>")
        for n in agents:
            desc = escape_attr(truncate_sentence(n.description, 160))
            parts.append(f'  <LinkCard title="{escape_attr(n.id)}" href="/agents/{n.id}/" description="{desc}" />')
        parts.append("</CardGrid>")
        parts.append("</div>")
        parts.append("")

    # MCP section
    if mcps:
        parts.append("## MCP Servers")
        parts.append("")
        parts.append('<div class="catalog-mcp">')
        parts.append("<CardGrid>")
        for n in mcps:
            desc = escape_attr(truncate_sentence(n.description, 160))
            parts.append(f'  <LinkCard title="{escape_attr(n.id)}" href="/mcp/{n.id}/" description="{desc}" />')
        parts.append("</CardGrid>")
        parts.append("</div>")
        parts.append("")

    content_dir = ROOT / "docs" / "src" / "content" / "docs"
    content_dir.mkdir(parents=True, exist_ok=True)
    (content_dir / "index.mdx").write_text("\n".join(parts))


def write_cli_page() -> None:
    """Write the CLI reference page."""
    parts = []
    parts.append("---")
    parts.append("title: CLI Reference")
    parts.append("description: wagents CLI commands and usage")
    parts.append("---")
    parts.append("")
    parts.append("import { Tabs, TabItem, Steps, FileTree } from '@astrojs/starlight/components';")
    parts.append("")
    parts.append("The `wagents` CLI manages AI agent assets in this repository.")
    parts.append("")
    parts.append("## Installation")
    parts.append("")
    parts.append("<Steps>")
    parts.append("")
    parts.append("1. Clone the repository:")
    parts.append("   ```bash")
    parts.append("   git clone https://github.com/wyattowalsh/agents.git")
    parts.append("   cd agents")
    parts.append("   ```")
    parts.append("")
    parts.append("2. Install with uv:")
    parts.append("   ```bash")
    parts.append("   uv sync")
    parts.append("   ```")
    parts.append("")
    parts.append("3. Verify installation:")
    parts.append("   ```bash")
    parts.append("   uv run wagents --version")
    parts.append("   ```")
    parts.append("")
    parts.append("</Steps>")
    parts.append("")
    parts.append("## Commands")
    parts.append("")
    parts.append("<Tabs>")
    parts.append('  <TabItem label="new">')
    parts.append("")
    parts.append("Create new assets from reference templates.")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents new skill <name>    # Create a new skill")
    parts.append("wagents new agent <name>    # Create a new agent")
    parts.append("wagents new mcp <name>      # Create a new MCP server")
    parts.append("```")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append('  <TabItem label="docs">')
    parts.append("")
    parts.append("Manage the documentation site.")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents docs init        # One-time: pnpm install in docs/")
    parts.append("wagents docs generate    # Generate MDX content pages")
    parts.append("wagents docs dev         # Generate + launch dev server")
    parts.append("wagents docs build       # Generate + static build")
    parts.append("wagents docs preview     # Generate + build + preview server")
    parts.append("wagents docs clean       # Remove generated content pages")
    parts.append("```")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append('  <TabItem label="validate">')
    parts.append("")
    parts.append("Validate all skills and agents frontmatter.")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents validate")
    parts.append("```")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append('  <TabItem label="readme">')
    parts.append("")
    parts.append("Generate or check the README.")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents readme           # Regenerate README.md")
    parts.append("wagents readme --check   # Check if README is up to date")
    parts.append("```")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append("</Tabs>")
    parts.append("")
    parts.append("## Repository Structure")
    parts.append("")
    parts.append("<FileTree>")
    parts.append("- skills/")
    parts.append("  - \\<name>/")
    parts.append("    - SKILL.md")
    parts.append("    - references/ (optional)")
    parts.append("- agents/")
    parts.append("  - \\<name>.md")
    parts.append("- mcp/")
    parts.append("  - \\<name>/")
    parts.append("    - server.py")
    parts.append("    - pyproject.toml")
    parts.append("    - fastmcp.json")
    parts.append("- docs/ (this site)")
    parts.append("- wagents/ (CLI source)")
    parts.append("  - cli.py")
    parts.append("</FileTree>")
    parts.append("")

    content_dir = ROOT / "docs" / "src" / "content" / "docs"
    content_dir.mkdir(parents=True, exist_ok=True)
    (content_dir / "cli.mdx").write_text("\n".join(parts))


# ---------------------------------------------------------------------------
# Category index pages
# ---------------------------------------------------------------------------


def write_skills_index(nodes: list) -> None:
    """Write skills/index.mdx category page."""
    custom = [n for n in nodes if n.source == "custom"]
    installed = [n for n in nodes if n.source != "custom"]

    parts = []
    parts.append("---")
    parts.append("title: Skills")
    parts.append("description: Browse all available AI agent skills")
    parts.append("---")
    parts.append("")
    parts.append("import { Card, CardGrid, LinkCard, Badge } from '@astrojs/starlight/components';")
    parts.append("")
    parts.append(
        "> Reusable knowledge and workflows that extend AI agent capabilities"
        " across Claude Code, Gemini CLI, Codex, Cursor, and more."
    )
    parts.append("")

    # Install section
    parts.append('<div class="install-section">')
    parts.append("")
    parts.append("### Quick Install All")
    parts.append("")
    parts.append("```bash")
    parts.append("npx skills add wyattowalsh/agents --all -g")
    parts.append("```")
    parts.append("")
    parts.append("</div>")
    parts.append("")

    # Custom skills
    if custom:
        parts.append(f"## Custom Skills ({len(custom)})")
        parts.append("")
        parts.append('<div class="catalog-skill">')
        parts.append("<CardGrid>")
        for n in custom:
            desc = escape_attr(truncate_sentence(n.description, 160))
            parts.append(f'  <LinkCard title="{escape_attr(n.id)}" href="/skills/{n.id}/" description="{desc}" />')
        parts.append("</CardGrid>")
        parts.append("</div>")
        parts.append("")

    # Installed skills — link to anchors on aggregated page
    if installed:
        parts.append(f"## Installed Skills ({len(installed)})")
        parts.append("")
        parts.append('<div class="catalog-installed">')
        parts.append("<CardGrid>")
        for n in installed:
            desc = escape_attr(truncate_sentence(n.description, 160))
            parts.append(
                f'  <LinkCard title="{escape_attr(n.id)}" href="/skills/installed/#{n.id}" description="{desc}" />'
            )
        parts.append("</CardGrid>")
        parts.append("</div>")
        parts.append("")

    out_dir = CONTENT_DIR / "skills"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.mdx").write_text("\n".join(parts))


def write_installed_skills_page(nodes: list) -> None:
    """Write skills/installed.mdx — aggregated page for all installed skills."""
    parts = []
    parts.append("---")
    parts.append(f"title: Installed Skills ({len(nodes)})")
    parts.append("description: Skills installed from external sources")
    parts.append("---")
    parts.append("")
    parts.append("import { Badge, Card, CardGrid, LinkCard } from '@astrojs/starlight/components';")
    parts.append("")
    parts.append(f"> {len(nodes)} skills installed from external sources via `~/.claude/skills/`.")
    parts.append("")

    for n in nodes:
        fm = n.metadata
        meta = fm.get("metadata", {}) if isinstance(fm.get("metadata"), dict) else {}

        # Anchor heading for each skill
        parts.append(f"## {n.id}")
        parts.append("")

        # Badge row
        badges = [f'<Badge text="{escape_attr(n.id)}" variant="note" />']
        word_count = len(n.body.split()) if n.body else 0
        badges.append(f'<Badge text="{word_count} words" variant="default" />')
        if fm.get("license"):
            badges.append(f'<Badge text="{escape_attr(fm["license"])}" variant="success" />')
        if meta.get("version"):
            badges.append(f'<Badge text="v{escape_attr(str(meta["version"]))}" variant="success" />')
        if meta.get("author"):
            badges.append(f'<Badge text="{escape_attr(meta["author"])}" variant="caution" />')
        if fm.get("model"):
            badges.append(f'<Badge text="{escape_attr(fm["model"])}" variant="tip" />')
        parts.append(" ".join(badges))
        parts.append("")

        # Description
        parts.append(f"> {n.description}")
        parts.append("")

        # Install + use
        parts.append(f"**Install:** `npx skills add {n.id} -g`")
        use_line = f"**Use:** `/{n.id}`"
        if fm.get("argument-hint"):
            use_line += f" `{fm['argument-hint']}`"
        parts.append(use_line)
        parts.append("")

        # Collapsible raw SKILL.md
        raw_content = read_raw_content(n)
        outer_fence = safe_outer_fence(raw_content)
        parts.append("<details>")
        parts.append("<summary>View SKILL.md</summary>")
        parts.append("")
        parts.append(f'{outer_fence}yaml title="SKILL.md"')
        parts.append(raw_content)
        parts.append(outer_fence)
        parts.append("")
        parts.append("</details>")
        parts.append("")
        parts.append("---")
        parts.append("")

    out_dir = CONTENT_DIR / "skills"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "installed.mdx").write_text("\n".join(parts))


def write_agents_index(nodes: list) -> None:
    """Write agents/index.mdx category page."""
    parts = []
    parts.append("---")
    parts.append("title: Agents")
    parts.append("description: Browse all available AI agent configurations")
    parts.append("---")
    parts.append("")
    parts.append("import { Card, CardGrid, LinkCard, Badge } from '@astrojs/starlight/components';")
    parts.append("")
    parts.append(
        "> Specialized agent configurations with tools, permissions,"
        " and system prompts for various AI coding assistants."
    )
    parts.append("")
    parts.append('<div class="stats-bar">')
    parts.append(f'  <span class="stat stat-agent">{len(nodes)} agents available</span>')
    parts.append("</div>")
    parts.append("")
    parts.append("## All Agents")
    parts.append("")
    parts.append('<div class="catalog-agent">')
    parts.append("<CardGrid>")
    for n in nodes:
        desc = escape_attr(truncate_sentence(n.description, 160))
        parts.append(f'  <LinkCard title="{escape_attr(n.id)}" href="/agents/{n.id}/" description="{desc}" />')
    parts.append("</CardGrid>")
    parts.append("</div>")
    parts.append("")

    out_dir = CONTENT_DIR / "agents"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.mdx").write_text("\n".join(parts))


def write_mcp_index(nodes: list) -> None:
    """Write mcp/index.mdx category page."""
    parts = []
    parts.append("---")
    parts.append("title: MCP Servers")
    parts.append("description: Browse all available MCP servers")
    parts.append("---")
    parts.append("")
    parts.append("import { Card, CardGrid, LinkCard, Badge } from '@astrojs/starlight/components';")
    parts.append("")
    parts.append("> Model Context Protocol servers providing tools and data to AI agents.")
    parts.append("")
    parts.append('<div class="stats-bar">')
    parts.append(f'  <span class="stat stat-mcp">{len(nodes)} MCP servers available</span>')
    parts.append("</div>")
    parts.append("")
    parts.append("## All MCP Servers")
    parts.append("")
    parts.append('<div class="catalog-mcp">')
    parts.append("<CardGrid>")
    for n in nodes:
        desc = escape_attr(truncate_sentence(n.description, 160))
        parts.append(f'  <LinkCard title="{escape_attr(n.id)}" href="/mcp/{n.id}/" description="{desc}" />')
    parts.append("</CardGrid>")
    parts.append("</div>")
    parts.append("")

    out_dir = CONTENT_DIR / "mcp"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.mdx").write_text("\n".join(parts))


def write_sidebar(nodes: list) -> None:
    """Write docs/src/generated-sidebar.mjs with dynamic sidebar config."""
    custom_skills = [n for n in nodes if n.kind == "skill" and n.source == "custom"]
    installed_skills = [n for n in nodes if n.kind == "skill" and n.source != "custom"]
    agents = [n for n in nodes if n.kind == "agent"]
    mcps = [n for n in nodes if n.kind == "mcp"]

    lines = []
    lines.append("// Auto-generated by wagents docs generate — do not edit")
    lines.append("export const navLinks = [")
    nav_items = ["  { label: 'Skills', link: '/skills/' }"]
    if agents:
        nav_items.append("  { label: 'Agents', link: '/agents/' }")
    if mcps:
        nav_items.append("  { label: 'MCP', link: '/mcp/' }")
    nav_items.append("  { label: 'CLI', link: '/cli/' }")
    lines.append(",\n".join(nav_items))
    lines.append("];")
    lines.append("")
    lines.append("export default [")
    lines.append("  { slug: '' },")

    # Skills group with subgroups
    total_skills = len(custom_skills) + len(installed_skills)
    lines.append("  {")
    lines.append("    label: 'Skills',")
    lines.append(f"    badge: {{ text: '{total_skills}', variant: 'tip' }},")
    lines.append("    items: [")
    lines.append("      { slug: 'skills', label: 'Overview' },")

    if custom_skills:
        lines.append("      {")
        lines.append(f"        label: 'Custom ({len(custom_skills)})',")
        lines.append("        items: [")
        for n in custom_skills:
            lines.append(f"          {{ slug: 'skills/{n.id}' }},")
        lines.append("        ],")
        lines.append("      },")

    if installed_skills:
        lines.append(f"      {{ label: 'Installed ({len(installed_skills)})', slug: 'skills/installed' }},")

    lines.append("    ],")
    lines.append("  },")

    if agents:
        lines.append("  {")
        lines.append("    label: 'Agents',")
        lines.append("    autogenerate: { directory: 'agents' },")
        lines.append("  },")

    if mcps:
        lines.append("  {")
        lines.append("    label: 'MCP Servers',")
        lines.append("    autogenerate: { directory: 'mcp' },")
        lines.append("  },")

    # Guides group — auto-discover hand-maintained guide pages
    guides_dir = CONTENT_DIR / "guides"
    if guides_dir.exists():
        guide_files = sorted(guides_dir.glob("*.mdx"))
        if guide_files:
            lines.append("  {")
            lines.append("    label: 'Guides',")
            lines.append(f"    badge: {{ text: '{len(guide_files)}', variant: 'note' }},")
            lines.append("    items: [")
            for gf in guide_files:
                lines.append(f"      {{ slug: 'guides/{gf.stem}' }},")
            lines.append("    ],")
            lines.append("  },")

    lines.append("  { slug: 'cli', label: 'CLI Reference' },")
    lines.append("];")
    lines.append("")

    sidebar_path = DOCS_DIR / "src" / "generated-sidebar.mjs"
    sidebar_path.parent.mkdir(parents=True, exist_ok=True)
    sidebar_path.write_text("\n".join(lines))


def regenerate_sidebar_and_indexes() -> None:
    """Regenerate sidebar and index pages from current nodes."""
    nodes = collect_nodes()
    # Also collect installed if content dir exists
    if CONTENT_DIR.exists():
        existing_ids = {n.id for n in nodes if n.kind == "skill"}
        installed = collect_installed_skills(existing_ids)
        nodes.extend(installed)

    skills = [n for n in nodes if n.kind == "skill"]
    agents_list = [n for n in nodes if n.kind == "agent"]
    mcps = [n for n in nodes if n.kind == "mcp"]

    write_sidebar(nodes)
    write_skills_index(skills)
    installed_skills = [n for n in skills if n.source != "custom"]
    if installed_skills:
        write_installed_skills_page(installed_skills)
    if agents_list:
        write_agents_index(agents_list)
    if mcps:
        write_mcp_index(mcps)
    write_index_page(nodes)


# ---------------------------------------------------------------------------
# docs subcommand group
# ---------------------------------------------------------------------------

docs_app = typer.Typer(help="Documentation site management")


@docs_app.command("init")
def docs_init():
    """One-time setup: install docs dependencies."""
    if not (DOCS_DIR / "package.json").exists():
        typer.echo("Error: docs/package.json not found. Is the scaffold committed?", err=True)
        raise typer.Exit(code=1)
    typer.echo("Installing docs dependencies...")
    result = subprocess.run(["pnpm", "install"], cwd=str(DOCS_DIR))
    if result.returncode != 0:
        typer.echo("Error: pnpm install failed", err=True)
        raise typer.Exit(code=1)
    typer.echo("Done.")


@docs_app.command("generate")
def docs_generate(
    include_drafts: bool = typer.Option(False, "--include-drafts", help="Include draft skills"),
    include_installed: bool = typer.Option(
        True,
        "--include-installed/--no-installed",
        help="Include installed skills from ~/.claude/skills/",
    ),
):
    """Generate MDX content pages from repo assets."""
    # Clean existing generated content
    for subdir in ["skills", "agents", "mcp"]:
        d = CONTENT_DIR / subdir
        if d.exists():
            shutil.rmtree(d)
    # Remove generated index and cli pages
    for f in ["index.mdx", "cli.mdx"]:
        p = CONTENT_DIR / f
        if p.exists():
            p.unlink()
    # Remove generated sidebar
    sidebar_path = DOCS_DIR / "src" / "generated-sidebar.mjs"
    if sidebar_path.exists():
        sidebar_path.unlink()

    nodes = collect_nodes()

    # Collect installed skills
    if include_installed:
        existing_ids = {n.id for n in nodes if n.kind == "skill"}
        installed = collect_installed_skills(existing_ids)
        nodes.extend(installed)
        if installed:
            typer.echo(f"  Found {len(installed)} installed skills")

    # Filter drafts
    if not include_drafts:
        nodes = [n for n in nodes if not (n.kind == "skill" and n.description.strip().upper().startswith("TODO"))]

    edges = collect_edges(nodes)

    # Write individual pages (skip installed skills — they go on a single aggregated page)
    for node in nodes:
        if node.kind == "skill" and node.source != "custom":
            continue  # installed skills aggregated on skills/installed.mdx
        page_content = render_page(node, edges, nodes)
        page_dir = CONTENT_DIR / (node.kind + "s" if node.kind != "mcp" else "mcp")
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / f"{node.id}.mdx").write_text(page_content)
        typer.echo(
            f"  Generated {node.kind}s/{node.id}.mdx" if node.kind != "mcp" else f"  Generated mcp/{node.id}.mdx"
        )

    # Write category index pages
    skills = [n for n in nodes if n.kind == "skill"]
    agents = [n for n in nodes if n.kind == "agent"]
    mcps = [n for n in nodes if n.kind == "mcp"]

    write_skills_index(skills)
    typer.echo("  Generated skills/index.mdx")
    installed_skills = [n for n in skills if n.source != "custom"]
    if installed_skills:
        write_installed_skills_page(installed_skills)
        typer.echo("  Generated skills/installed.mdx")
    if agents:
        write_agents_index(agents)
        typer.echo("  Generated agents/index.mdx")
    if mcps:
        write_mcp_index(mcps)
        typer.echo("  Generated mcp/index.mdx")

    # Write main index and CLI pages
    write_index_page(nodes)
    typer.echo("  Generated index.mdx")
    write_cli_page()
    typer.echo("  Generated cli.mdx")

    # Generate sidebar
    write_sidebar(nodes)
    typer.echo("  Generated generated-sidebar.mjs")

    typer.echo(f"Generated {len(nodes)} pages + indexes + sidebar")


@docs_app.command("dev")
def docs_dev():
    """Generate content and start dev server."""
    docs_generate()
    typer.echo("Starting dev server...")
    subprocess.run(["pnpm", "dev"], cwd=str(DOCS_DIR))


@docs_app.command("build")
def docs_build():
    """Generate content and build static site."""
    docs_generate()
    typer.echo("Building...")
    result = subprocess.run(["pnpm", "build"], cwd=str(DOCS_DIR))
    if result.returncode != 0:
        typer.echo("Error: build failed", err=True)
        raise typer.Exit(code=1)
    typer.echo("Build complete. Output in docs/dist/")


@docs_app.command("preview")
def docs_preview():
    """Generate, build, and preview the site."""
    docs_generate()
    typer.echo("Building...")
    result = subprocess.run(["pnpm", "build"], cwd=str(DOCS_DIR))
    if result.returncode != 0:
        typer.echo("Error: build failed", err=True)
        raise typer.Exit(code=1)
    typer.echo("Starting preview server...")
    subprocess.run(["pnpm", "preview"], cwd=str(DOCS_DIR))


@docs_app.command("clean")
def docs_clean():
    """Remove generated content pages (preserves hand-written content like guides/)."""
    cleaned = False
    for subdir in ["skills", "agents", "mcp"]:
        d = CONTENT_DIR / subdir
        if d.exists():
            shutil.rmtree(d)
            cleaned = True
    for f in ["index.mdx", "cli.mdx"]:
        p = CONTENT_DIR / f
        if p.exists():
            p.unlink()
            cleaned = True
    sidebar_path = DOCS_DIR / "src" / "generated-sidebar.mjs"
    if sidebar_path.exists():
        sidebar_path.unlink()
        cleaned = True
    if cleaned:
        typer.echo("Cleaned generated content pages")
    else:
        typer.echo("Nothing to clean")
