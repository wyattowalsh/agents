"""Unit tests for cross-agent-install-smoke phase1 dry-run schema validation."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

DRY_RUN_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "cross-agent-install-smoke"
    / "scripts"
    / "dry_run.py"
)


def _load_dry_run():
    spec = importlib.util.spec_from_file_location("cross_agent_install_smoke_dry_run", DRY_RUN_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dry_run = _load_dry_run()


def _base_payload(agent_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "mode": "dry-run",
        "inventory_count": 1,
        "include_installed": False,
        "agents": [agent_row],
    }


def _legacy_agent() -> dict[str, Any]:
    return {
        "agent": "codex",
        "missing": ["alpha [repo-owned]"],
        "already_present": [],
        "unresolved": [],
        "skipped": ["beta [skipped]"],
    }


def _compact_bucket(count: int = 0, sample: list[str] | None = None, truncated: int = 0) -> dict[str, Any]:
    return {
        "count": count,
        "sample": list(sample or []),
        "truncated": truncated,
    }


def _compact_agent() -> dict[str, Any]:
    return {
        "agent": "cursor",
        "missing": _compact_bucket(2, ["a [repo-owned]", "b [repo-owned]"], 0),
        "already_present": _compact_bucket(),
        "projection_ensure": _compact_bucket(1, ["c [repo-owned]"], 0),
        "projection_blocked": _compact_bucket(),
        "store_missing": _compact_bucket(2, ["a [repo-owned]", "b [repo-owned]"], 0),
        "internal_projection": _compact_bucket(),
        "unresolved": _compact_bucket(),
        "skipped": _compact_bucket(1, ["d [skipped]"], 0),
        "pin_blocked": _compact_bucket(),
    }


def test_validate_payload_accepts_legacy_list_buckets() -> None:
    errors = dry_run.validate_payload(_base_payload(_legacy_agent()))
    assert errors == []


def test_validate_payload_accepts_compact_count_sample_buckets() -> None:
    errors = dry_run.validate_payload(_base_payload(_compact_agent()))
    assert errors == []


def test_validate_payload_rejects_invalid_compact_bucket() -> None:
    row = _compact_agent()
    row["missing"] = {"count": 1, "sample": "not-a-list", "truncated": 0}
    errors = dry_run.validate_payload(_base_payload(row))
    assert any("missing" in message and "sample" in message for message in errors)


def test_validate_payload_rejects_non_list_non_compact() -> None:
    row = _legacy_agent()
    row["already_present"] = "wrong"
    errors = dry_run.validate_payload(_base_payload(row))
    assert any("already_present" in message for message in errors)


def test_validate_payload_rejects_bad_optional_bucket_when_present() -> None:
    row = _compact_agent()
    row["projection_ensure"] = {"count": -1, "sample": [], "truncated": 0}
    errors = dry_run.validate_payload(_base_payload(row))
    assert any("projection_ensure" in message for message in errors)


@pytest.mark.parametrize(
    "mode",
    ["apply", "unknown"],
)
def test_validate_payload_requires_dry_run_mode(mode: str) -> None:
    payload = _base_payload(_legacy_agent())
    payload["mode"] = mode
    errors = dry_run.validate_payload(payload)
    assert any("dry-run" in message for message in errors)
