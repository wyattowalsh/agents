"""Tests for Cursor authoritative skill-link ensure (Wave 1a CUR lane)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from wagents.platforms.cursor import (
    CursorAuthoritativeLinksReport,
    ensure_cursor_authoritative_links,
)

if TYPE_CHECKING:
    from pathlib import Path


def _write_skill(root: Path, name: str, body: str) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    return skill_dir


def _roots(tmp_path: Path) -> tuple[Path, Path, Path]:
    home = tmp_path / "home"
    store = home / ".agents" / "skills"
    projection = home / ".cursor" / "skills"
    store.mkdir(parents=True)
    projection.mkdir(parents=True)
    return home, store, projection


def test_missing_projection_creates_symlink_to_store_realpath(tmp_path: Path) -> None:
    home, store, projection = _roots(tmp_path)
    store_dir = _write_skill(store, "alpha", "---\nname: alpha\n---\nbody-a\n")

    report = ensure_cursor_authoritative_links(
        names=["alpha"],
        home=home,
        dry_run=False,
    )

    link = projection / "alpha"
    assert report.created == ("alpha",)
    assert report.repaired == ()
    assert report.already_correct == ()
    assert report.blocked == ()
    assert report.skipped_missing_store == ()
    assert link.is_symlink()
    assert link.resolve() == store_dir.resolve()


def test_dry_run_does_not_create_symlink(tmp_path: Path) -> None:
    home, _store, projection = _roots(tmp_path)
    _write_skill(home / ".agents" / "skills", "alpha", "---\nname: alpha\n---\nbody\n")

    report = ensure_cursor_authoritative_links(names=["alpha"], home=home, dry_run=True)

    assert report.created == ("alpha",)
    assert not (projection / "alpha").exists()
    assert not (projection / "alpha").is_symlink()


def test_broken_symlink_is_repaired(tmp_path: Path) -> None:
    home, store, projection = _roots(tmp_path)
    store_dir = _write_skill(store, "beta", "---\nname: beta\n---\nbody-b\n")
    broken = projection / "beta"
    broken.symlink_to(tmp_path / "missing-target", target_is_directory=True)

    report = ensure_cursor_authoritative_links(names=["beta"], home=home, dry_run=False)

    assert report.repaired == ("beta",)
    assert report.created == ()
    assert broken.is_symlink()
    assert broken.resolve() == store_dir.resolve()


def test_wrong_symlink_is_repaired(tmp_path: Path) -> None:
    home, store, projection = _roots(tmp_path)
    store_dir = _write_skill(store, "gamma", "---\nname: gamma\n---\nbody-g\n")
    other = _write_skill(tmp_path / "other-store", "gamma", "---\nname: gamma\n---\nother\n")
    wrong = projection / "gamma"
    wrong.symlink_to(other.resolve(), target_is_directory=True)

    report = ensure_cursor_authoritative_links(names=["gamma"], home=home, dry_run=False)

    assert report.repaired == ("gamma",)
    assert wrong.resolve() == store_dir.resolve()


def test_correct_symlink_is_already_correct(tmp_path: Path) -> None:
    home, store, projection = _roots(tmp_path)
    store_dir = _write_skill(store, "delta", "---\nname: delta\n---\nbody-d\n")
    link = projection / "delta"
    link.symlink_to(store_dir.resolve(), target_is_directory=True)

    report = ensure_cursor_authoritative_links(names=["delta"], home=home, dry_run=False)

    assert report.already_correct == ("delta",)
    assert report.created == ()
    assert report.repaired == ()
    assert link.resolve() == store_dir.resolve()


def test_real_dir_same_skill_body_is_already_correct(tmp_path: Path) -> None:
    home, store, projection = _roots(tmp_path)
    body = "---\nname: epsilon\n---\nsame-body\n"
    _write_skill(store, "epsilon", body)
    real = _write_skill(projection, "epsilon", body)
    # Extra local file must not force replacement when SKILL.md matches.
    (real / "notes.md").write_text("local\n", encoding="utf-8")

    report = ensure_cursor_authoritative_links(names=["epsilon"], home=home, dry_run=False)

    assert report.already_correct == ("epsilon",)
    assert real.is_dir()
    assert not real.is_symlink()
    assert (real / "notes.md").is_file()


def test_real_dir_divergent_skill_body_is_blocked(tmp_path: Path) -> None:
    home, store, projection = _roots(tmp_path)
    _write_skill(store, "zeta", "---\nname: zeta\n---\nstore-body\n")
    real = _write_skill(projection, "zeta", "---\nname: zeta\n---\nlocal-body\n")
    (real / "keep-me.txt").write_text("do-not-delete\n", encoding="utf-8")

    report = ensure_cursor_authoritative_links(names=["zeta"], home=home, dry_run=False)

    assert report.blocked == (
        {
            "name": "zeta",
            "reason": "real directory with divergent SKILL.md; refusing to replace tree",
        },
    )
    assert real.is_dir()
    assert not real.is_symlink()
    assert (real / "keep-me.txt").read_text(encoding="utf-8") == "do-not-delete\n"


def test_missing_store_skill_is_skipped(tmp_path: Path) -> None:
    home, store, projection = _roots(tmp_path)
    (store / "eta").mkdir()
    # No SKILL.md in store.

    report = ensure_cursor_authoritative_links(names=["eta", "missing"], home=home, dry_run=False)

    assert report.skipped_missing_store == ("eta", "missing")
    assert report.created == ()
    assert not (projection / "eta").exists()


def test_explicit_store_and_projection_roots(tmp_path: Path) -> None:
    store = tmp_path / "custom-store"
    projection = tmp_path / "custom-projection"
    store_dir = _write_skill(store, "theta", "---\nname: theta\n---\nbody-t\n")

    report = ensure_cursor_authoritative_links(
        names=["theta"],
        store_root=store,
        projection_root=projection,
        dry_run=False,
    )

    link = projection / "theta"
    assert report.created == ("theta",)
    assert link.is_symlink()
    assert link.resolve() == store_dir.resolve()


def test_real_file_projection_is_blocked(tmp_path: Path) -> None:
    home, store, projection = _roots(tmp_path)
    _write_skill(store, "iota", "---\nname: iota\n---\nbody-i\n")
    file_path = projection / "iota"
    file_path.write_text("not-a-skill-dir\n", encoding="utf-8")

    report = ensure_cursor_authoritative_links(names=["iota"], home=home, dry_run=False)

    assert report.blocked == (
        {
            "name": "iota",
            "reason": "projection path exists and is not a replaceable symlink",
        },
    )
    assert file_path.is_file()


def test_repair_never_removes_real_tree_on_dry_run(tmp_path: Path) -> None:
    home, store, projection = _roots(tmp_path)
    _write_skill(store, "kappa", "---\nname: kappa\n---\nstore\n")
    real = _write_skill(projection, "kappa", "---\nname: kappa\n---\nlocal\n")

    report = ensure_cursor_authoritative_links(names=["kappa"], home=home, dry_run=True)

    assert report.blocked[0]["name"] == "kappa"
    assert real.is_dir()
    assert (real / "SKILL.md").is_file()


def test_report_type_and_mixed_batch(tmp_path: Path) -> None:
    home, store, projection = _roots(tmp_path)
    _write_skill(store, "ok", "---\nname: ok\n---\nshared\n")
    _write_skill(projection, "ok", "---\nname: ok\n---\nshared\n")
    _write_skill(store, "new", "---\nname: new\n---\nnew\n")
    _write_skill(store, "conflict", "---\nname: conflict\n---\nstore\n")
    _write_skill(projection, "conflict", "---\nname: conflict\n---\nlocal\n")

    report = ensure_cursor_authoritative_links(
        names=["ok", "new", "conflict", "absent"],
        home=home,
        dry_run=False,
    )

    assert isinstance(report, CursorAuthoritativeLinksReport)
    assert report.already_correct == ("ok",)
    assert report.created == ("new",)
    assert report.blocked[0]["name"] == "conflict"
    assert report.skipped_missing_store == ("absent",)
    assert (projection / "new").is_symlink()
