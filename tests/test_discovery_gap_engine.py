"""Tests for harness-master discovery gap_engine.py."""

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
    assert spec
    assert spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def gap_mod():
    return _load("gap_engine", "gap_engine.py")


@pytest.fixture
def taxonomy():
    path = ROOT / "skills" / "harness-master" / "data" / "discovery" / "discovery-taxonomy.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_web_quality_is_high_priority(gap_mod, taxonomy) -> None:
    report = gap_mod.build_gap_report(
        taxonomy=taxonomy, inventory={"repo_count": 10, "installed_count": 5, "skills": []}
    )
    web = next(d for d in report.domains if d.id == "web-quality")
    assert web.coverage == "none"
    assert web.classification == "high"
    assert web.priority >= 9


def test_gap_report_validates(gap_mod, taxonomy) -> None:
    report = gap_mod.build_gap_report(taxonomy=taxonomy)
    payload = report.public_dict()
    errors = gap_mod.validate_gap_report(payload)
    assert errors == []
    assert "hooks" in payload
    assert isinstance(payload["hooks"], dict)


def test_gap_engine_cli(tmp_path, gap_mod) -> None:
    out = tmp_path / "gap.json"
    taxonomy = ROOT / "skills" / "harness-master" / "data" / "discovery" / "discovery-taxonomy.json"
    rc = gap_mod.main(["--taxonomy", str(taxonomy), "-o", str(out)])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "domains" in data
    assert len(data["domains"]) >= 18
