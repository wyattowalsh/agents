"""Ensure harness fixture manifest pytest -k selectors collect at least one test."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_manifest(rel_path: str) -> dict:
    return __import__("json").loads((ROOT / rel_path).read_text(encoding="utf-8"))


def _pytest_k_selector(cmd: str) -> tuple[str, str] | None:
    """Return (test_file_rel, k_expr) when cmd is a pytest invocation with -k."""
    if "pytest " not in cmd or "-k " not in cmd:
        return None
    file_match = re.search(r"pytest\s+([^\s]+\.py)", cmd)
    k_match = re.search(r"-k\s+(['\"]?)(.+?)\1(?:\s|$)", cmd)
    if not file_match or not k_match:
        return None
    return file_match.group(1), k_match.group(2).strip("'\"")


def test_rollback_validation_commands_collect_at_least_one_test() -> None:
    """Manifest rollback pytest commands must collect tests (prevents exit-code-5 drift)."""
    fixture_support = _load_manifest("planning/manifests/harness-fixture-support.json")
    failures: list[str] = []

    for rec in fixture_support["records"]:
        harness_id = rec["harness_id"]
        for cmd in rec.get("validation_commands", []):
            if "test_harness_rollback_fixtures.py" not in cmd:
                continue
            parsed = _pytest_k_selector(cmd)
            if parsed is None:
                failures.append(f"{harness_id}: rollback command missing pytest -k: {cmd}")
                continue
            test_rel, k_expr = parsed
            test_path = ROOT / test_rel
            proc = subprocess.run(
                ["uv", "run", "pytest", str(test_path), "-q", "-k", k_expr, "--collect-only"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            combined = proc.stdout + proc.stderr
            if proc.returncode == 5 or "no tests collected" in combined.lower():
                failures.append(f"{harness_id}: no tests collected for -k {k_expr!r}")
                continue
            if proc.returncode != 0:
                failures.append(
                    f"{harness_id}: collect failed for -k {k_expr!r} (exit {proc.returncode}): {combined.strip()}"
                )

    if failures:
        pytest.fail("\n".join(failures))