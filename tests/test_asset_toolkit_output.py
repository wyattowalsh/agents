"""Tests for asset_toolkit validation output formatting."""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "skill-creator" / "scripts"))

from asset_toolkit.common import emit_validation_output


@pytest.mark.parametrize(
    ("format_", "errors", "expected_lines"),
    [
        ("text", [], ["All validations passed"]),
        (
            "text",
            [{"source": "skills/foo/SKILL.md", "message": "missing name"}],
            ["skills/foo/SKILL.md: missing name"],
        ),
    ],
)
def test_emit_validation_output_text(format_: str, errors: list[dict[str, str]], expected_lines: list[str]) -> None:
    buffer = StringIO()
    sys.stdout = buffer
    try:
        emit_validation_output(format_, errors)
    finally:
        sys.stdout = sys.__stdout__
    assert buffer.getvalue().strip().splitlines() == expected_lines


def test_emit_validation_output_json() -> None:
    errors = [{"source": "agents/a.md", "message": "bad"}]
    buffer = StringIO()
    sys.stdout = buffer
    try:
        emit_validation_output("json", errors)
    finally:
        sys.stdout = sys.__stdout__
    payload = json.loads(buffer.getvalue())
    assert payload["ok"] is False
    assert payload["error_count"] == 1
    assert payload["errors"] == errors
    assert payload["message"] == "Validation failed"


def test_emit_validation_output_jsonl_contract() -> None:
    errors = [{"source": "skills/x/SKILL.md", "message": "empty body"}]
    buffer = StringIO()
    sys.stdout = buffer
    try:
        emit_validation_output("jsonl", errors)
    finally:
        sys.stdout = sys.__stdout__
    records = [json.loads(line) for line in buffer.getvalue().strip().splitlines()]
    assert records[0] == {"type": "error", **errors[0]}
    assert records[-1]["type"] == "summary"
    assert records[-1]["ok"] is False
    assert records[-1]["error_count"] == 1
    assert records[-1]["message"] == "Validation failed"
