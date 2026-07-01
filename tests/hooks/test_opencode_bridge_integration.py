"""Integration tests for OpenCode wagents hook bridge deny propagation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "hooks" / "run-wagents-hook"


def _run_policy(policy_id: str, payload: dict) -> tuple[int, str]:
    completed = subprocess.run(
        [str(RUNNER), policy_id, "--harness", "opencode"],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )
    return completed.returncode, completed.stdout.strip()


def test_bridge_read_policy_id_denies_env_read() -> None:
    code, stdout = _run_policy(
        "cursor-before-read-file-guard",
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "read",
            "tool_input": {"path": ".env"},
            "cwd": str(REPO_ROOT),
        },
    )
    assert code == 0
    decision = json.loads(stdout)
    assert decision["permission"] == "deny"


def test_bridge_write_policy_denies_protected_path() -> None:
    code, stdout = _run_policy(
        "cursor-protected-file-guard",
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "write",
            "tool_input": {"file_path": ".env"},
            "cwd": str(REPO_ROOT),
        },
    )
    assert code == 0
    decision = json.loads(stdout)
    assert decision["permission"] == "deny"


def test_bridge_shell_policy_denies_destructive_command() -> None:
    code, stdout = _run_policy(
        "cursor-destructive-shell-guard",
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "bash",
            "tool_input": {"command": "rm -rf /"},
            "cwd": str(REPO_ROOT),
        },
    )
    assert code == 0
    decision = json.loads(stdout)
    assert decision["permission"] == "deny"


def test_bridge_git_push_force_denies_via_git_commit_push_guard() -> None:
    code, stdout = _run_policy(
        "git-commit-push-guard",
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "bash",
            "tool_input": {"command": "git push --force origin main"},
            "cwd": str(REPO_ROOT),
        },
    )
    assert code == 0
    decision = json.loads(stdout)
    assert decision["permission"] == "deny"
