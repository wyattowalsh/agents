"""Tests for skills/skill-creator/scripts/progress.py — progress tracking."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Insert the script directory into sys.path so we can import directly.
sys.path.insert(
    0, str(Path(__file__).parent.parent / "skills" / "skill-creator" / "scripts")
)

from progress import cmd_init, cmd_metric, cmd_phase, cmd_read, cmd_status, main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_init(state_dir: Path, skill: str = "test-skill", mode: str = "create"):
    """Initialize a session and return the parsed state dict."""
    import argparse

    args = argparse.Namespace(
        skill=skill,
        mode=mode,
        session_id=None,
        state_dir=state_dir,
    )
    with patch("sys.stdout"):
        cmd_init(args)
    state_file = state_dir / f"{skill}.json"
    return json.loads(state_file.read_text())


# ---------------------------------------------------------------------------
# init subcommand
# ---------------------------------------------------------------------------


class TestInit:
    def test_creates_state_file(self, tmp_path: Path):
        state = _run_init(tmp_path)
        assert state["skill_name"] == "test-skill"
        assert state["mode"] == "create"
        assert state["status"] == "active"
        assert len(state["phases"]) == 6
        assert len(state["waves"]) == 2

    def test_improve_mode_skips_scaffold(self, tmp_path: Path):
        state = _run_init(tmp_path, mode="improve")
        scaffold = next(p for p in state["phases"] if p["id"] == "scaffold")
        assert scaffold["status"] == "skipped"

    def test_metrics_initialized(self, tmp_path: Path):
        state = _run_init(tmp_path)
        metrics = state["metrics"]
        assert metrics["files_created"] == 0
        assert metrics["lines_written"] == 0
        assert metrics["patterns_applied"] == []
        assert metrics["baseline_score"] is None
        assert metrics["current_score"] is None
        assert metrics["iteration_count"] == 0


# ---------------------------------------------------------------------------
# metric subcommand
# ---------------------------------------------------------------------------


class TestMetric:
    def test_set_integer_metric(self, tmp_path: Path):
        _run_init(tmp_path)
        import argparse

        args = argparse.Namespace(
            skill="test-skill", key="files_created", value="5", state_dir=tmp_path
        )
        with patch("sys.stdout"):
            cmd_metric(args)
        state = json.loads((tmp_path / "test-skill.json").read_text())
        assert state["metrics"]["files_created"] == 5

    def test_increment_integer_metric(self, tmp_path: Path):
        _run_init(tmp_path)
        import argparse

        # Set initial value
        args = argparse.Namespace(
            skill="test-skill", key="files_created", value="3", state_dir=tmp_path
        )
        with patch("sys.stdout"):
            cmd_metric(args)

        # Increment
        args.value = "+2"
        with patch("sys.stdout"):
            cmd_metric(args)

        state = json.loads((tmp_path / "test-skill.json").read_text())
        assert state["metrics"]["files_created"] == 5

    def test_set_none_metric_to_integer(self, tmp_path: Path):
        """HR-003 regression: None + plain integer should store as int, not string."""
        _run_init(tmp_path)
        import argparse

        args = argparse.Namespace(
            skill="test-skill",
            key="baseline_score",
            value="85",
            state_dir=tmp_path,
        )
        with patch("sys.stdout"):
            cmd_metric(args)
        state = json.loads((tmp_path / "test-skill.json").read_text())
        assert state["metrics"]["baseline_score"] == 85
        assert isinstance(state["metrics"]["baseline_score"], int)

    def test_set_none_metric_to_float(self, tmp_path: Path):
        _run_init(tmp_path)
        import argparse

        args = argparse.Namespace(
            skill="test-skill",
            key="baseline_score",
            value="85.5",
            state_dir=tmp_path,
        )
        with patch("sys.stdout"):
            cmd_metric(args)
        state = json.loads((tmp_path / "test-skill.json").read_text())
        assert state["metrics"]["baseline_score"] == 85.5

    def test_increment_none_metric(self, tmp_path: Path):
        """Incrementing a None metric should start from 0."""
        _run_init(tmp_path)
        import argparse

        args = argparse.Namespace(
            skill="test-skill",
            key="baseline_score",
            value="+10",
            state_dir=tmp_path,
        )
        with patch("sys.stdout"):
            cmd_metric(args)
        state = json.loads((tmp_path / "test-skill.json").read_text())
        assert state["metrics"]["baseline_score"] == 10

    def test_append_to_list_metric(self, tmp_path: Path):
        _run_init(tmp_path)
        import argparse

        args = argparse.Namespace(
            skill="test-skill",
            key="patterns_applied",
            value="dispatch-table",
            state_dir=tmp_path,
        )
        with patch("sys.stdout"):
            cmd_metric(args)
        state = json.loads((tmp_path / "test-skill.json").read_text())
        assert "dispatch-table" in state["metrics"]["patterns_applied"]

    def test_unknown_key_exits(self, tmp_path: Path):
        _run_init(tmp_path)
        import argparse

        args = argparse.Namespace(
            skill="test-skill",
            key="nonexistent_key",
            value="42",
            state_dir=tmp_path,
        )
        with pytest.raises(SystemExit):
            with patch("sys.stdout"):
                cmd_metric(args)


# ---------------------------------------------------------------------------
# phase subcommand
# ---------------------------------------------------------------------------


class TestPhase:
    def test_update_phase_status(self, tmp_path: Path):
        _run_init(tmp_path)
        import argparse

        args = argparse.Namespace(
            skill="test-skill",
            phase="understand",
            status="active",
            notes=None,
            state_dir=tmp_path,
        )
        with patch("sys.stdout"):
            cmd_phase(args)
        state = json.loads((tmp_path / "test-skill.json").read_text())
        phase = next(p for p in state["phases"] if p["id"] == "understand")
        assert phase["status"] == "active"
        assert phase["started_at"] is not None

    def test_complete_phase_sets_timestamp(self, tmp_path: Path):
        _run_init(tmp_path)
        import argparse

        args = argparse.Namespace(
            skill="test-skill",
            phase="understand",
            status="completed",
            notes="Done.",
            state_dir=tmp_path,
        )
        with patch("sys.stdout"):
            cmd_phase(args)
        state = json.loads((tmp_path / "test-skill.json").read_text())
        phase = next(p for p in state["phases"] if p["id"] == "understand")
        assert phase["status"] == "completed"
        assert phase["completed_at"] is not None
        assert phase["notes"] == "Done."

    def test_invalid_phase_exits(self, tmp_path: Path):
        _run_init(tmp_path)
        import argparse

        args = argparse.Namespace(
            skill="test-skill",
            phase="nonexistent",
            status="active",
            notes=None,
            state_dir=tmp_path,
        )
        with pytest.raises(SystemExit):
            with patch("sys.stdout"):
                cmd_phase(args)


# ---------------------------------------------------------------------------
# status subcommand
# ---------------------------------------------------------------------------


class TestStatus:
    def test_update_session_status(self, tmp_path: Path):
        _run_init(tmp_path)
        import argparse

        args = argparse.Namespace(
            skill="test-skill", status="completed", state_dir=tmp_path
        )
        with patch("sys.stdout"):
            cmd_status(args)
        state = json.loads((tmp_path / "test-skill.json").read_text())
        assert state["status"] == "completed"

    def test_invalid_status_exits(self, tmp_path: Path):
        _run_init(tmp_path)
        import argparse

        args = argparse.Namespace(
            skill="test-skill", status="invalid", state_dir=tmp_path
        )
        with pytest.raises(SystemExit):
            with patch("sys.stdout"):
                cmd_status(args)


# ---------------------------------------------------------------------------
# read subcommand
# ---------------------------------------------------------------------------


class TestRead:
    def test_read_json_format(self, tmp_path: Path, capsys):
        _run_init(tmp_path)
        import argparse

        args = argparse.Namespace(
            skill="test-skill", format="json", state_dir=tmp_path
        )
        cmd_read(args)
        output = capsys.readouterr().out
        state = json.loads(output)
        assert state["skill_name"] == "test-skill"

    def test_read_missing_skill_exits(self, tmp_path: Path):
        import argparse

        args = argparse.Namespace(
            skill="nonexistent", format="json", state_dir=tmp_path
        )
        with pytest.raises(SystemExit):
            cmd_read(args)


# ---------------------------------------------------------------------------
# CLI argument parsing (--inject no longer required)
# ---------------------------------------------------------------------------


class TestCLIParsing:
    def test_audit_without_inject_flag(self, monkeypatch):
        """HR-001 regression: --inject should not be required."""
        monkeypatch.setattr(sys, "argv", ["progress.py", "audit", "--skill", "nonexistent"])
        with pytest.raises(SystemExit) as exc_info:
            main()
        # Exit code 1 = runtime error (no state file) — expected
        # Exit code 2 = argument parsing error — would mean --inject still required
        assert exc_info.value.code == 1
