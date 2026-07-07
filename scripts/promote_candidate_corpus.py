#!/usr/bin/env python3
"""Build trust-gated promotion packets for the July 2026 corpus.

The generator consumes repo-local intake manifests only. It does not clone,
install, import, execute, or enable candidate code.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
EXPECTED_RAW_COUNT = 293
EXPECTED_UNIQUE_COUNT = 289

RAW_PACKET_FILE = "raw-research-packets.json"
UNIQUE_PACKET_FILE = "unique-target-research-packets.json"
GATE_MATRIX_FILE = "promotion-gate-matrix.json"
INSTALL_PREVIEW_FILE = "live-install-command-preview.json"
SUMMARY_FILE = "promotion-gate-summary.md"

TERMINAL_DECISION_MAP = {
    "merge_into_existing": "merged",
    "quarantine": "blocked",
    "reference_only": "docs-reference",
    "skip_duplicate": "merged",
    "skip_inaccessible": "blocked",
}

TRUST_GATES = [
    "source-list evidence",
    "license review",
    "security review",
    "attribution review",
    "auth review",
    "docs-steward promotion",
    "target-specific validation",
]


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


def dedupe(values: list[Any]) -> list[Any]:
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


def readiness_by_url(readiness: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    for bucket in ("ready_for_repo_promotion", "ready_for_live_install", "blocked_until_trust_gates"):
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
    return TERMINAL_DECISION_MAP.get(decision, "blocked")


def record_blockers(record: dict[str, Any], readiness_item: dict[str, Any] | None) -> list[str]:
    blockers = list(readiness_item.get("blocking_gates", TRUST_GATES) if readiness_item else TRUST_GATES)
    if record.get("skipped_reason"):
        blockers.append(record["skipped_reason"])
    if record.get("install_or_integration_decision") == "skip_duplicate":
        blockers.append("duplicate raw entry covered by canonical normalized target")
    if source_status(record) == "unavailable":
        blockers.append("upstream unavailable or malformed")
    return dedupe(blockers)


def build_context() -> dict[str, Any]:
    normalized = load_json("normalized-urls.json")
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

    return {
        "normalized": normalized,
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
            "blockers": record_blockers(record, readiness_item),
            "reviewer_notes": record["reviewer_notes"],
            "current_intake_decision": record["install_or_integration_decision"],
            "risk_tier": record["risk_tier"],
            "risk_keywords": record["risk_keywords"],
            "canonical_source": record["canonical_source"],
            "existing_integration_status": coverage_item.get("coverage_status", "unknown"),
            "existing_rows": coverage_item.get("existing_rows", []),
            "source_list_evidence": source_list_item or {},
            "leaf_checks": raw_lane["leaf_checks"],
            "source_support_matrix": record["source_support_matrix"],
            "github_metadata_packet": record["github_metadata_packet"],
            "license_packet": record["license_packet"],
            "security_packet": record["security_packet"],
            "compliance_packet": record["compliance_packet"],
            "execution_policy": "candidate code was not executed; live install is blocked until all trust gates pass",
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
        decision_item = context["decisions_by_url"].get(key, {})
        readiness_item = context["readiness_by_url"].get(key, {})
        unique_lane = context["unique_lanes_by_url"][key]
        wave = context["wave_by_url"].get(key, {})
        source_list_item = context["source_list_by_url"].get(key)
        blockers = dedupe([blocker for packet in raw_group for blocker in packet["blockers"]])
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
            "existing_integration_status": coverage_item.get("coverage_status", "unknown"),
            "existing_rows": coverage_item.get("existing_rows", []),
            "source_list_evidence": source_list_item or {},
            "install_command": readiness_item.get("install_command", ""),
            "live_install_eligible": readiness_item.get("live_install_eligible", False),
            "repo_mutation_eligible": readiness_item.get("repo_mutation_eligible", False),
            "docs_steward_surfaces": docs_surfaces,
            "blockers": blockers,
            "leaf_checks": unique_lane["leaf_checks"],
            "promotion_wave": wave,
            "reviewer_notes": "Unique-target synthesis packet; final promotion requires all raw packet gates to pass.",
        }
        packets.append(packet)
    return packets


def gate_statuses(packet: dict[str, Any]) -> dict[str, str]:
    has_existing_installable = packet["existing_integration_status"] == "covered-by-existing-installable-catalog"
    source_list_evidence = packet.get("source_list_evidence") or {}
    source_list_evidence_status = source_list_evidence.get("evidence_status")
    has_source_list = bool(source_list_evidence)
    license_status = "metadata-present-needs-file-review" if packet["licenses"] else "missing-license-review"
    if any(str(license_value).lower().startswith("not-fetched") for license_value in packet["licenses"]):
        license_status = "license-unavailable-needs-review"
    if source_list_evidence_status == "source-list-found" and has_existing_installable:
        source_list_status = "source-list-found-existing-installable-catalog"
    elif source_list_evidence_status == "source-list-found":
        source_list_status = "source-list-found-pending-promotion-review"
    elif source_list_evidence_status == "source-list-no-skills-listed":
        source_list_status = "source-list-reviewed-no-installable-skills"
    elif source_list_evidence_status == "source-list-timeout":
        source_list_status = "source-list-timeout-needs-retry"
    elif source_list_evidence_status == "source-list-unavailable":
        source_list_status = "source-list-unavailable-needs-manual-review"
    elif source_list_evidence_status == "source-list-empty-or-unparsed":
        source_list_status = "source-list-empty-or-unparsed-needs-parser-review"
    elif source_list_evidence_status == "source-list-error":
        source_list_status = "source-list-error-needs-manual-review"
    elif source_list_evidence_status == "source-list-unavailable":
        source_list_status = "source-list-unavailable-needs-manual-review"
    elif source_list_evidence_status == "source-list-empty-or-unparsed":
        source_list_status = "source-list-empty-or-unparsed-needs-manual-review"
    elif has_existing_installable:
        source_list_status = "existing-installable-catalog-row-present"
    elif has_source_list and source_list_evidence_status:
        source_list_status = f"{source_list_evidence_status}-needs-review"
    elif has_source_list:
        source_list_status = "source-list-evidence-unclassified"
    else:
        source_list_status = "pending-source-list-output"
    return {
        "source-list evidence": source_list_status,
        "license review": license_status,
        "security review": "pending-executable-surface-review",
        "attribution review": "pending-source-specific-attribution-note",
        "auth review": "auth-required-review" if packet["auth_required"] else "metadata-only-no-auth-detected",
        "docs-steward promotion": "catalog-intake-present-final-docs-pending",
        "target-specific validation": "pending-target-validation",
        "live install": "blocked",
    }


def build_gate_matrix(unique_packets: list[dict[str, Any]]) -> dict[str, Any]:
    items = []
    gate_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for packet in unique_packets:
        statuses = gate_statuses(packet)
        for gate, status in statuses.items():
            gate_counts[gate][status] += 1
        items.append(
            {
                "packet_id": packet["packet_id"],
                "normalized_url": packet["normalized_url"],
                "raw_indexes": packet["raw_indexes"],
                "existing_integration_status": packet["existing_integration_status"],
                "auth_required": packet["auth_required"],
                "gate_statuses": statuses,
                "final_status": "blocked-until-trust-gates",
                "install_command": "",
            }
        )
    return {
        "version": 1,
        "generated_at": now(),
        "summary": {
            "unique_targets": len(unique_packets),
            "ready_for_repo_promotion": 0,
            "ready_for_live_install": 0,
            "blocked_until_trust_gates": len(unique_packets),
        },
        "trust_gates": TRUST_GATES,
        "gate_status_counts": {gate: dict(counts) for gate, counts in sorted(gate_counts.items())},
        "items": items,
    }


def build_install_preview(unique_packets: list[dict[str, Any]]) -> dict[str, Any]:
    blocked = [
        {
            "packet_id": packet["packet_id"],
            "normalized_url": packet["normalized_url"],
            "raw_indexes": packet["raw_indexes"],
            "blocking_gates": packet["blockers"],
        }
        for packet in unique_packets
    ]
    return {
        "version": 1,
        "generated_at": now(),
        "status": "no-live-install-commands-emitted",
        "command_count": 0,
        "commands": [],
        "blocked_target_count": len(blocked),
        "blocked_targets": blocked,
        "rule": (
            "Do not run npx skills add, wagents skills sync --apply, MCP installs, or plugin installs until "
            "target packets pass source, license, security, attribution, auth, docs, and validation gates."
        ),
    }


def write_summary(matrix: dict[str, Any], preview: dict[str, Any]) -> None:
    lines = [
        "# Candidate Corpus Promotion Gate Summary",
        "",
        f"- Unique targets evaluated: {matrix['summary']['unique_targets']}",
        f"- Ready for repo promotion: {matrix['summary']['ready_for_repo_promotion']}",
        f"- Ready for live install: {matrix['summary']['ready_for_live_install']}",
        f"- Blocked until trust gates: {matrix['summary']['blocked_until_trust_gates']}",
        f"- Live install commands emitted: {preview['command_count']}",
        "",
        "All candidate sources remain blocked from live installation until the per-target trust gates pass.",
        "The packet files are promotion work queues, not proof of completed adaptation or installation.",
    ]
    (MANIFEST_DIR / SUMMARY_FILE).write_text("\n".join(lines) + "\n", encoding="utf-8")


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

    errors: list[str] = []
    required = set(schema["required_packet_fields"])
    raw_packets = raw.get("packets", [])
    unique_packets = unique.get("packets", [])
    if len(raw_packets) != EXPECTED_RAW_COUNT:
        errors.append(f"raw packet count {len(raw_packets)} != {EXPECTED_RAW_COUNT}")
    if len(unique_packets) != EXPECTED_UNIQUE_COUNT:
        errors.append(f"unique packet count {len(unique_packets)} != {EXPECTED_UNIQUE_COUNT}")
    if [packet.get("raw_index") for packet in raw_packets] != list(range(1, EXPECTED_RAW_COUNT + 1)):
        errors.append("raw packet indexes are not contiguous 1..293")
    missing_fields = [
        packet["raw_index"]
        for packet in raw_packets
        if not required.issubset(packet)
    ]
    if missing_fields:
        errors.append(f"raw packets missing required fields: {missing_fields[:10]}")
    raw_unique_urls = {packet["normalized_url"] for packet in raw_packets}
    if raw_unique_urls != set(normalized["unique_targets"]):
        errors.append("raw packets do not cover every normalized target")
    if {packet["normalized_url"] for packet in unique_packets} != set(normalized["unique_targets"]):
        errors.append("unique packets do not cover every normalized target")
    if any(packet["live_install_eligible"] for packet in raw_packets + unique_packets):
        errors.append("a packet is unexpectedly live-install eligible")
    if any(packet.get("install_command") for packet in raw_packets + unique_packets):
        errors.append("a packet unexpectedly emitted an install command")
    if preview.get("command_count") != 0 or preview.get("commands") != []:
        errors.append("live install preview emitted commands before trust gates")
    if matrix.get("summary", {}).get("blocked_until_trust_gates") != EXPECTED_UNIQUE_COUNT:
        errors.append("gate matrix does not block every unique target")

    return {
        "raw": len(raw_packets),
        "unique": len(unique_packets),
        "matrix_items": len(matrix.get("items", [])),
        "command_count": preview.get("command_count"),
        "ok": not errors,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write promotion packet outputs")
    parser.add_argument("--check-coverage", action="store_true", help="validate generated packet coverage")
    args = parser.parse_args()

    if args.write:
        write_outputs()
    if args.check_coverage:
        result = validate_outputs()
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1
    if not args.write:
        parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
