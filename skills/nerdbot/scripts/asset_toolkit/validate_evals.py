#!/usr/bin/env python3
"""Validate skill eval JSON manifests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

_SCRIPT_ROOT = Path(__file__).resolve().parent.parent
if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))

from asset_toolkit.common import emit_validation_output, find_repo_root


def _is_eval_manifest(data: dict[str, object]) -> bool:
    return "evals" in data


def _validate_projection_files(path: Path, data: dict[str, object], add_error) -> None:
    """Validate opt-in per-case projections owned by a canonical manifest."""
    if "projection_files" not in data:
        return

    projection_files = data.get("projection_files")
    if not isinstance(projection_files, list) or not projection_files:
        add_error(path, "'projection_files' must be a non-empty list of JSON filenames")
        return

    declared: list[str] = []
    for item in projection_files:
        if not isinstance(item, str) or not item:
            add_error(path, "each 'projection_files' entry must be a non-empty string")
            continue
        candidate = Path(item)
        if candidate.name != item or candidate.suffix != ".json" or item == "evals.json":
            add_error(path, f"invalid projection filename: {item!r}")
            continue
        declared.append(item)

    if len(declared) != len(set(declared)):
        add_error(path, "'projection_files' contains duplicate filenames")

    evals = data.get("evals")
    if not isinstance(evals, list):
        return
    cases: dict[str, dict] = {}
    for index, item in enumerate(evals, start=1):
        if not isinstance(item, dict):
            continue
        case_id = item.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            add_error(path, f"eval {index} requires a non-empty string 'id' when projections are declared")
            continue
        expected_filename = f"{case_id}.json"
        if Path(expected_filename).name != expected_filename:
            add_error(path, f"eval {index} has a projection-unsafe id: {case_id!r}")
            continue
        if case_id in cases:
            add_error(path, f"eval {index} duplicates id {case_id!r}")
            continue
        assertions = item.get("assertions")
        if not isinstance(assertions, list) or not assertions:
            add_error(path, f"eval {index} requires a non-empty string list 'assertions' when projections are declared")
        elif any(not isinstance(assertion, str) or not assertion.strip() for assertion in assertions):
            add_error(path, f"eval {index} has an invalid 'assertions' entry")
        files = item.get("files", [])
        if not isinstance(files, list) or any(not isinstance(file, str) for file in files):
            add_error(path, f"eval {index} requires a string list 'files' when projections are declared")
        cases[case_id] = item

    expected = {f"{case_id}.json" for case_id in cases}
    declared_set = set(declared)
    if declared_set != expected:
        missing = sorted(expected - declared_set)
        extra = sorted(declared_set - expected)
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("unexpected " + ", ".join(extra))
        add_error(path, "projection declaration mismatch: " + "; ".join(details))

    actual = {candidate.name for candidate in path.parent.glob("*.json") if candidate.name != path.name}
    if actual != declared_set:
        missing = sorted(declared_set - actual)
        extra = sorted(actual - declared_set)
        details = []
        if missing:
            details.append("missing files " + ", ".join(missing))
        if extra:
            details.append("undeclared files " + ", ".join(extra))
        add_error(path, "projection file-set mismatch: " + "; ".join(details))

    skill_name = data.get("skill_name")
    for filename in sorted(expected & actual & declared_set):
        projection_path = path.parent / filename
        try:
            projection = json.loads(projection_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(projection, dict):
            add_error(projection_path, "top-level JSON value must be an object")
            continue
        case = cases[filename.removesuffix(".json")]
        parity = {
            "skills": [skill_name],
            "query": case.get("prompt"),
            "files": case.get("files", []),
            "expected_behavior": case.get("assertions", []),
        }
        unexpected_fields = sorted(set(projection) - set(parity))
        missing_fields = sorted(set(parity) - set(projection))
        if unexpected_fields:
            add_error(projection_path, "projection has unsupported fields: " + ", ".join(unexpected_fields))
        if missing_fields:
            add_error(projection_path, "projection is missing fields: " + ", ".join(missing_fields))
        for field, expected_value in parity.items():
            if projection.get(field) != expected_value:
                add_error(projection_path, f"projection field {field!r} does not match canonical manifest")


def collect_evals(skills_dir: Path) -> list[tuple[Path, object]]:
    results: list[tuple[Path, object]] = []
    if not skills_dir.is_dir():
        return results
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        evals_dir = skill_dir / "evals"
        if not evals_dir.is_dir():
            continue
        for eval_file in sorted(evals_dir.glob("*.json")):
            try:
                data = json.loads(eval_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = None
            results.append((eval_file, data))
    return results


def validate_evals(skills_dir: Path) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []

    def add_error(source: Path, message: str) -> None:
        errors.append({"source": str(source), "message": message})

    for path, data in collect_evals(skills_dir):
        if data is None:
            add_error(path, "invalid JSON")
            continue
        if not isinstance(data, dict):
            add_error(path, "top-level JSON value must be an object")
            continue
        record = cast("dict[str, object]", data)

        if _is_eval_manifest(record):
            skill_name = record.get("skill_name")
            if not isinstance(skill_name, str) or not skill_name.strip():
                add_error(path, "'skill_name' must be a non-empty string")
            elif not (skills_dir / skill_name).is_dir():
                add_error(path, f"skill '{skill_name}' does not match a skill directory")

            evals = record.get("evals")
            if not isinstance(evals, list) or len(evals) < 1:
                add_error(path, "'evals' must be a non-empty list")
                continue

            seen_prompts: dict[str, int] = {}
            for index, item in enumerate(evals, start=1):
                case_label = f"eval {index}"
                if not isinstance(item, dict):
                    add_error(path, f"{case_label} must be an object")
                    continue
                prompt = item.get("prompt")
                if not isinstance(prompt, str) or not prompt.strip():
                    add_error(path, f"{case_label} missing required non-empty string 'prompt'")
                else:
                    normalized_prompt = prompt.strip()
                    if normalized_prompt in seen_prompts:
                        add_error(
                            path,
                            f"{case_label} duplicates prompt from eval {seen_prompts[normalized_prompt]}: "
                            f"{normalized_prompt!r}",
                        )
                    else:
                        seen_prompts[normalized_prompt] = index
                expected_output = item.get("expected_output")
                if not isinstance(expected_output, str) or not expected_output.strip():
                    add_error(path, f"{case_label} missing required non-empty string 'expected_output'")
            _validate_projection_files(path, record, add_error)
            continue

        if "skills" not in record:
            add_error(path, "missing required field 'skills'")
        elif not isinstance(record["skills"], list) or len(record["skills"]) < 1:
            add_error(path, "'skills' must be a non-empty list of strings")
        else:
            for skill in record["skills"]:
                if not isinstance(skill, str):
                    add_error(path, "each entry in 'skills' must be a string")
                elif not (skills_dir / skill).is_dir():
                    add_error(path, f"skill '{skill}' does not match a skill directory")

        if "query" not in record:
            add_error(path, "missing required field 'query'")
        elif not isinstance(record["query"], str) or not record["query"].strip():
            add_error(path, "'query' must be a non-empty string")

        expected = record.get("expected_behavior")
        if expected is None:
            add_error(path, "missing required field 'expected_behavior'")
        elif not isinstance(expected, list) or len(expected) < 1:
            add_error(path, "'expected_behavior' must be a non-empty list of strings")
        else:
            for entry in expected:
                if not isinstance(entry, str):
                    add_error(path, "each entry in 'expected_behavior' must be a string")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate skill eval JSON files")
    parser.add_argument("path", nargs="?", default="", help="skills/ root or single skill dir")
    parser.add_argument("--repo-root", default="", help="Repository root to validate when path is omitted")
    parser.add_argument("--format", choices=["text", "json", "jsonl"], default="text")
    args = parser.parse_args(argv)

    if args.path:
        target = Path(args.path).resolve()
        if (target / "evals").is_dir() and (target / "SKILL.md").is_file():
            errors = validate_evals_for_skill(target)
        else:
            errors = validate_evals(target)
    else:
        repo_root = Path(args.repo_root).resolve() if args.repo_root else find_repo_root()
        if repo_root is None:
            print("Could not find repo skills/ directory", file=sys.stderr)
            return 1
        errors = validate_evals(repo_root / "skills")

    emit_validation_output(
        args.format,
        errors,
        ok_message="All evals valid",
        fail_message="Eval validation failed",
    )
    return 0 if not errors else 1


def validate_evals_for_skill(skill_dir: Path) -> list[dict[str, str]]:
    """Validate eval files for one skill directory only."""
    skills_root = skill_dir.parent
    all_errors = validate_evals(skills_root)
    prefix = str(skill_dir / "evals")
    return [error for error in all_errors if error["source"].startswith(prefix)]


if __name__ == "__main__":
    raise SystemExit(main())
