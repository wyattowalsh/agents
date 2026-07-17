"""Coverage checks for the July 2026 candidate corpus intake."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

from wagents.candidate_corpus_reports import (
    RUNNER_CHECKLIST_HEADING,
    RUNNER_RESULTS_HEADING,
    STANDARD_MUTATION_POLICY,
    TERMINAL_PROMOTION_ASSIGNMENT_RULE,
    TERMINAL_PROMOTION_POLICY,
    TERMINAL_PROMOTION_WAVE_STATUS,
    W00_MUTATION_POLICY,
    W99_MUTATION_POLICY,
    preserve_runner_owned_results,
    render_promotion_wave_report,
    validate_promotion_wave_plan,
)

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
RECORDS_DIR = MANIFEST_DIR / "records"
AUTHORING_DIR = ROOT / "docs" / "src" / "authoring" / "skills"
CATALOG_INDEX = ROOT / "docs" / "public" / "generated-registries" / "skills-catalog-index.json"
CATALOG_DIR = ROOT / "docs" / "src" / "authoring" / "skills"
GENERATED_EXTERNAL_DIR = ROOT / "docs" / "src" / "content" / "docs" / "skills" / "catalog" / "external"
LEGACY_CANDIDATE_PREFIX = "candidate-corpus-"
INTEGRATION_ENTRY_MARKER = "GENERATED-INTEGRATION-TARGET-JUL2026"
EXPECTED_INTEGRATION_CLASSIFICATION_COUNTS = {
    "installable-existing": 121,
    "inspection-existing": 6,
    "integrated-reference": 158,
    "integrated-quarantine-reference": 4,
}
PROMOTION_OVERRIDES = json.loads((MANIFEST_DIR / "promotion-overrides.json").read_text(encoding="utf-8"))["overrides"]
RAW_RESEARCH_SUFFIXES = {
    "URL",
    "LIVE",
    "HEAD",
    "README",
    "LICENSE",
    "PKG",
    "SKILL",
    "MCP",
    "PLUGIN",
    "AGENT",
    "CLI",
    "AUTH",
    "SEC",
    "TOS",
    "IDIO",
    "DEDUPE",
    "ROUTE",
    "PROMOTE",
    "VAL",
}
UNIQUE_SYNTHESIS_SUFFIXES = {"RAW-MAP", "CANON", "SURFACE", "ATTRIB", "AUTH", "INSTALL", "DOCS", "VAL"}

EXPECTED_DUPLICATES = {
    "https://github.com/antonbabenko/terraform-skill",
    "https://github.com/conorluddy/ios-simulator-skill",
    "https://github.com/ramziddin/solid-skills",
    "https://github.com/MohamedAbdallah-14/unslop",
}
PROMOTED_SKILL_NAMES = {override["skill_name"] for override in PROMOTION_OVERRIDES}
PROMOTED_INSTALL_SELECTORS = {
    override["skill_name"]: override.get("install_skill_name", override["skill_name"])
    for override in PROMOTION_OVERRIDES
}
PROMOTED_INSTALLED_PATH_REFS = sum(
    len(override.get("installed_paths", []))
    for override in PROMOTION_OVERRIDES
    if override.get("live_install_executed")
)
TERMINAL_ROW_STATUS_COUNTS = {
    "hard-blocked-quarantine": 4,
    "integrated-existing-surface": 92,
    "integrated-native-surface": 31,
    "integrated-skill-catalog-surface": 27,
    "integrated-collection-surface": 4,
    "integrated-mcp-surface": 8,
    "integrated-plugin-surface": 1,
    "integrated-tool-surface": 1,
}
TERMINAL_DECISIONS = {
    "duplicate_covered",
    "hard_blocked_inaccessible",
    "hard_blocked_quarantine",
    "integrated_collection_surface",
    "integrated_existing_surface",
    "integrated_mcp_surface",
    "integrated_native_surface",
    "integrated_plugin_surface",
    "integrated_skill_catalog_surface",
    "integrated_tool_surface",
}

REQUIRED_RECORD_FIELDS = {
    "raw_url",
    "normalized_url",
    "source_name",
    "category",
    "inspected_commit_sha",
    "license",
    "latest_release_or_commit_date",
    "artifact_types_found",
    "install_or_integration_decision",
    "reason",
    "auth_required",
    "env_vars_or_credentials",
    "safety_notes",
    "attribution_notes",
    "files_added",
    "files_modified",
    "tests_or_checks_run",
    "skipped_reason",
    "reviewer_notes",
    "deep_research_claims",
    "source_support_matrix",
    "docs_steward_surfaces",
    "docs_steward_status",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _terminal_wave_plan(target_url: str | None = None) -> dict:
    target = (
        {
            "normalized_url": target_url,
            "raw_indexes": [1],
            "coverage_status": "needs-promotion-review",
            "risk_tier": "standard-review",
        }
        if target_url
        else None
    )
    waves = [
        {
            "wave_id": "W00",
            "name": "existing-catalog-coverage",
            "target_count": 0,
            "promotion_policy": TERMINAL_PROMOTION_POLICY,
            "mutation_policy": W00_MUTATION_POLICY,
            "targets": [],
        },
        {
            "wave_id": "W08",
            "name": "general-terminal-routing",
            "target_count": 1 if target else 0,
            "promotion_policy": TERMINAL_PROMOTION_POLICY,
            "mutation_policy": STANDARD_MUTATION_POLICY,
            "targets": [target] if target else [],
        },
        {
            "wave_id": "W99",
            "name": "hard-blocked",
            "target_count": 0,
            "promotion_policy": TERMINAL_PROMOTION_POLICY,
            "mutation_policy": W99_MUTATION_POLICY,
            "targets": [],
        },
    ]
    target_count = 1 if target else 0
    return {
        "version": 1,
        "status": TERMINAL_PROMOTION_WAVE_STATUS,
        "wave_count": len(waves),
        "total_targets": target_count,
        "unique_targets_assigned": target_count,
        "raw_entries_covered": target_count,
        "live_install_eligible_count": 0,
        "assignment_rule": TERMINAL_PROMOTION_ASSIGNMENT_RULE,
        "waves": waves,
    }


def _is_trust_cleared_existing_row(row: dict) -> bool:
    has_install_command = bool(row.get("has_install_command")) or bool(str(row.get("install_command", "")).strip())
    sync_kind = str(row.get("sync_kind", "")).strip()
    return (
        has_install_command
        and sync_kind not in {"", "none"}
        and row.get("status") == "install-now-after-trust-gate"
        and row.get("trust_tier") == "curated-trust-gated"
    )


def _existing_rows_are_trust_cleared(rows: list[dict]) -> bool:
    install_surface_rows = [
        row for row in rows if isinstance(row, dict) and (row.get("has_install_command") or row.get("install_command"))
    ]
    return bool(install_surface_rows) and all(_is_trust_cleared_existing_row(row) for row in install_surface_rows)


def _load_generator_module():
    module_name = "_candidate_corpus_generator"
    spec = importlib.util.spec_from_file_location(
        module_name,
        ROOT / "scripts" / "generate_candidate_corpus_shards.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_source_list_audit_module():
    module_name = "_candidate_source_list_auditor"
    spec = importlib.util.spec_from_file_location(
        module_name,
        ROOT / "scripts" / "audit_candidate_source_lists.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_deep_source_audit_module():
    module_name = "_candidate_deep_source_auditor"
    spec = importlib.util.spec_from_file_location(
        module_name,
        ROOT / "scripts" / "audit_candidate_deep_sources.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_promoter_module():
    module_name = "_candidate_corpus_promoter"
    spec = importlib.util.spec_from_file_location(
        module_name,
        ROOT / "scripts" / "promote_candidate_corpus.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_apply_promotions_module():
    module_name = "_candidate_corpus_apply_promotions"
    spec = importlib.util.spec_from_file_location(
        module_name,
        ROOT / "scripts" / "apply_candidate_corpus_promotions.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_terminal_route_note_normalizers_preserve_scalar_string_as_one_note() -> None:
    generator = _load_generator_module()
    apply_promotions = _load_apply_promotions_module()

    assert generator.normalize_source_list_item({"terminal_route_notes": "blocked"})["terminal_route_notes"] == [
        "blocked"
    ]
    assert apply_promotions.normalize_override_record({"terminal_route_notes": "blocked"})["terminal_route_notes"] == [
        "blocked"
    ]


def _valid_promotion_override(**updates):
    payload = {
        "normalized_url": "https://example.test/source",
        "source_name": "example/source",
        "candidate_authoring_name": "candidate-corpus-001-source",
        "skill_name": "source-skill",
        "description": "Reviewed test skill.",
        "install_source": "example/source",
        "install_command": "npx skills add example/source --skill source-skill -y -g -a codex",
        "status": "install-now-after-trust-gate",
        "trust_tier": "curated-trust-gated",
        "sync_kind": "skills-cli",
        "source_list_evidence": "source-list-found",
        "license": "MIT",
        "live_install_executed": True,
        "executed_commands": ["npx skills add example/source --skill source-skill -y -g -a codex"],
        "installed_paths": ["~/.agents/skills/source-skill"],
    }
    payload.update(updates)
    return payload


def test_candidate_corpus_counts_and_duplicates() -> None:
    raw_urls = [
        line.strip()
        for line in (MANIFEST_DIR / "raw-urls.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    normalized = _load_json(MANIFEST_DIR / "normalized-urls.json")
    decisions = _load_json(MANIFEST_DIR / "integration-decisions.json")

    assert len(raw_urls) == 293
    assert normalized["raw_count"] == 293
    assert normalized["unique_count"] == 289
    assert len(decisions["decisions"]) == 289

    duplicate_urls = {url for url in raw_urls if raw_urls.count(url) > 1}
    assert duplicate_urls == EXPECTED_DUPLICATES
    assert len(normalized["duplicate_groups"]) == 4


def test_candidate_records_cover_every_raw_entry() -> None:
    record_paths = sorted(RECORDS_DIR.glob("*.json"))
    assert len(record_paths) == 293
    raw_indexes = []
    for path in record_paths:
        record = _load_json(path)
        assert set(record) >= REQUIRED_RECORD_FIELDS
        assert record["inspected_commit_sha"]
        assert record["docs_steward_surfaces"]
        assert record["source_support_matrix"]
        assert record["tests_or_checks_run"]
        assert record["files_added"]
        assert record["files_modified"]
        assert "human review required before promotion" not in record["reviewer_notes"].lower()
        overlap_packet = record.get("overlap_packet", {})
        if record["install_or_integration_decision"] == "integrated_mcp_surface":
            assert overlap_packet.get("mcp_registry_match") is True
        if record["install_or_integration_decision"] == "integrated_plugin_surface":
            assert overlap_packet.get("plugin_registry_match") is True
        raw_indexes.append(record["raw_index"])
    assert raw_indexes == list(range(1, 294))


def test_mixed_unregistered_mcp_client_routes_to_installed_tool_surface() -> None:
    generator = _load_generator_module()

    decision, _ = generator.decision(
        {"is_duplicate_raw": False, "normalized_url": "https://example.test/inspector"},
        {"status": "ok"},
        ["MCP server", "CLI/tool"],
        "standard-review",
        {"catalog_matches": [], "mcp_registry_match": False, "plugin_registry_match": False},
    )

    assert decision == "integrated_tool_surface"
    assert generator.classify({
        "raw_url": "https://github.com/modelcontextprotocol/inspector",
        "normalized_url": "https://github.com/modelcontextprotocol/inspector",
        "source_name": "modelcontextprotocol/inspector",
        "tree_subpath": "",
    }) == ["CLI/tool"]


def test_integration_target_builder_covers_every_real_identity() -> None:
    generator = _load_generator_module()
    apply_promotions = _load_apply_promotions_module()
    records = _load_json(MANIFEST_DIR / "all-records.json")["records"]
    coverage = _load_json(MANIFEST_DIR / "existing-integration-coverage.json")
    occupied_names, _ = generator._generated_authoring_names()

    targets = generator.build_integration_targets(records, coverage, occupied_names=occupied_names)

    assert targets["unique_targets"] == 289
    assert targets["integrated_targets"] == 289
    assert targets["unintegrated_targets"] == 0
    assert targets["raw_entries_covered"] == 293
    assert targets["generated_reference_count"] == 162
    assert targets["classification_counts"] == EXPECTED_INTEGRATION_CLASSIFICATION_COUNTS
    assert {index for item in targets["items"] for index in item["raw_indexes"]} == set(range(1, 294))
    generated_names = {
        item["generated_reference_name"] for item in targets["items"] if item["generated_reference_name"]
    }
    assert len(generated_names) == 162
    quarantine = [item for item in targets["items"] if item["hard_blocked"]]
    assert len(quarantine) == 4
    assert all(item["integration_classification"] == "integrated-quarantine-reference" for item in quarantine)
    assert all(item["catalog_rows"][0]["has_install_command"] is False for item in quarantine)
    assert apply_promotions.integration_target_errors(targets) == []


def test_stable_integration_names_hash_collisions_truncation_and_occupied_names() -> None:
    generator = _load_generator_module()
    records = [
        {
            "raw_index": 1,
            "normalized_url": "https://example.test/one",
            "source_name": "owner/repository",
            "tree_subpath": "same/path",
        },
        {
            "raw_index": 2,
            "normalized_url": "https://example.test/two",
            "source_name": "owner-repository",
            "tree_subpath": "same-path",
        },
        {
            "raw_index": 3,
            "normalized_url": "https://example.test/long",
            "source_name": "owner/" + "very-long-repository-name-" * 4,
            "tree_subpath": "deep/reference",
        },
        {
            "raw_index": 4,
            "normalized_url": "https://example.test/occupied",
            "source_name": "already/taken",
            "tree_subpath": "",
        },
    ]

    forward = generator.stable_integration_names(records, occupied_names={"already-taken"})
    reverse = generator.stable_integration_names(list(reversed(records)), occupied_names={"already-taken"})

    assert forward == reverse
    assert len(set(forward.values())) == len(records)
    assert all(len(name) <= 64 for name in forward.values())
    assert forward["https://example.test/one"] != "owner-repository-same-path"
    assert forward["https://example.test/two"] != "owner-repository-same-path"
    assert forward["https://example.test/occupied"] != "already-taken"
    assert re.search(r"-[0-9a-f]{10,16}$", forward["https://example.test/long"])


def test_integration_reference_writer_cleans_legacy_markers_and_public_staging_language(tmp_path, monkeypatch) -> None:
    generator = _load_generator_module()
    records = _load_json(MANIFEST_DIR / "all-records.json")["records"]
    coverage = _load_json(MANIFEST_DIR / "existing-integration-coverage.json")
    catalog_dir = tmp_path / "authoring"
    manifest_dir = tmp_path / "manifests"
    catalog_dir.mkdir()
    manifest_dir.mkdir()
    legacy_path = catalog_dir / "candidate-corpus-old.mdx"
    legacy_path.write_text("{/* GENERATED-CANDIDATE-CORPUS-JUL2026 */}\n", encoding="utf-8")
    monkeypatch.setattr(generator, "ROOT", tmp_path)
    monkeypatch.setattr(generator, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(generator, "MANIFEST_DIR", manifest_dir)

    summary = generator.write_catalog_authoring(records, coverage)

    generated_paths = sorted(catalog_dir.glob("*.mdx"))
    integration_targets = _load_json(manifest_dir / "integration-targets.json")
    assert legacy_path.exists() is False
    assert summary["rows_written"] == 162
    assert integration_targets["generated_reference_count"] == 162
    assert len(generated_paths) == 162
    assert not any(path.name.startswith(LEGACY_CANDIDATE_PREFIX) for path in generated_paths)
    for path in generated_paths:
        text = path.read_text(encoding="utf-8")
        assert INTEGRATION_ENTRY_MARKER in text
        assert "candidate corpus" not in text.lower()
        assert "candidate-corpus" not in text.lower()
        assert 'sync_kind: "none"' in text
        assert "install_command:" not in text


def test_auth_matrix_uses_placeholders_only() -> None:
    deep_audit = _load_json(MANIFEST_DIR / "deep-source-audit.json")
    all_records = _load_json(MANIFEST_DIR / "all-records.json")["records"]
    compliance = _load_json(MANIFEST_DIR / "compliance-auth-matrix.json")
    auth_matrix = _load_json(MANIFEST_DIR / "auth-matrix.json")
    deep_by_url = {item["normalized_url"]: item for item in deep_audit["items"]}

    assert len(compliance["items"]) == 293
    assert auth_matrix["items"]
    assert {item["raw_index"] for item in auth_matrix["items"]} == {
        record["raw_index"] for record in all_records if record["auth_required"]
    }
    assert any(
        value != "PLACEHOLDER_ONLY_REVIEW_REQUIRED"
        for item in auth_matrix["items"]
        for value in item["env_vars_or_credentials"]
    )
    for item in auth_matrix["items"]:
        for value in item["env_vars_or_credentials"]:
            assert value == "PLACEHOLDER_ONLY_REVIEW_REQUIRED" or re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", value)
    for record in all_records:
        auth_review = deep_by_url[record["normalized_url"]]["auth_review"]
        assert record["auth_required"] is auth_review["auth_required"]
        expected_env = {
            value for value in auth_review["env_vars_or_credentials"] if value != "PLACEHOLDER_ONLY_REVIEW_REQUIRED"
        }
        assert expected_env <= set(record["env_vars_or_credentials"])
        if not auth_review["auth_required"]:
            assert record["env_vars_or_credentials"] == []


def test_every_unique_target_has_a_real_integration_identity() -> None:
    integration_targets = _load_json(MANIFEST_DIR / "integration-targets.json")
    summary = _load_json(MANIFEST_DIR / "catalog-authoring-summary.json")
    generated_paths = [
        path
        for path in CATALOG_DIR.glob("*.mdx")
        if INTEGRATION_ENTRY_MARKER in path.read_text(encoding="utf-8", errors="replace")
    ]

    assert integration_targets["unique_targets"] == 289
    assert integration_targets["integrated_targets"] == 289
    assert integration_targets["unintegrated_targets"] == 0
    assert integration_targets["raw_entries_covered"] == 293
    assert integration_targets["generated_reference_count"] == 162
    assert integration_targets["classification_counts"] == EXPECTED_INTEGRATION_CLASSIFICATION_COUNTS
    assert len(integration_targets["items"]) == 289
    assert {index for item in integration_targets["items"] for index in item["raw_indexes"]} == set(range(1, 294))
    assert all(item["catalog_rows"] for item in integration_targets["items"])
    assert len(generated_paths) == 162
    assert not list(CATALOG_DIR.glob(f"{LEGACY_CANDIDATE_PREFIX}*.mdx"))

    assert summary["unique_targets"] == 289
    assert summary["install_commands_published"] == len(PROMOTED_SKILL_NAMES)
    assert summary["live_installs_recorded"] == len(PROMOTED_SKILL_NAMES)
    for skill_name in PROMOTED_SKILL_NAMES:
        assert (CATALOG_DIR / f"{skill_name}.mdx").exists()

    normalized = _load_json(MANIFEST_DIR / "normalized-urls.json")
    assert {item["normalized_url"] for item in integration_targets["items"]} == set(normalized["unique_targets"])

    for path in generated_paths:
        text = path.read_text(encoding="utf-8")
        assert "candidate corpus" not in text.lower()
        assert "candidate-corpus" not in text.lower()
        assert 'sync_kind: "none"' in text
        assert "install_command:" not in text


def test_docs_steward_surfaces_are_all_accounted_for() -> None:
    surface_map = _load_json(MANIFEST_DIR / "docs-steward-surface-map.json")
    docs_impact = _load_json(MANIFEST_DIR / "docs-impact-matrix.json")
    decisions_summary = _load_json(MANIFEST_DIR / "integration-decisions.json")["summary"]
    raw_count = decisions_summary["raw_count"]
    surfaces = {entry["surface"]: entry for entry in surface_map["surfaces"]}
    for required in [
        "README",
        "catalog-authoring",
        "catalog-generated",
        "skill-research",
        "mcp-tools",
        "auth-matrix",
        "install-docs",
        "openspec",
        "runbooks",
        "decision-log",
        "changelog",
        "reports",
        "generated-drift",
    ]:
        assert required in surfaces
        assert surfaces[required]["candidate_count"] > 0
    assert "agents-instructions" not in surfaces
    assert "agents-instructions" not in docs_impact["surfaces"]
    assert "agents-instructions" in surface_map["omitted_zero_count_surfaces"]
    assert "agents-instructions" in docs_impact["omitted_zero_count_surfaces"]
    assert all(entry["candidate_count"] > 0 for entry in surface_map["surfaces"])
    for catalog_surface in ["README", "catalog-authoring", "catalog-generated", "skill-research", "install-docs"]:
        assert surfaces[catalog_surface]["candidate_count"] == raw_count


def test_terminal_decision_summary_has_no_legacy_reference_or_skip_decisions() -> None:
    decisions_payload = _load_json(MANIFEST_DIR / "integration-decisions.json")
    summary = decisions_payload["summary"]
    decision_values = {item["decision"] for item in decisions_payload["decisions"]}

    assert "reference" + "_only_count" not in summary
    assert summary["historical_intake_terminal_non_install_count"] == summary["unique_count"]
    assert summary["terminal_non_install_count"] == (
        EXPECTED_INTEGRATION_CLASSIFICATION_COUNTS["integrated-reference"]
        + EXPECTED_INTEGRATION_CLASSIFICATION_COUNTS["integrated-quarantine-reference"]
    )
    assert summary["live_install_added_count"] == len(PROMOTED_SKILL_NAMES)
    assert summary["terminal_integrated_count"] + summary["hard_blocked_count"] == summary["unique_count"]
    assert decision_values <= TERMINAL_DECISIONS
    legacy_decisions = {"reference" + "_only", "quarantine", "skip" + "_inaccessible", "skip" + "_duplicate"}
    assert decision_values.isdisjoint(legacy_decisions)


def test_risk_keyword_matching_is_token_boundary_aware() -> None:
    generator = _load_generator_module()
    spreadsheet_entry = {
        "raw_url": "https://github.com/example/tools/tree/main/spreadsheet-formula-helper",
        "source_name": "example/tools",
        "tree_subpath": "spreadsheet-formula-helper",
    }
    ads_entry = {
        "raw_url": "https://github.com/example/tools/tree/main/competitive-ads-extractor",
        "source_name": "example/tools",
        "tree_subpath": "competitive-ads-extractor",
    }

    spreadsheet_tier, spreadsheet_hits, _ = generator.risk(spreadsheet_entry, ["skill"])
    ads_tier, ads_hits, _ = generator.risk(ads_entry, ["skill"])

    assert spreadsheet_tier == "standard-review"
    assert spreadsheet_hits == []
    assert ads_tier == "quarantine"
    assert "ads" in ads_hits
    assert "competitive-ads" in ads_hits


def test_generated_reports_do_not_claim_unobserved_validation_results() -> None:
    validation_report = (MANIFEST_DIR / "validation-report.md").read_text(encoding="utf-8")
    final_report = (MANIFEST_DIR / "final-review-report.md").read_text(encoding="utf-8")
    docs_summary = (MANIFEST_DIR / "docs-steward-surface-summary.md").read_text(encoding="utf-8")
    changelog = (MANIFEST_DIR / "changelog-entry.md").read_text(encoding="utf-8")
    decision_log = (MANIFEST_DIR / "risky-skipped-deduped-decision-log.md").read_text(encoding="utf-8")

    assert "## Observed Generated Evidence" in validation_report
    assert RUNNER_CHECKLIST_HEADING in validation_report
    assert "does not execute them or claim outcomes" in validation_report
    assert "returned warnings only" not in validation_report
    assert "currently exits 1" not in validation_report
    assert "docs build passes" not in final_report
    assert "corpus-integration-complete" in final_report
    assert "Final commit hash: recorded by the runner" not in final_report
    assert "Final all-agent Skills CLI apply assurance" not in validation_report
    assert "Final all-agent Skills CLI apply assurance" not in final_report
    assert "passed as a no-op" not in validation_report
    assert "passed as a no-op" not in final_report
    generator_owned_report = validation_report.split(RUNNER_RESULTS_HEADING, 1)[0]
    assert re.search(r"\bpassed\b", generator_owned_report, flags=re.IGNORECASE) is None
    assert "- `agents-instructions`: 0 candidates" in docs_summary
    assert "with 0 installs" not in changelog
    assert "Kept all third-party candidates discovery-only" not in changelog
    assert f"Promoted {len(PROMOTION_OVERRIDES)} installable skill rows" in changelog
    assert "Active install blocks: 4" in decision_log
    assert "## Integrated Quarantine References" in decision_log
    assert "## Active Install Blocks" in decision_log


def test_runner_owned_validation_results_are_preserved_without_synthesis() -> None:
    rendered = f"# Validation\n\n{RUNNER_CHECKLIST_HEADING}\n\n> Commands are not executed.\n"
    existing = f"# Old\n\n{RUNNER_RESULTS_HEADING}\n\n- Focused tests passed with runner evidence.\n"

    preserved = preserve_runner_owned_results(rendered, existing)
    without_results = preserve_runner_owned_results(rendered, "# Old\n")

    assert preserved.count(RUNNER_RESULTS_HEADING) == 1
    assert "Focused tests passed with runner evidence." in preserved
    assert RUNNER_RESULTS_HEADING not in without_results
    assert "passed" not in without_results.lower()


def test_integration_target_catalog_rows_replace_staging_rows() -> None:
    integration_targets = _load_json(MANIFEST_DIR / "integration-targets.json")
    catalog_index = _load_json(CATALOG_INDEX)
    indexed_by_name = {row.get("name"): row for row in catalog_index["externalSkillIndex"]}
    staged_rows = [
        row
        for row in catalog_index["externalSkillIndex"]
        if str(row.get("name", "")).startswith(LEGACY_CANDIDATE_PREFIX)
    ]
    promoted_rows = {
        row.get("name"): row for row in catalog_index["externalSkillIndex"] if row.get("name") in PROMOTED_SKILL_NAMES
    }
    generated_references = [item for item in integration_targets["items"] if item["generated_reference_name"]]
    quarantine_references = [item for item in generated_references if item["hard_blocked"]]

    assert staged_rows == []
    assert len(generated_references) == 162
    assert len(quarantine_references) == 4
    assert all(item["generated_reference_name"] in indexed_by_name for item in generated_references)
    for item in generated_references:
        row = indexed_by_name[item["generated_reference_name"]]
        assert row["syncKind"] == "none"
        assert row["status"] == item["integration_classification"]
        assert row.get("installCommand", "") == ""
        assert row.get("useCommand", "") == ""
    for item in quarantine_references:
        assert item["integration_classification"] == "integrated-quarantine-reference"
        assert item["trust_cleared_installable"] is False
        assert item["catalog_rows"][0]["has_install_command"] is False
        assert indexed_by_name[item["generated_reference_name"]]["trustTier"] == "hard-blocked"

    assert set(promoted_rows) == PROMOTED_SKILL_NAMES
    for skill_name, promoted_row in promoted_rows.items():
        assert promoted_row["syncKind"] == "skills-cli"
        assert promoted_row["status"] == "install-now-after-trust-gate"
        assert promoted_row["installCommand"].startswith("npx skills add ")
        assert f"--skill {PROMOTED_INSTALL_SELECTORS[skill_name]}" in promoted_row["installCommand"]
    assert not list(GENERATED_EXTERNAL_DIR.glob(f"{LEGACY_CANDIDATE_PREFIX}*.mdx"))
    for skill_name in PROMOTED_SKILL_NAMES:
        generated_page = GENERATED_EXTERNAL_DIR / f"{skill_name}.mdx"
        text = generated_page.read_text(encoding="utf-8")
        assert "SkillPageHeader" in text
        assert "Harness Coverage" in text
        assert "Portable multi-harness install command" in text
        assert "Trust / Audit" in text
        assert f"--skill {PROMOTED_INSTALL_SELECTORS[skill_name]}" in text


def test_github_metadata_audit_covers_unique_sources() -> None:
    audit = _load_json(MANIFEST_DIR / "github-metadata-audit.json")
    records = _load_json(MANIFEST_DIR / "all-records.json")["records"]

    unique_sources = {record["canonical_source"] or record["source_name"] for record in records}
    assert audit["source_count"] == len(unique_sources)
    assert sum(audit["status_counts"].values()) == audit["source_count"]

    by_source = {item["source"].lower(): item for item in audit["items"]}
    cloudflare = by_source["https://github.com/cloudflare/skills"]
    assert cloudflare["status"] == "ok"
    assert cloudflare["default_branch"]
    assert cloudflare["pushed_at"]
    assert not cloudflare["license"].startswith("not-fetched")

    record_7 = next(record for record in records if record["raw_index"] == 7)
    assert record_7["github_metadata_packet"]["status"] == "ok"
    assert record_7["license"] == cloudflare["license"]
    assert "gh api repos/cloudflare/skills" in record_7["tests_or_checks_run"]


def test_candidate_corpus_coverage_cli() -> None:
    result = subprocess.run(
        ["uv", "run", "python", "scripts/generate_candidate_corpus_shards.py", "--check-coverage"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload == {"raw": 293, "unique": 289, "records": 293, "decisions": 289, "ok": True}


def test_full_integration_research_task_graph_covers_every_lane() -> None:
    graph = _load_json(MANIFEST_DIR / "research-task-graph.json")
    normalized = _load_json(MANIFEST_DIR / "normalized-urls.json")

    assert graph["raw_lane_count"] == 293
    assert graph["unique_target_lane_count"] == 289
    assert graph["raw_leaf_check_count"] == 293 * 19
    assert graph["unique_leaf_check_count"] == 289 * 8
    assert graph["total_leaf_check_count"] == (293 * 19) + (289 * 8)
    assert graph["live_install_eligible_count"] == 0

    raw_lanes = graph["raw_lanes"]
    assert [lane["raw_index"] for lane in raw_lanes] == list(range(1, 294))
    assert {lane["raw_url"] for lane in raw_lanes} == {entry["raw_url"] for entry in normalized["entries"]}
    assert {lane["normalized_url"] for lane in raw_lanes} == set(normalized["unique_targets"])

    for lane in raw_lanes:
        assert lane["live_install_eligible"] is False
        assert {leaf["suffix"] for leaf in lane["leaf_checks"]} == RAW_RESEARCH_SUFFIXES
        assert len(lane["leaf_checks"]) == len(RAW_RESEARCH_SUFFIXES)
        assert any(leaf["status"] == "terminal-non-install-surface" for leaf in lane["leaf_checks"])

    unique_lanes = graph["unique_target_lanes"]
    assert {lane["normalized_url"] for lane in unique_lanes} == set(normalized["unique_targets"])
    for lane in unique_lanes:
        assert lane["live_install_eligible"] is False
        if lane["existing_integration_status"] == "covered-by-existing-installable-catalog":
            assert lane["terminal_decision_status"] == "covered-by-existing-catalog"
        else:
            assert lane["terminal_decision_status"] in TERMINAL_ROW_STATUS_COUNTS
        assert {leaf["suffix"] for leaf in lane["leaf_checks"]} == UNIQUE_SYNTHESIS_SUFFIXES
        assert len(lane["leaf_checks"]) == len(UNIQUE_SYNTHESIS_SUFFIXES)


def test_full_integration_progress_and_packet_schema_are_trust_gated() -> None:
    progress = _load_json(MANIFEST_DIR / "full-integration-progress.json")
    schema = _load_json(MANIFEST_DIR / "research-packet-schema.json")
    coverage = _load_json(MANIFEST_DIR / "existing-integration-coverage.json")
    readiness = _load_json(MANIFEST_DIR / "promotion-readiness-queue.json")
    preview = _load_json(MANIFEST_DIR / "live-install-command-preview.json")
    state_report = (MANIFEST_DIR / "full-integration-state.md").read_text(encoding="utf-8")
    covered_existing = coverage["summary"]["covered-by-existing-installable-catalog"]
    readiness_summary = readiness["summary"]

    assert progress["phase"] == "corpus-integration-complete"
    assert progress["complete"] is True
    assert "Complete for the July 2026 corpus" in progress["completion_scope"]
    assert all(progress["completion_checks"].values())
    assert progress["completion_errors"] == []
    assert progress["raw_candidates"] == 293
    assert progress["unique_normalized_targets"] == 289
    assert progress["live_install"]["eligible_count"] == preview["command_count"] == 0
    assert progress["live_install"]["status"] == preview["status"] == "no-live-install-commands-emitted"
    assert progress["live_install"]["installed_skill_rows"] == len(PROMOTED_SKILL_NAMES)
    assert progress["live_install"]["recorded_install_evidence_rows"] == len(PROMOTED_SKILL_NAMES)
    assert progress["live_install"]["new_live_install_commands_emitted"] == 0
    assert progress["live_install"]["installed_path_refs"] == PROMOTED_INSTALLED_PATH_REFS
    assert progress["live_install"]["verified_skill_md_count"] == PROMOTED_INSTALLED_PATH_REFS
    assert progress["live_install"]["missing_skill_md_count"] == 0
    assert progress["promotion_readiness"]["covered_by_existing_installable_catalog"] == covered_existing
    assert (
        progress["promotion_readiness"]["covered_by_existing_installable_catalog"]
        == (readiness_summary["covered_by_existing_installable_catalog"])
    )
    assert readiness_summary["ready_for_repo_promotion"] == 0
    assert readiness_summary["ready_for_live_install"] == 0
    assert progress["promotion_readiness"]["ready_for_repo_promotion"] == 0
    assert progress["promotion_readiness"]["ready_for_live_install"] == 0
    assert (
        progress["promotion_readiness"]["terminal_native_or_hard_blocked"]
        == (readiness_summary["terminal_native_or_hard_blocked"])
    )
    assert progress["promotion_readiness"]["promoted_installable_rows"] == len(PROMOTED_SKILL_NAMES)
    assert progress["promotion_readiness"]["recorded_install_evidence_rows"] == len(PROMOTED_SKILL_NAMES)
    assert progress["promotion_readiness"]["terminal_non_install_rows"] == 162
    assert progress["terminal_decisions"] == {
        "raw_candidates_processed": 293,
        "unique_normalized_targets": 289,
        "installable_curated_rows": len(PROMOTED_SKILL_NAMES),
        "live_installs_recorded": len(PROMOTED_SKILL_NAMES),
        "new_live_install_commands_emitted": 0,
        "terminal_non_install_rows": 162,
        "duplicate_raw_groups": 4,
        "conservative_intake_hard_blocks": 4,
        "integrated_targets": 289,
        "unintegrated_targets": 0,
        "integration_classification_counts": EXPECTED_INTEGRATION_CLASSIFICATION_COUNTS,
        "integrated_quarantine_targets": 4,
        "active_install_blocks": 4,
    }

    required_fields = {
        "raw_index",
        "raw_url",
        "normalized_url",
        "source_name",
        "inspected_commit_sha",
        "license",
        "artifact_types_found",
        "auth_required",
        "env_vars_or_credentials",
        "security_notes",
        "attribution_notes",
        "surface_decision",
        "live_install_eligible",
        "docs_steward_surfaces",
        "tests_or_checks_run",
        "reviewer_notes",
    }
    assert set(schema["required_packet_fields"]) >= required_fields
    assert set(schema["raw_leaf_check_suffixes"]) == RAW_RESEARCH_SUFFIXES
    assert set(schema["unique_synthesis_leaf_check_suffixes"]) == UNIQUE_SYNTHESIS_SUFFIXES
    assert "corpus-integration-complete" in state_report
    assert "Complete: `true`" in state_report
    assert "Live install eligible: 0" in state_report
    assert (
        f"Installed path references verified: {PROMOTED_INSTALLED_PATH_REFS}/{PROMOTED_INSTALLED_PATH_REFS}"
        in state_report
    )
    assert "Ready for repo promotion: 0" in state_report
    assert f"Promoted installable catalog rows: {len(PROMOTED_SKILL_NAMES)}" in state_report
    assert "Install-root verification found 0 missing `SKILL.md` files" in state_report


def test_subagent_wave_queue_covers_every_raw_entry_read_only() -> None:
    wave_queue = _load_json(MANIFEST_DIR / "subagent-wave-queue.json")

    assert wave_queue["status"] == "ready-for-read-only-subagent-dispatch"
    assert wave_queue["covered_raw_count"] == 293
    assert wave_queue["covered_raw_indexes"] == list(range(1, 294))
    assert wave_queue["micro_wave_count"] == 6
    assert wave_queue["domain_wave_count"] >= 20

    micro_indexes = [index for wave in wave_queue["micro_waves"] for index in wave["raw_indexes"]]
    domain_indexes = [index for wave in wave_queue["domain_waves"] for index in wave["raw_indexes"]]
    assert sorted(micro_indexes) == list(range(1, 294))
    assert sorted(domain_indexes) == list(range(1, 294))
    assert all(wave["mode"] == "parallel-read-only" for wave in wave_queue["domain_waves"])
    assert all("root integrator" in wave["mutation_policy"] for wave in wave_queue["domain_waves"])


def test_promotion_readiness_queue_records_terminal_native_and_hard_block_routes() -> None:
    readiness = _load_json(MANIFEST_DIR / "promotion-readiness-queue.json")
    progress = _load_json(MANIFEST_DIR / "full-integration-progress.json")
    covered_existing = len(readiness["covered_by_existing_installable_catalog"])
    terminal_count = len(readiness["terminal_native_or_hard_blocked"])

    assert readiness["status"] == "terminal-integration-reconciled"
    assert readiness["summary"] == {
        "unique_targets": 289,
        "covered_by_existing_installable_catalog": covered_existing,
        "ready_for_repo_promotion": 0,
        "ready_for_live_install": 0,
        "terminal_native_or_hard_blocked": terminal_count,
    }
    assert readiness["ready_for_repo_promotion"] == []
    assert readiness["ready_for_live_install"] == []
    assert covered_existing + terminal_count == 289
    assert progress["promotion_readiness"]["covered_by_existing_installable_catalog"] == covered_existing
    assert progress["promotion_readiness"]["ready_for_repo_promotion"] == 0
    assert progress["promotion_readiness"]["ready_for_live_install"] == 0
    assert progress["promotion_readiness"]["promoted_installable_rows"] == len(PROMOTED_SKILL_NAMES)
    assert progress["promotion_readiness"]["recorded_install_evidence_rows"] == len(PROMOTED_SKILL_NAMES)
    assert progress["promotion_readiness"]["terminal_non_install_rows"] == 162
    assert progress["promotion_readiness"]["promoted_unique_targets"] >= 1

    for item in readiness["covered_by_existing_installable_catalog"]:
        assert item["terminal_status"] == "covered-by-existing-installable-catalog"
        assert item["live_install_eligible"] is False
        assert item["repo_mutation_eligible"] is False
        assert item["install_command"] == ""
        assert item["existing_rows"]
        assert _existing_rows_are_trust_cleared(item["existing_rows"])
        assert item["terminal_route_requirements"] == []

    for item in readiness["terminal_native_or_hard_blocked"]:
        assert item["terminal_status"] in TERMINAL_ROW_STATUS_COUNTS
        assert item["live_install_eligible"] is False
        assert item["repo_mutation_eligible"] is False
        assert item["install_command"] == ""
        assert "use repo-native MCP/plugin/tool/catalog surfaces" in item["terminal_route_requirements"]

    terraform = next(
        item
        for item in readiness["terminal_native_or_hard_blocked"]
        if item["source_name"].lower() == "antonbabenko/terraform-skill"
    )
    assert terraform["existing_integration_status"] == "covered-by-existing-inspection-required"
    assert terraform["terminal_status"] == "integrated-existing-surface"
    assert "preserve attribution and license notes" in terraform["terminal_route_requirements"]
    assert terraform["existing_rows"]
    assert not _existing_rows_are_trust_cleared(terraform["existing_rows"])


def test_existing_integration_coverage_maps_exact_curated_rows() -> None:
    coverage = _load_json(MANIFEST_DIR / "existing-integration-coverage.json")
    graph = _load_json(MANIFEST_DIR / "research-task-graph.json")
    decisions = _load_json(MANIFEST_DIR / "integration-decisions.json")

    assert coverage["summary"]["covered-by-existing-installable-catalog"] > 0
    assert coverage["summary"]["needs-promotion-review"] > 0
    assert sum(coverage["summary"].values()) == 289
    assert graph["existing_integration_summary"] == coverage["summary"]

    by_source = {item["source_name"].lower(): item for item in coverage["items"]}
    for source in [
        "cloudflare/skills",
        "supabase/agent-skills",
        "avdlee/swift-concurrency-agent-skill",
    ]:
        item = by_source[source]
        assert item["coverage_status"] == "covered-by-existing-installable-catalog"
        assert item["existing_rows"]
        assert _existing_rows_are_trust_cleared(item["existing_rows"])

    terraform = by_source["antonbabenko/terraform-skill"]
    assert terraform["coverage_status"] == "covered-by-existing-inspection-required"
    assert terraform["existing_rows"]
    assert any(row["status"] == "inspect-then-install" for row in terraform["existing_rows"])
    assert any(row["trust_tier"] == "needs-inspection" for row in terraform["existing_rows"])
    assert not _existing_rows_are_trust_cleared(terraform["existing_rows"])

    by_decision_url = {item["normalized_url"].lower(): item for item in decisions["decisions"]}
    needs_promotion = [item for item in coverage["items"] if item["coverage_status"] == "needs-promotion-review"]
    assert needs_promotion
    for item in needs_promotion[:3]:
        assert item["coverage_status"] == "needs-promotion-review"
        assert item["existing_rows"] == []
        assert by_decision_url[item["normalized_url"].lower()]["decision"] in TERMINAL_DECISIONS
    for source in ["wordpress/agent-skills", "tanstack/cli", "dimillian/skills"]:
        item = by_source[source]
        assert item["coverage_status"] == "covered-by-existing-installable-catalog"
        assert item["existing_rows"]
        assert _existing_rows_are_trust_cleared(item["existing_rows"])

    by_url = {lane["normalized_url"].lower(): lane for lane in graph["unique_target_lanes"]}
    cloudflare = by_url["https://github.com/cloudflare/skills"]
    assert cloudflare["existing_integration_status"] == "covered-by-existing-installable-catalog"
    assert cloudflare["terminal_decision_status"] == "covered-by-existing-catalog"


def test_existing_integration_coverage_distinguishes_trust_cleared_from_inspection_required(monkeypatch) -> None:
    generator = _load_generator_module()
    monkeypatch.setattr(
        generator,
        "catalog_authoring_rows",
        lambda: [
            {
                "name": "trusted",
                "path": "trusted.mdx",
                "source": "trusted/source",
                "install_source": "trusted/source",
                "source_url": "https://github.com/trusted/source",
                "install_command": "npx skills add trusted/source --skill trusted -y -g -a codex",
                "status": "install-now-after-trust-gate",
                "trust_tier": "curated-trust-gated",
                "sync_kind": "skills-cli",
            },
            {
                "name": "needs-inspection",
                "path": "needs-inspection.mdx",
                "source": "inspect/source",
                "install_source": "inspect/source",
                "source_url": "https://github.com/inspect/source",
                "install_command": "npx skills add inspect/source --skill inspect -y -g -a codex",
                "status": "inspect-then-install",
                "trust_tier": "needs-inspection",
                "sync_kind": "skills-cli",
            },
            {
                "name": "terminal-row",
                "path": "terminal-row.mdx",
                "source": "terminal/source",
                "install_source": "terminal/source",
                "source_url": "https://github.com/terminal/source",
                "install_command": "",
                "status": "integrated-native-surface",
                "trust_tier": "curated-trust-gated",
                "sync_kind": "none",
            },
        ],
    )
    records = [
        {
            "raw_index": 1,
            "source_name": "trusted/source",
            "normalized_url": "https://github.com/trusted/source",
            "tree_subpath": "",
            "canonical_source": "https://github.com/trusted/source",
            "install_or_integration_decision": "integrated_existing_surface",
        },
        {
            "raw_index": 2,
            "source_name": "inspect/source",
            "normalized_url": "https://github.com/inspect/source",
            "tree_subpath": "",
            "canonical_source": "https://github.com/inspect/source",
            "install_or_integration_decision": "integrated_existing_surface",
        },
        {
            "raw_index": 3,
            "source_name": "terminal/source",
            "normalized_url": "https://github.com/terminal/source",
            "tree_subpath": "",
            "canonical_source": "https://github.com/terminal/source",
            "install_or_integration_decision": "integrated_native_surface",
        },
    ]

    coverage = generator.build_existing_integration_coverage(records)

    by_source = {item["source_name"]: item for item in coverage["items"]}
    assert by_source["trusted/source"]["coverage_status"] == "covered-by-existing-installable-catalog"
    assert by_source["inspect/source"]["coverage_status"] == "covered-by-existing-inspection-required"
    assert by_source["terminal/source"]["coverage_status"] == "covered-by-existing-reference"


def test_tree_target_coverage_requires_exact_subresource_source_url(monkeypatch) -> None:
    generator = _load_generator_module()
    exact_url = "https://github.com/example/skills/tree/main/skills/exact"
    monkeypatch.setattr(
        generator,
        "catalog_authoring_rows",
        lambda: [
            {
                "name": "unrelated",
                "path": "unrelated.mdx",
                "source": "example/skills",
                "install_source": "example/skills",
                "source_url": "https://github.com/example/skills/tree/main/skills/unrelated",
                "install_command": "npx skills add example/skills --skill unrelated -y -g -a codex",
                "status": "install-now-after-trust-gate",
                "trust_tier": "curated-trust-gated",
                "sync_kind": "skills-cli",
            },
            {
                "name": "exact",
                "path": "exact.mdx",
                "source": "example/skills",
                "install_source": "example/skills",
                "source_url": exact_url,
                "install_command": "npx skills add example/skills --skill exact -y -g -a codex",
                "status": "install-now-after-trust-gate",
                "trust_tier": "curated-trust-gated",
                "sync_kind": "skills-cli",
            },
        ],
    )
    records = [
        {
            "raw_index": 1,
            "source_name": "example/skills",
            "normalized_url": exact_url,
            "tree_subpath": "skills/exact",
            "canonical_source": "https://github.com/example/skills",
            "install_or_integration_decision": "integrated_existing_surface",
        }
    ]

    coverage = generator.build_existing_integration_coverage(records)

    assert [row["name"] for row in coverage["items"][0]["existing_rows"]] == ["exact"]


def test_promotion_readiness_keeps_inspection_required_existing_rows_blocked() -> None:
    generator = _load_generator_module()
    decisions = [
        {
            "normalized_url": "https://github.com/inspect/source",
            "source_name": "inspect/source",
            "raw_indexes": [1],
            "decision": "integrated_existing_surface",
        }
    ]
    graph = {
        "unique_target_lanes": [
            {
                "lane_id": "N001",
                "normalized_url": "https://github.com/inspect/source",
                "existing_integration_status": "covered-by-existing-inspection-required",
                "existing_rows": [
                    {
                        "name": "inspect",
                        "status": "inspect-then-install",
                        "trust_tier": "needs-inspection",
                        "has_install_command": True,
                        "sync_kind": "skills-cli",
                    }
                ],
                "risk_tier": "standard-review",
                "auth_required": False,
            }
        ]
    }

    readiness = generator.build_promotion_readiness_queue(decisions, graph)

    assert readiness["covered_by_existing_installable_catalog"] == []
    assert readiness["summary"]["covered_by_existing_installable_catalog"] == 0
    assert readiness["summary"]["terminal_native_or_hard_blocked"] == 1
    terminal = readiness["terminal_native_or_hard_blocked"][0]
    assert terminal["terminal_status"] == "integrated-existing-surface"
    assert terminal["existing_rows"]
    assert "preserve attribution and license notes" in terminal["terminal_route_requirements"]


def test_promotion_wave_plan_assigns_every_unique_target_once() -> None:
    coverage = _load_json(MANIFEST_DIR / "existing-integration-coverage.json")
    wave_plan = _load_json(MANIFEST_DIR / "promotion-wave-plan.json")
    wave_plan_report = (MANIFEST_DIR / "promotion-wave-plan.md").read_text(encoding="utf-8")
    progress = _load_json(MANIFEST_DIR / "full-integration-progress.json")

    assert validate_promotion_wave_plan(wave_plan) == []
    assert wave_plan_report == render_promotion_wave_report(wave_plan)
    assert wave_plan["status"] == TERMINAL_PROMOTION_WAVE_STATUS
    assert wave_plan["assignment_rule"] == TERMINAL_PROMOTION_ASSIGNMENT_RULE
    assert wave_plan["live_install_eligible_count"] == 0
    assert wave_plan["total_targets"] == 289
    assert sum(wave["target_count"] for wave in wave_plan["waves"]) == 289
    assert progress["promotion_waves"] == {
        wave["wave_id"]: wave["target_count"] for wave in wave_plan["waves"] if wave["target_count"]
    }

    assigned_urls = [target["normalized_url"] for wave in wave_plan["waves"] for target in wave["targets"]]
    assert len(assigned_urls) == len(set(assigned_urls)) == 289

    by_wave = {wave["wave_id"]: wave for wave in wave_plan["waves"]}
    assert by_wave["W00"]["target_count"] == coverage["summary"]["covered-by-existing-installable-catalog"]
    assert by_wave["W00"]["mutation_policy"] == W00_MUTATION_POLICY
    assert by_wave["W99"]["mutation_policy"] == W99_MUTATION_POLICY
    assert (
        sum(wave["target_count"] for wave in wave_plan["waves"][1:])
        == 289 - coverage["summary"]["covered-by-existing-installable-catalog"]
    )
    expected_nonempty_waves = {
        "W01",
        "W02",
        "W03",
        "W04",
        "W05",
        "W06",
        "W07",
        "W08",
    }
    assert expected_nonempty_waves.issubset({wave["wave_id"] for wave in wave_plan["waves"] if wave["target_count"]})
    assert "W99" in by_wave
    assert by_wave["W99"]["target_count"] == 4
    assert all(target["risk_tier"] == "quarantine" for target in by_wave["W99"]["targets"])
    assert all(
        target["coverage_status"] == "covered-by-existing-installable-catalog" for target in by_wave["W00"]["targets"]
    )
    assert "https://github.com/antonbabenko/terraform-skill" not in {
        target["normalized_url"] for target in by_wave["W00"]["targets"]
    }
    for wave in wave_plan["waves"]:
        raw_indexes = sorted({index for target in wave["targets"] for index in target["raw_indexes"]})
        coverage_counts: dict[str, int] = {}
        risk_counts: dict[str, int] = {}
        for target in wave["targets"]:
            assert "risk_tier" in target
            coverage_counts[target["coverage_status"]] = coverage_counts.get(target["coverage_status"], 0) + 1
            risk_counts[target["risk_tier"]] = risk_counts.get(target["risk_tier"], 0) + 1
        assert wave["raw_indexes"] == raw_indexes
        assert wave["raw_entry_count"] == len(raw_indexes)
        assert wave["unique_target_count"] == wave["target_count"]
        assert len(wave["lanes"]) == wave["target_count"]
        assert wave["coverage_status_counts"] == dict(sorted(coverage_counts.items()))
        assert wave["risk_tier_counts"] == dict(sorted(risk_counts.items()))
        assert wave["promotion_policy"] == TERMINAL_PROMOTION_POLICY
        if wave["targets"]:
            assert "unclassified" not in wave["risk_tier_counts"]
        assert f"### {wave['wave_id']} {wave['name']}" in wave_plan_report
        assert f"- Unique targets: {wave['target_count']}" in wave_plan_report
        assert f"- Raw entries: {len(raw_indexes)}" in wave_plan_report
        coverage = ", ".join(f"{key}={value}" for key, value in sorted(coverage_counts.items())) or "none"
        risks = ", ".join(f"{key}={value}" for key, value in sorted(risk_counts.items())) or "none"
        assert f"- Coverage: {coverage}" in wave_plan_report
        assert f"- Risk tiers: {risks}" in wave_plan_report
        assert f"- Promotion policy: {TERMINAL_PROMOTION_POLICY}" in wave_plan_report
        assert f"- Mutation policy: {wave['mutation_policy']}" in wave_plan_report


def test_generator_builds_the_canonical_terminal_wave_contract() -> None:
    generator = _load_generator_module()
    records = _load_json(MANIFEST_DIR / "all-records.json")["records"]
    graph = _load_json(MANIFEST_DIR / "research-task-graph.json")

    plan = generator.build_promotion_wave_plan(records, graph)

    assert validate_promotion_wave_plan(plan) == []
    by_wave = {wave["wave_id"]: wave for wave in plan["waves"]}
    assert by_wave["W00"]["mutation_policy"] == W00_MUTATION_POLICY
    assert by_wave["W99"]["mutation_policy"] == W99_MUTATION_POLICY


def test_promotion_wave_renderer_is_strict_but_preserves_optional_fallbacks() -> None:
    plan = _terminal_wave_plan("https://example.test/source")

    report = render_promotion_wave_report(plan)

    assert "- Raw entries: 1" in report
    assert "- Coverage: needs-promotion-review=1" in report
    assert "- Risk tiers: standard-review=1" in report

    invalid = copy.deepcopy(plan)
    invalid.pop("status")
    with pytest.raises(ValueError, match="missing required field status"):
        render_promotion_wave_report(invalid)

    invalid = copy.deepcopy(plan)
    invalid["assignment_rule"] = "non-canonical routing"
    with pytest.raises(ValueError, match="assignment_rule is not canonical"):
        render_promotion_wave_report(invalid)

    invalid = copy.deepcopy(plan)
    invalid["raw_entries_covered"] = 2
    with pytest.raises(ValueError, match="raw indexes do not match raw_entries_covered"):
        render_promotion_wave_report(invalid)


def test_promotion_research_packets_cover_every_raw_and_unique_target() -> None:
    raw_packets = _load_json(MANIFEST_DIR / "raw-research-packets.json")
    unique_packets = _load_json(MANIFEST_DIR / "unique-target-research-packets.json")
    normalized = _load_json(MANIFEST_DIR / "normalized-urls.json")
    schema = _load_json(MANIFEST_DIR / "research-packet-schema.json")

    required = set(schema["required_packet_fields"])
    raw_items = raw_packets["packets"]
    unique_items = unique_packets["packets"]

    assert raw_packets["packet_count"] == 293
    assert unique_packets["packet_count"] == 289
    assert raw_packets["required_packet_fields"] == schema["required_packet_fields"]
    assert [packet["raw_index"] for packet in raw_items] == list(range(1, 294))
    assert {packet["normalized_url"] for packet in raw_items} == set(normalized["unique_targets"])
    assert {packet["normalized_url"] for packet in unique_items} == set(normalized["unique_targets"])

    for packet in raw_items:
        assert required.issubset(packet)
        assert packet["packet_id"] == f"U{packet['raw_index']:03d}"
        assert packet["install_command"] == ""
        assert packet["live_install_eligible"] is False
        if packet["existing_integration_status"] == "covered-by-existing-installable-catalog":
            if packet["current_intake_decision"] == "integrated_existing_surface":
                assert packet["terminal_route_requirements"] == []
        else:
            assert packet["terminal_route_requirements"]
        assert {leaf["suffix"] for leaf in packet["leaf_checks"]} == RAW_RESEARCH_SUFFIXES

    for packet in unique_items:
        assert packet["install_command"] == ""
        assert packet["live_install_eligible"] is False
        assert packet["repo_mutation_eligible"] is False
        assert packet["raw_packet_ids"] == [f"U{raw_index:03d}" for raw_index in packet["raw_indexes"]]
        assert {leaf["suffix"] for leaf in packet["leaf_checks"]} == UNIQUE_SYNTHESIS_SUFFIXES
        if packet["existing_integration_status"] == "covered-by-existing-installable-catalog":
            assert packet["terminal_route_requirements"] == []
            assert _existing_rows_are_trust_cleared(packet["existing_rows"])
        else:
            assert "use repo-native MCP/plugin/tool/catalog surfaces" in packet["terminal_route_requirements"]


def test_promotion_source_list_evidence_gate_statuses_are_unique() -> None:
    promoter = _load_promoter_module()
    evidence_statuses = [row[0] for row in promoter._SOURCE_LIST_EVIDENCE_GATE_STATUSES]
    assert len(evidence_statuses) == len(set(evidence_statuses))


def test_promotion_gate_matrix_and_install_preview_keep_live_installs_blocked() -> None:
    matrix = _load_json(MANIFEST_DIR / "promotion-gate-matrix.json")
    preview = _load_json(MANIFEST_DIR / "live-install-command-preview.json")
    unique = _load_json(MANIFEST_DIR / "unique-target-research-packets.json")
    summary = (MANIFEST_DIR / "promotion-gate-summary.md").read_text(encoding="utf-8")
    assert matrix["summary"] == {
        "unique_targets": 289,
        "integrated_targets": 289,
        "unintegrated_targets": 0,
        "classification_counts": EXPECTED_INTEGRATION_CLASSIFICATION_COUNTS,
        "trust_cleared_installable_targets": 121,
        "integrated_quarantine_targets": 4,
        "active_install_blocks": 4,
        "ready_for_repo_promotion": 0,
        "ready_for_live_install": 0,
    }
    assert len(matrix["items"]) == 289
    assert matrix["gate_status_counts"]["live install"] == {
        "active-hard-block-no-command": 4,
        "inspection-required-no-command": 6,
        "non-installable-reference-no-command": 158,
        "no-new-live-install-command-emitted": 121,
    }
    final_counts = {
        status: sum(1 for item in matrix["items"] if item["final_status"] == status)
        for status in {item["final_status"] for item in matrix["items"]}
    }
    assert final_counts == EXPECTED_INTEGRATION_CLASSIFICATION_COUNTS
    assert not any(item["install_command"] for item in matrix["items"])

    unique_by_url = {packet["normalized_url"]: packet for packet in unique["packets"]}
    for item in matrix["items"]:
        packet = unique_by_url[item["normalized_url"]]
        assert item["final_status"] == packet["integration_classification"]
        assert item["integrated"] is True

    terraform = next(
        item for item in matrix["items"] if item["normalized_url"] == "https://github.com/antonbabenko/terraform-skill"
    )
    assert terraform["existing_integration_status"] == "covered-by-existing-inspection-required"
    assert terraform["final_status"] == "inspection-existing"
    assert terraform["gate_statuses"]["live install"] == "inspection-required-no-command"
    assert terraform["gate_statuses"]["license review"] != "existing-catalog-row-owns-license-and-attribution"

    assert preview["status"] == "no-live-install-commands-emitted"
    assert preview["command_count"] == 0
    assert preview["commands"] == []
    assert preview["integrated_target_count"] == 289
    assert preview["unintegrated_target_count"] == 0
    assert preview["classification_counts"] == EXPECTED_INTEGRATION_CLASSIFICATION_COUNTS
    assert preview["trust_cleared_installable_target_count"] == 121
    assert len(preview["trust_cleared_installable_targets"]) == 121
    assert preview["non_installable_integrated_target_count"] == 168
    assert len(preview["non_installable_integrated_targets"]) == 168
    assert preview["integrated_quarantine_target_count"] == 4
    assert preview["active_install_blocks"] == 4
    assert "https://github.com/antonbabenko/terraform-skill" not in {
        item["normalized_url"] for item in preview["trust_cleared_installable_targets"]
    }
    assert "https://github.com/antonbabenko/terraform-skill" in {
        item["normalized_url"] for item in preview["non_installable_integrated_targets"]
    }
    assert "Every normalized source has a stable catalog integration" in summary


def test_promotion_packet_coverage_cli() -> None:
    result = subprocess.run(
        ["uv", "run", "python", "scripts/promote_candidate_corpus.py", "--check-coverage"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload == {
        "raw": 293,
        "unique": 289,
        "matrix_items": 289,
        "command_count": 0,
        "ok": True,
        "errors": [],
    }


def test_deep_source_audit_covers_every_unique_target_without_execution() -> None:
    audit = _load_json(MANIFEST_DIR / "deep-source-audit.json")

    assert audit["candidate_code_executed"] is False
    assert audit["unique_target_count"] == 289
    assert len(audit["items"]) == 289
    assert sum(audit["status_counts"].values()) == 289
    assert audit["status_counts"]["audited"] == 289
    assert audit["status_counts"].get("terminal-blocker", 0) == 0
    assert audit["auth_required_count"] >= 49
    assert audit["security_indicator_target_count"] >= 1

    by_url = {item["normalized_url"]: item for item in audit["items"]}
    nvidia = by_url["https://github.com/NVIDIA/skills"]
    assert nvidia["status"] == "audited"
    assert nvidia["candidate_code_executed"] is False
    csvglow = by_url["https://github.com/Ratnaditya-J/csvglow"]
    assert csvglow["status"] == "audited"
    assert csvglow["readme"]["path"]
    assert csvglow["license"]["status"] in {"ok", "error"}
    assert csvglow["candidate_code_executed"] is False


def test_deep_source_audit_extracts_auth_variable_names_without_values() -> None:
    auditor = _load_deep_source_audit_module()
    fetched = [
        {
            "path": "README.md",
            "text": (
                "Set APIFY_TOKEN and ${OPENAI_API_KEY}. "
                "Use process.env.LANGFUSE_SECRET_KEY; TOKEN=MY_SECRET_VALUE. "
                "Authenticate with AZURE_CLIENT_ID; never paste actual-secret-value."
            ),
        }
    ]

    auth = auditor.detect_auth(fetched, ["README.md"], "example/tool")

    assert auth["auth_required"] is True
    assert auth["env_vars_or_credentials"] == [
        "APIFY_TOKEN",
        "AZURE_CLIENT_ID",
        "LANGFUSE_SECRET_KEY",
        "OPENAI_API_KEY",
        "TOKEN",
    ]
    assert "MY_SECRET_VALUE" not in auth["env_vars_or_credentials"]
    assert "actual-secret-value" not in json.dumps(auth)


def test_deep_source_audit_env_names_make_auth_required() -> None:
    auditor = _load_deep_source_audit_module()
    auth = auditor.detect_auth(
        [{"path": "README.md", "text": "Configure ${AZURE_CLIENT_ID}."}],
        ["README.md"],
        "example/tool",
    )

    assert auth["auth_required"] is True
    assert auth["env_vars_or_credentials"] == ["AZURE_CLIENT_ID"]


def test_harness_install_assurance_is_complete_and_cross_harness() -> None:
    assurance = _load_json(MANIFEST_DIR / "harness-install-assurance.json")
    catalog = _load_json(ROOT / "docs/public/generated-registries/skills-catalog-index.json")

    assert assurance["complete"] is True
    assert assurance["catalog_entry_count"] == len(catalog["allSkillIndex"])
    assert assurance["target_harness_count"] == 9
    assert assurance["totals"]["missing"] == 0
    assert assurance["totals"]["pin_blocked"] == 0
    assert assurance["totals"]["commands"] == 0
    assert {item["agent"] for item in assurance["agents"]} == {
        "antigravity",
        "claude-code",
        "codex",
        "crush",
        "cursor",
        "gemini-cli",
        "github-copilot",
        "grok",
        "opencode",
    }


def test_non_skill_install_assurance_covers_every_normalized_target() -> None:
    assurance = _load_json(MANIFEST_DIR / "non-skill-install-assurance.json")
    targets = _load_json(MANIFEST_DIR / "integration-targets.json")["items"]
    rows = assurance["items"]

    assert assurance["complete"] is True
    assert assurance["unique_target_count"] == 289
    assert len(rows) == 289
    assert {row["normalized_url"].lower() for row in rows} == {target["normalized_url"].lower() for target in targets}
    assert assurance["totals"]["runtime_artifacts"] == assurance["totals"]["verified_runtime_artifacts"]
    assert assurance["totals"]["failed_runtime_artifacts"] == 0


def test_non_skill_install_assurance_keeps_candidate_mcps_disabled_and_pinned() -> None:
    registry = _load_json(ROOT / "config/mcp-registry.json")["servers"]
    expected = {
        "axiom-mcp": ["-y", "axiom-mcp@27.0.0-beta.22"],
        "csvglow": ["--from", "csvglow==0.1.0", "csvglow", "--mcp"],
        "designer-skill-mcp": ["-y", "designer-skill-mcp@0.14.0"],
        "geo-mcp": ["--from", "geo-optimizer-skill[mcp]==4.15.0", "geo-mcp"],
        "prompt-to-asset": ["-y", "prompt-to-asset@0.5.1"],
    }

    for name, args in expected.items():
        assert registry[name]["enabled"] is False
        assert registry[name]["args"] == args
    assert registry["prompt-to-asset"]["env"]["PROMPT_TO_BUNDLE_DRY_RUN"]["value"] == "1"


def test_non_skill_install_assurance_is_secret_free_and_quarantine_safe() -> None:
    assurance = _load_json(MANIFEST_DIR / "non-skill-install-assurance.json")
    auth_name = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")

    for row in assurance["items"]:
        assert all(auth_name.fullmatch(value) for value in row["auth_env_names"])
        for artifact in row["artifacts"]:
            assert artifact["verified"] is True
            assert all(not path.startswith("/") and "/Users/" not in path for path in artifact["resolved_paths"])
            if artifact["kind"] == "mcp":
                assert artifact["mcp_enabled"] is False
        if row["runtime_disposition"] == "hard-quarantined":
            assert row["artifacts"] == []
            assert row["activation_state"] == "quarantined"


def test_final_records_and_progress_bind_non_skill_assurance() -> None:
    records = _load_json(MANIFEST_DIR / "all-records.json")["records"]
    progress = _load_json(MANIFEST_DIR / "full-integration-progress.json")

    assert all(
        record["final_integration"]["non_skill_assurance"] == "non-skill-install-assurance.json"
        and record["final_integration"]["runtime_disposition"]
        for record in records
    )
    assert progress["completion_checks"]["non_skill_install_assurance"] is True
    assert progress["non_skill_install"]["complete"] is True
    assert progress["non_skill_install"]["unique_target_count"] == 289


def test_non_skill_install_assurance_check_cli() -> None:
    result = subprocess.run(
        ["uv", "run", "python", "scripts/record_candidate_non_skill_assurance.py", "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert json.loads(result.stdout) == {"ok": True, "errors": []}


def test_promotion_final_check_cli_validates_completed_overlay() -> None:
    result = subprocess.run(
        ["uv", "run", "python", "scripts/promote_candidate_corpus.py", "--final-check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)

    assert payload["ok"] is True
    assert payload["raw"] == 293
    assert payload["unique"] == 289
    assert payload["deep_audited"] == 289
    assert payload["deep_terminal_blockers"] == 0
    assert payload["promoted_overrides"] == len(PROMOTED_SKILL_NAMES)
    assert payload["live_installed"] == len(PROMOTED_SKILL_NAMES)
    assert payload["installed_path_refs"] == PROMOTED_INSTALLED_PATH_REFS
    assert payload["verified_skill_md"] == PROMOTED_INSTALLED_PATH_REFS
    assert payload["missing_skill_md"] == 0
    assert payload["errors"] == []


def test_promotion_combined_checks_run_both_phases() -> None:
    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/promote_candidate_corpus.py",
            "--check-coverage",
            "--final-check",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert '"matrix_items": 289' in result.stdout
    assert '"deep_audited": 289' in result.stdout


def _valid_apply_override(**updates):
    override = {
        "normalized_url": "https://example.test/source",
        "source_name": "example/source",
        "candidate_authoring_name": "candidate-corpus-001-source",
        "skill_name": "example-skill",
        "description": "Example promoted skill.",
        "install_source": "example/source",
        "install_command": "npx skills add example/source --skill example-skill -y -g -a codex",
        "target_agents": ["codex"],
        "status": "install-now-after-trust-gate",
        "trust_tier": "curated-trust-gated",
        "provenance_status": "verified-install-command",
        "selector_mode": "named",
        "sync_kind": "skills-cli",
        "audit_date": "2026-07-07",
        "audited_head": "abc123",
        "license": "MIT",
        "pin_policy": "pin-before-install",
        "source_list_evidence": "source-list-found",
        "found_skill_count": 1,
        "raw_indexes": [1],
        "live_install_executed": True,
        "executed_commands": ["npx skills add example/source --skill example-skill -y -g -a codex"],
        "installed_paths": ["~/.agents/skills/example-skill"],
        "risk_category": "standard-review",
        "risk_tier": "standard-review",
        "intake_decision": "integrated_native_surface",
        "executable_surface": "prompt-only-skill",
        "credential_behavior": "No credentials.",
        "network_access": "No declared network access.",
        "file_access": "No declared file access.",
        "live_action_risk": "User invoked only.",
        "promotion_policy": "Reviewed test promotion.",
        "provenance_evidence": "Fixture evidence.",
        "remaining_blockers": [],
    }
    override.update(updates)
    return override


def _prepare_apply_promotion_fixture(tmp_path, monkeypatch, overrides, rows=None, *, create_installed_paths=True):
    apply_promotions = _load_apply_promotions_module()
    authoring_dir = tmp_path / "authoring"
    authoring_dir.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(apply_promotions, "ROOT", tmp_path)
    monkeypatch.setattr(apply_promotions, "MANIFEST_DIR", tmp_path)
    monkeypatch.setattr(apply_promotions, "AUTHORING_DIR", authoring_dir)
    monkeypatch.setattr(apply_promotions, "OVERRIDES", tmp_path / "promotion-overrides.json")
    monkeypatch.setattr(apply_promotions, "SUMMARY", tmp_path / "catalog-authoring-summary.json")
    monkeypatch.setattr(apply_promotions, "REPORT", tmp_path / "applied-promotion-overrides.json")
    monkeypatch.setattr(apply_promotions, "PROGRESS", tmp_path / "full-integration-progress.json")
    monkeypatch.setattr(apply_promotions, "STATE_REPORT", tmp_path / "full-integration-state.md")
    if rows is None:
        rows = [
            {
                "name": "candidate-corpus-001-source",
                "path": "docs/src/authoring/skills/candidate-corpus-001-source.mdx",
                "normalized_url": "https://example.test/source",
                "source_name": "example/source",
                "raw_indexes": [1],
                "status": "integrated-native-surface",
                "sync_kind": "none",
                "source_list_evidence": "source-list-found",
                "remaining_blockers": ["promotion review"],
            }
        ]
    (tmp_path / "promotion-overrides.json").write_text(
        json.dumps({"overrides": overrides}, indent=2) + "\n",
        encoding="utf-8",
    )
    if create_installed_paths:
        for override in overrides:
            if not isinstance(override, dict) or not override.get("live_install_executed"):
                continue
            for raw_path in override.get("installed_paths", []):
                if not isinstance(raw_path, str) or not raw_path.strip():
                    continue
                skill_md = Path(os.path.expanduser(raw_path))
                if skill_md.name != "SKILL.md":
                    skill_md = skill_md / "SKILL.md"
                skill_md.parent.mkdir(parents=True, exist_ok=True)
                installed_name = str(override.get("install_skill_name") or override.get("skill_name") or "")
                skill_md.write_text(f"---\nname: {installed_name}\n---\n", encoding="utf-8")
    live_stats = apply_promotions.live_install_evidence_stats(overrides)
    (tmp_path / "catalog-authoring-summary.json").write_text(
        json.dumps({"version": 1, "rows_written": len(rows), "rows": rows}, indent=2) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "full-integration-progress.json").write_text(
        json.dumps(
            {
                "phase": "promotion-overlay-installed",
                "complete": True,
                "live_install": {
                    "installed_skill_rows": live_stats["live_install_rows"],
                    "recorded_install_evidence_rows": live_stats["live_install_rows"],
                    "eligible_count": 0,
                    "new_live_install_commands_emitted": 0,
                    "installed_path_refs": live_stats["installed_path_refs"],
                    "verified_skill_md_count": live_stats["verified_skill_md_count"],
                    "missing_skill_md_count": len(live_stats["missing_installed_skill_md"]),
                    "status": "no-live-install-commands-emitted",
                },
                "promotion_readiness": {
                    "ready_for_repo_promotion": 0,
                    "ready_for_live_install": 0,
                    "promoted_installable_rows": sum(isinstance(override, dict) for override in overrides),
                    "recorded_install_evidence_rows": live_stats["live_install_rows"],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    plan = _terminal_wave_plan("https://example.test/source")
    (tmp_path / "promotion-wave-plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    (tmp_path / "promotion-wave-plan.md").write_text(render_promotion_wave_report(plan), encoding="utf-8")
    return apply_promotions


def test_apply_promotions_rejects_path_traversal_before_writes(tmp_path, monkeypatch):
    apply_promotions = _prepare_apply_promotion_fixture(
        tmp_path,
        monkeypatch,
        [_valid_apply_override(skill_name="../escape")],
    )

    with pytest.raises(ValueError, match="invalid skill_name"):
        apply_promotions.apply_overrides()

    assert not (tmp_path / "escape.mdx").exists()
    assert not (tmp_path / "authoring" / ".." / "escape.mdx").exists()


def test_apply_promotions_preflight_rejects_plan_before_normalization_or_writes(tmp_path, monkeypatch):
    apply_promotions = _prepare_apply_promotion_fixture(tmp_path, monkeypatch, [_valid_apply_override()])
    plan = json.loads((tmp_path / "promotion-wave-plan.json").read_text(encoding="utf-8"))
    plan.pop("status")
    (tmp_path / "promotion-wave-plan.json").write_text(json.dumps(plan), encoding="utf-8")
    overrides_before = (tmp_path / "promotion-overrides.json").read_text(encoding="utf-8")
    normalized = False

    def record_normalize() -> None:
        nonlocal normalized
        normalized = True

    monkeypatch.setattr(apply_promotions, "normalize_overrides_file", record_normalize)

    with pytest.raises(ValueError, match=r"Run .*generate_candidate_corpus_shards\.py.*first"):
        apply_promotions.apply_overrides()

    assert normalized is False
    assert (tmp_path / "promotion-overrides.json").read_text(encoding="utf-8") == overrides_before
    assert not (tmp_path / "applied-promotion-overrides.json").exists()
    assert not (tmp_path / "authoring" / "example-skill.mdx").exists()


def test_apply_promotions_validate_reports_missing_required_reports(tmp_path, monkeypatch):
    apply_promotions = _prepare_apply_promotion_fixture(tmp_path, monkeypatch, [_valid_apply_override()])

    result = apply_promotions.validate()

    assert result["ok"] is False
    for filename in (
        "changelog-entry.md",
        "risky-skipped-deduped-decision-log.md",
        "validation-report.md",
        "final-review-report.md",
    ):
        assert f"missing {filename}" in result["errors"]


def test_apply_promotions_validator_rejects_duplicate_skill_names(tmp_path, monkeypatch):
    overrides = [
        _valid_apply_override(),
        _valid_apply_override(normalized_url="https://example.test/other"),
    ]
    rows = [
        {"normalized_url": "https://example.test/source"},
        {"normalized_url": "https://example.test/other"},
    ]
    apply_promotions = _prepare_apply_promotion_fixture(tmp_path, monkeypatch, overrides, rows=rows)

    errors = apply_promotions.validate_override_records(overrides, rows)

    assert "duplicate promoted skill_name example-skill" in errors


def test_apply_promotions_validator_rejects_missing_integration_target(tmp_path, monkeypatch):
    overrides = [_valid_apply_override(normalized_url="https://example.test/missing")]
    rows = [{"normalized_url": "https://example.test/source"}]
    apply_promotions = _prepare_apply_promotion_fixture(tmp_path, monkeypatch, overrides, rows=rows)

    errors = apply_promotions.validate_override_records(overrides, rows)

    assert any("normalized_url has no integration target" in error for error in errors)


def test_apply_promotions_validator_requires_live_install_evidence(tmp_path, monkeypatch):
    overrides = [
        _valid_apply_override(
            executed_commands=["npx skills add example/source --skill example-skill --dry-run"],
            installed_paths=[],
        )
    ]
    apply_promotions = _prepare_apply_promotion_fixture(tmp_path, monkeypatch, overrides)

    errors = apply_promotions.validate_override_records(
        overrides,
        apply_promotions.load_json(apply_promotions.SUMMARY)["rows"],
    )

    assert "live install for https://example.test/source lacks non-dry-run install command evidence" in errors
    assert "live install for https://example.test/source lacks installed path evidence" in errors


def test_apply_promotions_validator_accepts_bulk_live_install_evidence(tmp_path, monkeypatch):
    overrides = [
        _valid_apply_override(
            executed_commands=["npx skills add example/source -y -g -a codex"],
            installed_paths=["~/.agents/skills/example-skill"],
            source_bulk_install_evidence=True,
        )
    ]
    apply_promotions = _prepare_apply_promotion_fixture(tmp_path, monkeypatch, overrides)

    errors = apply_promotions.validate_override_records(
        overrides,
        apply_promotions.load_json(apply_promotions.SUMMARY)["rows"],
    )

    assert not any("lacks non-dry-run install command evidence" in error for error in errors)


def test_apply_promotions_validator_rejects_unmarked_bulk_install_evidence(tmp_path, monkeypatch):
    overrides = [_valid_apply_override(executed_commands=["npx skills add example/source -y -g -a codex"])]
    apply_promotions = _prepare_apply_promotion_fixture(tmp_path, monkeypatch, overrides)

    errors = apply_promotions.validate_override_records(
        overrides,
        apply_promotions.load_json(apply_promotions.SUMMARY)["rows"],
    )

    assert any("lacks matching skill selector evidence" in error for error in errors)


def test_apply_promotions_validator_rejects_quarantine_and_unlicensed_override(tmp_path, monkeypatch):
    overrides = [
        _valid_apply_override(
            intake_decision="hard_blocked_quarantine",
            license="NOASSERTION",
        )
    ]
    apply_promotions = _prepare_apply_promotion_fixture(tmp_path, monkeypatch, overrides)

    errors = apply_promotions.validate_override_records(
        overrides,
        apply_promotions.load_json(apply_promotions.SUMMARY)["rows"],
    )

    assert "override 1 cannot promote a terminal hard-block decision" in errors
    assert "override 1 lacks a compatible asserted license" in errors


def test_apply_promotions_validator_binds_hard_block_to_source_decision(tmp_path, monkeypatch):
    overrides = [_valid_apply_override(intake_decision="integrated_native_surface")]
    apply_promotions = _prepare_apply_promotion_fixture(tmp_path, monkeypatch, overrides)
    (tmp_path / "integration-decisions.json").write_text(
        json.dumps({
            "decisions": [
                {
                    "normalized_url": "https://example.test/source",
                    "decision": "hard_blocked_quarantine",
                }
            ]
        }),
        encoding="utf-8",
    )

    errors = apply_promotions.validate_override_records(
        overrides,
        apply_promotions.load_json(apply_promotions.SUMMARY)["rows"],
    )

    assert "override 1 conflicts with the source decision hard-block gate" in errors


def test_apply_promotions_validator_binds_command_and_path_to_override(tmp_path, monkeypatch):
    overrides = [
        _valid_apply_override(
            executed_commands=["echo 'skills add example/source --skill example-skill'"],
            installed_paths=["~/.agents/skills/unrelated-skill"],
        )
    ]
    apply_promotions = _prepare_apply_promotion_fixture(tmp_path, monkeypatch, overrides)

    errors = apply_promotions.validate_override_records(
        overrides,
        apply_promotions.load_json(apply_promotions.SUMMARY)["rows"],
    )

    assert any("lacks non-dry-run install command evidence" in error for error in errors)
    assert any("has unrelated installed path" in error for error in errors)


def test_apply_promotions_validator_rejects_shell_control_and_wrong_frontmatter(tmp_path, monkeypatch):
    overrides = [
        _valid_apply_override(
            executed_commands=["npx skills add example/source --skill example-skill -y -g -a codex ; echo nope"],
        )
    ]
    apply_promotions = _prepare_apply_promotion_fixture(tmp_path, monkeypatch, overrides)
    skill_md = tmp_path / ".agents" / "skills" / "example-skill" / "SKILL.md"
    skill_md.write_text("---\nname: unrelated-skill\n---\n", encoding="utf-8")

    errors = apply_promotions.validate_override_records(
        overrides,
        apply_promotions.load_json(apply_promotions.SUMMARY)["rows"],
    )

    assert any("lacks non-dry-run install command evidence" in error for error in errors)
    assert any("has unrelated installed path" in error for error in errors)


def test_apply_promotions_validator_rejects_mismatched_source_selector_and_agents(tmp_path, monkeypatch):
    overrides = [
        _valid_apply_override(
            executed_commands=["npx skills add other/source --skill other-skill -y -g -a cursor"],
        )
    ]
    apply_promotions = _prepare_apply_promotion_fixture(tmp_path, monkeypatch, overrides)

    errors = apply_promotions.validate_override_records(
        overrides,
        apply_promotions.load_json(apply_promotions.SUMMARY)["rows"],
    )

    assert any("mismatched install source evidence" in error for error in errors)
    assert any("lacks matching skill selector evidence" in error for error in errors)
    assert any("lacks target harness command evidence" in error for error in errors)


def test_apply_promotions_validator_rejects_missing_installed_skill_md(tmp_path, monkeypatch):
    overrides = [_valid_apply_override()]
    apply_promotions = _prepare_apply_promotion_fixture(
        tmp_path,
        monkeypatch,
        overrides,
        create_installed_paths=False,
    )

    errors = apply_promotions.validate_override_records(
        overrides,
        apply_promotions.load_json(apply_promotions.SUMMARY)["rows"],
    )

    assert any("has missing installed SKILL.md" in error for error in errors)


def test_apply_promotions_validator_rejects_non_object_override(tmp_path, monkeypatch):
    overrides = [_valid_apply_override(), "not-an-object"]
    apply_promotions = _prepare_apply_promotion_fixture(tmp_path, monkeypatch, overrides)

    result = apply_promotions.validate()

    assert result["ok"] is False
    assert "override 2 is not an object" in result["errors"]


def test_apply_promotions_validator_checks_dynamic_summary_counters(tmp_path, monkeypatch):
    overrides = [_valid_apply_override()]
    rows = [
        {
            "name": "example-skill",
            "normalized_url": "https://example.test/source",
            "install_command": overrides[0]["install_command"],
            "live_install_executed": True,
        }
    ]
    apply_promotions = _prepare_apply_promotion_fixture(tmp_path, monkeypatch, overrides, rows=rows)
    summary = apply_promotions.load_json(apply_promotions.SUMMARY)
    summary.update({
        "install_commands_published": 0,
        "live_installs_recorded": 1,
        "status_counts": {"install-now-after-trust-gate": 0},
        "sync_kind_counts": {"skills-cli": 0},
    })
    apply_promotions.write_json(apply_promotions.SUMMARY, summary)
    (apply_promotions.AUTHORING_DIR / "example-skill.mdx").write_text("---\nname: example-skill\n---\n")

    result = apply_promotions.validate()

    assert result["ok"] is False
    assert "summary install_commands_published does not match installable rows" in result["errors"]
    assert "summary install_commands_published does not match promotion override count" in result["errors"]
    assert "summary installable status count does not match promotion override count" in result["errors"]
    assert "summary skills-cli sync count does not match promotion override count" in result["errors"]


def test_apply_promotions_validator_rejects_non_trust_cleared_retained_coverage(tmp_path, monkeypatch):
    overrides = [_valid_apply_override()]
    rows = [
        {
            "name": "example-skill",
            "normalized_url": "https://example.test/source",
            "install_command": overrides[0]["install_command"],
            "live_install_executed": True,
        }
    ]
    apply_promotions = _prepare_apply_promotion_fixture(tmp_path, monkeypatch, overrides, rows=rows)
    summary = apply_promotions.load_json(apply_promotions.SUMMARY)
    summary.update({
        "install_commands_published": 1,
        "live_installs_recorded": 1,
        "status_counts": {"install-now-after-trust-gate": 1},
        "sync_kind_counts": {"skills-cli": 1},
    })
    apply_promotions.write_json(apply_promotions.SUMMARY, summary)
    (apply_promotions.AUTHORING_DIR / "example-skill.mdx").write_text("---\nname: example-skill\n---\n")
    inspect_row = {
        "name": "needs-inspection",
        "status": "inspect-then-install",
        "trust_tier": "needs-inspection",
        "has_install_command": True,
        "sync_kind": "skills-cli",
    }
    apply_promotions.write_json(
        tmp_path / "existing-integration-coverage.json",
        {
            "items": [
                {
                    "normalized_url": "https://example.test/source",
                    "coverage_status": "covered-by-existing-installable-catalog",
                    "existing_rows": [inspect_row],
                }
            ]
        },
    )
    apply_promotions.write_json(
        tmp_path / "promotion-readiness-queue.json",
        {
            "covered_by_existing_installable_catalog": [
                {
                    "normalized_url": "https://example.test/source",
                    "existing_rows": [inspect_row],
                }
            ]
        },
    )

    result = apply_promotions.validate()

    assert result["ok"] is False
    assert "retained existing coverage lacks trust-cleared row for https://example.test/source" in result["errors"]
    assert "covered readiness row lacks trust-cleared existing row for https://example.test/source" in result["errors"]


def _write_promoter_json(tmp_path, name, payload):
    (tmp_path / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _prepare_promoter_validation_fixture(tmp_path, monkeypatch):
    promoter = _load_promoter_module()
    monkeypatch.setattr(promoter, "MANIFEST_DIR", tmp_path)
    monkeypatch.setattr(promoter, "EXPECTED_RAW_COUNT", 2)
    monkeypatch.setattr(promoter, "EXPECTED_UNIQUE_COUNT", 2)
    classification_counts = {"installable-existing": 1, "integrated-reference": 1}
    monkeypatch.setattr(promoter, "EXPECTED_CLASSIFICATION_COUNTS", classification_counts)
    raw_packets = [
        {
            "raw_index": 1,
            "normalized_url": "https://example.test/covered",
            "live_install_eligible": False,
            "install_command": "",
        },
        {
            "raw_index": 2,
            "normalized_url": "https://example.test/blocked",
            "live_install_eligible": False,
            "install_command": "",
        },
    ]
    unique_packets = [
        {
            "packet_id": "N001",
            "normalized_url": "https://example.test/covered",
            "raw_indexes": [1],
            "integration_classification": "installable-existing",
            "integration_surface": "integrated-existing-surface",
            "trust_cleared_installable": True,
            "hard_blocked": False,
            "integrated": True,
            "existing_integration_status": "covered-by-existing-installable-catalog",
            "existing_rows": [
                {
                    "name": "existing-covered",
                    "status": "install-now-after-trust-gate",
                    "trust_tier": "curated-trust-gated",
                    "has_install_command": True,
                    "sync_kind": "skills-cli",
                }
            ],
            "catalog_rows": [
                {
                    "name": "existing-covered",
                    "status": "install-now-after-trust-gate",
                    "trust_tier": "curated-trust-gated",
                    "has_install_command": True,
                    "sync_kind": "skills-cli",
                }
            ],
            "auth_required": False,
            "licenses": ["MIT"],
            "source_list_evidence": {"evidence_status": "source-list-found"},
            "terminal_route_requirements": [],
            "live_install_eligible": False,
            "repo_mutation_eligible": False,
            "install_command": "",
        },
        {
            "packet_id": "N002",
            "normalized_url": "https://example.test/blocked",
            "raw_indexes": [2],
            "integration_classification": "integrated-reference",
            "integration_surface": "integrated-native-surface",
            "trust_cleared_installable": False,
            "hard_blocked": False,
            "integrated": True,
            "existing_integration_status": "needs-promotion-review",
            "existing_rows": [],
            "catalog_rows": [
                {
                    "name": "example-blocked",
                    "path": "docs/src/authoring/skills/example-blocked.mdx",
                    "status": "integrated-reference",
                    "trust_tier": "curated-trust-gated",
                    "has_install_command": False,
                    "sync_kind": "none",
                }
            ],
            "auth_required": True,
            "licenses": ["MIT"],
            "source_list_evidence": {"evidence_status": "source-list-found"},
            "terminal_route_requirements": ["use repo-native MCP/plugin/tool/catalog surfaces"],
            "live_install_eligible": False,
            "repo_mutation_eligible": False,
            "install_command": "",
        },
    ]
    matrix = promoter.build_gate_matrix(unique_packets)
    preview = promoter.build_install_preview(unique_packets)
    _write_promoter_json(tmp_path, promoter.RAW_PACKET_FILE, {"packets": raw_packets})
    _write_promoter_json(tmp_path, promoter.UNIQUE_PACKET_FILE, {"packets": unique_packets})
    _write_promoter_json(tmp_path, promoter.GATE_MATRIX_FILE, matrix)
    _write_promoter_json(tmp_path, promoter.INSTALL_PREVIEW_FILE, preview)
    _write_promoter_json(
        tmp_path,
        "research-packet-schema.json",
        {"required_packet_fields": ["raw_index", "normalized_url", "live_install_eligible", "install_command"]},
    )
    _write_promoter_json(
        tmp_path,
        "normalized-urls.json",
        {
            "unique_targets": ["https://example.test/covered", "https://example.test/blocked"],
            "entries": [
                {"raw_index": 1, "normalized_url": "https://example.test/covered"},
                {"raw_index": 2, "normalized_url": "https://example.test/blocked"},
            ],
        },
    )
    _write_promoter_json(
        tmp_path,
        promoter.INTEGRATION_TARGET_FILE,
        {
            "raw_entries_covered": 2,
            "unique_targets": 2,
            "integrated_targets": 2,
            "unintegrated_targets": 0,
            "classification_counts": classification_counts,
            "generated_reference_count": 1,
            "items": [
                {
                    "normalized_url": packet["normalized_url"],
                    "raw_indexes": packet["raw_indexes"],
                    "integration_classification": packet["integration_classification"],
                    "integration_surface": packet["integration_surface"],
                    "trust_cleared_installable": packet["trust_cleared_installable"],
                    "hard_blocked": packet["hard_blocked"],
                    "catalog_rows": packet["catalog_rows"],
                    "generated_reference_name": "" if index == 0 else "example-blocked",
                    "generated_reference_path": ("" if index == 0 else "docs/src/authoring/skills/example-blocked.mdx"),
                }
                for index, packet in enumerate(unique_packets)
            ],
        },
    )
    (tmp_path / promoter.SUMMARY_FILE).write_text(
        promoter.promotion_gate_summary_text(matrix, preview),
        encoding="utf-8",
    )
    return promoter


def test_integration_validators_bind_generated_references_to_classification_and_catalog_row() -> None:
    apply_promotions = _load_apply_promotions_module()
    promoter = _load_promoter_module()
    payload = _load_json(MANIFEST_DIR / "integration-targets.json")
    normalized = _load_json(MANIFEST_DIR / "normalized-urls.json")

    reference_item = next(
        item for item in payload["items"] if item["integration_classification"] == "integrated-reference"
    )
    existing_item = next(
        item for item in payload["items"] if item["integration_classification"] == "installable-existing"
    )
    reference_item["generated_reference_name"] = ""
    reference_item["generated_reference_path"] = ""
    existing_item["generated_reference_name"] = "invented-reference"
    existing_item["generated_reference_path"] = "docs/src/authoring/skills/invented-reference.mdx"

    apply_errors = apply_promotions.integration_target_errors(payload)
    promote_errors = promoter.integration_target_errors(payload, normalized)

    for errors in (apply_errors, promote_errors):
        assert any("reference classification lacks generated reference identity" in error for error in errors)
        assert any("existing classification exposes generated reference identity" in error for error in errors)
        assert any("does not match exactly one catalog row" in error for error in errors)


def test_promotion_gate_matrix_blocks_inspection_required_existing_rows() -> None:
    promoter = _load_promoter_module()
    unique_packets = [
        {
            "packet_id": "N001",
            "normalized_url": "https://example.test/inspect",
            "raw_indexes": [1],
            "integration_classification": "inspection-existing",
            "integration_surface": "integrated-existing-surface",
            "trust_cleared_installable": False,
            "hard_blocked": False,
            "integrated": True,
            "existing_integration_status": "covered-by-existing-inspection-required",
            "existing_rows": [
                {
                    "status": "inspect-then-install",
                    "trust_tier": "needs-inspection",
                    "has_install_command": True,
                    "sync_kind": "skills-cli",
                }
            ],
            "catalog_rows": [
                {
                    "status": "inspect-then-install",
                    "trust_tier": "needs-inspection",
                    "has_install_command": True,
                    "sync_kind": "skills-cli",
                }
            ],
            "auth_required": False,
            "licenses": ["MIT"],
            "source_list_evidence": {"evidence_status": "source-list-found"},
            "terminal_route_requirements": ["use repo-native MCP/plugin/tool/catalog surfaces"],
        }
    ]

    matrix = promoter.build_gate_matrix(unique_packets)
    preview = promoter.build_install_preview(unique_packets)

    assert matrix["summary"]["integrated_targets"] == 1
    assert matrix["summary"]["unintegrated_targets"] == 0
    assert matrix["summary"]["classification_counts"] == {"inspection-existing": 1}
    assert matrix["items"][0]["final_status"] == "inspection-existing"
    assert matrix["items"][0]["gate_statuses"]["live install"] == "inspection-required-no-command"
    assert preview["trust_cleared_installable_targets"] == []
    assert preview["non_installable_integrated_targets"][0]["normalized_url"] == "https://example.test/inspect"


def test_promotion_validator_rejects_packet_installability_drift(tmp_path, monkeypatch):
    promoter = _prepare_promoter_validation_fixture(tmp_path, monkeypatch)
    unique = promoter.load_json(promoter.UNIQUE_PACKET_FILE)
    inspection_rows = [
        {
            "name": "needs-inspection",
            "status": "inspect-then-install",
            "trust_tier": "needs-inspection",
            "has_install_command": True,
            "sync_kind": "skills-cli",
        }
    ]
    unique["packets"][0]["existing_rows"] = inspection_rows
    unique["packets"][0]["catalog_rows"] = inspection_rows
    unique["packets"][0]["trust_cleared_installable"] = False
    matrix = promoter.build_gate_matrix(unique["packets"])
    preview = promoter.build_install_preview(unique["packets"])
    _write_promoter_json(tmp_path, promoter.UNIQUE_PACKET_FILE, unique)
    _write_promoter_json(tmp_path, promoter.GATE_MATRIX_FILE, matrix)
    _write_promoter_json(tmp_path, promoter.INSTALL_PREVIEW_FILE, preview)
    (tmp_path / promoter.SUMMARY_FILE).write_text(
        promoter.promotion_gate_summary_text(matrix, preview),
        encoding="utf-8",
    )

    result = promoter.validate_outputs()

    assert result["ok"] is False
    assert "packet N001 trust_cleared_installable drifted from integration target" in result["errors"]
    assert "packet N001 catalog_rows drifted from integration target" in result["errors"]


def test_promotion_validator_detects_missing_matrix_row(tmp_path, monkeypatch):
    promoter = _prepare_promoter_validation_fixture(tmp_path, monkeypatch)
    matrix = promoter.load_json(promoter.GATE_MATRIX_FILE)
    matrix["items"].pop()
    _write_promoter_json(tmp_path, promoter.GATE_MATRIX_FILE, matrix)

    result = promoter.validate_outputs()

    assert result["ok"] is False
    assert "gate matrix item count 1 != 2" in result["errors"]


def test_promotion_validator_detects_matrix_identity_drift(tmp_path, monkeypatch):
    promoter = _prepare_promoter_validation_fixture(tmp_path, monkeypatch)
    matrix = promoter.load_json(promoter.GATE_MATRIX_FILE)
    matrix["items"][0]["normalized_url"] = "https://example.test/wrong"
    _write_promoter_json(tmp_path, promoter.GATE_MATRIX_FILE, matrix)

    result = promoter.validate_outputs()

    assert result["ok"] is False
    assert "gate matrix target rows do not match unique packet order" in result["errors"]


def test_promotion_validator_detects_gate_count_drift(tmp_path, monkeypatch):
    promoter = _prepare_promoter_validation_fixture(tmp_path, monkeypatch)
    matrix = promoter.load_json(promoter.GATE_MATRIX_FILE)
    matrix["gate_status_counts"]["live install"] = {"blocked": 2}
    _write_promoter_json(tmp_path, promoter.GATE_MATRIX_FILE, matrix)

    result = promoter.validate_outputs()

    assert result["ok"] is False
    assert "gate matrix gate status counts do not match rows" in result["errors"]


def test_promotion_validator_detects_preview_identity_drift(tmp_path, monkeypatch):
    promoter = _prepare_promoter_validation_fixture(tmp_path, monkeypatch)
    preview = promoter.load_json(promoter.INSTALL_PREVIEW_FILE)
    preview["trust_cleared_installable_targets"][0]["normalized_url"] = "https://example.test/wrong"
    _write_promoter_json(tmp_path, promoter.INSTALL_PREVIEW_FILE, preview)

    result = promoter.validate_outputs()

    assert result["ok"] is False
    assert "live install preview installable targets do not match unique packets" in result["errors"]


def test_promotion_validator_detects_preview_count_drift(tmp_path, monkeypatch):
    promoter = _prepare_promoter_validation_fixture(tmp_path, monkeypatch)
    preview = promoter.load_json(promoter.INSTALL_PREVIEW_FILE)
    preview["non_installable_integrated_target_count"] = 99
    _write_promoter_json(tmp_path, promoter.INSTALL_PREVIEW_FILE, preview)

    result = promoter.validate_outputs()

    assert result["ok"] is False
    assert "live install preview non-installable target count does not match rows" in result["errors"]


def test_promotion_validator_detects_summary_markdown_drift(tmp_path, monkeypatch):
    promoter = _prepare_promoter_validation_fixture(tmp_path, monkeypatch)
    (tmp_path / promoter.SUMMARY_FILE).write_text("stale\n", encoding="utf-8")

    result = promoter.validate_outputs()

    assert result["ok"] is False
    assert "promotion gate summary markdown is stale" in result["errors"]


def test_promotion_validator_detects_unique_packet_install_drift(tmp_path, monkeypatch):
    promoter = _prepare_promoter_validation_fixture(tmp_path, monkeypatch)
    unique = promoter.load_json(promoter.UNIQUE_PACKET_FILE)
    unique["packets"] = copy.deepcopy(unique["packets"])
    unique["packets"][0]["install_command"] = "npx skills add example"
    _write_promoter_json(tmp_path, promoter.UNIQUE_PACKET_FILE, unique)

    result = promoter.validate_outputs()

    assert result["ok"] is False
    assert "a packet unexpectedly emitted an install command" in result["errors"]


def test_promotion_validator_detects_synchronized_unique_packet_identity_drift(tmp_path, monkeypatch):
    promoter = _prepare_promoter_validation_fixture(tmp_path, monkeypatch)
    unique = promoter.load_json(promoter.UNIQUE_PACKET_FILE)
    unique["packets"] = copy.deepcopy(unique["packets"])
    unique["packets"][0]["packet_id"] = "N999"
    matrix = promoter.build_gate_matrix(unique["packets"])
    preview = promoter.build_install_preview(unique["packets"])
    _write_promoter_json(tmp_path, promoter.UNIQUE_PACKET_FILE, unique)
    _write_promoter_json(tmp_path, promoter.GATE_MATRIX_FILE, matrix)
    _write_promoter_json(tmp_path, promoter.INSTALL_PREVIEW_FILE, preview)
    (tmp_path / promoter.SUMMARY_FILE).write_text(
        promoter.promotion_gate_summary_text(matrix, preview),
        encoding="utf-8",
    )

    result = promoter.validate_outputs()

    assert result["ok"] is False
    assert "unique packet target rows do not match normalized target order" in result["errors"]


def test_promotion_validator_detects_missing_raw_required_field_without_crashing(tmp_path, monkeypatch):
    promoter = _prepare_promoter_validation_fixture(tmp_path, monkeypatch)
    raw = promoter.load_json(promoter.RAW_PACKET_FILE)
    raw["packets"][0].pop("normalized_url")
    _write_promoter_json(tmp_path, promoter.RAW_PACKET_FILE, raw)

    result = promoter.validate_outputs()

    assert result["ok"] is False
    assert any(error.startswith("raw packets missing required fields") for error in result["errors"])
    assert "raw packets do not cover every normalized target" in result["errors"]


def test_promotion_validator_detects_missing_unique_target_without_crashing(tmp_path, monkeypatch):
    promoter = _prepare_promoter_validation_fixture(tmp_path, monkeypatch)
    unique = promoter.load_json(promoter.UNIQUE_PACKET_FILE)
    unique["packets"][0].pop("normalized_url")
    _write_promoter_json(tmp_path, promoter.UNIQUE_PACKET_FILE, unique)

    result = promoter.validate_outputs()

    assert result["ok"] is False
    assert "unique packets do not cover every normalized target" in result["errors"]
    assert "gate matrix target rows do not match unique packet order" in result["errors"]


def test_promotion_validator_detects_non_object_matrix_without_crashing(tmp_path, monkeypatch):
    promoter = _prepare_promoter_validation_fixture(tmp_path, monkeypatch)
    _write_promoter_json(tmp_path, promoter.GATE_MATRIX_FILE, [])

    result = promoter.validate_outputs()

    assert result["ok"] is False
    assert "gate matrix payload is not an object" in result["errors"]
    assert "gate matrix terminal route checks drifted" in result["errors"]


def test_safe_wave_source_list_evidence_is_list_only() -> None:
    evidence = _load_json(MANIFEST_DIR / "safe-wave-source-list-evidence.json")

    assert evidence["status"] in {
        "starter-wave-source-list-evidence-recorded",
        "source-list-evidence-recorded",
    }
    assert evidence["live_install_executed"] is False
    assert evidence["install_command_count"] == 0
    assert len(evidence["items"]) == 289
    assert evidence["summary"]["recorded_target_count"] == 289
    assert evidence["summary"]["remaining_target_count"] == 0
    assert {item["wave_id"] for item in evidence["items"]}
    assert sum(1 for item in evidence["items"] if item["evidence_status"] == "source-list-found") >= 13
    assert all("--list" in item["command"] and "--skill" not in item["command"] for item in evidence["items"])
    assert all(item["terminal_route_notes"] for item in evidence["items"])
    assert all(item["evidence_status"].startswith("source-list-") for item in evidence["items"])
    assert all("stdout_excerpt" not in item and "listed_skills" not in item for item in evidence["items"])


def test_source_list_audit_check_requires_complete_evidence() -> None:
    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/audit_candidate_source_lists.py",
            "--check",
            "--require-complete",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)

    assert payload["ok"] is True
    assert payload["items"] == 289
    assert payload["unique_targets"] == 289
    assert payload["complete"] is True
    assert payload["summary"]["remaining_target_count"] == 0


def test_source_list_audit_parser_extracts_available_skills() -> None:
    auditor = _load_source_list_audit_module()
    output = """
│
◇  Found 2 skills
│
◇  Available Skills
│
│    workers-best-practices
│
│      Reviews and authors Cloudflare Workers code.
│
│    wrangler
│
│      Cloudflare Workers CLI.
│
└  Use --skill <name> to install specific skills
"""

    parsed = auditor.parse_skill_list_output(output)

    assert parsed == {
        "reported_skill_count": 2,
        "parsed_skill_count": 2,
        "listed_skills": ["workers-best-practices", "wrangler"],
    }


def test_source_list_audit_plan_is_read_only() -> None:
    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/audit_candidate_source_lists.py",
            "--wave",
            "W08",
            "--limit",
            "2",
            "--force",
            "--plan-only",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)

    assert payload["selected_count"] == 2
    assert all("--list" in item["command"] for item in payload["targets"])
    assert not any("--skill" in item["command"] for item in payload["targets"])
    assert not any("--apply" in item["command"] for item in payload["targets"])


def test_source_list_audit_timeout_kills_descendant_processes() -> None:
    auditor = _load_source_list_audit_module()
    command = [
        sys.executable,
        "-c",
        (
            "import subprocess, sys, time; "
            "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(10)']); "
            "time.sleep(10)"
        ),
    ]

    started = time.monotonic()
    exit_code, timed_out, _, _ = auditor.run_command_capture(command, timeout_seconds=1)
    duration = time.monotonic() - started

    assert exit_code == 124
    assert timed_out is True
    assert duration < 5
