"""Shared data model for generated docs and install surfaces."""

from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from wagents import ROOT
from wagents.external_skills import SYNC_KIND_SKILLS_CLI, infer_sync_kind

if TYPE_CHECKING:
    from wagents.catalog import CatalogNode
    from wagents.external_skills import ExternalSkillEntry

NodeSourceType = Literal["custom", "curated-external", "installed"]
BucketSourceType = Literal["custom", "external"]

REPO_SOURCE = "github:wyattowalsh/agents"
LOCAL_INSTALLED_SOURCE_LABEL = "local installed inventory"


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def use_command_for_catalog_row(install_command: str, name: str) -> str:
    """Slash skill vs CLI tool invocation label for catalog indexes."""
    command = (install_command or "").strip()
    cmd = command.lower()
    if not cmd:
        return ""
    if cmd.startswith("pip install ") or cmd.startswith("pipx install "):
        return "apm --help"
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = []
    if "--skill" in parts:
        index = parts.index("--skill")
        if index + 1 < len(parts) and parts[index + 1]:
            return f"/{parts[index + 1]}"
    return f"/{name}"


@dataclass(frozen=True)
class SupportedAgent:
    id: str
    label: str
    href: str
    description: str
    runtime_instructions: str
    runtime_skills: str
    runtime_tools: str
    runtime_hooks: str
    runtime_agents: str


@dataclass(frozen=True)
class IntegrationSurface:
    id: str
    label: str
    href: str
    surface_kind: str
    description: str


SUPPORTED_AGENTS: tuple[SupportedAgent, ...] = (
    SupportedAgent(
        "claude-code",
        "Claude Code",
        "https://docs.anthropic.com/en/docs/claude-code",
        "Anthropic's official CLI for Claude.",
        "native import",
        "plugin/Skills CLI",
        "MCP",
        "generated",
        "native subagents",
    ),
    SupportedAgent(
        "codex",
        "Codex",
        "https://github.com/openai/codex",
        "Autonomous coding workflows for command-line development.",
        "generated",
        "plugin/Skills CLI",
        "MCPHub",
        "generated",
        "dynamic delegation",
    ),
    SupportedAgent(
        "crush",
        "Crush",
        "https://github.com/charmbracelet/crush",
        "Autonomous development agent focused on fast terminal workflows.",
        "AGENTS.md",
        "Skills CLI",
        "MCP projection",
        "limited",
        "not primary",
    ),
    SupportedAgent(
        "cursor",
        "Cursor",
        "https://cursor.com/",
        "The AI Code Editor.",
        "rules + AGENTS.md",
        "Skills CLI",
        "MCPHub",
        "native hooks",
        ".cursor/agents",
    ),
    SupportedAgent(
        "grok",
        "Grok Build",
        "https://x.ai/cli",
        "xAI's agentic coding CLI with skills, MCP, and Claude Code compatibility.",
        "generated config",
        "mirrored skills",
        "MCPHub",
        "generated",
        "delegation",
    ),
    SupportedAgent(
        "opencode",
        "OpenCode",
        "https://github.com/anomalyco/opencode",
        "Native AGENTS.md support plus repo-level OpenCode config and subagents.",
        "native AGENTS.md",
        "Skills CLI",
        "MCPHub + plugins",
        "generated",
        "native agents",
    ),
)

SUPPORTED_AGENT_IDS = tuple(agent.id for agent in SUPPORTED_AGENTS)

# Skills CLI has no native `grok` adapter. Install docs and `npx skills add`
# flags use native CLI agent IDs only; Grok is installed via `wagents install -a grok`
# (claude-code adapter + mirror into ~/.grok/skills).
SKILLS_CLI_NATIVE_AGENT_IDS = tuple(agent_id for agent_id in SUPPORTED_AGENT_IDS if agent_id != "grok")

ADDITIONAL_INTEGRATION_SURFACES: tuple[IntegrationSurface, ...] = (
    IntegrationSurface(
        "cherry-studio",
        "Cherry Studio",
        "https://www.cherry-ai.com/",
        "mcp-only",
        "MCPHub registry and generated import pack; not a managed agent family.",
    ),
    IntegrationSurface(
        "claude-desktop",
        "Claude Desktop",
        "https://claude.ai/download",
        "mcp-only",
        "Managed MCP configuration client; not a managed agent family.",
    ),
    IntegrationSurface(
        "chatgpt",
        "ChatGPT",
        "https://chatgpt.com/",
        "connector",
        "Remote MCP connector surface; not a managed agent family.",
    ),
    IntegrationSurface(
        "lm-studio",
        "LM Studio",
        "https://lmstudio.ai/",
        "hybrid",
        "MCP plus managed instruction and agent presets, with an optional skill mirror.",
    ),
)


