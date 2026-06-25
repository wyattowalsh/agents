"""Executable tests proving harness rollback fixture behavior.

Covers:
- ensure_symlink() creates .bak backup on directory replacement when apply=True
- .bak backup can be used to restore prior content (rollback path)
- Config drop protection (assert_no_config_drops / write_local_json_config) still rejects drops (negative test)

These exercise the shared paths used by ensure_symlink/merge helpers for
harnesses that declare rollback-fixture coverage.
"""

import json
import shutil
from pathlib import Path

import pytest

from scripts.sync_agent_stack import MCP_REGISTRY_PATH, SyncContext, ensure_symlink, load_json, write_local_json_config
from wagents.platforms import base as platform_base
from wagents.platforms import cursor as cursor_platform
from wagents.platforms.grok import assert_no_grok_config_drops, render_grok_config


def test_ensure_symlink_replacement_creates_bak_backup_when_apply_true(tmp_path: Path) -> None:
    """Symlink replacement of an existing directory creates <name>.bak when apply=True."""
    skills_root = tmp_path / "skills"
    skills_root.mkdir()

    existing_dir = skills_root / "local-skill"
    existing_dir.mkdir()
    (existing_dir / "SKILL.md").write_text("local original content\n", encoding="utf-8")
    (existing_dir / "notes.txt").write_text("local notes\n", encoding="utf-8")

    managed_target = tmp_path / "repo" / "skills" / "local-skill"
    managed_target.mkdir(parents=True)
    (managed_target / "SKILL.md").write_text("managed skill content\n", encoding="utf-8")

    ctx = SyncContext(apply=True)
    ensure_symlink(ctx, existing_dir, managed_target)

    # Replaced path is now a symlink
    assert existing_dir.is_symlink(), f"expected symlink, got {existing_dir}"
    # Backup exists with original content
    backup = skills_root / "local-skill.bak"
    assert backup.exists(), "backup dir must exist"
    assert backup.is_dir(), "backup must be a directory"
    assert (backup / "SKILL.md").read_text(encoding="utf-8") == "local original content\n"
    assert (backup / "notes.txt").read_text(encoding="utf-8") == "local notes\n"

    # Symlink resolves to managed content
    assert (existing_dir / "SKILL.md").read_text(encoding="utf-8") == "managed skill content\n"

    # A note was recorded
    assert any("symlink" in change for change in ctx.changes)


def test_ensure_symlink_backup_enables_rollback_restore(tmp_path: Path) -> None:
    """After .bak is created, prior content can be restored by moving the backup back."""
    skills_root = tmp_path / "skills"
    skills_root.mkdir()

    existing_dir = skills_root / "my-skill"
    existing_dir.mkdir()
    (existing_dir / "SKILL.md").write_text("user version before sync\n", encoding="utf-8")

    managed = tmp_path / "repo-skills" / "my-skill"
    managed.mkdir(parents=True)
    (managed / "SKILL.md").write_text("repo managed\n", encoding="utf-8")

    ctx = SyncContext(apply=True)
    ensure_symlink(ctx, existing_dir, managed)

    backup = skills_root / "my-skill.bak"
    assert backup.exists()

    # Simulate rollback: remove the symlink and restore backup into place
    if existing_dir.exists() or existing_dir.is_symlink():
        if existing_dir.is_symlink():
            existing_dir.unlink()
        elif existing_dir.is_dir():
            shutil.rmtree(existing_dir)
    shutil.move(str(backup), str(existing_dir))

    assert existing_dir.exists()
    assert existing_dir.is_dir()
    assert not backup.exists()
    assert (existing_dir / "SKILL.md").read_text(encoding="utf-8") == "user version before sync\n"


def test_ensure_symlink_does_not_backup_in_dry_run(tmp_path: Path) -> None:
    """When apply=False, ensure_symlink notes the action but leaves original and creates no .bak."""
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    existing = target_dir / "skill-dir"
    existing.mkdir()
    (existing / "SKILL.md").write_text("keep this\n", encoding="utf-8")

    managed = tmp_path / "managed" / "skill-dir"
    managed.mkdir(parents=True)
    (managed / "SKILL.md").write_text("would be linked\n", encoding="utf-8")

    ctx = SyncContext(apply=False)
    ensure_symlink(ctx, existing, managed)

    # Still a dir, no backup created
    assert existing.exists()
    assert existing.is_dir()
    assert not (target_dir / "skill-dir.bak").exists()
    assert any("symlink" in c for c in ctx.changes)


