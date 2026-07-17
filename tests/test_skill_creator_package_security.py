"""Adversarial archive-safety tests for the Skill Creator packager."""

from __future__ import annotations

import json
import os
import stat
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "skill-creator" / "scripts"))

import package

VALID_SKILL_MD = """\
---
name: secure-pkg
description: A test skill for archive safety
license: MIT
metadata:
  author: tester
  version: "1.0.0"
---

# Secure Pkg

Body.
"""


def _make_skill(tmp_path: Path) -> Path:
    skill_dir = tmp_path / "secure-pkg"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(VALID_SKILL_MD, encoding="utf-8")
    return skill_dir


def _assert_safety_block(result: dict, expected: str) -> None:
    assert result["blocked"] is True
    assert result["errors"]
    assert expected in "\n".join(result["errors"]).lower()
    assert result["output_path"] is None or not Path(result["output_path"]).exists()


def test_rejects_file_symlink_without_reading_target(tmp_path: Path) -> None:
    skill_dir = _make_skill(tmp_path)
    outside = tmp_path / "outside-secret.txt"
    outside.write_text("do not package", encoding="utf-8")
    (skill_dir / "leak.txt").symlink_to(outside)

    result = package.package_skill(skill_dir, tmp_path / "dist", dry_run=True)

    _assert_safety_block(result, "symbolic link")
    assert "outside-secret.txt" not in "\n".join(result["files_included"])


