from __future__ import annotations

import pytest

from wagents.platforms import get_adapter
from wagents.platforms.base import SyncContext


def test_codex_adapter_dry_run_notes_changes(tmp_path, monkeypatch):
    stale = tmp_path / "instructions" / "codex-global.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale\n", encoding="utf-8")
    monkeypatch.setattr("scripts.sync_agent_stack.CODEX_GLOBAL_MD", stale)

    ctx = SyncContext(apply=False)
    adapter = get_adapter("codex")
    adapter.sync_repo(ctx, {}, {}, {})
    assert ctx.changes


@pytest.mark.parametrize("retired_id", ["antigravity", "gemini-cli", "github-copilot"])
def test_retired_harness_adapters_are_rejected(retired_id):
    with pytest.raises(KeyError):
        get_adapter(retired_id)
