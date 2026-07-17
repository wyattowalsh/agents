"""Safety and selection tests for the bundled asset-toolkit synchronizer."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skills" / "skill-creator" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import sync_asset_toolkit as sync  # noqa: E402,I001


SKILL_MD = """\
---
name: {name}
description: Sync test skill
---

Body.
"""


def _skills_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    monkeypatch.setattr(sync, "SKILLS_DIR", skills_dir)
    return skills_dir


def _make_skill(skills_dir: Path, name: str) -> Path:
    skill_dir = skills_dir / name
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(SKILL_MD.format(name=name), encoding="utf-8")
    return skill_dir


def _write_stale_module(skill_dir: Path, module: str = "common.py") -> Path:
    toolkit_dir = skill_dir / "scripts" / "asset_toolkit"
    toolkit_dir.mkdir(parents=True, exist_ok=True)
    destination = toolkit_dir / module
    destination.write_text("# stale\n", encoding="utf-8")
    return destination


def test_unknown_skill_id_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    skills_dir = _skills_root(tmp_path, monkeypatch)
    _make_skill(skills_dir, "known-skill")

    rc = sync.main(["--skill-ids", "unknown-skill", "--modules", "common.py", "--check"])

    assert rc == 2
    assert "unknown skill ids" in capsys.readouterr().err


def test_empty_selector_is_rejected_by_argparse() -> None:
    with pytest.raises(SystemExit) as exc_info:
        sync.main(["--skill-ids"])
    assert exc_info.value.code == 2


def test_preflights_all_targets_before_first_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    skills_dir = _skills_root(tmp_path, monkeypatch)
    first = _make_skill(skills_dir, "first-skill")
    stale = _write_stale_module(first)
    second = _make_skill(skills_dir, "second-skill")
    (second / "scripts").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (second / "scripts" / "asset_toolkit").symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlinks are unavailable: {exc}")

    rc = sync.main([
        "--skill-ids",
        "first-skill",
        "second-skill",
        "--modules",
        "common.py",
        "--apply",
    ])

    assert rc == 2
    assert stale.read_text(encoding="utf-8") == "# stale\n"
    assert list(outside.iterdir()) == []


def test_rejects_symlinked_destination_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    skills_dir = _skills_root(tmp_path, monkeypatch)
    skill_dir = _make_skill(skills_dir, "linked-target")
    toolkit_dir = skill_dir / "scripts" / "asset_toolkit"
    toolkit_dir.mkdir(parents=True)
    outside = tmp_path / "outside.py"
    outside.write_text("# sentinel\n", encoding="utf-8")
    try:
        (toolkit_dir / "common.py").symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"file symlinks are unavailable: {exc}")

    rc = sync.main(["--skill-ids", "linked-target", "--modules", "common.py", "--apply"])

    assert rc == 2
    assert outside.read_text(encoding="utf-8") == "# sentinel\n"


def test_atomic_apply_fsyncs_destination_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    skills_dir = _skills_root(tmp_path, monkeypatch)
    skill_dir = _make_skill(skills_dir, "atomic-target")
    destination = _write_stale_module(skill_dir)
    fsynced: list[Path] = []
    monkeypatch.setattr(sync, "_fsync_directory", fsynced.append)

    rc = sync.main(["--skill-ids", "atomic-target", "--modules", "common.py", "--apply"])

    assert rc == 0
    assert destination.read_bytes() == sync._source("common.py").read_bytes()
    assert destination.parent in fsynced
    assert list(destination.parent.glob(".common.py.*.tmp")) == []


def test_junction_preflight_blocks_without_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    skills_dir = _skills_root(tmp_path, monkeypatch)
    skill_dir = _make_skill(skills_dir, "junction-target")
    destination = _write_stale_module(skill_dir)
    toolkit_dir = destination.parent
    monkeypatch.setattr(sync, "_path_is_junction", lambda path: path == toolkit_dir)

    rc = sync.main(["--skill-ids", "junction-target", "--modules", "common.py", "--apply"])

    assert rc == 2
    assert destination.read_text(encoding="utf-8") == "# stale\n"


def test_atomic_publish_rejects_destination_changed_after_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    skills_dir = _skills_root(tmp_path, monkeypatch)
    skill_dir = _make_skill(skills_dir, "concurrent-edit")
    destination = _write_stale_module(skill_dir)
    operation = sync._build_operations([skill_dir], ("common.py",))[0]
    destination.write_text("# user changed this after preflight\n", encoding="utf-8")

    with pytest.raises(sync.SyncSafetyError, match="changed after preflight"):
        sync._atomic_publish(operation)

    assert destination.read_text(encoding="utf-8") == "# user changed this after preflight\n"


def test_atomic_publish_rejects_destination_created_after_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    skills_dir = _skills_root(tmp_path, monkeypatch)
    skill_dir = _make_skill(skills_dir, "concurrent-create")
    operation = sync._build_operations([skill_dir], ("common.py",))[0]
    destination = operation.destination
    destination.parent.mkdir(parents=True)
    destination.write_text("# user created this after preflight\n", encoding="utf-8")

    with pytest.raises(sync.SyncSafetyError, match="appeared after preflight"):
        sync._atomic_publish(operation)

    assert destination.read_text(encoding="utf-8") == "# user created this after preflight\n"
