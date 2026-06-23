"""Tests for opt-in wagents telemetry."""

import json
import sys
from pathlib import Path

from typer.testing import CliRunner

from wagents.cli import app, run
from wagents.telemetry import end_command_telemetry

runner = CliRunner()


def _invoke(args: list[str]):
    result = runner.invoke(app, args)
    end_command_telemetry(result.exit_code)
    return result


def test_telemetry_records_when_enabled(tmp_path: Path, monkeypatch):
    telemetry_file = tmp_path / "telemetry.jsonl"
    monkeypatch.setenv("WAGENTS_TELEMETRY", "1")
    monkeypatch.setenv("WAGENTS_TELEMETRY_PATH", str(telemetry_file))

    result = _invoke(["self", "doctor", "--format", "json"])
    assert result.exit_code == 0, result.output

    lines = telemetry_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert "self" in payload["command"]
    assert payload["exit_code"] == 0
    assert payload["duration_ms"] >= 0


def test_telemetry_skipped_when_disabled(tmp_path: Path, monkeypatch):
    telemetry_file = tmp_path / "telemetry.jsonl"
    monkeypatch.delenv("WAGENTS_TELEMETRY", raising=False)
    monkeypatch.setenv("WAGENTS_TELEMETRY_PATH", str(telemetry_file))

    result = _invoke(["self", "doctor"])
    assert result.exit_code == 0, result.output
    assert not telemetry_file.exists()


def test_run_entrypoint_records_telemetry(tmp_path: Path, monkeypatch):
    telemetry_file = tmp_path / "telemetry.jsonl"
    monkeypatch.setenv("WAGENTS_TELEMETRY", "1")
    monkeypatch.setenv("WAGENTS_TELEMETRY_PATH", str(telemetry_file))
    monkeypatch.setattr(sys, "argv", ["wagents", "self", "doctor"])

    run()

    lines = telemetry_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
