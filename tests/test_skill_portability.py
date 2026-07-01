"""Run portable check.py for every skill in PLAN_SKILL_IDS."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.skill_portability_ids import PLAN_SKILL_IDS, SLOW_SKILLS

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("skill_id", PLAN_SKILL_IDS)
def test_skill_portable_check(skill_id: str) -> None:
    skill_dir = ROOT / "skills" / skill_id
    check_py = skill_dir / "scripts" / "check.py"
    assert check_py.is_file(), f"missing scripts/check.py for {skill_id}"
    env = {**os.environ, "SKILL_PORTABLE_CI": "1"}
    timeout = 600 if skill_id in SLOW_SKILLS else 120
    result = subprocess.run(
        [sys.executable, str(check_py)],
        cwd=skill_dir,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        msg = result.stderr or result.stdout
        pytest.fail(f"{skill_id} portable check failed:\n{msg}")
