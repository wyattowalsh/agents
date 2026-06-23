#!/usr/bin/env python3
"""Scaffold a new MCP server from template (no repo CLI dependency)."""

from __future__ import annotations

import argparse
import json
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


def update_workspace_members(root_pyproject: Path, workspace_member: str) -> None:
    content = root_pyproject.read_text(encoding="utf-8")

    if "[tool.uv.workspace]" not in content:
        if not content.endswith("\n"):
            content += "\n"
        content += f'\n[tool.uv.workspace]\nmembers = ["{workspace_member}"]\n'
        root_pyproject.write_text(content, encoding="utf-8")
        return

    if f'"{workspace_member}"' in content or f"'{workspace_member}'" in content:
        return

    workspace_match = re.search(r"(?ms)^\[tool\.uv\.workspace\]\n(?P<body>.*?)(?=^\[|\Z)", content)
    if not workspace_match:
        return

    body = workspace_match.group("body")
    members_match = re.search(r"(?ms)^members\s*=\s*\[(?P<members>.*?)\]", body)
    if members_match:
        members = members_match.group("members").strip()
        replacement = (
            f'members = ["{workspace_member}"]' if not members else f'members = [{members}, "{workspace_member}"]'
        )
        start = workspace_match.start("body") + members_match.start()
        end = workspace_match.start("body") + members_match.end()
        content = content[:start] + replacement + content[end:]
    else:
        insert_at = workspace_match.start("body")
        content = content[:insert_at] + f'members = ["{workspace_member}"]\n' + content[insert_at:]

    root_pyproject.write_text(content, encoding="utf-8")


def scaffold_mcp(repo_root: Path, name: str, *, dry_run: bool = False) -> Path:
    validate_name(name)
    mcp_dir = repo_root / "mcp" / name

    if mcp_dir.exists():
        raise FileExistsError(f"{mcp_dir} already exists")

    title = to_title(name)
    server_content = f'''"""MCP server: {name}."""

from fastmcp import FastMCP

mcp = FastMCP("{title}")


@mcp.tool
def hello(query: str) -> str:
    """Example tool — replace with your implementation."""
    return f"Hello from {name}: {{query}}"
'''
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
    fastmcp_config = {
        "$schema": "https://gofastmcp.com/public/schemas/fastmcp.json/v1.json",
        "source": {"path": "server.py", "entrypoint": "mcp"},
        "environment": {"type": "uv"},
    }
    fastmcp_content = json.dumps(fastmcp_config, indent=2) + "\n"

    if dry_run:
        print(server_content)
        print("--- pyproject.toml ---")
        print(pyproject_content)
        print("--- fastmcp.json ---")
        print(fastmcp_content)
        return mcp_dir

    mcp_dir.mkdir(parents=True, exist_ok=True)
    (mcp_dir / "server.py").write_text(server_content, encoding="utf-8")
    (mcp_dir / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")
    (mcp_dir / "fastmcp.json").write_text(fastmcp_content, encoding="utf-8")

    root_pyproject = repo_root / "pyproject.toml"
    if root_pyproject.is_file():
        update_workspace_members(root_pyproject, f"mcp/{name}")

    return mcp_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new MCP server")
    parser.add_argument("name", help="kebab-case MCP server name")
    parser.add_argument("--dry-run", action="store_true", help="Print scaffold output without writing files")
    args = parser.parse_args(argv)

    repo_root = find_repo_root()
    if repo_root is None:
        print("Could not find repo root (expected a parent with skills/)", file=sys.stderr)
        return 1

    try:
        path = scaffold_mcp(repo_root, args.name, dry_run=args.dry_run)
    except (ValueError, FileExistsError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not args.dry_run:
        rel = path.relative_to(repo_root)
        print(f"Created {rel}/ with server.py, pyproject.toml, and fastmcp.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
