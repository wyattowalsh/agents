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
    assert "- `config`: unchanged" in rendered
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


def test_collect_markdown_pages_respects_include_unlayered(tmp_path: Path) -> None:
    (tmp_path / "wiki").mkdir()
    (tmp_path / "wiki" / "index.md").write_text("# KB\n", encoding="utf-8")
    (tmp_path / "notes.md").write_text("# Notes\n", encoding="utf-8")

    layered_only = kb_lint.collect_markdown_pages(tmp_path)
    with_unlayered = kb_lint.collect_markdown_pages(tmp_path, include_unlayered=True)

    assert "wiki/index.md" in layered_only
    assert "notes.md" not in layered_only
    assert "notes.md" in with_unlayered


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

    # Title derived from root name appears in the wiki index
    assert "Acme Docs" in wiki_index
    # Activity log contains the initial bootstrap entry
    assert "- Mode: create" in activity_log
    assert "Bootstrap" in activity_log


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
