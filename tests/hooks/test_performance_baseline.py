"""Behavior-neutral baseline coverage for the ``WAGENTS_HOOK_TIMING`` sidecar.

These tests assert two invariants for the fleet-hooks-performance program's
W1 baseline wave:

1. The timing sidecar is fully opt-in: unset ``WAGENTS_HOOK_TIMING`` never
   writes anything and never changes a policy's stdout/exit code.
2. When enabled, the sidecar appends one well-formed JSON line per
   invocation without altering the wrapped policy's return value.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

HOOK_PATH = Path(__file__).parent.parent.parent / "hooks" / "wagents-hook.py"
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "hooks"


def _load_hook_module():
    spec = importlib.util.spec_from_file_location("wagents_hook_perf_baseline", HOOK_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


wagents_hook = _load_hook_module()


class CaptureStream:
    def __init__(self) -> None:
        self.value = ""

    def write(self, text: str) -> None:
        self.value += text

    def flush(self) -> None:
        pass


def _run(monkeypatch, fixture_name: str, args: list[str]) -> tuple[int, str]:
    payload = json.loads((FIXTURES_DIR / fixture_name).read_text(encoding="utf-8"))
    monkeypatch.setattr(sys, "stdin", type("In", (), {"read": lambda self: json.dumps(payload)})())
    stdout = CaptureStream()
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", CaptureStream())
    code = wagents_hook.main(args)
    return code, stdout.value


@pytest.fixture(autouse=True)
def timing_path(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook, "HOOK_TIMING_PATH", tmp_path / "hook-timing.jsonl")
    monkeypatch.delenv(wagents_hook.HOOK_TIMING_ENV, raising=False)
    return tmp_path / "hook-timing.jsonl"


def test_timing_disabled_by_default_writes_nothing(monkeypatch, timing_path):
    code, _ = _run(monkeypatch, "cursor-bash-benign.json", ["cursor-destructive-shell-guard", "--harness", "cursor"])

    assert code == 0
    assert not timing_path.exists()


def test_timing_disabled_does_not_change_deny_behavior(monkeypatch, timing_path):
    code, stdout = _run(
        monkeypatch, "cursor-bash-destructive.json", ["cursor-destructive-shell-guard", "--harness", "cursor"]
    )

    payload = json.loads(stdout)
    assert code == 0
    assert payload["permission"] == "deny"
    assert not timing_path.exists()


def test_timing_enabled_appends_one_jsonl_record(monkeypatch, timing_path):
    monkeypatch.setenv(wagents_hook.HOOK_TIMING_ENV, "1")

    code, _ = _run(monkeypatch, "cursor-bash-benign.json", ["cursor-destructive-shell-guard", "--harness", "cursor"])

    assert code == 0
    lines = timing_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["policy_id"] == "cursor-destructive-shell-guard"
    assert record["harness"] == "cursor"
    assert record["exit_code"] == 0
    assert isinstance(record["duration_ms"], (int, float))
    assert record["duration_ms"] >= 0


def test_timing_enabled_preserves_deny_decision_and_exit_code(monkeypatch, timing_path):
    monkeypatch.setenv(wagents_hook.HOOK_TIMING_ENV, "1")

    code, stdout = _run(
        monkeypatch, "opencode-bash-force-push.json", ["git-commit-push-guard", "--harness", "opencode"]
    )

    payload = json.loads(stdout)
    assert code == 0
    assert payload["permission"] == "deny"
    record = json.loads(timing_path.read_text(encoding="utf-8").strip().splitlines()[0])
    assert record["exit_code"] == 0
    assert record["policy_id"] == "git-commit-push-guard"


def test_timing_write_failure_never_raises(monkeypatch, tmp_path):
    monkeypatch.setenv(wagents_hook.HOOK_TIMING_ENV, "1")
    # Point the timing path at a location whose parent cannot be created
    # (a file masquerading as a directory) to exercise the best-effort guard.
    blocked_parent = tmp_path / "not-a-directory"
    blocked_parent.write_text("blocked", encoding="utf-8")
    monkeypatch.setattr(wagents_hook, "HOOK_TIMING_PATH", blocked_parent / "hook-timing.jsonl")

    args = ["cursor-destructive-shell-guard", "--harness", "cursor"]
    code, stdout = _run(monkeypatch, "cursor-bash-benign.json", args)

    assert code == 0
    assert json.loads(stdout)["permission"] == "allow"
    assert not wagents_hook.HOOK_TIMING_PATH.exists()


def test_record_decision_write_failure_never_raises(monkeypatch, tmp_path):
    """RV-001: an audit-ledger write failure never raises or flips the decision."""
    blocked_parent = tmp_path / "not-a-directory"
    blocked_parent.write_text("blocked", encoding="utf-8")
    monkeypatch.setattr(
        wagents_hook, "_agent_home", lambda harness: blocked_parent / "nested"
    )

    args = ["cursor-destructive-shell-guard", "--harness", "cursor"]
    code, stdout = _run(monkeypatch, "cursor-bash-benign.json", args)

    assert code == 0
    assert json.loads(stdout)["permission"] == "allow"
    assert not (blocked_parent / "nested").exists()


def test_write_state_failure_never_raises(monkeypatch, tmp_path):
    """RV-001: a hook-state write failure never raises out of the wrapped policy."""
    blocked_parent = tmp_path / "not-a-directory"
    blocked_parent.write_text("blocked", encoding="utf-8")
    monkeypatch.setattr(
        wagents_hook, "_agent_home", lambda harness: blocked_parent / "nested"
    )

    payload = wagents_hook._normalize(
        {"hook_event_name": "UserPromptSubmit", "prompt": "please research this topic thoroughly"},
        "cursor",
    )

    wagents_hook._write_state(payload)

    assert not (blocked_parent / "nested").exists()


def test_clear_state_failure_never_raises(monkeypatch, tmp_path):
    """RV-001: a hook-state clear failure (write phase) never raises."""
    payload = wagents_hook._normalize({"hook_event_name": "PreToolUse", "session_id": "clear-failure"}, "cursor")
    state_path = wagents_hook._state_path(payload)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"active": True}), encoding="utf-8")

    def _boom(*args, **kwargs):
        raise OSError("simulated write failure")

    monkeypatch.setattr(Path, "write_text", _boom)

    wagents_hook._clear_state(payload)  # must not raise


def test_record_decision_chmod_failure_never_raises(monkeypatch, tmp_path):
    """RV-001 edge case: a chmod failure after a successful write is also swallowed."""
    monkeypatch.setattr(wagents_hook, "_agent_home", lambda harness: tmp_path / "agent-home")

    def _boom(self, mode):
        raise OSError("simulated chmod failure")

    monkeypatch.setattr(Path, "chmod", _boom)

    args = ["cursor-destructive-shell-guard", "--harness", "cursor"]
    code, stdout = _run(monkeypatch, "cursor-bash-benign.json", args)

    assert code == 0
    assert json.loads(stdout)["permission"] == "allow"


def test_hook_registry_rows_render_without_timing_env():
    """Rendered harness commands never hardcode WAGENTS_HOOK_TIMING=1 (behavior-neutral default)."""
    import json as _json

    registry = _json.loads(
        (Path(__file__).parent.parent.parent / "config" / "hook-registry.json").read_text(encoding="utf-8")
    )
    for hook in registry["hooks"]:
        assert "WAGENTS_HOOK_TIMING" not in str(hook.get("command", ""))


def test_timing_forwarded_path_records_forwarded_flag(monkeypatch, timing_path):
    """RV-NEW-003: worker-socket forwards still append timing when enabled."""
    monkeypatch.setenv(wagents_hook.HOOK_TIMING_ENV, "1")

    def _fake_forward(**kwargs):
        return {"stdout": '{"permission":"allow"}\n', "exit_code": 0}

    monkeypatch.setattr(wagents_hook, "_forward_to_worker", lambda **kwargs: _fake_forward(**kwargs))

    code, stdout = _run(
        monkeypatch,
        "cursor-bash-benign.json",
        [
            "--worker-socket",
            "/tmp/missing-but-mocked.sock",
            "cursor-destructive-shell-guard",
            "--harness",
            "cursor",
        ],
    )

    assert code == 0
    assert json.loads(stdout)["permission"] == "allow"
    record = json.loads(timing_path.read_text(encoding="utf-8").strip().splitlines()[0])
    assert record["forwarded"] is True
    assert record["policy_id"] == "cursor-destructive-shell-guard"