def test_rejects_directory_symlink_without_traversing_target(tmp_path: Path) -> None:
    skill_dir = _make_skill(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("do not package", encoding="utf-8")
    (skill_dir / "references").symlink_to(outside, target_is_directory=True)

    result = package.package_skill(skill_dir, tmp_path / "dist", dry_run=True)

    _assert_safety_block(result, "symbolic link")
    assert "secret.txt" not in "\n".join(result["files_included"])


@pytest.mark.skipif(not hasattr(os, "link"), reason="hard links are unavailable")
def test_rejects_hard_linked_regular_files(tmp_path: Path) -> None:
    skill_dir = _make_skill(tmp_path)
    original = skill_dir / "original.txt"
    original.write_text("shared inode", encoding="utf-8")
    try:
        os.link(original, skill_dir / "alias.txt")
    except OSError as exc:
        pytest.skip(f"hard links are unavailable on this filesystem: {exc}")

    result = package.package_skill(skill_dir, tmp_path / "dist", dry_run=True)

    _assert_safety_block(result, "hard-linked")


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFOs are unavailable")
def test_rejects_non_regular_files(tmp_path: Path) -> None:
    skill_dir = _make_skill(tmp_path)
    fifo = skill_dir / "input.pipe"
    os.mkfifo(fifo)

    result = package.package_skill(skill_dir, tmp_path / "dist", dry_run=True)

    _assert_safety_block(result, "non-regular")


def test_rejects_traversal_and_member_name_collisions() -> None:
    with pytest.raises(package.PackageSafetyError, match="traversal"):
        package._normalize_member_name("../escape.txt")
    with pytest.raises(package.PackageSafetyError, match="duplicate normalized"):
        package._ensure_unique_member_names([
            "caf\N{LATIN SMALL LETTER E WITH ACUTE}.txt",
            "cafe\N{COMBINING ACUTE ACCENT}.txt",
        ])
    with pytest.raises(package.PackageSafetyError, match="case-insensitive"):
        package._ensure_unique_member_names(["README.md", "readme.MD"])


@pytest.mark.parametrize(
    "member_name",
    [
        "CON",
        "con.txt",
        "folder/NUL.md",
        "name:stream",
        "trailing.",
        "trailing ",
        "control\nname.txt",
    ],
)
def test_rejects_windows_invalid_member_names(member_name: str) -> None:
    with pytest.raises(package.PackageSafetyError):
        package._normalize_member_name(member_name)


def test_rejects_junction_or_reparse_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    skill_dir = _make_skill(tmp_path)
    junction = skill_dir / "references"
    junction.mkdir()
    (junction / "secret.txt").write_text("outside", encoding="utf-8")
    monkeypatch.setattr(package, "_path_is_junction", lambda path: path == junction)

    result = package.package_skill(skill_dir, tmp_path / "dist", dry_run=True)

    _assert_safety_block(result, "junction")


def test_excludes_repo_local_instructions_and_cache_artifacts(tmp_path: Path) -> None:
    skill_dir = _make_skill(tmp_path)
    (skill_dir / "AGENTS.md").write_text("repo-only instructions", encoding="utf-8")
    (skill_dir / ".coverage.local").write_text("cache", encoding="utf-8")
    (skill_dir / ".hypothesis" / "examples").mkdir(parents=True)
    (skill_dir / ".hypothesis" / "examples" / "case").write_text("cache", encoding="utf-8")

    result = package.package_skill(skill_dir, tmp_path / "dist")

    assert not result["errors"]
    assert {"AGENTS.md", ".coverage.local", ".hypothesis"}.issubset(result["files_excluded"])
    with zipfile.ZipFile(result["output_path"]) as archive:
        assert all("AGENTS.md" not in name for name in archive.namelist())
        assert all(".coverage" not in name and ".hypothesis" not in name for name in archive.namelist())


def test_enforces_file_count_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    skill_dir = _make_skill(tmp_path)
    (skill_dir / "extra.txt").write_text("extra", encoding="utf-8")
    monkeypatch.setattr(package, "ASSET_TOOLKIT_SRC", tmp_path / "missing-toolkit")
    monkeypatch.setattr(package, "MAX_ARCHIVE_FILES", 1)

    result = package.package_skill(skill_dir, tmp_path / "dist", dry_run=True)

    _assert_safety_block(result, "file-count limit")


def test_enforces_depth_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    skill_dir = _make_skill(tmp_path)
    nested = skill_dir / "one" / "two"
    nested.mkdir(parents=True)
    (nested / "deep.txt").write_text("deep", encoding="utf-8")
    monkeypatch.setattr(package, "ASSET_TOOLKIT_SRC", tmp_path / "missing-toolkit")
    monkeypatch.setattr(package, "MAX_ARCHIVE_DEPTH", 2)

    result = package.package_skill(skill_dir, tmp_path / "dist", dry_run=True)

    _assert_safety_block(result, "depth limit")


def test_enforces_per_file_byte_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    skill_dir = _make_skill(tmp_path)
    (skill_dir / "large.bin").write_bytes(b"x" * 4096)
    monkeypatch.setattr(package, "ASSET_TOOLKIT_SRC", tmp_path / "missing-toolkit")
    monkeypatch.setattr(package, "MAX_ARCHIVE_FILE_BYTES", 2048)

    result = package.package_skill(skill_dir, tmp_path / "dist", dry_run=True)

    _assert_safety_block(result, "per-file byte limit")


def test_enforces_total_byte_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    skill_dir = _make_skill(tmp_path)
    (skill_dir / "one.bin").write_bytes(b"x" * 1024)
    (skill_dir / "two.bin").write_bytes(b"y" * 1024)
    monkeypatch.setattr(package, "ASSET_TOOLKIT_SRC", tmp_path / "missing-toolkit")
    monkeypatch.setattr(package, "MAX_ARCHIVE_TOTAL_BYTES", len(VALID_SKILL_MD.encode()) + 1500)

    result = package.package_skill(skill_dir, tmp_path / "dist", dry_run=True)

    _assert_safety_block(result, "total byte limit")


def test_generated_manifest_bytes_count_toward_total_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    skill_dir = _make_skill(tmp_path)
    source_bytes = (skill_dir / "SKILL.md").stat().st_size
    toolkit_bytes = sum(
        (package.ASSET_TOOLKIT_SRC / module).stat().st_size for module in package.PORTABLE_TOOLKIT_MODULES
    )
    monkeypatch.setattr(package, "MAX_ARCHIVE_TOTAL_BYTES", source_bytes + toolkit_bytes)

    result = package.package_skill(skill_dir, tmp_path / "dist", dry_run=True)

    _assert_safety_block(result, "total byte limit")


def test_non_string_manifest_metadata_is_structured_safety_error(tmp_path: Path) -> None:
    skill_dir = _make_skill(tmp_path)
    skill_md = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    (skill_dir / "SKILL.md").write_text(
        skill_md.replace("author: tester", "author: 2026-01-01"),
        encoding="utf-8",
    )

    result = package.package_skill(skill_dir, tmp_path / "dist")

    _assert_safety_block(result, "author must be a string")


def test_manifest_covers_source_and_vendored_members_exactly(tmp_path: Path) -> None:
    skill_dir = _make_skill(tmp_path)
    (skill_dir / "scripts").mkdir()
    (skill_dir / "scripts" / "check.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")

    result = package.package_skill(skill_dir, tmp_path / "dist")

    assert not result["errors"]
    with zipfile.ZipFile(result["output_path"]) as archive:
        names = archive.namelist()
        manifest = json.loads(archive.read("secure-pkg/manifest.json"))
    member_names = {name.removeprefix("secure-pkg/") for name in names if name != "secure-pkg/manifest.json"}
    assert set(manifest["files"]) == member_names
    assert any(name.startswith("scripts/asset_toolkit/") for name in manifest["files"])
    assert set(result["files_included"]) == member_names
    assert all("\\" not in name for name in manifest["files"])


def test_zip_entries_have_deterministic_order_and_metadata(tmp_path: Path) -> None:
    skill_dir = _make_skill(tmp_path)
    (skill_dir / "z-last.txt").write_text("z", encoding="utf-8")
    (skill_dir / "a-first.txt").write_text("a", encoding="utf-8")

    result = package.package_skill(skill_dir, tmp_path / "dist")

    assert not result["errors"]
    with zipfile.ZipFile(result["output_path"]) as archive:
        infos = archive.infolist()
    assert [info.filename for info in infos] == sorted(info.filename for info in infos)
    assert {info.date_time for info in infos} == {package.ZIP_TIMESTAMP}
    assert {info.create_system for info in infos} == {3}
    assert {stat.S_IMODE(info.external_attr >> 16) for info in infos} == {0o644}


def test_source_date_epoch_produces_byte_reproducible_archives(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    skill_dir = _make_skill(tmp_path)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1_700_000_000".replace("_", ""))

    first = package.package_skill(skill_dir, tmp_path / "dist-one")
    second = package.package_skill(skill_dir, tmp_path / "dist-two")

    assert not first["errors"]
    assert not second["errors"]
    assert Path(first["output_path"]).read_bytes() == Path(second["output_path"]).read_bytes()
    with zipfile.ZipFile(first["output_path"]) as archive:
        manifest = json.loads(archive.read("secure-pkg/manifest.json"))
    assert manifest["created_at"] == "2023-11-14T22:13:20+00:00"


def test_invalid_source_date_epoch_is_structured_safety_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    skill_dir = _make_skill(tmp_path)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "not-an-integer")

    result = package.package_skill(skill_dir, tmp_path / "dist")

    _assert_safety_block(result, "source_date_epoch")


def test_failed_publish_preserves_existing_archive_and_cleans_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    skill_dir = _make_skill(tmp_path)
    output_dir = tmp_path / "dist"
    output_dir.mkdir()
    destination = output_dir / "secure-pkg-v1.0.0.skill.zip"
    destination.write_bytes(b"previous archive")
    original_read = package._read_regular_file_no_follow
    calls = 0

    def fail_read(member: package.ArchiveMember) -> bytes:
        nonlocal calls
        calls += 1
        if calls > 1:
            raise package.PackageSafetyError("simulated read failure")
        return original_read(member)

    monkeypatch.setattr(package, "_read_regular_file_no_follow", fail_read)

    result = package.package_skill(skill_dir, output_dir)

    assert result["blocked"] is True
    assert "simulated read failure" in "\n".join(result["errors"])
    assert destination.read_bytes() == b"previous archive"
    assert list(output_dir.glob(".secure-pkg-v1.0.0.skill.zip.*.tmp")) == []