def _strip(v: str) -> str:
    """Normalize value to stripped string (centralized to reduce duplication in source/path/trust logic)."""
    return str(v or "").strip()


def trust_badge_for_tier(trust_tier: str) -> tuple[str, str]:
    """Map trust tier to public docs badge text and Starlight variant."""
    mapping = {
        "repo": ("Repo-owned", "tip"),
        "repo-owned": ("Repo-owned", "tip"),
        "curated-trust-gated": ("Curated", "note"),
        "needs-inspection": ("Inspect first", "caution"),
        "read-only-discovered": ("Inspect first", "caution"),
        "external-installed": ("Local install", "default"),
        "global-only-or-avoid": ("Avoid default", "danger"),
        "hard-blocked": ("Hard-blocked", "danger"),
        "github": ("GitHub", "note"),
        "git": ("Git source", "note"),
    }
    return mapping.get(_strip(trust_tier), ("External", "default"))


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
        "/skills/catalog/custom/review/",
        "Review a diff with evidence, structure, and severity instead of ad hoc feedback.",
    ),
    FeaturedSkill(
        "Strategic Decision Analysis",
        "/skills/catalog/custom/wargame/",
        "Pressure-test a product or engineering decision before you commit to it.",
    ),
    FeaturedSkill(
        "Host Expert Panels",
        "/skills/catalog/custom/host-panel/",
        "Get multiple expert perspectives in one session when the problem has real trade-offs.",
    ),
    FeaturedSkill(
        "Run Spec Workflows",
        "/skills/catalog/custom/openspec-workflow/",
        "Plan, inspect, validate, and archive OpenSpec changes with repo-aware wrapper commands.",
    ),
    FeaturedSkill(
        "Create MCP Servers",
        "/skills/catalog/custom/mcp-creator/",
        "Build a production-ready FastMCP server with design, testing, and deployment guidance.",
    ),
)


def agent_flags(agent_ids: tuple[str, ...] = SKILLS_CLI_NATIVE_AGENT_IDS) -> str:
    """Render Skills CLI-native agent flags (excludes Grok; no native adapter)."""
    seen: set[str] = set()
    ordered: list[str] = []
    for agent_id in agent_ids:
        if agent_id == "grok":
            continue
        if agent_id in seen:
            continue
        seen.add(agent_id)
        ordered.append(agent_id)
    return " ".join(f"--agent {agent_id}" for agent_id in ordered)


