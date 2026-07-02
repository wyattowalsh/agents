"""Regression tests for ffmpeg skill helper scripts."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = ROOT / "skills" / "ffmpeg" / "scripts"


def _load_module(name: str, filename: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doctor = _load_module("ffmpeg_doctor", "doctor.py")


def _run_doctor(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "doctor.py"), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_doctor_json_shape(monkeypatch) -> None:
    monkeypatch.setattr(doctor.shutil, "which", lambda name: f"/usr/local/bin/{name}")
    monkeypatch.setattr(doctor, "_binary_version", lambda _path: "ffmpeg version 6.0")

    report = doctor.build_report(doctor.collect_checks())

    assert set(report) == {"ok", "summary", "checks"}
    assert report["summary"]["total"] == 2
    assert report["ok"] is True
    names = {check["name"] for check in report["checks"]}
    assert names == {"ffmpeg-binary", "ffprobe-binary"}
    for check in report["checks"]:
        assert check["status"] == "ok"
        assert "name" in check
        assert "summary" in check


def test_doctor_cli_emits_json() -> None:
    result = _run_doctor("--format", "json")
    payload = json.loads(result.stdout)

    assert "ok" in payload
    assert "summary" in payload
    assert isinstance(payload["checks"], list)
    assert len(payload["checks"]) == 2


def test_doctor_missing_binaries_report_fail(monkeypatch) -> None:
    monkeypatch.setattr(doctor.shutil, "which", lambda _name: None)

    report = doctor.build_report(doctor.collect_checks())

    assert report["ok"] is False
    assert report["summary"]["fail"] == 2
    for check in report["checks"]:
        assert check["status"] == "fail"
        assert "remediation" in check