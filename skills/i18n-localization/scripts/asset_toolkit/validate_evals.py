#!/usr/bin/env python3
"""Validate skill eval JSON manifests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPT_ROOT = Path(__file__).resolve().parent.parent
if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))

from asset_toolkit.common import emit_validation_output, find_repo_root


def _is_eval_manifest(data: dict) -> bool:
    return "evals" in data


def collect_evals(skills_dir: Path) -> list[tuple[Path, dict]]:
    results: list[tuple[Path, dict]] = []
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
                data = {}
            results.append((eval_file, data))
    return results


def validate_evals(skills_dir: Path) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []

    def add_error(source: Path, message: str) -> None:
        errors.append({"source": str(source), "message": message})

    for path, data in collect_evals(skills_dir):
        if not data and path.stat().st_size > 2:
            add_error(path, "invalid JSON")
            continue

        if _is_eval_manifest(data):
            skill_name = data.get("skill_name")
            if not isinstance(skill_name, str) or not skill_name.strip():
                add_error(path, "'skill_name' must be a non-empty string")
            elif not (skills_dir / skill_name).is_dir():
                add_error(path, f"skill '{skill_name}' does not match a skill directory")

            evals = data.get("evals")
            if not isinstance(evals, list) or len(evals) < 1:
                add_error(path, "'evals' must be a non-empty list")
                continue

            for index, item in enumerate(evals, start=1):
                case_label = f"eval {index}"
                if not isinstance(item, dict):
                    add_error(path, f"{case_label} must be an object")
                    continue
                if not isinstance(item.get("prompt"), str) or not item["prompt"].strip():
                    add_error(path, f"{case_label} missing required non-empty string 'prompt'")
                if not isinstance(item.get("expected_output"), str) or not item["expected_output"].strip():
                    add_error(path, f"{case_label} missing required non-empty string 'expected_output'")
            continue

        if "skills" not in data:
            add_error(path, "missing required field 'skills'")
        elif not isinstance(data["skills"], list) or len(data["skills"]) < 1:
            add_error(path, "'skills' must be a non-empty list of strings")
        else:
            for skill in data["skills"]:
                if not isinstance(skill, str):
                    add_error(path, "each entry in 'skills' must be a string")
                elif not (skills_dir / skill).is_dir():
                    add_error(path, f"skill '{skill}' does not match a skill directory")

        if "query" not in data:
            add_error(path, "missing required field 'query'")
        elif not isinstance(data["query"], str) or not data["query"].strip():
            add_error(path, "'query' must be a non-empty string")

        expected = data.get("expected_behavior")
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
