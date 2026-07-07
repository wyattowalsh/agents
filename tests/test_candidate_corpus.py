"""Coverage checks for the July 2026 candidate corpus intake."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
RECORDS_DIR = MANIFEST_DIR / "records"
AUTHORING_DIR = ROOT / "docs" / "src" / "authoring" / "skills"
CATALOG_INDEX = ROOT / "docs" / "public" / "generated-registries" / "skills-catalog-index.json"
CATALOG_DIR = ROOT / "docs" / "src" / "authoring" / "skills"
GENERATED_EXTERNAL_DIR = ROOT / "docs" / "src" / "content" / "docs" / "skills" / "catalog" / "external"
CATALOG_PREFIX = "candidate-corpus-"
PROMOTION_OVERRIDES = json.loads((MANIFEST_DIR / "promotion-overrides.json").read_text(encoding="utf-8"))[
    "overrides"
]
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
PROMOTED_SKILL_NAMES = {
    override["skill_name"]
    for override in PROMOTION_OVERRIDES
}
PROMOTED_INSTALL_SELECTORS = {
    override["skill_name"]: override.get("install_skill_name", override["skill_name"])
    for override in PROMOTION_OVERRIDES
}
PROMOTED_CANDIDATE_NAMES = {
    override["candidate_authoring_name"]
    for override in PROMOTION_OVERRIDES
}
PROMOTED_INSTALLED_PATH_REFS = sum(
    len(override.get("installed_paths", []))
    for override in PROMOTION_OVERRIDES
    if override.get("live_install_executed")
)

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
        assert record["docs_steward_surfaces"]
        assert record["source_support_matrix"]
        assert record["tests_or_checks_run"]
        raw_indexes.append(record["raw_index"])
    assert raw_indexes == list(range(1, 294))


def test_auth_matrix_uses_placeholders_only() -> None:
    auth_matrix = _load_json(MANIFEST_DIR / "auth-matrix.json")
    assert auth_matrix["items"]
    for item in auth_matrix["items"]:
        for value in item["env_vars_or_credentials"]:
            assert value == "PLACEHOLDER_ONLY_REVIEW_REQUIRED"


def test_every_unique_target_has_catalog_authoring_row() -> None:
    summary = _load_json(MANIFEST_DIR / "catalog-authoring-summary.json")
    catalog_paths = sorted(CATALOG_DIR.glob(f"{CATALOG_PREFIX}*.mdx"))
    source_list_counts = summary["source_list_status_counts"]

    assert summary["rows_written"] == 289 - len(PROMOTED_CANDIDATE_NAMES) + len(PROMOTED_SKILL_NAMES)
    assert summary["unique_targets"] == 289
    assert summary["install_commands_published"] == len(PROMOTED_SKILL_NAMES)
    assert summary["live_installs_recorded"] == len(PROMOTED_SKILL_NAMES)
    assert summary["status_counts"] == {
        "global-only-or-avoid": 289 - len(PROMOTED_CANDIDATE_NAMES),
        "install-now-after-trust-gate": len(PROMOTED_SKILL_NAMES),
    }
    assert summary["sync_kind_counts"] == {
        "none": 289 - len(PROMOTED_CANDIDATE_NAMES),
        "skills-cli": len(PROMOTED_SKILL_NAMES),
    }
    assert sum(source_list_counts.values()) == 289
    assert source_list_counts["source-list-found"] >= 13
    assert "not-run" not in source_list_counts
    assert len(catalog_paths) == 289 - len(PROMOTED_CANDIDATE_NAMES)
    for skill_name in PROMOTED_SKILL_NAMES:
        assert (CATALOG_DIR / f"{skill_name}.mdx").exists()

    row_urls = {row["normalized_url"] for row in summary["rows"]}
    normalized = _load_json(MANIFEST_DIR / "normalized-urls.json")
    assert row_urls == set(normalized["unique_targets"])

    for path in catalog_paths[:20]:
        text = path.read_text(encoding="utf-8")
        assert "GENERATED-CANDIDATE-CORPUS-JUL2026" in text
        assert 'status: "global-only-or-avoid"' in text
        assert 'sync_kind: "none"' in text
        assert 'source_list_evidence: "not-run"' not in text
        assert "install_command:" not in text


def test_docs_steward_surfaces_are_all_accounted_for() -> None:
    surface_map = _load_json(MANIFEST_DIR / "docs-steward-surface-map.json")
    docs_impact = _load_json(MANIFEST_DIR / "docs-impact-matrix.json")
    decisions_summary = _load_json(MANIFEST_DIR / "integration-decisions.json")["summary"]
    unique_count = decisions_summary["unique_count"]
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
        assert surfaces[catalog_surface]["candidate_count"] == unique_count


def test_reference_only_count_uses_unique_terminal_decisions() -> None:
    decisions_payload = _load_json(MANIFEST_DIR / "integration-decisions.json")
    summary = decisions_payload["summary"]
    unique_reference_only = sum(
        1 for item in decisions_payload["decisions"] if item["decision"] == "reference_only"
    )

    assert summary["reference_only_count"] == unique_reference_only
    assert summary["reference_only_count"] < summary["unique_count"]


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

    assert "## Observed Generated Evidence" in validation_report
    assert "## Command Checklist" in validation_report
    assert "returned warnings only" not in validation_report
    assert "currently exits 1" not in validation_report
    assert "docs build passes" not in final_report
    assert "promotion-overlay-installed" in final_report
    assert "Final commit hash: recorded by the runner" not in final_report
    assert "- `agents-instructions`: 0 candidates" in docs_summary


def test_candidate_catalog_authoring_rows_track_promoted_installable_override() -> None:
    summary = _load_json(MANIFEST_DIR / "catalog-authoring-summary.json")
    generated_rows = sorted(AUTHORING_DIR.glob("candidate-corpus-*.mdx"))
    catalog_index = _load_json(CATALOG_INDEX)
    indexed_rows = [
        row for row in catalog_index["externalSkillIndex"] if str(row.get("name", "")).startswith("candidate-corpus-")
    ]
    promoted_rows = {
        row.get("name"): row
        for row in catalog_index["externalSkillIndex"]
        if row.get("name") in PROMOTED_SKILL_NAMES
    }

    assert summary["rows_written"] == 289 - len(PROMOTED_CANDIDATE_NAMES) + len(PROMOTED_SKILL_NAMES)
    assert summary["unique_targets"] == 289
    assert summary["install_commands_published"] == len(PROMOTED_SKILL_NAMES)
    assert summary["live_installs_recorded"] == len(PROMOTED_SKILL_NAMES)
    assert len(generated_rows) == 289 - len(PROMOTED_CANDIDATE_NAMES)
    assert len(indexed_rows) == 289 - len(PROMOTED_CANDIDATE_NAMES)
    assert {row["syncKind"] for row in indexed_rows} == {"none"}
    assert {row["status"] for row in indexed_rows} == {"global-only-or-avoid"}
    assert not any(row.get("installCommand") for row in indexed_rows)
    assert not any(row.get("useCommand") for row in indexed_rows)
    assert set(promoted_rows) == PROMOTED_SKILL_NAMES
    for skill_name, promoted_row in promoted_rows.items():
        assert promoted_row["syncKind"] == "skills-cli"
        assert promoted_row["status"] == "install-now-after-trust-gate"
        assert promoted_row["installCommand"].startswith("npx skills add ")
        assert f"--skill {PROMOTED_INSTALL_SELECTORS[skill_name]}" in promoted_row["installCommand"]
    assert {row["source_list_evidence"] for row in summary["rows"]} <= {
        "source-list-error",
        "source-list-found",
        "source-list-timeout",
    }

    for candidate_name in PROMOTED_CANDIDATE_NAMES:
        assert not (GENERATED_EXTERNAL_DIR / f"{candidate_name}.mdx").exists()
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
    assert "gh api repos/{owner}/{repo}" in record_7["tests_or_checks_run"]


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
        assert any(leaf["status"] == "blocked-until-trust-gates" for leaf in lane["leaf_checks"])

    unique_lanes = graph["unique_target_lanes"]
    assert {lane["normalized_url"] for lane in unique_lanes} == set(normalized["unique_targets"])
    for lane in unique_lanes:
        assert lane["live_install_eligible"] is False
        expected_status = (
            "covered-by-existing-catalog"
            if lane["existing_integration_status"] == "covered-by-existing-installable-catalog"
            else "provisional-intake-only"
        )
        assert lane["terminal_decision_status"] == expected_status
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

    assert progress["phase"] == "promotion-overlay-installed"
    assert progress["complete"] is True
    assert "Complete for the July 2026 candidate-corpus goal" in progress["completion_scope"]
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
    assert progress["promotion_readiness"]["covered_by_existing_installable_catalog"] == (
        readiness_summary["covered_by_existing_installable_catalog"]
    )
    assert readiness_summary["ready_for_repo_promotion"] == 0
    assert readiness_summary["ready_for_live_install"] == 0
    assert progress["promotion_readiness"]["ready_for_repo_promotion"] == 0
    assert progress["promotion_readiness"]["ready_for_live_install"] == 0
    assert progress["promotion_readiness"]["blocked_until_trust_gates"] == (
        readiness_summary["blocked_until_trust_gates"]
    )
    assert progress["promotion_readiness"]["promoted_installable_rows"] == len(PROMOTED_SKILL_NAMES)
    assert progress["promotion_readiness"]["recorded_install_evidence_rows"] == len(PROMOTED_SKILL_NAMES)
    assert progress["promotion_readiness"]["remaining_reference_rows"] == (
        289 - len(PROMOTED_CANDIDATE_NAMES)
    )
    assert progress["terminal_decisions"] == {
        "raw_candidates_processed": 293,
        "unique_normalized_targets": 289,
        "installable_curated_rows": len(PROMOTED_SKILL_NAMES),
        "live_installs_recorded": len(PROMOTED_SKILL_NAMES),
        "new_live_install_commands_emitted": 0,
        "reference_only_or_terminal_gated_rows": 289 - len(PROMOTED_CANDIDATE_NAMES),
        "duplicate_raw_groups": 4,
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
    assert "promotion-overlay-installed" in state_report
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


def test_promotion_readiness_queue_blocks_live_install_until_trust_gates() -> None:
    readiness = _load_json(MANIFEST_DIR / "promotion-readiness-queue.json")
    progress = _load_json(MANIFEST_DIR / "full-integration-progress.json")
    covered_existing = len(readiness["covered_by_existing_installable_catalog"])
    blocked_count = len(readiness["blocked_until_trust_gates"])

    assert readiness["status"] == "existing-coverage-reconciled-with-trust-gated-backlog"
    assert readiness["summary"] == {
        "unique_targets": 289,
        "covered_by_existing_installable_catalog": covered_existing,
        "ready_for_repo_promotion": 0,
        "ready_for_live_install": 0,
        "blocked_until_trust_gates": blocked_count,
    }
    assert readiness["ready_for_repo_promotion"] == []
    assert readiness["ready_for_live_install"] == []
    assert covered_existing + blocked_count == 289
    assert progress["promotion_readiness"]["covered_by_existing_installable_catalog"] == covered_existing
    assert progress["promotion_readiness"]["ready_for_repo_promotion"] == 0
    assert progress["promotion_readiness"]["ready_for_live_install"] == 0
    assert progress["promotion_readiness"]["promoted_installable_rows"] == len(PROMOTED_SKILL_NAMES)
    assert progress["promotion_readiness"]["recorded_install_evidence_rows"] == len(PROMOTED_SKILL_NAMES)
    assert progress["promotion_readiness"]["remaining_reference_rows"] == (
        289 - len(PROMOTED_CANDIDATE_NAMES)
    )
    assert progress["promotion_readiness"]["promoted_unique_targets"] >= 1

    for item in readiness["covered_by_existing_installable_catalog"]:
        assert item["terminal_status"] == "covered-by-existing-installable-catalog"
        assert item["live_install_eligible"] is False
        assert item["repo_mutation_eligible"] is False
        assert item["install_command"] == ""
        assert item["existing_rows"]
        assert _existing_rows_are_trust_cleared(item["existing_rows"])
        assert item["blocking_gates"] == []

    for item in readiness["blocked_until_trust_gates"]:
        assert item["terminal_status"] == "blocked-until-trust-gates"
        assert item["live_install_eligible"] is False
        assert item["repo_mutation_eligible"] is False
        assert item["install_command"] == ""
        assert "source-list evidence" in item["blocking_gates"]
        assert "target-specific validation" in item["blocking_gates"]

    terraform = next(
        item
        for item in readiness["blocked_until_trust_gates"]
        if item["source_name"].lower() == "antonbabenko/terraform-skill"
    )
    assert terraform["existing_integration_status"] == "covered-by-existing-inspection-required"
    assert terraform["terminal_status"] == "blocked-until-trust-gates"
    assert "license review" in terraform["blocking_gates"]
    assert "security review" in terraform["blocking_gates"]
    assert "target-specific validation" in terraform["blocking_gates"]
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
        assert by_decision_url[item["normalized_url"].lower()]["decision"] in {
            "merge_into_existing",
            "quarantine",
            "reference_only",
            "skip_inaccessible",
        }
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
                "name": "reference",
                "path": "reference.mdx",
                "source": "reference/source",
                "install_source": "reference/source",
                "source_url": "https://github.com/reference/source",
                "install_command": "",
                "status": "catalog-reference",
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
            "install_or_integration_decision": "reference_only",
        },
        {
            "raw_index": 2,
            "source_name": "inspect/source",
            "normalized_url": "https://github.com/inspect/source",
            "tree_subpath": "",
            "canonical_source": "https://github.com/inspect/source",
            "install_or_integration_decision": "reference_only",
        },
        {
            "raw_index": 3,
            "source_name": "reference/source",
            "normalized_url": "https://github.com/reference/source",
            "tree_subpath": "",
            "canonical_source": "https://github.com/reference/source",
            "install_or_integration_decision": "reference_only",
        },
    ]

    coverage = generator.build_existing_integration_coverage(records)

    by_source = {item["source_name"]: item for item in coverage["items"]}
    assert by_source["trusted/source"]["coverage_status"] == "covered-by-existing-installable-catalog"
    assert by_source["inspect/source"]["coverage_status"] == "covered-by-existing-inspection-required"
    assert by_source["reference/source"]["coverage_status"] == "covered-by-existing-reference"


def test_promotion_readiness_keeps_inspection_required_existing_rows_blocked() -> None:
    generator = _load_generator_module()
    decisions = [
        {
            "normalized_url": "https://github.com/inspect/source",
            "source_name": "inspect/source",
            "raw_indexes": [1],
            "decision": "reference_only",
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
    assert readiness["summary"]["blocked_until_trust_gates"] == 1
    blocked = readiness["blocked_until_trust_gates"][0]
    assert blocked["terminal_status"] == "blocked-until-trust-gates"
    assert blocked["existing_rows"]
    assert "license review" in blocked["blocking_gates"]
    assert "security review" in blocked["blocking_gates"]
    assert "target-specific validation" in blocked["blocking_gates"]


def test_promotion_wave_plan_assigns_every_unique_target_once() -> None:
    coverage = _load_json(MANIFEST_DIR / "existing-integration-coverage.json")
    wave_plan = _load_json(MANIFEST_DIR / "promotion-wave-plan.json")
    progress = _load_json(MANIFEST_DIR / "full-integration-progress.json")

    assert wave_plan["total_targets"] == 289
    assert sum(wave["target_count"] for wave in wave_plan["waves"]) == 289
    assert progress["promotion_waves"] == {
        wave["wave_id"]: wave["target_count"] for wave in wave_plan["waves"] if wave["target_count"]
    }

    assigned_urls = [target["normalized_url"] for wave in wave_plan["waves"] for target in wave["targets"]]
    assert len(assigned_urls) == len(set(assigned_urls)) == 289

    by_wave = {wave["wave_id"]: wave for wave in wave_plan["waves"]}
    assert by_wave["W00"]["target_count"] == coverage["summary"]["covered-by-existing-installable-catalog"]
    assert by_wave["W00"]["mutation_policy"] == "no mutation; use existing catalog rows"
    assert sum(wave["target_count"] for wave in wave_plan["waves"][1:]) == 289 - coverage["summary"][
        "covered-by-existing-installable-catalog"
    ]
    assert all(
        target["coverage_status"] == "covered-by-existing-installable-catalog"
        for target in by_wave["W00"]["targets"]
    )
    assert "https://github.com/antonbabenko/terraform-skill" not in {
        target["normalized_url"] for target in by_wave["W00"]["targets"]
    }


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
            assert "source-list evidence" not in packet["blockers"]
        else:
            assert "source-list evidence" in packet["blockers"]
        assert {leaf["suffix"] for leaf in packet["leaf_checks"]} == RAW_RESEARCH_SUFFIXES

    for packet in unique_items:
        assert packet["install_command"] == ""
        assert packet["live_install_eligible"] is False
        assert packet["repo_mutation_eligible"] is False
        assert packet["raw_packet_ids"] == [f"U{raw_index:03d}" for raw_index in packet["raw_indexes"]]
        assert {leaf["suffix"] for leaf in packet["leaf_checks"]} == UNIQUE_SYNTHESIS_SUFFIXES
        if packet["existing_integration_status"] == "covered-by-existing-installable-catalog":
            assert packet["blockers"] == []
            assert _existing_rows_are_trust_cleared(packet["existing_rows"])
        else:
            assert "target-specific validation" in packet["blockers"]


def test_promotion_source_list_evidence_gate_statuses_are_unique() -> None:
    promoter = _load_promoter_module()
    evidence_statuses = [row[0] for row in promoter._SOURCE_LIST_EVIDENCE_GATE_STATUSES]
    assert len(evidence_statuses) == len(set(evidence_statuses))


def test_promotion_gate_matrix_and_install_preview_keep_live_installs_blocked() -> None:
    matrix = _load_json(MANIFEST_DIR / "promotion-gate-matrix.json")
    preview = _load_json(MANIFEST_DIR / "live-install-command-preview.json")
    unique = _load_json(MANIFEST_DIR / "unique-target-research-packets.json")
    summary = (MANIFEST_DIR / "promotion-gate-summary.md").read_text(encoding="utf-8")
    covered_count = sum(
        1
        for item in matrix["items"]
        if item["final_status"] == "covered-by-existing-installable-catalog"
    )
    blocked_count = len(matrix["items"]) - covered_count

    assert matrix["summary"] == {
        "unique_targets": 289,
        "covered_by_existing_installable_catalog": covered_count,
        "ready_for_repo_promotion": 0,
        "ready_for_live_install": 0,
        "blocked_until_trust_gates": blocked_count,
    }
    assert len(matrix["items"]) == 289
    auth_counts = matrix["gate_status_counts"]["auth review"]
    assert sum(auth_counts.values()) == 289
    assert auth_counts["auth-required-review"] == sum(
        1
        for item in matrix["items"]
        if item["auth_required"] and item["final_status"] != "covered-by-existing-installable-catalog"
    )
    assert auth_counts["existing-catalog-row-owns-auth-boundaries"] == covered_count
    assert auth_counts["metadata-only-no-auth-detected"] == sum(
        1
        for item in matrix["items"]
        if not item["auth_required"] and item["final_status"] != "covered-by-existing-installable-catalog"
    )
    source_counts = matrix["gate_status_counts"]["source-list evidence"]
    assert sum(source_counts.values()) == 289
    assert (
        source_counts.get("source-list-found-existing-installable-catalog", 0)
        + source_counts.get("existing-installable-catalog-row-present", 0)
        == covered_count
    )
    assert matrix["gate_status_counts"]["live install"] == {
        "blocked": blocked_count,
        "no-new-live-install-command-emitted": covered_count,
    }
    final_counts = {
        status: sum(1 for item in matrix["items"] if item["final_status"] == status)
        for status in {item["final_status"] for item in matrix["items"]}
    }
    assert final_counts == {
        "blocked-until-trust-gates": blocked_count,
        "covered-by-existing-installable-catalog": covered_count,
    }
    assert not any(item["install_command"] for item in matrix["items"])

    unique_by_url = {packet["normalized_url"]: packet for packet in unique["packets"]}
    for item in matrix["items"]:
        packet = unique_by_url[item["normalized_url"]]
        if item["final_status"] == "covered-by-existing-installable-catalog":
            assert _existing_rows_are_trust_cleared(packet["existing_rows"])
        else:
            assert item["gate_statuses"]["live install"] == "blocked"

    terraform = next(
        item
        for item in matrix["items"]
        if item["normalized_url"] == "https://github.com/antonbabenko/terraform-skill"
    )
    assert terraform["existing_integration_status"] == "covered-by-existing-inspection-required"
    assert terraform["final_status"] == "blocked-until-trust-gates"
    assert terraform["gate_statuses"]["live install"] == "blocked"
    assert terraform["gate_statuses"]["license review"] != "existing-catalog-row-owns-license-and-attribution"

    assert preview["status"] == "no-live-install-commands-emitted"
    assert preview["command_count"] == 0
    assert preview["commands"] == []
    assert preview["covered_existing_target_count"] == covered_count
    assert len(preview["covered_existing_targets"]) == covered_count
    assert preview["blocked_target_count"] == blocked_count
    assert len(preview["blocked_targets"]) == blocked_count
    assert "https://github.com/antonbabenko/terraform-skill" not in {
        item["normalized_url"] for item in preview["covered_existing_targets"]
    }
    assert "https://github.com/antonbabenko/terraform-skill" in {
        item["normalized_url"] for item in preview["blocked_targets"]
    }
    assert "remaining packet files are promotion work queues" in summary


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
    assert audit["status_counts"]["audited"] == 288
    assert audit["status_counts"]["terminal-blocker"] == 1
    assert audit["auth_required_count"] >= 49
    assert audit["security_indicator_target_count"] >= 1

    by_url = {item["normalized_url"]: item for item in audit["items"]}
    nvidia = by_url["https://github.com/NVIDIA/skills-"]
    assert nvidia["status"] == "terminal-blocker"
    assert "tree API unavailable" in nvidia["blockers"][0]
    csvglow = by_url["https://github.com/Ratnaditya-J/csvglow"]
    assert csvglow["status"] == "audited"
    assert csvglow["readme"]["path"]
    assert csvglow["license"]["status"] in {"ok", "error"}
    assert csvglow["candidate_code_executed"] is False


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
    assert payload["deep_audited"] == 288
    assert payload["deep_terminal_blockers"] == 1
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
    assert '"deep_audited": 288' in result.stdout


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
        "intake_decision": "reference_only",
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
                "status": "global-only-or-avoid",
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
                skill_md.write_text("---\nname: fixture\n---\n", encoding="utf-8")
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


def test_apply_promotions_validator_rejects_missing_source_summary_row(tmp_path, monkeypatch):
    overrides = [_valid_apply_override(normalized_url="https://example.test/missing")]
    rows = [{"normalized_url": "https://example.test/source"}]
    apply_promotions = _prepare_apply_promotion_fixture(tmp_path, monkeypatch, overrides, rows=rows)

    errors = apply_promotions.validate_override_records(overrides, rows)

    assert any("normalized_url has no source summary row" in error for error in errors)


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
    summary.update(
        {
            "install_commands_published": 0,
            "live_installs_recorded": 1,
            "status_counts": {"install-now-after-trust-gate": 0},
            "sync_kind_counts": {"skills-cli": 0},
        }
    )
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
    summary.update(
        {
            "install_commands_published": 1,
            "live_installs_recorded": 1,
            "status_counts": {"install-now-after-trust-gate": 1},
            "sync_kind_counts": {"skills-cli": 1},
        }
    )
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
            "auth_required": False,
            "licenses": ["MIT"],
            "source_list_evidence": {"evidence_status": "source-list-found"},
            "blockers": [],
            "live_install_eligible": False,
            "repo_mutation_eligible": False,
            "install_command": "",
        },
        {
            "packet_id": "N002",
            "normalized_url": "https://example.test/blocked",
            "raw_indexes": [2],
            "existing_integration_status": "needs-promotion-review",
            "existing_rows": [],
            "auth_required": True,
            "licenses": ["MIT"],
            "source_list_evidence": {"evidence_status": "source-list-found"},
            "blockers": ["source-list evidence"],
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
        {"unique_targets": ["https://example.test/covered", "https://example.test/blocked"]},
    )
    (tmp_path / promoter.SUMMARY_FILE).write_text(
        promoter.promotion_gate_summary_text(matrix, preview),
        encoding="utf-8",
    )
    return promoter


def test_promotion_gate_matrix_blocks_inspection_required_existing_rows() -> None:
    promoter = _load_promoter_module()
    unique_packets = [
        {
            "packet_id": "N001",
            "normalized_url": "https://example.test/inspect",
            "raw_indexes": [1],
            "existing_integration_status": "covered-by-existing-inspection-required",
            "existing_rows": [
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
            "blockers": ["license review", "security review", "target-specific validation"],
        }
    ]

    matrix = promoter.build_gate_matrix(unique_packets)
    preview = promoter.build_install_preview(unique_packets)

    assert matrix["summary"]["covered_by_existing_installable_catalog"] == 0
    assert matrix["summary"]["blocked_until_trust_gates"] == 1
    assert matrix["items"][0]["final_status"] == "blocked-until-trust-gates"
    assert matrix["items"][0]["gate_statuses"]["live install"] == "blocked"
    assert preview["covered_existing_targets"] == []
    assert preview["blocked_targets"][0]["normalized_url"] == "https://example.test/inspect"


def test_promotion_validator_rejects_non_trust_cleared_covered_packet(tmp_path, monkeypatch):
    promoter = _prepare_promoter_validation_fixture(tmp_path, monkeypatch)
    unique = promoter.load_json(promoter.UNIQUE_PACKET_FILE)
    unique["packets"][0]["existing_rows"] = [
        {
            "name": "needs-inspection",
            "status": "inspect-then-install",
            "trust_tier": "needs-inspection",
            "has_install_command": True,
            "sync_kind": "skills-cli",
        }
    ]
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
    assert (
        "covered packet https://example.test/covered lacks trust-cleared existing catalog row"
        in result["errors"]
    )


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
    preview["covered_existing_targets"][0]["normalized_url"] = "https://example.test/wrong"
    _write_promoter_json(tmp_path, promoter.INSTALL_PREVIEW_FILE, preview)

    result = promoter.validate_outputs()

    assert result["ok"] is False
    assert "live install preview covered targets do not match unique packets" in result["errors"]


def test_promotion_validator_detects_preview_count_drift(tmp_path, monkeypatch):
    promoter = _prepare_promoter_validation_fixture(tmp_path, monkeypatch)
    preview = promoter.load_json(promoter.INSTALL_PREVIEW_FILE)
    preview["blocked_target_count"] = 99
    _write_promoter_json(tmp_path, promoter.INSTALL_PREVIEW_FILE, preview)

    result = promoter.validate_outputs()

    assert result["ok"] is False
    assert "live install preview blocked target count does not match rows" in result["errors"]


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
    assert "gate matrix trust gates drifted" in result["errors"]


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
    assert all(item["remaining_blockers"] for item in evidence["items"])
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
