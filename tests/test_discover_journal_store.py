"""Tests for discover-skills journal-store.py — YAML frontmatter, state blocks, CRUD commands."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Load the module from its file path (not a normal importable package)
# ---------------------------------------------------------------------------

_SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "discover-skills"
    / "scripts"
    / "journal-store.py"
)

_spec = importlib.util.spec_from_file_location("journal_store", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None, f"Cannot find {_SCRIPT_PATH}"
jmod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(jmod)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def journal_dir(tmp_path, monkeypatch):
    """Point JOURNAL_DIR and ARCHIVE_DIR at a temp directory."""
    jdir = tmp_path / "discover-skills"
    jdir.mkdir()
    monkeypatch.setattr(jmod, "JOURNAL_DIR", jdir)
    monkeypatch.setattr(jmod, "ARCHIVE_DIR", jdir / "archive")
    return jdir


def _init_journal(journal_dir: Path, focus: str = "test domain") -> dict:
    """Create a journal via cmd_init and return the parsed JSON result."""
    args = argparse.Namespace(focus=focus)
    import io

    buf = io.StringIO()
    with patch.object(sys, "stdout", buf):
        jmod.cmd_init(args)
    return json.loads(buf.getvalue())


# ---------------------------------------------------------------------------
# 1. parse_frontmatter / serialize_frontmatter round-trip
# ---------------------------------------------------------------------------


def test_parse_frontmatter_roundtrip():
    """serialize_frontmatter -> parse_frontmatter preserves all field types."""
    meta = {
        "title": "Hello World",
        "count": 42,
        "enabled": True,
        "disabled": False,
        "ratio": 3.14,
        "tags": ["alpha", "beta"],
        "empty_list": [],
        "nothing": None,
    }
    text = jmod.serialize_frontmatter(meta) + "\n\nBody text here.\n"
    parsed_meta, body = jmod.parse_frontmatter(text)

    assert parsed_meta["title"] == "Hello World"
    assert parsed_meta["count"] == 42
    assert parsed_meta["enabled"] is True
    assert parsed_meta["disabled"] is False
    assert parsed_meta["ratio"] == 3.14
    assert parsed_meta["tags"] == ["alpha", "beta"]
    assert parsed_meta["empty_list"] == []
    assert parsed_meta["nothing"] is None
    assert "Body text here." in body


# ---------------------------------------------------------------------------
# 2. Body containing '---' horizontal rule does NOT corrupt frontmatter
# ---------------------------------------------------------------------------


def test_parse_frontmatter_body_with_hrule():
    """A horizontal rule (---) inside the body must not be confused with frontmatter."""
    text = (
        "---\ntitle: My Doc\nstatus: ok\n---\n\n"
        "# Heading\n\nSome text.\n\n---\n\nMore text after hrule.\n"
    )
    meta, body = jmod.parse_frontmatter(text)
    assert meta["title"] == "My Doc"
    assert meta["status"] == "ok"
    assert "More text after hrule." in body


# ---------------------------------------------------------------------------
# 3. Quoted string round-trip (escaped characters)
# ---------------------------------------------------------------------------


def test_parse_yaml_value_quoted_roundtrip():
    """Double-quoted strings with escaped chars survive serialize -> parse."""
    original = 'He said "hi"'
    scalar = jmod._yaml_scalar(original)
    parsed = jmod._parse_yaml_value(scalar)
    assert parsed == original

    # Also test backslash
    original2 = "path\\to\\file"
    scalar2 = jmod._yaml_scalar(original2)
    parsed2 = jmod._parse_yaml_value(scalar2)
    assert parsed2 == original2


# ---------------------------------------------------------------------------
# 4. Hyphenated keys are parsed correctly
# ---------------------------------------------------------------------------


def test_parse_yaml_simple_hyphenated_keys():
    """Keys with hyphens like 'session-type' must be parsed, not dropped."""
    yaml_text = "session-type: discovery\nfocus-area: AI tooling"
    result = jmod._parse_yaml_simple(yaml_text)
    assert result["session-type"] == "discovery"
    assert result["focus-area"] == "AI tooling"


# ---------------------------------------------------------------------------
# 5. cmd_init creates a journal file
# ---------------------------------------------------------------------------


def test_cmd_init_creates_journal(journal_dir):
    """cmd_init with a focus creates a journal file with valid frontmatter."""
    result = _init_journal(journal_dir, focus="AI tooling")
    assert result["action"] == "created"

    path = Path(result["path"])
    assert path.exists()
    assert path.parent == journal_dir

    text = path.read_text(encoding="utf-8")
    meta, body = jmod.parse_frontmatter(text)
    assert meta["session_type"] == "discovery"
    assert meta["focus"] == "AI tooling"
    assert meta["status"] == "In Progress"
    assert meta["candidates_found"] == 0
    assert "created" in meta
    assert "updated" in meta


# ---------------------------------------------------------------------------
# 6. cmd_save stores full data (candidates, wave, etc.)
# ---------------------------------------------------------------------------


def test_cmd_save_stores_full_data(journal_dir):
    """After init + save with --candidates, the journal has the data block."""
    init_result = _init_journal(journal_dir)
    journal_path = init_result["path"]

    candidates = [{"name": "test-skill", "score": 9}]
    save_args = argparse.Namespace(
        target=journal_path,
        status="In Progress",
        wave=2,
        candidates=json.dumps(candidates),
        proposals=None,
        installed=None,
    )
    import io

    buf = io.StringIO()
    with patch.object(sys, "stdout", buf):
        jmod.cmd_save(save_args)
    save_result = json.loads(buf.getvalue())

    assert save_result["metadata"]["candidates_found"] == 1
    assert save_result["metadata"]["last_wave"] == 2

    # Read the file and verify the data block exists
    text = Path(journal_path).read_text(encoding="utf-8")
    assert "<!-- CANDIDATES_WAVE_2 -->" in text
    assert '"test-skill"' in text


# ---------------------------------------------------------------------------
# 7. cmd_save rejects non-list JSON for --candidates
# ---------------------------------------------------------------------------


def test_cmd_save_rejects_non_list_json(journal_dir):
    """--candidates with a JSON object (not array) should exit(1)."""
    init_result = _init_journal(journal_dir)
    journal_path = init_result["path"]

    save_args = argparse.Namespace(
        target=journal_path,
        status=None,
        wave=1,
        candidates='{"bad": true}',
        proposals=None,
        installed=None,
    )
    with pytest.raises(SystemExit) as exc_info:
        jmod.cmd_save(save_args)
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# 8. _resolve_path rejects path traversal outside JOURNAL_DIR
# ---------------------------------------------------------------------------


def test_resolve_path_jail_rejects_traversal(journal_dir):
    """Attempting to resolve a path outside JOURNAL_DIR should exit(1)."""
    _init_journal(journal_dir)

    # Create a real file outside the journal directory so _resolve_path
    # finds it via the direct-path branch before hitting the jail check.
    outside_file = journal_dir.parent / "secret.md"
    outside_file.write_text("---\ntitle: secret\n---\n\nSecret data.\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        jmod._resolve_path(f"../{outside_file.name}")
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# 9. _resolve_path finds journal by keyword matching session_type
# ---------------------------------------------------------------------------


def test_resolve_path_keyword_matches_session_type(journal_dir):
    """Resolving by keyword 'discovery' should match a journal with that session_type."""
    init_result = _init_journal(journal_dir, focus="AI tooling")
    journal_path = Path(init_result["path"])

    resolved = jmod._resolve_path("discovery")
    assert resolved is not None
    assert resolved == journal_path.resolve()


# ---------------------------------------------------------------------------
# 10. STATE block timestamp contains full ISO format (with colons)
# ---------------------------------------------------------------------------


def test_state_block_timestamp_parsed(journal_dir):
    """After save, STATE block timestamp has a full ISO timestamp (colons)."""
    init_result = _init_journal(journal_dir)
    journal_path = init_result["path"]

    save_args = argparse.Namespace(
        target=journal_path,
        status="In Progress",
        wave=1,
        candidates='[{"name": "x"}]',
        proposals=None,
        installed=None,
    )
    import io

    buf = io.StringIO()
    with patch.object(sys, "stdout", buf):
        jmod.cmd_save(save_args)

    text = Path(journal_path).read_text(encoding="utf-8")
    _meta, body = jmod.parse_frontmatter(text)
    state_blocks = jmod.parse_state_blocks(body)
    assert len(state_blocks) >= 1

    ts = state_blocks[0].get("timestamp", "")
    # Must contain colons for HH:MM:SS, not be truncated
    assert ":" in str(ts), f"Timestamp appears truncated: {ts}"
    # Should look like YYYY-MM-DDTHH:MM:SS
    assert "T" in str(ts) or len(str(ts)) >= 19


# ---------------------------------------------------------------------------
# 11. cmd_resume returns resume_context with expected keys
# ---------------------------------------------------------------------------


def test_cmd_resume_returns_resume_context(journal_dir):
    """cmd_resume should return JSON with a resume_context key."""
    init_result = _init_journal(journal_dir)
    journal_path = init_result["path"]

    # Do a save first so there's meaningful state
    save_args = argparse.Namespace(
        target=journal_path,
        status="In Progress",
        wave=1,
        candidates='[{"name": "x"}]',
        proposals=None,
        installed=None,
    )
    import io

    buf = io.StringIO()
    with patch.object(sys, "stdout", buf):
        jmod.cmd_save(save_args)

    # Now resume (no target => picks most recent active)
    resume_args = argparse.Namespace(target=None)
    buf2 = io.StringIO()
    with patch.object(sys, "stdout", buf2):
        jmod.cmd_resume(resume_args)
    resume_result = json.loads(buf2.getvalue())

    assert "resume_context" in resume_result
    rc = resume_result["resume_context"]
    assert "last_wave" in rc
    assert "last_updated" in rc
    assert "candidates_found" in rc
    assert "proposals_made" in rc
    assert "installed" in rc
    assert "rejected" in rc
    assert rc["last_wave"] == 1
    assert rc["candidates_found"] == 1


# ---------------------------------------------------------------------------
# 12. _atomic_write leaves original file intact on failure
# ---------------------------------------------------------------------------


def test_atomic_write_leaves_original_on_failure(tmp_path):
    """If _atomic_write fails during os.replace, the original is preserved."""
    target = tmp_path / "test.md"
    target.write_text("original content", encoding="utf-8")

    with patch("os.replace", side_effect=OSError("mock replace failure")), pytest.raises(
        OSError, match="mock replace failure"
    ):
        jmod._atomic_write(target, "new content that should NOT land")

    assert target.read_text(encoding="utf-8") == "original content"
    # Temp file should have been cleaned up
    assert not (tmp_path / "test.tmp").exists()


# ---------------------------------------------------------------------------
# 13. cmd_delete with --force removes the journal file
# ---------------------------------------------------------------------------


def test_cmd_delete_with_force(journal_dir):
    """cmd_delete --force should delete the journal without prompting."""
    init_result = _init_journal(journal_dir)
    journal_path = Path(init_result["path"])
    assert journal_path.exists()

    delete_args = argparse.Namespace(target=str(journal_path), force=True)
    import io

    buf = io.StringIO()
    with patch.object(sys, "stdout", buf):
        jmod.cmd_delete(delete_args)
    delete_result = json.loads(buf.getvalue())

    assert delete_result["action"] == "deleted"
    assert not journal_path.exists()


# ---------------------------------------------------------------------------
# 14. parse_data_blocks extracts candidate and proposal data
# ---------------------------------------------------------------------------


def test_parse_data_blocks():
    """parse_data_blocks should extract CANDIDATES_WAVE and PROPOSALS_WAVE blocks."""
    body = (
        "# Discovery\n\n"
        "Some text.\n\n"
        '<!-- CANDIDATES_WAVE_2 -->\n```json\n[{"name": "alpha"}]\n```\n\n'
        '<!-- PROPOSALS_WAVE_2 -->\n```json\n[{"name": "beta", "action": "install"}]\n```\n\n'
        "Final notes.\n"
    )
    data = jmod.parse_data_blocks(body)

    assert 2 in data["candidates_by_wave"]
    assert data["candidates_by_wave"][2] == [{"name": "alpha"}]
    assert 2 in data["proposals_by_wave"]
    assert data["proposals_by_wave"][2] == [{"name": "beta", "action": "install"}]
