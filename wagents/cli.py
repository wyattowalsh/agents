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


def _validate_name(name: str) -> None:
    """Validate asset name is kebab-case and within length limit."""
    if not KEBAB_CASE_PATTERN.match(name):
        typer.echo(f"Error: name must be kebab-case (got '{name}')", err=True)
        raise typer.Exit(code=1)
    if len(name) > 64:
        typer.echo("Error: name exceeds 64 characters", err=True)
        raise typer.Exit(code=1)


@new_app.command("skill")
def new_skill(name: str):
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


@new_app.command("agent")
def new_agent(name: str):
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


@new_app.command("mcp")
def new_mcp(name: str):
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
    source_path: str   # relative path from repo root


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
    fence_char = None
    fence_count = 0

    for line in lines:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if indent <= 3:
            if stripped.startswith('```') or stripped.startswith('~~~'):
                char = stripped[0]
                count = len(stripped) - len(stripped.lstrip(char))

                if fence_char is None:
                    fence_char = char
                    fence_count = count
                    result.append(line)
                    continue
                elif char == fence_char and count >= fence_count:
                    fence_char = None
                    fence_count = 0
                    result.append(line)
                    continue

        if fence_char is not None:
            result.append(line)
            continue

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


def _render_page(node: CatalogNode, edges: list[CatalogEdge], all_nodes: list[CatalogNode]) -> str:
    """Render a CatalogNode to MDX string."""
    if node.kind == "skill":
        return _render_skill_page(node, edges, all_nodes)
    elif node.kind == "agent":
        return _render_agent_page(node, edges, all_nodes)
    elif node.kind == "mcp":
        return _render_mcp_page(node, edges, all_nodes)
    return ""


