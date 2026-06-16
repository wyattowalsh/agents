"""Documentation site generation: indexes, sidebar, and docs subcommands."""

import json
import re
import subprocess
from pathlib import Path

import typer
from typer.models import OptionInfo

from wagents import CONTENT_DIR, DOCS_DIR, ROOT
from wagents.catalog import collect_edges
from wagents.external_skills import ExternalSkillEntry, read_external_skill_entries
from wagents.parsing import escape_attr, truncate_sentence
from wagents.rendering import render_page
from wagents.site_model import (
    VISUAL_ASSET_BY_ID,
    agent_flags,
    build_install_command,
    render_site_data_module,
    render_visual_assets_css,
    site_data,
)
from wagents.skill_docs import (
    SKILL_DETAIL_SLUG_PREFIX,
    collect_all_doc_nodes,
    collect_skill_doc_nodes,
    skill_detail_href,
)
from wagents.skill_research import (
    RESEARCH_DIR,
    build_batch_prompt,
    partition_skills_by_source,
    partition_skills_for_research,
    research_artifact_path,
    research_coverage,
    seed_curated_config_research,
    seed_phase_a_research,
    update_research_manifest,
    validate_artifact,
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
    if external_entries is None:
        external_entries = read_external_skill_entries()
    data = site_data(
        nodes,
        mcp_config_count=_count_mcp_servers_from_config(),
        has_mcp_overview=_has_mcp_overview_page(),
        external_skills=external_entries,
    )
    (DOCS_DIR / "src" / "generated-site-data.mjs").write_text(render_site_data_module(data), encoding="utf-8")
    public_index_dir = DOCS_DIR / "public" / "generated-skill-indexes"
    public_index_dir.mkdir(parents=True, exist_ok=True)
    for stale in ("custom.json", "external.json", "all.json", "installed.json"):
        stale_path = public_index_dir / stale
        if stale_path.exists():
            stale_path.unlink()
    (public_index_dir / "install-scripts.json").write_text(
        json.dumps(data["skillInstallScripts"], indent=2, sort_keys=True), encoding="utf-8"
    )
    indexes_mjs = DOCS_DIR / "src" / "generated-skill-indexes.mjs"
    if indexes_mjs.exists():
        indexes_mjs.unlink()
    update_research_manifest()
    (DOCS_DIR / "src" / "generated-visual-assets.css").write_text(render_visual_assets_css(), encoding="utf-8")


def _mdx_asset_import_path(src: str) -> str:
    """Return a generated MDX import path for an asset under docs/src/assets."""
    if not src.startswith("/src/assets/"):
        raise ValueError(f"Expected docs src asset path, got {src!r}")
    return "../../assets/" + src.removeprefix("/src/assets/")


def write_index_page(nodes: list, external_entries: list[ExternalSkillEntry] | None = None) -> None:
    """Write the index.mdx splash page."""
    if external_entries is None:
        external_entries = read_external_skill_entries()
    data = site_data(
        nodes,
        mcp_config_count=_count_mcp_servers_from_config(),
        has_mcp_overview=_has_mcp_overview_page(),
        external_skills=external_entries,
    )
    skills = [n for n in nodes if n.kind == "skill"]
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
        '  <LinkCard title="OpenSpec Workflow" href="/skills/catalog/openspec-workflow/"'
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
            "No bundled agent definitions were discovered for this generated docs snapshot, "
            "while the MCP overview is a hand-maintained summary of "
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
            "No bundled agent definitions were discovered for this generated docs snapshot. "
            "Repo workflow and policy truth lives "
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
        ' href="/skills/catalog/skill-creator/"'
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
        "Also validates hook registry, harness paths, and lifecycle event names via "
        "`scripts/validate/validate_repo.py`."
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
    parts.append(
        "| **Hooks** | Registry entries, runner paths, harness coverage, and known lifecycle events "
        "across skills, agents, and settings |"
    )
    parts.append("")
    parts.append("The command exits with code 1 if any validation fails, printing each error to stdout.")
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
        "`cursor`, `gemini-cli`, `github-copilot`, `grok`, `opencode`"
    )
    parts.append("")
    parts.append('<Aside type="note" title="Grok Build install alias">')
    parts.append(
        "Skills CLI has no native `grok` adapter. `wagents install -a grok` and "
        "`wagents skills sync -a grok` install via the `claude-code` adapter, then "
        "mirror missing skills into `~/.grok/skills`."
    )
    parts.append("</Aside>")
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("### `wagents grok plannotator install` -- Plannotator for Grok")
    parts.append("")
    parts.append(
        "Install the Plannotator CLI, core slash skills, optional extras, mirror into `~/.grok/skills`, "
        "and sync repo-managed plan-review hooks to `~/.grok/hooks/plannotator.json`. "
        "Grok has no npm plugin like OpenCode's `@plannotator/opencode`."
    )
    parts.append("")
    parts.append("```bash")
    parts.append("wagents grok plannotator install")
    parts.append("wagents grok plannotator install --no-extras --no-hooks")
    parts.append("wagents grok plannotator sync")
    parts.append("```")
    parts.append("")
    parts.append(
        "Grok home sync enables Plannotator hooks and skill overlays by default. "
        "Pass `--no-plannotator-hooks` to `sync_agent_stack.py` to skip hook refresh."
    )
    parts.append("")
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("### `wagents grok doctor` -- Grok Build diagnostics")
    parts.append("")
    parts.append(
        "Report Grok config paths, managed MCP/policy blocks, experimental env vars, skill roots, "
        "and Plannotator binary/skills/hooks status:"
    )
    parts.append("")
    parts.append("```bash")
    parts.append("wagents grok doctor")
    parts.append("```")
    parts.append("")
    parts.append("Source optional env defaults before sessions:")
    parts.append("")
    parts.append("```bash")
    parts.append("source config/grok-env.sh")
    parts.append("```")
    parts.append("")
    parts.append("Isolated home sync (skips OpenCode and other harness home merges):")
    parts.append("")
    parts.append("```bash")
    parts.append("uv run python scripts/sync_agent_stack.py --apply --platforms grok --targets home")
    parts.append("```")
    parts.append("")
    parts.append(
        "Repo-owned policy lives in `config/grok-config.toml`; project MCP projection is "
        "`.grok/config.toml`; full home merge targets `~/.grok/config.toml`. Blend-owned "
        "tables (`ui`, `features`, etc.) keep user-only keys while repo policy overrides shared keys."
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
    parts.append("# Default: repository-only catalog (CI parity)")
    parts.append("wagents docs generate --no-installed")
    parts.append("")
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
        "By default, generation is deterministic and repository-only (`--no-installed`). Opt in with `--include-installed` for local harness inventory rows. The generator creates "
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
            'description="See the current bundle surface and generated docs inputs." />'
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



def _skill_source_group(node) -> str:
    """Map a catalog node to a hub grouping label."""
    if node.source == "custom":
        return "custom"
    if node.source == "installed":
        return "installed"
    return "curated-external"


def _skill_group_title(group: str) -> str:
    return {
        "custom": "Custom Skills",
        "installed": "Installed External",
        "curated-external": "Curated External",
    }.get(group, group)


_LINKABLE_SKILL_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _skill_id_is_linkable(skill_id: str) -> bool:
    """Return whether a skill id is safe for Starlight catalog routes."""
    return _LINKABLE_SKILL_ID.fullmatch(skill_id) is not None


def _render_skill_linkcards(nodes: list, *, limit: int | None = None) -> list[str]:
    """Render LinkCard rows for skill hub pages."""
    rows = sorted(nodes, key=lambda item: item.id)
    if limit is not None:
        rows = rows[:limit]
    parts: list[str] = []
    for node in rows:
        desc = escape_attr(truncate_sentence(node.description, 160))
        if _skill_id_is_linkable(node.id):
            href = skill_detail_href(node.id)
            title = escape_attr(node.id)
            parts.append(
                f'  <LinkCard title="{title}" href="{href}" description="{desc}" />'
            )
        else:
            parts.append(f'  <Card title="{escape_attr(node.id)}">{desc}</Card>')
    return parts


def write_skills_index(nodes: list) -> None:
    """Write skills/index.mdx as the repo-owned custom skill catalog."""
    custom = [n for n in nodes if n.kind == "skill" and n.source == "custom"]
    user_invocable = [n for n in custom if n.metadata.get("user-invocable") is not False]
    auto_invoke = [n for n in custom if n.metadata.get("user-invocable") is False]

    parts = [
        "---",
        "title: Custom Skills",
        "description: Browse repo-owned AI agent skills",
        "---",
        "",
        "import { Card, CardGrid, LinkCard, Badge, Aside } from '@astrojs/starlight/components';",
        "import InstallCommand from '../../../components/InstallCommand.astro';",
        "import { installCommands } from '../../../generated-site-data.mjs';",
        "",
        "These are the repo-owned skills in `./skills/`. Detail pages live under "
        f"`/{SKILL_DETAIL_SLUG_PREFIX}/<name>/`. Use [All Skills](/skills/all/) for the combined index.",
        "",
        "### Quick Install",
        "",
        '<InstallCommand command={installCommands.all} title="Install this repository catalog" '
        'note="Use the copy button or scroll horizontally inside the command area." />',
        "",
        '<InstallCommand command={installCommands.starter} title="Install a focused starter skill" />',
        "",
        '<Aside type="tip" title="How to use this page">',
        "Every card here corresponds to one tracked `skills/<name>/SKILL.md` file.",
        "</Aside>",
        "",
        '<div class="stats-bar">',
        f'  <span class="stat stat-skill">{len(custom)} Custom Skills</span>',
        f'  <span class="stat stat-installed">{len(user_invocable)} User-Invocable</span>',
        f'  <span class="stat stat-agent">{len(auto_invoke)} Convention Skills</span>',
        "</div>",
        "",
        "## Skill Lanes",
        "",
        "<CardGrid>",
        f'  <LinkCard title="Review & QA" href="{skill_detail_href("honest-review")}" '
        'description="Code review, docs QA, test strategy, performance, or security scanning." />',
        f'  <LinkCard title="Build & Design" href="{skill_detail_href("frontend-designer")}" '
        'description="Use these when you are creating frontends, APIs, data systems, infra, or MCP servers." />',
        f'  <LinkCard title="Strategy & Research" href="{skill_detail_href("research")}" '
        'description="Fuzzy problems, real trade-offs, or deeper investigation first." />',
        f'  <LinkCard title="Workflow & Utility" href="{skill_detail_href("orchestrator")}" '
        'description="Coordinate work, simplify code, git flow, releases, or local file tasks." />',
        "</CardGrid>",
        "",
    ]

    if user_invocable:
        parts.extend(
            [
                f"## User-Invocable Skills ({len(user_invocable)})",
                "",
                '<Badge text="Manual invocation" variant="tip" /> '
                "Call these when you want a specialist on demand. They appear in the autocomplete menu.",
                "",
                '<div class="catalog-skill">',
                "<CardGrid>",
                *_render_skill_linkcards(user_invocable),
                "</CardGrid>",
                "</div>",
                "",
            ]
        )

    if auto_invoke:
        parts.extend(
            [
                f"## Convention Skills ({len(auto_invoke)})",
                "",
                '<Badge text="Auto-invoked" variant="caution" /> '
                "The agent loads these automatically when repo context matches. They stay out of the `/` menu.",
                "",
                '<div class="catalog-skill">',
                "<CardGrid>",
                *_render_skill_linkcards(auto_invoke),
                "</CardGrid>",
                "</div>",
                "",
            ]
        )

    parts.extend(
        [
            "---",
            "",
            "## Installing Individual Skills",
            "",
            "You can also install specific skills rather than the full collection:",
            "",
            "```bash",
            "# Install a single skill globally",
            build_install_command(skill="honest-review"),
            "",
            "# Install multiple specific skills",
            build_install_command(skills=("honest-review", "wargame")),
            "",
            "# Install to a specific agent only",
            build_install_command(skill="orchestrator", agent_ids=("claude-code",)),
            "```",
            "",
            '<Aside type="tip" title="Creating your own skills">',
            f"Want to build a custom skill? Use the [skill-creator]({skill_detail_href('skill-creator')}) "
            "to scaffold, develop, audit, and package skills following proven structural patterns. "
            "Or run `wagents new skill my-skill` from the [CLI](/cli/).",
            "</Aside>",
        ]
    )

    out_dir = CONTENT_DIR / "skills"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.mdx").write_text("\n".join(parts))


def write_all_skills_index(nodes: list) -> None:
    """Write skills/all.mdx as the deduped combined skill index."""
    skills = [n for n in nodes if n.kind == "skill"]
    groups: dict[str, list] = {"custom": [], "installed": [], "curated-external": []}
    for node in skills:
        groups.setdefault(_skill_source_group(node), []).append(node)

    parts = [
        "---",
        "title: All Skills",
        "description: Combined index of custom, curated external, and installed external skills",
        "---",
        "",
        "import { Aside, Card, CardGrid, LinkCard } from '@astrojs/starlight/components';",
        "",
        "# All Skills",
        "",
        "This generated index combines repo-owned custom skills, curated external (config-enriched), and installed external "
        "skills. Each row links to the unified detail page under "
        f"`/{SKILL_DETAIL_SLUG_PREFIX}/<name>/`.",
        "",
        '<div class="stats-bar">',
        f'  <span class="stat stat-skill">{len(groups["custom"])} Custom</span>',
        f'  <span class="stat stat-external">{len(groups["curated-external"])} Curated External</span>',
        f'  <span class="stat stat-installed">{len(groups["installed"])} Installed External</span>',
        f'  <span class="stat stat-agent">{len(skills)} Total</span>',
        "</div>",
        "",
        '<Aside type="note" title="Installed skills are external">',
        "Local installed skills appear here unless their name already exists under `./skills/`. "
        "Regenerate with `uv run wagents docs generate` to refresh the installed inventory from local harnesses.",
        "</Aside>",
        "",
    ]

    for group in ("custom", "curated-external", "installed"):
        rows = sorted(groups.get(group, []), key=lambda item: item.id)
        if not rows:
            continue
        parts.append(f"## {_skill_group_title(group)} ({len(rows)})")
        parts.append("")
        parts.append("<details>")
        parts.append(f"<summary>Browse {len(rows)} {_skill_group_title(group).lower()}</summary>")
        parts.append("")
        parts.append('<div class="catalog-skill">')
        parts.append("<CardGrid>")
        parts.extend(_render_skill_linkcards(rows))
        parts.append("</CardGrid>")
        parts.append("</div>")
        parts.append("</details>")
        parts.append("")

    out_dir = CONTENT_DIR / "skills"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "all.mdx").write_text("\n".join(parts))


