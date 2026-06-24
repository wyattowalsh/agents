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
            "audit_date": "2026-06-23",
            "audited_head": "abc123",
            "pin_policy": "pinned commit preferred",
            "source_list_evidence": "npx skills add owner/repo --list",
            "executable_surface": "No hooks; one helper script.",
            "allowed_tools": "Bash Read",
            "hook_surface": "none",
            "script_surface": "helper.py --json --dry-run",
            "credential_behavior": "No credentials requested.",
            "network_access": "No network access during normal use.",
            "file_access": "Reads workspace files only.",
            "live_action_risk": "No live actions.",
            "risk_category": "low",
            "dedupe_notes": "No overlap with repo-owned skills.",
            "unsupported_target_agents": ["grok"],
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
    assert e.audit_date == "2026-06-23"
    assert e.audited_head == "abc123"
    assert e.source_list_evidence.startswith("npx skills add")
    assert e.executable_surface == "No hooks; one helper script."
    assert e.allowed_tools == "Bash Read"
    assert e.hook_surface == "none"
    assert e.script_surface == "helper.py --json --dry-run"
    assert e.credential_behavior == "No credentials requested."
    assert e.network_access == "No network access during normal use."
    assert e.file_access == "Reads workspace files only."
    assert e.live_action_risk == "No live actions."
    assert e.risk_category == "low"
    assert e.dedupe_notes == "No overlap with repo-owned skills."
    assert e.unsupported_target_agents == ("grok",)


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


def test_build_catalog_index_preserves_curated_audit_fields(tmp_authoring_dir: Path):
    _write_mdx(
        tmp_authoring_dir,
        "ext-audit",
        {
            "name": "ext-audit",
            "description": "External with audit evidence",
            "source_kind": "curated-external",
            "audit_date": "2026-06-23",
            "audited_head": "abc123",
            "pin_policy": "pin where source supports commit refs",
            "no_pin_rationale": "registry source has no commit selector",
            "source_list_evidence": "npx skills add owner/repo --list",
            "executable_surface": "No hooks.",
            "allowed_tools": "Read",
            "hook_surface": "none",
            "script_surface": "none",
            "credential_behavior": "No credential access.",
            "network_access": "No runtime network access.",
            "file_access": "Reads requested files.",
            "live_action_risk": "None.",
            "risk_category": "low",
            "dedupe_notes": "Fold if a repo-owned equivalent appears.",
            "unsupported_target_agents": ["grok"],
        },
    )
    idx = build_catalog_index(load_authoring_entries(tmp_authoring_dir))
    row = idx["externalSkillIndex"][0]
    assert row["auditDate"] == "2026-06-23"
    assert row["auditedHead"] == "abc123"
    assert row["pinPolicy"].startswith("pin where")
    assert row["noPinRationale"].startswith("registry source")
    assert row["sourceListEvidence"].startswith("npx skills add")
    assert row["executableSurface"] == "No hooks."
    assert row["allowedTools"] == "Read"
    assert row["hookSurface"] == "none"
    assert row["scriptSurface"] == "none"
    assert row["credentialBehavior"] == "No credential access."
    assert row["networkAccess"] == "No runtime network access."
    assert row["fileAccess"] == "Reads requested files."
    assert row["liveActionRisk"] == "None."
    assert row["riskCategory"] == "low"
    assert row["dedupeNotes"].startswith("Fold if")
    assert row["unsupportedTargetAgents"] == ["grok"]


def test_external_source_kind_receives_curated_catalog_metadata(tmp_authoring_dir: Path):
    _write_mdx(
        tmp_authoring_dir,
        "external-spelling",
        {
            "name": "external-spelling",
            "description": "External source_kind spelling",
            "source_kind": "external",
            "source": "owner/repo",
            "install_source": "owner/repo@abc123",
            "install_command": "npx skills add owner/repo --skill external-spelling -y -g -a codex",
            "status": "install-now-after-trust-gate",
            "trust_tier": "curated-trust-gated",
            "provenance_status": "verified-install-command",
            "target_agents": ["codex"],
            "audit_date": "2026-06-23",
            "audited_head": "abc123",
            "source_list_evidence": "npx skills add owner/repo --list",
            "dedupe_notes": "No repo-owned overlap.",
            "unsupported_target_agents": ["grok"],
        },
    )
    entry = load_authoring_entries(tmp_authoring_dir)[0]

    idx = build_catalog_index([entry])
    row = idx["externalSkillIndex"][0]
    assert row["sourceType"] == "curated-external"
    assert row["sourceKind"] == "external"
    assert row["installCommand"].startswith("npx skills add owner/repo")
    assert row["targetAgents"] == ["codex"]
    assert row["auditDate"] == "2026-06-23"
    assert row["auditedHead"] == "abc123"
    assert row["sourceListEvidence"].startswith("npx skills add")
    assert row["dedupeNotes"] == "No repo-owned overlap."
    assert row["unsupportedTargetAgents"] == ["grok"]

    node = authoring_entry_to_catalog_node(entry)
    assert node.source == "curated-external"
    assert node.metadata["_skills_install_command"].startswith("npx skills add owner/repo")
    assert node.metadata["_skills_target_agents"] == ["codex"]
    assert node.metadata["_skills_source"] == "owner/repo"
    assert node.metadata["_skills_install_source"] == "owner/repo@abc123"
    assert node.metadata["_skills_provenance_status"] == "verified-install-command"
    assert node.metadata["_skills_trust_tier"] == "curated-trust-gated"
    assert node.metadata["_curated_status"] == "install-now-after-trust-gate"
    assert node.metadata["_audit_date"] == "2026-06-23"
    assert node.metadata["_audited_head"] == "abc123"
    assert node.metadata["_source_list_evidence"].startswith("npx skills add")
    assert node.metadata["_dedupe_notes"] == "No repo-owned overlap."
    assert node.metadata["_unsupported_target_agents"] == ["grok"]


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
            "license_status": "declared",
            "audit_date": "2026-06-23",
            "audited_head": "abc123",
            "executable_surface": "No executable hooks.",
            "dedupe_notes": "No repo-owned overlap.",
        },
    )
    e = load_authoring_entries(tmp_authoring_dir)[0]
    node = authoring_entry_to_catalog_node(e)
    assert node.source == "curated-external"
    assert node.metadata.get("_is_stub") is True  # empty body
    assert node.metadata.get("_skills_source") == "foo/bar"
    assert node.metadata.get("_curated_status") == "inspect-then-install"
    assert node.metadata.get("license_status") == "declared"
    assert node.metadata.get("_audit_date") == "2026-06-23"
    assert node.metadata.get("_audited_head") == "abc123"
    assert node.metadata.get("_executable_surface") == "No executable hooks."
    assert node.metadata.get("_dedupe_notes") == "No repo-owned overlap."


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
