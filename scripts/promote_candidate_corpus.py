#!/usr/bin/env python3
"""Build trust-gated promotion packets for the July 2026 corpus.

The generator consumes repo-local intake manifests only. It does not clone,
install, import, execute, or enable candidate code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from wagents.candidate_corpus_reports import generated_reference_materialization_errors
from wagents.site_model import SUPPORTED_AGENT_IDS

if TYPE_CHECKING:
    from collections.abc import Iterable

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
AUTHORING_DIR = ROOT / "docs" / "src" / "authoring" / "skills"
EXPECTED_RAW_COUNT = 293
EXPECTED_UNIQUE_COUNT = 289
EXPECTED_CLASSIFICATION_COUNTS = {
    "installable-existing": 121,
    "inspection-existing": 6,
    "integrated-reference": 158,
    "integrated-quarantine-reference": 4,
}
GENERATED_REFERENCE_CLASSIFICATIONS = {
    "integrated-reference",
}

RAW_PACKET_FILE = "raw-research-packets.json"
UNIQUE_PACKET_FILE = "unique-target-research-packets.json"
GATE_MATRIX_FILE = "promotion-gate-matrix.json"
INSTALL_PREVIEW_FILE = "live-install-command-preview.json"
SUMMARY_FILE = "promotion-gate-summary.md"
DEEP_AUDIT_FILE = "deep-source-audit.json"
HARNESS_ASSURANCE_FILE = "harness-install-assurance.json"
NON_SKILL_ASSURANCE_FILE = "non-skill-install-assurance.json"
INTEGRATION_TARGET_FILE = "integration-targets.json"

_SOURCE_LIST_EVIDENCE_GATE_STATUSES: tuple[tuple[str, str], ...] = (
    ("source-list-found", "source-list-found-pending-promotion-review"),
    ("source-list-no-skills-listed", "source-list-reviewed-no-installable-skills"),
    ("source-list-timeout", "source-list-timeout-needs-retry"),
    ("source-list-unavailable", "source-list-unavailable-needs-manual-review"),
    ("source-list-empty-or-unparsed", "source-list-empty-or-unparsed-needs-parser-review"),
    ("source-list-error", "source-list-error-needs-manual-review"),
)

TERMINAL_DECISION_MAP = {
    "duplicate_covered": "merged",
    "hard_blocked_inaccessible": "hard-blocked",
    "hard_blocked_quarantine": "hard-blocked",
    "integrated_collection_surface": "collection-surface",
    "integrated_existing_surface": "existing-surface",
    "integrated_mcp_surface": "mcp-surface",
    "integrated_native_surface": "native-surface",
    "integrated_plugin_surface": "plugin-surface",
    "integrated_skill_catalog_surface": "skill-catalog-surface",
    "integrated_tool_surface": "tool-surface",
    "merge_into_existing": "existing-surface",
}

TERMINAL_ROUTE_CHECKS = [
    "source-list evidence",
    "license review",
    "security review",
    "attribution review",
    "auth review",
    "docs-steward promotion",
    "target-specific validation",
]
COVERAGE_TRUST_CLEARED = "covered-by-existing-installable-catalog"
TRUST_CLEARED_STATUS = "install-now-after-trust-gate"
TRUST_CLEARED_TIER = "curated-trust-gated"


def now() -> str:
    return datetime.now(UTC).isoformat()


def load_json(name: str) -> Any:
    path = MANIFEST_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_optional_json(name: str, default: Any) -> Any:
    path = MANIFEST_DIR / name
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, payload: Any) -> None:
    path = MANIFEST_DIR / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def semantic_json_sha256(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    payload.pop("generated_at", None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def dedupe(values: Iterable[Any]) -> list[Any]:
    seen = set()
    result = []
    for value in values:
        key = json.dumps(value, sort_keys=True, ensure_ascii=False) if isinstance(value, (dict, list)) else value
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def by_normalized(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["normalized_url"].lower(): item for item in items}


def normalized_raw_indexes(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    indexes = {
        int(index)
        for index in value
        if (isinstance(index, int) and not isinstance(index, bool)) or (isinstance(index, str) and index.isdigit())
    }
    return sorted(indexes)


def integration_target_is_accounted(item: dict[str, Any]) -> bool:
    """Return whether a target has a durable terminal integration identity."""
    return bool(item.get("catalog_rows")) or item.get("hard_blocked") is True


def integration_target_errors(payload: Any, normalized: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["integration-targets.json is not an object"]
    items = payload.get("items", [])
    if not isinstance(items, list):
        return ["integration-targets.json items must be a list"]
    targets = [item for item in items if isinstance(item, dict)]
    if len(targets) != len(items):
        errors.append("integration targets contain non-object rows")
    if payload.get("raw_entries_covered") != EXPECTED_RAW_COUNT:
        errors.append("integration targets raw entry count is not 293")
    if payload.get("unique_targets") != EXPECTED_UNIQUE_COUNT or len(targets) != EXPECTED_UNIQUE_COUNT:
        errors.append("integration target count is not 289")
    if payload.get("integrated_targets") != EXPECTED_UNIQUE_COUNT:
        errors.append("integration target integrated count is not 289")
    if payload.get("unintegrated_targets") != 0:
        errors.append("integration target unintegrated count is not zero")

    normalized_targets = normalized.get("unique_targets", []) if isinstance(normalized, dict) else []
    target_urls = [str(item.get("normalized_url") or "").lower() for item in targets]
    normalized_urls = [str(url).lower() for url in normalized_targets]
    if len(target_urls) != len(set(target_urls)):
        errors.append("integration targets contain duplicate normalized URLs")
    if set(target_urls) != set(normalized_urls):
        errors.append("integration target URLs do not match normalized targets")
    normalized_entries = normalized.get("entries", []) if isinstance(normalized, dict) else []
    expected_raw_by_url: dict[str, list[int]] = defaultdict(list)
    for entry in normalized_entries if isinstance(normalized_entries, list) else []:
        if not isinstance(entry, dict) or not isinstance(entry.get("normalized_url"), str):
            continue
        raw_index = entry.get("raw_index")
        if isinstance(raw_index, int) and not isinstance(raw_index, bool):
            expected_raw_by_url[entry["normalized_url"].lower()].append(raw_index)

    classifications: Counter[str] = Counter()
    raw_indexes: list[int] = []
    target_skill_keys: set[tuple[str, str]] = set()
    generated_reference_count = 0
    for item in targets:
        normalized_url = str(item.get("normalized_url") or "")
        key = normalized_url.lower()
        item_raw_indexes = normalized_raw_indexes(item.get("raw_indexes"))
        raw_indexes.extend(item_raw_indexes)
        if item_raw_indexes != sorted(expected_raw_by_url.get(key, [])):
            errors.append(f"integration target raw indexes drifted: {normalized_url}")
        classification = str(item.get("integration_classification") or "")
        if classification not in EXPECTED_CLASSIFICATION_COUNTS:
            errors.append(f"integration target has invalid classification: {normalized_url}")
        else:
            classifications[classification] += 1
        hard_blocked = item.get("hard_blocked") is True
        if hard_blocked != (classification == "integrated-quarantine-reference"):
            errors.append(f"integration target hard-block state drifted: {normalized_url}")
        if hard_blocked and item.get("trust_cleared_installable") is not False:
            errors.append(f"hard-blocked target is marked installable: {normalized_url}")

        rows = item.get("catalog_rows", [])
        if not isinstance(rows, list):
            errors.append(f"integration target catalog rows are not a list: {normalized_url}")
            rows = []
        if hard_blocked:
            if rows:
                errors.append(f"hard-blocked target exposes catalog rows: {normalized_url}")
        elif not rows:
            errors.append(f"integration target has no catalog rows: {normalized_url}")
            continue
        install_rows = [row for row in rows if isinstance(row, dict) and existing_row_has_install_surface(row)]
        derived_installable = bool(install_rows) and all(existing_row_trust_cleared(row) for row in install_rows)
        if hard_blocked:
            derived_installable = False
        if item.get("trust_cleared_installable") is not derived_installable:
            errors.append(f"integration target installability disagrees with catalog rows: {normalized_url}")
        generated_name = str(item.get("generated_reference_name") or "")
        generated_path = str(item.get("generated_reference_path") or "")
        has_generated_identity = bool(generated_name and generated_path)
        expects_generated_identity = classification in GENERATED_REFERENCE_CLASSIFICATIONS
        if bool(generated_name) != bool(generated_path):
            errors.append(f"integration target has incomplete generated reference identity: {normalized_url}")
        elif expects_generated_identity and not has_generated_identity:
            errors.append(
                f"integration target reference classification lacks generated reference identity: {normalized_url}"
            )
        elif not expects_generated_identity and has_generated_identity:
            errors.append(
                f"integration target existing classification exposes generated reference identity: {normalized_url}"
            )
        generated_reference_count += int(has_generated_identity)
        matching_reference_rows: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                errors.append(f"integration target has a non-object catalog row: {normalized_url}")
                continue
            row_name = str(row.get("name") or "")
            row_path = str(row.get("path") or "")
            target_skill_key = (key, row_name)
            if not row_name or target_skill_key in target_skill_keys:
                errors.append(f"integration target has a duplicate or empty URL/skill mapping: {normalized_url}")
            target_skill_keys.add(target_skill_key)
            if row_name.startswith("candidate-corpus-") or "candidate-corpus-" in row_path:
                errors.append(f"integration target retains a candidate-corpus authoring row: {normalized_url}")
            if has_generated_identity and row_name == generated_name and row_path == generated_path:
                matching_reference_rows.append(row)
        if has_generated_identity:
            if len(matching_reference_rows) != 1:
                errors.append(
                    f"integration target generated reference identity does not match exactly one catalog row: "
                    f"{normalized_url}"
                )
            else:
                reference_row = matching_reference_rows[0]
                if (
                    reference_row.get("has_install_command") is True
                    or bool(str(reference_row.get("install_command") or "").strip())
                    or str(reference_row.get("sync_kind") or "").strip() != "none"
                ):
                    errors.append(f"generated integration reference exposes an install surface: {normalized_url}")

    if sorted(raw_indexes) != list(range(1, EXPECTED_RAW_COUNT + 1)):
        errors.append("integration targets do not cover raw indexes 1 through 293 exactly once")
    if dict(classifications) != EXPECTED_CLASSIFICATION_COUNTS:
        errors.append("integration target classifications do not match the expected 121/6/158/4 split")
    if payload.get("classification_counts") != EXPECTED_CLASSIFICATION_COUNTS:
        errors.append("integration target top-level classification counts drifted")
    if payload.get("generated_reference_count") != generated_reference_count:
        errors.append("integration target generated reference count drifted")
    expected_reference_count = sum(
        EXPECTED_CLASSIFICATION_COUNTS.get(classification, 0) for classification in GENERATED_REFERENCE_CLASSIFICATIONS
    )
    if generated_reference_count != expected_reference_count:
        errors.append("integration target item generated reference count does not match reference classifications")
    errors.extend(
        generated_reference_materialization_errors(
            payload,
            root=ROOT,
            authoring_dir=AUTHORING_DIR,
            marker="GENERATED-INTEGRATION-TARGET-JUL2026",
        )
    )
    return errors


def existing_row_has_install_surface(row: dict[str, Any]) -> bool:
    has_install_command = bool(row.get("has_install_command")) or bool(str(row.get("install_command", "")).strip())
    sync_kind = str(row.get("sync_kind", "")).strip()
    return has_install_command and sync_kind not in {"", "none"}


def existing_row_trust_cleared(row: dict[str, Any]) -> bool:
    return (
        existing_row_has_install_surface(row)
        and row.get("status") == TRUST_CLEARED_STATUS
        and row.get("trust_tier") == TRUST_CLEARED_TIER
    )


def packet_has_trust_cleared_existing_row(packet: dict[str, Any]) -> bool:
    rows = packet.get("catalog_rows", packet.get("existing_rows", []))
    if not isinstance(rows, list):
        return False
    install_surface_rows = [row for row in rows if isinstance(row, dict) and existing_row_has_install_surface(row)]
    return bool(install_surface_rows) and all(existing_row_trust_cleared(row) for row in install_surface_rows)


def packet_has_trust_cleared_coverage(packet: dict[str, Any]) -> bool:
    return packet.get("trust_cleared_installable") is True and packet_has_trust_cleared_existing_row(packet)


def readiness_by_url(readiness: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    for bucket in (
        "covered_by_existing_installable_catalog",
        "ready_for_repo_promotion",
        "ready_for_live_install",
        "terminal_native_or_hard_blocked",
    ):
        for item in readiness.get(bucket, []):
            result[item["normalized_url"].lower()] = item
    return result


def subresource(record: dict[str, Any]) -> str:
    parts = []
    if record.get("tree_subpath"):
        ref = record.get("tree_ref") or "unknown-ref"
        parts.append(f"tree:{ref}/{record['tree_subpath']}")
    if record.get("fragment"):
        parts.append(f"fragment:#{record['fragment']}")
    return "; ".join(parts)


def idiosyncrasies(record: dict[str, Any], normalized_entry: dict[str, Any] | None) -> list[str]:
    notes: list[str] = []
    if record.get("fragment"):
        notes.append(f"raw URL fragment preserved: #{record['fragment']}")
    if record.get("tree_subpath"):
        notes.append(f"tree subdirectory target preserved: {record.get('tree_ref')}/{record['tree_subpath']}")
    if record.get("duplicate_group"):
        notes.append(f"duplicate group raw indexes: {record['duplicate_group']}")
    if normalized_entry and normalized_entry.get("malformed_reason"):
        notes.append(f"malformed source evidence: {normalized_entry['malformed_reason']}")
    if record.get("risk_keywords"):
        notes.append(f"risk keywords: {', '.join(record['risk_keywords'])}")
    if record.get("github_metadata_packet", {}).get("archived"):
        notes.append("GitHub metadata reports repository is archived")
    return notes


def source_status(record: dict[str, Any]) -> str:
    packet = record.get("source_capture_packet", {})
    metadata = record.get("github_metadata_packet", {})
    if metadata.get("status") == "unavailable" or packet.get("github_api_status") == "unavailable":
        return "unavailable"
    if packet.get("git_status") == "ok" or metadata.get("status") == "ok":
        return "ok"
    return packet.get("git_status") or metadata.get("status") or "unknown"


def surface_decision(record: dict[str, Any]) -> str:
    decision = record.get("install_or_integration_decision", "")
    return TERMINAL_DECISION_MAP.get(decision, "native-surface")


def record_route_requirements(record: dict[str, Any], readiness_item: dict[str, Any] | None) -> list[str]:
    requirements = list(
        readiness_item.get("terminal_route_requirements", TERMINAL_ROUTE_CHECKS)
        if readiness_item
        else TERMINAL_ROUTE_CHECKS
    )
    if record.get("skipped_reason"):
        requirements.append(record["skipped_reason"])
    if record.get("install_or_integration_decision") == "duplicate_covered":
        requirements.append("duplicate raw entry covered by canonical normalized target")
    if source_status(record) == "unavailable":
        requirements.append("upstream unavailable or malformed")
    return dedupe(requirements)


def build_context() -> dict[str, Any]:
    normalized = load_json("normalized-urls.json")
    integration_targets = load_json(INTEGRATION_TARGET_FILE)
    target_errors = integration_target_errors(integration_targets, normalized)
    if target_errors:
        raise ValueError("invalid integration target ledger: " + "; ".join(target_errors))
    records = load_json("all-records.json")["records"]
    decisions = load_json("integration-decisions.json")["decisions"]
    coverage = load_json("existing-integration-coverage.json")
    graph = load_json("research-task-graph.json")
    readiness = load_json("promotion-readiness-queue.json")
    wave_plan = load_json("promotion-wave-plan.json")
    schema = load_json("research-packet-schema.json")
    source_list_evidence = load_optional_json("safe-wave-source-list-evidence.json", {"items": []})

    normalized_entries_by_raw = {entry["raw_index"]: entry for entry in normalized["entries"]}
    raw_lanes_by_index = {lane["raw_index"]: lane for lane in graph["raw_lanes"]}
    unique_lanes_by_url = by_normalized(graph["unique_target_lanes"])
    decisions_by_url = by_normalized(decisions)
    coverage_by_url = by_normalized(coverage["items"])
    readiness_items_by_url = readiness_by_url(readiness)
    wave_by_url = {
        target["normalized_url"].lower(): {
            "wave_id": wave["wave_id"],
            "name": wave["name"],
            "description": wave["description"],
            "mutation_policy": wave["mutation_policy"],
        }
        for wave in wave_plan["waves"]
        for target in wave["targets"]
    }
    source_list_by_url = by_normalized(source_list_evidence.get("items", []))
    integration_targets_by_url = by_normalized(integration_targets["items"])

    return {
        "normalized": normalized,
        "integration_targets": integration_targets,
        "integration_targets_by_url": integration_targets_by_url,
        "records": records,
        "schema": schema,
        "normalized_entries_by_raw": normalized_entries_by_raw,
        "raw_lanes_by_index": raw_lanes_by_index,
        "unique_lanes_by_url": unique_lanes_by_url,
        "decisions_by_url": decisions_by_url,
        "coverage_by_url": coverage_by_url,
        "readiness_by_url": readiness_items_by_url,
        "wave_by_url": wave_by_url,
        "source_list_by_url": source_list_by_url,
    }


def build_raw_packets(context: dict[str, Any]) -> list[dict[str, Any]]:
    packets = []
    for record in context["records"]:
        key = record["normalized_url"].lower()
        normalized_entry = context["normalized_entries_by_raw"].get(record["raw_index"])
        raw_lane = context["raw_lanes_by_index"][record["raw_index"]]
        readiness_item = context["readiness_by_url"].get(key)
        coverage_item = context["coverage_by_url"].get(key, {})
        integration_target = context["integration_targets_by_url"][key]
        source_list_item = context["source_list_by_url"].get(key)
        packet = {
            "packet_id": f"U{record['raw_index']:03d}",
            "raw_index": record["raw_index"],
            "raw_url": record["raw_url"],
            "normalized_url": record["normalized_url"],
            "subresource": subresource(record),
            "source_name": record["source_name"],
            "upstream_status": source_status(record),
            "inspected_commit_sha": record["inspected_commit_sha"],
            "latest_release_or_commit_date": record["latest_release_or_commit_date"],
            "license": record["license"],
            "artifact_types_found": record["artifact_types_found"],
            "idiosyncrasies": idiosyncrasies(record, normalized_entry),
            "auth_required": record["auth_required"],
            "env_vars_or_credentials": record["env_vars_or_credentials"],
            "security_notes": record["safety_notes"],
            "attribution_notes": record["attribution_notes"],
            "surface_decision": surface_decision(record),
            "install_command": "",
            "live_install_eligible": False,
            "docs_steward_surfaces": record["docs_steward_surfaces"],
            "tests_or_checks_run": record["tests_or_checks_run"],
            "terminal_route_requirements": record_route_requirements(record, readiness_item),
            "reviewer_notes": record["reviewer_notes"],
            "current_intake_decision": record["install_or_integration_decision"],
            "risk_tier": record["risk_tier"],
            "risk_keywords": record["risk_keywords"],
            "canonical_source": record["canonical_source"],
            "integration_classification": integration_target["integration_classification"],
            "integration_surface": integration_target["integration_surface"],
            "trust_cleared_installable": integration_target["trust_cleared_installable"],
            "hard_blocked": integration_target["hard_blocked"],
            "integrated": integration_target_is_accounted(integration_target),
            "catalog_rows": integration_target["catalog_rows"],
            "existing_integration_status": coverage_item.get("coverage_status", "unknown"),
            "existing_rows": coverage_item.get("existing_rows", []),
            "source_list_evidence": source_list_item or {},
            "leaf_checks": raw_lane["leaf_checks"],
            "source_support_matrix": record["source_support_matrix"],
            "github_metadata_packet": record["github_metadata_packet"],
            "license_packet": record["license_packet"],
            "security_packet": record["security_packet"],
            "compliance_packet": record["compliance_packet"],
            "execution_policy": "candidate code was not executed; terminal rows do not emit live install commands",
        }
        packets.append(packet)
    return packets


def grouped_raw_packets(raw_packets: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for packet in raw_packets:
        groups[packet["normalized_url"].lower()].append(packet)
    return groups


def build_unique_packets(context: dict[str, Any], raw_packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = grouped_raw_packets(raw_packets)
    packets = []
    for index, normalized_url in enumerate(context["normalized"]["unique_targets"], 1):
        key = normalized_url.lower()
        raw_group = sorted(groups[key], key=lambda packet: packet["raw_index"])
        primary = raw_group[0]
        coverage_item = context["coverage_by_url"].get(key, {})
        integration_target = context["integration_targets_by_url"][key]
        decision_item = context["decisions_by_url"].get(key, {})
        unique_lane = context["unique_lanes_by_url"][key]
        wave = context["wave_by_url"].get(key, {})
        source_list_item = context["source_list_by_url"].get(key)
        route_requirements = dedupe(
            requirement for packet in raw_group for requirement in packet["terminal_route_requirements"]
        )
        if coverage_item.get("coverage_status") == COVERAGE_TRUST_CLEARED:
            route_requirements = []
        env_values = dedupe([value for packet in raw_group for value in packet["env_vars_or_credentials"]])
        docs_surfaces = sorted({surface for packet in raw_group for surface in packet["docs_steward_surfaces"]})
        artifact_types = sorted({artifact for packet in raw_group for artifact in packet["artifact_types_found"]})
        packet = {
            "packet_id": f"N{index:03d}",
            "normalized_url": normalized_url,
            "source_name": primary["source_name"],
            "raw_indexes": [packet["raw_index"] for packet in raw_group],
            "raw_packet_ids": [packet["packet_id"] for packet in raw_group],
            "canonical_source": decision_item.get("canonical_source") or primary["canonical_source"],
            "upstream_statuses": Counter(packet["upstream_status"] for packet in raw_group),
            "inspected_commit_shas": dedupe([packet["inspected_commit_sha"] for packet in raw_group]),
            "latest_release_or_commit_date": primary["latest_release_or_commit_date"],
            "licenses": dedupe([packet["license"] for packet in raw_group]),
            "artifact_types_found": artifact_types,
            "auth_required": any(packet["auth_required"] for packet in raw_group),
            "env_vars_or_credentials": env_values,
            "security_notes": dedupe([packet["security_notes"] for packet in raw_group]),
            "attribution_notes": dedupe([packet["attribution_notes"] for packet in raw_group]),
            "current_intake_decision": decision_item.get("decision", primary["current_intake_decision"]),
            "surface_decision": unique_lane["terminal_decision_status"],
            "integration_classification": integration_target["integration_classification"],
            "integration_surface": integration_target["integration_surface"],
            "trust_cleared_installable": integration_target["trust_cleared_installable"],
            "hard_blocked": integration_target["hard_blocked"],
            "integrated": integration_target_is_accounted(integration_target),
            "catalog_rows": integration_target["catalog_rows"],
            "existing_integration_status": coverage_item.get("coverage_status", "unknown"),
            "existing_rows": coverage_item.get("existing_rows", []),
            "source_list_evidence": source_list_item or {},
            "install_command": "",
            "live_install_eligible": False,
            "repo_mutation_eligible": False,
            "docs_steward_surfaces": docs_surfaces,
            "terminal_route_requirements": route_requirements,
            "leaf_checks": unique_lane["leaf_checks"],
            "promotion_wave": wave,
            "reviewer_notes": "Unique-target synthesis packet; final promotion requires all raw packet gates to pass.",
        }
        packets.append(packet)
    return packets


def gate_statuses(packet: dict[str, Any]) -> dict[str, str]:
    has_existing_installable = packet_has_trust_cleared_coverage(packet)
    classification = str(packet.get("integration_classification") or "")
    source_list_evidence = packet.get("source_list_evidence") or {}
    source_list_evidence_status = source_list_evidence.get("evidence_status")
    has_source_list = bool(source_list_evidence)
    if has_existing_installable:
        return {
            "source-list evidence": (
                "source-list-found-existing-installable-catalog"
                if source_list_evidence_status == "source-list-found"
                else "existing-installable-catalog-row-present"
            ),
            "license review": "existing-catalog-row-owns-license-and-attribution",
            "security review": "existing-catalog-row-owns-executable-surface-review",
            "attribution review": "existing-catalog-row-owns-attribution",
            "auth review": "existing-catalog-row-owns-auth-boundaries",
            "docs-steward promotion": "existing-catalog-row-generated-and-indexed",
            "target-specific validation": "existing-catalog-row-covered-by-repo-validation",
            "live install": "no-new-live-install-command-emitted",
        }
    if classification == "integrated-quarantine-reference":
        return {
            "source-list evidence": "quarantine-source-evidence-recorded",
            "license review": "quarantine-license-evidence-recorded",
            "security review": "hard-quarantine-risk-recorded",
            "attribution review": "quarantine-source-attribution-recorded",
            "auth review": "non-executable-reference-no-auth-use",
            "docs-steward promotion": "stable-quarantine-reference-generated-and-indexed",
            "target-specific validation": "quarantine-reference-validated",
            "live install": "active-hard-block-no-command",
        }
    if classification == "integrated-reference":
        return {
            "source-list evidence": "source-evidence-recorded-for-reference",
            "license review": "reference-license-evidence-recorded",
            "security review": "non-executable-reference-boundary-recorded",
            "attribution review": "reference-source-attribution-recorded",
            "auth review": "non-executable-reference-no-auth-use",
            "docs-steward promotion": "stable-reference-generated-and-indexed",
            "target-specific validation": "integrated-reference-validated",
            "live install": "non-installable-reference-no-command",
        }
    if classification == "inspection-existing":
        return {
            "source-list evidence": "existing-catalog-surface-recorded",
            "license review": "existing-surface-retains-inspection-gate",
            "security review": "existing-surface-retains-inspection-gate",
            "attribution review": "existing-surface-attribution-recorded",
            "auth review": "existing-surface-retains-inspection-gate",
            "docs-steward promotion": "existing-inspection-surface-indexed",
            "target-specific validation": "integration-present-installability-not-cleared",
            "live install": "inspection-required-no-command",
        }
    license_status = "metadata-present-needs-file-review" if packet["licenses"] else "missing-license-review"
    if any(str(license_value).lower().startswith("not-fetched") for license_value in packet["licenses"]):
        license_status = "license-unavailable-needs-review"
    source_list_status = "pending-source-list-output"
    for evidence_status, gate_status in _SOURCE_LIST_EVIDENCE_GATE_STATUSES:
        if source_list_evidence_status == evidence_status:
            source_list_status = gate_status
            break
    else:
        if has_source_list and source_list_evidence_status:
            source_list_status = f"{source_list_evidence_status}-needs-review"
        elif has_source_list:
            source_list_status = "source-list-evidence-unclassified"
    return {
        "source-list evidence": source_list_status,
        "license review": license_status,
        "security review": "pending-executable-surface-review",
        "attribution review": "pending-source-specific-attribution-note",
        "auth review": "auth-required-review" if packet["auth_required"] else "metadata-only-no-auth-detected",
        "docs-steward promotion": "catalog-intake-present-final-docs-pending",
        "target-specific validation": "pending-target-validation",
        "live install": "terminal-native-surface-no-command",
    }


def build_gate_matrix(unique_packets: list[dict[str, Any]]) -> dict[str, Any]:
    items = []
    gate_counts: dict[str, Counter[str]] = defaultdict(Counter)
    classifications: Counter[str] = Counter()
    integrated_count = 0
    trust_cleared_installable_count = 0
    active_install_blocks = 0
    for packet in unique_packets:
        statuses = gate_statuses(packet)
        classification = str(packet.get("integration_classification") or "")
        classifications[classification] += 1
        integrated_count += int(packet.get("integrated") is True)
        trust_cleared_installable_count += int(packet_has_trust_cleared_coverage(packet))
        active_install_blocks += int(packet.get("hard_blocked") is True)
        for gate, status in statuses.items():
            gate_counts[gate][status] += 1
        items.append({
            "packet_id": packet["packet_id"],
            "normalized_url": packet["normalized_url"],
            "raw_indexes": packet["raw_indexes"],
            "integration_classification": classification,
            "integration_surface": packet["integration_surface"],
            "trust_cleared_installable": packet["trust_cleared_installable"],
            "hard_blocked": packet["hard_blocked"],
            "integrated": packet["integrated"],
            "existing_integration_status": packet["existing_integration_status"],
            "auth_required": packet["auth_required"],
            "gate_statuses": statuses,
            "final_status": classification,
            "install_command": "",
        })
    return {
        "version": 1,
        "generated_at": now(),
        "summary": {
            "unique_targets": len(unique_packets),
            "integrated_targets": integrated_count,
            "unintegrated_targets": len(unique_packets) - integrated_count,
            "classification_counts": dict(sorted(classifications.items())),
            "trust_cleared_installable_targets": trust_cleared_installable_count,
            "integrated_quarantine_targets": classifications["integrated-quarantine-reference"],
            "active_install_blocks": active_install_blocks,
            "ready_for_repo_promotion": 0,
            "ready_for_live_install": 0,
        },
        "terminal_route_checks": TERMINAL_ROUTE_CHECKS,
        "gate_status_counts": {gate: dict(counts) for gate, counts in sorted(gate_counts.items())},
        "items": items,
    }


def build_install_preview(unique_packets: list[dict[str, Any]]) -> dict[str, Any]:
    trust_cleared_installable_targets = [
        {
            "packet_id": packet["packet_id"],
            "normalized_url": packet["normalized_url"],
            "raw_indexes": packet["raw_indexes"],
            "integration_classification": packet["integration_classification"],
            "catalog_rows": packet["catalog_rows"],
        }
        for packet in unique_packets
        if packet_has_trust_cleared_coverage(packet)
    ]
    non_installable_integrated_targets = [
        {
            "packet_id": packet["packet_id"],
            "normalized_url": packet["normalized_url"],
            "raw_indexes": packet["raw_indexes"],
            "integration_classification": packet["integration_classification"],
            "hard_blocked": packet["hard_blocked"],
            "terminal_route_requirements": packet["terminal_route_requirements"],
        }
        for packet in unique_packets
        if not packet_has_trust_cleared_coverage(packet)
    ]
    integrated_quarantine_targets = [
        item for item in non_installable_integrated_targets if item["hard_blocked"] is True
    ]
    classifications = Counter(str(packet["integration_classification"]) for packet in unique_packets)
    return {
        "version": 1,
        "generated_at": now(),
        "status": "no-live-install-commands-emitted",
        "command_count": 0,
        "commands": [],
        "integrated_target_count": sum(packet.get("integrated") is True for packet in unique_packets),
        "unintegrated_target_count": sum(packet.get("integrated") is not True for packet in unique_packets),
        "classification_counts": dict(sorted(classifications.items())),
        "trust_cleared_installable_target_count": len(trust_cleared_installable_targets),
        "trust_cleared_installable_targets": trust_cleared_installable_targets,
        "non_installable_integrated_target_count": len(non_installable_integrated_targets),
        "non_installable_integrated_targets": non_installable_integrated_targets,
        "integrated_quarantine_target_count": len(integrated_quarantine_targets),
        "integrated_quarantine_targets": integrated_quarantine_targets,
        "active_install_blocks": len(integrated_quarantine_targets),
        "rule": (
            "This artifact is command-free. Integration classification does not grant live-install permission, "
            "and hard-quarantine references retain active install blocks."
        ),
    }


def promotion_target_key(item: dict[str, Any]) -> tuple[Any, Any, tuple[Any, ...]]:
    return (item.get("packet_id"), item.get("normalized_url"), tuple(item.get("raw_indexes") or []))


def promotion_final_status(item: dict[str, Any]) -> str:
    return str(item.get("integration_classification") or "")


def expected_matrix_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    classifications = Counter(promotion_final_status(item) for item in items)
    integrated = sum(item.get("integrated") is True for item in items)
    return {
        "unique_targets": len(items),
        "integrated_targets": integrated,
        "unintegrated_targets": len(items) - integrated,
        "classification_counts": dict(sorted(classifications.items())),
        "trust_cleared_installable_targets": sum(item.get("trust_cleared_installable") is True for item in items),
        "integrated_quarantine_targets": classifications["integrated-quarantine-reference"],
        "active_install_blocks": sum(item.get("hard_blocked") is True for item in items),
        "ready_for_repo_promotion": 0,
        "ready_for_live_install": 0,
    }


def expected_gate_status_counts(items: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for item in items:
        statuses = item.get("gate_statuses") or {}
        for gate, status in statuses.items():
            counts[gate][status] += 1
    return {gate: dict(counter) for gate, counter in sorted(counts.items())}


def expected_preview_partitions(
    unique_packets: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    trust_cleared_installable = []
    non_installable_integrated = []
    for packet in unique_packets:
        if packet_has_trust_cleared_coverage(packet):
            trust_cleared_installable.append({
                "packet_id": packet.get("packet_id"),
                "normalized_url": packet.get("normalized_url"),
                "raw_indexes": packet.get("raw_indexes"),
                "integration_classification": packet.get("integration_classification"),
                "catalog_rows": packet.get("catalog_rows"),
            })
        else:
            non_installable_integrated.append({
                "packet_id": packet.get("packet_id"),
                "normalized_url": packet.get("normalized_url"),
                "raw_indexes": packet.get("raw_indexes"),
                "integration_classification": packet.get("integration_classification"),
                "hard_blocked": packet.get("hard_blocked"),
                "terminal_route_requirements": packet.get("terminal_route_requirements"),
            })
    quarantine = [item for item in non_installable_integrated if item["hard_blocked"] is True]
    return trust_cleared_installable, non_installable_integrated, quarantine


def _packet_rows(payload: Any) -> list[dict[str, Any]]:
    packets = payload.get("packets", []) if isinstance(payload, dict) else []
    if not isinstance(packets, list):
        return []
    return [packet for packet in packets if isinstance(packet, dict)]


def _safe_count(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def installed_skill_md_path(raw_path: Any) -> Path:
    path = Path(os.path.expanduser(str(raw_path)))
    return path if path.name == "SKILL.md" else path / "SKILL.md"


def missing_installed_skill_md_paths(override: dict[str, Any]) -> list[str]:
    missing = []
    for raw_path in override.get("installed_paths", []):
        if not isinstance(raw_path, str) or not raw_path.strip():
            continue
        skill_md = installed_skill_md_path(raw_path)
        if not skill_md.exists():
            missing.append(str(skill_md))
    return missing


def live_install_evidence_stats(overrides: list[Any]) -> dict[str, Any]:
    live_rows = [
        override for override in overrides if isinstance(override, dict) and override.get("live_install_executed")
    ]
    installed_paths = [
        raw_path
        for override in live_rows
        for raw_path in override.get("installed_paths", [])
        if isinstance(raw_path, str) and raw_path.strip()
    ]
    missing = [path for override in live_rows for path in missing_installed_skill_md_paths(override)]
    return {
        "live_install_rows": len(live_rows),
        "installed_path_refs": len(installed_paths),
        "verified_skill_md_count": len(installed_paths) - len(missing),
        "missing_installed_skill_md": missing,
    }


def expected_unique_packet_keys(
    raw_packets: list[dict[str, Any]], normalized_targets: list[Any]
) -> list[tuple[str, Any, tuple[Any, ...]]]:
    raw_indexes_by_url: dict[str, list[Any]] = defaultdict(list)
    for packet in raw_packets:
        normalized_url = packet.get("normalized_url")
        if isinstance(normalized_url, str):
            raw_indexes_by_url[normalized_url.lower()].append(packet.get("raw_index"))
    expected = []
    for index, normalized_url in enumerate(normalized_targets, 1):
        raw_indexes = raw_indexes_by_url.get(str(normalized_url).lower(), [])
        expected.append((f"N{index:03d}", normalized_url, tuple(sorted(raw_indexes))))
    return expected


def promotion_gate_summary_text(matrix: dict[str, Any], preview: dict[str, Any]) -> str:
    summary = matrix["summary"]
    lines = [
        "# Candidate Corpus Integration Gate Summary",
        "",
        f"- Unique targets evaluated: {summary['unique_targets']}",
        f"- Integrated targets: {summary['integrated_targets']}",
        f"- Unintegrated targets: {summary['unintegrated_targets']}",
        f"- Integration classifications: {summary['classification_counts']}",
        f"- Trust-cleared installable targets: {summary['trust_cleared_installable_targets']}",
        f"- Integrated quarantine references: {summary['integrated_quarantine_targets']}",
        f"- Active install blocks: {summary['active_install_blocks']}",
        f"- Ready for repo promotion: {summary['ready_for_repo_promotion']}",
        f"- Ready for live install: {summary['ready_for_live_install']}",
        f"- Live install commands emitted: {preview['command_count']}",
        "",
        (
            "Every normalized source has a durable terminal integration identity; integration classification is "
            "independent from trust-cleared installability."
        ),
        "Quarantine references remain non-installable with active hard blocks.",
    ]
    return "\n".join(lines) + "\n"


def write_summary(matrix: dict[str, Any], preview: dict[str, Any]) -> None:
    (MANIFEST_DIR / SUMMARY_FILE).write_text(promotion_gate_summary_text(matrix, preview), encoding="utf-8")


def build_payloads() -> dict[str, Any]:
    context = build_context()
    raw_packets = build_raw_packets(context)
    unique_packets = build_unique_packets(context, raw_packets)
    matrix = build_gate_matrix(unique_packets)
    preview = build_install_preview(unique_packets)
    return {
        "raw": {
            "version": 1,
            "generated_at": now(),
            "packet_count": len(raw_packets),
            "required_packet_fields": context["schema"]["required_packet_fields"],
            "packets": raw_packets,
        },
        "unique": {
            "version": 1,
            "generated_at": now(),
            "packet_count": len(unique_packets),
            "packets": unique_packets,
        },
        "matrix": matrix,
        "preview": preview,
    }


def write_outputs() -> dict[str, Any]:
    payloads = build_payloads()
    write_json(RAW_PACKET_FILE, payloads["raw"])
    write_json(UNIQUE_PACKET_FILE, payloads["unique"])
    write_json(GATE_MATRIX_FILE, payloads["matrix"])
    write_json(INSTALL_PREVIEW_FILE, payloads["preview"])
    write_summary(payloads["matrix"], payloads["preview"])
    return payloads


def validate_outputs() -> dict[str, Any]:
    raw = load_json(RAW_PACKET_FILE)
    unique = load_json(UNIQUE_PACKET_FILE)
    matrix = load_json(GATE_MATRIX_FILE)
    preview = load_json(INSTALL_PREVIEW_FILE)
    schema = load_json("research-packet-schema.json")
    normalized = load_json("normalized-urls.json")
    integration_targets = load_json(INTEGRATION_TARGET_FILE)

    errors: list[str] = []
    errors.extend(integration_target_errors(integration_targets, normalized))
    required = set(schema.get("required_packet_fields", [])) if isinstance(schema, dict) else set()
    raw_packet_rows = raw.get("packets", []) if isinstance(raw, dict) else []
    unique_packet_rows = unique.get("packets", []) if isinstance(unique, dict) else []
    matrix_item_rows = matrix.get("items", []) if isinstance(matrix, dict) else []
    raw_packets = _packet_rows(raw)
    unique_packets = _packet_rows(unique)
    if isinstance(matrix_item_rows, list):
        matrix_items = [item for item in matrix_item_rows if isinstance(item, dict)]
    else:
        matrix_items = []
    preview_payload = preview if isinstance(preview, dict) else {}
    normalized_targets = normalized.get("unique_targets", []) if isinstance(normalized, dict) else []
    if not isinstance(normalized_targets, list):
        normalized_targets = []
    target_items = integration_targets.get("items", []) if isinstance(integration_targets, dict) else []
    if not isinstance(target_items, list):
        target_items = []
    targets_by_url = by_normalized([item for item in target_items if isinstance(item, dict)])
    if not isinstance(raw, dict):
        errors.append("raw packets payload is not an object")
    if not isinstance(unique, dict):
        errors.append("unique packets payload is not an object")
    if not isinstance(matrix, dict):
        errors.append("gate matrix payload is not an object")
    if not isinstance(preview, dict):
        errors.append("live install preview payload is not an object")
    if not isinstance(raw_packet_rows, list) or len(raw_packets) != len(raw_packet_rows):
        errors.append("raw packets payload contains non-object rows")
    if not isinstance(unique_packet_rows, list) or len(unique_packets) != len(unique_packet_rows):
        errors.append("unique packets payload contains non-object rows")
    if not isinstance(matrix_item_rows, list) or len(matrix_items) != len(matrix_item_rows):
        errors.append("gate matrix contains non-object rows")
    if len(raw_packets) != EXPECTED_RAW_COUNT:
        errors.append(f"raw packet count {len(raw_packets)} != {EXPECTED_RAW_COUNT}")
    if len(unique_packets) != EXPECTED_UNIQUE_COUNT:
        errors.append(f"unique packet count {len(unique_packets)} != {EXPECTED_UNIQUE_COUNT}")
    if [packet.get("raw_index") for packet in raw_packets] != list(range(1, EXPECTED_RAW_COUNT + 1)):
        errors.append("raw packet indexes are not contiguous 1..293")
    missing_fields = [
        packet.get("raw_index", f"position-{index}")
        for index, packet in enumerate(raw_packets, 1)
        if not required.issubset(packet)
    ]
    if missing_fields:
        errors.append(f"raw packets missing required fields: {missing_fields[:10]}")
    raw_unique_urls = {packet.get("normalized_url") for packet in raw_packets if packet.get("normalized_url")}
    if raw_unique_urls != set(normalized_targets):
        errors.append("raw packets do not cover every normalized target")
    unique_urls = {packet.get("normalized_url") for packet in unique_packets if packet.get("normalized_url")}
    if unique_urls != set(normalized_targets):
        errors.append("unique packets do not cover every normalized target")
    if any(packet.get("live_install_eligible") for packet in raw_packets + unique_packets):
        errors.append("a packet is unexpectedly live-install eligible")
    if any(packet.get("install_command") for packet in raw_packets + unique_packets):
        errors.append("a packet unexpectedly emitted an install command")
    target_fields = (
        "integration_classification",
        "integration_surface",
        "trust_cleared_installable",
        "hard_blocked",
        "catalog_rows",
    )
    for packet in raw_packets + unique_packets:
        target = targets_by_url.get(str(packet.get("normalized_url") or "").lower())
        if target is None:
            errors.append(f"packet has no integration target: {packet.get('normalized_url')}")
            continue
        for field in target_fields:
            if packet.get(field) != target.get(field):
                errors.append(f"packet {packet.get('packet_id')} {field} drifted from integration target")
        if packet.get("integrated") is not integration_target_is_accounted(target):
            errors.append(f"packet {packet.get('packet_id')} integrated state drifted from integration target")
    preview_commands = preview_payload.get("commands", [])
    if not isinstance(preview_commands, list):
        preview_commands = []
    if preview_payload.get("command_count") != 0 or preview_commands != []:
        errors.append("live install preview emitted commands from terminal rows")

    summary = matrix.get("summary", {}) if isinstance(matrix, dict) else {}
    if not isinstance(summary, dict):
        summary = {}
    if _safe_count(summary.get("integrated_targets")) != EXPECTED_UNIQUE_COUNT:
        errors.append("gate matrix does not report all 289 targets integrated")
    if _safe_count(summary.get("unintegrated_targets")) != 0:
        errors.append("gate matrix reports unintegrated targets")
    if summary.get("classification_counts") != EXPECTED_CLASSIFICATION_COUNTS:
        errors.append("gate matrix integration classification counts drifted")
    if _safe_count(summary.get("integrated_quarantine_targets")) != 4:
        errors.append("gate matrix quarantine integration count drifted")
    if _safe_count(summary.get("active_install_blocks")) != 4:
        errors.append("gate matrix active install block count drifted")
    if len(matrix_items) != EXPECTED_UNIQUE_COUNT:
        errors.append(f"gate matrix item count {len(matrix_items)} != {EXPECTED_UNIQUE_COUNT}")

    unique_keys = [promotion_target_key(packet) for packet in unique_packets]
    matrix_keys = [promotion_target_key(item) for item in matrix_items]
    if len(set(matrix_keys)) != len(matrix_keys):
        errors.append("gate matrix contains duplicate target rows")
    if unique_keys != expected_unique_packet_keys(raw_packets, normalized_targets):
        errors.append("unique packet target rows do not match normalized target order")
    if matrix_keys != unique_keys:
        errors.append("gate matrix target rows do not match unique packet order")

    unique_by_key = {promotion_target_key(packet): packet for packet in unique_packets}
    expected_status_keys = set(TERMINAL_ROUTE_CHECKS) | {"live install"}
    for item in matrix_items:
        key = promotion_target_key(item)
        packet = unique_by_key.get(key)
        if packet is None:
            continue
        for field in (
            "integration_classification",
            "integration_surface",
            "trust_cleared_installable",
            "hard_blocked",
            "integrated",
            "existing_integration_status",
            "auth_required",
        ):
            if item.get(field) != packet.get(field):
                errors.append(f"gate matrix row {item.get('packet_id')} {field} drifted from unique packet")
        expected_statuses = gate_statuses(packet)
        if item.get("gate_statuses") != expected_statuses:
            errors.append(f"gate matrix row {item.get('packet_id')} gate statuses drifted")
        if set((item.get("gate_statuses") or {}).keys()) != expected_status_keys:
            errors.append(f"gate matrix row {item.get('packet_id')} has invalid gate status keys")
        expected_final = promotion_final_status(item)
        if item.get("final_status") != expected_final:
            errors.append(f"gate matrix row {item.get('packet_id')} final status drifted")
        if item.get("install_command"):
            errors.append(f"gate matrix row {item.get('packet_id')} unexpectedly emitted an install command")

    expected_summary = expected_matrix_summary(matrix_items)
    if summary != expected_summary:
        errors.append("gate matrix summary does not match matrix rows")
    if not isinstance(matrix, dict) or matrix.get("terminal_route_checks") != TERMINAL_ROUTE_CHECKS:
        errors.append("gate matrix terminal route checks drifted")
    if not isinstance(matrix, dict) or matrix.get("gate_status_counts") != expected_gate_status_counts(matrix_items):
        errors.append("gate matrix gate status counts do not match rows")

    if preview_payload.get("command_count") != len(preview_commands):
        errors.append("live install preview command count does not match commands")
    expected_installable, expected_non_installable, expected_quarantine = expected_preview_partitions(unique_packets)
    installable_targets = preview_payload.get("trust_cleared_installable_targets", [])
    non_installable_targets = preview_payload.get("non_installable_integrated_targets", [])
    quarantine_targets = preview_payload.get("integrated_quarantine_targets", [])
    if not isinstance(installable_targets, list):
        installable_targets = []
    if not isinstance(non_installable_targets, list):
        non_installable_targets = []
    if not isinstance(quarantine_targets, list):
        quarantine_targets = []
    if preview_payload.get("integrated_target_count") != EXPECTED_UNIQUE_COUNT:
        errors.append("live install preview integrated target count drifted")
    if preview_payload.get("unintegrated_target_count") != 0:
        errors.append("live install preview reports unintegrated targets")
    if preview_payload.get("classification_counts") != EXPECTED_CLASSIFICATION_COUNTS:
        errors.append("live install preview classification counts drifted")
    if preview_payload.get("trust_cleared_installable_target_count") != len(installable_targets):
        errors.append("live install preview installable target count does not match rows")
    if preview_payload.get("non_installable_integrated_target_count") != len(non_installable_targets):
        errors.append("live install preview non-installable target count does not match rows")
    if preview_payload.get("integrated_quarantine_target_count") != len(quarantine_targets):
        errors.append("live install preview quarantine target count does not match rows")
    if preview_payload.get("active_install_blocks") != len(quarantine_targets):
        errors.append("live install preview active install block count does not match quarantine rows")
    if installable_targets != expected_installable:
        errors.append("live install preview installable targets do not match unique packets")
    if non_installable_targets != expected_non_installable:
        errors.append("live install preview non-installable targets do not match unique packets")
    if quarantine_targets != expected_quarantine:
        errors.append("live install preview quarantine targets do not match unique packets")

    try:
        summary_text = (MANIFEST_DIR / SUMMARY_FILE).read_text(encoding="utf-8")
    except OSError:
        summary_text = None
    try:
        expected_summary_text = promotion_gate_summary_text(matrix, preview_payload)
    except (KeyError, TypeError):
        expected_summary_text = None
    if summary_text != expected_summary_text:
        errors.append("promotion gate summary markdown is stale")

    return {
        "raw": len(raw_packets),
        "unique": len(unique_packets),
        "matrix_items": len(matrix_items),
        "command_count": preview_payload.get("command_count"),
        "ok": not errors,
        "errors": errors,
    }


def _load_promotions() -> list[dict[str, Any]]:
    payload = load_optional_json("promotion-overrides.json", {"overrides": []})
    overrides = payload.get("overrides", []) if isinstance(payload, dict) else []
    return [override for override in overrides if isinstance(override, dict)]


def validate_final_state() -> dict[str, Any]:
    normalized = load_json("normalized-urls.json")
    integration_targets = load_json(INTEGRATION_TARGET_FILE)
    all_records = load_json("all-records.json")
    summary = load_json("catalog-authoring-summary.json")
    progress = load_json("full-integration-progress.json")
    deep_audit = load_json(DEEP_AUDIT_FILE)
    raw_packets = load_json(RAW_PACKET_FILE)
    unique_packets = load_json(UNIQUE_PACKET_FILE)
    final_report = (MANIFEST_DIR / "final-review-report.md").read_text(encoding="utf-8")
    overrides = _load_promotions()
    harness_assurance = load_json(HARNESS_ASSURANCE_FILE)
    non_skill_assurance = load_json(NON_SKILL_ASSURANCE_FILE)

    records = all_records.get("records", []) if isinstance(all_records, dict) else []
    deep_items = deep_audit.get("items", []) if isinstance(deep_audit, dict) else []
    raw_packet_rows = raw_packets.get("packets", []) if isinstance(raw_packets, dict) else []
    unique_packet_rows = unique_packets.get("packets", []) if isinstance(unique_packets, dict) else []
    errors: list[str] = []
    errors.extend(integration_target_errors(integration_targets, normalized))
    target_items = integration_targets.get("items", []) if isinstance(integration_targets, dict) else []
    if not isinstance(target_items, list):
        target_items = []
    targets_by_url = by_normalized([item for item in target_items if isinstance(item, dict)])

    if normalized.get("raw_count") != EXPECTED_RAW_COUNT:
        errors.append("normalized raw_count drifted")
    if normalized.get("unique_count") != EXPECTED_UNIQUE_COUNT:
        errors.append("normalized unique_count drifted")
    if len(records) != EXPECTED_RAW_COUNT:
        errors.append("all-records does not cover every raw candidate")
    if len(raw_packet_rows) != EXPECTED_RAW_COUNT:
        errors.append("raw research packets do not cover every raw candidate")
    if len(unique_packet_rows) != EXPECTED_UNIQUE_COUNT:
        errors.append("unique research packets do not cover every normalized target")
    if list(AUTHORING_DIR.glob("candidate-corpus-*.mdx")):
        errors.append("candidate-corpus authoring rows remain after integration")
    if deep_audit.get("candidate_code_executed") is not False:
        errors.append("deep source audit must not execute candidate code")
    if deep_audit.get("unique_target_count") != EXPECTED_UNIQUE_COUNT:
        errors.append("deep source audit does not cover every normalized target")
    if len(deep_items) != EXPECTED_UNIQUE_COUNT:
        errors.append("deep source audit item count drifted")
    status_counts = deep_audit.get("status_counts", {})
    audited_count = _safe_count(status_counts.get("audited"))
    terminal_blocker_count = _safe_count(status_counts.get("terminal-blocker"))
    if audited_count + terminal_blocker_count != EXPECTED_UNIQUE_COUNT:
        errors.append("deep source audit status counts do not cover every normalized target")
    deep_by_url = {
        str(item.get("normalized_url") or "").lower(): item
        for item in deep_items
        if isinstance(item, dict) and item.get("normalized_url")
    }
    for record in records:
        if not isinstance(record, dict):
            continue
        deep_item = deep_by_url.get(str(record.get("normalized_url") or "").lower(), {})
        auth_review = deep_item.get("auth_review", {}) if isinstance(deep_item, dict) else {}
        if isinstance(auth_review, dict) and deep_item.get("audit_complete"):
            if record.get("auth_required") is not bool(auth_review.get("auth_required")):
                errors.append(f"record {record.get('raw_index')} auth drifted from deep source audit")
            expected_env = {
                str(value)
                for value in auth_review.get("env_vars_or_credentials", [])
                if str(value).strip() and str(value) != "PLACEHOLDER_ONLY_REVIEW_REQUIRED"
            }
            actual_env = set(record.get("env_vars_or_credentials", []))
            if not expected_env.issubset(actual_env):
                errors.append(f"record {record.get('raw_index')} auth variables drifted from deep source audit")
            if not auth_review.get("auth_required") and actual_env:
                errors.append(f"record {record.get('raw_index')} has auth variables without a deep auth boundary")
        if not record.get("files_added") or not record.get("files_modified"):
            errors.append(f"record {record.get('raw_index')} lacks final integration file evidence")
    nvidia_records = [
        record
        for record in records
        if isinstance(record, dict) and record.get("raw_url") == "https://github.com/NVIDIA/skills-"
    ]
    if len(nvidia_records) != 1:
        errors.append("malformed NVIDIA/skills- raw entry is not preserved exactly once")
    elif nvidia_records[0].get("normalized_url") != "https://github.com/NVIDIA/skills":
        errors.append("malformed NVIDIA/skills- raw entry is not resolved to canonical NVIDIA/skills")
    nvidia_audited = [
        item
        for item in deep_items
        if isinstance(item, dict)
        and item.get("normalized_url") == "https://github.com/NVIDIA/skills"
        and item.get("status") == "audited"
    ]
    if len(nvidia_audited) != 1:
        errors.append("canonical NVIDIA/skills target is not recorded as one audited target")

    live_stats = live_install_evidence_stats(overrides)
    live_installed = live_stats["live_install_rows"]
    installed_path_refs = live_stats["installed_path_refs"]
    verified_skill_md = live_stats["verified_skill_md_count"]
    missing_skill_md = live_stats["missing_installed_skill_md"]
    if len(overrides) != summary.get("install_commands_published"):
        errors.append("promotion override count does not match install command count")
    if live_installed != summary.get("live_installs_recorded"):
        errors.append("live install override count does not match summary")
    if live_installed != progress.get("live_install", {}).get("installed_skill_rows"):
        errors.append("live install count does not match progress")
    if progress.get("live_install", {}).get("installed_path_refs") != installed_path_refs:
        errors.append("installed path reference count does not match progress")
    if progress.get("live_install", {}).get("verified_skill_md_count") != verified_skill_md:
        errors.append("verified SKILL.md count does not match progress")
    if progress.get("live_install", {}).get("missing_skill_md_count") != len(missing_skill_md):
        errors.append("missing SKILL.md count does not match progress")
    if missing_skill_md:
        errors.append("recorded live install evidence has missing SKILL.md paths: " + ", ".join(missing_skill_md[:5]))
    if any(override.get("source_list_evidence") != "source-list-found" for override in overrides):
        errors.append("a promoted override lacks source-list-found evidence")
    if any(str(override.get("license") or "").upper() in {"", "NOASSERTION", "UNKNOWN"} for override in overrides):
        errors.append("a promoted override lacks license evidence")
    if any(str(override.get("intake_decision") or "").startswith("hard_blocked_") for override in overrides):
        errors.append("a terminal hard-block override was promoted")
    for override in overrides:
        normalized_url = str(override.get("normalized_url") or "")
        target = targets_by_url.get(normalized_url.lower())
        if target is None:
            errors.append(f"promoted override has no integration target: {normalized_url}")
            continue
        if target.get("hard_blocked") is True:
            errors.append(f"hard-blocked integration target was promoted: {normalized_url}")
        if target.get("integration_classification") != "installable-existing":
            errors.append(f"current promoted override is not classified installable-existing: {normalized_url}")
        target_row_names = {
            str(row.get("name") or "") for row in target.get("catalog_rows", []) if isinstance(row, dict)
        }
        if str(override.get("skill_name") or "") not in target_row_names:
            errors.append(f"promoted override row is absent from integration target: {normalized_url}")
    assurance_totals = harness_assurance.get("totals", {}) if isinstance(harness_assurance, dict) else {}
    harness_agents = harness_assurance.get("agents", [])
    observed_harnesses = (
        {str(agent.get("agent") or "") for agent in harness_agents if isinstance(agent, dict)}
        if isinstance(harness_agents, list)
        else set()
    )
    if (
        harness_assurance.get("complete") is not True
        or harness_assurance.get("target_harness_count") != len(SUPPORTED_AGENT_IDS)
        or observed_harnesses != set(SUPPORTED_AGENT_IDS)
    ):
        errors.append("post-install harness assurance is incomplete")
    if any(_safe_count(assurance_totals.get(field)) for field in ("missing", "pin_blocked", "commands")):
        errors.append("post-install harness assurance has remaining install work")
    fingerprint_paths = (
        ("catalog_index_sha256", ROOT / "docs/public/generated-registries/skills-catalog-index.json"),
        ("promotion_overrides_sha256", MANIFEST_DIR / "promotion-overrides.json"),
    )
    for field, path in fingerprint_paths:
        if not path.is_file() or harness_assurance.get(field) != hashlib.sha256(path.read_bytes()).hexdigest():
            errors.append(f"post-install harness assurance {field} is stale")
    non_skill_items = non_skill_assurance.get("items", []) if isinstance(non_skill_assurance, dict) else []
    if non_skill_assurance.get("complete") is not True or non_skill_assurance.get("unique_target_count") != 289:
        errors.append("non-skill install assurance is incomplete")
    if not isinstance(non_skill_items, list) or len(non_skill_items) != EXPECTED_UNIQUE_COUNT:
        errors.append("non-skill install assurance does not cover 289 targets")
        non_skill_items = []
    non_skill_urls = {
        str(item.get("normalized_url") or "").lower()
        for item in non_skill_items
        if isinstance(item, dict) and item.get("normalized_url")
    }
    if non_skill_urls != set(targets_by_url):
        errors.append("non-skill install assurance target coverage drifted")
    if non_skill_assurance.get("failed_artifacts"):
        errors.append("non-skill install assurance contains failed runtime artifacts")
    non_skill_source_paths = {
        "integration_decisions": MANIFEST_DIR / "integration-decisions.json",
        "mcp_registry": ROOT / "config/mcp-registry.json",
        "plugin_registry": ROOT / "config/plugin-extension-registry.json",
        "tooling_policy": ROOT / "config/tooling-policy.json",
    }
    expected_non_skill_fingerprints = {
        name: semantic_json_sha256(path) for name, path in non_skill_source_paths.items()
    }
    if non_skill_assurance.get("source_fingerprints") != expected_non_skill_fingerprints:
        errors.append("non-skill install assurance source fingerprints are stale")
    if progress.get("complete") is not True:
        errors.append("full integration progress does not mark completion")
    if progress.get("phase") != "corpus-integration-complete":
        errors.append("full integration progress phase is not corpus-integration-complete")
    if progress.get("non_skill_install", {}).get("complete") is not True:
        errors.append("full integration progress does not bind complete non-skill assurance")
    progress_readiness = progress.get("promotion_readiness", {})
    if not isinstance(progress_readiness, dict):
        progress_readiness = {}
    if progress_readiness.get("integrated_targets") != EXPECTED_UNIQUE_COUNT:
        errors.append("progress does not report all 289 targets integrated")
    if progress_readiness.get("unintegrated_targets") != 0:
        errors.append("progress reports unintegrated targets")
    if progress_readiness.get("integration_classification_counts") != EXPECTED_CLASSIFICATION_COUNTS:
        errors.append("progress integration classifications drifted")
    if progress_readiness.get("integrated_quarantine_targets") != 4:
        errors.append("progress quarantine integration count drifted")
    if progress_readiness.get("active_install_blocks") != 4:
        errors.append("progress active install block count drifted")
    if progress.get("unique_terminal_decisions") != EXPECTED_UNIQUE_COUNT:
        errors.append("progress unique terminal decisions drifted")
    terminal_decisions = progress.get("terminal_decisions", {})
    if terminal_decisions.get("raw_candidates_processed") != EXPECTED_RAW_COUNT:
        errors.append("terminal decision raw count drifted")
    if terminal_decisions.get("unique_normalized_targets") != EXPECTED_UNIQUE_COUNT:
        errors.append("terminal decision unique target count drifted")
    if terminal_decisions.get("live_installs_recorded") != live_installed:
        errors.append("terminal decision live install count drifted")
    if "Final commit hash: recorded by the runner" in final_report:
        errors.append("final review report still contains placeholder commit hash text")

    return {
        "raw": normalized.get("raw_count"),
        "unique": normalized.get("unique_count"),
        "deep_audited": audited_count,
        "deep_terminal_blockers": terminal_blocker_count,
        "integrated_targets": integration_targets.get("integrated_targets"),
        "unintegrated_targets": integration_targets.get("unintegrated_targets"),
        "integration_classification_counts": integration_targets.get("classification_counts"),
        "integrated_quarantine_targets": EXPECTED_CLASSIFICATION_COUNTS["integrated-quarantine-reference"],
        "active_install_blocks": sum(item.get("hard_blocked") is True for item in target_items),
        "promoted_overrides": len(overrides),
        "live_installed": live_installed,
        "installed_path_refs": installed_path_refs,
        "verified_skill_md": verified_skill_md,
        "missing_skill_md": len(missing_skill_md),
        "ok": not errors,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write promotion packet outputs")
    parser.add_argument("--check-coverage", action="store_true", help="validate generated packet coverage")
    parser.add_argument("--final-check", action="store_true", help="validate completed promotion overlay evidence")
    args = parser.parse_args()

    ran_action = False
    exit_code = 0
    if args.write:
        write_outputs()
        ran_action = True
    if args.check_coverage:
        result = validate_outputs()
        print(json.dumps(result, indent=2))
        ran_action = True
        if not result["ok"]:
            exit_code = 1
    if args.final_check:
        result = validate_final_state()
        print(json.dumps(result, indent=2))
        ran_action = True
        if not result["ok"]:
            exit_code = 1
    if not ran_action:
        parser.print_help()
        return 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
