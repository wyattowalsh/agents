"""Tests for the Grok Build platform adapter."""

from __future__ import annotations

import pytest

from scripts.sync_agent_stack import MCP_REGISTRY_PATH, load_json
from wagents.platforms.base import SyncContext
from wagents.platforms.grok import (
    GROK_CONFIG_POLICY_PATH,
    Adapter,
    GrokConfigDropError,
    apply_model_defaults,
    assert_no_grok_config_drops,
    blend_owned_table,
    is_grok_blend_header,
    is_grok_owned_header,
    parse_toml_table_kv,
    registry_mcp_server_names,
    render_grok_config,
    render_preserved_grok_config,
    strip_registry_mcp_tables,
)


def test_is_grok_owned_header_matches_policy_tables():
    assert is_grok_owned_header("models")
    assert is_grok_owned_header("mcp_servers.mcphub_group_harness-safe")
    assert is_grok_owned_header("compat.claude")
    assert not is_grok_owned_header("cli")
    assert not is_grok_owned_header("marketplace.sources")


def test_is_grok_blend_header_matches_blend_tables():
    assert is_grok_blend_header("ui")
    assert is_grok_blend_header("features.lsp")
    assert not is_grok_blend_header("models")
    assert not is_grok_blend_header("mcp_servers.foo")


def test_parse_toml_table_kv_extracts_header_and_keys():
    chunk = '[ui]\nyolo = true\ntheme = "dark"\n'
    header, values = parse_toml_table_kv(chunk)
    assert header == "ui"
    assert values["yolo"] == "true"
    assert values['theme'] == '"dark"'


def test_blend_owned_table_policy_overrides_shared_keys():
    policy = '[ui]\nyolo = true\npermission_mode = "always-approve"\n'
    user = '[ui]\nyolo = false\ntheme = "dark"\n'
    blended = blend_owned_table(policy, user)
    assert 'yolo = true' in blended
    assert 'theme = "dark"' in blended
    assert 'permission_mode = "always-approve"' in blended
    assert "yolo = false" not in blended


def test_blend_owned_table_keeps_user_only_keys():
    policy = "[ui]\nyolo = true\n"
    user = '[ui]\nnotifications = false\n'
    blended = blend_owned_table(policy, user)
    assert "yolo = true" in blended
    assert "notifications = false" in blended


def test_render_preserved_grok_config_keeps_user_tables():
    current = """
[cli]
auto_update = true

[models]
default = "old-model"
"""
    preserved = render_preserved_grok_config(current)
    assert "[cli]" in preserved
    assert "auto_update = true" in preserved
    assert "[models]" not in preserved


def test_assert_no_grok_config_drops_detects_user_table_loss():
    before = "[cli]\nauto_update = true\n"
    after = ""
    with pytest.raises(GrokConfigDropError):
        assert_no_grok_config_drops(before, after)


def test_assert_no_drops_ignores_blend_tables():
    before = '[ui]\ntheme = "dark"\n'
    after = render_grok_config(before, load_json(MCP_REGISTRY_PATH), repo_only=False)
    assert_no_grok_config_drops(before, after, load_json(MCP_REGISTRY_PATH))


def test_grok_merge_preserves_user_sections(tmp_path, monkeypatch):
    registry = load_json(MCP_REGISTRY_PATH)
    policy_path = tmp_path / "config" / "grok-config.toml"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text("[ui]\nyolo = true\n", encoding="utf-8")
    monkeypatch.setattr("wagents.platforms.grok.GROK_CONFIG_POLICY_PATH", policy_path)

    current = """
[user_custom]
flag = true

[ui]
theme = "dark"
"""
    rendered = render_grok_config(current, registry, repo_only=False, repo_root=tmp_path)
    assert "[user_custom]" in rendered
    assert "flag = true" in rendered
    assert 'theme = "dark"' in rendered
    assert "yolo = true" in rendered


def test_strip_registry_mcp_without_markers():
    registry = load_json(MCP_REGISTRY_PATH)
    names = registry_mcp_server_names(registry)
    current = """
[cli]
auto_update = true

[mcp_servers.mcphub_group_harness-safe]
url = "http://127.0.0.1:46683/mcp/harness-safe"
enabled = true
"""
    stripped = strip_registry_mcp_tables(current, names)
    assert "mcphub_group_harness-safe" not in stripped
    assert "[cli]" in stripped


