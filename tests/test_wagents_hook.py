from __future__ import annotations

import importlib.util
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import cast

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
        command.split(marker, 1)[1].strip().split()[0]
        for hook in registry["hooks"]
        for command in [hook.get("command", "")]
        for marker in ("wagents-hook.py ", "{hook_runner} ")
        if marker in command
    }

    assert policy_ids <= set(wagents_hook.POLICIES)


def test_image_optimizer_registry_timeout_covers_subprocess_budget():
    registry = json.loads((Path(__file__).parent.parent / "config" / "hook-registry.json").read_text(encoding="utf-8"))

    [hook] = [entry for entry in registry["hooks"] if entry["id"] == wagents_hook.IMAGE_OPTIMIZER_POLICY_ID]

    assert hook["timeout"] == wagents_hook.IMAGE_OPTIMIZER_REGISTRY_TIMEOUT_SECONDS
    assert hook["timeout"] > wagents_hook.IMAGE_OPTIMIZER_TIMEOUT_SECONDS
    forward_budget = (
        wagents_hook.IMAGE_OPTIMIZER_REGISTRY_TIMEOUT_SECONDS
        + wagents_hook._FORWARD_TIMEOUT_MARGIN_SECONDS
    )
    assert forward_budget >= wagents_hook.IMAGE_OPTIMIZER_TIMEOUT_SECONDS


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


def test_prompt_triage_clears_research_state_on_implementation_handoff(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, _stdout, _stderr = run_hook(
        monkeypatch,
        {"session_id": "s1", "hook_event_name": "UserPromptSubmit", "prompt": "/research rtk integration"},
        ["research-prompt-triage-context", "--harness", "codex"],
    )
    assert code == 0

    code, stdout, _stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "UserPromptSubmit",
            "prompt": "continue and fix the hooks",
        },
        ["research-prompt-triage-context", "--harness", "codex"],
    )
    assert code == 0
    assert "Research hook inactive" in stdout

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


def test_prompt_triage_does_not_clear_research_state_for_research_continuation(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, _stdout, _stderr = run_hook(
        monkeypatch,
        {"session_id": "s1", "hook_event_name": "UserPromptSubmit", "prompt": "/research rtk integration"},
        ["research-prompt-triage-context", "--harness", "codex"],
    )
    assert code == 0

    for prompt in (
        "continue researching and write notes",
        "continue research and apply source filters",
        "write up findings",
        "edit the research notes",
    ):
        code, stdout, stderr = run_hook(
            monkeypatch,
            {"session_id": "s1", "hook_event_name": "UserPromptSubmit", "prompt": prompt},
            ["research-prompt-triage-context", "--harness", "codex"],
        )
        assert code == 0
        assert stdout == ""
        assert stderr == ""

        code, stdout, _stderr = run_hook(
            monkeypatch,
            {
                "session_id": "s1",
                "hook_event_name": "PreToolUse",
                "tool_name": "Edit",
                "tool_input": {"file_path": "README.md"},
            },
            ["research-readonly-write-guard", "--harness", "codex"],
        )
        payload = json.loads(stdout)
        assert code == 0
        assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_prompt_triage_does_not_clear_forced_research_mode(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "UserPromptSubmit",
            "prompt": "continue and fix the hooks",
        },
        ["research-prompt-triage-context", "--harness", "codex"],
        env_active=True,
    )
    assert code == 0
    assert stdout == ""
    assert stderr == ""

    code, stdout, _stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "README.md"},
        },
        ["research-readonly-write-guard", "--harness", "codex"],
        env_active=True,
    )
    payload = json.loads(stdout)
    assert code == 0
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


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


