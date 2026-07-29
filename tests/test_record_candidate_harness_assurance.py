from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def _module():
    path = Path(__file__).parents[1] / "scripts" / "record_candidate_harness_assurance.py"
    spec = importlib.util.spec_from_file_location("record_candidate_harness_assurance", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


@pytest.mark.parametrize("mode", ["dry-run", "apply"])
def test_build_assurance_accepts_successful_sync_modes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mode: str,
) -> None:
    module = _module()
    catalog = tmp_path / "catalog.json"
    overrides = tmp_path / "overrides.json"
    report = tmp_path / "report.json"
    _write(catalog, {"allSkillIndex": [{"name": "example"}]})
    _write(overrides, {"overrides": []})
    _write(
        report,
        {
            "ok": True,
            "mode": mode,
            "inventory_count": 1,
            "agents": [
                {
                    "agent": agent,
                    "already_present": ["example [verified] - owner/repo"],
                    "missing": [],
                    "pin_blocked": [],
                    "unresolved": [],
                    "commands": [],
                    "warning": "",
                    "error": "",
                }
                for agent in module.EXPECTED_AGENTS
            ],
        },
    )
    monkeypatch.setattr(module, "CATALOG_INDEX", catalog)
    monkeypatch.setattr(module, "PROMOTION_OVERRIDES", overrides)

    assurance = module.build_assurance(report)

    assert assurance["complete"] is True
    assert assurance["source_mode"] == mode
    assert assurance["assurance_kind"] == f"post-install-{mode}"
    assert assurance["command"] == f"uv run wagents skills sync --{mode} --format json"


def test_build_assurance_rejects_unrecognized_mode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _module()
    report = tmp_path / "report.json"
    _write(report, {"ok": True, "mode": "preview"})
    monkeypatch.setattr(module, "CATALOG_INDEX", tmp_path / "unused-catalog.json")
    monkeypatch.setattr(module, "PROMOTION_OVERRIDES", tmp_path / "unused-overrides.json")

    with pytest.raises(ValueError, match="dry-run"):
        module.build_assurance(report)
