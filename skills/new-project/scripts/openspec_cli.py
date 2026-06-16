#!/usr/bin/env python3
"""Portable OpenSpec wrapper via npx (no repo CLI dependency)."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

OPENSPEC_PACKAGE = "@fission-ai/openspec@latest"
OPENSPEC_TELEMETRY_ENV = "OPENSPEC_TELEMETRY"


def find_repo_root(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for path in [current, *current.parents]:
        if (path / "openspec").is_dir() or (path / "skills").is_dir():
            return path
    return None


def build_argv(args: list[str], *, package: str = OPENSPEC_PACKAGE) -> list[str]:
    return ["npx", "-y", package, *args]


def run_openspec(args: list[str], *, cwd: Path, package: str = OPENSPEC_PACKAGE, capture: bool = False) -> int:
    if not shutil.which("npx"):
        print("Error: npx not found. Install Node.js >= 20.19.0 first.", file=sys.stderr)
        return 1

    argv = build_argv(args, package=package)
    env = os.environ.copy()
    env.setdefault(OPENSPEC_TELEMETRY_ENV, "0")
    result = subprocess.run(argv, cwd=cwd, env=env, check=False, capture_output=capture, text=True)
    if capture:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
    return result.returncode


def cmd_validate(repo_root: Path, package: str) -> int:
    return run_openspec(["validate", "--all", "--json"], cwd=repo_root, package=package)


def cmd_init(repo_root: Path, package: str, *, apply: bool) -> int:
    argv = ["init"]
    if apply:
        argv.append("--apply")
    return run_openspec(argv, cwd=repo_root, package=package)


def cmd_doctor(repo_root: Path, package: str) -> int:
    openspec_dir = repo_root / "openspec"
    report = {
        "package": package,
        "configExists": (openspec_dir / "config.yaml").exists(),
        "specsExists": (openspec_dir / "specs").exists(),
        "changesExists": (openspec_dir / "changes").exists(),
        "npxAvailable": shutil.which("npx") is not None,
    }
    print(json.dumps(report, indent=2))
    return 0 if report["npxAvailable"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run OpenSpec through npx")
    parser.add_argument("--package", default=OPENSPEC_PACKAGE, help="OpenSpec npm package spec")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate", help="Run openspec validate --all --json")
    init_parser = subparsers.add_parser("init", help="Run openspec init")
    init_parser.add_argument("--apply", action="store_true", help="Apply init instead of dry-run")
    subparsers.add_parser("doctor", help="Report OpenSpec project and toolchain state")

    args = parser.parse_args(argv)
    repo_root = find_repo_root()
    if repo_root is None:
        print("Could not find repo root", file=sys.stderr)
        return 1

    if args.command == "validate":
        return cmd_validate(repo_root, args.package)
    if args.command == "init":
        return cmd_init(repo_root, args.package, apply=args.apply)
    if args.command == "doctor":
        return cmd_doctor(repo_root, args.package)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())