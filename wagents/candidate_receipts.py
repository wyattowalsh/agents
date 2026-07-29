"""Transactional storage for candidate runtime activation receipts."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

ReceiptKey = tuple[str, str]
_SAFE_PATH_PART = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
_IMMUTABLE_BUCKETS = {"journals", "failures", "transcripts"}


class ReceiptConflictError(RuntimeError):
    """Raised when an owned receipt key changed after its snapshot."""


class ReceiptSchemaError(ValueError):
    """Raised when a receipt document violates the v2 contract."""


@dataclass(frozen=True)
class StoreSnapshot:
    """A key-owned view of one receipt-store revision."""

    revision: int
    document: dict[str, Any]
    artifact_preimages: dict[ReceiptKey, str | None]
    closure_preimages: dict[str, str | None]

    @property
    def artifact_rows(self) -> dict[ReceiptKey, dict[str, Any]]:
        return _artifact_rows(self.document)

    @property
    def closure_rows(self) -> dict[str, dict[str, Any]]:
        return _closure_rows(self.document)


@dataclass(frozen=True)
class CommitResult:
    """Result of a successful receipt-store commit."""

    revision: int
    transaction_id: str
    document_sha256: str


@dataclass(frozen=True)
class MigrationResult:
    """Result of checking or migrating a legacy receipt document."""

    migrated: bool
    revision: int
    transaction_id: str | None
    document_sha256: str


def canonical_json(value: object) -> str:
    """Return stable JSON used for per-key optimistic comparisons."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _row_digest(row: dict[str, Any] | None) -> str | None:
    if row is None:
        return None
    return hashlib.sha256(canonical_json(row).encode("utf-8")).hexdigest()


def _artifact_rows(document: dict[str, Any]) -> dict[ReceiptKey, dict[str, Any]]:
    return {(str(row["artifact_id"]), str(row["phase"])): dict(row) for row in document["receipts"]}


def _closure_rows(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["gate_id"]): dict(row) for row in document["closure_receipts"]}


def _validate_row_object(row: object, *, label: str) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise ReceiptSchemaError(f"{label} must be an object")
    if not all(isinstance(key, str) for key in row):
        raise ReceiptSchemaError(f"{label} keys must be strings")
    return cast("dict[str, Any]", row)


def validate_receipt_document(document: object, *, allow_v1: bool = False) -> dict[str, Any]:
    """Validate and normalize a candidate receipt document."""

    if not isinstance(document, dict):
        raise ReceiptSchemaError("runtime receipt document must be an object")
    if not all(isinstance(key, str) for key in document):
        raise ReceiptSchemaError("runtime receipt document keys must be strings")
    normalized_document = cast("dict[str, Any]", document)
    version = normalized_document.get("version")
    if version == 1 and allow_v1:
        raw_revision = normalized_document.get("revision", 0)
        if not isinstance(raw_revision, int) or isinstance(raw_revision, bool) or raw_revision < 0:
            raise ReceiptSchemaError("receipt document revision must be a nonnegative integer")
        revision = raw_revision
        version_number = 1
    elif version == 2:
        revision = normalized_document.get("revision")
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
            raise ReceiptSchemaError("receipt document revision must be a nonnegative integer")
        version_number = 2
    else:
        raise ReceiptSchemaError("receipt document must be version 2; run the receipt migration for version 1")

    receipts = normalized_document.get("receipts")
    closures = normalized_document.get("closure_receipts")
    if not isinstance(receipts, list):
        raise ReceiptSchemaError("receipts must be an array")
    if not isinstance(closures, list):
        raise ReceiptSchemaError("closure_receipts must be an array")

    artifact_keys: set[ReceiptKey] = set()
    normalized_receipts: list[dict[str, Any]] = []
    for index, raw in enumerate(receipts):
        row = _validate_row_object(raw, label=f"receipts[{index}]")
        artifact_id = row.get("artifact_id")
        phase = row.get("phase")
        if not isinstance(artifact_id, str) or not artifact_id:
            raise ReceiptSchemaError(f"receipts[{index}].artifact_id must be a nonempty string")
        if not isinstance(phase, str) or not phase:
            raise ReceiptSchemaError(f"receipts[{index}].phase must be a nonempty string")
        key = (artifact_id, phase)
        if key in artifact_keys:
            raise ReceiptSchemaError(f"duplicate artifact receipt key: {artifact_id}:{phase}")
        artifact_keys.add(key)
        normalized_receipts.append(dict(row))

    closure_keys: set[str] = set()
    normalized_closures: list[dict[str, Any]] = []
    for index, raw in enumerate(closures):
        row = _validate_row_object(raw, label=f"closure_receipts[{index}]")
        gate_id = row.get("gate_id")
        if not isinstance(gate_id, str) or not gate_id:
            raise ReceiptSchemaError(f"closure_receipts[{index}].gate_id must be a nonempty string")
        if gate_id in closure_keys:
            raise ReceiptSchemaError(f"duplicate closure receipt key: {gate_id}")
        closure_keys.add(gate_id)
        normalized_closures.append(dict(row))

    return {
        **normalized_document,
        "version": version_number,
        "revision": revision,
        "receipts": sorted(normalized_receipts, key=lambda row: (str(row["artifact_id"]), str(row["phase"]))),
        "closure_receipts": sorted(normalized_closures, key=lambda row: str(row["gate_id"])),
    }


