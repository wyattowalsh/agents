"""Tests for catalog page composition helpers."""

from pathlib import Path

from wagents.docs_compose import build_compose_batch_prompt, compose_coverage, is_composed_mdx
from wagents.docs_compose import ComposeTarget


def test_is_composed_mdx_hand_maintained() -> None:
    text = "---\ntitle: x\n---\n{/* HAND-MAINTAINED */}\n"
    assert is_composed_mdx(text) is True


def test_is_composed_mdx_frontmatter_flag() -> None:
    text = "---\ntitle: x\ncomposed: true\n---\nbody\n"
    assert is_composed_mdx(text) is True


def test_is_composed_mdx_scaffold() -> None:
    text = "---\ntitle: x\ncomposed: false\n---\nbody\n"
    assert is_composed_mdx(text) is False


def test_build_compose_batch_prompt_lists_targets() -> None:
    batch = [
        ComposeTarget(
            surface="skills",
            asset_id="learn",
            page_path=Path("docs/src/content/docs/skills/catalog/custom/learn.mdx"),
            source_path="skills/learn/SKILL.md",
            source_kind="custom",
        )
    ]
    prompt = build_compose_batch_prompt(batch, wave_id="test-wave")
    assert "learn" in prompt
    assert "orchestrator.mdx" in prompt
    assert "grok-composer-2.5-fast" in prompt


def test_compose_coverage_structure() -> None:
    report = compose_coverage(surface="skills")
    assert "total" in report
    assert "composed_pct" in report
    assert "by_surface" in report


def test_apply_compose_batch_dry_run_counts_scaffolds() -> None:
    from wagents.docs_compose_apply import apply_compose_batch

    result = apply_compose_batch(surface="agents", dry_run=True, wave_id="test-wave")
    assert result.written >= 0
    assert result.skipped >= 0


def test_compose_skill_mdx_external_contract(tmp_path, monkeypatch) -> None:
    from wagents.catalog import CatalogNode
    from wagents.docs_compose_apply import compose_skill_mdx

    node = CatalogNode(
        kind="skill",
        id="ab-testing",
        title="Ab Testing",
        description="A/B testing skill",
        metadata={
            "_curated_status": "install-now-after-trust-gate",
            "_skills_install_command": "npx skills add example -y",
            "target_agents": ["claude-code"],
        },
        body="",
        source_path="docs/src/authoring/skills/ab-testing.mdx",
        source="curated-external",
    )
    text = compose_skill_mdx(node, [], [node], wave_id="test-wave")
    assert "composed: true" in text
    assert "{/* HAND-MAINTAINED */}" in text
    assert "Curated external (hand-maintained)" in text


def test_upgrade_custom_batch_dry_run() -> None:
    from wagents.docs_compose_upgrade import upgrade_custom_batch

    result = upgrade_custom_batch(dry_run=True)
    assert result.written >= 49


def test_upgrade_external_batch_dry_run() -> None:
    from wagents.docs_compose_upgrade_external import upgrade_external_batch

    result = upgrade_external_batch(dry_run=True)
    assert result.written == 0
    assert result.skipped == 0
