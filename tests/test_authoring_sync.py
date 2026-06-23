"""Tests for wagents.authoring_sync — syncing SKILL.md into authoring mdx with marker comments."""

from __future__ import annotations

from typing import TYPE_CHECKING

from wagents.authoring_sync import (
    GENERATED_MARKER,
    sync_custom_authoring_from_skills,
)
from wagents.parsing import parse_frontmatter
from wagents.skill_index import load_authoring_entries

if TYPE_CHECKING:
    from pathlib import Path


def _write_skill(tmp_repo: Path, name: str, description: str, body: str = "Body.") -> Path:
    d = tmp_repo / "skills" / name
    d.mkdir(parents=True, exist_ok=True)
    content = f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\n{body}\n"
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    return d / "SKILL.md"


def test_sync_custom_authoring_from_skills_writes_mdx_with_custom_kind_and_marker(tmp_repo: Path, tmp_path: Path):
    # Prepare a skill
    _write_skill(tmp_repo, "alpha", "Alpha does things.", "Alpha body here.")

    # Target authoring dir under tmp
    auth_dir = tmp_path / "authoring-skills"
    written = sync_custom_authoring_from_skills(authoring_dir=auth_dir)

    assert len(written) == 1
    p = written[0]
    assert p.exists()
    assert p.name == "alpha.mdx"

    content = p.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)
    assert fm["name"] == "alpha"
    assert fm["description"] == "Alpha does things."
    assert fm["source_kind"] == "custom"

    # Body contains the generated marker pointing to SKILL.md
    marker = GENERATED_MARKER.format(name="alpha")
    assert marker in body
    # And includes the original body content after marker
    assert "Alpha body here." in body


def test_sync_is_idempotent_and_overwrites_canonical_shape(tmp_repo: Path, tmp_path: Path):
    _write_skill(tmp_repo, "beta", "Beta desc.")

    auth_dir = tmp_path / "auth2"
    first = sync_custom_authoring_from_skills(authoring_dir=auth_dir)
    assert len(first) == 1

    # Modify SKILL.md description
    (tmp_repo / "skills" / "beta" / "SKILL.md").write_text(
        "---\nname: beta\ndescription: Updated desc.\n---\n\n# beta\n\nNew body.\n"
    )

    second = sync_custom_authoring_from_skills(authoring_dir=auth_dir)
    assert len(second) == 1
    p = second[0]
    fm, body = parse_frontmatter(p.read_text(encoding="utf-8"))
    assert fm["description"] == "Updated desc."
    assert "New body." in body
    # Marker still present in canonical location
    assert GENERATED_MARKER.format(name="beta") in body


def test_sync_dry_run_does_not_write(tmp_repo: Path, tmp_path: Path):
    _write_skill(tmp_repo, "gamma", "G.")
    auth_dir = tmp_path / "auth-dry"
    targets = sync_custom_authoring_from_skills(authoring_dir=auth_dir, dry_run=True)
    assert len(targets) == 1
    assert not targets[0].exists()


def test_sync_prunes_stale_generated_custom_authoring(tmp_repo: Path, tmp_path: Path):
    _write_skill(tmp_repo, "live", "Live desc.")
    auth_dir = tmp_path / "auth-prune"
    auth_dir.mkdir()
    stale = auth_dir / "stale.mdx"
    stale.write_text(
        f"---\nname: stale\ndescription: stale\nsource_kind: custom\n---\n\n{GENERATED_MARKER.format(name='stale')}\n",
        encoding="utf-8",
    )
    curated = auth_dir / "curated.mdx"
    curated.write_text(
        "---\nname: curated\nsource_kind: curated-external\n---\n\nCurated external entry.\n",
        encoding="utf-8",
    )

    written = sync_custom_authoring_from_skills(authoring_dir=auth_dir)

    assert stale in written
    assert not stale.exists()
    assert curated.exists()
    assert (auth_dir / "live.mdx").exists()


def test_load_synced_authoring_entries_roundtrips_custom(tmp_repo: Path, tmp_path: Path, monkeypatch):
    # Ensure module-level AUTHORING_SKILLS_DIR default doesn't interfere; we pass explicit
    _write_skill(tmp_repo, "delta", "D.")
    auth_dir = tmp_path / "auth-load"
    sync_custom_authoring_from_skills(authoring_dir=auth_dir)

    entries = load_authoring_entries(auth_dir)
    assert len(entries) == 1
    e = entries[0]
    assert e.name == "delta"
    assert e.source_kind == "custom"
    # Body should be present (marker + content)
    assert "Body." in e.body or "D." in e.body
