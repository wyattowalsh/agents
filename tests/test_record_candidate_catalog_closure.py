from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from wagents.candidate_predicates import evaluate_predicate

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "_candidate_catalog_closure",
        ROOT / "scripts" / "record_candidate_catalog_closure.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _authoring_source(row: dict[str, Any]) -> str:
    agents = ", ".join(f'"{agent}"' for agent in row["target_agents"])
    return "\n".join([
        "---",
        'name: "example"',
        'install_skill_name: "example"',
        f'source_url: "{row["normalized_url"]}"',
        'source_kind: "curated-external"',
        'install_source: "Example/Repo"',
        'install_command: "npx skills add Example/Repo --skill example"',
        'status: "install-now-after-trust-gate"',
        'trust_tier: "curated-trust-gated"',
        'provenance_status: "verified-install-command"',
        'selector_mode: "named"',
        'sync_kind: "skills-cli"',
        f"target_agents: [{agents}]",
        "---",
        "",
    ])


def _promotion_row(tmp_path: Path) -> dict[str, Any]:
    installed = tmp_path / "installed" / "example"
    installed.mkdir(parents=True, exist_ok=True)
    (installed / "SKILL.md").write_text("---\nname: example\ndescription: Example.\n---\n", encoding="utf-8")
    return {
        "normalized_url": "https://github.com/Example/Repo",
        "skill_name": "example",
        "target_agents": ["codex", "cursor"],
        "install_source": "Example/Repo",
        "install_command": "npx skills add Example/Repo --skill example",
        "status": "install-now-after-trust-gate",
        "trust_tier": "curated-trust-gated",
        "provenance_status": "verified-install-command",
        "selector_mode": "named",
        "sync_kind": "skills-cli",
        "audited_head": "a" * 40,
        "installed_paths": [str(installed)],
    }


def _catalog_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": "example",
        "sourceUrl": row["normalized_url"],
        "sourcePath": "docs/src/authoring/skills/example.mdx",
        "installSource": row["install_source"],
        "installCommand": row["install_command"],
        "installable": True,
        "sourceKind": "curated-external",
        "provenanceStatus": row["provenance_status"],
        "status": row["status"],
        "trustTier": row["trust_tier"],
        "selectorMode": row["selector_mode"],
        "syncKind": row["sync_kind"],
        "targetAgents": row["target_agents"],
        "auditedHead": row["audited_head"],
        "useCommand": "/example",
    }


