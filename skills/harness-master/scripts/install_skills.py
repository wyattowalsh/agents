#!/usr/bin/env python3
"""Build and optionally run npx skills add install commands."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_REPO_SOURCE = "github:wyattowalsh/agents"
SUPPORTED_AGENTS = (
    "antigravity",
    "claude-code",
    "codex",
    "crush",
    "cursor",
    "gemini-cli",
    "github-copilot",
    "grok",
    "opencode",
)


def build_install_command(
    *,
    source: str,
    skills: list[str] | None,
    agents: list[str] | None,
    global_install: bool,
    copy: bool,
    yes: bool,
    list_only: bool,
) -> list[str]:
    cmd = ["npx", "-y", "skills", "add", source]
    if list_only:
        cmd.append("--list")
        return cmd

    if skills:
        for skill in skills:
            cmd.extend(["--skill", skill])
    else:
        cmd.extend(["--skill", "*"])

    if agents:
        for agent in agents:
            cmd.extend(["-a", agent])
    else:
        cmd.extend(["--agent", "*"])

    if global_install:
        cmd.append("-g")
    if copy:
        cmd.append("--copy")
    if yes:
        cmd.append("-y")
    return cmd


def validate_agents(agents: list[str]) -> list[str]:
    errors: list[str] = []
    for agent in agents:
        if agent not in SUPPORTED_AGENTS:
            errors.append(f"unknown agent '{agent}'; supported: {', '.join(SUPPORTED_AGENTS)}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build npx skills add install commands")
    parser.add_argument("skills", nargs="*", help="Skill name(s) to install (omit for all)")
    parser.add_argument("-a", "--agent", action="append", dest="agents", help="Target agent(s), repeatable")
    parser.add_argument("-s", "--source", default=DEFAULT_REPO_SOURCE, help="Published skills source")
    parser.add_argument("--local", action="store_true", help="Install project-local instead of global")
    parser.add_argument("--copy", action="store_true", help="Copy files instead of symlinking")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompts")
    parser.add_argument("--list", action="store_true", help="List available skills without installing")
    parser.add_argument("--dry-run", action="store_true", help="Print command without executing")
    parser.add_argument("--execute", action="store_true", help="Run the install command")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    if args.agents:
        agent_errors = validate_agents(args.agents)
        if agent_errors:
            for error in agent_errors:
                print(error, file=sys.stderr)
            return 1

    cmd = build_install_command(
        source=args.source,
        skills=args.skills or None,
        agents=args.agents,
        global_install=not args.local,
        copy=args.copy,
        yes=args.yes,
        list_only=args.list,
    )

    if args.format == "json":
        print(json.dumps({"command": cmd, "argv": cmd}, indent=2))
    else:
        print(" ".join(cmd))

    if args.dry_run or not args.execute:
        return 0

    if not shutil.which("npx"):
        print("Error: npx not found. Install Node.js first.", file=sys.stderr)
        return 1

    result = subprocess.run(cmd, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())