#!/usr/bin/env python3
"""Record exact selector and harness-binding closure for the July 2026 corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from wagents.candidate_evidence import (
    RUNTIME_DIGEST_IGNORED_DIRS,
    RUNTIME_PREDICATE_VERSION,
    filesystem_digest,
)
from wagents.candidate_predicates import evaluate_predicate
from wagents.candidate_receipts import ReceiptStore
from wagents.parsing import parse_frontmatter
from wagents.site_model import normalize_public_install_command

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
PROMOTION_OVERRIDES = MANIFEST_DIR / "promotion-overrides.json"
APPLIED_OVERRIDES = MANIFEST_DIR / "applied-promotion-overrides.json"
HARNESS_ASSURANCE = MANIFEST_DIR / "harness-install-assurance.json"
CATALOG_INDEX = ROOT / "docs" / "public" / "generated-registries" / "skills-catalog-index.json"
RECEIPTS = MANIFEST_DIR / "runtime-activation-receipts.json"
RUNTIME_STATE = Path("~/.local/share/wagents/candidate-runtime").expanduser()
BINDING_PROOF_PHASES = (
    "discovery",
    "behavior",
    "fresh_process",
    "rollback",
    "promoted_final",
)


def load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain an object")
    return payload


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_sha256(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def evidence(paths: list[Path]) -> tuple[list[str], dict[str, str]]:
    relative_paths = sorted({relative(path) for path in paths})
    return relative_paths, {path: sha256(ROOT / path) for path in relative_paths}


def selector_id(normalized_url: str, skill_name: str) -> str:
    return f"selector:{normalized_url.lower()}:{skill_name}"


def sync_skill_name(row: object) -> str:
    value = str(row)
    marker = " ["
    if marker not in value:
        raise ValueError(f"sync inventory row has no skill-name marker: {value!r}")
    name = value.split(marker, 1)[0]
    if not name:
        raise ValueError("sync inventory row has an empty skill name")
    return name


def promotion_rows() -> list[dict[str, Any]]:
    rows = load_object(PROMOTION_OVERRIDES).get("overrides", [])
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("promotion overrides must be an object list")
    return rows


def selector_graph(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        normalized_url = str(row.get("normalized_url") or "")
        skill_name = str(row.get("skill_name") or "")
        target_agents = row.get("target_agents", [])
        if not normalized_url or not skill_name:
            raise ValueError("promotion override requires normalized_url and skill_name")
        if not isinstance(target_agents, list) or not all(isinstance(agent, str) and agent for agent in target_agents):
            raise ValueError(f"promotion selector {skill_name!r} has invalid target_agents")
        if len(target_agents) != len(set(target_agents)):
            raise ValueError(f"promotion selector {skill_name!r} has duplicate target_agents")
        installed_paths = row.get("installed_paths", [])
        if (
            not isinstance(installed_paths, list)
            or not installed_paths
            or not all(isinstance(path, str) and path for path in installed_paths)
        ):
            raise ValueError(f"promotion selector {skill_name!r} has invalid installed_paths")
        if len(installed_paths) != len(set(installed_paths)):
            raise ValueError(f"promotion selector {skill_name!r} has duplicate installed_paths")
        node_id = selector_id(normalized_url, skill_name)
        if node_id in result:
            raise ValueError(f"duplicate promotion selector: {node_id}")
        result[node_id] = {
            "selector_id": node_id,
            "normalized_url": normalized_url,
            "skill_name": skill_name,
            "install_skill_name": str(row.get("install_skill_name") or skill_name),
            "path": f"docs/src/authoring/skills/{skill_name}.mdx",
            "target_agents": sorted(target_agents),
            "install_source": str(row.get("install_source") or ""),
            "install_command": str(row.get("install_command") or ""),
            "status": str(row.get("status") or ""),
            "trust_tier": str(row.get("trust_tier") or ""),
            "provenance_status": str(row.get("provenance_status") or ""),
            "selector_mode": str(row.get("selector_mode") or ""),
            "sync_kind": str(row.get("sync_kind") or ""),
            "audited_head": str(row.get("audited_head") or ""),
            "installed_paths": sorted(installed_paths),
        }
    return result


def authoring_binding(item: dict[str, Any], path: Path) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not path.is_file():
        return {}, ["authoring path is missing"]
    try:
        frontmatter, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {}, [f"authoring frontmatter is invalid: {exc}"]
    if not isinstance(frontmatter, dict):
        return {}, ["authoring frontmatter must be an object"]

    expected = {
        "name": item["skill_name"],
        "install_skill_name": item["install_skill_name"],
        "source_url": item["normalized_url"],
        "source_kind": "curated-external",
        "install_source": item["install_source"],
        "install_command": item["install_command"],
        "status": item["status"],
        "trust_tier": item["trust_tier"],
        "provenance_status": item["provenance_status"],
        "selector_mode": item["selector_mode"],
        "sync_kind": item["sync_kind"],
        "target_agents": item["target_agents"],
    }
    actual = {field: frontmatter.get(field) for field in expected}
    for field, expected_value in expected.items():
        actual_value = actual[field]
        if field == "source_url":
            matches = str(actual_value or "").lower() == str(expected_value).lower()
        elif field == "target_agents":
            matches = (
                isinstance(actual_value, list)
                and all(isinstance(agent, str) and agent for agent in actual_value)
                and len(actual_value) == len(set(actual_value))
                and sorted(actual_value) == expected_value
            )
        else:
            matches = actual_value == expected_value
        if not matches:
            errors.append(f"authoring frontmatter {field} drifted")
    return actual, errors


def catalog_rows_by_name() -> dict[str, dict[str, Any]]:
    catalog_rows = load_object(CATALOG_INDEX).get("allSkillIndex", [])
    if not isinstance(catalog_rows, list) or not all(isinstance(row, dict) for row in catalog_rows):
        raise ValueError("catalog allSkillIndex must be an object list")
    result: dict[str, dict[str, Any]] = {}
    for row in catalog_rows:
        name = str(row.get("name") or "")
        if not name or name in result:
            raise ValueError(f"invalid or duplicate generated catalog name: {name!r}")
        result[name] = row
    return result


def required_capabilities(item: dict[str, Any], catalog_row: dict[str, Any] | None) -> tuple[list[str], list[str]]:
    """Derive portable behavior requirements from current catalog metadata."""

    if not isinstance(catalog_row, dict):
        return [], ["generated catalog row is missing; required capabilities are unavailable"]
    use_command = catalog_row.get("useCommand")
    if not isinstance(use_command, str) or not use_command.strip():
        return [], ["generated catalog useCommand is missing; required capabilities are unavailable"]
    if catalog_row.get("syncKind") != item.get("sync_kind"):
        return [], ["generated catalog syncKind drift prevents capability derivation"]
    if catalog_row.get("selectorMode") != item.get("selector_mode"):
        return [], ["generated catalog selectorMode drift prevents capability derivation"]
    return [f"invoke:{use_command.strip()}"], []


def current_installed_digest(item: dict[str, Any]) -> tuple[str, list[str]]:
    """Hash the current installed selector roots declared by promotion metadata."""

    raw_paths = item.get("installed_paths", [])
    if not isinstance(raw_paths, list) or not raw_paths:
        return "", ["current installed paths are unavailable"]
    resolved = [Path(str(value)).expanduser().absolute() for value in raw_paths]
    missing = [
        str(raw) for raw, path in zip(raw_paths, resolved, strict=True) if not path.exists() and not path.is_symlink()
    ]
    if missing:
        return "", [f"current installed paths are missing: {missing!r}"]
    try:
        return (
            filesystem_digest(resolved, ignored_dirs=RUNTIME_DIGEST_IGNORED_DIRS),
            [],
        )
    except OSError as exc:
        return "", [f"current installed paths could not be hashed: {type(exc).__name__}"]


def binding_input_digest(
    item: dict[str, Any],
    *,
    agent: str,
    authoring_sha256: str,
    catalog_row: dict[str, Any],
    sync_report_sha256: str,
    capabilities: list[str],
) -> str:
    """Bind one edge to the exact portable catalog and sync inputs."""

    return object_sha256({
        "agent": agent,
        "authoring_sha256": authoring_sha256,
        "catalog_row_sha256": object_sha256(catalog_row),
        "install_command": normalize_public_install_command(str(item["install_command"])),
        "install_skill_name": item["install_skill_name"],
        "install_source": item["install_source"],
        "normalized_url": item["normalized_url"],
        "required_capabilities": capabilities,
        "selector_id": item["selector_id"],
        "selector_mode": item["selector_mode"],
        "skill_name": item["skill_name"],
        "sync_report_sha256": sync_report_sha256,
        "sync_kind": item["sync_kind"],
        "target_agents": item["target_agents"],
    })


def comparable_artifact_receipt(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "store_transaction_id"}


def artifact_receipt_sha256(value: dict[str, Any]) -> str:
    return object_sha256(comparable_artifact_receipt(value))


def build_selector_receipt(
    graph: dict[str, dict[str, Any]],
    catalog_by_name: dict[str, dict[str, Any]],
    binding_leaves: list[dict[str, Any]],
) -> dict[str, Any]:
    applied_rows = load_object(APPLIED_OVERRIDES).get("items", [])
    if not isinstance(applied_rows, list) or not all(isinstance(row, dict) for row in applied_rows):
        raise ValueError("applied promotion overrides must be an object list")

    applied: dict[str, dict[str, Any]] = {}
    for row in applied_rows:
        node_id = selector_id(str(row.get("normalized_url") or ""), str(row.get("skill_name") or ""))
        if node_id in applied:
            raise ValueError(f"duplicate applied selector: {node_id}")
        applied[node_id] = row
    if set(applied) != set(graph):
        raise ValueError("applied promotion selectors do not exactly match promotion overrides")

    bindings_by_selector: dict[str, list[dict[str, Any]]] = {}
    for leaf in binding_leaves:
        bindings_by_selector.setdefault(str(leaf.get("selector_id") or ""), []).append(leaf)

    leaves: list[dict[str, Any]] = []
    for node_id, item in sorted(graph.items()):
        applied_row = applied[node_id]
        catalog_row = catalog_by_name.get(str(item["skill_name"]))
        authoring_path = ROOT / str(item["path"])
        errors: list[str] = []
        if applied_row.get("path") != item["path"]:
            errors.append("applied authoring path drifted")
        frontmatter, frontmatter_errors = authoring_binding(item, authoring_path)
        errors.extend(frontmatter_errors)
        capabilities, capability_errors = required_capabilities(item, catalog_row)
        errors.extend(capability_errors)
        if not isinstance(catalog_row, dict):
            errors.append("generated catalog row is missing")
        else:
            expected_catalog = {
                "name": item["skill_name"],
                "sourceUrl": item["normalized_url"],
                "sourcePath": item["path"],
                "installSource": item["install_source"],
                "installCommand": normalize_public_install_command(item["install_command"]),
                "installable": True,
                "sourceKind": "curated-external",
                "provenanceStatus": item["provenance_status"],
                "status": item["status"],
                "trustTier": item["trust_tier"],
                "selectorMode": item["selector_mode"],
                "syncKind": item["sync_kind"],
                "targetAgents": item["target_agents"],
                "auditedHead": item["audited_head"],
            }
            for field, expected in expected_catalog.items():
                actual = catalog_row.get(field)
                if field == "sourceUrl":
                    matches = str(actual or "").lower() == str(expected).lower()
                elif field == "targetAgents":
                    matches = (
                        isinstance(actual, list) and sorted(actual) == expected and len(actual) == len(set(actual))
                    )
                else:
                    matches = actual == expected
                if not matches:
                    errors.append(f"generated catalog {field} drifted")
        source_errors = list(errors)
        selector_bindings = bindings_by_selector.get(node_id, [])
        if len(selector_bindings) != len(item["target_agents"]):
            errors.append("selector does not have exactly one binding leaf per target harness")
        proved = sorted(
            capability
            for capability in capabilities
            if selector_bindings
            and all(capability in binding.get("proved_capabilities", []) for binding in selector_bindings)
        )
        untested = sorted(set(capabilities) - set(proved))
        if untested:
            errors.append(f"required selector capabilities remain untested: {untested!r}")
        leaves.append({
            "node_id": node_id,
            "selector_id": node_id,
            "normalized_url": item["normalized_url"],
            "skill_name": item["skill_name"],
            "path": item["path"],
            "authoring_sha256": sha256(authoring_path) if authoring_path.is_file() else "",
            "frontmatter_binding_sha256": object_sha256(frontmatter) if frontmatter else "",
            "frontmatter_fields_verified": sorted(frontmatter),
            "source_evidence_status": "passed" if not source_errors else "failed",
            "required_capabilities": capabilities,
            "proved_capabilities": proved,
            "untested_capabilities": untested,
            "status": "accepted" if not errors else "incomplete",
            "predicate_errors": errors,
        })

    authoring_paths = sorted(
        (ROOT / str(item["path"]) for item in graph.values() if (ROOT / str(item["path"])).is_file()),
        key=relative,
    )
    paths, digests = evidence([PROMOTION_OVERRIDES, APPLIED_OVERRIDES, CATALOG_INDEX, *authoring_paths])
    blockers = [leaf["node_id"] for leaf in leaves if leaf["status"] != "accepted"]
    aggregate_required = sorted(
        f"{leaf['node_id']}::{capability}" for leaf in leaves for capability in leaf["required_capabilities"]
    )
    aggregate_proved = sorted(
        f"{leaf['node_id']}::{capability}" for leaf in leaves for capability in leaf["proved_capabilities"]
    )
    return {
        "gate_id": "selector-closure",
        "expected_leaf_ids": sorted(graph),
        "leaf_receipts": leaves,
        "verification_status": "passed" if not blockers else "failed",
        "active_blockers": blockers,
        "required_capabilities": aggregate_required,
        "proved_capabilities": aggregate_proved,
        "untested_capabilities": sorted(set(aggregate_required) - set(aggregate_proved)),
        "evidence_paths": paths,
        "evidence_digests": digests,
    }


SYNC_INVENTORY_FIELDS = ("already_present", "missing", "pin_blocked", "unresolved", "skipped")


def sync_inventory(row: dict[str, Any], field: str) -> Counter[str]:
    values = row.get(field, [])
    if not isinstance(values, list):
        raise ValueError(f"sync report {field} must be a list")
    return Counter(sync_skill_name(value) for value in values)


def sanitized_sync_evidence(report: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    agents: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: str(item.get("agent") or "")):
        commands = row.get("commands", [])
        if not isinstance(commands, list):
            raise ValueError("sync report commands must be a list")
        agents.append({
            "agent": str(row.get("agent") or ""),
            "inventory": {field: dict(sorted(sync_inventory(row, field).items())) for field in SYNC_INVENTORY_FIELDS},
            "command_count": len(commands),
            "error_present": bool(row.get("error")),
        })
    return {
        "schema_version": 1,
        "sanitization": "inventory rows reduced to skill-name counters; commands, paths, and error bodies omitted",
        "ok": report.get("ok"),
        "mode": report.get("mode"),
        "agents": agents,
    }


def binding_artifact_keys(graph: dict[str, dict[str, Any]]) -> set[tuple[str, str]]:
    return {
        (f"binding:{node_id}:{agent}", phase)
        for node_id, item in graph.items()
        for agent in item["target_agents"]
        for phase in BINDING_PROOF_PHASES
    }


def build_binding_receipt(
    graph: dict[str, dict[str, Any]],
    sync_report: Path,
    artifact_rows: dict[tuple[str, str], dict[str, Any]],
    catalog_by_name: dict[str, dict[str, Any]],
    *,
    now: str | None = None,
) -> dict[str, Any]:
    raw = sync_report.read_bytes()
    source_digest = hashlib.sha256(raw).hexdigest()
    report = json.loads(raw)
    assurance = load_object(HARNESS_ASSURANCE)
    if not isinstance(report, dict) or report.get("ok") is not True or report.get("mode") not in {"dry-run", "apply"}:
        raise ValueError("sync report must be a successful dry-run or apply JSON report")
    if assurance.get("complete") is not True or assurance.get("source_sha256") != source_digest:
        raise ValueError("sync report is not the exact report bound by harness-install-assurance.json")
    agent_rows = report.get("agents", [])
    if not isinstance(agent_rows, list) or not all(isinstance(row, dict) for row in agent_rows):
        raise ValueError("sync report agents must be an object list")

    expected_agents = sorted({agent for item in graph.values() for agent in item["target_agents"]})
    by_agent: dict[str, dict[str, Any]] = {}
    for row in agent_rows:
        agent = str(row.get("agent") or "")
        if not agent or agent in by_agent:
            raise ValueError(f"invalid or duplicate sync agent row: {agent!r}")
        by_agent[agent] = row
    if sorted(by_agent) != expected_agents:
        raise ValueError("sync report agents do not exactly match promotion target agents")
    retained_evidence = sanitized_sync_evidence(report, agent_rows)
    retained_digest = object_sha256(retained_evidence)
    freshness_now = now or datetime.now(UTC).isoformat()

    leaves: list[dict[str, Any]] = []
    for node_id, item in sorted(graph.items()):
        skill_name = str(item["skill_name"])
        catalog_row = catalog_by_name.get(skill_name)
        capabilities, capability_errors = required_capabilities(item, catalog_row)
        authoring_path = ROOT / str(item["path"])
        authoring_digest = sha256(authoring_path) if authoring_path.is_file() else ""
        installed_digest, installed_errors = current_installed_digest(item)
        for agent in item["target_agents"]:
            row = by_agent[agent]
            inventory = {field: sync_inventory(row, field) for field in SYNC_INVENTORY_FIELDS}
            errors: list[str] = []
            if row.get("error"):
                errors.append("harness sync row reports an error")
            if row.get("commands"):
                errors.append("harness sync row still proposes commands")
            if inventory["already_present"][skill_name] != 1:
                errors.append(f"already-present count is {inventory['already_present'][skill_name]}, expected 1")
            if inventory["missing"][skill_name]:
                errors.append("selector remains missing")
            if inventory["pin_blocked"][skill_name]:
                errors.append("selector remains pin-blocked")
            if inventory["unresolved"][skill_name]:
                errors.append("selector remains unresolved")
            if inventory["skipped"][skill_name]:
                errors.append("selector remains skipped")
            sync_errors = list(errors)
            binding_id = f"binding:{node_id}:{agent}"
            errors.extend(capability_errors)
            if not authoring_digest:
                errors.append("authoring path is missing; binding input digest is unavailable")
            errors.extend(installed_errors)
            input_digest = (
                binding_input_digest(
                    item,
                    agent=agent,
                    authoring_sha256=authoring_digest,
                    catalog_row=catalog_row,
                    sync_report_sha256=source_digest,
                    capabilities=capabilities,
                )
                if isinstance(catalog_row, dict) and authoring_digest and capabilities
                else ""
            )
            prior_phase_digests = {
                phase: artifact_receipt_sha256(artifact_rows[binding_id, phase])
                for phase in BINDING_PROOF_PHASES[:-1]
                if (binding_id, phase) in artifact_rows
            }
            phase_evidence: dict[str, dict[str, Any]] = {}
            for phase in BINDING_PROOF_PHASES:
                phase_row = artifact_rows.get((binding_id, phase))
                phase_errors: list[str]
                if phase_row is None:
                    phase_errors = [f"missing binding phase receipt: {binding_id}:{phase}"]
                    receipt_digest = ""
                    assertion_digest = ""
                else:
                    phase_context = {
                        "expected_artifact_id": binding_id,
                        "expected_phase": phase,
                        "expected_selector_id": node_id,
                        "expected_harness": agent,
                        "source_commit_sha": item["audited_head"],
                        "input_digest": input_digest,
                        "installed_digest": installed_digest,
                        "predicate_version": RUNTIME_PREDICATE_VERSION,
                        "required_capabilities": capabilities,
                        "expected_phase_receipt_digests": prior_phase_digests,
                        "expected_sync_report_sha256": source_digest,
                        "now": freshness_now,
                    }
                    phase_errors = evaluate_predicate("harness-binding-phase", phase_row, phase_context)
                    if phase == "discovery" and phase_row.get("sync_report_sha256") != source_digest:
                        phase_errors.append("discovery receipt is not bound to the current sync report")
                    receipt_digest = artifact_receipt_sha256(phase_row)
                    assertion_digest = str(phase_row.get("assertion_sha256") or "")
                summary: dict[str, Any] = {
                    "receipt_sha256": receipt_digest,
                    "assertion_sha256": assertion_digest,
                    "status": "accepted" if not phase_errors else "incomplete",
                    "predicate_errors": phase_errors,
                }
                if phase == "behavior" and phase_row is not None and not phase_errors:
                    summary["proved_capabilities"] = sorted(
                        capability
                        for capability in phase_row.get("proved_capabilities", [])
                        if isinstance(capability, str)
                    )
                phase_evidence[phase] = summary
                errors.extend(f"{phase}: {error}" for error in phase_errors)
            leaves.append({
                "node_id": binding_id,
                "selector_id": node_id,
                "normalized_url": item["normalized_url"],
                "skill_name": skill_name,
                "agent": agent,
                "sync_disposition": "already-present" if not sync_errors else "incomplete",
                "sync_report_sha256": source_digest,
                "sync_evidence_sha256": retained_digest,
                "input_digest": input_digest,
                "installed_digest": installed_digest,
                "installed_path_refs": list(item["installed_paths"]),
                "required_capabilities": capabilities,
                "proved_capabilities": [],
                "untested_capabilities": capabilities,
                "phase_evidence": phase_evidence,
                "status": "incomplete",
                "predicate_errors": errors,
            })

    assertion_owners: dict[str, list[tuple[dict[str, Any], str]]] = {}
    for leaf in leaves:
        for phase, summary in leaf["phase_evidence"].items():
            assertion_digest = summary.get("assertion_sha256")
            if isinstance(assertion_digest, str) and assertion_digest:
                assertion_owners.setdefault(assertion_digest, []).append((leaf, phase))
    for assertion_digest, owners in assertion_owners.items():
        if len(owners) < 2:
            continue
        owner_ids = sorted(f"{leaf['node_id']}:{phase}" for leaf, phase in owners)
        duplicate_error = f"assertion digest is reused across binding phases: {assertion_digest} {owner_ids!r}"
        for leaf, phase in owners:
            summary = leaf["phase_evidence"][phase]
            summary["status"] = "incomplete"
            summary["predicate_errors"].append(duplicate_error)
            leaf["predicate_errors"].append(f"{phase}: {duplicate_error}")

    for leaf in leaves:
        behavior = leaf["phase_evidence"]["behavior"]
        proved = behavior.get("proved_capabilities", []) if behavior["status"] == "accepted" else []
        leaf["proved_capabilities"] = sorted(set(proved) & set(leaf["required_capabilities"]))
        leaf["untested_capabilities"] = sorted(set(leaf["required_capabilities"]) - set(leaf["proved_capabilities"]))
        if leaf["untested_capabilities"]:
            leaf["predicate_errors"].append(f"required capabilities remain untested: {leaf['untested_capabilities']!r}")
        if leaf["sync_disposition"] == "incomplete" or leaf["predicate_errors"]:
            leaf["status"] = "incomplete"
        else:
            leaf["status"] = "accepted"

    authoring_paths = sorted(
        (ROOT / str(item["path"]) for item in graph.values() if (ROOT / str(item["path"])).is_file()),
        key=relative,
    )
    paths, digests = evidence([HARNESS_ASSURANCE, PROMOTION_OVERRIDES, CATALOG_INDEX, *authoring_paths])
    blockers = [leaf["node_id"] for leaf in leaves if leaf["status"] != "accepted"]
    aggregate_required = sorted(
        f"{leaf['node_id']}::{capability}" for leaf in leaves for capability in leaf["required_capabilities"]
    )
    aggregate_proved = sorted(
        f"{leaf['node_id']}::{capability}" for leaf in leaves for capability in leaf["proved_capabilities"]
    )
    return {
        "gate_id": "harness-binding-closure",
        "expected_leaf_ids": [leaf["node_id"] for leaf in leaves],
        "leaf_receipts": leaves,
        "target_harnesses": expected_agents,
        "sync_report_sha256": source_digest,
        "source_report_sha256": source_digest,
        "sanitized_sync_report": retained_evidence,
        "sanitized_sync_report_sha256": retained_digest,
        "source_report_evidence_sha256": retained_digest,
        "verification_status": "passed" if not blockers else "failed",
        "active_blockers": blockers,
        "required_capabilities": aggregate_required,
        "proved_capabilities": aggregate_proved,
        "untested_capabilities": sorted(set(aggregate_required) - set(aggregate_proved)),
        "evidence_paths": paths,
        "evidence_digests": digests,
    }


def build_receipts(
    graph: dict[str, dict[str, Any]],
    sync_report: Path,
    artifact_rows: dict[tuple[str, str], dict[str, Any]],
    *,
    now: str | None = None,
) -> dict[str, dict[str, Any]]:
    catalog_by_name = catalog_rows_by_name()
    binding = build_binding_receipt(
        graph,
        sync_report,
        artifact_rows,
        catalog_by_name,
        now=now,
    )
    return {
        "selector-closure": build_selector_receipt(graph, catalog_by_name, binding["leaf_receipts"]),
        "harness-binding-closure": binding,
    }


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def comparable_receipt(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {key: item for key, item in value.items() if key != "store_transaction_id"}


def generated_receipt_errors(generated: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for gate_id, receipt in sorted(generated.items()):
        blockers = receipt.get("active_blockers")
        if receipt.get("verification_status") != "passed":
            errors.append(f"{gate_id} verification_status is not passed")
        if not isinstance(blockers, list):
            errors.append(f"{gate_id} active_blockers must be a list")
        elif blockers:
            errors.append(f"{gate_id} has {len(blockers)} active blockers")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sync-report", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()

    store = ReceiptStore(RECEIPTS, RUNTIME_STATE)
    graph = selector_graph(promotion_rows())
    snapshot = store.snapshot(
        artifact_keys=binding_artifact_keys(graph),
        closure_keys={"selector-closure", "harness-binding-closure"},
    )
    generated = build_receipts(graph, args.sync_report, snapshot.artifact_rows)
    existing = snapshot.closure_rows
    errors = generated_receipt_errors(generated)
    if args.check and any(
        canonical(comparable_receipt(existing.get(key))) != canonical(row) for key, row in generated.items()
    ):
        errors.append("stored selector or harness-binding closure receipts are stale")
    applied = args.apply and not errors
    if applied:
        store.commit(snapshot, closure_upserts=generated)

    summary = {
        "ok": not errors,
        "applied": applied,
        "selector_leaf_count": len(generated["selector-closure"]["leaf_receipts"]),
        "binding_leaf_count": len(generated["harness-binding-closure"]["leaf_receipts"]),
        "target_harnesses": generated["harness-binding-closure"]["target_harnesses"],
        "source_report_sha256": generated["harness-binding-closure"]["source_report_sha256"],
        "errors": errors,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
