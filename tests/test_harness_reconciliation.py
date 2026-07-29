"""Static checks for the local harness reconciliation evidence packet."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast

from wagents.installed_inventory import HarnessQueryResult, InstalledInventorySnapshot, InstalledSkillInventoryRow

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "planning" / "manifests" / "harness-reconciliation.json"
TERMINAL_ACTIONS = {
    "synced",
    "repo-source-synced",
    "local-only-preserve",
    "curate-external",
    "catalog-non-sync",
    "cache-refresh-needed",
    "home-sync-needed",
    "blocked-needs-approval",
    "config-repair-needed",
}
SUPPORTED_SKILL_AGENTS = {
    "claude-code",
    "codex",
    "crush",
    "cursor",
    "grok",
    "opencode",
}


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def load_generator_module():
    module_path = ROOT / "scripts" / "generate_harness_reconciliation.py"
    spec = importlib.util.spec_from_file_location("generate_harness_reconciliation", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def count_skill_agents(manifest: dict, *, field: str, provenance_statuses: set[str]) -> dict[str, int]:
    counts = dict.fromkeys(SUPPORTED_SKILL_AGENTS, 0)
    for row in manifest["matrix"]:
        if row["asset_type"] != "skill":
            continue
        if row.get("provenance_status") not in provenance_statuses:
            continue
        for agent in row.get(field, []):
            counts[agent] = counts.get(agent, 0) + 1
    return counts


def test_harness_reconciliation_manifest_has_terminal_dispositions() -> None:
    manifest = load_manifest()

    assert manifest["version"] == 1
    assert manifest["generated_by"] == "scripts/generate_harness_reconciliation.py"
    assert set(manifest["terminal_actions"]) == TERMINAL_ACTIONS
    assert manifest["summary"]["row_count"] == len(manifest["matrix"])

    for row in manifest["matrix"]:
        assert row["action"] in TERMINAL_ACTIONS
        assert row["classification"] in TERMINAL_ACTIONS
        assert row["asset_type"] in {"extension", "plugin", "plugin-cache", "skill"}
        assert row["harness"]
        assert row["name"]
        assert row["evidence"]
        assert row["owner"] in {"catalog", "repo", "unknown", "user-local"}


def test_harness_reconciliation_records_full_skill_sync_result() -> None:
    manifest = load_manifest()
    skills = manifest["summary"]["skills"]
    default_missing = skills["default_sync_missing_by_agent"]
    include_installed_missing = skills["include_installed_missing_by_agent"]
    query_blocked = skills["query_blocked_by_agent"]

    assert skills["desired_count"] > 0
    assert set(default_missing) == SUPPORTED_SKILL_AGENTS
    assert set(include_installed_missing) == SUPPORTED_SKILL_AGENTS
    assert set(query_blocked) == SUPPORTED_SKILL_AGENTS

    default_statuses = {"repo-owned", "verified-curated-external"}
    assert default_missing == count_skill_agents(
        manifest,
        field="missing_agents",
        provenance_statuses=default_statuses,
    )
    assert include_installed_missing == count_skill_agents(
        manifest,
        field="missing_agents",
        provenance_statuses={*default_statuses, "installed-external"},
    )
    assert query_blocked == count_skill_agents(
        manifest,
        field="query_blocked_agents",
        provenance_statuses=default_statuses,
    )

    if not skills["query_errors"]:
        assert all(count == 0 for count in default_missing.values())
        assert all(count == 0 for count in query_blocked.values())
    else:
        assert any(count > 0 for count in default_missing.values()) or any(
            count > 0 for count in query_blocked.values()
        )


def test_harness_reconciliation_covers_plugin_drift_and_config_blockers() -> None:
    manifest = load_manifest()
    rows = {(row["harness"], row["name"]): row for row in manifest["matrix"]}

    assert rows["codex", "agents@agents"]["action"] == "cache-refresh-needed"
    assert rows["codex", "agents@agents-cache"]["action"] == "cache-refresh-needed"
    assert rows["opencode", "opencode-adaptive-thinking@latest"]["action"] == "synced"
    assert rows["opencode", "opencode-claude-auth@latest"]["action"] == "synced"

    assert not any(
        row["harness"] in {"antigravity", "gemini-cli", "github-copilot"}
        for row in manifest["matrix"]
    )


def test_harness_reconciliation_records_opencode_plugin_source_surfaces() -> None:
    manifest = load_manifest()
    opencode_rows = [
        row for row in manifest["matrix"] if row["harness"] == "opencode" and row["asset_type"] == "plugin"
    ]
    expected_path_by_surface = {
        "repo": "opencode.json",
        "live": "~/.config/opencode/opencode.json",
        "tui": "~/.config/opencode/tui.json",
    }

    assert opencode_rows
    for row in opencode_rows:
        expected_paths = [path for surface, path in expected_path_by_surface.items() if row["installed_state"][surface]]
        assert row["source_paths"] == expected_paths
        assert row["source_path"] == expected_paths[0]

    tui_only = next(row for row in opencode_rows if row["name"] == "@ishaksebsib/opencode-tree@latest")
    assert tui_only["installed_state"] == {"live": False, "repo": False, "tui": True}
    assert tui_only["source_path"] == "~/.config/opencode/tui.json"
    assert tui_only["source_paths"] == ["~/.config/opencode/tui.json"]


def test_native_plugin_detection_requires_successful_positive_output() -> None:
    module = load_generator_module()

    assert not module._native_plugins_reported({"ok": False, "stdout": "", "stderr": "missing command"})
    assert not module._native_plugins_reported({"ok": False, "stdout": "plugin-a\n", "stderr": "timed out"})
    assert not module._native_plugins_reported({"ok": True, "stdout": "", "stderr": ""})
    assert not module._native_plugins_reported({"ok": True, "stdout": "No plugins installed\n", "stderr": ""})
    assert not module._native_plugins_reported({"ok": True, "stdout": "0 plugins\n", "stderr": ""})
    assert module._native_plugins_reported({"ok": True, "stdout": "plugin-a installed, enabled\n", "stderr": ""})


def test_skill_rows_subtracts_owner_covered_agents_and_exports_cleanup_metadata(monkeypatch) -> None:
    module = load_generator_module()
    row = InstalledSkillInventoryRow(
        name="repo-owned-skill",
        path="",
        source_path="skills/repo-owned-skill/SKILL.md",
        scope="desired",
        description="Repo owned.",
        license="",
        version="",
        author="",
        source="github:wyattowalsh/agents",
        install_source="github:wyattowalsh/agents",
        source_url="https://github.com/wyattowalsh/agents",
        install_command="npx skills add github:wyattowalsh/agents --skill repo-owned-skill -y -g",
        provenance_status="repo-owned",
        trust_tier="repo-owned",
        selector_mode="named",
        installed_agents=(),
        discovered_in=(),
        target_agents=("codex", "opencode", "claude-code"),
        sync_kind="skills-cli",
        docs_status="documented",
    )
    exposure = SimpleNamespace(
        name="repo-owned-skill",
        duplicate_class="same-realpath",
        cleanup_action="remove-generated-symlink",
        docs_status="documented",
        canonical_owner="plugin",
        exposure_owner="skills-cli",
    )

    monkeypatch.setattr(module, "read_external_skill_entries", lambda strict=True: [])
    monkeypatch.setattr(module, "collect_installed_inventory", lambda **kwargs: SimpleNamespace(queries=()))
    monkeypatch.setattr(module, "collect_desired_sync_rows", lambda **kwargs: (row,))
    monkeypatch.setattr(module, "merge_desired_with_installed", lambda snapshot, desired: SimpleNamespace(rows=desired))
    monkeypatch.setattr(module, "collect_skill_cleanup_exposures", lambda: (exposure,))
    monkeypatch.setattr(module, "supported_agent_ids", lambda: ("codex", "opencode", "claude-code"))
    monkeypatch.setattr(
        module,
        "repo_skill_owner_covered_agents",
        lambda row, target_agents, **kwargs: tuple(agent for agent in target_agents if agent in {"codex", "opencode"}),
    )

    rows, summary = module._skill_rows()

    assert rows[0]["owner_covered_agents"] == ["codex", "opencode"]
    assert rows[0]["missing_agents"] == ["claude-code"]
    assert rows[0]["store_missing_agents"] == ["claude-code"]
    assert rows[0]["projection_missing_agents"] == []
    assert rows[0]["exposure_owner"] == "plugin"
    assert rows[0]["duplicate_class"] == "same-realpath"
    assert rows[0]["cleanup_action"] == "remove-generated-symlink"
    assert rows[0]["docs_status"] == "documented"
    assert summary["default_sync_missing_by_agent"]["codex"] == 0
    assert summary["default_sync_missing_by_agent"]["opencode"] == 0
    assert summary["default_sync_missing_by_agent"]["claude-code"] == 1
    assert summary["store_missing_by_agent"]["claude-code"] == 1
    assert summary["projection_missing_by_agent"]["claude-code"] == 0


def test_skill_rows_cursor_store_only_counts_projection_missing(monkeypatch, tmp_path) -> None:
    module = load_generator_module()
    home = tmp_path / "home"
    store = home / ".agents" / "skills" / "cursor-skill"
    store.mkdir(parents=True)
    (store / "SKILL.md").write_text(
        "---\nname: cursor-skill\ndescription: t\n---\n\nbody\n",
        encoding="utf-8",
    )
    row = InstalledSkillInventoryRow(
        name="cursor-skill",
        path="",
        source_path="skills/cursor-skill/SKILL.md",
        scope="desired",
        description="Cursor skill.",
        license="",
        version="",
        author="",
        source="github:wyattowalsh/agents",
        install_source="github:wyattowalsh/agents",
        source_url="https://github.com/wyattowalsh/agents",
        install_command="npx skills add github:wyattowalsh/agents --skill cursor-skill -y -g",
        provenance_status="repo-owned",
        trust_tier="repo-owned",
        selector_mode="named",
        installed_agents=(),
        discovered_in=(),
        target_agents=("cursor",),
        sync_kind="skills-cli",
        docs_status="documented",
    )

    monkeypatch.setattr(module, "HOME", home)
    monkeypatch.setattr(module, "read_external_skill_entries", lambda strict=True: [])
    monkeypatch.setattr(module, "collect_installed_inventory", lambda **kwargs: SimpleNamespace(queries=()))
    monkeypatch.setattr(module, "collect_desired_sync_rows", lambda **kwargs: (row,))
    monkeypatch.setattr(module, "merge_desired_with_installed", lambda snapshot, desired: SimpleNamespace(rows=desired))
    monkeypatch.setattr(module, "collect_skill_cleanup_exposures", lambda: ())
    monkeypatch.setattr(module, "supported_agent_ids", lambda: ("cursor",))
    monkeypatch.setattr(module, "repo_skill_owner_covered_agents", lambda row, target_agents, **kwargs: ())

    rows, summary = module._skill_rows()

    assert rows[0]["missing_agents"] == ["cursor"]
    assert rows[0]["store_missing_agents"] == []
    assert rows[0]["projection_missing_agents"] == ["cursor"]
    assert summary["default_sync_missing_by_agent"]["cursor"] == 1
    assert summary["store_missing_by_agent"]["cursor"] == 0
    assert summary["projection_missing_by_agent"]["cursor"] == 1
    assert "store/secondary is not durable Cursor sync" in rows[0]["evidence"]


def test_skills_sync_treats_upstream_selector_alias_as_installed(monkeypatch) -> None:
    from wagents import cli as module

    desired = InstalledSkillInventoryRow(
        name="opsx-tdd",
        path="",
        source_path="docs/src/authoring/skills/opsx-tdd.mdx",
        scope="desired",
        description="OpenSpec TDD.",
        license="",
        version="",
        author="",
        source="yuritoledo/openspec-tdd",
        install_source="yuritoledo/openspec-tdd",
        source_url="https://github.com/yuritoledo/openspec-tdd",
        install_command="npx skills add yuritoledo/openspec-tdd --skill opsx:tdd -y -g",
        provenance_status="verified-curated-external",
        trust_tier="curated-trust-gated",
        selector_mode="named",
        installed_agents=(),
        discovered_in=(),
        target_agents=("codex",),
        sync_kind="skills-cli",
        docs_status="documented",
    )
    installed_alias = InstalledSkillInventoryRow(
        name="opsx:tdd",
        path="/Users/example/.agents/skills/opsx-tdd",
        source_path="/Users/example/.agents/skills/opsx-tdd/SKILL.md",
        scope="global",
        description="OpenSpec TDD.",
        license="",
        version="",
        author="",
        source="yuritoledo/openspec-tdd",
        install_source="yuritoledo/openspec-tdd",
        source_url="https://github.com/yuritoledo/openspec-tdd",
        install_command="",
        provenance_status="installed-external",
        trust_tier="github",
        selector_mode="named",
        installed_agents=("codex",),
        discovered_in=("codex",),
        target_agents=(),
        sync_kind="skills-cli",
    )
    snapshot = InstalledInventorySnapshot(
        rows=(installed_alias,),
        queries=(HarnessQueryResult(agent_id="codex", ok=True, entries=()),),
    )

    monkeypatch.setattr(module, "collect_installed_inventory", lambda **kwargs: snapshot)
    monkeypatch.setattr(module, "collect_desired_sync_rows", lambda **kwargs: (desired,))

    report = module._build_sync_report(("codex",), include_installed=False, external_entries=[])
    agents = cast("list[dict[str, object]]", report["agents"])
    agent_report = agents[0]

    assert agent_report["missing"] == []
    assert agent_report["commands"] == []
    assert agent_report["already_present"] == ["opsx-tdd [verified-curated-external] — yuritoledo/openspec-tdd"]


def test_harness_reconciliation_is_redacted_and_has_parallel_task_graph() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    manifest = json.loads(text)

    assert "/Users/ww" not in text
    assert "Authorization" not in text
    assert "auth.json" not in text
    assert "api_key" not in text.lower()
    assert "bearer" not in text.lower()

    task_graph = manifest["task_graph"]
    shard_nodes = [node for node in task_graph if node["id"] not in {"T-000", "T-999"}]

    assert len(task_graph) >= 30
    assert any(node["parallel"] for node in task_graph)
    assert sum(node["row_count"] for node in shard_nodes) == manifest["summary"]["row_count"]
    for node in task_graph:
        assert node["id"].startswith("T-")
        assert node["lane"]
        assert node["files"]
        assert node["done_when"]

    for node in shard_nodes:
        assert node["depends_on"] == ["T-000"]
        assert node["filter"]
        assert node["manual_inspection"]
        assert node["terminal_action"] in TERMINAL_ACTIONS

    opencode_plugin_nodes = [
        node
        for node in shard_nodes
        if node["filter"]["harness"] == "opencode" and node["filter"]["asset_type"] == "plugin"
    ]
    assert opencode_plugin_nodes
    assert all("~/.config/opencode/tui.json" in node["files"] for node in opencode_plugin_nodes)

    assert task_graph[-1]["id"] == "T-999"
    assert set(task_graph[-1]["depends_on"]) == {node["id"] for node in shard_nodes}
