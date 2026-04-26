from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "wagents-hook.py"
SPEC = importlib.util.spec_from_file_location("wagents_hook", HOOK_PATH)
assert SPEC and SPEC.loader
wagents_hook = importlib.util.module_from_spec(SPEC)
sys.modules["wagents_hook"] = wagents_hook
SPEC.loader.exec_module(wagents_hook)


class CaptureStream:
    def __init__(self) -> None:
        self.value = ""

    def write(self, text: str) -> None:
        self.value += text

    def flush(self) -> None:
        pass


def run_hook(monkeypatch, payload: dict, args: list[str], env_active: bool = False) -> tuple[int, str, str]:
    monkeypatch.setattr(sys, "stdin", type("In", (), {"read": lambda self: json.dumps(payload)})())
    if env_active:
        monkeypatch.setenv("WAGENTS_RESEARCH_ACTIVE", "1")
    else:
        monkeypatch.delenv("WAGENTS_RESEARCH_ACTIVE", raising=False)
    stdout = CaptureStream()
    stderr = CaptureStream()
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)
    code = wagents_hook.main(args)
    return code, stdout.value, stderr.value


def test_prompt_triage_activates_research_context(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, _stderr = run_hook(
        monkeypatch,
        {"session_id": "s1", "hook_event_name": "UserPromptSubmit", "prompt": "agents:research hook logic SOTA"},
        ["research-prompt-triage-context", "--harness", "codex"],
    )

    assert code == 0
    assert "Research hook active" in stdout
    assert list((tmp_path / ".codex" / "research" / "hook-state").glob("*.json"))


def test_copilot_readonly_guard_denies_write_when_active(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, _stderr = run_hook(
        monkeypatch,
        {"toolName": "edit", "toolArgs": json.dumps({"path": "src/app.py"}), "sessionId": "s1"},
        ["research-readonly-write-guard", "--harness", "github-copilot"],
        env_active=True,
    )

    payload = json.loads(stdout)
    assert code == 0
    assert payload["permissionDecision"] == "deny"
    assert "read-only" in payload["permissionDecisionReason"]


def test_claude_readonly_guard_blocks_with_exit_2(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": "README.md"}},
        ["research-readonly-write-guard", "--harness", "claude-code"],
        env_active=True,
    )

    assert code == 2
    assert stdout == ""
    assert "read-only" in stderr


def test_codex_dangerous_shell_guard_denies_recursive_remove(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, _stderr = run_hook(
        monkeypatch,
        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/research"}},
        ["research-dangerous-shell-guard", "--harness", "codex"],
        env_active=True,
    )

    payload = json.loads(stdout)
    assert code == 0
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "recursive remove" in payload["hookSpecificOutput"]["permissionDecisionReason"]
    ledger = next((tmp_path / ".codex" / "research" / "hook-ledger").glob("*.jsonl"))
    record = json.loads(ledger.read_text(encoding="utf-8").splitlines()[0])
    assert record["decision"] == "deny"
    assert record["session_id_hash"]


def test_inactive_guard_records_allow_decision(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "README.md"},
        },
        ["research-readonly-write-guard", "--harness", "codex"],
    )

    assert code == 0
    assert stdout == ""
    assert stderr == ""
    ledger = next((tmp_path / ".codex" / "research" / "hook-ledger").glob("*.jsonl"))
    record = json.loads(ledger.read_text(encoding="utf-8").splitlines()[0])
    assert record["decision"] == "allow"
    assert record["policy"] == "research-readonly-write-guard"


def test_gemini_evidence_ledger_records_urls(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, _stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "AfterTool",
            "tool_name": "web_search",
            "tool_response": {"llmContent": "See https://example.com/research and https://example.com/research."},
        },
        ["research-evidence-ledger", "--harness", "gemini-cli"],
        env_active=True,
    )

    assert code == 0
    assert stdout == ""
    ledger = next((tmp_path / ".gemini" / "research" / "hook-ledger").glob("*.jsonl"))
    record = json.loads(ledger.read_text(encoding="utf-8"))
    assert record["urls"] == ["https://example.com/research"]


def test_stop_verifier_skips_recursive_payload(monkeypatch):
    code, stdout, stderr = run_hook(
        monkeypatch,
        {"stop_hook_active": True},
        ["research-stop-verifier", "--harness", "codex"],
        env_active=True,
    )

    assert code == 0
    assert stdout == ""
    assert stderr == ""
