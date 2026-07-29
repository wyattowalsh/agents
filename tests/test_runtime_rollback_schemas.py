from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _schema(name: str) -> dict[str, object]:
    return json.loads((ROOT / "config" / "schemas" / name).read_text(encoding="utf-8"))


def test_commit_pending_journal_schema_requires_passed_artifacts() -> None:
    schema = _schema("runtime-rollback-journal.schema.json")
    valid = {
        "version": 2,
        "transaction_id": "transaction",
        "kind": "cli",
        "status": "commit-pending",
        "artifacts": [{"artifact_id": "artifact", "transaction_id": "artifact-transaction", "status": "passed"}],
    }

    jsonschema.validate(valid, schema)

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({**valid, "status": "passed"}, schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({**valid, "artifacts": [{**valid["artifacts"][0], "status": "failed"}]}, schema)


def test_rollback_commit_marker_schema_requires_receipt_cas_binding() -> None:
    schema = _schema("runtime-rollback-commit-marker.schema.json")
    valid = {
        "version": 2,
        "transaction_id": "transaction",
        "status": "passed",
        "journal_path": "/managed/journal.json",
        "journal_sha256": "a" * 64,
        "artifact_ids": ["artifact"],
        "receipt_revision": 1,
        "receipt_store_transaction_id": "receipt-transaction",
        "receipt_document_sha256": "b" * 64,
    }

    jsonschema.validate(valid, schema)

    for field in (
        "artifact_ids",
        "receipt_revision",
        "receipt_store_transaction_id",
        "receipt_document_sha256",
    ):
        invalid = dict(valid)
        invalid.pop(field)
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid, schema)


def test_rollback_failure_marker_schema_matches_transaction_failures() -> None:
    schema = _schema("runtime-rollback-failure-marker.schema.json")
    valid = {
        "version": 2,
        "transaction_id": "transaction",
        "status": "failed",
        "error_type": "ReceiptConflictError",
        "journal_path": "/managed/journal.json",
        "journal_sha256": "a" * 64,
    }

    jsonschema.validate(valid, schema)

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({**valid, "status": "passed"}, schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({**valid, "artifact_ids": ["artifact"]}, schema)
