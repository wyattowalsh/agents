"""Tests for legacy /skill-research/ redirect helpers."""

from __future__ import annotations

import json
from pathlib import Path

from wagents.skill_research_redirect import (
    build_skill_research_redirect_map,
    parse_skill_research_path,
    skill_research_redirect_target,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_INDEX = REPO_ROOT / "docs/public/generated-registries/skills-catalog-index.json"


def test_parse_skill_research_path_matches_legacy_urls():
    assert parse_skill_research_path("/skill-research/review") == "review"
    assert parse_skill_research_path("/skill-research/review/") == "review"
    assert parse_skill_research_path("/skill-research/foo%20bar/") == "foo bar"
    assert parse_skill_research_path("/skills/catalog/custom/review/") is None
    assert parse_skill_research_path("/skill-research/review/extra") is None


def test_build_skill_research_redirect_map_classifies_source_kind():
    index = {
        "allSkillIndex": [
            {"name": "review", "sourceKind": "custom"},
            {"name": "firecrawl", "sourceKind": "curated-external"},
            {"name": "no-kind"},
        ]
    }
    groups = build_skill_research_redirect_map(index)
    assert groups["review"] == "custom"
    assert groups["firecrawl"] == "external"
    assert groups["no-kind"] == "external"


def test_skill_research_redirect_target_uses_catalog_group():
    groups = {"review": "custom", "firecrawl": "external"}
    assert skill_research_redirect_target("review", groups) == "/skills/catalog/custom/review/"
    assert skill_research_redirect_target("unknown", groups) == "/skills/catalog/external/unknown/"


def test_redirect_targets_align_with_committed_catalog_index():
    if not CATALOG_INDEX.exists():
        return
    index = json.loads(CATALOG_INDEX.read_text(encoding="utf-8"))
    groups = build_skill_research_redirect_map(index)
    assert groups
    assert skill_research_redirect_target("review", groups).startswith("/skills/catalog/")
