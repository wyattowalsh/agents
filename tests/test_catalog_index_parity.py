"""Parity between legacy external-skills.md parser and authoring/index SSOT."""

from __future__ import annotations

import wagents
from wagents.external_skills import parse_external_skill_entries_legacy, read_external_skill_entries
from wagents.skill_index import (
    AUTHORING_SKILLS_DIR,
    build_catalog_index,
    load_authoring_entries,
)

EXTERNAL_SKILLS_PATH = wagents.ROOT / "config" / "external-skills.md"


def test_index_external_ids_match_legacy_parser_when_authoring_present() -> None:
    if not AUTHORING_SKILLS_DIR.exists() or not any(AUTHORING_SKILLS_DIR.glob("*.mdx")):
        return
    if not EXTERNAL_SKILLS_PATH.exists():
        return

    legacy_text = EXTERNAL_SKILLS_PATH.read_text(encoding="utf-8")
    legacy_names = {e.name for e in parse_external_skill_entries_legacy(legacy_text)}
    legacy_names.discard("unparsed-command")

    entries = load_authoring_entries()
    authoring_names = {e.name for e in entries}
    curated_external_names = {e.name for e in entries if e.source_kind != "custom"}

    assert curated_external_names, "expected curated-external authoring mdx after migration"
    # Legacy may still list repo-owned custom skills (e.g. opencode-ensemble); any authoring row satisfies parity.
    missing_from_authoring = legacy_names - authoring_names
    assert not missing_from_authoring, f"legacy entries missing from authoring: {sorted(missing_from_authoring)[:10]}"


def test_write_catalog_index_roundtrip_external_count() -> None:
    entries = load_authoring_entries()
    if not entries:
        return
    index = build_catalog_index(entries)
    external_rows = index.get("externalSkillIndex") or []
    external_from_authoring = [e for e in entries if e.source_kind != "custom"]
    assert len(external_rows) == len(external_from_authoring)


def test_read_external_skill_entries_non_empty_with_authoring_or_legacy() -> None:
    rows = read_external_skill_entries()
    if (
        (AUTHORING_SKILLS_DIR.exists() and any(AUTHORING_SKILLS_DIR.glob("*.mdx")))
        or EXTERNAL_SKILLS_PATH.exists()
    ):
        assert len(rows) > 0
