from __future__ import annotations

from wagents.platforms.codex import Adapter


def test_codex_adapter_render_hooks_projects_official_events():
    registry = {
        "hooks": [
            {
                "id": "codex-session-start-context",
                "logical_event": "SessionStart",
                "command": "python3 {repo_root}/hooks/wagents-hook.py codex-session-start-context --harness {harness}",
                "timeout": 5,
                "status_message": "Gathering context",
                "harnesses": ["codex"],
            },
            {
                "id": "codex-permission-request-guard",
                "logical_event": "PermissionRequest",
                "command": (
                    "python3 {repo_root}/hooks/wagents-hook.py codex-permission-request-guard --harness {harness}"
                ),
                "timeout": 7,
                "command_windows": (
                    "py {repo_root}/hooks/wagents-hook.py codex-permission-request-guard --harness {harness}"
                ),
                "harnesses": ["codex"],
            },
        ]
    }

    rendered = Adapter().render_hooks(registry, repo_relative=True)

    assert rendered is not None
    assert set(rendered["hooks"]) == {"SessionStart", "PermissionRequest"}
    session = rendered["hooks"]["SessionStart"][0]["hooks"][0]
    assert session["command"] == "python3 ./hooks/wagents-hook.py codex-session-start-context --harness codex"
    assert session["statusMessage"] == "Gathering context"
    permission = rendered["hooks"]["PermissionRequest"][0]["hooks"][0]
    assert permission["timeout"] == 7
    assert permission["commandWindows"] == "py ./hooks/wagents-hook.py codex-permission-request-guard --harness codex"
