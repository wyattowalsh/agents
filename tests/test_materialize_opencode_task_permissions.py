"""Tests for scripts/materialize_opencode_task_permissions.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "materialize_opencode_task_permissions.py"


def test_materialize_script_check_passes_when_overlay_matches_policy() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_materialize_script_apply_is_idempotent() -> None:
    first = subprocess.run(
        [sys.executable, str(SCRIPT), "--apply"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert first.returncode == 0, first.stderr or first.stdout
    second = subprocess.run(
        [sys.executable, str(SCRIPT), "--apply"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert second.returncode == 0, second.stderr or second.stdout
    overlay = json.loads((ROOT / "config" / "opencode-agents.json").read_text(encoding="utf-8"))
    orchestrator = next(entry for entry in overlay["agents"] if entry["name"] == "orchestrator")
    assert orchestrator["permission"]["task"]["mcp-capability-mapper"] == "allow"