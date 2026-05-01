"""Tests for OpenSpec CLI integration helpers and commands."""

from __future__ import annotations

import subprocess

from typer.testing import CliRunner

from wagents.cli import app
from wagents.openspec import (
    OPENSPEC_PACKAGE,
    OPENSPEC_TELEMETRY_ENV,
    build_openspec_argv,
    node_version_supported,
    parse_node_version,
    select_openspec_tools,
)

runner = CliRunner()


def test_parse_node_version_and_support():
    assert parse_node_version("v20.19.0") == (20, 19, 0)
    assert node_version_supported("v20.19.0") is True
    assert node_version_supported("v20.18.0") is False
    assert node_version_supported("not-a-version") is None


def test_select_openspec_tools_deduplicates_repo_agents_and_raw_tools():
    assert select_openspec_tools(agents=["claude-code", "gemini-cli"], tools=["opencode", "claude"]) == (
        "claude",
        "gemini",
        "opencode",
    )


def test_build_openspec_argv_uses_npx_package():
    assert build_openspec_argv(["validate", "--all"]) == [
        "npx",
        "-y",
        OPENSPEC_PACKAGE,
        "validate",
        "--all",
    ]


def test_openspec_init_dry_run_defaults_to_supported_repo_tools(tmp_repo):
    result = runner.invoke(app, ["openspec", "init"])

    assert result.exit_code == 0, result.output
    assert "npx -y @fission-ai/openspec@latest init --tools" in result.output
    assert "claude,codex,crush,cursor,gemini,github-copilot,opencode,antigravity" not in result.output
    assert "antigravity,claude,codex,crush,cursor,gemini,github-copilot,opencode" in result.output
    assert "--profile core" in result.output


def test_openspec_init_reports_unknown_agent_without_traceback(tmp_repo):
    result = runner.invoke(app, ["openspec", "init", "--agent", "invalid-agent"])

    assert result.exit_code == 1
    assert "unknown agent 'invalid-agent'" in result.output
    assert "Traceback" not in result.output


def test_openspec_update_dry_run_prints_command(tmp_repo):
    result = runner.invoke(app, ["openspec", "update", "--force"])

    assert result.exit_code == 0, result.output
    assert "npx -y @fission-ai/openspec@latest update --force" in result.output


def test_openspec_archive_dry_run_prints_command(tmp_repo):
    result = runner.invoke(app, ["openspec", "archive", "demo-change", "--yes", "--skip-specs", "--no-validate"])

    assert result.exit_code == 0, result.output
    assert "npx -y @fission-ai/openspec@latest archive demo-change --yes --skip-specs --no-validate" in result.output


def test_openspec_doctor_reports_project_state(tmp_repo, monkeypatch):
    (tmp_repo / "openspec" / "specs").mkdir(parents=True)
    (tmp_repo / "openspec" / "changes").mkdir()
    (tmp_repo / "openspec" / "config.yaml").write_text("schema: agent-asset-change\n")

    monkeypatch.setattr("wagents.openspec.shutil.which", lambda tool: f"/usr/bin/{tool}")

    def fake_run(argv, **kwargs):
        if argv == ["node", "--version"]:
            return subprocess.CompletedProcess(argv, 0, stdout="v20.19.0\n", stderr="")
        if argv == ["npx", "--version"]:
            return subprocess.CompletedProcess(argv, 0, stdout="10.9.0\n", stderr="")
        raise AssertionError(f"unexpected argv: {argv}")

    monkeypatch.setattr("wagents.openspec.subprocess.run", fake_run)

    result = runner.invoke(app, ["openspec", "doctor", "--format", "json"])

    assert result.exit_code == 0, result.output
    assert '"supported": true' in result.output
    assert '"configExists": true' in result.output
    assert '"claude-code": "claude"' in result.output


def test_openspec_validate_wraps_json_output(tmp_repo, monkeypatch):
    completed = subprocess.CompletedProcess(
        ["npx", "-y", OPENSPEC_PACKAGE, "validate", "--all", "--json", "--strict"],
        0,
        stdout='{"summary":{"valid":1}}\n',
        stderr="",
    )

    def fake_run(argv, **kwargs):
        assert kwargs["env"][OPENSPEC_TELEMETRY_ENV] == "0"
        assert argv == completed.args
        return completed

    monkeypatch.setattr("wagents.openspec.subprocess.run", fake_run)

    result = runner.invoke(app, ["openspec", "validate", "--format", "json"])

    assert result.exit_code == 0, result.output
    assert '"returncode": 0' in result.output
    assert '"valid": 1' in result.output


def test_openspec_validate_preserves_user_telemetry_opt_in(tmp_repo, monkeypatch):
    completed = subprocess.CompletedProcess(
        ["npx", "-y", OPENSPEC_PACKAGE, "validate", "--all", "--json", "--strict"],
        0,
        stdout='{"summary":{"valid":1}}\n',
        stderr="",
    )

    def fake_run(argv, **kwargs):
        assert kwargs["env"][OPENSPEC_TELEMETRY_ENV] == "1"
        assert argv == completed.args
        return completed

    monkeypatch.setattr("wagents.openspec.subprocess.run", fake_run)

    result = runner.invoke(app, ["openspec", "validate", "--format", "json"], env={OPENSPEC_TELEMETRY_ENV: "1"})

    assert result.exit_code == 0, result.output


def test_openspec_json_commands_wrap_subprocess_output(tmp_repo, monkeypatch):
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, stdout='{"ok":true}\n', stderr="")

    monkeypatch.setattr("wagents.openspec.subprocess.run", fake_run)

    cases = [
        (["openspec", "status", "--change", "demo", "--format", "json"], ["status", "--change", "demo", "--json"]),
        (
            ["openspec", "instructions", "design", "--change", "demo", "--format", "json"],
            ["instructions", "design", "--change", "demo", "--json"],
        ),
        (["openspec", "schemas", "--format", "json"], ["schemas", "--json"]),
        (
            ["openspec", "validate", "--no-strict", "--concurrency", "2", "--format", "json"],
            ["validate", "--all", "--json", "--concurrency", "2"],
        ),
    ]

    for command, args in cases:
        result = runner.invoke(app, command)

        assert result.exit_code == 0, result.output
        assert '"ok": true' in result.output
        assert calls[-1][0] == ["npx", "-y", OPENSPEC_PACKAGE, *args]
        assert calls[-1][1]["cwd"] == tmp_repo


def test_openspec_apply_mode_preserves_exit_code(tmp_repo, monkeypatch):
    def fake_run(argv, **kwargs):
        assert argv == ["npx", "-y", OPENSPEC_PACKAGE, "update"]
        assert kwargs["capture_output"] is False
        return subprocess.CompletedProcess(argv, 7, stdout="", stderr="")

    monkeypatch.setattr("wagents.openspec.subprocess.run", fake_run)

    result = runner.invoke(app, ["openspec", "update", "--apply"])

    assert result.exit_code == 7
