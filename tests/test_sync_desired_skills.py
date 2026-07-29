"""Tests for desired-set sync: Install Now curated + repo-owned rows."""

import json
import subprocess
from pathlib import Path
from typing import cast

from typer.testing import CliRunner

from wagents.cli import _build_sync_report, _optional_installed_superseded, app
from wagents.external_skills import (
    ExternalSkillCatalogError,
    ExternalSkillEntry,
    desired_install_now_entries,
    parse_external_skill_entries,
)
from wagents.installed_inventory import (
    HarnessQueryResult,
    InstalledInventorySnapshot,
    InstalledSkillInventoryRow,
    collect_desired_sync_rows,
    collect_installed_inventory,
    external_entry_to_inventory_row,
    merge_desired_with_installed,
    resolve_repo_install_source,
)

runner = CliRunner()


def _empty_snapshot() -> InstalledInventorySnapshot:
    return InstalledInventorySnapshot(rows=(), queries=())


def _failed_query_snapshot(agent_id: str = "codex", error: str = "inventory boom") -> InstalledInventorySnapshot:
    return InstalledInventorySnapshot(rows=(), queries=(HarnessQueryResult(agent_id, False, (), error),))


def _warning_query_snapshot(
    agent_id: str = "codex",
    warning: str = "Fallback inventory used",
) -> InstalledInventorySnapshot:
    return InstalledInventorySnapshot(rows=(), queries=(HarnessQueryResult(agent_id, True, (), warning),))


def _repo_owned_desired_row() -> InstalledSkillInventoryRow:
    return InstalledSkillInventoryRow(
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
        target_agents=("codex",),
        sync_kind="skills-cli",
    )


def test_desired_install_now_entries_excludes_inspect_tier(tmp_path):
    config = tmp_path / "curated-skills.md"
    config.write_text(
        """
## Install Now After Trust Gate

```bash
npx skills add addyosmani/web-quality-skills --skill performance -y -g -a codex
```

## Inspect Then Install

```bash
npx skills add openai/skills --skill security-best-practices -y -g -a codex
```
""",
        encoding="utf-8",
    )
    desired = desired_install_now_entries(config)
    names = {entry.name for entry in desired}
    assert "performance" in names
    assert "security-best-practices" not in names


def test_external_entry_to_inventory_row_is_verified_with_empty_install_state():
    (entry,) = parse_external_skill_entries(
        """
## Install Now After Trust Gate

```bash
npx skills add vercel-labs/agent-skills --skill curated-skill -y -g -a codex
```
"""
    )
    row = external_entry_to_inventory_row(entry)

    assert row.provenance_status == "verified-curated-external"
    assert row.installed_agents == ()
    assert row.target_agents == ("codex",)
    assert "curated-skill" in row.install_command


def test_external_entry_to_inventory_row_does_not_synthesize_global_only_command():
    row = external_entry_to_inventory_row(
        ExternalSkillEntry(
            name="avoid-skill",
            source="owner/repo",
            install_source="owner/repo",
            status="global-only-or-avoid",
            trust_tier="global-only-or-avoid",
            provenance_status="explicit-unresolved",
            install_command="",
            target_agents=(),
            source_url="https://github.com/owner/repo",
            notes="Avoid duplicate plugin-owned skill.",
            selector_mode="unresolved",
            sync_kind="none",
        )
    )

    assert row.install_command == ""
    assert row.sync_kind == "none"
    assert not row.is_installable()


