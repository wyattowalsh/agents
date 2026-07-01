from __future__ import annotations

from wagents.platforms.claude import Adapter


def test_claude_adapter_render_hooks_supports_extended_events():
    registry = {
        "hooks": [
            {
                "id": "claude-session-start-context",
                "logical_event": "SessionStart",
                "command": "python3 {repo_root}/hooks/wagents-hook.py claude-session-start-context --harness {harness}",
                "timeout": 5,
                "harnesses": ["claude-code"],
            },
            {
                "id": "claude-permission-request-guard",
                "logical_event": "PermissionRequest",
                "command": (
                    "python3 {repo_root}/hooks/wagents-hook.py claude-permission-request-guard --harness {harness}"
                ),
                "timeout": 5,
                "harnesses": ["claude-code"],
            },
            {
                "id": "claude-subagent-stop-synth",
                "logical_event": "SubagentStop",
                "command": "python3 {repo_root}/hooks/wagents-hook.py claude-subagent-stop-synth --harness {harness}",
                "harnesses": ["claude-code"],
            },
        ]
    }

    rendered = Adapter().render_hooks(registry, repo_relative=True)

    assert rendered is not None
    assert set(rendered["hooks"]) == {"SessionStart", "PermissionRequest", "SubagentStop"}
    for event, entries in rendered["hooks"].items():
        assert entries[0]["hooks"][0]["type"] == "command", event
        assert entries[0]["hooks"][0]["command"].startswith("python3 ./hooks/wagents-hook.py "), event