def test_render_grok_config_repo_only_is_mcp_block():
    registry = load_json(MCP_REGISTRY_PATH)
    rendered = render_grok_config("", registry, repo_only=True)
    assert "BEGIN MANAGED BY sync_agent_stack.py: MCP_SERVERS" in rendered
    assert "[mcp_servers.mcphub_group_harness-safe]" in rendered


def test_render_grok_config_home_includes_policy_and_preserves_user(tmp_path, monkeypatch):
    registry = load_json(MCP_REGISTRY_PATH)
    policy_path = tmp_path / "config" / "grok-config.toml"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text("[models]\ndefault = \"grok-composer-2.5-fast\"\n", encoding="utf-8")
    monkeypatch.setattr("wagents.platforms.grok.GROK_CONFIG_POLICY_PATH", policy_path)

    current = "[cli]\nauto_update = false\n"
    rendered = render_grok_config(current, registry, repo_only=False, repo_root=tmp_path)
    assert "[cli]" in rendered
    assert "GROK_POLICY" in rendered or "grok-composer-2.5-fast" in rendered
    assert "BEGIN MANAGED BY sync_agent_stack.py: MCP_SERVERS" in rendered


def test_render_grok_config_home_blend_ui(tmp_path, monkeypatch):
    registry = load_json(MCP_REGISTRY_PATH)
    policy_path = tmp_path / "config" / "grok-config.toml"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text(
        '[ui]\nyolo = true\npermission_mode = "always-approve"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("wagents.platforms.grok.GROK_CONFIG_POLICY_PATH", policy_path)

    current = '[ui]\ntheme = "solarized"\n'
    rendered = render_grok_config(current, registry, repo_only=False, repo_root=tmp_path)
    assert 'theme = "solarized"' in rendered
    assert "yolo = true" in rendered


def test_apply_model_defaults_from_tooling_policy():
    body = "[models]\ndefault = \"old\"\n"
    policy = {"model_defaults": {"grok": {"default": "grok-composer-2.5-fast", "web_search": "grok-4.20-multi-agent"}}}
    rendered = apply_model_defaults(body, policy)
    assert 'default = "grok-composer-2.5-fast"' in rendered
    assert 'web_search = "grok-4.20-multi-agent"' in rendered


def test_grok_config_copy_matches_sanitized_template():
    if not GROK_CONFIG_POLICY_PATH.exists():
        pytest.skip("policy template missing")
    text = GROK_CONFIG_POLICY_PATH.read_text(encoding="utf-8")
    assert "[models]" in text
    assert "grok-composer-2.5-fast" in text
    assert "[ui]" in text
    assert "/Users/" not in text


def test_grok_adapter_is_available_when_config_exists(monkeypatch, tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text("[models]\ndefault = \"x\"\n", encoding="utf-8")
    monkeypatch.setattr("wagents.platforms.grok.GROK_CONFIG_PATH", cfg)
    monkeypatch.setattr("wagents.platforms.grok.GROK_BINARY_PATH", tmp_path / "missing-grok")
    assert Adapter().is_available()


def test_sync_repo_writes_project_mcp_only(tmp_path, monkeypatch):
    repo_cfg = tmp_path / ".grok" / "config.toml"
    monkeypatch.setattr("wagents.platforms.grok.GROK_CONFIG_REPO_PATH", repo_cfg)
    monkeypatch.setattr("wagents.platforms.grok.AGENTS_DIR", tmp_path / "agents")
    registry = load_json(MCP_REGISTRY_PATH)
    ctx = SyncContext(apply=True)
    Adapter().sync_repo(ctx, registry, {}, {})
    assert repo_cfg.exists()
    text = repo_cfg.read_text(encoding="utf-8")
    assert "MCP_SERVERS" in text
    assert "GROK_POLICY" not in text


def test_sync_grok_agents_creates_symlinks(tmp_path, monkeypatch):
    from wagents.platforms.grok import sync_grok_agents

    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "planner.md").write_text("---\nname: planner\ndescription: Plan\n---\n", encoding="utf-8")
    grok_agents = tmp_path / ".grok" / "agents"
    monkeypatch.setattr("wagents.platforms.grok.AGENTS_DIR", agents_dir)
    monkeypatch.setattr("wagents.platforms.grok.GROK_AGENTS_HOME_DIR", grok_agents)

    ctx = SyncContext(apply=True)
    sync_grok_agents(ctx)

    link = grok_agents / "planner.md"
    assert link.is_symlink()
    assert link.resolve() == (agents_dir / "planner.md").resolve()
