"""Tests for wagents grok doctor --format json."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from wagents.cli import app
from wagents.grok_doctor import collect_grok_doctor_checks, grok_doctor_report

runner = CliRunner()


def test_grok_doctor_report_shape(monkeypatch, tmp_path):
    grok_cfg = tmp_path / "config.toml"
    grok_cfg.write_text(
        "# BEGIN MANAGED BY sync_agent_stack.py: MCP_SERVERS\n"
        "[mcp_servers.mcphub_group_harness-safe]\nenabled = true\n"
        "# END MANAGED BY sync_agent_stack.py: MCP_SERVERS\n"
        "# BEGIN MANAGED BY sync_agent_stack.py: GROK_POLICY\n"
        '[models]\ndefault = "grok-composer-2.5-fast"\n'
        "# END MANAGED BY sync_agent_stack.py: GROK_POLICY\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("wagents.grok_doctor.GROK_CONFIG_PATH", grok_cfg)
    monkeypatch.setattr("wagents.grok_doctor.GROK_CONFIG_REPO_PATH", tmp_path / "repo.toml")
    monkeypatch.setattr("wagents.grok_doctor.GROK_CONFIG_POLICY_PATH", tmp_path / "policy.toml")
    monkeypatch.setattr("wagents.grok_doctor.GROK_BINARY_PATH", tmp_path / "grok")
    monkeypatch.setenv("GROK_WEB_FETCH", "1")
    monkeypatch.setenv("GROK_MEMORY", "1")
    monkeypatch.setenv("GROK_SUBAGENTS", "1")
    monkeypatch.setenv("GROK_LSP_TOOLS", "1")

    def fake_which(cmd: str) -> str | None:
        if cmd == "grok":
            return str(tmp_path / "grok")
        return None

    monkeypatch.setattr("wagents.grok_doctor.shutil.which", fake_which)

    report = grok_doctor_report(home=tmp_path)
    assert "ok" in report
    assert "summary" in report
    assert "checks" in report
    assert isinstance(report["checks"], list)
    assert report["checks"][0]["name"] == "grok-binary"
    assert report["ok"] is True


def test_grok_doctor_json_cli(monkeypatch, tmp_path):
    grok_cfg = tmp_path / "config.toml"
    grok_cfg.write_text(
        "# BEGIN MANAGED BY sync_agent_stack.py: MCP_SERVERS\n"
        "[mcp_servers.mcphub_group_harness-safe]\nenabled = true\n"
        "# END MANAGED BY sync_agent_stack.py: MCP_SERVERS\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("wagents.grok_doctor.GROK_CONFIG_PATH", grok_cfg)
    monkeypatch.setattr("wagents.grok_doctor.GROK_CONFIG_REPO_PATH", tmp_path / "repo.toml")
    monkeypatch.setattr("wagents.grok_doctor.GROK_CONFIG_POLICY_PATH", tmp_path / "policy.toml")
    monkeypatch.setattr("wagents.grok_doctor.GROK_BINARY_PATH", tmp_path / "grok")

    def fake_which(cmd: str) -> str | None:
        if cmd == "grok":
            return str(tmp_path / "grok")
        return None

    monkeypatch.setattr("wagents.grok_doctor.shutil.which", fake_which)
    monkeypatch.delenv("GROK_WEB_FETCH", raising=False)

    result = runner.invoke(app, ["grok", "doctor", "--format", "json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["summary"]["total"] == len(collect_grok_doctor_checks(home=tmp_path))


def test_grok_doctor_json_uppercase_format(monkeypatch, tmp_path):
    grok_cfg = tmp_path / "config.toml"
    grok_cfg.write_text(
        "# BEGIN MANAGED BY sync_agent_stack.py: MCP_SERVERS\n"
        "[mcp_servers.mcphub_group_harness-safe]\nenabled = true\n"
        "# END MANAGED BY sync_agent_stack.py: MCP_SERVERS\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("wagents.grok_doctor.GROK_CONFIG_PATH", grok_cfg)
    monkeypatch.setattr("wagents.grok_doctor.GROK_CONFIG_REPO_PATH", tmp_path / "repo.toml")
    monkeypatch.setattr("wagents.grok_doctor.GROK_CONFIG_POLICY_PATH", tmp_path / "policy.toml")
    monkeypatch.setattr("wagents.grok_doctor.GROK_BINARY_PATH", tmp_path / "grok")

    def fake_which(cmd: str) -> str | None:
        if cmd == "grok":
            return str(tmp_path / "grok")
        return None

    monkeypatch.setattr("wagents.grok_doctor.shutil.which", fake_which)

    result = runner.invoke(app, ["grok", "doctor", "--format", "JSON"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert "ok" in payload
    assert "checks" in payload


def test_grok_doctor_rejects_invalid_format():
    result = runner.invoke(app, ["grok", "doctor", "--format", "yaml"])
    assert result.exit_code == 1
    assert "unsupported format" in result.output.lower()


def test_grok_doctor_json_fails_on_missing_binary(monkeypatch, tmp_path):
    grok_cfg = tmp_path / "config.toml"
    grok_cfg.write_text("", encoding="utf-8")
    monkeypatch.setattr("wagents.grok_doctor.GROK_CONFIG_PATH", grok_cfg)
    monkeypatch.setattr("wagents.grok_doctor.GROK_CONFIG_REPO_PATH", tmp_path / "repo.toml")
    monkeypatch.setattr("wagents.grok_doctor.GROK_CONFIG_POLICY_PATH", tmp_path / "policy.toml")
    monkeypatch.setattr("wagents.grok_doctor.GROK_BINARY_PATH", tmp_path / "missing-grok")
    monkeypatch.setattr("wagents.grok_doctor.shutil.which", lambda _cmd: None)

    result = runner.invoke(app, ["grok", "doctor", "--format", "json"])
    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
