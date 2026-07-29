"""Pin-gate coverage for skills sync install command preservation."""

from __future__ import annotations

import json
from dataclasses import replace

from typer.testing import CliRunner

from wagents.cli import app
from wagents.external_skills import parse_external_skill_entries
from wagents.installed_inventory import (
    HarnessQueryResult,
    InstalledInventorySnapshot,
    external_entry_to_inventory_row,
)

runner = CliRunner()


def _empty_snapshot() -> InstalledInventorySnapshot:
    return InstalledInventorySnapshot(rows=(), queries=())


def test_skills_sync_pin_gate_preserves_commit_pin_in_command(monkeypatch):
    """Pinned @commit install sources must survive command regrouping."""
    install_cmd = (
        "npx skills add github:ChromeDevTools/chrome-devtools-mcp@deadbeef "
        "--skill chrome-devtools --skill chrome-devtools-cli -y -g -a codex"
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
    monkeypatch.setattr("wagents.cli.repo_skill_owner_covered_agents", lambda row, agent_ids: ())

    result = runner.invoke(
        app,
        ["skills", "sync", "--agent", "codex", "--format", "json", "--verbose"],
    )

    assert result.exit_code == 0
    agent = json.loads(result.output)["agents"][0]
    assert agent["store_missing"]
    assert agent["commands"] == [
        "npx skills add github:ChromeDevTools/chrome-devtools-mcp@deadbeef "
        "--skill chrome-devtools --skill chrome-devtools-cli -y -g -a codex"
    ]


def test_skills_sync_pin_gate_cursor_store_missing_keeps_pin(tmp_path, monkeypatch):
    install_cmd = "npx skills add github:example/skills@abc123 --skill pinned-skill -y -g -a cursor"
    curated = parse_external_skill_entries(
        f"""
## Install Now After Trust Gate

```bash
{install_cmd}
```
"""
    )[0]
    desired_row = replace(external_entry_to_inventory_row(curated), target_agents=("cursor",))
    home = tmp_path / "home"
    home.mkdir()

    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
    monkeypatch.setattr("wagents.cli.read_external_skill_entries", lambda **kwargs: [])
    monkeypatch.setattr(
        "wagents.cli.collect_installed_inventory",
        lambda **kwargs: InstalledInventorySnapshot(
            rows=(),
            queries=(HarnessQueryResult("cursor", True, (), ""),),
        ),
    )
    monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: (desired_row,))
    monkeypatch.setattr("wagents.cli.repo_skill_owner_covered_agents", lambda row, agent_ids: ())
    monkeypatch.setattr("wagents.cli.HOME", home)

    result = runner.invoke(
        app,
        ["skills", "sync", "--agent", "cursor", "--format", "json", "--verbose"],
    )

    assert result.exit_code == 0, result.output
    agent = json.loads(result.output)["agents"][0]
    assert "pinned-skill" in " ".join(agent["store_missing"])
    assert any("@abc123" in command for command in agent["commands"])
