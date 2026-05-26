#!/usr/bin/env python3
"""Read-only project preflight for new-project workflows."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

SECRET_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "kaggle.json",
    "credentials.json",
    "auth.json",
    "secrets.toml",
}


def exists(path: Path, *parts: str) -> bool:
    return path.joinpath(*parts).exists()


def git_status(path: Path) -> tuple[bool, bool]:
    result = subprocess.run(
        ["git", "-C", str(path), "status", "--short"],
        check=False,
        text=True,
        capture_output=True,
    )
    return result.returncode == 0, bool(result.stdout.strip())


def detect(path: Path) -> dict:
    repo_exists, dirty_git = git_status(path)
    stacks: list[str] = []
    package_managers: list[str] = []
    docs_roots: list[str] = []
    agent_files: list[str] = []
    cloud_configs: list[str] = []
    risk_flags: list[str] = []
    secret_placeholders: list[str] = []

    if exists(path, "pyproject.toml"):
        stacks.append("python")
    if exists(path, "package.json"):
        stacks.append("node")
    if exists(path, "pnpm-lock.yaml"):
        package_managers.append("pnpm")
    if exists(path, "package-lock.json"):
        package_managers.append("npm")
    if exists(path, "uv.lock") or exists(path, "pyproject.toml"):
        package_managers.append("uv")

    for candidate in ("docs", "apps/docs", "website"):
        root = path / candidate
        if root.exists() and (root / "astro.config.mjs").exists() or (root / "astro.config.ts").exists():
            docs_roots.append(candidate)
        elif root.exists() and any(root.iterdir()):
            docs_roots.append(candidate)
            risk_flags.append("existing-docs-root")

    for candidate in ("AGENTS.md", "CLAUDE.md", "opencode.json"):
        if exists(path, candidate):
            agent_files.append(candidate)

    for candidate in ("wrangler.jsonc", "vercel.json", "supabase/config.toml", "docker-compose.yml", "agentcore.json"):
        if exists(path, *candidate.split("/")):
            cloud_configs.append(candidate)

    for candidate in SECRET_NAMES:
        if exists(path, candidate):
            secret_placeholders.append(candidate)
            risk_flags.append("secret-like-file-present")

    if dirty_git:
        risk_flags.append("dirty-worktree")

    return {
        "ok": True,
        "path": str(path),
        "repo_exists": repo_exists,
        "dirty_git": dirty_git,
        "detected_stack": sorted(set(stacks)),
        "package_managers": sorted(set(package_managers)),
        "docs_roots": sorted(set(docs_roots)),
        "existing_agent_files": sorted(set(agent_files)),
        "cloud_configs": sorted(set(cloud_configs)),
        "secret_like_files_present": sorted(set(secret_placeholders)),
        "risk_flags": sorted(set(risk_flags)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run read-only project preflight.")
    parser.add_argument("--path", default=".", help="Target project path")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()

    result = detect(Path(args.path).resolve())
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("ok")
        print(", ".join(result["risk_flags"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
