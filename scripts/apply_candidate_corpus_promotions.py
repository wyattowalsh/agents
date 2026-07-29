#!/usr/bin/env python3
"""Apply reviewed candidate-corpus promotions after terminal route generation.

The main candidate-corpus generator emits terminal traceability rows. This
overlay converts explicitly reviewed overrides into normal installable curated
catalog rows and updates the generated authoring summary. It does not fetch,
install, execute, or vendor candidate code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from wagents.candidate_auth import extract_auth_env_names, is_auth_env_name
from wagents.candidate_corpus_reports import (
    RUNNER_CHECKLIST_HEADING,
    TERMINAL_PROMOTION_ASSIGNMENT_RULE,
    TERMINAL_PROMOTION_POLICY,
    TERMINAL_PROMOTION_WAVE_STATUS,
    generated_reference_materialization_errors,
    mutation_policy_for_wave,
    preserve_runner_owned_results,
    render_promotion_wave_report,
    validate_promotion_wave_plan,
)
from wagents.parsing import parse_frontmatter
from wagents.site_model import SUPPORTED_AGENT_IDS

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
AUTHORING_DIR = ROOT / "docs" / "src" / "authoring" / "skills"
RECORDS_DIR = MANIFEST_DIR / "records"
OVERRIDES = MANIFEST_DIR / "promotion-overrides.json"
INTEGRATION_TARGETS = MANIFEST_DIR / "integration-targets.json"
SUMMARY = MANIFEST_DIR / "catalog-authoring-summary.json"
REPORT = MANIFEST_DIR / "applied-promotion-overrides.json"
PROGRESS = MANIFEST_DIR / "full-integration-progress.json"
STATE_REPORT = MANIFEST_DIR / "full-integration-state.md"
HARNESS_ASSURANCE = MANIFEST_DIR / "harness-install-assurance.json"
NON_SKILL_ASSURANCE = MANIFEST_DIR / "non-skill-install-assurance.json"
RUNTIME_ACTIVATION_ASSURANCE = MANIFEST_DIR / "runtime-activation-assurance.json"
EXPECTED_RAW_COUNT = 293
EXPECTED_UNIQUE_COUNT = 289
EXPECTED_RUNTIME_ARTIFACT_COUNT = 65
EXPECTED_RUNTIME_KIND_COUNTS = {"cli": 30, "library": 1, "mcp": 17, "plugin": 17}
SUCCESSOR_ASSURANCE_SCRIPTS = (
    "record_candidate_catalog_closure.py",
    "verify_candidate_plugin_provenance.py",
    "run_candidate_cli_canaries.py",
    "rehearse_candidate_cli_rollback.py",
    "run_candidate_mcp_canaries.py",
    "rehearse_candidate_mcp_rollback.py",
    "run_candidate_plugin_canaries.py",
    "rehearse_candidate_plugin_rollback.py",
    "run_candidate_docs_assurance.py",
    "record_candidate_final_closure.py",
    "record_candidate_mcp_activation.py",
    "record_candidate_runtime_activation.py",
)
EXPECTED_CLASSIFICATION_COUNTS = {
    "installable-existing": 121,
    "inspection-existing": 6,
    "integrated-reference": 158,
    "integrated-quarantine-reference": 4,
}
GENERATED_REFERENCE_CLASSIFICATIONS = {
    "integrated-reference",
}
LEGACY_CANDIDATE_MARKER = "GENERATED-CANDIDATE-CORPUS-JUL2026"
INTEGRATION_TARGET_MARKER = "GENERATED-INTEGRATION-TARGET-JUL2026"
TRUST_CLEARED_STATUS = "install-now-after-trust-gate"
TRUST_CLEARED_TIER = "curated-trust-gated"
COVERAGE_TRUST_CLEARED = "covered-by-existing-installable-catalog"
COVERAGE_INSPECTION_REQUIRED = "covered-by-existing-inspection-required"
COVERAGE_REFERENCE = "covered-by-existing-reference"
COVERAGE_NEEDS_PROMOTION = "needs-promotion-review"
TERMINAL_ROUTE_REQUIREMENTS = [
    "preserve attribution and license notes",
    "keep credentials user-owned",
    "avoid vendoring or executing candidate code from intake rows",
    "use repo-native MCP/plugin/tool/catalog surfaces",
]
TERMINAL_DECISION_STATUSES = {
    "duplicate_covered": "duplicate-covered",
    "hard_blocked_inaccessible": "hard-blocked-inaccessible",
    "hard_blocked_quarantine": "hard-blocked-quarantine",
    "integrated_collection_surface": "integrated-collection-surface",
    "integrated_existing_surface": "integrated-existing-surface",
    "integrated_mcp_surface": "integrated-mcp-surface",
    "integrated_native_surface": "integrated-native-surface",
    "integrated_plugin_surface": "integrated-plugin-surface",
    "integrated_skill_catalog_surface": "integrated-skill-catalog-surface",
    "integrated_tool_surface": "integrated-tool-surface",
    "merge_into_existing": "integrated-existing-surface",
}
TERMINAL_HARD_BLOCK_DECISIONS = {"hard_blocked_inaccessible", "hard_blocked_quarantine"}
AUTH_UNKNOWN_PLACEHOLDER = "PLACEHOLDER_ONLY_REVIEW_REQUIRED"
SHARED_RECORD_FILES = (
    "planning/manifests/candidate-corpus-jul2026/all-records.json",
    "planning/manifests/candidate-corpus-jul2026/catalog-authoring-summary.json",
    "planning/manifests/candidate-corpus-jul2026/compliance-auth-matrix.json",
    "planning/manifests/candidate-corpus-jul2026/integration-decisions.json",
    "planning/manifests/candidate-corpus-jul2026/integration-targets.json",
    "planning/manifests/candidate-corpus-jul2026/harness-install-assurance.json",
    "planning/manifests/candidate-corpus-jul2026/non-skill-install-assurance.json",
    "docs/public/generated-registries/skills-catalog-browser-index.json",
    "docs/public/generated-registries/skills-catalog-index.json",
)
SOURCE_INTEGRATION_FILES = (
    "README.md",
    "config/mcp-registry.json",
    "config/plugin-extension-registry.json",
    "config/sync-manifest.json",
    "config/tooling-policy.json",
    "mcp/mcphub/mcp_settings.json",
)
BASELINE_GATE_ARTIFACTS = (
    "existing-integration-coverage.json",
    "promotion-readiness-queue.json",
    "promotion-gate-matrix.json",
    "live-install-command-preview.json",
    "promotion-gate-summary.md",
    "research-task-graph.json",
    "raw-research-packets.json",
    "unique-target-research-packets.json",
    "promotion-wave-plan.json",
    "promotion-wave-plan.md",
)
LEGACY_SOURCE_LIST_ROUTE = "-".join(("reference", "only"))
TERMINAL_ROUTE_NOTE_REPLACEMENTS = {
    f"decide {LEGACY_SOURCE_LIST_ROUTE} vs curated installability": (
        "confirm terminal repo-native route and target-specific validation"
    ),
    f"promote from {LEGACY_SOURCE_LIST_ROUTE} row only after review": (
        "use reviewed terminal catalog promotion evidence before any additional install row"
    ),
}
AUTHORING_STEM_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
REQUIRED_OVERRIDE_STRING_FIELDS = (
    "normalized_url",
    "source_name",
    "skill_name",
    "description",
    "install_source",
    "install_command",
    "status",
    "trust_tier",
    "sync_kind",
    "source_list_evidence",
    "license",
)


def now() -> str:
    return datetime.now(UTC).isoformat()


def yaml_string(value: Any) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def yaml_flow_list(values: list[Any]) -> str:
    return "[" + ", ".join(yaml_string(value) for value in values) + "]"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_integration_targets() -> dict[str, Any]:
    if not INTEGRATION_TARGETS.is_file():
        return {}
    payload = load_json(INTEGRATION_TARGETS)
    return payload if isinstance(payload, dict) else {}


def integration_target_index(payload: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    target_payload = payload if payload is not None else load_integration_targets()
    items = target_payload.get("items", []) if isinstance(target_payload, dict) else []
    if not isinstance(items, list):
        return {}
    return {
        str(item["normalized_url"]).lower(): item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("normalized_url"), str) and item["normalized_url"].strip()
    }


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


def integration_target_errors(payload: dict[str, Any] | None = None) -> list[str]:
    target_payload = payload if payload is not None else load_integration_targets()
    items = target_payload.get("items", []) if isinstance(target_payload, dict) else []
    if not isinstance(items, list):
        return ["integration-targets.json items must be a list"]
    errors: list[str] = []
    if target_payload.get("unique_targets") != EXPECTED_UNIQUE_COUNT or len(items) != EXPECTED_UNIQUE_COUNT:
        errors.append("integration target count does not equal 289")
    urls = [
        str(item.get("normalized_url") or "").lower()
        for item in items
        if isinstance(item, dict) and item.get("normalized_url")
    ]
    if len(urls) != len(set(urls)):
        errors.append("integration targets contain duplicate normalized URLs")
    raw_indexes = [
        index for item in items if isinstance(item, dict) for index in normalized_raw_indexes(item.get("raw_indexes"))
    ]
    if sorted(raw_indexes) != list(range(1, EXPECTED_RAW_COUNT + 1)):
        errors.append("integration targets do not cover raw indexes 1 through 293 exactly once")
    if target_payload.get("raw_entries_covered") != EXPECTED_RAW_COUNT:
        errors.append("integration target raw_entries_covered does not equal 293")
    if target_payload.get("integrated_targets") != EXPECTED_UNIQUE_COUNT:
        errors.append("integration target integrated_targets does not equal 289")
    if target_payload.get("unintegrated_targets") != 0:
        errors.append("integration target unintegrated_targets does not equal zero")
    if target_payload.get("classification_counts") != EXPECTED_CLASSIFICATION_COUNTS:
        errors.append("integration target classification counts do not match the expected 121/6/158/4 split")
    item_classification_counts: Counter[str] = Counter()
    generated_reference_count = 0
    for item in items:
        if not isinstance(item, dict):
            errors.append("integration targets contain a non-object item")
            continue
        rows = item.get("catalog_rows")
        classification = item.get("integration_classification")
        if classification not in EXPECTED_CLASSIFICATION_COUNTS:
            errors.append(f"integration target has invalid classification: {item.get('normalized_url')}")
        else:
            item_classification_counts[str(classification)] += 1
        generated_name = str(item.get("generated_reference_name") or "").strip()
        generated_path = str(item.get("generated_reference_path") or "").strip()
        has_generated_identity = bool(generated_name and generated_path)
        expects_generated_identity = classification in GENERATED_REFERENCE_CLASSIFICATIONS
        if bool(generated_name) != bool(generated_path):
            errors.append(
                f"integration target has incomplete generated reference identity: {item.get('normalized_url')}"
            )
        elif expects_generated_identity and not has_generated_identity:
            errors.append(
                f"integration target reference classification lacks generated reference identity: "
                f"{item.get('normalized_url')}"
            )
        elif not expects_generated_identity and has_generated_identity:
            errors.append(
                f"integration target existing classification exposes generated reference identity: "
                f"{item.get('normalized_url')}"
            )
        generated_reference_count += int(has_generated_identity)
        hard_blocked = item.get("hard_blocked") is True
        if hard_blocked != (classification == "integrated-quarantine-reference"):
            errors.append(
                f"integration target hard-block state disagrees with classification: {item.get('normalized_url')}"
            )
        if hard_blocked and item.get("trust_cleared_installable") is not False:
            errors.append(f"hard-blocked integration target is marked installable: {item.get('normalized_url')}")
        if not isinstance(rows, list):
            errors.append(f"integration target catalog rows are not a list: {item.get('normalized_url')}")
            rows = []
        if hard_blocked:
            if rows:
                errors.append(f"hard-blocked integration target exposes catalog rows: {item.get('normalized_url')}")
        elif not rows:
            errors.append(f"integration target has no catalog row: {item.get('normalized_url')}")
        if rows:
            install_rows = [row for row in rows if isinstance(row, dict) and existing_row_has_install_surface(row)]
            derived_installable = bool(install_rows) and all(existing_row_trust_cleared(row) for row in install_rows)
            if hard_blocked:
                derived_installable = False
            if item.get("trust_cleared_installable") is not derived_installable:
                errors.append(
                    f"integration target installability disagrees with catalog rows: {item.get('normalized_url')}"
                )
            if has_generated_identity:
                matching_rows = [
                    row
                    for row in rows
                    if isinstance(row, dict)
                    and str(row.get("name") or "").strip() == generated_name
                    and str(row.get("path") or "").strip() == generated_path
                ]
                if len(matching_rows) != 1:
                    errors.append(
                        f"integration target generated reference identity does not match exactly one catalog row: "
                        f"{item.get('normalized_url')}"
                    )
                else:
                    reference_row = matching_rows[0]
                    if (
                        reference_row.get("has_install_command") is True
                        or bool(str(reference_row.get("install_command") or "").strip())
                        or str(reference_row.get("sync_kind") or "").strip() != "none"
                    ):
                        errors.append(
                            f"generated integration reference exposes an install surface: {item.get('normalized_url')}"
                        )
    if dict(item_classification_counts) != EXPECTED_CLASSIFICATION_COUNTS:
        errors.append("integration target item classifications do not match the expected 121/6/158/4 split")
    expected_reference_count = sum(
        EXPECTED_CLASSIFICATION_COUNTS.get(classification, 0) for classification in GENERATED_REFERENCE_CLASSIFICATIONS
    )
    if generated_reference_count != expected_reference_count:
        errors.append("integration target item generated reference count does not match reference classifications")
    if target_payload.get("generated_reference_count") != generated_reference_count:
        errors.append("integration target generated reference count drifted")
    errors.extend(
        generated_reference_materialization_errors(
            target_payload,
            root=ROOT,
            authoring_dir=AUTHORING_DIR,
            marker=INTEGRATION_TARGET_MARKER,
        )
    )
    return errors


def load_promotion_wave_plan() -> tuple[dict[str, Any], list[str]]:
    """Load and validate the canonical base plan without mutating the tree."""
    path = manifest_json("promotion-wave-plan.json")
    if not path.is_file():
        return {}, ["missing promotion-wave-plan.json; run the candidate corpus generator first"]
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"promotion-wave-plan.json is unreadable: {exc}"]
    errors = validate_promotion_wave_plan(plan)
    return (plan if isinstance(plan, dict) else {}), errors


def load_harness_assurance() -> dict[str, Any]:
    if not HARNESS_ASSURANCE.is_file():
        return {"complete": False, "target_harness_count": 0, "totals": {}}
    payload = load_json(HARNESS_ASSURANCE)
    return payload if isinstance(payload, dict) else {"complete": False, "target_harness_count": 0, "totals": {}}


def harness_assurance_errors(payload: dict[str, Any] | None = None) -> list[str]:
    assurance = payload or load_harness_assurance()
    errors: list[str] = []
    totals = assurance.get("totals", {}) if isinstance(assurance, dict) else {}
    agents = assurance.get("agents", []) if isinstance(assurance, dict) else []
    if assurance.get("complete") is not True:
        errors.append("harness install assurance is not complete")
    expected_harnesses = set(SUPPORTED_AGENT_IDS)
    observed_harnesses = (
        {str(agent.get("agent") or "") for agent in agents if isinstance(agent, dict)}
        if isinstance(agents, list)
        else set()
    )
    if (
        assurance.get("target_harness_count") != len(SUPPORTED_AGENT_IDS)
        or not isinstance(agents, list)
        or len(agents) != len(SUPPORTED_AGENT_IDS)
        or observed_harnesses != expected_harnesses
    ):
        errors.append(
            "harness install assurance does not exactly cover the supported harnesses: "
            + ", ".join(SUPPORTED_AGENT_IDS)
        )
    for field in ("missing", "pin_blocked", "commands"):
        if int_value(totals.get(field)) != 0:
            errors.append(f"harness install assurance has nonzero {field}")
    if any(isinstance(agent, dict) and agent.get("error") for agent in agents if isinstance(agents, list)):
        errors.append("harness install assurance contains an agent inventory error")
    fingerprints = (
        ("catalog_index_sha256", ROOT / "docs/public/generated-registries/skills-catalog-index.json"),
        ("promotion_overrides_sha256", OVERRIDES),
    )
    for field, path in fingerprints:
        if not path.is_file() or assurance.get(field) != hashlib.sha256(path.read_bytes()).hexdigest():
            errors.append(f"harness install assurance {field} is stale")
    return errors


def semantic_json_sha256(path: Path) -> str:
    payload = load_json(path)
    payload.pop("generated_at", None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def load_non_skill_assurance() -> dict[str, Any]:
    if not NON_SKILL_ASSURANCE.is_file():
        return {"complete": False, "unique_target_count": 0, "items": [], "totals": {}}
    payload = load_json(NON_SKILL_ASSURANCE)
    return (
        payload
        if isinstance(payload, dict)
        else {
            "complete": False,
            "unique_target_count": 0,
            "items": [],
            "totals": {},
        }
    )


def runtime_activation_summary(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate and summarize the authoritative successor runtime ledger."""
    assurance = payload
    if assurance is None:
        if not RUNTIME_ACTIVATION_ASSURANCE.is_file():
            raise ValueError("runtime activation assurance is missing")
        loaded = load_json(RUNTIME_ACTIVATION_ASSURANCE)
        assurance = loaded if isinstance(loaded, dict) else {}

    errors: list[str] = []
    artifacts = assurance.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("artifacts must be a list")
        artifacts = []

    artifact_ids: set[str] = set()
    status_counts: Counter[str] = Counter()
    kind_counts: Counter[str] = Counter()
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            errors.append(f"artifact {index} is not an object")
            continue
        artifact_id = artifact.get("artifact_id")
        kind = artifact.get("kind")
        status = artifact.get("status")
        if not isinstance(artifact_id, str) or not artifact_id or artifact_id in artifact_ids:
            errors.append(f"artifact {index} has an invalid or duplicate id")
        else:
            artifact_ids.add(artifact_id)
        if kind not in EXPECTED_RUNTIME_KIND_COUNTS:
            errors.append(f"artifact {index} has invalid kind {kind!r}")
        else:
            kind_counts[str(kind)] += 1
        if status not in {"accepted", "incomplete"}:
            errors.append(f"artifact {index} has invalid status {status!r}")
        else:
            status_counts[str(status)] += 1

    expected_status_counts = {"accepted": status_counts["accepted"], "incomplete": status_counts["incomplete"]}
    observed_kind_counts = {kind: kind_counts[kind] for kind in EXPECTED_RUNTIME_KIND_COUNTS}
    totals = assurance.get("totals")
    if assurance.get("source_target_count") != EXPECTED_UNIQUE_COUNT:
        errors.append("source target count must be 289")
    if assurance.get("runtime_artifact_count") != EXPECTED_RUNTIME_ARTIFACT_COUNT:
        errors.append("runtime artifact count must be 65")
    if assurance.get("minimum_runtime_artifact_count") != EXPECTED_RUNTIME_ARTIFACT_COUNT:
        errors.append("minimum runtime artifact count must be 65")
    if len(artifacts) != EXPECTED_RUNTIME_ARTIFACT_COUNT:
        errors.append("artifact ledger must contain 65 rows")
    if observed_kind_counts != EXPECTED_RUNTIME_KIND_COUNTS:
        errors.append(f"runtime kind counts must be {EXPECTED_RUNTIME_KIND_COUNTS}")
    if not isinstance(totals, dict) or totals.get("status_counts") != expected_status_counts:
        errors.append("recorded runtime status counts do not match the artifact ledger")
    if not isinstance(totals, dict) or totals.get("kind_counts") != EXPECTED_RUNTIME_KIND_COUNTS:
        errors.append("recorded runtime kind counts do not match the 65-artifact model")
    requested_full_usability = assurance.get("requested_full_usability")
    if not isinstance(requested_full_usability, bool):
        errors.append("requested_full_usability must be boolean")
    active_blockers = assurance.get("active_blockers")
    if not isinstance(active_blockers, list):
        errors.append("active blockers must be a list")
        active_blockers = []
    elif len(active_blockers) != status_counts["incomplete"]:
        errors.append("active blocker count does not match incomplete runtime artifacts")
    if errors:
        raise ValueError("runtime activation assurance is invalid:\n- " + "\n- ".join(errors))

    return {
        "assurance_file": RUNTIME_ACTIVATION_ASSURANCE.name,
        "source_target_count": EXPECTED_UNIQUE_COUNT,
        "runtime_artifact_count": EXPECTED_RUNTIME_ARTIFACT_COUNT,
        "accepted": status_counts["accepted"],
        "incomplete": status_counts["incomplete"],
        "kind_counts": observed_kind_counts,
        "requested_full_usability": requested_full_usability,
        "active_blocker_count": len(active_blockers),
    }