def test_image_input_optimizer_blocks_codex_with_retry_path(monkeypatch, tmp_path):
    home = tmp_path / "home"
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: home)
    source = work / "screenshot.png"
    optimized = work / "cache" / "optimized.jpg"
    source.write_bytes(b"placeholder")
    monkeypatch.setattr(wagents_hook, "_uv_executable", lambda: "/opt/homebrew/bin/uv")
    monkeypatch.setattr(wagents_hook, "_run_image_optimizer_batch_inprocess", lambda *_args, **_kwargs: (None, None))

    def fake_run(*_args, **_kwargs):
        return type(
            "Proc",
            (),
            {
                "returncode": 0,
                "stdout": json.dumps({
                    "status": "ok",
                    "results": [
                        {
                            "status": "optimized",
                            "fits": True,
                            "changed": True,
                            "sourcePath": str(source),
                            "optimizedPath": str(optimized),
                            "optimizedWidth": 1200,
                            "optimizedHeight": 800,
                            "optimizedBytes": 12345,
                        }
                    ],
                }),
                "stderr": "",
            },
        )()

    monkeypatch.setattr(wagents_hook.subprocess, "run", fake_run)
    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "view_image",
            "tool_input": {"image_path": str(source)},
            "cwd": str(work),
        },
        ["image-input-optimizer-guard", "--harness", "codex"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert str(optimized) in payload["hookSpecificOutput"]["permissionDecisionReason"]


def test_image_input_optimizer_preserves_inprocess_error_without_subprocess(monkeypatch, tmp_path):
    home = tmp_path / "home"
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: home)
    source = work / "screenshot.png"
    source.write_bytes(b"placeholder")
    error = "Image optimizer exhausted the hook execution budget."
    monkeypatch.setattr(wagents_hook, "_run_image_optimizer_batch_inprocess", lambda *_args, **_kwargs: (None, error))

    def fail_subprocess_fallback(*_args, **_kwargs):
        raise AssertionError("subprocess fallback should not run after an in-process optimizer error")

    monkeypatch.setattr(wagents_hook, "_run_image_optimizer_batch", fail_subprocess_fallback)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "view_image",
            "tool_input": {"image_path": str(source)},
            "cwd": str(work),
        },
        ["image-input-optimizer-guard", "--harness", "codex"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert error in payload["hookSpecificOutput"]["permissionDecisionReason"]


def test_image_input_optimizer_command_uses_uv_project(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook, "_uv_executable", lambda: "/opt/homebrew/bin/uv")

    command, error = wagents_hook._image_optimizer_command()

    assert error is None
    assert command[:5] == ["/opt/homebrew/bin/uv", "run", "--project", str(wagents_hook.REPO_ROOT), "python"]
    assert command[5:] == ["-m", "wagents.image_inputs", "--batch-json-stdin"]


def test_image_input_optimizer_trusted_uv_rejects_foreign_user_path(monkeypatch, tmp_path):
    home = tmp_path / "home"
    foreign = tmp_path / "Users" / "other" / ".local" / "bin"
    foreign.mkdir(parents=True)
    uv = foreign / "uv"
    uv.write_text("#!/bin/sh\n", encoding="utf-8")
    uv.chmod(0o755)
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: home)

    assert wagents_hook._trusted_uv_path(str(uv)) is None


def test_image_input_optimizer_trusted_uv_accepts_current_home_path(monkeypatch, tmp_path):
    home = tmp_path / "home"
    bin_dir = home / ".local" / "bin"
    bin_dir.mkdir(parents=True)
    for parent in (home, home / ".local", bin_dir):
        parent.chmod(0o700)
    uv = bin_dir / "uv"
    uv.write_text("#!/bin/sh\n", encoding="utf-8")
    uv.chmod(0o755)
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: home)

    assert wagents_hook._trusted_uv_path(str(uv)) == str(uv.resolve())