def write_skill_install_scripts_page() -> None:
    """Write skills/install.mdx with copyable install scripts."""
    parts = [
        "---",
        "title: Skill Install Scripts",
        "description: Copyable install commands for custom and external skills",
        "---",
        "",
        "import InstallScripts from '../../../components/InstallScripts.astro';",
        "",
        "# Skill Install Scripts",
        "",
        "The canonical portable install path is `npx skills add`. `uv run wagents ...` commands are repo-local "
        "control-plane commands for validation and reconciliation, not a replacement for Skills CLI installation.",
        "",
        '<InstallScripts src="/generated-skill-indexes/install-scripts.json" />',
    ]

    out_dir = CONTENT_DIR / "skills"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "install.mdx").write_text("\n".join(parts))


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




def write_harness_support_page() -> None:
    """Generate public harness support honesty matrix."""
    import json

    harness_registry = json.loads((ROOT / "config" / "harness-surface-registry.json").read_text(encoding="utf-8"))
    fixture_support = json.loads(
        (ROOT / "planning/manifests/harness-fixture-support.json").read_text(encoding="utf-8")
    )
    support_by_id = {record["harness_id"]: record for record in fixture_support.get("records", [])}

    parts = [
        "---",
        "title: Harness Support Matrix",
        "description: Honest support tiers and fixture status for each agent harness",
        "---",
        "",
        "{/* Auto-generated by wagents docs generate - do not edit */}",
        "",
        "import { Aside, Badge } from '@astrojs/starlight/components';",
        "",
        "Public honesty matrix for repo-managed harness surfaces. No harness is labeled **validated** until fixture-backed CI is green.",
        "",
        '<Aside type="caution" title="Stranger defaults">',
        "Use MCPHub only when you explicitly opt in. Repo docs and public catalog default to repository + curated skills (`wagents docs generate --no-installed`).",
        "</Aside>",
        "",
        "| Harness | Support tier | Fixture status | Validation commands |",
        "| ------- | ------------ | -------------- | ------------------- |",
    ]
    for harness in harness_registry.get("harnesses", []):
        harness_id = str(harness.get("id") or "")
        evidence = support_by_id.get(harness_id, {})
        cmds = evidence.get("validation_commands") or []
        cmd_cell = "<br />".join(f"`{cmd}`" for cmd in cmds[:3]) if cmds else "—"
        parts.append(
            f"| {harness.get('label', harness_id)} | `{harness.get('support_tier', '')}` | "
            f"`{evidence.get('fixture_status', '')}` | {cmd_cell} |"
        )
    parts.extend([
        "",
        "## Executable fixtures today",
        "",
        "These harnesses have **fixture-executable** status in `planning/manifests/harness-fixture-support.json`:",
        "",
    ])
    for record in fixture_support.get("records", []):
        if record.get("fixture_status") == "fixture-executable":
            parts.append(f"- `{record['harness_id']}` — {record.get('promotion_blocker', '').strip()}")
    parts.append("")
    out = CONTENT_DIR / "harness-support.mdx"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")