def _render_skill_page(node: CatalogNode, edges: list[CatalogEdge], all_nodes: list[CatalogNode]) -> str:
    fm = node.metadata
    parts = []

    # Frontmatter
    parts.append("---")
    parts.append(f"title: \"{node.id}\"")
    parts.append(f"description: \"{node.description[:200].replace(chr(34), chr(39))}\"")
    parts.append("---")
    parts.append("")

    # Imports
    parts.append("import { Badge, Tabs, TabItem, Card, CardGrid, LinkCard, Aside, Steps } from '@astrojs/starlight/components';")
    parts.append("")

    # Badge row — only fields that have values
    badges = []
    if fm.get("license"):
        badges.append(f'<Badge text="{fm["license"]}" variant="note" />')
    meta = fm.get("metadata", {})
    if isinstance(meta, dict):
        if meta.get("version"):
            badges.append(f'<Badge text="v{meta["version"]}" variant="success" />')
        if meta.get("author"):
            badges.append(f'<Badge text="{meta["author"]}" variant="caution" />')
    if fm.get("model"):
        badges.append(f'<Badge text="{fm["model"]}" variant="tip" />')
    if badges:
        parts.append(" ".join(badges))
        parts.append("")

    # Description
    parts.append(f"> {node.description}")
    parts.append("")

    # Install
    parts.append("<Aside type=\"tip\" title=\"Install\">")
    parts.append("```bash")
    parts.append(f"npx skills add wyattowalsh/agents/skills/{node.id} -g")
    parts.append("```")
    parts.append("</Aside>")
    parts.append("")

    # Tabbed metadata
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
        parts.append("<Tabs>")
        for label, content in tab_items:
            parts.append(f'  <TabItem label="{label}">')
            parts.append(content)
            parts.append("  </TabItem>")
        parts.append("</Tabs>")
        parts.append("")

    # Cross-links
    related_edges = [e for e in edges if e.to_id == f"skill:{node.id}"]
    if related_edges:
        parts.append("## Used By")
        parts.append("")
        parts.append("<CardGrid>")
        for edge in related_edges:
            agent_id = edge.from_id.split(":")[1]
            agent_node = next((n for n in all_nodes if n.kind == "agent" and n.id == agent_id), None)
            if agent_node:
                parts.append(f'  <LinkCard title="{agent_id}" href="/agents/{agent_id}/" description="{agent_node.description[:100]}" />')
        parts.append("</CardGrid>")
        parts.append("")

    # Body
    if node.body:
        parts.append("## Details")
        parts.append("")
        parts.append(_escape_mdx(node.body))
        parts.append("")

    # Source link
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
    parts.append(f"description: \"{node.description[:200].replace(chr(34), chr(39))}\"")
    parts.append("---")
    parts.append("")

    # Imports
    parts.append("import { Badge, Tabs, TabItem, Card, CardGrid, LinkCard, Aside } from '@astrojs/starlight/components';")
    parts.append("")

    # Badge row
    badges = []
    if fm.get("model") and fm["model"] != "inherit":
        badges.append(f'<Badge text="{fm["model"]}" variant="tip" />')
    if fm.get("permissionMode") and fm["permissionMode"] != "default":
        badges.append(f'<Badge text="{fm["permissionMode"]}" variant="caution" />')
    if badges:
        parts.append(" ".join(badges))
        parts.append("")

    # Description
    parts.append(f"> {node.description}")
    parts.append("")

    # Tabbed config
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
                desc = skill_node.description[:100] if skill_node else ""
                parts.append(f'  <LinkCard title="{skill_id}" href="/skills/{skill_id}/" description="{desc}" />')
            parts.append("</CardGrid>")
            parts.append("")

        if mcp_edges:
            parts.append("## Uses MCP Servers")
            parts.append("")
            parts.append("<CardGrid>")
            for edge in mcp_edges:
                mcp_id = edge.to_id.split(":")[1]
                mcp_node = next((n for n in all_nodes if n.kind == "mcp" and n.id == mcp_id), None)
                desc = mcp_node.description[:100] if mcp_node else ""
                parts.append(f'  <LinkCard title="{mcp_id}" href="/mcp/{mcp_id}/" description="{desc}" />')
            parts.append("</CardGrid>")
            parts.append("")

    # System prompt body
    if node.body:
        parts.append("## System Prompt")
        parts.append("")
        parts.append(_escape_mdx(node.body))
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
    parts.append(f"description: \"{desc[:200].replace(chr(34), chr(39))}\"")
    parts.append("---")
    parts.append("")

    # Imports
    parts.append("import { Badge, Tabs, TabItem, Aside, Code } from '@astrojs/starlight/components';")
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

    # Tabbed config
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

    # Dependencies tab
    deps = proj.get("dependencies", [])
    if deps:
        dep_lines = "\n".join(f"- `{d}`" for d in deps)
        tab_items.append(("Dependencies", dep_lines))

    # FastMCP config tab
    fastmcp_config = fm.get("fastmcp_config", {})
    if fastmcp_config:
        tab_items.append(("FastMCP Config", "```json\n" + json.dumps(fastmcp_config, indent=2) + "\n```"))

    if tab_items:
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
        parts.append(f"```python title=\"mcp/{node.id}/server.py\"")
        parts.append(node.body)
        parts.append("```")
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
                parts.append(f'  <LinkCard title="{agent_id}" href="/agents/{agent_id}/" description="{agent_node.description[:100]}" />')
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
    parts = []
    parts.append("---")
    parts.append("title: agents")
    parts.append("description: AI agent artifacts, configs, skills, tools, and more")
    parts.append("template: splash")
    parts.append("hero:")
    parts.append("  tagline: Browse, discover, and install AI agent skills, agents, and MCP servers")
    parts.append("  actions:")

    # Link to first skill if one exists
    skills = [n for n in nodes if n.kind == "skill"]
    if skills:
        parts.append("    - text: Browse Skills")
        parts.append(f"      link: /skills/{skills[0].id}/")
        parts.append("      icon: right-arrow")

    parts.append("    - text: GitHub")
    parts.append("      link: https://github.com/wyattowalsh/agents")
    parts.append("      variant: minimal")
    parts.append("      icon: external")
    parts.append("---")
    parts.append("")
    parts.append("import { Card, CardGrid, LinkCard } from '@astrojs/starlight/components';")
    parts.append("")
    parts.append("## Install")
    parts.append("")
    parts.append("```bash")
    parts.append("npx skills add wyattowalsh/agents --all -g")
    parts.append("```")
    parts.append("")

    # Skills section
    if skills:
        parts.append("## Skills")
        parts.append("")
        parts.append('<div class="catalog-skill">')
        parts.append("<CardGrid>")
        for n in skills:
            desc = n.description[:120].replace('"', "'")
            parts.append(f'  <LinkCard title="{n.id}" href="/skills/{n.id}/" description="{desc}" />')
        parts.append("</CardGrid>")
        parts.append("</div>")
        parts.append("")

    # Agents section
    agents = [n for n in nodes if n.kind == "agent"]
    if agents:
        parts.append("## Agents")
        parts.append("")
        parts.append('<div class="catalog-agent">')
        parts.append("<CardGrid>")
        for n in agents:
            desc = n.description[:120].replace('"', "'")
            parts.append(f'  <LinkCard title="{n.id}" href="/agents/{n.id}/" description="{desc}" />')
        parts.append("</CardGrid>")
        parts.append("</div>")
        parts.append("")

    # MCP section
    mcps = [n for n in nodes if n.kind == "mcp"]
    if mcps:
        parts.append("## MCP Servers")
        parts.append("")
        parts.append('<div class="catalog-mcp">')
        parts.append("<CardGrid>")
        for n in mcps:
            desc = n.description[:120].replace('"', "'")
            parts.append(f'  <LinkCard title="{n.id}" href="/mcp/{n.id}/" description="{desc}" />')
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
def docs_generate():
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

    nodes = _collect_nodes()
    edges = _collect_edges(nodes)

    # Write individual pages
    for node in nodes:
        page_content = _render_page(node, edges, nodes)
        page_dir = CONTENT_DIR / (node.kind + "s" if node.kind != "mcp" else "mcp")
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / f"{node.id}.mdx").write_text(page_content)
        typer.echo(f"  Generated {node.kind}s/{node.id}.mdx" if node.kind != "mcp" else f"  Generated mcp/{node.id}.mdx")

    # Write index and CLI pages
    _write_index_page(nodes)
    typer.echo("  Generated index.mdx")
    _write_cli_page()
    typer.echo("  Generated cli.mdx")

    typer.echo(f"Generated {len(nodes)} pages + index + cli")


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
    """Remove generated content pages."""
    if CONTENT_DIR.exists():
        shutil.rmtree(CONTENT_DIR)
        CONTENT_DIR.mkdir(parents=True)
        typer.echo("Cleaned generated content pages")
    else:
        typer.echo("Nothing to clean")


if __name__ == "__main__":
    app()