def test_merge_desired_with_installed_preserves_installed_agents():
    desired = external_entry_to_inventory_row(
        parse_external_skill_entries(
            """
## Install Now After Trust Gate

```bash
npx skills add vercel-labs/agent-skills --skill curated-skill -y -g -a codex claude-code
```
"""
        )[0]
    )
    installed = InstalledSkillInventoryRow(
        name="curated-skill",
        path="/tmp/curated-skill",
        source_path="/tmp/curated-skill/SKILL.md",
        scope="global",
        description="Installed copy",
        license="",
        version="",
        author="",
        source="vercel-labs/agent-skills",
        install_source="vercel-labs/agent-skills",
        source_url="https://github.com/vercel-labs/agent-skills",
        install_command="npx skills add vercel-labs/agent-skills --skill curated-skill -y -g",
        provenance_status="verified-curated-external",
        trust_tier="curated-trust-gated",
        selector_mode="named",
        installed_agents=("codex",),
        discovered_in=("codex",),
        target_agents=("codex", "claude-code"),
    )
    snapshot = InstalledInventorySnapshot(rows=(installed,), queries=())

    merged = merge_desired_with_installed(snapshot, (desired,))

    (row,) = merged.rows
    assert row.installed_agents == ("codex",)
    assert row.path == "/tmp/curated-skill"
    assert row.install_command == desired.install_command
    assert row.sync_kind == "skills-cli"


def test_desired_install_now_entries_excludes_external_tool_rows(monkeypatch):
    rows = [
        ExternalSkillEntry(
            name="apm-cli",
            source="microsoft/apm",
            install_source="microsoft/apm",
            status="install-now-after-trust-gate",
            trust_tier="curated-trust-gated",
            provenance_status="verified-install-command",
            install_command="pip install apm-cli",
            target_agents=("codex",),
            source_url="https://github.com/microsoft/apm",
            notes="External package manager.",
            sync_kind="external-tool",
        ),
        parse_external_skill_entries(
            """
## Install Now After Trust Gate

```bash
npx skills add owner/repo --skill syncable-skill -y -g -a codex
```
"""
        )[0],
    ]
    monkeypatch.setattr("wagents.external_skills.read_external_skill_entries", lambda path=None: rows)

    desired = desired_install_now_entries()

    assert {entry.name for entry in desired} == {"syncable-skill"}


def test_sync_reports_uninstalled_install_now_as_missing(monkeypatch):
    curated = parse_external_skill_entries(
        """
## Install Now After Trust Gate

```bash
npx skills add vercel-labs/agent-skills --skill missing-curated -y -g -a codex
```
"""
    )[0]
    desired_row = external_entry_to_inventory_row(curated)

    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _empty_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (desired_row,))

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex"])

    assert result.exit_code == 0
    assert "store-missing (1)" in result.output
    assert "missing-curated [verified-curated-external]" in result.output
    assert "npx skills add vercel-labs/agent-skills --skill missing-curated -y -g -a codex" in result.output


def test_sync_preserves_pinned_multi_skill_bundle_command(monkeypatch):
    install_cmd = (
        "npx skills add github:ChromeDevTools/chrome-devtools-mcp@abc123 "
        "--skill chrome-devtools --skill chrome-devtools-cli --skill a11y-debugging -y -g -a codex"
    )
    curated = parse_external_skill_entries(
        f"""
## Install Now After Trust Gate

```bash
{install_cmd}
```
"""
    )[0]
    desired_row = external_entry_to_inventory_row(curated)

    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _empty_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (desired_row,))

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex"])

    assert result.exit_code == 0
    assert (
        "npx skills add github:ChromeDevTools/chrome-devtools-mcp@abc123 "
        "--skill a11y-debugging --skill chrome-devtools --skill chrome-devtools-cli -y -g -a codex"
    ) in result.output


def test_sync_skips_external_tool_rows(monkeypatch):
    row = InstalledSkillInventoryRow(
        name="apm-cli",
        path="",
        source_path="docs/src/authoring/skills/apm-cli.mdx",
        scope="desired",
        description="External package manager.",
        license="",
        version="",
        author="",
        source="microsoft/apm",
        install_source="microsoft/apm",
        source_url="https://github.com/microsoft/apm",
        install_command="pip install apm-cli",
        provenance_status="verified-curated-external",
        trust_tier="curated-trust-gated",
        selector_mode="named",
        installed_agents=(),
        discovered_in=(),
        target_agents=("codex",),
        sync_kind="external-tool",
    )

    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _empty_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (row,))

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex"])

    assert result.exit_code == 0
    assert "store-missing (0)" in result.output
    assert "commands (0)" in result.output
    assert "pip install apm-cli" not in result.output


