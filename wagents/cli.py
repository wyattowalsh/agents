"""CLI for managing centralized AI agent assets."""

import importlib.util
import json
import re
import shutil
import sys
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

OUTPUT_FORMATS = ("text", "json", "jsonl")


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


def _normalize_output_format(format_: str) -> str:
    """Normalize and validate a requested output format."""
    normalized = format_.lower()
    if normalized not in OUTPUT_FORMATS:
        typer.echo(
            f"Error: unsupported format '{format_}'. Use one of: {', '.join(OUTPUT_FORMATS)}",
            err=True,
        )
        raise typer.Exit(code=1)
    return normalized


def _emit_structured_output(
    format_: str,
    *,
    text_lines: list[str] | None = None,
    json_data: dict | list | None = None,
    jsonl_records: list[dict] | None = None,
) -> None:
    """Emit command output in text, json, or jsonl format."""
    normalized = _normalize_output_format(format_)
    if normalized == "text":
        for line in text_lines or []:
            typer.echo(line)
        return
    if normalized == "json":
        typer.echo(json.dumps(json_data, indent=2))
        return
    for record in jsonl_records or []:
        typer.echo(json.dumps(record))


def _format_error(source: str, message: str) -> str:
    """Render a validation-style error for text output."""
    return f"{source}: {message}"


def _collect_hooks():
    """Collect hooks from settings, skills, and agents."""
    from wagents.parsing import Hook, extract_hooks

    all_hooks: list[Hook] = []

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

    return all_hooks


def _parse_min_python_version(spec: str) -> tuple[int, int] | None:
    """Extract a minimum major/minor version from a requires-python spec."""
    match = re.search(r">=\s*(\d+)\.(\d+)", spec)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _make_doctor_check(
    name: str,
    status: str,
    summary: str,
    remediation: str | None = None,
) -> dict[str, str]:
    """Create a normalized doctor check record."""
    check = {"name": name, "status": status, "summary": summary}
    if remediation:
        check["remediation"] = remediation
    return check


