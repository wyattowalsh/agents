"""CLI for managing centralized AI agent assets."""

import importlib.metadata
import json
import re
import shutil
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import typer
import yaml

# Constants
ROOT = Path(__file__).resolve().parent.parent
VERSION = importlib.metadata.version("wagents")
KEBAB_CASE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")

# Typer apps
app = typer.Typer(help="CLI for managing centralized AI agent assets")
new_app = typer.Typer(help="Create new assets from reference templates")
app.add_typer(new_app, name="new")


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        typer.echo(f"wagents {VERSION}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, help="Show version and exit"
    )
):
    """CLI for managing centralized AI agent assets."""
    pass


def to_title(name: str) -> str:
    """Convert kebab-case name to Title Case."""
    return name.replace("-", " ").title()


def _truncate_sentence(text: str, max_len: int) -> str:
    """Truncate at sentence boundary before max_len; fall back to word boundary with ellipsis."""
    if len(text) <= max_len:
        return text
    chunk = text[:max_len]
    # Find last sentence boundary
    for i in range(len(chunk) - 1, -1, -1):
        if chunk[i] in '.!?':
            return chunk[: i + 1]
    # Fall back to word boundary
    last_space = chunk.rfind(' ')
    if last_space > 0:
        return chunk[:last_space] + '\u2026'
    return chunk[:max_len - 1] + '\u2026'


def _strip_relative_md_links(text: str) -> str:
    """Convert relative .md links [text](file.md) to just `text` (no link)."""
    return re.sub(
        r'\[([^\]]+)\]\((?!https?://|/)[^)]*\.md\)',
        r'`\1`',
        text,
    )


class _FenceTracker:
    """Track fenced code block state for fence-aware markdown processing."""

    def __init__(self) -> None:
        self._char: str | None = None
        self._count: int = 0

    @property
    def inside_fence(self) -> bool:
        return self._char is not None

    def update(self, line: str) -> bool:
        """Update state for *line*. Returns True if the line is a fence boundary."""
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent <= 3 and (stripped.startswith('```') or stripped.startswith('~~~')):
            char = stripped[0]
            count = len(stripped) - len(stripped.lstrip(char))
            if self._char is None:
                self._char = char
                self._count = count
                return True
            if char == self._char and count >= self._count:
                self._char = None
                self._count = 0
                return True
        return False


def _shift_headings(body: str, levels: int = 1) -> str:
    """Shift all markdown headings down by `levels` (e.g. # -> ## when levels=1).

    Fence-aware: skips headings inside fenced code blocks.
    """
    extra = '#' * levels
    lines = body.split('\n')
    result = []
    fence = _FenceTracker()

    for line in lines:
        if fence.update(line) or fence.inside_fence:
            result.append(line)
        else:
            result.append(re.sub(r'^(#{1,5})', lambda m: extra + m.group(1), line))

    return '\n'.join(result)