def test_image_input_optimizer_batch_command_omits_secret_context(monkeypatch, tmp_path):
    home = tmp_path / "home"
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: home)
    monkeypatch.setattr(wagents_hook, "_uv_executable", lambda: "/opt/homebrew/bin/uv")
    monkeypatch.setenv("PYTHONPATH", "SECRET_PYTHONPATH")
    monkeypatch.setenv("BASH_ENV", "SECRET_BASH_ENV")
    monkeypatch.setenv("UV_CACHE_DIR", str(tmp_path / "unsafe-uv-cache"))
    source = work / "screenshot.png"
    optimized = work / "cache" / "optimized.jpg"
    source.write_bytes(b"placeholder")
    monkeypatch.setattr(wagents_hook, "_run_image_optimizer_batch_inprocess", lambda *_args, **_kwargs: (None, None))
    captured: dict[str, object] = {}
    secret = "sk-review-secret"

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["input"] = kwargs.get("input")
        captured["env"] = kwargs.get("env")
        return type(
            "Proc",
            (),
            {
                "returncode": 0,
                "stdout": json.dumps({
                    "status": "ok",
                    "results": [
                        {
                            "status": "optimized",
                            "fits": True,
                            "changed": True,
                            "sourcePath": str(source),
                            "optimizedPath": str(optimized),
                            "optimizedWidth": 1200,
                            "optimizedHeight": 800,
                            "optimizedBytes": 12345,
                        }
                    ],
                }),
                "stderr": "",
            },
        )()

    monkeypatch.setattr(wagents_hook.subprocess, "run", fake_run)
    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "view_image",
            "tool_input": {
                "image_path": str(source),
                "headers": {"Authorization": f"Bearer {secret}"},
                "token": secret,
            },
            "cwd": str(work),
        },
        ["image-input-optimizer-guard", "--harness", "codex"],
    )

    assert code == 0
    assert stderr == ""
    assert json.loads(stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    command_text = json.dumps(captured["command"])
    input_payload = json.loads(str(captured["input"]))
    input_text = json.dumps(input_payload)
    env = captured["env"]
    assert isinstance(env, dict)
    env_map = cast("dict[str, str]", env)
    assert secret not in command_text
    assert secret not in input_text
    assert "Authorization" not in command_text
    assert "Authorization" not in input_text
    assert env_map["PYTHONPATH"] == str(wagents_hook.REPO_ROOT)
    assert "BASH_ENV" not in env_map
    assert "UV_CACHE_DIR" not in env_map
    assert input_payload["images"][0]["identity"]["size"] == source.stat().st_size


def test_image_input_optimizer_denies_with_uv_remediation_when_uv_missing(monkeypatch, tmp_path):
    home = tmp_path / "home"
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: home)
    monkeypatch.setattr(wagents_hook, "_uv_executable", lambda: None)
    monkeypatch.setattr(wagents_hook, "_run_image_optimizer_batch_inprocess", lambda *_args, **_kwargs: (None, None))
    source = work / "screenshot.png"
    source.write_bytes(b"placeholder")

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "view_image",
            "tool_input": {"image_path": str(source)},
            "cwd": str(work),
        },
        ["image-input-optimizer-guard", "--harness", "codex"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "trusted uv" in payload["hookSpecificOutput"]["permissionDecisionReason"]
    assert "uv sync" in payload["hookSpecificOutput"]["permissionDecisionReason"]


def test_image_input_optimizer_blocks_cursor_with_retry_path(monkeypatch, tmp_path):
    home = tmp_path / "home"
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: home)
    source = work / "screen.png"
    optimized = work / "cache" / "screen.jpg"
    source.write_bytes(b"placeholder")
    monkeypatch.setattr(wagents_hook, "_uv_executable", lambda: "/opt/homebrew/bin/uv")
    monkeypatch.setattr(wagents_hook, "_run_image_optimizer_batch_inprocess", lambda *_args, **_kwargs: (None, None))

    def fake_run(*_args, **_kwargs):
        return type(
            "Proc",
            (),
            {
                "returncode": 0,
                "stdout": json.dumps({
                    "status": "ok",
                    "results": [
                        {
                            "status": "optimized",
                            "fits": True,
                            "changed": True,
                            "sourcePath": str(source),
                            "optimizedPath": str(optimized),
                            "optimizedWidth": 900,
                            "optimizedHeight": 600,
                            "optimizedBytes": 9000,
                        }
                    ],
                }),
                "stderr": "",
            },
        )()

    monkeypatch.setattr(wagents_hook.subprocess, "run", fake_run)
    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "preToolUse",
            "tool_name": "view_image",
            "tool_input": {"image_path": str(source)},
            "cwd": str(work),
        },
        ["image-input-optimizer-guard", "--harness", "cursor"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert payload["permission"] == "deny"
    assert str(optimized) in payload["user_message"]


def test_image_input_optimizer_rewrites_duplicate_path_spellings_for_claude(monkeypatch, tmp_path):
    home = tmp_path / "home"
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: home)
    source = work / "screen.png"
    optimized = work / "cache" / "screen.jpg"
    source.write_bytes(b"placeholder")
    monkeypatch.setattr(wagents_hook, "_uv_executable", lambda: "/opt/homebrew/bin/uv")
    monkeypatch.setattr(wagents_hook, "_run_image_optimizer_batch_inprocess", lambda *_args, **_kwargs: (None, None))

    def fake_run(*_args, **_kwargs):
        return type(
            "Proc",
            (),
            {
                "returncode": 0,
                "stdout": json.dumps({
                    "status": "ok",
                    "results": [
                        {
                            "status": "optimized",
                            "fits": True,
                            "changed": True,
                            "sourcePath": str(source),
                            "optimizedPath": str(optimized),
                            "optimizedWidth": 900,
                            "optimizedHeight": 600,
                            "optimizedBytes": 9000,
                        }
                    ],
                }),
                "stderr": "",
            },
        )()

    monkeypatch.setattr(wagents_hook.subprocess, "run", fake_run)
    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "view_image",
            "tool_input": {"images": ["screen.png", "./screen.png", str(source)]},
            "cwd": str(work),
        },
        ["image-input-optimizer-guard", "--harness", "claude-code"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert payload["hookSpecificOutput"]["updatedInput"]["images"] == [str(optimized), str(optimized), str(optimized)]


def test_image_input_optimizer_denies_unsafe_broad_roots(monkeypatch, tmp_path):
    source = tmp_path / "screen.png"
    source.write_bytes(b"placeholder")
    monkeypatch.setenv("TMPDIR", "/")

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "view_image",
            "tool_input": {"image_path": str(source)},
            "cwd": "/",
        },
        ["image-input-optimizer-guard", "--harness", "codex"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "unsafe image root" in payload["hookSpecificOutput"]["permissionDecisionReason"]


def test_image_input_optimizer_ignores_read_on_non_image_in_repo_cwd(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    config = repo / "config.json"
    config.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(wagents_hook, "REPO_ROOT", repo)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "preToolUse",
            "tool_name": "Read",
            "tool_input": {"path": str(config)},
            "cwd": str(repo),
        },
        ["image-input-optimizer-guard", "--harness", "cursor"],
    )

    assert code == 0
    assert stdout == ""
    assert stderr == ""


