"""Shared data model for generated docs and install surfaces."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from wagents.catalog import CatalogNode
from wagents.external_skills import ExternalSkillEntry

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
        "`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` expose the repo root "
        "as a Git-hosted plugin. The plugin version is intentionally unpinned so Git commits drive updates.",
    ),
    DistributionPath(
        "Codex Plugin",
        "native",
        "note",
        "`.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json` package the same "
        "`skills/` and `mcp.json` bundle for Codex.",
    ),
    DistributionPath(
        "OpenCode Project Config",
        "native",
        "note",
        "`opencode.json` keeps repo-managed npm plugin specs on `@latest` and scopes "
        "Plannotator to the `plan` agent; restart OpenCode "
        "or refresh `~/.cache/opencode/packages/` when Bun's plugin cache is stale.",
    ),
    DistributionPath(
        "Skills CLI",
        "fallback",
        "success",
        f"`npx skills add {REPO_SOURCE} ...` remains the portable install path for supported agents.",
    ),
    DistributionPath(
        "OpenSpec",
        "workflow",
        "caution",
        "`openspec/` and `uv run wagents openspec ...` provide a spec/change workflow plus local "
        "materialization of upstream OpenSpec skills and commands for downstream AI tools.",
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
        "Pull specialists together for review, architecture, docs, and runtime work without "
        "rebuilding the workflow each time.",
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
        "Run Spec Workflows",
        "/skills/openspec-workflow/",
        "Plan, inspect, validate, and archive OpenSpec changes with repo-aware wrapper commands.",
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


def node_counts(
    nodes: list[CatalogNode], *, mcp_config_count: int | None = None, has_mcp_overview: bool = False
) -> dict[str, int | str]:
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
    nodes: list[CatalogNode],
    *,
    mcp_config_count: int | None = None,
    has_mcp_overview: bool = False,
    external_skills: list[ExternalSkillEntry] | None = None,
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
        "skillIndex": skill_index_data(nodes, external_skills=external_skills or []),
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
        "export const skillIndex = siteData.skillIndex;\n"
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


def skill_index_data(
    nodes: list[CatalogNode], *, external_skills: list[ExternalSkillEntry] | None = None
) -> list[dict[str, Any]]:
    """Return normalized skill rows for UI islands and generated docs."""
    rows = [_skill_node_row(node) for node in nodes if node.kind == "skill"]
    rows.extend(_external_skill_row(entry) for entry in (external_skills or []))
    rows.sort(key=lambda row: (str(row["sourceType"]), str(row["name"])))
    return rows


def _skill_node_row(node: CatalogNode) -> dict[str, Any]:
    fm = node.metadata if isinstance(node.metadata, dict) else {}
    meta = fm.get("metadata", {}) if isinstance(fm.get("metadata"), dict) else {}
    source_type = "custom" if node.source == "custom" else "installed"
    source_root = REPO_SOURCE if source_type == "custom" else str(fm.get("_skills_source") or node.source_path)
    install_source = REPO_SOURCE if source_type == "custom" else str(fm.get("_skills_install_source") or source_root)
    install_command = (
        build_install_command(skill=node.id)
        if source_type == "custom"
        else str(fm.get("_skills_install_command") or f"npx skills add {install_source} --skill {node.id} -y -g")
    )
    installed_agents = (
        fm.get("_skills_installed_agents") if isinstance(fm.get("_skills_installed_agents"), list) else []
    )
    provenance_status = (
        "repo-owned" if source_type == "custom" else str(fm.get("_skills_provenance_status") or "installed-external")
    )
    return {
        "name": node.id,
        "title": node.title,
        "description": node.description,
        "sourceType": source_type,
        "sourceRoot": source_root,
        "installSource": install_source,
        "trustTier": "repo" if source_type == "custom" else str(fm.get("_skills_trust_tier") or "external-installed"),
        "sourcePath": node.source_path,
        "sourceUrl": _source_url_for_node(node),
        "installCommand": install_command,
        "useCommand": f"/{node.id}",
        "provenanceStatus": provenance_status,
        "installedAgents": installed_agents,
        "license": fm.get("license", ""),
        "version": meta.get("version", ""),
        "author": meta.get("author", ""),
        "model": fm.get("model", ""),
        "argumentHint": fm.get("argument-hint", ""),
        "userInvocable": fm.get("user-invocable") is not False,
        "knowledge": _knowledge_inventory(node),
    }


def _external_skill_row(entry: ExternalSkillEntry) -> dict[str, Any]:
    return {
        "name": entry.name,
        "title": entry.name.replace("-", " ").title(),
        "description": entry.notes,
        "sourceType": "curated-external",
        "sourceRoot": entry.source,
        "installSource": entry.install_source,
        "trustTier": entry.trust_tier,
        "sourcePath": entry.source_path,
        "sourceUrl": entry.source_url,
        "installCommand": entry.install_command,
        "useCommand": f"/{entry.name}",
        "provenanceStatus": entry.provenance_status,
        "selectorMode": entry.selector_mode,
        "unresolvedReason": entry.unresolved_reason,
        "license": "",
        "version": "",
        "author": "",
        "model": "",
        "argumentHint": "",
        "userInvocable": True,
        "status": entry.status,
        "targetAgents": list(entry.target_agents),
        "knowledge": {
            "headings": [],
            "references": [],
            "scripts": [],
            "templates": [],
            "evals": [],
            "data": [],
            "resourceLinks": [entry.source_url] if entry.source_url else [],
            "wordCount": 0,
        },
    }


def _knowledge_inventory(node: CatalogNode) -> dict[str, Any]:
    skill_file = _node_skill_file(node)
    skill_dir = skill_file.parent if skill_file else None
    body = node.body or ""
    return {
        "headings": [match.group(1).strip() for match in re.finditer(r"^#{1,6}\s+(.+)$", body, flags=re.MULTILINE)][
            :24
        ],
        "references": _relative_children(skill_dir, "references"),
        "scripts": _relative_children(skill_dir, "scripts"),
        "templates": _relative_children(skill_dir, "templates"),
        "evals": _relative_children(skill_dir, "evals"),
        "data": _relative_children(skill_dir, "data"),
        "resourceLinks": sorted(set(re.findall(r"https?://[^\s)>\"]+", body)))[:24],
        "wordCount": len(body.split()),
    }


def _node_skill_file(node: CatalogNode) -> Path | None:
    path = Path(node.source_path)
    if path.is_absolute():
        return path if path.exists() else None
    candidate = Path.cwd() / path
    if candidate.exists():
        return candidate
    repo_candidate = Path(__file__).resolve().parents[1] / path
    return repo_candidate if repo_candidate.exists() else None


def _relative_children(skill_dir: Path | None, child_name: str) -> list[str]:
    if skill_dir is None:
        return []
    child = skill_dir / child_name
    if not child.exists() or not child.is_dir():
        return []
    items = []
    for path in sorted(p for p in child.rglob("*") if p.is_file()):
        if "__pycache__" in path.parts or path.suffix == ".pyc" or path.name == ".DS_Store":
            continue
        try:
            items.append(str(path.relative_to(skill_dir)))
        except ValueError:
            items.append(str(path))
    return items


def _source_url_for_node(node: CatalogNode) -> str:
    if node.source == "custom":
        return f"https://github.com/wyattowalsh/agents/blob/main/{node.source_path}"
    source = node.metadata.get("_skills_source") if isinstance(node.metadata, dict) else None
    if isinstance(source, str) and re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", source):
        return f"https://github.com/{source}"
    return ""
