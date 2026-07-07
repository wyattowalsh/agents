"""Coverage checks for the July 2026 candidate corpus intake."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
RECORDS_DIR = MANIFEST_DIR / "records"
AUTHORING_DIR = ROOT / "docs" / "src" / "authoring" / "skills"
CATALOG_INDEX = ROOT / "docs" / "public" / "generated-registries" / "skills-catalog-index.json"
CATALOG_DIR = ROOT / "docs" / "src" / "authoring" / "skills"
GENERATED_EXTERNAL_DIR = ROOT / "docs" / "src" / "content" / "docs" / "skills" / "catalog" / "external"
CATALOG_PREFIX = "candidate-corpus-"
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
    "csvglow",
    "swiftdata-pro",
    "swiftui-design-principles",
}
PROMOTED_CANDIDATE_NAMES = {
    "candidate-corpus-001-csvglow",
    "candidate-corpus-002-swiftdata-agent-skill",
    "candidate-corpus-003-swiftui-design-principles",
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

    assert summary["rows_written"] == 289
    assert summary["unique_targets"] == 289
    assert summary["install_commands_published"] == len(PROMOTED_SKILL_NAMES)
    assert summary["live_installs_recorded"] == len(PROMOTED_SKILL_NAMES)
    assert summary["status_counts"] == {
        "global-only-or-avoid": 289 - len(PROMOTED_SKILL_NAMES),
        "install-now-after-trust-gate": len(PROMOTED_SKILL_NAMES),
    }
    assert summary["sync_kind_counts"] == {
        "none": 289 - len(PROMOTED_SKILL_NAMES),
        "skills-cli": len(PROMOTED_SKILL_NAMES),
    }
    assert sum(source_list_counts.values()) == 289
    assert source_list_counts["source-list-found"] >= 13
    assert "not-run" not in source_list_counts
    assert len(catalog_paths) == 289 - len(PROMOTED_SKILL_NAMES)
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
    assert "execution results must be recorded by the runner" in final_report
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

    assert summary["rows_written"] == 289
    assert summary["unique_targets"] == 289
    assert summary["install_commands_published"] == len(PROMOTED_SKILL_NAMES)
    assert summary["live_installs_recorded"] == len(PROMOTED_SKILL_NAMES)
    assert len(generated_rows) == 289 - len(PROMOTED_SKILL_NAMES)
    assert len(indexed_rows) == 289 - len(PROMOTED_SKILL_NAMES)
    assert {row["syncKind"] for row in indexed_rows} == {"none"}
    assert {row["status"] for row in indexed_rows} == {"global-only-or-avoid"}
    assert not any(row.get("installCommand") for row in indexed_rows)
    assert not any(row.get("useCommand") for row in indexed_rows)
    assert set(promoted_rows) == PROMOTED_SKILL_NAMES
    for skill_name, promoted_row in promoted_rows.items():
        assert promoted_row["syncKind"] == "skills-cli"
        assert promoted_row["status"] == "install-now-after-trust-gate"
        assert promoted_row["installCommand"].startswith("npx skills add ")
        assert f"--skill {skill_name}" in promoted_row["installCommand"]
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
        assert f"--skill {skill_name}" in text


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
    state_report = (MANIFEST_DIR / "full-integration-state.md").read_text(encoding="utf-8")

    assert progress["phase"] == "research-graph-ready"
    assert progress["complete"] is False
    assert progress["raw_candidates"] == 293
    assert progress["unique_normalized_targets"] == 289
    assert progress["live_install"]["eligible_count"] == 0
    assert progress["live_install"]["status"] == "no-new-live-installs-eligible"
    assert progress["promotion_readiness"]["covered_by_existing_installable_catalog"] == 14
    assert progress["promotion_readiness"]["ready_for_repo_promotion"] == 0
    assert progress["promotion_readiness"]["ready_for_live_install"] == 0
    assert progress["promotion_readiness"]["blocked_until_trust_gates"] == 275

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
    assert "Existing installable catalog rows cover the W00 targets" in state_report


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

    assert readiness["status"] == "existing-coverage-reconciled-with-trust-gated-backlog"
    assert readiness["summary"] == {
        "unique_targets": 289,
        "covered_by_existing_installable_catalog": 14,
        "ready_for_repo_promotion": 0,
        "ready_for_live_install": 0,
        "blocked_until_trust_gates": 275,
    }
    assert len(readiness["covered_by_existing_installable_catalog"]) == 14
    assert readiness["ready_for_repo_promotion"] == []
    assert readiness["ready_for_live_install"] == []
    assert len(readiness["blocked_until_trust_gates"]) == 275
    assert progress["promotion_readiness"] == readiness["summary"]

    for item in readiness["covered_by_existing_installable_catalog"]:
        assert item["terminal_status"] == "covered-by-existing-installable-catalog"
        assert item["live_install_eligible"] is False
        assert item["repo_mutation_eligible"] is False
        assert item["install_command"] == ""
        assert item["existing_rows"]
        assert item["blocking_gates"] == []

    for item in readiness["blocked_until_trust_gates"]:
        assert item["terminal_status"] == "blocked-until-trust-gates"
        assert item["live_install_eligible"] is False
        assert item["repo_mutation_eligible"] is False
        assert item["install_command"] == ""
        assert "source-list evidence" in item["blocking_gates"]
        assert "target-specific validation" in item["blocking_gates"]


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
        "antonbabenko/terraform-skill",
        "avdlee/swift-concurrency-agent-skill",
    ]:
        item = by_source[source]
        assert item["coverage_status"] == "covered-by-existing-installable-catalog"
        assert item["existing_rows"]
        assert any(row["has_install_command"] for row in item["existing_rows"])

    by_decision_url = {item["normalized_url"].lower(): item for item in decisions["decisions"]}
    for source in ["wordpress/agent-skills", "tanstack/cli", "dimillian/skills"]:
        item = by_source[source]
        assert item["coverage_status"] == "needs-promotion-review"
        assert item["existing_rows"] == []
        assert by_decision_url[item["normalized_url"].lower()]["decision"] == "reference_only"

    by_url = {lane["normalized_url"].lower(): lane for lane in graph["unique_target_lanes"]}
    cloudflare = by_url["https://github.com/cloudflare/skills"]
    assert cloudflare["existing_integration_status"] == "covered-by-existing-installable-catalog"
    assert cloudflare["terminal_decision_status"] == "covered-by-existing-catalog"


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
    assert by_wave["W99"]["target_count"] >= 1


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


def test_promotion_gate_matrix_and_install_preview_keep_live_installs_blocked() -> None:
    matrix = _load_json(MANIFEST_DIR / "promotion-gate-matrix.json")
    preview = _load_json(MANIFEST_DIR / "live-install-command-preview.json")
    summary = (MANIFEST_DIR / "promotion-gate-summary.md").read_text(encoding="utf-8")

    assert matrix["summary"] == {
        "unique_targets": 289,
        "covered_by_existing_installable_catalog": 14,
        "ready_for_repo_promotion": 0,
        "ready_for_live_install": 0,
        "blocked_until_trust_gates": 275,
    }
    assert len(matrix["items"]) == 289
    auth_counts = matrix["gate_status_counts"]["auth review"]
    assert sum(auth_counts.values()) == 289
    assert auth_counts["auth-required-review"] == sum(1 for item in matrix["items"] if item["auth_required"])
    assert (
        auth_counts["metadata-only-no-auth-detected"] + auth_counts["existing-catalog-row-owns-auth-boundaries"]
        == sum(1 for item in matrix["items"] if not item["auth_required"])
    )
    source_counts = matrix["gate_status_counts"]["source-list evidence"]
    assert source_counts == {
        "source-list-error-needs-manual-review": 21,
        "source-list-found-existing-installable-catalog": 14,
        "source-list-found-pending-promotion-review": 222,
        "source-list-timeout-needs-retry": 32,
    }
    assert matrix["gate_status_counts"]["live install"] == {
        "blocked": 275,
        "no-new-live-install-command-emitted": 14,
    }
    final_counts = {
        status: sum(1 for item in matrix["items"] if item["final_status"] == status)
        for status in {item["final_status"] for item in matrix["items"]}
    }
    assert final_counts == {"blocked-until-trust-gates": 275, "covered-by-existing-installable-catalog": 14}
    assert not any(item["install_command"] for item in matrix["items"])

    assert preview["status"] == "no-live-install-commands-emitted"
    assert preview["command_count"] == 0
    assert preview["commands"] == []
    assert preview["covered_existing_target_count"] == 14
    assert len(preview["covered_existing_targets"]) == 14
    assert preview["blocked_target_count"] == 275
    assert len(preview["blocked_targets"]) == 275
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
            "existing_rows": [{"name": "existing-covered"}],
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
            "W01",
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
