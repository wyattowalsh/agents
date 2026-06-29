"""Contract tests for kb-research-ingest goal verification (shipped goal-verify.sh)."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
KB_ROOT = REPO_ROOT / "kb"
GOAL_VERIFY = REPO_ROOT / "kb" / "activity" / "goal-verify.sh"
GOAL_SCOPE_RESET = REPO_ROOT / "kb" / "activity" / "goal-scope-reset.sh"
WAVE_ONE_SUBJECT = "feat(kb): wave 01"
SCRATCH_DEFAULT = Path(
    "/var/folders/z9/yr58561n1rj8_lqtzwkjt24m0000gp/T/grok-goal-cd5f675df757/implementer"
)


def _run_goal_scope_reset() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(GOAL_SCOPE_RESET)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
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


def _save_pytest_evidence(name: str, content: str) -> None:
    SCRATCH_DEFAULT.mkdir(parents=True, exist_ok=True)
    (SCRATCH_DEFAULT / name).write_text(content, encoding="utf-8")


def test_kb_lint_issue_count_zero():
    result = subprocess.run(
        ["uv", "run", "python", "skills/nerdbot/scripts/kb_lint.py", "--root", "kb", "--fail-on", "warning"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    _save_pytest_evidence("pytest-kb-lint.txt", result.stdout + result.stderr)
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
    assert "122" not in source_map


def test_kb_tree_never_cites_122_source_count():
    for path in KB_ROOT.rglob("*"):
        if path.suffix not in {".md", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        assert "source_count: 122" not in text
        assert "122 source-map rows" not in text.lower()


def test_plan_step4_header_count_at_least_10():
    log = (KB_ROOT / "activity" / "log.md").read_text(encoding="utf-8")
    header_count = sum(1 for line in log.splitlines() if line.startswith("### ["))
    assert header_count >= 10


def test_macro_wave_count_at_least_30():
    log = (KB_ROOT / "activity" / "log.md").read_text(encoding="utf-8")
    wave_lines = [line for line in log.splitlines() if re.match(r"^### \[2026-06-25\] Wave \d+", line)]
    assert len(wave_lines) >= 30


def test_all_feat_kb_wave_commits_touch_kb_only():
    result = subprocess.run(
        [
            "git",
            "log",
            "--format=%H",
            "--grep=feat(kb): wave",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    violations: list[str] = []
    for sha in result.stdout.splitlines():
        sha = sha.strip()
        if not sha:
            continue
        names = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.splitlines()
        non_kb = [name for name in names if name and not name.startswith("kb/")]
        if non_kb:
            subject = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%s", sha],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            ).stdout
            violations.append(f"{sha} {subject}: {non_kb}")
    _save_pytest_evidence("pytest-wave-scope-full.txt", "\n".join(violations) or "feat_kb_wave_scope_violations: 0")
    assert not violations


def test_log_has_no_goal_closure_wave_header_pollution():
    log = (KB_ROOT / "activity" / "log.md").read_text(encoding="utf-8")
    assert "### [2026-06-29] Goal closure" not in log


def test_goal_verify_produces_passing_summary(tmp_path: Path):
    reset = _run_goal_scope_reset()
    assert reset.returncode == 0, reset.stderr or reset.stdout
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
    assert summary["ac1_goal_window_non_kb_outstanding"] == "0"
    assert summary["ac1_feat_kb_wave_scope_violations"] == "0"
    assert int(summary["ac1_goal_window_non_kb_historical"]) > 0
    assert "source_count: 153" in summary["source_map_source_count"]
    assert int(summary["ac4_plan_step4_headers"]) >= 10
    assert int(summary["ac4_macro_waves"]) >= 30
    assert "scope_reset_prerequisite" in summary

    worktree = (tmp_path / "worktree-scope.txt").read_text(encoding="utf-8")
    assert "kb_dirty_paths: 0" in worktree
    assert "unrelated_dirty_paths: 0" in worktree
    assert summary["ac1_scope_violations"] == "scope_violations: 0"

    historical = (tmp_path / "goal-window-scope.txt").read_text(encoding="utf-8")
    assert "goal_window_historical_non_kb_commits:" in historical
    assert "scope_reset_prerequisite:" in historical

    SCRATCH_DEFAULT.mkdir(parents=True, exist_ok=True)
    for artifact in tmp_path.glob("*.txt"):
        dest = SCRATCH_DEFAULT / artifact.name
        if not dest.exists():
            dest.write_text(artifact.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.parametrize(
    "artifact",
    [
        "kb-lint.txt",
        "commit-evidence.txt",
        "delivered-commits-audit.txt",
        "goal-window-scope.txt",
        "wave-scope-full.txt",
    ],
)
def test_goal_verify_writes_required_artifacts(tmp_path: Path, artifact: str):
    _run_goal_scope_reset()
    _run_goal_verify(scratch=tmp_path)
    assert (tmp_path / artifact).is_file()


def test_wave_one_commit_exists():
    result = subprocess.run(
        ["git", "log", "--oneline", "--grep", WAVE_ONE_SUBJECT, "-1"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert WAVE_ONE_SUBJECT in result.stdout