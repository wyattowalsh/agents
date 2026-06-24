#!/usr/bin/env python3
"""Validate this skill's SKILL.md and eval manifests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

SKILL_DIR = Path(__file__).resolve().parent.parent

_REQUIRED_STRING_FIELDS = ("id", "description", "input")
_EXPECTED_OR_VALIDATION_PREFIXES = ("expected_", "validation_")


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_expected_or_validation_field(case: dict[str, Any]) -> bool:
    for key, value in case.items():
        if any(key.startswith(prefix) for prefix in _EXPECTED_OR_VALIDATION_PREFIXES):
            if key == "expected_output_contains":
                if isinstance(value, list) and any(isinstance(item, str) and item.strip() for item in value):
                    return True
                continue
            if _non_empty_string(value):
                return True
            if isinstance(value, list) and value:
                return True
    return False


def validate_yaml_test_cases(skill_dir: Path) -> list[str]:
    """Validate evals/test-cases.yaml structure for the research skill."""
    path = skill_dir / "evals" / "test-cases.yaml"
    if not path.is_file():
        return []

    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"evals/test-cases.yaml: invalid YAML ({exc})"]

    if not isinstance(payload, dict):
        return ["evals/test-cases.yaml: root must be a mapping"]

    cases = payload.get("test_cases")
    if cases is None:
        return ["evals/test-cases.yaml: missing 'test_cases' list"]
    if not isinstance(cases, list):
        return ["evals/test-cases.yaml: 'test_cases' must be a list"]

    errors: list[str] = []
    seen_ids: dict[str, int] = {}

    for index, case in enumerate(cases, start=1):
        label = f"evals/test-cases.yaml test_cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{label}: must be a mapping")
            continue

        for field in _REQUIRED_STRING_FIELDS:
            value = case.get(field)
            if not _non_empty_string(value):
                errors.append(f"{label}: missing non-empty string '{field}'")

        case_id = case.get("id")
        if _non_empty_string(case_id):
            seen_ids[str(case_id)] = seen_ids.get(str(case_id), 0) + 1

        if not _has_expected_or_validation_field(case):
            errors.append(f"{label}: must include at least one expected or validation field")

        contains = case.get("expected_output_contains")
        if contains is not None:
            if not isinstance(contains, list) or not any(
                isinstance(item, str) and item.strip() for item in contains
            ):
                errors.append(f"{label}: field 'expected_output_contains' must be a non-empty list of strings")

    for case_id, count in sorted(seen_ids.items()):
        if count > 1:
            errors.append(f"evals/test-cases.yaml duplicates id '{case_id}'")

    return errors


def _toolkit_path() -> Path:
    bundled = SKILL_DIR / "scripts" / "asset_toolkit" / "validate_skill.py"
    if bundled.is_file():
        return SKILL_DIR / "scripts" / "asset_toolkit"
    return SKILL_DIR.parent / "skill-creator" / "scripts" / "asset_toolkit"


def _run(command: list[str]) -> int:
    return subprocess.run(command, check=False).returncode


def main() -> int:
    yaml_errors = validate_yaml_test_cases(SKILL_DIR)
    if yaml_errors:
        for error in yaml_errors:
            print(error, file=sys.stderr)
        return 1

    toolkit = _toolkit_path()
    commands: list[list[str]] = [
        [sys.executable, str(toolkit / "validate_skill.py"), str(SKILL_DIR)],
    ]
    if (SKILL_DIR / "evals").is_dir():
        commands.append([sys.executable, str(toolkit / "validate_evals.py"), str(SKILL_DIR)])

    package_script = SKILL_DIR / "scripts" / "package.py"
    if not package_script.is_file():
        package_script = SKILL_DIR.parent / "skill-creator" / "scripts" / "package.py"
    if package_script.is_file():
        commands.append([sys.executable, str(package_script), str(SKILL_DIR), "--dry-run"])

    audit_script = SKILL_DIR.parent / "skill-creator" / "scripts" / "audit.py"
    if audit_script.is_file():
        commands.append([sys.executable, str(audit_script), str(SKILL_DIR)])

    exit_code = 0
    for command in commands:
        exit_code = _run(command) or exit_code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
