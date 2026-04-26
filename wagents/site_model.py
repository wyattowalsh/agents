"""Shared data model for generated docs and install surfaces."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from wagents.catalog import CatalogNode

REPO_SOURCE = "github:wyattowalsh/agents"


@dataclass(frozen=True)
class SupportedAgent:
    id: str
    label: str
    href: str
    description: str


SUPPORTED_AGENTS: tuple[SupportedAgent, ...] = (
    SupportedAgent(
        "antigravity",
        "Antigravity",
        "https://antigravity.google/",
        "Advanced Agentic Coding assistant.",
    ),
    SupportedAgent(
        "claude-code",
        "Claude Code",
        "https://docs.anthropic.com/en/docs/claude-code",
        "Anthropic's official CLI for Claude.",
    ),
    SupportedAgent(
        "codex",
        "Codex",
        "https://github.com/openai/codex",
        "Autonomous coding workflows for command-line development.",
    ),
    SupportedAgent(
        "crush",
        "Crush",
        "https://github.com/crush-ai/crush",
        "Autonomous development agent focused on fast terminal workflows.",
    ),
    SupportedAgent(
        "cursor",
        "Cursor",
        "https://cursor.com/",
        "The AI Code Editor.",
    ),
    SupportedAgent(
        "gemini-cli",
        "Gemini CLI",
        "https://github.com/google/gemini-cli",
        "Google's command-line interface for Gemini.",
    ),
    SupportedAgent(
        "github-copilot",
        "GitHub Copilot",
        "https://github.com/features/copilot",
        "Your AI pair programmer, right in your IDE.",
    ),
    SupportedAgent(
        "opencode",
        "OpenCode",
        "https://github.com/anomalyco/opencode",
        "Native AGENTS.md support plus repo-level OpenCode config and subagents.",
    ),
)

SUPPORTED_AGENT_IDS = tuple(agent.id for agent in SUPPORTED_AGENTS)


@dataclass(frozen=True)
class DistributionPath:
    title: str
    badge_text: str
    badge_variant: str
    body: str


DISTRIBUTION_PATHS: tuple[DistributionPath, ...] = (
    DistributionPath(
        "Claude Code Plugin",
        "native",
        "tip",
        "`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` expose the repo root as a Git-hosted plugin. The plugin version is intentionally unpinned so Git commits drive updates.",
    ),
    DistributionPath(
        "Codex Plugin",
        "native",
        "note",
        "`.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json` package the same `skills/` and `mcp.json` bundle for Codex.",
    ),
    DistributionPath(
        "Skills CLI",
        "fallback",
        "success",
        f"`npx skills add {REPO_SOURCE} ...` remains the portable install path for supported agents.",
    ),
)


@dataclass(frozen=True)
class FeatureCard:
    title: str
    icon: str
    badge_text: str
    badge_variant: str
    body: str


FEATURE_CARDS: tuple[FeatureCard, ...] = (
    FeatureCard(
        "Portable",
        "P",
        "Install once",
        "note",
        "Move the same workflows across supported coding agents without maintaining parallel prompt copies.",
    ),
    FeatureCard(
        "Inspectable",
        "C",
        "Versioned",
        "tip",
        "Keep prompts, workflows, and conventions in source control instead of buried in copy-paste docs.",
    ),
    FeatureCard(
        "Composable",
        "OS",
        "Stackable",
        "success",
        "Pull specialists together for review, architecture, docs, and runtime work without rebuilding the workflow each time.",
    ),
)


@dataclass(frozen=True)
class FeaturedSkill:
    title: str
    href: str
    description: str


@dataclass(frozen=True)
class VisualAsset:
    id: str
    title: str
    src: str
    alt: str
    description: str


VISUAL_ASSETS: tuple[VisualAsset, ...] = (
    VisualAsset(
        "logo",
        "Agents Logo",
        "/src/assets/brand/logo.webp",
        "Abstract connected-node logo for the Agents repository",
        "Square brand mark used by Starlight and README surfaces.",
    ),
    VisualAsset(
        "social-card",
        "Social Preview",
        "/social-card.png",
        "Agents documentation social preview card",
        "Default Open Graph and README social preview.",
    ),
    VisualAsset(
        "control-plane-hero",
        "Control Plane",
        "/src/assets/brand/control-plane-hero.webp",
        "Abstract control-plane workspace with connected agent nodes and tool panels",
        "Homepage atmosphere and Open Graph background plate.",
    ),
    VisualAsset(
        "catalog-mesh",
        "Catalog Mesh",
        "/src/assets/illustrations/catalog-mesh.webp",
        "Portable skills represented as connected modular interface cards",
        "Explains the skill catalog as reusable, connected workflow components.",
    ),
    VisualAsset(
        "mcp-routing",
        "MCP Routing",
        "/src/assets/illustrations/mcp-routing.webp",
        "MCP tools and document pipelines represented as a luminous routing graph",
        "Explains tool, server, and document flow across configured MCP surfaces.",
    ),
    VisualAsset(
        "harness-matrix",
        "Harness Matrix",
        "/src/assets/illustrations/harness-matrix.webp",
        "Multiple coding-agent harness interfaces connected to one shared skill source",
        "Shows supported agents consuming one portable skill bundle.",
    ),
    VisualAsset(
        "workflow-map",
        "Workflow Map",
        "/src/assets/illustrations/workflow-map.webp",
        "Repository bundle flowing through install, invocation, and validation panels",
        "Shows the operational path from bundle source to validated agent workflow.",
    ),
)

VISUAL_ASSET_BY_ID = {asset.id: asset for asset in VISUAL_ASSETS}


def docs_asset_repo_path(src: str) -> str:
    """Map a docs asset URL to its repository path."""
    if src.startswith("/src/"):
        return f"docs{src}"
    return f"docs/public{src}"


def docs_src_asset_css_url(src: str) -> str:
    """Map a docs/src asset URL to a generated CSS url() path."""
    if not src.startswith("/src/assets/"):
        raise ValueError(f"Expected docs src asset path, got {src!r}")
    return f"./assets/{src.removeprefix('/src/assets/')}"


FEATURED_SKILLS: tuple[FeaturedSkill, ...] = (
    FeaturedSkill(
        "Enhance Code Reviews",
        "/skills/honest-review/",
        "Review a diff with evidence, structure, and severity instead of ad hoc feedback.",
    ),
    FeaturedSkill(
        "Strategic Decision Analysis",
        "/skills/wargame/",
        "Pressure-test a product or engineering decision before you commit to it.",
    ),
    FeaturedSkill(
        "Host Expert Panels",
        "/skills/host-panel/",
        "Get multiple expert perspectives in one session when the problem has real trade-offs.",
    ),
    FeaturedSkill(
        "Create MCP Servers",
        "/skills/mcp-creator/",
        "Build a production-ready FastMCP server with design, testing, and deployment guidance.",
    ),
)


def agent_flags(agent_ids: tuple[str, ...] = SUPPORTED_AGENT_IDS) -> str:
    """Render supported agent flags for the skills CLI."""
    return " ".join(f"--agent {agent_id}" for agent_id in agent_ids)


def build_install_command(
    *,
    skill: str | None = None,
    skills: tuple[str, ...] | None = None,
    all_skills: bool = False,
    agent_ids: tuple[str, ...] = SUPPORTED_AGENT_IDS,
) -> str:
    """Return the canonical install command for generated docs."""
    if all_skills:
        selector = "--all"
    else:
        selected = skills or ((skill,) if skill else ())
        if not selected:
            raise ValueError("build_install_command requires skill, skills, or all_skills=True")
        selector = " ".join(f"--skill {name}" for name in selected)
    return f"npx skills add {REPO_SOURCE} {selector} -y -g {agent_flags(agent_ids)}"


def node_counts(nodes: list[CatalogNode], *, mcp_config_count: int | None = None, has_mcp_overview: bool = False) -> dict[str, int | str]:
    """Summarize catalog counts for generated docs UI."""
    skills = [node for node in nodes if node.kind == "skill"]
    counts: dict[str, int | str] = {
        "customSkills": len([node for node in skills if node.source == "custom"]),
        "installedSkills": len([node for node in skills if node.source != "custom"]),
        "agents": len([node for node in nodes if node.kind == "agent"]),
        "mcpServers": len([node for node in nodes if node.kind == "mcp"]),
    }
    if counts["mcpServers"] == 0 and mcp_config_count:
        counts["mcpServers"] = mcp_config_count
    if counts["mcpServers"] == 0 and has_mcp_overview:
        counts["mcpOverview"] = "available"
    return counts


def site_data(
    nodes: list[CatalogNode], *, mcp_config_count: int | None = None, has_mcp_overview: bool = False
) -> dict[str, Any]:
    """Return serializable site data consumed by generated docs and Astro components."""
    return {
        "repoSource": REPO_SOURCE,
        "supportedAgents": [agent.__dict__ for agent in SUPPORTED_AGENTS],
        "installCommands": {
            "all": build_install_command(all_skills=True),
            "starter": build_install_command(skill="honest-review"),
        },
        "counts": node_counts(nodes, mcp_config_count=mcp_config_count, has_mcp_overview=has_mcp_overview),
        "distributionPaths": [path.__dict__ for path in DISTRIBUTION_PATHS],
        "featureCards": [card.__dict__ for card in FEATURE_CARDS],
        "featuredSkills": [skill.__dict__ for skill in FEATURED_SKILLS],
        "visualAssets": [asset.__dict__ for asset in VISUAL_ASSETS],
    }


def render_site_data_module(data: dict[str, Any]) -> str:
    """Render an ESM module for Astro components."""
    encoded = json.dumps(data, indent=2, sort_keys=True)
    return (
        "// Auto-generated by wagents docs generate - do not edit\n"
        f"export const siteData = {encoded};\n"
        "export const repoSource = siteData.repoSource;\n"
        "export const supportedAgents = siteData.supportedAgents;\n"
        "export const installCommands = siteData.installCommands;\n"
        "export const counts = siteData.counts;\n"
        "export const distributionPaths = siteData.distributionPaths;\n"
        "export const featureCards = siteData.featureCards;\n"
        "export const featuredSkills = siteData.featuredSkills;\n"
        "export const visualAssets = siteData.visualAssets;\n"
    )


def render_visual_assets_css(assets: tuple[VisualAsset, ...] = VISUAL_ASSETS) -> str:
    """Render CSS variables for docs/src visual assets."""
    lines = [
        "/* Auto-generated by wagents docs generate - do not edit */",
        ":root {",
    ]
    for asset in assets:
        if not asset.src.startswith("/src/assets/"):
            continue
        lines.append(f"  --agents-asset-{asset.id}: url('{docs_src_asset_css_url(asset.src)}');")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)