def write_sidebar(nodes: list) -> None:
    """Write docs/src/generated-sidebar.mjs with dynamic sidebar config."""
    skills = [n for n in nodes if n.kind == "skill"]
    custom_skills = [n for n in skills if n.source == "custom"]
    agents = [n for n in nodes if n.kind == "agent"]
    mcps = [n for n in nodes if n.kind == "mcp"]
    mcp_config_count = _count_mcp_servers_from_config()
    mcp_overview_path = CONTENT_DIR / "mcp" / "index.mdx"
    total_skills = len(skills)

    lines = []
    lines.append("// Auto-generated by wagents docs generate — do not edit")
    lines.append("export const navLinks = [")
    nav_items = [
        "  { label: 'Start Here', link: '/start-here/' }",
        "  { label: 'Contributing', link: '/contributing/' }",
        "  { label: 'Harness Support', link: '/harness-support/' }",
    ]
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
    lines.append("  { slug: 'contributing', label: 'Contributing' },")
    lines.append("  { slug: 'harness-support', label: 'Harness Support' },")
    lines.append("  {")
    lines.append("    label: 'Skills',")
    lines.append(f"    badge: {{ text: '{total_skills}', variant: 'tip' }},")
    lines.append("    collapsed: true,")
    lines.append("    items: [")
    lines.append(f"      {{ slug: 'skills', label: 'Custom Skills ({len(custom_skills)})' }},")
    lines.append(f"      {{ slug: 'skills/all', label: 'All Skills ({total_skills})' }},")
    lines.append("      { slug: 'skills/install', label: 'Install Scripts' },")
    lines.append("      {")
    lines.append(f"        label: 'Catalog ({total_skills})',")
    lines.append("        autogenerate: { directory: 'skills/catalog' },")
    lines.append("      },")
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


