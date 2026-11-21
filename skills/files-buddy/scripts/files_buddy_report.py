"""Validate and normalize Files Buddy report snapshots without inventing evidence."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from datetime import UTC, datetime
from typing import Any, cast

SCHEMA_VERSION = "2.0"
MAX_REPORT_BYTES = 16 * 1024 * 1024
MAX_ROWS = 100_000
MAX_SAFE_INTEGER = 2**53 - 1
STATUSES = frozenset(
    {"unknown", "running", "waiting-for-approval", "executing", "completed", "partial", "failed", "cancelled"}
)
COVERAGE_STATUSES = frozenset({"unknown", "complete", "partial", "unavailable"})
RISKS = frozenset({"unknown", "low", "medium", "high", "critical"})
COLLECTIONS = (
    "files",
    "directories",
    "duplicates",
    "recommendations",
    "categories",
    "events",
    "operations",
    "cloud",
    "caches",
)
SAVINGS_FIELDS = (
    "logical_bytes",
    "allocated_bytes",
    "eligible_bytes",
    "candidate_bytes",
    "selected_bytes",
    "acted_bytes",
    "quarantined_bytes",
    "trash_retained_bytes",
    "verified_reclaimed_bytes",
    "observed_free_space_delta_bytes",
    "cloud_bytes_affected",
    "legacy_verified_local_bytes",
)
LEGACY_SAVINGS = {
    "discovered_bytes": "logical_bytes",
    "eligible_bytes": "eligible_bytes",
    "recommended_local_bytes": "candidate_bytes",
    "approved_local_bytes": "selected_bytes",
    "completed_local_bytes": "acted_bytes",
    # The published 1.1 meaning includes moves. It cannot prove reclaimed space.
    "verified_local_bytes": "legacy_verified_local_bytes",
}
BYTE_KEYS = frozenset({"bytes", "size", "size_bytes", "file_len", "reclaimable", "local_bytes", "local_bytes_saved"})


class ReportError(ValueError):
    """Input does not satisfy the supported report contract."""


def _object(value: object, path: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ReportError(f"{path} must be a JSON object")
    return cast("dict[str, Any]", value)


def _text(value: object, path: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        raise ReportError(f"{path} must be a string{' or null' if nullable else ''}")
    return value


def _integer(value: object, path: str, *, signed: bool = False, nullable: bool = True) -> int | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReportError(f"{path} must be an integer{' or null' if nullable else ''}")
    if (not signed and value < 0) or abs(value) > MAX_SAFE_INTEGER:
        raise ReportError(f"{path} is outside the supported integer range")
    return value


def _timestamp(value: object, path: str, *, nullable: bool = True) -> str | None:
    text = _text(value, path, nullable=nullable)
    if text is None:
        return None
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", text):
        raise ReportError(f"{path} must use RFC 3339 date/time with a timezone")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReportError(f"{path} must be an ISO 8601 timestamp") from exc
    if parsed.utcoffset() is None:
        raise ReportError(f"{path} must include a timezone")
    return text


def _string_list(value: object, path: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ReportError(f"{path} must be an array of strings")
    return cast("list[str]", value)


def canonical_digest(data: object) -> str:
    """Return an algorithm-labelled digest of JSON content, not authorization."""
    try:
        encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    except (TypeError, ValueError, RecursionError) as exc:
        raise ReportError("Report must contain finite JSON values") from exc
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def load_report(raw: str) -> dict[str, Any]:
    """Parse bounded JSON, reject ambiguous duplicate keys, and normalize it."""
    if len(raw.encode("utf-8")) > MAX_REPORT_BYTES:
        raise ReportError(f"Report exceeds {MAX_REPORT_BYTES} bytes; export a capped summary")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ReportError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        data = json.loads(raw, object_pairs_hook=unique_object)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ReportError(f"Invalid JSON: {exc}") from exc
    return normalize_report(data)


def new_report(mode: str, scope: str | list[str]) -> dict[str, Any]:
    """Create a v2 producer envelope; unknown evidence remains unknown."""
    return normalize_report(
        {
            "schema_version": SCHEMA_VERSION,
            "run_id": uuid.uuid4().hex,
            "mode": mode,
            "updated_at": datetime.now(UTC).isoformat(),
            "status": "running",
            "scope": [scope] if isinstance(scope, str) else scope,
            "coverage": {"status": "unknown", "omissions": []},
            "counts": {},
            "savings": {},
        }
    )


def _validate_row(row: dict[str, Any], path: str) -> None:
    for key, value in row.items():
        if key in BYTE_KEYS or key.endswith("_bytes"):
            _integer(value, f"{path}.{key}", signed=key == "observed_free_space_delta_bytes")
        elif key in {"path", "name", "action", "restore_path", "repercussion", "message", "level", "time"}:
            _text(value, f"{path}.{key}", nullable=True)
        elif key in {"risk", "approval_tier"}:
            if value is not None and (not isinstance(value, str) or value.lower() not in RISKS):
                raise ReportError(f"{path}.{key} must be a known risk or null")
        elif key in {"paths", "dependency_evidence", "repercussions"}:
            if isinstance(value, str) and key == "repercussions":
                continue  # Published v1.1 also permits a single prose repercussion.
            _string_list(value, f"{path}.{key}")


def normalize_report(data: object) -> dict[str, Any]:
    """Normalize published legacy/v1.1 and v2 reports to one validated v2 shape.

    Structure and accounting labels are checked, not the truth of observations,
    risk assessments, authorization, or claimed savings.
    """
    source = _object(data, "report")
    digest = canonical_digest(source)
    report = copy.deepcopy(source)
    version = report.get("schema_version")
    if version not in (None, "1.1", SCHEMA_VERSION):
        raise ReportError(f"Unsupported report schema_version: {version!r}")
    legacy = version != SCHEMA_VERSION
    if not legacy:
        required = {"run_id", "updated_at", "status", "scope", "coverage", "counts", "savings"}
        missing = required - report.keys()
        if missing:
            raise ReportError(f"Missing v2 report fields: {', '.join(sorted(missing))}")
    report["schema_version"] = SCHEMA_VERSION
    report.setdefault("run_id", f"import-{digest[7:23]}")
    run_id = _text(report["run_id"], "run_id")
    if not run_id or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", run_id):
        raise ReportError("run_id must start with a letter or number and contain 1-128 safe identifier characters")
    report.setdefault("updated_at", report.get("generated"))
    _timestamp(report["updated_at"], "updated_at")
    if "started_at" in report:
        _timestamp(report["started_at"], "started_at")
    report.setdefault("mode", "report")
    _text(report["mode"], "mode")
    report.setdefault("status", "unknown")
    if not isinstance(report["status"], str) or report["status"] not in STATUSES:
        raise ReportError("status is not a supported run state")
    report.setdefault("scope", [])
    if legacy and isinstance(report["scope"], str):
        report["scope"] = [report["scope"]]
    _string_list(report["scope"], "scope")
    coverage = _object(report.setdefault("coverage", {}), "coverage")
    coverage.setdefault("status", "unknown")
    coverage.setdefault("omissions", [])
    if not isinstance(coverage["status"], str) or coverage["status"] not in COVERAGE_STATUSES:
        raise ReportError("coverage.status is not supported")
    _string_list(coverage["omissions"], "coverage.omissions")
    counts = _object(report.setdefault("counts", {}), "counts")
    for key, value in counts.items():
        _integer(value, f"counts.{key}", nullable=False)
    savings = _object(report.setdefault("savings", {}), "savings")
    for key, value in list(savings.items()):
        if key not in SAVINGS_FIELDS and (not legacy or key not in LEGACY_SAVINGS):
            raise ReportError(f"Unknown savings metric: {key}")
        _integer(value, f"savings.{key}", signed=key == "observed_free_space_delta_bytes")
    if legacy:
        for old_key, new_key in LEGACY_SAVINGS.items():
            if old_key in savings:
                savings.setdefault(new_key, savings.pop(old_key))
    for key in SAVINGS_FIELDS:
        savings.setdefault(key, None)
    for old_key, new_key in {"treemap": "directories", "duplicate_clusters": "duplicates"}.items():
        if legacy and old_key in report and new_key not in report:
            report[new_key] = report.pop(old_key)
    for key in COLLECTIONS:
        rows = report.setdefault(key, [])
        if not isinstance(rows, list) or len(rows) > MAX_ROWS:
            raise ReportError(f"{key} must be an array with at most {MAX_ROWS} rows")
        for index, item in enumerate(rows):
            row = _object(item, f"{key}[{index}]")
            _validate_row(row, f"{key}[{index}]")
            if key in {"recommendations", "categories", "duplicates", "cloud", "caches"}:
                risk = row.get("risk") or row.get("approval_tier")
                row["risk"] = risk.lower() if isinstance(risk, str) else "unknown"
            if key in {"recommendations", "cloud"}:
                if legacy and "local_bytes" not in row:
                    row["local_bytes"] = row.get("local_bytes_saved", row.get("bytes"))
                row.setdefault("local_bytes", None)
                row.setdefault("cloud_bytes", None)
                row.setdefault("restore_path", None)
            if key == "duplicates":
                row.setdefault("kind", "unknown")
                if not isinstance(row["kind"], str) or row["kind"] not in {"unknown", "exact", "similar"}:
                    raise ReportError(f"{key}[{index}].kind must be exact, similar, or unknown")
    if "summary" in report:
        _object(report["summary"], "summary")
    if "phase" in report:
        phase = _object(report["phase"], "phase")
        for key in ("index", "total"):
            if key in phase:
                _integer(phase[key], f"phase.{key}", nullable=False)
        for key in ("name", "message"):
            if key in phase:
                _text(phase[key], f"phase.{key}")
    manifest = report.setdefault("manifest", None)
    if manifest is not None:
        if isinstance(manifest, str):
            report["manifest"] = {"path": manifest}
        else:
            _object(manifest, "manifest")
            _text(manifest.get("path"), "manifest.path", nullable=True)
    warnings = report.setdefault("normalization_warnings", [])
    _string_list(warnings, "normalization_warnings")
    if legacy:
        warnings.append("Imported legacy report; missing coverage, risk and recovery evidence remain unknown.")
        if savings["legacy_verified_local_bytes"] is not None:
            warnings.append("Legacy verified_local_bytes included moves; it does not establish reclaimed space.")
    if "source_digest" in report and (
        not isinstance(report["source_digest"], str)
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", report["source_digest"])
    ):
        raise ReportError("source_digest must be an algorithm-labelled SHA-256 digest")
    report["source_digest"] = canonical_digest({key: value for key, value in report.items() if key != "source_digest"})
    return report