def test_sync_grok_desired_install_now_uses_claude_code_adapter(monkeypatch):
    curated = parse_external_skill_entries(
        """
## Install Now After Trust Gate

```bash
npx skills add vercel-labs/agent-skills --skill grok-curated -y -g -a grok
```
"""
    )[0]
    desired_row = external_entry_to_inventory_row(curated)

    calls: list[list[str]] = []
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _empty_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (desired_row,))

    def mock_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("subprocess.run", mock_run)
    monkeypatch.setattr("wagents.cli.mirror_grok_skills_from_claude", lambda **kwargs: 0)

    result = runner.invoke(app, ["skills", "sync", "--agent", "grok", "--apply"])

    assert result.exit_code == 0
    assert calls == [
        [
            "npx",
            "skills",
            "add",
            "vercel-labs/agent-skills",
            "--skill",
            "grok-curated",
            "-y",
            "-g",
            "-a",
            "claude-code",
        ]
    ]


def test_sync_strict_catalog_failure_text_exits_before_inventory(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr(
        "wagents.cli.read_external_skill_entries",
        lambda **kwargs: (_ for _ in ()).throw(ExternalSkillCatalogError("catalog broken")),
    )
    monkeypatch.setattr(
        "wagents.cli.collect_installed_inventory",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("inventory should not run")),
    )

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex"])

    assert result.exit_code == 1
    assert "catalog broken" in result.output
    assert "commands (" not in result.output


def test_sync_strict_catalog_failure_json(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr(
        "wagents.cli.read_external_skill_entries",
        lambda **kwargs: (_ for _ in ()).throw(ExternalSkillCatalogError("catalog broken")),
    )

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex", "--format", "json", "--verbose"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["mode"] == "dry-run"
    assert payload["inventory_count"] is None
    assert payload["agents"] == []
    assert payload["error"] == "catalog broken"
    assert payload["error_type"] == "external-skill-catalog"


def test_sync_strict_catalog_failure_jsonl(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr(
        "wagents.cli.read_external_skill_entries",
        lambda **kwargs: (_ for _ in ()).throw(ExternalSkillCatalogError("catalog broken")),
    )

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex", "--format", "jsonl"])

    assert result.exit_code == 1
    records = [json.loads(line) for line in result.output.splitlines()]
    assert records == [
        {
            "type": "skills-sync",
            "ok": False,
            "mode": "dry-run",
            "inventory_count": None,
            "include_installed": False,
            "verbose": False,
            "agents": [],
            "error": "catalog broken",
            "error_type": "external-skill-catalog",
        }
    ]


def test_sync_success_json_reports_ok(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _empty_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: ())

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex", "--format", "json", "--verbose"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["agents"][0]["agent"] == "codex"


def test_sync_dry_run_inventory_failure_reports_not_ok(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _failed_query_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: ())

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex", "--format", "json", "--verbose"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["error_type"] == "inventory"
    assert payload["error"] == "Target harness inventory failed for: codex"
    assert payload["agents"][0]["agent"] == "codex"
    assert payload["agents"][0]["error"] == "inventory boom"


def test_sync_apply_inventory_failure_exits_before_install_commands(monkeypatch):
    calls: list[list[str]] = []

    def mock_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _failed_query_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: ())
    monkeypatch.setattr("wagents.cli.subprocess.run", mock_run)

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex", "--apply", "--format", "json", "--verbose"])

    assert result.exit_code == 1
    assert calls == []
    assert json.loads(result.output)["ok"] is False


def test_sync_warning_inventory_fallback_remains_ok(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _warning_query_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: ())

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex", "--format", "json", "--verbose"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert "error" not in payload
    assert payload["agents"][0]["warning"] == "Fallback inventory used"


def test_sync_reuses_one_strict_external_snapshot(monkeypatch):
    strict_entries = parse_external_skill_entries(
        """
## Install Now After Trust Gate

```bash
npx skills add owner/repo --skill strict-snapshot -y -g -a codex
```
"""
    )
    seen: dict[str, list[ExternalSkillEntry] | None] = {}

    def fake_inventory(**kwargs):
        seen["inventory"] = kwargs.get("external_entries")
        return _empty_snapshot()

    def fake_desired(**kwargs):
        seen["desired"] = kwargs.get("external_entries")
        return ()

    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: strict_entries)
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", fake_inventory)
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", fake_desired)

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex"])

    assert result.exit_code == 0
    assert seen == {"inventory": strict_entries, "desired": strict_entries}


