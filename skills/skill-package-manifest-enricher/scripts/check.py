#!/usr/bin/env python3
"""Portable validator for skill-package-manifest-enricher."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent


def _toolkit_path() -> Path:
    bundled = SKILL_DIR / "scripts" / "asset_toolkit" / "validate_skill.py"
    if bundled.is_file():
        return SKILL_DIR / "scripts" / "asset_toolkit"
    return SKILL_DIR.parent / "skill-creator" / "scripts" / "asset_toolkit"


def _run(command: list[str]) -> int:
    return subprocess.run(command, check=False).returncode


def _portable_smoke() -> int:
    """Exercise real YAML semantics and non-mutating preview in an isolated tree."""
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        target = root / "sample-skill"
        target.mkdir()
        target.joinpath("SKILL.md").write_text(
            """---
name: sample-skill
description: >-
  Folded
  description.
compatibility: "Python: 3.11+"
tags:
  - portable
metadata:
  nested: true
---
# Sample
""",
            encoding="utf-8",
        )
        catalog = root / "catalog.json"
        catalog.write_text(
            json.dumps({
                "customSkillIndex": [
                    {"name": "sample-skill", "targetAgents": ["codex", "cursor"]},
                ]
            }),
            encoding="utf-8",
        )
        command = [
            sys.executable,
            str(SKILL_DIR / "scripts" / "enrich_manifest.py"),
            "--skill-dir",
            str(target),
            "--catalog-metadata",
            str(catalog),
            "--dry-run",
        ]
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.returncode:
            print(completed.stdout, file=sys.stderr)
            print(completed.stderr, file=sys.stderr)
            return completed.returncode
        try:
            payload: dict[str, Any] = json.loads(completed.stdout)
            manifest = payload["manifest"]
            passed = (
                manifest["description"] == "Folded description."
                and manifest["compatibility_notes"] == "Python: 3.11+"
                and manifest["harness_targets"] == ["codex", "cursor"]
                and manifest["harness_targets_status"] == "catalog"
                and manifest["harness_targets_source"] == "catalog/catalog.json"
                and len(manifest["harness_targets_source_sha256"]) == 64
                and not (target / "manifest.enriched.json").exists()
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            passed = False
        if not passed:
            print("portable manifest enrichment smoke check failed", file=sys.stderr)
            return 1
    return 0


def main() -> int:
    toolkit = _toolkit_path()
    exit_code = _run([sys.executable, str(toolkit / "validate_skill.py"), str(SKILL_DIR)])
    if (SKILL_DIR / "evals").is_dir():
        exit_code = _run([sys.executable, str(toolkit / "validate_evals.py"), str(SKILL_DIR)]) or exit_code
    exit_code = _portable_smoke() or exit_code
    return (
        _run(
            [
                sys.executable,
                str(SKILL_DIR / "scripts" / "enrich_manifest.py"),
                SKILL_DIR.name,
                "--dry-run",
            ]
        )
        or exit_code
    )


if __name__ == "__main__":
    raise SystemExit(main())
