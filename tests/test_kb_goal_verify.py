"""Contract tests for kb-research-ingest goal verification (shipped goal-verify.sh)."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
KB_ROOT = REPO_ROOT / "kb"
GOAL_VERIFY = REPO_ROOT / "kb" / "activity" / "goal-verify.sh"
SCRATCH_DEFAULT = Path(
    "/var/folders/z9/yr58561n1rj8_lqtzwkjt24m0000gp/T/grok-goal-cd5f675df757/implementer"
)


def _run_goal_verify(*, scratch: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["SCRATCH"] = str(scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        ["bash", str(GOAL_VERIFY)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def _parse_summary(scratch: Path) -> dict[str, str]:
    text = (scratch / "verification-summary.txt").read_text(encoding="utf-8")
    return dict(re.findall(r"^([a-z0-9_]+): (.+)$", text, re.MULTILINE))


def test_kb_lint_issue_count_zero():
    result = subprocess.run(
        ["uv", "run", "python", "skills/nerdbot/scripts/kb_lint.py", "--root", "kb", "--fail-on", "warning"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["summary"]["issue_count"] == 0


def test_coverage_has_no_partial_rows():
    coverage = (KB_ROOT / "indexes" / "coverage.md").read_text(encoding="utf-8")
    assert "| partial |" not in coverage


def test_source_map_count_is_153():
    source_map = (KB_ROOT / "indexes" / "source-map.md").read_text(encoding="utf-8")
    match = re.search(r"^source_count: (\d+)$", source_map, re.MULTILINE)
    assert match is not None
    assert int(match.group(1)) == 153


def test_macro_wave_count_at_least_30():
    log = (KB_ROOT / "activity" / "log.md").read_text(encoding="utf-8")
    wave_lines = [line for line in log.splitlines() if re.match(r"^### \[2026-06-25\] Wave \d+", line)]
    assert len(wave_lines) >= 30


def test_log_has_no_goal_closure_wave_header_pollution():
    log = (KB_ROOT / "activity" / "log.md").read_text(encoding="utf-8")
    assert "### [2026-06-29] Goal closure" not in log


def test_goal_verify_produces_passing_summary(tmp_path: Path):
    result = _run_goal_verify(scratch=tmp_path)
    assert result.returncode == 0, result.stderr or result.stdout
    summary = _parse_summary(tmp_path)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    assert summary["verification_tree"] == head
    assert summary["ac2_partials"] == "match_count: 0"
    assert summary["step2_issue_count"] == "issue_count: 0"
    assert summary["ac1_delivered_scope_violations"] == "delivered_scope_violations: 0"
    assert "source_count: 153" in summary["source_map_source_count"]

    worktree = (tmp_path / "worktree-scope.txt").read_text(encoding="utf-8")
    assert "unrelated_dirty_paths: 0" in worktree


@pytest.mark.parametrize("artifact", ["kb-lint.txt", "commit-evidence.txt", "delivered-commits-audit.txt"])
def test_goal_verify_writes_required_artifacts(tmp_path: Path, artifact: str):
    _run_goal_verify(scratch=tmp_path)
    assert (tmp_path / artifact).is_file()