"""Cross-backend serialization and opaque two-phase mutation receipts."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import secrets
import sqlite3
import time
from contextlib import contextmanager, suppress
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .canonical import canonical_bytes
from .security import (
    AdvisoryMutationLock,
    SecureRuntimePaths,
    SecurityViolation,
    secure_file_descriptor,
    secure_read_bytes,
    secure_read_from_descriptor,
    secure_write_bytes,
    secure_write_to_descriptor,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

MIN_RECEIPT_TTL_SECONDS = 1.0
MAX_RECEIPT_TTL_SECONDS = 300.0
MAX_RECEIPT_STORE_BYTES = 64 * 1024 * 1024


class MutationError(RuntimeError):
    """Base class for fail-closed mutation protocol errors."""


class MutationBusyError(MutationError):
    """Another unexpired Things++ mutation reservation is active."""


class MutationReceiptError(MutationError):
    """A receipt is missing, replayed, expired, or bound to another request."""


class MutationStateError(MutationError):
    """The target state changed after preview."""


class MutationAmbiguousError(MutationError):
    """Execution may have happened and must never be retried automatically."""


class MutationPhase(StrEnum):
    PREVIEW = "preview"
    EXECUTE = "execute"


class MutationIntent(BaseModel):
    """Internal binding for one typed mutation; values are never stored verbatim."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    principal: str = Field(min_length=1, max_length=512)
    client_id: str = Field(min_length=1, max_length=256)
    resource: str = Field(min_length=1, max_length=1024)
    tool: str = Field(pattern=r"^[a-z0-9][a-z0-9_]{0,127}$")
    target_ids: tuple[str, ...] = Field(default=(), max_length=25)
    arguments: dict[str, Any]
    minimum_scope: Literal["things.read", "things.write", "things.admin"]

    @field_validator("target_ids")
    @classmethod
    def _unique_targets(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item or len(item) > 512 for item in value):
            raise ValueError("Target identifiers must be nonempty and bounded.")
        if len(set(value)) != len(value):
            raise ValueError("Target identifiers must be unique.")
        return value