def test_image_input_optimizer_blocks_read_on_oversized_repo_image(monkeypatch, tmp_path):
    from PIL import Image

    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setattr(wagents_hook, "REPO_ROOT", repo)
    source = repo / "screenshot.png"
    Image.new("RGB", (4200, 2800), (32, 96, 160)).save(source, format="PNG")
    monkeypatch.setattr(wagents_hook, "_uv_executable", lambda: "/opt/homebrew/bin/uv")
    # Exercise the subprocess fallback path (deny message shape) rather than the
    # in-process optimizer, which writes to the global wagents image-input cache.
    monkeypatch.setattr(
        wagents_hook,
        "_run_image_optimizer_batch_inprocess",
        lambda *_args, **_kwargs: (None, None),
    )

    def fake_run(*_args, **_kwargs):
        optimized = repo / "cache" / "optimized.jpg"
        return type(
            "Proc",
            (),
            {
                "returncode": 0,
                "stdout": json.dumps({
                    "status": "ok",
                    "results": [
                        {
                            "status": "optimized",
                            "fits": True,
                            "changed": True,
                            "sourcePath": str(source),
                            "optimizedPath": str(optimized),
                            "optimizedWidth": 3000,
                            "optimizedHeight": 2000,
                            "optimizedBytes": 12345,
                        }
                    ],
                }),
                "stderr": "",
            },
        )()

    monkeypatch.setattr(wagents_hook.subprocess, "run", fake_run)
    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "preToolUse",
            "tool_name": "Read",
            "tool_input": {"path": str(source)},
            "cwd": str(repo),
        },
        ["image-input-optimizer-guard", "--harness", "cursor"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert payload["permission"] == "deny"
    assert str(repo / "cache" / "optimized.jpg") in payload["user_message"]


def test_image_input_optimizer_allows_macos_style_temp_image(monkeypatch, tmp_path):
    from PIL import Image

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: home)
    source = tmp_path / "screen.png"
    Image.new("RGB", (4200, 2800), (32, 96, 160)).save(source, format="PNG")
    monkeypatch.setattr(wagents_hook, "_uv_executable", lambda: "/opt/homebrew/bin/uv")

    def fake_run(*_args, **_kwargs):
        optimized = home / "cache" / "optimized.jpg"
        return type(
            "Proc",
            (),
            {
                "returncode": 0,
                "stdout": json.dumps({
                    "status": "ok",
                    "results": [
                        {
                            "status": "optimized",
                            "fits": True,
                            "changed": True,
                            "sourcePath": str(source),
                            "optimizedPath": str(optimized),
                            "optimizedWidth": 3000,
                            "optimizedHeight": 2000,
                            "optimizedBytes": 12345,
                        }
                    ],
                }),
                "stderr": "",
            },
        )()

    monkeypatch.setattr(wagents_hook.subprocess, "run", fake_run)
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "preToolUse",
            "tool_name": "view_image",
            "tool_input": {"image_path": str(source)},
            "cwd": str(tmp_path),
        },
        ["image-input-optimizer-guard", "--harness", "cursor"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert payload["permission"] == "deny"
    assert "symlink" not in payload["user_message"].lower()


def test_image_input_optimizer_denies_symlink_source_path(monkeypatch, tmp_path):
    home = tmp_path / "home"
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: home)
    source = work / "screen.png"
    source.write_bytes(b"placeholder")
    link = work / "screen-link.png"
    link.symlink_to(source)

    def fake_run(*_args, **_kwargs):
        raise AssertionError("optimizer subprocess should not run for symlink source paths")

    monkeypatch.setattr(wagents_hook.subprocess, "run", fake_run)
    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "view_image",
            "tool_input": {"image_path": str(link)},
            "cwd": str(work),
        },
        ["image-input-optimizer-guard", "--harness", "codex"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "symlink" in payload["hookSpecificOutput"]["permissionDecisionReason"]


def test_image_input_optimizer_denies_more_than_candidate_cap(monkeypatch, tmp_path):
    home = tmp_path / "home"
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: home)
    sources = []
    for idx in range(wagents_hook.IMAGE_OPTIMIZER_MAX_CANDIDATES + 1):
        source = work / f"screen-{idx}.png"
        source.write_bytes(b"placeholder")
        sources.append(str(source))

    def fake_run(*_args, **_kwargs):
        raise AssertionError("optimizer subprocess should not run when candidate cap is exceeded")

    monkeypatch.setattr(wagents_hook.subprocess, "run", fake_run)
    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "view_image",
            "tool_input": {"images": sources},
            "cwd": str(work),
        },
        ["image-input-optimizer-guard", "--harness", "codex"],
    )

    payload = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "exceeding the per-tool limit" in payload["hookSpecificOutput"]["permissionDecisionReason"]


