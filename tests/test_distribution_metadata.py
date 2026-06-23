"""Tests for cross-agent bundle and plugin distribution metadata."""

import hashlib
import json
import re
import subprocess
from pathlib import Path

import jsonschema

from wagents.openspec import OPENSPEC_PACKAGE, OPENSPEC_TOOL_BY_AGENT, format_min_node_version

ROOT = Path(__file__).resolve().parents[1]
OWNER_CHANGE_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

OPENCODE_RUNTIME_PLUGINS = {
    "@plannotator/opencode@latest",
    "@slkiser/opencode-quota@latest",
    "@gotgenes/opencode-agent-identity@latest",
    "@hueyexe/opencode-ensemble@latest",
    "btw-opencode@latest",
    "opencode-adaptive-thinking@latest",
    "opencode-history-search@latest",
    "opencode-ignore@latest",
    "opencode-large-image-optimizer@latest",
    "opencode-lmstudio@latest",
    "opencode-pty@latest",
    "opencode-token-monitor@latest",
    "opencode-wakatime@latest",
    "opencode-scheduler@latest",
    "opencode-claude-auth@latest",
    "opencode-plugin-langfuse@latest",
    "opencode-rules@latest",
    "opencode-terminal-progress@latest",
    "octto@latest",
}

OPENCODE_TUI_ONLY_PLUGINS = {
    "@ishaksebsib/opencode-tree@latest",
    "@thiagos1lva/opencode-token-usage-chart@latest",
    "opencode-subagent-statusline@latest",
}

OPENCODE_OCX_SURFACE_FILES = {
    ".opencode/ocx.jsonc",
    ".ocx/receipt.jsonc",
    ".opencode/package.json",
}

OPENCODE_DEFERRED_WORKFLOW_PLUGINS = {
    "@codemcp/workflows-opencode@latest",
    "@codemcp/workflows-opencode-tui@latest",
}

OPENCODE_DEPRECATED_PLUGINS = {
    "open-plan-annotator@latest",
    "opencode-auto-resume@latest",
}


def load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text())


def opencode_plugin_name(plugin_spec: str | list) -> str:
    if isinstance(plugin_spec, str):
        return plugin_spec
    return plugin_spec[0]


def assert_git_tracked(relative_path: str) -> None:
    subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def test_agent_bundle_points_to_canonical_sources():
    bundle = load_json("agent-bundle.json")

    assert bundle["name"] == "agents"
    assert "bundled agent definitions" in bundle["description"]
    assert bundle["source"]["repository"] == "wyattowalsh/agents"
    assert bundle["source"]["skillsSource"] == "github:wyattowalsh/agents"
    assert bundle["components"]["skills"] == "./skills/"
    assert bundle["components"]["openspec"] == "./openspec/"
    assert bundle["adapters"]["claude-code"]["pluginManifest"] == "./.claude-plugin/plugin.json"
    assert bundle["adapters"]["codex"]["pluginManifest"] == "./.codex-plugin/plugin.json"
    assert bundle["adapters"]["openspec"]["package"] == OPENSPEC_PACKAGE
    assert bundle["adapters"]["openspec"]["minimumNode"] == format_min_node_version()
    assert bundle["adapters"]["openspec"]["toolMapping"] == OPENSPEC_TOOL_BY_AGENT

    # apm adapter (Wave 4) - assert structure when present
    if "apm" in bundle.get("adapters", {}):
        apm = bundle["adapters"]["apm"]
        assert "install" in apm
        assert "update" in apm
        assert "audit" in apm
        assert "compile" in apm
        assert "materialize" in apm
        assert apm["install"]  # non-empty command
        # explicit keys per Wave 4 polish
        assert {"install", "audit", "materialize"} <= set(apm.keys())


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
    assert manifest["agents"] == "./agents/"
    assert (ROOT / manifest["skills"]).is_dir()
    assert (ROOT / manifest["agents"]).is_dir()
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


