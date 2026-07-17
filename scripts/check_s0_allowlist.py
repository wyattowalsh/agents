#!/usr/bin/env python3
# ruff: noqa
"""Fail if git changed paths are outside the S0 security closeout allowlist.

Usage:
  uv run python scripts/check_s0_allowlist.py
  git diff --name-only HEAD | uv run python scripts/check_s0_allowlist.py --stdin
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

S0_ALLOWLIST = frozenset(
    {
        "mcp/source-url-health/pyproject.toml",
        "mcp/source-url-health/server.py",
        "mcp/source-url-health/mcp_source_url_health/__init__.py",
        "mcp/source-url-health/mcp_source_url_health/server.py",
        "mcp/source-url-health/mcp_source_url_health/ssrf.py",
        "tests/test_ssrf_policy.py",
        "tests/test_pinned_httpx_client.py",
        "tests/mcp/test_source_url_health.py",
        "tests/mcp/test_source_url_health_wheel.py",
        "wagents/hooks/policies/secret_paths.py",
        "wagents/hooks/policies/protected_file_guard.py",
        "wagents/hooks/policies/__init__.py",
        "hooks/wagents-hook.py",
        "tests/hooks/test_policies_modules.py",
        "tests/test_wagents_hook.py",
        "scripts/sync_agent_stack.py",
        "scripts/validate/collectors/quarantine.py",
        "tests/test_validate_collectors.py",
        "tests/test_mcp_render_placeholders.py",
        "wagents/platforms/opencode.py",
        "wagents/platforms/base.py",
        "agents/orchestrator.md",
        "agents/performance-profiler.md",
        "agents/planner.md",
        "agents/researcher.md",
        "config/opencode-agents.json",
        ".opencode/agents/orchestrator.md",
        ".opencode/agents/performance-profiler.md",
        "docs/src/content/docs/hooks/index.mdx",
        "wagents/cli.py",
        "tests/test_external_skills_pin.py",
        "tests/test_skills_sync_pin_gate.py",
        "tests/test_agent_bash_posture.py",
        "tests/test_remediation_rg_gates.py",
        "scripts/check_s0_allowlist.py",
        "planning/manifests/full-audit-remediation-residual-2026-07.md",
        "wagents/external_skills.py",
        "platforms/opencode/plugins/wagents-hook-bridge.ts",
        "tests/test_sync_agent_stack.py",
    }
)


def _git_changed() -> list[str]:
    out = subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=REPO,
        text=True,
    )
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO,
        text=True,
    )
    paths = [p.strip() for p in (out + "\n" + untracked).splitlines() if p.strip()]
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", help="Read paths from stdin instead of git")
    parser.add_argument(
        "--s0-only",
        action="store_true",
        help="Only report violations among paths that look like S0 security edits (heuristic)",
    )
    args = parser.parse_args(argv)

    if args.stdin:
        paths = [line.strip() for line in sys.stdin if line.strip()]
    else:
        paths = _git_changed()

    # When the tree is huge, default mode reports all non-allowlisted *security-core* hits
    # if --s0-only, else all non-allowlisted paths (noisy on dirty trees).
    security_prefixes = (
        "mcp/source-url-health/",
        "wagents/hooks/policies/",
        "hooks/wagents-hook.py",
        "scripts/sync_agent_stack.py",
        "wagents/platforms/",
        "agents/orchestrator.md",
        "agents/performance-profiler.md",
        "wagents/cli.py",
        "tests/test_ssrf",
        "tests/test_mcp_render",
        "tests/test_skills_sync_pin",
        "tests/test_agent_bash",
        "tests/test_remediation_rg",
        "scripts/check_s0_allowlist.py",
        "planning/manifests/full-audit-remediation",
    )

    violations: list[str] = []
    for path in paths:
        if path in S0_ALLOWLIST:
            continue
        if args.s0_only and not any(path.startswith(p) or p in path for p in security_prefixes):
            continue
        if args.s0_only or path.startswith(security_prefixes) or path in {
            "hooks/wagents-hook.py",
            "scripts/sync_agent_stack.py",
            "wagents/cli.py",
        }:
            # For default (no --s0-only) on dirty monorepo: only fail on security-core paths outside allowlist
            if not args.s0_only:
                if not (
                    path.startswith("mcp/source-url-health/")
                    or path.startswith("wagents/hooks/policies/")
                    or path.startswith("wagents/platforms/")
                    or path in {
                        "hooks/wagents-hook.py",
                        "scripts/sync_agent_stack.py",
                        "wagents/cli.py",
                        "agents/orchestrator.md",
                        "agents/performance-profiler.md",
                        "scripts/check_s0_allowlist.py",
                    }
                    or path.startswith("tests/test_ssrf")
                    or path.startswith("tests/test_mcp_render")
                    or path.startswith("tests/test_skills_sync_pin")
                    or path.startswith("tests/test_agent_bash")
                    or path.startswith("tests/test_remediation_rg")
                    or path.startswith("tests/mcp/test_source_url")
                ):
                    continue
            violations.append(path)

    if violations:
        print("S0 allowlist violations (security-core paths not on allowlist):", file=sys.stderr)
        for path in sorted(set(violations)):
            print(f"  {path}", file=sys.stderr)
        return 1
    print("S0 allowlist check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
