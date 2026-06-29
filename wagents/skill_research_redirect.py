"""Legacy /skill-research/ URL redirect helpers.

Keep behavior aligned with docs/src/lib/skill-research-redirect.ts.
"""

from __future__ import annotations

import re
from typing import Literal
from urllib.parse import unquote

SkillCatalogGroup = Literal["custom", "external"]

_SKILL_RESEARCH_PATH = re.compile(r"^/skill-research/([^/]+)/?$")


def parse_skill_research_path(pathname: str) -> str | None:
    match = _SKILL_RESEARCH_PATH.match(pathname)
    if not match:
        return None
    return unquote(match.group(1))


def build_skill_research_redirect_map(index: dict) -> dict[str, SkillCatalogGroup]:
    groups: dict[str, SkillCatalogGroup] = {}
    for entry in index.get("allSkillIndex") or []:
        name = entry.get("name")
        if not name:
            continue
        groups[str(name)] = "custom" if entry.get("sourceKind") == "custom" else "external"
    return groups


def skill_research_redirect_target(
    skill_id: str,
    groups: dict[str, SkillCatalogGroup],
) -> str:
    group = groups.get(skill_id, "external")
    return f"/skills/catalog/{group}/{skill_id}/"