def test_opencode_project_config_enforces_openai_and_tooling_defaults():
    config = load_json("opencode.json")

    assert config["model"] == "openai/gpt-5.5"
    assert config["small_model"] == "openai/gpt-5.4-mini"
    assert config["autoupdate"] == "notify"
    expected_agent = {
        "model": "openai/gpt-5.5",
        "variant": "xhigh",
        "options": {"reasoningEffort": "xhigh"},
    }
    assert config["agent"]["build"] == expected_agent
    assert config["agent"]["plan"] == expected_agent
    assert config["agent"]["explore"] == expected_agent
    assert config["agent"]["general"] == expected_agent

    openai = config["provider"]["openai"]
    assert openai["options"]["reasoningEffort"] == "xhigh"
    assert openai["options"]["websearch_cited"] == {"model": "gpt-5.5"}
    assert set(openai["models"]) == {"gpt-5.5", "gpt-5.4-mini", "gpt-5.3-codex-spark"}
    assert '"reasoningSummary": "auto"' not in json.dumps(openai)

    assert set(config["formatter"]) == {"biome", "prettier", "ruff", "shell", "toml", "just", "gofmt", "rustfmt"}
    assert config["formatter"]["ruff"]["command"] == ["ruff", "format", "$FILE"]
    assert config["lsp"]["ruff"]["command"] == ["ruff", "server"]
    assert config["lsp"]["ty"]["command"] == ["ty", "server"]
    assert config["experimental"] == {
        "disable_paste_summary": False,
        "batch_tool": True,
        "openTelemetry": True,
        "continue_loop_on_deny": True,
        "mcp_timeout": 120000,
    }
    assert config["permission"]["lsp"] == "allow"
    assert config["tool_output"] == {"max_lines": 4000, "max_bytes": 120000}


def test_opencode_plan_review_plugin_stays_plan_agent_scoped():
    config = load_json("opencode.json")

    [plugin_spec] = [
        plugin_spec
        for plugin_spec in config["plugin"]
        if opencode_plugin_name(plugin_spec) == "@plannotator/opencode@latest"
    ]

    assert plugin_spec[1] == {"workflow": "plan-agent", "planningAgents": ["plan"]}


def test_opencode_large_image_optimizer_config_enables_openai():
    config = load_json("config/opencode-large-image-optimizer.json")

    assert config == {
        "providers": {
            "anthropic": True,
            "google": True,
            "openai": True,
        },
        "defaultPolicy": True,
    }


def test_opencode_ignore_patterns_cover_secret_and_generated_paths():
    ignore_text = (ROOT / ".ignore").read_text(encoding="utf-8")

    assert ".env*" in ignore_text
    assert "!.env.example" in ignore_text
    assert "mcp/secrets/**" in ignore_text
    assert ".opencode/skills/**" in ignore_text
    assert "node_modules/**" in ignore_text


def test_context_cache_plugin_is_vendored_without_raw_key_logging():
    plugin_source = (ROOT / "platforms/opencode/plugins/opencode-context-cache.mjs").read_text(encoding="utf-8")

    assert "promptCacheKey" in plugin_source
    assert 'PROMPT_CACHE_PROVIDER_IDS = new Set(["openai"])' in plugin_source
    assert "Skipping prompt cache for provider" in plugin_source
    assert "x-session-id" in plugin_source
    assert "OPENCODE_PROMPT_CACHE_KEY" in plugin_source
    assert "Raw:" not in plugin_source


def test_octto_primary_inherit_plugin_removes_only_primary_model_pin():
    plugin_source = (ROOT / "platforms/opencode/plugins/octto-primary-inherit.mjs").read_text(encoding="utf-8")

    assert "config?.agent?.octto" in plugin_source
    assert "delete octtoAgent.model" in plugin_source
    assert "bootstrapper" in plugin_source
    assert "probe" in plugin_source


def test_incomplete_resume_plugin_uses_conservative_explicit_trigger():
    plugin_source = (ROOT / "platforms/opencode/plugins/opencode-incomplete-resume.mjs").read_text(encoding="utf-8")

    assert "MAX_CONTINUES = 3" in plugin_source
    assert "COOLDOWN_MS = 2000" in plugin_source
    assert "TASK_STATUS:\\s*INCOMPLETE" in plugin_source
    assert "const TRIGGER_PHRASES = [/TASK_STATUS:\\s*INCOMPLETE/i]" in plugin_source
    assert "continue\\s*working" not in plugin_source
    assert "resume\\s*task" not in plugin_source
    assert "next\\s*step" not in plugin_source
    assert "client.app.log" not in plugin_source
    assert 'event.type !== "session.idle" && event.type !== "message.updated"' in plugin_source
    assert "sessionIdFromEvent" not in plugin_source


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


def test_opencode_project_plugins_exclude_ocx_component_plugins():
    config = load_json("opencode.json")
    plugin_names = {opencode_plugin_name(plugin_spec) for plugin_spec in config["plugin"]}

    assert "ocx@latest" not in plugin_names
    assert "opencode-worktree@latest" not in plugin_names
    assert "opencode-background-agents@latest" not in plugin_names


def test_opencode_ocx_worktree_component_files_are_tracked_surfaces():
    receipt = load_json(".ocx/receipt.jsonc")
    assert not Path(receipt["root"]).is_absolute()

    component_files = {
        component_file["path"]: component_file["hash"]
        for component in receipt["installed"].values()
        for component_file in component["files"]
    }

    for component_file in OPENCODE_OCX_SURFACE_FILES | set(component_files):
        assert (ROOT / component_file).is_file()
        assert_git_tracked(component_file)

    for component_file, expected_hash in component_files.items():
        digest = hashlib.sha256((ROOT / component_file).read_bytes()).hexdigest()
        assert digest == expected_hash


