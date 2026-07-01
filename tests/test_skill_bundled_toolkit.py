"""Assert bundled asset_toolkit modules exist for PLAN_SKILL_IDS."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.skill_portability_ids import PLAN_SKILL_IDS

ROOT = Path(__file__).resolve().parent.parent
MODULES = (
    "__init__.py",
    "_shared.py",
    "common.py",
    "package.py",
    "validate_skill.py",
    "validate_evals.py",
    "validate_hooks.py",
)


@pytest.mark.parametrize("skill_id", PLAN_SKILL_IDS)
def test_bundled_toolkit_modules(skill_id: str) -> None:
    toolkit = ROOT / "skills" / skill_id / "scripts" / "asset_toolkit"
    missing = [m for m in MODULES if not (toolkit / m).is_file()]
    assert not missing, f"{skill_id} missing toolkit modules: {missing}"
