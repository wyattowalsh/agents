"""Tests for shared docs site data."""

from pathlib import Path

import pytest

from wagents.catalog import CatalogNode
from wagents.external_skills import parse_external_skill_entries
from wagents.site_model import (
    SUPPORTED_AGENT_IDS,
    VISUAL_ASSET_BY_ID,
    build_install_command,
    docs_asset_repo_path,
    docs_src_asset_css_url,
    external_skill_groups,
    render_site_data_module,
    render_visual_assets_css,
    site_data,
    trust_badge_for_tier,
)


def test_install_commands_use_shared_supported_agents():
    command = build_install_command(skill="review")

    assert command.startswith("npx skills add github:wyattowalsh/agents --skill review -y -g")
    for agent_id in SUPPORTED_AGENT_IDS:
        assert f"--agent {agent_id}" in command
    assert "claude-code --agent codex --agent gemini-cli" not in command


def test_site_data_derives_counts_from_catalog_nodes():
    nodes = [
        CatalogNode("skill", "one", "One", "Skill", {}, "", "skills/one/SKILL.md"),
        CatalogNode("skill", "two", "Two", "Skill", {}, "", "/tmp/two/SKILL.md", source="installed"),
        CatalogNode("agent", "agent-one", "Agent One", "Agent", {}, "", "agents/agent-one.md"),
    ]

    data = site_data(nodes, mcp_config_count=30, has_mcp_overview=True)

    assert data["counts"] == {
        "skills": 2,
        "customSkills": 1,
        "externalSkills": 1,
        "customMcp": 0,
        "externalMcp": 30,
        "mcpTools": 30,
        "supportedHarnesses": len(SUPPORTED_AGENT_IDS),
        "bundledAgents": 1,
    }


def test_site_data_filters_generated_skill_inventory_artifacts(tmp_path):
    skill_dir = tmp_path / "skills" / "demo"
    scripts_dir = skill_dir / "scripts"
    cache_dir = scripts_dir / "__pycache__"
    scripts_dir.mkdir(parents=True)
    cache_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: demo\ndescription: Demo\n---\n\n# Demo\n")
    (scripts_dir / "run.py").write_text("print('ok')\n")
    (scripts_dir / ".DS_Store").write_text("")
    (cache_dir / "run.cpython-313.pyc").write_bytes(b"cache")
    node = CatalogNode("skill", "demo", "Demo", "Demo", {}, "", str(skill_dir / "SKILL.md"))

    data = site_data([node])
    scripts = data["skillIndex"][0]["knowledge"]["scripts"]

    assert scripts == [str(Path("scripts") / "run.py")]


def test_render_site_data_module_exports_runtime_constants():
    rendered = render_site_data_module(site_data([]))

    assert "export const siteData =" in rendered
    assert "export const supportedAgents = baseSiteData.supportedAgents;" in rendered
    assert "export const installCommands = baseSiteData.installCommands;" in rendered
    assert "export const visualAssets = baseSiteData.visualAssets;" in rendered


def test_visual_assets_are_manifest_backed():
    data = site_data([])
    asset_ids = {asset["id"] for asset in data["visualAssets"]}

    assert {"logo", "social-card", "control-plane-hero", "catalog-mesh", "mcp-routing"} <= asset_ids
    assert docs_asset_repo_path(VISUAL_ASSET_BY_ID["logo"].src) == "docs/src/assets/brand/logo.webp"
    assert docs_asset_repo_path(VISUAL_ASSET_BY_ID["social-card"].src) == "docs/public/social-card.png"
    assert docs_src_asset_css_url(VISUAL_ASSET_BY_ID["control-plane-hero"].src) == (
        "./assets/brand/control-plane-hero.webp"
    )


def test_render_visual_assets_css_exports_src_asset_variables():
    rendered = render_visual_assets_css()

    assert "--agents-asset-control-plane-hero: url('./assets/brand/control-plane-hero.webp');" in rendered
    assert "--agents-asset-social-card" not in rendered


def test_site_data_splits_custom_and_external_indexes():
    curated = parse_external_skill_entries(
        """
## Install Now After Trust Gate

```bash
npx skills add example/skills --skill external-one -y -g -a codex
```
"""
    )
    nodes = [
        CatalogNode("skill", "custom-one", "Custom One", "Custom", {}, "", "skills/custom-one/SKILL.md"),
        CatalogNode(
            "skill",
            "installed-one",
            "Installed One",
            "Installed",
            {
                "_skills_source": "other/skills",
                "_skills_install_command": "npx skills add other/skills --skill installed-one -y -g",
            },
            "",
            "/tmp/installed-one/SKILL.md",
            source="installed",
        ),
    ]

    data = site_data(nodes, external_skills=curated)

    assert [row["name"] for row in data["customSkillIndex"]] == ["custom-one"]
    assert {row["name"] for row in data["externalSkillIndex"]} == {"external-one", "installed-one"}
    assert {row["name"] for row in data["allSkillIndex"]} == {"custom-one", "external-one", "installed-one"}
    assert data["skillIndex"] == data["allSkillIndex"]


