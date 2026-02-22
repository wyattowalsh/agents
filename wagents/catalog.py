"""Data model and collection functions for skills, agents, and MCP servers."""

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path

import typer

from wagents import KEBAB_CASE_PATTERN, ROOT
from wagents.parsing import parse_frontmatter, to_title


@dataclass
class CatalogNode:
    kind: str  # 'skill' | 'agent' | 'mcp'
    id: str  # kebab-case name
    title: str  # Title Case display name
    description: str
    metadata: dict  # frontmatter (skill/agent) or pyproject data (mcp)
    body: str  # markdown body content
    source_path: str  # relative path from repo root (custom) or absolute path (installed)
    source: str = "custom"  # "custom" or "installed"


@dataclass
class CatalogEdge:
    from_id: str  # e.g., "agent:my-agent"
    to_id: str  # e.g., "skill:honest-review"
    relation: str  # 'uses-skill' | 'uses-mcp'


# Manually curated — update when skills are added, removed, or renamed
RELATED_SKILLS = {
    "wargame": ["host-panel", "prompt-engineer"],
    "host-panel": ["wargame"],
    "honest-review": ["add-badges"],
    "add-badges": ["honest-review"],
    "prompt-engineer": ["skill-creator", "wargame"],
    "skill-creator": ["prompt-engineer", "mcp-creator"],
    "mcp-creator": ["skill-creator"],
}


def collect_nodes() -> list[CatalogNode]:
    """Scan skills/, agents/, mcp/ and build CatalogNode list."""
    nodes = []

    # Skills
    skills_dir = ROOT / "skills"
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            try:
                content = skill_file.read_text()
                fm, body = parse_frontmatter(content)
                nodes.append(
                    CatalogNode(
                        kind="skill",
                        id=fm.get("name", skill_dir.name),
                        title=to_title(fm.get("name", skill_dir.name)),
                        description=str(fm.get("description", "")),
                        metadata=fm,
                        body=body,
                        source_path=f"skills/{skill_dir.name}/SKILL.md",
                    )
                )
            except Exception as e:
                typer.echo(f"Warning: skipping {skill_file}: {e}", err=True)

    # Agents
    agents_dir = ROOT / "agents"
    if agents_dir.exists():
        for agent_file in sorted(agents_dir.glob("*.md")):
            try:
                content = agent_file.read_text()
                fm, body = parse_frontmatter(content)
                nodes.append(
                    CatalogNode(
                        kind="agent",
                        id=fm.get("name", agent_file.stem),
                        title=to_title(fm.get("name", agent_file.stem)),
                        description=str(fm.get("description", "")),
                        metadata=fm,
                        body=body,
                        source_path=f"agents/{agent_file.name}",
                    )
                )
            except Exception as e:
                typer.echo(f"Warning: skipping {agent_file}: {e}", err=True)

    # MCP servers
    mcp_dir = ROOT / "mcp"
    if mcp_dir.exists():
        for mcp_subdir in sorted(mcp_dir.iterdir()):
            if not mcp_subdir.is_dir():
                continue
            pyproject = mcp_subdir / "pyproject.toml"
            server_py = mcp_subdir / "server.py"
            if not pyproject.exists():
                continue
            try:
                data = tomllib.loads(pyproject.read_text())
                proj = data.get("project", {})
                name = mcp_subdir.name
                server_body = server_py.read_text() if server_py.exists() else ""

                # Read fastmcp.json if it exists
                fastmcp_json = mcp_subdir / "fastmcp.json"
                fastmcp_config = {}
                if fastmcp_json.exists():
                    fastmcp_config = json.loads(fastmcp_json.read_text())

                metadata = {**data, "fastmcp_config": fastmcp_config}

                nodes.append(
                    CatalogNode(
                        kind="mcp",
                        id=name,
                        title=to_title(name),
                        description=str(proj.get("description", "")),
                        metadata=metadata,
                        body=server_body,
                        source_path=f"mcp/{name}/server.py",
                    )
                )
            except Exception as e:
                typer.echo(f"Warning: skipping {mcp_subdir}: {e}", err=True)

    return nodes


def collect_installed_skills(existing_ids: set[str]) -> list[CatalogNode]:
    """Scan ~/.claude/skills/ for installed skills not in the repo."""
    nodes = []
    skills_dir = Path.home() / ".claude" / "skills"
    if not skills_dir.exists():
        return nodes

    seen_ids: set[str] = set()
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir() and not skill_dir.is_symlink():
            continue
        # Resolve symlinks
        resolved = skill_dir.resolve() if skill_dir.is_symlink() else skill_dir
        skill_file = resolved / "SKILL.md"
        if not skill_file.exists():
            continue

        dir_name = skill_dir.name
        # Skip if already in custom skills
        if dir_name in existing_ids:
            continue

        try:
            content = skill_file.read_text()
            fm, body = parse_frontmatter(content)
            # Graceful fallback: use directory name if 'name' field missing
            skill_name = fm.get("name", dir_name)
            resolved_id = skill_name if KEBAB_CASE_PATTERN.match(str(skill_name)) else dir_name
            # Skip if resolved ID collides with existing or already-seen installed skill
            if resolved_id in existing_ids or resolved_id in seen_ids:
                continue
            seen_ids.add(resolved_id)
            nodes.append(
                CatalogNode(
                    kind="skill",
                    id=resolved_id,
                    title=to_title(skill_name if KEBAB_CASE_PATTERN.match(str(skill_name)) else dir_name),
                    description=str(fm.get("description", f"Installed skill: {dir_name}")),
                    metadata=fm,
                    body=body,
                    source_path=str(skill_file),
                    source="installed",
                )
            )
        except Exception as e:
            typer.echo(f"Warning: skipping installed skill {skill_dir.name}: {e}", err=True)

    return nodes


def collect_edges(nodes: list[CatalogNode]) -> list[CatalogEdge]:
    """Extract cross-reference edges from agent metadata."""
    edges = []
    for node in nodes:
        if node.kind != "agent":
            continue
        # Agent skills references
        skills = node.metadata.get("skills", [])
        if isinstance(skills, list):
            for skill_name in skills:
                edges.append(
                    CatalogEdge(
                        from_id=f"agent:{node.id}",
                        to_id=f"skill:{skill_name}",
                        relation="uses-skill",
                    )
                )
        # Agent MCP server references
        mcps = node.metadata.get("mcpServers", [])
        if isinstance(mcps, list):
            for mcp_name in mcps:
                edges.append(
                    CatalogEdge(
                        from_id=f"agent:{node.id}",
                        to_id=f"mcp:{mcp_name}",
                        relation="uses-mcp",
                    )
                )
    return edges
