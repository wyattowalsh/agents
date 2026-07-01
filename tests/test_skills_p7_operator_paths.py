"""No repo-root skills/*/scripts/ paths in SKILL.md prose."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "skill-creator" / "scripts"))
from _shared import find_nonportable_body_operator_lines, parse_frontmatter

from tests.skill_portability_ids import PLAN_SKILL_IDS

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("skill_id", PLAN_SKILL_IDS)
def test_skill_body_has_no_repo_root_script_paths(skill_id: str) -> None:
    skill_md = ROOT / "skills" / skill_id / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    _fm, body = parse_frontmatter(content)
    issues = find_nonportable_body_operator_lines(body)
    assert not issues, (
        f"{skill_id} SKILL.md has non-portable body operator paths: " +
        "; ".join(f"line {i['line']}: {i['match']}" for i in issues[:5])
    )
