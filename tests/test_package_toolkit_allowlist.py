"""Ensure packaged skill ZIPs only include portable asset_toolkit modules."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "skill-creator" / "scripts"))

from package import PORTABLE_TOOLKIT_MODULES, package_skill

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
    assert "validate_repo.py" not in toolkit_names
    assert "validate_mcp.py" not in toolkit_names
