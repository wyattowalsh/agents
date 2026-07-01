"""Unit tests for validate collectors."""

from __future__ import annotations

from pathlib import Path

from scripts.validate.collectors.quarantine import collect_quarantine_errors

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_collect_quarantine_errors_returns_list() -> None:
    issues = collect_quarantine_errors(REPO_ROOT)
    assert isinstance(issues, list)
