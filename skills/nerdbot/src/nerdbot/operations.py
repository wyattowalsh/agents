"""Operation journal helpers for replayable mutating workflows."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from nerdbot.safety import append_text_no_follow, normalize_vault_relative_path


@dataclass(frozen=True, slots=True)
class OperationEntry:
    """Append-friendly record of a Nerdbot operation."""

    operation_id: str
    mode: str
    target: str
    status: str
    summary: str
    changed_paths: tuple[str, ...] = ()
    review_items: tuple[str, ...] = ()
    rollback_paths: tuple[str, ...] = ()
    created_at: str = ""

    def to_json_line(self) -> str:
        """Serialize as deterministic JSONL for append-only journals."""
        payload = asdict(self)
        return json.dumps(payload, sort_keys=True, ensure_ascii=False)

    def to_dict(self) -> dict[str, object]:
        """Return the JSON-safe operation payload."""
        return asdict(self)


def stable_operation_id(mode: str, target: str, summary: str) -> str:
    """Build a correlation ID prefix from operation intent."""
    return hashlib.sha256(f"{mode}\0{target}\0{summary}".encode()).hexdigest()[:8]


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
) -> OperationEntry:
    """Create an operation entry without writing it to disk."""
    operation_id = f"op-{stable_operation_id(mode, target, summary)}-{uuid.uuid4().hex[:12]}"
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


def append_operation_entry(journal_path: Path, entry: OperationEntry) -> None:
    """Append an operation entry to an append-only JSONL journal."""
    append_text_no_follow(journal_path, f"{entry.to_json_line()}\n")