def test_sync_repo_owned_skill_covered_by_non_cli_owner_is_already_present(monkeypatch):
    row = _repo_owned_desired_row()

    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _empty_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (row,))
    monkeypatch.setattr("wagents.cli.repo_skill_owner_covered_agents", lambda row, agent_ids: tuple(agent_ids))

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex", "--format", "json", "--verbose"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    agent = payload["agents"][0]
    assert agent["missing"] == []
    assert agent["commands"] == []
    assert agent["already_present"] == ["repo-owned-skill [repo-owned]"]


def test_sync_repo_owned_skill_missing_when_owner_is_skills_cli(monkeypatch):
    row = _repo_owned_desired_row()

    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _empty_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (row,))
    monkeypatch.setattr("wagents.cli.repo_skill_owner_covered_agents", lambda row, agent_ids: ())

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex", "--format", "json", "--verbose"])

    assert result.exit_code == 0
    agent = json.loads(result.output)["agents"][0]
    assert agent["missing"] == ["repo-owned-skill [repo-owned]"]
    assert agent["commands"] == [
        "npx skills add github:wyattowalsh/agents --skill repo-owned-skill -y -g -a codex"
    ]


def test_sync_inventory_failure_still_blocks_owner_covered_repo_skill(monkeypatch):
    calls: list[list[str]] = []

    def mock_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _failed_query_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (_repo_owned_desired_row(),))
    monkeypatch.setattr("wagents.cli.repo_skill_owner_covered_agents", lambda row, agent_ids: tuple(agent_ids))
    monkeypatch.setattr("wagents.cli.subprocess.run", mock_run)

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex", "--apply", "--format", "json", "--verbose"])

    assert result.exit_code == 1
    assert calls == []
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["error_type"] == "inventory"


def test_collect_desired_sync_rows_includes_repo_owned_skills(tmp_path):
    repo = tmp_path / "repo"
    skill_dir = repo / "skills" / "demo-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: Demo\n---\n\n# Demo\n",
        encoding="utf-8",
    )

    rows = collect_desired_sync_rows(root=repo)
    by_name = {row.name: row for row in rows}

    assert by_name["demo-skill"].provenance_status == "repo-owned"
    assert by_name["demo-skill"].installed_agents == ()
    assert by_name["demo-skill"].install_source == str(repo.resolve())


def test_resolve_repo_install_source_prefers_local_clone(tmp_path):
    repo = tmp_path / "repo"
    skill_dir = repo / "skills" / "trafilatura"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: trafilatura\ndescription: Local only\n---\n\n# Trafilatura\n",
        encoding="utf-8",
    )

    assert resolve_repo_install_source("trafilatura", repo_root=repo) == str(repo.resolve())
    assert resolve_repo_install_source("missing-skill", repo_root=repo) == "github:wyattowalsh/agents"


def _flutter_verified_row(name: str) -> InstalledSkillInventoryRow:
    return InstalledSkillInventoryRow(
        name=name,
        path="",
        source_path="",
        scope="desired",
        description="Flutter catalog",
        license="",
        version="",
        author="",
        source="flutter/skills",
        install_source="flutter/skills",
        source_url="",
        install_command=f"npx skills add flutter/skills --skill {name} -y -g",
        provenance_status="verified-curated-external",
        trust_tier="curated-trust-gated",
        selector_mode="named",
        installed_agents=(),
        discovered_in=(),
        target_agents=("codex",),
        sync_kind="skills-cli",
    )


