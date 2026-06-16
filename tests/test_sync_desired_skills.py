"""Tests for desired-set sync: Install Now curated + repo-owned rows."""

import subprocess

from typer.testing import CliRunner

from wagents.cli import app
from wagents.external_skills import desired_install_now_entries, parse_external_skill_entries
from wagents.installed_inventory import (
    InstalledInventorySnapshot,
    InstalledSkillInventoryRow,
    collect_desired_sync_rows,
    external_entry_to_inventory_row,
    merge_desired_with_installed,
)

runner = CliRunner()


def _empty_snapshot() -> InstalledInventorySnapshot:
    return InstalledInventorySnapshot(rows=(), queries=())


def test_desired_install_now_entries_excludes_inspect_tier(tmp_path):
    config = tmp_path / "external-skills.md"
    config.write_text(
        """
## Install Now After Trust Gate

```bash
npx skills add addyosmani/web-quality-skills --skill accessibility -y -g -a codex
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
    assert "accessibility" in names
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
    monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: _empty_snapshot())
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (desired_row,))

    result = runner.invoke(app, ["skills", "sync", "--agent", "codex"])

    assert result.exit_code == 0
    assert "missing (1)" in result.output
    assert "missing-curated [verified-curated-external]" in result.output
    assert "npx skills add vercel-labs/agent-skills --skill missing-curated -y -g -a codex" in result.output


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
