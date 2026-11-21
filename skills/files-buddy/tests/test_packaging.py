"""Portable installation and validation regression cases."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]


def copy_skill(destination: Path) -> Path:
    """Copy only distributable source, without a checkout or environment."""
    target = destination / "files-buddy"
    shutil.copytree(
        SKILL,
        target,
        ignore=shutil.ignore_patterns(".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "*.pyc"),
    )
    return target


def check_skill(skill: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(skill / "scripts/check.py")],
        cwd=skill,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_standalone_uses_bundled_packager(tmp_path: Path) -> None:
    skill = copy_skill(tmp_path)
    result = check_skill(skill)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert {check["name"] for check in report["checks"]} >= {"skill", "evals", "package"}
    assert "repository-audit" not in {check["name"] for check in report["checks"]}


def test_missing_indexed_reference_fails_standalone_check(tmp_path: Path) -> None:
    skill = copy_skill(tmp_path)
    (skill / "references/safety-workflow.md").unlink()
    result = check_skill(skill)
    assert result.returncode != 0
    report = json.loads(result.stdout)
    package = next(check for check in report["checks"] if check["name"] == "package")
    assert package["passed"] is False
    assert "safety-workflow.md" in package["stdout"]


def test_missing_bundled_packager_is_not_silently_skipped(tmp_path: Path) -> None:
    skill = copy_skill(tmp_path)
    (skill / "scripts/asset_toolkit/package.py").unlink()
    result = check_skill(skill)
    assert result.returncode != 0
    assert "Missing bundled gate: package.py" in result.stdout


def test_runtime_specific_frontmatter_is_rejected(tmp_path: Path) -> None:
    skill = copy_skill(tmp_path)
    source = skill / "SKILL.md"
    source.write_text(source.read_text().replace("name: files-buddy", "name: files-buddy\nmodel: sonnet", 1))
    result = check_skill(skill)
    assert result.returncode != 0
    assert "Nonportable frontmatter key: model" in result.stdout