def _flutter_stale_installed_row(name: str) -> InstalledSkillInventoryRow:
    return InstalledSkillInventoryRow(
        name=name,
        path="/tmp/flutter-old",
        source_path="/tmp/flutter-old/SKILL.md",
        scope="installed",
        description="Stale flutter lockfile",
        license="",
        version="",
        author="",
        source="flutter/skills",
        install_source="flutter/skills",
        source_url="",
        install_command=f"npx skills add flutter/skills --skill {name} -y -g",
        provenance_status="installed-external",
        trust_tier="installed",
        selector_mode="named",
        installed_agents=(),
        discovered_in=("codex",),
        target_agents=("codex",),
        sync_kind="skills-cli",
    )


def test_optional_installed_superseded_flutter_stale_id():
    verified = [_flutter_verified_row("flutter-apply-architecture-best-practices")]
    stale = _flutter_stale_installed_row("flutter-architecting-apps")

    assert _optional_installed_superseded(stale, verified) is True
    assert _optional_installed_superseded(verified[0], verified) is False


def test_optional_installed_superseded_does_not_skip_unaliased_flutter_installed():
    verified = [_flutter_verified_row("flutter-apply-architecture-best-practices")]
    installed = _flutter_stale_installed_row("flutter-build-responsive-layout")

    assert _optional_installed_superseded(installed, verified) is False


def test_sync_include_installed_skips_superseded_flutter_stale_id(monkeypatch):
    verified = _flutter_verified_row("flutter-apply-architecture-best-practices")
    stale = _flutter_stale_installed_row("flutter-architecting-apps")
    snapshot = InstalledInventorySnapshot(
        rows=(stale,),
        queries=(HarnessQueryResult("codex", True, (), ""),),
    )

    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: snapshot)
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (verified,))

    report = _build_sync_report(("codex",), include_installed=True, external_entries=[])
    agent_reports = cast("list[dict[str, object]]", report["agents"])
    agent = agent_reports[0]

    skipped_names = [line.split()[0] for line in cast("list[str]", agent["skipped"])]
    missing_names = [line.split()[0] for line in cast("list[str]", agent["missing"])]
    assert "flutter-architecting-apps" in skipped_names
    assert "flutter-architecting-apps" not in missing_names


def test_sync_apply_partial_failure_json_includes_apply_failures(monkeypatch):
    row = _repo_owned_desired_row()
    calls: list[list[str]] = []

    def mock_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 1 if len(calls) == 1 else 0)

    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _empty_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (row,))
    monkeypatch.setattr("wagents.cli.repo_skill_owner_covered_agents", lambda row, agent_ids: ())
    monkeypatch.setattr("wagents.cli.subprocess.run", mock_run)

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex", "--apply", "--format", "json", "--verbose"])

    assert result.exit_code == 1
    assert len(calls) == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["mode"] == "apply"
    assert len(payload["apply_failures"]) == 1
    assert payload["apply_failures"][0]["returncode"] == 1


def test_sync_apply_continue_on_error_runs_all_batches(monkeypatch):
    row_a = _repo_owned_desired_row()
    row_b = InstalledSkillInventoryRow(
        name="cursor-only-skill",
        path="",
        source_path="skills/cursor-only-skill/SKILL.md",
        scope="desired",
        description="Cursor target skill.",
        license="",
        version="",
        author="",
        source="github:wyattowalsh/agents",
        install_source="github:wyattowalsh/agents",
        source_url="https://github.com/wyattowalsh/agents",
        install_command="npx skills add github:wyattowalsh/agents --skill cursor-only-skill -y -g",
        provenance_status="repo-owned",
        trust_tier="repo-owned",
        selector_mode="named",
        installed_agents=(),
        discovered_in=(),
        target_agents=("cursor",),
        sync_kind="skills-cli",
    )
    calls: list[list[str]] = []

    def mock_run(cmd, **kwargs):
        calls.append(cmd)
        returncode = 1 if "repo-owned-skill" in cmd else 0
        return subprocess.CompletedProcess(cmd, returncode)

    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _empty_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (row_a, row_b))
    monkeypatch.setattr("wagents.cli.repo_skill_owner_covered_agents", lambda row, agent_ids: ())
    monkeypatch.setattr("wagents.cli.subprocess.run", mock_run)
    monkeypatch.setattr(
        "wagents.cli.ensure_cursor_authoritative_links",
        lambda **kwargs: type(
            "R",
            (),
            {
                "created": tuple(kwargs.get("names") or ()),
                "repaired": (),
                "already_correct": (),
                "blocked": (),
                "skipped_missing_store": (),
            },
        )(),
    )

    result = runner.invoke(
        app,
        ["skills", "sync", "--agent", "codex", "--agent", "cursor", "--apply", "--format", "json", "--verbose"],
    )

    assert result.exit_code == 1
    assert len(calls) == 2
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert len(payload["apply_failures"]) == 1


