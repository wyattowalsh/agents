#!/usr/bin/env python3
"""Regenerate docs artifacts and run Astro build health checks."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for path in [current, *current.parents]:
        if (path / "docs").is_dir() and (path / "skills").is_dir():
            return path
    return None


def repo_cli_name(repo_root: Path) -> str | None:
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.is_file():
        return None
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    scripts = data.get("project", {}).get("scripts", {})
    if not isinstance(scripts, dict) or not scripts:
        return None
    return next(iter(scripts))


def run_command(command: list[str], *, cwd: Path, label: str) -> int:
    print(f"[docs-sync] {label}: {' '.join(command)}", file=sys.stderr)
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode != 0:
        print(f"[docs-sync] {label} failed with exit code {result.returncode}", file=sys.stderr)
    return result.returncode


def generate_docs(repo_root: Path, *, include_installed: bool) -> int:
    cli_name = repo_cli_name(repo_root)
    if cli_name is None:
        print("[docs-sync] no project CLI script found in pyproject.toml", file=sys.stderr)
        return 1

    flag = "--include-installed" if include_installed else "--no-installed"
    if shutil.which("uv"):
        command = ["uv", "run", cli_name, "docs", "generate", flag]
    else:
        command = [sys.executable, "-m", cli_name, "docs", "generate", flag]
    return run_command(command, cwd=repo_root, label="generate")


def build_docs(repo_root: Path) -> int:
    docs_dir = repo_root / "docs"
    if not docs_dir.is_dir():
        print(f"[docs-sync] docs directory not found: {docs_dir}", file=sys.stderr)
        return 1
    if not shutil.which("pnpm"):
        print("[docs-sync] pnpm not found; cannot run docs build", file=sys.stderr)
        return 1
    return run_command(["pnpm", "build"], cwd=docs_dir, label="build")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate docs artifacts and build the docs site")
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["sync", "generate", "build"],
        default="sync",
        help="sync=generate+build (default), generate only, or build only",
    )
    parser.add_argument(
        "--include-installed",
        action="store_true",
        help="Include installed skills when generating docs (default: --no-installed)",
    )
    args = parser.parse_args(argv)

    repo_root = find_repo_root()
    if repo_root is None:
        print("Could not find repo root with docs/ and skills/", file=sys.stderr)
        return 1

    exit_code = 0
    if args.mode in {"sync", "generate"}:
        exit_code = generate_docs(repo_root, include_installed=args.include_installed) or exit_code
    if args.mode in {"sync", "build"}:
        exit_code = build_docs(repo_root) or exit_code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())