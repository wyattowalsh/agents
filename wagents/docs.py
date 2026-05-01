"""Documentation site generation: indexes, sidebar, and docs subcommands."""

import json
import shutil
import subprocess
from pathlib import Path

import typer
from typer.models import OptionInfo

from wagents import CONTENT_DIR, DOCS_DIR, ROOT
from wagents.catalog import collect_edges, collect_installed_skills, collect_nodes
from wagents.external_skills import ExternalSkillEntry, read_external_skill_entries
from wagents.parsing import escape_attr, truncate_sentence
from wagents.rendering import (
    read_raw_content,
    render_page,
    safe_outer_fence,
)
from wagents.site_model import (
    VISUAL_ASSET_BY_ID,
    agent_flags,
    build_install_command,
    render_site_data_module,
    render_visual_assets_css,
    site_data,
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


def _has_repo_agents() -> bool:
    """Whether the repository currently contains any bundled agent definitions."""
    return any((ROOT / "agents").glob("*.md"))


def write_site_data(nodes: list, external_entries: list[ExternalSkillEntry] | None = None) -> None:
    """Write generated site data consumed by Astro components."""
    data = site_data(
        nodes,
        mcp_config_count=_count_mcp_servers_from_config(),
        has_mcp_overview=_has_mcp_overview_page(),
        external_skills=external_entries or read_external_skill_entries(),
    )
    (DOCS_DIR / "src" / "generated-site-data.mjs").write_text(render_site_data_module(data), encoding="utf-8")
    (DOCS_DIR / "src" / "generated-visual-assets.css").write_text(render_visual_assets_css(), encoding="utf-8")


def _mdx_asset_import_path(src: str) -> str:
    """Return a generated MDX import path for an asset under docs/src/assets."""
    if not src.startswith("/src/assets/"):
        raise ValueError(f"Expected docs src asset path, got {src!r}")
    return "../../assets/" + src.removeprefix("/src/assets/")


def write_index_page(nodes: list, external_entries: list[ExternalSkillEntry] | None = None) -> None:
    """Write the index.mdx splash page."""
    external_entries = external_entries or read_external_skill_entries()
    data = site_data(
        nodes,
        mcp_config_count=_count_mcp_servers_from_config(),
        has_mcp_overview=_has_mcp_overview_page(),
        external_skills=external_entries,
    )
    skills = [n for n in nodes if n.kind == "skill"]
    installed_skills = [n for n in skills if n.source != "custom"]
    agents = [n for n in nodes if n.kind == "agent"]
    mcps = [n for n in nodes if n.kind == "mcp"]

    parts = []
    parts.append("---")
    parts.append("title: Agents")
    parts.append("description: Portable skills and MCP tools for coding agents")
    parts.append("template: splash")
    parts.append("hero:")
    parts.append("  tagline: Portable skills and MCP tools for coding agents")
    parts.append("  image:")
    parts.append("    html: |")
    parts.append('      <div class="hero-terminal">')
    parts.append('        <div class="hero-terminal-header">')
    parts.append('          <span class="hero-terminal-dot red"></span>')
    parts.append('          <span class="hero-terminal-dot yellow"></span>')
    parts.append('          <span class="hero-terminal-dot green"></span>')
    parts.append('          <span class="hero-terminal-title">agent control plane</span>')
    parts.append("        </div>")
    parts.append('        <div class="hero-terminal-body">')
    parts.append('          <span class="hero-terminal-prompt">$</span>')
    parts.append(f'          <span class="hero-terminal-cmd">{build_install_command(all_skills=True)}</span>')
    parts.append('          <span class="hero-terminal-cursor">▋</span>')
    parts.append("        </div>")
    parts.append('        <div class="hero-agents-row">')
    for agent in data["supportedAgents"]:
        parts.append(f'          <span class="hero-agent-badge">{escape_attr(agent["label"])}</span>')
    parts.append("        </div>")
    parts.append("      </div>")
    parts.append("  actions:")
    parts.append("    - text: Get Started")
    parts.append("      link: /start-here/")
    parts.append("      icon: right-arrow")
    parts.append("    - text: Explore Skills")
    parts.append("      link: /skills/")
    parts.append("      variant: minimal")
    parts.append("      icon: right-arrow")
    parts.append("---")
    parts.append("")
    parts.append("import { Badge, Card, CardGrid, LinkCard, Aside } from '@astrojs/starlight/components';")
    parts.append("import InstallCommand from '../../components/InstallCommand.astro';")
    parts.append("import { installCommands } from '../../generated-site-data.mjs';")
    visual_imports = {
        "catalogMeshArt": VISUAL_ASSET_BY_ID["catalog-mesh"],
        "mcpRoutingArt": VISUAL_ASSET_BY_ID["mcp-routing"],
        "harnessMatrixArt": VISUAL_ASSET_BY_ID["harness-matrix"],
        "workflowMapArt": VISUAL_ASSET_BY_ID["workflow-map"],
    }
    for import_name, asset in visual_imports.items():
        parts.append(f"import {import_name} from '{_mdx_asset_import_path(asset.src)}';")
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
    if external_entries:
        stat_items.append(f'  <span class="stat stat-external">{len(external_entries)} Curated External</span>')
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

    parts.append('<div class="hero-badge-row">')
    parts.append(
        '  <a href="https://github.com/wyattowalsh/agents/stargazers">'
        '<img src="https://img.shields.io/github/stars/wyattowalsh/agents?style=flat-square&label=stars&color=0f766e" '
        'alt="GitHub stars" /></a>'
    )
    parts.append(
        '  <a href="https://github.com/wyattowalsh/agents/actions/workflows/ci.yml">'
        '<img src="https://github.com/wyattowalsh/agents/actions/workflows/ci.yml/badge.svg" '
        'alt="CI status" /></a>'
    )
    parts.append(
        '  <a href="https://github.com/wyattowalsh/agents/blob/main/LICENSE">'
        '<img src="https://img.shields.io/github/license/wyattowalsh/agents?style=flat-square&color=5d6d7e" '
        'alt="License" /></a>'
    )
    parts.append(
        '  <a href="https://github.com/wyattowalsh/agents/releases">'
        '<img src="https://img.shields.io/github/v/release/wyattowalsh/agents?style=flat-square&color=0284c7" '
        'alt="Latest release" /></a>'
    )
    parts.append("</div>")
    parts.append("")

    parts.append("## Start Here")
    parts.append("")
    parts.append(
        "Install the catalog once, then call a focused specialist inside your agent. "
        "Use OpenSpec for non-trivial repo changes that need a durable proposal, tasks, and validation trail. "
        "If you want the shortest guided path through setup, start with [Start Here](/start-here/)."
    )
    parts.append("")

    parts.append(
        '<InstallCommand command={installCommands.all} title="Install the full catalog" '
        'note="Globally installs repo skills across supported agent harnesses." />'
    )
    parts.append("")
    parts.append(
        '<InstallCommand command={installCommands.starter} title="Install one starter skill" '
        'note="Use this when you want to test the workflow before installing everything." />'
    )
    parts.append("")
    parts.append(
        "Then run `/honest-review`, `/wargame`, or `/mcp-creator` inside Claude Code, "
        "Gemini CLI, OpenCode, or any [agentskills.io](https://agentskills.io)-compatible agent."
    )
    parts.append("")
    parts.append("Check OpenSpec workflow health when a change affects public asset formats or downstream tooling:")
    parts.append("")
    parts.append("```bash")
    parts.append("uv run wagents openspec doctor")
    parts.append("```")
    parts.append("")
    parts.append("## Distribution Paths")
    parts.append("")
    parts.append("<CardGrid>")
    for path in data["distributionPaths"]:
        parts.append(f'  <Card title="{escape_attr(path["title"])}">')
        parts.append(
            f'    <Badge text="{escape_attr(path["badge_text"])}" variant="{escape_attr(path["badge_variant"])}" /> '
            f"{path['body']}"
        )
        parts.append("  </Card>")
    parts.append("</CardGrid>")
    parts.append("")
    parts.append('<Aside type="tip" title="Fastest path">')
    parts.append(
        "Use [Start Here](/start-here/) when you want the shortest setup path, "
        "a few strong starter skills, and a quick mental model of the repo."
    )
    parts.append("</Aside>")
    parts.append("")

    parts.append("## Visual Map")
    parts.append("")
    parts.append('<div class="visual-showcase">')
    for import_name, asset in visual_imports.items():
        parts.append('  <figure class="visual-panel">')
        parts.append(f'    <img src={{{import_name}.src}} alt="{escape_attr(asset.alt)}" />')
        parts.append("    <figcaption>")
        parts.append(f"      <strong>{escape_attr(asset.title)}</strong>")
        parts.append(f"      <span>{escape_attr(asset.description)}</span>")
        parts.append("    </figcaption>")
        parts.append("  </figure>")
    parts.append("</div>")
    parts.append("")

    parts.append("## What Skills Are")
    parts.append("")
    parts.append('<div class="catalog-skill">')
    parts.append("<CardGrid>")
    for card in data["featureCards"]:
        parts.append(f'  <Card title="{escape_attr(card["title"])}">')
        parts.append(f'    <div class="feature-card-icon" aria-hidden="true">{escape_attr(card["icon"])}</div>')
        parts.append(
            f'    <Badge text="{escape_attr(card["badge_text"])}" variant="{escape_attr(card["badge_variant"])}" /> '
            f"{card['body']}"
        )
        parts.append("  </Card>")
    parts.append("</CardGrid>")
    parts.append("</div>")
    parts.append("")

    parts.append("## Popular Starting Points")
    parts.append("")
    parts.append("<CardGrid>")
    for skill in data["featuredSkills"]:
        parts.append(
            f'  <LinkCard title="{escape_attr(skill["title"])}" href="{escape_attr(skill["href"])}"'
            f' description="{escape_attr(skill["description"])}" />'
        )
    parts.append("</CardGrid>")
    parts.append("")

    parts.append("## Explore the Catalog")
    parts.append("")
    parts.append("<CardGrid>")
    parts.append(
        '  <LinkCard title="Start Here" href="/start-here/" description="The shortest guided path: '
        'install the catalog, pick a starter skill, and understand the repo layout." />'
    )
    skills_index_desc = (
        "Browse repository skills with install commands, generated detail pages, and convention-skill context."
    )
    if installed_skills:
        skills_index_desc = (
            "Browse repository skills plus optional installed external skills from local agent directories."
        )
    parts.append(f'  <LinkCard title="Skills Index" href="/skills/" description="{escape_attr(skills_index_desc)}" />')
    if has_mcp_overview:
        if mcp_config_count:
            mcp_desc = (
                f"Hand-maintained overview of {mcp_config_count} configured MCP servers from `mcp.json`, "
                "including repo-local and external servers."
            )
        else:
            mcp_desc = "Hand-maintained overview of configured MCP servers."
        parts.append(f'  <LinkCard title="MCP Overview" href="/mcp/" description="{escape_attr(mcp_desc)}" />')
    parts.append(
        '  <LinkCard title="CLI Reference" href="/cli/"'
        ' description="Commands for scaffolding, validation, packaging,'
        ' installation, and docs generation workflows." />'
    )
    parts.append(
        '  <LinkCard title="OpenSpec Workflow" href="/skills/openspec-workflow/"'
        ' description="Use spec/change artifacts and JSON wrappers for non-trivial repo and downstream-tooling'
        ' changes." />'
    )
    parts.append("</CardGrid>")
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
        ' href="https://github.com/google/gemini-cli"'
        ' description="Google\'s command-line interface for Gemini." />'
    )
    parts.append(
        '  <LinkCard title="Codex"'
        ' href="https://github.com/openai/codex"'
        ' description="Autonomous coding workflows for command-line development." />'
    )
    parts.append('  <LinkCard title="Cursor" href="https://cursor.com/" description="The AI Code Editor." />')
    parts.append(
        '  <LinkCard title="GitHub Copilot"'
        ' href="https://github.com/features/copilot"'
        ' description="Your AI pair programmer, right in your IDE." />'
    )
    parts.append(
        '  <LinkCard title="Antigravity"'
        ' href="https://antigravity.google/"'
        ' description="Advanced Agentic Coding assistant." />'
    )
    parts.append(
        '  <LinkCard title="Crush"'
        ' href="https://github.com/crush-ai/crush"'
        ' description="Autonomous development agent focused on fast terminal workflows." />'
    )
    parts.append(
        '  <LinkCard title="OpenCode"'
        ' href="https://github.com/anomalyco/opencode"'
        ' description="Native AGENTS.md support plus repo-level OpenCode config and subagents." />'
    )
    parts.append("</CardGrid>")
    parts.append("")

    parts.append("## How These Docs Work")
    parts.append("")
    parts.append('<Aside type="note" title="Generated pages, curated framing">')
    if not agents and has_mcp_overview and not mcps and mcp_config_count:
        parts.append(
            "Generated catalog pages currently come from repository skills in `skills/`. "
            "The repo-level `agents/` directory is currently empty and reserved for future bundled "
            "agent definitions, while the MCP overview is a hand-maintained summary of "
            f"{mcp_config_count} servers from `mcp.json`. Repo workflow and policy truth lives in "
            "`AGENTS.md`, and the public README is regenerated with `wagents readme`."
        )
    elif has_mcp_overview and not mcps and mcp_config_count:
        parts.append(
            "Most pages in this site are generated from repository assets "
            "(`skills/`, `agents/`, `mcp/`) via `wagents docs generate`, while OpenSpec state lives in `openspec/`. "
            "Repo workflow and policy truth lives in `AGENTS.md`, the public "
            "README is regenerated with `wagents readme`, the top-level "
            "navigation stays concise, curated onboarding pages stay "
            "hand-maintained, and the MCP overview is currently a hand-maintained summary of "
            f"{mcp_config_count} servers from `mcp.json`."
        )
    elif not agents:
        parts.append(
            "Generated catalog pages currently come from populated repository assets. "
            "Right now that means `skills/`; the repo-level `agents/` directory is currently empty "
            "and reserved for future bundled agent definitions. Repo workflow and policy truth lives "
            "in `AGENTS.md`, and the public README is regenerated with `wagents readme`."
        )
    else:
        parts.append(
            "Most pages in this site are generated from repository assets "
            "(`skills/`, `agents/`, `mcp/`) via `wagents docs generate`, while OpenSpec state lives in `openspec/`. "
            "Repo workflow and policy truth lives in `AGENTS.md`, the public "
            "README is regenerated with `wagents readme`, curated onboarding "
            "pages stay hand-maintained, and generated catalogs keep the docs "
            "in sync with the repo."
        )
    parts.append("</Aside>")
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
        '  <LinkCard title="Start Here" href="/start-here/" description="Use the shortest guided path '
        'through install, invocation, and the repo map." />'
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
    parts.append(f"import harnessMatrixArt from '{_mdx_asset_import_path(VISUAL_ASSET_BY_ID['harness-matrix'].src)}';")
    parts.append("")
    parts.append(
        "`wagents` is the repo control plane for skills, agents, MCP servers, and generated docs. "
        "Use it to scaffold new assets, validate the repo, publish docs, and package skills for release."
    )
    parts.append("")
    parts.append('<figure class="visual-panel">')
    parts.append(
        f'  <img src={{harnessMatrixArt.src}} alt="{escape_attr(VISUAL_ASSET_BY_ID["harness-matrix"].alt)}" />'
    )
    parts.append("  <figcaption>")
    parts.append(f"    <strong>{escape_attr(VISUAL_ASSET_BY_ID['harness-matrix'].title)}</strong>")
    parts.append(f"    <span>{escape_attr(VISUAL_ASSET_BY_ID['harness-matrix'].description)}</span>")
    parts.append("  </figcaption>")
    parts.append("</figure>")
    parts.append("")
    parts.append("## Boot Sequence")
    parts.append("")
    parts.append("<Steps>")
    parts.append("")
    parts.append("1. Sync the repo environment:")
    parts.append("   ```bash")
    parts.append("   uv sync")
    parts.append("   ```")
    parts.append("")
    parts.append("2. Sanity-check your toolchain:")
    parts.append("   ```bash")
    parts.append("   uv run wagents doctor")
    parts.append("   ```")
    parts.append("")
    parts.append("3. Validate the repo before making changes:")
    parts.append("   ```bash")
    parts.append("   uv run wagents validate")
    parts.append("   ```")
    parts.append("")
    parts.append("4. Start the docs site when you need to inspect generated output:")
    parts.append("   ```bash")
    parts.append("   uv run wagents docs dev")
    parts.append("   ```")
    parts.append("")
    parts.append("</Steps>")
    parts.append("")
    parts.append('<Aside type="tip" title="Running commands">')
    parts.append(
        "Examples below omit the `uv run` prefix for brevity. "
        "In practice, run `uv run wagents ...` from the repository root."
    )
    parts.append("</Aside>")
    parts.append("")
    parts.append("## Command Map")
    parts.append("")
    parts.append("| Command | Description |")
    parts.append("|---------|-------------|")
    parts.append("| `wagents new <asset>` | Scaffold a new skill, agent, or MCP server from repo templates |")
    parts.append("| `wagents validate` | Check frontmatter, naming, hooks, and related-skill integrity |")
    parts.append("| `wagents doctor` | Sanity-check Python, uv, Node tooling, docs deps, and Playwright |")
    parts.append("| `wagents readme` | Regenerate `README.md` or fail if it is stale |")
    parts.append(
        "| `wagents openspec <subcommand>` | Inspect, validate, and materialize OpenSpec workflows for "
        "downstream AI tools |"
    )
    parts.append("| `wagents install` | Install repo skills into supported agent platforms |")
    parts.append("| `wagents update` | Refresh installed skills from their recorded sources |")
    parts.append(
        "| `wagents skills <subcommand>` | Inventory, sync, search, read, and diagnose local skills on demand |"
    )
    parts.append("| `wagents package <name>` | Build portable ZIP packages for sharing or release |")
    parts.append("| `wagents docs <subcommand>` | Generate, serve, build, preview, or clean the docs site |")
    parts.append("| `wagents hooks <subcommand>` | List and validate lifecycle hooks |")
    parts.append("| `wagents eval <subcommand>` | List, validate, and check eval coverage |")
    parts.append("")
    parts.append("## Command Reference")
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
        "The command also adds the exact `mcp/<name>` entry to the uv workspace in `pyproject.toml` "
        "if not already present."
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

    # --- wagents openspec ---
    parts.append("### `wagents openspec` -- Spec Workflow Control")
    parts.append("")
    parts.append(
        "Wrap OpenSpec CLI commands with repo defaults, downstream tool mappings, and `OPENSPEC_TELEMETRY=0` "
        "for automation. Use these wrappers when AI agents need JSON status or instructions."
    )
    parts.append("")
    parts.append("```bash")
    parts.append("wagents openspec doctor")
    parts.append("wagents openspec init --apply")
    parts.append("wagents openspec status --change add-feature --format json")
    parts.append("wagents openspec instructions design --change add-feature --format json")
    parts.append("wagents openspec validate")
    parts.append("```")
    parts.append("")
    parts.append("**Subcommands:**")
    parts.append("")
    parts.append("| Command | Purpose |")
    parts.append("|---------|---------|")
    parts.append("| `doctor` | Check Node, npx, OpenSpec project files, generated artifacts, and tool mapping |")
    parts.append("| `init` | Print or run `openspec init` for repo-supported downstream tools |")
    parts.append("| `update` | Print or run `openspec update` after CLI/profile changes |")
    parts.append("| `validate` | Run `openspec validate --all --strict --json` |")
    parts.append("| `status` | Return artifact state for one change as JSON-compatible output |")
    parts.append("| `instructions` | Return artifact or apply instructions as JSON-compatible output |")
    parts.append("| `schemas` | List available OpenSpec schemas |")
    parts.append("")
    parts.append('<Aside type="note" title="Generated OpenSpec artifacts">')
    parts.append(
        "OpenSpec-generated `.claude`, `.cursor`, `.opencode`, `.github`, `.agent`, `.crush`, `.codex`, "
        "and `.gemini` artifacts are local/generated unless a specific file is promoted to repo-owned source."
    )
    parts.append("</Aside>")
    parts.append("")
    parts.append("---")
    parts.append("")

    # --- wagents validate ---
    parts.append("### `wagents validate` -- Check All Assets")
    parts.append("")
    parts.append(
        "Validate frontmatter and structure for every skill, agent, and MCP server in the repository. "
        "Also validates hook event names and `RELATED_SKILLS` references."
    )
    parts.append("")
    parts.append("```bash")
    parts.append("wagents validate")
    parts.append("")
    parts.append("# Output as JSON or JSONL")
    parts.append("wagents validate --format json")
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
    parts.append("| **Hooks** | Hook event names are known lifecycle events across skills, agents, and settings |")
    parts.append("| **Related skills** | Every key and value in `RELATED_SKILLS` maps to an existing skill directory |")
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

    # --- wagents doctor ---
    parts.append("### `wagents doctor` -- Environment Health Check")
    parts.append("")
    parts.append(
        "Diagnose your local environment and toolchain. Checks for required tools, "
        "correct Python version, docs dependency status, and Playwright availability."
    )
    parts.append("")
    parts.append("```bash")
    parts.append("wagents doctor")
    parts.append("")
    parts.append("# Output as JSON for scripting")
    parts.append("wagents doctor --format json")
    parts.append("```")
    parts.append("")
    parts.append("**What it checks:**")
    parts.append("")
    parts.append("| Check | Status on failure |")
    parts.append("|-------|-------------------|")
    parts.append("| Python version satisfies `requires-python` | `fail` |")
    parts.append("| `uv` on PATH | `fail` |")
    parts.append("| `node`, `npx`, `pnpm` on PATH | `warn` |")
    parts.append("| `docs/node_modules` present and fresh | `warn` |")
    parts.append("| Playwright Python package installed | `warn` |")
    parts.append("| Playwright browser cache exists | `warn` |")
    parts.append("")
    parts.append(
        "Exits with code 1 if any check has `fail` status. Warnings are informational and do not affect the exit code."
    )
    parts.append("")
    parts.append('<Aside type="tip" title="First-time setup">')
    parts.append("Run `wagents doctor` after cloning to verify your environment before working with skills or docs.")
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
    parts.append("# Project-local install instead of global")
    parts.append("wagents install --local")
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
    parts.append("For third-party skill sources or curated subsets, use `npx skills add` directly:")
    parts.append("")
    parts.append("```bash")
    parts.append(f"npx skills add <source> --skill <name> -y -g {agent_flags()}")
    parts.append("```")
    parts.append("")
    parts.append("| Option | Default | Description |")
    parts.append("|--------|---------|-------------|")
    parts.append("| `<skills>` | all | Positional skill name(s) to install |")
    parts.append("| `-a`, `--agent` | all | Target agent(s), repeatable |")
    parts.append("| `-g`, `--global` | `true` | Install globally (default) |")
    parts.append("| `--local` | `false` | Install into current project only |")
    parts.append("| `--list` | `false` | List available skills without installing |")
    parts.append("| `--copy` | `false` | Copy files instead of symlinking |")
    parts.append("| `-y`, `--yes` | `false` | Skip confirmation prompts |")
    parts.append("")
    parts.append(
        "**Supported agents:** `antigravity`, `claude-code`, `codex`, `crush`, "
        "`cursor`, `gemini-cli`, `github-copilot`, `opencode`"
    )
    parts.append("")
    parts.append("---")
    parts.append("")

    # --- wagents update ---
    parts.append("### `wagents update` -- Refresh Installed Skills")
    parts.append("")
    parts.append(
        "Refresh installed skills from the sources recorded by the `skills` CLI. "
        "Use this after this repository changes so downstream agent installs pick up the latest committed skill files."
    )
    parts.append("")
    parts.append("```bash")
    parts.append("wagents update")
    parts.append("")
    parts.append("# Equivalent lower-level command")
    parts.append("npx skills update")
    parts.append("```")
    parts.append("")
    parts.append("---")
    parts.append("")

    # --- wagents skills sync ---
    parts.append("### `wagents skills sync` -- Additive Cross-Harness Sync")
    parts.append("")
    parts.append(
        "Build a normalized installed-skill inventory from `npx skills ls -g -a <agent> --json`, "
        "then preview or apply additive installs for the desired sync set."
    )
    parts.append("")
    parts.append("```bash")
    parts.append("# Default mode is dry-run across all supported harnesses")
    parts.append("wagents skills sync")
    parts.append("")
    parts.append("# Target one harness")
    parts.append("wagents skills sync --agent github-copilot")
    parts.append("")
    parts.append("# Include verified one-off installed external skills")
    parts.append("wagents skills sync --include-installed")
    parts.append("")
    parts.append("# Execute the verified install commands")
    parts.append("wagents skills sync --apply")
    parts.append("```")
    parts.append("")
    parts.append("| Option | Default | Description |")
    parts.append("|--------|---------|-------------|")
    parts.append("| `-a`, `--agent` | all | Restrict sync to one or more harnesses |")
    parts.append("| `--all-agents` | `false` | Explicitly target all supported harnesses |")
    parts.append(
        "| `--dry-run` | `true` | Preview missing, already-present, unresolved, "
        "skipped rows, and exact install commands |"
    )
    parts.append("| `--apply` | `false` | Execute only the verified additive install commands |")
    parts.append(
        "| `--include-installed` | `false` | Include verified one-off installed "
        "external skills outside the curated desired set |"
    )
    parts.append("")
    parts.append('<Aside type="note" title="Desired sync set">')
    parts.append(
        "By default, sync targets repo-owned custom skills plus verified curated external skills. "
        "It never removes user-installed skills."
    )
    parts.append("</Aside>")
    parts.append("")
    parts.append('<Aside type="caution" title="GitHub Copilot caveat">')
    parts.append(
        "GitHub Copilot remains part of config and instruction sync, but the skills inventory reports "
        "only what the Skills CLI returns. A legitimate `0` installed-skills result stays `0`."
    )
    parts.append("</Aside>")
    parts.append("")
    parts.append("---")
    parts.append("")

    # --- wagents skills ---
    parts.append("### `wagents skills` -- On-Demand Skill Index")
    parts.append("")
    parts.append(
        "Inspect repository, installed, curated, and plugin skills without loading every skill description "
        "into startup context. Use this when local skill inventory exceeds an agent's context budget or when you "
        "need additive sync diagnostics."
    )
    parts.append("")
    parts.append("<Tabs>")
    parts.append('  <TabItem label="sync">')
    parts.append("")
    parts.append("Preview additive cross-harness installs from the normalized inventory:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents skills sync --dry-run")
    parts.append("")
    parts.append("# Narrow to one harness and include verified one-off installs")
    parts.append("wagents skills sync --agent codex --include-installed")
    parts.append("```")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append('  <TabItem label="search">')
    parts.append("")
    parts.append("Search for matching skills with deterministic lexical ranking:")
    parts.append("")
    parts.append("```bash")
    parts.append('wagents skills search "fix GitHub Actions workflow"')
    parts.append("")
    parts.append("# Restrict to repo skills and emit JSON")
    parts.append('wagents skills search "release notes" --source repo --format json')
    parts.append("```")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append('  <TabItem label="context">')
    parts.append("")
    parts.append("Build a compact context packet from the top matching skill bodies:")
    parts.append("")
    parts.append("```bash")
    parts.append('wagents skills context "debug browser rendering" --limit 3')
    parts.append("```")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append('  <TabItem label="read">')
    parts.append("")
    parts.append("Read one known skill by exact name or path:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents skills read skill-router")
    parts.append("wagents skills read /path/to/SKILL.md")
    parts.append("```")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append('  <TabItem label="doctor">')
    parts.append("")
    parts.append("Inspect skill roots, counts, and warning totals:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents skills doctor")
    parts.append("```")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append("</Tabs>")
    parts.append("")
    parts.append("| Source | Roots |")
    parts.append("|--------|-------|")
    parts.append("| `repo` | `skills/` |")
    parts.append("| `project` | `.agents/skills/` in the current project path |")
    parts.append("| `codex` | `~/.codex/skills/` |")
    parts.append("| `global` | `~/.agents/skills/` plus supported agent skill stores |")
    parts.append("| `plugin` | `~/.codex/plugins/cache/**/skills/` |")
    parts.append("")
    parts.append("Each result includes `name`, `path`, `source`, `trust_tier`, `score`, matched fields, and warnings.")
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
    parts.append(
        "# Include installed skills from local agent skill directories "
        "(~/.config/opencode/skills/, ~/.agents/skills/, ~/.claude/skills/)"
    )
    parts.append("wagents docs generate --include-installed")
    parts.append("")
    parts.append("# Include skills with TODO descriptions")
    parts.append("wagents docs generate --include-drafts")
    parts.append("```")
    parts.append("")
    parts.append(
        "By default, generation is deterministic and repository-only. The generator creates "
        "individual pages for each skill, agent, and MCP server, plus category index pages "
        "and the sidebar navigation."
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

    # --- wagents hooks ---
    parts.append("### `wagents hooks` -- Lifecycle Hooks")
    parts.append("")
    parts.append(
        "Inspect and validate lifecycle hooks defined in `.claude/settings.json`, "
        "skill frontmatter, agent frontmatter, and the portable `config/hook-registry.json`."
    )
    parts.append("")
    parts.append("<Tabs>")
    parts.append('  <TabItem label="list">')
    parts.append("")
    parts.append("List all hooks across skills, agents, settings, and the portable hook registry:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents hooks list")
    parts.append("")
    parts.append("# Output as JSON")
    parts.append("wagents hooks list --format json")
    parts.append("```")
    parts.append("")
    parts.append("Shows source, event, matcher, harness support, handler type, and command/prompt for each hook.")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append('  <TabItem label="validate">')
    parts.append("")
    parts.append("Validate hook definitions for correct structure and known event names:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents hooks validate")
    parts.append("```")
    parts.append("")
    parts.append(
        "Checks that every hook event is a known lifecycle event (`PreToolUse`, `PostToolUse`, etc.), "
        "handler types are valid (`command`, `prompt`, `agent`), registry harnesses are supported, "
        "and required fields are present."
    )
    parts.append("")
    parts.append("  </TabItem>")
    parts.append("</Tabs>")
    parts.append("")
    parts.append("---")
    parts.append("")

    # --- wagents eval ---
    parts.append("### `wagents eval` -- Skill Evals")
    parts.append("")
    parts.append(
        "Manage and validate eval files stored in `skills/<name>/evals/*.json`. "
        "Evals define test queries and expected behaviors for skills."
    )
    parts.append("")
    parts.append("<Tabs>")
    parts.append('  <TabItem label="list">')
    parts.append("")
    parts.append("List all eval files grouped by skill:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents eval list")
    parts.append("")
    parts.append("# Output as JSON")
    parts.append("wagents eval list --format json")
    parts.append("```")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append('  <TabItem label="validate">')
    parts.append("")
    parts.append("Validate eval JSON files for required fields and referential integrity:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents eval validate")
    parts.append("```")
    parts.append("")
    parts.append(
        "Legacy scenario files must contain `skills`, `query`, and `expected_behavior`. "
        "Canonical manifests may use `evals/evals.json` with `skill_name` plus an `evals` array "
        "of cases containing `prompt` and `expected_output`, with optional `files` and `assertions`."
    )
    parts.append("")
    parts.append("  </TabItem>")
    parts.append('  <TabItem label="coverage">')
    parts.append("")
    parts.append("Show which skills have evals and how many:")
    parts.append("")
    parts.append("```bash")
    parts.append("wagents eval coverage")
    parts.append("```")
    parts.append("")
    parts.append("Useful for identifying skills that lack test coverage.")
    parts.append("")
    parts.append("  </TabItem>")
    parts.append("</Tabs>")
    parts.append("")
    parts.append("---")
    parts.append("")

    # --- Structured output ---
    parts.append('### Structured Output <Badge text="All validation commands" variant="note" />')
    parts.append("")
    parts.append("Most inspection and validation commands accept `--format` to control output:")
    parts.append("")
    parts.append("| Format | Description |")
    parts.append("|--------|-------------|")
    parts.append("| `text` | Human-readable table output (default) |")
    parts.append("| `json` | Single JSON object with full results |")
    parts.append("| `jsonl` | One JSON object per line — ideal for piping to `jq` or log aggregators |")
    parts.append("")
    parts.append(
        "Commands supporting `--format`: `validate`, `doctor`, `hooks list`, "
        "`hooks validate`, `eval list`, `eval validate`, `eval coverage`, "
        "`skills index`, `skills search`, `skills read`, `skills context`, `skills doctor`."
    )
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
    parts.append("### Checking environment health")
    parts.append("")
    parts.append("<Steps>")
    parts.append("")
    parts.append("1. Run the doctor check:")
    parts.append("   ```bash")
    parts.append("   wagents doctor")
    parts.append("   ```")
    parts.append("")
    parts.append("2. Fix any `FAIL` items shown in the output.")
    parts.append("")
    parts.append("3. Run validation and hook checks:")
    parts.append("   ```bash")
    parts.append("   wagents validate && wagents hooks validate")
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
    parts.append("  - servers/ (ignored local third-party installs)")
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
    parts.append("## Related Pages")
    parts.append("")
    parts.append("<CardGrid>")
    parts.append('  <LinkCard title="Skills Catalog" href="/skills/" description="Browse all available skills." />')
    if _has_repo_agents():
        parts.append(
            '  <LinkCard title="Agents Directory" href="https://github.com/wyattowalsh/agents/tree/main/agents" '
            'description="Browse agent configurations in the repository." />'
        )
    else:
        parts.append(
            '  <LinkCard title="Bundle Manifest" '
            'href="https://github.com/wyattowalsh/agents/blob/main/agent-bundle.json" '
            'description="See the current bundle surface; repo-level bundled agents are not published yet." />'
        )
    parts.append('  <LinkCard title="MCP Servers" href="/mcp/" description="Browse MCP server integrations." />')
    parts.append("</CardGrid>")
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
    parts.append('  <LinkCard title="ty" href="https://docs.astral.sh/ty/" description="Fast Python type checker." />')
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


def write_skills_index(nodes: list, external_entries: list[ExternalSkillEntry] | None = None) -> None:
    """Write skills/index.mdx category page."""
    external_entries = external_entries or read_external_skill_entries()
    custom = [n for n in nodes if n.source == "custom"]
    installed = [n for n in nodes if n.source != "custom"]

    parts = []
    parts.append("---")
    parts.append("title: Skills")
    parts.append("description: Browse all available AI agent skills")
    parts.append("---")
    parts.append("")
    parts.append("import { Card, CardGrid, LinkCard, Badge, Aside } from '@astrojs/starlight/components';")
    parts.append("import InstallCommand from '../../../components/InstallCommand.astro';")
    parts.append("import SkillCatalog from '../../../components/SkillCatalog.astro';")
    parts.append("import SkillTopology from '../../../components/SkillTopology.astro';")
    parts.append("import { installCommands, skillIndex } from '../../../generated-site-data.mjs';")
    parts.append("")
    parts.append(
        "Skills are portable prompt-and-workflow bundles for coding agents. "
        "Install them once, invoke them with `/skill-name`, and keep the behavior under version control."
    )
    parts.append("")
    parts.append("New here? Start with [Start Here](/start-here/) for the shortest setup path.")
    parts.append("")

    parts.append("### Quick Install")
    parts.append("")
    parts.append(
        '<InstallCommand command={installCommands.all} title="Install this repository catalog" '
        'note="Use the copy button or scroll horizontally inside the command area." />'
    )
    parts.append("")
    parts.append('<InstallCommand command={installCommands.starter} title="Install a focused starter skill" />')
    parts.append("")

    parts.append('<Aside type="tip" title="How to use this page">')
    parts.append(
        "Use the lane cards below when you want a fast starting point. "
        "Use the full catalog sections when you already know the exact skill you need."
    )
    parts.append("</Aside>")
    parts.append("")
    parts.append('<Aside type="note" title="Installed external skills">')
    parts.append(
        "Use `npx skills add <source> --skill <name> -y -g --agent <agent>` for third-party collections "
        "or curated subsets. See [External Skills](/external-skills/) for the curated install set "
        "and trust gates. Run `wagents docs generate --include-installed` when you want those locally "
        "installed skills included in a docs build."
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
    if external_entries:
        parts.append(f'  <span class="stat stat-external">{len(external_entries)} Curated External</span>')
    parts.append("</div>")
    parts.append("")

    parts.append("## Complete Intelligence Index")
    parts.append("")
    parts.append(
        "This generated index combines repo-owned custom skills, optional locally installed external skills, "
        "and the curated third-party source list. Each row carries source, trust, install, and knowledge metadata."
    )
    parts.append("")
    parts.append("<SkillCatalog skills={skillIndex} />")
    parts.append("")
    parts.append("<SkillTopology skills={skillIndex} />")
    parts.append("")

    parts.append("## Skill Lanes")
    parts.append("")
    parts.append("<CardGrid>")
    parts.append(
        '  <LinkCard title="Review & QA" href="/skills/honest-review/" description="Start here for '
        'code review, docs QA, test strategy, performance review, or security scanning." />'
    )
    parts.append(
        '  <LinkCard title="Build & Design" href="/skills/frontend-designer/" description="Use these '
        'when you are creating frontends, APIs, data systems, infra, or MCP servers." />'
    )
    parts.append(
        '  <LinkCard title="Strategy & Research" href="/skills/research/" description="Use these when '
        'the problem is fuzzy, the trade-offs are real, or you need deeper investigation first." />'
    )
    parts.append(
        '  <LinkCard title="Workflow & Utility" href="/skills/orchestrator/" description="Use these to '
        'coordinate work, simplify code, manage git flow, package releases, or handle local file tasks." />'
    )
    parts.append("</CardGrid>")
    parts.append("")

    if user_invocable:
        parts.append(f"## User-Invocable Skills ({len(user_invocable)})")
        parts.append("")
        parts.append(
            '<Badge text="Manual invocation" variant="tip" /> '
            "Call these when you want a specialist on demand. They appear in the autocomplete menu."
        )
        parts.append("")
        parts.append(
            "These are the main building blocks in the catalog: focused specialists for review, docs, "
            "architecture, data, infra, research, prompting, and workflow design."
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
            "The agent loads these automatically when repo context matches. They stay out of the `/` menu."
        )
        parts.append("")
        parts.append(
            "Convention skills quietly enforce repo standards like Python tooling, shell conventions, "
            "JavaScript package management, and agent metadata rules."
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

    # Installed skills — link to anchors on aggregated page
    if installed:
        parts.append(f"## Installed Skills ({len(installed)})")
        parts.append("")
        parts.append(
            '<Badge text="External" variant="default" /> '
            "Third-party skills installed from the [agentskills.io](https://agentskills.io) ecosystem "
            "via `npx skills add`."
        )
        parts.append("")
        parts.append(
            "Installed skills only appear in docs builds that opt into local agent skill directories such as "
            "`~/.config/opencode/skills/`, `~/.agents/skills/`, and `~/.claude/skills/`."
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
    parts.append(build_install_command(skill="honest-review"))
    parts.append("")
    parts.append("# Install multiple specific skills")
    parts.append(build_install_command(skills=("honest-review", "wargame")))
    parts.append("")
    parts.append("# Install to a specific agent only")
    parts.append(build_install_command(skill="orchestrator", agent_ids=("claude-code",)))
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
    parts.append(
        f"> {len(nodes)} skills installed from external sources and discovered from the normalized harness inventory "
        "built with `npx skills ls -g -a <agent> --json` plus local skill metadata from directories like "
        "`~/.config/opencode/skills/`, `~/.agents/skills/`, and `~/.claude/skills/`."
    )
    parts.append("")

    def install_command(node) -> str:
        if isinstance(node.metadata, dict) and node.metadata.get("_skills_install_command"):
            return str(node.metadata["_skills_install_command"])
        source = node.metadata.get("_skills_source") if isinstance(node.metadata, dict) else None
        if source:
            return f"npx skills add {source} --skill {node.id} -y -g"
        return f"npx skills add {node.id} -y -g"

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
        if isinstance(fm.get("_skills_provenance_status"), str):
            badges.append(f'<Badge text="{escape_attr(str(fm["_skills_provenance_status"]))}" variant="tip" />')
        if fm.get("license"):
            badges.append(f'<Badge text="{escape_attr(fm["license"])}" variant="success" />')
        if meta.get("version"):
            badges.append(f'<Badge text="v{escape_attr(str(meta["version"]))}" variant="success" />')
        if meta.get("author"):
            badges.append(f'<Badge text="{escape_attr(meta["author"])}" variant="caution" />')
        installed_agents = (
            fm.get("_skills_installed_agents") if isinstance(fm.get("_skills_installed_agents"), list) else []
        )
        if installed_agents:
            badges.append(
                f'<Badge text="{escape_attr(", ".join(str(agent) for agent in installed_agents))}" variant="default" />'
            )
        if fm.get("model"):
            badges.append(f'<Badge text="{escape_attr(fm["model"])}" variant="tip" />')
        parts.append(" ".join(badges))
        parts.append("")

        # Description
        parts.append(f"> {n.description}")
        parts.append("")

        # Install + use
        parts.append(f"**Install:** `{install_command(n)}`")
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


def write_external_skills_page(entries: list[ExternalSkillEntry]) -> None:
    """Write external-skills.mdx from the curated instruction source."""
    groups = {
        "install-now-after-trust-gate": "Install Now After Trust Gate",
        "inspect-then-install": "Inspect Then Install",
        "global-only-or-avoid": "Keep Global Only Or Avoid",
    }
    by_status = {status: [entry for entry in entries if entry.status == status] for status in groups}

    parts = []
    parts.append("---")
    parts.append('title: "External Skills"')
    parts.append('description: "Curated external Agent Skills with source, trust, install, and provenance metadata."')
    parts.append("---")
    parts.append("")
    parts.append("import { Aside, Badge } from '@astrojs/starlight/components';")
    parts.append("import SkillCatalog from '../../components/SkillCatalog.astro';")
    parts.append("import { skillIndex } from '../../generated-site-data.mjs';")
    parts.append(
        "export const externalSkillIndex = skillIndex.filter((skill) => skill.sourceType === 'curated-external');"
    )
    parts.append("")
    parts.append("# External Skills")
    parts.append("")
    parts.append(
        "This page is generated from `instructions/external-skills.md`. "
        "It indexes curated third-party skills by source, trust gate, install command, "
        "provenance state, and target agents."
    )
    parts.append("")
    parts.append('<Aside type="caution">')
    parts.append(
        "Do not bulk-import entire external repositories. Install only curated skills, inspect source-list output, "
        "and run `external-skill-auditor` before repo promotion."
    )
    parts.append("</Aside>")
    parts.append("")
    parts.append("<SkillCatalog skills={externalSkillIndex} />")
    parts.append("")

    for status, title in groups.items():
        rows = by_status[status]
        if not rows:
            continue
        parts.append(f"## {title} ({len(rows)})")
        parts.append("")
        parts.append('<div class="external-skill-grid">')
        for entry in rows:
            source = (
                f'<a href="{escape_attr(entry.source_url)}"><code>{escape_attr(entry.source)}</code></a>'
                if entry.source_url
                else f"<code>{escape_attr(entry.source)}</code>"
            )
            parts.append('<article class="external-skill-card">')
            parts.append("  <header>")
            parts.append(f"    <h3><code>{escape_attr(entry.name)}</code></h3>")
            parts.append(f'    <Badge text="{escape_attr(entry.trust_tier)}" variant="note" />')
            parts.append(f'    <Badge text="{escape_attr(entry.provenance_status)}" variant="default" />')
            parts.append("  </header>")
            parts.append(f"  <p>Source: {source}</p>")
            parts.append(f"  <p>{escape_attr(entry.notes)}</p>")
            if entry.unresolved_reason:
                parts.append(f"  <p><strong>Unresolved:</strong> {escape_attr(entry.unresolved_reason)}</p>")
            if entry.install_command:
                parts.append("  <details>")
                parts.append("    <summary>Install command</summary>")
                parts.append('    <pre class="agents-scrollbar"><code>')
                parts.append(escape_attr(entry.install_command))
                parts.append("    </code></pre>")
                parts.append("  </details>")
            parts.append("</article>")
        parts.append("")
        parts.append("</div>")
        parts.append("")

    parts.append("## Source Of Truth")
    parts.append("")
    parts.append(
        "Update `instructions/external-skills.md` first, then run `uv run wagents docs generate` "
        "so this page and the generated skill index stay synchronized."
    )
    parts.append("")

    (CONTENT_DIR / "external-skills.mdx").write_text("\n".join(parts))


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
    external_entries = read_external_skill_entries()
    agents = [n for n in nodes if n.kind == "agent"]
    mcps = [n for n in nodes if n.kind == "mcp"]
    mcp_config_count = _count_mcp_servers_from_config()
    mcp_overview_path = CONTENT_DIR / "mcp" / "index.mdx"

    lines = []
    lines.append("// Auto-generated by wagents docs generate — do not edit")
    lines.append("export const navLinks = [")
    total_skills = len(custom_skills) + len(installed_skills) + len(external_entries)
    nav_items = ["  { label: 'Start Here', link: '/start-here/' }"]
    skills_nav = "  { label: 'Skills', link: '/skills/'"
    if total_skills:
        skills_nav += f", badge: '{total_skills}'"
    skills_nav += " }"
    nav_items.append(skills_nav)
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
    lines.append("  { slug: 'start-here', label: 'Start Here' },")

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

    if external_entries:
        lines.append(f"      {{ label: 'External Sources ({len(external_entries)})', slug: 'external-skills' }},")

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
    external_entries = read_external_skill_entries()
    # Also collect installed if content dir exists
    if CONTENT_DIR.exists():
        existing_ids = {n.id for n in nodes if n.kind == "skill"}
        installed = collect_installed_skills(existing_ids)
        nodes.extend(installed)

    skills = [n for n in nodes if n.kind == "skill"]
    agents_list = [n for n in nodes if n.kind == "agent"]
    mcps = [n for n in nodes if n.kind == "mcp"]

    write_sidebar(nodes)
    write_skills_index(skills, external_entries)
    write_external_skills_page(external_entries)
    installed_skills = [n for n in skills if n.source != "custom"]
    if installed_skills:
        write_installed_skills_page(installed_skills)
    if agents_list:
        write_agents_index(agents_list)
    if mcps:
        write_mcp_index(mcps)
    write_site_data(nodes, external_entries)
    write_index_page(nodes, external_entries)


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


def _docs_generate_impl(*, include_drafts: bool, include_installed: bool) -> None:
    """Generate MDX content pages from repo assets."""
    # Clean existing generated content (preserves hand-maintained files)
    for subdir in ["skills", "agents", "mcp"]:
        _clean_content_subdir(CONTENT_DIR / subdir)
    # Remove generated top-level pages
    for f in ["index.mdx", "cli.mdx", "external-skills.mdx"]:
        p = CONTENT_DIR / f
        if p.exists():
            p.unlink()
    # Remove generated sidebar
    sidebar_path = DOCS_DIR / "src" / "generated-sidebar.mjs"
    if sidebar_path.exists():
        sidebar_path.unlink()

    nodes = collect_nodes()
    external_entries = read_external_skill_entries()

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

    write_skills_index(skills, external_entries)
    typer.echo("  Generated skills/index.mdx")
    write_external_skills_page(external_entries)
    typer.echo("  Generated external-skills.mdx")
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
    write_site_data(nodes, external_entries)
    write_index_page(nodes, external_entries)
    typer.echo("  Generated index.mdx")
    write_cli_page()
    typer.echo("  Generated cli.mdx")

    # Generate sidebar
    write_sidebar(nodes)
    typer.echo("  Generated generated-sidebar.mjs")

    typer.echo(f"Generated {len(nodes)} pages + indexes + sidebar")


@docs_app.command("generate")
def docs_generate(
    include_drafts: bool = typer.Option(False, "--include-drafts", help="Include draft skills"),
    include_installed: bool = typer.Option(
        False,
        "--include-installed/--no-installed",
        help="Include installed skills discovered from local agent skill directories in generated docs",
    ),
):
    """Generate MDX content pages from repo assets."""
    if isinstance(include_drafts, OptionInfo):
        include_drafts = include_drafts.default
    if isinstance(include_installed, OptionInfo):
        include_installed = include_installed.default
    _docs_generate_impl(include_drafts=include_drafts, include_installed=include_installed)


@docs_app.command("dev")
def docs_dev():
    """Generate content and start dev server."""
    _docs_generate_impl(include_drafts=False, include_installed=False)
    typer.echo("Starting dev server...")
    subprocess.run(["pnpm", "dev"], cwd=str(DOCS_DIR))


@docs_app.command("build")
def docs_build():
    """Generate content and build static site."""
    _docs_generate_impl(include_drafts=False, include_installed=False)
    typer.echo("Building...")
    result = subprocess.run(["pnpm", "build"], cwd=str(DOCS_DIR))
    if result.returncode != 0:
        typer.echo("Error: build failed", err=True)
        raise typer.Exit(code=1)
    typer.echo("Build complete. Output in docs/dist/")


@docs_app.command("preview")
def docs_preview():
    """Generate, build, and preview the site."""
    _docs_generate_impl(include_drafts=False, include_installed=False)
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