def regenerate_sidebar_and_indexes(*, include_installed: bool = False) -> None:
    """Regenerate sidebar and index pages from current nodes."""
    nodes = collect_all_doc_nodes(include_installed=include_installed, include_drafts=False)
    external_entries = read_external_skill_entries()

    skills = [n for n in nodes if n.kind == "skill"]
    agents_list = [n for n in nodes if n.kind == "agent"]
    mcps = [n for n in nodes if n.kind == "mcp"]

    write_sidebar(nodes)
    write_skills_index(skills)
    write_all_skills_index(skills)
    write_skill_install_scripts_page()
    if agents_list:
        write_agents_index(agents_list)
    if mcps:
        write_mcp_index(mcps)
    write_site_data(nodes, external_entries)
    write_index_page(nodes, external_entries)
    write_harness_support_page()


# ---------------------------------------------------------------------------
# Sentinel-aware clean helper
# ---------------------------------------------------------------------------


def _is_hand_maintained_mdx(path: Path) -> bool:
    """Return whether an MDX file should be preserved during clean."""
    if path.suffix != ".mdx":
        return False
    try:
        return "HAND-MAINTAINED" in path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False


def _resolve_typer_option(value: object, *, default: object = None) -> object:
    """Coerce Typer OptionInfo (seen on some direct-invocation/test paths) to resolved value.

    Extracts .default when an OptionInfo instance is passed instead of the
    concrete bool/int/str/etc; falls back to caller-supplied default when None.
    """
    if isinstance(value, OptionInfo):
        value = value.default
    if value is None:
        value = default
    return value