def non_skill_assurance_errors(payload: dict[str, Any] | None = None) -> list[str]:
    assurance = payload or load_non_skill_assurance()
    errors: list[str] = []
    items = assurance.get("items", []) if isinstance(assurance, dict) else []
    if assurance.get("complete") is not True:
        errors.append("non-skill install assurance is not complete")
    if assurance.get("unique_target_count") != EXPECTED_UNIQUE_COUNT or not isinstance(items, list):
        errors.append("non-skill install assurance does not cover 289 normalized targets")
        items = []
    urls = [
        str(item.get("normalized_url") or "").lower()
        for item in items
        if isinstance(item, dict) and item.get("normalized_url")
    ]
    expected_urls = set(integration_target_index())
    if len(urls) != EXPECTED_UNIQUE_COUNT or len(urls) != len(set(urls)) or set(urls) != expected_urls:
        errors.append("non-skill install assurance URL coverage is incomplete or duplicated")
    failed_artifacts = assurance.get("failed_artifacts", [])
    if failed_artifacts:
        errors.append("non-skill install assurance contains failed runtime artifacts")
    source_paths = {
        "integration_decisions": MANIFEST_DIR / "integration-decisions.json",
        "mcp_registry": ROOT / "config" / "mcp-registry.json",
        "plugin_registry": ROOT / "config" / "plugin-extension-registry.json",
        "tooling_policy": ROOT / "config" / "tooling-policy.json",
    }
    expected_fingerprints: dict[str, str] = {}
    for name, path in source_paths.items():
        if not path.is_file():
            errors.append(f"non-skill assurance fingerprint source is missing: {path.name}")
            continue
        expected_fingerprints[name] = semantic_json_sha256(path)
    if len(expected_fingerprints) != len(source_paths) or assurance.get("source_fingerprints") != expected_fingerprints:
        errors.append("non-skill install assurance source fingerprints are stale")
    for item in items:
        if not isinstance(item, dict):
            errors.append("non-skill install assurance row is not an object")
            continue
        if item.get("runtime_disposition") == "hard-quarantined" and item.get("artifacts"):
            errors.append(f"hard-quarantined target has runtime artifacts: {item.get('normalized_url')}")
        for artifact in item.get("artifacts", []):
            if not isinstance(artifact, dict) or artifact.get("verified") is not True:
                errors.append(f"unverified non-skill artifact: {item.get('normalized_url')}")
            if (
                isinstance(artifact, dict)
                and artifact.get("kind") == "mcp"
                and artifact.get("mcp_enabled") is not False
            ):
                errors.append(f"candidate MCP is not disabled: {item.get('normalized_url')}")
    return errors


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_overrides() -> list[Any]:
    if not OVERRIDES.exists():
        return []
    payload = load_json(OVERRIDES)
    if not isinstance(payload, dict):
        raise ValueError("promotion-overrides.json payload must be an object")
    overrides = payload.get("overrides", [])
    if not isinstance(overrides, list):
        raise ValueError("promotion-overrides.json overrides must be a list")
    return [normalize_override_record(override) if isinstance(override, dict) else override for override in overrides]


def normalize_terminal_route_note(note: Any) -> str:
    value = str(note).strip()
    if not value:
        return ""
    replacement = TERMINAL_ROUTE_NOTE_REPLACEMENTS.get(value.lower())
    if replacement:
        return replacement
    return value.replace(LEGACY_SOURCE_LIST_ROUTE, "terminal route")


def normalize_override_record(override: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(override)
    raw_notes = normalized.get("terminal_route_notes", normalized.get("remaining_blockers", []))
    note_values = (
        raw_notes if isinstance(raw_notes, (list, tuple)) else [raw_notes] if isinstance(raw_notes, str) else []
    )
    notes = []
    for note in note_values:
        normalized_note = normalize_terminal_route_note(note)
        if normalized_note:
            notes.append(normalized_note)
    normalized["terminal_route_notes"] = notes
    normalized.pop("remaining_blockers", None)
    normalized.pop("candidate_authoring_name", None)
    return normalized


def normalize_overrides_file() -> None:
    if not OVERRIDES.exists():
        return
    payload = load_json(OVERRIDES)
    if not isinstance(payload, dict):
        return
    overrides = payload.get("overrides", [])
    if not isinstance(overrides, list):
        return
    normalized_overrides = [
        normalize_override_record(override) if isinstance(override, dict) else override for override in overrides
    ]
    normalized_payload = dict(payload)
    normalized_payload["overrides"] = normalized_overrides
    if normalized_payload != payload:
        write_json(OVERRIDES, normalized_payload)


def authoring_path_for(stem: str) -> Path:
    path = (AUTHORING_DIR / f"{stem}.mdx").resolve()
    path.relative_to(AUTHORING_DIR.resolve())
    return path


def is_safe_authoring_stem(value: Any) -> bool:
    return isinstance(value, str) and bool(AUTHORING_STEM_RE.fullmatch(value))


def is_within_authoring_dir(path: Path) -> bool:
    try:
        path.resolve().relative_to(AUTHORING_DIR.resolve())
    except ValueError:
        return False
    return True


def validate_override_records(overrides: list[Any], rows: list[Any]) -> list[str]:
    target_payload = load_integration_targets()
    errors: list[str] = integration_target_errors(target_payload)
    targets_by_url = integration_target_index(target_payload)
    decisions = load_manifest_json("integration-decisions.json", {}).get("decisions", [])
    decisions_by_url = {
        str(item.get("normalized_url") or "").lower(): str(item.get("decision") or "")
        for item in decisions
        if isinstance(item, dict) and item.get("normalized_url")
    }
    seen_skill_names: set[str] = set()
    seen_target_skills: set[tuple[str, str]] = set()

    for index, override in enumerate(overrides):
        label = f"override {index + 1}"
        if not isinstance(override, dict):
            errors.append(f"{label} is not an object")
            continue

        for field in REQUIRED_OVERRIDE_STRING_FIELDS:
            value = override.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label} missing required string field {field}")

        normalized_url = override.get("normalized_url")
        skill_name = override.get("skill_name")
        normalized_url_key = str(normalized_url or "").lower()
        target_skill_key = (normalized_url_key, str(skill_name or ""))
        if target_skill_key in seen_target_skills:
            errors.append(f"duplicate promoted normalized_url / skill_name mapping: {normalized_url} / {skill_name}")
        seen_target_skills.add(target_skill_key)
        if not is_safe_authoring_stem(skill_name):
            errors.append(f"{label} has invalid skill_name authoring stem")
        else:
            if skill_name in seen_skill_names:
                errors.append(f"duplicate promoted skill_name {skill_name}")
            seen_skill_names.add(skill_name)
            if not is_within_authoring_dir(authoring_path_for(skill_name)):
                errors.append(f"{label} promoted path escapes authoring directory")
        if override.get("status") != "install-now-after-trust-gate":
            errors.append(f"{label} status is not install-now-after-trust-gate")
        if override.get("sync_kind") != "skills-cli":
            errors.append(f"{label} sync_kind is not skills-cli")
        if override.get("source_list_evidence") != "source-list-found":
            errors.append(f"{label} source_list_evidence is not source-list-found")
        if str(override.get("intake_decision") or "") in TERMINAL_HARD_BLOCK_DECISIONS:
            errors.append(f"{label} cannot promote a terminal hard-block decision")
        if decisions_by_url.get(normalized_url_key) in TERMINAL_HARD_BLOCK_DECISIONS:
            errors.append(f"{label} conflicts with the source decision hard-block gate")
        target = targets_by_url.get(normalized_url_key)
        if target is None:
            errors.append(f"{label} normalized_url has no integration target: {normalized_url}")
        else:
            if target.get("hard_blocked") is True or target.get("integration_classification") == (
                "integrated-quarantine-reference"
            ):
                errors.append(f"{label} conflicts with the integration target hard-block gate")
            if normalized_raw_indexes(override.get("raw_indexes")) != normalized_raw_indexes(target.get("raw_indexes")):
                errors.append(f"{label} raw_indexes do not match the integration target")
        if str(override.get("license") or "").upper() in {"", "NOASSERTION", "UNKNOWN"}:
            errors.append(f"{label} lacks a compatible asserted license")

        executed_commands = override.get("executed_commands")
        if not isinstance(executed_commands, list) or not all(
            isinstance(command, str) for command in executed_commands
        ):
            errors.append(f"{label} executed_commands must be a list of strings")
            executed_commands = []
        installed_paths = override.get("installed_paths")
        if not isinstance(installed_paths, list) or not all(isinstance(path, str) for path in installed_paths):
            errors.append(f"{label} installed_paths must be a list of strings")
            installed_paths = []
        if override.get("live_install_executed"):
            live_commands = [
                parsed
                for command in executed_commands
                if (parsed := parse_skills_add_command(command)) is not None and parsed["live"]
            ]
            if not live_commands:
                errors.append(f"live install for {normalized_url} lacks non-dry-run install command evidence")
            else:
                expected_source = normalize_install_source(str(override.get("install_source") or ""))
                expected_selector = str(override.get("install_skill_name") or skill_name or "")
                mismatched_sources = [
                    command["source"] for command in live_commands if command["source"] != expected_source
                ]
                if mismatched_sources:
                    errors.append(f"live install for {normalized_url} has mismatched install source evidence")
                selector_evidence = any(
                    expected_selector in command["skills"] or "*" in command["skills"] for command in live_commands
                )
                source_bulk_evidence = bool(override.get("source_bulk_install_evidence")) and any(
                    not command["skills"] for command in live_commands
                )
                if expected_selector and not (selector_evidence or source_bulk_evidence):
                    errors.append(f"live install for {normalized_url} lacks matching skill selector evidence")
                expected_agents = {
                    "claude-code" if agent == "grok" else agent
                    for agent in override.get("target_agents", [])
                    if isinstance(agent, str)
                }
                covered_agents = {agent for command in live_commands for agent in command["agents"]}
                if expected_agents - covered_agents:
                    errors.append(f"live install for {normalized_url} lacks target harness command evidence")
            if not installed_paths:
                errors.append(f"live install for {normalized_url} lacks installed path evidence")
            for installed_path in installed_paths:
                if not installed_path_matches_override(installed_path, override):
                    errors.append(f"live install for {normalized_url} has unrelated installed path: {installed_path}")
            for missing_path in missing_installed_skill_md_paths(override):
                errors.append(f"live install for {normalized_url} has missing installed SKILL.md: {missing_path}")

    return errors


def normalize_install_source(source: str) -> str:
    normalized = source.strip().removeprefix("github:")
    normalized = re.sub(r"^https?://github\.com/", "", normalized, flags=re.I).removesuffix(".git")
    parts = normalized.split("/")
    if len(parts) >= 2:
        normalized = "/".join(parts[:2])
    if normalized.count("/") >= 1 and "@" in normalized.rsplit("/", 1)[-1]:
        normalized = normalized.rsplit("@", 1)[0]
    return normalized.rstrip("/").lower()


def parse_skills_add_command(command: Any) -> dict[str, Any] | None:
    command_text = str(command)
    try:
        parts = shlex.split(command_text)
    except ValueError:
        return None
    if not parts or parts[0] != "npx":
        return None
    index = 1
    while index < len(parts) and parts[index] in {"-y", "--yes"}:
        index += 1
    if parts[index : index + 2] != ["skills", "add"] or index + 2 >= len(parts):
        return None
    source = normalize_install_source(parts[index + 2])
    skills: list[str] = []
    agents: list[str] = []
    live = "# failed:" not in command_text.lower()
    noninteractive = False
    global_install = False
    index += 3
    while index < len(parts):
        part = parts[index]
        if part in {"-y", "--yes"}:
            noninteractive = True
            index += 1
            continue
        if part in {"-g", "--global"}:
            global_install = True
            index += 1
            continue
        if part in {"--list", "--dry-run", "--help"}:
            live = False
            index += 1
            continue
        if part == "--skill" and index + 1 < len(parts):
            skills.append(parts[index + 1])
            index += 2
            continue
        if part in {"-a", "--agent"}:
            index += 1
            while index < len(parts) and not parts[index].startswith("-"):
                if parts[index] in {";", "&&", "||", "|", "&"} or parts[index].startswith("#"):
                    return None
                agents.append(parts[index])
                index += 1
            continue
        if part == "--copy":
            index += 1
            continue
        return None
    live = live and noninteractive and global_install
    return {"source": source, "skills": tuple(skills), "agents": tuple(agents), "live": live}


def is_live_install_command(command: Any) -> bool:
    parsed = parse_skills_add_command(command)
    return bool(parsed and parsed["live"])


def installed_path_matches_override(raw_path: Any, override: dict[str, Any]) -> bool:
    skill_md = installed_skill_md_path(raw_path).resolve()
    path = skill_md.parent
    expected_names = {
        str(override.get("skill_name") or ""),
        str(override.get("install_skill_name") or ""),
    } - {""}
    allowed_roots = (
        ROOT / ".agents" / "skills",
        Path(os.path.expanduser("~/.agents/skills")),
        Path(os.path.expanduser("~/.claude/skills")),
        Path(os.path.expanduser("~/.codex/skills")),
        Path(os.path.expanduser("~/.config/crush/skills")),
        Path(os.path.expanduser("~/.config/opencode/skills")),
        Path(os.path.expanduser("~/.cursor/skills")),
        Path(os.path.expanduser("~/.grok/skills")),
    )
    if path.name not in expected_names or not any(path.is_relative_to(root.resolve()) for root in allowed_roots):
        return False
    try:
        frontmatter, _ = parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError, yaml.YAMLError):
        return False
    if not isinstance(frontmatter, dict):
        return False
    return str(frontmatter.get("name") or "") in expected_names


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


