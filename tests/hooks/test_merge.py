"""Hook-group merge idempotency and generated-entry stripping contracts.

``merge_hook_groups`` must be idempotent: re-running it over its own output may
not accumulate duplicate managed entries. The tricky case is registry hooks that
shell out to plain scripts (no ``wagents-hook.py`` / ``run-wagents-hook``
marker) — they are detected as managed only by matching a freshly rendered
command.
"""

from __future__ import annotations

from wagents.hooks.merge import (
    merge_cursor_flat_hooks,
    merge_hook_groups,
    strip_foreign_claude_hook_entries,
    strip_generated_hook_entries,
)


def _generated() -> dict[str, object]:
    verifier_cmd = "python3 ./hooks/wagents-hook.py verifier --harness claude-code"
    return {
        "hooks": {
            "Stop": [
                {"hooks": [{"type": "command", "command": verifier_cmd}]},
                {"hooks": [{"type": "command", "command": "./hooks/verify-before-stop.sh", "timeout": 60}]},
            ],
            "SubagentStop": [
                {"hooks": [{"type": "command", "command": "./hooks/teammate-idle-gate.sh", "timeout": 120}]},
            ],
        }
    }


def test_merge_onto_empty_renders_generated():
    merged = merge_hook_groups({}, _generated())
    assert len(merged["Stop"]) == 2
    assert len(merged["SubagentStop"]) == 1


def test_merge_is_idempotent_for_markerless_script_hooks():
    once = merge_hook_groups({}, _generated())
    twice = merge_hook_groups(once, _generated())
    # No duplicate accumulation across re-runs.
    assert twice == once
    stop_commands = [hook["command"] for group in twice["Stop"] for hook in group["hooks"]]
    assert stop_commands.count("./hooks/verify-before-stop.sh") == 1


def test_merge_preserves_user_authored_hooks():
    existing = {
        "Stop": [
            {"hooks": [{"type": "command", "command": "./hooks/my-user-hook.sh"}]},
        ]
    }
    merged = merge_hook_groups(existing, _generated())
    stop_commands = [hook["command"] for group in merged["Stop"] for hook in group["hooks"]]
    assert "./hooks/my-user-hook.sh" in stop_commands
    assert "./hooks/verify-before-stop.sh" in stop_commands


def test_strip_removes_marker_and_managed_command_entries():
    hooks = {
        "Stop": [
            {"hooks": [{"type": "command", "command": "python3 ./hooks/wagents-hook.py x --harness claude-code"}]},
            {"hooks": [{"type": "command", "command": "./hooks/verify-before-stop.sh"}]},
            {"hooks": [{"type": "command", "command": "./hooks/keep-me.sh"}]},
        ]
    }
    stripped = strip_generated_hook_entries(hooks, frozenset({"./hooks/verify-before-stop.sh"}))
    remaining = [hook["command"] for group in stripped["Stop"] for hook in group["hooks"]]
    assert remaining == ["./hooks/keep-me.sh"]


def test_strip_without_managed_commands_keeps_markerless_scripts():
    hooks = {"Stop": [{"hooks": [{"type": "command", "command": "./hooks/verify-before-stop.sh"}]}]}
    stripped = strip_generated_hook_entries(hooks)
    assert stripped == hooks


def test_strip_foreign_claude_hook_entries_removes_copilot_and_cursor_shapes():
    hooks = {
        "PostToolUse": [
            {
                "type": "command",
                "bash": "./hooks/auto-format.sh",
                "cwd": ".",
                "timeoutSec": 30,
            },
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": (
                            "python3 ${workspaceFolder}/hooks/wagents-hook.py "
                            "research-evidence-ledger --harness cursor"
                        ),
                        "timeout": 5,
                    }
                ],
                "matcher": "WebSearch",
            },
            {
                "matcher": "Edit|Write",
                "hooks": [{"type": "command", "command": "jq -r '.tool_input.file_path // empty'"}],
            },
        ],
        "sessionStart": [{"type": "command", "bash": "./hooks/session-start.sh", "cwd": "."}],
        "PreToolUse": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "python3 ./hooks/wagents-hook.py git-commit-push-guard --harness claude-code",
                        "timeout": 5,
                    }
                ],
                "matcher": "Bash",
            }
        ],
    }
    stripped = strip_foreign_claude_hook_entries(hooks)
    assert "sessionStart" not in stripped
    post_commands = [hook["command"] for group in stripped["PostToolUse"] for hook in group["hooks"]]
    assert post_commands == ["jq -r '.tool_input.file_path // empty'"]
    assert len(stripped["PreToolUse"]) == 1


def test_merge_cursor_flat_hooks_replaces_managed_plannotator_rows():
    plannotator = "/Users/example/.local/bin/plannotator"
    existing = {
        "preToolUse": [
            {
                "matcher": "exit_plan_mode|ExitPlanMode",
                "hooks": [{"type": "command", "command": plannotator, "timeout": 345600}],
            },
            {"command": "/usr/local/bin/my-custom-hook.sh"},
        ]
    }
    generated = {
        "preToolUse": [
            {"matcher": "exit_plan_mode|ExitPlanMode", "command": plannotator, "timeout": 345600},
            {"matcher": "enter_plan_mode|EnterPlanMode", "command": f"{plannotator} improve-context", "timeout": 5},
        ]
    }
    merged = merge_cursor_flat_hooks(existing, generated)
    commands = [entry["command"] for entry in merged["preToolUse"]]
    assert commands == ["/usr/local/bin/my-custom-hook.sh", plannotator, f"{plannotator} improve-context"]
