"""Data model and collection functions for skills, agents, and MCP servers."""

import json
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

import typer

from wagents import KEBAB_CASE_PATTERN, ROOT
from wagents.installed_inventory import collect_installed_inventory
from wagents.parsing import parse_frontmatter, to_title

LOCAL_MCP_DIR_NAMES = {"archives", "cache", "notes", "secrets", "servers"}


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
    "wargame": ["host-panel", "prompt-engineer", "orchestrator"],
    "host-panel": ["wargame"],
    "honest-review": ["add-badges", "orchestrator"],
    "add-badges": ["honest-review"],
    "prompt-engineer": ["skill-creator", "wargame"],
    "skill-creator": ["prompt-engineer", "mcp-creator"],
    "mcp-creator": ["skill-creator"],
    "orchestrator": ["honest-review", "wargame"],
    "python-conventions": ["javascript-conventions"],
    "javascript-conventions": ["python-conventions"],
    "learn": ["python-conventions", "javascript-conventions", "agent-conventions"],
    "release-pipeline-architect": ["devops-engineer", "incident-response-engineer", "changelog-writer"],
    "incident-response-engineer": ["release-pipeline-architect", "security-scanner", "honest-review"],
    "observability-advisor": ["incident-response-engineer", "performance-profiler", "devops-engineer"],
    "shell-conventions": ["shell-scripter", "python-conventions", "javascript-conventions"],
    "schema-evolution-planner": ["database-architect", "api-designer", "data-pipeline-architect"],
    "event-driven-architect": ["api-designer", "orchestrator", "data-pipeline-architect"],
    "data-pipeline-architect": ["data-wizard", "database-architect", "event-driven-architect"],
}


def _load_installed_skill_sources() -> dict[str, dict]:
    """Load installed skill source metadata from known global lock files."""
    merged: dict[str, dict] = {}
    candidates = [
        Path.home() / ".agents" / ".skill-lock.json",
        Path.home() / ".local" / "state" / "skills" / ".skill-lock.json",
    ]
    for lock_path in candidates:
        if not lock_path.exists():
            continue
        try:
            data = json.loads(lock_path.read_text())
            skills = data.get("skills", {})
            if isinstance(skills, dict):
                merged.update(skills)
        except (OSError, json.JSONDecodeError):
            continue
    return merged


def _is_git_ignored(path: Path) -> bool:
    try:
        rel_path = path.relative_to(ROOT)
    except ValueError:
        return False
    candidates = [str(rel_path)]
    if path.is_dir():
        candidates.append(str(rel_path / "__wagents_check__"))
    for candidate in candidates:
        try:
            result = subprocess.run(
                ["git", "-C", str(ROOT), "check-ignore", "-q", candidate],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except OSError:
            return False
        if result.returncode == 0:
            return True
    return False


def _is_local_mcp_dir(path: Path) -> bool:
    """Return whether an MCP subdirectory is reserved for local machine assets."""
    return path.name in LOCAL_MCP_DIR_NAMES or _is_git_ignored(path)


def _collect_mcp_nodes(nodes: list[CatalogNode]) -> None:
    """Append repo-authored MCP server nodes from mcp/<name>/."""
    mcp_dir = ROOT / "mcp"
    if not mcp_dir.exists():
        return

    for mcp_subdir in sorted(mcp_dir.iterdir()):
        if not mcp_subdir.is_dir():
            continue
        if _is_local_mcp_dir(mcp_subdir):
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


def collect_nodes() -> list[CatalogNode]:
    """Scan skills/, agents/, and repo-authored mcp/<name>/ servers."""
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

    _collect_mcp_nodes(nodes)

    return nodes


def collect_installed_skills(existing_ids: set[str]) -> list[CatalogNode]:
    """Collect installed skills from the normalized harness inventory."""
    snapshot = collect_installed_inventory()
    if snapshot.rows:
        return _catalog_nodes_from_inventory(snapshot.rows, existing_ids)
    return _collect_legacy_installed_skills(existing_ids)


def _catalog_nodes_from_inventory(rows, existing_ids: set[str]) -> list[CatalogNode]:
    nodes: list[CatalogNode] = []
    seen_ids: set[str] = set()
    for row in rows:
        if row.name in existing_ids or row.name in seen_ids:
            continue
        skill_file = Path(row.source_path)
        if skill_file.is_dir():
            skill_file = skill_file / "SKILL.md"
        if not skill_file.exists():
            continue
        try:
            fm, body = parse_frontmatter(skill_file.read_text(encoding="utf-8", errors="replace"))
        except Exception as exc:
            typer.echo(f"Warning: skipping installed skill {row.name}: {exc}", err=True)
            continue
        metadata = dict(fm)
        if row.source:
            metadata["_skills_source"] = row.source
        if row.install_source:
            metadata["_skills_install_source"] = row.install_source
        metadata["_skills_install_command"] = row.install_command
        metadata["_skills_provenance_status"] = row.provenance_status
        metadata["_skills_trust_tier"] = row.trust_tier
        metadata["_skills_installed_agents"] = list(row.installed_agents)
        metadata["_skills_target_agents"] = list(row.target_agents)
        if row.selector_mode:
            metadata["_skills_selector_mode"] = row.selector_mode
        seen_ids.add(row.name)
        nodes.append(
            CatalogNode(
                kind="skill",
                id=row.name,
                title=to_title(row.name),
                description=row.description or str(fm.get("description", f"Installed skill: {row.name}")),
                metadata=metadata,
                body=body,
                source_path=str(skill_file),
                source="installed",
            )
        )
    return nodes


def _collect_legacy_installed_skills(existing_ids: set[str]) -> list[CatalogNode]:
    """Fallback scan for environments without `npx skills ls --json`."""
    nodes = []
    skills_dir = Path.home() / ".claude" / "skills"
    if not skills_dir.exists():
        return nodes
    installed_sources = _load_installed_skill_sources()

    seen_ids: set[str] = set()
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir() and not skill_dir.is_symlink():
            continue
        resolved = skill_dir.resolve() if skill_dir.is_symlink() else skill_dir
        skill_file = resolved / "SKILL.md"
        if not skill_file.exists():
            continue

        dir_name = skill_dir.name
        if dir_name in existing_ids:
            continue

        try:
            content = skill_file.read_text()
            fm, body = parse_frontmatter(content)
            skill_name = fm.get("name", dir_name)
            resolved_id = skill_name if KEBAB_CASE_PATTERN.match(str(skill_name)) else dir_name
            if resolved_id in existing_ids or resolved_id in seen_ids:
                continue
            seen_ids.add(resolved_id)
            lock_meta = installed_sources.get(resolved_id) or installed_sources.get(dir_name) or {}
            metadata = dict(fm)
            if isinstance(lock_meta, dict) and lock_meta.get("source"):
                metadata["_skills_source"] = lock_meta["source"]
            nodes.append(
                CatalogNode(
                    kind="skill",
                    id=resolved_id,
                    title=to_title(skill_name if KEBAB_CASE_PATTERN.match(str(skill_name)) else dir_name),
                    description=str(fm.get("description", f"Installed skill: {dir_name}")),
                    metadata=metadata,
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
