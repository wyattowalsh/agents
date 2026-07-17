"""Crash-recoverable operation journal helpers for mutating workflows."""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from nerdbot.contracts import (
    ACTIVITY_LOG_PATH,
    MUTATING_MODES,
    OPERATION_JOURNAL_PATH,
    OPERATION_LOCK_PATH,
)
from nerdbot.safety import (
    append_text_no_follow,
    normalize_vault_relative_path,
    project_file_lock,
    read_text_no_follow,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence
    from pathlib import Path


OPERATION_MODES = frozenset({*MUTATING_MODES, "repair"})
OPERATION_STATES = frozenset({"planned", "prepared", "committed", "failed", "review-needed"})
JOURNAL_OPERATION_STATES = frozenset({"prepared", "committed", "failed", "review-needed"})
TERMINAL_OPERATION_STATES = frozenset({"committed", "failed", "review-needed"})
OPERATION_ID_RE = re.compile(r"^op-[a-f0-9]{8}-[a-f0-9]{12}$")
ACTIVITY_MARKER_RE = re.compile(r"^<!-- nerdbot-operation-id: (?P<operation_id>op-[a-f0-9]{8}-[a-f0-9]{12}) -->$")


def _validate_log_scalar(value: str, *, field: str, allow_empty: bool = False) -> str:
    """Reject scalar text that can break the line-oriented journal projection."""
    if not value and not allow_empty:
        raise ValueError(f"Operation field {field!r} must be non-empty")
    if "`" in value:
        raise ValueError(f"Operation field {field!r} must not contain backticks")
    if any(unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for character in value):
        raise ValueError(
            f"Operation field {field!r} must not contain line-breaking, control, format, or surrogate characters"
        )
    return value


def _validate_operation_id(operation_id: str) -> str:
    if not OPERATION_ID_RE.fullmatch(operation_id):
        raise ValueError("Operation field 'operation_id' must match op-<8 hex>-<12 hex>")
    return operation_id


def _validate_created_at(created_at: str) -> str:
    _validate_log_scalar(created_at, field="created_at")
    try:
        parsed = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Operation field 'created_at' must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("Operation field 'created_at' must include a timezone")
    return created_at


def _validate_path_tuple(field: str, values: tuple[str, ...]) -> None:
    for value in values:
        _validate_log_scalar(value, field=field)
        normalized = normalize_vault_relative_path(value)
        if normalized != value:
            raise ValueError(f"Operation field {field!r} must contain normalized POSIX vault paths")


@dataclass(frozen=True, slots=True)
class OperationEntry:
    """One state transition for a Nerdbot operation."""

    operation_id: str
    mode: str
    target: str
    status: str
    summary: str
    changed_paths: tuple[str, ...] = ()
    review_items: tuple[str, ...] = ()
    rollback_paths: tuple[str, ...] = ()
    created_at: str = ""

    def __post_init__(self) -> None:
        _validate_operation_id(self.operation_id)
        if self.mode not in OPERATION_MODES:
            raise ValueError(f"Unknown operation mode: {self.mode!r}")
        if self.status not in OPERATION_STATES:
            raise ValueError(f"Unknown operation status: {self.status!r}")
        _validate_log_scalar(self.target, field="target")
        _validate_log_scalar(self.summary, field="summary")
        _validate_created_at(self.created_at)
        _validate_path_tuple("changed_paths", self.changed_paths)
        _validate_path_tuple("review_items", self.review_items)
        _validate_path_tuple("rollback_paths", self.rollback_paths)

    def to_json_line(self) -> str:
        """Serialize as deterministic JSONL for append-only journals."""
        return json.dumps(asdict(self), sort_keys=True, ensure_ascii=False)

    def to_dict(self) -> dict[str, object]:
        """Return the JSON-safe operation payload."""
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> OperationEntry:
        """Load one strict operation transition while restoring tuple fields."""
        known_fields = {
            "operation_id",
            "mode",
            "target",
            "status",
            "summary",
            "changed_paths",
            "review_items",
            "rollback_paths",
            "created_at",
        }
        unknown_fields = set(payload) - known_fields
        if unknown_fields:
            raise ValueError(f"Unknown operation fields: {', '.join(sorted(unknown_fields))}")

        def required_text(field: str) -> str:
            value = payload.get(field)
            if not isinstance(value, str):
                raise ValueError(f"Operation field {field!r} must be a string")
            return value

        def path_tuple(field: str) -> tuple[str, ...]:
            value = payload.get(field)
            if not isinstance(value, (list, tuple)) or any(not isinstance(item, str) for item in value):
                raise ValueError(f"Operation field {field!r} must be a string array")
            return tuple(item for item in value if isinstance(item, str))

        return cls(
            operation_id=required_text("operation_id"),
            mode=required_text("mode"),
            target=required_text("target"),
            status=required_text("status"),
            summary=required_text("summary"),
            changed_paths=path_tuple("changed_paths"),
            review_items=path_tuple("review_items"),
            rollback_paths=path_tuple("rollback_paths"),
            created_at=required_text("created_at"),
        )


@dataclass(slots=True)
class OperationTransaction:
    """Mutable context result for one locked apply attempt."""

    prepared_entry: OperationEntry
    resumed: bool
    final_entry: OperationEntry | None = None
    apply_required: bool = True

    @property
    def entry(self) -> OperationEntry:
        """Return the terminal entry after exit, otherwise the prepared entry."""
        return self.final_entry or self.prepared_entry


def stable_operation_id(mode: str, target: str, summary: str, *, resume_key: str = "") -> str:
    """Build the deterministic correlation prefix for one operation intent."""
    return hashlib.sha256(f"{mode}\0{target}\0{summary}\0{resume_key}".encode()).hexdigest()[:8]


def build_operation_entry(
    *,
    mode: str,
    target: str,
    status: str,
    summary: str,
    changed_paths: tuple[str, ...] = (),
    review_items: tuple[str, ...] = (),
    rollback_paths: tuple[str, ...] = (),
    created_at: str | None = None,
    resume_key: str = "",
) -> OperationEntry:
    """Create a validated operation transition without writing it to disk."""
    operation_id = f"op-{stable_operation_id(mode, target, summary, resume_key=resume_key)}-{uuid.uuid4().hex[:12]}"
    return OperationEntry(
        operation_id=operation_id,
        mode=mode,
        target=target,
        status=status,
        summary=summary,
        changed_paths=tuple(normalize_vault_relative_path(path) for path in changed_paths),
        review_items=tuple(normalize_vault_relative_path(path) for path in review_items),
        rollback_paths=tuple(normalize_vault_relative_path(path) for path in rollback_paths),
        created_at=created_at or datetime.now(UTC).replace(microsecond=0).isoformat(),
    )


def transition_operation(entry: OperationEntry, status: str) -> OperationEntry:
    """Return the same immutable operation payload in a new lifecycle state."""
    return replace(entry, status=status)


def _immutable_payload(entry: OperationEntry) -> tuple[object, ...]:
    return (
        entry.operation_id,
        entry.mode,
        entry.target,
        entry.summary,
        entry.changed_paths,
        entry.review_items,
        entry.rollback_paths,
        entry.created_at,
    )


def _validate_journal_transition(
    latest_by_id: Mapping[str, OperationEntry], entry: OperationEntry, *, line_number: int
) -> None:
    if entry.status not in JOURNAL_OPERATION_STATES:
        raise ValueError(f"line {line_number}: journal status must be prepared or terminal, got {entry.status!r}")
    previous = latest_by_id.get(entry.operation_id)
    if previous is None:
        if entry.status != "prepared":
            raise ValueError(f"line {line_number}: first state for {entry.operation_id} must be 'prepared'")
        return
    if _immutable_payload(previous) != _immutable_payload(entry):
        raise ValueError(f"line {line_number}: operation {entry.operation_id} changed immutable payload")
    if previous.status != "prepared":
        raise ValueError(f"line {line_number}: operation {entry.operation_id} already ended as {previous.status!r}")
    if entry.status not in TERMINAL_OPERATION_STATES:
        raise ValueError(f"line {line_number}: duplicate prepared state for {entry.operation_id}")


def load_operation_entries(journal_text: str) -> list[OperationEntry]:
    """Parse and validate every transition in canonical JSONL journal text."""
    entries: list[OperationEntry] = []
    latest_by_id: dict[str, OperationEntry] = {}
    for line_number, line in enumerate(journal_text.split("\n"), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_number}: invalid operation JSON: {exc.msg}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"line {line_number}: operation journal lines must contain JSON objects")
        try:
            entry = OperationEntry.from_dict(payload)
        except ValueError as exc:
            raise ValueError(f"line {line_number}: {exc}") from exc
        _validate_journal_transition(latest_by_id, entry, line_number=line_number)
        entries.append(entry)
        latest_by_id[entry.operation_id] = entry
    return entries


