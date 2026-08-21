"""Atuin agent-history hooks survive render and Claude native-event stripping."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

from scripts.sync_agent_stack import render_codex_hooks, render_standard_hooks
from wagents.hooks.merge import CLAUDE_NATIVE_HOOK_EVENTS, strip_foreign_claude_hook_entries
from wagents.hooks.render import CLAUDE_EVENT_MAP
from wagents.platforms.claude import Adapter

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "config" / "hook-registry.json"
WRAPPER = REPO_ROOT / "hooks" / "atuin-agent-hook.sh"


def _registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _run_wrapper(path_dir: Path, *args: str, stdin: str = "{}") -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["ATUIN_HOOK_PATH"] = str(path_dir)
    env["PATH"] = f"{path_dir}:/usr/bin:/bin"
    return subprocess.run(
        [str(WRAPPER), *args],
        input=stdin,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def test_post_tool_use_failure_is_a_native_claude_event():
    assert "PostToolUseFailure" in CLAUDE_EVENT_MAP
    assert "PostToolUseFailure" in CLAUDE_NATIVE_HOOK_EVENTS
    assert CLAUDE_EVENT_MAP["PostToolUseFailure"] == "PostToolUseFailure"


def test_atuin_wrapper_is_tracked_and_executable():
    assert WRAPPER.is_file()
    assert WRAPPER.stat().st_mode & 0o111


def test_atuin_registry_rows_are_context_mode_and_wrapper_backed():
    ids = {
        "atuin-claude-pre",
        "atuin-claude-post",
        "atuin-claude-post-failure",
        "atuin-codex-pre",
        "atuin-codex-post",
        "atuin-codex-post-failure",
    }
    rows = [hook for hook in _registry()["hooks"] if hook["id"] in ids]
    assert {hook["id"] for hook in rows} == ids
    for hook in rows:
        assert hook["mode"] == "context"
        assert "atuin-agent-hook.sh" in hook["command"]
        assert "bundle_group" not in hook


def test_claude_render_includes_atuin_hook_on_failure_event():
    rendered = render_standard_hooks(_registry(), "claude-code", repo_relative=True)
    failure = rendered["hooks"]["PostToolUseFailure"]
    commands = [hook["command"] for group in failure for hook in group["hooks"]]
    assert any("atuin-agent-hook.sh claude-code" in cmd for cmd in commands)


def test_claude_adapter_render_includes_atuin_post_tool_use_failure():
    rendered = Adapter().render_hooks(_registry(), repo_relative=True)
    assert rendered is not None
    failure = rendered["hooks"]["PostToolUseFailure"]
    commands = [hook["command"] for group in failure for hook in group["hooks"]]
    assert any("atuin-agent-hook.sh claude-code" in cmd for cmd in commands)


def test_codex_render_includes_atuin_hook():
    rendered = render_codex_hooks(_registry(), repo_relative=True)
    atuin_events: set[str] = set()
    for event in ("PreToolUse", "PostToolUse", "PostToolUseFailure"):
        for group in rendered["hooks"].get(event, []):
            commands = [hook["command"] for hook in group["hooks"]]
            if any("atuin-agent-hook.sh" in cmd for cmd in commands):
                atuin_events.add(event)
                assert group.get("matcher") == "^Bash$"
    assert atuin_events == {"PreToolUse", "PostToolUse", "PostToolUseFailure"}


def test_strip_foreign_claude_keeps_post_tool_use_failure_atuin_entry():
    hooks = {
        "PostToolUseFailure": [
            {
                "matcher": "Bash",
                "hooks": [
                    {
                        "type": "command",
                        "command": "./hooks/atuin-agent-hook.sh claude-code",
                        "timeout": 5,
                    }
                ],
            }
        ]
    }
    stripped = strip_foreign_claude_hook_entries(hooks)
    commands = [hook["command"] for group in stripped["PostToolUseFailure"] for hook in group["hooks"]]
    assert commands == ["./hooks/atuin-agent-hook.sh claude-code"]


def test_wrapper_exits_zero_when_atuin_missing(tmp_path: Path):
    result = _run_wrapper(tmp_path, "claude-code")
    assert result.returncode == 0


def test_wrapper_exits_zero_when_atuin_fails(tmp_path: Path):
    atuin = tmp_path / "atuin"
    atuin.write_text("#!/bin/sh\nexit 2\n", encoding="utf-8")
    atuin.chmod(atuin.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    result = _run_wrapper(tmp_path, "claude-code", stdin='{"command":"true"}')
    assert result.returncode == 0


def test_wrapper_does_not_eval_stdin(tmp_path: Path):
    marker = tmp_path / "pwned"
    atuin = tmp_path / "atuin"
    atuin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    atuin.chmod(atuin.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    result = _run_wrapper(tmp_path, "claude-code", stdin=f"touch {marker}")
    assert result.returncode == 0
    assert not marker.exists()
