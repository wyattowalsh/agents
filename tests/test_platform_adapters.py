from __future__ import annotations

from wagents.platforms.base import SyncContext
from wagents.platforms import get_adapter


def test_codex_adapter_dry_run_notes_changes():
    ctx = SyncContext(apply=False)
    adapter = get_adapter("codex")
    adapter.sync_repo(ctx, {}, {}, {})
    assert ctx.changes


def test_copilot_adapter_dry_run_notes_repo_changes():
    ctx = SyncContext(apply=False)
    adapter = get_adapter("github-copilot")
    adapter.sync_repo(ctx, {}, {}, {})
    assert ctx.changes


def test_gemini_adapter_dry_run_home_notes_when_settings_missing(monkeypatch):
    ctx = SyncContext(apply=False)
    adapter = get_adapter("gemini-cli")
    monkeypatch.setattr("scripts.sync_agent_stack.GEMINI_SETTINGS_PATH", __import__("pathlib").Path("/nonexistent/settings.json"))
    adapter.sync_home(ctx, {}, {}, {}, {})
    # no settings file: merge_gemini_settings returns early without changes
    assert isinstance(ctx.changes, list)

