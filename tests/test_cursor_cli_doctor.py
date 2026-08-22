"""Tests for wagents cursor-cli doctor."""

from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from wagents.cli import app
from wagents.cursor_cli_doctor import collect_cursor_cli_doctor_checks, cursor_cli_doctor_report

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()

SECRET_EMAIL = "secret.user@example.com"
SECRET_MODEL = "do-not-dump-this-model"
SECRET_TOKEN = "tok_live_do_not_print"


def _write(path: Path, payload: object | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
        return
    path.write_text(json.dumps(payload), encoding="utf-8")


def _trees(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    repo.mkdir()
    home.mkdir()
    return repo, home


def _completed(argv: list[str], stdout: str = "", stderr: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(argv, returncode, stdout, stderr)


def _fake_agent_run(argv, **_kwargs):
    args = [str(item) for item in argv]
    if args[1:] == ["--version"]:
        return _completed(args, "2026.08.11-e8db854\n")
    if args[1:] == ["about", "--format", "json"]:
        return _completed(
            args,
            json.dumps({
                "cliVersion": "2026.08.11-e8db854",
                "model": "cursor-grok",
                "userEmail": SECRET_EMAIL,
                "apiKey": SECRET_TOKEN,
                "idToken": SECRET_TOKEN,
                "authorization": "Bearer abc.def",
            }),
        )
    return _completed(args, returncode=1, stderr="unexpected")


def test_missing_binary_is_warning(tmp_path, monkeypatch):
    repo, home = _trees(tmp_path)
    monkeypatch.setattr("wagents.cursor_cli_doctor.shutil.which", lambda _name: None)

    report = cursor_cli_doctor_report(repo_root=repo, home=home)

    assert report["ok"] is True
    by_name = {check["name"]: check for check in report["checks"]}
    assert by_name["cursor-cli-binary"]["status"] == "warn"
    assert "cursor-cli-version" not in by_name
    assert "cursor-cli-about" not in by_name


def test_about_redacts_user_email(tmp_path, monkeypatch):
    repo, home = _trees(tmp_path)
    monkeypatch.setattr(
        "wagents.cursor_cli_doctor.shutil.which",
        lambda name: str(tmp_path / name) if name in {"agent", "cursor-agent"} else None,
    )
    monkeypatch.setattr("wagents.cursor_cli_doctor.subprocess.run", _fake_agent_run)

    report = cursor_cli_doctor_report(repo_root=repo, home=home)
    blob = json.dumps(report)

    assert SECRET_EMAIL not in blob
    assert SECRET_TOKEN not in blob
    assert "userEmail" not in blob
    assert "apiKey" not in blob
    assert "idToken" not in blob
    assert "Bearer abc.def" not in blob
    by_name = {check["name"]: check for check in report["checks"]}
    assert by_name["cursor-cli-about"]["status"] == "ok"
    assert "cliVersion=2026.08.11-e8db854" in by_name["cursor-cli-about"]["summary"]
    assert by_name["cursor-cli-version"]["summary"] == "2026.08.11-e8db854"


def test_version_stderr_secret_is_not_reported(tmp_path, monkeypatch):
    repo, home = _trees(tmp_path)

    def _version_leaks(argv, **_kwargs):
        args = [str(item) for item in argv]
        if args[1:] == ["--version"]:
            return _completed(args, stdout="", stderr=SECRET_TOKEN + "\n", returncode=1)
        if args[1:] == ["about", "--format", "json"]:
            return _completed(args, json.dumps({"cliVersion": "2026.08.11-e8db854"}))
        return _completed(args, returncode=1, stderr="unexpected")

    monkeypatch.setattr(
        "wagents.cursor_cli_doctor.shutil.which",
        lambda name: str(tmp_path / name) if name in {"agent", "cursor-agent"} else None,
    )
    monkeypatch.setattr("wagents.cursor_cli_doctor.subprocess.run", _version_leaks)

    report = cursor_cli_doctor_report(repo_root=repo, home=home)
    blob = json.dumps(report)
    assert SECRET_TOKEN not in blob
    by_name = {check["name"]: check for check in report["checks"]}
    assert "cursor-cli-version" not in by_name or by_name["cursor-cli-version"]["status"] != "ok"


def test_home_config_reports_key_presence_only(tmp_path, monkeypatch):
    repo, home = _trees(tmp_path)
    _write(
        home / ".cursor" / "cli-config.json",
        {
            "version": 1,
            "editor": {"vimMode": True},
            "permissions": {"allow": [SECRET_TOKEN]},
            "approvalMode": "allowlist",
            "sandbox": {"mode": "disabled"},
            "model": SECRET_MODEL,
        },
    )
    monkeypatch.setattr("wagents.cursor_cli_doctor.shutil.which", lambda _name: None)

    report = cursor_cli_doctor_report(repo_root=repo, home=home)
    blob = json.dumps(report)
    by_name = {check["name"]: check for check in report["checks"]}

    assert SECRET_MODEL not in blob
    assert SECRET_TOKEN not in blob
    assert by_name["cursor-cli-home-config-keys"]["status"] == "ok"
    assert (
        "present: version, editor, permissions, approvalMode, sandbox, model"
        in by_name["cursor-cli-home-config-keys"]["summary"]
    )
    assert "absent: exploreSubagentModel" in by_name["cursor-cli-home-config-keys"]["summary"]
    assert by_name["cursor-cli-explore-subagent-model"]["status"] == "warn"


def test_project_cli_flags_unexpected_keys(tmp_path, monkeypatch):
    repo, home = _trees(tmp_path)
    _write(
        repo / ".cursor" / "cli.json",
        {"permissions": {"allow": ["Read(AGENTS.md)"]}, "model": SECRET_MODEL},
    )
    monkeypatch.setattr("wagents.cursor_cli_doctor.shutil.which", lambda _name: None)

    checks = collect_cursor_cli_doctor_checks(repo_root=repo, home=home)
    by_name = {check["name"]: check for check in checks}
    blob = json.dumps(checks)

    assert by_name["cursor-cli-project-config"]["status"] == "warn"
    assert "model" in by_name["cursor-cli-project-config"]["summary"]
    assert SECRET_MODEL not in blob
    assert "Read(AGENTS.md)" not in blob


def test_presence_surfaces(tmp_path, monkeypatch):
    repo, home = _trees(tmp_path)
    _write(repo / ".cursor" / "hooks.json", {"version": 1})
    _write(repo / ".cursor" / "mcp.json", {"mcpServers": {}})
    _write(repo / "instructions" / "cursor-cli-global.md", "# overlay\n")
    _write(repo / ".cursor" / "rules" / "cursor-cli.mdc", "---\n")
    _write(repo / ".cursor" / "cli.json", {"permissions": {}})
    _write(
        home / ".cursor" / "cli-config.json",
        {"exploreSubagentModel": "inherit", "version": 1},
    )
    monkeypatch.setattr("wagents.cursor_cli_doctor.shutil.which", lambda _name: None)

    report = cursor_cli_doctor_report(repo_root=repo, home=home)
    by_name = {check["name"]: check for check in report["checks"]}

    assert by_name["cursor-cli-hooks"]["status"] == "ok"
    assert by_name["cursor-cli-mcp"]["status"] == "ok"
    assert by_name["cursor-cli-instructions"]["status"] == "ok"
    assert by_name["cursor-cli-rule"]["status"] == "ok"
    assert by_name["cursor-cli-project-config"]["status"] == "ok"
    assert by_name["cursor-cli-explore-subagent-model"]["status"] == "ok"


def test_cursor_cli_doctor_json_cli(tmp_path, monkeypatch):
    repo, home_dir = _trees(tmp_path)
    real_report = cursor_cli_doctor_report
    real_collect = collect_cursor_cli_doctor_checks
    monkeypatch.setattr("wagents.cursor_cli_doctor.shutil.which", lambda _name: None)
    monkeypatch.setattr(
        "wagents.cursor_cli_doctor.cursor_cli_doctor_report",
        lambda repo_root=None, home=None: real_report(repo_root=repo, home=home_dir),
    )
    monkeypatch.setattr(
        "wagents.cursor_cli_doctor.collect_cursor_cli_doctor_checks",
        lambda repo_root=None, home=None: real_collect(repo_root=repo, home=home_dir),
    )

    result = runner.invoke(app, ["cursor-cli", "doctor", "--format", "json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    names = {check["name"] for check in payload["checks"]}
    assert "cursor-cli-binary" in names
    assert payload["summary"]["total"] == len(payload["checks"])


def test_cursor_cli_doctor_cli_redacts_about_email(tmp_path, monkeypatch):
    repo, home_dir = _trees(tmp_path)
    real_report = cursor_cli_doctor_report
    real_collect = collect_cursor_cli_doctor_checks
    monkeypatch.setattr(
        "wagents.cursor_cli_doctor.shutil.which",
        lambda name: str(tmp_path / name) if name == "agent" else None,
    )
    monkeypatch.setattr("wagents.cursor_cli_doctor.subprocess.run", _fake_agent_run)
    monkeypatch.setattr(
        "wagents.cursor_cli_doctor.cursor_cli_doctor_report",
        lambda repo_root=None, home=None: real_report(repo_root=repo, home=home_dir),
    )
    monkeypatch.setattr(
        "wagents.cursor_cli_doctor.collect_cursor_cli_doctor_checks",
        lambda repo_root=None, home=None: real_collect(repo_root=repo, home=home_dir),
    )

    result = runner.invoke(app, ["cursor-cli", "doctor", "--format", "json"])

    assert result.exit_code == 0, result.output
    assert SECRET_EMAIL not in result.output
    assert "userEmail" not in result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True


def test_cursor_cli_doctor_rejects_invalid_format():
    result = runner.invoke(app, ["cursor-cli", "doctor", "--format", "yaml"])
    assert result.exit_code == 1
    assert "unsupported format" in result.output.lower()


def test_plannotator_checks_are_warn_only_when_missing(tmp_path, monkeypatch):
    repo, home = _trees(tmp_path)
    monkeypatch.setattr("wagents.cursor_cli_doctor.shutil.which", lambda _name: None)
    report = cursor_cli_doctor_report(repo_root=repo, home=home)
    assert report["ok"] is True
    by_name = {check["name"]: check for check in report["checks"]}
    assert by_name["plannotator-binary"]["status"] == "warn"
    assert by_name["plannotator-hooks"]["status"] == "warn"
    assert by_name["plannotator-shim"]["status"] == "warn"


def test_plannotator_checks_ok_when_home_surfaces_present(tmp_path, monkeypatch):
    repo, home = _trees(tmp_path)
    binary = home / ".local" / "bin" / "plannotator"
    binary.parent.mkdir(parents=True)
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    shim = home / ".cursor" / "hooks" / "plannotator-plan-hook.py"
    shim.parent.mkdir(parents=True)
    shim.write_text("# shim\n", encoding="utf-8")
    _write(
        home / ".cursor" / "hooks.json",
        {
            "version": 1,
            "hooks": {
                "preToolUse": [
                    {"matcher": "SwitchMode", "command": str(shim) + " enter"},
                    {"matcher": "CreatePlan", "command": str(shim) + " exit"},
                ]
            },
        },
    )
    monkeypatch.setattr("wagents.cursor_cli_doctor.shutil.which", lambda _name: None)
    report = cursor_cli_doctor_report(repo_root=repo, home=home)
    assert report["ok"] is True
    by_name = {check["name"]: check for check in report["checks"]}
    assert by_name["plannotator-binary"]["status"] == "ok"
    assert by_name["plannotator-hooks"]["status"] == "ok"
    assert by_name["plannotator-shim"]["status"] == "ok"
