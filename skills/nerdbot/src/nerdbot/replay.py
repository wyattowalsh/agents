"""Dry-run replay summaries for interrupted Nerdbot operations."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from nerdbot.operations import OperationEntry
from nerdbot.safety import normalize_vault_relative_path


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """Machine-readable replay result."""

    operation_id: str
    status: str
    changed: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()
    review_needed: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()
    resume_token: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Return the JSON-safe replay result."""
        return asdict(self)


def classify_replay_status(
    changed: tuple[str, ...],
    skipped: tuple[str, ...],
    review_needed: tuple[str, ...],
    failed: tuple[str, ...],
) -> str:
    """Classify a dry-run replay result from path buckets."""
    if failed:
        return "failed"
    if review_needed:
        return "review-needed"
    if skipped and not changed:
        return "skipped"
    return "verified"


def _resume_token(operation_id: str, status: str) -> str | None:
    return None if status == "verified" else f"resume:{operation_id}:{status}"


def dry_run_replay(operation_id: str, intended_paths: list[str], existing_paths: set[str]) -> ReplayResult:
    """Compare intended changes with existing paths without mutating files."""
    normalized_existing = {normalize_vault_relative_path(path) for path in existing_paths}
    changed: list[str] = []
    review_needed: list[str] = []
    failed: list[str] = []
    for path in intended_paths:
        try:
            normalized = normalize_vault_relative_path(path)
        except ValueError as exc:
            failed.append(f"{path}: {exc}")
            continue
        if normalized in normalized_existing:
            changed.append(normalized)
        else:
            review_needed.append(normalized)
    changed_tuple = tuple(changed)
    skipped_tuple: tuple[str, ...] = ()
    review_tuple = tuple(review_needed)
    failed_tuple = tuple(failed)
    status = classify_replay_status(changed_tuple, skipped_tuple, review_tuple, failed_tuple)
    return ReplayResult(
        operation_id=operation_id,
        status=status,
        changed=changed_tuple,
        skipped=skipped_tuple,
        review_needed=review_tuple,
        failed=failed_tuple,
        resume_token=_resume_token(operation_id, status),
    )


def load_operation_entries(journal_text: str) -> list[OperationEntry]:
    """Load operation entries from JSONL journal text."""
    entries: list[OperationEntry] = []
    for line in journal_text.splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        entries.append(OperationEntry(**payload))
    return entries


def dry_run_replay_entry(entry: OperationEntry, existing_paths: set[str]) -> ReplayResult:
    """Replay an operation entry by comparing its changed paths to existing paths."""
    return dry_run_replay(entry.operation_id, list(entry.changed_paths), existing_paths)
