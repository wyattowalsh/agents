"""Fail-closed behavior when enforce-tier policy modules cannot load."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

HOOK_PATH = Path(__file__).resolve().parents[2] / "hooks" / "wagents-hook.py"
SPEC = importlib.util.spec_from_file_location("wagents_hook_enforce", HOOK_PATH)
assert SPEC is not None
assert SPEC.loader is not None
wagents_hook = importlib.util.module_from_spec(SPEC)
sys.modules["wagents_hook_enforce"] = wagents_hook
SPEC.loader.exec_module(wagents_hook)


class CaptureStream:
    def __init__(self) -> None:
        self.value = ""

    def write(self, text: str) -> None:
        self.value += text

    def flush(self) -> None:
        pass


def _run(monkeypatch, payload: dict, args: list[str]) -> tuple[int, str]:
    monkeypatch.setattr(sys, "stdin", type("In", (), {"read": lambda self: json.dumps(payload)})())
    stdout = CaptureStream()
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", CaptureStream())
    code = wagents_hook.main(args)
    return code, stdout.value


def test_enforce_read_guard_fails_closed_when_module_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(wagents_hook, "evaluate_before_read_file", None)
    code, stdout = _run(
        monkeypatch,
        {"hook_event_name": "BeforeReadFile", "tool_input": {"path": "README.md"}},
        ["cursor-before-read-file-guard", "--harness", "cursor"],
    )
    payload = json.loads(stdout)
    assert code == 0
    assert payload["permission"] == "deny"
    assert "failed to load" in payload["user_message"]


def test_enforce_git_guard_fails_closed_when_module_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(wagents_hook, "evaluate_git_commit_push", None)
    code, stdout = _run(
        monkeypatch,
        {"hook_event_name": "PreToolUse", "tool_name": "bash", "tool_input": {"command": "git push"}},
        ["git-commit-push-guard", "--harness", "codex"],
    )
    payload = json.loads(stdout)
    assert code == 0
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_enforce_policy_ids_loaded_from_registry():
    assert "cursor-before-read-file-guard" in wagents_hook.ENFORCE_POLICY_IDS
    assert "git-commit-push-guard" in wagents_hook.ENFORCE_POLICY_IDS
    assert "cursor-before-shell-execution-guard" in wagents_hook.ENFORCE_POLICY_IDS


def test_enforce_shell_guard_fails_closed_on_git_push_when_module_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(wagents_hook, "evaluate_git_commit_push", None)
    code, stdout = _run(
        monkeypatch,
        {
            "hook_event_name": "BeforeShellExecution",
            "command": "git push origin main",
        },
        ["cursor-before-shell-execution-guard", "--harness", "cursor"],
    )
    payload = json.loads(stdout)
    assert code == 0
    assert payload["permission"] == "deny"
    assert "failed to load" in payload["user_message"]


@pytest.mark.parametrize(
    ("harness", "deny_key", "deny_value"),
    [
        ("cursor", "permission", "deny"),
        ("opencode", "permission", "deny"),
        ("grok-build", "decision", "block"),
    ],
)
def test_enforce_shell_guard_fails_closed_across_harnesses(
    monkeypatch, tmp_path, harness, deny_key, deny_value
):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(wagents_hook, "evaluate_git_commit_push", None)
    code, stdout = _run(
        monkeypatch,
        {
            "hook_event_name": "BeforeShellExecution",
            "command": "git push origin main",
        },
        ["cursor-before-shell-execution-guard", "--harness", harness],
    )
    payload = json.loads(stdout)
    assert code == 0
    assert payload[deny_key] == deny_value


def test_enforce_shell_guard_allows_git_status_when_module_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(wagents_hook, "evaluate_git_commit_push", None)
    code, stdout = _run(
        monkeypatch,
        {
            "hook_event_name": "BeforeShellExecution",
            "command": "git status",
        },
        ["cursor-before-shell-execution-guard", "--harness", "cursor"],
    )
    assert code == 0
    assert json.loads(stdout) == {"permission": "allow"}
