"""Cursor home sync preserves orphans and pins allowlisted model rules."""

from __future__ import annotations

from scripts import sync_agent_stack
from scripts.sync_agent_stack import SyncContext, sync_cursor_home_allowlisted_rules, sync_home_targets
from wagents.platforms import cursor as cursor_platform


def test_sync_cursor_home_allowlisted_rules_copies_models_and_keeps_orphans(
    tmp_path,
    monkeypatch,
) -> None:
    repo_rules = tmp_path / "repo-rules"
    home_rules = tmp_path / "home-rules"
    repo_rules.mkdir()
    home_rules.mkdir()

    models_src = repo_rules / "cursor-models.mdc"
    models_src.write_text("# pin models\n", encoding="utf-8")
    orphan = home_rules / "copilot.mdc"
    orphan.write_text("# user orphan\n", encoding="utf-8")

    monkeypatch.setattr(sync_agent_stack, "CURSOR_RULES_REPO_DIR", repo_rules)
    monkeypatch.setattr(sync_agent_stack, "CURSOR_RULES_DIR", home_rules)
    monkeypatch.setattr(sync_agent_stack, "CURSOR_HOME_RULES_ALLOWLIST", frozenset({"cursor-models.mdc"}))

    ctx = SyncContext(apply=True)
    sync_cursor_home_allowlisted_rules(ctx)

    assert (home_rules / "cursor-models.mdc").read_text(encoding="utf-8") == "# pin models\n"
    assert orphan.exists()
    assert orphan.read_text(encoding="utf-8") == "# user orphan\n"


def test_sync_cursor_home_allowlisted_rules_dry_run_skips_mkdir(
    tmp_path,
    monkeypatch,
) -> None:
    repo_rules = tmp_path / "repo-rules"
    home_rules = tmp_path / "home-rules"
    repo_rules.mkdir()
    (repo_rules / "cursor-models.mdc").write_text("# pin models\n", encoding="utf-8")

    monkeypatch.setattr(sync_agent_stack, "CURSOR_RULES_REPO_DIR", repo_rules)
    monkeypatch.setattr(sync_agent_stack, "CURSOR_RULES_DIR", home_rules)
    monkeypatch.setattr(sync_agent_stack, "CURSOR_HOME_RULES_ALLOWLIST", frozenset({"cursor-models.mdc"}))

    ctx = SyncContext(apply=False)
    sync_cursor_home_allowlisted_rules(ctx)

    assert not home_rules.exists()
    expected = f"copy {repo_rules / 'cursor-models.mdc'} -> {home_rules / 'cursor-models.mdc'}"
    assert expected in ctx.changes


def test_sync_cursor_home_allowlisted_rules_notes_missing_source(
    tmp_path,
    monkeypatch,
) -> None:
    repo_rules = tmp_path / "repo-rules"
    home_rules = tmp_path / "home-rules"
    repo_rules.mkdir()
    home_rules.mkdir()

    monkeypatch.setattr(sync_agent_stack, "CURSOR_RULES_REPO_DIR", repo_rules)
    monkeypatch.setattr(sync_agent_stack, "CURSOR_RULES_DIR", home_rules)
    monkeypatch.setattr(sync_agent_stack, "CURSOR_HOME_RULES_ALLOWLIST", frozenset({"cursor-models.mdc"}))

    ctx = SyncContext(apply=True)
    sync_cursor_home_allowlisted_rules(ctx)

    assert "skip missing allowlisted Cursor rule: cursor-models.mdc" in ctx.changes
    assert not (home_rules / "cursor-models.mdc").exists()


def test_sync_home_targets_cursor_filter_invokes_allowlisted_rules(monkeypatch) -> None:
    called: list[str] = []
    rules_calls: list[bool] = []

    def fake_sync(name, ctx, registry, policy, fallbacks, hook_registry):
        called.append(name)

    def fake_rules(ctx):
        rules_calls.append(True)

    monkeypatch.setattr(sync_agent_stack, "sync_platform_home_target", fake_sync)
    monkeypatch.setattr(sync_agent_stack, "sync_cursor_home_allowlisted_rules", fake_rules)

    ctx = SyncContext(apply=False)
    sync_home_targets(ctx, {}, {}, {}, {}, platforms_filter={"cursor"})

    assert called == ["cursor"]
    assert rules_calls == [True]


def test_cursor_adapter_sync_home_writes_managed_agents_preserves_unmarked(
    tmp_path,
    monkeypatch,
) -> None:
    home_cursor = tmp_path / ".cursor"
    agents_dir = home_cursor / "agents"
    agents_dir.mkdir(parents=True)

    user_agent = agents_dir / "my-custom.md"
    user_agent.write_text(
        "---\nname: my-custom\ndescription: User owned.\nmodel: cursor-grok-4.5-high\n---\n\nCustom.\n",
        encoding="utf-8",
    )
    stale_managed = agents_dir / "stale-managed.md"
    stale_managed.write_text(
        "---\nname: stale-managed\ndescription: Old managed.\nmodel: cursor-grok-4.5-high\n---\n\n"
        f"{cursor_platform.CURSOR_MANAGED_AGENT_MARKER}stale-managed.md -->\n\nGone.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(cursor_platform, "CURSOR_HOME_MCP_PATH", home_cursor / "mcp.json")
    monkeypatch.setattr(cursor_platform, "CURSOR_HOME_HOOKS_PATH", home_cursor / "hooks.json")
    monkeypatch.setattr(cursor_platform, "CURSOR_HOME_AGENTS_DIR", agents_dir)
    monkeypatch.setattr(
        cursor_platform,
        "_render_cursor_agents",
        lambda: {
            "planner.md": (
                "---\nname: planner\ndescription: Plan.\nmodel: cursor-grok-4.5-high\n"
                "readonly: true\n---\n\n"
                f"{cursor_platform.CURSOR_MANAGED_AGENT_MARKER}planner.md -->\n\nPlan body.\n"
            )
        },
    )
    monkeypatch.setattr(cursor_platform, "render_cursor_global_hooks", lambda: None)

    adapter = cursor_platform.Adapter()
    ctx = cursor_platform.SyncContext(apply=True)
    adapter.sync_home(ctx, {"servers": {}}, {}, {}, {})

    managed = agents_dir / "planner.md"
    assert managed.is_file()
    assert cursor_platform.CURSOR_MANAGED_AGENT_MARKER in managed.read_text(encoding="utf-8")
    assert "model: cursor-grok-4.5-high" in managed.read_text(encoding="utf-8")
    assert user_agent.is_file()
    assert user_agent.read_text(encoding="utf-8").startswith("---\nname: my-custom")
    assert not stale_managed.exists()
