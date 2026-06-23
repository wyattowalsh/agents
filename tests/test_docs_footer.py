"""Contract tests for skill install footer parsing.

Keep in sync with docs/src/lib/skillInstallFooter.ts.
"""

import re

from tests.skill_hub_slugs import SKILL_HUB_SLUGS


def skill_id_for_install_footer(path: str) -> str | None:
    catalog_match = re.match(r"^skills/catalog/(?:custom|external)/([^/]+)$", path)
    return catalog_match.group(1) if catalog_match else None


class TestSkillInstallFooter:
    def test_catalog_detail_path(self):
        assert skill_id_for_install_footer("skills/catalog/custom/review") == "review"

    def test_hub_pages_return_none(self):
        for slug in SKILL_HUB_SLUGS:
            assert skill_id_for_install_footer(f"skills/{slug}") is None

    def test_legacy_single_segment_detail_returns_none(self):
        assert skill_id_for_install_footer("skills/review") is None

    def test_non_skill_paths_return_none(self):
        assert skill_id_for_install_footer("agents/planner") is None
