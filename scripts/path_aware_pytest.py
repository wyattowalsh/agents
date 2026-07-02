#!/usr/bin/env python3
"""Path-aware pytest selection based on git diff.

Maps changed repository paths to a focused pytest subset for fast inner loops.
When no mapping matches, falls back to a small core smoke bundle.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

CORE_SMOKE_TESTS = (
    "tests/test_parsing.py",
    "tests/test_validate_repo.py",
    "tests/test_cli_failure_paths.py",
)

DEFAULT_FALLBACK = (
    *CORE_SMOKE_TESTS,
    "tests/test_golden_docs.py",
    "tests/test_precommit_contract.py",
)

PATH_TEST_MAP: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("wagents/", "scripts/validate/"), ("tests/test_validate_repo.py", "tests/test_cli_failure_paths.py")),
    (("wagents/",), ("tests/test_cli_integration.py", "tests/test_wagents_self.py")),
    (
        ("skills/", "agents/"),
        (
            "tests/test_parsing.py",
            "tests/test_eval_ci_flagship.py",
            "tests/test_skill_portability.py",
        ),
    ),
    (("skills/mcp-creator/",), ("tests/test_new_mcp_scaffold.py",)),
    (("docs/",), ("tests/test_golden_docs.py", "tests/test_docs.py", "tests/test_skills_catalog_schemas.py")),
    ((".github/workflows/",), ("tests/test_github_workflows.py", "tests/test_precommit_contract.py")),
    (("hooks/", "config/hook-registry.json"), ("tests/hooks/", "tests/test_wagents_hook.py")),
    (("planning/manifests/eval-ci-flagship-skills.json",), ("tests/test_eval_ci_flagship.py",)),
    ((".pre-commit-config.yaml",), ("tests/test_precommit_contract.py",)),
)


def _git_changed_paths(base_ref: str) -> list[str]:
    for spec in (f"{base_ref}...HEAD", base_ref, "HEAD"):
        result = subprocess.run(
            ["git", "diff", "--name-only", spec],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return []


def select_tests(changed_paths: list[str]) -> list[str]:
    if not changed_paths:
        return list(DEFAULT_FALLBACK)

    selected: list[str] = []
    for prefixes, tests in PATH_TEST_MAP:
        prefix_tuple = prefixes if isinstance(prefixes, tuple) else (prefixes,)
        if any(
            any(path.startswith(prefix) or path == prefix for prefix in prefix_tuple)
            for path in changed_paths
        ):
            selected.extend(tests)

    if not selected:
        return list(DEFAULT_FALLBACK)

    deduped: list[str] = []
    seen: set[str] = set()
    for item in selected:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Select and optionally run path-aware pytest subset")
    parser.add_argument("--base-ref", default="main", help="Git ref to diff against (default: main)")
    parser.add_argument("--list-only", action="store_true", help="Print selected tests and exit")
    parser.add_argument("--pytest-args", nargs=argparse.REMAINDER, help="Extra args forwarded to pytest")
    args = parser.parse_args(argv)

    changed = _git_changed_paths(args.base_ref)
    tests = select_tests(changed)

    if args.list_only:
        for test_path in tests:
            print(test_path)
        return 0

    pytest_cmd = ["uv", "run", "pytest", *tests, "-q", "--tb=line"]
    if args.pytest_args:
        pytest_cmd.extend(args.pytest_args)

    print(f"Changed paths ({len(changed)}):", ", ".join(changed[:8]) + ("..." if len(changed) > 8 else ""))
    print("Running:", " ".join(pytest_cmd))
    result = subprocess.run(pytest_cmd, cwd=REPO_ROOT, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
