"""Ensure packaged skill ZIPs only include portable asset_toolkit modules."""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_CREATOR_SCRIPTS = ROOT / "skills" / "skill-creator" / "scripts"
BUNDLED_PACKAGE_SCRIPT = SKILL_CREATOR_SCRIPTS / "asset_toolkit" / "package.py"

sys.path.insert(0, str(SKILL_CREATOR_SCRIPTS))

from package import PORTABLE_TOOLKIT_MODULES, package_skill  # noqa: E402

VALID_SKILL_MD = """\
---
name: toolkit-allowlist
description: Skill used to verify portable toolkit vendoring
license: MIT
metadata:
  author: test
  version: 1.0.0
---

# Toolkit Allowlist

Body.
"""


def test_package_vendors_only_allowlisted_toolkit_modules(tmp_path: Path) -> None:
    skill_dir = tmp_path / "toolkit-allowlist"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(VALID_SKILL_MD)
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "check.py").write_text("#!/usr/bin/env python3\n")

    result = package_skill(skill_dir, tmp_path / "dist")
    assert not result["errors"]

    zip_path = Path(result["output_path"])
    with zipfile.ZipFile(zip_path) as zf:
        toolkit_names = {Path(name).name for name in zf.namelist() if "/scripts/asset_toolkit/" in name}

    assert toolkit_names == set(PORTABLE_TOOLKIT_MODULES)
    assert toolkit_names == {
        "__init__.py",
        "_shared.py",
        "common.py",
        "package.py",
        "validate_evals.py",
        "validate_hooks.py",
        "validate_skill.py",
    }
    assert "validate_repo.py" not in toolkit_names
    assert "validate_mcp.py" not in toolkit_names


def test_bundled_package_script_vendors_its_own_toolkit(tmp_path: Path) -> None:
    skill_dir = tmp_path / "toolkit-allowlist"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(VALID_SKILL_MD, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(BUNDLED_PACKAGE_SCRIPT), str(skill_dir), "--dry-run"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["blocked"] is False
    assert set(payload["files_included"]) == {
        "SKILL.md",
        *(f"scripts/asset_toolkit/{module}" for module in PORTABLE_TOOLKIT_MODULES),
    }


def _make_skill_with_local_toolkit(tmp_path: Path, modules: set[str]) -> Path:
    skill_dir = tmp_path / "toolkit-allowlist"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(VALID_SKILL_MD, encoding="utf-8")
    toolkit_dir = skill_dir / "scripts" / "asset_toolkit"
    toolkit_dir.mkdir(parents=True)
    for module in modules:
        (toolkit_dir / module).write_text(f"# local divergent {module}\n", encoding="utf-8")
    return skill_dir


def test_existing_toolkit_allows_exact_seven_modules_without_digest_enforcement(tmp_path: Path) -> None:
    skill_dir = _make_skill_with_local_toolkit(tmp_path, set(PORTABLE_TOOLKIT_MODULES))

    result = package_skill(skill_dir, tmp_path / "dist")

    assert not result["errors"]
    with zipfile.ZipFile(result["output_path"]) as archive:
        packaged = archive.read("toolkit-allowlist/scripts/asset_toolkit/package.py")
    assert packaged == b"# local divergent package.py\n"


def test_existing_toolkit_rejects_unexpected_modules(tmp_path: Path) -> None:
    modules = {*PORTABLE_TOOLKIT_MODULES, "validate_repo.py"}
    skill_dir = _make_skill_with_local_toolkit(tmp_path, modules)

    result = package_skill(skill_dir, tmp_path / "dist", dry_run=True)

    assert result["blocked"] is True
    assert "unexpected: validate_repo.py" in "\n".join(result["errors"])


def test_existing_toolkit_rejects_missing_modules(tmp_path: Path) -> None:
    modules = set(PORTABLE_TOOLKIT_MODULES) - {"validate_hooks.py"}
    skill_dir = _make_skill_with_local_toolkit(tmp_path, modules)

    result = package_skill(skill_dir, tmp_path / "dist", dry_run=True)

    assert result["blocked"] is True
    assert "missing: validate_hooks.py" in "\n".join(result["errors"])
