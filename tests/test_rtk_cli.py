from __future__ import annotations

import json
import subprocess

from typer.testing import CliRunner

from wagents.cli import app
from wagents.rtk import build_rtk_sync_plan, rtk_doctor_report, run_rtk_sync_plan

runner = CliRunner()


def _completed(argv: list[str], stdout: str = "", stderr: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(argv, returncode, stdout, stderr)


def _fake_rtk_run(argv, **_kwargs):
    args = [str(item) for item in argv]
    if args == ["rtk", "--version"]:
        return _completed(args, "rtk 0.43.0\n")
    if args == ["rtk", "gain"]:
        return _completed(args, "RTK Token Savings\nTokens saved: 100 (80.0%)\n")
    if args == ["rtk", "init", "--help"]:
        return _completed(
            args,
            "--agent <AGENT>\n--auto-patch\n--codex\n--copilot\n--dry-run\n--gemini\n--opencode\n",
        )
    if args == ["rtk", "init", "--show"]:
        return _completed(
            args,
            "\n".join(
                [
                    "rtk Configuration:",
                    "[ok] Hook: installed",
                    "[ok] RTK.md: installed",
                    "[ok] OpenCode: plugin installed (/tmp/rtk.ts)",
                    "[ok] Cursor hook: installed",
                ]
            ),
        )
    if args == ["rtk", "init", "--show", "--codex"]:
        return _completed(
            args,
            "rtk Configuration (Codex CLI):\n[ok] Global RTK.md: installed\n[ok] Global AGENTS.md: configured\n",
        )
    raise AssertionError(f"unexpected subprocess argv: {args}")


def test_rtk_doctor_report_shape(monkeypatch):
    monkeypatch.setattr("wagents.rtk.shutil.which", lambda name: "/usr/local/bin/rtk" if name == "rtk" else None)
    monkeypatch.setattr("wagents.rtk.subprocess.run", _fake_rtk_run)

    report = rtk_doctor_report()

    assert report["ok"] is True
    assert report["summary"]["total"] == len(report["checks"])
    names = {check["name"] for check in report["checks"]}
    assert "rtk-binary" in names
    assert "rtk-version" in names
    assert "rtk-opencode" in names


def test_rtk_doctor_cli_json(monkeypatch):
    monkeypatch.setattr("wagents.rtk.shutil.which", lambda name: "/usr/local/bin/rtk" if name == "rtk" else None)
    monkeypatch.setattr("wagents.rtk.subprocess.run", _fake_rtk_run)

    result = runner.invoke(app, ["rtk", "doctor", "--format", "json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["summary"]["total"] == len(payload["checks"])


def test_rtk_doctor_cli_fails_without_binary(monkeypatch):
    monkeypatch.setattr("wagents.rtk.shutil.which", lambda _name: None)

    result = runner.invoke(app, ["rtk", "doctor", "--format", "json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    by_name = {check["name"]: check for check in payload["checks"]}
    assert by_name["rtk-binary"]["status"] == "fail"


def test_rtk_sync_plan_filters_platforms():
    plan = build_rtk_sync_plan(platforms="opencode,codex", dry_run=True)

    assert plan["dry_run"] is True
    assert [command["platform"] for command in plan["commands"]] == ["opencode", "codex"]
    assert plan["commands"][0]["argv"][:2] == ["rtk", "init"]


def test_rtk_sync_cli_json_dry_run():
    result = runner.invoke(app, ["rtk", "sync", "--platforms", "opencode,codex", "--format", "json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["dry_run"] is True
    assert [command["platform"] for command in payload["commands"]] == ["opencode", "codex"]
    assert all(result["dry_run"] is True for result in payload["results"])


def test_rtk_sync_rejects_unknown_platform():
    result = runner.invoke(app, ["rtk", "sync", "--platforms", "unknown", "--format", "json"])

    assert result.exit_code == 2
    assert "Unknown RTK platform" in result.output


def _live_plan(tmp_path):
    return {
        "dry_run": False,
        "repo_root": str(tmp_path),
        "env": {"RTK_TELEMETRY_DISABLED": "1"},
        "commands": [
            {
                "platform": "opencode",
                "command": "rtk init -g --opencode --auto-patch",
                "argv": ["rtk", "init", "-g", "--opencode", "--auto-patch"],
                "dry_run": False,
            }
        ],
    }


def test_rtk_sync_apply_uses_bounded_noninteractive_subprocess(monkeypatch, tmp_path):
    def fake_run(argv, **kwargs):
        assert argv == ["rtk", "init", "-g", "--opencode", "--auto-patch"]
        assert kwargs["stdin"] is subprocess.DEVNULL
        assert kwargs["timeout"] == 120
        assert kwargs["cwd"] == tmp_path
        assert kwargs["env"]["RTK_TELEMETRY_DISABLED"] == "1"
        return _completed(argv, "ok\n", "", 0)

    monkeypatch.setattr("wagents.rtk.subprocess.run", fake_run)

    results = run_rtk_sync_plan(_live_plan(tmp_path), cwd=tmp_path)

    assert results == [
        {
            "platform": "opencode",
            "command": "rtk init -g --opencode --auto-patch",
            "returncode": 0,
            "stdout": "ok",
            "stderr": "",
        }
    ]


def test_rtk_sync_apply_timeout_returns_structured_result(monkeypatch, tmp_path):
    def fake_run(argv, **_kwargs):
        raise subprocess.TimeoutExpired(argv, timeout=120, output="partial stdout", stderr="partial stderr")

    monkeypatch.setattr("wagents.rtk.subprocess.run", fake_run)

    result = run_rtk_sync_plan(_live_plan(tmp_path), cwd=tmp_path)[0]

    assert result["returncode"] == 124
    assert result["stdout"] == "partial stdout"
    assert result["stderr"] == "timed out after 120s"
    assert result["timeout_seconds"] == 120


def test_rtk_sync_apply_missing_binary_returns_structured_result(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "wagents.rtk.subprocess.run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(FileNotFoundError("no rtk")),
    )

    result = run_rtk_sync_plan(_live_plan(tmp_path), cwd=tmp_path)[0]

    assert result["returncode"] == 127
    assert "no rtk" in result["stderr"]


def test_rtk_sync_apply_preserves_nonzero_result(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "wagents.rtk.subprocess.run",
        lambda argv, **_kwargs: _completed(argv, "stdout text\n", "stderr text\n", 3),
    )

    result = run_rtk_sync_plan(_live_plan(tmp_path), cwd=tmp_path)[0]

    assert result["returncode"] == 3
    assert result["stdout"] == "stdout text"
    assert result["stderr"] == "stderr text"


def test_rtk_sync_apply_rejects_non_init_rtk_command_without_subprocess(monkeypatch, tmp_path):
    def fail_run(*_args, **_kwargs):
        raise AssertionError("non-init RTK sync command should not execute")

    monkeypatch.setattr("wagents.rtk.subprocess.run", fail_run)
    plan = _live_plan(tmp_path)
    plan["commands"][0]["command"] = "rtk gain"
    plan["commands"][0]["argv"] = ["rtk", "gain"]

    result = run_rtk_sync_plan(plan, cwd=tmp_path)[0]

    assert result == {
        "platform": "opencode",
        "command": "rtk gain",
        "returncode": 2,
        "stdout": "",
        "stderr": "only rtk init commands are executable",
    }


def test_rtk_sync_apply_rejects_invalid_argv_without_subprocess(monkeypatch, tmp_path):
    def fail_run(*_args, **_kwargs):
        raise AssertionError("invalid RTK sync command should not execute")

    monkeypatch.setattr("wagents.rtk.subprocess.run", fail_run)

    for argv in ([], ["rtk"], ["echo", "x"]):
        plan = _live_plan(tmp_path)
        plan["commands"][0]["command"] = " ".join(argv)
        plan["commands"][0]["argv"] = argv

        result = run_rtk_sync_plan(plan, cwd=tmp_path)[0]

        assert result["returncode"] == 2
        assert result["stdout"] == ""
        assert result["stderr"] == "only rtk init commands are executable"


def test_rtk_sync_plan_skips_malformed_non_init_policy_command(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "rtk-integration.json").write_text(
        json.dumps({
            "version": 1,
            "harnesses": {
                "bad": {
                    "tier": "test",
                    "mode": "test",
                    "init": ["rtk gain"],
                    "notes": "bad policy entry",
                },
                "good": {
                    "tier": "test",
                    "mode": "test",
                    "init": ["rtk init --codex"],
                    "notes": "good policy entry",
                },
            },
        }),
        encoding="utf-8",
    )

    plan = build_rtk_sync_plan(root=tmp_path)

    assert [command["platform"] for command in plan["commands"]] == ["good"]
    assert plan["commands"][0]["argv"] == ["rtk", "init", "--codex"]
    assert plan["skipped"] == [
        {
            "platform": "bad",
            "reason": "unsupported sync command: only rtk init commands are executable: rtk gain",
        }
    ]
