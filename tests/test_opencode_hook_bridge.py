"""Tests for the OpenCode wagents hook bridge plugin and its deployment."""

from __future__ import annotations

from pathlib import Path

from wagents.platforms import opencode as opencode_platform
from wagents.platforms.base import SyncContext

REPO_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_REL = "platforms/opencode/plugins/wagents-hook-bridge.ts"


def test_hook_bridge_plugin_source_present_and_shaped() -> None:
    source = (REPO_ROOT / BRIDGE_REL).read_text(encoding="utf-8")
    assert "WagentsHookBridgePlugin" in source
    assert "tool.execute.before" in source
    assert "run-wagents-hook" in source
    # Enforce-tier, fail-open on missing runner.
    assert "--harness" in source
    assert "opencode" in source
    assert 'read: ["cursor-before-read-file-guard"]' in source


def test_deploy_plugins_copies_hook_bridge(tmp_path, monkeypatch) -> None:
    plugins_dir = tmp_path / "plugins"
    monkeypatch.setattr(opencode_platform, "OPENCODE_PLUGINS_DIR", plugins_dir)

    ctx = SyncContext(apply=True)
    opencode_platform.Adapter()._deploy_plugins(ctx)

    deployed = plugins_dir / "wagents-hook-bridge.ts"
    assert deployed.is_file()
    assert "WagentsHookBridgePlugin" in deployed.read_text(encoding="utf-8")