def _clean_content_subdir(d: Path) -> bool:
    """Remove generated files from *d*, preserving hand-maintained ones recursively.

    Returns True if any items were removed.
    """
    if not d.exists():
        return False

    cleaned = False
    for item in sorted(d.rglob("*"), key=lambda path: len(path.parts), reverse=True):
        if item.is_file():
            if _is_hand_maintained_mdx(item):
                typer.echo(f"  Preserved {item.relative_to(CONTENT_DIR)} (hand-maintained)")
                continue
            item.unlink()
            cleaned = True
        elif item.is_dir() and item != d and not any(item.iterdir()):
            item.rmdir()
            cleaned = True

    if not any(d.iterdir()):
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
    for subdir in ["skills", "agents", "mcp"]:
        _clean_content_subdir(CONTENT_DIR / subdir)
    for f in ["index.mdx", "cli.mdx", "harness-support.mdx"]:
        p = CONTENT_DIR / f
        if p.exists() and not _is_hand_maintained_mdx(p):
            p.unlink()
    external_path = CONTENT_DIR / "external-skills.mdx"
    if external_path.exists():
        external_path.unlink()
    sidebar_path = DOCS_DIR / "src" / "generated-sidebar.mjs"
    if sidebar_path.exists():
        sidebar_path.unlink()

    nodes = collect_all_doc_nodes(include_installed=include_installed, include_drafts=include_drafts)
    external_entries = read_external_skill_entries()
    installed_count = len([n for n in nodes if n.kind == "skill" and n.source == "installed"])
    if installed_count:
        typer.echo(f"  Found {installed_count} installed external skills")

    edges = collect_edges(nodes)
    catalog_dir = CONTENT_DIR / SKILL_DETAIL_SLUG_PREFIX
    catalog_dir.mkdir(parents=True, exist_ok=True)

    for node in nodes:
        if node.kind == "skill":
            out_file = catalog_dir / f"{node.id}.mdx"
            rel = f"{SKILL_DETAIL_SLUG_PREFIX}/{node.id}.mdx"
        else:
            kind_dir = f"{node.kind}s" if node.kind != "mcp" else "mcp"
            page_dir = CONTENT_DIR / kind_dir
            page_dir.mkdir(parents=True, exist_ok=True)
            out_file = page_dir / f"{node.id}.mdx"
            rel = f"{kind_dir}/{node.id}.mdx"
        if out_file.exists() and _is_hand_maintained_mdx(out_file):
            typer.echo(f"  Preserved {rel} (hand-maintained)")
            continue
        out_file.write_text(render_page(node, edges, nodes))
        typer.echo(f"  Generated {rel}")

    skills = [n for n in nodes if n.kind == "skill"]
    agents = [n for n in nodes if n.kind == "agent"]
    mcps = [n for n in nodes if n.kind == "mcp"]

    write_skills_index(skills)
    typer.echo("  Generated skills/index.mdx")
    write_all_skills_index(skills)
    typer.echo("  Generated skills/all.mdx")
    write_skill_install_scripts_page()
    typer.echo("  Generated skills/install.mdx")
    if agents:
        write_agents_index(agents)
        typer.echo("  Generated agents/index.mdx")
    if mcps:
        write_mcp_index(mcps)
        typer.echo("  Generated mcp/index.mdx")

    write_site_data(nodes, external_entries)
    write_index_page(nodes, external_entries)
    typer.echo("  Generated index.mdx")
    write_cli_page()
    typer.echo("  Generated cli.mdx")
    write_harness_support_page()
    typer.echo("  Generated harness-support.mdx")

    write_sidebar(nodes)
    typer.echo("  Generated generated-sidebar.mjs")

    typer.echo(f"Generated {len(nodes)} pages + indexes + sidebar")