def test_opencode_worktree_config_template_avoids_secret_copy_examples():
    worktree_source = (ROOT / ".opencode/plugin/worktree.ts").read_text()

    assert 'Example: [".env"' not in worktree_source
    assert "allowRepoCommands" in worktree_source
    assert "isSensitiveSyncPath" in worktree_source
    assert "normalizedLower" in worktree_source
    assert 'basename === ".env"' in worktree_source
    assert '".npmrc"' in worktree_source
    assert '".ssh"' in worktree_source
    assert '".docker/config.json"' in worktree_source
    assert '".docker"' in worktree_source
    assert '".cargo"' in worktree_source
    assert '".envrc"' in worktree_source
    assert '".direnv"' in worktree_source
    assert "isSafeSyncSource" in worktree_source
    assert "prepareSafeDestinationParent" in worktree_source
    assert "Refusing to overwrite symlink destination" in worktree_source
    assert worktree_source.index("Refusing to overwrite symlink destination") < worktree_source.index(
        "await Bun.write(targetPath"
    )
    assert "isSymbolicLink" in worktree_source
    assert "cleanupForkContext" in worktree_source
    assert "safeStateSubdir" in worktree_source
    assert "resolveSafeStateSubdir" in worktree_source
    assert 'stdout: "pipe"' in worktree_source
    assert '"--force"' not in worktree_source
    assert "Patterns to exclude from copying" not in worktree_source
    assert "Reserved for future use; sync exclusions are not currently enforced" in worktree_source
    assert "profile check exited" in worktree_source


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
        "cursor-cli",
        "cursor-cloud-agent",
        "cursor-cloud-subagent",
        "cursor-bugbot",
        "cursor-acp",
        "grok-build",
        "perplexity-desktop",
        "cherry-studio",
    }

    assert expected_ids.issubset(harnesses)
    assert harnesses["cursor-cloud-agent"]["support_tier"] == "planned-research-backed"
    assert harnesses["cursor-cli"]["support_tier"] == "repo-present-validation-required"
    assert harnesses["perplexity-desktop"]["support_tier"] == "experimental"
    assert harnesses["cherry-studio"]["support_tier"] == "experimental"
    assert "skills" not in harnesses["claude-desktop"]["projection_surfaces"]
    assert "skills" not in harnesses["chatgpt"]["projection_surfaces"]
    assert "hooks" in harnesses["grok-build"]["projection_surfaces"]


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
    known_opencode_sync_paths = {
        "${REPO_ROOT}/config/opencode-dcp.jsonc",
        "${REPO_ROOT}/config/opencode-large-image-optimizer.json",
        "${REPO_ROOT}/config/opencode-notifier.json",
        "${REPO_ROOT}/config/opencode-tui-plugins.json",
        "${REPO_ROOT}/config/opencode-quota-toast.json",
        "${REPO_ROOT}/config/opencode-token-monitor.json",
        "${REPO_ROOT}/config/opencode-ensemble.json",
        "${REPO_ROOT}/config/opencode-octto.json",
        "~/.config/opencode/dcp.jsonc",
        "~/.config/opencode/large-image-optimizer.json",
        "~/.config/opencode/opencode-notifier.json",
        "~/.config/opencode/tui.json",
        "~/.config/opencode/opencode-quota/quota-toast.json",
        "~/.config/opencode/token-monitor.json",
        "~/.config/opencode/ensemble.json",
        "~/.config/opencode/octto.json",
    }

    sync_paths = {record["path"] for record in sync_manifest["managed"]}
    inventory_paths = {record["path"] for record in inventory["records"]}
    drift_paths = {record["path"] for record in drift_ledger["records"]}

    assert known_opencode_sync_paths <= sync_paths
    assert sync_paths <= inventory_paths
    assert inventory_paths <= drift_paths

    sync_modes_by_path = {record["path"]: record["mode"] for record in sync_manifest["managed"]}
    for record in inventory["records"]:
        assert record["mode"] == sync_modes_by_path[record["path"]]
        assert OWNER_CHANGE_RE.fullmatch(record["owner_change"])
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
            "fixture-executable",
            "fixture-plan-only",
            "docs-ledger-required",
            "blocked",
        }
        assert evidence["validation_commands"]
        assert evidence["rollback_coverage"] in {"present", "planned", "not-applicable", "blocked"}

        if harness["support_tier"] != "validated":
            assert evidence["promotion_blocker"]
