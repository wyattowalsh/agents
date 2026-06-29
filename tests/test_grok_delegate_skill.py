"""Tests for grok-delegate skill assets and helper scripts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from wagents.parsing import parse_frontmatter

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "skills" / "grok-delegate"
PARSER = SKILL_DIR / "scripts" / "parse_grok_json.py"
DOCTOR = SKILL_DIR / "scripts" / "doctor.py"
PREFLIGHT = SKILL_DIR / "scripts" / "preflight.sh"
CHECK = SKILL_DIR / "scripts" / "check.py"

REQUIRED_DOCTOR_CHECKS = {
    "grok-binary",
    "grok-home-config",
    "grok-target-config",
    "grok-cli-smoke",
}


def _run_parser(payload: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PARSER)],
        input=payload,
        text=True,
        capture_output=True,
        check=False,
    )


def _run_doctor(*extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(DOCTOR), "--format", "json", *extra],
        text=True,
        capture_output=True,
        check=False,
    )


def test_skill_frontmatter_description_under_200_chars():
    fm, _ = parse_frontmatter((SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"))
    description = fm.get("description", "")
    assert isinstance(description, str)
    assert description
    assert len(description) <= 200
    assert "Use when" in description
    assert "NOT for" in description


def test_reference_files_exist():
    index = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    for name in (
        "wave-dag.md",
        "graph-patterns.md",
        "command-templates.md",
        "output-json.md",
        "doctor-output.md",
        "session-ledger.md",
        "agent-map.md",
        "concurrency.md",
        "leader-lifecycle.md",
        "acp-driver.md",
        "safety-permissions.md",
    ):
        assert f"references/{name}" in index
        assert (SKILL_DIR / "references" / name).is_file()


def test_parse_grok_json_happy_path():
    result = _run_parser('{"sessionId":"abc","stopReason":"EndTurn","text":"done"}')
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert "sessionId=abc" in lines
    assert "stopReason=EndTurn" in lines
    assert "text=done" in lines


@pytest.mark.parametrize("payload", ["", "not-json"])
def test_parse_grok_json_rejects_invalid_input(payload: str):
    result = _run_parser(payload)
    assert result.returncode == 1
    assert result.stderr


@pytest.mark.skipif(not Path("/tmp").exists(), reason="needs /tmp")
def test_doctor_emits_valid_json_schema():
    result = _run_doctor("--cwd", str(REPO_ROOT))
    assert result.returncode in (0, 1), result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert "ok" in payload
    assert "summary" in payload
    assert "checks" in payload
    names = {c["name"] for c in payload["checks"]}
    assert REQUIRED_DOCTOR_CHECKS.issubset(names)


@pytest.mark.skipif(not Path("/tmp").exists(), reason="needs /tmp")
def test_preflight_script_executable_and_emits_json():
    assert PREFLIGHT.is_file()
    assert PREFLIGHT.stat().st_mode & 0o111
    result = subprocess.run(
        ["bash", str(PREFLIGHT), "--cwd", str(REPO_ROOT)],
        cwd="/tmp",
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode in (0, 1), result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert "ok" in payload
    assert "checks" in payload
    assert any(c["name"] == "grok-binary" for c in payload["checks"])


def test_doctor_fails_when_grok_binary_missing():
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    try:
        import importlib

        doctor_module = importlib.import_module("doctor")
        with patch.object(doctor_module, "_grok_binary_path", return_value=None):
            report = doctor_module.build_report(doctor_module.collect_checks(cwd=REPO_ROOT))
        assert report["ok"] is False
        assert any(c["name"] == "grok-binary" and c["status"] == "fail" for c in report["checks"])
    finally:
        sys.path.pop(0)
        sys.modules.pop("doctor", None)


def test_check_py_passes():
    result = subprocess.run(
        [sys.executable, str(CHECK)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr