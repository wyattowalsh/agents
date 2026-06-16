"""Tests for wagents.catalog_rows — public row builders, curated lookup, and text helpers (3-4 core tests)."""

from wagents.catalog_rows import (
    curated_catalog_parity_gaps,
    curated_entry_by_name,
    entry_to_public_row,
    first_sentence,
    merge_installed_agents,
)
from wagents.external_skills import ExternalSkillEntry, parse_external_skill_entries


def test_curated_entry_by_name_prefers_first_verified_row_for_duplicate_names():
    entries = [
        ExternalSkillEntry(
            name="vitest",
            source="antfu/skills",
            install_source="antfu/skills",
            status="install-now-after-trust-gate",
            trust_tier="low",
            provenance_status="verified-install-command",
            install_command="npx ...",
            target_agents=(),
            source_url="",
            notes="first",
        ),
        ExternalSkillEntry(
            name="vitest",
            source="PaulRBerg/agent-skills",
            install_source="PaulRBerg/agent-skills@abc",
            status="install-now-after-trust-gate",
            trust_tier="low",
            provenance_status="verified-install-command",
            install_command="npx ...",
            target_agents=(),
            source_url="",
            notes="second",
        ),
    ]
    found = curated_entry_by_name(entries, "vitest")
    assert found is not None
    assert found.install_source == "antfu/skills"
    assert found.notes == "first"


def test_curated_entry_by_name_prefers_verified_provenance():
    """Lookup by name should return the verified variant when both unresolved and verified exist."""
    entries = parse_external_skill_entries(
        """
## Install Now After Trust Gate

```bash
npx skills add example/skills --skill demo-skill -y -g -a claude-code
```

## Inspect Then Install

```bash
npx skills add example/skills --skill demo-skill -y -g -a claude-code
```
"""
    )
    found = curated_entry_by_name(entries, "demo-skill")
    assert found is not None
    assert found.provenance_status == "verified-install-command"
    assert found.status == "install-now-after-trust-gate"


def test_entry_to_public_row_includes_full_external_fields_and_badges():
    """entry_to_public_row must emit the expected public row keys and computed badge/status."""
    entry = ExternalSkillEntry(
        name="shieldcn-badges",
        source="jal-co/shieldcn",
        install_source="jal-co/shieldcn",
        status="install-now-after-trust-gate",
        trust_tier="curated-trust-gated",
        provenance_status="verified-install-command",
        install_command="npx skills add jal-co/shieldcn --skill shieldcn-badges -y -g",
        target_agents=("claude-code", "codex"),
        source_url="https://github.com/jal-co/shieldcn",
        notes="Install shieldcn-badges for local badge-generation workflows.",
        risk_notes="Dynamic JSON badge patterns can embed arbitrary external JSON endpoints.",
        promotion_policy="Install only after trust gate; audit again before repo promotion.",
        provenance_evidence=(
            "Curated `npx skills add` command with named `--skill` selectors "
            "under `install-now-after-trust-gate` in config/external-skills.md."
        ),
        selector_mode="named",
        unresolved_reason="",
        unsupported_target_agents=(),
    )
    row = entry_to_public_row(entry)

    assert row["name"] == "shieldcn-badges"
    assert row["sourceType"] == "curated-external"
    assert row["status"] == "install-now-after-trust-gate"
    assert row["trustTier"] == "curated-trust-gated"
    assert row["trustBadge"] == "Curated"
    assert row["trustBadgeVariant"] == "note"
    assert row["installable"] is True
    assert row["selectorMode"] == "named"
    assert row["installedAgents"] == []
    assert "Install only after trust gate" in str(row.get("promotionPolicy", ""))
    assert row.get("riskNotes", "").startswith("Dynamic JSON")
    assert row["sourceUrl"] == "https://github.com/jal-co/shieldcn"
    # knowledge skeleton present
    assert "resourceLinks" in row["knowledge"]


def test_merge_installed_agents_merges_from_node_metadata():
    """merge_installed_agents should union installed agent lists from CatalogNode-style metadata (in place)."""
    row: dict[str, object] = {
        "name": "demo-skill",
        "installedAgents": ["codex"],
        "status": "install-now-after-trust-gate",
    }
    node_metadata = {
        "_skills_installed_agents": ["claude-code", "grok", "codex"],
        "_skills_provenance_status": "verified-curated-external",
        "_skills_source": "jal-co/shieldcn",
    }
    merge_installed_agents(row, node_metadata)

    assert sorted(row["installedAgents"]) == ["claude-code", "codex", "grok"]
    assert row.get("installedProvenanceStatus") == "verified-curated-external"
    assert row.get("installedExternalPath") == "jal-co/shieldcn"


def test_curated_catalog_parity_gaps_reports_repo_superseded_ids():
    """Gaps reporter detects curated entries that are superseded by higher-priority repo custom skills.

    In authoring-SSOT, sync_custom sets source_kind=custom for skills/ names (overwriting any prior
    migrate of same name), so they appear only as custom (not curated-external). To exercise the
    supersede detection without depending on global config/skills overlap state, we patch read
    to inject a colliding entry while letting collect see the real repo custom.
    """
    from pathlib import Path
    from unittest.mock import patch

    from wagents.external_skills import ExternalSkillEntry

    fake_superseded = ExternalSkillEntry(
        name="opencode-ensemble",
        source="example/repo",
        install_source="example/repo",
        status="inspect-then-install",
        trust_tier="needs-inspection",
        provenance_status="explicit-unresolved",
        install_command="",
        target_agents=(),
        source_url="",
        notes="",
        risk_notes="",
        promotion_policy="",
        provenance_evidence="",
        source_path="",
        selector_mode="named",
        unresolved_reason="",
        unsupported_target_agents=(),
    )
    with patch("wagents.catalog_rows.read_external_skill_entries", return_value=[fake_superseded]):
        gaps = curated_catalog_parity_gaps()
    assert "opencode-ensemble" in gaps


def test_first_sentence_skips_abbreviations_and_splits_on_sentence_boundaries():
    """first_sentence must reproduce the abbreviation-safe behavior used elsewhere in the repo."""
    # Abbreviation should not truncate
    assert first_sentence("e.g. explore options for the design") == "e.g. explore options for the design"
    # Standard boundaries
    assert first_sentence("What should we do? Then plan the next steps.") == "What should we do?"
    assert first_sentence("This is broken! We need to fix it.") == "This is broken!"
    assert first_sentence("The system is failing. We need to investigate why.") == "The system is failing."
    # No boundary
    assert first_sentence("no punctuation here") == "no punctuation here"
    # Empty / non-str
    assert first_sentence("") == ""
    assert first_sentence(None) == ""  # type: ignore[arg-type]