def test_collect_installed_inventory_respects_empty_external_entries(monkeypatch):
    monkeypatch.setattr(
        "wagents.installed_inventory.read_external_skill_entries",
        lambda: (_ for _ in ()).throw(AssertionError("should not re-read external entries")),
    )
    monkeypatch.setattr("wagents.installed_inventory.query_harness_skills", lambda **kwargs: ())

    snapshot = collect_installed_inventory(external_entries=[])

    assert snapshot.rows == ()


def _write_skill_body(skill_dir: Path, name: str, body: str = "body\n") -> None:
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\ndescription: t\n---\n\n{body}", encoding="utf-8")


def _cursor_desired_row(name: str = "cursor-skill") -> InstalledSkillInventoryRow:
    return InstalledSkillInventoryRow(
        name=name,
        path="",
        source_path=f"skills/{name}/SKILL.md",
        scope="desired",
        description="Cursor skill.",
        license="",
        version="",
        author="",
        source="github:wyattowalsh/agents",
        install_source="github:wyattowalsh/agents",
        source_url="https://github.com/wyattowalsh/agents",
        install_command=f"npx skills add github:wyattowalsh/agents --skill {name} -y -g",
        provenance_status="repo-owned",
        trust_tier="repo-owned",
        selector_mode="named",
        installed_agents=(),
        discovered_in=(),
        target_agents=("cursor",),
        sync_kind="skills-cli",
    )


def test_cursor_store_only_is_projection_ensure_not_already_present(tmp_path, monkeypatch):
    home = tmp_path / "home"
    store = home / ".agents" / "skills" / "cursor-skill"
    _write_skill_body(store, "cursor-skill")
    row = _cursor_desired_row()

    monkeypatch.setattr("wagents.cli.HOME", home)
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _empty_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (row,))
    monkeypatch.setattr("wagents.cli.repo_skill_owner_covered_agents", lambda row, agent_ids: ())

    report = _build_sync_report(("cursor",), include_installed=False, external_entries=[], home=home)
    agent = cast("dict[str, object]", cast("list", report["agents"])[0])
    assert agent["already_present"] == []
    assert agent["store_missing"] == []
    assert agent["projection_ensure"] == ["cursor-skill [repo-owned]"]
    assert agent["commands"] == []


def test_cursor_store_and_projection_is_already_present(tmp_path, monkeypatch):
    home = tmp_path / "home"
    store = home / ".agents" / "skills" / "cursor-skill"
    projection = home / ".cursor" / "skills" / "cursor-skill"
    _write_skill_body(store, "cursor-skill")
    _write_skill_body(projection, "cursor-skill")
    row = _cursor_desired_row()

    monkeypatch.setattr("wagents.cli.HOME", home)
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _empty_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (row,))
    monkeypatch.setattr("wagents.cli.repo_skill_owner_covered_agents", lambda row, agent_ids: ())

    report = _build_sync_report(("cursor",), include_installed=False, external_entries=[], home=home)
    agent = cast("dict[str, object]", cast("list", report["agents"])[0])
    assert agent["already_present"] == ["cursor-skill [repo-owned]"]
    assert agent["projection_ensure"] == []
    assert agent["store_missing"] == []


