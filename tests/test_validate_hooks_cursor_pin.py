"""tmp_path unit tests for Cursor pin presence in validate_hooks (RV-S-008 + 010)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SKILL_CREATOR_SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "skill-creator" / "scripts"
sys.path.insert(0, str(SKILL_CREATOR_SCRIPTS))

from asset_toolkit.validate_hooks import (  # noqa: E402
    CURSOR_REQUIRED_PIN_COMMAND_SUBSTRINGS,
    validate_hooks,
)

PIN_REWRITE = "cursor-task-model-pin-rewrite"
PIN_ALLOWLIST = "cursor-subagent-model-allowlist"


def _write_cursor_hooks(repo_root: Path, hooks: dict) -> None:
    cursor_dir = repo_root / ".cursor"
    cursor_dir.mkdir(parents=True, exist_ok=True)
    (cursor_dir / "hooks.json").write_text(
        json.dumps({"version": 1, "hooks": hooks}, indent=2) + "\n",
        encoding="utf-8",
    )


def _happy_pin_hooks() -> dict:
    runner = '"$CURSOR_PROJECT_DIR/hooks/run-wagents-hook"'
    return {
        "preToolUse": [
            {
                "command": f"{runner} {PIN_REWRITE} --harness cursor",
                "matcher": "Task",
                "timeout": 5,
                "failClosed": False,
            }
        ],
        "subagentStart": [
            {
                "command": f"{runner} {PIN_ALLOWLIST} --harness cursor",
                "timeout": 5,
                "failClosed": False,
            }
        ],
    }


def test_missing_cursor_hooks_json_is_error(tmp_path: Path) -> None:
    errors = validate_hooks(tmp_path, harness="cursor")
    assert any(
        e["source"] == ".cursor/hooks.json" and "missing required" in e["message"]
        for e in errors
    )


def test_missing_pin_command_is_error(tmp_path: Path) -> None:
    _write_cursor_hooks(
        tmp_path,
        {
            "preToolUse": [
                {
                    "command": '"$CURSOR_PROJECT_DIR/hooks/run-wagents-hook" demo --harness cursor',
                    "matcher": "Bash",
                    "timeout": 5,
                }
            ]
        },
    )
    errors = validate_hooks(tmp_path, harness="cursor")
    messages = "\n".join(e["message"] for e in errors)
    for pin_id in CURSOR_REQUIRED_PIN_COMMAND_SUBSTRINGS:
        assert pin_id in messages


def test_wrong_fail_closed_is_error(tmp_path: Path) -> None:
    hooks = _happy_pin_hooks()
    hooks["preToolUse"][0]["failClosed"] = True
    hooks["subagentStart"][0]["failClosed"] = True
    _write_cursor_hooks(tmp_path, hooks)

    errors = validate_hooks(tmp_path, harness="cursor")
    messages = "\n".join(e["message"] for e in errors)
    assert PIN_REWRITE in messages
    assert PIN_ALLOWLIST in messages
    assert "failClosed" in messages


def test_omitted_fail_closed_is_error(tmp_path: Path) -> None:
    hooks = _happy_pin_hooks()
    del hooks["preToolUse"][0]["failClosed"]
    del hooks["subagentStart"][0]["failClosed"]
    _write_cursor_hooks(tmp_path, hooks)

    errors = validate_hooks(tmp_path, harness="cursor")
    assert any("failClosed" in e["message"] for e in errors)


def test_happy_stub_passes_cursor_harness(tmp_path: Path) -> None:
    _write_cursor_hooks(tmp_path, _happy_pin_hooks())
    errors = validate_hooks(tmp_path, harness="cursor")
    assert errors == []


def test_claude_code_harness_skips_cursor_projection(tmp_path: Path) -> None:
    errors = validate_hooks(tmp_path, harness="claude-code")
    assert not any(e["source"] == ".cursor/hooks.json" for e in errors)