def _collect_doctor_checks() -> list[dict[str, str]]:
    """Collect environment and toolchain diagnostics for the repo."""
    checks: list[dict[str, str]] = []

    pyproject_file = ROOT / "pyproject.toml"
    requires_python = ""
    if pyproject_file.exists():
        data = tomllib.loads(pyproject_file.read_text())
        requires_python = str(data.get("project", {}).get("requires-python", ""))

    min_version = _parse_min_python_version(requires_python)
    current_version = (sys.version_info.major, sys.version_info.minor)
    if min_version is None:
        checks.append(
            _make_doctor_check(
                "python-version",
                "warn",
                "Could not determine required Python version from pyproject.toml",
                "Set project.requires-python in pyproject.toml.",
            )
        )
    elif current_version >= min_version:
        checks.append(
            _make_doctor_check(
                "python-version",
                "ok",
                f"Python {current_version[0]}.{current_version[1]} satisfies {requires_python}",
            )
        )
    else:
        checks.append(
            _make_doctor_check(
                "python-version",
                "fail",
                f"Python {current_version[0]}.{current_version[1]} does not satisfy {requires_python}",
                "Install a compatible Python version and run commands through uv.",
            )
        )

    tool_checks = [
        ("uv", "fail", "Install uv: https://docs.astral.sh/uv/"),
        ("node", "warn", "Install Node.js to use docs and install workflows."),
        ("npx", "warn", "Install Node.js so npx is available for wagents install."),
        ("pnpm", "warn", "Install pnpm to manage docs dependencies."),
    ]
    for tool_name, missing_status, remediation in tool_checks:
        tool_path = shutil.which(tool_name)
        if tool_path:
            checks.append(_make_doctor_check(tool_name, "ok", f"Found at {tool_path}"))
        else:
            checks.append(
                _make_doctor_check(
                    tool_name,
                    missing_status,
                    f"{tool_name} is not available on PATH",
                    remediation,
                )
            )

    docs_dir = ROOT / "docs"
    package_json = docs_dir / "package.json"
    lock_file = docs_dir / "pnpm-lock.yaml"
    node_modules = docs_dir / "node_modules"
    if not docs_dir.exists():
        checks.append(
            _make_doctor_check(
                "docs-deps",
                "warn",
                "docs directory is missing",
                "Restore docs/ if you intend to build the documentation site.",
            )
        )
    elif not package_json.exists() or not lock_file.exists():
        checks.append(
            _make_doctor_check(
                "docs-deps",
                "warn",
                "docs dependency manifests are incomplete",
                "Ensure docs/package.json and docs/pnpm-lock.yaml both exist.",
            )
        )
    elif not node_modules.exists():
        checks.append(
            _make_doctor_check(
                "docs-deps",
                "warn",
                "docs/node_modules is missing",
                "Run pnpm --dir docs install.",
            )
        )
    else:
        node_modules_mtime = node_modules.stat().st_mtime
        stale_inputs = [path.name for path in (package_json, lock_file) if path.stat().st_mtime > node_modules_mtime]
        if stale_inputs:
            checks.append(
                _make_doctor_check(
                    "docs-deps",
                    "warn",
                    f"docs/node_modules may be stale relative to {', '.join(stale_inputs)}",
                    "Run pnpm --dir docs install to refresh docs dependencies.",
                )
            )
        else:
            checks.append(
                _make_doctor_check(
                    "docs-deps",
                    "ok",
                    "docs dependency manifests and node_modules look present",
                )
            )

    if importlib.util.find_spec("playwright") is None:
        checks.append(
            _make_doctor_check(
                "playwright-python",
                "warn",
                "Python Playwright package is not installed",
                "Run uv add --dev playwright.",
            )
        )
    else:
        checks.append(
            _make_doctor_check(
                "playwright-python",
                "ok",
                "Python Playwright package is installed",
            )
        )

    browser_cache_candidates = [
        Path.home() / "Library/Caches/ms-playwright",
        Path.home() / ".cache/ms-playwright",
    ]
    browser_cache = next((candidate for candidate in browser_cache_candidates if candidate.exists()), None)
    if browser_cache and any(browser_cache.iterdir()):
        checks.append(
            _make_doctor_check(
                "playwright-browsers",
                "ok",
                f"Playwright browser cache found at {browser_cache}",
            )
        )
    else:
        checks.append(
            _make_doctor_check(
                "playwright-browsers",
                "warn",
                "No Playwright browser cache detected",
                "Run uv run playwright install chromium.",
            )
        )

    return checks


def _emit_doctor_report(format_: str, checks: list[dict[str, str]]) -> None:
    """Emit doctor results in text, json, or jsonl format."""
    counts = {
        "ok": sum(1 for check in checks if check["status"] == "ok"),
        "warn": sum(1 for check in checks if check["status"] == "warn"),
        "fail": sum(1 for check in checks if check["status"] == "fail"),
    }
    json_result = {
        "ok": counts["fail"] == 0,
        "summary": {
            "total": len(checks),
            **counts,
        },
        "checks": checks,
    }
    text_lines = [
        (f"Doctor summary: {len(checks)} checks, {counts['ok']} ok, {counts['warn']} warn, {counts['fail']} fail")
    ]
    for check in checks:
        line = f"{check['status'].upper():<4} {check['name']:<20} {check['summary']}"
        if check.get("remediation"):
            line = f"{line} Fix: {check['remediation']}"
        text_lines.append(line)

    jsonl_records: list[dict[str, object]] = [{"type": "check", **check} for check in checks]
    jsonl_records.append({"type": "summary", **json_result["summary"], "ok": json_result["ok"]})

    _emit_structured_output(
        format_,
        text_lines=text_lines,
        json_data=json_result,
        jsonl_records=jsonl_records,
    )