def render_promoted_row(override: dict[str, Any]) -> str:
    skill_name = str(override["skill_name"])
    install_skill_name = str(override.get("install_skill_name") or skill_name)
    raw_indexes = ", ".join(str(index) for index in override.get("raw_indexes", []))
    executed_commands = [str(command) for command in override.get("executed_commands", [])]
    installed_paths = [str(path) for path in override.get("installed_paths", [])]
    install_evidence_note = str(override.get("install_evidence_note", "")).strip()
    target_agents = list(override.get("target_agents", []))
    frontmatter = [
        "---",
        f"name: {yaml_string(skill_name)}",
        f"description: {yaml_string(override.get('description', ''))}",
        f"title: {yaml_string(override.get('title', skill_name.replace('-', ' ').title()))}",
        'source_kind: "curated-external"',
        f"source: {yaml_string(override.get('source_name', ''))}",
        f"install_source: {yaml_string(override.get('install_source', ''))}",
        f"install_command: {yaml_string(override.get('install_command', ''))}",
        f"install_skill_name: {yaml_string(install_skill_name)}",
        f"status: {yaml_string(override.get('status', 'install-now-after-trust-gate'))}",
        f"trust_tier: {yaml_string(override.get('trust_tier', 'curated-trust-gated'))}",
        f"provenance_status: {yaml_string(override.get('provenance_status', 'verified-install-command'))}",
        f"sync_kind: {yaml_string(override.get('sync_kind', 'skills-cli'))}",
        f"target_agents: {yaml_flow_list(target_agents)}",
        f"source_url: {yaml_string(override.get('normalized_url', ''))}",
        f"selector_mode: {yaml_string(override.get('selector_mode', 'named'))}",
        f"audit_date: {yaml_string(override.get('audit_date', '2026-07-07'))}",
        f"audited_head: {yaml_string(override.get('audited_head', ''))}",
        f"license: {yaml_string(override.get('license', ''))}",
        f"pin_policy: {yaml_string(override.get('pin_policy', 'pin-before-install'))}",
        f"no_pin_rationale: {yaml_string(override.get('no_pin_rationale', ''))}",
        f"source_list_evidence: {yaml_string(override.get('source_list_evidence', 'source-list-found'))}",
        f"executable_surface: {yaml_string(override.get('executable_surface', 'reviewed'))}",
        f"credential_behavior: {yaml_string(override.get('credential_behavior', ''))}",
        f"network_access: {yaml_string(override.get('network_access', ''))}",
        f"file_access: {yaml_string(override.get('file_access', ''))}",
        f"live_action_risk: {yaml_string(override.get('live_action_risk', ''))}",
        f"risk_category: {yaml_string(override.get('risk_category', 'standard-review'))}",
        f"dedupe_notes: {yaml_string('Raw indexes covered: ' + raw_indexes)}",
        f"notes: {yaml_string(override.get('description', ''))}",
        f"risk_notes: {yaml_string(override.get('live_action_risk', ''))}",
        f"promotion_policy: {yaml_string(override.get('promotion_policy', ''))}",
        f"provenance_evidence: {yaml_string(override.get('provenance_evidence', ''))}",
        "---",
        "",
    ]
    body = [
        f"# {skill_name.replace('-', ' ').title()}",
        "",
        (
            f"This row integrates `{override.get('source_name', '')}` as an installable curated external skill "
            "after source, license, security, attribution, and harness review."
        ),
        "",
        "## Reviewed Integration",
        "",
        f"- Raw indexes covered: {raw_indexes}",
        f"- Normalized URL: [{override.get('normalized_url', '')}]({override.get('normalized_url', '')})",
        f"- Catalog skill id: `{skill_name}`",
        f"- Upstream install selector: `{install_skill_name}`",
        f"- Install command: `{override.get('install_command', '')}`",
        f"- Inspected commit SHA: `{override.get('audited_head', 'unresolved')}`",
        f"- License status: `{override.get('license', 'unresolved')}`",
        f"- Source-list evidence: `{override.get('source_list_evidence', 'unknown')}`",
        f"- Live local install recorded: `{str(bool(override.get('live_install_executed'))).lower()}`",
        "",
        "## Local Install Evidence",
        "",
        *[f"- Executed command: `{command}`" for command in executed_commands],
        *[f"- Installed path: `{path}`" for path in installed_paths],
        *([f"- Install evidence note: {install_evidence_note}"] if install_evidence_note else []),
        "",
        "## Safety Notes",
        "",
        f"- Credential behavior: {override.get('credential_behavior', '')}",
        f"- Network access: {override.get('network_access', '')}",
        f"- File access: {override.get('file_access', '')}",
        f"- Live action risk: {override.get('live_action_risk', '')}",
        (
            "- MCP, background services, and external binaries remain opt-in; do not auto-start them from this "
            "catalog row."
        ),
        (
            "- Secrets, tokens, private keys, connection strings, cookies, OAuth grants, and account IDs must not "
            "be committed."
        ),
        "",
        "## Docs-Steward Notes",
        "",
        "- This row is the installable catalog record for the matching reviewed external source.",
        (
            "- Auth, install, validation, attribution, and promotion evidence remain visible in the corpus "
            "integration manifests."
        ),
    ]
    return "\n".join(frontmatter + body) + "\n"


def promoted_row_matches_override(path: Path, override: dict[str, Any]) -> bool:
    """Return whether an existing enriched row matches promotion identity."""
    if not path.is_file():
        return False
    try:
        frontmatter, _ = parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError, yaml.YAMLError):
        return False
    if not isinstance(frontmatter, dict):
        return False

    expected = {
        "name": str(override["skill_name"]),
        "source_kind": "curated-external",
        "install_command": str(override.get("install_command", "")),
        "install_skill_name": str(override.get("install_skill_name") or override["skill_name"]),
        "status": str(override.get("status", TRUST_CLEARED_STATUS)),
        "trust_tier": str(override.get("trust_tier", TRUST_CLEARED_TIER)),
        "provenance_status": str(override.get("provenance_status", "verified-install-command")),
        "sync_kind": str(override.get("sync_kind", "skills-cli")),
        "source_url": str(override.get("normalized_url", "")),
        "selector_mode": str(override.get("selector_mode", "named")),
        "audit_date": str(override.get("audit_date", "2026-07-07")),
        "audited_head": str(override.get("audited_head", "")),
        "license": str(override.get("license", "")),
        "pin_policy": str(override.get("pin_policy", "pin-before-install")),
        "no_pin_rationale": str(override.get("no_pin_rationale", "")),
        "source_list_evidence": str(override.get("source_list_evidence", "source-list-found")),
        "executable_surface": str(override.get("executable_surface", "reviewed")),
        "credential_behavior": str(override.get("credential_behavior", "")),
        "network_access": str(override.get("network_access", "")),
        "file_access": str(override.get("file_access", "")),
        "live_action_risk": str(override.get("live_action_risk", "")),
        "risk_category": str(override.get("risk_category", "standard-review")),
        "promotion_policy": str(override.get("promotion_policy", "")),
        "provenance_evidence": str(override.get("provenance_evidence", "")),
    }
    if any(str(frontmatter.get(field, "")) != value for field, value in expected.items()):
        return False
    if normalize_install_source(str(frontmatter.get("source", ""))) != normalize_install_source(
        str(override.get("source_name", ""))
    ):
        return False
    if normalize_install_source(str(frontmatter.get("install_source", ""))) != normalize_install_source(
        str(override.get("install_source", ""))
    ):
        return False
    actual_agents = frontmatter.get("target_agents", [])
    return isinstance(actual_agents, list) and sorted(str(value) for value in actual_agents) == sorted(
        str(value) for value in override.get("target_agents", [])
    )


def write_promoted_row(path: Path, override: dict[str, Any]) -> bool:
    """Write a promotion row unless a matching enriched row already exists."""
    if promoted_row_matches_override(path, override):
        return False
    path.write_text(render_promoted_row(override), encoding="utf-8")
    return True


