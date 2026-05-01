"""Tests for cross-agent bundle and plugin distribution metadata."""

import json
from pathlib import Path

import jsonschema

from wagents.openspec import OPENSPEC_PACKAGE, OPENSPEC_TOOL_BY_AGENT, format_min_node_version

ROOT = Path(__file__).resolve().parents[1]

OPENCODE_RUNTIME_PLUGINS = {
    "@plannotator/opencode@latest",
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

OPENCODE_DEPRECATED_PLUGINS = {
    "open-plan-annotator@latest",
}


def load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text())


def opencode_plugin_name(plugin_spec: str | list) -> str:
    if isinstance(plugin_spec, str):
        return plugin_spec
    return plugin_spec[0]


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
        plugin_name = opencode_plugin_name(plugin_spec)
        assert plugin_name.endswith("@latest"), f"{plugin_name} must use @latest"


def test_opencode_project_plugins_include_runtime_integrations():
    config = load_json("opencode.json")
    plugin_names = {opencode_plugin_name(plugin_spec) for plugin_spec in config["plugin"]}

    assert OPENCODE_RUNTIME_PLUGINS.issubset(plugin_names)


def test_opencode_plan_review_plugin_stays_plan_agent_scoped():
    config = load_json("opencode.json")

    [plugin_spec] = [
        plugin_spec
        for plugin_spec in config["plugin"]
        if opencode_plugin_name(plugin_spec) == "@plannotator/opencode@latest"
    ]

    assert plugin_spec[1] == {"workflow": "plan-agent", "planningAgents": ["plan"]}


def test_opencode_project_plugins_exclude_tui_only_plugins():
    config = load_json("opencode.json")
    plugin_names = {opencode_plugin_name(plugin_spec) for plugin_spec in config["plugin"]}

    for plugin_spec in OPENCODE_TUI_ONLY_PLUGINS:
        assert plugin_spec not in plugin_names


def test_opencode_project_plugins_exclude_deferred_workflow_plugins():
    config = load_json("opencode.json")
    plugin_names = {opencode_plugin_name(plugin_spec) for plugin_spec in config["plugin"]}

    for plugin_spec in OPENCODE_DEFERRED_WORKFLOW_PLUGINS:
        assert plugin_spec not in plugin_names


def test_opencode_project_plugins_exclude_deprecated_plan_plugins():
    config = load_json("opencode.json")
    plugin_names = {opencode_plugin_name(plugin_spec) for plugin_spec in config["plugin"]}

    for plugin_spec in OPENCODE_DEPRECATED_PLUGINS:
        assert plugin_spec not in plugin_names


def test_opencode_project_plugins_exclude_known_unresolved_packages():
    config = load_json("opencode.json")
    plugin_names = {opencode_plugin_name(plugin_spec) for plugin_spec in config["plugin"]}

    assert all(not plugin_spec.startswith("opencode-shell-strategy") for plugin_spec in plugin_names)


def test_platform_overhaul_registries_validate_against_schemas():
    registry_pairs = (
        ("config/support-tier-registry.json", "config/schemas/support-tier-registry.schema.json"),
        ("config/harness-surface-registry.json", "config/schemas/harness-surface-registry.schema.json"),
        ("config/config-transaction-registry.json", "config/schemas/config-transaction-registry.schema.json"),
        ("config/docs-artifact-registry.json", "config/schemas/docs-artifact-registry.schema.json"),
        ("config/skill-registry-policy.json", "config/schemas/skill-registry-policy.schema.json"),
        ("config/mcp-registry.json", "config/schemas/mcp-registry.schema.json"),
        ("config/plugin-extension-registry.json", "config/schemas/plugin-extension-registry.schema.json"),
        (
            "planning/manifests/mcp-conformance-requirements.json",
            "config/schemas/mcp-conformance-requirements.schema.json",
        ),
        (
            "planning/manifests/security-quarantine-register.json",
            "config/schemas/security-quarantine-register.schema.json",
        ),
        (
            "planning/manifests/external-repo-evaluation-summary.json",
            "config/schemas/external-repo-evaluation-summary.schema.json",
        ),
        (
            "planning/manifests/repo-sync-inventory.json",
            "config/schemas/repo-sync-inventory.schema.json",
        ),
        (
            "planning/manifests/repo-drift-ledger.json",
            "config/schemas/repo-drift-ledger.schema.json",
        ),
        (
            "planning/manifests/harness-fixture-support.json",
            "config/schemas/harness-fixture-support.schema.json",
        ),
    )

    for registry_path, schema_path in registry_pairs:
        jsonschema.validate(load_json(registry_path), load_json(schema_path))


