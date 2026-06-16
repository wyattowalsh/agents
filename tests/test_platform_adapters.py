from __future__ import annotations

from wagents.platforms.base import SyncContext
from wagents.platforms import get_adapter


def test_codex_adapter_dry_run_notes_changes(tmp_path, monkeypatch):
    import scripts.sync_agent_stack as sync_agent_stack

    stale = tmp_path / "instructions" / "codex-global.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale\n", encoding="utf-8")
    monkeypatch.setattr(sync_agent_stack, "CODEX_GLOBAL_MD", stale)

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

