"""Unit and dispatcher tests for Cursor Task model pin policy."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.hooks.fixtures.cursor_pin_acceptance import (
    PHASE_A_HIGH_NOOP,
    PHASE_A_HIGH_PLUS_ALT,
    PHASE_A_HIGH_PLUS_MODEL_NAME,
    PHASE_A_MODEL_ID_ONLY,
    PHASE_A_MODEL_NAME_ONLY,
    PHASE_A_OMIT,
    PHASE_A_WRONG_MODEL,
    PHASE_B_HIGH_ALLOW,
    PHASE_B_MODEL_ID_DENY,
    PHASE_B_OMIT_ALLOW,
    PHASE_B_WRONG_MODEL_DENY,
)
from wagents.hooks.policies.cursor_task_model_pin import (
    _TOOL_INPUT_MODEL_ALT_KEYS,
    CURSOR_PINNED_MODEL,
    evaluate_subagent_model_allowlist,
    is_task_tool,
    rewrite_task_input,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK_PATH = REPO_ROOT / "hooks" / "wagents-hook.py"


def _assert_no_alt_keys(payload: dict) -> None:
    for key in _TOOL_INPUT_MODEL_ALT_KEYS:
        assert key not in payload


# --- A-1 / A-2 unit contracts ---


def test_tool_input_model_alt_keys_contract() -> None:
    assert _TOOL_INPUT_MODEL_ALT_KEYS == ("modelId", "model_name")


def test_rewrite_task_input_pins_omitted_model() -> None:
    updated, changed, reason = rewrite_task_input(dict(PHASE_A_OMIT))
    assert changed is True
    assert updated["model"] == CURSOR_PINNED_MODEL
    assert updated["model"] == "cursor-grok-4.5-high"
    assert "omitted" in reason.lower() or "Pinned omitted" in reason
    _assert_no_alt_keys(updated)


def test_rewrite_task_input_pins_wrong_model() -> None:
    updated, changed, reason = rewrite_task_input(dict(PHASE_A_WRONG_MODEL))
    assert changed is True
    assert updated["model"] == "cursor-grok-4.5-high"
    assert "cursor-grok-4.5-fast" in reason
    _assert_no_alt_keys(updated)


def test_rewrite_task_input_noop_when_already_pinned() -> None:
    updated, changed, reason = rewrite_task_input(dict(PHASE_A_HIGH_NOOP))
    assert changed is False
    assert updated["model"] == "cursor-grok-4.5-high"
    assert "already pinned" in reason.lower()
    _assert_no_alt_keys(updated)


def test_rewrite_task_input_model_id_only_emits_and_clears_alt() -> None:
    updated, changed, reason = rewrite_task_input(dict(PHASE_A_MODEL_ID_ONLY))
    assert changed is True
    assert updated["model"] == CURSOR_PINNED_MODEL
    _assert_no_alt_keys(updated)
    assert "modelId" not in updated
    assert "cursor-grok-4.5-fast" in reason or CURSOR_PINNED_MODEL in reason


def test_rewrite_task_input_model_name_only_emits_and_clears_alt() -> None:
    updated, changed, reason = rewrite_task_input(dict(PHASE_A_MODEL_NAME_ONLY))
    assert changed is True
    assert updated["model"] == CURSOR_PINNED_MODEL
    _assert_no_alt_keys(updated)
    assert "composer-1" in reason or CURSOR_PINNED_MODEL in reason


def test_rewrite_task_input_high_plus_conflicting_model_id_emits() -> None:
    """A-4b: High + conflicting modelId must emit updated_input with alts cleared."""
    updated, changed, reason = rewrite_task_input(dict(PHASE_A_HIGH_PLUS_ALT))
    assert changed is True
    assert updated["model"] == CURSOR_PINNED_MODEL
    _assert_no_alt_keys(updated)
    assert "Cleared alternate" in reason or "modelId" not in updated


def test_rewrite_task_input_high_plus_model_name_emits() -> None:
    updated, changed, reason = rewrite_task_input(dict(PHASE_A_HIGH_PLUS_MODEL_NAME))
    assert changed is True
    assert updated["model"] == CURSOR_PINNED_MODEL
    _assert_no_alt_keys(updated)
    assert "Cleared alternate" in reason or CURSOR_PINNED_MODEL in reason


# --- Phase B allowlist (omit → allow) ---


@pytest.mark.parametrize(
    ("tool_input", "expect_deny"),
    [
        (PHASE_B_WRONG_MODEL_DENY, True),
        ({"model": "composer-1"}, True),
        (PHASE_B_HIGH_ALLOW, False),
        (PHASE_B_OMIT_ALLOW, False),
        (PHASE_B_MODEL_ID_DENY, True),
        ({"model": "cursor-grok-4.5-high"}, False),
        ({}, False),
    ],
)
def test_evaluate_subagent_model_allowlist(tool_input: dict, expect_deny: bool) -> None:
    reason = evaluate_subagent_model_allowlist(dict(tool_input))
    if expect_deny:
        assert reason is not None
        assert "not allowed" in reason
    else:
        assert reason is None


def test_phase_b_omit_allows() -> None:
    assert evaluate_subagent_model_allowlist(dict(PHASE_B_OMIT_ALLOW)) is None
    assert evaluate_subagent_model_allowlist({}) is None
    assert evaluate_subagent_model_allowlist(None) is None


def test_phase_b_model_id_deny() -> None:
    reason = evaluate_subagent_model_allowlist(dict(PHASE_B_MODEL_ID_DENY))
    assert reason is not None
    assert "not allowed" in reason
    assert "composer-1" in reason


@pytest.mark.parametrize("name", ["Task", "task", "TASK"])
def test_is_task_tool_true_for_task_names(name: str) -> None:
    assert is_task_tool(name) is True


@pytest.mark.parametrize("name", ["Bash", "Shell", "Write", ""])
def test_is_task_tool_false_for_non_task(name: str) -> None:
    assert is_task_tool(name) is False


# --- Dispatcher smokes ---


def _run_hook(policy: str, payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(HOOK_PATH),
            policy,
            "--harness",
            "cursor",
        ],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )


def test_dispatcher_smoke_rewrites_missing_task_model() -> None:
    payload = {
        "session_id": "fixture-cursor-task-pin",
        "hook_event_name": "preToolUse",
        "tool_name": "Task",
        "tool_input": dict(PHASE_A_OMIT),
        "cwd": str(REPO_ROOT),
    }
    completed = _run_hook("cursor-task-model-pin-rewrite", payload)
    assert completed.returncode == 0, completed.stderr
    decision = json.loads(completed.stdout)
    assert decision["permission"] == "allow"
    assert decision["updated_input"]["model"] == "cursor-grok-4.5-high"
    _assert_no_alt_keys(decision["updated_input"])


def test_dispatcher_smoke_model_id_only_emits() -> None:
    payload = {
        "session_id": "fixture-cursor-task-pin-modelid",
        "hook_event_name": "preToolUse",
        "tool_name": "Task",
        "tool_input": dict(PHASE_A_MODEL_ID_ONLY),
        "cwd": str(REPO_ROOT),
    }
    completed = _run_hook("cursor-task-model-pin-rewrite", payload)
    assert completed.returncode == 0, completed.stderr
    decision = json.loads(completed.stdout)
    assert decision["permission"] == "allow"
    assert decision["updated_input"]["model"] == CURSOR_PINNED_MODEL
    _assert_no_alt_keys(decision["updated_input"])


def test_dispatcher_smoke_high_plus_conflicting_model_id_emits() -> None:
    """A-4b dispatcher: High + conflicting modelId must emit updated_input."""
    payload = {
        "session_id": "fixture-cursor-task-pin-a4b",
        "hook_event_name": "preToolUse",
        "tool_name": "Task",
        "tool_input": dict(PHASE_A_HIGH_PLUS_ALT),
        "cwd": str(REPO_ROOT),
    }
    completed = _run_hook("cursor-task-model-pin-rewrite", payload)
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip(), "expected updated_input emit for High+conflicting modelId"
    decision = json.loads(completed.stdout)
    assert decision["permission"] == "allow"
    assert decision["updated_input"]["model"] == CURSOR_PINNED_MODEL
    _assert_no_alt_keys(decision["updated_input"])


def test_dispatcher_smoke_high_noop_no_emit() -> None:
    payload = {
        "session_id": "fixture-cursor-task-pin-noop",
        "hook_event_name": "preToolUse",
        "tool_name": "Task",
        "tool_input": dict(PHASE_A_HIGH_NOOP),
        "cwd": str(REPO_ROOT),
    }
    completed = _run_hook("cursor-task-model-pin-rewrite", payload)
    assert completed.returncode == 0, completed.stderr
    assert not completed.stdout.strip()


@pytest.mark.parametrize(
    ("model", "expect_deny"),
    [
        ("cursor-grok-4.5-fast", True),
        ("composer-1", True),
        ("composer-2.5", True),
        ("cursor-grok-4.5-high", False),
        (None, False),
    ],
)
def test_dispatcher_smoke_subagent_model_allowlist(model: str | None, expect_deny: bool) -> None:
    tool_input: dict = {"description": "Investigate pin"}
    raw: dict = {
        "session_id": "fixture-cursor-subagent-allowlist",
        "hook_event_name": "subagentStart",
        "cwd": str(REPO_ROOT),
        "tool_input": tool_input,
    }
    if model is not None:
        tool_input["model"] = model
        raw["subagent_model"] = model
    completed = _run_hook("cursor-subagent-model-allowlist", raw)
    assert completed.returncode == 0, completed.stderr
    if expect_deny:
        decision = json.loads(completed.stdout)
        assert decision.get("permission") == "deny"
        reason = str(decision.get("user_message") or decision.get("agent_message") or decision)
        assert "not allowed" in reason.lower() or "cursor-grok-4.5-high" in reason
    else:
        # allow may be empty stdout / exit 0 with no deny payload
        if completed.stdout.strip():
            decision = json.loads(completed.stdout)
            assert decision.get("permission", "allow") in {"allow", None} or "permission" not in decision


def test_dispatcher_smoke_phase_b_model_id_deny() -> None:
    raw = {
        "session_id": "fixture-cursor-subagent-modelid-deny",
        "hook_event_name": "subagentStart",
        "cwd": str(REPO_ROOT),
        "tool_input": dict(PHASE_B_MODEL_ID_DENY),
    }
    completed = _run_hook("cursor-subagent-model-allowlist", raw)
    assert completed.returncode == 0, completed.stderr
    decision = json.loads(completed.stdout)
    assert decision.get("permission") == "deny"


def test_dispatcher_smoke_phase_b_omit_allow() -> None:
    raw = {
        "session_id": "fixture-cursor-subagent-omit-allow",
        "hook_event_name": "subagentStart",
        "cwd": str(REPO_ROOT),
        "tool_input": dict(PHASE_B_OMIT_ALLOW),
    }
    completed = _run_hook("cursor-subagent-model-allowlist", raw)
    assert completed.returncode == 0, completed.stderr
    if completed.stdout.strip():
        decision = json.loads(completed.stdout)
        assert decision.get("permission", "allow") != "deny"
