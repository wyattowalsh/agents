"""Regression tests for the nerdbot helper scripts."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skills" / "nerdbot" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import kb_bootstrap  # noqa: E402
import kb_inventory  # noqa: E402
import kb_lint  # noqa: E402
from kb_inventory import STARTER_FILES  # noqa: E402


def test_parse_bootstrap_packet_sections_exposes_activity_log_template() -> None:
    packet_text = kb_bootstrap.read_asset_text(kb_bootstrap.KB_BOOTSTRAP_TEMPLATE_PATH)

    sections = kb_bootstrap.parse_bootstrap_packet_sections(packet_text)

    assert STARTER_FILES["wiki_index"] in sections
    assert STARTER_FILES["source_map"] in sections
    assert STARTER_FILES["coverage_index"] in sections
    assert STARTER_FILES["activity_log"] in sections
    assert "Risks / rollback" in sections[STARTER_FILES["activity_log"]]


def test_render_activity_log_keeps_mode_and_risk_fields(tmp_path: Path) -> None:
    rendered = kb_bootstrap.render_activity_log(tmp_path / "example-kb")

    assert "- Mode: create" in rendered
    assert "- `schema`: unchanged" in rendered
    assert "- `config`: added `config/obsidian-vault.md`" in rendered
    assert "- `vault`: initialized `.obsidian/` shared surfaces and note metadata defaults" in rendered
    assert "- Risks / rollback:" in rendered


def test_canonicalize_reference_path_normalizes_relative_links() -> None:
    page = kb_lint.MarkdownPage(
        path=Path("wiki/topics/example.md"),
        relative_path="wiki/topics/example.md",
        text="",
        title="Example",
        normalized_title="example",
        headings=set(),
        links=[],
        is_wiki=True,
        is_index_like=False,
        plain_excerpt="example",
    )

    assert kb_lint.canonicalize_reference_path(page, "../index.md#overview") == "wiki/index.md"
    assert kb_lint.canonicalize_reference_path(page, "../../indexes/source-map.md") == "indexes/source-map.md"


def test_extract_obsidian_references_splits_links_and_embeds() -> None:
    text = "See [[wiki/index|Home]] and ![[raw/assets/diagram.png|300]]."

    links, embeds = kb_inventory.extract_obsidian_references(text)

    assert links == ["wiki/index"]
    assert embeds == ["raw/assets/diagram.png"]


def test_extract_frontmatter_aliases_supports_list_and_scalar_forms() -> None:
    list_text = "---\naliases:\n  - Alpha\n  - Beta\n---\n# Note\n"
    scalar_text = "---\nalias: Gamma\n---\n# Note\n"

    assert kb_inventory.extract_frontmatter_aliases(list_text) == ["Alpha", "Beta"]
    assert kb_inventory.extract_frontmatter_aliases(scalar_text) == ["Gamma"]


def test_collect_markdown_pages_respects_include_unlayered(tmp_path: Path) -> None:
    (tmp_path / "wiki").mkdir()
    (tmp_path / "wiki" / "index.md").write_text("# KB\n", encoding="utf-8")
    (tmp_path / "notes.md").write_text("# Notes\n", encoding="utf-8")

    layered_only = kb_lint.collect_markdown_pages(tmp_path)
    with_unlayered = kb_lint.collect_markdown_pages(tmp_path, include_unlayered=True)

    assert "wiki/index.md" in layered_only
    assert "notes.md" not in layered_only
    assert "notes.md" in with_unlayered


def test_build_inventory_detects_obsidian_vault_and_shared_surfaces(tmp_path: Path) -> None:
    (tmp_path / ".obsidian" / "templates").mkdir(parents=True)
    (tmp_path / ".obsidian" / "snippets").mkdir(parents=True)
    (tmp_path / "wiki").mkdir()
    (tmp_path / "wiki" / "index.md").write_text(
        "---\n"
        "aliases:\n"
        "  - Home\n"
        "kind: overview\n"
        "status: active\n"
        "updated: 2026-04-13\n"
        "---\n"
        "# KB\n\n"
        "See [[wiki/topic]].\n",
        encoding="utf-8",
    )
    (tmp_path / "wiki" / "topic.md").write_text("# Topic\n", encoding="utf-8")

    inventory = kb_inventory.build_inventory(tmp_path)

    assert inventory["vault"]["detected"] is True
    assert inventory["vault"]["mode"] in {"obsidian_native_vault", "mixed_vault"}
    assert ".obsidian/templates" in inventory["vault"]["shared_config_paths"]
    assert inventory["vault"]["link_summary"]["obsidian_links"] >= 1
    assert inventory["vault"]["frontmatter_summary"]["alias_count"] >= 1


def test_lint_links_resolves_wikilinks_aliases_and_block_refs(tmp_path: Path) -> None:
    (tmp_path / "wiki").mkdir()
    source = tmp_path / "wiki" / "source.md"
    target = tmp_path / "wiki" / "target.md"
    source.write_text(
        "---\naliases:\n  - Source Alias\n---\n# Source\n\nSee [[Target Note#^claim-block]].\n",
        encoding="utf-8",
    )
    target.write_text(
        "---\naliases:\n  - Target Note\n---\n# Target\n\nClaim text. ^claim-block\n",
        encoding="utf-8",
    )

    pages = kb_lint.collect_markdown_pages(tmp_path)
    issues, inbound = kb_lint.lint_links(tmp_path, pages)

    assert issues == []
    assert inbound["wiki/target.md"] == {"wiki/source.md"}


def test_lint_obsidian_vault_flags_tracked_volatile_state(tmp_path: Path) -> None:
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / ".obsidian" / "workspace.json").write_text("{}", encoding="utf-8")
    (tmp_path / "wiki").mkdir()
    (tmp_path / "wiki" / "index.md").write_text("# KB\n", encoding="utf-8")

    pages = kb_lint.collect_markdown_pages(tmp_path)
    issues = kb_lint.lint_obsidian_vault(tmp_path, pages)

    assert any(issue["rule"] == "tracked_volatile_obsidian_state" for issue in issues)


# ---------------------------------------------------------------------------
# scaffold() end-to-end regression tests
# ---------------------------------------------------------------------------


def _all_starter_rel_paths() -> set[str]:
    """Return the set of relative paths for all starter files."""
    return set(STARTER_FILES.values())


def _non_append_only_rel_paths() -> set[str]:
    """Return starter file paths excluding append-only files."""
    return _all_starter_rel_paths() - kb_bootstrap.APPEND_ONLY_STARTER_FILES


def test_scaffold_initial_creates_all_directories_and_starter_files(
    tmp_path: Path,
) -> None:
    """First scaffold into an empty root creates every directory and file."""
    root = tmp_path / "my-kb"

    result = kb_bootstrap.scaffold(root, force=False, dry_run=False)

    # All default directories were created
    for rel_dir in kb_inventory.DEFAULT_DIRECTORIES:
        assert (root / rel_dir).is_dir(), f"Missing directory: {rel_dir}"

    # All starter files were created on disk
    for rel_path in _all_starter_rel_paths():
        target = root / rel_path
        assert target.is_file(), f"Missing starter file: {rel_path}"
        assert target.read_text(encoding="utf-8").strip(), f"Empty starter file: {rel_path}"

    assert (root / ".obsidian" / "templates").is_dir()
    assert (root / ".obsidian" / "snippets").is_dir()
    assert (root / "raw" / "assets").is_dir()

    # Return dict reports everything as newly created
    assert result["root_created"] is True
    assert result["dry_run"] is False
    assert result["force"] is False
    assert set(result["created_directories"]) == set(kb_inventory.DEFAULT_DIRECTORIES)
    assert set(result["created_files"]) == _all_starter_rel_paths()
    assert result["overwritten_files"] == []
    assert result["skipped_existing"] == []
    assert result["skipped_directories"] == []


def test_scaffold_initial_renders_placeholders_from_root_name(
    tmp_path: Path,
) -> None:
    """Starter files contain repo-local placeholders derived from root name."""
    root = tmp_path / "acme-docs"
    kb_bootstrap.scaffold(root, force=False, dry_run=False)

    wiki_index = (root / STARTER_FILES["wiki_index"]).read_text(encoding="utf-8")
    activity_log = (root / STARTER_FILES["activity_log"]).read_text(encoding="utf-8")
    vault_config = (root / STARTER_FILES["vault_config"]).read_text(encoding="utf-8")

    # Title derived from root name appears in the wiki index
    assert "Acme Docs" in wiki_index
    # Activity log contains the initial bootstrap entry
    assert "- Mode: create" in activity_log
    assert "Bootstrap" in activity_log
    assert "obsidian-native" in vault_config


def test_scaffold_rerun_no_force_preserves_all_existing_files(
    tmp_path: Path,
) -> None:
    """Second scaffold without --force skips every existing file including activity log."""
    root = tmp_path / "my-kb"
    kb_bootstrap.scaffold(root, force=False, dry_run=False)

    # Mutate each starter file so we can verify no overwrite occurred
    sentinel = "# USER-ADDED CONTENT\n"
    for rel_path in _all_starter_rel_paths():
        target = root / rel_path
        target.write_text(sentinel + rel_path, encoding="utf-8")

    result = kb_bootstrap.scaffold(root, force=False, dry_run=False)

    # Every file still contains the user sentinel
    for rel_path in _all_starter_rel_paths():
        content = (root / rel_path).read_text(encoding="utf-8")
        assert content == sentinel + rel_path, f"File was overwritten when it should have been skipped: {rel_path}"

    # Return dict reports nothing created, everything skipped
    assert result["root_created"] is False
    assert result["created_files"] == []
    assert result["overwritten_files"] == []
    assert set(result["skipped_existing"]) == _all_starter_rel_paths()
    assert set(result["skipped_directories"]) == set(kb_inventory.DEFAULT_DIRECTORIES)


def test_scaffold_rerun_force_overwrites_normal_but_preserves_activity_log(
    tmp_path: Path,
) -> None:
    """Second scaffold with --force overwrites normal starter files but never the activity log."""
    root = tmp_path / "my-kb"
    kb_bootstrap.scaffold(root, force=False, dry_run=False)

    # Write distinctive content into every starter file
    user_sentinel = "# HAND-WRITTEN NOTES\n"
    for rel_path in _all_starter_rel_paths():
        (root / rel_path).write_text(user_sentinel + rel_path, encoding="utf-8")

    result = kb_bootstrap.scaffold(root, force=True, dry_run=False)

    # Activity log must still contain the user sentinel (append-only contract)
    activity_content = (root / STARTER_FILES["activity_log"]).read_text(encoding="utf-8")
    assert activity_content == user_sentinel + STARTER_FILES["activity_log"], (
        "Append-only activity log was overwritten despite --force"
    )

    # Non-append-only files must have been overwritten (no more sentinel)
    for rel_path in _non_append_only_rel_paths():
        content = (root / rel_path).read_text(encoding="utf-8")
        assert user_sentinel not in content, f"Starter file was NOT overwritten by --force: {rel_path}"
        assert content.strip(), f"Overwritten file is empty: {rel_path}"

    # Return dict reports the right buckets
    assert set(result["overwritten_files"]) == _non_append_only_rel_paths()
    assert STARTER_FILES["activity_log"] in result["skipped_existing"]
    assert STARTER_FILES["activity_log"] not in result["overwritten_files"]
    assert result["created_files"] == []


def test_scaffold_dry_run_writes_nothing_to_disk(tmp_path: Path) -> None:
    """Dry-run returns what would happen but touches no files."""
    root = tmp_path / "dry-kb"

    result = kb_bootstrap.scaffold(root, force=False, dry_run=True)

    # Root should not have been created
    assert not root.exists()
    assert result["dry_run"] is True
    assert result["root_created"] is True  # would have been created
    assert len(result["created_directories"]) == len(kb_inventory.DEFAULT_DIRECTORIES)
    assert len(result["created_files"]) == len(_all_starter_rel_paths())


def test_should_fail_respects_severity_thresholds() -> None:
    issues = [{"severity": "suggestion"}, {"severity": "warning"}, {"severity": "critical"}]

    assert kb_lint.should_fail(issues, "critical") is True
    assert kb_lint.should_fail([{"severity": "suggestion"}], "critical") is False
    assert kb_lint.should_fail([{"severity": "warning"}], "warning") is True
    assert kb_lint.should_fail([{"severity": "suggestion"}], "warning") is False
    assert kb_lint.should_fail(issues, "none") is False
