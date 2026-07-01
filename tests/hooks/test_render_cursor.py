"""Cursor flat hook-shape rendering snapshots.

Cursor consumes a flat per-event entry shape (``{command, matcher?, timeout?,
failClosed?}``), not the nested Claude ``{"hooks": [...]}`` group shape. These
tests pin that contract for both the platform adapter and the shared renderer.
"""

from __future__ import annotations

import json
from pathlib import Path

from wagents.hooks.render import CURSOR_EVENT_MAP, render_cursor_global_hooks, render_cursor_hooks
from wagents.platforms import cursor as cursor_platform

REPO_ROOT = Path(__file__).resolve().parents[2]


def _registry() -> dict[str, object]:
    return {
        "version": 1,
        "hooks": [
            {
                "id": "cursor-session-start-context",
                "logical_event": "SessionStart",
                "matcher": "startup|resume|clear",
                "mode": "context",
                "command": "python3 {repo_root}/hooks/wagents-hook.py cursor-session-start-context --harness {harness}",
                "timeout": 5,
                "harnesses": ["cursor"],
            },
            {
                "id": "cursor-destructive-shell-guard",
                "logical_event": "PreToolUse",
                "matcher": "Bash|bash|run_shell_command",
                "mode": "enforce",
                "command": (
                    "python3 {repo_root}/hooks/wagents-hook.py cursor-destructive-shell-guard --harness {harness}"
                ),
                "timeout": 5,
                "harnesses": ["cursor"],
            },
            {
                "id": "cursor-stop-truth-gate",
                "logical_event": "Stop",
                "mode": "enforce",
                "command": "python3 {repo_root}/hooks/wagents-hook.py cursor-stop-truth-gate --harness {harness}",
                "timeout": 5,
                "harnesses": ["cursor"],
            },
            {
                "id": "codex-only",
                "logical_event": "PreToolUse",
                "command": "python3 {repo_root}/hooks/wagents-hook.py codex-only --harness {harness}",
                "harnesses": ["codex"],
            },
        ],
    }


def test_render_cursor_hooks_is_flat_shape():
    rendered = render_cursor_hooks(_registry())
    assert rendered is not None
    assert rendered["version"] == 1
    # Every entry must be flat: a dict with a top-level "command", never a
    # nested "hooks" group.
    for event, entries in rendered["hooks"].items():
        assert isinstance(entries, list)
        for entry in entries:
            assert "command" in entry, f"{event} entry missing command"
            assert "hooks" not in entry, f"{event} entry must not nest a hooks group"
            assert "type" not in entry, f"{event} entry must not carry a type field"


def test_render_cursor_hooks_maps_events_and_failclosed():
    rendered = render_cursor_hooks(_registry())
    assert rendered is not None
    hooks = rendered["hooks"]
    assert set(hooks) == {"sessionStart", "preToolUse", "stop"}

    pre = hooks["preToolUse"]
    assert pre == [
        {
            "command": (
                '"$CURSOR_PROJECT_DIR/hooks/run-wagents-hook" '
                "cursor-destructive-shell-guard --harness cursor"
            ),
            "matcher": "Bash|bash|run_shell_command",
            "timeout": 5,
            "failClosed": True,
        }
    ]
    # enforce-mode Stop is not a pre-execution event, so no failClosed.
    assert "failClosed" not in hooks["stop"][0]
    # context-mode session start is not fail-closed either.
    assert "failClosed" not in hooks["sessionStart"][0]


def test_render_cursor_hooks_fail_opens_catch_all_image_optimizer():
    rendered = render_cursor_hooks({
        "hooks": [
            {
                "id": "image-input-optimizer-guard",
                "logical_event": "PreToolUse",
                "matcher": ".*",
                "mode": "enforce",
                "command": "{hook_runner} image-input-optimizer-guard --harness {harness}",
                "timeout": 60,
                "harnesses": ["cursor"],
            }
        ]
    })
    assert rendered == {
        "version": 1,
        "hooks": {
            "preToolUse": [
                {
                    "command": (
                        '"$CURSOR_PROJECT_DIR/hooks/run-wagents-hook" '
                        "image-input-optimizer-guard --harness cursor"
                    ),
                    "matcher": ".*",
                    "timeout": 60,
                    "failClosed": False,
                }
            ]
        },
    }


