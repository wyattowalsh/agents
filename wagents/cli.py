"""CLI for managing centralized AI agent assets."""

import json
import tomllib
from pathlib import Path
from typing import Annotated

import typer

from wagents import KEBAB_CASE_PATTERN, ROOT, VERSION
from wagents.catalog import RELATED_SKILLS, CatalogNode
from wagents.docs import docs_app, regenerate_sidebar_and_indexes
from wagents.parsing import parse_frontmatter, to_title
from wagents.rendering import scaffold_doc_page

# Typer apps
app = typer.Typer(help="CLI for managing centralized AI agent assets")
new_app = typer.Typer(help="Create new assets from reference templates")
app.add_typer(new_app, name="new")
app.add_typer(docs_app, name="docs")
hooks_app = typer.Typer(help="Manage hooks across skills and agents")
app.add_typer(hooks_app, name="hooks")
eval_app = typer.Typer(help="Manage and validate skill evals")
app.add_typer(eval_app, name="eval")


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        typer.echo(f"wagents {VERSION}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(None, "--version", callback=version_callback, help="Show version and exit"),
):
    """CLI for managing centralized AI agent assets."""
    pass


def validate_name(name: str) -> None:
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
    validate_name(name)
    skill_dir = ROOT / "skills" / name
    skill_file = skill_dir / "SKILL.md"

    if skill_file.exists():
        typer.echo(f"Error: {skill_file} already exists", err=True)
        raise typer.Exit(code=1)

    skill_dir.mkdir(parents=True, exist_ok=True)

    title = to_title(name)
    content = f"""---
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
"""

    skill_file.write_text(content)
    typer.echo(f"Created skills/{name}/SKILL.md")

    if not no_docs:
        fm, body = parse_frontmatter(content)
        node = CatalogNode(
            kind="skill",
            id=name,
            title=to_title(name),
            description=str(fm.get("description", "")),
            metadata=fm,
            body=body,
            source_path=f"skills/{name}/SKILL.md",
        )
        scaffold_doc_page(node)
        regenerate_sidebar_and_indexes()
        typer.echo("Regenerated sidebar and index pages")


@new_app.command("agent")
def new_agent(
    name: str,
    no_docs: bool = typer.Option(False, "--no-docs", help="Skip docs page scaffold"),
):
    """Create a new agent from template."""
    validate_name(name)
    agents_dir = ROOT / "agents"
    agent_file = agents_dir / f"{name}.md"

    if agent_file.exists():
        typer.echo(f"Error: {agent_file} already exists", err=True)
        raise typer.Exit(code=1)

    agents_dir.mkdir(parents=True, exist_ok=True)

    title = to_title(name)
    content = f"""---
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
"""

    agent_file.write_text(content)
    typer.echo(f"Created agents/{name}.md")

    if not no_docs:
        fm, body = parse_frontmatter(content)
        node = CatalogNode(
            kind="agent",
            id=name,
            title=to_title(name),
            description=str(fm.get("description", "")),
            metadata=fm,
            body=body,
            source_path=f"agents/{name}.md",
        )
        scaffold_doc_page(node)
        regenerate_sidebar_and_indexes()
        typer.echo("Regenerated sidebar and index pages")


