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
LOCAL_INSTALLED_SOURCE_LABEL = "local installed inventory"


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
        "grok",
        "Grok Build",
        "https://x.ai/cli",
        "xAI's agentic coding CLI with skills, MCP, and Claude Code compatibility.",
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
        "/skills/catalog/honest-review/",
        "Review a diff with evidence, structure, and severity instead of ad hoc feedback.",
    ),
    FeaturedSkill(
        "Strategic Decision Analysis",
        "/skills/catalog/wargame/",
        "Pressure-test a product or engineering decision before you commit to it.",
    ),
    FeaturedSkill(
        "Host Expert Panels",
        "/skills/catalog/host-panel/",
        "Get multiple expert perspectives in one session when the problem has real trade-offs.",
    ),
    FeaturedSkill(
        "Run Spec Workflows",
        "/skills/catalog/openspec-workflow/",
        "Plan, inspect, validate, and archive OpenSpec changes with repo-aware wrapper commands.",
    ),
    FeaturedSkill(
        "Create MCP Servers",
        "/skills/catalog/mcp-creator/",
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
    indexes = skill_indexes(nodes, external_skills=external_skills or [])
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
        "skillIndex": indexes["allSkillIndex"],
        **indexes,
        "skillInstallScripts": skill_install_scripts(indexes),
        "externalSkillGroups": external_skill_groups(indexes["externalSkillIndex"]),
    }