def latest_operation_entries(entries: Sequence[OperationEntry]) -> list[OperationEntry]:
    """Collapse validated transitions to one latest state per operation."""
    latest: dict[str, OperationEntry] = {}
    order: list[str] = []
    for entry in entries:
        if entry.operation_id not in latest:
            order.append(entry.operation_id)
        latest[entry.operation_id] = entry
    return [latest[operation_id] for operation_id in order]


def append_operation_entry(journal_path: Path, entry: OperationEntry) -> None:
    """Append one already-validated operation transition to a JSONL journal."""
    append_text_no_follow(journal_path, f"{entry.to_json_line()}\n")


def render_activity_log_entry(entry: OperationEntry) -> str:
    """Render one unambiguous human projection for a committed operation."""
    if entry.status != "committed":
        raise ValueError("Only committed operations may be projected to the activity log")
    changed = ", ".join(entry.changed_paths) if entry.changed_paths else "none"
    review = ", ".join(entry.review_items) if entry.review_items else "none"
    rollback = ", ".join(entry.rollback_paths) if entry.rollback_paths else OPERATION_JOURNAL_PATH
    return (
        f"\n## {entry.created_at} - {entry.mode} - {entry.status}\n\n"
        f"- Target: {entry.target}\n"
        f"- Summary: {entry.summary}\n"
        f"- Changed paths: {changed}\n"
        f"- Review items: {review}\n"
        f"- Rollback/reference: {rollback}\n"
        f"<!-- nerdbot-operation-id: {entry.operation_id} -->\n"
    )