class MutationPreview(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    status: Literal["preview"] = "preview"
    mutation_receipt: str = Field(min_length=43, max_length=64)
    receipt_id: str = Field(pattern=r"^[0-9a-f]{16}$")
    expires_at: float
    target_count: int = Field(ge=0, le=25)


class MutationExecution(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    status: Literal["changed", "skipped", "failed", "ambiguous"]
    receipt_id: str = Field(pattern=r"^[0-9a-f]{16}$")
    changed: int = Field(default=0, ge=0, le=25)
    skipped: int = Field(default=0, ge=0, le=25)
    failed: int = Field(default=0, ge=0, le=25)
    ambiguous: int = Field(default=0, ge=0, le=25)
    verification_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class MutationRecovery(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    status: Literal["changed", "unchanged", "ambiguous"]
    receipt_id: str = Field(pattern=r"^[0-9a-f]{16}$")
    verification_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class MutationCoordinator:
    """Issue and atomically consume receipts under one shared lock and SQLite store."""

    def __init__(
        self,
        paths: SecureRuntimePaths | None = None,
        *,
        receipt_ttl_seconds: float = MAX_RECEIPT_TTL_SECONDS,
        lock_timeout_seconds: float = 5.0,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if not MIN_RECEIPT_TTL_SECONDS <= receipt_ttl_seconds <= MAX_RECEIPT_TTL_SECONDS:
            raise ValueError("Receipt TTL must be between 1 and 300 seconds.")
        self.paths = paths or SecureRuntimePaths.create()
        self.receipt_ttl_seconds = receipt_ttl_seconds
        self.lock_timeout_seconds = lock_timeout_seconds
        self.clock = clock
        self._database_descriptors: dict[int, int] = {}
        self._key = self._load_or_create_key()
        self._initialize_store()

    def _lock(self) -> AdvisoryMutationLock:
        return AdvisoryMutationLock(self.paths.lock_file, timeout_seconds=self.lock_timeout_seconds)

    def _load_or_create_key(self) -> bytes:
        try:
            key = secure_read_bytes(self.paths.receipt_key, max_bytes=32)
        except FileNotFoundError:
            with suppress(FileExistsError):
                secure_write_bytes(self.paths.receipt_key, secrets.token_bytes(32), exclusive=True)
            key = secure_read_bytes(self.paths.receipt_key, max_bytes=32)
        if len(key) != 32:
            raise SecurityViolation("Receipt-store key has the wrong length.")
        return key

    def _prepare_db_path(self) -> None:
        if not self.paths.receipts_db.exists():
            secure_write_bytes(self.paths.receipts_db, b"", exclusive=True)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Load SQLite bytes into private memory without reopening a pathname.

        Python's sqlite3 API cannot adopt an already verified file descriptor.
        Passing the runtime pathname to ``sqlite3.connect`` would therefore
        reintroduce a symlink-swap window after our O_NOFOLLOW check.  The
        receipt store instead uses SQLite's serialize/deserialize API and only
        reads or writes through the shared descriptor-verified helpers.
        """
        self._prepare_db_path()
        with secure_file_descriptor(self.paths.receipts_db) as descriptor:
            payload = secure_read_from_descriptor(
                self.paths.receipts_db,
                descriptor,
                max_bytes=MAX_RECEIPT_STORE_BYTES,
            )
            connection = sqlite3.connect(":memory:", timeout=self.lock_timeout_seconds, isolation_level=None)
            self._database_descriptors[id(connection)] = descriptor
            try:
                connection.row_factory = sqlite3.Row
                connection.execute("PRAGMA journal_mode=MEMORY")
                connection.execute("PRAGMA synchronous=FULL")
                connection.execute("PRAGMA trusted_schema=OFF")
                if payload:
                    try:
                        connection.deserialize(payload)
                    except sqlite3.DatabaseError as exc:
                        raise SecurityViolation("Receipt store is not a valid SQLite database.") from exc
                    connection.execute("PRAGMA trusted_schema=OFF")
                yield connection
            finally:
                self._database_descriptors.pop(id(connection), None)
                connection.close()

    def _persist_database(self, db: sqlite3.Connection) -> None:
        """Persist a committed in-memory database through O_NOFOLLOW only."""
        if db.in_transaction:
            raise MutationStateError("Receipt-store persistence requires a committed transaction.")
        payload = db.serialize()
        if len(payload) > MAX_RECEIPT_STORE_BYTES:
            raise SecurityViolation("Receipt store exceeds its maximum allowed size.")
        descriptor = self._database_descriptors.get(id(db))
        if descriptor is None:
            raise MutationStateError("Receipt-store descriptor is not active.")
        secure_write_to_descriptor(self.paths.receipts_db, descriptor, payload)

    def _initialize_store(self) -> None:
        with self._lock(), self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS receipts (
                    receipt_hash TEXT PRIMARY KEY,
                    receipt_id TEXT NOT NULL UNIQUE,
                    binding_hash TEXT NOT NULL,
                    state_hash TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(
                        status IN ('issued','executing','consumed','abandoned','expired','ambiguous')
                    ),
                    issued_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    verification_hash TEXT
                ) STRICT
                """
            )
            self._persist_database(db)

    def _hmac(self, domain: bytes, payload: bytes) -> str:
        return hmac.new(self._key, domain + b"\0" + payload, hashlib.sha256).hexdigest()

    def _receipt_hash(self, receipt: str) -> str:
        return self._hmac(b"receipt", receipt.encode("ascii"))

    def _binding_hash(self, intent: MutationIntent) -> str:
        return self._hmac(b"binding", canonical_bytes(intent))

    def _state_hash(self, state: Any) -> str:
        return self._hmac(b"state", canonical_bytes(state))

    def _verification_hash(self, evidence: Any) -> str:
        return self._hmac(b"verification", canonical_bytes(evidence))

    @staticmethod
    def _receipt_id(receipt_hash: str) -> str:
        return receipt_hash[:16]

    def _expire_abandoned(self, db: sqlite3.Connection, now: float) -> None:
        db.execute(
            "UPDATE receipts SET status='expired', updated_at=? WHERE status='issued' AND expires_at<=?",
            (now, now),
        )
        db.execute(
            "UPDATE receipts SET status='ambiguous', updated_at=? WHERE status='executing' AND expires_at<=?",
            (now, now),
        )

    def preview(self, intent: MutationIntent, read_state: Callable[[], Any]) -> MutationPreview:
        """Reserve the global mutation lane after a fresh state read."""
        with self._lock(), self._connect() as db:
            now = self.clock()
            db.execute("BEGIN IMMEDIATE")
            try:
                self._expire_abandoned(db, now)
                active = db.execute(
                    "SELECT receipt_id FROM receipts WHERE status IN ('issued','executing') LIMIT 1"
                ).fetchone()
                if active is not None:
                    raise MutationBusyError("Another Things++ mutation reservation is active.")
                state = read_state()
                receipt = secrets.token_urlsafe(32)
                receipt_hash = self._receipt_hash(receipt)
                receipt_id = self._receipt_id(receipt_hash)
                expires_at = now + self.receipt_ttl_seconds
                db.execute(
                    "INSERT INTO receipts VALUES (?,?,?,?,?,?,?,?,NULL)",
                    (
                        receipt_hash,
                        receipt_id,
                        self._binding_hash(intent),
                        self._state_hash(state),
                        "issued",
                        now,
                        expires_at,
                        now,
                    ),
                )
                db.execute("COMMIT")
                self._persist_database(db)
            except BaseException:
                if db.in_transaction:
                    db.execute("ROLLBACK")
                raise
        return MutationPreview(
            mutation_receipt=receipt,
            receipt_id=receipt_id,
            expires_at=expires_at,
            target_count=_intent_target_count(intent),
        )

    async def apreview(self, intent: MutationIntent, read_state: Callable[[], Any]) -> MutationPreview:
        """Async equivalent of :meth:`preview` for MCP server callbacks."""
        lock = self._lock()
        await asyncio.to_thread(lock.acquire)
        try:
            with self._connect() as db:
                now = self.clock()
                db.execute("BEGIN IMMEDIATE")
                try:
                    self._expire_abandoned(db, now)
                    active = db.execute(
                        "SELECT receipt_id FROM receipts WHERE status IN ('issued','executing') LIMIT 1"
                    ).fetchone()
                    if active is not None:
                        raise MutationBusyError("Another Things++ mutation reservation is active.")
                    state = await read_state()
                    receipt = secrets.token_urlsafe(32)
                    receipt_hash = self._receipt_hash(receipt)
                    receipt_id = self._receipt_id(receipt_hash)
                    expires_at = now + self.receipt_ttl_seconds
                    db.execute(
                        "INSERT INTO receipts VALUES (?,?,?,?,?,?,?,?,NULL)",
                        (
                            receipt_hash,
                            receipt_id,
                            self._binding_hash(intent),
                            self._state_hash(state),
                            "issued",
                            now,
                            expires_at,
                            now,
                        ),
                    )
                    db.execute("COMMIT")
                    self._persist_database(db)
                except BaseException:
                    if db.in_transaction:
                        db.execute("ROLLBACK")
                    raise
        finally:
            lock.release()
        return MutationPreview(
            mutation_receipt=receipt,
            receipt_id=receipt_id,
            expires_at=expires_at,
            target_count=_intent_target_count(intent),
        )

    def execute(
        self,
        intent: MutationIntent,
        mutation_receipt: str,
        read_state: Callable[[], Any],
        mutate: Callable[[], Any],
        verify: Callable[[Any], Any],
    ) -> MutationExecution:
        """Consume exactly one matching receipt, mutate once, and verify before unlock."""
        receipt_hash = self._receipt_hash(mutation_receipt)
        receipt_id = self._receipt_id(receipt_hash)
        with self._lock(), self._connect() as db:
            now = self.clock()
            db.execute("BEGIN IMMEDIATE")
            try:
                self._expire_abandoned(db, now)
                row = db.execute("SELECT * FROM receipts WHERE receipt_hash=?", (receipt_hash,)).fetchone()
                if row is None or row["status"] != "issued":
                    raise MutationReceiptError("Receipt is unknown, expired, replayed, or not executable.")
                if row["expires_at"] <= now:
                    raise MutationReceiptError("Receipt has expired.")
                if not hmac.compare_digest(row["binding_hash"], self._binding_hash(intent)):
                    raise MutationReceiptError("Receipt binding does not match the execute request.")
                fresh_state = read_state()
                if not hmac.compare_digest(row["state_hash"], self._state_hash(fresh_state)):
                    raise MutationStateError("Target state changed after preview.")
                updated = db.execute(
                    "UPDATE receipts SET status='executing', updated_at=? WHERE receipt_hash=? AND status='issued'",
                    (now, receipt_hash),
                )
                if updated.rowcount != 1:
                    raise MutationReceiptError("Receipt was consumed concurrently.")
                db.execute("COMMIT")
                self._persist_database(db)
            except BaseException:
                if db.in_transaction:
                    db.execute("ROLLBACK")
                raise

            try:
                backend_result = mutate()
                verification = verify(backend_result)
                counts = _verification_counts(verification, _intent_target_count(intent))
                verification_hash = self._verification_hash(verification)
            except BaseException as exc:
                db.execute("BEGIN IMMEDIATE")
                db.execute(
                    "UPDATE receipts SET status='ambiguous', updated_at=? WHERE receipt_hash=? AND status='executing'",
                    (self.clock(), receipt_hash),
                )
                db.execute("COMMIT")
                self._persist_database(db)
                raise MutationAmbiguousError(
                    "Mutation execution did not produce conclusive verification; do not retry automatically."
                ) from exc

            db.execute("BEGIN IMMEDIATE")
            sealed = db.execute(
                "UPDATE receipts SET status='consumed', updated_at=?, verification_hash=? "
                "WHERE receipt_hash=? AND status='executing'",
                (self.clock(), verification_hash, receipt_hash),
            )
            db.execute("COMMIT")
            self._persist_database(db)
            if sealed.rowcount != 1:
                raise MutationAmbiguousError("Mutation receipt could not be sealed after verification.")
        return MutationExecution(receipt_id=receipt_id, verification_hash=verification_hash, **counts)

    async def aexecute(
        self,
        intent: MutationIntent,
        mutation_receipt: str,
        read_state: Callable[[], Any],
        mutate: Callable[[], Any],
        verify: Callable[[Any], Any],
    ) -> MutationExecution:
        """Async execute/readback critical section; backend execution is never replayed."""
        receipt_hash = self._receipt_hash(mutation_receipt)
        receipt_id = self._receipt_id(receipt_hash)
        lock = self._lock()
        await asyncio.to_thread(lock.acquire)
        try:
            with self._connect() as db:
                now = self.clock()
                db.execute("BEGIN IMMEDIATE")
                try:
                    self._expire_abandoned(db, now)
                    row = db.execute("SELECT * FROM receipts WHERE receipt_hash=?", (receipt_hash,)).fetchone()
                    if row is None or row["status"] != "issued":
                        raise MutationReceiptError("Receipt is unknown, expired, replayed, or not executable.")
                    if row["expires_at"] <= now:
                        raise MutationReceiptError("Receipt has expired.")
                    if not hmac.compare_digest(row["binding_hash"], self._binding_hash(intent)):
                        raise MutationReceiptError("Receipt binding does not match the execute request.")
                    fresh_state = await read_state()
                    if not hmac.compare_digest(row["state_hash"], self._state_hash(fresh_state)):
                        raise MutationStateError("Target state changed after preview.")
                    updated = db.execute(
                        "UPDATE receipts SET status='executing', updated_at=? WHERE receipt_hash=? AND status='issued'",
                        (now, receipt_hash),
                    )
                    if updated.rowcount != 1:
                        raise MutationReceiptError("Receipt was consumed concurrently.")
                    db.execute("COMMIT")
                    self._persist_database(db)
                except BaseException:
                    if db.in_transaction:
                        db.execute("ROLLBACK")
                    raise

                try:
                    backend_result = await mutate()
                    verification = await verify(backend_result)
                    counts = _verification_counts(verification, _intent_target_count(intent))
                    verification_hash = self._verification_hash(verification)
                except BaseException as exc:
                    db.execute("BEGIN IMMEDIATE")
                    db.execute(
                        "UPDATE receipts SET status='ambiguous', updated_at=? "
                        "WHERE receipt_hash=? AND status='executing'",
                        (self.clock(), receipt_hash),
                    )
                    db.execute("COMMIT")
                    self._persist_database(db)
                    raise MutationAmbiguousError(
                        "Mutation execution did not produce conclusive verification; do not retry automatically."
                    ) from exc

                db.execute("BEGIN IMMEDIATE")
                sealed = db.execute(
                    "UPDATE receipts SET status='consumed', updated_at=?, verification_hash=? "
                    "WHERE receipt_hash=? AND status='executing'",
                    (self.clock(), verification_hash, receipt_hash),
                )
                db.execute("COMMIT")
                self._persist_database(db)
                if sealed.rowcount != 1:
                    raise MutationAmbiguousError("Mutation receipt could not be sealed after verification.")
        finally:
            lock.release()
        return MutationExecution(receipt_id=receipt_id, verification_hash=verification_hash, **counts)

    def abandon(self, intent: MutationIntent, mutation_receipt: str) -> None:
        """Explicitly release one still-issued reservation."""
        receipt_hash = self._receipt_hash(mutation_receipt)
        with self._lock(), self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT binding_hash,status FROM receipts WHERE receipt_hash=?", (receipt_hash,)
            ).fetchone()
            if row is None or row["status"] != "issued":
                db.execute("ROLLBACK")
                raise MutationReceiptError("Only an issued receipt can be abandoned.")
            if not hmac.compare_digest(row["binding_hash"], self._binding_hash(intent)):
                db.execute("ROLLBACK")
                raise MutationReceiptError("Receipt binding does not match the abandon request.")
            db.execute(
                "UPDATE receipts SET status='abandoned', updated_at=? WHERE receipt_hash=?",
                (self.clock(), receipt_hash),
            )
            db.execute("COMMIT")
            self._persist_database(db)

    def recover(
        self,
        mutation_receipt: str,
        verify: Callable[[], tuple[Literal["changed", "unchanged", "ambiguous"], Any]],
    ) -> MutationRecovery:
        """Verify an ambiguous execution without replaying its backend action."""
        receipt_hash = self._receipt_hash(mutation_receipt)
        receipt_id = self._receipt_id(receipt_hash)
        with self._lock(), self._connect() as db:
            row = db.execute("SELECT status FROM receipts WHERE receipt_hash=?", (receipt_hash,)).fetchone()
            if row is None or row["status"] not in {"executing", "ambiguous"}:
                raise MutationReceiptError("Receipt does not name an ambiguous execution.")
            status, evidence = verify()
            verification_hash = self._verification_hash(evidence)
            new_status = "consumed" if status == "changed" else "ambiguous"
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "UPDATE receipts SET status=?,updated_at=?,verification_hash=? WHERE receipt_hash=?",
                (new_status, self.clock(), verification_hash, receipt_hash),
            )
            db.execute("COMMIT")
            self._persist_database(db)
        return MutationRecovery(status=status, receipt_id=receipt_id, verification_hash=verification_hash)

    def receipt_status(self, mutation_receipt: str) -> str | None:
        """Return a content-free receipt lifecycle state for tests and doctors."""
        with self._lock(), self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._expire_abandoned(db, self.clock())
            row = db.execute(
                "SELECT status FROM receipts WHERE receipt_hash=?", (self._receipt_hash(mutation_receipt),)
            ).fetchone()
            db.execute("COMMIT")
            self._persist_database(db)
            return None if row is None else str(row["status"])


def _intent_target_count(intent: MutationIntent) -> int:
    """Treat target-free create operations as one logical target."""
    return max(1, len(intent.target_ids))


def _verification_counts(verification: Any, target_count: int) -> dict[str, Any]:
    if not isinstance(verification, dict):
        raise MutationStateError("Verification evidence must contain explicit per-outcome counts.")
    counts: dict[str, int] = {}
    for key in ("changed", "skipped", "failed", "ambiguous"):
        value = verification.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 25:
            raise MutationStateError(f"Verification count {key} is missing or invalid.")
        counts[key] = value
    if target_count < 1 or target_count > 25 or sum(counts.values()) != target_count:
        raise MutationStateError("Verification counts do not reconcile to the mutation target count.")
    if counts["ambiguous"]:
        status = "ambiguous"
    elif counts["failed"] and not counts["changed"]:
        status = "failed"
    elif counts["changed"]:
        status = "changed"
    else:
        status = "skipped"
    return {"status": status, **counts}