def test_harness_surface_registry_splits_cloud_desktop_cli_and_editor_variants():
    registry = load_json("config/harness-surface-registry.json")
    harnesses = {record["id"]: record for record in registry["harnesses"]}

    expected_ids = {
        "claude-code",
        "claude-desktop",
        "chatgpt",
        "codex",
        "github-copilot-web",
        "github-copilot-cli",
        "opencode",
        "gemini-cli",
        "antigravity",
        "cursor-editor",
        "cursor-agent-web",
        "cursor-agent-cli",
        "perplexity-desktop",
        "cherry-studio",
    }

    assert expected_ids.issubset(harnesses)
    assert harnesses["cursor-agent-web"]["support_tier"] == "planned-research-backed"
    assert harnesses["cursor-agent-cli"]["support_tier"] == "planned-research-backed"
    assert harnesses["perplexity-desktop"]["support_tier"] == "experimental"
    assert harnesses["cherry-studio"]["support_tier"] == "experimental"
    assert "skills" not in harnesses["claude-desktop"]["projection_surfaces"]
    assert "skills" not in harnesses["chatgpt"]["projection_surfaces"]


def test_registry_core_freezes_support_tiers_and_plugin_sources():
    support_tiers = load_json("config/support-tier-registry.json")
    skill_policy = load_json("config/skill-registry-policy.json")
    plugin_registry = load_json("config/plugin-extension-registry.json")

    assert set(support_tiers["tiers"]) == {
        "validated",
        "repo-present-validation-required",
        "planned-research-backed",
        "experimental",
        "unverified",
        "unsupported",
        "quarantine",
    }
    assert "quarantine-external" in skill_policy["source_classes"]
    assert {plugin["id"] for plugin in plugin_registry["plugins"]} >= {
        "claude-code-plugin",
        "codex-plugin",
        "opencode-runtime-plugins",
        "cherry-studio-mcp-import",
    }


def test_mcp_and_quarantine_planning_manifests_cover_required_gates():
    mcp_requirements = load_json("planning/manifests/mcp-conformance-requirements.json")
    quarantine = load_json("planning/manifests/security-quarantine-register.json")

    assert set(mcp_requirements["required_fields"]) >= {
        "transport_model",
        "auth_model",
        "secrets_model",
        "sandbox_model",
        "smoke_fixture",
        "skill_replacement_fit",
    }
    assert {record["id"] for record in quarantine["external_repo_records"]} >= {
        "EXT-011",
        "EXT-015",
        "EXT-017",
        "EXT-084",
    }
    assert "auth-bridging" in quarantine["quarantine_triggers"]


def test_repo_sync_inventory_covers_sync_manifest_paths():
    sync_manifest = load_json("config/sync-manifest.json")
    inventory = load_json("planning/manifests/repo-sync-inventory.json")
    drift_ledger = load_json("planning/manifests/repo-drift-ledger.json")

    sync_paths = {record["path"] for record in sync_manifest["managed"]}
    inventory_paths = {record["path"] for record in inventory["records"]}
    drift_paths = {record["path"] for record in drift_ledger["records"]}

    assert sync_paths <= inventory_paths
    assert inventory_paths <= drift_paths

    sync_modes_by_path = {record["path"]: record["mode"] for record in sync_manifest["managed"]}
    for record in inventory["records"]:
        assert record["mode"] == sync_modes_by_path[record["path"]]
        assert record["owner_change"].startswith("agents-c") or record["owner_change"] == "agents-platform-overhaul"
        assert record["secret_handling"] in {"not-secret-bearing", "path-only", "redacted", "unknown"}
        assert record["drift_policy"] in {"canonical", "generated", "merged", "symlink", "symlinked-entries"}


def test_harness_fixture_support_covers_every_harness_without_tier_promotion():
    harness_registry = load_json("config/harness-surface-registry.json")
    fixture_support = load_json("planning/manifests/harness-fixture-support.json")

    harnesses = {record["id"]: record for record in harness_registry["harnesses"]}
    support = {record["harness_id"]: record for record in fixture_support["records"]}

    assert set(harnesses) == set(support)

    for harness_id, harness in harnesses.items():
        evidence = support[harness_id]
        assert evidence["current_support_tier"] == harness["support_tier"]
        assert evidence["owner_change"] == harness["owner_change"]
        assert evidence["fixture_status"] in {
            "fixture-backed",
            "fixture-plan-only",
            "docs-ledger-required",
            "blocked",
        }
        assert evidence["validation_commands"]
        assert evidence["rollback_coverage"] in {"present", "planned", "not-applicable", "blocked"}

        if harness["support_tier"] != "validated":
            assert evidence["promotion_blocker"]