def append_activity_log_entry(root: Path, entry: OperationEntry) -> None:
    """Append the human projection for one committed operation."""
    append_text_no_follow(root / ACTIVITY_LOG_PATH, render_activity_log_entry(entry))


def _load_operation_entries(journal_path: Path) -> list[OperationEntry]:
    if not os.path.lexists(journal_path):
        return []
    try:
        return load_operation_entries(read_text_no_follow(journal_path))
    except ValueError as exc:
        raise RuntimeError(f"Invalid canonical operation journal: {exc}") from exc


def _activity_operation_ids(activity_text: str) -> set[str]:
    """Extract exact structured projection markers, never arbitrary prose."""
    return {
        match.group("operation_id")
        for raw_line in activity_text.split("\n")
        if (match := ACTIVITY_MARKER_RE.fullmatch(raw_line.removesuffix("\r"))) is not None
    }


def _repair_activity_log_projections_locked(root: Path, entries: Sequence[OperationEntry]) -> tuple[str, ...]:
    """Repair committed projections while the caller owns the project lock."""
    activity_path = root / ACTIVITY_LOG_PATH
    activity_text = read_text_no_follow(activity_path) if os.path.lexists(activity_path) else ""
    projected_ids = _activity_operation_ids(activity_text)
    repaired: list[str] = []
    for entry in latest_operation_entries(entries):
        if entry.status != "committed" or entry.operation_id in projected_ids:
            continue
        append_activity_log_entry(root, entry)
        projected_ids.add(entry.operation_id)
        repaired.append(entry.operation_id)
    return tuple(repaired)


def _append_operation_state_locked(root: Path, entries: list[OperationEntry], entry: OperationEntry) -> None:
    """Validate and append one state while the caller owns the project lock."""
    latest = {item.operation_id: item for item in latest_operation_entries(entries)}
    _validate_journal_transition(latest, entry, line_number=len(entries) + 1)
    append_operation_entry(root / OPERATION_JOURNAL_PATH, entry)
    entries.append(entry)


