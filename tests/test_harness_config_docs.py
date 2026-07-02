from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_plugin_skill_ownership_docs_cover_cleanup_and_catalog_surfaces() -> None:
    page = ROOT / "docs" / "src" / "content" / "docs" / "harness-config" / "plugin-skill-ownership.mdx"
    text = page.read_text(encoding="utf-8")

    assert "Codex" in text
    assert "OpenCode" in text
    assert "wagents skills cleanup --dry-run --format json" in text
    assert "remove-generated-symlink" in text
    assert "docs/src/authoring/skills/<name>.mdx" in text
    assert "/skills/catalog/external/<name>/" in text


def test_harness_config_hub_links_plugin_skill_ownership_page() -> None:
    index = ROOT / "docs" / "src" / "content" / "docs" / "harness-config" / "index.mdx"
    text = index.read_text(encoding="utf-8")

    assert "/harness-config/plugin-skill-ownership/" in text
    assert "4 surfaces" in text


def test_cli_docs_include_skills_cleanup_command() -> None:
    cli = ROOT / "docs" / "src" / "content" / "docs" / "cli.mdx"
    text = cli.read_text(encoding="utf-8")

    assert "`wagents skills cleanup`" in text
    assert "wagents skills cleanup --dry-run --format json" in text
    assert "`skills cleanup`" in text