@new_app.command("mcp")
def new_mcp(
    name: str,
    no_docs: bool = typer.Option(False, "--no-docs", help="Skip docs page scaffold"),
):
    """Create a new MCP server from template."""
    validate_name(name)
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
    pyproject_content = f"""[project]
name = "mcp-{name}"
version = "0.1.0"
description = "TODO — What this MCP server does"
requires-python = ">=3.13"
dependencies = ["fastmcp>=2"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
    (mcp_dir / "pyproject.toml").write_text(pyproject_content)

    # Create fastmcp.json
    fastmcp_config = {
        "$schema": "https://gofastmcp.com/public/schemas/fastmcp.json/v1.json",
        "source": {"path": "server.py", "entrypoint": "mcp"},
        "environment": {"type": "uv"},
    }
    (mcp_dir / "fastmcp.json").write_text(json.dumps(fastmcp_config, indent=2) + "\n")

    # Update root pyproject.toml if needed
    root_pyproject = ROOT / "pyproject.toml"
    content = root_pyproject.read_text()

    if "[tool.uv.workspace]" not in content:
        if not content.endswith("\n"):
            content += "\n"
        content += '\n[tool.uv.workspace]\nmembers = ["mcp/*"]\n'
        root_pyproject.write_text(content)

    typer.echo(f"Created mcp/{name}/ with server.py, pyproject.toml, and fastmcp.json")

    if not no_docs:
        metadata = {
            "project": {
                "name": f"mcp-{name}",
                "version": "0.1.0",
                "description": "TODO — What this MCP server does",
                "requires-python": ">=3.13",
                "dependencies": ["fastmcp>=2"],
            },
            "fastmcp_config": fastmcp_config,
        }
        node = CatalogNode(
            kind="mcp",
            id=name,
            title=to_title(name),
            description="TODO — What this MCP server does",
            metadata=metadata,
            body=server_content,
            source_path=f"mcp/{name}/server.py",
        )
        scaffold_doc_page(node)
        regenerate_sidebar_and_indexes()
        typer.echo("Regenerated sidebar and index pages")


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

    # Validate MCP servers
    mcp_dir = ROOT / "mcp"
    if mcp_dir.exists():
        for mcp_subdir in mcp_dir.iterdir():
            if not mcp_subdir.is_dir():
                continue
            dir_name = mcp_subdir.name
            if not KEBAB_CASE_PATTERN.match(dir_name):
                errors.append(f"mcp/{dir_name}: directory name must be kebab-case")
            server_py = mcp_subdir / "server.py"
            if not server_py.exists():
                errors.append(f"mcp/{dir_name}: missing server.py")
            else:
                server_text = server_py.read_text()
                if "FastMCP" not in server_text:
                    errors.append(f"mcp/{dir_name}: server.py does not reference FastMCP")
            pyproject = mcp_subdir / "pyproject.toml"
            if not pyproject.exists():
                errors.append(f"mcp/{dir_name}: missing pyproject.toml")
            else:
                pyproject_text = pyproject.read_text()
                if "fastmcp" not in pyproject_text:
                    errors.append(f"mcp/{dir_name}: pyproject.toml missing fastmcp dependency")
            fastmcp_json = mcp_subdir / "fastmcp.json"
            if not fastmcp_json.exists():
                errors.append(f"mcp/{dir_name}: missing fastmcp.json")

    # Validate RELATED_SKILLS references
    for key, values in RELATED_SKILLS.items():
        if not (ROOT / "skills" / key).is_dir():
            errors.append(f"RELATED_SKILLS: key '{key}' does not match a skill directory")
        for val in values:
            if not (ROOT / "skills" / val).is_dir():
                errors.append(f"RELATED_SKILLS: value '{val}' (in '{key}') does not match a skill directory")

    # Validate hooks
    from wagents.parsing import KNOWN_HOOK_EVENTS

    def _check_hooks(source: str, hooks_dict: dict) -> None:
        if not isinstance(hooks_dict, dict):
            errors.append(f"{source}: hooks must be a mapping")
            return
        for event in hooks_dict:
            if event not in KNOWN_HOOK_EVENTS:
                errors.append(f"{source}: unknown hook event '{event}'")

    for settings_name in ["settings.json", "settings.local.json"]:
        settings_file = ROOT / ".claude" / settings_name
        if settings_file.exists():
            try:
                data = json.loads(settings_file.read_text())
                hooks_dict = data.get("hooks", {})
                if hooks_dict:
                    _check_hooks(settings_name, hooks_dict)
            except json.JSONDecodeError as e:
                errors.append(f"{settings_name}: invalid JSON: {e}")

    # Skills hooks — check events from already-parsed frontmatter
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            try:
                content = skill_file.read_text()
                fm, _ = parse_frontmatter(content)
                hooks_dict = fm.get("hooks", {})
                if hooks_dict:
                    _check_hooks(f"skill:{skill_dir.name}", hooks_dict)
            except Exception:
                pass

    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            try:
                content = agent_file.read_text()
                fm, _ = parse_frontmatter(content)
                hooks_dict = fm.get("hooks", {})
                if hooks_dict:
                    _check_hooks(f"agent:{agent_file.stem}", hooks_dict)
            except Exception:
                pass

    if errors:
        for error in errors:
            typer.echo(error, err=True)
        raise typer.Exit(code=1)
    else:
        typer.echo("All validations passed")


SUPPORTED_AGENTS = [
    "antigravity",
    "claude-code",
    "codex",
    "crush",
    "cursor",
    "gemini-cli",
    "github-copilot",
    "opencode",
]

REPO_SOURCE = "wyattowalsh/agents"


@app.command()
def install(
    skills: Annotated[list[str] | None, typer.Argument(help="Skill name(s) to install (omit for all)")] = None,
    agent: Annotated[list[str] | None, typer.Option("-a", "--agent", help="Target agent(s), repeatable")] = None,
    global_: bool = typer.Option(True, "-g", "--global/--local", help="Install globally vs project-local"),
    list_: bool = typer.Option(False, "--list", help="List available skills without installing"),
    copy: bool = typer.Option(False, "--copy", help="Copy files instead of symlinking"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation prompts"),
):
    """Install skills into agent platforms via npx skills."""
    import shutil
    import subprocess

    if not shutil.which("npx"):
        typer.echo("Error: npx not found. Install Node.js first.", err=True)
        raise typer.Exit(code=1)

    cmd = ["npx", "-y", "skills", "add", REPO_SOURCE]

    if list_:
        cmd.append("--list")
    else:
        # Skills
        if skills:
            for s in skills:
                cmd.extend(["--skill", s])
        else:
            cmd.extend(["--skill", "*"])

        # Agents
        if agent:
            for a in agent:
                if a not in SUPPORTED_AGENTS:
                    typer.echo(
                        f"Error: unknown agent '{a}'. Supported: {', '.join(SUPPORTED_AGENTS)}",
                        err=True,
                    )
                    raise typer.Exit(code=1)
                cmd.extend(["-a", a])
        else:
            cmd.extend(["--agent", "*"])

        # Flags
        if global_:
            cmd.append("-g")
        if copy:
            cmd.append("--copy")
        if yes:
            cmd.append("-y")

    result = subprocess.run(cmd, capture_output=False)
    raise typer.Exit(code=result.returncode)


@app.command()
def package(
    name: str = typer.Argument("", help="Skill name (omit for --all)"),
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output directory")] = None,
    dry_run: bool = typer.Option(False, "--dry-run", help="Check portability without creating ZIPs"),
    all_skills: bool = typer.Option(False, "--all", help="Package all skills"),
    format_: str = typer.Option("table", "--format", help="Output format: json or table"),
):
    """Package skills into portable ZIP files."""
    import subprocess

    script = ROOT / "skills" / "skill-creator" / "scripts" / "package.py"
    cmd = ["uv", "run", "python", str(script)]

    if all_skills:
        cmd.append("--all")
    elif name:
        skill_dir = ROOT / "skills" / name
        cmd.append(str(skill_dir))
    else:
        typer.echo("Error: provide a skill name or use --all", err=True)
        raise typer.Exit(code=1)

    if output:
        cmd.extend(["--output", str(output)])
    if dry_run:
        cmd.append("--dry-run")
    cmd.extend(["--format", format_])

    result = subprocess.run(cmd, capture_output=False)
    raise typer.Exit(code=result.returncode)


@app.command()
def readme(
    check: bool = typer.Option(False, "--check", help="Check if README is up to date"),
):
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
        "",
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
            content_parts.extend(["## Skills", "", "| Name | Description |", "| ---- | ----------- |"])
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
            content_parts.extend(["## Agents", "", "| Name | Description |", "| ---- | ----------- |"])
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
            content_parts.extend(
                [
                    "## MCP Servers",
                    "",
                    "| Name | Description |",
                    "| ---- | ----------- |",
                ]
            )
            for name, desc in mcps:
                content_parts.append(f"| {name} | {desc} |")
            content_parts.append("")

    # Dev commands
    content_parts.extend(
        [
            "## Development",
            "",
            "| Command | Description |",
            "| ------- | ----------- |",
            "| `wagents new skill <name>` | Create a new skill |",
            "| `wagents new agent <name>` | Create a new agent |",
            "| `wagents new mcp <name>` | Create a new MCP server |",
            "| `wagents validate` | Validate all skills and agents |",
            "| `wagents readme` | Regenerate this README |",
            "| `wagents package <name>` | Package a skill into portable ZIP |",
            "| `wagents package --all` | Package all skills |",
            "| `wagents install` | Install all skills to all agents |",
            "| `wagents install -a <agent>` | Install all skills to specific agent |",
            "| `wagents install <name>` | Install specific skill to all agents |",
            "| `wagents docs init` | One-time setup: install docs dependencies |",
            "| `wagents docs generate` | Generate MDX content pages from assets |",
            "| `wagents docs dev` | Generate + launch dev server |",
            "| `wagents docs build` | Generate + production build |",
            "| `wagents docs preview` | Generate + build + preview server |",
            "| `wagents docs clean` | Remove generated content pages |",
            "",
        ]
    )

    # Supported agents
    content_parts.extend(
        [
            "## Supported Agents",
            "",
            "Claude Code, Codex, Gemini CLI, and other agentskills.io-compatible agents.",
            "",
        ]
    )

    # License
    content_parts.extend(["## License", "", "[MIT](LICENSE)", ""])

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
# wagents hooks list / validate
# ---------------------------------------------------------------------------


@hooks_app.command("list")
def hooks_list():
    """List all hooks across skills, agents, and settings."""
    from wagents.parsing import Hook, extract_hooks

    all_hooks: list[Hook] = []

    # 1. Scan .claude/settings.json and .claude/settings.local.json
    for settings_name in ["settings.json", "settings.local.json"]:
        settings_file = ROOT / ".claude" / settings_name
        if settings_file.exists():
            try:
                data = json.loads(settings_file.read_text())
                hooks_dict = data.get("hooks", {})
                all_hooks.extend(extract_hooks(settings_name, hooks_dict))
            except Exception as e:
                typer.echo(
                    f"Warning: could not parse {settings_name}: {e}",
                    err=True,
                )

    # 2. Scan skills
    skills_dir = ROOT / "skills"
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            try:
                fm, _ = parse_frontmatter(skill_file.read_text())
                hooks_dict = fm.get("hooks", {})
                if hooks_dict:
                    all_hooks.extend(extract_hooks(f"skill:{skill_dir.name}", hooks_dict))
            except Exception:
                pass

    # 3. Scan agents
    agents_dir = ROOT / "agents"
    if agents_dir.exists():
        for agent_file in sorted(agents_dir.glob("*.md")):
            try:
                fm, _ = parse_frontmatter(agent_file.read_text())
                hooks_dict = fm.get("hooks", {})
                if hooks_dict:
                    all_hooks.extend(extract_hooks(f"agent:{agent_file.stem}", hooks_dict))
            except Exception:
                pass

    if not all_hooks:
        typer.echo("No hooks found.")
        return

    # Print table
    typer.echo(f"{'Source':<30} {'Event':<20} {'Matcher':<15} {'Type':<10} {'Command/Prompt'}")
    typer.echo("-" * 100)
    for h in all_hooks:
        value = h.command if h.handler_type == "command" else h.prompt
        # Truncate long values
        if len(value) > 50:
            value = value[:47] + "..."
        typer.echo(f"{h.source:<30} {h.event:<20} {h.matcher or '(all)':<15} {h.handler_type:<10} {value}")


@hooks_app.command("validate")
def hooks_validate():
    """Validate all hooks across skills, agents, and settings."""
    from wagents.parsing import KNOWN_HOOK_EVENTS

    errors: list[str] = []

    def _validate_hooks(source: str, hooks_dict: dict) -> None:
        if not isinstance(hooks_dict, dict):
            errors.append(f"{source}: hooks must be a mapping")
            return
        for event, entries in hooks_dict.items():
            if event not in KNOWN_HOOK_EVENTS:
                errors.append(f"{source}: unknown hook event '{event}'")
            if not isinstance(entries, list):
                errors.append(f"{source}: entries for '{event}' must be a list")
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    errors.append(f"{source}: each entry in '{event}' must be a mapping")
                    continue
                hook_list = entry.get("hooks", [])
                # Standard format: nested hooks list
                if isinstance(hook_list, list) and hook_list:
                    for hook_def in hook_list:
                        if not isinstance(hook_def, dict):
                            errors.append(f"{source}: each hook definition must be a mapping")
                            continue
                        handler_type = hook_def.get("type", "command")
                        if handler_type not in ("command", "prompt", "agent"):
                            errors.append(f"{source}: unknown handler type '{handler_type}' in '{event}'")
                        if handler_type == "command" and not hook_def.get("command"):
                            errors.append(f"{source}: command handler in '{event}' has empty command")
                        if handler_type in (
                            "prompt",
                            "agent",
                        ) and not hook_def.get("prompt"):
                            errors.append(f"{source}: {handler_type} handler in '{event}' has empty prompt")
                elif not isinstance(hook_list, list):
                    errors.append(f"{source}: 'hooks' in '{event}' entry must be a list")
                # Shorthand format: command/prompt directly on entry
                elif "command" in entry or "prompt" in entry:
                    handler_type = entry.get("type", "command")
                    if handler_type not in ("command", "prompt", "agent"):
                        errors.append(f"{source}: unknown handler type '{handler_type}' in '{event}'")
                    if handler_type == "command" and not entry.get("command"):
                        errors.append(f"{source}: command handler in '{event}' has empty command")
                    if handler_type in (
                        "prompt",
                        "agent",
                    ) and not entry.get("prompt"):
                        errors.append(f"{source}: {handler_type} handler in '{event}' has empty prompt")

    # 1. Settings files
    for settings_name in ["settings.json", "settings.local.json"]:
        settings_file = ROOT / ".claude" / settings_name
        if settings_file.exists():
            try:
                data = json.loads(settings_file.read_text())
                hooks_dict = data.get("hooks", {})
                if hooks_dict:
                    _validate_hooks(settings_name, hooks_dict)
            except json.JSONDecodeError as e:
                errors.append(f"{settings_name}: invalid JSON: {e}")

    # 2. Skills
    skills_dir = ROOT / "skills"
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            try:
                fm, _ = parse_frontmatter(skill_file.read_text())
                hooks_dict = fm.get("hooks", {})
                if hooks_dict:
                    _validate_hooks(f"skill:{skill_dir.name}", hooks_dict)
            except Exception:
                pass

    # 3. Agents
    agents_dir = ROOT / "agents"
    if agents_dir.exists():
        for agent_file in sorted(agents_dir.glob("*.md")):
            try:
                fm, _ = parse_frontmatter(agent_file.read_text())
                hooks_dict = fm.get("hooks", {})
                if hooks_dict:
                    _validate_hooks(f"agent:{agent_file.stem}", hooks_dict)
            except Exception:
                pass

    if errors:
        for error in errors:
            typer.echo(error, err=True)
        raise typer.Exit(code=1)
    else:
        typer.echo("All hooks valid")


# ---------------------------------------------------------------------------
# wagents eval list / validate / coverage
# ---------------------------------------------------------------------------


def _collect_evals() -> list[tuple[Path, dict]]:
    """Scan skills/*/evals/*.json and return (path, parsed_data) pairs."""
    results: list[tuple[Path, dict]] = []
    evals_root = ROOT / "skills"
    if not evals_root.exists():
        return results
    for skill_dir in sorted(evals_root.iterdir()):
        if not skill_dir.is_dir():
            continue
        evals_dir = skill_dir / "evals"
        if not evals_dir.is_dir():
            continue
        for eval_file in sorted(evals_dir.glob("*.json")):
            try:
                data = json.loads(eval_file.read_text())
                results.append((eval_file, data))
            except json.JSONDecodeError:
                results.append((eval_file, {}))
    return results


@eval_app.command("list")
def eval_list():
    """List all eval files grouped by skill."""
    evals = _collect_evals()
    if not evals:
        typer.echo("No evals found.")
        return

    # Group by skill directory name
    by_skill: dict[str, list[dict]] = {}
    for path, data in evals:
        skill_name = path.parent.parent.name
        by_skill.setdefault(skill_name, []).append(data)

    # Print table
    typer.echo(f"{'Skill':<25} {'Evals':>5}  Sample Query")
    typer.echo("-" * 70)
    for skill_name in sorted(by_skill):
        items = by_skill[skill_name]
        count = len(items)
        sample = ""
        for item in items:
            q = item.get("query", "")
            if q:
                sample = q
                break
        typer.echo(f"{skill_name:<25} {count:>5}  {sample}")


@eval_app.command("validate")
def eval_validate():
    """Validate all eval JSON files."""
    evals = _collect_evals()
    if not evals:
        typer.echo("No evals found. Nothing to validate.")
        return

    errors: list[str] = []
    skills_dir = ROOT / "skills"

    for path, data in evals:
        rel = path.relative_to(ROOT)

        # Check for parse failure (empty dict from JSONDecodeError)
        if not data and path.stat().st_size > 2:
            errors.append(f"{rel}: invalid JSON")
            continue

        # Required field: skills
        if "skills" not in data:
            errors.append(f"{rel}: missing required field 'skills'")
        elif not isinstance(data["skills"], list) or len(data["skills"]) < 1:
            errors.append(f"{rel}: 'skills' must be a non-empty list of strings")
        else:
            for s in data["skills"]:
                if not isinstance(s, str):
                    errors.append(f"{rel}: each entry in 'skills' must be a string")
                elif not (skills_dir / s).is_dir():
                    errors.append(f"{rel}: skill '{s}' does not match a skill directory")

        # Required field: query
        if "query" not in data:
            errors.append(f"{rel}: missing required field 'query'")
        elif not isinstance(data["query"], str) or not data["query"].strip():
            errors.append(f"{rel}: 'query' must be a non-empty string")

        # Required field: expected_behavior
        if "expected_behavior" not in data:
            errors.append(f"{rel}: missing required field 'expected_behavior'")
        elif not isinstance(data["expected_behavior"], list) or len(data["expected_behavior"]) < 1:
            errors.append(f"{rel}: 'expected_behavior' must be a non-empty list of strings")
        else:
            for eb in data["expected_behavior"]:
                if not isinstance(eb, str):
                    errors.append(f"{rel}: each entry in 'expected_behavior' must be a string")

    if errors:
        for error in errors:
            typer.echo(error, err=True)
        raise typer.Exit(code=1)
    else:
        typer.echo("All evals valid")


@eval_app.command("coverage")
def eval_coverage():
    """Show eval coverage for all skills."""
    skills_dir = ROOT / "skills"
    if not skills_dir.exists():
        typer.echo("No skills directory found.")
        return

    # Collect all skills
    skill_names: list[str] = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            skill_names.append(skill_dir.name)

    if not skill_names:
        typer.echo("No skills found.")
        return

    # Count evals per skill
    evals = _collect_evals()
    counts: dict[str, int] = {}
    for path, _data in evals:
        skill_name = path.parent.parent.name
        counts[skill_name] = counts.get(skill_name, 0) + 1

    # Print table
    typer.echo(f"{'Skill':<25} {'Has Evals':<12} {'Count':>5}")
    typer.echo("-" * 45)
    for name in skill_names:
        count = counts.get(name, 0)
        has = "Yes" if count > 0 else "No"
        typer.echo(f"{name:<25} {has:<12} {count:>5}")


if __name__ == "__main__":
    app()
