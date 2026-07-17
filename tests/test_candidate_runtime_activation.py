from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "_candidate_runtime_activation",
        ROOT / "scripts" / "record_candidate_runtime_activation.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_runtime_activation_reopens_all_65_artifacts(monkeypatch) -> None:
    module = _module()
    monkeypatch.setattr(module, "load_receipts", lambda: {})

    payload = module.build_assurance()

    assert payload["source_target_count"] == 289
    assert payload["runtime_artifact_count"] == 65
    assert payload["totals"]["kind_counts"] == {"cli": 30, "library": 1, "mcp": 17, "plugin": 17}
    assert payload["requested_full_usability"] is False
    assert payload["totals"]["active_blocker_count"] == 65


def test_runtime_activation_does_not_import_path_or_config_evidence(monkeypatch) -> None:
    module = _module()
    monkeypatch.setattr(module, "load_receipts", lambda: {})

    payload = module.build_assurance()

    assert all(item["status"] == "incomplete" for item in payload["artifacts"])
    assert all(
        any("missing behavior receipt" in error for error in item["errors"])
        for item in payload["artifacts"]
    )


def test_runtime_activation_structural_gate_rejects_false_complete() -> None:
    module = _module()
    payload = {
        "source_target_count": 289,
        "runtime_artifact_count": 65,
        "artifacts": [
            {"artifact_id": f"a-{index}", "status": "incomplete"}
            for index in range(65)
        ],
        "requested_full_usability": True,
        "active_blockers": [],
    }

    assert "full usability cannot be true with incomplete artifacts" in module.structural_errors(payload)
