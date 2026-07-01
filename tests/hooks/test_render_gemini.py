from __future__ import annotations

from wagents.platforms.gemini import Adapter


def test_gemini_adapter_render_hooks_uses_native_events_and_metadata():
    registry = {
        "hooks": [
            {
                "id": "gemini-session-start-context",
                "description": "Gather Gemini context.",
                "logical_event": "SessionStart",
                "command": "python3 {repo_root}/hooks/wagents-hook.py gemini-session-start-context --harness {harness}",
                "timeout": 5,
                "harnesses": ["gemini-cli"],
            },
            {
                "id": "gemini-before-tool-guard",
                "description": "Guard Gemini tools.",
                "logical_event": "PreToolUse",
                "matcher": "Bash",
                "command": "python3 {repo_root}/hooks/wagents-hook.py gemini-before-tool-guard --harness {harness}",
                "timeout": 9,
                "harnesses": ["gemini-cli"],
            },
            {
                "id": "research-stop-verifier",
                "logical_event": "Stop",
                "command": "python3 {repo_root}/hooks/wagents-hook.py research-stop-verifier --harness {harness}",
                "timeout": 30,
                "harnesses": ["gemini-cli"],
            },
        ]
    }

    rendered = Adapter().render_hooks(registry, repo_relative=True)

    assert rendered is not None
    assert set(rendered["hooks"]) == {"sessionStart", "BeforeTool", "AfterAgent"}
    before_tool = rendered["hooks"]["BeforeTool"][0]
    assert before_tool["matcher"] == "Bash"
    assert before_tool["sequential"] is True
    command = before_tool["hooks"][0]
    assert command == {
        "type": "command",
        "command": "python3 ./hooks/wagents-hook.py gemini-before-tool-guard --harness gemini-cli",
        "name": "gemini-before-tool-guard",
        "timeout": 9000,
        "description": "Guard Gemini tools.",
    }