def normalize_public_install_command(
    command: str,
    *,
    drop_agents: frozenset[str] = frozenset({"antigravity", "gemini-cli", "github-copilot", "grok"}),
) -> str:
    """Strip unsupported agent tokens from published Skills CLI commands.

    Operates only on agent-flag value positions (``-a`` / ``--agent``). Never rewrites
    ``--skill``, source URLs, or non-CLI install strings. Idempotent.
    """
    from wagents.external_skills import is_skills_cli_install_command

    raw = (command or "").strip()
    if not raw:
        return ""
    if not is_skills_cli_install_command(raw):
        return raw
    try:
        tokens = shlex.split(raw)
    except ValueError:
        # Conservative: remove only explicit agent-flag pairs when parse fails.
        drop_pattern = "|".join(re.escape(agent) for agent in sorted(drop_agents))
        cleaned = re.sub(
            rf"(?:--agent(?:=|\s+)|-a\s+)(?:{drop_pattern})\b",
            "",
            raw,
        )
        return re.sub(r"\s+", " ", cleaned).strip()

    drop = set(drop_agents)
    short_flags = {"-a"}
    long_flags = {"--agent", "--agents"}

    def _is_flag(tok: str) -> bool:
        return tok.startswith("-")

    def _split_agent_values(value: str) -> list[str]:
        return [part for part in value.split(",") if part]

    def _keep(agents: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for agent in agents:
            if agent in drop or agent in seen:
                continue
            seen.add(agent)
            out.append(agent)
        return out

    out: list[str] = []
    i = 0
    n = len(tokens)
    while i < n:
        token = tokens[i]
        if token.startswith("--agent=") or token.startswith("--agents="):
            flag_name, rhs = token.split("=", 1)
            kept = _keep(_split_agent_values(rhs))
            if len(kept) == 1 and "," not in rhs and len(_split_agent_values(rhs)) == 1:
                out.append(f"{flag_name}={kept[0]}")
            else:
                for agent in kept:
                    out.append("--agent")
                    out.append(agent)
            i += 1
            continue
        if token.startswith("-a=") and token != "-a=":
            kept = _keep(_split_agent_values(token[3:]))
            if kept:
                out.append("-a")
                out.extend(kept)
            i += 1
            continue
        if token in short_flags:
            i += 1
            values: list[str] = []
            while i < n and not _is_flag(tokens[i]):
                values.extend(_split_agent_values(tokens[i]))
                i += 1
            kept = _keep(values)
            if kept:
                out.append("-a")
                out.extend(kept)
            continue
        if token in long_flags:
            i += 1
            if i >= n or _is_flag(tokens[i]):
                continue
            values = _split_agent_values(tokens[i])
            i += 1
            for agent in _keep(values):
                out.append("--agent")
                out.append(agent)
            continue
        out.append(token)
        i += 1
    return shlex.join(out)


def build_install_command(
    *,
    skill: str | None = None,
    skills: tuple[str, ...] | None = None,
    all_skills: bool = False,
    agent_ids: tuple[str, ...] = SKILLS_CLI_NATIVE_AGENT_IDS,
) -> str:
    """Return the canonical install command for generated docs.

    Uses Skills CLI-native agent IDs only. Grok installs go through
    ``wagents install -a grok`` / ``wagents skills sync -a grok``.
    """
    if all_skills:
        selector = "--all"
    else:
        selected = skills or ((skill,) if skill else ())
        if not selected:
            raise ValueError("build_install_command requires skill, skills, or all_skills=True")
        selector = " ".join(f"--skill {name}" for name in selected)
    return f"npx skills add {REPO_SOURCE} {selector} -y -g {agent_flags(agent_ids)}"


def _node_source_type(node: CatalogNode) -> NodeSourceType:
    """Return the catalog node's skill source type."""
    if node.source == "custom":
        return "custom"
    if node.source == "curated-external":
        return "curated-external"
    return "installed"


def _bucket_source_type(node: CatalogNode) -> BucketSourceType:
    """Map catalog source to public custom vs external bucket."""
    return "custom" if _node_source_type(node) == "custom" else "external"


def skill_source_counts(skills: list[CatalogNode]) -> dict[str, int]:
    """Count skills by public custom/external taxonomy from catalog nodes."""
    custom = sum(1 for node in skills if _node_source_type(node) == "custom")
    external = sum(1 for node in skills if _bucket_source_type(node) == "external")
    return {
        "skills": custom + external,
        "customSkills": custom,
        "externalSkills": external,
    }


def mcp_source_counts(nodes: list[CatalogNode], *, mcp_config_count: int | None = None) -> dict[str, int]:
    """Count MCP tools by repo packages vs configured external servers."""
    custom_mcp = len([node for node in nodes if node.kind == "mcp"])
    external_mcp = mcp_config_count or 0
    return {
        "customMcp": custom_mcp,
        "externalMcp": external_mcp,
        "mcpTools": custom_mcp + external_mcp,
    }


def node_counts(
    nodes: list[CatalogNode], *, mcp_config_count: int | None = None, has_mcp_overview: bool = False
) -> dict[str, int | str]:
    """Summarize catalog counts for generated docs UI."""
    skills = [node for node in nodes if node.kind == "skill"]
    counts: dict[str, int | str] = {
        **skill_source_counts(skills),
        **mcp_source_counts(nodes, mcp_config_count=mcp_config_count),
        "supportedHarnesses": len(SUPPORTED_AGENTS),
        "skillsCliNativeHarnesses": len(SKILLS_CLI_NATIVE_AGENT_IDS),
        "additionalIntegrationSurfaces": len(ADDITIONAL_INTEGRATION_SURFACES),
        "bundledAgents": len([node for node in nodes if node.kind == "agent"]),
    }
    if counts["customMcp"] == 0 and counts["externalMcp"] == 0 and has_mcp_overview:
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
    indexes = skill_indexes(nodes, external_skills=external_skills or [])
    return {
        "repoSource": REPO_SOURCE,
        "supportedAgents": [agent.__dict__ for agent in SUPPORTED_AGENTS],
        "skillsCliNativeAgentIds": list(SKILLS_CLI_NATIVE_AGENT_IDS),
        "additionalIntegrationSurfaces": [surface.__dict__ for surface in ADDITIONAL_INTEGRATION_SURFACES],
        "installCommands": {
            "all": build_install_command(all_skills=True),
            "starter": build_install_command(skill="review"),
        },
        "counts": node_counts(nodes, mcp_config_count=mcp_config_count, has_mcp_overview=has_mcp_overview),
        "distributionPaths": [path.__dict__ for path in DISTRIBUTION_PATHS],
        "featureCards": [card.__dict__ for card in FEATURE_CARDS],
        "featuredSkills": [skill.__dict__ for skill in FEATURED_SKILLS],
        "visualAssets": [asset.__dict__ for asset in VISUAL_ASSETS],
        "skillIndex": indexes["allSkillIndex"],
        **indexes,
        "skillInstallScripts": skill_install_scripts(indexes),
        "externalSkillGroups": external_skill_groups(indexes["externalSkillIndex"]),
    }


def render_site_data_module(data: dict[str, Any]) -> str:
    """Render an ESM module for Astro components."""
    index_keys = ("customSkillIndex", "externalSkillIndex", "allSkillIndex", "skillIndex")
    base_data = {key: value for key, value in data.items() if key not in index_keys}
    encoded = json.dumps(base_data, indent=2, sort_keys=True)
    return (
        "// Auto-generated by wagents docs generate - do not edit\n"
        f"const baseSiteData = {encoded};\n"
        "export const siteData = baseSiteData;\n"
        "export const repoSource = baseSiteData.repoSource;\n"
        "export const supportedAgents = baseSiteData.supportedAgents;\n"
        "export const skillsCliNativeAgentIds = baseSiteData.skillsCliNativeAgentIds;\n"
        "export const additionalIntegrationSurfaces = baseSiteData.additionalIntegrationSurfaces;\n"
        "export const installCommands = baseSiteData.installCommands;\n"
        "export const counts = baseSiteData.counts;\n"
        "export const distributionPaths = baseSiteData.distributionPaths;\n"
        "export const featureCards = baseSiteData.featureCards;\n"
        "export const featuredSkills = baseSiteData.featuredSkills;\n"
        "export const visualAssets = baseSiteData.visualAssets;\n"
        "export const skillInstallScripts = baseSiteData.skillInstallScripts;\n"
        "export const externalSkillGroups = baseSiteData.externalSkillGroups;\n"
    )


def render_skill_indexes_module(data: dict[str, Any]) -> str:
    """Render an ESM module for heavy skill indexes used by catalog browsers."""
    index_keys = ("customSkillIndex", "externalSkillIndex", "allSkillIndex", "skillIndex")
    skill_indexes = {key: data[key] for key in index_keys if key in data}
    encoded_indexes = json.dumps(skill_indexes, indent=2, sort_keys=True)
    return (
        "// Auto-generated by wagents docs generate - do not edit\n"
        f"const skillIndexes = {encoded_indexes};\n"
        "export const externalSkillIndex = skillIndexes.externalSkillIndex;\n"
        "export const customSkillIndex = skillIndexes.customSkillIndex;\n"
        "export const allSkillIndex = skillIndexes.allSkillIndex;\n"
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
    return skill_indexes(nodes, external_skills=external_skills or [])["allSkillIndex"]


def skill_indexes(
    nodes: list[CatalogNode], *, external_skills: list[ExternalSkillEntry] | None = None
) -> dict[str, list[dict[str, Any]]]:
    """Return filtered and deduped skill indexes for generated docs."""
    custom_rows = sorted(
        (_skill_node_row(node) for node in nodes if node.kind == "skill" and node.source == "custom"),
        key=lambda row: str(row["name"]),
    )
    custom_names = {str(row["name"]).lower() for row in custom_rows}
    curated_parser_rows = sorted(
        (_external_skill_row(entry) for entry in (external_skills or [])),
        key=lambda row: (str(row["status"]), str(row["sourceRoot"]), str(row["name"])),
    )
    curated_stub_rows = sorted(
        [
            _skill_node_row(node)
            for node in nodes
            if node.kind == "skill" and node.source == "curated-external" and node.id.lower() not in custom_names
        ],
        key=lambda row: str(row["name"]),
    )
    curated_merged = _merge_curated_catalog_rows(curated_parser_rows, curated_stub_rows)
    installed_rows = sorted(
        [
            _skill_node_row(node)
            for node in nodes
            if node.kind == "skill" and node.source == "installed" and node.id.lower() not in custom_names
        ],
        key=lambda row: (str(row["sourceRoot"]), str(row["name"])),
    )
    external_rows = _merge_external_rows(curated_merged, installed_rows)
    external_rows = sorted(
        external_rows,
        key=lambda row: (str(row["sourceType"]), str(row.get("status", "")), str(row["name"])),
    )
    rows = sorted(
        [*custom_rows, *external_rows],
        key=lambda row: (str(row["sourceType"]), str(row["name"])),
    )
    return {
        "customSkillIndex": custom_rows,
        "externalSkillIndex": external_rows,
        "allSkillIndex": rows,
    }


def skill_install_scripts(indexes: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Build copyable install scripts for generated docs pages."""
    custom_rows = indexes["customSkillIndex"]
    external_rows = indexes["externalSkillIndex"]
    custom_individual = [
        {"name": row["name"], "command": build_install_command(skill=str(row["name"]))} for row in custom_rows
    ]
    external_commands: dict[str, dict[str, Any]] = {}
    for row in external_rows:
        command = str(row.get("installCommand") or "").strip()
        if not command or row.get("selectorMode") == "unresolved":
            continue
        key = command
        record = external_commands.setdefault(
            key,
            {
                "source": row.get("displaySource") or row.get("sourceRoot") or row.get("installSource") or "",
                "command": command,
                "skills": [],
                "status": row.get("status", "installed-external"),
                "trustTier": row.get("trustTier", ""),
                "sourceType": row.get("sourceType", "curated-external"),
            },
        )
        record["skills"].append(row["name"])
    return {
        "customAll": build_install_command(all_skills=True),
        "customIndividual": custom_individual,
        "externalCommands": sorted(external_commands.values(), key=lambda item: (item["source"], item["command"])),
        "syncDryRun": "uv run wagents skills sync --dry-run",
        "syncApply": "uv run wagents skills sync --apply",
    }


def external_skill_groups(external_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Group external rows by status and source for generated docs."""
    by_status: dict[str, list[dict[str, Any]]] = {}
    by_source: dict[str, list[dict[str, Any]]] = {}
    for row in external_rows:
        status = str(row.get("status") or "installed-external")
        source = str(row.get("displaySource") or row.get("sourceRoot") or row.get("installSource") or "unknown")
        by_status.setdefault(status, []).append(row)
        by_source.setdefault(source, []).append(row)
    return {
        "byStatus": [
            {
                "status": status,
                "count": len(rows),
                "skills": [str(row["name"]) for row in sorted(rows, key=lambda row: str(row["name"]))],
            }
            for status, rows in sorted(by_status.items())
        ],
        "bySource": [
            {
                "source": source,
                "count": len(rows),
                "skills": [str(row["name"]) for row in sorted(rows, key=lambda row: str(row["name"]))],
            }
            for source, rows in sorted(by_source.items())
        ],
    }


def _merge_curated_catalog_rows(
    parser_rows: list[dict[str, Any]], stub_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Merge parser curated rows with catalog stub rows; parser wins on name collision."""
    merged = [dict(row) for row in parser_rows]
    by_name = {str(row["name"]).lower(): row for row in merged}
    for stub in stub_rows:
        if str(stub["name"]).lower() in by_name:
            continue
        row = dict(stub)
        merged.append(row)
        by_name[str(row["name"]).lower()] = row
    return merged


def _merge_external_rows(
    curated_rows: list[dict[str, Any]], installed_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Merge installed external rows into matching curated rows and keep installed-only rows."""
    merged = [dict(row) for row in curated_rows]
    by_exact = {_external_row_key(row): row for row in merged}
    by_name: dict[str, dict[str, Any]] = {}
    for row in merged:
        by_name.setdefault(str(row["name"]).lower(), row)

    for installed in installed_rows:
        target = by_exact.get(_external_row_key(installed))
        if target is None:
            target = by_name.get(str(installed["name"]).lower())
        if target is not None:
            agents = sorted(set(target.get("installedAgents") or []) | set(installed.get("installedAgents") or []))
            target["installedAgents"] = agents
            target["installedExternalPath"] = _public_source_path(str(installed.get("sourcePath", "")))
            target["installedProvenanceStatus"] = installed.get("provenanceStatus", "")
            target["installedLocalInventoryOnly"] = bool(installed.get("localInventoryOnly"))
            continue
        merged.append(installed)
    return merged


def _external_row_key(row: dict[str, Any]) -> tuple[str, str]:
    source = str(row.get("sourceRoot") or row.get("installSource") or "").removeprefix("github:").lower()
    return (str(row["name"]).lower(), source)


def resolve_trust_tier_for_node(node: CatalogNode) -> str:
    """Derive trust tier for node rows (custom always repo-owned)."""
    if getattr(node, "source", None) == "custom":
        return "repo-owned"
    fm = node.metadata if isinstance(node.metadata, dict) else {}
    tier = fm.get("_skills_trust_tier") or fm.get("trust_tier")
    if tier:
        normalized = _strip(tier)
        if normalized == "repo":
            return "repo-owned"
        return normalized
    if getattr(node, "source", None) == "curated-external":
        return "curated-trust-gated"
    return "external-installed"


def _skill_node_row(node: CatalogNode) -> dict[str, Any]:
    fm = node.metadata if isinstance(node.metadata, dict) else {}
    meta = fm.get("metadata", {}) if isinstance(fm.get("metadata"), dict) else {}
    source_type = _node_source_type(node)
    if source_type == "custom":
        raw_source_root = REPO_SOURCE
        source_root = REPO_SOURCE
        # Catalog-index schema sourceKind uses custom|curated-external|external (not "repo").
        source_kind = "custom"
        local_inventory_only = False
        install_source = REPO_SOURCE
        install_command = build_install_command(skill=node.id)
        provenance_status = "repo-owned"
        review_status = "reviewed"
        sync_kind = SYNC_KIND_SKILLS_CLI
    elif source_type == "curated-external":
        raw_source_root = str(fm.get("_skills_source") or node.source_path or REPO_SOURCE)
        source_root = _public_source_label(raw_source_root)
        source_kind = "curated-external"
        local_inventory_only = False
        raw_install_source = str(fm.get("_skills_install_source") or raw_source_root)
        install_source = raw_install_source
        install_command = _installed_install_command(
            node.id, fm, install_source, local_inventory_only=local_inventory_only
        )
        provenance_status = str(fm.get("_skills_provenance_status") or "verified-curated-external")
        review_status = "curated"
        sync_kind = infer_sync_kind(str(fm.get("_sync_kind") or fm.get("sync_kind") or ""), install_command)
    else:
        raw_source_root = str(fm.get("_skills_source") or node.source_path)
        source_root = _public_source_label(raw_source_root)
        source_kind = _source_kind(raw_source_root, source_type=source_type)
        local_inventory_only = source_kind == "local-inventory"
        raw_install_source = str(fm.get("_skills_install_source") or raw_source_root)
        install_source = "" if local_inventory_only and _is_local_path_like(raw_install_source) else raw_install_source
        install_command = _installed_install_command(
            node.id, fm, install_source, local_inventory_only=local_inventory_only
        )
        provenance_status = str(fm.get("_skills_provenance_status") or "installed-external")
        review_status = "reviewed"
        sync_kind = infer_sync_kind(str(fm.get("_sync_kind") or fm.get("sync_kind") or ""), install_command)
    installed_agents = (
        fm.get("_skills_installed_agents") if isinstance(fm.get("_skills_installed_agents"), list) else []
    )
    target_agents = (
        list(SKILLS_CLI_NATIVE_AGENT_IDS) if source_type == "custom" else _as_str_list(fm.get("_skills_target_agents"))
    )
    trust_tier = resolve_trust_tier_for_node(node)
    trust_badge, trust_badge_variant = trust_badge_for_tier(trust_tier)
    return {
        "name": node.id,
        "title": node.title,
        "description": node.description,
        "sourceType": source_type,
        "sourceRoot": source_root,
        "displaySource": source_root,
        "sourceKind": source_kind,
        "installSource": install_source,
        "installable": bool(install_command) or source_type == "custom",
        "localInventoryOnly": local_inventory_only,
        "trustTier": trust_tier,
        "trustBadge": trust_badge,
        "trustBadgeVariant": trust_badge_variant,
        "sourcePath": _public_source_path(node.source_path),
        "sourceUrl": _source_url_for_node(node),
        "installCommand": install_command,
        "syncKind": sync_kind,
        "useCommand": use_command_for_catalog_row(install_command, node.id),
        "provenanceStatus": provenance_status,
        "status": fm.get("_curated_status") or provenance_status,
        "reviewStatus": review_status,
        "targetAgents": target_agents,
        "installedAgents": installed_agents,
        "riskNotes": fm.get("_risk_notes", ""),
        "promotionPolicy": fm.get("_promotion_policy", ""),
        "provenanceEvidence": fm.get("_provenance_evidence", provenance_status),
        "auditDate": fm.get("_audit_date", ""),
        "auditedHead": fm.get("_audited_head", ""),
        "pinPolicy": fm.get("_pin_policy", ""),
        "noPinRationale": fm.get("_no_pin_rationale", ""),
        "sourceListEvidence": fm.get("_source_list_evidence", ""),
        "executableSurface": fm.get("_executable_surface", ""),
        "allowedTools": fm.get("_allowed_tools", ""),
        "hookSurface": fm.get("_hook_surface", ""),
        "scriptSurface": fm.get("_script_surface", ""),
        "credentialBehavior": fm.get("_credential_behavior", ""),
        "networkAccess": fm.get("_network_access", ""),
        "fileAccess": fm.get("_file_access", ""),
        "liveActionRisk": fm.get("_live_action_risk", ""),
        "riskCategory": fm.get("_risk_category", ""),
        "dedupeNotes": fm.get("_dedupe_notes", ""),
        "unsupportedTargetAgents": _as_str_list(fm.get("_unsupported_target_agents")),
        "license": fm.get("license", ""),
        "licenseStatus": fm.get("license_status", fm.get("licenseStatus", "")),
        "version": meta.get("version", ""),
        "author": meta.get("author", ""),
        "model": fm.get("model", ""),
        "argumentHint": fm.get("argument-hint", ""),
        "userInvocable": fm.get("user-invocable") is not False,
        "knowledge": _knowledge_inventory(node),
    }


def _external_skill_row(entry: ExternalSkillEntry) -> dict[str, Any]:
    trust_badge, trust_badge_variant = trust_badge_for_tier(entry.trust_tier)
    return {
        "name": entry.name,
        "title": entry.name.replace("-", " ").title(),
        "description": entry.notes,
        "sourceType": "curated-external",
        "sourceRoot": entry.source,
        "displaySource": entry.source or "curated external source",
        "sourceKind": "curated-external",
        "installSource": entry.install_source,
        "installable": bool(entry.install_command and entry.selector_mode != "unresolved"),
        "localInventoryOnly": False,
        "trustTier": entry.trust_tier or "curated-trust-gated",
        "trustBadge": trust_badge,
        "trustBadgeVariant": trust_badge_variant,
        "sourcePath": _public_source_path(entry.source_path),
        "sourceUrl": entry.source_url,
        "installCommand": entry.install_command,
        "useCommand": use_command_for_catalog_row(entry.install_command, entry.name),
        "provenanceStatus": entry.provenance_status,
        "reviewStatus": "curated" if entry.provenance_status == "verified-install-command" else "unresolved",
        "selectorMode": entry.selector_mode,
        "syncKind": infer_sync_kind(entry.sync_kind, entry.install_command),
        "unresolvedReason": entry.unresolved_reason,
        "license": entry.license,
        "licenseStatus": entry.license_status,
        "version": "",
        "author": "",
        "model": "",
        "argumentHint": "",
        "userInvocable": True,
        "status": entry.status,
        "targetAgents": list(entry.target_agents),
        "installedAgents": [],
        "riskNotes": entry.risk_notes or entry.notes,
        "promotionPolicy": entry.promotion_policy or _promotion_policy_for_external_status(entry.status),
        "provenanceEvidence": entry.provenance_evidence or entry.provenance_status,
        "auditDate": entry.audit_date,
        "auditedHead": entry.audited_head,
        "pinPolicy": entry.pin_policy,
        "noPinRationale": entry.no_pin_rationale,
        "sourceListEvidence": entry.source_list_evidence,
        "executableSurface": entry.executable_surface,
        "allowedTools": entry.allowed_tools,
        "hookSurface": entry.hook_surface,
        "scriptSurface": entry.script_surface,
        "credentialBehavior": entry.credential_behavior,
        "networkAccess": entry.network_access,
        "fileAccess": entry.file_access,
        "liveActionRisk": entry.live_action_risk,
        "riskCategory": entry.risk_category,
        "dedupeNotes": entry.dedupe_notes,
        "unsupportedTargetAgents": list(entry.unsupported_target_agents),
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


def _installed_install_command(
    skill_id: str, metadata: dict[str, Any], install_source: str, *, local_inventory_only: bool
) -> str:
    sync_kind = str(metadata.get("_sync_kind") or metadata.get("sync_kind") or "").strip()
    selector_mode = str(metadata.get("_selector_mode") or metadata.get("selector_mode") or "").strip()
    curated_status = str(metadata.get("_curated_status") or metadata.get("status") or "").strip()
    if sync_kind == "none" or selector_mode == "unresolved" or curated_status == "global-only-or-avoid":
        return ""
    command = str(metadata.get("_skills_install_command") or "").strip()
    if command and not _contains_local_path(command):
        return normalize_public_install_command(command)
    if local_inventory_only or not install_source or _is_local_path_like(install_source):
        return ""
    return f"npx skills add {install_source} --skill {skill_id} -y -g"


def _public_source_label(value: str) -> str:
    source = _strip(value)
    if not source:
        return LOCAL_INSTALLED_SOURCE_LABEL
    if _is_local_path_like(source):
        return LOCAL_INSTALLED_SOURCE_LABEL
    return source


def _source_kind(value: str, *, source_type: str) -> str:
    source = _strip(value)
    if source_type == "custom" or source == REPO_SOURCE:
        return "repo"
    if not source or _is_local_path_like(source):
        return "local-inventory"
    if source.startswith("github:") or re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", source):
        return "github"
    if source.startswith(("http://", "https://")):
        return "url"
    return "external"


def _is_public_path_like(value: str) -> bool:
    path = _strip(value)
    return bool(path) and not _is_local_path_like(path)


def _public_source_path(value: str) -> str:
    """Return a public-safe source path for generated catalog rows."""
    path = _strip(value)
    if not path:
        return ""
    raw = Path(path).expanduser()
    if raw.is_absolute():
        try:
            return raw.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            return ""
    return path if _is_public_path_like(path) else ""


def _contains_local_path(value: str) -> bool:
    return bool(re.search(r"(?:/Users/|/home/|/private/|/tmp/|~/|[A-Za-z]:[\\/])", str(value or "")))


def _is_local_path_like(value: str) -> bool:
    source = _strip(value)
    if not source:
        return False
    if source.startswith(("http://", "https://", "github:")):
        return False
    if source.startswith(("~/", "$HOME/", "/Users/", "/home/", "/private/", "/tmp/")):
        return True
    if re.match(r"^[A-Za-z]:[\\/]", source):
        return True
    return Path(source).is_absolute()


def contains_local_path(value: str) -> bool:
    """Public SSOT: true when *value* embeds a machine-local path marker."""
    return _contains_local_path(value)


def is_local_path_like(value: str) -> bool:
    """Public SSOT: true when *value* looks like a local filesystem path."""
    return _is_local_path_like(value)


def _promotion_policy_for_external_status(status: str) -> str:
    return {
        "install-now-after-trust-gate": "Install only after trust gate; audit again before repo promotion.",
        "inspect-then-install": "Inspect source, hooks, scripts, credentials, and dedupe before install.",
        "global-only-or-avoid": "Keep global-only or avoid unless explicitly approved.",
        "installed-external": "Treat as local installed inventory until curated and audited.",
        "integrated-collection-surface": "Terminal collection integration; do not vendor wholesale.",
        "integrated-existing-surface": "Terminal existing-surface integration; do not duplicate.",
        "integrated-mcp-surface": "Terminal MCP integration; use repo-native MCP surfaces only.",
        "integrated-native-surface": "Terminal native-surface integration; no portable skill install emitted.",
        "integrated-plugin-surface": "Terminal plugin integration; use plugin registry/manual activation only.",
        "integrated-skill-catalog-surface": (
            "Terminal skill-catalog integration; install metadata is recorded separately."
        ),
        "integrated-tool-surface": "Terminal tool integration; use tool docs/manual smoke tests only.",
        "hard-blocked-inaccessible": "Hard-blocked because the upstream source is inaccessible or malformed.",
        "hard-blocked-quarantine": "Hard-blocked by quarantine policy; do not install or execute.",
    }.get(status, "")


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