def test_config_drop_protection_still_works_negative(tmp_path: Path) -> None:
    """assert_no_config_drops and write_local_json_config reject writes that would drop keys (negative test)."""
    cfg_path = tmp_path / "settings.json"
    original = {
        "mcpServers": {"local-only": {"command": "local"}, "shared": {"command": "keep"}},
        "userOwned": {"custom": True, "nested": {"a": 1}},
    }
    cfg_path.write_text(json.dumps(original) + "\n", encoding="utf-8")

    current = load_json(cfg_path)
    # Rendered drops local-only and userOwned entirely
    rendered = {"mcpServers": {"managed": {"command": "uvx managed"}}}

    with pytest.raises(platform_base.ConfigDropError, match="would remove local config entries"):
        platform_base.assert_no_config_drops(cfg_path, current, rendered)

    # Also via write_local helper (uses the assert internally)
    ctx = SyncContext(apply=True)
    with pytest.raises(platform_base.ConfigDropError, match="would remove"):
        write_local_json_config(ctx, cfg_path, rendered)

    # Original file untouched because write_local never reached write on drop
    after = load_json(cfg_path)
    assert "local-only" in after.get("mcpServers", {})
    assert "userOwned" in after


def test_write_local_json_config_preserves_and_writes_when_no_drops(tmp_path: Path) -> None:
    """write_local_json_config succeeds (and writes on apply) when no drops detected."""
    cfg_path = tmp_path / "mcp.json"
    original = {"mcpServers": {"existing": {"command": "old"}}}
    cfg_path.write_text(json.dumps(original) + "\n", encoding="utf-8")

    # Merge adds without removing
    rendered = {
        "mcpServers": {
            "existing": {"command": "old"},
            "managed": {"command": "uv", "args": ["x", "foo"]},
        }
    }

    ctx = SyncContext(apply=True)
    write_local_json_config(ctx, cfg_path, rendered)

    written = load_json(cfg_path)
    assert "managed" in written["mcpServers"]
    assert "existing" in written["mcpServers"]
    assert any("update" in ch for ch in ctx.changes)


def test_cursor_rollback_home_mcp_merge_preserves_unknown_servers(tmp_path, monkeypatch) -> None:
    """Home MCP sync merges managed servers without dropping user-owned entries (rollback-safe merge)."""
    config_path = tmp_path / "mcp.json"
    config_path.write_text(
        json.dumps({
            "mcpServers": {"custom": {"command": "custom-mcp"}},
            "other": True,
        })
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cursor_platform, "CURSOR_HOME_MCP_PATH", config_path)

    adapter = cursor_platform.Adapter()
    ctx = cursor_platform.SyncContext(apply=True)
    registry = {
        "servers": {
            "managed": {
                "command": "uvx",
                "args": ["managed-mcp"],
                "enabled": True,
            }
        }
    }

    adapter.sync_home(ctx, registry, {}, {}, {})
    payload = json.loads(config_path.read_text(encoding="utf-8"))

    assert payload["other"] is True
    assert payload["mcpServers"]["custom"] == {"command": "custom-mcp"}
    assert payload["mcpServers"]["managed"]["command"] == "uvx"


def test_cursor_rollback_cli_sync_repo_writes_stable_cli_json(tmp_path, monkeypatch) -> None:
    """Project CLI is repo-managed full replace; repeat sync_repo is idempotent on disk."""
    monkeypatch.setattr(cursor_platform, "cursor_project_dir", lambda: tmp_path / ".cursor")
    adapter = cursor_platform.Adapter()
    cli_path = tmp_path / ".cursor" / "cli.json"
    cli_path.parent.mkdir(parents=True)
    cli_path.write_text('{"user": true}\n', encoding="utf-8")

    ctx = cursor_platform.SyncContext(apply=True)
    adapter.sync_repo(ctx, {"servers": {}}, {}, {})
    expected = adapter.render_cli_config({})
    assert json.loads(cli_path.read_text(encoding="utf-8")) == expected
    assert expected["permissions"]["allow"]
    assert expected["permissions"]["deny"]

    ctx2 = cursor_platform.SyncContext(apply=True)
    adapter.sync_repo(ctx2, {"servers": {}}, {}, {})
    assert json.loads(cli_path.read_text(encoding="utf-8")) == expected
    assert not ctx2.changes


def test_grok_rollback_merge_preserves_user_owned_tables(tmp_path, monkeypatch) -> None:
    """Grok config merge preserves user-owned TOML tables (merge-preservation rollback model)."""
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
    assert_no_grok_config_drops(current, rendered, registry)
    assert "[user_custom]" in rendered
    assert "flag = true" in rendered
    assert 'theme = "dark"' in rendered