@docs_app.command("generate")
def docs_generate(
    include_drafts: bool = typer.Option(False, "--include-drafts", help="Include draft skills"),
    include_installed: bool = typer.Option(
        False,
        "--include-installed/--no-installed",
        help="Include installed skills as external rows unless they already exist under ./skills",
    ),
):
    """Generate MDX content pages from repo assets."""
    include_drafts = _resolve_typer_option(include_drafts, default=False)
    include_installed = _resolve_typer_option(include_installed, default=False)
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




def _research_coverage_types(resolved_source_type: str, *, include_installed: bool) -> list[str]:
    """Return source types to report when checking research cache coverage."""
    if resolved_source_type != "all":
        return [resolved_source_type]
    types = ["custom", "curated-external"]
    if include_installed:
        types.append("installed")
    return types


@docs_app.command("research")
def docs_research(
    dry_run: bool = typer.Option(False, "--dry-run", help="Print batch plan without writing artifacts"),
    include_installed: bool = typer.Option(
        False,
        "--include-installed/--no-installed",
        help="Include installed and curated external skills in research batches",
    ),
    batch_size: int = typer.Option(25, "--batch-size", help="Skills per research batch"),
    source_type: str = typer.Option(
        "all",
        "--source-type",
        help="Filter batches to custom, installed, curated-external, or all",
    ),
    skill: str | None = typer.Option(
        None,
        "--skill",
        help="Research a single skill id instead of batching the full catalog",
    ),
    check_research: bool = typer.Option(
        False,
        "--check-research",
        help="Exit 1 when cached research coverage is below 100% for the selected source type",
    ),
    seed_from_repo: bool = typer.Option(
        False,
        "--seed-from-repo",
        help="Write Phase A research artifacts grounded in repo SKILL.md (custom skills only)",
    ),
    seed_from_config: bool = typer.Option(
        False,
        "--seed-from-config",
        help="Write research artifacts for curated-external from config/external-skills.md fields (W1)",
    ),
    curated_status: str | None = typer.Option(
        None,
        "--curated-status",
        help="Filter curated external by status (e.g. install-now-after-trust-gate) for seed/partition/waves",
    ),
    validate_artifacts: bool = typer.Option(
        False,
        "--validate-artifacts",
        help="Validate existing research (and upstream) artifacts for frontmatter, sections, local-path redaction",
    ),
    emit_waves: bool = typer.Option(
        False,
        "--emit-waves",
        help="Emit orchestrator batch packets using partition_skills_by_source (GROUP BY install_source)",
    ),
):
    """Plan or refresh cached per-skill web research artifacts. Supports seed-from-repo/config, grouped waves, artifact validation."""
    dry_run = _resolve_typer_option(dry_run, default=False)
    include_installed = _resolve_typer_option(include_installed, default=False)
    batch_size = _resolve_typer_option(batch_size, default=25) or 25
    resolved_source_type = _resolve_typer_option(source_type, default="all") or "all"
    resolved_skill = _resolve_typer_option(skill, default=None)
    check_research = _resolve_typer_option(check_research, default=False)
    seed_from_repo = _resolve_typer_option(seed_from_repo, default=False)
    seed_from_config = _resolve_typer_option(seed_from_config, default=False)
    resolved_curated_status = _resolve_typer_option(curated_status, default=None)
    validate_artifacts = _resolve_typer_option(validate_artifacts, default=False)
    emit_waves = _resolve_typer_option(emit_waves, default=False)

    allowed = {"all", "custom", "installed", "curated-external"}
    if resolved_source_type not in allowed:
        typer.echo(f"Error: --source-type must be one of {sorted(allowed)}", err=True)
        raise typer.Exit(code=1)

    source_types = None if resolved_source_type == "all" else {resolved_source_type}
    doc_nodes = collect_skill_doc_nodes(include_installed=include_installed, include_curated=True)
    if source_types is not None:
        doc_nodes = [node for node in doc_nodes if node.source_type in source_types]
    if resolved_skill:
        doc_nodes = [node for node in doc_nodes if node.id == resolved_skill]
        if not doc_nodes:
            typer.echo(f"Error: skill not found in catalog: {resolved_skill}", err=True)
            raise typer.Exit(code=1)

    if seed_from_repo:
        if resolved_source_type not in {"all", "custom"}:
            typer.echo("Error: --seed-from-repo only supports --source-type custom or all", err=True)
            raise typer.Exit(code=1)
        custom_nodes = [node for node in doc_nodes if node.source_type == "custom"]
        if resolved_skill:
            custom_nodes = [node for node in custom_nodes if node.id == resolved_skill]
        if dry_run:
            missing = [node for node in custom_nodes if not research_artifact_path(node.id).exists()]
            typer.echo(f"Would seed {len(missing)} research artifact(s) from repository SKILL.md")
        else:
            written = seed_phase_a_research(custom_nodes, overwrite=bool(resolved_skill))
            typer.echo(f"Seeded {len(written)} research artifact(s) from repository SKILL.md")
        present, total = research_coverage(custom_nodes or doc_nodes, source_type="custom")
        typer.echo(f"Research cache coverage (custom): {present}/{total}")
        if check_research and total and present < total:
            typer.echo(
                f"Error: research cache incomplete for custom: {present}/{total}",
                err=True,
            )
            raise typer.Exit(code=1)
        return

    if seed_from_config:
        if resolved_source_type not in {"all", "curated-external"}:
            typer.echo("Error: --seed-from-config only supports --source-type curated-external or all", err=True)
            raise typer.Exit(code=1)
        if dry_run:
            typer.echo(f"Would seed curated research artifacts (status={resolved_curated_status or 'any'})")
        else:
            written = seed_curated_config_research(
                curated_status=resolved_curated_status, overwrite=bool(resolved_skill)
            )
            typer.echo(f"Seeded {len(written)} curated research artifact(s) from config")
        cov_nodes = [n for n in doc_nodes if n.source_type == "curated-external"]
        present, total = research_coverage(cov_nodes, source_type="curated-external", curated_status=resolved_curated_status)
        typer.echo(f"Research cache coverage (curated-external): {present}/{total}")
        if check_research and total and present < total:
            typer.echo(f"Error: research cache incomplete for curated-external: {present}/{total}", err=True)
            raise typer.Exit(code=1)
        return

    if emit_waves:
        # Use the fixed partition that groups by install_source then chunks
        batches = partition_skills_by_source(
            batch_max=batch_size if not resolved_skill else max(len(doc_nodes), 1),
            curated_status=resolved_curated_status,
            include_installed=include_installed,
        )
        if source_types is not None:
            batches = [[d for d in b if d.source_type in source_types] for b in batches]
            batches = [b for b in batches if b]
        typer.echo(f"Emit waves (grouped by _skills_install_source): {len(batches)} batches")
        for index, batch in enumerate(batches, start=1):
            names = ", ".join(d.id for d in batch)
            srcs = ", ".join(sorted({str((d.node.metadata or {}).get("_skills_install_source", ""))[:40] for d in batch}))
            typer.echo(f"  WaveBatch {index}: {len(batch)} skills (sources: {srcs}) — {names}")
            if dry_run:
                typer.echo(build_batch_prompt(batch))
                typer.echo("")
        if not dry_run:
            update_research_manifest()
            typer.echo("Updated manifest after wave emission planning.")
        return

    if validate_artifacts:
        errors: list[tuple[str, list[str]]] = []
        if RESEARCH_DIR.exists():
            for p in sorted(RESEARCH_DIR.glob("*.md")):
                errs = validate_artifact(p)
                if errs:
                    errors.append((str(p.relative_to(RESEARCH_DIR.parent.parent)), errs))
        # also check upstream if present (lazy) — simple local path scan
        _local_re = re.compile(r"(/Users/|/home/|/private/)")
        upstream_dir = DOCS_DIR / "src" / "skill-upstream"
        if upstream_dir.exists():
            for p in sorted(upstream_dir.glob("*.md")):
                txt = p.read_text(encoding="utf-8")
                if _local_re.search(txt):
                    errors.append((str(p), ["contains local path (upstream)"]))
        if errors:
            for rel, es in errors:
                typer.echo(f"INVALID {rel}: {es}")
            if check_research or not dry_run:
                raise typer.Exit(code=1)
        else:
            typer.echo("All research (and upstream) artifacts validated (no local paths, required fields/sections present).")
        return

    batches = partition_skills_for_research(
        doc_nodes,
        batch_size=batch_size if not resolved_skill else max(len(doc_nodes), 1),
        include_installed=include_installed,
        source_types=None,
    )
    typer.echo(f"Research batches: {len(batches)} (batch_size={batch_size})")
    for index, batch in enumerate(batches, start=1):
        names = ", ".join(doc.id for doc in batch)
        typer.echo(f"  Batch {index}: {len(batch)} skills — {names}")
        if dry_run:
            typer.echo(build_batch_prompt(batch))
            typer.echo("")

    if not dry_run and not seed_from_repo and not seed_from_config:
        typer.echo(
            "Note: this command does not auto-write research artifacts. "
            "Use --dry-run prompts for agent batches or --seed-from-repo/--seed-from-config for seeding."
        )

    coverage_types = _research_coverage_types(resolved_source_type, include_installed=include_installed)
    incomplete: list[tuple[str, int, int]] = []
    for coverage_type in coverage_types:
        present, total = research_coverage(doc_nodes, source_type=coverage_type, curated_status=resolved_curated_status)
        typer.echo(f"Research cache coverage ({coverage_type}): {present}/{total}")
        if check_research and total and present < total:
            incomplete.append((coverage_type, present, total))
    if incomplete:
        for coverage_type, present, total in incomplete:
            typer.echo(
                f"Error: research cache incomplete for {coverage_type}: {present}/{total}",
                err=True,
            )
        raise typer.Exit(code=1)
    if not dry_run:
        update_research_manifest()
        typer.echo("Updated generated-skill-research-index.mjs")


@docs_app.command("clean")
def docs_clean():
    """Remove generated content pages (preserves hand-written content like guides/)."""
    cleaned = False
    for subdir in ["skills", "agents", "mcp"]:
        if _clean_content_subdir(CONTENT_DIR / subdir):
            cleaned = True
    for f in ["index.mdx", "cli.mdx", "harness-support.mdx"]:
        p = CONTENT_DIR / f
        if p.exists() and not _is_hand_maintained_mdx(p):
            p.unlink()
            cleaned = True
    external_path = CONTENT_DIR / "external-skills.mdx"
    if external_path.exists():
        external_path.unlink()
        cleaned = True
    sidebar_path = DOCS_DIR / "src" / "generated-sidebar.mjs"
    if sidebar_path.exists():
        sidebar_path.unlink()
        cleaned = True
    if cleaned:
        typer.echo("Cleaned generated content pages")
    else:
        typer.echo("Nothing to clean")