def test_image_input_optimizer_ignores_missing_tool_name(monkeypatch, tmp_path):
    home = tmp_path / "home"
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: home)
    source = work / "screen.png"
    source.write_bytes(b"placeholder")

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "PreToolUse",
            "tool_name": "",
            "tool_input": {"image_path": str(source)},
            "cwd": str(work),
        },
        ["image-input-optimizer-guard", "--harness", "codex"],
    )

    assert code == 0
    assert stdout == ""
    assert stderr == ""


def test_image_input_optimizer_wrapper_command_uses_uv_environment(monkeypatch, tmp_path):
    from PIL import Image

    home = tmp_path / "home"
    source = tmp_path / "screenshot.png"
    Image.new("RGB", (4200, 2800), (80, 120, 160)).save(source, format="PNG")
    bin_dir = home / ".local" / "bin"
    bin_dir.mkdir(parents=True)
    for parent in (home, home / ".local", bin_dir):
        parent.chmod(0o700)
    real_uv = shutil.which("uv")
    assert real_uv is not None
    helper = bin_dir / "fake_uv_optimizer.py"
    helper.write_text(
        """
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

payload = json.loads(sys.stdin.read() or "{}")
cache_root = Path(os.environ["HOME"]) / ".cache" / "wagents" / "image-inputs" / "test"
cache_root.mkdir(parents=True, exist_ok=True)
results = []
for index, item in enumerate(payload["images"]):
    source = Path(item["path"])
    optimized = cache_root / f"{source.stem}-{index}{source.suffix}"
    shutil.copyfile(source, optimized)
    results.append({
        "optimizedPath": str(optimized),
        "fits": True,
        "changed": True,
    })
print(json.dumps({"status": "ok", "results": results}, separators=(",", ":")))
""".lstrip(),
        encoding="utf-8",
    )
    uv = bin_dir / "uv"
    uv.write_text(
        f"#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(helper))} \"$@\"\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    monkeypatch.setenv("HOME", str(home))
    payload = {
        "session_id": "s1",
        "hook_event_name": "PreToolUse",
        "tool_name": "view_image",
        "tool_input": {"image_path": str(source)},
        "cwd": str(tmp_path),
    }

    proc = subprocess.run(
        [str(HOOK_PATH.parent / "run-wagents-hook"), "image-input-optimizer-guard", "--harness", "claude-code"],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=HOOK_PATH.parent.parent,
        timeout=60,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    response = json.loads(proc.stdout)
    assert response["hookSpecificOutput"]["permissionDecision"] == "allow"
    optimized = Path(response["hookSpecificOutput"]["updatedInput"]["image_path"])
    assert optimized.exists()
    assert home / ".cache" / "wagents" / "image-inputs" in optimized.parents


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


def test_codex_stop_truth_gate_allows_bare_ty_check(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {
            "session_id": "s1",
            "hook_event_name": "Stop",
            "last_assistant_message": (
                "Implemented the hook changes in hooks/wagents-hook.py.\n\nValidation: ty check"
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


def test_cursor_protected_file_guard_allows_with_explicit_permission(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {"hook_event_name": "preToolUse", "tool_name": "Edit", "tool_input": {"file_path": "README.md"}},
        ["cursor-protected-file-guard", "--harness", "cursor"],
    )

    assert code == 0
    assert stderr == ""
    assert json.loads(stdout) == {"permission": "allow"}


def test_cursor_readonly_write_guard_allows_with_explicit_permission_when_inactive(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {"hook_event_name": "preToolUse", "tool_name": "Edit", "tool_input": {"file_path": "README.md"}},
        ["research-readonly-write-guard", "--harness", "cursor"],
    )

    assert code == 0
    assert stderr == ""
    assert json.loads(stdout) == {"permission": "allow"}


def test_cursor_destructive_shell_guard_allows_safe_command_with_permission(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {"hook_event_name": "preToolUse", "tool_name": "Bash", "tool_input": {"command": "git status"}},
        ["cursor-destructive-shell-guard", "--harness", "cursor"],
    )

    assert code == 0
    assert stderr == ""
    assert json.loads(stdout) == {"permission": "allow"}


def test_codex_protected_file_guard_allow_stays_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": "README.md"}},
        ["codex-protected-file-guard", "--harness", "codex"],
    )

    assert code == 0
    assert stdout == ""
    assert stderr == ""


def test_cursor_image_optimizer_allow_stays_empty_fail_open(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)

    code, stdout, stderr = run_hook(
        monkeypatch,
        {"hook_event_name": "preToolUse", "tool_name": "Bash", "tool_input": {"command": "git status"}},
        ["image-input-optimizer-guard", "--harness", "cursor"],
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


def test_git_commit_push_guard_blocks_force_push_to_main(monkeypatch):
    code, stdout, _ = run_hook(
        monkeypatch,
        {"tool_name": "bash", "tool_input": {"command": "git push --force origin main"}},
        ["git-commit-push-guard", "--harness", "codex"],
    )
    payload = json.loads(stdout)
    assert code == 0
    specific = payload["hookSpecificOutput"]
    assert specific["permissionDecision"] == "deny"
    assert "protected branch" in specific["permissionDecisionReason"]


def test_git_commit_push_guard_allows_safe_commit(monkeypatch):
    code, stdout, _ = run_hook(
        monkeypatch,
        {"tool_name": "bash", "tool_input": {"command": "git commit -m ok"}},
        ["git-commit-push-guard", "--harness", "codex"],
    )
    assert code == 0
    assert stdout == ""


def test_cursor_before_read_file_guard_blocks_env(monkeypatch):
    code, stdout, _ = run_hook(
        monkeypatch,
        {"hook_event_name": "BeforeReadFile", "tool_input": {"path": ".env.local"}},
        ["cursor-before-read-file-guard", "--harness", "cursor"],
    )
    payload = json.loads(stdout)
    assert code == 0
    assert payload["permission"] == "deny"


def test_cursor_before_read_file_guard_allows_source(monkeypatch):
    code, stdout, _ = run_hook(
        monkeypatch,
        {"hook_event_name": "BeforeReadFile", "tool_input": {"path": "src/app.py"}},
        ["cursor-before-read-file-guard", "--harness", "cursor"],
    )
    # Fail-closed cursor event: a clean allow emits an explicit permission allow.
    assert code == 0
    assert json.loads(stdout)["permission"] == "allow"


def test_cursor_before_mcp_execution_guard_blocks_destructive(monkeypatch):
    code, stdout, _ = run_hook(
        monkeypatch,
        {"hook_event_name": "BeforeMCPExecution", "tool_name": "shell.exec", "tool_input": {"command": "rm -rf /"}},
        ["cursor-before-mcp-execution-guard", "--harness", "cursor"],
    )
    payload = json.loads(stdout)
    assert code == 0
    assert payload["permission"] == "deny"


def test_cursor_subagent_start_context_returns_context(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(wagents_hook, "_git_session_context", lambda cwd: "branch=main; dirty_paths=0")
    code, stdout, _ = run_hook(
        monkeypatch,
        {"hook_event_name": "SubagentStart", "cwd": str(tmp_path)},
        ["cursor-subagent-start-context", "--harness", "cursor"],
    )
    payload = json.loads(stdout)
    assert code == 0
    assert "branch=main" in payload["additional_context"]
    assert "config/hook-registry.json" in payload["additional_context"]


def test_grok_build_destructive_shell_emits_block_json(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    code, stdout, _ = run_hook(
        monkeypatch,
        {"hook_event_name": "PreToolUse", "tool_name": "bash", "tool_input": {"command": "rm -rf /"}},
        ["cursor-destructive-shell-guard", "--harness", "grok-build"],
    )
    payload = json.loads(stdout)
    assert code == 0
    assert payload["decision"] == "block"


def test_grok_build_read_guard_blocks_env(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    code, stdout, _ = run_hook(
        monkeypatch,
        {"hook_event_name": "BeforeReadFile", "tool_input": {"path": ".env"}},
        ["cursor-before-read-file-guard", "--harness", "grok-build"],
    )
    payload = json.loads(stdout)
    assert code == 0
    assert payload["decision"] == "block"


def test_grok_build_stop_retry_emits_block_json(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    code, stdout, _ = run_hook(
        monkeypatch,
        {
            "hook_event_name": "Stop",
            "last_assistant_message": "Implemented the hook changes in hooks/wagents-hook.py.",
            "stop_hook_active": False,
        },
        ["cursor-stop-truth-gate", "--harness", "grok-build"],
    )
    payload = json.loads(stdout)
    assert code == 0
    assert payload["decision"] == "block"


def test_opencode_destructive_shell_emits_deny_json(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    code, stdout, _ = run_hook(
        monkeypatch,
        {"hook_event_name": "PreToolUse", "tool_name": "bash", "tool_input": {"command": "rm -rf /"}},
        ["cursor-destructive-shell-guard", "--harness", "opencode"],
    )
    payload = json.loads(stdout)
    assert code == 0
    assert payload["permission"] == "deny"


def test_opencode_env_read_emits_deny_json(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    code, stdout, _ = run_hook(
        monkeypatch,
        {"hook_event_name": "PreToolUse", "tool_name": "read", "tool_input": {"path": ".env"}},
        ["cursor-before-read-file-guard", "--harness", "opencode"],
    )
    payload = json.loads(stdout)
    assert code == 0
    assert payload["permission"] == "deny"


def test_before_read_file_guard_alias_blocks_env(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    code, stdout, _ = run_hook(
        monkeypatch,
        {"hook_event_name": "PreToolUse", "tool_name": "read", "tool_input": {"path": ".env"}},
        ["before-read-file-guard", "--harness", "opencode"],
    )
    payload = json.loads(stdout)
    assert code == 0
    assert payload["permission"] == "deny"


def test_opencode_protected_file_write_denies(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    code, stdout, _ = run_hook(
        monkeypatch,
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "write",
            "tool_input": {"file_path": ".env"},
        },
        ["cursor-protected-file-guard", "--harness", "opencode"],
    )
    payload = json.loads(stdout)
    assert code == 0
    assert payload["permission"] == "deny"


def test_grok_build_protected_file_write_blocks(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    code, stdout, _ = run_hook(
        monkeypatch,
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "write",
            "tool_input": {"file_path": ".env"},
        },
        ["cursor-protected-file-guard", "--harness", "grok-build"],
    )
    payload = json.loads(stdout)
    assert code == 0
    assert payload["decision"] == "block"


def test_opencode_read_guard_allows_source_file(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    code, stdout, _ = run_hook(
        monkeypatch,
        {"hook_event_name": "PreToolUse", "tool_name": "read", "tool_input": {"path": "src/foo.py"}},
        ["cursor-before-read-file-guard", "--harness", "opencode"],
    )
    assert code == 0
    assert stdout.strip() == ""


def test_grok_build_read_guard_allows_source_file(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    code, stdout, _ = run_hook(
        monkeypatch,
        {"hook_event_name": "BeforeReadFile", "tool_input": {"path": "src/foo.py"}},
        ["cursor-before-read-file-guard", "--harness", "grok-build"],
    )
    assert code == 0
    assert stdout.strip() == ""


def test_opencode_bash_allows_safe_ls(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    code, stdout, _ = run_hook(
        monkeypatch,
        {"hook_event_name": "PreToolUse", "tool_name": "bash", "tool_input": {"command": "ls"}},
        ["cursor-destructive-shell-guard", "--harness", "opencode"],
    )
    assert code == 0
    assert stdout.strip() == ""


def test_grok_build_bash_allows_safe_ls(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    code, stdout, _ = run_hook(
        monkeypatch,
        {"hook_event_name": "PreToolUse", "tool_name": "bash", "tool_input": {"command": "ls"}},
        ["cursor-destructive-shell-guard", "--harness", "grok-build"],
    )
    assert code == 0
    assert stdout.strip() == ""


def test_before_read_file_guard_alias_allows_source_file(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    code, stdout, _ = run_hook(
        monkeypatch,
        {"hook_event_name": "PreToolUse", "tool_name": "read", "tool_input": {"path": "src/foo.py"}},
        ["before-read-file-guard", "--harness", "opencode"],
    )
    assert code == 0
    assert stdout.strip() == ""


def test_cursor_shell_guard_allows_git_status_when_git_module_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(wagents_hook, "evaluate_git_commit_push", None)
    code, stdout, _ = run_hook(
        monkeypatch,
        {"hook_event_name": "BeforeShellExecution", "command": "git status"},
        ["cursor-before-shell-execution-guard", "--harness", "cursor"],
    )
    assert code == 0
    assert json.loads(stdout) == {"permission": "allow"}