def test_cursor_absent_is_store_missing_with_cli_command(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    row = _cursor_desired_row()

    monkeypatch.setattr("wagents.cli.HOME", home)
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _empty_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (row,))
    monkeypatch.setattr("wagents.cli.repo_skill_owner_covered_agents", lambda row, agent_ids: ())

    report = _build_sync_report(("cursor",), include_installed=False, external_entries=[], home=home)
    agent = cast("dict[str, object]", cast("list", report["agents"])[0])
    assert agent["store_missing"] == ["cursor-skill [repo-owned]"]
    assert agent["missing"] == agent["store_missing"]
    assert agent["commands"] == [
        "npx skills add github:wyattowalsh/agents --skill cursor-skill -y -g -a cursor"
    ]


def test_cursor_divergent_projection_is_blocked(tmp_path, monkeypatch):
    home = tmp_path / "home"
    store = home / ".agents" / "skills" / "cursor-skill"
    projection = home / ".cursor" / "skills" / "cursor-skill"
    _write_skill_body(store, "cursor-skill", "store-body\n")
    _write_skill_body(projection, "cursor-skill", "local-body\n")
    row = _cursor_desired_row()

    monkeypatch.setattr("wagents.cli.HOME", home)
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _empty_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (row,))
    monkeypatch.setattr("wagents.cli.repo_skill_owner_covered_agents", lambda row, agent_ids: ())

    report = _build_sync_report(("cursor",), include_installed=False, external_entries=[], home=home)
    agent = cast("dict[str, object]", cast("list", report["agents"])[0])
    assert agent["projection_blocked"] == ["cursor-skill [repo-owned]"]
    assert agent["already_present"] == []
    assert agent["commands"] == []


def test_cursor_apply_runs_cli_then_ensure(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    row = _cursor_desired_row()
    cli_calls: list[list[str]] = []
    ensure_calls: list[dict[str, object]] = []

    def mock_run(cmd, **kwargs):
        cli_calls.append(cmd)
        # Simulate Skills CLI writing the store body.
        _write_skill_body(home / ".agents" / "skills" / "cursor-skill", "cursor-skill")
        return subprocess.CompletedProcess(cmd, 0)

    def mock_ensure(**kwargs):
        ensure_calls.append(kwargs)
        return type(
            "R",
            (),
            {
                "created": ("cursor-skill",),
                "repaired": (),
                "already_correct": (),
                "blocked": (),
                "skipped_missing_store": (),
            },
        )()

    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.HOME", home)
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _empty_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (row,))
    monkeypatch.setattr("wagents.cli.repo_skill_owner_covered_agents", lambda row, agent_ids: ())
    monkeypatch.setattr("wagents.cli.subprocess.run", mock_run)
    monkeypatch.setattr("wagents.cli.ensure_cursor_authoritative_links", mock_ensure)

    result = runner.invoke(
        app,
        ["skills", "sync", "--agent", "cursor", "--apply", "--format", "json", "--verbose"],
    )

    assert result.exit_code == 0
    assert len(cli_calls) == 1
    assert ensure_calls
    assert ensure_calls[0]["dry_run"] is False
    assert "cursor-skill" in ensure_calls[0]["names"]
    payload = json.loads(result.output)
    assert payload["cursor_projection_ensure"]["created"] == ["cursor-skill"]


def test_sync_json_default_is_compact_counts_and_samples(monkeypatch):
    row = _repo_owned_desired_row()
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _empty_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (row,))
    monkeypatch.setattr("wagents.cli.repo_skill_owner_covered_agents", lambda row, agent_ids: ())

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex", "--format", "json"])

    assert result.exit_code == 0
    agent = json.loads(result.output)["agents"][0]
    assert agent["store_missing"]["count"] == 1
    assert agent["store_missing"]["sample"] == ["repo-owned-skill [repo-owned]"]
    assert agent["store_missing"]["truncated"] == 0
    assert isinstance(agent["already_present"], dict)