@app.command()
def doctor(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Check environment and toolchain health for this repo."""
    checks = _collect_doctor_checks()
    _emit_doctor_report(format_, checks)
    if any(check["status"] == "fail" for check in checks):
        raise typer.Exit(code=1)


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
def validate(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Validate all skills and agents."""
    errors: list[dict[str, str]] = []

    def add_error(source: str | Path, message: str) -> None:
        errors.append({"source": str(source), "message": message})

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
                    add_error(skill_file, "missing required field 'name'")
                else:
                    name = fm["name"]
                    if not KEBAB_CASE_PATTERN.match(name):
                        add_error(skill_file, "name must be kebab-case")
                    if len(name) > 64:
                        add_error(skill_file, "name exceeds 64 characters")
                    if name != skill_dir.name:
                        add_error(skill_file, f"name '{name}' doesn't match directory '{skill_dir.name}'")

                # Validate description
                if "description" not in fm:
                    add_error(skill_file, "missing required field 'description'")
                elif not str(fm["description"]).strip():
                    add_error(skill_file, "description cannot be empty")
                elif len(str(fm["description"])) > 1024:
                    add_error(skill_file, "description exceeds 1024 characters")

                # Validate body
                if not body:
                    add_error(skill_file, "body cannot be empty")

            except Exception as e:
                add_error(skill_file, str(e))

    # Validate agents
    agents_dir = ROOT / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            try:
                content = agent_file.read_text()
                fm, _ = parse_frontmatter(content)

                # Validate name
                if "name" not in fm:
                    add_error(agent_file, "missing required field 'name'")
                else:
                    name = fm["name"]
                    if not KEBAB_CASE_PATTERN.match(name):
                        add_error(agent_file, "name must be kebab-case")
                    if name != agent_file.stem:
                        add_error(agent_file, f"name '{name}' doesn't match filename '{agent_file.stem}'")

                # Validate description
                if "description" not in fm:
                    add_error(agent_file, "missing required field 'description'")
                elif not str(fm["description"]).strip():
                    add_error(agent_file, "description cannot be empty")

            except Exception as e:
                add_error(agent_file, str(e))

    # Validate MCP servers
    mcp_dir = ROOT / "mcp"
    if mcp_dir.exists():
        for mcp_subdir in mcp_dir.iterdir():
            if not mcp_subdir.is_dir():
                continue
            dir_name = mcp_subdir.name
            if not KEBAB_CASE_PATTERN.match(dir_name):
                add_error(f"mcp/{dir_name}", "directory name must be kebab-case")
            # Check if it's a Node.js project
            package_json = mcp_subdir / "package.json"
            if package_json.exists():
                continue

            server_py = mcp_subdir / "server.py"
            if not server_py.exists():
                add_error(f"mcp/{dir_name}", "missing server.py")
            else:
                server_text = server_py.read_text()
                if "FastMCP" not in server_text:
                    add_error(f"mcp/{dir_name}", "server.py does not reference FastMCP")
            pyproject = mcp_subdir / "pyproject.toml"
            if not pyproject.exists():
                add_error(f"mcp/{dir_name}", "missing pyproject.toml")
            else:
                pyproject_text = pyproject.read_text()
                if "fastmcp" not in pyproject_text:
                    add_error(f"mcp/{dir_name}", "pyproject.toml missing fastmcp dependency")
            fastmcp_json = mcp_subdir / "fastmcp.json"
            if not fastmcp_json.exists():
                add_error(f"mcp/{dir_name}", "missing fastmcp.json")

    # Validate RELATED_SKILLS references
    for key, values in RELATED_SKILLS.items():
        if not (ROOT / "skills" / key).is_dir():
            add_error("RELATED_SKILLS", f"key '{key}' does not match a skill directory")
        for val in values:
            if not (ROOT / "skills" / val).is_dir():
                add_error("RELATED_SKILLS", f"value '{val}' (in '{key}') does not match a skill directory")

    # Validate hooks
    from wagents.parsing import KNOWN_HOOK_EVENTS

    def _check_hooks(source: str, hooks_dict: dict) -> None:
        if not isinstance(hooks_dict, dict):
            add_error(source, "hooks must be a mapping")
            return
        for event in hooks_dict:
            if event not in KNOWN_HOOK_EVENTS:
                add_error(source, f"unknown hook event '{event}'")

    for settings_name in ["settings.json", "settings.local.json"]:
        settings_file = ROOT / ".claude" / settings_name
        if settings_file.exists():
            try:
                data = json.loads(settings_file.read_text())
                hooks_dict = data.get("hooks", {})
                if hooks_dict:
                    _check_hooks(settings_name, hooks_dict)
            except json.JSONDecodeError as e:
                add_error(settings_name, f"invalid JSON: {e}")

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

    text_errors = [_format_error(error["source"], error["message"]) for error in errors]
    json_result = {
        "ok": not errors,
        "error_count": len(errors),
        "errors": errors,
        "message": "All validations passed" if not errors else "Validation failed",
    }
    jsonl_records: list[dict[str, object]] = [{"type": "error", **error} for error in errors]
    jsonl_records.append(
        {
            "type": "summary",
            "ok": not errors,
            "error_count": len(errors),
            "message": json_result["message"],
        }
    )

    _emit_structured_output(
        format_,
        text_lines=text_errors if errors else ["All validations passed"],
        json_data=json_result,
        jsonl_records=jsonl_records,
    )
    if errors:
        raise typer.Exit(code=1)


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
    skills = []
    skills_dir = ROOT / "skills"
    if skills_dir.exists():
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

    agents = []
    agents_dir = ROOT / "agents"
    if agents_dir.exists():
        for agent_file in sorted(agents_dir.glob("*.md")):
            try:
                fm, _ = parse_frontmatter(agent_file.read_text())
                agents.append((fm.get("name", agent_file.stem), fm.get("description", "")))
            except Exception as e:
                typer.echo(f"Warning: skipping {agent_file}: {e}", err=True)

    mcps = []
    mcp_dir = ROOT / "mcp"
    if mcp_dir.exists():
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

    content_parts = [
        '<div align="center">',
        (
            '  <img src="https://raw.githubusercontent.com/wyattowalsh/agents/main/'
            'docs/src/assets/logo.webp" alt="Agents Logo" width="100" height="100">'
        ),
        "  <h1>agents</h1>",
        "  <p><b>AI agent artifacts, configs, skills, tools, and more</b></p>",
        "  <p>",
        (
            '    <a href="https://github.com/wyattowalsh/agents/actions/workflows/ci.yml">'
            '<img src="https://github.com/wyattowalsh/agents/actions/workflows/ci.yml/'
            'badge.svg" alt="CI"></a>'
        ),
        (
            '    <a href="https://github.com/wyattowalsh/agents/blob/main/LICENSE">'
            '<img src="https://img.shields.io/github/license/wyattowalsh/agents?'
            'style=flat-square&color=5D6D7E" alt="License"></a>'
        ),
        (
            '    <a href="https://github.com/wyattowalsh/agents/releases"><img '
            'src="https://img.shields.io/github/v/release/wyattowalsh/agents?'
            'style=flat-square&color=2E86C1" alt="Release"></a>'
        ),
        (
            f'    <a href="https://agents.w4w.dev/skills/"><img '
            f'src="https://img.shields.io/badge/skills-{len(skills)}-0f766e?'
            'style=flat-square" alt="Skills"></a>'
        ),
        (
            '    <a href="https://agents.w4w.dev"><img src="https://img.shields.io/'
            "badge/docs-agents.w4w.dev-00b4d8?style=flat-square&logo=read-the-docs"
            '&logoColor=white" alt="Docs"></a>'
        ),
        "  </p>",
        "</div>",
        "",
        "---",
        "",
        "## 🚀 Quick Start",
        "",
        "Install all skills globally into your favorite agents:",
        "",
        "```bash",
        (
            "npx skills add github:wyattowalsh/agents --all -y -g --agent claude-code "
            "--agent codex --agent gemini-cli --agent antigravity "
            "--agent github-copilot --agent opencode"
        ),
        "```",
        "",
        "## ✨ Why use this repository?",
        "",
        "| 📦 **Portable** | 🧩 **Composable** | 🌐 **Open Source** |",
        "| :--- | :--- | :--- |",
        (
            "| Use skills across Claude Code, Cursor, Copilot, and more. | Combine "
            "simple skills into complex, multi-agent workflows. | Extensible, "
            "readable, and community-driven. |"
        ),
        "",
    ]

    if skills:
        content_parts.extend(
            [
                "## 🧰 Skills",
                "",
                "Reusable actions and knowledge bases for AI agents.",
                "",
                "| Name | Description |",
                "| ---- | ----------- |",
            ]
        )
        for name, desc in skills:
            content_parts.append(f"| {name} | {desc} |")
        content_parts.append("")

    if agents:
        content_parts.extend(
            [
                "## 🤖 Agents",
                "",
                "System prompts and context definitions for AI agents.",
                "",
                "| Name | Description |",
                "| ---- | ----------- |",
            ]
        )
        for name, desc in agents:
            content_parts.append(f"| {name} | {desc} |")
        content_parts.append("")

    if mcps:
        content_parts.extend(
            [
                "## 🔌 MCP Servers",
                "",
                "Model Context Protocol servers for interacting with external tools.",
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
            "## 🛠️ Development",
            "",
            "| Command | Description |",
            "| ------- | ----------- |",
            "| `wagents new skill <name>` | Create a new skill |",
            "| `wagents new agent <name>` | Create a new agent |",
            "| `wagents new mcp <name>` | Create a new MCP server |",
            "| `wagents doctor` | Check local environment and toolchain health |",
            "| `wagents validate` | Validate all skills and agents |",
            "| `make typecheck` | Run ty across `wagents/` and `scripts/` |",
            "| `wagents readme` | Regenerate this README |",
            "| `wagents package <name>` | Package a skill into portable ZIP |",
            "| `wagents package --all` | Package all skills |",
            "| `wagents install` | Install all skills to all agents |",
            "| `wagents install -a <agent>` | Install all skills to specific agent |",
            "| `wagents install <name>` | Install specific skill to all agents |",
            "| `wagents install <name> -a <agent>` | Install specific skill to specific agents |",
            "| `wagents docs init` | One-time setup: install docs dependencies |",
            "| `wagents docs generate` | Generate MDX content pages from assets |",
            (
                "| `wagents docs generate --include-installed` | Include installed "
                "skills discovered from local agent skill directories in generated docs |"
            ),
            "| `wagents docs dev` | Generate + launch dev server |",
            "| `wagents docs build` | Generate + production build |",
            "| `wagents docs preview` | Generate + build + preview server |",
            "| `wagents docs clean` | Remove generated content pages |",
            "",
            "Third-party skill collections can be installed directly with "
            "`npx skills add <source> --skill <name> -y -g --agent <agent>`. "
            "Repeat `--skill` and `--agent` to target a curated subset.",
            "",
        ]
    )

    # Supported agents
    content_parts.extend(
        [
            "## 🤝 Supported Agents",
            "",
            "- [Antigravity](https://antigravity.google/)",
            "- [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)",
            "- [Codex](https://github.com/openai/codex)",
            "- [Crush](https://github.com/crush-ai/crush)",
            "- [Cursor](https://cursor.sh/)",
            "- [Gemini CLI](https://github.com/google/gemini-cli)",
            "- [GitHub Copilot](https://github.com/features/copilot)",
            "- [OpenCode](https://github.com/anomalyco/opencode) — native AGENTS.md support with repo-level config",
            "And other [agentskills.io](https://agentskills.io)-compatible agents.",
            "",
        ]
    )

    content_parts.extend(
        [
            "## 📚 Documentation",
            "",
            (
                "Explore the full catalog, installation guides, and generated reference pages "
                "at [agents.w4w.dev](https://agents.w4w.dev)."
            ),
            "",
        ]
    )

    # License
    content_parts.extend(["## 📜 License", "", "[MIT](LICENSE)", ""])

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
def hooks_list(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """List all hooks across skills, agents, and settings."""
    all_hooks = _collect_hooks()

    if not all_hooks:
        _emit_structured_output(
            format_,
            text_lines=["No hooks found."],
            json_data={"count": 0, "hooks": []},
            jsonl_records=[{"type": "summary", "count": 0}],
        )
        return

    rows: list[dict[str, str]] = []
    for hook in all_hooks:
        rows.append(
            {
                "source": hook.source,
                "event": hook.event,
                "matcher": hook.matcher,
                "handler_type": hook.handler_type,
                "command": hook.command,
                "prompt": hook.prompt,
            }
        )

    text_lines = [f"{'Source':<30} {'Event':<20} {'Matcher':<15} {'Type':<10} {'Command/Prompt'}", "-" * 100]
    for row in rows:
        value = row["command"] if row["handler_type"] == "command" else row["prompt"]
        if len(value) > 50:
            value = value[:47] + "..."
        matcher = row["matcher"] or "(all)"
        text_lines.append(f"{row['source']:<30} {row['event']:<20} {matcher:<15} {row['handler_type']:<10} {value}")

    _emit_structured_output(
        format_,
        text_lines=text_lines,
        json_data={"count": len(rows), "hooks": rows},
        jsonl_records=[{"type": "hook", **row} for row in rows] + [{"type": "summary", "count": len(rows)}],
    )


@hooks_app.command("validate")
def hooks_validate(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Validate all hooks across skills, agents, and settings."""
    from wagents.parsing import KNOWN_HOOK_EVENTS

    errors: list[dict[str, str]] = []

    def add_error(source: str, message: str) -> None:
        errors.append({"source": source, "message": message})

    def _validate_hooks(source: str, hooks_dict: dict) -> None:
        if not isinstance(hooks_dict, dict):
            add_error(source, "hooks must be a mapping")
            return
        for event, entries in hooks_dict.items():
            if event not in KNOWN_HOOK_EVENTS:
                add_error(source, f"unknown hook event '{event}'")
            if not isinstance(entries, list):
                add_error(source, f"entries for '{event}' must be a list")
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    add_error(source, f"each entry in '{event}' must be a mapping")
                    continue
                hook_list = entry.get("hooks", [])
                # Standard format: nested hooks list
                if isinstance(hook_list, list) and hook_list:
                    for hook_def in hook_list:
                        if not isinstance(hook_def, dict):
                            add_error(source, "each hook definition must be a mapping")
                            continue
                        handler_type = hook_def.get("type", "command")
                        if handler_type not in ("command", "prompt", "agent"):
                            add_error(source, f"unknown handler type '{handler_type}' in '{event}'")
                        if handler_type == "command" and not hook_def.get("command"):
                            add_error(source, f"command handler in '{event}' has empty command")
                        if handler_type in (
                            "prompt",
                            "agent",
                        ) and not hook_def.get("prompt"):
                            add_error(source, f"{handler_type} handler in '{event}' has empty prompt")
                elif not isinstance(hook_list, list):
                    add_error(source, f"'hooks' in '{event}' entry must be a list")
                # Shorthand format: command/prompt directly on entry
                elif "command" in entry or "prompt" in entry:
                    handler_type = entry.get("type", "command")
                    if handler_type not in ("command", "prompt", "agent"):
                        add_error(source, f"unknown handler type '{handler_type}' in '{event}'")
                    if handler_type == "command" and not entry.get("command"):
                        add_error(source, f"command handler in '{event}' has empty command")
                    if handler_type in (
                        "prompt",
                        "agent",
                    ) and not entry.get("prompt"):
                        add_error(source, f"{handler_type} handler in '{event}' has empty prompt")

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
                add_error(settings_name, f"invalid JSON: {e}")

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

    text_errors = [_format_error(error["source"], error["message"]) for error in errors]
    json_result = {
        "ok": not errors,
        "error_count": len(errors),
        "errors": errors,
        "message": "All hooks valid" if not errors else "Hook validation failed",
    }
    jsonl_records: list[dict[str, object]] = [{"type": "error", **error} for error in errors]
    jsonl_records.append(
        {
            "type": "summary",
            "ok": not errors,
            "error_count": len(errors),
            "message": json_result["message"],
        }
    )

    _emit_structured_output(
        format_,
        text_lines=text_errors if errors else ["All hooks valid"],
        json_data=json_result,
        jsonl_records=jsonl_records,
    )
    if errors:
        raise typer.Exit(code=1)


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


def _is_eval_manifest(data: dict) -> bool:
    """Return True when an eval JSON file uses the canonical manifest shape."""
    return "evals" in data


def _expand_eval_cases(path: Path, data: dict) -> list[dict[str, object]]:
    """Expand an eval file into normalized per-case records."""
    skill_name = path.parent.parent.name
    if _is_eval_manifest(data):
        records: list[dict[str, object]] = []
        manifest_skill = data.get("skill_name", skill_name)
        for index, item in enumerate(data.get("evals", []), start=1):
            if not isinstance(item, dict):
                records.append({"skill": manifest_skill, "query": "", "source": path.name, "case_id": index})
                continue
            records.append(
                {
                    "skill": manifest_skill,
                    "query": item.get("prompt", ""),
                    "source": path.name,
                    "case_id": item.get("id", index),
                }
            )
        return records
    return [{"skill": skill_name, "query": data.get("query", ""), "source": path.name, "case_id": path.stem}]


@eval_app.command("list")
def eval_list(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """List all eval files grouped by skill."""
    evals = _collect_evals()
    if not evals:
        _emit_structured_output(
            format_,
            text_lines=["No evals found."],
            json_data={"count": 0, "eval_count": 0, "skills": []},
            jsonl_records=[{"type": "summary", "count": 0, "eval_count": 0}],
        )
        return

    # Group by skill directory name.
    by_skill: dict[str, list[dict[str, object]]] = {}
    for path, data in evals:
        for record in _expand_eval_cases(path, data):
            skill_name = str(record["skill"])
            by_skill.setdefault(skill_name, []).append(record)

    rows: list[dict[str, str | int]] = []
    for skill_name in sorted(by_skill):
        items = by_skill[skill_name]
        count = len(items)
        sample = next((str(item.get("query", "")) for item in items if item.get("query", "")), "")
        rows.append({"skill": skill_name, "eval_count": count, "sample_query": sample})

    total_cases = sum(len(items) for items in by_skill.values())

    text_lines = [f"{'Skill':<25} {'Evals':>5}  Sample Query", "-" * 70]
    text_lines.extend([f"{row['skill']:<25} {row['eval_count']:>5}  {row['sample_query']}" for row in rows])
    _emit_structured_output(
        format_,
        text_lines=text_lines,
        json_data={"count": len(rows), "eval_count": total_cases, "skills": rows},
        jsonl_records=[{"type": "skill", **row} for row in rows],
    )


@eval_app.command("validate")
def eval_validate(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Validate all eval JSON files."""
    evals = _collect_evals()
    if not evals:
        _emit_structured_output(
            format_,
            text_lines=["No evals found. Nothing to validate."],
            json_data={"ok": True, "eval_count": 0, "error_count": 0, "errors": []},
            jsonl_records=[{"type": "summary", "ok": True, "eval_count": 0, "error_count": 0}],
        )
        return

    errors: list[dict[str, str]] = []
    skills_dir = ROOT / "skills"

    def add_error(source: str | Path, message: str) -> None:
        errors.append({"source": str(source), "message": message})

    for path, data in evals:
        rel = path.relative_to(ROOT)

        # Check for parse failure (empty dict from JSONDecodeError)
        if not data and path.stat().st_size > 2:
            add_error(rel, "invalid JSON")
            continue

        if _is_eval_manifest(data):
            if not isinstance(data.get("skill_name"), str) or not data["skill_name"].strip():
                add_error(rel, "'skill_name' must be a non-empty string")
            elif not (skills_dir / data["skill_name"]).is_dir():
                add_error(rel, f"skill '{data['skill_name']}' does not match a skill directory")

            if not isinstance(data.get("evals"), list) or len(data["evals"]) < 1:
                add_error(rel, "'evals' must be a non-empty list")
                continue

            for index, item in enumerate(data["evals"], start=1):
                case_label = f"eval {index}"
                if not isinstance(item, dict):
                    add_error(rel, f"{case_label} must be an object")
                    continue
                if not isinstance(item.get("prompt"), str) or not item["prompt"].strip():
                    add_error(rel, f"{case_label} missing required non-empty string 'prompt'")
                if not isinstance(item.get("expected_output"), str) or not item["expected_output"].strip():
                    add_error(rel, f"{case_label} missing required non-empty string 'expected_output'")
                if "files" in item and (
                    not isinstance(item["files"], list)
                    or any(not isinstance(file_path, str) for file_path in item["files"])
                ):
                    add_error(rel, f"{case_label} field 'files' must be a list of strings")
                if "assertions" in item:
                    if not isinstance(item["assertions"], list) or len(item["assertions"]) < 1:
                        add_error(rel, f"{case_label} field 'assertions' must be a non-empty list of strings")
                    elif any(not isinstance(assertion, str) for assertion in item["assertions"]):
                        add_error(rel, f"{case_label} field 'assertions' must contain only strings")
            continue

        # Legacy eval scenario format.
        if "skills" not in data:
            add_error(rel, "missing required field 'skills'")
        elif not isinstance(data["skills"], list) or len(data["skills"]) < 1:
            add_error(rel, "'skills' must be a non-empty list of strings")
        else:
            for s in data["skills"]:
                if not isinstance(s, str):
                    add_error(rel, "each entry in 'skills' must be a string")
                elif not (skills_dir / s).is_dir():
                    add_error(rel, f"skill '{s}' does not match a skill directory")

        if "query" not in data:
            add_error(rel, "missing required field 'query'")
        elif not isinstance(data["query"], str) or not data["query"].strip():
            add_error(rel, "'query' must be a non-empty string")

        if "expected_behavior" not in data:
            add_error(rel, "missing required field 'expected_behavior'")
        elif not isinstance(data["expected_behavior"], list) or len(data["expected_behavior"]) < 1:
            add_error(rel, "'expected_behavior' must be a non-empty list of strings")
        else:
            for eb in data["expected_behavior"]:
                if not isinstance(eb, str):
                    add_error(rel, "each entry in 'expected_behavior' must be a string")

    total_cases = sum(len(_expand_eval_cases(path, data)) for path, data in evals)
    text_errors = [_format_error(error["source"], error["message"]) for error in errors]
    json_result = {
        "ok": not errors,
        "eval_count": total_cases,
        "error_count": len(errors),
        "errors": errors,
        "message": "All evals valid" if not errors else "Eval validation failed",
    }
    jsonl_records: list[dict[str, object]] = [{"type": "error", **error} for error in errors]
    jsonl_records.append(
        {
            "type": "summary",
            "ok": not errors,
            "eval_count": total_cases,
            "error_count": len(errors),
            "message": json_result["message"],
        }
    )

    _emit_structured_output(
        format_,
        text_lines=text_errors if errors else ["All evals valid"],
        json_data=json_result,
        jsonl_records=jsonl_records,
    )
    if errors:
        raise typer.Exit(code=1)


@eval_app.command("coverage")
def eval_coverage(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
):
    """Show eval coverage for all skills."""
    skills_dir = ROOT / "skills"
    if not skills_dir.exists():
        _emit_structured_output(
            format_,
            text_lines=["No skills directory found."],
            json_data={"count": 0, "skills": []},
            jsonl_records=[{"type": "summary", "count": 0}],
        )
        return

    # Collect all skills
    skill_names: list[str] = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            skill_names.append(skill_dir.name)

    if not skill_names:
        _emit_structured_output(
            format_,
            text_lines=["No skills found."],
            json_data={"count": 0, "skills": []},
            jsonl_records=[{"type": "summary", "count": 0}],
        )
        return

    # Count evals per skill
    evals = _collect_evals()
    counts: dict[str, int] = {}
    for path, data in evals:
        for record in _expand_eval_cases(path, data):
            skill_name = str(record["skill"])
            counts[skill_name] = counts.get(skill_name, 0) + 1

    rows: list[dict[str, str | int | bool]] = []
    for name in skill_names:
        count = counts.get(name, 0)
        rows.append({"skill": name, "has_evals": count > 0, "eval_count": count})

    text_lines = [f"{'Skill':<25} {'Has Evals':<12} {'Count':>5}", "-" * 45]
    text_lines.extend(
        [f"{row['skill']:<25} {('Yes' if row['has_evals'] else 'No'):<12} {row['eval_count']:>5}" for row in rows]
    )
    _emit_structured_output(
        format_,
        text_lines=text_lines,
        json_data={"count": len(rows), "skills": rows},
        jsonl_records=[{"type": "skill", **row} for row in rows],
    )


if __name__ == "__main__":
    app()