def _binding_phase_rows(
    module,
    graph: dict[str, dict[str, Any]],
    report: Path,
    catalog_by_name: dict[str, dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    retained = module.sanitized_sync_evidence(report_payload, report_payload["agents"])
    sync_digest = module.sha256(report)
    assert module.object_sha256(retained)
    recorded_at = datetime.now(UTC).isoformat()
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for selector_id, item in graph.items():
        catalog_row = catalog_by_name[item["skill_name"]]
        capabilities, errors = module.required_capabilities(item, catalog_row)
        assert errors == []
        installed_digest, errors = module.current_installed_digest(item)
        assert errors == []
        authoring_digest = module.sha256(module.ROOT / item["path"])
        for agent in item["target_agents"]:
            binding_id = f"binding:{selector_id}:{agent}"
            input_digest = module.binding_input_digest(
                item,
                agent=agent,
                authoring_sha256=authoring_digest,
                catalog_row=catalog_row,
                sync_report_sha256=sync_digest,
                capabilities=capabilities,
            )
            common = {
                "artifact_id": binding_id,
                "selector_id": selector_id,
                "harness": agent,
                "source_commit_sha": item["audited_head"],
                "input_digest": input_digest,
                "installed_digest": installed_digest,
                "predicate_version": module.RUNTIME_PREDICATE_VERSION,
                "recorded_at": recorded_at,
            }
            phase_values = {
                "discovery": {
                    "discovery_status": "passed",
                    "sync_disposition": "already-present",
                    "sync_report_sha256": sync_digest,
                },
                "behavior": {
                    "positive_status": "passed",
                    "negative_status": "passed",
                    "positive_assertions": ["invocation produced the expected semantic result"],
                    "negative_assertions": ["invalid input was rejected"],
                    "proved_capabilities": capabilities,
                },
                "fresh_process": {
                    "fresh_process_status": "passed",
                    "initial_process_id": f"{binding_id}:initial",
                    "fresh_process_id": f"{binding_id}:fresh",
                },
                "rollback": {
                    "absence_status": "passed",
                    "restore_status": "passed",
                    "unchanged_state_status": "passed",
                    "final_state_status": "passed",
                    "restored_installed_digest": installed_digest,
                },
            }
            for phase, values in phase_values.items():
                row = {**common, "phase": phase, **values}
                row["assertion_sha256"] = module.object_sha256(row)
                rows[binding_id, phase] = row
            prior = {
                phase: module.artifact_receipt_sha256(rows[binding_id, phase])
                for phase in module.BINDING_PROOF_PHASES[:-1]
            }
            final = {
                **common,
                "phase": "promoted_final",
                "promoted_final_status": "passed",
                "phase_receipt_digests": prior,
            }
            final["assertion_sha256"] = module.object_sha256(final)
            rows[binding_id, "promoted_final"] = final
    return rows


def _closure_fixture(monkeypatch, tmp_path: Path):
    module = _module()
    row = _promotion_row(tmp_path)
    authoring = tmp_path / "docs" / "src" / "authoring" / "skills"
    authoring.mkdir(parents=True, exist_ok=True)
    (authoring / "example.mdx").write_text(_authoring_source(row), encoding="utf-8")
    promotion = tmp_path / "promotion.json"
    applied = tmp_path / "applied.json"
    catalog = tmp_path / "catalog.json"
    assurance = tmp_path / "assurance.json"
    report = tmp_path / "sync.json"
    _write(promotion, {"overrides": [row]})
    _write(
        applied,
        {
            "items": [
                {
                    "normalized_url": row["normalized_url"],
                    "skill_name": "example",
                    "path": "docs/src/authoring/skills/example.mdx",
                }
            ]
        },
    )
    _write(catalog, {"allSkillIndex": [_catalog_row(row)]})
    report_payload = {
        "ok": True,
        "mode": "apply",
        "agents": [
            {
                "agent": agent,
                "already_present": ["example [verified] - Example/Repo"],
                "missing": [],
                "pin_blocked": [],
            }
            for agent in ("codex", "cursor")
        ],
    }
    _write(report, report_payload)
    _write(assurance, {"complete": True, "source_sha256": module.sha256(report)})
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "PROMOTION_OVERRIDES", promotion)
    monkeypatch.setattr(module, "APPLIED_OVERRIDES", applied)
    monkeypatch.setattr(module, "CATALOG_INDEX", catalog)
    monkeypatch.setattr(module, "HARNESS_ASSURANCE", assurance)
    graph = module.selector_graph(module.promotion_rows())
    catalog_by_name = module.catalog_rows_by_name()
    rows = _binding_phase_rows(module, graph, report, catalog_by_name)
    return module, graph, report, rows


def test_build_receipts_proves_each_selector_and_binding(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    authoring = tmp_path / "docs" / "src" / "authoring" / "skills"
    authoring.mkdir(parents=True)
    row = _promotion_row(tmp_path)
    authoring_path = authoring / "example.mdx"
    authoring_path.write_text(_authoring_source(row), encoding="utf-8")
    promotion = tmp_path / "promotion.json"
    applied = tmp_path / "applied.json"
    catalog = tmp_path / "catalog.json"
    assurance = tmp_path / "assurance.json"
    report = tmp_path / "sync.json"
    _write(promotion, {"overrides": [row]})
    _write(
        applied,
        {
            "items": [
                {
                    "normalized_url": row["normalized_url"],
                    "skill_name": "example",
                    "path": "docs/src/authoring/skills/example.mdx",
                }
            ]
        },
    )
    _write(
        catalog,
        {"allSkillIndex": [_catalog_row(row)]},
    )
    report_payload = {
        "ok": True,
        "mode": "apply",
        "agents": [
            {"agent": agent, "already_present": ["example [verified] - Example/Repo"], "missing": [], "pin_blocked": []}
            for agent in ("codex", "cursor")
        ],
    }
    _write(report, report_payload)
    _write(assurance, {"complete": True, "source_sha256": module.sha256(report)})
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "PROMOTION_OVERRIDES", promotion)
    monkeypatch.setattr(module, "APPLIED_OVERRIDES", applied)
    monkeypatch.setattr(module, "CATALOG_INDEX", catalog)
    monkeypatch.setattr(module, "HARNESS_ASSURANCE", assurance)

    graph = module.selector_graph(module.promotion_rows())
    catalog_by_name = module.catalog_rows_by_name()
    artifact_rows = _binding_phase_rows(module, graph, report, catalog_by_name)
    receipts = module.build_receipts(graph, report, artifact_rows)

    assert len(receipts["selector-closure"]["leaf_receipts"]) == 1
    assert len(receipts["harness-binding-closure"]["leaf_receipts"]) == 2
    assert all(leaf["status"] == "accepted" for leaf in receipts["harness-binding-closure"]["leaf_receipts"])
    selector = receipts["selector-closure"]
    selector_leaf = selector["leaf_receipts"][0]
    authoring_relative = "docs/src/authoring/skills/example.mdx"
    assert selector_leaf["authoring_sha256"] == module.sha256(authoring_path)
    assert selector_leaf["frontmatter_binding_sha256"]
    assert authoring_relative in selector["evidence_paths"]
    assert selector["evidence_digests"][authoring_relative] == module.sha256(authoring_path)
    binding = receipts["harness-binding-closure"]
    assert binding["source_report_sha256"] == module.sha256(report)
    assert binding["sync_report_sha256"] == binding["source_report_sha256"]
    assert binding["sanitized_sync_report"]["agents"][0]["inventory"]["already_present"] == {"example": 1}
    assert binding["sanitized_sync_report_sha256"] == module.object_sha256(binding["sanitized_sync_report"])
    assert binding["source_report_evidence_sha256"] == binding["sanitized_sync_report_sha256"]
    assert all(
        leaf["sync_report_sha256"] == binding["source_report_sha256"]
        and leaf["sync_evidence_sha256"] == binding["source_report_evidence_sha256"]
        for leaf in binding["leaf_receipts"]
    )
    selector_metadata = {
        selector_leaf["node_id"]: {
            field: selector_leaf[field]
            for field in ("selector_id", "normalized_url", "skill_name", "path", "authoring_sha256")
        }
    }
    assert (
        evaluate_predicate(
            "selector-closure",
            selector,
            {
                "expected_leaf_ids": list(selector_metadata),
                "expected_leaf_metadata": selector_metadata,
            },
        )
        == []
    )
    binding_metadata = {
        leaf["node_id"]: {field: leaf[field] for field in ("selector_id", "normalized_url", "skill_name", "agent")}
        for leaf in binding["leaf_receipts"]
    }
    assert (
        evaluate_predicate(
            "harness-binding-closure",
            binding,
            {
                "expected_leaf_ids": list(binding_metadata),
                "expected_leaf_metadata": binding_metadata,
                "target_harnesses": binding["target_harnesses"],
                "expected_sync_report_sha256": binding["sync_report_sha256"],
            },
        )
        == []
    )


def test_binding_closure_rejects_missing_phase(monkeypatch, tmp_path: Path) -> None:
    module, graph, report, rows = _closure_fixture(monkeypatch, tmp_path)
    binding_id = next(binding_id for binding_id, phase in rows if phase == "rollback")
    rows.pop((binding_id, "rollback"))

    receipts = module.build_receipts(graph, report, rows)
    leaf = next(item for item in receipts["harness-binding-closure"]["leaf_receipts"] if item["node_id"] == binding_id)

    assert leaf["status"] == "incomplete"
    assert leaf["phase_evidence"]["rollback"]["status"] == "incomplete"
    assert "missing binding phase receipt" in " ".join(leaf["predicate_errors"])


@pytest.mark.parametrize("field", ("input_digest", "installed_digest"))
def test_binding_closure_rejects_stale_current_digest(
    monkeypatch,
    tmp_path: Path,
    field: str,
) -> None:
    module, graph, report, rows = _closure_fixture(monkeypatch, tmp_path)
    key = next(key for key in rows if key[1] == "behavior")
    rows[key][field] = "f" * 64
    rows[key]["assertion_sha256"] = module.object_sha256({
        name: value for name, value in rows[key].items() if name != "assertion_sha256"
    })

    receipt = module.build_receipts(graph, report, rows)["harness-binding-closure"]
    leaf = next(item for item in receipt["leaf_receipts"] if item["node_id"] == key[0])

    assert leaf["status"] == "incomplete"
    assert f"{field} does not match the current binding" in " ".join(leaf["predicate_errors"])


def test_binding_closure_derives_untested_capabilities(monkeypatch, tmp_path: Path) -> None:
    module, graph, report, rows = _closure_fixture(monkeypatch, tmp_path)
    key = next(key for key in rows if key[1] == "behavior")
    rows[key]["proved_capabilities"] = []
    rows[key]["assertion_sha256"] = module.object_sha256({
        name: value for name, value in rows[key].items() if name != "assertion_sha256"
    })

    receipt = module.build_receipts(graph, report, rows)["harness-binding-closure"]
    leaf = next(item for item in receipt["leaf_receipts"] if item["node_id"] == key[0])

    assert leaf["required_capabilities"] == ["invoke:/example"]
    assert leaf["proved_capabilities"] == []
    assert leaf["untested_capabilities"] == ["invoke:/example"]
    assert receipt["untested_capabilities"]
    assert leaf["status"] == "incomplete"


def test_binding_closure_rejects_reused_assertion_digest(monkeypatch, tmp_path: Path) -> None:
    module, graph, report, rows = _closure_fixture(monkeypatch, tmp_path)
    behavior_keys = [key for key in rows if key[1] == "behavior"]
    rows[behavior_keys[1]]["assertion_sha256"] = rows[behavior_keys[0]]["assertion_sha256"]

    receipt = module.build_receipts(graph, report, rows)["harness-binding-closure"]
    errors = " ".join(error for leaf in receipt["leaf_receipts"] for error in leaf["predicate_errors"])

    assert "assertion digest is reused across binding phases" in errors
    assert "canonical content digest" in errors


def test_selector_receipt_fails_when_authoring_frontmatter_drifts(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    authoring = tmp_path / "docs" / "src" / "authoring" / "skills"
    authoring.mkdir(parents=True)
    row = _promotion_row(tmp_path)
    (authoring / "example.mdx").write_text(
        _authoring_source(row).replace('install_skill_name: "example"', 'install_skill_name: "wrong"'),
        encoding="utf-8",
    )
    promotion = tmp_path / "promotion.json"
    applied = tmp_path / "applied.json"
    catalog = tmp_path / "catalog.json"
    _write(promotion, {"overrides": [row]})
    _write(
        applied,
        {
            "items": [
                {
                    "normalized_url": row["normalized_url"],
                    "skill_name": "example",
                    "path": "docs/src/authoring/skills/example.mdx",
                }
            ]
        },
    )
    _write(
        catalog,
        {"allSkillIndex": [_catalog_row(row)]},
    )
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "PROMOTION_OVERRIDES", promotion)
    monkeypatch.setattr(module, "APPLIED_OVERRIDES", applied)
    monkeypatch.setattr(module, "CATALOG_INDEX", catalog)

    graph = module.selector_graph(module.promotion_rows())
    receipt = module.build_selector_receipt(graph, module.catalog_rows_by_name(), [])

    assert receipt["verification_status"] == "failed"
    assert receipt["active_blockers"]
    assert "install_skill_name drifted" in " ".join(receipt["leaf_receipts"][0]["predicate_errors"])


def test_selector_receipt_rejects_generated_catalog_policy_drift(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    row = _promotion_row(tmp_path)
    authoring = tmp_path / "docs" / "src" / "authoring" / "skills"
    authoring.mkdir(parents=True)
    (authoring / "example.mdx").write_text(_authoring_source(row), encoding="utf-8")
    promotion = tmp_path / "promotion.json"
    applied = tmp_path / "applied.json"
    catalog = tmp_path / "catalog.json"
    _write(promotion, {"overrides": [row]})
    _write(
        applied,
        {
            "items": [
                {
                    "normalized_url": row["normalized_url"],
                    "skill_name": "example",
                    "path": "docs/src/authoring/skills/example.mdx",
                }
            ]
        },
    )
    catalog_row = _catalog_row(row)
    for field in ("installSource", "targetAgents", "trustTier", "status", "selectorMode", "syncKind"):
        catalog_row[field] = "wrong" if field != "targetAgents" else ["wrong"]
    _write(catalog, {"allSkillIndex": [catalog_row]})
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "PROMOTION_OVERRIDES", promotion)
    monkeypatch.setattr(module, "APPLIED_OVERRIDES", applied)
    monkeypatch.setattr(module, "CATALOG_INDEX", catalog)

    graph = module.selector_graph(module.promotion_rows())
    receipt = module.build_selector_receipt(graph, module.catalog_rows_by_name(), [])

    assert receipt["verification_status"] == "failed"
    errors = " ".join(receipt["leaf_receipts"][0]["predicate_errors"])
    for field in ("installSource", "targetAgents", "trustTier", "status", "selectorMode", "syncKind"):
        assert f"generated catalog {field} drifted" in errors


def test_binding_receipt_rejects_duplicate_inventory_names(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    row = _promotion_row(tmp_path)
    row["target_agents"] = ["codex"]
    authoring = tmp_path / "docs" / "src" / "authoring" / "skills"
    authoring.mkdir(parents=True)
    (authoring / "example.mdx").write_text(_authoring_source(row), encoding="utf-8")
    assurance = tmp_path / "assurance.json"
    report = tmp_path / "sync.json"
    _write(
        report,
        {
            "ok": True,
            "mode": "dry-run",
            "agents": [
                {
                    "agent": "codex",
                    "already_present": ["example [verified] - one", "example [verified] - two"],
                    "missing": [],
                    "pin_blocked": [],
                }
            ],
        },
    )
    _write(assurance, {"complete": True, "source_sha256": module.sha256(report)})
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "HARNESS_ASSURANCE", assurance)
    monkeypatch.setattr(module, "PROMOTION_OVERRIDES", tmp_path / "promotion.json")
    monkeypatch.setattr(module, "CATALOG_INDEX", tmp_path / "catalog.json")
    _write(module.PROMOTION_OVERRIDES, {"overrides": [row]})
    _write(module.CATALOG_INDEX, {"allSkillIndex": [_catalog_row(row)]})
    graph = module.selector_graph(module.promotion_rows())

    receipt = module.build_binding_receipt(graph, report, {}, module.catalog_rows_by_name())

    assert receipt["verification_status"] == "failed"
    assert any("already-present count is 2" in error for error in receipt["leaf_receipts"][0]["predicate_errors"])


def test_sync_skill_name_rejects_unstructured_rows() -> None:
    module = _module()
    with pytest.raises(ValueError, match="marker"):
        module.sync_skill_name("example")


def _failed_receipts() -> dict[str, dict[str, object]]:
    return {
        "selector-closure": {
            "gate_id": "selector-closure",
            "verification_status": "failed",
            "active_blockers": ["selector:a"],
            "leaf_receipts": [],
        },
        "harness-binding-closure": {
            "gate_id": "harness-binding-closure",
            "verification_status": "passed",
            "active_blockers": [],
            "leaf_receipts": [],
            "target_harnesses": [],
            "source_report_sha256": "a" * 64,
        },
    }


def test_main_refuses_invalid_apply(monkeypatch, capsys, tmp_path: Path) -> None:
    module = _module()
    receipts = tmp_path / "receipts.json"
    _write(receipts, {"version": 2, "revision": 0, "receipts": [], "closure_receipts": []})
    before = receipts.read_bytes()
    monkeypatch.setattr(module, "RECEIPTS", receipts)
    monkeypatch.setattr(module, "RUNTIME_STATE", tmp_path / "state")
    monkeypatch.setattr(module, "promotion_rows", lambda: [])
    monkeypatch.setattr(module, "build_receipts", lambda _graph, _path, _rows: _failed_receipts())
    monkeypatch.setattr(sys, "argv", ["record_candidate_catalog_closure.py", "--sync-report", "sync.json", "--apply"])

    assert module.main() == 1
    assert receipts.read_bytes() == before
    summary = json.loads(capsys.readouterr().out)
    assert summary["ok"] is False
    assert summary["applied"] is False
    assert "selector-closure verification_status is not passed" in summary["errors"]


def test_main_check_fails_for_invalid_current_receipts(monkeypatch, capsys, tmp_path: Path) -> None:
    module = _module()
    generated = _failed_receipts()
    current = [generated[key] for key in sorted(generated)]
    receipts = tmp_path / "receipts.json"
    _write(receipts, {"version": 2, "revision": 0, "receipts": [], "closure_receipts": current})
    monkeypatch.setattr(module, "RECEIPTS", receipts)
    monkeypatch.setattr(module, "RUNTIME_STATE", tmp_path / "state")
    monkeypatch.setattr(module, "promotion_rows", lambda: [])
    monkeypatch.setattr(module, "build_receipts", lambda _graph, _path, _rows: generated)
    monkeypatch.setattr(sys, "argv", ["record_candidate_catalog_closure.py", "--sync-report", "sync.json", "--check"])

    assert module.main() == 1
    summary = json.loads(capsys.readouterr().out)
    assert summary["ok"] is False
    assert summary["applied"] is False
    assert "stored selector or harness-binding closure receipts are stale" not in summary["errors"]
    assert "selector-closure has 1 active blockers" in summary["errors"]


def test_main_uses_one_snapshot_for_all_binding_phases_and_closure_commit(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    module = _module()
    row = _promotion_row(tmp_path)
    graph = module.selector_graph([row])
    expected_artifact_keys = module.binding_artifact_keys(graph)
    snapshot = SimpleNamespace(artifact_rows={}, closure_rows={})
    calls: dict[str, object] = {}

    class _FakeStore:
        def __init__(self, _path: Path, _state: Path) -> None:
            pass

        def snapshot(self, *, artifact_keys, closure_keys):
            calls["artifact_keys"] = artifact_keys
            calls["closure_keys"] = closure_keys
            return snapshot

        def commit(self, received_snapshot, *, closure_upserts):
            calls["commit_snapshot"] = received_snapshot
            calls["closure_upserts"] = closure_upserts

    generated = {
        "selector-closure": {
            "gate_id": "selector-closure",
            "verification_status": "passed",
            "active_blockers": [],
            "leaf_receipts": [{"node_id": "selector"}],
        },
        "harness-binding-closure": {
            "gate_id": "harness-binding-closure",
            "verification_status": "passed",
            "active_blockers": [],
            "leaf_receipts": [{"node_id": "binding"}],
            "target_harnesses": row["target_agents"],
            "source_report_sha256": "a" * 64,
        },
    }

    def _build(received_graph, _report, artifact_rows):
        assert received_graph == graph
        assert artifact_rows is snapshot.artifact_rows
        return generated

    monkeypatch.setattr(module, "ReceiptStore", _FakeStore)
    monkeypatch.setattr(module, "promotion_rows", lambda: [row])
    monkeypatch.setattr(module, "build_receipts", _build)
    monkeypatch.setattr(module, "RECEIPTS", tmp_path / "receipts.json")
    monkeypatch.setattr(module, "RUNTIME_STATE", tmp_path / "state")
    monkeypatch.setattr(sys, "argv", ["record_candidate_catalog_closure.py", "--sync-report", "sync.json", "--apply"])

    assert module.main() == 0
    assert calls["artifact_keys"] == expected_artifact_keys
    assert calls["closure_keys"] == {"selector-closure", "harness-binding-closure"}
    assert calls["commit_snapshot"] is snapshot
    assert calls["closure_upserts"] == generated
    assert json.loads(capsys.readouterr().out)["binding_leaf_count"] == 1
