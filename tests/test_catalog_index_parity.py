"""Parity checks for authoring MDX and catalog index SSOT."""

from __future__ import annotations

from wagents.external_skills import read_external_skill_entries
from wagents.skill_index import (
    AUTHORING_SKILLS_DIR,
    build_catalog_index,
    load_authoring_entries,
)


def test_write_catalog_index_roundtrip_external_count() -> None:
    entries = load_authoring_entries()
    if not entries:
        return
    index = build_catalog_index(entries)
    external_rows = index.get("externalSkillIndex") or []
    external_from_authoring = [e for e in entries if e.source_kind != "custom"]
    assert len(external_rows) == len(external_from_authoring)


def test_read_external_skill_entries_non_empty_with_authoring() -> None:
    if not AUTHORING_SKILLS_DIR.exists() or not any(AUTHORING_SKILLS_DIR.glob("*.mdx")):
        return
    rows = read_external_skill_entries()
    assert len(rows) > 0
