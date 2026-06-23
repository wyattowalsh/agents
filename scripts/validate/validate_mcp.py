#!/usr/bin/env python3
"""Validate first-party MCP server layout in the repository."""

from __future__ import annotations

import argparse
from pathlib import Path

from _toolkit import ensure_validate_importable, repo_root_from_validate

ensure_validate_importable()

from asset_toolkit.common import emit_validation_output, find_repo_root
from collectors.mcp import collect_mcp_errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate MCP server layout")
    parser.add_argument("--format", choices=["text", "json", "jsonl"], default="text")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: auto-detect from cwd)",
    )
    args = parser.parse_args(argv)

    if args.repo_root is not None:
        repo_root = args.repo_root.resolve()
    else:
        repo_root = find_repo_root() or repo_root_from_validate()
    errors = collect_mcp_errors(repo_root)
    emit_validation_output(
        args.format,
        errors,
        ok_message="All MCP servers valid",
        fail_message="MCP validation failed",
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
