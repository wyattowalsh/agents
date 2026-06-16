"""Contract tests for legacy skill catalog redirects.

Keep in sync with docs/src/lib/legacySkillCatalogRedirect.ts and skillHubSlugs.ts.
"""

import re

from tests.skill_hub_slugs import SKILL_HUB_SLUGS


def legacy_skill_catalog_redirect(pathname: str) -> str | None:
    match = re.match(r"^/skills/([^/]+)/?$", pathname)
    if not match:
        return None
    if match.group(1) in SKILL_HUB_SLUGS:
        return None
    return f"/skills/catalog/{match.group(1)}/"


class TestLegacySkillCatalogRedirect:
    def test_legacy_detail_redirects_to_catalog(self):
        assert legacy_skill_catalog_redirect("/skills/honest-review/") == "/skills/catalog/honest-review/"
        assert legacy_skill_catalog_redirect("/skills/honest-review") == "/skills/catalog/honest-review/"

    def test_hub_slugs_are_not_redirected(self):
        for slug in SKILL_HUB_SLUGS:
            assert legacy_skill_catalog_redirect(f"/skills/{slug}/") is None

    def test_catalog_detail_paths_are_not_redirected(self):
        assert legacy_skill_catalog_redirect("/skills/catalog/foo/") is None

    def test_unrelated_paths_are_not_redirected(self):
        assert legacy_skill_catalog_redirect("/skills/") is None
        assert legacy_skill_catalog_redirect("/agents/planner/") is None
