"""Documentation site generation: indexes, sidebar, and docs subcommands."""

import json
import shutil
import subprocess
from pathlib import Path

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


def _count_mcp_servers_from_config() -> int | None:
    """Return configured MCP server count from repo-level mcp.json, if present."""
    mcp_config = ROOT / "mcp.json"
    if not mcp_config.exists():
        return None
    try:
        data = json.loads(mcp_config.read_text(encoding="utf-8"))
        servers = data.get("mcpServers", {})
        return len(servers) if isinstance(servers, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _has_mcp_overview_page() -> bool:
    """Whether docs contains an MCP overview page (generated or hand-maintained)."""
    return (CONTENT_DIR / "mcp" / "index.mdx").exists()


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
    parts.append("import { Card, CardGrid, LinkCard, Aside, Steps } from '@astrojs/starlight/components';")
    parts.append("")

    # Stats bar — only show non-zero counts
    custom_skills = [n for n in skills if n.source == "custom"]
    installed_skills = [n for n in skills if n.source != "custom"]
    mcp_config_count = _count_mcp_servers_from_config()
    has_mcp_overview = _has_mcp_overview_page()

    stat_items = []
    if custom_skills:
        stat_items.append(f'  <span class="stat stat-skill">{len(custom_skills)} Custom Skills</span>')
    if installed_skills:
        stat_items.append(f'  <span class="stat stat-installed">{len(installed_skills)} Installed Skills</span>')
    if agents:
        stat_items.append(f'  <span class="stat stat-agent">{len(agents)} Agents</span>')
    if mcps:
        stat_items.append(f'  <span class="stat stat-mcp">{len(mcps)} MCP Servers</span>')
    elif has_mcp_overview and mcp_config_count:
        stat_items.append(f'  <span class="stat stat-mcp">{mcp_config_count} MCP Tools Configured</span>')
    elif has_mcp_overview:
        stat_items.append('  <span class="stat stat-mcp">MCP Overview Available</span>')

    if stat_items:
        parts.append('<div class="stats-bar">')
        parts.extend(stat_items)
        parts.append("</div>")
        parts.append("")

    # "What are Skills?" explainer
    parts.append('<Aside type="tip" title="What are Skills?">')
    parts.append(
        "Skills are reusable knowledge and workflows that extend AI coding agents. "
        "Install once, invoke with `/skill-name` in any supported agent. "
        "[Learn more at agentskills.io \u2192](https://agentskills.io)"
    )
    parts.append("</Aside>")
    parts.append("")

    parts.append('<Aside type="note" title="How these docs are built">')
    if has_mcp_overview and not mcps and mcp_config_count:
        parts.append(
            "Most pages in this site are generated from repository assets (`skills/`, `agents/`, `mcp/`) via "
            "`wagents docs generate`. The MCP overview is currently hand-maintained and summarizes the "
            f"{mcp_config_count} servers configured in `mcp.json`"
            " (including local and remote servers outside this repo)."
        )
    else:
        parts.append(
            "Most pages in this site are generated from repository assets (`skills/`, `agents/`, `mcp/`) via "
            "`wagents docs generate`. Hand-maintained pages are preserved"
            " when they include the `HAND-MAINTAINED` sentinel."
        )
    parts.append("</Aside>")
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

    # How it Works
    parts.append("## How it Works")
    parts.append("")
    parts.append("<Steps>")
    parts.append("")
    parts.append("1. **Install** — `npx skills add wyattowalsh/agents --all -g` installs all skills globally.")
    parts.append("")
    parts.append(
        "2. **Invoke** — Type `/skill-name` in "
        "[Claude Code](https://docs.anthropic.com/en/docs/claude-code), "
        "[Gemini CLI](https://github.com/google-gemini/gemini-cli), "
        "or any [agentskills.io](https://agentskills.io)-compatible agent."
    )
    parts.append("")
    parts.append(
        "3. **Enhance** — Each skill provides domain expertise, "
        "structured workflows, and proven patterns that make your "
        "agent dramatically more capable."
    )
    parts.append("")
    parts.append("</Steps>")
    parts.append("")

    parts.append("## Explore the Catalog")
    parts.append("")
    parts.append("<CardGrid>")
    parts.append(
        '  <LinkCard title="Skills Index" href="/skills/"'
        ' description="Browse custom and installed skills grouped by'
        ' invocation model, with install commands and docs pages." />'
    )
    if has_mcp_overview:
        if mcp_config_count:
            mcp_desc = f"Hand-maintained overview of {mcp_config_count} configured MCP servers from `mcp.json`."
        else:
            mcp_desc = "Hand-maintained overview of configured MCP servers."
        parts.append(f'  <LinkCard title="MCP Overview" href="/mcp/" description="{escape_attr(mcp_desc)}" />')
    parts.append(
        '  <LinkCard title="CLI Reference" href="/cli/"'
        ' description="Commands for scaffolding, validation, packaging,'
        ' installation, and docs generation workflows." />'
    )
    parts.append("</CardGrid>")
    parts.append("")

    # Skills section — curated featured picks + link to full index
    _featured_ids = ["wargame", "honest-review", "skill-creator"]
    _skills_by_id = {n.id: n for n in skills}
    featured = [_skills_by_id[fid] for fid in _featured_ids if fid in _skills_by_id]
    if featured:
        parts.append("## Featured Skills")
        parts.append("")
        parts.append('<div class="catalog-skill">')
        parts.append("<CardGrid>")
        for n in featured:
            desc = escape_attr(truncate_sentence(n.description, 160))
            parts.append(f'  <LinkCard title="{escape_attr(n.id)}" href="/skills/{n.id}/" description="{desc}" />')
        parts.append("</CardGrid>")
        parts.append("</div>")
        parts.append("")
        if len(skills) > len(featured):
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
    elif has_mcp_overview:
        parts.append("## MCP Servers")
        parts.append("")
        parts.append('<div class="catalog-mcp">')
        parts.append("<CardGrid>")
        if mcp_config_count:
            desc = escape_attr(
                f"Hand-maintained overview of {mcp_config_count} configured"
                " MCP servers from mcp.json (local and remote)."
            )
        else:
            desc = "Hand-maintained overview of configured MCP servers."
        parts.append(f'  <LinkCard title="MCP Overview" href="/mcp/" description="{desc}" />')
        parts.append("</CardGrid>")
        parts.append("</div>")
        parts.append("")

    # Supported Agents
    parts.append("## Supported Agents")
    parts.append("")
    parts.append("<CardGrid>")
    parts.append(
        '  <LinkCard title="Claude Code"'
        ' href="https://docs.anthropic.com/en/docs/claude-code"'
        ' description="Anthropic\'s official CLI for Claude." />'
    )
    parts.append(
        '  <LinkCard title="Gemini CLI"'
        ' href="https://github.com/google-gemini/gemini-cli"'
        ' description="Google\'s command-line interface for Gemini." />'
    )
    parts.append(
        '  <LinkCard title="Codex CLI"'
        ' href="https://github.com/openai/codex"'
        ' description="OpenAI\'s coding agent with skills support." />'
    )
    parts.append(
        '  <LinkCard title="agentskills.io"'
        ' href="https://agentskills.io"'
        ' description="The open ecosystem for cross-agent skills." />'
    )
    parts.append("</CardGrid>")
    parts.append("")

    # Resources
    parts.append("## Resources")
    parts.append("")
    parts.append("<CardGrid>")
    parts.append(
        '  <LinkCard title="GitHub"'
        ' href="https://github.com/wyattowalsh/agents"'
        ' description="Source code, issues, and contributions." />'
    )
    parts.append(
        '  <LinkCard title="CLI Reference" href="/cli/" description="Full command reference for the wagents CLI." />'
    )
    parts.append(
        '  <LinkCard title="Create Your Own"'
        ' href="/skills/skill-creator/"'
        ' description="Build, improve, and audit skills'
        ' with the skill-creator." />'
    )
    parts.append("</CardGrid>")
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
    parts.append(
        "import { Tabs, TabItem, Steps, FileTree, CardGrid, LinkCard, Aside, Badge }"
        " from '@astrojs/starlight/components';"
    )
    parts.append("")
    parts.append(
        "The `wagents` CLI manages AI agent assets in this repository"
        " -- creating skills, agents, and MCP servers from templates,"
        " validating frontmatter, generating documentation, and packaging skills for distribution."
    )
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
    parts.append('<Aside type="tip" title="Running commands">')
    parts.append(
        "All `wagents` commands should be run with `uv run wagents` from the repository root. "
        "The examples below omit the `uv run` prefix for brevity."
    )
    parts.append("</Aside>")
    parts.append("")
    parts.append("## Commands")
    parts.append("")

    # --- wagents new ---
    parts.append("### `wagents new` -- Create Assets")
    parts.append("")
    parts.append(
        "Scaffold new skills, agents, or MCP servers from reference templates. "
        "Each template includes commented examples for all optional fields."
    )
    parts.append("")
    parts.append("<Tabs>")
    parts.append('  <TabItem label="skill">')
    parts.append("")
    parts.append("Create a new skill with YAML frontmatter and markdown body:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents new skill my-skill")
    parts.append("```")
    parts.append("")
    parts.append(
        "This creates `skills/my-skill/SKILL.md` with a complete template "
        "including all optional frontmatter fields as comments, and scaffolds a documentation page."
    )
    parts.append("")
    parts.append("```bash")
    parts.append("# Skip the docs page scaffold")
    parts.append("wagents new skill my-skill --no-docs")
    parts.append("```")
    parts.append("")
    parts.append("**Output structure:**")
    parts.append("```")
    parts.append("skills/my-skill/")
    parts.append("  SKILL.md          # Frontmatter + instructions")
    parts.append("```")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append('  <TabItem label="agent">')
    parts.append("")
    parts.append("Create a new agent configuration:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents new agent my-agent")
    parts.append("```")
    parts.append("")
    parts.append(
        "This creates `agents/my-agent.md` with frontmatter for tools, permissions, "
        "model selection, and a system prompt body."
    )
    parts.append("")
    parts.append("```bash")
    parts.append("# Skip the docs page scaffold")
    parts.append("wagents new agent my-agent --no-docs")
    parts.append("```")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append('  <TabItem label="mcp">')
    parts.append("")
    parts.append("Create a new MCP server with FastMCP v3:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents new mcp my-server")
    parts.append("```")
    parts.append("")
    parts.append("This creates a complete MCP server directory:")
    parts.append("")
    parts.append("```")
    parts.append("mcp/my-server/")
    parts.append("  server.py         # FastMCP entry point with example tool")
    parts.append("  pyproject.toml    # Package config with fastmcp>=2 dependency")
    parts.append("  fastmcp.json      # FastMCP configuration")
    parts.append("```")
    parts.append("")
    parts.append(
        "The command also adds the `mcp/` directory to the uv workspace in `pyproject.toml` if not already present."
    )
    parts.append("")
    parts.append("```bash")
    parts.append("# Skip the docs page scaffold")
    parts.append("wagents new mcp my-server --no-docs")
    parts.append("```")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append("</Tabs>")
    parts.append("")
    parts.append('<Aside type="note" title="Naming rules">')
    parts.append(
        "All asset names must be kebab-case (`^[a-z0-9][a-z0-9-]*$`) "
        "and at most 64 characters. The name must match the directory name "
        "(for skills and MCP servers) or filename (for agents)."
    )
    parts.append("</Aside>")
    parts.append("")
    parts.append("---")
    parts.append("")

    # --- wagents validate ---
    parts.append("### `wagents validate` -- Check All Assets")
    parts.append("")
    parts.append("Validate frontmatter and structure for every skill, agent, and MCP server in the repository:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents validate")
    parts.append("```")
    parts.append("")
    parts.append("**What it checks:**")
    parts.append("")
    parts.append("| Asset type | Validations |")
    parts.append("|-----------|-------------|")
    parts.append(
        "| **Skills** | Required `name` and `description` fields, kebab-case naming, "
        "name matches directory, description within 1024 chars, body is non-empty |"
    )
    parts.append("| **Agents** | Required `name` and `description` fields, kebab-case naming, name matches filename |")
    parts.append(
        "| **MCP servers** | Directory is kebab-case, `server.py` exists and references FastMCP, "
        "`pyproject.toml` includes fastmcp dependency, `fastmcp.json` exists |"
    )
    parts.append("")
    parts.append("The command exits with code 1 if any validation fails, printing each error to stderr.")
    parts.append("")
    parts.append('<Aside type="tip" title="CI integration">')
    parts.append(
        "Run `wagents validate` in your CI pipeline to catch frontmatter issues before merge. "
        "It is included in the repository's pre-commit and CI checks."
    )
    parts.append("</Aside>")
    parts.append("")
    parts.append("---")
    parts.append("")

    # --- wagents readme ---
    parts.append("### `wagents readme` -- Generate README")
    parts.append("")
    parts.append(
        "Regenerate `README.md` from the current repository contents, or check if the existing README is up to date:"
    )
    parts.append("")
    parts.append("```bash")
    parts.append("# Fully regenerate README.md")
    parts.append("wagents readme")
    parts.append("")
    parts.append("# Check if README is stale (exits 1 if out of date)")
    parts.append("wagents readme --check")
    parts.append("```")
    parts.append("")
    parts.append(
        "The generated README includes tables for all skills, agents, and MCP servers, "
        "plus a development commands reference."
    )
    parts.append("")
    parts.append("---")
    parts.append("")

    # --- wagents install ---
    parts.append("### `wagents install` -- Install Skills")
    parts.append("")
    parts.append("Install skills into agent platforms via `npx skills`:")
    parts.append("")
    parts.append("```bash")
    parts.append("# Install all skills to all supported agents globally")
    parts.append("wagents install")
    parts.append("")
    parts.append("# Install specific skill(s)")
    parts.append("wagents install my-skill")
    parts.append("")
    parts.append("# Install to a specific agent")
    parts.append("wagents install -a claude-code")
    parts.append("")
    parts.append("# List available skills without installing")
    parts.append("wagents install --list")
    parts.append("")
    parts.append("# Copy files instead of symlinking")
    parts.append("wagents install --copy")
    parts.append("")
    parts.append("# Skip confirmation prompts")
    parts.append("wagents install -y")
    parts.append("```")
    parts.append("")
    parts.append(
        "**Supported agents:** `claude-code`, `gemini-cli`, `codex`, `crush`, "
        "`cursor`, `antigravity`, `github-copilot`, `opencode`"
    )
    parts.append("")
    parts.append("---")
    parts.append("")

    # --- wagents package ---
    parts.append("### `wagents package` -- Package Skills")
    parts.append("")
    parts.append("Package skills into portable ZIP files for distribution:")
    parts.append("")
    parts.append("```bash")
    parts.append("# Package a single skill")
    parts.append("wagents package my-skill")
    parts.append("")
    parts.append("# Package all skills")
    parts.append("wagents package --all")
    parts.append("")
    parts.append("# Check portability without creating ZIPs")
    parts.append("wagents package --dry-run")
    parts.append("")
    parts.append("# Specify output directory")
    parts.append("wagents package my-skill --output dist/")
    parts.append("")
    parts.append("# Output as JSON instead of table")
    parts.append("wagents package my-skill --format json")
    parts.append("```")
    parts.append("")
    parts.append(
        "Packaged ZIPs are self-contained and can be distributed independently or attached to GitHub releases."
    )
    parts.append("")
    parts.append('<Aside type="note" title="Automated releases">')
    parts.append(
        "The `release-skills.yml` CI workflow automatically packages and releases "
        "all skills when a version tag (`v*.*.*`) is pushed."
    )
    parts.append("</Aside>")
    parts.append("")
    parts.append("---")
    parts.append("")

    # --- wagents docs ---
    parts.append("### `wagents docs` -- Documentation Site")
    parts.append("")
    parts.append(
        "Manage the [Starlight](https://starlight.astro.build/)-powered documentation site "
        "at [agents.w4w.dev](https://agents.w4w.dev)."
    )
    parts.append("")
    parts.append("<Tabs>")
    parts.append('  <TabItem label="init">')
    parts.append("")
    parts.append("One-time setup to install documentation dependencies:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents docs init")
    parts.append("```")
    parts.append("")
    parts.append("This runs `pnpm install` in the `docs/` directory.")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append('  <TabItem label="generate">')
    parts.append("")
    parts.append("Generate MDX content pages, sidebar, and index pages from repository assets:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents docs generate")
    parts.append("```")
    parts.append("")
    parts.append("**Options:**")
    parts.append("")
    parts.append("```bash")
    parts.append("# Skip installed skills from ~/.claude/skills/")
    parts.append("wagents docs generate --no-installed")
    parts.append("")
    parts.append("# Include skills with TODO descriptions")
    parts.append("wagents docs generate --include-drafts")
    parts.append("```")
    parts.append("")
    parts.append(
        "The generator creates individual pages for each skill, agent, and MCP server, "
        "plus category index pages and the sidebar navigation."
    )
    parts.append("")
    parts.append("  </TabItem>")
    parts.append('  <TabItem label="dev">')
    parts.append("")
    parts.append("Generate content and start the development server with hot reload:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents docs dev")
    parts.append("```")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append('  <TabItem label="build">')
    parts.append("")
    parts.append("Generate content and produce a static build:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents docs build")
    parts.append("```")
    parts.append("")
    parts.append("Output goes to `docs/dist/`.")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append('  <TabItem label="preview">')
    parts.append("")
    parts.append("Generate, build, and start a preview server for the production build:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents docs preview")
    parts.append("```")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append('  <TabItem label="clean">')
    parts.append("")
    parts.append("Remove generated content pages while preserving hand-maintained files:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents docs clean")
    parts.append("```")
    parts.append("")
    parts.append("Files containing `HAND-MAINTAINED` in their content are preserved during clean operations.")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append("</Tabs>")
    parts.append("")
    parts.append('<Aside type="tip" title="Typical docs workflow">')
    parts.append(
        "For day-to-day development, `wagents docs dev` is the most common command "
        "-- it regenerates all content and launches a hot-reloading dev server in one step."
    )
    parts.append("</Aside>")
    parts.append("")
    parts.append("---")
    parts.append("")

    # --- Common Workflows ---
    parts.append("## Common Workflows")
    parts.append("")
    parts.append("### Adding a new skill end-to-end")
    parts.append("")
    parts.append("<Steps>")
    parts.append("")
    parts.append("1. Scaffold the skill:")
    parts.append("   ```bash")
    parts.append("   wagents new skill my-skill")
    parts.append("   ```")
    parts.append("")
    parts.append("2. Edit `skills/my-skill/SKILL.md` with your instructions.")
    parts.append("")
    parts.append("3. Validate the frontmatter:")
    parts.append("   ```bash")
    parts.append("   wagents validate")
    parts.append("   ```")
    parts.append("")
    parts.append("4. Preview the docs page:")
    parts.append("   ```bash")
    parts.append("   wagents docs dev")
    parts.append("   ```")
    parts.append("")
    parts.append("5. Package for distribution:")
    parts.append("   ```bash")
    parts.append("   wagents package my-skill")
    parts.append("   ```")
    parts.append("")
    parts.append("</Steps>")
    parts.append("")
    parts.append("### Updating documentation after changes")
    parts.append("")
    parts.append("<Steps>")
    parts.append("")
    parts.append("1. Regenerate all docs:")
    parts.append("   ```bash")
    parts.append("   wagents docs generate")
    parts.append("   ```")
    parts.append("")
    parts.append("2. Rebuild the README:")
    parts.append("   ```bash")
    parts.append("   wagents readme")
    parts.append("   ```")
    parts.append("")
    parts.append("3. Run validation:")
    parts.append("   ```bash")
    parts.append("   wagents validate")
    parts.append("   ```")
    parts.append("")
    parts.append("</Steps>")
    parts.append("")
    parts.append("---")
    parts.append("")

    # --- Repository Structure ---
    parts.append("## Repository Structure")
    parts.append("")
    parts.append("<FileTree>")
    parts.append("- skills/")
    parts.append("  - \\<name>/")
    parts.append("    - SKILL.md")
    parts.append("    - references/ (optional)")
    parts.append("    - scripts/ (optional)")
    parts.append("    - evals/ (optional)")
    parts.append("- agents/")
    parts.append("  - \\<name>.md")
    parts.append("- mcp/")
    parts.append("  - \\<name>/")
    parts.append("    - server.py")
    parts.append("    - pyproject.toml")
    parts.append("    - fastmcp.json")
    parts.append("- docs/ (this site)")
    parts.append("  - src/")
    parts.append("    - content/")
    parts.append("      - docs/ (generated MDX pages)")
    parts.append("    - generated-sidebar.mjs")
    parts.append("- wagents/")
    parts.append("  - \\_\\_init\\_\\_.py")
    parts.append("  - cli.py")
    parts.append("  - parsing.py")
    parts.append("  - catalog.py")
    parts.append("  - rendering.py")
    parts.append("  - docs.py")
    parts.append("- tests/")
    parts.append("</FileTree>")
    parts.append("")

    # Built With
    parts.append("## Built With")
    parts.append("")
    parts.append("<CardGrid>")
    parts.append(
        '  <LinkCard title="uv" href="https://docs.astral.sh/uv/" description="Fast Python package manager." />'
    )
    parts.append(
        '  <LinkCard title="Typer" href="https://typer.tiangolo.com/" description="CLI framework for Python." />'
    )
    parts.append(
        '  <LinkCard title="Starlight"'
        ' href="https://starlight.astro.build/"'
        ' description="Documentation framework for this site." />'
    )
    parts.append(
        '  <LinkCard title="ruff"'
        ' href="https://docs.astral.sh/ruff/"'
        ' description="Fast Python linter and formatter." />'
    )
    parts.append("</CardGrid>")
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
    parts.append("import { Card, CardGrid, LinkCard, Badge, Aside, Steps } from '@astrojs/starlight/components';")
    parts.append("")
    parts.append(
        "Skills are reusable knowledge and workflows that make AI coding agents dramatically more capable. "
        "They work across **Claude Code**, **Gemini CLI**, **Codex**, **Cursor**, **GitHub Copilot**, "
        "and any [agentskills.io](https://agentskills.io)-compatible agent."
    )
    parts.append("")
    parts.append(
        "Each skill packages domain expertise into a portable format: install once, invoke anywhere with `/skill-name`."
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

    # New-to-skills aside
    parts.append('<Aside type="tip" title="New to skills?">')
    parts.append(
        "Skills extend your AI agent with domain expertise, structured workflows, and proven patterns. "
        "Install with `npx skills add` and invoke with "
        "`/skill-name` in any supported agent. "
        "See [How it Works](/) for a quick overview, or browse the full "
        "[agentskills.io](https://agentskills.io) ecosystem."
    )
    parts.append("</Aside>")
    parts.append("")

    # Split custom skills into user-invocable and auto-invoke
    user_invocable = [n for n in custom if n.metadata.get("user-invocable") is not False]
    auto_invoke = [n for n in custom if n.metadata.get("user-invocable") is False]

    parts.append('<div class="stats-bar">')
    parts.append(f'  <span class="stat stat-skill">{len(user_invocable)} User-Invocable</span>')
    parts.append(f'  <span class="stat stat-agent">{len(auto_invoke)} Convention Skills</span>')
    if installed:
        parts.append(f'  <span class="stat stat-installed">{len(installed)} Installed Skills</span>')
    parts.append("</div>")
    parts.append("")

    # Category explanation table
    parts.append("## Understanding Skill Categories")
    parts.append("")
    parts.append("This repository contains three categories of skills, each serving a different purpose:")
    parts.append("")
    parts.append("| Category | Count | How they work |")
    parts.append("|----------|-------|---------------|")
    parts.append(
        f"| **User-Invocable** | {len(user_invocable)} "
        "| You trigger these manually with `/skill-name`. They appear in the autocomplete menu. |"
    )
    parts.append(
        f"| **Convention** | {len(auto_invoke)} "
        "| The agent auto-invokes these when it detects relevant context "
        "(e.g., editing Python files). Hidden from the `/` menu. |"
    )
    parts.append(
        f"| **Installed** | {len(installed)} "
        "| Third-party skills installed from external sources via `~/.claude/skills/`. |"
    )
    parts.append("")
    parts.append('<Aside type="note" title="Generated docs vs hand-maintained guides">')
    parts.append(
        "Skill pages under `/skills/*` are generated from each skill's `SKILL.md`. "
        "If a deeper curated guide exists (for example, architecture"
        " or roadmap notes), the generated skill page links to it."
    )
    parts.append("</Aside>")
    parts.append("")
    parts.append("---")
    parts.append("")

    if user_invocable:
        parts.append(f"## User-Invocable Skills ({len(user_invocable)})")
        parts.append("")
        parts.append(
            '<Badge text="Manual invocation" variant="tip" /> '
            "Trigger these with `/skill-name` during a conversation. "
            "They appear in the autocomplete menu."
        )
        parts.append("")
        parts.append('<div class="catalog-skill">')
        parts.append("<CardGrid>")
        for n in user_invocable:
            desc = escape_attr(truncate_sentence(n.description, 160))
            parts.append(f'  <LinkCard title="{escape_attr(n.id)}" href="/skills/{n.id}/" description="{desc}" />')
        parts.append("</CardGrid>")
        parts.append("</div>")
        parts.append("")

    if auto_invoke:
        parts.append(f"## Convention Skills ({len(auto_invoke)})")
        parts.append("")
        parts.append(
            '<Badge text="Auto-invoked" variant="caution" /> '
            "The agent loads these automatically when it detects relevant context "
            "-- no manual invocation needed. They enforce consistency across the codebase."
        )
        parts.append("")
        parts.append('<div class="catalog-skill">')
        parts.append("<CardGrid>")
        for n in auto_invoke:
            desc = escape_attr(truncate_sentence(n.description, 160))
            parts.append(f'  <LinkCard title="{escape_attr(n.id)}" href="/skills/{n.id}/" description="{desc}" />')
        parts.append("</CardGrid>")
        parts.append("</div>")
        parts.append("")
        parts.append('<Aside type="note" title="How convention skills work">')
        parts.append(
            "Convention skills set `user-invocable: false` in their frontmatter. "
            "This hides them from the `/` menu but keeps their descriptions in the agent's context, "
            "allowing automatic discovery and invocation when the agent encounters matching "
            "file types or patterns."
        )
        parts.append("</Aside>")
        parts.append("")

    # Installed skills — link to anchors on aggregated page
    if installed:
        parts.append(f"## Installed Skills ({len(installed)})")
        parts.append("")
        parts.append(
            '<Badge text="External" variant="default" /> '
            "Third-party skills installed from the "
            "[agentskills.io](https://agentskills.io) ecosystem via `npx skills add`. "
            "These live in `~/.claude/skills/` and are available across all your projects."
        )
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

    # Individual install instructions
    parts.append("---")
    parts.append("")
    parts.append("## Installing Individual Skills")
    parts.append("")
    parts.append("You can also install specific skills rather than the full collection:")
    parts.append("")
    parts.append("```bash")
    parts.append("# Install a single skill globally")
    parts.append("npx skills add wyattowalsh/agents --skill honest-review -g")
    parts.append("")
    parts.append("# Install multiple specific skills")
    parts.append("npx skills add wyattowalsh/agents --skill honest-review --skill wargame -g")
    parts.append("")
    parts.append("# Install to a specific agent only")
    parts.append("npx skills add wyattowalsh/agents --skill orchestrator -g -a claude-code")
    parts.append("```")
    parts.append("")
    parts.append('<Aside type="tip" title="Creating your own skills">')
    parts.append(
        "Want to build a custom skill? Use the [skill-creator](/skills/skill-creator/) "
        "to scaffold, develop, audit, and package skills following proven structural patterns. "
        "Or run `wagents new skill my-skill` from the [CLI](/cli/)."
    )
    parts.append("</Aside>")

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
    out_dir = CONTENT_DIR / "mcp"
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "index.mdx"

    # Preserve hand-maintained files
    if index_path.exists():
        existing = index_path.read_text(encoding="utf-8")
        if "HAND-MAINTAINED" in existing:
            return

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

    (index_path).write_text("\n".join(parts))


def write_sidebar(nodes: list) -> None:
    """Write docs/src/generated-sidebar.mjs with dynamic sidebar config."""
    custom_skills = [n for n in nodes if n.kind == "skill" and n.source == "custom"]
    installed_skills = [n for n in nodes if n.kind == "skill" and n.source != "custom"]
    agents = [n for n in nodes if n.kind == "agent"]
    mcps = [n for n in nodes if n.kind == "mcp"]
    mcp_config_count = _count_mcp_servers_from_config()
    mcp_overview_path = CONTENT_DIR / "mcp" / "index.mdx"

    lines = []
    lines.append("// Auto-generated by wagents docs generate — do not edit")
    lines.append("export const navLinks = [")
    total_skills = len(custom_skills) + len(installed_skills)
    skills_nav = "  { label: 'Skills', link: '/skills/'"
    if total_skills:
        skills_nav += f", badge: '{total_skills}'"
    skills_nav += " }"
    nav_items = [skills_nav]
    if agents:
        nav_items.append("  { label: 'Agents', link: '/agents/' }")
    mcp_content_dir = CONTENT_DIR / "mcp"
    if mcp_content_dir.exists():
        mcp_nav = "  { label: 'MCP', link: '/mcp/'"
        if mcp_config_count:
            mcp_nav += f", badge: '{mcp_config_count}'"
        mcp_nav += " }"
        nav_items.append(mcp_nav)
    nav_items.append("  { label: 'CLI', link: '/cli/' }")
    lines.append(",\n".join(nav_items))
    lines.append("];")
    lines.append("")
    lines.append("export default [")
    lines.append("  { slug: '' },")

    # Skills group with subgroups
    lines.append("  {")
    lines.append("    label: 'Skills',")
    lines.append(f"    badge: {{ text: '{total_skills}', variant: 'tip' }},")
    lines.append("    collapsed: true,")
    lines.append("    items: [")
    lines.append("      { slug: 'skills', label: 'Overview' },")

    if custom_skills:
        lines.append("      {")
        lines.append(f"        label: 'Custom ({len(custom_skills)})',")
        lines.append("        collapsed: true,")
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
        if mcp_config_count:
            lines.append(f"    badge: {{ text: '{mcp_config_count}', variant: 'note' }},")
        lines.append("    autogenerate: { directory: 'mcp' },")
        lines.append("  },")
    elif mcp_overview_path.exists():
        lines.append("  {")
        lines.append("    label: 'MCP Servers',")
        if mcp_config_count:
            lines.append(f"    badge: {{ text: '{mcp_config_count}', variant: 'note' }},")
        lines.append("    items: [")
        lines.append("      { slug: 'mcp', label: 'Overview' },")
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
# Sentinel-aware clean helper
# ---------------------------------------------------------------------------


def _clean_content_subdir(d: Path) -> bool:
    """Remove generated files from *d*, preserving hand-maintained ones.

    Returns True if any items were removed.
    """
    if not d.exists():
        return False

    hand_maintained: set[str] = set()
    for item in d.iterdir():
        if item.is_file() and item.suffix == ".mdx":
            try:
                if "HAND-MAINTAINED" in item.read_text(encoding="utf-8"):
                    hand_maintained.add(item.name)
            except (UnicodeDecodeError, OSError):
                pass

    cleaned = False
    for item in d.iterdir():
        if item.name in hand_maintained:
            typer.echo(f"  Preserved {d.name}/{item.name} (hand-maintained)")
            continue
        if item.is_file():
            item.unlink()
            cleaned = True
        elif item.is_dir():
            shutil.rmtree(item)
            cleaned = True

    if not hand_maintained and not any(d.iterdir()):
        d.rmdir()
        cleaned = True

    return cleaned


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
    # Clean existing generated content (preserves hand-maintained files)
    for subdir in ["skills", "agents", "mcp"]:
        _clean_content_subdir(CONTENT_DIR / subdir)
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
        kind_dir = f"{node.kind}s" if node.kind != "mcp" else "mcp"
        page_dir = CONTENT_DIR / kind_dir
        page_dir.mkdir(parents=True, exist_ok=True)
        out_file = page_dir / f"{node.id}.mdx"
        # Preserve hand-maintained pages (e.g. merged guide content)
        if out_file.exists() and out_file.suffix == ".mdx":
            try:
                if "HAND-MAINTAINED" in out_file.read_text(encoding="utf-8"):
                    typer.echo(f"  Preserved {kind_dir}/{node.id}.mdx (hand-maintained)")
                    continue
            except (UnicodeDecodeError, OSError):
                pass
        page_content = render_page(node, edges, nodes)
        out_file.write_text(page_content)
        typer.echo(f"  Generated {kind_dir}/{node.id}.mdx")

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
        if _clean_content_subdir(CONTENT_DIR / subdir):
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
