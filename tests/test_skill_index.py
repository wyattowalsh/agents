"""Tests for wagents.skill_index — authoring catalog entries, index build, converters, and I/O."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from wagents.catalog import CatalogNode
from wagents.external_skills import ExternalSkillEntry
from wagents.skill_index import (
    CatalogAuthoringEntry,
    authoring_entry_to_catalog_node,
    build_catalog_index,
    entry_to_external_skill_entry,
    load_authoring_entries,
    read_catalog_index,
    write_catalog_index,
)

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures (tmp paths)
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_authoring_dir(tmp_path: Path) -> Path:
    d = tmp_path / "authoring" / "skills"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def tmp_index_path(tmp_path: Path) -> Path:
    return tmp_path / "generated-registries" / "skills-catalog-index.json"


def _write_mdx(dir_path: Path, name: str, frontmatter: dict, body: str = "") -> Path:
    lines = ["---"]
    for k, v in frontmatter.items():
        if isinstance(v, (list, tuple)):
            # simple inline list for YAML-ish frontmatter used by our parser
            items = ", ".join(str(x) for x in v)
            lines.append(f"{k}: [{items}]")
        else:
            val = str(v).replace('"', '\\"')
            lines.append(f'{k}: "{val}"')
    lines.append("---")
    content = "\n".join(lines) + ("\n\n" + body if body else "\n")
    p = dir_path / f"{name}.mdx"
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# load_authoring_entries
# ---------------------------------------------------------------------------


def test_load_authoring_entries_reads_mdx_with_frontmatter_and_body(tmp_authoring_dir: Path):
    _write_mdx(
        tmp_authoring_dir,
        "demo-skill",
        {"name": "demo-skill", "description": "A demo", "source_kind": "custom"},
        "# Demo\n\nBody text.",
    )
    entries = load_authoring_entries(tmp_authoring_dir)
    assert len(entries) == 1
    e = entries[0]
    assert isinstance(e, CatalogAuthoringEntry)
    assert e.name == "demo-skill"
    assert e.description == "A demo"
    assert e.source_kind == "custom"
    assert "Body text." in e.body
    assert e.path.endswith("demo-skill.mdx")


def test_load_authoring_entries_handles_curated_fields(tmp_authoring_dir: Path):
    _write_mdx(
        tmp_authoring_dir,
        "ext-foo",
        {
            "name": "ext-foo",
            "description": "From external",
            "source_kind": "curated-external",
            "source": "owner/repo",
            "install_command": "npx skills add owner/repo --skill ext-foo",
            "status": "install-now-after-trust-gate",
            "trust_tier": "curated-trust-gated",
            "target_agents": ["claude-code", "codex"],
        },
        "{/* marker */}",
    )
    entries = load_authoring_entries(tmp_authoring_dir)
    assert len(entries) == 1
    e = entries[0]
    assert e.source_kind == "curated-external"
    assert e.source == "owner/repo"
    assert e.install_command.startswith("npx skills add")
    assert e.status == "install-now-after-trust-gate"
    assert e.trust_tier == "curated-trust-gated"
    assert e.target_agents == ("claude-code", "codex")


def test_load_authoring_entries_returns_empty_for_missing_dir(tmp_path: Path):
    missing = tmp_path / "no-such-dir"
    assert load_authoring_entries(missing) == []


# ---------------------------------------------------------------------------
# build_catalog_index
# ---------------------------------------------------------------------------


def test_build_catalog_index_separates_custom_and_external(tmp_authoring_dir: Path):
    _write_mdx(tmp_authoring_dir, "custom-a", {"name": "custom-a", "source_kind": "custom"})
    _write_mdx(
        tmp_authoring_dir,
        "ext-b",
        {"name": "ext-b", "source_kind": "curated-external", "status": "inspect-then-install"},
    )
    entries = load_authoring_entries(tmp_authoring_dir)
    idx = build_catalog_index(entries)
    assert "customSkillIndex" in idx
    assert "externalSkillIndex" in idx
    assert "allSkillIndex" in idx
    custom_names = {r["name"] for r in idx["customSkillIndex"]}
    ext_names = {r["name"] for r in idx["externalSkillIndex"]}
    assert custom_names == {"custom-a"}
    assert ext_names == {"ext-b"}
    # all should contain both
    all_names = {r["name"] for r in idx["allSkillIndex"]}
    assert all_names == {"custom-a", "ext-b"}


# ---------------------------------------------------------------------------
# write/read_catalog_index (roundtrip via tmp path)
# ---------------------------------------------------------------------------


def test_write_and_read_catalog_index_roundtrip(tmp_index_path: Path):
    data = {"customSkillIndex": [{"name": "x"}], "externalSkillIndex": [], "allSkillIndex": [{"name": "x"}]}
    out = write_catalog_index(data, path=tmp_index_path)
    assert out.exists()
    loaded = read_catalog_index(path=tmp_index_path)
    assert loaded is not None
    assert loaded["customSkillIndex"][0]["name"] == "x"


def test_read_catalog_index_returns_none_for_missing(tmp_path: Path):
    assert read_catalog_index(path=tmp_path / "nope.json") is None


# ---------------------------------------------------------------------------
# entry_to_external_skill_entry
# ---------------------------------------------------------------------------


def test_entry_to_external_skill_entry_maps_fields(tmp_authoring_dir: Path):
    _write_mdx(
        tmp_authoring_dir,
        "ext-1",
        {
            "name": "ext-1",
            "source_kind": "curated-external",
            "source": "acme/tools",
            "install_source": "acme/tools@HEAD",
            "install_command": 'npx skills add acme/tools --skill "ext-1"',
            "status": "install-now-after-trust-gate",
            "trust_tier": "curated-trust-gated",
            "target_agents": ["claude-code"],
            "notes": "Use for X.",
        },
    )
    e = load_authoring_entries(tmp_authoring_dir)[0]
    ext = entry_to_external_skill_entry(e)
    assert isinstance(ext, ExternalSkillEntry)
    assert ext.name == "ext-1"
    assert ext.source == "acme/tools"
    assert ext.status == "install-now-after-trust-gate"
    assert ext.trust_tier == "curated-trust-gated"
    assert "acme/tools" in ext.install_command
    assert ext.target_agents == ("claude-code",)


# ---------------------------------------------------------------------------
# authoring_entry_to_catalog_node
# ---------------------------------------------------------------------------


def test_authoring_entry_to_catalog_node_custom_produces_custom_node(tmp_authoring_dir: Path):
    _write_mdx(
        tmp_authoring_dir,
        "my-skill",
        {"name": "my-skill", "description": "Does things", "source_kind": "custom", "license": "MIT"},
        "# My Skill\n\nDetails.",
    )
    e = load_authoring_entries(tmp_authoring_dir)[0]
    node = authoring_entry_to_catalog_node(e)
    assert isinstance(node, CatalogNode)
    assert node.kind == "skill"
    assert node.id == "my-skill"
    assert node.source == "custom"
    assert node.description == "Does things"
    assert "Details." in node.body
    assert node.metadata.get("license") == "MIT"


def test_authoring_entry_to_catalog_node_curated_produces_curated_stub(tmp_authoring_dir: Path):
    _write_mdx(
        tmp_authoring_dir,
        "curated-x",
        {
            "name": "curated-x",
            "source_kind": "curated-external",
            "source": "foo/bar",
            "install_command": "npx ...",
            "status": "inspect-then-install",
            "trust_tier": "needs-inspection",
        },
    )
    e = load_authoring_entries(tmp_authoring_dir)[0]
    node = authoring_entry_to_catalog_node(e)
    assert node.source == "curated-external"
    assert node.metadata.get("_is_stub") is True  # empty body
    assert node.metadata.get("_skills_source") == "foo/bar"
    assert node.metadata.get("_curated_status") == "inspect-then-install"


def test_catalog_index_stale_reason_none_when_index_matches_authoring(tmp_path, monkeypatch):
    from wagents.skill_index import (
        AUTHORING_SKILLS_DIR,
        build_catalog_index,
        catalog_index_stale_reason,
        load_authoring_entries,
        write_catalog_index,
    )

    if not AUTHORING_SKILLS_DIR.exists() or not any(AUTHORING_SKILLS_DIR.glob("*.mdx")):
        return

    entries = load_authoring_entries()
    index_path = tmp_path / "skills-catalog-index.json"
    write_catalog_index(build_catalog_index(entries), path=index_path)
    monkeypatch.setattr("wagents.skill_index.CATALOG_INDEX_PATH", index_path)
    assert catalog_index_stale_reason(index_path) is None