def test_installed_local_inventory_rows_use_public_safe_source_labels():
    node = CatalogNode(
        "skill",
        "local-only",
        "Local Only",
        "Installed from local inventory",
        {},
        "",
        "/Users/example/.codex/skills/local-only/SKILL.md",
        source="installed",
    )

    data = site_data([node])
    row = data["externalSkillIndex"][0]

    assert row["sourceType"] == "installed"
    assert row["sourceRoot"] == "local installed inventory"
    assert row["displaySource"] == "local installed inventory"
    assert row["sourceKind"] == "local-inventory"
    assert row["sourcePath"] == ""
    assert row["installSource"] == ""
    assert row["installCommand"] == ""
    assert row["installable"] is False
    assert row["localInventoryOnly"] is True
    assert row["status"] == "installed-external"
    assert "/Users/" not in " ".join(str(value) for value in row.values())


def test_external_skill_groups_use_display_source_not_local_path():
    node = CatalogNode(
        "skill",
        "local-only",
        "Local Only",
        "Installed from local inventory",
        {},
        "",
        "/Users/example/.codex/skills/local-only/SKILL.md",
        source="installed",
    )

    data = site_data([node])
    sources = {group["source"] for group in external_skill_groups(data["externalSkillIndex"])["bySource"]}

    assert sources == {"local installed inventory"}
    assert all("/Users/" not in source for source in sources)


def test_site_data_excludes_installed_rows_that_match_custom_and_merges_curated_matches():
    curated = parse_external_skill_entries(
        """
## Install Now After Trust Gate

```bash
npx skills add example/skills --skill external-one -y -g -a codex
```
"""
    )
    nodes = [
        CatalogNode("skill", "custom-one", "Custom One", "Custom", {}, "", "skills/custom-one/SKILL.md"),
        CatalogNode(
            "skill",
            "custom-one",
            "Custom One Installed",
            "Installed duplicate",
            {"_skills_source": "example/skills", "_skills_installed_agents": ["codex"]},
            "",
            "/tmp/custom-one/SKILL.md",
            source="installed",
        ),
        CatalogNode(
            "skill",
            "external-one",
            "External One Installed",
            "Installed curated duplicate",
            {"_skills_source": "example/skills", "_skills_installed_agents": ["codex"]},
            "",
            "/tmp/external-one/SKILL.md",
            source="installed",
        ),
    ]

    data = site_data(nodes, external_skills=curated)
    rows = {row["name"]: row for row in data["allSkillIndex"]}

    assert set(rows) == {"custom-one", "external-one"}
    assert rows["external-one"]["sourceType"] == "curated-external"
    assert rows["external-one"]["installedAgents"] == ["codex"]
    assert rows["external-one"]["displaySource"] == "example/skills"
    assert rows["external-one"]["installedLocalInventoryOnly"] is False
    assert rows["external-one"]["installedExternalPath"] == ""
    assert "external-one" in {row["name"] for row in data["externalSkillIndex"]}


@pytest.mark.parametrize(
    ("tier", "expected"),
    [
        ("repo", ("Repo-owned", "tip")),
        ("curated-trust-gated", ("Curated", "note")),
        ("needs-inspection", ("Inspect first", "caution")),
        ("read-only-discovered", ("Inspect first", "caution")),
        ("external-installed", ("Local install", "default")),
        ("global-only-or-avoid", ("Avoid default", "danger")),
        ("github", ("GitHub", "note")),
        ("git", ("Git source", "note")),
        ("unknown-unknown", ("External", "default")),
        ("", ("External", "default")),
    ],
)
def test_trust_badge_for_tier_maps_public_labels(tier, expected):
    assert trust_badge_for_tier(tier) == expected


def test_skill_index_rows_include_trust_badges():
    node = CatalogNode("skill", "demo", "Demo", "Demo skill", {}, "", "skills/demo/SKILL.md")
    data = site_data([node])
    row = data["customSkillIndex"][0]
    assert row["trustBadge"] == "Repo-owned"
    assert row["trustBadgeVariant"] == "tip"


def test_installed_node_with_read_only_discovered_trust_tier_emits_inspect_badge():
    node = CatalogNode(
        "skill",
        "discovered-one",
        "Discovered One",
        "Discovered skill",
        {"_skills_trust_tier": "read-only-discovered"},
        "",
        "/tmp/discovered-one/SKILL.md",
        source="installed",
    )
    data = site_data([node])
    row = data["externalSkillIndex"][0]
    assert row["trustTier"] == "read-only-discovered"
    assert row["trustBadge"] == "Inspect first"
    assert row["trustBadgeVariant"] == "caution"


def test_curated_external_stub_node_with_curated_trust_gated_tier_emits_curated_badge():
    node = CatalogNode(
        "skill",
        "curated-stub",
        "Curated Stub",
        "Curated external stub",
        {"_skills_trust_tier": "curated-trust-gated"},
        "",
        "config/external-skills.md",
        source="curated-external",
    )
    data = site_data([node])
    row = data["externalSkillIndex"][0]
    assert row["trustTier"] == "curated-trust-gated"
    assert row["trustBadge"] == "Curated"
    assert row["trustBadgeVariant"] == "note"
