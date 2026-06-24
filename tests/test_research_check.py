"""Tests for research skill validation helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK_PATH = ROOT / "skills" / "research" / "scripts" / "check.py"


def _load_check_module():
    spec = importlib.util.spec_from_file_location("research_check_for_tests", CHECK_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_yaml(skill_dir: Path, content: str) -> None:
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir(parents=True)
    (evals_dir / "test-cases.yaml").write_text(content, encoding="utf-8")


def test_validate_yaml_test_cases_accepts_valid_fixture(tmp_path):
    check = _load_check_module()
    skill_dir = tmp_path / "research"
    _write_yaml(
        skill_dir,
        """
test_cases:
  - id: eval-001
    description: Valid case
    input: /research check example claim
    expected_tier: standard
    expected_mode: factcheck
    expected_output_contains:
      - source-support audit
    validation_rules:
      - classify support status
""",
    )

    assert check.validate_yaml_test_cases(skill_dir) == []


def test_validate_yaml_test_cases_rejects_duplicate_ids(tmp_path):
    check = _load_check_module()
    skill_dir = tmp_path / "research"
    _write_yaml(
        skill_dir,
        """
test_cases:
  - id: eval-001
    description: First
    input: /research first
    expected_tier: standard
  - id: eval-001
    description: Second
    input: /research second
    expected_tier: standard
""",
    )

    errors = check.validate_yaml_test_cases(skill_dir)
    assert any("duplicates id 'eval-001'" in error for error in errors)


def test_validate_yaml_test_cases_rejects_missing_required_fields(tmp_path):
    check = _load_check_module()
    skill_dir = tmp_path / "research"
    _write_yaml(
        skill_dir,
        """
test_cases:
  - id: ""
    description: ""
    input: ""
    expected_output_contains: []
""",
    )

    errors = check.validate_yaml_test_cases(skill_dir)
    assert any("missing non-empty string 'id'" in error for error in errors)
    assert any("missing non-empty string 'description'" in error for error in errors)
    assert any("missing non-empty string 'input'" in error for error in errors)
    assert any("must include at least one expected or validation field" in error for error in errors)
    assert any("field 'expected_output_contains' must be a non-empty list of strings" in error for error in errors)
