"""Tests for desired-set sync: Install Now curated + repo-owned rows."""

import json
import subprocess

from typer.testing import CliRunner

from wagents.cli import app
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
    collect_installed_inventory,
    collect_desired_sync_rows,
    external_entry_to_inventory_row,
    merge_desired_with_installed,
)

runner = CliRunner()


def _empty_snapshot() -> InstalledInventorySnapshot:
    return InstalledInventorySnapshot(rows=(), queries=())


def _failed_query_snapshot(agent_id: str = "codex", error: str = "inventory boom") -> InstalledInventorySnapshot:
    return InstalledInventorySnapshot(rows=(), queries=(HarnessQueryResult(agent_id, False, (), error),))


def _warning_query_snapshot(agent_id: str = "codex", warning: str = "Fallback inventory used") -> InstalledInventorySnapshot:
    return InstalledInventorySnapshot(rows=(), queries=(HarnessQueryResult(agent_id, True, (), warning),))


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
    assert "missing (1)" in result.output
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
    assert "missing (0)" in result.output
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

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex", "--format", "json"])

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

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex", "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["agents"][0]["agent"] == "codex"


def test_sync_dry_run_inventory_failure_reports_not_ok(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _failed_query_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: ())

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex", "--format", "json"])

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

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex", "--apply", "--format", "json"])

    assert result.exit_code == 1
    assert calls == []
    assert json.loads(result.output)["ok"] is False


def test_sync_warning_inventory_fallback_remains_ok(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _warning_query_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: ())

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex", "--format", "json"])

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


def test_collect_installed_inventory_respects_empty_external_entries(monkeypatch):
    monkeypatch.setattr(
        "wagents.installed_inventory.read_external_skill_entries",
        lambda: (_ for _ in ()).throw(AssertionError("should not re-read external entries")),
    )
    monkeypatch.setattr("wagents.installed_inventory.query_harness_skills", lambda **kwargs: ())

    snapshot = collect_installed_inventory(external_entries=[])

    assert snapshot.rows == ()
