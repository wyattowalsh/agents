"""Tests for harness-master discovery coordinator.py."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "harness-master" / "scripts" / "discovery"


def _load(name: str, filename: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    path = SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def coord_mod():
    return _load("coordinator", "coordinator.py")


@pytest.fixture
def gap_report():
    path = ROOT / "skills" / "harness-master" / "data" / "discovery" / "discovery-taxonomy.json"
    taxonomy = json.loads(path.read_text(encoding="utf-8"))
    gap_mod = _load("gap_engine", "gap_engine.py")
    report = gap_mod.build_gap_report(taxonomy=taxonomy)
    return report.public_dict()


def test_plan_wave2_manifest(coord_mod, gap_report, tmp_path) -> None:
    artifacts = tmp_path / "session"
    manifest = coord_mod.plan_wave(
        gap_report=gap_report,
        session_id="test-session",
        wave=2,
        artifacts_root=artifacts,
    )
    assert manifest["expected_count"] == len(manifest["tasks"])
    assert manifest["expected_count"] > 0
    assert manifest["expected_count"] <= coord_mod.MAX_WAVE2_TASKS
    errors = coord_mod.validate_wave_manifest(manifest)
    assert errors == []
    task_ids = [t["id"] for t in manifest["tasks"]]
    task_roles = {t["id"]: t["role"] for t in manifest["tasks"]}
    assert "W2-HK-00" in task_ids
    assert task_roles.get("W2-HK-00") == "hook-scout"


def test_verify_detects_missing(coord_mod, tmp_path) -> None:
    manifest = {
        "session_id": "s",
        "wave": 2,
        "expected_count": 1,
        "tasks": [
            {
                "id": "W2-RS-00",
                "role": "registry-scout",
                "outputs": {"artifact": str(tmp_path / "missing.json")},
            }
        ],
    }
    result = coord_mod.verify_manifest(manifest=manifest, artifacts_dir=tmp_path)
    assert result["ok"] is False
    assert result["resolved_count"] == 0


def test_write_checkpoint_includes_journal_v2_fields(coord_mod, tmp_path) -> None:
    artifacts = tmp_path / "session"
    artifacts.mkdir()
    coord_mod.write_checkpoint(
        artifacts,
        {
            "session_id": "test-session",
            "session_version": 2,
            "artifact_root": str(artifacts),
            "wave": 2,
            "manifest": str(artifacts / "wave-2.json"),
        },
    )
    payload = json.loads((artifacts / "checkpoint.json").read_text(encoding="utf-8"))
    assert payload["session_version"] == 2
    assert payload["artifact_root"] == str(artifacts)


def test_verify_counts_success(coord_mod, tmp_path) -> None:
    artifact = tmp_path / "W2-RS-00.json"
    artifact.write_text(
        json.dumps(
            {
                "task_id": "W2-RS-00",
                "role": "registry-scout",
                "status": "success",
                "candidates": [],
            }
        ),
        encoding="utf-8",
    )
    manifest = {
        "session_id": "s",
        "wave": 2,
        "expected_count": 1,
        "tasks": [
            {
                "id": "W2-RS-00",
                "role": "registry-scout",
                "outputs": {"artifact": str(artifact)},
            }
        ],
    }
    result = coord_mod.verify_manifest(manifest=manifest, artifacts_dir=tmp_path)
    assert result["ok"] is True
    assert result["resolved_count"] == 1