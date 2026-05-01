"""Tests for cross-agent bundle and plugin distribution metadata."""

import json
from pathlib import Path

from wagents.openspec import OPENSPEC_PACKAGE, OPENSPEC_TOOL_BY_AGENT, format_min_node_version

ROOT = Path(__file__).resolve().parents[1]

OPENCODE_RUNTIME_PLUGINS = {
    "opencode-scheduler@latest",
    "opencode-claude-auth@latest",
    "opencode-plugin-langfuse@latest",
}

OPENCODE_TUI_ONLY_PLUGINS = {
    "opencode-subagent-statusline@latest",
}

OPENCODE_DEFERRED_WORKFLOW_PLUGINS = {
    "@codemcp/workflows-opencode@latest",
    "@codemcp/workflows-opencode-tui@latest",
}


def load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text())


def test_agent_bundle_points_to_canonical_sources():
    bundle = load_json("agent-bundle.json")

    assert bundle["name"] == "agents"
    assert "reserved for future bundled agent definitions" in bundle["description"]
    assert bundle["source"]["repository"] == "wyattowalsh/agents"
    assert bundle["source"]["skillsSource"] == "github:wyattowalsh/agents"
    assert bundle["components"]["skills"] == "./skills/"
    assert bundle["components"]["openspec"] == "./openspec/"
    assert bundle["adapters"]["claude-code"]["pluginManifest"] == "./.claude-plugin/plugin.json"
    assert bundle["adapters"]["codex"]["pluginManifest"] == "./.codex-plugin/plugin.json"
    assert bundle["adapters"]["openspec"]["package"] == OPENSPEC_PACKAGE
    assert bundle["adapters"]["openspec"]["minimumNode"] == format_min_node_version()
    assert bundle["adapters"]["openspec"]["toolMapping"] == OPENSPEC_TOOL_BY_AGENT


def test_claude_plugin_manifest_uses_repo_root_components():
    manifest = load_json(".claude-plugin/plugin.json")

    assert manifest["name"] == "agents"
    assert "version" not in manifest
    assert (ROOT / manifest["skills"]).is_dir()
    assert (ROOT / manifest["agents"]).is_dir()
    assert (ROOT / manifest["mcpServers"]).is_file()


def test_claude_marketplace_exposes_repo_root_plugin_without_version_pin():
    marketplace = load_json(".claude-plugin/marketplace.json")

    assert marketplace["name"] == "agents"
    assert marketplace["owner"]["name"]
    assert len(marketplace["plugins"]) == 1
    plugin = marketplace["plugins"][0]
    assert plugin["name"] == "agents"
    assert plugin["source"] == "./"
    assert "version" not in plugin


def test_codex_plugin_manifest_and_marketplace_are_git_backed():
    manifest = load_json(".codex-plugin/plugin.json")
    marketplace = load_json(".agents/plugins/marketplace.json")

    assert manifest["name"] == "agents"
    assert "version" not in manifest
    assert manifest["skills"] == "./skills/"
    assert (ROOT / manifest["skills"]).is_dir()
    assert (ROOT / manifest["mcpServers"]).is_file()

    assert marketplace["name"] == "agents"
    assert len(marketplace["plugins"]) == 1
    plugin = marketplace["plugins"][0]
    assert plugin["name"] == "agents"
    assert plugin["source"] == {
        "source": "url",
        "url": "https://github.com/wyattowalsh/agents.git",
        "ref": "main",
    }
    assert plugin["policy"]["installation"] == "AVAILABLE"


def test_opencode_project_plugins_use_latest_dist_tag():
    config = load_json("opencode.json")

    for plugin_spec in config["plugin"]:
        assert plugin_spec.endswith("@latest"), f"{plugin_spec} must use @latest"


def test_opencode_project_plugins_include_runtime_integrations():
    config = load_json("opencode.json")

    assert OPENCODE_RUNTIME_PLUGINS.issubset(config["plugin"])


def test_opencode_project_plugins_exclude_tui_only_plugins():
    config = load_json("opencode.json")

    for plugin_spec in OPENCODE_TUI_ONLY_PLUGINS:
        assert plugin_spec not in config["plugin"]


def test_opencode_project_plugins_exclude_deferred_workflow_plugins():
    config = load_json("opencode.json")

    for plugin_spec in OPENCODE_DEFERRED_WORKFLOW_PLUGINS:
        assert plugin_spec not in config["plugin"]


def test_opencode_project_plugins_exclude_known_unresolved_packages():
    config = load_json("opencode.json")

    assert all(not plugin_spec.startswith("opencode-shell-strategy") for plugin_spec in config["plugin"])
