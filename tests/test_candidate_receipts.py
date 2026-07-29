from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from wagents.candidate_receipts import (
    ReceiptConflictError,
    ReceiptSchemaError,
    ReceiptStore,
    validate_receipt_document,
)

ROOT = Path(__file__).resolve().parents[1]


def store(tmp_path: Path) -> ReceiptStore:
    return ReceiptStore(tmp_path / "receipts.json", tmp_path / "state")


def artifact(artifact_id: str, phase: str, value: str) -> dict[str, str]:
    return {"artifact_id": artifact_id, "phase": phase, "value": value}


def closure(gate_id: str, value: str) -> dict[str, str]:
    return {"gate_id": gate_id, "value": value}


def test_disjoint_commits_merge_against_fresh_document(tmp_path: Path) -> None:
    receipts = store(tmp_path)
    left_key = ("left", "install")
    right_key = ("right", "install")
    left = receipts.snapshot(artifact_keys={left_key})
    right = receipts.snapshot(artifact_keys={right_key})

    receipts.commit(left, artifact_upserts={left_key: artifact(*left_key, "left")})
    receipts.commit(right, artifact_upserts={right_key: artifact(*right_key, "right")})

    rows = receipts.snapshot().artifact_rows
    assert set(rows) == {left_key, right_key}
    assert rows[left_key]["value"] == "left"
    assert rows[right_key]["value"] == "right"


def test_same_key_conflict_fails_closed(tmp_path: Path) -> None:
    receipts = store(tmp_path)
    key = ("shared", "behavior")
    first = receipts.snapshot(artifact_keys={key})
    stale = receipts.snapshot(artifact_keys={key})
    receipts.commit(first, artifact_upserts={key: artifact(*key, "first")})

    with pytest.raises(ReceiptConflictError, match="changed during transaction"):
        receipts.commit(stale, artifact_upserts={key: artifact(*key, "stale")})

    assert receipts.snapshot().artifact_rows[key]["value"] == "first"


def test_artifact_and_closure_commits_preserve_each_other(tmp_path: Path) -> None:
    receipts = store(tmp_path)
    artifact_key = ("tool", "identity")
    gate_id = "global-closure"
    artifact_snapshot = receipts.snapshot(artifact_keys={artifact_key})
    closure_snapshot = receipts.snapshot(closure_keys={gate_id})

    receipts.commit(artifact_snapshot, artifact_upserts={artifact_key: artifact(*artifact_key, "accepted")})
    receipts.commit(closure_snapshot, closure_upserts={gate_id: closure(gate_id, "accepted")})

    snapshot = receipts.snapshot()
    assert snapshot.artifact_rows[artifact_key]["value"] == "accepted"
    assert snapshot.closure_rows[gate_id]["value"] == "accepted"
    assert snapshot.revision == 2


def test_unowned_upsert_is_rejected(tmp_path: Path) -> None:
    receipts = store(tmp_path)
    snapshot = receipts.snapshot()
    key = ("unowned", "install")
    with pytest.raises(ReceiptConflictError, match="not owned"):
        receipts.commit(snapshot, artifact_upserts={key: artifact(*key, "value")})


def test_v1_is_diagnostic_only(tmp_path: Path) -> None:
    path = tmp_path / "receipts.json"
    path.write_text('{"version":1,"receipts":[],"closure_receipts":[]}\n', encoding="utf-8")
    receipts = ReceiptStore(path, tmp_path / "state")

    with pytest.raises(ReceiptSchemaError, match="run the receipt migration"):
        receipts.load()
    assert receipts.load(allow_v1=True)["revision"] == 0


def test_duplicate_keys_are_rejected() -> None:
    document = {
        "version": 2,
        "revision": 0,
        "receipts": [
            artifact("duplicate", "install", "one"),
            artifact("duplicate", "install", "two"),
        ],
        "closure_receipts": [],
    }
    with pytest.raises(ReceiptSchemaError, match="duplicate artifact receipt key"):
        validate_receipt_document(document)


def test_runtime_receipt_schema_validates_committed_ledger() -> None:
    schema = json.loads((ROOT / "config/schemas/runtime-activation-receipts.schema.json").read_text(encoding="utf-8"))
    ledger = json.loads(
        (ROOT / "planning/manifests/candidate-corpus-jul2026/runtime-activation-receipts.json").read_text(
            encoding="utf-8"
        )
    )

    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(ledger)


def test_runtime_receipt_schema_rejects_unproven_passed_activation() -> None:
    schema = json.loads((ROOT / "config/schemas/runtime-activation-receipts.schema.json").read_text(encoding="utf-8"))
    document = {
        "version": 2,
        "revision": 0,
        "receipts": [
            {
                "artifact_id": "candidate",
                "phase": "activation",
                "status": "passed",
            }
        ],
        "closure_receipts": [],
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(document)


def test_migrate_v1_preserves_rows_and_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "receipts.json"
    state = tmp_path / "state"
    legacy = {
        "version": 1,
        "receipts": [
            {
                "artifact_id": "artifact",
                "phase": "install",
                "installed_digest": "a" * 64,
            }
        ],
        "closure_receipts": [{"gate_id": "docs-closure", "status": "passed"}],
    }
    path.write_text(json.dumps(legacy) + "\n", encoding="utf-8")
    receipts = ReceiptStore(path, state)

    first = receipts.migrate_v1()
    migrated = receipts.load()
    second = receipts.migrate_v1()

    assert first.migrated is True
    assert first.revision == 1
    assert first.transaction_id == migrated["migration_transaction_id"]
    assert migrated["receipts"] == legacy["receipts"]
    assert migrated["closure_receipts"] == legacy["closure_receipts"]
    assert second.migrated is False
    assert second.revision == 1
    assert second.transaction_id is None
    assert second.document_sha256 == first.document_sha256


def test_immutable_evidence_refuses_overwrite(tmp_path: Path) -> None:
    receipts = store(tmp_path)
    path = receipts.write_immutable_json(
        kind="plugin",
        transaction_id="tx-1",
        payload={"version": 2, "status": "passed"},
    )
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "passed"
    with pytest.raises(FileExistsError):
        receipts.write_immutable_json(
            kind="plugin",
            transaction_id="tx-1",
            payload={"version": 2, "status": "failed"},
        )


def test_immutable_evidence_failure_before_publish_leaves_no_final_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipts = store(tmp_path)
    destination = receipts.state_root / "receipts" / "journals" / "plugin" / "tx-crash.json"

    def fail_link(_source: Path, _destination: Path) -> None:
        raise OSError("simulated publish crash")

    monkeypatch.setattr("wagents.candidate_receipts.os.link", fail_link)
    with pytest.raises(OSError, match="simulated publish crash"):
        receipts.write_immutable_json(
            kind="plugin",
            transaction_id="tx-crash",
            payload={"version": 2, "status": "passed"},
        )

    assert not destination.exists()
    assert not list(destination.parent.glob(".*.staging-*"))


def test_atomic_write_failure_preserves_preimage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    receipts = store(tmp_path)
    key = ("stable", "install")
    first = receipts.snapshot(artifact_keys={key})
    receipts.commit(first, artifact_upserts={key: artifact(*key, "stable")})
    before = receipts.path.read_bytes()
    next_snapshot = receipts.snapshot(artifact_keys={key})

    def fail_write(_document: dict[str, object]) -> str:
        raise OSError("simulated crash")

    monkeypatch.setattr(receipts, "_atomic_write", fail_write)
    with pytest.raises(OSError, match="simulated crash"):
        receipts.commit(next_snapshot, artifact_upserts={key: artifact(*key, "changed")})
    assert receipts.path.read_bytes() == before
