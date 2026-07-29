from __future__ import annotations

import os
from typing import TYPE_CHECKING

from wagents.candidate_evidence import RUNTIME_DIGEST_IGNORED_DIRS, filesystem_digest

if TYPE_CHECKING:
    from pathlib import Path


def test_filesystem_digest_detects_content_and_mode_changes(tmp_path: Path) -> None:
    target = tmp_path / "tool"
    target.write_text("one", encoding="utf-8")
    target.chmod(0o644)
    baseline = filesystem_digest([target])

    target.write_text("two", encoding="utf-8")
    assert filesystem_digest([target]) != baseline
    target.write_text("one", encoding="utf-8")
    target.chmod(0o755)
    assert filesystem_digest([target]) != baseline


def test_filesystem_digest_hashes_symlink_target_without_following(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.write_text("same", encoding="utf-8")
    second.write_text("same", encoding="utf-8")
    link = tmp_path / "link"
    link.symlink_to(first.name)
    baseline = filesystem_digest([link])

    link.unlink()
    link.symlink_to(second.name)
    assert os.readlink(link) == second.name
    assert filesystem_digest([link]) != baseline


def test_filesystem_digest_marks_missing_paths(tmp_path: Path) -> None:
    target = tmp_path / "missing"
    before = filesystem_digest([target])
    target.write_text("created", encoding="utf-8")
    assert filesystem_digest([target]) != before


def test_runtime_integrity_includes_node_modules_dependencies(tmp_path: Path) -> None:
    package = tmp_path / "package"
    dependency = package / "node_modules" / "dependency" / "index.js"
    dependency.parent.mkdir(parents=True)
    dependency.write_text("one\n", encoding="utf-8")
    before = filesystem_digest([package], ignored_dirs=RUNTIME_DIGEST_IGNORED_DIRS)

    dependency.write_text("two\n", encoding="utf-8")

    assert "node_modules" not in RUNTIME_DIGEST_IGNORED_DIRS
    assert filesystem_digest([package], ignored_dirs=RUNTIME_DIGEST_IGNORED_DIRS) != before
