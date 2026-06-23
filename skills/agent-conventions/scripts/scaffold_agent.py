#!/usr/bin/env python3
"""Scaffold a new agent definition from template (no repo CLI dependency)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

KEBAB_CASE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def find_repo_root(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for path in [current, *current.parents]:
        if (path / "skills").is_dir():
            return path
    return None


def validate_name(name: str) -> None:
    if not KEBAB_CASE_PATTERN.match(name):
        raise ValueError(f"name must be kebab-case (got '{name}')")
    if len(name) > 64:
        raise ValueError("name exceeds 64 characters")


def to_title(name: str) -> str:
    return name.replace("-", " ").title()


def scaffold_agent(repo_root: Path, name: str, *, dry_run: bool = False) -> Path:
    validate_name(name)
    agents_dir = repo_root / "agents"
    agent_file = agents_dir / f"{name}.md"

    if agent_file.exists():
        raise FileExistsError(f"{agent_file} already exists")

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

    if dry_run:
        print(content)
        return agent_file

    agents_dir.mkdir(parents=True, exist_ok=True)
    agent_file.write_text(content, encoding="utf-8")
    return agent_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new agent definition")
    parser.add_argument("name", help="kebab-case agent name")
    parser.add_argument("--dry-run", action="store_true", help="Print scaffold output without writing files")
    args = parser.parse_args(argv)

    repo_root = find_repo_root()
    if repo_root is None:
        print("Could not find repo root (expected a parent with skills/)", file=sys.stderr)
        return 1

    try:
        path = scaffold_agent(repo_root, args.name, dry_run=args.dry_run)
    except (ValueError, FileExistsError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not args.dry_run:
        print(f"Created {path.relative_to(repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
