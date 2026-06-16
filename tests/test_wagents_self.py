"""Tests for wagents self-management commands."""

import json
from pathlib import Path

from typer.testing import CliRunner

from wagents.cli import app

runner = CliRunner()


def test_self_doctor_json():
    result = runner.invoke(app, ["self", "doctor", "--format", "json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    names = {check["name"] for check in payload["checks"]}
    assert "install-mode" in names
    assert "repo-discovery" in names


def test_self_install_dry_run(monkeypatch):
    monkeypatch.setattr("wagents.self_cmd.shutil.which", lambda name: "/usr/bin/uv" if name == "uv" else None)
    result = runner.invoke(app, ["self", "install", "--dry-run", "--format", "json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["dry_run"] is True
    assert payload["command"][0] == "uv"
    assert "--from" in payload["command"]
    assert "git+https://github.com/wyattowalsh/agents" in payload["command"]
    assert "--force" in payload["command"]


def test_self_install_local_dry_run(tmp_path: Path, monkeypatch):
    (tmp_path / "skills").mkdir()
    (tmp_path / "agents").mkdir()
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "wagents"\n', encoding="utf-8")
    monkeypatch.setattr("wagents.ROOT", tmp_path)
    monkeypatch.setattr("wagents.self_cmd.shutil.which", lambda name: "/usr/bin/uv" if name == "uv" else None)

    result = runner.invoke(app, ["self", "install", "--local", "--dry-run", "--format", "json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert str(tmp_path.resolve()) in payload["command"]