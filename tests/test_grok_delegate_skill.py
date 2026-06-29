"""Tests for grok-delegate skill assets and helper scripts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from wagents.parsing import parse_frontmatter

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "skills" / "grok-delegate"
PARSER = SKILL_DIR / "scripts" / "parse_grok_json.py"
CHECK = SKILL_DIR / "scripts" / "check.py"


def _run_parser(payload: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PARSER)],
        input=payload,
        text=True,
        capture_output=True,
        check=False,
    )


def test_skill_frontmatter_description_under_200_chars():
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    frontmatter, _ = parse_frontmatter(text)
    description = frontmatter["description"]
    assert isinstance(description, str)
    assert "Use when delegating Grok" in description
    assert len(description) <= 200


def test_reference_files_exist():
    index = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    for name in (
        "wave-dag.md",
        "graph-patterns.md",
        "command-templates.md",
        "output-json.md",
        "session-ledger.md",
        "agent-map.md",
        "concurrency.md",
        "leader-lifecycle.md",
        "acp-driver.md",
        "safety-permissions.md",
        "doctor-output.md",
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


def test_check_py_passes():
    result = subprocess.run(
        [sys.executable, str(CHECK)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr