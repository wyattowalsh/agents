"""Cross-harness hook-document conversion contracts.

``wagents.hooks.convert`` reshapes an *already rendered* hook document between
harness projection families while preserving the command string verbatim. These
tests pin the shape per target and the round-trip stability of logical events,
matchers, and commands.
"""

from __future__ import annotations

import pytest

from wagents.hooks.convert import (
    HookSpec,
    convert_hooks,
    normalize_from,
    render_to,
)


def _claude_doc() -> dict[str, object]:
    return {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {"type": "command", "command": "guard --harness claude-code", "timeout": 5}
                    ],
                }
            ],
            "Stop": [
                {"hooks": [{"type": "command", "command": "stop-gate --harness claude-code"}]}
            ],
        }
    }


def _cursor_doc() -> dict[str, object]:
    return {
        "version": 1,
        "hooks": {
            "preToolUse": [
                {"command": "guard --harness cursor", "matcher": "Bash", "timeout": 5, "failClosed": True}
            ],
            "stop": [{"command": "stop-gate --harness cursor"}],
        },
    }


def test_cursor_to_claude_drops_cursor_native_events():
    cursor_native = {
        "version": 1,
        "hooks": {
            "beforeReadFile": [{"command": "read-guard", "matcher": ".*"}],
            "preToolUse": [{"command": "shell-guard", "matcher": "Bash"}],
        },
    }
    out = convert_hooks(cursor_native, source="cursor", target="claude-code")
    assert "beforeReadFile" not in out.get("hooks", {})
    assert "PreToolUse" in out["hooks"]


def test_normalize_from_claude_extracts_specs():
    specs = normalize_from(_claude_doc(), "claude-code")
    expected = HookSpec(
        logical_event="PreToolUse",
        command="guard --harness claude-code",
        matcher="Bash",
        timeout=5,
    )
    assert expected in specs
    assert any(s.logical_event == "Stop" and s.command == "stop-gate --harness claude-code" for s in specs)


def test_claude_to_cursor_is_flat_and_preserves_command():
    out = convert_hooks(_claude_doc(), source="claude-code", target="cursor")
    assert out["version"] == 1
    assert set(out["hooks"]) == {"preToolUse", "stop"}
    pre = out["hooks"]["preToolUse"][0]
    assert pre["command"] == "guard --harness claude-code"
    assert pre["matcher"] == "Bash"
    assert "hooks" not in pre
    assert "type" not in pre


def test_cursor_to_claude_nests_command_group():
    out = convert_hooks(_cursor_doc(), source="cursor", target="claude-code")
    pre = out["hooks"]["PreToolUse"][0]
    assert pre["matcher"] == "Bash"
    assert pre["hooks"][0] == {"type": "command", "command": "guard --harness cursor", "timeout": 5}


def test_round_trip_claude_cursor_claude_is_stable():
    doc = _claude_doc()
    back = convert_hooks(
        convert_hooks(doc, source="claude-code", target="cursor"),
        source="cursor",
        target="claude-code",
    )
    assert back == doc


def test_codex_target_adds_status_message():
    specs = [HookSpec(logical_event="PreToolUse", command="g", description="status")]
    out = render_to(specs, "codex")
    config = out["hooks"]["PreToolUse"][0]["hooks"][0]
    assert config["statusMessage"] == "status"
    assert config["timeout"] == 5


def test_unsupported_harness_raises():
    with pytest.raises(ValueError, match="unsupported source harness"):
        normalize_from({"hooks": {}}, "bogus")
    with pytest.raises(ValueError, match="unsupported target harness"):
        render_to([], "bogus")