def _escape_attr(text: str) -> str:
    """Escape text for use in HTML/MDX attribute values."""
    return (
        text.replace('&', '&amp;')
        .replace('"', '&quot;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
    )


def _validate_name(name: str) -> None:
    """Validate asset name is kebab-case and within length limit."""
    if not KEBAB_CASE_PATTERN.match(name):
        typer.echo(f"Error: name must be kebab-case (got '{name}')", err=True)
        raise typer.Exit(code=1)
    if len(name) > 64:
        typer.echo("Error: name exceeds 64 characters", err=True)
        raise typer.Exit(code=1)


@new_app.command("skill")
def new_skill(
    name: str,
    no_docs: bool = typer.Option(False, "--no-docs", help="Skip docs page scaffold"),
):
    """Create a new skill from template."""
    _validate_name(name)
    skill_dir = ROOT / "skills" / name
    skill_file = skill_dir / "SKILL.md"

    if skill_file.exists():
        typer.echo(f"Error: {skill_file} already exists", err=True)
        raise typer.Exit(code=1)

    skill_dir.mkdir(parents=True, exist_ok=True)

    title = to_title(name)
    content = f'''---
name: {name}
description: TODO — What this skill does and when to use it

## Cross-Platform (agentskills.io spec)
# license: MIT                              # SPDX identifier
# compatibility: "Requires git and docker"  # Environment requirements (max 500 chars)
# allowed-tools: Read Grep Glob             # Space-delimited tool allowlist (experimental)
# metadata:
#   author: wyattowalsh
#   version: "1.0"
#   internal: false                         # If true, hidden unless INSTALL_INTERNAL_SKILLS=1

## Claude Code Extensions
# argument-hint: "[query]"                  # Shown during autocomplete
# model: sonnet                             # Model override: sonnet | opus | haiku
# context: fork                             # Run in isolated subagent
# agent: Explore                            # Subagent type when context: fork
# user-invocable: true                      # Set false to hide from / menu (background knowledge only)
# disable-model-invocation: false           # Set true to prevent auto-invocation (manual /name only)
# hooks:                                    # Lifecycle hooks scoped to this skill
#   PreToolUse:
#     - matcher: Bash
#       hooks: [{{command: "echo check"}}]
---

# {title}

Skill instructions go here in markdown. Use imperative voice.

## When to Use

Describe when an AI agent should invoke this skill.

## Instructions

Step-by-step instructions for the agent.
'''

    skill_file.write_text(content)
    typer.echo(f"Created skills/{name}/SKILL.md")

    if not no_docs:
        fm, body = parse_frontmatter(content)
        node = CatalogNode(
            kind="skill", id=name, title=to_title(name),
            description=str(fm.get("description", "")),
            metadata=fm, body=body,
            source_path=f"skills/{name}/SKILL.md",
        )
        _scaffold_doc_page(node)
        _regenerate_sidebar_and_indexes()
        typer.echo("Regenerated sidebar and index pages")


@new_app.command("agent")
def new_agent(
    name: str,
    no_docs: bool = typer.Option(False, "--no-docs", help="Skip docs page scaffold"),
):
    """Create a new agent from template."""
    _validate_name(name)
    agents_dir = ROOT / "agents"
    agent_file = agents_dir / f"{name}.md"

    if agent_file.exists():
        typer.echo(f"Error: {agent_file} already exists", err=True)
        raise typer.Exit(code=1)

    agents_dir.mkdir(parents=True, exist_ok=True)

    title = to_title(name)
    content = f'''---
name: {name}
description: TODO — When Claude should delegate to this agent

# tools: Read, Glob, Grep, Bash            # Tool allowlist (inherits all if omitted)
# disallowedTools: Write, Edit              # Tool denylist (removed from inherited set)
# model: sonnet                             # Model: sonnet | opus | haiku | inherit
# permissionMode: default                   # default | acceptEdits | delegate | dontAsk | bypassPermissions | plan
# maxTurns: 50                              # Maximum agentic turns before stopping
# skills:                                   # Skills preloaded into agent context
#   - skill-name
# mcpServers:                               # MCP servers available to this agent
#   - server-name
# memory: project                           # Persistent memory: user | project | local
# hooks:                                    # Lifecycle hooks scoped to this agent
#   PreToolUse:
#     - matcher: Bash
#       hooks: [{{command: "echo check"}}]
---

# {title}

This is the agent's system prompt. Everything below the frontmatter
is injected as instructions when this agent is spawned.

## Capabilities

Describe what this agent specializes in.

## Guidelines

Rules and constraints for this agent's behavior.
'''

    agent_file.write_text(content)
    typer.echo(f"Created agents/{name}.md")

    if not no_docs:
        fm, body = parse_frontmatter(content)
        node = CatalogNode(
            kind="agent", id=name, title=to_title(name),
            description=str(fm.get("description", "")),
            metadata=fm, body=body,
            source_path=f"agents/{name}.md",
        )
        _scaffold_doc_page(node)
        _regenerate_sidebar_and_indexes()
        typer.echo("Regenerated sidebar and index pages")


@new_app.command("mcp")
def new_mcp(
    name: str,
    no_docs: bool = typer.Option(False, "--no-docs", help="Skip docs page scaffold"),
):
    """Create a new MCP server from template."""
    _validate_name(name)
    mcp_dir = ROOT / "mcp" / name

    if mcp_dir.exists():
        typer.echo(f"Error: {mcp_dir} already exists", err=True)
        raise typer.Exit(code=1)

    mcp_dir.mkdir(parents=True, exist_ok=True)

    title = to_title(name)

    # Create server.py
    server_content = f'''"""MCP server: {name}."""

from fastmcp import FastMCP

mcp = FastMCP("{title}")


@mcp.tool
def hello(query: str) -> str:
    """Example tool — replace with your implementation."""
    return f"Hello from {name}: {{query}}"
'''
    (mcp_dir / "server.py").write_text(server_content)

    # Create pyproject.toml
    pyproject_content = f'''[project]
name = "mcp-{name}"
version = "0.1.0"
description = "TODO — What this MCP server does"
requires-python = ">=3.13"
dependencies = ["fastmcp>=2"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
'''
    (mcp_dir / "pyproject.toml").write_text(pyproject_content)

    # Create fastmcp.json
    fastmcp_config = {
        "$schema": "https://gofastmcp.com/public/schemas/fastmcp.json/v1.json",
        "source": {
            "path": "server.py",
            "entrypoint": "mcp"
        },
        "environment": {
            "type": "uv"
        }
    }
    (mcp_dir / "fastmcp.json").write_text(json.dumps(fastmcp_config, indent=2) + "\n")

    # Update root pyproject.toml if needed
    root_pyproject = ROOT / "pyproject.toml"
    content = root_pyproject.read_text()

    if "[tool.uv.workspace]" not in content:
        if not content.endswith("\n"):
            content += "\n"
        content += "\n[tool.uv.workspace]\nmembers = [\"mcp/*\"]\n"
        root_pyproject.write_text(content)

    typer.echo(f"Created mcp/{name}/ with server.py, pyproject.toml, and fastmcp.json")

    if not no_docs:
        metadata = {
            "project": {"name": f"mcp-{name}", "version": "0.1.0",
                        "description": "TODO — What this MCP server does",
                        "requires-python": ">=3.13",
                        "dependencies": ["fastmcp>=2"]},
            "fastmcp_config": fastmcp_config,
        }
        node = CatalogNode(
            kind="mcp", id=name, title=to_title(name),
            description="TODO — What this MCP server does",
            metadata=metadata, body=server_content,
            source_path=f"mcp/{name}/server.py",
        )
        _scaffold_doc_page(node)
        _regenerate_sidebar_and_indexes()
        typer.echo("Regenerated sidebar and index pages")


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter and return (frontmatter_dict, body)."""
    if not content.startswith("---\n"):
        raise ValueError("Invalid frontmatter: must start with '---'")
    rest = content[4:]
    end_idx = rest.find("\n---\n")
    if end_idx == -1:
        # Handle case where --- is at very end of file
        if rest.endswith("\n---"):
            end_idx = len(rest) - 3
        else:
            raise ValueError("Invalid frontmatter: missing closing '---'")
    frontmatter = yaml.safe_load(rest[:end_idx])
    body = rest[end_idx + 5:].strip() if end_idx + 5 <= len(rest) else ""
    return frontmatter, body


@app.command()
def validate():
    """Validate all skills and agents."""
    errors = []

    # Validate skills
    skills_dir = ROOT / "skills"
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            try:
                content = skill_file.read_text()
                fm, body = parse_frontmatter(content)

                # Validate name
                if "name" not in fm:
                    errors.append(f"{skill_file}: missing required field 'name'")
                else:
                    name = fm["name"]
                    if not KEBAB_CASE_PATTERN.match(name):
                        errors.append(f"{skill_file}: name must be kebab-case")
                    if len(name) > 64:
                        errors.append(f"{skill_file}: name exceeds 64 characters")
                    if name != skill_dir.name:
                        errors.append(f"{skill_file}: name '{name}' doesn't match directory '{skill_dir.name}'")

                # Validate description
                if "description" not in fm:
                    errors.append(f"{skill_file}: missing required field 'description'")
                elif not str(fm["description"]).strip():
                    errors.append(f"{skill_file}: description cannot be empty")
                elif len(str(fm["description"])) > 1024:
                    errors.append(f"{skill_file}: description exceeds 1024 characters")

                # Validate body
                if not body:
                    errors.append(f"{skill_file}: body cannot be empty")

            except Exception as e:
                errors.append(f"{skill_file}: {e}")

    # Validate agents
    agents_dir = ROOT / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            try:
                content = agent_file.read_text()
                fm, _ = parse_frontmatter(content)

                # Validate name
                if "name" not in fm:
                    errors.append(f"{agent_file}: missing required field 'name'")
                else:
                    name = fm["name"]
                    if not KEBAB_CASE_PATTERN.match(name):
                        errors.append(f"{agent_file}: name must be kebab-case")
                    if name != agent_file.stem:
                        errors.append(f"{agent_file}: name '{name}' doesn't match filename '{agent_file.stem}'")

                # Validate description
                if "description" not in fm:
                    errors.append(f"{agent_file}: missing required field 'description'")
                elif not str(fm["description"]).strip():
                    errors.append(f"{agent_file}: description cannot be empty")

            except Exception as e:
                errors.append(f"{agent_file}: {e}")

    if errors:
        for error in errors:
            typer.echo(error, err=True)
        raise typer.Exit(code=1)
    else:
        typer.echo("All validations passed")


@app.command()
def readme(check: bool = typer.Option(False, "--check", help="Check if README is up to date")):
    """Generate or check README.md."""
    content_parts = [
        "# agents",
        "",
        "AI agent artifacts, configs, skills, tools, and more",
        "",
        "## Install",
        "",
        "```bash",
        "npx skills add wyattowalsh/agents --all -g",
        "```",
        ""
    ]

    # Skills table
    skills_dir = ROOT / "skills"
    if skills_dir.exists():
        skills = []
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                try:
                    fm, _ = parse_frontmatter(skill_file.read_text())
                    skills.append((fm.get("name", skill_dir.name), fm.get("description", "")))
                except Exception as e:
                    typer.echo(f"Warning: skipping {skill_file}: {e}", err=True)

        if skills:
            content_parts.extend([
                "## Skills",
                "",
                "| Name | Description |",
                "| ---- | ----------- |"
            ])
            for name, desc in skills:
                content_parts.append(f"| {name} | {desc} |")
            content_parts.append("")

    # Agents table
    agents_dir = ROOT / "agents"
    if agents_dir.exists():
        agents = []
        for agent_file in sorted(agents_dir.glob("*.md")):
            try:
                fm, _ = parse_frontmatter(agent_file.read_text())
                agents.append((fm.get("name", agent_file.stem), fm.get("description", "")))
            except Exception as e:
                typer.echo(f"Warning: skipping {agent_file}: {e}", err=True)

        if agents:
            content_parts.extend([
                "## Agents",
                "",
                "| Name | Description |",
                "| ---- | ----------- |"
            ])
            for name, desc in agents:
                content_parts.append(f"| {name} | {desc} |")
            content_parts.append("")

    # MCP servers table
    mcp_dir = ROOT / "mcp"
    if mcp_dir.exists():
        mcps = []
        for mcp_subdir in sorted(mcp_dir.iterdir()):
            if not mcp_subdir.is_dir():
                continue
            pyproject = mcp_subdir / "pyproject.toml"
            if pyproject.exists():
                try:
                    data = tomllib.loads(pyproject.read_text())
                    name = data.get("project", {}).get("name", mcp_subdir.name)
                    desc = data.get("project", {}).get("description", "")
                    mcps.append((name, desc))
                except Exception:
                    mcps.append((mcp_subdir.name, ""))

        if mcps:
            content_parts.extend([
                "## MCP Servers",
                "",
                "| Name | Description |",
                "| ---- | ----------- |"
            ])
            for name, desc in mcps:
                content_parts.append(f"| {name} | {desc} |")
            content_parts.append("")

    # Dev commands
    content_parts.extend([
        "## Development",
        "",
        "| Command | Description |",
        "| ------- | ----------- |",
        "| `wagents new skill <name>` | Create a new skill |",
        "| `wagents new agent <name>` | Create a new agent |",
        "| `wagents new mcp <name>` | Create a new MCP server |",
        "| `wagents validate` | Validate all skills and agents |",
        "| `wagents readme` | Regenerate this README |",
        ""
    ])

    # Supported agents
    content_parts.extend([
        "## Supported Agents",
        "",
        "Claude Code, Codex, Gemini CLI, and other agentskills.io-compatible agents.",
        ""
    ])

    # License
    content_parts.extend([
        "## License",
        "",
        "[MIT](LICENSE)",
        ""
    ])

    generated_content = "\n".join(content_parts)

    readme_file = ROOT / "README.md"

    if check:
        if not readme_file.exists():
            typer.echo("README.md is missing. Run `wagents readme` to create it.")
            raise typer.Exit(code=1)
        if readme_file.read_text() != generated_content:
            typer.echo("README.md is stale. Run `wagents readme` to update.")
            raise typer.Exit(code=1)
        typer.echo("README.md is up to date")
    else:
        readme_file.write_text(generated_content)
        typer.echo("Updated README.md")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class CatalogNode:
    kind: str          # 'skill' | 'agent' | 'mcp'
    id: str            # kebab-case name
    title: str         # Title Case display name
    description: str
    metadata: dict     # frontmatter (skill/agent) or pyproject data (mcp)
    body: str          # markdown body content
    source_path: str   # relative path from repo root (custom) or absolute path (installed)
    source: str = "custom"  # "custom" or "installed"


@dataclass
class CatalogEdge:
    from_id: str       # e.g., "agent:my-agent"
    to_id: str         # e.g., "skill:honest-review"
    relation: str      # 'uses-skill' | 'uses-mcp'


# ---------------------------------------------------------------------------
# Collector functions
# ---------------------------------------------------------------------------


def _collect_nodes() -> list[CatalogNode]:
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
                nodes.append(CatalogNode(
                    kind="skill",
                    id=fm.get("name", skill_dir.name),
                    title=to_title(fm.get("name", skill_dir.name)),
                    description=str(fm.get("description", "")),
                    metadata=fm,
                    body=body,
                    source_path=f"skills/{skill_dir.name}/SKILL.md",
                ))
            except Exception as e:
                typer.echo(f"Warning: skipping {skill_file}: {e}", err=True)

    # Agents
    agents_dir = ROOT / "agents"
    if agents_dir.exists():
        for agent_file in sorted(agents_dir.glob("*.md")):
            try:
                content = agent_file.read_text()
                fm, body = parse_frontmatter(content)
                nodes.append(CatalogNode(
                    kind="agent",
                    id=fm.get("name", agent_file.stem),
                    title=to_title(fm.get("name", agent_file.stem)),
                    description=str(fm.get("description", "")),
                    metadata=fm,
                    body=body,
                    source_path=f"agents/{agent_file.name}",
                ))
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

                nodes.append(CatalogNode(
                    kind="mcp",
                    id=name,
                    title=to_title(name),
                    description=str(proj.get("description", "")),
                    metadata=metadata,
                    body=server_body,
                    source_path=f"mcp/{name}/server.py",
                ))
            except Exception as e:
                typer.echo(f"Warning: skipping {mcp_subdir}: {e}", err=True)

    return nodes


def _collect_installed_skills(existing_ids: set[str]) -> list[CatalogNode]:
    """Scan ~/.claude/skills/ for installed skills not in the repo."""
    nodes = []
    skills_dir = Path.home() / ".claude" / "skills"
    if not skills_dir.exists():
        return nodes

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
            nodes.append(CatalogNode(
                kind="skill",
                id=skill_name if KEBAB_CASE_PATTERN.match(str(skill_name)) else dir_name,
                title=to_title(skill_name if KEBAB_CASE_PATTERN.match(str(skill_name)) else dir_name),
                description=str(fm.get("description", f"Installed skill: {dir_name}")),
                metadata=fm,
                body=body,
                source_path=str(skill_file),
                source="installed",
            ))
        except Exception as e:
            typer.echo(f"Warning: skipping installed skill {skill_dir.name}: {e}", err=True)

    return nodes


def _collect_edges(nodes: list[CatalogNode]) -> list[CatalogEdge]:
    """Extract cross-reference edges from agent metadata."""
    edges = []
    for node in nodes:
        if node.kind != "agent":
            continue
        # Agent skills references
        skills = node.metadata.get("skills", [])
        if isinstance(skills, list):
            for skill_name in skills:
                edges.append(CatalogEdge(
                    from_id=f"agent:{node.id}",
                    to_id=f"skill:{skill_name}",
                    relation="uses-skill",
                ))
        # Agent MCP server references
        mcps = node.metadata.get("mcpServers", [])
        if isinstance(mcps, list):
            for mcp_name in mcps:
                edges.append(CatalogEdge(
                    from_id=f"agent:{node.id}",
                    to_id=f"mcp:{mcp_name}",
                    relation="uses-mcp",
                ))
    return edges


# ---------------------------------------------------------------------------
# MDX escaper
# ---------------------------------------------------------------------------


def _escape_mdx(body: str) -> str:
    """Escape markdown body for safe MDX embedding."""
    lines = body.split('\n')
    result = []
    fence = _FenceTracker()

    for line in lines:
        if fence.update(line) or fence.inside_fence:
            result.append(line)
        else:
            result.append(_escape_mdx_line(line))

    return '\n'.join(result)


def _escape_mdx_line(line: str) -> str:
    """Escape a single MDX line, preserving inline code spans."""
    if line.startswith('import ') or line.startswith('export '):
        return '\\' + line

    # Find all inline code span ranges
    code_ranges = []
    i = 0
    while i < len(line):
        if line[i] == '`':
            bt_start = i
            bt_count = 0
            while i < len(line) and line[i] == '`':
                bt_count += 1
                i += 1
            close_idx = line.find('`' * bt_count, i)
            if close_idx != -1:
                code_ranges.append((bt_start, close_idx + bt_count))
                i = close_idx + bt_count
        else:
            i += 1

    def in_code(pos):
        return any(s <= pos < e for s, e in code_ranges)

    out = []
    i = 0
    while i < len(line):
        if in_code(i):
            out.append(line[i])
            i += 1
            continue
        if line[i:i+4] == '<!--':
            end = line.find('-->', i + 4)
            if end != -1:
                content = line[i+4:end].strip()
                out.append('{/* ' + content + ' */}')
                i = end + 3
                continue
        if line[i] in '{}':
            out.append('\\' + line[i])
            i += 1
            continue
        if line[i] == '<':
            out.append('\\<')
            i += 1
            continue
        out.append(line[i])
        i += 1

    return ''.join(out)


# ---------------------------------------------------------------------------
# Page renderers
# ---------------------------------------------------------------------------

GITHUB_BASE = "https://github.com/wyattowalsh/agents/blob/main"

RELATED_SKILLS = {
    "wargame": ["host-panel", "prompt-engineer"],
    "host-panel": ["wargame"],
    "honest-review": ["add-badges"],
    "add-badges": ["honest-review"],
    "prompt-engineer": ["skill-creator", "wargame"],
    "skill-creator": ["prompt-engineer", "mcp-creator"],
    "mcp-creator": ["skill-creator"],
}


def _render_page(node: CatalogNode, edges: list[CatalogEdge], all_nodes: list[CatalogNode]) -> str:
    """Render a CatalogNode to MDX string."""
    if node.kind == "skill":
        return _render_skill_page(node, edges, all_nodes)
    elif node.kind == "agent":
        return _render_agent_page(node, edges, all_nodes)
    elif node.kind == "mcp":
        return _render_mcp_page(node, edges, all_nodes)
    return ""


def _scaffold_doc_page(node: CatalogNode) -> None:
    """Create a single docs page for a newly scaffolded asset."""
    if not CONTENT_DIR.exists():
        return
    page_dir = CONTENT_DIR / (node.kind + "s" if node.kind != "mcp" else "mcp")
    page_dir.mkdir(parents=True, exist_ok=True)
    content = _render_page(node, [], [node])
    (page_dir / f"{node.id}.mdx").write_text(content)
    rel = page_dir.relative_to(ROOT) / f"{node.id}.mdx"
    typer.echo(f"Created {rel}")


def _read_raw_content(node: CatalogNode) -> str:
    """Read the raw file content for a CatalogNode from disk."""
    if node.source == "custom":
        raw_path = ROOT / node.source_path
    else:
        raw_path = Path(node.source_path)
    try:
        return raw_path.read_text()
    except Exception:
        # Fallback: reconstruct from parsed data
        raw_lines = ["---"]
        for key, value in node.metadata.items():
            raw_lines.append(yaml.dump({key: value}, default_flow_style=False).strip())
        raw_lines.append("---")
        if node.body:
            raw_lines.append("")
            raw_lines.append(node.body)
        return "\n".join(raw_lines)


def _render_skill_page(node: CatalogNode, edges: list[CatalogEdge], all_nodes: list[CatalogNode]) -> str:
    fm = node.metadata
    parts = []

    # Read raw content from disk for the copyable code block
    raw_content = _read_raw_content(node)

    # Frontmatter
    parts.append("---")
    parts.append(f"title: \"{node.id}\"")
    parts.append(f"description: \"{_escape_attr(_truncate_sentence(node.description, 200))}\"")
    parts.append("---")
    parts.append("")

    # Imports
    parts.append("import { Badge, Tabs, TabItem, Card, CardGrid, LinkCard, Aside, Steps } from '@astrojs/starlight/components';")
    parts.append("")

    # === TIER 1: Human summary ===

    # Badge row — standardized: always show name + word count
    badges = []
    badges.append(f'<Badge text="{_escape_attr(node.id)}" variant="note" />')
    word_count = len(node.body.split()) if node.body else 0
    badges.append(f'<Badge text="{word_count} words" variant="default" />')
    if fm.get("license"):
        badges.append(f'<Badge text="{_escape_attr(fm["license"])}" variant="success" />')
    meta = fm.get("metadata", {})
    if isinstance(meta, dict):
        if meta.get("version"):
            badges.append(f'<Badge text="v{_escape_attr(str(meta["version"]))}" variant="success" />')
        if meta.get("author"):
            badges.append(f'<Badge text="{_escape_attr(meta["author"])}" variant="caution" />')
    if fm.get("model"):
        badges.append(f'<Badge text="{_escape_attr(fm["model"])}" variant="tip" />')
    if node.source != "custom":
        badges.append(f'<Badge text="Installed" variant="caution" />')
    parts.append(" ".join(badges))
    parts.append("")

    # Description
    parts.append(f"> {node.description}")
    parts.append("")

    # Quick Start box
    parts.append('<div class="quick-start">')
    parts.append("")
    parts.append("### Quick Start")
    parts.append("")
    parts.append("**Install:**")
    parts.append("```bash")
    if node.source == "custom":
        parts.append(f"npx skills add wyattowalsh/agents/skills/{node.id} -g")
    else:
        parts.append(f"npx skills add {node.id} -g")
    parts.append("```")
    parts.append("")
    use_line = f"**Use:** `/{node.id}`"
    if fm.get("argument-hint"):
        use_line += f" `{fm['argument-hint']}`"
    parts.append(use_line)
    parts.append("")
    parts.append("</div>")
    parts.append("")

    # Guide cross-link — check if a hand-maintained guide page exists
    guide_path = CONTENT_DIR / "guides" / f"{node.id}.mdx"
    if guide_path.exists():
        parts.append(f'<LinkCard title="Full Guide: {node.id}" href="/guides/{node.id}/" description="Architecture, research sources, framework catalog, design decisions, and roadmap." />')
        parts.append("")

    # "What it does" section — first paragraph after first heading
    what_it_does = ""
    if node.body:
        body_lines = node.body.split('\n')
        found_heading = False
        para_lines = []
        for bl in body_lines:
            if not found_heading:
                if bl.strip().startswith('#'):
                    found_heading = True
                continue
            if bl.strip() == '':
                if para_lines:
                    break
                continue
            para_lines.append(bl.strip())
        if para_lines:
            what_it_does = ' '.join(para_lines)

    if what_it_does:
        parts.append("## What It Does")
        parts.append("")
        parts.append(_strip_relative_md_links(_escape_mdx(what_it_does)))
        parts.append("")

    # Extract dispatch table if present
    dispatch_table = ""
    if node.body:
        body_lines = node.body.split('\n')
        table_lines = []
        in_table = False
        for bl in body_lines:
            if '|' in bl and ('$ARGUMENTS' in bl or '\\$ARGUMENTS' in bl):
                in_table = True
            if in_table:
                if bl.strip().startswith('|'):
                    table_lines.append(bl)
                elif bl.strip() == '':
                    if table_lines:
                        break
                else:
                    if table_lines:
                        break
        # Include the header row before the $ARGUMENTS row
        if table_lines:
            for i, bl in enumerate(body_lines):
                if bl == table_lines[0]:
                    header_idx = i - 2 if i >= 2 and body_lines[i-1].strip().startswith('|') else i - 1
                    if header_idx >= 0 and body_lines[header_idx].strip().startswith('|'):
                        prefix = []
                        for j in range(header_idx, i):
                            if body_lines[j].strip().startswith('|'):
                                prefix.append(body_lines[j])
                        table_lines = prefix + table_lines
                    break
            dispatch_table = '\n'.join(table_lines)

    if dispatch_table:
        parts.append("## Modes")
        parts.append("")
        parts.append(_strip_relative_md_links(_escape_mdx(dispatch_table)))
        parts.append("")

    # Tabbed metadata (with single-tab fix)
    tab_items = []

    # General tab
    general_rows = []
    if fm.get("name"):
        general_rows.append(f"| Name | `{fm['name']}` |")
    if fm.get("license"):
        general_rows.append(f"| License | {fm['license']} |")
    if isinstance(meta, dict) and meta.get("version"):
        general_rows.append(f"| Version | {meta['version']} |")
    if isinstance(meta, dict) and meta.get("author"):
        general_rows.append(f"| Author | {meta['author']} |")
    if general_rows:
        tab_items.append(("General", "| Field | Value |\n| ----- | ----- |\n" + "\n".join(general_rows)))

    # Claude Code tab
    cc_rows = []
    if fm.get("model"):
        cc_rows.append(f"| Model | `{fm['model']}` |")
    if fm.get("context"):
        cc_rows.append(f"| Context | `{fm['context']}` |")
    if fm.get("agent"):
        cc_rows.append(f"| Agent | `{fm['agent']}` |")
    if fm.get("argument-hint"):
        cc_rows.append(f"| Argument Hint | `{fm['argument-hint']}` |")
    if fm.get("user-invocable") is False:
        cc_rows.append("| User Invocable | No |")
    if fm.get("disable-model-invocation"):
        cc_rows.append("| Disable Model Invocation | Yes |")
    if cc_rows:
        tab_items.append(("Claude Code", "| Field | Value |\n| ----- | ----- |\n" + "\n".join(cc_rows)))

    # Compatibility tab
    compat_rows = []
    if fm.get("compatibility"):
        compat_rows.append(f"| Compatibility | {fm['compatibility']} |")
    if fm.get("allowed-tools"):
        compat_rows.append(f"| Allowed Tools | `{fm['allowed-tools']}` |")
    if compat_rows:
        tab_items.append(("Compatibility", "| Field | Value |\n| ----- | ----- |\n" + "\n".join(compat_rows)))

    if tab_items:
        if len(tab_items) == 1:
            # Single tab — render content directly without Tabs wrapper
            label, content = tab_items[0]
            parts.append(f"### {label}")
            parts.append("")
            parts.append(content)
            parts.append("")
        else:
            parts.append("<Tabs>")
            for label, content in tab_items:
                parts.append(f'  <TabItem label="{label}">')
                parts.append(content)
                parts.append("  </TabItem>")
            parts.append("</Tabs>")
            parts.append("")

    # Cross-links (Used By)
    related_edges = [e for e in edges if e.to_id == f"skill:{node.id}"]
    if related_edges:
        parts.append("## Used By")
        parts.append("")
        parts.append("<CardGrid>")
        for edge in related_edges:
            agent_id = edge.from_id.split(":")[1]
            agent_node = next((n for n in all_nodes if n.kind == "agent" and n.id == agent_id), None)
            if agent_node:
                parts.append(f'  <LinkCard title="{_escape_attr(agent_id)}" href="/agents/{agent_id}/" description="{_escape_attr(_truncate_sentence(agent_node.description, 160))}" />')
        parts.append("</CardGrid>")
        parts.append("")

    # Related Skills
    related = RELATED_SKILLS.get(node.id, [])
    if related:
        parts.append("## Related Skills")
        parts.append("")
        parts.append("<CardGrid>")
        for rel_id in related:
            rel_node = next((n for n in all_nodes if n.kind == "skill" and n.id == rel_id), None)
            if rel_node:
                desc = _escape_attr(_truncate_sentence(rel_node.description, 160))
                parts.append(f'  <LinkCard title="{_escape_attr(rel_id)}" href="/skills/{rel_id}/" description="{desc}" />')
        parts.append("</CardGrid>")
        parts.append("")

    # === TIER 2: Copyable asset preview ===
    # Use wider fence than any fence inside the raw content
    max_fence = 3
    for line in raw_content.split('\n'):
        stripped = line.lstrip()
        if stripped.startswith('```') or stripped.startswith('~~~'):
            fence_len = len(stripped) - len(stripped.lstrip(stripped[0]))
            max_fence = max(max_fence, fence_len)
    outer_fence = '`' * (max_fence + 1)
    parts.append("<details>")
    parts.append("<summary>View Full SKILL.md</summary>")
    parts.append("")
    parts.append(f'{outer_fence}yaml title="SKILL.md"')
    parts.append(raw_content)
    parts.append(outer_fence)
    parts.append("")
    if node.source == "custom":
        parts.append(f"[Download from GitHub](https://raw.githubusercontent.com/wyattowalsh/agents/main/{node.source_path})")
        parts.append("")
    parts.append("</details>")
    parts.append("")

    # === TIER 3: Rendered specification ===
    if node.body:
        parts.append("<details>")
        parts.append("<summary>Rendered Specification</summary>")
        parts.append("")
        parts.append(_strip_relative_md_links(_escape_mdx(_shift_headings(node.body, 1))))
        parts.append("")
        parts.append("</details>")
        parts.append("")

    # Source link (only for custom skills)
    if node.source == "custom":
        parts.append("---")
        parts.append(f"[View source on GitHub]({GITHUB_BASE}/{node.source_path})")
        parts.append("")

    return "\n".join(parts)


def _render_agent_page(node: CatalogNode, edges: list[CatalogEdge], all_nodes: list[CatalogNode]) -> str:
    fm = node.metadata
    parts = []

    # Frontmatter
    parts.append("---")
    parts.append(f"title: \"{node.id}\"")
    parts.append(f"description: \"{_escape_attr(_truncate_sentence(node.description, 200))}\"")
    parts.append("---")
    parts.append("")

    # Imports
    parts.append("import { Badge, Tabs, TabItem, Card, CardGrid, LinkCard, Aside } from '@astrojs/starlight/components';")
    parts.append("")

    # Badge row
    badges = []
    if fm.get("model") and fm["model"] != "inherit":
        badges.append(f'<Badge text="{_escape_attr(fm["model"])}" variant="tip" />')
    if fm.get("permissionMode") and fm["permissionMode"] != "default":
        badges.append(f'<Badge text="{_escape_attr(fm["permissionMode"])}" variant="caution" />')
    if badges:
        parts.append(" ".join(badges))
        parts.append("")

    # Description
    parts.append(f"> {node.description}")
    parts.append("")

    # Tools as pill badges
    if fm.get("tools"):
        parts.append('<div class="tool-pills">')
        pills = ' '.join(f'<Badge text="{_escape_attr(t.strip())}" variant="note" />' for t in fm["tools"].split(','))
        parts.append(pills)
        parts.append('</div>')
        parts.append("")

    # Tabbed config (with single-tab fix)
    tab_items = []

    # Identity tab
    id_rows = [f"| Name | `{fm.get('name', node.id)}` |"]
    if fm.get("model"):
        id_rows.append(f"| Model | `{fm['model']}` |")
    if fm.get("permissionMode"):
        id_rows.append(f"| Permission Mode | `{fm['permissionMode']}` |")
    if fm.get("maxTurns"):
        id_rows.append(f"| Max Turns | {fm['maxTurns']} |")
    if fm.get("memory"):
        id_rows.append(f"| Memory | `{fm['memory']}` |")
    tab_items.append(("Identity", "| Field | Value |\n| ----- | ----- |\n" + "\n".join(id_rows)))

    # Tools tab
    tools_rows = []
    if fm.get("tools"):
        tools_rows.append(f"| Allowed | `{fm['tools']}` |")
    if fm.get("disallowedTools"):
        tools_rows.append(f"| Disallowed | `{fm['disallowedTools']}` |")
    if tools_rows:
        tab_items.append(("Tools", "| Field | Value |\n| ----- | ----- |\n" + "\n".join(tools_rows)))

    # Integrations tab
    int_rows = []
    if fm.get("skills"):
        skills_list = ", ".join(f"`{s}`" for s in fm["skills"])
        int_rows.append(f"| Skills | {skills_list} |")
    if fm.get("mcpServers"):
        mcp_list = ", ".join(f"`{m}`" for m in fm["mcpServers"])
        int_rows.append(f"| MCP Servers | {mcp_list} |")
    if int_rows:
        tab_items.append(("Integrations", "| Field | Value |\n| ----- | ----- |\n" + "\n".join(int_rows)))

    if tab_items:
        if len(tab_items) == 1:
            # Single tab — render content directly without Tabs wrapper
            label, content = tab_items[0]
            parts.append(f"### {label}")
            parts.append("")
            parts.append(content)
            parts.append("")
        else:
            parts.append("<Tabs>")
            for label, content in tab_items:
                parts.append(f'  <TabItem label="{label}">')
                parts.append(content)
                parts.append("  </TabItem>")
            parts.append("</Tabs>")
            parts.append("")

    # Cross-links
    outgoing = [e for e in edges if e.from_id == f"agent:{node.id}"]
    if outgoing:
        skill_edges = [e for e in outgoing if e.relation == "uses-skill"]
        mcp_edges = [e for e in outgoing if e.relation == "uses-mcp"]

        if skill_edges:
            parts.append("## Uses Skills")
            parts.append("")
            parts.append("<CardGrid>")
            for edge in skill_edges:
                skill_id = edge.to_id.split(":")[1]
                skill_node = next((n for n in all_nodes if n.kind == "skill" and n.id == skill_id), None)
                if skill_node:
                    parts.append(f'  <LinkCard title="{_escape_attr(skill_id)}" href="/skills/{skill_id}/" description="{_escape_attr(_truncate_sentence(skill_node.description, 160))}" />')
            parts.append("</CardGrid>")
            parts.append("")

        if mcp_edges:
            parts.append("## Uses MCP Servers")
            parts.append("")
            parts.append("<CardGrid>")
            for edge in mcp_edges:
                mcp_id = edge.to_id.split(":")[1]
                mcp_node = next((n for n in all_nodes if n.kind == "mcp" and n.id == mcp_id), None)
                if mcp_node:
                    parts.append(f'  <LinkCard title="{_escape_attr(mcp_id)}" href="/mcp/{mcp_id}/" description="{_escape_attr(_truncate_sentence(mcp_node.description, 160))}" />')
            parts.append("</CardGrid>")
            parts.append("")

    # Skills as LinkCard grid
    if fm.get("skills") and isinstance(fm["skills"], list):
        parts.append("## Skills")
        parts.append("")
        parts.append("<CardGrid>")
        for skill_name in fm["skills"]:
            skill_node = next((n for n in all_nodes if n.kind == "skill" and n.id == skill_name), None)
            if skill_node:
                parts.append(f'  <LinkCard title="{_escape_attr(skill_name)}" href="/skills/{skill_name}/" description="{_escape_attr(_truncate_sentence(skill_node.description, 160))}" />')
            else:
                parts.append(f'  <LinkCard title="{_escape_attr(skill_name)}" href="/skills/{skill_name}/" />')
        parts.append("</CardGrid>")
        parts.append("")

    # MCP Servers as LinkCard grid
    if fm.get("mcpServers") and isinstance(fm["mcpServers"], list):
        parts.append("## MCP Servers")
        parts.append("")
        parts.append("<CardGrid>")
        for mcp_name in fm["mcpServers"]:
            mcp_node = next((n for n in all_nodes if n.kind == "mcp" and n.id == mcp_name), None)
            if mcp_node:
                parts.append(f'  <LinkCard title="{_escape_attr(mcp_name)}" href="/mcp/{mcp_name}/" description="{_escape_attr(_truncate_sentence(mcp_node.description, 160))}" />')
            else:
                parts.append(f'  <LinkCard title="{_escape_attr(mcp_name)}" href="/mcp/{mcp_name}/" />')
        parts.append("</CardGrid>")
        parts.append("")

    # System prompt body (shift headings)
    if node.body:
        parts.append("## System Prompt")
        parts.append("")
        parts.append(_strip_relative_md_links(_escape_mdx(_shift_headings(node.body, 1))))
        parts.append("")

    # Source link
    parts.append("---")
    parts.append(f"[View source on GitHub]({GITHUB_BASE}/{node.source_path})")
    parts.append("")

    return "\n".join(parts)


def _render_mcp_page(node: CatalogNode, edges: list[CatalogEdge], all_nodes: list[CatalogNode]) -> str:
    fm = node.metadata
    proj = fm.get("project", {})
    parts = []

    # Frontmatter
    parts.append("---")
    parts.append(f"title: \"{node.id}\"")
    desc = node.description or f"MCP server: {node.id}"
    parts.append(f"description: \"{_escape_attr(_truncate_sentence(desc, 200))}\"")
    parts.append("---")
    parts.append("")

    # Imports
    parts.append("import { Badge, Tabs, TabItem, Aside, Code, CardGrid, LinkCard } from '@astrojs/starlight/components';")
    parts.append("")

    # Badges
    parts.append('<Badge text="MCP" variant="note" /> <Badge text="FastMCP" variant="success" />')
    parts.append("")

    # Description
    if node.description:
        parts.append(f"> {node.description}")
        parts.append("")

    # Usage aside
    parts.append('<Aside type="tip" title="Usage">')
    parts.append("Add to your `claude_desktop_config.json`:")
    parts.append("```json")
    mcp_config = {
        "mcpServers": {
            node.id: {
                "command": "uv",
                "args": ["run", "--directory", f"mcp/{node.id}", "python", "server.py"]
            }
        }
    }
    parts.append(json.dumps(mcp_config, indent=2))
    parts.append("```")
    parts.append("</Aside>")
    parts.append("")

    # Tabbed config (with single-tab fix)
    tab_items = []

    # Package info tab
    pkg_rows = []
    if proj.get("name"):
        pkg_rows.append(f"| Name | `{proj['name']}` |")
    if proj.get("version"):
        pkg_rows.append(f"| Version | {proj['version']} |")
    if proj.get("requires-python"):
        pkg_rows.append(f"| Python | `{proj['requires-python']}` |")
    if pkg_rows:
        tab_items.append(("Package", "| Field | Value |\n| ----- | ----- |\n" + "\n".join(pkg_rows)))

    # Dependencies as badges
    deps = proj.get("dependencies", [])
    if deps:
        dep_badges = ' '.join(f'<Badge text="{_escape_attr(d)}" variant="note" />' for d in deps)
        tab_items.append(("Dependencies", dep_badges))

    # FastMCP config tab
    fastmcp_config = fm.get("fastmcp_config", {})
    if fastmcp_config:
        tab_items.append(("FastMCP Config", "```json\n" + json.dumps(fastmcp_config, indent=2) + "\n```"))

    if tab_items:
        if len(tab_items) == 1:
            # Single tab — render content directly without Tabs wrapper
            label, content = tab_items[0]
            parts.append(f"### {label}")
            parts.append("")
            parts.append(content)
            parts.append("")
        else:
            parts.append("<Tabs>")
            for label, content in tab_items:
                parts.append(f'  <TabItem label="{label}">')
                parts.append(content)
                parts.append("  </TabItem>")
            parts.append("</Tabs>")
            parts.append("")

    # Server source
    if node.body:
        parts.append("## Server Source")
        parts.append("")
        parts.append('<div class="server-source">')
        parts.append("")
        parts.append(f"```python title=\"mcp/{node.id}/server.py\"")
        parts.append(node.body)
        parts.append("```")
        parts.append("")
        parts.append("</div>")
        parts.append("")

    # Cross-links (agents that use this MCP)
    related_edges = [e for e in edges if e.to_id == f"mcp:{node.id}"]
    if related_edges:
        parts.append("## Used By")
        parts.append("")
        parts.append("<CardGrid>")
        for edge in related_edges:
            agent_id = edge.from_id.split(":")[1]
            agent_node = next((n for n in all_nodes if n.kind == "agent" and n.id == agent_id), None)
            if agent_node:
                parts.append(f'  <LinkCard title="{_escape_attr(agent_id)}" href="/agents/{agent_id}/" description="{_escape_attr(_truncate_sentence(agent_node.description, 160))}" />')
        parts.append("</CardGrid>")
        parts.append("")

    # Source link
    parts.append("---")
    parts.append(f"[View source on GitHub]({GITHUB_BASE}/{node.source_path})")
    parts.append("")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Index and CLI pages
# ---------------------------------------------------------------------------


def _write_index_page(nodes: list[CatalogNode]) -> None:
    """Write the index.mdx splash page."""
    skills = [n for n in nodes if n.kind == "skill"]
    agents = [n for n in nodes if n.kind == "agent"]
    mcps = [n for n in nodes if n.kind == "mcp"]

    parts = []
    parts.append("---")
    parts.append("title: Agents")
    parts.append("description: AI agent skills, tools, and MCP servers for Claude Code, Gemini CLI, Codex, Cursor, and more")
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
    parts.append('        </div>')
    parts.append('        <div class="hero-terminal-body">')
    parts.append('          <span class="hero-terminal-prompt">$</span>')
    parts.append('          <span class="hero-terminal-cmd">npx skills add wyattowalsh/agents --all -g</span>')
    parts.append('          <span class="hero-terminal-cursor">▋</span>')
    parts.append('        </div>')
    parts.append('        <div class="hero-agents-row">')
    parts.append('          <span class="hero-agent-badge">Claude</span>')
    parts.append('          <span class="hero-agent-badge">Gemini</span>')
    parts.append('          <span class="hero-agent-badge">Codex</span>')
    parts.append('          <span class="hero-agent-badge">Cursor</span>')
    parts.append('          <span class="hero-agent-badge">Copilot</span>')
    parts.append('        </div>')
    parts.append('      </div>')
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
        parts.append('</div>')
        parts.append("")

    # What Can You Do section — use-case framing
    parts.append("## What Can You Do?")
    parts.append("")
    parts.append("<CardGrid>")
    parts.append('  <LinkCard title="Enhance Code Reviews" href="/skills/honest-review/" description="Research-driven code review at multiple abstraction levels with AI code smell detection and severity calibration." />')
    parts.append('  <LinkCard title="Strategic Decision Analysis" href="/skills/wargame/" description="Domain-agnostic wargaming with Monte Carlo exploration, structured adjudication, and visual dashboards." />')
    parts.append('  <LinkCard title="Host Expert Panels" href="/skills/host-panel/" description="Simulated panel discussions among AI experts in roundtable, Oxford-style, and Socratic formats." />')
    parts.append('  <LinkCard title="Create MCP Servers" href="/skills/mcp-creator/" description="Build production-ready MCP servers using FastMCP v3 with tool design, testing, and deployment guidance." />')
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
            desc = _escape_attr(_truncate_sentence(n.description, 160))
            parts.append(f'  <LinkCard title="{_escape_attr(n.id)}" href="/skills/{n.id}/" description="{desc}" />')
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
            desc = _escape_attr(_truncate_sentence(n.description, 160))
            parts.append(f'  <LinkCard title="{_escape_attr(n.id)}" href="/agents/{n.id}/" description="{desc}" />')
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
            desc = _escape_attr(_truncate_sentence(n.description, 160))
            parts.append(f'  <LinkCard title="{_escape_attr(n.id)}" href="/mcp/{n.id}/" description="{desc}" />')
        parts.append("</CardGrid>")
        parts.append("</div>")
        parts.append("")

    content_dir = ROOT / "docs" / "src" / "content" / "docs"
    content_dir.mkdir(parents=True, exist_ok=True)
    (content_dir / "index.mdx").write_text("\n".join(parts))


def _write_cli_page() -> None:
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


def _write_skills_index(nodes: list[CatalogNode]) -> None:
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
    parts.append("> Reusable knowledge and workflows that extend AI agent capabilities across Claude Code, Gemini CLI, Codex, Cursor, and more.")
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
            desc = _escape_attr(_truncate_sentence(n.description, 160))
            parts.append(f'  <LinkCard title="{_escape_attr(n.id)}" href="/skills/{n.id}/" description="{desc}" />')
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
            desc = _escape_attr(_truncate_sentence(n.description, 160))
            parts.append(f'  <LinkCard title="{_escape_attr(n.id)}" href="/skills/installed/#{n.id}" description="{desc}" />')
        parts.append("</CardGrid>")
        parts.append("</div>")
        parts.append("")

    out_dir = CONTENT_DIR / "skills"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.mdx").write_text("\n".join(parts))


def _write_installed_skills_page(nodes: list[CatalogNode]) -> None:
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
        badges = [f'<Badge text="{_escape_attr(n.id)}" variant="note" />']
        word_count = len(n.body.split()) if n.body else 0
        badges.append(f'<Badge text="{word_count} words" variant="default" />')
        if fm.get("license"):
            badges.append(f'<Badge text="{_escape_attr(fm["license"])}" variant="success" />')
        if meta.get("version"):
            badges.append(f'<Badge text="v{_escape_attr(str(meta["version"]))}" variant="success" />')
        if meta.get("author"):
            badges.append(f'<Badge text="{_escape_attr(meta["author"])}" variant="caution" />')
        if fm.get("model"):
            badges.append(f'<Badge text="{_escape_attr(fm["model"])}" variant="tip" />')
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
        raw_content = _read_raw_content(n)
        max_fence = 3
        for line in raw_content.split('\n'):
            stripped = line.lstrip()
            if stripped.startswith('```') or stripped.startswith('~~~'):
                fence_len = len(stripped) - len(stripped.lstrip(stripped[0]))
                max_fence = max(max_fence, fence_len)
        outer_fence = '`' * (max_fence + 1)
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


def _write_agents_index(nodes: list[CatalogNode]) -> None:
    """Write agents/index.mdx category page."""
    parts = []
    parts.append("---")
    parts.append("title: Agents")
    parts.append("description: Browse all available AI agent configurations")
    parts.append("---")
    parts.append("")
    parts.append("import { Card, CardGrid, LinkCard, Badge } from '@astrojs/starlight/components';")
    parts.append("")
    parts.append("> Specialized agent configurations with tools, permissions, and system prompts for various AI coding assistants.")
    parts.append("")
    parts.append('<div class="stats-bar">')
    parts.append(f'  <span class="stat stat-agent">{len(nodes)} agents available</span>')
    parts.append('</div>')
    parts.append("")
    parts.append("## All Agents")
    parts.append("")
    parts.append('<div class="catalog-agent">')
    parts.append("<CardGrid>")
    for n in nodes:
        desc = _escape_attr(_truncate_sentence(n.description, 160))
        parts.append(f'  <LinkCard title="{_escape_attr(n.id)}" href="/agents/{n.id}/" description="{desc}" />')
    parts.append("</CardGrid>")
    parts.append("</div>")
    parts.append("")

    out_dir = CONTENT_DIR / "agents"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.mdx").write_text("\n".join(parts))


def _write_mcp_index(nodes: list[CatalogNode]) -> None:
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
    parts.append('</div>')
    parts.append("")
    parts.append("## All MCP Servers")
    parts.append("")
    parts.append('<div class="catalog-mcp">')
    parts.append("<CardGrid>")
    for n in nodes:
        desc = _escape_attr(_truncate_sentence(n.description, 160))
        parts.append(f'  <LinkCard title="{_escape_attr(n.id)}" href="/mcp/{n.id}/" description="{desc}" />')
    parts.append("</CardGrid>")
    parts.append("</div>")
    parts.append("")

    out_dir = CONTENT_DIR / "mcp"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.mdx").write_text("\n".join(parts))


def _write_sidebar(nodes: list[CatalogNode]) -> None:
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
            lines.append(f"    label: 'Guides',")
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


def _regenerate_sidebar_and_indexes() -> None:
    """Regenerate sidebar and index pages from current nodes."""
    nodes = _collect_nodes()
    # Also collect installed if content dir exists
    if CONTENT_DIR.exists():
        existing_ids = {n.id for n in nodes if n.kind == "skill"}
        installed = _collect_installed_skills(existing_ids)
        nodes.extend(installed)

    skills = [n for n in nodes if n.kind == "skill"]
    agents_list = [n for n in nodes if n.kind == "agent"]
    mcps = [n for n in nodes if n.kind == "mcp"]

    _write_sidebar(nodes)
    _write_skills_index(skills)
    installed_skills = [n for n in skills if n.source != "custom"]
    if installed_skills:
        _write_installed_skills_page(installed_skills)
    if agents_list:
        _write_agents_index(agents_list)
    if mcps:
        _write_mcp_index(mcps)
    _write_index_page(nodes)


# ---------------------------------------------------------------------------
# docs subcommand group
# ---------------------------------------------------------------------------

docs_app = typer.Typer(help="Documentation site management")
app.add_typer(docs_app, name="docs")

DOCS_DIR = ROOT / "docs"
CONTENT_DIR = DOCS_DIR / "src" / "content" / "docs"


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
    include_installed: bool = typer.Option(True, "--include-installed/--no-installed", help="Include installed skills from ~/.claude/skills/"),
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

    nodes = _collect_nodes()

    # Collect installed skills
    if include_installed:
        existing_ids = {n.id for n in nodes if n.kind == "skill"}
        installed = _collect_installed_skills(existing_ids)
        nodes.extend(installed)
        if installed:
            typer.echo(f"  Found {len(installed)} installed skills")

    # Filter drafts
    if not include_drafts:
        nodes = [n for n in nodes if not (n.kind == "skill" and n.description.strip().upper().startswith("TODO"))]

    edges = _collect_edges(nodes)

    # Write individual pages (skip installed skills — they go on a single aggregated page)
    for node in nodes:
        if node.kind == "skill" and node.source != "custom":
            continue  # installed skills aggregated on skills/installed.mdx
        page_content = _render_page(node, edges, nodes)
        page_dir = CONTENT_DIR / (node.kind + "s" if node.kind != "mcp" else "mcp")
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / f"{node.id}.mdx").write_text(page_content)
        typer.echo(f"  Generated {node.kind}s/{node.id}.mdx" if node.kind != "mcp" else f"  Generated mcp/{node.id}.mdx")

    # Write category index pages
    skills = [n for n in nodes if n.kind == "skill"]
    agents = [n for n in nodes if n.kind == "agent"]
    mcps = [n for n in nodes if n.kind == "mcp"]

    _write_skills_index(skills)
    typer.echo("  Generated skills/index.mdx")
    installed_skills = [n for n in skills if n.source != "custom"]
    if installed_skills:
        _write_installed_skills_page(installed_skills)
        typer.echo("  Generated skills/installed.mdx")
    if agents:
        _write_agents_index(agents)
        typer.echo("  Generated agents/index.mdx")
    if mcps:
        _write_mcp_index(mcps)
        typer.echo("  Generated mcp/index.mdx")

    # Write main index and CLI pages
    _write_index_page(nodes)
    typer.echo("  Generated index.mdx")
    _write_cli_page()
    typer.echo("  Generated cli.mdx")

    # Generate sidebar
    _write_sidebar(nodes)
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


if __name__ == "__main__":
    app()
