"""CLI for managing centralized AI agent assets."""

import importlib.metadata
import json
import re
import tomllib
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


if __name__ == "__main__":
    app()