class ReceiptStore:
    """Key-owned optimistic receipt store with one shared commit lock."""

    def __init__(self, path: Path, state_root: Path | None = None) -> None:
        self.path = path.expanduser().absolute()
        self.state_root = (
            state_root.expanduser().absolute()
            if state_root is not None
            else Path("~/.local/share/wagents/candidate-runtime").expanduser().absolute()
        )
        path_key = hashlib.sha256(str(self.path).encode("utf-8")).hexdigest()[:24]
        self.lock_path = self.state_root / "locks" / f"{path_key}-runtime-activation-receipts.lock"

    def _empty_document(self) -> dict[str, Any]:
        return {"version": 2, "revision": 0, "receipts": [], "closure_receipts": []}

    def _load_unlocked(self, *, allow_v1: bool = False) -> dict[str, Any]:
        if not self.path.is_file():
            return self._empty_document()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return validate_receipt_document(payload, allow_v1=allow_v1)

    def load(self, *, allow_v1: bool = False) -> dict[str, Any]:
        """Read a validated document under the shared store lock."""

        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_SH)
            try:
                return self._load_unlocked(allow_v1=allow_v1)
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def snapshot(
        self,
        *,
        artifact_keys: set[ReceiptKey] | frozenset[ReceiptKey] = frozenset(),
        closure_keys: set[str] | frozenset[str] = frozenset(),
        allow_v1: bool = False,
    ) -> StoreSnapshot:
        """Capture canonical preimages for keys owned by one operation."""

        document = self.load(allow_v1=allow_v1)
        artifacts = _artifact_rows(document)
        closures = _closure_rows(document)
        return StoreSnapshot(
            revision=int(document["revision"]),
            document=document,
            artifact_preimages={key: _row_digest(artifacts.get(key)) for key in artifact_keys},
            closure_preimages={key: _row_digest(closures.get(key)) for key in closure_keys},
        )

    def migrate_v1(self) -> MigrationResult:
        """Atomically migrate a validated v1 document to the v2 store contract."""

        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                current = self._load_unlocked(allow_v1=True)
                if current["version"] == 2:
                    digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
                    return MigrationResult(
                        migrated=False,
                        revision=int(current["revision"]),
                        transaction_id=None,
                        document_sha256=digest,
                    )
                transaction_id = uuid.uuid4().hex
                migrated = validate_receipt_document({
                    **current,
                    "version": 2,
                    "revision": int(current["revision"]) + 1,
                    "migration_transaction_id": transaction_id,
                })
                digest = self._atomic_write(migrated)
                return MigrationResult(
                    migrated=True,
                    revision=int(migrated["revision"]),
                    transaction_id=transaction_id,
                    document_sha256=digest,
                )
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def _atomic_write(self, document: dict[str, Any]) -> str:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        encoded = (json.dumps(document, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
        temporary = self.path.with_name(f".{self.path.name}.wagents-{os.getpid()}-{uuid.uuid4().hex}")
        try:
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            directory_fd = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            temporary.unlink(missing_ok=True)
        return hashlib.sha256(encoded).hexdigest()

    def commit(
        self,
        snapshot: StoreSnapshot,
        *,
        artifact_upserts: dict[ReceiptKey, dict[str, Any]] | None = None,
        closure_upserts: dict[str, dict[str, Any]] | None = None,
    ) -> CommitResult:
        """Commit only owned keys and reject drift on those keys."""

        artifact_upserts = artifact_upserts or {}
        closure_upserts = closure_upserts or {}
        if not set(artifact_upserts).issubset(snapshot.artifact_preimages):
            raise ReceiptConflictError("artifact upserts include keys not owned by the snapshot")
        if not set(closure_upserts).issubset(snapshot.closure_preimages):
            raise ReceiptConflictError("closure upserts include keys not owned by the snapshot")

        transaction_id = uuid.uuid4().hex
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                current = self._load_unlocked()
                artifacts = _artifact_rows(current)
                closures = _closure_rows(current)
                for key, expected in snapshot.artifact_preimages.items():
                    if _row_digest(artifacts.get(key)) != expected:
                        raise ReceiptConflictError(f"artifact receipt changed during transaction: {key[0]}:{key[1]}")
                for key, expected in snapshot.closure_preimages.items():
                    if _row_digest(closures.get(key)) != expected:
                        raise ReceiptConflictError(f"closure receipt changed during transaction: {key}")

                for key, raw in artifact_upserts.items():
                    row = dict(raw)
                    if (str(row.get("artifact_id")), str(row.get("phase"))) != key:
                        raise ReceiptSchemaError(f"artifact upsert key does not match row: {key[0]}:{key[1]}")
                    row["store_transaction_id"] = transaction_id
                    artifacts[key] = row
                for key, raw in closure_upserts.items():
                    row = dict(raw)
                    if str(row.get("gate_id")) != key:
                        raise ReceiptSchemaError(f"closure upsert key does not match row: {key}")
                    row["store_transaction_id"] = transaction_id
                    closures[key] = row

                document = validate_receipt_document({
                    **current,
                    "version": 2,
                    "revision": int(current["revision"]) + 1,
                    "receipts": list(artifacts.values()),
                    "closure_receipts": list(closures.values()),
                })
                digest = self._atomic_write(document)
                return CommitResult(
                    revision=int(document["revision"]),
                    transaction_id=transaction_id,
                    document_sha256=digest,
                )
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def write_immutable_json(
        self,
        *,
        kind: str,
        transaction_id: str,
        payload: dict[str, Any],
        failure: bool = False,
        bucket: str | None = None,
    ) -> Path:
        """Finalize one immutable local journal or failure record."""

        if not _SAFE_PATH_PART.fullmatch(kind) or not _SAFE_PATH_PART.fullmatch(transaction_id):
            raise ValueError("immutable evidence kind and transaction id must be safe path components")
        bucket_name = bucket or ("failures" if failure else "journals")
        if bucket_name not in _IMMUTABLE_BUCKETS:
            raise ValueError(f"unsupported immutable evidence bucket: {bucket_name}")
        destination = self.state_root / "receipts" / bucket_name / kind / f"{transaction_id}.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        encoded = (json.dumps(payload, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
        temporary = destination.with_name(f".{destination.name}.staging-{os.getpid()}-{uuid.uuid4().hex}")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.link(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
        directory_fd = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return destination