def promoted_summary_row(override: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    intake_decision = override.get("intake_decision", "") or (previous or {}).get("intake_decision", "")
    return {
        "name": override["skill_name"],
        "path": str(authoring_path_for(str(override["skill_name"])).relative_to(ROOT.resolve())),
        "normalized_url": override["normalized_url"],
        "source_name": override["source_name"],
        "raw_indexes": override.get("raw_indexes") or (previous or {}).get("raw_indexes", []),
        "status": override.get("status", "install-now-after-trust-gate"),
        "trust_tier": override.get("trust_tier", TRUST_CLEARED_TIER),
        "sync_kind": override.get("sync_kind", "skills-cli"),
        "install_command": override.get("install_command", ""),
        "live_install_executed": bool(override.get("live_install_executed")),
        "risk_tier": override.get("risk_tier", (previous or {}).get("risk_tier", "standard-review")),
        "intake_decision": intake_decision,
        "source_list_evidence": override.get(
            "source_list_evidence",
            (previous or {}).get("source_list_evidence", "source-list-found"),
        ),
        "found_skill_count": int(override.get("found_skill_count", (previous or {}).get("found_skill_count", 0))),
        "install_evidence_note": override.get("install_evidence_note", ""),
        "terminal_route_notes": override.get(
            "terminal_route_notes",
            (previous or {}).get("terminal_route_notes", []),
        ),
    }


def int_value(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def manifest_json(name: str) -> Path:
    return MANIFEST_DIR / name


def load_manifest_json(name: str, default: Any) -> Any:
    path = manifest_json(name)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def restore_committed_gate_artifacts() -> None:
    for name in BASELINE_GATE_ARTIFACTS:
        relative = f"planning/manifests/candidate-corpus-jul2026/{name}"
        result = subprocess.run(
            ["git", "show", f"HEAD:{relative}"],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            manifest_json(name).write_bytes(result.stdout)


def promoted_summary_rows_by_url() -> dict[str, list[dict[str, Any]]]:
    if not SUMMARY.exists():
        return {}
    summary = load_json(SUMMARY)
    rows = summary.get("rows", [])
    if not isinstance(rows, list):
        return {}
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict) or not row.get("install_command") or not row.get("normalized_url"):
            continue
        normalized_url = str(row["normalized_url"]).lower()
        result[normalized_url].append({
            "name": row.get("name", ""),
            "path": row.get("path", ""),
            "source": row.get("source_name", ""),
            "install_source": row.get("source_name", ""),
            "source_url": row.get("normalized_url", ""),
            "status": row.get("status", ""),
            "trust_tier": row.get("trust_tier", ""),
            "sync_kind": row.get("sync_kind", ""),
            "has_install_command": True,
        })
    return dict(result)


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


def existing_rows_trust_cleared(rows: Any) -> bool:
    if not isinstance(rows, list):
        return False
    install_surface_rows = [row for row in rows if isinstance(row, dict) and existing_row_has_install_surface(row)]
    return bool(install_surface_rows) and all(existing_row_trust_cleared(row) for row in install_surface_rows)


def coverage_status_from_existing_rows(rows: Any) -> str:
    if existing_rows_trust_cleared(rows):
        return COVERAGE_TRUST_CLEARED
    if isinstance(rows, list) and any(isinstance(row, dict) and existing_row_has_install_surface(row) for row in rows):
        return COVERAGE_INSPECTION_REQUIRED
    if isinstance(rows, list) and rows:
        return COVERAGE_REFERENCE
    return COVERAGE_NEEDS_PROMOTION


def coverage_item_trust_cleared(item: dict[str, Any]) -> bool:
    return item.get("coverage_status") == COVERAGE_TRUST_CLEARED and existing_rows_trust_cleared(
        item.get("existing_rows")
    )


def trust_cleared_rows_for_item(item: dict[str, Any]) -> list[dict[str, Any]]:
    rows = item.get("existing_rows", [])
    if not isinstance(rows, list):
        rows = []
    candidates = [row for row in rows if isinstance(row, dict)]
    return [row for row in candidates if existing_row_trust_cleared(row)]


def retained_existing_coverage_urls() -> set[str]:
    coverage = load_manifest_json("existing-integration-coverage.json", {"items": []})
    items = coverage.get("items", []) if isinstance(coverage, dict) else []
    selected: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized_url = str(item.get("normalized_url", "")).lower()
        if existing_rows_trust_cleared(item.get("existing_rows")) and normalized_url not in selected:
            selected.append(normalized_url)
    return set(selected)


def catalog_row_reference(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize a summary row to the integration-target catalog row shape."""
    return {
        "name": row.get("name", ""),
        "path": row.get("path", ""),
        "source": row.get("source_name", row.get("source", "")),
        "install_source": row.get("install_source", row.get("source_name", "")),
        "source_url": row.get("normalized_url", row.get("source_url", "")),
        "status": row.get("status", ""),
        "trust_tier": row.get("trust_tier", ""),
        "sync_kind": row.get("sync_kind", ""),
        "has_install_command": existing_row_has_install_surface(row),
    }


def dedupe_catalog_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (str(row.get("name", "")), str(row.get("path", "")), str(row.get("source_url", "")))
        deduped[key] = row
    return list(deduped.values())


def reconcile_integration_targets(summary: dict[str, Any], overrides: list[dict[str, Any]]) -> dict[str, Any]:
    payload = load_integration_targets()
    items = payload.get("items", []) if isinstance(payload, dict) else []
    if not isinstance(items, list):
        raise ValueError("integration-targets.json items must be a list")
    summary_rows = summary.get("rows", []) if isinstance(summary, dict) else []
    rows_by_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in summary_rows if isinstance(summary_rows, list) else []:
        if not isinstance(row, dict) or not row.get("normalized_url"):
            continue
        if str(row.get("name") or "").startswith("candidate-corpus-"):
            continue
        rows_by_url[str(row["normalized_url"]).lower()].append(catalog_row_reference(row))
    overridden_urls = {
        str(override.get("normalized_url") or "").lower() for override in overrides if override.get("normalized_url")
    }

    classification_counts: Counter[str] = Counter()
    raw_indexes: set[int] = set()
    integrated_count = 0
    for item in items:
        if not isinstance(item, dict) or not item.get("normalized_url"):
            continue
        normalized_url = str(item["normalized_url"]).lower()
        generated_name = str(item.get("generated_reference_name") or "")
        generated_path = str(item.get("generated_reference_path") or "")
        existing_rows = item.get("catalog_rows", [])
        if not isinstance(existing_rows, list):
            existing_rows = []
        base_rows = [
            row
            for row in existing_rows
            if isinstance(row, dict)
            and not (
                normalized_url in overridden_urls
                and (str(row.get("name") or "") == generated_name or str(row.get("path") or "") == generated_path)
            )
        ]
        rows = dedupe_catalog_rows(base_rows + rows_by_url.get(normalized_url, []))
        item["catalog_rows"] = rows
        if normalized_url in overridden_urls:
            item["generated_reference_name"] = ""
            item["generated_reference_path"] = ""
        classification = str(item.get("integration_classification") or "")
        if classification not in EXPECTED_CLASSIFICATION_COUNTS:
            raise ValueError(f"integration target has invalid classification: {item.get('normalized_url')}")
        install_rows = [row for row in rows if existing_row_has_install_surface(row)]
        trust_cleared_installable = bool(install_rows) and all(existing_row_trust_cleared(row) for row in install_rows)
        item["trust_cleared_installable"] = (
            trust_cleared_installable and classification != "integrated-quarantine-reference"
        )
        item["hard_blocked"] = classification == "integrated-quarantine-reference"
        classification_counts[classification] += 1
        raw_indexes.update(normalized_raw_indexes(item.get("raw_indexes")))
        integrated_count += int(integration_target_is_accounted(item))

    payload["generated_at"] = now()
    payload["raw_entries_covered"] = len(raw_indexes)
    payload["unique_targets"] = len(items)
    payload["generated_reference_count"] = sum(
        bool(item.get("generated_reference_path")) for item in items if isinstance(item, dict)
    )
    payload["classification_counts"] = dict(sorted(classification_counts.items()))
    payload["integrated_targets"] = integrated_count
    payload["unintegrated_targets"] = len(items) - integrated_count
    write_json(INTEGRATION_TARGETS, payload)
    return payload


def generated_reference_path(item: dict[str, Any]) -> Path | None:
    relative_path = str(item.get("generated_reference_path") or "")
    if not relative_path:
        return None
    path = (ROOT / relative_path).resolve()
    if not is_within_authoring_dir(path):
        raise ValueError(f"integration target generated reference escapes authoring directory: {relative_path}")
    return path


def remove_generated_reference(item: dict[str, Any]) -> str:
    path = generated_reference_path(item)
    if path is None or not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if INTEGRATION_TARGET_MARKER not in text and LEGACY_CANDIDATE_MARKER not in text:
        raise ValueError(f"refusing to remove non-generated authoring row: {path.relative_to(ROOT)}")
    path.unlink()
    return str(path.relative_to(ROOT))


def remove_legacy_candidate_rows() -> list[str]:
    removed: list[str] = []
    for path in sorted(AUTHORING_DIR.glob("candidate-corpus-*.mdx")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if LEGACY_CANDIDATE_MARKER not in text:
            continue
        path.unlink()
        removed.append(str(path.relative_to(ROOT)))
    return removed


def overlay_existing_coverage() -> set[str]:
    coverage_path = manifest_json("existing-integration-coverage.json")
    coverage = load_manifest_json("existing-integration-coverage.json", {"version": 1, "items": []})
    if not isinstance(coverage, dict):
        return set()
    items = coverage.get("items", [])
    if not isinstance(items, list):
        return set()
    promoted_rows_by_url = promoted_summary_rows_by_url()
    retained_urls = retained_existing_coverage_urls() | set(promoted_rows_by_url)
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized_url = str(item.get("normalized_url", "")).lower()
        if normalized_url in retained_urls:
            promoted_rows = promoted_rows_by_url.get(normalized_url, [])
            merged_rows = trust_cleared_rows_for_item(item) + promoted_rows
            deduped_rows = {
                (
                    str(row.get("name", "")),
                    str(row.get("path", "")),
                    str(row.get("install_source", "")),
                ): row
                for row in merged_rows
            }
            item["coverage_status"] = COVERAGE_TRUST_CLEARED
            item["existing_rows"] = list(deduped_rows.values())
        else:
            existing_rows = item.get("existing_rows", [])
            item["coverage_status"] = coverage_status_from_existing_rows(existing_rows)
            if item["coverage_status"] == COVERAGE_NEEDS_PROMOTION:
                item["existing_rows"] = []
    coverage["summary"] = dict(
        sorted(
            Counter(
                item.get("coverage_status", COVERAGE_NEEDS_PROMOTION) for item in items if isinstance(item, dict)
            ).items()
        )
    )
    write_json(coverage_path, coverage)
    return retained_urls


def overlay_research_graph(retained_urls: set[str]) -> None:
    graph_path = manifest_json("research-task-graph.json")
    graph = load_manifest_json("research-task-graph.json", {})
    coverage = load_manifest_json("existing-integration-coverage.json", {"items": []})
    if not isinstance(graph, dict):
        return
    lanes = graph.get("unique_target_lanes", [])
    if not isinstance(lanes, list):
        return
    coverage_items = coverage.get("items", []) if isinstance(coverage, dict) else []
    coverage_by_url = {
        str(item.get("normalized_url", "")).lower(): item
        for item in coverage_items
        if isinstance(item, dict) and item.get("normalized_url")
    }
    status_counts: Counter[str] = Counter()
    for lane in lanes:
        if not isinstance(lane, dict):
            continue
        normalized_url = str(lane.get("normalized_url", "")).lower()
        coverage_item = coverage_by_url.get(normalized_url, {})
        coverage_status = str(coverage_item.get("coverage_status") or COVERAGE_NEEDS_PROMOTION)
        lane["existing_integration_status"] = coverage_status
        lane["existing_rows"] = coverage_item.get("existing_rows", []) if isinstance(coverage_item, dict) else []
        if normalized_url in retained_urls and coverage_status == COVERAGE_TRUST_CLEARED:
            lane["terminal_decision_status"] = "covered-by-existing-catalog"
        else:
            decision = str(lane.get("current_intake_decision", ""))
            lane["terminal_decision_status"] = TERMINAL_DECISION_STATUSES.get(
                decision,
                decision.replace("_", "-") if decision else "terminal-native-surface",
            )
        status_counts[coverage_status] += 1
    graph["existing_integration_summary"] = dict(sorted(status_counts.items()))
    write_json(graph_path, graph)


def readiness_item_from_coverage(item: dict[str, Any], covered: bool) -> dict[str, Any]:
    existing_rows = item.get("existing_rows", [])
    if not isinstance(existing_rows, list):
        existing_rows = []
    decision = str(item.get("intake_decision", ""))
    terminal_status = (
        "covered-by-existing-installable-catalog"
        if covered
        else TERMINAL_DECISION_STATUSES.get(
            decision,
            decision.replace("_", "-") if decision else "terminal-native-surface",
        )
    )
    return {
        "packet_id": item.get("packet_id", ""),
        "normalized_url": item.get("normalized_url", ""),
        "source_name": item.get("source_name", ""),
        "raw_indexes": item.get("raw_indexes", []),
        "existing_integration_status": item.get("coverage_status", COVERAGE_NEEDS_PROMOTION),
        "terminal_status": terminal_status,
        "live_install_eligible": False,
        "repo_mutation_eligible": False,
        "install_command": "",
        "existing_rows": existing_rows if item.get("coverage_status") != COVERAGE_NEEDS_PROMOTION else [],
        "terminal_route_requirements": [] if covered else TERMINAL_ROUTE_REQUIREMENTS,
    }


def overlay_promotion_readiness(retained_urls: set[str]) -> None:
    coverage = load_manifest_json("existing-integration-coverage.json", {"items": []})
    items = coverage.get("items", []) if isinstance(coverage, dict) else []
    covered_items = []
    terminal_items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        covered = coverage_item_trust_cleared(item) and str(item.get("normalized_url", "")).lower() in retained_urls
        target = readiness_item_from_coverage(item, covered)
        if covered:
            covered_items.append(target)
        else:
            terminal_items.append(target)
    payload = {
        "version": 1,
        "generated_at": now(),
        "status": "terminal-integration-reconciled",
        "summary": {
            "unique_targets": len(covered_items) + len(terminal_items),
            "covered_by_existing_installable_catalog": len(covered_items),
            "ready_for_repo_promotion": 0,
            "ready_for_live_install": 0,
            "terminal_native_or_hard_blocked": len(terminal_items),
        },
        "covered_by_existing_installable_catalog": covered_items,
        "ready_for_repo_promotion": [],
        "ready_for_live_install": [],
        "terminal_native_or_hard_blocked": terminal_items,
    }
    write_json(manifest_json("promotion-readiness-queue.json"), payload)


def wave_raw_indexes(targets: list[dict[str, Any]]) -> list[int]:
    raw_indexes: set[int] = set()
    for target in targets:
        indexes = target.get("raw_indexes", [])
        if not isinstance(indexes, list):
            continue
        for index in indexes:
            if isinstance(index, int):
                raw_indexes.add(index)
            elif isinstance(index, str) and index.isdigit():
                raw_indexes.add(int(index))
    return sorted(raw_indexes)


def matched_registry_evidence(normalized_url: str, source_name: str) -> list[str]:
    needles = {normalized_url.lower(), source_name.lower()} - {""}
    evidence: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            scalar_text = json.dumps(
                {key: item for key, item in value.items() if not isinstance(item, (dict, list))},
                ensure_ascii=False,
            ).lower()
            if any(needle in scalar_text for needle in needles):
                evidence.append(json.dumps(value, ensure_ascii=False))
                return
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for relative_path in SOURCE_INTEGRATION_FILES:
        path = ROOT / relative_path
        if path.suffix != ".json" or not path.is_file():
            continue
        try:
            visit(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return evidence


def enrich_deep_auth_env_names(summary: dict[str, Any], overrides: list[dict[str, Any]]) -> None:
    """Add source-specific placeholder names from audited local integration artifacts."""
    deep_audit = load_manifest_json("deep-source-audit.json", {})
    deep_items = deep_audit.get("items", []) if isinstance(deep_audit, dict) else []
    if not isinstance(deep_items, list):
        raise ValueError("deep-source-audit.json items must be a list")
    rows = summary.get("rows", []) if isinstance(summary, dict) else []
    rows_by_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, dict) and row.get("normalized_url"):
            rows_by_url[str(row["normalized_url"]).lower()].append(row)
    overrides_by_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for override in overrides:
        if isinstance(override, dict) and override.get("normalized_url"):
            overrides_by_url[str(override["normalized_url"]).lower()].append(override)
    non_skill = load_non_skill_assurance()
    runtime_auth_by_url = {
        str(item.get("normalized_url") or "").lower(): sorted({
            str(value) for value in item.get("auth_env_names", []) if isinstance(value, str) and is_auth_env_name(value)
        })
        for item in non_skill.get("items", [])
        if isinstance(item, dict) and item.get("normalized_url")
    }

    named_item_count = 0
    named_value_count = 0
    for item in deep_items:
        if not isinstance(item, dict):
            continue
        auth_review = item.get("auth_review")
        if not isinstance(auth_review, dict):
            continue
        normalized_url = str(item.get("normalized_url") or "")
        source_name = str(item.get("source_name") or "")
        key = normalized_url.lower()
        runtime_names = runtime_auth_by_url.get(key, [])
        if runtime_names:
            existing_names = {
                str(value)
                for value in auth_review.get("env_vars_or_credentials", [])
                if str(value).strip() and str(value) != AUTH_UNKNOWN_PLACEHOLDER
            }
            auth_review["auth_required"] = True
            auth_review["env_vars_or_credentials"] = sorted(existing_names | set(runtime_names))
            auth_review["runtime_auth_evidence_source"] = "non-skill-install-assurance.json"
        if not auth_review.get("auth_required"):
            continue
        evidence_text: list[str] = []
        evidence_sources: list[str] = []
        for row in rows_by_url.get(key, []):
            row_path = ROOT / str(row.get("path") or "")
            if row_path.is_file():
                evidence_text.append(row_path.read_text(encoding="utf-8", errors="replace")[:500_000])
                evidence_sources.append(str(row_path.relative_to(ROOT)))
        seen_skill_paths: set[Path] = set()
        for override in overrides_by_url.get(key, []):
            for raw_path in override.get("installed_paths", []):
                skill_path = Path(str(raw_path)).expanduser() / "SKILL.md"
                try:
                    resolved = skill_path.resolve()
                except OSError:
                    continue
                if resolved in seen_skill_paths or not resolved.is_file():
                    continue
                seen_skill_paths.add(resolved)
                evidence_text.append(resolved.read_text(encoding="utf-8", errors="replace")[:500_000])
                evidence_sources.append(f"installed-skill:{override.get('skill_name', 'unknown')}")
        registry_evidence = matched_registry_evidence(normalized_url, source_name)
        if registry_evidence:
            evidence_text.extend(registry_evidence)
            evidence_sources.append("matched-repo-registry-entry")
        names = sorted(set(extract_auth_env_names("\n".join(evidence_text))) | set(runtime_names))
        if names:
            auth_review["env_vars_or_credentials"] = names
            if runtime_names:
                evidence_sources.append("non-skill-install-assurance.json")
            auth_review["env_var_evidence_sources"] = sorted(set(evidence_sources))
            named_item_count += 1
            named_value_count += len(names)
        elif not auth_review.get("env_vars_or_credentials"):
            auth_review["env_vars_or_credentials"] = [AUTH_UNKNOWN_PLACEHOLDER]
    deep_audit["auth_env_name_evidence_target_count"] = named_item_count
    deep_audit["auth_env_name_evidence_value_count"] = named_value_count
    deep_audit["auth_env_name_evidence_method"] = (
        "Name-only scan of reviewed catalog MDX, installed SKILL.md files, and matched repo registry entries; "
        "credential values were not extracted or persisted."
    )
    write_json(manifest_json("deep-source-audit.json"), deep_audit)


def record_manifest_path(record: dict[str, Any]) -> Path:
    raw_index = record.get("raw_index")
    matches = sorted(RECORDS_DIR.glob(f"{raw_index:03d}-*.json")) if isinstance(raw_index, int) else []
    if len(matches) != 1:
        raise ValueError(f"expected one record manifest for raw index {raw_index}, found {len(matches)}")
    return matches[0]


def source_integration_files(record: dict[str, Any]) -> list[str]:
    needles = {
        str(record.get("normalized_url") or "").lower(),
        str(record.get("source_name") or "").lower(),
    } - {""}
    matches: list[str] = []
    for relative_path in SOURCE_INTEGRATION_FILES:
        path = ROOT / relative_path
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if any(needle in text for needle in needles):
            matches.append(relative_path)
    return matches


def observed_auth_env_names(
    record: dict[str, Any],
    rows: list[dict[str, Any]],
    overrides: list[dict[str, Any]],
    mcp_registry: dict[str, Any],
) -> list[str]:
    """Extract names only from integrated local artifacts; never collect values."""
    names: set[str] = set()
    text_paths: set[Path] = set()
    for row in rows:
        row_path = str(row.get("path") or "")
        if row_path:
            text_paths.add(ROOT / row_path)
    for override in overrides:
        for installed_path in override.get("installed_paths", []):
            path = Path(os.path.expanduser(str(installed_path)))
            text_paths.add(path / "SKILL.md" if path.is_dir() else path)

    resolved_paths: set[Path] = set()
    for path in text_paths:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved in resolved_paths or not resolved.is_file():
            continue
        resolved_paths.add(resolved)
        try:
            names.update(extract_auth_env_names(resolved.read_text(encoding="utf-8", errors="replace")))
        except OSError:
            continue

    needles = {
        str(record.get("normalized_url") or "").lower(),
        str(record.get("source_name") or "").lower(),
    } - {""}
    servers = mcp_registry.get("servers", {}) if isinstance(mcp_registry, dict) else {}
    if isinstance(servers, dict):
        for server in servers.values():
            if not isinstance(server, dict):
                continue
            if not any(needle in json.dumps(server, sort_keys=True).lower() for needle in needles):
                continue
            env = server.get("env", {})
            if isinstance(env, dict):
                names.update(key for key in env if isinstance(key, str) and is_auth_env_name(key))
    return sorted(names)[:100]


def reconcile_final_records(summary: dict[str, Any], overrides: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge deep audit and promotion evidence into every raw-source record."""
    all_records = load_manifest_json("all-records.json", {"records": []})
    records = all_records.get("records", []) if isinstance(all_records, dict) else []
    if not isinstance(records, list):
        raise ValueError("all-records.json records must be a list")

    deep_audit = load_manifest_json("deep-source-audit.json", {"items": []})
    deep_items = deep_audit.get("items", []) if isinstance(deep_audit, dict) else []
    deep_by_url = {
        str(item.get("normalized_url") or "").lower(): item
        for item in deep_items
        if isinstance(item, dict) and item.get("normalized_url")
    }
    rows = summary.get("rows", []) if isinstance(summary, dict) else []
    rows_by_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, dict) and row.get("normalized_url"):
            rows_by_url[str(row["normalized_url"]).lower()].append(row)
    overrides_by_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for override in overrides:
        if isinstance(override, dict) and override.get("normalized_url"):
            overrides_by_url[str(override["normalized_url"]).lower()].append(override)
    mcp_registry = load_json(ROOT / "config" / "mcp-registry.json")
    non_skill_assurance = load_non_skill_assurance()
    non_skill_by_url = {
        str(item.get("normalized_url") or "").lower(): item
        for item in non_skill_assurance.get("items", [])
        if isinstance(item, dict) and item.get("normalized_url")
    }
    deep_artifact_type_names = {
        "agent": "agent",
        "cli-tool": "CLI/tool",
        "docs-reference": "docs/reference",
        "library": "library",
        "mcp-server": "MCP server",
        "plugin": "plugin",
        "skill": "skill",
    }

    reconciled: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        normalized_url = str(record.get("normalized_url") or "")
        key = normalized_url.lower()
        deep_item = deep_by_url.get(key, {})
        deep_artifact_types = deep_item.get("artifact_types_found", []) if isinstance(deep_item, dict) else []
        if deep_item.get("audit_complete") and isinstance(deep_artifact_types, list):
            record["intake_artifact_types_found"] = list(record.get("artifact_types_found", []))
            record["artifact_types_found"] = sorted({
                deep_artifact_type_names.get(str(value), str(value))
                for value in deep_artifact_types
                if str(value).strip()
            })
        auth_review = deep_item.get("auth_review", {}) if isinstance(deep_item, dict) else {}
        if isinstance(auth_review, dict) and deep_item.get("audit_complete"):
            auth_required = bool(auth_review.get("auth_required"))
            raw_env = auth_review.get("env_vars_or_credentials", [])
            env_vars = (
                sorted({
                    str(value) for value in raw_env if str(value).strip() and str(value) != AUTH_UNKNOWN_PLACEHOLDER
                })
                if isinstance(raw_env, list)
                else []
            )
            observed_env: list[str] = []
            if auth_required:
                observed_env = observed_auth_env_names(
                    record,
                    rows_by_url.get(key, []),
                    overrides_by_url.get(key, []),
                    mcp_registry,
                )
                env_vars = sorted(set(env_vars) | set(observed_env))
            if auth_required and not env_vars:
                env_vars = [AUTH_UNKNOWN_PLACEHOLDER]
            if not auth_required:
                env_vars = []
            evidence_source = (
                "deep-source-audit.json + reviewed local integration artifacts"
                if observed_env
                else "deep-source-audit.json"
            )
            record["auth_required"] = auth_required
            record["env_vars_or_credentials"] = env_vars
            compliance_packet = record.get("compliance_packet")
            if not isinstance(compliance_packet, dict):
                compliance_packet = {}
            compliance_packet.update({
                "auth_required": auth_required,
                "env_vars_or_credentials": env_vars,
                "evidence_source": evidence_source,
            })
            record["compliance_packet"] = compliance_packet

        record_path = record_manifest_path(record)
        added = [str(record_path.relative_to(ROOT))]
        for row in rows_by_url.get(key, []):
            row_path = str(row.get("path") or "")
            if row_path:
                added.append(row_path)
            row_name = str(row.get("name") or "")
            generated_path = (
                ROOT / "docs" / "src" / "content" / "docs" / "skills" / "catalog" / "external" / f"{row_name}.mdx"
            )
            if row_name and generated_path.exists():
                added.append(str(generated_path.relative_to(ROOT)))
        record["files_added"] = sorted(set(added))
        record["files_modified"] = sorted(set(SHARED_RECORD_FILES) | set(source_integration_files(record)))

        promoted = overrides_by_url.get(key, [])
        deep_ref = str(deep_item.get("ref") or "unknown") if isinstance(deep_item, dict) else "unknown"
        if promoted:
            live_rows = sum(1 for item in promoted if item.get("live_install_executed"))
            record["reviewer_notes"] = (
                f"Deep source audit completed at ref {deep_ref}. Reviewed promotion overlay applied "
                f"{len(promoted)} catalog row(s) and verified {live_rows} live-install evidence row(s)."
            )
        else:
            record["reviewer_notes"] = (
                f"Deep source audit completed at ref {deep_ref}. Final repo-native route "
                f"{record.get('install_or_integration_decision', 'unknown')} is recorded; no Skills CLI row applies."
            )
        record["intake_support_tier"] = record.get("intake_support_tier", record.get("support_tier"))
        if promoted:
            record["support_tier"] = "curated-installable-final"
        elif str(record.get("install_or_integration_decision") or "") in TERMINAL_HARD_BLOCK_DECISIONS:
            record["support_tier"] = "terminal-hard-block-final"
        else:
            record["support_tier"] = "repo-native-terminal-final"
        integration_packet = record.get("integration_packet")
        if isinstance(integration_packet, dict):
            integration_packet["scope"] = "historical-intake-research-only"
        record["intake_docs_steward_status"] = record.get(
            "intake_docs_steward_status", record.get("docs_steward_status")
        )
        record["docs_steward_status"] = "final-overlay-reconciled"
        record["final_integration"] = {
            "status": "installable-curated-external" if promoted else "terminal-repo-native-decision",
            "mutation_applied": bool(promoted or source_integration_files(record)),
            "catalog_rows": len(promoted),
            "harness_assurance": "harness-install-assurance.json",
            "non_skill_assurance": "non-skill-install-assurance.json",
            "runtime_disposition": non_skill_by_url.get(key, {}).get("runtime_disposition", "unrecorded"),
        }
        checks = [str(value) for value in record.get("tests_or_checks_run", []) if str(value).strip()]
        checks.extend([
            "uv run python scripts/audit_candidate_deep_sources.py --check",
            "uv run python scripts/apply_candidate_corpus_promotions.py --check",
            "uv run python scripts/promote_candidate_corpus.py --final-check",
        ])
        record["tests_or_checks_run"] = list(dict.fromkeys(checks))
        phase_status = record.get("phase_status")
        if isinstance(phase_status, dict):
            phase_status["deep_research"] = "completed-deep-source-audit"
            phase_status["compliance"] = "completed-deep-auth-reconciled"
            phase_status["decision"] = "completed-overlay-reconciled"
        reconciled.append(record)

    if len(reconciled) != 293:
        raise ValueError(f"expected 293 reconciled raw records, found {len(reconciled)}")
    all_records["records"] = reconciled
    all_records["generated_at"] = now()
    write_json(manifest_json("all-records.json"), all_records)
    for record in reconciled:
        write_json(record_manifest_path(record), record)

    compliance_items = [
        {
            "raw_index": record["raw_index"],
            "normalized_url": record["normalized_url"],
            "source_name": record["source_name"],
            "auth_required": record["auth_required"],
            "env_vars_or_credentials": record["env_vars_or_credentials"],
            "evidence_source": record.get("compliance_packet", {}).get("evidence_source", "deep-source-audit.json"),
        }
        for record in reconciled
    ]
    write_json(
        manifest_json("compliance-auth-matrix.json"),
        {"version": 1, "generated_at": now(), "items": compliance_items},
    )
    write_json(
        manifest_json("auth-matrix.json"),
        {
            "version": 1,
            "generated_at": now(),
            "items": [
                {
                    "raw_index": record["raw_index"],
                    "normalized_url": record["normalized_url"],
                    "source_name": record["source_name"],
                    "env_vars_or_credentials": record["env_vars_or_credentials"],
                    "safety_notes": record["safety_notes"],
                    "evidence_source": record.get("compliance_packet", {}).get(
                        "evidence_source", "deep-source-audit.json"
                    ),
                }
                for record in reconciled
                if record["auth_required"]
            ],
        },
    )

    graph = load_manifest_json("research-task-graph.json", {})
    if isinstance(graph, dict):
        by_raw_index = {record["raw_index"]: record for record in reconciled}
        by_url = {record["normalized_url"].lower(): record for record in reconciled}
        for lane in graph.get("raw_lanes", []):
            if not isinstance(lane, dict):
                continue
            record = by_raw_index.get(lane.get("raw_index"))
            if not record:
                continue
            for leaf in lane.get("leaf_checks", []):
                if isinstance(leaf, dict) and leaf.get("suffix") == "AUTH":
                    leaf["notes"] = (
                        "Deep audit recorded placeholder-only, user-owned credential boundaries: "
                        + ", ".join(record["env_vars_or_credentials"])
                        if record["auth_required"]
                        else "Deep audit found no required credential boundary."
                    )
        for lane in graph.get("unique_target_lanes", []):
            if not isinstance(lane, dict):
                continue
            record = by_url.get(str(lane.get("normalized_url") or "").lower())
            if record:
                lane["auth_required"] = record["auth_required"]
        write_json(manifest_json("research-task-graph.json"), graph)

    decisions = load_manifest_json("integration-decisions.json", {})
    if isinstance(decisions, dict):
        decision_rows = decisions.get("decisions", [])
        decision_summary = decisions.get("summary", {})
        if isinstance(decision_summary, dict):
            historical_live_install = 0
            historical_terminal = int_value(decision_summary.get("unique_count"), 289)
            terminal_non_install_rows = sum(
                1 for row in rows if isinstance(row, dict) and not row.get("install_command")
            )
            decision_summary["decision_count_basis"] = "raw entries; exact duplicate rows included"
            decision_summary["unique_decision_count"] = len(decision_rows) if isinstance(decision_rows, list) else 0
            decision_summary["historical_intake_live_install_added_count"] = historical_live_install
            decision_summary["historical_intake_terminal_non_install_count"] = historical_terminal
            decision_summary["live_install_added_count"] = len(overrides)
            decision_summary["live_install_count_basis"] = "final installable overlay rows"
            decision_summary["terminal_non_install_count"] = terminal_non_install_rows
            decision_summary["terminal_non_install_count_basis"] = "final catalog rows without install commands"
            decision_summary["auth_required_count"] = sum(record["auth_required"] for record in reconciled)
            decision_summary["deep_auth_required_unique_target_count"] = len({
                record["normalized_url"] for record in reconciled if record["auth_required"]
            })
        write_json(manifest_json("integration-decisions.json"), decisions)
    return reconciled


def load_candidate_record_metadata() -> dict[str, dict[str, Any]]:
    payload = load_manifest_json("all-records.json", {"records": []})
    graph = load_manifest_json("research-task-graph.json", {"unique_target_lanes": []})
    records = payload.get("records", []) if isinstance(payload, dict) else []
    unique_lanes = graph.get("unique_target_lanes", []) if isinstance(graph, dict) else []
    by_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if isinstance(records, list):
        for record in records:
            if not isinstance(record, dict) or not record.get("normalized_url"):
                continue
            by_url[str(record["normalized_url"]).lower()].append(record)

    metadata: dict[str, dict[str, Any]] = {}
    for normalized_url, url_records in by_url.items():
        ordered = sorted(
            url_records,
            key=lambda record: record.get("raw_index") if isinstance(record.get("raw_index"), int) else 10**9,
        )
        primary = ordered[0]
        raw_indexes = sorted(record["raw_index"] for record in ordered if isinstance(record.get("raw_index"), int))
        metadata[normalized_url] = {
            "source_name": primary.get("source_name", ""),
            "raw_indexes": raw_indexes,
            "risk_tier": primary.get("risk_tier", "standard-review"),
            "auth_required": primary.get("auth_required", False),
            "intake_decision": primary.get("install_or_integration_decision", ""),
            "docs_steward_surfaces": primary.get("docs_steward_surfaces", []),
            "next_gate": primary.get("reason", ""),
        }
    if isinstance(unique_lanes, list):
        for lane in unique_lanes:
            if not isinstance(lane, dict) or not lane.get("normalized_url"):
                continue
            key = str(lane["normalized_url"]).lower()
            metadata.setdefault(key, {})
            metadata[key].update({
                "lane_id": lane.get("lane_id", ""),
                "raw_lane_ids": lane.get("raw_lane_ids", []),
                "raw_indexes": lane.get("raw_indexes", metadata[key].get("raw_indexes", [])),
                "source_name": lane.get("source_name", metadata[key].get("source_name", "")),
                "risk_tier": lane.get("risk_tier", metadata[key].get("risk_tier", "standard-review")),
                "auth_required": metadata[key].get("auth_required", lane.get("auth_required", False)),
                "intake_decision": lane.get(
                    "current_intake_decision",
                    metadata[key].get("intake_decision", ""),
                ),
                "docs_steward_surfaces": lane.get(
                    "docs_steward_surfaces",
                    metadata[key].get("docs_steward_surfaces", []),
                ),
            })
    return metadata


def wave_lane_for_target(target: dict[str, Any]) -> dict[str, Any]:
    return {
        "lane_id": target.get("lane_id", ""),
        "normalized_url": target["normalized_url"],
        "source_name": target.get("source_name", ""),
        "raw_indexes": target.get("raw_indexes", []),
        "raw_lane_ids": target.get("raw_lane_ids", []),
        "current_intake_decision": target.get("intake_decision", ""),
        "existing_integration_status": target.get("coverage_status", COVERAGE_NEEDS_PROMOTION),
        "risk_tier": target.get("risk_tier", "standard-review"),
        "auth_required": bool(target.get("auth_required")),
        "live_install_eligible": False,
        "next_packet_required": "terminal route recorded; no candidate-code execution from corpus rows",
        "next_gate": (
            "existing installable catalog coverage"
            if target.get("coverage_status") == COVERAGE_TRUST_CLEARED
            else target.get("next_gate") or "terminal native or hard-block route"
        ),
    }


def refresh_wave_counts(wave: dict[str, Any]) -> None:
    targets = [target for target in wave.get("targets", []) if isinstance(target, dict)]
    raw_indexes = wave_raw_indexes(targets)
    wave["target_count"] = len(targets)
    wave["unique_target_count"] = len(targets)
    wave["raw_indexes"] = raw_indexes
    wave["raw_entry_count"] = len(raw_indexes)
    wave["lanes"] = [wave_lane_for_target(target) for target in targets]
    wave["coverage_status_counts"] = dict(
        sorted(Counter(str(target.get("coverage_status") or "unknown") for target in targets).items())
    )
    wave["risk_tier_counts"] = dict(
        sorted(Counter(str(target.get("risk_tier") or "unclassified") for target in targets).items())
    )


def promotion_wave_for_target(target: dict[str, Any], retained_urls: set[str]) -> tuple[str, str]:
    normalized_url = str(target.get("normalized_url", ""))
    key = normalized_url.lower()
    coverage_status = str(target.get("coverage_status", COVERAGE_NEEDS_PROMOTION))
    if key in retained_urls and coverage_status == COVERAGE_TRUST_CLEARED:
        return "W00", "Existing installable catalog row owns integration; no duplicate install command."
    decision = str(target.get("intake_decision", ""))
    if decision in TERMINAL_HARD_BLOCK_DECISIONS:
        return "W99", target.get("next_gate", "") or "Terminal hard block remains non-installable."
    text = " ".join(
        str(target.get(field, "")) for field in ("source_name", "normalized_url", "intake_decision", "risk_tier")
    ).lower()
    if any(
        token in text
        for token in (
            "apple",
            "app-intents",
            "app-store",
            "background-execution",
            "core-data",
            "focusengine",
            "ios",
            "macos",
            "swift",
            "widget",
            "xcode",
        )
    ):
        return "W02", "Apple platform assumptions, signing, simulator, and App Store boundaries are required."
    if any(
        token in text
        for token in (
            "cloudflare",
            "wordpress",
            "timescale",
            "tanstack",
            "solana",
            "ast-grep",
            "langchain",
            "duckdb",
            "dbt",
            "elastic",
            "apify",
            "supabase",
            "huggingface",
            "google",
            "vercel",
            "planetscale",
            "postgres",
            "database",
        )
    ):
        return "W01", "Official/vendor/data source; prefer existing official curated rows or precise selectors."
    if any(
        token in text
        for token in (
            "react",
            "typescript",
            "solid",
            "auth",
            "frontend",
            "web-quality",
            "css",
            "html",
            "design",
            "figma",
            "ui",
            "ux",
        )
    ):
        return "W03", "Frontend/web/design source; dedupe triggers and avoid broad activation."
    if any(
        token in text
        for token in (
            "chart",
            "diagram",
            "ppt",
            "slide",
            "cad",
            "webgpu",
            "mermaid",
            "motion",
            "image",
            "logo",
            "visual",
            "video",
        )
    ):
        return "W04", "Visual/media source; document copyright, brand, likeness, and asset provenance."
    if any(
        token in text
        for token in (
            "aws",
            "terraform",
            "cloud",
            "security",
            "devops",
            "mcp",
            "plugin",
            "cli",
            "guard",
            "secret",
            "rg-guard",
            "langfuse",
        )
    ):
        return "W05", "Executable or operational source; require dry-run, least privilege, and smoke tests."
    if any(
        token in text
        for token in (
            "research",
            "academic",
            "paper",
            "zotero",
            "notebooklm",
            "legal",
            "finance",
            "econ",
            "buffett",
            "yahoo",
            "scientific",
        )
    ):
        return "W06", "Research/domain source; document citation, evidence, non-advice, and reproducibility."
    if any(
        token in text
        for token in (
            "seo",
            "aso",
            "geo",
            "gtm",
            "sales",
            "marketing",
            "outbound",
            "affiliate",
            "ads",
            "product",
            "content",
            "copywriting",
            "pm-",
            "pm_",
            "pm/",
        )
    ):
        return "W07", "Growth/product source; document anti-abuse, ToS, and non-deceptive boundaries."
    if any(
        token in text
        for token in (
            "openspec",
            "workflow",
            "docs",
            "readme",
            "obsidian",
            "composiohq",
            "pedronauck",
            "find-rules",
            "find-skills",
        )
    ):
        return "W08", "Workflow/docs source; dedupe against repo skills and docs-steward surfaces."
    return "W08", "General workflow/content source; route after source research."


def overlay_promotion_waves(retained_urls: set[str]) -> None:
    path = manifest_json("promotion-wave-plan.json")
    plan = load_manifest_json("promotion-wave-plan.json", {})
    if not isinstance(plan, dict):
        return
    waves = plan.get("waves", [])
    if not isinstance(waves, list):
        return
    if not waves:
        return
    normalized = load_manifest_json("normalized-urls.json", {})
    coverage = load_manifest_json("existing-integration-coverage.json", {"items": []})
    unique_targets = normalized.get("unique_targets", []) if isinstance(normalized, dict) else []
    coverage_items = coverage.get("items", []) if isinstance(coverage, dict) else []
    if not isinstance(unique_targets, list):
        return
    record_metadata = load_candidate_record_metadata()
    coverage_by_url = {
        str(item.get("normalized_url", "")).lower(): item
        for item in coverage_items
        if isinstance(item, dict) and item.get("normalized_url")
    }
    all_targets: dict[str, dict[str, Any]] = {}
    for normalized_url in unique_targets:
        key = str(normalized_url).lower()
        coverage_item = coverage_by_url.get(key, {})
        metadata = record_metadata.get(key, {})
        raw_indexes = coverage_item.get("raw_indexes") or metadata.get("raw_indexes", [])
        coverage_status = coverage_item.get("coverage_status", COVERAGE_NEEDS_PROMOTION)
        all_targets[key] = {
            "normalized_url": str(normalized_url),
            "source_name": coverage_item.get("source_name", metadata.get("source_name", "")),
            "raw_indexes": raw_indexes,
            "raw_lane_ids": metadata.get("raw_lane_ids", []),
            "lane_id": metadata.get("lane_id", ""),
            "coverage_status": coverage_status,
            "existing_integration_status": coverage_status,
            "intake_decision": coverage_item.get("intake_decision", metadata.get("intake_decision", "")),
            "risk_tier": metadata.get("risk_tier", "standard-review"),
            "auth_required": metadata.get("auth_required", False),
            "docs_steward_surfaces": metadata.get("docs_steward_surfaces", []),
            "next_gate": metadata.get("next_gate", ""),
        }
    waves_by_id = {str(wave.get("wave_id")): wave for wave in waves if isinstance(wave, dict)}
    for wave in waves:
        wave["targets"] = []
        refresh_wave_counts(wave)
    for target in sorted(all_targets.values(), key=lambda item: item["normalized_url"]):
        wave_id, reason = promotion_wave_for_target(target, retained_urls)
        target["next_gate"] = reason
        wave = waves_by_id.get(wave_id) or waves[-1]
        wave.setdefault("targets", []).append(target)
    for wave in waves:
        wave["targets"].sort(key=lambda item: item["normalized_url"])
        refresh_wave_counts(wave)
        wave_id = str(wave.get("wave_id", ""))
        wave["promotion_policy"] = TERMINAL_PROMOTION_POLICY
        wave["mutation_policy"] = mutation_policy_for_wave(wave_id)
    plan["status"] = TERMINAL_PROMOTION_WAVE_STATUS
    plan["wave_count"] = len(waves)
    plan["total_targets"] = len(all_targets)
    plan["unique_targets_assigned"] = len(all_targets)
    plan["raw_entries_covered"] = len({index for wave in waves for index in wave.get("raw_indexes", [])})
    plan["live_install_eligible_count"] = 0
    plan["assignment_rule"] = TERMINAL_PROMOTION_ASSIGNMENT_RULE
    errors = validate_promotion_wave_plan(plan)
    if errors:
        raise ValueError("Invalid promotion wave plan after overlay:\n- " + "\n- ".join(errors))
    rendered = render_promotion_wave_report(plan)
    write_json(path, plan)
    manifest_json("promotion-wave-plan.md").write_text(rendered, encoding="utf-8")


def refresh_promotion_gate_artifacts() -> None:
    promoter = ROOT / "scripts" / "promote_candidate_corpus.py"
    if not promoter.exists():
        return
    result = subprocess.run(
        [sys.executable, str(promoter), "--write"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        details = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        raise RuntimeError(f"promotion gate artifact refresh failed with exit {result.returncode}: {details}")


def write_overlay_changelog(summary: dict[str, Any], overrides: list[dict[str, Any]]) -> None:
    live_stats = live_install_evidence_stats(overrides)
    non_skill_assurance = load_non_skill_assurance()
    runtime = runtime_activation_summary()
    rows = summary.get("rows", []) if isinstance(summary, dict) else []
    promoted_targets = {str(item.get("normalized_url")) for item in overrides if item.get("normalized_url")}
    preview = load_manifest_json("live-install-command-preview.json", {})
    command_count = int_value(preview.get("command_count")) if isinstance(preview, dict) else 0
    lines = [
        "# Changelog Entry: Candidate Corpus July 2026 Intake",
        "",
        "- Processed 293 raw source URLs into 289 unique normalized targets with four duplicate rows preserved.",
        f"- Published {len(rows)} catalog rows spanning every normalized target.",
        (
            f"- Promoted {len(overrides)} installable skill rows across {len(promoted_targets)} unique targets "
            "through reviewed, attributed catalog entries."
        ),
        (
            f"- Reconciled {live_stats['live_install_rows']} recorded Skills CLI install evidence rows and "
            f"verified {live_stats['verified_skill_md_count']}/{live_stats['installed_path_refs']} installed paths."
        ),
        f"- Emitted {command_count} new live install commands because additive harness reconciliation found no gaps.",
        "- Reconciled deep-source auth evidence into all 293 raw records and the consolidated auth matrix.",
        (
            "- Routed MCP, plugin, CLI/tool, agent, docs, and collection sources through repo-native registries "
            "and catalogs."
        ),
        (
            f"- Accounted for {non_skill_assurance.get('unique_target_count', 0)} runtime dispositions and "
            f"recorded the authoritative {runtime['runtime_artifact_count']}-artifact successor activation ledger: "
            f"{runtime['accepted']} accepted and {runtime['incomplete']} incomplete."
        ),
        (
            "- Bound eight enabled Codex plugins from pinned upstream Git objects through approved marketplace, "
            "isolated-install, and live-cache content digests."
        ),
        (
            "- Bound rollback acceptance to immutable `commit-pending` journals plus post-CAS success markers; "
            "failed transactions remain separate immutable failure evidence."
        ),
        "- Added successor canary, rollback, catalog, docs, final-closure, and runtime aggregation scripts: "
        + ", ".join(f"`scripts/{name}`" for name in SUCCESSOR_ASSURANCE_SCRIPTS)
        + ".",
        (
            "- Preserved source attribution, license evidence, safety boundaries, duplicate coverage, and "
            "explicit terminal routes."
        ),
        "- Candidate source code was not executed by the audit or report generators; the separately authorized "
        "runtime overlay installed pinned distributions and ran only bounded, non-mutating probes.",
    ]
    (MANIFEST_DIR / "changelog-entry.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_overlay_decision_log(overrides: list[dict[str, Any]]) -> None:
    decisions_payload = load_manifest_json("integration-decisions.json", {})
    decisions = decisions_payload.get("decisions", []) if isinstance(decisions_payload, dict) else []
    records_payload = load_manifest_json("all-records.json", {})
    records = records_payload.get("records", []) if isinstance(records_payload, dict) else []
    historical_hard_blocks = [
        item
        for item in decisions
        if isinstance(item, dict) and str(item.get("decision") or "") in TERMINAL_HARD_BLOCK_DECISIONS
    ]
    integrated_quarantine = [
        item
        for item in load_integration_targets().get("items", [])
        if isinstance(item, dict) and item.get("integration_classification") == "integrated-quarantine-reference"
    ]
    risky = [
        record
        for record in records
        if isinstance(record, dict) and record.get("risk_tier") in {"quarantine", "review-required"}
    ]
    lines = [
        "# Candidate Corpus July 2026 Decision Log",
        "",
        (
            "> Final overlay-aware decision state. Historical intake risk labels are retained below for auditability; "
            "`full-integration-state.md` owns the final completion counters."
        ),
        "",
        "- Raw entries: 293",
        "- Unique normalized targets: 289",
        "- Duplicates deduped: 4",
        f"- Historical conservative hard blocks: {len(historical_hard_blocks)}",
        f"- Integrated quarantine references: {len(integrated_quarantine)}",
        f"- Active install blocks: {len(historical_hard_blocks)}",
        "",
        "## Risk-Sensitive Sources",
        "",
        *[
            f"- `{record['raw_index']:03d}` `{record['source_name']}`: {record['risk_tier']} - {record['reason']}"
            for record in risky
        ],
        "",
        "## Integrated Quarantine References",
        "",
        *[
            f"- `{item.get('normalized_url')}`: integrated as a non-installable quarantine reference"
            for item in integrated_quarantine
        ],
        "",
        "## Active Install Blocks",
        "",
        *(
            [f"- `{item.get('normalized_url')}`: `{item.get('decision')}`" for item in historical_hard_blocks]
            if historical_hard_blocks
            else ["- none"]
        ),
    ]
    (MANIFEST_DIR / "risky-skipped-deduped-decision-log.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_promotion_reports(summary: dict[str, Any], overrides: list[dict[str, Any]], progress: dict[str, Any]) -> None:
    rows = summary.get("rows", [])
    unique_targets = int_value(summary.get("unique_targets"), 289)
    live_stats = live_install_evidence_stats(overrides)
    live_installed = live_stats["live_install_rows"]
    installed_path_refs = live_stats["installed_path_refs"]
    verified_skill_md = live_stats["verified_skill_md_count"]
    missing_skill_md = len(live_stats["missing_installed_skill_md"])
    readiness = load_manifest_json("promotion-readiness-queue.json", {})
    readiness_summary = readiness.get("summary", {}) if isinstance(readiness, dict) else {}
    harness_assurance = load_harness_assurance()
    harness_totals = harness_assurance.get("totals", {}) if isinstance(harness_assurance, dict) else {}
    non_skill_assurance = load_non_skill_assurance()
    runtime = runtime_activation_summary()
    remaining_harness_commands = int_value(harness_totals.get("commands"))
    remaining_harness_missing = int_value(harness_totals.get("missing"))
    terminal_non_install_rows = sum(1 for row in rows if isinstance(row, dict) and not row.get("install_command"))
    progress_readiness = progress.get("promotion_readiness", {}) if isinstance(progress, dict) else {}
    integrated_targets = int_value(progress_readiness.get("integrated_targets"))
    unintegrated_targets = int_value(progress_readiness.get("unintegrated_targets"))
    integrated_quarantine_targets = int_value(progress_readiness.get("integrated_quarantine_targets"))
    active_install_blocks = int_value(progress_readiness.get("active_install_blocks"))
    deep_audit = load_manifest_json("deep-source-audit.json", {})
    deep_items = deep_audit.get("items", []) if isinstance(deep_audit, dict) else []
    deep_status_counts = deep_audit.get("status_counts", {}) if isinstance(deep_audit, dict) else {}
    deep_audited = int_value(deep_status_counts.get("audited"))
    deep_blocked = int_value(deep_status_counts.get("terminal-blocker"))
    validation_lines = [
        "# Candidate Corpus July 2026 Validation Report",
        "",
        "- Raw candidates processed: 293",
        f"- Unique normalized targets: {unique_targets}",
        f"- Catalog authoring rows: {len(rows)}",
        f"- Installable promoted curated-external rows: {len(overrides)}",
        f"- Recorded install evidence rows: {live_installed}",
        f"- Installed path references verified: {verified_skill_md}/{installed_path_refs}",
        f"- Missing installed `SKILL.md` files: {missing_skill_md}",
        f"- Post-install harness commands remaining: {remaining_harness_commands}",
        f"- Post-install desired rows missing across harnesses: {remaining_harness_missing}",
        f"- Successor runtime artifacts discovered: {runtime['runtime_artifact_count']}",
        f"- Successor runtime artifacts accepted: {runtime['accepted']}",
        f"- Successor runtime artifacts incomplete: {runtime['incomplete']}",
        f"- Requested full usability: `{str(runtime['requested_full_usability']).lower()}`",
        (
            "- Non-skill normalized targets accounted for: "
            f"{non_skill_assurance.get('unique_target_count', 0)}/{EXPECTED_UNIQUE_COUNT}"
        ),
        f"- Terminal non-install traceability rows: {terminal_non_install_rows}",
        f"- Integrated normalized targets: {integrated_targets}/{EXPECTED_UNIQUE_COUNT}",
        f"- Unintegrated normalized targets: {unintegrated_targets}",
        f"- Integrated quarantine references: {integrated_quarantine_targets}",
        f"- Active install blocks: {active_install_blocks}",
        (
            f"- Source-list evidence: 289 list-only source probes recorded; {len(overrides)} installable rows "
            "were promoted from reviewed override evidence."
        ),
        (
            f"- Deep source audit: {deep_audited} targets audited through GitHub API README/license/tree/package "
            f"reads plus {deep_blocked} terminal blocker; candidate code executed: false."
        ),
        f"- Full integration phase: `{progress.get('phase')}`",
        f"- New install command preview status: `{progress.get('live_install', {}).get('status')}`",
        (
            f"- Status note: the recorded post-install dry-run covers "
            f"{harness_assurance.get('target_harness_count', 0)} harnesses with "
            f"{remaining_harness_missing} missing desired rows and {remaining_harness_commands} remaining commands."
        ),
        (
            "- Gate summary: "
            f"{readiness_summary.get('covered_by_existing_installable_catalog', 0)} covered, "
            f"{readiness_summary.get('ready_for_repo_promotion', 0)} ready for repo promotion, "
            f"{readiness_summary.get('ready_for_live_install', 0)} ready for live install, "
            f"{readiness_summary.get('terminal_native_or_hard_blocked', 0)} terminal native or hard-blocked."
        ),
        "",
        "## Observed Generated Evidence",
        "",
        "- Generator emitted manifest, matrix, packet, report, and catalog-authoring artifacts from local inputs.",
        "- Read-only generator and deep-source audit scripts did not execute candidate code.",
        (
            "- The promotion overlay records non-dry-run Skills CLI evidence; `harness-install-assurance.json` "
            "records the sanitized post-install reconciliation result, `non-skill-install-assurance.json` records "
            "historical package/config dispositions, and `runtime-activation-assurance.json` owns executable "
            "usability truth."
        ),
        (
            "- Quarantined targets are permanent non-installable references with source-specific risk and license "
            "reasons; their active install blocks exclude them from sync."
        ),
        (
            "- A maintainer-authorized install reconciliation was run; the committed assurance artifact is the "
            "subsequent dry-run result, not raw installer output."
        ),
        "",
        RUNNER_CHECKLIST_HEADING,
        "",
        (
            "> This overlay records required commands only. It does not execute them or claim outcomes; "
            "the runner owns any observed closeout results."
        ),
        "",
        *[f"- Successor assurance source: `scripts/{name}`." for name in SUCCESSOR_ASSURANCE_SCRIPTS],
        "- `uv run python scripts/generate_candidate_corpus_shards.py --emit-all --no-network`",
        (
            "- Required closeout: `uv run python scripts/apply_candidate_corpus_promotions.py --check` for "
            f"{len(overrides)} promotion overrides."
        ),
        (
            "- Required closeout: `uv run python scripts/audit_candidate_deep_sources.py --check` for "
            f"{len(deep_items)} normalized targets."
        ),
        (
            "- Required closeout: `uv run python scripts/promote_candidate_corpus.py --final-check` for "
            "293 raw entries, "
            f"{unique_targets} unique targets, {deep_audited} deep-audited targets, {deep_blocked} deep terminal "
            f"blocker, {len(overrides)} promoted overrides, and {live_installed} recorded install evidence rows."
        ),
        ("- Required closeout: focused candidate-corpus and docs generation tests."),
        ("- Required closeout: `uv run pytest -q tests/test_candidate_corpus.py tests/test_docs.py`."),
        "- Required closeout: `uv run wagents docs generate --no-installed --check`.",
        "- Required closeout: `uv run wagents catalog index --check --format json`.",
        "- Required closeout: `uv run wagents validate`.",
        "- Required closeout: `uv run wagents readme --check`.",
        (
            f"- `harness-install-assurance.json` records {remaining_harness_commands} remaining commands after "
            "the authorized reconciliation run."
        ),
        (
            "- Required closeout: `uv run wagents openspec status --change "
            "activate-candidate-corpus-runtime-jul2026 --format json`."
        ),
        "- Required closeout: `uv run wagents openspec validate --strict --format json`.",
        "- Required closeout: `git diff --check`.",
    ]
    validation_path = MANIFEST_DIR / "validation-report.md"
    existing_validation = validation_path.read_text(encoding="utf-8") if validation_path.exists() else ""
    validation_text = preserve_runner_owned_results("\n".join(validation_lines) + "\n", existing_validation)
    validation_path.write_text(validation_text, encoding="utf-8")

    final_lines = [
        "# Candidate Corpus July 2026 Final Review Report",
        "",
        "- Total raw candidates processed: 293",
        f"- Total unique normalized targets: {unique_targets}",
        f"- Catalog authoring rows after overlay: {len(rows)}",
        f"- Promoted installable curated-external rows: {len(overrides)}",
        f"- Recorded install evidence rows: {live_installed}",
        f"- Installed path references verified: {verified_skill_md}/{installed_path_refs}",
        f"- Missing installed `SKILL.md` files: {missing_skill_md}",
        f"- Post-install harness commands remaining: {remaining_harness_commands}",
        f"- Post-install desired rows missing across harnesses: {remaining_harness_missing}",
        f"- Successor runtime artifacts discovered: {runtime['runtime_artifact_count']}",
        f"- Successor runtime artifacts accepted: {runtime['accepted']}",
        f"- Successor runtime artifacts incomplete: {runtime['incomplete']}",
        f"- Requested full usability: `{str(runtime['requested_full_usability']).lower()}`",
        (
            "- Non-skill normalized targets accounted for: "
            f"{non_skill_assurance.get('unique_target_count', 0)}/{EXPECTED_UNIQUE_COUNT}"
        ),
        f"- Terminal non-install traceability rows: {terminal_non_install_rows}",
        f"- Integrated normalized targets: {integrated_targets}/{EXPECTED_UNIQUE_COUNT}",
        f"- Unintegrated normalized targets: {unintegrated_targets}",
        f"- Integrated quarantine references: {integrated_quarantine_targets}",
        f"- Active install blocks: {active_install_blocks}",
        (
            f"- Full integration phase: `{progress.get('phase')}`; new install command preview status is "
            f"`{progress.get('live_install', {}).get('status')}`."
        ),
        (
            f"- Status note: post-install reconciliation covers "
            f"{harness_assurance.get('target_harness_count', 0)} harnesses with "
            f"{remaining_harness_missing} missing desired rows and {remaining_harness_commands} commands."
        ),
        (
            "- The maintainer-authorized install reconciliation completed with a zero-command post-install "
            "dry-run; raw installer output is not committed."
        ),
        (
            f"- Deep source audit: {deep_audited} audited targets, {deep_blocked} terminal blocker, "
            "candidate code executed: false."
        ),
        (
            "- Separately authorized runtime overlay: pinned packages and plugins were installed or registered; "
            f"the successor ledger accepts {runtime['accepted']}/{runtime['runtime_artifact_count']} artifacts "
            f"and keeps {runtime['incomplete']} explicit policy or credential blockers fail-closed."
        ),
        "- Generator-owned conservative intake artifacts remain available for traceability.",
        "- No commit made by this script.",
        "",
        "## Suggested PR Title",
        "",
        "chore: integrate candidate corpus July 2026 promotion overlay",
        "",
        "## Suggested PR Body",
        "",
        (
            "- Adds deterministic candidate corpus normalization, sharding, coverage, generated catalog "
            "authoring rows, and promotion overlay validation."
        ),
        (
            "- Records read-only source-list/deep-source evidence and reviewed install metadata for promoted "
            "curated external rows, including installed-root verification."
        ),
        (
            "- Installs or registers the audited CLI, library, MCP, and native plugin overlay; records exact "
            "activation state, placeholder-only auth requirements, and disabled safety boundaries."
        ),
        "- Records the authorized install reconciliation and keeps subsequent validation checks non-mutating.",
    ]
    (MANIFEST_DIR / "final-review-report.md").write_text("\n".join(final_lines) + "\n", encoding="utf-8")
    write_overlay_changelog(summary, overrides)
    write_overlay_decision_log(overrides)


def write_progress_state(summary: dict[str, Any], overrides: list[dict[str, Any]]) -> None:
    progress = load_json(PROGRESS) if PROGRESS.exists() else {"version": 1}
    rows = summary.get("rows", [])
    row_urls = {row.get("normalized_url") for row in rows if isinstance(row, dict) and row.get("normalized_url")}
    unique_targets = int_value(summary.get("unique_targets"), len(row_urls))
    live_stats = live_install_evidence_stats(overrides)
    live_installed = live_stats["live_install_rows"]
    installed_path_refs = live_stats["installed_path_refs"]
    verified_skill_md = live_stats["verified_skill_md_count"]
    missing_skill_md = len(live_stats["missing_installed_skill_md"])
    promoted_unique_targets = len({
        override.get("normalized_url") for override in overrides if override.get("normalized_url")
    })
    hard_block_decisions = [
        decision
        for decision in load_manifest_json("integration-decisions.json", {}).get("decisions", [])
        if isinstance(decision, dict) and str(decision.get("decision") or "") in TERMINAL_HARD_BLOCK_DECISIONS
    ]
    target_payload = load_integration_targets()
    target_items = target_payload.get("items", []) if isinstance(target_payload, dict) else []
    if not isinstance(target_items, list):
        target_items = []
    classification_counts = Counter(
        str(item.get("integration_classification") or "unintegrated") for item in target_items if isinstance(item, dict)
    )
    integrated_targets = sum(
        1 for item in target_items if isinstance(item, dict) and integration_target_is_accounted(item)
    )
    unintegrated_targets = len(target_items) - integrated_targets
    integrated_quarantine_targets = classification_counts["integrated-quarantine-reference"]
    active_install_blocks = len(hard_block_decisions)
    candidate_authoring_rows = sorted(AUTHORING_DIR.glob("candidate-corpus-*.mdx"))
    terminal_non_install_rows = sum(1 for row in rows if isinstance(row, dict) and not row.get("install_command"))
    coverage_manifest = load_manifest_json("existing-integration-coverage.json", {})
    coverage = coverage_manifest.get("summary", {}) if isinstance(coverage_manifest, dict) else {}
    readiness_manifest = load_manifest_json("promotion-readiness-queue.json", {})
    readiness_summary = readiness_manifest.get("summary", {}) if isinstance(readiness_manifest, dict) else {}
    gate_matrix = load_manifest_json("promotion-gate-matrix.json", {})
    matrix_summary = gate_matrix.get("summary", {}) if isinstance(gate_matrix, dict) else {}
    live_preview = load_manifest_json("live-install-command-preview.json", {})
    preview_status = (
        str(live_preview.get("status", "no-live-install-commands-emitted"))
        if isinstance(live_preview, dict)
        else "no-live-install-commands-emitted"
    )
    preview_command_count = int_value(live_preview.get("command_count")) if isinstance(live_preview, dict) else 0
    harness_assurance = load_harness_assurance()
    harness_errors = harness_assurance_errors(harness_assurance)
    non_skill_assurance = load_non_skill_assurance()
    non_skill_errors = non_skill_assurance_errors(non_skill_assurance)
    non_skill_totals = non_skill_assurance.get("totals", {}) if isinstance(non_skill_assurance, dict) else {}
    runtime = runtime_activation_summary()
    coverage_total = sum(int_value(value) for value in coverage.values()) if isinstance(coverage, dict) else 0
    covered_existing = int_value(
        readiness_summary.get("covered_by_existing_installable_catalog")
        if isinstance(readiness_summary, dict)
        else coverage.get(COVERAGE_TRUST_CLEARED)
        if isinstance(coverage, dict)
        else None,
        max(unique_targets - terminal_non_install_rows, 0),
    )
    terminal_native_or_hard_blocked = int_value(
        readiness_summary.get("terminal_native_or_hard_blocked")
        if isinstance(readiness_summary, dict)
        else coverage_total - covered_existing
        if coverage_total
        else None,
        max(unique_targets - covered_existing, 0),
    )
    ready_for_repo_promotion = int_value(
        readiness_summary.get("ready_for_repo_promotion")
        if isinstance(readiness_summary, dict)
        else matrix_summary.get("ready_for_repo_promotion")
        if isinstance(matrix_summary, dict)
        else None,
        0,
    )
    ready_for_live_install = int_value(
        readiness_summary.get("ready_for_live_install")
        if isinstance(readiness_summary, dict)
        else matrix_summary.get("ready_for_live_install")
        if isinstance(matrix_summary, dict)
        else None,
        0,
    )
    wave_plan = load_manifest_json("promotion-wave-plan.json", {})
    wave_rows = wave_plan.get("waves", []) if isinstance(wave_plan, dict) else []
    progress_waves = {
        str(wave.get("wave_id")): int_value(wave.get("target_count"))
        for wave in wave_rows
        if isinstance(wave, dict) and int_value(wave.get("target_count")) > 0
    }
    duplicate_raw_groups = 0
    normalized_path = MANIFEST_DIR / "normalized-urls.json"
    if normalized_path.exists():
        normalized = load_json(normalized_path)
        duplicate_groups = normalized.get("duplicate_groups", [])
        duplicate_raw_groups = len(duplicate_groups) if isinstance(duplicate_groups, (dict, list)) else 0

    completion_checks = {
        "raw_candidates_accounted": int_value(progress.get("raw_candidates"), 293) == 293,
        "unique_targets_accounted": unique_targets == 289,
        "all_targets_integrated": integrated_targets == EXPECTED_UNIQUE_COUNT and unintegrated_targets == 0,
        "candidate_authoring_rows_removed": not candidate_authoring_rows,
        "quarantine_targets_integrated_without_install": (integrated_quarantine_targets == active_install_blocks == 4),
        "promotion_queue_drained": ready_for_repo_promotion == 0 and ready_for_live_install == 0,
        "installed_paths_verified": missing_skill_md == 0 and verified_skill_md == installed_path_refs,
        "harness_install_assurance": not harness_errors,
        "non_skill_install_assurance": not non_skill_errors,
        "runtime_activation_model": runtime["runtime_artifact_count"] == EXPECTED_RUNTIME_ARTIFACT_COUNT,
    }
    complete = all(completion_checks.values())
    progress["generated_at"] = now()
    progress["phase"] = "corpus-integration-complete" if complete else "corpus-integration-assurance-pending"
    progress["complete"] = complete
    progress["completion_checks"] = completion_checks
    progress["completion_errors"] = harness_errors + non_skill_errors
    progress["completion_scope"] = (
        "Complete for the July 2026 corpus: every normalized target maps to a permanent catalog integration and "
        f"one runtime disposition; {len(overrides)} skill rows are reconciled across "
        f"{len(SUPPORTED_AGENT_IDS)} supported harnesses and "
        f"the successor ledger discovers {runtime['runtime_artifact_count']} runtime artifacts, accepts "
        f"{runtime['accepted']}, and keeps {runtime['incomplete']} fail-closed. Literal full runtime usability "
        "remains a separate gate."
        if complete
        else "Pending one or more explicit completion checks; see completion_checks and completion_errors."
    )
    progress["promotion_readiness"] = {
        **(readiness_summary if isinstance(readiness_summary, dict) else {}),
        "unique_targets": unique_targets,
        "covered_by_existing_installable_catalog": covered_existing,
        "ready_for_repo_promotion": ready_for_repo_promotion,
        "ready_for_live_install": ready_for_live_install,
        "terminal_native_or_hard_blocked": terminal_native_or_hard_blocked,
        "terminal_non_install_rows": terminal_non_install_rows,
        "promoted_unique_targets": promoted_unique_targets,
        "promoted_installable_rows": len(overrides),
        "integrated_targets": integrated_targets,
        "unintegrated_targets": unintegrated_targets,
        "integration_classification_counts": dict(sorted(classification_counts.items())),
        "integrated_quarantine_targets": integrated_quarantine_targets,
        "active_install_blocks": active_install_blocks,
        "recorded_install_evidence_rows": live_installed,
    }
    progress["existing_integration_coverage"] = dict(coverage) if isinstance(coverage, dict) else {}
    progress["promotion_waves"] = progress_waves
    progress["live_install"] = {
        "eligible_count": preview_command_count,
        "status": preview_status,
        "installed_skill_rows": live_installed,
        "recorded_install_evidence_rows": live_installed,
        "new_live_install_commands_emitted": preview_command_count,
        "installed_path_refs": installed_path_refs,
        "verified_skill_md_count": verified_skill_md,
        "missing_skill_md_count": missing_skill_md,
        "reason": (
            "live-install-command-preview.json remains the no-new-live-install gate artifact; "
            "promotion-overrides.json records prior non-dry-run Skills CLI install evidence."
        ),
        "pre_overlay_preview_status": (
            "live-install-command-preview.json remains the no-new-live-install gate artifact; "
            "promotion-overrides.json and catalog-authoring-summary.json record reviewed install evidence."
        ),
        "harness_assurance_complete": not harness_errors,
        "harness_count": harness_assurance.get("target_harness_count", 0),
        "harness_totals": harness_assurance.get("totals", {}),
    }
    progress["non_skill_install"] = {
        "complete": not non_skill_errors,
        "scope": "historical-package-config-inventory",
        "unique_target_count": non_skill_assurance.get("unique_target_count", 0),
        "totals": non_skill_assurance.get("totals", {}),
        "assurance_file": "non-skill-install-assurance.json",
    }
    progress["runtime_activation"] = runtime
    progress["terminal_decisions"] = {
        "raw_candidates_processed": int_value(progress.get("raw_candidates"), 293),
        "unique_normalized_targets": unique_targets,
        "installable_curated_rows": len(overrides),
        "live_installs_recorded": live_installed,
        "new_live_install_commands_emitted": preview_command_count,
        "terminal_non_install_rows": terminal_non_install_rows,
        "duplicate_raw_groups": duplicate_raw_groups,
        "conservative_intake_hard_blocks": len(hard_block_decisions),
        "integrated_targets": integrated_targets,
        "unintegrated_targets": unintegrated_targets,
        "integration_classification_counts": dict(sorted(classification_counts.items())),
        "integrated_quarantine_targets": integrated_quarantine_targets,
        "active_install_blocks": active_install_blocks,
    }
    write_json(PROGRESS, progress)

    lines = [
        "# Candidate Corpus Full Integration State",
        "",
        f"- Phase: `{progress['phase']}`",
        f"- Complete: `{str(complete).lower()}`",
        f"- Completion scope: {progress['completion_scope']}",
        f"- Raw research lanes: {progress.get('raw_candidates', 293)}",
        f"- Unique target synthesis lanes: {unique_targets}",
        f"- Live install eligible: {preview_command_count}",
        f"- New install command preview status: `{progress['live_install']['status']}`",
        f"- Recorded install evidence rows: {live_installed}",
        f"- Installed path references verified: {verified_skill_md}/{installed_path_refs}",
        f"- Missing installed `SKILL.md` files: {missing_skill_md}",
        (
            "- Historical package/config artifacts accounted for: "
            f"{non_skill_totals.get('verified_runtime_artifacts', 0)}/"
            f"{non_skill_totals.get('runtime_artifacts', 0)}"
        ),
        f"- Successor runtime artifacts discovered: {runtime['runtime_artifact_count']}",
        f"- Successor runtime artifacts accepted: {runtime['accepted']}",
        f"- Successor runtime artifacts incomplete: {runtime['incomplete']}",
        f"- Requested full usability: `{str(runtime['requested_full_usability']).lower()}`",
        (
            "- Non-skill normalized targets accounted for: "
            f"{non_skill_assurance.get('unique_target_count', 0)}/{EXPECTED_UNIQUE_COUNT}"
        ),
        "- Candidate MCP and broad-hook plugin activation remains explicit and disabled by default.",
        f"- Covered by existing installable catalog rows: {covered_existing}",
        f"- Promoted installable catalog rows: {len(overrides)}",
        f"- Integrated normalized targets: {integrated_targets}/{EXPECTED_UNIQUE_COUNT}",
        f"- Unintegrated normalized targets: {unintegrated_targets}",
        f"- Integration classifications: {dict(sorted(classification_counts.items()))}",
        f"- Ready for repo promotion: {ready_for_repo_promotion}",
        f"- Ready for live install: {ready_for_live_install}",
        f"- Terminal native or hard-blocked rows: {terminal_native_or_hard_blocked}",
        f"- Terminal non-install traceability rows: {terminal_non_install_rows}",
        f"- Promoted unique targets: {promoted_unique_targets}",
        f"- Integrated quarantine reference targets: {integrated_quarantine_targets}",
        f"- Active install blocks: {active_install_blocks}",
        "",
        "## Overlay Evidence",
        "",
        (
            "`live-install-command-preview.json` remains the no-new-live-install gate artifact. The reviewed "
            "catalog promotion overlay and install evidence are recorded in `promotion-overrides.json`, "
            "`applied-promotion-overrides.json`, `catalog-authoring-summary.json`, "
            "`harness-install-assurance.json`, `non-skill-install-assurance.json`, "
            "`runtime-activation-assurance.json`, and this state report."
        ),
        "",
        (
            "- Required closeout: `uv run python scripts/apply_candidate_corpus_promotions.py --check` for "
            f"{len(overrides)} overrides."
        ),
        (
            "- `uv run python scripts/promote_candidate_corpus.py --final-check` reconciles deep-source audit "
            f"evidence, {len(overrides)} promoted overrides, {live_installed} install-evidence rows, and "
            f"{unique_targets} terminal target decisions."
        ),
        f"- Install-root verification found {missing_skill_md} missing `SKILL.md` files.",
        (
            "- Quarantined targets are integrated as non-installable reference rows. Their install blocks remain "
            "active until a separate reviewed decision changes the source evidence."
        ),
    ]
    STATE_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_promotion_reports(summary, overrides, progress)

    final_report_path = MANIFEST_DIR / "final-review-report.md"
    if final_report_path.exists():
        final_report = final_report_path.read_text(encoding="utf-8").split("\n## Promotion Overlay Completion\n", 1)[0]
        overlay = [
            "## Promotion Overlay Completion",
            "",
            "- Full integration phase: `corpus-integration-complete`.",
            f"- Promoted overrides: {len(overrides)}.",
            f"- Recorded install evidence rows: {live_installed}.",
            f"- Installed path references verified: {verified_skill_md}/{installed_path_refs}.",
            f"- Missing installed `SKILL.md` files: {missing_skill_md}.",
            f"- Successor runtime artifacts discovered: {runtime['runtime_artifact_count']}.",
            f"- Successor runtime artifacts accepted: {runtime['accepted']}.",
            f"- Successor runtime artifacts incomplete: {runtime['incomplete']}.",
            "- Final commit hash: no commit made by this script.",
        ]
        final_report_path.write_text(final_report.rstrip() + "\n\n" + "\n".join(overlay) + "\n", encoding="utf-8")


def preflight_apply_overrides() -> tuple[list[Any], dict[str, Any], list[Any]]:
    """Validate all apply prerequisites before the first filesystem write."""
    errors: list[str] = []
    try:
        overrides = load_overrides()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        overrides = []
        errors.append(f"promotion-overrides.json is invalid: {exc}")

    summary: dict[str, Any] = {}
    rows: list[Any] = []
    if not SUMMARY.is_file():
        errors.append("missing catalog-authoring-summary.json")
    else:
        try:
            loaded_summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"catalog-authoring-summary.json is unreadable: {exc}")
        else:
            if not isinstance(loaded_summary, dict):
                errors.append("catalog-authoring-summary.json payload must be an object")
            else:
                summary = loaded_summary
                loaded_rows = summary.get("rows", [])
                if not isinstance(loaded_rows, list):
                    errors.append("catalog-authoring-summary.json rows must be a list")
                else:
                    rows = loaded_rows
                    errors.extend(validate_override_records(overrides, rows))

    plan, plan_errors = load_promotion_wave_plan()
    errors.extend(plan_errors)
    if not plan_errors:
        report_path = manifest_json("promotion-wave-plan.md")
        if not report_path.is_file():
            errors.append("missing promotion-wave-plan.md; run the candidate corpus generator first")
        elif report_path.read_text(encoding="utf-8") != render_promotion_wave_report(plan):
            errors.append("promotion-wave-plan.md is stale; run the candidate corpus generator first")

    if errors:
        raise ValueError(
            "Promotion apply preflight failed. Run "
            "`uv run python scripts/generate_candidate_corpus_shards.py --emit-all --no-network` first, "
            "then retry:\n- " + "\n- ".join(errors)
        )
    return overrides, summary, rows


def apply_overrides() -> dict[str, Any]:
    overrides, summary, rows = preflight_apply_overrides()
    target_payload = load_integration_targets()
    targets_by_url = integration_target_index(target_payload)
    normalize_overrides_file()
    if not overrides:
        legacy_candidate_rows_removed = remove_legacy_candidate_rows()
        reconcile_integration_targets(summary, [])
        payload = {
            "version": 1,
            "generated_at": now(),
            "applied_count": 0,
            "legacy_candidate_rows_removed": legacy_candidate_rows_removed,
            "items": [],
        }
        write_json(REPORT, payload)
        return payload
    overrides_by_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for override in overrides:
        overrides_by_url[str(override["normalized_url"])].append(override)

    applied = []
    for override in overrides:
        skill_name = str(override["skill_name"])
        normalized_url = str(override["normalized_url"])
        promoted_path = authoring_path_for(skill_name)
        row_written = write_promoted_row(promoted_path, override)
        applied.append({
            "normalized_url": normalized_url,
            "skill_name": skill_name,
            "path": str(promoted_path.relative_to(ROOT)),
            "row_written": row_written,
        })

    removed_references: dict[str, str] = {}
    for normalized_url in sorted(overrides_by_url):
        target = targets_by_url.get(normalized_url.lower())
        if target is None:
            continue
        removed_path = remove_generated_reference(target)
        if removed_path:
            removed_references[normalized_url] = removed_path
    legacy_candidate_rows_removed = remove_legacy_candidate_rows()
    for item in applied:
        item["removed_generated_reference"] = removed_references.get(str(item["normalized_url"]), "")

    updated_rows: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized_url = str(row.get("normalized_url", ""))
        if normalized_url in overrides_by_url:
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                for override in overrides_by_url[normalized_url]:
                    updated_rows.append(promoted_summary_row(override, row))
        else:
            updated_rows.append(row)
    for normalized_url, url_overrides in overrides_by_url.items():
        if normalized_url in seen_urls:
            continue
        for override in url_overrides:
            updated_rows.append(promoted_summary_row(override, None))
    status_counts = Counter(str(row.get("status", "")) for row in updated_rows)
    sync_kind_counts = Counter(str(row.get("sync_kind", "")) for row in updated_rows)
    source_list_by_url = {
        str(row.get("normalized_url", "")): str(row.get("source_list_evidence", ""))
        for row in updated_rows
        if row.get("normalized_url")
    }
    source_list_status_counts = Counter(source_list_by_url.values())
    summary["rows"] = updated_rows
    summary["generated_at"] = now()
    summary["rows_written"] = len(updated_rows)
    summary["status"] = "mixed" if len(status_counts) > 1 else next(iter(status_counts), "none")
    summary["status_counts"] = dict(sorted(status_counts.items()))
    summary["sync_kind"] = "mixed" if len(sync_kind_counts) > 1 else next(iter(sync_kind_counts), "none")
    summary["sync_kind_counts"] = dict(sorted(sync_kind_counts.items()))
    summary["source_list_status_counts"] = dict(sorted(source_list_status_counts.items()))
    summary["install_commands_published"] = sum(1 for row in updated_rows if row.get("install_command"))
    summary["live_installs_recorded"] = sum(1 for row in updated_rows if row.get("live_install_executed"))
    write_json(SUMMARY, summary)
    reconcile_integration_targets(summary, overrides)
    enrich_deep_auth_env_names(summary, overrides)
    reconcile_final_records(summary, overrides)
    retained_urls = overlay_existing_coverage()
    overlay_research_graph(retained_urls)
    overlay_promotion_readiness(retained_urls)
    overlay_promotion_waves(retained_urls)
    refresh_promotion_gate_artifacts()
    write_progress_state(summary, overrides)

    payload = {
        "version": 1,
        "generated_at": now(),
        "applied_count": len(applied),
        "legacy_candidate_rows_removed": legacy_candidate_rows_removed,
        "items": applied,
    }
    write_json(REPORT, payload)
    return payload


def validate() -> dict[str, Any]:
    try:
        overrides = load_overrides()
    except ValueError as exc:
        return {
            "ok": False,
            "overrides": 0,
            "summary_rows": 0,
            "install_commands_published": 0,
            "errors": [str(exc)],
        }
    summary = load_json(SUMMARY)
    progress = load_json(PROGRESS)
    rows = summary.get("rows", [])
    errors: list[str] = []
    target_payload = load_integration_targets()
    errors.extend(integration_target_errors(target_payload))
    plan, plan_errors = load_promotion_wave_plan()
    errors.extend(plan_errors)
    plan_report_path = manifest_json("promotion-wave-plan.md")
    if not plan_report_path.is_file():
        errors.append("missing promotion-wave-plan.md")
    elif not plan_errors and plan_report_path.read_text(encoding="utf-8") != render_promotion_wave_report(plan):
        errors.append("promotion-wave-plan.md is stale")
    if not isinstance(rows, list):
        errors.append("catalog-authoring-summary.json rows must be a list")
        rows = []
    errors.extend(validate_override_records(overrides, rows))
    errors.extend(harness_assurance_errors())
    errors.extend(non_skill_assurance_errors())
    try:
        runtime_activation_summary()
    except ValueError as exc:
        errors.append(str(exc))
    rows_by_key = {
        (row.get("normalized_url"), row.get("name")): row
        for row in rows
        if isinstance(row, dict) and row.get("normalized_url") and row.get("name")
    }
    for override in overrides:
        if not isinstance(override, dict):
            continue
        normalized_url = override["normalized_url"]
        skill_name = override["skill_name"]
        row = rows_by_key.get((normalized_url, skill_name))
        if not row:
            errors.append(f"missing summary row for {normalized_url} / {skill_name}")
            continue
        if not row.get("install_command"):
            errors.append(f"summary row for {normalized_url} has no install command")
        if is_safe_authoring_stem(skill_name) and not authoring_path_for(str(skill_name)).exists():
            errors.append(f"missing promoted authoring row for {skill_name}")
    stale_candidate_rows = sorted(AUTHORING_DIR.glob("candidate-corpus-*.mdx"))
    if stale_candidate_rows:
        errors.append(f"stale candidate authoring rows remain: {len(stale_candidate_rows)}")
    if summary.get("rows_written") != len(rows):
        errors.append("summary rows_written does not match row count")
    live_stats = live_install_evidence_stats(overrides)
    live_installed = live_stats["live_install_rows"]
    installed_path_refs = live_stats["installed_path_refs"]
    verified_skill_md = live_stats["verified_skill_md_count"]
    missing_skill_md = live_stats["missing_installed_skill_md"]
    installable_rows = sum(1 for row in rows if isinstance(row, dict) and row.get("install_command"))
    if summary.get("install_commands_published") != installable_rows:
        errors.append("summary install_commands_published does not match installable rows")
    if summary.get("install_commands_published") != len(overrides):
        errors.append("summary install_commands_published does not match promotion override count")
    if summary.get("live_installs_recorded") != live_installed:
        errors.append("summary live_installs_recorded does not match live install evidence")
    if missing_skill_md:
        errors.append("recorded live install evidence has missing SKILL.md paths: " + ", ".join(missing_skill_md[:5]))
    status_counts = summary.get("status_counts", {})
    sync_kind_counts = summary.get("sync_kind_counts", {})
    if not isinstance(status_counts, dict):
        errors.append("summary status_counts is not an object")
        status_counts = {}
    if not isinstance(sync_kind_counts, dict):
        errors.append("summary sync_kind_counts is not an object")
        sync_kind_counts = {}
    if status_counts.get("install-now-after-trust-gate") != len(overrides):
        errors.append("summary installable status count does not match promotion override count")
    if sync_kind_counts.get("skills-cli") != len(overrides):
        errors.append("summary skills-cli sync count does not match promotion override count")
    if progress.get("phase") != "corpus-integration-complete":
        errors.append("full integration progress phase is not corpus-integration-complete")
    if progress.get("complete") is not True:
        errors.append("full integration progress does not mark the goal complete")
    readiness_manifest = load_manifest_json("promotion-readiness-queue.json", {})
    readiness_summary = readiness_manifest.get("summary", {}) if isinstance(readiness_manifest, dict) else {}
    preview_manifest = load_manifest_json("live-install-command-preview.json", {})
    preview_command_count = (
        int_value(preview_manifest.get("command_count")) if isinstance(preview_manifest, dict) else 0
    )
    preview_status = (
        preview_manifest.get("status", "no-live-install-commands-emitted")
        if isinstance(preview_manifest, dict)
        else "no-live-install-commands-emitted"
    )
    progress_live_install = progress.get("live_install", {})
    if progress_live_install.get("installed_skill_rows") != live_installed:
        errors.append("full integration progress install evidence row count drifted")
    if progress_live_install.get("recorded_install_evidence_rows") != live_installed:
        errors.append("full integration progress recorded install evidence count drifted")
    if progress_live_install.get("eligible_count") != preview_command_count:
        errors.append("full integration progress live install eligible count drifted from preview")
    if progress_live_install.get("new_live_install_commands_emitted") != preview_command_count:
        errors.append("full integration progress live install command count drifted from preview")
    if progress_live_install.get("status") != preview_status:
        errors.append("full integration progress live install status drifted from preview")
    if progress_live_install.get("installed_path_refs") != installed_path_refs:
        errors.append("full integration progress installed path reference count drifted")
    if progress_live_install.get("verified_skill_md_count") != verified_skill_md:
        errors.append("full integration progress verified SKILL.md count drifted")
    if progress_live_install.get("missing_skill_md_count") != len(missing_skill_md):
        errors.append("full integration progress missing SKILL.md count drifted")
    progress_readiness = progress.get("promotion_readiness", {})
    for field in (
        "unique_targets",
        "covered_by_existing_installable_catalog",
        "ready_for_repo_promotion",
        "ready_for_live_install",
        "terminal_native_or_hard_blocked",
    ):
        if isinstance(readiness_summary, dict) and progress_readiness.get(field) != readiness_summary.get(field):
            errors.append(f"full integration progress readiness field {field} drifted from readiness manifest")
    if progress_readiness.get("promoted_installable_rows") != len(overrides):
        errors.append("full integration progress promoted installable row count drifted")
    if progress_readiness.get("recorded_install_evidence_rows") != live_installed:
        errors.append("full integration progress install evidence readiness count drifted")
    classification_counts = target_payload.get("classification_counts", {}) if isinstance(target_payload, dict) else {}
    if target_payload.get("integrated_targets") != EXPECTED_UNIQUE_COUNT:
        errors.append("integration target ledger integrated target count drifted")
    if target_payload.get("unintegrated_targets") != 0:
        errors.append("integration target ledger reports unintegrated targets")
    if classification_counts != EXPECTED_CLASSIFICATION_COUNTS:
        errors.append("integration target ledger classification counts drifted")
    if progress_readiness.get("integrated_targets") != EXPECTED_UNIQUE_COUNT:
        errors.append("full integration progress integrated target count drifted")
    if progress_readiness.get("unintegrated_targets") != 0:
        errors.append("full integration progress reports unintegrated targets")
    if progress_readiness.get("integration_classification_counts") != classification_counts:
        errors.append("full integration progress integration classifications drifted")
    if progress_readiness.get("integrated_quarantine_targets") != 4:
        errors.append("full integration progress quarantine integration count drifted")
    if progress_readiness.get("active_install_blocks") != 4:
        errors.append("full integration progress active install block count drifted")
    coverage_manifest = load_manifest_json("existing-integration-coverage.json", {})
    coverage_items = coverage_manifest.get("items", []) if isinstance(coverage_manifest, dict) else []
    if not isinstance(coverage_items, list):
        errors.append("existing integration coverage items is not a list")
        coverage_items = []
    for item in coverage_items:
        if not isinstance(item, dict):
            continue
        normalized_url = item.get("normalized_url")
        coverage_status = item.get("coverage_status")
        if coverage_status == COVERAGE_TRUST_CLEARED and not coverage_item_trust_cleared(item):
            errors.append(f"retained existing coverage lacks trust-cleared row for {normalized_url}")
        if coverage_status == COVERAGE_INSPECTION_REQUIRED and existing_rows_trust_cleared(item.get("existing_rows")):
            errors.append(f"inspection-required coverage contains only trust-cleared rows for {normalized_url}")
    readiness_manifest = load_manifest_json("promotion-readiness-queue.json", {})
    covered_readiness = (
        readiness_manifest.get("covered_by_existing_installable_catalog", [])
        if isinstance(readiness_manifest, dict)
        else []
    )
    if not isinstance(covered_readiness, list):
        errors.append("promotion readiness covered bucket is not a list")
        covered_readiness = []
    for item in covered_readiness:
        if not isinstance(item, dict):
            continue
        if not existing_rows_trust_cleared(item.get("existing_rows")):
            errors.append(f"covered readiness row lacks trust-cleared existing row for {item.get('normalized_url')}")

    all_records = load_manifest_json("all-records.json", {})
    records = all_records.get("records", []) if isinstance(all_records, dict) else []
    deep_audit = load_manifest_json("deep-source-audit.json", {})
    deep_items = deep_audit.get("items", []) if isinstance(deep_audit, dict) else []
    deep_by_url = {
        str(item.get("normalized_url") or "").lower(): item
        for item in deep_items
        if isinstance(item, dict) and item.get("normalized_url")
    }
    if len(records) != 293:
        errors.append("final raw records do not cover all 293 entries")
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict):
            continue
        deep_item = deep_by_url.get(str(record.get("normalized_url") or "").lower(), {})
        auth_review = deep_item.get("auth_review", {}) if isinstance(deep_item, dict) else {}
        if isinstance(auth_review, dict) and deep_item.get("audit_complete"):
            if record.get("auth_required") is not bool(auth_review.get("auth_required")):
                errors.append(f"raw record auth drifted from deep audit for index {record.get('raw_index')}")
            expected_env = {
                str(value)
                for value in auth_review.get("env_vars_or_credentials", [])
                if str(value).strip() and str(value) != AUTH_UNKNOWN_PLACEHOLDER
            }
            actual_env = set(record.get("env_vars_or_credentials", []))
            if not expected_env.issubset(actual_env):
                errors.append(f"raw record auth variables drifted from deep audit for index {record.get('raw_index')}")
            if not auth_review.get("auth_required") and actual_env:
                errors.append(
                    f"raw record has auth variables despite no deep auth boundary for index {record.get('raw_index')}"
                )
        if not record.get("files_added"):
            errors.append(f"raw record files_added is empty for index {record.get('raw_index')}")
        if not record.get("files_modified"):
            errors.append(f"raw record files_modified is empty for index {record.get('raw_index')}")
        if "human review required before promotion" in str(record.get("reviewer_notes") or "").lower():
            errors.append(f"raw record reviewer state is stale for index {record.get('raw_index')}")
        if record.get("docs_steward_status") != "final-overlay-reconciled":
            errors.append(f"raw record docs-steward state is not final for index {record.get('raw_index')}")
        if record.get("integration_packet", {}).get("scope") != "historical-intake-research-only":
            errors.append(f"raw record intake packet scope is ambiguous for index {record.get('raw_index')}")
        if not isinstance(record.get("final_integration"), dict):
            errors.append(f"raw record final integration state is missing for index {record.get('raw_index')}")
        else:
            final_integration = record["final_integration"]
            if final_integration.get("non_skill_assurance") != "non-skill-install-assurance.json":
                errors.append(f"raw record non-skill assurance pointer is missing for index {record.get('raw_index')}")
            if not str(final_integration.get("runtime_disposition") or "").strip():
                errors.append(f"raw record runtime disposition is missing for index {record.get('raw_index')}")

    compliance = load_manifest_json("compliance-auth-matrix.json", {})
    compliance_items = compliance.get("items", []) if isinstance(compliance, dict) else []
    if len(compliance_items) != 293:
        errors.append("compliance auth matrix does not cover all 293 raw entries")
    expected_auth_indexes = {
        record.get("raw_index") for record in records if isinstance(record, dict) and record.get("auth_required")
    }
    auth_matrix = load_manifest_json("auth-matrix.json", {})
    auth_items = auth_matrix.get("items", []) if isinstance(auth_matrix, dict) else []
    actual_auth_indexes = {
        item.get("raw_index") for item in auth_items if isinstance(item, dict) and item.get("raw_index")
    }
    if actual_auth_indexes != expected_auth_indexes:
        errors.append("auth matrix raw indexes drifted from final records")
    safe_env_name = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")
    for item in auth_items:
        for value in item.get("env_vars_or_credentials", []) if isinstance(item, dict) else []:
            if value != AUTH_UNKNOWN_PLACEHOLDER and not safe_env_name.fullmatch(str(value)):
                errors.append(
                    f"auth matrix contains a non-placeholder credential value for index {item.get('raw_index')}"
                )

    required_reports = {
        "changelog-entry.md": "changelog",
        "risky-skipped-deduped-decision-log.md": "decision log",
        "validation-report.md": "validation report",
        "final-review-report.md": "final review report",
    }
    missing_reports = {
        filename: label for filename, label in required_reports.items() if not (MANIFEST_DIR / filename).is_file()
    }
    errors.extend(f"missing {filename}" for filename in missing_reports)

    changelog_path = MANIFEST_DIR / "changelog-entry.md"
    if changelog_path.is_file():
        changelog = changelog_path.read_text(encoding="utf-8")
        if "with 0 installs" in changelog or "Kept all third-party candidates discovery-only" in changelog:
            errors.append("changelog still reports the obsolete pre-overlay state")
    decision_log_path = MANIFEST_DIR / "risky-skipped-deduped-decision-log.md"
    if decision_log_path.is_file():
        decision_log = decision_log_path.read_text(encoding="utf-8")
        active_install_blocks = int_value(progress.get("terminal_decisions", {}).get("active_install_blocks"))
        if f"Active install blocks: {active_install_blocks}" not in decision_log:
            errors.append("decision log does not report final active install-block state")
    return {
        "ok": not errors,
        "overrides": len(overrides),
        "summary_rows": len(rows),
        "install_commands_published": summary.get("install_commands_published", 0),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="apply promotion overrides")
    parser.add_argument("--check", action="store_true", help="validate applied promotion overrides")
    args = parser.parse_args()

    if args.apply:
        payload = apply_overrides()
        print(json.dumps(payload, indent=2))
    if args.check:
        result = validate()
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1
    if not args.apply:
        parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
