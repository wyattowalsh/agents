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


def test_hook_bridge_bundle_dispatch_uses_bundle_timeout_budget() -> None:
    source = (REPO_ROOT / BRIDGE_REL).read_text(encoding="utf-8")

    assert "const SINGLE_POLICY_TIMEOUT_MS = 5000" in source
    assert "const BUNDLE_TIMEOUT_SECONDS = 30" in source
    assert "const BUNDLE_TIMEOUT_MARGIN_MS = 1000" in source
    assert '"--bundle-timeout"' in source
    assert "String(BUNDLE_TIMEOUT_SECONDS)" in source
    assert "const commandTimeoutMs = isBundle" in source
    assert "BUNDLE_TIMEOUT_SECONDS * 1000 + BUNDLE_TIMEOUT_MARGIN_MS" in source
    assert "SINGLE_POLICY_TIMEOUT_MS" in source
    assert "timeout: commandTimeoutMs" in source


def test_deploy_plugins_copies_hook_bridge(tmp_path, monkeypatch) -> None:
    plugins_dir = tmp_path / "plugins"
    monkeypatch.setattr(opencode_platform, "OPENCODE_PLUGINS_DIR", plugins_dir)

    ctx = SyncContext(apply=True)
    opencode_platform.Adapter()._deploy_plugins(ctx)

    deployed = plugins_dir / "wagents-hook-bridge.ts"
    assert deployed.is_file()
    assert "WagentsHookBridgePlugin" in deployed.read_text(encoding="utf-8")


def test_hook_bridge_worker_tier_uses_runner_worker_socket() -> None:
    source = (REPO_ROOT / BRIDGE_REL).read_text(encoding="utf-8")
    assert "--worker-socket" in source
    assert "WAGENTS_HOOK_WORKER_SOCKET" in source
    assert "wagents-hook-worker.py" not in source
