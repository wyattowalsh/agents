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
RESEARCH_VALIDATE_EVALS = ROOT / "skills" / "research" / "scripts" / "asset_toolkit" / "validate_evals.py"


@pytest.mark.parametrize("skill_id", PLAN_SKILL_IDS)
def test_bundled_toolkit_modules(skill_id: str) -> None:
    toolkit = ROOT / "skills" / skill_id / "scripts" / "asset_toolkit"
    missing = [m for m in MODULES if not (toolkit / m).is_file()]
    assert not missing, f"{skill_id} missing toolkit modules: {missing}"


def test_bundled_validate_evals_matches_canonical() -> None:
    canonical = ROOT / "skills" / "skill-creator" / "scripts" / "asset_toolkit" / "validate_evals.py"
    expected = canonical.read_text(encoding="utf-8")
    mismatches = []

    for bundled in sorted((ROOT / "skills").glob("*/scripts/asset_toolkit/validate_evals.py")):
        # Research skill source is guarded by policy; keep its bundled copy out of this sync gate.
        if bundled in {canonical, RESEARCH_VALIDATE_EVALS}:
            continue
        if bundled.read_text(encoding="utf-8") != expected:
            mismatches.append(str(bundled.relative_to(ROOT)))

    assert not mismatches, "stale eligible bundled validate_evals.py copies: " + ", ".join(mismatches)


def test_bundled_validate_hooks_matches_canonical() -> None:
    canonical = ROOT / "skills" / "skill-creator" / "scripts" / "asset_toolkit" / "validate_hooks.py"
    expected = canonical.read_text(encoding="utf-8")
    mismatches = []

    for bundled in sorted((ROOT / "skills").glob("*/scripts/asset_toolkit/validate_hooks.py")):
        if bundled == canonical:
            continue
        if bundled.read_text(encoding="utf-8") != expected:
            mismatches.append(str(bundled.relative_to(ROOT)))

    assert not mismatches, "stale bundled validate_hooks.py copies: " + ", ".join(mismatches)