def test_render_cursor_hooks_excludes_other_harnesses():
    rendered = render_cursor_hooks(_registry())
    assert rendered is not None
    flattened = json.dumps(rendered)
    assert "codex-only" not in flattened


def test_render_cursor_hooks_returns_none_when_empty():
    assert render_cursor_hooks({"hooks": []}) is None
    assert render_cursor_hooks({"hooks": [{"id": "x", "harnesses": ["codex"]}]}) is None


def test_adapter_render_hooks_matches_shared_renderer():
    adapter = cursor_platform.Adapter()
    registry = _registry()
    assert adapter.render_hooks(registry) == render_cursor_hooks(registry, harness="cursor")


def test_adapter_render_hooks_uses_cursor_project_dir_by_default():
    adapter = cursor_platform.Adapter()
    rendered = adapter.render_hooks(_registry())
    assert rendered is not None
    flattened = json.dumps(rendered)
    assert "${workspaceFolder}" not in flattened
    assert "$CURSOR_PROJECT_DIR/hooks/run-wagents-hook" in flattened


def test_repo_cursor_hooks_json_is_flat_if_present():
    path = REPO_ROOT / ".cursor" / "hooks.json"
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    for event, entries in data.get("hooks", {}).items():
        for entry in entries:
            assert "command" in entry, f"{event} entry in .cursor/hooks.json is not flat"
            assert "hooks" not in entry, f"{event} entry in .cursor/hooks.json nests a group"


def test_cursor_event_map_covers_native_surface():
    # The native fine-grained events must be representable for later waves.
    for native in ("beforeShellExecution", "beforeReadFile", "afterFileEdit", "beforeMCPExecution", "subagentStart"):
        assert native in CURSOR_EVENT_MAP.values()


def _real_registry() -> dict[str, object]:
    return json.loads((REPO_ROOT / "config" / "hook-registry.json").read_text(encoding="utf-8"))


def test_real_registry_renders_cursor_native_events():
    rendered = render_cursor_hooks(_real_registry())
    assert rendered is not None
    events = rendered["hooks"]
    for native in ("beforeReadFile", "beforeShellExecution", "beforeMCPExecution", "afterFileEdit", "subagentStart"):
        assert native in events, f"missing native event {native}"


def test_real_registry_cursor_native_enforce_events_are_fail_closed():
    rendered = render_cursor_hooks(_real_registry())
    assert rendered is not None
    events = rendered["hooks"]
    # Fine-grained pre-execution enforce guards use no matcher -> fail-closed.
    for native in ("beforeReadFile", "beforeShellExecution", "beforeMCPExecution"):
        entry = events[native][0]
        assert entry.get("failClosed") is True, f"{native} should be fail-closed"
        assert "matcher" not in entry
    # Context-tier native events never carry failClosed.
    for native in ("afterFileEdit", "subagentStart"):
        assert "failClosed" not in events[native][0]


def test_repo_cursor_hooks_json_contains_native_events():
    path = REPO_ROOT / ".cursor" / "hooks.json"
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    events = data.get("hooks", {})
    for native in ("beforeReadFile", "beforeShellExecution", "beforeMCPExecution", "afterFileEdit", "subagentStart"):
        assert native in events


def test_render_cursor_global_hooks_is_flat_plannotator_shape(monkeypatch, tmp_path):
    template = tmp_path / "cursor-global-hooks.json"
    template.write_text(
        json.dumps({
            "version": 1,
            "hooks": {
                "preToolUse": [
                    {
                        "matcher": "exit_plan_mode|ExitPlanMode",
                        "command": "__PLANNOTATOR_BIN__",
                        "timeout": 345600,
                    }
                ]
            },
        })
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("wagents.hooks.render.resolve_plannotator_binary", lambda: tmp_path / "plannotator")
    rendered = render_cursor_global_hooks(template_path=template)
    assert rendered == {
        "version": 1,
        "hooks": {
            "preToolUse": [
                {
                    "matcher": "exit_plan_mode|ExitPlanMode",
                    "command": str(tmp_path / "plannotator"),
                    "timeout": 345600,
                }
            ]
        },
    }