def repair_activity_log_projections(root: Path, *, lock_timeout: float = 10.0) -> tuple[str, ...]:
    """Idempotently project committed operations missing from the human log."""
    with project_file_lock(root / OPERATION_LOCK_PATH, timeout=lock_timeout):
        entries = _load_operation_entries(root / OPERATION_JOURNAL_PATH)
        return _repair_activity_log_projections_locked(root, entries)


@contextmanager
def operation_apply_transaction(
    root: Path,
    *,
    mode: str,
    target: str,
    summary: str,
    changed_paths: Sequence[str],
    resume_key: str,
    lock_timeout: float = 10.0,
) -> Iterator[OperationTransaction]:
    """Hold the project lock across prepare, mutation, and terminal commit."""
    intent_prefix = f"op-{stable_operation_id(mode, target, summary, resume_key=resume_key)}-"
    with project_file_lock(root / OPERATION_LOCK_PATH, timeout=lock_timeout):
        entries = _load_operation_entries(root / OPERATION_JOURNAL_PATH)
        repaired_ids = _repair_activity_log_projections_locked(root, entries)
        latest_entries = latest_operation_entries(entries)
        latest_entry = latest_entries[-1] if latest_entries else None
        if (
            latest_entry is not None
            and latest_entry.status == "committed"
            and latest_entry.operation_id in repaired_ids
            and latest_entry.operation_id.startswith(intent_prefix)
            and latest_entry.mode == mode
            and latest_entry.target == target
            and latest_entry.summary == summary
        ):
            # A crash after the durable commit but before its human projection is
            # recoverable without creating a second operation for the same retry.
            transaction = OperationTransaction(
                prepared_entry=transition_operation(latest_entry, "prepared"),
                resumed=True,
                final_entry=latest_entry,
                apply_required=False,
            )
            yield transaction
            return
        resumable = [
            entry
            for entry in latest_entries
            if entry.status == "prepared"
            and entry.operation_id.startswith(intent_prefix)
            and entry.mode == mode
            and entry.target == target
            and entry.summary == summary
        ]
        if len(resumable) > 1:
            operation_ids = ", ".join(entry.operation_id for entry in resumable)
            raise RuntimeError(f"Multiple prepared operations match this intent: {operation_ids}")
        if resumable:
            prepared = resumable[0]
            transaction = OperationTransaction(prepared_entry=prepared, resumed=True)
        else:
            prepared = build_operation_entry(
                mode=mode,
                target=target,
                status="prepared",
                summary=summary,
                changed_paths=tuple(changed_paths),
                resume_key=resume_key,
            )
            _append_operation_state_locked(root, entries, prepared)
            transaction = OperationTransaction(prepared_entry=prepared, resumed=False)
        try:
            yield transaction
        except Exception:
            failed = transition_operation(prepared, "failed")
            _append_operation_state_locked(root, entries, failed)
            transaction.final_entry = failed
            raise
        else:
            committed = transition_operation(prepared, "committed")
            _append_operation_state_locked(root, entries, committed)
            transaction.final_entry = committed
            append_activity_log_entry(root, committed)


def record_operation(root: Path, entry: OperationEntry, *, lock_timeout: float = 10.0) -> None:
    """Idempotently record one prebuilt committed operation and its projection."""
    if entry.status != "committed":
        raise ValueError("record_operation requires a committed OperationEntry")
    prepared = transition_operation(entry, "prepared")
    with project_file_lock(root / OPERATION_LOCK_PATH, timeout=lock_timeout):
        entries = _load_operation_entries(root / OPERATION_JOURNAL_PATH)
        _repair_activity_log_projections_locked(root, entries)
        existing = next(
            (item for item in latest_operation_entries(entries) if item.operation_id == entry.operation_id), None
        )
        if existing is not None:
            if existing == entry:
                return
            if existing != prepared:
                raise RuntimeError(f"Operation ID has conflicting payload or terminal state: {entry.operation_id}")
        else:
            _append_operation_state_locked(root, entries, prepared)
        _append_operation_state_locked(root, entries, entry)
        append_activity_log_entry(root, entry)