def render_site_data_module(data: dict[str, Any]) -> str:
    """Render an ESM module for Astro components."""
    base_data = {
        key: value
        for key, value in data.items()
        if key
        not in {
            "customSkillIndex",
            "curatedExternalSkillIndex",
            "installedSkillIndex",
            "externalSkillIndex",
            "allSkillIndex",
            "skillIndex",
        }
    }
    encoded = json.dumps(base_data, indent=2, sort_keys=True)
    return (
        "// Auto-generated by wagents docs generate - do not edit\n"
        f"const baseSiteData = {encoded};\n"
        "export const siteData = baseSiteData;\n"
        "export const repoSource = baseSiteData.repoSource;\n"
        "export const supportedAgents = baseSiteData.supportedAgents;\n"
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
    """Render large skill index exports in a separate module."""
    custom_index = json.dumps(data["customSkillIndex"], indent=2, sort_keys=True)
    curated_external_index = json.dumps(data["curatedExternalSkillIndex"], indent=2, sort_keys=True)
    installed_index = json.dumps(data["installedSkillIndex"], indent=2, sort_keys=True)
    external_index = json.dumps(data["externalSkillIndex"], indent=2, sort_keys=True)
    return (
        "// Auto-generated by wagents docs generate - do not edit\n"
        f"export const customSkillIndex = {custom_index};\n"
        f"export const curatedExternalSkillIndex = {curated_external_index};\n"
        f"export const installedSkillIndex = {installed_index};\n"
        f"export const externalSkillIndex = {external_index};\n"
        "export const allSkillIndex = [...customSkillIndex, ...externalSkillIndex];\n"
        "export const skillIndex = allSkillIndex;\n"
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
    rows = skill_indexes(nodes, external_skills=external_skills or [])["allSkillIndex"]
    return rows


def skill_indexes(
    nodes: list[CatalogNode], *, external_skills: list[ExternalSkillEntry] | None = None
) -> dict[str, list[dict[str, Any]]]:
    """Return filtered and deduped skill indexes for generated docs."""
    custom_rows = [_skill_node_row(node) for node in nodes if node.kind == "skill" and node.source == "custom"]
    custom_names = {str(row["name"]).lower() for row in custom_rows}
    curated_rows = [_external_skill_row(entry) for entry in (external_skills or [])]
    installed_rows = [
        _skill_node_row(node)
        for node in nodes
        if node.kind == "skill" and node.source != "custom" and node.id.lower() not in custom_names
    ]
    external_rows = _merge_external_rows(curated_rows, installed_rows)
    rows = [*custom_rows, *external_rows]
    rows.sort(key=lambda row: (str(row["sourceType"]), str(row["name"])))
    custom_rows.sort(key=lambda row: str(row["name"]))
    curated_rows.sort(key=lambda row: (str(row["status"]), str(row["sourceRoot"]), str(row["name"])))
    installed_rows.sort(key=lambda row: (str(row["sourceRoot"]), str(row["name"])))
    external_rows.sort(key=lambda row: (str(row["sourceType"]), str(row.get("status", "")), str(row["name"])))
    return {
        "customSkillIndex": custom_rows,
        "curatedExternalSkillIndex": curated_rows,
        "installedSkillIndex": installed_rows,
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
    installed_commands: dict[str, dict[str, Any]] = {}
    for row in external_rows:
        command = str(row.get("installCommand") or "").strip()
        if not command or row.get("selectorMode") == "unresolved":
            continue
        bucket = installed_commands if row["sourceType"] == "installed" else external_commands
        key = command
        record = bucket.setdefault(
            key,
            {
                "source": row.get("displaySource") or row.get("sourceRoot") or row.get("installSource") or "",
                "command": command,
                "skills": [],
                "status": row.get("status", "installed-external"),
                "trustTier": row.get("trustTier", ""),
            },
        )
        record["skills"].append(row["name"])
    return {
        "customAll": build_install_command(all_skills=True),
        "customIndividual": custom_individual,
        "externalCommands": sorted(external_commands.values(), key=lambda item: (item["source"], item["command"])),
        "installedCommands": sorted(installed_commands.values(), key=lambda item: (item["source"], item["command"])),
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
            target["installedExternalPath"] = installed.get("sourcePath", "")
            target["installedProvenanceStatus"] = installed.get("provenanceStatus", "")
            target["installedLocalInventoryOnly"] = bool(installed.get("localInventoryOnly"))
            continue
        merged.append(installed)
    return merged


def _external_row_key(row: dict[str, Any]) -> tuple[str, str]:
    source = str(row.get("sourceRoot") or row.get("installSource") or "").removeprefix("github:").lower()
    return (str(row["name"]).lower(), source)


def _skill_node_row(node: CatalogNode) -> dict[str, Any]:
    fm = node.metadata if isinstance(node.metadata, dict) else {}
    meta = fm.get("metadata", {}) if isinstance(fm.get("metadata"), dict) else {}
    source_type = "custom" if node.source == "custom" else "installed"
    raw_source_root = REPO_SOURCE if source_type == "custom" else str(fm.get("_skills_source") or node.source_path)
    source_root = raw_source_root if source_type == "custom" else _public_source_label(raw_source_root)
    source_kind = _source_kind(raw_source_root, source_type=source_type)
    local_inventory_only = source_type != "custom" and source_kind == "local-inventory"
    raw_install_source = (
        REPO_SOURCE if source_type == "custom" else str(fm.get("_skills_install_source") or raw_source_root)
    )
    install_source = "" if local_inventory_only and _is_local_path_like(raw_install_source) else raw_install_source
    install_command = (
        build_install_command(skill=node.id)
        if source_type == "custom"
        else _installed_install_command(node.id, fm, install_source, local_inventory_only=local_inventory_only)
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
        "displaySource": source_root,
        "sourceKind": source_kind,
        "installSource": install_source,
        "installable": bool(install_command),
        "localInventoryOnly": local_inventory_only,
        "trustTier": "repo" if source_type == "custom" else str(fm.get("_skills_trust_tier") or "external-installed"),
        "sourcePath": node.source_path if _is_public_path_like(node.source_path) else "",
        "sourceUrl": _source_url_for_node(node),
        "installCommand": install_command,
        "useCommand": f"/{node.id}",
        "provenanceStatus": provenance_status,
        "status": provenance_status,
        "reviewStatus": "reviewed" if source_type in {"custom", "installed"} else "",
        "targetAgents": list(SUPPORTED_AGENT_IDS) if source_type == "custom" else [],
        "installedAgents": installed_agents,
        "riskNotes": "",
        "promotionPolicy": "",
        "provenanceEvidence": provenance_status,
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
        "displaySource": entry.source or "curated external source",
        "sourceKind": _source_kind(entry.source, source_type="curated-external"),
        "installSource": entry.install_source,
        "installable": bool(entry.install_command and entry.selector_mode != "unresolved"),
        "localInventoryOnly": False,
        "trustTier": entry.trust_tier,
        "sourcePath": entry.source_path,
        "sourceUrl": entry.source_url,
        "installCommand": entry.install_command,
        "useCommand": f"/{entry.name}",
        "provenanceStatus": entry.provenance_status,
        "reviewStatus": "curated" if entry.provenance_status == "verified-install-command" else "unresolved",
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
        "installedAgents": [],
        "riskNotes": entry.risk_notes or entry.notes,
        "promotionPolicy": entry.promotion_policy or _promotion_policy_for_external_status(entry.status),
        "provenanceEvidence": entry.provenance_evidence or entry.provenance_status,
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
    command = str(metadata.get("_skills_install_command") or "").strip()
    if command and not _contains_local_path(command):
        return command
    if local_inventory_only or not install_source or _is_local_path_like(install_source):
        return ""
    return f"npx skills add {install_source} --skill {skill_id} -y -g"


def _public_source_label(value: str) -> str:
    source = str(value or "").strip()
    if not source:
        return LOCAL_INSTALLED_SOURCE_LABEL
    if _is_local_path_like(source):
        return LOCAL_INSTALLED_SOURCE_LABEL
    return source


def _source_kind(value: str, *, source_type: str) -> str:
    source = str(value or "").strip()
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
    path = str(value or "").strip()
    return bool(path) and not _is_local_path_like(path)


def _contains_local_path(value: str) -> bool:
    return bool(re.search(r"(?:/Users/|/home/|/private/|/tmp/|~/|[A-Za-z]:[\\/])", str(value or "")))


def _is_local_path_like(value: str) -> bool:
    source = str(value or "").strip()
    if not source:
        return False
    if source.startswith(("http://", "https://", "github:")):
        return False
    if source.startswith(("~/", "$HOME/", "/Users/", "/home/", "/private/", "/tmp/")):
        return True
    if re.match(r"^[A-Za-z]:[\\/]", source):
        return True
    return Path(source).is_absolute()


def _promotion_policy_for_external_status(status: str) -> str:
    return {
        "install-now-after-trust-gate": "Install only after trust gate; audit again before repo promotion.",
        "inspect-then-install": "Inspect source, hooks, scripts, credentials, and dedupe before install.",
        "global-only-or-avoid": "Keep global-only or avoid unless explicitly approved.",
        "installed-external": "Treat as local installed inventory until curated and audited.",
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
