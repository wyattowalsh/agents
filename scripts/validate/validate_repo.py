#!/usr/bin/env python3
"""Validate all repository skills, agents, MCP servers, and hooks."""

from __future__ import annotations

import argparse
from pathlib import Path

from _toolkit import ensure_validate_importable, repo_root_from_validate
from collectors.agents import collect_agent_errors
from collectors.authoring import collect_authoring_errors
from collectors.hooks import collect_hook_errors
from collectors.mcp import collect_mcp_validation_errors
from collectors.mcp_registry import collect_mcp_registry_errors
from collectors.mcphub_settings import collect_mcphub_settings_errors
from collectors.paths import collect_path_portability_errors
from collectors.quarantine import collect_quarantine_errors
from collectors.rtk import collect_rtk_instruction_errors
from collectors.skills import collect_skill_errors

ensure_validate_importable()

from asset_toolkit.common import emit_validation_output, find_repo_root
from sarif import emit_sarif_log


def collect_repo_errors(repo_root: Path) -> list[dict[str, str]]:
    """Merge validation errors from all collectors."""
    errors: list[dict[str, str]] = []
    errors.extend(collect_skill_errors(repo_root))
    errors.extend(collect_authoring_errors(repo_root))
    errors.extend(collect_agent_errors(repo_root))
    errors.extend(collect_mcp_validation_errors(repo_root))
    errors.extend(collect_hook_errors(repo_root))
    errors.extend(collect_path_portability_errors(repo_root))
    errors.extend(collect_mcp_registry_errors(repo_root))
    errors.extend(collect_mcphub_settings_errors(repo_root))
    errors.extend(collect_quarantine_errors(repo_root))
    errors.extend(collect_rtk_instruction_errors(repo_root))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate repository agent assets")
    parser.add_argument("--format", choices=["text", "json", "jsonl", "sarif"], default="text")
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
    errors = collect_repo_errors(repo_root)
    if args.format == "sarif":
        emit_sarif_log(errors)
    else:
        emit_validation_output(args.format, errors)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
