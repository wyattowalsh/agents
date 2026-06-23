from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "wagents-hook.py"
SPEC = importlib.util.spec_from_file_location("wagents_hook", HOOK_PATH)
assert SPEC
assert SPEC.loader
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
        monkeypatch.setenv("RESEARCH_SKILL_ACTIVE", "1")
    else:
        monkeypatch.delenv("RESEARCH_SKILL_ACTIVE", raising=False)
    stdout = CaptureStream()
    stderr = CaptureStream()
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)
    code = wagents_hook.main(args)
    return code, stdout.value, stderr.value


def test_hook_registry_wagents_policies_are_implemented():
    registry = json.loads((Path(__file__).parent.parent / "config" / "hook-registry.json").read_text(encoding="utf-8"))

    policy_ids = {
        command.split("wagents-hook.py ", 1)[1].split()[0]
        for hook in registry["hooks"]
        for command in [hook.get("command", "")]
        if "wagents-hook.py " in command
    }

    assert policy_ids <= set(wagents_hook.POLICIES)


def test_codex_session_start_context_returns_additional_context(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(wagents_hook, "_git_session_context", lambda cwd: f"cwd={cwd}; branch=main; dirty_paths=0")

    code, stdout, stderr = run_hook(
        monkeypatch,
        {"session_id": "s1", "hook_event_name": "SessionStart", "cwd": str(Path(__file__).parent.parent)},
        ["codex-session-start-context", "--harness", "codex"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "managed hooks source=config/hook-registry.json" in payload["hookSpecificOutput"]["additionalContext"]


def test_codex_always_on_destructive_shell_guard_blocks_git_reset(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, _stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "git reset --hard"},
        },
        ["codex-destructive-shell-guard", "--harness", "codex"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "git reset --hard" in payload["hookSpecificOutput"]["permissionDecisionReason"]


def test_codex_protected_file_guard_blocks_secret_path(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, _stderr = run_hook(
        monkeypatch,
        {"session_id": "s1", "hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": ".env"}},
        ["codex-protected-file-guard", "--harness", "codex"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "secret-bearing" in payload["hookSpecificOutput"]["permissionDecisionReason"]


def test_codex_permission_request_guard_uses_permission_decision_shape(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, _stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PermissionRequest",
            "tool_name": "Bash",
            "tool_input": {"command": "git clean -fd"},
        },
        ["codex-permission-request-guard", "--harness", "codex"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert payload["hookSpecificOutput"]["hookEventName"] == "PermissionRequest"
    assert payload["hookSpecificOutput"]["decision"]["behavior"] == "deny"


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


def test_research_skill_hooks_are_registry_projected():
    skill = (Path(__file__).parent.parent / "skills" / "research" / "SKILL.md").read_text(encoding="utf-8")

    frontmatter = skill.split("---", 2)[1]
    assert "hooks:" not in frontmatter
    registry = (Path(__file__).parent.parent / "config" / "hook-registry.json").read_text(encoding="utf-8")
    assert "research-readonly-write-guard" in registry
    assert "research-stop-verifier" in registry


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


def test_codex_destructive_shell_guard_denies_critical_remove(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, _stderr = run_hook(
        monkeypatch,
        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "rm -rf /Users"}},
        ["codex-destructive-shell-guard", "--harness", "codex"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert payload["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "critical path" in payload["hookSpecificOutput"]["permissionDecisionReason"]


def test_cursor_destructive_shell_guard_uses_native_permission_shape(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {"hook_event_name": "preToolUse", "tool_name": "Bash", "tool_input": {"command": "git reset --hard"}},
        ["cursor-destructive-shell-guard", "--harness", "cursor"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert payload == {
        "permission": "deny",
        "user_message": "git reset --hard is blocked because it destroys uncommitted work.",
        "agent_message": "git reset --hard is blocked because it destroys uncommitted work.",
    }


def test_cursor_stop_truth_gate_returns_followup_message(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "stop",
            "last_assistant_message": "Implemented the Cursor adapter changes in wagents/platforms/cursor.py.",
        },
        ["cursor-stop-truth-gate", "--harness", "cursor"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert "validation evidence" in payload["followup_message"]


def test_codex_protected_file_guard_blocks_apply_patch_secret(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, _stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": {"patch": "*** Begin Patch\n*** Update File: .env\n+TOKEN=secret\n*** End Patch\n"},
        },
        ["codex-protected-file-guard", "--harness", "codex"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "secret-bearing" in payload["hookSpecificOutput"]["permissionDecisionReason"]


def test_codex_protected_file_guard_blocks_bash_lockfile_write(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, _stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "printf '{}' > package-lock.json"},
        },
        ["codex-protected-file-guard", "--harness", "codex"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "Lock files" in payload["hookSpecificOutput"]["permissionDecisionReason"]


def test_codex_protected_file_guard_blocks_mcp_style_path(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, _stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "mcp__filesystem__write_file",
            "tool_input": {"arguments": {"path": "../outside.txt", "content": "data"}},
        },
        ["codex-protected-file-guard", "--harness", "codex"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "Path traversal" in payload["hookSpecificOutput"]["permissionDecisionReason"]


def test_codex_permission_request_guard_denies_high_risk_request(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PermissionRequest",
            "tool_name": "Bash",
            "tool_input": {"command": "git reset --hard"},
        },
        ["codex-permission-request-guard", "--harness", "codex"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert payload == {
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {
                "behavior": "deny",
                "message": "git reset --hard is blocked because it destroys uncommitted work.",
            },
        }
    }


def test_codex_permission_request_guard_preserves_normal_approval_flow(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PermissionRequest",
            "tool_name": "Bash",
            "tool_input": {"command": "python -m pytest tests/test_wagents_hook.py"},
        },
        ["codex-permission-request-guard", "--harness", "codex"],
    )

    assert code == 0
    assert stdout == ""
    assert stderr == ""


def test_codex_post_tool_verifier_reports_lightweight_quality_failures(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    target = tmp_path / "broken.json"
    target.write_text("{", encoding="utf-8")

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PostToolUse",
            "tool_name": "apply_patch",
            "tool_input": {"patch": "*** Begin Patch\n*** Update File: broken.json\n+{\n*** End Patch\n"},
            "cwd": str(tmp_path),
        },
        ["codex-post-tool-verify-context", "--harness", "codex"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert "post-edit quality context" in context
    assert "Fast quality checks found issues" in context
    assert "json failed" in context


def test_codex_stop_truth_gate_blocks_code_claim_without_validation(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "Stop",
            "last_assistant_message": "Implemented the hook changes in hooks/wagents-hook.py.",
        },
        ["codex-stop-truth-gate", "--harness", "codex"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert payload["decision"] == "block"
    assert "validation evidence" in payload["reason"]


def test_codex_stop_truth_gate_allows_explicit_validation_status(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "Stop",
            "last_assistant_message": (
                "Implemented the hook changes.\n\nValidation: uv run pytest tests/test_wagents_hook.py -q"
            ),
        },
        ["codex-stop-truth-gate", "--harness", "codex"],
    )

    assert code == 0
    assert stdout == ""
    assert stderr == ""


def test_codex_stop_truth_gate_allows_generic_non_code_addition(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "Stop",
            "last_assistant_message": "Added more candidates to the approval queue.",
        },
        ["codex-stop-truth-gate", "--harness", "codex"],
    )

    assert code == 0
    assert stdout == ""
    assert stderr == ""


def test_codex_stop_truth_gate_skips_recursive_stop(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "Stop",
            "stop_hook_active": True,
            "last_assistant_message": "Implemented the hook changes.",
        },
        ["codex-stop-truth-gate", "--harness", "codex"],
    )

    assert code == 0
    assert stdout == ""
    assert stderr == ""


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


def test_shell_write_guard_blocks_allowed_token_comment_bypass(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, _stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "echo data > hooks/generated.py # journal-store.py"},
            "cwd": str(Path(__file__).parent.parent),
        },
        ["research-readonly-write-guard", "--harness", "codex"],
        env_active=True,
    )

    payload = json.loads(stdout)
    assert code == 0
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_shell_write_guard_blocks_journal_token_on_write_api(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, _stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "python -c \"open('hooks/generated.py', 'w')\" journal-store.py"},
        },
        ["research-readonly-write-guard", "--harness", "codex"],
        env_active=True,
    )

    payload = json.loads(stdout)
    assert code == 0
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_shell_write_guard_blocks_compound_tee_source_write(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, _stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "printf data | tee hooks/generated.py"},
        },
        ["research-readonly-write-guard", "--harness", "codex"],
        env_active=True,
    )

    payload = json.loads(stdout)
    assert code == 0
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_shell_write_guard_allows_research_state_redirection(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    target = tmp_path / ".codex" / "research" / "notes.jsonl"

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": f"echo data > {target}"},
            "cwd": str(Path(__file__).parent.parent),
        },
        ["research-readonly-write-guard", "--harness", "codex"],
        env_active=True,
    )

    assert code == 0
    assert stdout == ""
    assert stderr == ""


def test_shell_write_guard_allows_dev_null_redirection(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "echo data > /dev/null"},
        },
        ["research-readonly-write-guard", "--harness", "codex"],
        env_active=True,
    )

    assert code == 0
    assert stdout == ""
    assert stderr == ""


def test_shell_write_guard_allows_direct_journal_store_invocation(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "uv run python skills/research/scripts/journal-store.py save --project demo"},
        },
        ["research-readonly-write-guard", "--harness", "codex"],
        env_active=True,
    )

    assert code == 0
    assert stdout == ""
    assert stderr == ""


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


def test_codex_stop_verifier_failure_requests_continuation(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    class Proc:
        returncode = 1
        stdout = ""
        stderr = "Need one more verification pass."

    monkeypatch.setattr(wagents_hook.subprocess, "run", lambda *args, **kwargs: Proc())

    code, stdout, stderr = run_hook(
        monkeypatch,
        {"session_id": "s1", "hook_event_name": "Stop"},
        ["research-stop-verifier", "--harness", "codex"],
        env_active=True,
    )

    payload = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert payload == {"decision": "block", "reason": "Need one more verification pass."}
