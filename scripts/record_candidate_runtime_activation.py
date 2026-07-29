#!/usr/bin/env python3
"""Build fail-closed runtime activation state for the July 2026 corpus."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from wagents.candidate_evidence import (
    FILESYSTEM_DIGEST_ALGORITHM,
    RUNTIME_DIGEST_IGNORED_DIRS,
    RUNTIME_PREDICATE_VERSION,
    filesystem_digest,
    receipt_input_digest,
)
from wagents.candidate_mcp_activation import (
    canonical_json_sha256,
    configured_tools,
    mcphub_exposed_tool_names,
    normalized_projection,
)
from wagents.candidate_plugin_provenance import (
    PLUGIN_CONTENT_DIGEST_ALGORITHM,
    PLUGIN_CONTENT_IGNORED_DIRS,
    codex_plugin_live_state,
    load_plugin_provenance_lock,
    plugin_installed_package_origin,
    plugin_lock_entry_sha256,
    resolve_locked_marketplace_source,
    verify_plugin_content,
)
from wagents.candidate_predicates import evaluate_predicate
from wagents.candidate_provenance import package_manager_provenance
from wagents.candidate_receipts import ReceiptStore

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
OUTPUT = MANIFEST_DIR / "runtime-activation-assurance.json"
RECEIPTS = MANIFEST_DIR / "runtime-activation-receipts.json"
PLUGIN_PROVENANCE_LOCK = MANIFEST_DIR / "plugin-provenance-lock.json"
RUNTIME_RECEIPT_ROOT = Path.home() / ".local/share/wagents/candidate-runtime/receipts"
RUNTIME_STATE = Path.home() / ".local/share/wagents/candidate-runtime"
UV_TOOLS = Path.home() / ".local/share/uv/tools"
CODEX_PLUGIN_CACHE = Path.home() / ".codex/plugins/cache"
CODEX_CONFIG = Path.home() / ".codex/config.toml"
PLUGIN_MARKETPLACE_ROOTS = {
    "candidate-corpus-local": Path.home() / ".local/share/wagents/candidate-corpus-plugin-marketplace",
    "awesome-codex-plugins": Path.home() / ".codex/.tmp/marketplaces/awesome-codex-plugins",
}
MCP_REGISTRY = ROOT / "config/mcp-registry.json"
MCPHUB_SETTINGS = ROOT / "mcp/mcphub/mcp_settings.json"
MCPHUB_LIVE_SETTINGS = ROOT / ".mcphub/runtime/mcp_settings.json"
LEGACY_SCRIPT = ROOT / "scripts" / "record_candidate_non_skill_assurance.py"
FINAL_CLOSURE_SCRIPT = ROOT / "scripts" / "record_candidate_final_closure.py"
CATALOG_CLOSURE_SCRIPT = ROOT / "scripts" / "record_candidate_catalog_closure.py"
EXPECTED_TARGET_COUNT = 289
EXPECTED_RUNTIME_COUNT = 65
EXPECTED_KIND_COUNTS = {"cli": 30, "library": 1, "mcp": 17, "plugin": 17}
NON_GLOBAL_CLOSURE_GATES = (
    "selector-closure",
    "harness-binding-closure",
    "docs-closure",
    "review-closure",
)
REQUIRED_CLOSURE_GATES = (*NON_GLOBAL_CLOSURE_GATES, "global-closure")
CLOSURE_PREDICATES = {
    "selector-closure": "selector-closure",
    "harness-binding-closure": "harness-binding-closure",
    "docs-closure": "docs-edges",
    "review-closure": "independent-reviews",
}
CLOSURE_STATUS_FIELDS = {
    "selector-closure": ("verification_status",),
    "harness-binding-closure": ("verification_status",),
    "docs-closure": ("generation_status", "check_status", "build_status", "idempotence_status"),
    "review-closure": ("findings_fixed_status",),
}
PHASE_PREDICATES = (
    ("identity", "package-identity"),
    ("install", "install-receipt"),
    ("behavior", "behavior-probe"),
    ("fresh_process", "fresh-process"),
    ("rollback", "rollback"),
)
_SAFE_EVIDENCE_PART = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SUCCESS_MARKER_FIELDS = frozenset({
    "version",
    "transaction_id",
    "status",
    "journal_path",
    "journal_sha256",
    "artifact_ids",
    "receipt_revision",
    "receipt_store_transaction_id",
    "receipt_document_sha256",
})


def now() -> str:
    return datetime.now(UTC).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain an object")
    return payload


def load_legacy_specs() -> dict[str, list[dict[str, Any]]]:
    spec = importlib.util.spec_from_file_location("_candidate_non_skill_seed", LEGACY_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {LEGACY_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return {str(url): [dict(item) for item in rows] for url, rows in module.RUNTIME_SPECS.items()}


def load_final_closure_module():
    spec = importlib.util.spec_from_file_location("_candidate_final_closure", FINAL_CLOSURE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {FINAL_CLOSURE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_catalog_closure_module():
    spec = importlib.util.spec_from_file_location("_candidate_catalog_closure", CATALOG_CLOSURE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {CATALOG_CLOSURE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def current_producer_closure_receipt(gate_id: str) -> dict[str, Any]:
    """Reconstruct docs/review evidence through the canonical producer."""
    module = load_final_closure_module()
    if gate_id == "docs-closure":
        return dict(module.docs_receipt())
    if gate_id == "review-closure":
        return dict(module.review_receipt())
    raise ValueError(f"unsupported producer closure gate: {gate_id}")


def runtime_specs() -> dict[str, list[dict[str, Any]]]:
    specs = load_legacy_specs()
    agentkits_url = "https://github.com/aitytech/agentkits-marketing"
    specs[agentkits_url].append({
        "kind": "cli",
        "package_manager": "npm",
        "package_name": "@aitytech/agentkits-marketing",
        "version": "1.7.2",
        "executables": ["agentkits-marketing", "markit"],
        "paths": [],
        "probe": [],
        "probe_contains": "",
        "probe_exit_codes": [0],
        "probe_env": {},
        "mcp_server": "",
        "plugin_id": "",
        "plugin_enabled": None,
        "auth_env_names": [],
        "auth_required": False,
        "config_surfaces": [],
        "notes": "Package CLI entrypoints were omitted from the historical library-only ledger.",
    })
    openspec_mcp_url = "https://github.com/lumiaqian/openspec-mcp"
    specs[openspec_mcp_url][0]["executables"] = ["openspec-mcp"]
    prompt_to_asset_url = "https://github.com/mohamedabdallah-14/prompt-to-asset"
    prompt_mcp = next(item for item in specs[prompt_to_asset_url] if item.get("kind") == "mcp")
    prompt_mcp["auth_env_names"] = sorted({*prompt_mcp.get("auth_env_names", []), "HORDE_API_KEY"})
    specs["https://github.com/openags/paper-search-mcp"][0]["auth_env_names"] = [
        "PAPER_SEARCH_MCP_CORE_API_KEY",
        "PAPER_SEARCH_MCP_SEMANTIC_SCHOLAR_API_KEY",
        "PAPER_SEARCH_MCP_UNPAYWALL_EMAIL",
        "PAPER_SEARCH_MCP_ZENODO_ACCESS_TOKEN",
    ]
    specs["https://github.com/antvis/mcp-server-chart"][0]["auth_env_names"] = []
    for url, package_name in (
        ("https://github.com/ratnaditya-j/csvglow", "csvglow"),
        ("https://github.com/auriti-labs/geo-optimizer-skill", "geo-optimizer-skill"),
        ("https://github.com/marzukia/charted", "charted"),
    ):
        mcp_artifact = next(item for item in specs[url] if item.get("kind") == "mcp")
        mcp_artifact.update({"package_manager": "uv-tool", "package_name": package_name})

    refreshed_sources = {
        "https://github.com/heygen-com/hyperframes": {
            "version": "0.7.61",
            "source_commit_sha": "c268f5ba85f2c9af751db1f33819fcb60c7848b0",
            "integrity": (
                "sha512-0k/FDNZ3mAGKoXDeOtrevpifmozqyXOvXAs2pApnAwyYU5M+aBJqW9wklGF2XNQfU77Dl53loaF8xkBBmkQLPg=="
            ),
        },
        "https://github.com/pythoughts-labs/designer-skill": {
            "source_commit_sha": "c96e7b743d0a2bc9cb41f0503b06d061426d1250",
        },
        "https://github.com/papischolz/roadmapsmith": {
            "version": "1.2.2",
            "source_commit_sha": "0d29db2d23f30e5e0fddf5466913e34bc518562a",
        },
        "https://github.com/sflueckiger/specboard": {
            "version": "1.2.0",
            "source_commit_sha": "0c8b4399e87dc332ef29247207186fe7f6f7186f",
            "integrity": (
                "sha512-fYfRUZGMztcxiJGqOT+ELgHzH74HeGu04jm4IjlSmiKkjjvD+tLk17GRiI5QcUweMz8RKQWXmcBy6Kj9rHa4Fg=="
            ),
        },
        "https://github.com/tanstack/cli": {
            "version": "0.69.6",
            "source_commit_sha": "d7818c3dc0736a3af1e6878ede0f7aaa25e4d34f",
            "integrity": (
                "sha512-Q8Uw54Yrp6Tr9niPBxUkPe35cwC2vLZdduCNtOWRwsbzd2/1ApJHen5OufDaiRvHiQKD4xuCw2Q/3TYpKfUsWw=="
            ),
        },
        "https://github.com/hardikpandya/stop-slop": {
            "version": "0.7.8",
            "source_commit_sha": "8da1f030185bdfe8471220585162991eaeb970e9",
            "integrity": (
                "sha512-mJ93im3OYUFTbb0/FJrc6pLd89IaNnPRq5a/k9xIqprlhsB5Y8raQJJWBIScUuoP5QOqFe8tTrXs8olqGi4VuA=="
            ),
        },
        "https://github.com/wxhou/openspec-playwright": {
            "version": "0.3.57",
            "source_commit_sha": "fc951a456d30136e2c74df0f567c9b7815d8a9d5",
            "integrity": (
                "sha512-h7Jv1iEoEPE4zMM/6P+SM/t5aZrPPa4fTjj/FLfwV5uYQ1Q1xnKDgal079iDZEb+TMR9zxgcX1qipo6i+Vlgpg=="
            ),
        },
        "https://github.com/millionco/react-doctor": {
            "version": "0.7.8",
            "source_commit_sha": "a16e452648eda8a2c05504219d1af66fd428dbf8",
            "integrity": (
                "sha512-G3spmtZJE/gWWPRJ3rpgUWTPRDJpEmdRja7iNZ7RAXlfpEO+NWVzPTca/cPI9hLwPo2Aq5/BZggo5JDBrwGrlA=="
            ),
        },
        "https://github.com/nteract/semiotic": {
            "version": "3.8.2",
            "source_commit_sha": "0cc4e4c0f5f0cec3a1f28091def66097ebddd5c3",
            "integrity": (
                "sha512-gTfM94TrmlcGpI8RrhYr5crpkKhn6n8gQ6RJjmeJVF0lFMDQA0QNjwKwH1KJ0k6+nJKeScF88kjGUBeEH177MQ=="
            ),
        },
    }
    for url, updates in refreshed_sources.items():
        for item in specs[url]:
            item.update(updates)
    designer_plugin = next(
        item for item in specs["https://github.com/pythoughts-labs/designer-skill"] if item.get("kind") == "plugin"
    )
    designer_plugin["version"] = "0.14.0"
    hyperframes_cli = next(
        item for item in specs["https://github.com/heygen-com/hyperframes"] if item.get("kind") == "cli"
    )
    hyperframes_cli["probe_contains"] = "0.7.61"

    # Provider credentials are optional for these bounded, keyless canaries.
    # Their names remain in the assurance and docs, but do not block base use.
    for rows in specs.values():
        for item in rows:
            item.setdefault("auth_required", False)
    langfuse = specs["https://github.com/avivsinai/langfuse-mcp"][0]
    langfuse.update({
        "auth_required": True,
        "auth_mode": "environment",
        "auth_provider": "langfuse",
        "auth_storage_backend": "environment",
        "minimum_scopes": ["trace-read-only"],
    })
    papersflow = specs["https://github.com/papersflow-ai/papersflow-codex-plugin"]
    hosted_papersflow = next(item for item in papersflow if item.get("kind") == "mcp")
    hosted_papersflow.update({
        "auth_required": True,
        "auth_mode": "oauth",
        "auth_provider": "papersflow",
        "auth_storage_backend": "oauth-session",
        "minimum_scopes": ["papersflow-mcp-access"],
        "auth_env_names": ["PAPERSFLOW_OAUTH_ACCOUNT"],
    })
    specs["https://github.com/octane0411/opencode-plugin-openspec"] = [
        {
            "kind": "plugin",
            "package_manager": "opencode-plugin",
            "package_name": "opencode-plugin-openspec",
            "version": "0.1.4",
            "source_commit_sha": "54864428bd0cb2afeb36f6558ca714b7bbc1203f",
            "integrity": (
                "sha512-g2g4bUvtC1Ovj/lrbAhL1b0befBN6LCCIRyrdXjfX1n8gn5mN4/z9s6q4wsEPcuk4DtSUZ+2Kig3+2UzASIBBg=="
            ),
            "executables": [],
            "paths": [],
            "probe": [],
            "probe_contains": "",
            "probe_exit_codes": [0],
            "probe_env": {},
            "mcp_server": "",
            "plugin_id": "candidate-opencode-plugin-openspec",
            "plugin_enabled": False,
            "auth_env_names": [],
            "config_surfaces": ["opencode.json", "~/.config/opencode/opencode.json"],
            "notes": "Activation must resolve overlap with the repo-native OpenSpec workflow.",
        }
    ]
    return specs


def artifact_id(url: str, spec: dict[str, Any]) -> str:
    identity = "\0".join((
        url.lower(),
        str(spec.get("kind") or ""),
        str(spec.get("package_manager") or ""),
        str(spec.get("package_name") or ""),
        str(spec.get("mcp_server") or spec.get("plugin_id") or ""),
    ))
    suffix = hashlib.sha256(identity.encode()).hexdigest()[:16]
    return f"candidate-artifact-{suffix}"


def load_receipt_document() -> dict[str, Any]:
    return ReceiptStore(RECEIPTS, RUNTIME_STATE).load()


def load_receipts(payload: dict[str, Any] | None = None) -> dict[str, dict[str, dict[str, Any]]]:
    if payload is None:
        payload = load_receipt_document()
    rows = payload.get("receipts", [])
    if not isinstance(rows, list):
        raise ValueError("runtime activation receipts must be a list")
    result: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("runtime activation receipt rows must be objects")
        candidate_id = str(row.get("artifact_id") or "")
        phase = str(row.get("phase") or "")
        if not candidate_id or not phase:
            raise ValueError("runtime activation receipt requires artifact_id and phase")
        if phase in result.setdefault(candidate_id, {}):
            raise ValueError(f"duplicate runtime receipt: {candidate_id}:{phase}")
        result[candidate_id][phase] = row
    return result


def load_closure_receipts(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = payload.get("closure_receipts", [])
    if not isinstance(rows, list):
        raise ValueError("runtime activation closure receipts must be a list")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("runtime activation closure receipt rows must be objects")
        gate_id = str(row.get("gate_id") or "")
        if not gate_id:
            raise ValueError("runtime activation closure receipt requires gate_id")
        if gate_id in result:
            raise ValueError(f"duplicate runtime activation closure receipt: {gate_id}")
        result[gate_id] = row
    return result


def closure_evidence_errors(gate_id: str, receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    paths = receipt.get("evidence_paths", [])
    digests = receipt.get("evidence_digests", {})
    if not isinstance(paths, list) or not paths or not all(isinstance(value, str) and value for value in paths):
        return [f"{gate_id} requires non-empty evidence_paths"]
    if not isinstance(digests, dict):
        return [f"{gate_id} requires evidence_digests"]
    for relative in paths:
        candidate = (ROOT / relative).resolve()
        try:
            candidate.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"{gate_id} evidence path escapes the repository: {relative}")
            continue
        if not candidate.is_file():
            errors.append(f"{gate_id} evidence path is missing: {relative}")
            continue
        expected = digests.get(relative)
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if expected != actual:
            errors.append(f"{gate_id} evidence digest is stale: {relative}")
    for field in CLOSURE_STATUS_FIELDS[gate_id]:
        if receipt.get(field) != "passed":
            errors.append(f"{gate_id} {field} must be 'passed'")
    if gate_id == "review-closure" and receipt.get("unresolved_actionable_findings"):
        errors.append("review-closure has unresolved actionable findings")
    return errors


def expected_selector_metadata() -> dict[str, dict[str, str]]:
    rows = load_json(MANIFEST_DIR / "promotion-overrides.json").get("overrides", [])
    if not isinstance(rows, list):
        raise ValueError("promotion overrides must be a list")
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("promotion override rows must be objects")
        normalized_url = str(row.get("normalized_url") or "")
        skill_name = str(row.get("skill_name") or "")
        if not normalized_url or not skill_name:
            raise ValueError("promotion override requires normalized_url and skill_name")
        selector_id = f"selector:{normalized_url.lower()}:{skill_name}"
        if selector_id in result:
            raise ValueError(f"duplicate promotion selector: {selector_id}")
        relative_path = f"docs/src/authoring/skills/{skill_name}.mdx"
        authoring_path = ROOT / relative_path
        result[selector_id] = {
            "selector_id": selector_id,
            "normalized_url": normalized_url,
            "skill_name": skill_name,
            "path": relative_path,
            "authoring_sha256": hashlib.sha256(authoring_path.read_bytes()).hexdigest()
            if authoring_path.is_file()
            else "missing",
        }
    return result


def expected_binding_metadata(
    closure_receipt: dict[str, Any] | None = None,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    rows = load_json(MANIFEST_DIR / "promotion-overrides.json").get("overrides", [])
    if not isinstance(rows, list):
        raise ValueError("promotion overrides must be a list")
    result: dict[str, dict[str, Any]] = {}
    harnesses: set[str] = set()
    closure_module = load_catalog_closure_module() if closure_receipt is not None else None
    catalog_by_name = closure_module.catalog_rows_by_name() if closure_module is not None else {}
    harness_assurance = load_json(MANIFEST_DIR / "harness-install-assurance.json")
    sync_report_sha256 = str(harness_assurance.get("source_sha256") or "")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("promotion override rows must be objects")
        normalized_url = str(row.get("normalized_url") or "")
        skill_name = str(row.get("skill_name") or "")
        selector_id = f"selector:{normalized_url.lower()}:{skill_name}"
        target_agents = row.get("target_agents", [])
        if not isinstance(target_agents, list) or not all(isinstance(value, str) and value for value in target_agents):
            raise ValueError(f"promotion selector {selector_id} has invalid target_agents")
        if len(target_agents) != len(set(target_agents)):
            raise ValueError(f"promotion selector {selector_id} has duplicate target_agents")
        current_fields: dict[str, Any] = {}
        if closure_module is not None:
            item = closure_module.selector_graph([row])[selector_id]
            catalog_row = catalog_by_name.get(skill_name)
            capabilities, capability_errors = closure_module.required_capabilities(item, catalog_row)
            authoring_path = ROOT / str(item["path"])
            authoring_sha256 = (
                hashlib.sha256(authoring_path.read_bytes()).hexdigest() if authoring_path.is_file() else ""
            )
            installed_digest, installed_errors = closure_module.current_installed_digest(item)
            current_fields = {
                "required_capabilities": capabilities,
                "installed_digest": installed_digest or "unavailable",
                "_input_ready": not (
                    capability_errors
                    or installed_errors
                    or not authoring_sha256
                    or not _SHA256.fullmatch(sync_report_sha256)
                    or not isinstance(catalog_row, dict)
                ),
                "_item": item,
                "_catalog_row": catalog_row,
                "_authoring_sha256": authoring_sha256,
            }
        for agent in target_agents:
            binding_id = f"binding:{selector_id}:{agent}"
            if binding_id in result:
                raise ValueError(f"duplicate harness binding: {binding_id}")
            metadata: dict[str, Any] = {
                "selector_id": selector_id,
                "normalized_url": normalized_url,
                "skill_name": skill_name,
                "agent": agent,
            }
            if closure_module is not None:
                input_digest = "unavailable"
                if current_fields["_input_ready"]:
                    input_digest = closure_module.binding_input_digest(
                        current_fields["_item"],
                        agent=agent,
                        authoring_sha256=current_fields["_authoring_sha256"],
                        catalog_row=current_fields["_catalog_row"],
                        sync_report_sha256=sync_report_sha256,
                        capabilities=current_fields["required_capabilities"],
                    )
                metadata.update({
                    "input_digest": input_digest,
                    "installed_digest": current_fields["installed_digest"],
                    "required_capabilities": current_fields["required_capabilities"],
                })
            result[binding_id] = metadata
            harnesses.add(agent)
    return result, sorted(harnesses)


def build_closure_gates(
    closure_receipts: dict[str, dict[str, Any]],
    active_blockers: list[dict[str, Any]],
    selector_metadata: dict[str, dict[str, str]] | None = None,
    binding_metadata: dict[str, dict[str, Any]] | None = None,
    target_harnesses: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    selector_metadata = selector_metadata or {}
    binding_metadata = binding_metadata or {}
    target_harnesses = target_harnesses or []
    harness_assurance = load_json(MANIFEST_DIR / "harness-install-assurance.json")
    expected_sync_report_sha256 = str(harness_assurance.get("source_sha256") or "")
    gates: dict[str, dict[str, Any]] = {}
    for gate_id in NON_GLOBAL_CLOSURE_GATES:
        receipt = closure_receipts.get(gate_id)
        context: dict[str, Any] = {}
        producer_receipt: dict[str, Any] | None = None
        producer_errors: list[str] = []
        if gate_id in {"docs-closure", "review-closure"}:
            try:
                producer_receipt = current_producer_closure_receipt(gate_id)
            except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
                producer_errors.append(
                    f"could not reconstruct {gate_id} producer evidence: {type(error).__name__}: {error}"
                )
        if gate_id == "selector-closure":
            context = {
                "expected_leaf_ids": sorted(selector_metadata),
                "expected_leaf_metadata": selector_metadata,
            }
        elif gate_id == "harness-binding-closure":
            context = {
                "expected_leaf_ids": sorted(binding_metadata),
                "expected_leaf_metadata": binding_metadata,
                "target_harnesses": target_harnesses,
                "expected_sync_report_sha256": expected_sync_report_sha256,
            }
        elif gate_id == "review-closure" and producer_receipt is not None:
            context = {
                "expected_reviewed_paths": producer_receipt.get("reviewed_paths"),
                "expected_reviewed_path_digests": producer_receipt.get("reviewed_path_digests"),
                "expected_reviewed_input_digest": producer_receipt.get("reviewed_input_digest"),
                "expected_worktree_digest": producer_receipt.get("worktree_digest"),
            }
        errors = [
            *producer_errors,
            *(
                [f"missing {gate_id} receipt"]
                if receipt is None
                else [
                    *evaluate_predicate(CLOSURE_PREDICATES[gate_id], receipt, context),
                    *closure_evidence_errors(gate_id, receipt),
                ]
            ),
        ]
        if receipt is not None and producer_receipt is not None and receipt != producer_receipt:
            errors.append(f"{gate_id} receipt does not exactly match canonical producer evidence")
        gates[gate_id] = {
            "predicate": CLOSURE_PREDICATES[gate_id],
            "status": "accepted" if not errors else "incomplete",
            "errors": errors,
        }

    global_receipt = closure_receipts.get("global-closure")
    global_errors: list[str] = []
    if global_receipt is None:
        global_errors.append("missing global-closure receipt")
    else:
        declared_values = global_receipt.get("expected_leaf_ids", [])
        if not isinstance(declared_values, list) or not all(isinstance(value, str) for value in declared_values):
            global_errors.append("global-closure expected_leaf_ids must be a string list")
            declared_values = []
        declared = set(declared_values)
        expected = set(NON_GLOBAL_CLOSURE_GATES)
        if declared != expected or len(declared_values) != len(declared):
            global_errors.append("global-closure expected_leaf_ids must exactly name the four prerequisite gates")
        derived = dict(global_receipt)
        derived["expected_leaf_ids"] = list(NON_GLOBAL_CLOSURE_GATES)
        derived["leaf_receipts"] = [
            {
                "node_id": gate_id,
                "status": gates[gate_id]["status"],
                "predicate_errors": gates[gate_id]["errors"],
            }
            for gate_id in NON_GLOBAL_CLOSURE_GATES
        ]
        declared_blockers = global_receipt.get("active_blockers", [])
        if not isinstance(declared_blockers, list):
            global_errors.append("global-closure active_blockers must be a list")
            declared_blockers = ["invalid declared blocker payload"]
        derived["active_blockers"] = [*active_blockers, *declared_blockers]
        global_errors.extend(
            evaluate_predicate(
                "global-closure",
                derived,
                {"expected_leaf_ids": list(NON_GLOBAL_CLOSURE_GATES)},
            )
        )
    gates["global-closure"] = {
        "predicate": "global-closure",
        "status": "accepted" if not global_errors else "incomplete",
        "errors": global_errors,
    }
    return gates


def inspected_source_shas() -> dict[str, str]:
    rows = load_json(MANIFEST_DIR / "all-records.json").get("records", [])
    result: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        url = str(row.get("normalized_url") or "").lower()
        sha = str(row.get("inspected_commit_sha") or "")
        if not url or not sha:
            continue
        if url in result and result[url] != sha:
            raise ValueError(f"conflicting inspected SHAs for {url}")
        result[url] = sha
    return result


def current_install_digest(receipt: dict[str, Any] | None) -> tuple[str | None, list[str]]:
    if receipt is None:
        return None, []
    errors: list[str] = []
    paths = receipt.get("installed_realpaths", [])
    if not isinstance(paths, list) or not paths or not all(isinstance(value, str) and value for value in paths):
        return None, ["install receipt installed_realpaths must be a non-empty string list"]
    if receipt.get("digest_algorithm") != FILESYSTEM_DIGEST_ALGORITHM:
        errors.append("install receipt does not use the current lstat digest algorithm")
    ignored = receipt.get("digest_ignored_dirs", [])
    expected_ignored = sorted(RUNTIME_DIGEST_IGNORED_DIRS)
    if not isinstance(ignored, list) or sorted(ignored) != expected_ignored:
        errors.append("install receipt digest ignore policy does not match the current runtime policy")
    missing = [value for value in paths if not Path(value).exists() and not Path(value).is_symlink()]
    if missing:
        errors.append(f"installed paths are missing: {missing!r}")
    try:
        current = filesystem_digest(paths, ignored_dirs=RUNTIME_DIGEST_IGNORED_DIRS)
    except OSError as error:
        errors.append(f"could not hash current installed paths: {type(error).__name__}")
        current = None
    return current, errors


def _entrypoint_xattr_digest(path: Path) -> str | None:
    executable = Path("/usr/bin/xattr")
    if not executable.is_file():
        return None
    argv = [str(executable), "-lx", str(path)]
    if path.is_symlink():
        argv.insert(1, "-s")
    result = subprocess.run(argv, check=True, capture_output=True)
    return hashlib.sha256(result.stdout).hexdigest()


def _entrypoint_snapshot(path: Path) -> dict[str, Any]:
    metadata = path.lstat()
    common: dict[str, Any] = {
        "mode": stat.S_IMODE(metadata.st_mode),
        "xattrs_sha256": _entrypoint_xattr_digest(path),
    }
    if path.is_symlink():
        return {**common, "kind": "symlink", "target": os.readlink(path)}
    if path.is_file():
        return {
            **common,
            "kind": "file",
            "size": metadata.st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    raise ValueError(f"unsupported activation surface: {path}")


def expected_live_entrypoint_paths(seed: dict[str, Any]) -> list[Path]:
    manager = str(seed.get("package_manager") or "")
    root = (Path.home() / ".cargo/bin" if manager == "cargo" else Path.home() / ".local/bin").resolve()
    names = seed.get("executables", [])
    if not isinstance(names, list) or not names or not all(isinstance(name, str) and name for name in names):
        raise ValueError("entrypoint recovery requires a non-empty executable list")
    if len(set(names)) != len(names) or any(Path(name).name != name or name in {".", ".."} for name in names):
        raise ValueError("entrypoint recovery executable names must be unique basenames")
    return [root / name for name in names]


def current_live_entrypoint_digest(
    receipt: dict[str, Any] | None,
    expected_paths: list[Path],
) -> tuple[str | None, list[str]]:
    if receipt is None:
        return None, []
    errors: list[str] = []
    expected = [str(path) for path in expected_paths]
    recorded = receipt.get("live_entrypoint_paths")
    if recorded != expected:
        errors.append("rollback live_entrypoint_paths do not match the current artifact entrypoints")
    for path in expected_paths:
        if not path.exists() and not path.is_symlink():
            errors.append(f"live entrypoint is missing: {path}")
            continue
        try:
            target = path.resolve(strict=True)
        except OSError:
            errors.append(f"live entrypoint target is missing: {path}")
            continue
        if not target.is_file() or not os.access(target, os.X_OK):
            errors.append(f"live entrypoint is not runnable: {path}")
    try:
        snapshot = {str(path): _entrypoint_snapshot(path) for path in sorted(expected_paths, key=str)}
        encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
        current = hashlib.sha256(encoded).hexdigest()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        errors.append(f"could not hash current live entrypoints: {type(error).__name__}")
        current = None
    return current, errors


def current_live_entrypoint_targets(expected_paths: list[Path]) -> dict[str, str]:
    targets: dict[str, str] = {}
    for path in expected_paths:
        try:
            target = path.resolve(strict=True)
        except OSError:
            continue
        if target.is_file() and os.access(target, os.X_OK):
            targets[path.name] = str(target)
    return targets


def _managed_evidence_bytes(path: Path, *, label: str) -> tuple[bytes | None, list[str]]:
    candidate = Path(os.path.abspath(path.expanduser()))
    root = Path(os.path.abspath(RUNTIME_RECEIPT_ROOT.expanduser()))
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        return None, [f"{label} must be inside the managed candidate receipt root"]
    if not relative.parts:
        return None, [f"{label} must be a managed regular file"]

    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    file_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptors: list[int] = []
    file_descriptor: int | None = None
    try:
        current = os.open(root, directory_flags)
        descriptors.append(current)
        for part in relative.parts[:-1]:
            current = os.open(part, directory_flags, dir_fd=current)
            descriptors.append(current)
        file_descriptor = os.open(relative.name, file_flags, dir_fd=current)
        before = os.fstat(file_descriptor)
        if not stat.S_ISREG(before.st_mode):
            return None, [f"{label} must be a regular file"]
        chunks: list[bytes] = []
        while chunk := os.read(file_descriptor, 1024 * 1024):
            chunks.append(chunk)
        after = os.fstat(file_descriptor)
        stable_fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        if any(getattr(before, field) != getattr(after, field) for field in stable_fields):
            return None, [f"{label} changed while it was being read"]
        return b"".join(chunks), []
    except OSError as error:
        return None, [f"{label} is unavailable: {type(error).__name__}: {error}"]
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def transcript_digest(receipt: dict[str, Any] | None) -> tuple[str | None, list[str]]:
    if receipt is None or not receipt.get("transcript_path"):
        return None, []
    raw_path = Path(str(receipt["transcript_path"])).expanduser()
    if not raw_path.is_absolute():
        return None, ["rollback transcript must be an absolute managed evidence path"]
    candidate = Path(os.path.abspath(raw_path))
    rehearsal_kind = str(receipt.get("rehearsal_kind") or "")
    if rehearsal_kind == "isolated-plugin-root-detach":
        transcript_kind = "candidate-plugin-rollback"
    elif rehearsal_kind == "isolated-entrypoint-root-detach" and "restored_use_launch_path" in receipt:
        transcript_kind = "candidate-mcp-rollback"
    elif rehearsal_kind == "isolated-entrypoint-root-detach" and "restored_use_launch_paths" in receipt:
        transcript_kind = "candidate-non-node-cli-rollback"
    else:
        return None, ["rollback transcript has an unsupported rehearsal shape"]
    artifact_id = receipt.get("artifact_id")
    transaction_id = receipt.get("transaction_id")
    if (
        not isinstance(artifact_id, str)
        or not _SAFE_EVIDENCE_PART.fullmatch(artifact_id)
        or not isinstance(transaction_id, str)
        or not _SAFE_EVIDENCE_PART.fullmatch(transaction_id)
    ):
        return None, ["rollback transcript artifact and transaction ids must be safe path components"]
    expected_path = Path(
        os.path.abspath(RUNTIME_RECEIPT_ROOT / "transcripts" / transcript_kind / f"{artifact_id}-{transaction_id}.json")
    )
    if candidate != expected_path:
        return None, ["rollback transcript path does not match its artifact transaction"]
    transcript_bytes, errors = _managed_evidence_bytes(candidate, label="rollback transcript evidence")
    if transcript_bytes is None:
        return None, errors
    try:
        payload = json.loads(transcript_bytes)
        if not isinstance(payload, dict):
            raise ValueError("transcript must be an object")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return None, [f"rollback transcript is invalid: {type(error).__name__}: {error}"]
    for field in (
        "artifact_id",
        "plugin_id",
        "process_ids",
        "launch_evidence",
        "rehearsal_kind",
        "transaction_id",
        "live_entrypoint_digest",
        "live_entrypoint_unchanged",
        "fresh_absence_process_id",
        "fresh_absence_output_sha256",
        "restored_use_process_id",
        "restored_use_output_sha256",
        "restored_use_launch_paths",
        "restored_use_launch_realpaths",
        "restored_executable_map",
        "restored_use_launch_path",
        "restored_use_launch_realpath",
        "live_install_unchanged",
    ):
        if field in receipt and payload.get(field) != receipt.get(field):
            errors.append(f"rollback transcript {field} does not match the receipt")
    return hashlib.sha256(transcript_bytes).hexdigest(), errors


def journal_digest(
    receipt: dict[str, Any] | None,
    *,
    runtime_kind: str | None = None,
) -> tuple[str | None, list[str]]:
    if receipt is None or not receipt.get("journal_path"):
        return None, []
    candidate = Path(os.path.abspath(Path(str(receipt["journal_path"])).expanduser()))
    allowed_root = Path(os.path.abspath(RUNTIME_RECEIPT_ROOT.expanduser()))
    try:
        candidate.relative_to(allowed_root)
    except ValueError:
        return None, ["rollback journal must be inside the managed candidate receipt root"]
    journal_bytes, journal_read_errors = _managed_evidence_bytes(candidate, label="rollback journal evidence")
    if journal_bytes is None:
        return None, journal_read_errors
    journal_sha256 = hashlib.sha256(journal_bytes).hexdigest()
    try:
        payload = json.loads(journal_bytes)
    except (ValueError, json.JSONDecodeError) as error:
        return None, [f"rollback journal is invalid: {type(error).__name__}: {error}"]
    if not isinstance(payload, dict):
        return None, ["rollback journal must be an object"]
    errors: list[str] = []
    rehearsal_kind = str(receipt.get("rehearsal_kind") or "")
    journal_type: str | None = None
    if rehearsal_kind == "isolated-entrypoint-root-detach":
        if runtime_kind == "mcp":
            journal_type = "mcp"
        elif runtime_kind in {"cli", "library"}:
            journal_type = "cli"
        else:
            errors.append("entrypoint rollback journal has an unsupported runtime kind")
    elif rehearsal_kind == "isolated-plugin-root-detach":
        journal_type = "plugin"

    if journal_type is not None:
        journal_kind = {
            "cli": "candidate-non-node-cli-rollback",
            "mcp": "candidate-mcp-rollback",
            "plugin": "candidate-plugin-rollback",
        }[journal_type]
        expected_journal_status = "commit-pending"
        if payload.get("status") != expected_journal_status:
            errors.append(f"rollback journal status is not {expected_journal_status}")
        journal_transaction_id = receipt.get("journal_transaction_id")
        if not isinstance(journal_transaction_id, str) or not _SAFE_EVIDENCE_PART.fullmatch(journal_transaction_id):
            errors.append("rollback journal transaction id must be a safe path component")
            journal_transaction_id = "invalid"
        expected_path = allowed_root / "journals" / journal_kind / f"{journal_transaction_id}.json"
        if candidate != expected_path:
            errors.append(f"rollback journal path does not match the {journal_type} rehearsal journal")
        if payload.get("version") != 2:
            errors.append("rollback journal version is not 2")
        if payload.get("kind") != journal_type:
            errors.append("rollback journal kind does not match the runtime kind")
        if payload.get("transaction_id") != journal_transaction_id:
            errors.append("rollback journal transaction_id does not match the receipt journal transaction")
        collection = payload.get("artifacts")
        if not isinstance(collection, list) or not all(isinstance(row, dict) for row in collection):
            errors.append("rollback journal artifacts must be an object list")
            matches: list[dict[str, Any]] = []
            journal_artifact_ids: list[str] = []
        else:
            matches = [row for row in collection if row.get("artifact_id") == receipt.get("artifact_id")]
            journal_artifact_ids = [
                str(row["artifact_id"])
                for row in collection
                if isinstance(row.get("artifact_id"), str) and row["artifact_id"]
            ]
            if len(journal_artifact_ids) != len(collection):
                errors.append("rollback journal artifact ids must be nonempty strings")
            if len(journal_artifact_ids) != len(set(journal_artifact_ids)):
                errors.append("rollback journal artifact ids must be unique")

        commit_path = allowed_root / "journals" / f"{journal_kind}-commit" / f"{journal_transaction_id}.json"
        commit_payload: dict[str, Any] | None = None
        commit_bytes, commit_read_errors = _managed_evidence_bytes(
            commit_path,
            label="rollback commit-success marker",
        )
        if commit_bytes is None:
            errors.extend(commit_read_errors)
        else:
            try:
                raw_commit_payload = json.loads(commit_bytes)
                if not isinstance(raw_commit_payload, dict):
                    raise ValueError("commit marker must be an object")
                commit_payload = raw_commit_payload
            except (OSError, ValueError, json.JSONDecodeError) as error:
                errors.append(f"rollback commit-success marker is invalid: {type(error).__name__}: {error}")
            if commit_payload is not None:
                if set(commit_payload) != _SUCCESS_MARKER_FIELDS:
                    errors.append("rollback commit-success marker fields do not match the version 2 contract")
                if commit_payload.get("version") != 2:
                    errors.append("rollback commit-success marker version is not 2")
                if commit_payload.get("status") != "passed":
                    errors.append("rollback commit-success marker status is not passed")
                if commit_payload.get("transaction_id") != journal_transaction_id:
                    errors.append("rollback commit-success marker transaction_id does not match")
                if commit_payload.get("journal_path") != str(candidate):
                    errors.append("rollback commit-success marker journal path does not match")
                if commit_payload.get("journal_sha256") != journal_sha256:
                    errors.append("rollback commit-success marker journal digest does not match")
                receipt_revision = commit_payload.get("receipt_revision")
                if not isinstance(receipt_revision, int) or isinstance(receipt_revision, bool) or receipt_revision < 1:
                    errors.append("rollback commit-success marker receipt revision is invalid")
                receipt_document_sha256 = commit_payload.get("receipt_document_sha256")
                if not isinstance(receipt_document_sha256, str) or not _SHA256.fullmatch(receipt_document_sha256):
                    errors.append("rollback commit-success marker receipt document digest is invalid")
                marker_artifact_ids = commit_payload.get("artifact_ids")
                if (
                    not isinstance(marker_artifact_ids, list)
                    or not all(isinstance(value, str) and value for value in marker_artifact_ids)
                    or marker_artifact_ids != sorted(set(marker_artifact_ids))
                ):
                    errors.append("rollback commit-success marker artifact ids must be sorted and unique")
                else:
                    if marker_artifact_ids != sorted(set(journal_artifact_ids)):
                        errors.append("rollback commit-success marker artifact ids do not match the journal")
                    if receipt.get("artifact_id") not in marker_artifact_ids:
                        errors.append("rollback commit-success marker omits the receipt artifact")
                marker_store_transaction = commit_payload.get("receipt_store_transaction_id")
                receipt_store_transaction = receipt.get("store_transaction_id")
                if not isinstance(marker_store_transaction, str) or not marker_store_transaction:
                    errors.append("rollback commit-success marker receipt-store transaction is invalid")
                if not isinstance(receipt_store_transaction, str) or not receipt_store_transaction:
                    errors.append("rollback receipt store transaction is missing")
                elif marker_store_transaction != receipt_store_transaction:
                    errors.append("rollback commit-success marker receipt-store transaction does not match")
        if len(matches) != 1:
            errors.append("rollback journal must contain exactly one record for the receipt artifact")
        else:
            record = matches[0]
            if record.get("status") != "passed":
                errors.append("rollback journal artifact status is not passed")
            if record.get("transaction_id") != receipt.get("transaction_id"):
                errors.append("rollback journal transaction_id does not match the receipt")

            if journal_type in {"cli", "mcp"}:
                field_map = {
                    "artifact_id": "artifact_id",
                    "rehearsal_kind": "rehearsal_kind",
                    "live_entrypoint_paths": "live_entrypoints",
                    "live_entrypoint_digest": "live_entrypoint_digest",
                    "live_entrypoint_unchanged": "live_entrypoint_unchanged",
                    "preimage_digest": "preimage_digest",
                    "rollback_digest": "rollback_digest",
                    "fresh_absence_process_id": "fresh_absence_process_id",
                    "fresh_absence_output_sha256": "fresh_absence_output_sha256",
                    "restored_use_process_id": (
                        "restored_process_id" if journal_type == "mcp" else "restored_use_process_id"
                    ),
                    "restored_use_output_sha256": (
                        "restored_output_sha256" if journal_type == "mcp" else "restored_use_output_sha256"
                    ),
                    "transcript_path": "transcript_path",
                    "transcript_sha256": "transcript_sha256",
                }
                if journal_type == "cli":
                    field_map.update({
                        "restored_use_launch_paths": "restored_use_launch_paths",
                        "restored_use_launch_realpaths": "restored_use_launch_realpaths",
                        "restored_executable_map": "restored_executable_map",
                    })
                else:
                    field_map.update({
                        "restored_use_launch_path": "restored_use_launch_path",
                        "restored_use_launch_realpath": "restored_use_launch_realpath",
                    })
            else:
                field_map = {
                    "artifact_id": "artifact_id",
                    "plugin_id": "plugin_id",
                    "plugin_scope": "plugin_scope",
                    "scope": "scope",
                    "rehearsal_kind": "rehearsal_kind",
                    "preimage_digest": "preimage_digest",
                    "rollback_digest": "rollback_digest",
                    "promoted_final_digest": "promoted_final_digest",
                    "fresh_absence_process_id": "fresh_absence_process_id",
                    "restored_use_process_id": "restored_use_process_id",
                    "restored_use_output_sha256": "restored_use_output_sha256",
                    "restored_installed_digest": "restored_installed_digest",
                    "restored_use_status": "restored_use_status",
                    "live_install_unchanged": "live_install_unchanged",
                    "process_ids": "process_ids",
                    "launch_evidence": "launch_evidence",
                    "transcript_path": "transcript_path",
                    "transcript_sha256": "transcript_sha256",
                }
            for receipt_field, journal_field in field_map.items():
                if receipt.get(receipt_field) != record.get(journal_field):
                    errors.append(f"rollback journal {journal_field} does not match the receipt")

    return journal_sha256, errors


def canonical_runtime_ids(specs: dict[str, list[dict[str, Any]]]) -> list[str]:
    return sorted(artifact_id(url, seed) for url, rows in specs.items() for seed in rows)


def projected_mcp_enabled(entry: dict[str, Any] | None) -> bool:
    return isinstance(entry, dict) and entry.get("enabled") is not False


def mcp_activation_errors(
    server_id: str,
    registry_entry: dict[str, Any] | None,
    generated_entry: dict[str, Any] | None,
    live_entry: dict[str, Any] | None,
    receipt: dict[str, Any] | None,
    *,
    freshness_context: dict[str, Any] | None = None,
) -> tuple[list[str], bool]:
    errors: list[str] = []
    registry_enabled = isinstance(registry_entry, dict) and registry_entry.get("enabled") is True
    generated_enabled = projected_mcp_enabled(generated_entry)
    live_enabled = projected_mcp_enabled(live_entry)
    if not registry_enabled:
        errors.append("MCP server is not enabled in config/mcp-registry.json")
    if not generated_enabled:
        errors.append("MCP server is not enabled in generated MCPHub settings")
    if not live_enabled:
        errors.append("MCP server is not enabled in the live MCPHub settings")
    reachable = False
    if registry_enabled and generated_enabled and live_enabled:
        assert isinstance(registry_entry, dict)
        assert isinstance(generated_entry, dict)
        assert isinstance(live_entry, dict)
        registry_projection = normalized_projection(registry_entry, registry=True)
        generated_projection = normalized_projection(generated_entry, registry=False)
        live_projection = normalized_projection(live_entry, registry=False)
        if registry_projection != generated_projection or generated_projection != live_projection:
            errors.append("MCP registry, generated, and live projections do not match")
        configured_tool_names, configured_tools_allow_all = configured_tools(registry_entry)
        expected_exposed_tool_names = mcphub_exposed_tool_names(server_id, configured_tool_names)
        if receipt is None:
            errors.append("current MCPHub reachability receipt is missing")
        else:
            if receipt.get("status") != "passed":
                errors.append("MCPHub reachability receipt status is not passed")
            if receipt.get("phase") != "activation":
                errors.append("MCPHub reachability receipt has the wrong phase")
            if receipt.get("mcp_server") != server_id:
                errors.append("MCPHub reachability receipt names the wrong server")
            for field in ("registry_enabled", "generated_enabled", "live_enabled", "mcphub_reachable"):
                if receipt.get(field) is not True:
                    errors.append(f"MCPHub reachability receipt {field} is not true")
            endpoint = receipt.get("endpoint")
            expected_endpoint = f"http://127.0.0.1:46683/mcp/{server_id}"
            if endpoint != expected_endpoint:
                errors.append("MCPHub reachability receipt endpoint is not the managed local endpoint")
            for field, entry in (
                ("registry_entry_sha256", registry_entry),
                ("generated_entry_sha256", generated_entry),
                ("live_entry_sha256", live_entry),
            ):
                if receipt.get(field) != canonical_json_sha256(entry):
                    errors.append(f"MCPHub reachability receipt {field} is stale")
            for field, projection in (
                ("registry_projection_sha256", registry_projection),
                ("generated_projection_sha256", generated_projection),
                ("live_projection_sha256", live_projection),
            ):
                if receipt.get(field) != canonical_json_sha256(projection):
                    errors.append(f"MCPHub reachability receipt {field} is stale")
            if receipt.get("configured_tool_names") != configured_tool_names:
                errors.append("MCPHub reachability receipt configured_tool_names is stale")
            if receipt.get("configured_tool_names_sha256") != canonical_json_sha256(configured_tool_names):
                errors.append("MCPHub reachability receipt configured_tool_names_sha256 is stale")
            if receipt.get("configured_tools_allow_all") is not configured_tools_allow_all:
                errors.append("MCPHub reachability receipt configured_tools_allow_all is stale")
            tool_names = receipt.get("tool_names")
            if (
                not isinstance(tool_names, list)
                or not tool_names
                or not all(isinstance(value, str) and value for value in tool_names)
                or tool_names != sorted(set(tool_names))
            ):
                errors.append("MCPHub reachability receipt tool_names must be a nonempty sorted unique list")
            else:
                if receipt.get("tool_count") != len(tool_names):
                    errors.append("MCPHub reachability receipt tool_count is stale")
                if receipt.get("tool_names_sha256") != canonical_json_sha256(tool_names):
                    errors.append("MCPHub reachability receipt tool_names_sha256 is stale")
                if not configured_tools_allow_all and not set(expected_exposed_tool_names).issubset(tool_names):
                    errors.append("MCPHub reachability receipt omits configured tools")
            if receipt.get("bearer_auth_used") is not True:
                errors.append("MCPHub reachability receipt did not prove bearer authentication")
            if receipt.get("mcphub_bearer_key_configured") is not True:
                errors.append("MCPHub reachability receipt did not prove a configured bearer key")
            if receipt.get("unauthenticated_denied") is not True:
                errors.append("MCPHub reachability receipt did not prove unauthenticated denial")
            if receipt.get("unauthenticated_status_code") not in {401, 403}:
                errors.append("MCPHub reachability receipt has an invalid unauthenticated status code")
            if receipt.get("network_probe_performed") is not True:
                errors.append("MCPHub reachability receipt did not prove a network probe")
            if receipt.get("secret_value_recorded") is not False:
                errors.append("MCPHub reachability receipt must not record secret values")
            if freshness_context is not None:
                errors.extend(evaluate_predicate("receipt-fresh", receipt, freshness_context))
            reachable = not errors
    return errors, reachable


def build_assurance() -> dict[str, Any]:
    specs = runtime_specs()
    plugin_provenance_entries = load_plugin_provenance_lock(PLUGIN_PROVENANCE_LOCK)
    enabled_plugin_ids = {
        str(seed.get("plugin_id") or "")
        for rows in specs.values()
        for seed in rows
        if seed.get("kind") == "plugin" and seed.get("plugin_enabled") is True
    }
    if set(plugin_provenance_entries) != enabled_plugin_ids:
        raise ValueError(
            "plugin provenance lock coverage drifted: "
            f"expected {sorted(enabled_plugin_ids)}, found {sorted(plugin_provenance_entries)}"
        )
    generated_at = now()
    receipt_document = load_receipt_document()
    receipts = load_receipts(receipt_document)
    closure_receipts = load_closure_receipts(receipt_document)
    source_shas = inspected_source_shas()
    source_targets = load_json(MANIFEST_DIR / "integration-targets.json").get("items", [])
    source_by_url = {
        str(item.get("normalized_url") or "").lower(): item for item in source_targets if isinstance(item, dict)
    }
    registry_servers = load_json(MCP_REGISTRY).get("servers", {})
    generated_servers = load_json(MCPHUB_SETTINGS).get("mcpServers", {})
    live_servers = load_json(MCPHUB_LIVE_SETTINGS).get("mcpServers", {}) if MCPHUB_LIVE_SETTINGS.is_file() else {}
    if (
        not isinstance(registry_servers, dict)
        or not isinstance(generated_servers, dict)
        or not isinstance(live_servers, dict)
    ):
        raise ValueError("MCP registry and generated MCPHub settings must contain server objects")
    artifacts: list[dict[str, Any]] = []
    for url, rows in sorted(specs.items()):
        source = source_by_url.get(url.lower(), {})
        for seed in rows:
            candidate_id = artifact_id(url, seed)
            phase_rows = receipts.get(candidate_id, {})
            install_receipt = phase_rows.get("install")
            installed_digest = str((install_receipt or {}).get("installed_digest") or "")
            live_installed_digest, live_install_errors = current_install_digest(install_receipt)
            current_digest = str(live_installed_digest or "unavailable")
            package_id = f"{seed.get('package_manager')}:{seed.get('package_name')}"
            source_commit_sha = str(seed.get("source_commit_sha") or source_shas.get(url.lower()) or "")
            resolved_version = str(seed.get("version") or "")
            phase_results: dict[str, Any] = {}
            provenance: dict[str, Any] | None = None
            provenance_errors: list[str] = []
            if seed.get("kind") == "mcp" and seed.get("package_manager") != "hosted":
                try:
                    provenance = package_manager_provenance(
                        seed,
                        runtime_state=RUNTIME_STATE,
                        uv_tools=UV_TOOLS,
                    )
                except (OSError, ValueError, json.JSONDecodeError) as error:
                    provenance_errors.append(f"{type(error).__name__}: {error}")
            plugin_provenance: dict[str, Any] | None = None
            plugin_provenance_errors: list[str] = []
            plugin_source_content_sha256: str | None = None
            plugin_installed_content_sha256: str | None = None
            plugin_origin: dict[str, Any] | None = None
            plugin_live_state: dict[str, Any] | None = None
            if seed.get("kind") == "plugin" and seed.get("plugin_enabled") is True:
                try:
                    plugin_id = str(seed["plugin_id"])
                    plugin_provenance = plugin_provenance_entries[plugin_id]
                    if plugin_provenance["normalized_url"].lower() != url.lower():
                        raise ValueError("plugin provenance lock URL drifted")
                    if plugin_provenance["resolved_version"] != resolved_version:
                        raise ValueError("plugin provenance lock version drifted")
                    if plugin_provenance["audited_source_commit_sha"] != source_commit_sha:
                        raise ValueError("plugin provenance lock audited commit drifted")
                    marketplace = str(plugin_provenance["marketplace"])
                    source_root = resolve_locked_marketplace_source(
                        PLUGIN_MARKETPLACE_ROOTS[marketplace],
                        plugin_provenance,
                    )
                    plugin_source_content_sha256 = verify_plugin_content(
                        source_root,
                        plugin_provenance,
                        label=f"marketplace source for {plugin_id}",
                    )
                    plugin_live_state = codex_plugin_live_state(
                        CODEX_CONFIG,
                        CODEX_PLUGIN_CACHE,
                        plugin_provenance,
                    )
                    if plugin_live_state["plugin_id"] != plugin_id:
                        raise ValueError("live Codex plugin id drifted")
                    if plugin_live_state["version"] != resolved_version:
                        raise ValueError("live Codex plugin version drifted")
                    if plugin_live_state["enabled"] is not True:
                        raise ValueError("live Codex plugin is disabled")
                    if plugin_live_state["installed"] is not True:
                        raise ValueError("live Codex plugin cache is missing")
                    live_root = Path(str(plugin_live_state["installed_path"]))
                    plugin_installed_content_sha256 = verify_plugin_content(
                        live_root,
                        plugin_provenance,
                        label=f"live install for {plugin_id}",
                    )
                    plugin_origin = plugin_installed_package_origin(
                        plugin_provenance,
                        source_content_sha256=plugin_source_content_sha256,
                        installed_content_sha256=plugin_installed_content_sha256,
                    )
                except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
                    plugin_provenance_errors.append(f"{type(error).__name__}: {error}")
            phase_errors: list[str] = [
                *[f"package-provenance: {error}" for error in provenance_errors],
                *[f"plugin-provenance: {error}" for error in plugin_provenance_errors],
            ]
            for phase, predicate_id in PHASE_PREDICATES:
                receipt = phase_rows.get(phase)
                context: dict[str, Any] = {}
                if phase == "identity":
                    context = {
                        "expected_package_id": package_id,
                        "expected_source_commit_sha": source_commit_sha,
                        "expected_resolved_version": seed.get("version"),
                    }
                    if seed.get("kind") == "mcp" and seed.get("package_manager") != "hosted":
                        context["require_installed_package_origin"] = True
                        if provenance is not None:
                            context["expected_integrity"] = provenance["integrity"]
                            context["expected_installed_package_origin"] = provenance["origin_digest"]
                    elif seed.get("kind") == "plugin" and seed.get("plugin_enabled") is True:
                        context["require_installed_package_origin"] = True
                        context["require_plugin_provenance"] = True
                        if plugin_provenance is not None and plugin_origin is not None:
                            context.update({
                                "expected_integrity": (
                                    f"plugin-content-sha256:{plugin_provenance['approved_content_sha256']}"
                                ),
                                "expected_installed_package_origin": plugin_origin["origin_digest"],
                                "expected_audited_source_commit_sha": plugin_provenance["audited_source_commit_sha"],
                                "expected_provenance_lock_entry_sha256": plugin_lock_entry_sha256(plugin_provenance),
                                "expected_approved_content_sha256": plugin_provenance["approved_content_sha256"],
                                "expected_source_content_sha256": plugin_source_content_sha256,
                                "expected_installed_content_sha256": plugin_installed_content_sha256,
                                "expected_content_digest_algorithm": PLUGIN_CONTENT_DIGEST_ALGORITHM,
                                "expected_content_digest_ignored_dirs": list(PLUGIN_CONTENT_IGNORED_DIRS),
                                "expected_plugin_inventory_enabled": True,
                                "expected_plugin_inventory_plugin_id": plugin_id,
                                "expected_plugin_inventory_version": resolved_version,
                                "current_plugin_inventory_enabled": plugin_live_state["enabled"]
                                if plugin_live_state is not None
                                else None,
                                "current_plugin_inventory_plugin_id": plugin_live_state["plugin_id"]
                                if plugin_live_state is not None
                                else None,
                                "current_plugin_inventory_version": plugin_live_state["version"]
                                if plugin_live_state is not None
                                else None,
                            })
                    elif seed.get("integrity"):
                        context["expected_integrity"] = seed["integrity"]
                elif phase == "install":
                    context = {
                        "current_installed_digest": live_installed_digest,
                        "expected_digest_algorithm": FILESYSTEM_DIGEST_ALGORITHM,
                        "expected_digest_ignored_dirs": sorted(RUNTIME_DIGEST_IGNORED_DIRS),
                    }
                    if seed.get("kind") == "plugin" and seed.get("plugin_enabled") is True:
                        context["require_plugin_provenance"] = True
                        if plugin_provenance is not None:
                            context.update({
                                "expected_provenance_lock_entry_sha256": plugin_lock_entry_sha256(plugin_provenance),
                                "expected_approved_content_sha256": plugin_provenance["approved_content_sha256"],
                                "current_installed_content_sha256": plugin_installed_content_sha256,
                                "expected_content_digest_algorithm": PLUGIN_CONTENT_DIGEST_ALGORITHM,
                                "expected_content_digest_ignored_dirs": list(PLUGIN_CONTENT_IGNORED_DIRS),
                            })
                elif phase in {"behavior", "fresh_process"}:
                    context = {"expected_installed_digest": installed_digest}
                    if phase == "behavior" and seed.get("kind") == "mcp":
                        context["require_distinct_negative_evidence"] = True
                elif phase == "rollback":
                    current_transcript_sha256, transcript_errors = transcript_digest(receipt)
                    current_journal_sha256, journal_errors = journal_digest(
                        receipt,
                        runtime_kind=str(seed.get("kind") or ""),
                    )
                    entrypoint_rehearsal_managers = {
                        "cargo",
                        "go",
                        "skill-bundled",
                        "standalone",
                        "uv-tool",
                        "uv-tool-git",
                    }
                    require_entrypoint_recovery = (
                        seed.get("kind") == "mcp" or seed.get("package_manager") in entrypoint_rehearsal_managers
                    )
                    live_entrypoint_errors: list[str] = []
                    current_live_entrypoint_sha256: str | None = None
                    expected_entrypoints: list[str] = []
                    expected_entrypoint_targets: dict[str, str] = {}
                    if require_entrypoint_recovery and receipt is not None:
                        try:
                            expected_paths = expected_live_entrypoint_paths(seed)
                        except ValueError as error:
                            live_entrypoint_errors.append(str(error))
                        else:
                            expected_entrypoints = [str(path) for path in expected_paths]
                            expected_entrypoint_targets = current_live_entrypoint_targets(expected_paths)
                            current_live_entrypoint_sha256, live_entrypoint_errors = current_live_entrypoint_digest(
                                receipt,
                                expected_paths,
                            )
                    context = {
                        "expected_promoted_final_digest": installed_digest,
                        "require_entrypoint_recovery": require_entrypoint_recovery,
                        "require_restored_use": seed.get("kind") == "plugin",
                        "expected_plugin_id": seed.get("plugin_id"),
                        "expected_plugin_scope": "user-global-codex",
                        "expected_rehearsal_kind": (
                            "isolated-plugin-root-detach"
                            if seed.get("kind") == "plugin"
                            else "isolated-entrypoint-root-detach"
                        ),
                        "current_transcript_sha256": current_transcript_sha256,
                        "current_journal_sha256": current_journal_sha256,
                        "expected_live_entrypoint_paths": expected_entrypoints,
                        "expected_live_entrypoint_targets": expected_entrypoint_targets,
                        "expected_entrypoint_recovery_kind": ("mcp" if seed.get("kind") == "mcp" else "cli"),
                        "current_live_entrypoint_digest": current_live_entrypoint_sha256,
                    }
                errors = (
                    [f"missing {phase} receipt"]
                    if receipt is None
                    else evaluate_predicate(predicate_id, receipt, context)
                )
                if phase == "install":
                    errors.extend(live_install_errors)
                if phase == "rollback" and receipt is not None:
                    errors.extend(transcript_errors)
                    errors.extend(journal_errors)
                    errors.extend(live_entrypoint_errors)
                if receipt is not None:
                    expected_input_digest = receipt_input_digest(
                        artifact_id=candidate_id,
                        phase=phase,
                        source_commit_sha=source_commit_sha,
                        package_id=package_id,
                        resolved_version=resolved_version,
                        installed_digest=current_digest,
                    )
                    errors.extend(
                        evaluate_predicate(
                            "receipt-fresh",
                            receipt,
                            {
                                "source_commit_sha": source_commit_sha,
                                "input_digest": expected_input_digest,
                                "predicate_version": RUNTIME_PREDICATE_VERSION,
                                "now": generated_at,
                                "ttl_seconds": 86_400,
                            },
                        )
                    )
                phase_results[phase] = {
                    "predicate": predicate_id,
                    "status": "accepted" if not errors else "incomplete",
                    "errors": errors,
                }
                phase_errors.extend(f"{phase}: {error}" for error in errors)

            auth_names = sorted({str(value) for value in seed.get("auth_env_names", [])})
            auth_required = seed.get("auth_required") is True
            if auth_required:
                auth_receipt = phase_rows.get("auth")
                auth_context = {
                    "expected_auth_required": True,
                    "expected_auth_mode": seed.get("auth_mode"),
                    "expected_auth_provider": seed.get("auth_provider"),
                    "expected_storage_backend": seed.get("auth_storage_backend"),
                    "expected_env_names": auth_names,
                    "expected_minimum_scopes": seed.get("minimum_scopes", []),
                }
                auth_errors = (
                    ["missing auth receipt"]
                    if auth_receipt is None
                    else evaluate_predicate("auth", auth_receipt, auth_context)
                )
                if auth_receipt is not None:
                    auth_errors.extend(
                        evaluate_predicate(
                            "receipt-fresh",
                            auth_receipt,
                            {
                                "source_commit_sha": source_commit_sha,
                                "input_digest": receipt_input_digest(
                                    artifact_id=candidate_id,
                                    phase="auth",
                                    source_commit_sha=source_commit_sha,
                                    package_id=package_id,
                                    resolved_version=resolved_version,
                                    installed_digest=current_digest,
                                ),
                                "predicate_version": RUNTIME_PREDICATE_VERSION,
                                "now": generated_at,
                                "ttl_seconds": 86_400,
                            },
                        )
                    )
                phase_results["auth"] = {
                    "predicate": "auth",
                    "status": "accepted" if not auth_errors else "incomplete",
                    "errors": auth_errors,
                }
                phase_errors.extend(f"auth: {error}" for error in auth_errors)

            plugin_enabled = (
                plugin_live_state.get("enabled")
                if seed.get("kind") == "plugin" and plugin_live_state is not None
                else (False if seed.get("kind") == "plugin" else None)
            )
            mcp_enabled = None
            mcp_generated_enabled = None
            mcp_live_enabled = None
            mcp_reachable = None
            if seed.get("kind") == "plugin" and plugin_enabled is not True:
                activation_errors = ["plugin is not enabled in the target harness"]
                phase_results["activation_policy"] = {
                    "predicate": "plugin-enabled",
                    "status": "incomplete",
                    "errors": activation_errors,
                }
                phase_errors.extend(f"activation-policy: {error}" for error in activation_errors)
            elif seed.get("kind") == "mcp":
                server_id = str(seed.get("mcp_server") or "")
                registry_entry = registry_servers.get(server_id)
                generated_entry = generated_servers.get(server_id)
                live_entry = live_servers.get(server_id)
                mcp_enabled = isinstance(registry_entry, dict) and registry_entry.get("enabled") is True
                mcp_generated_enabled = projected_mcp_enabled(
                    generated_entry if isinstance(generated_entry, dict) else None
                )
                mcp_live_enabled = projected_mcp_enabled(live_entry if isinstance(live_entry, dict) else None)
                activation_errors, mcp_reachable = mcp_activation_errors(
                    server_id,
                    registry_entry if isinstance(registry_entry, dict) else None,
                    generated_entry if isinstance(generated_entry, dict) else None,
                    live_entry if isinstance(live_entry, dict) else None,
                    phase_rows.get("activation"),
                    freshness_context={
                        "source_commit_sha": source_commit_sha,
                        "input_digest": receipt_input_digest(
                            artifact_id=candidate_id,
                            phase="activation",
                            source_commit_sha=source_commit_sha,
                            package_id=package_id,
                            resolved_version=resolved_version,
                            installed_digest=current_digest,
                        ),
                        "predicate_version": RUNTIME_PREDICATE_VERSION,
                        "now": generated_at,
                        "ttl_seconds": 86_400,
                    },
                )
                phase_results["activation_policy"] = {
                    "predicate": "mcp-enabled-and-mcphub-reachable",
                    "status": "accepted" if not activation_errors else "incomplete",
                    "errors": activation_errors,
                }
                phase_errors.extend(f"activation-policy: {error}" for error in activation_errors)

            artifacts.append({
                "artifact_id": candidate_id,
                "normalized_url": str(source.get("normalized_url") or url),
                "raw_indexes": source.get("raw_indexes", []),
                "kind": seed.get("kind"),
                "package_manager": seed.get("package_manager"),
                "package_name": seed.get("package_name"),
                "resolved_version": seed.get("version"),
                "entrypoints": sorted(
                    set(
                        [str(value) for value in seed.get("executables", [])]
                        + [str(seed.get("mcp_server") or "")]
                        + [str(seed.get("plugin_id") or "")]
                    )
                    - {""}
                ),
                "auth_env_names": auth_names,
                "auth_required": auth_required,
                "auth_mode": str(seed.get("auth_mode") or ("environment" if auth_required else "optional")),
                "plugin_enabled": plugin_enabled,
                "mcp_enabled": mcp_enabled,
                "mcp_generated_enabled": mcp_generated_enabled,
                "mcp_live_enabled": mcp_live_enabled,
                "mcp_reachable": mcp_reachable,
                "installed_package_origin": plugin_origin if seed.get("kind") == "plugin" else provenance,
                "phase_results": phase_results,
                "status": "accepted" if not phase_errors else "incomplete",
                "errors": phase_errors,
            })

    status_counts = Counter(str(item["status"]) for item in artifacts)
    kind_counts = Counter(str(item["kind"]) for item in artifacts)
    active_blockers = [
        {
            "artifact_id": item["artifact_id"],
            "normalized_url": item["normalized_url"],
            "errors": item["errors"],
        }
        for item in artifacts
        if item["status"] != "accepted"
    ]
    selector_metadata = expected_selector_metadata()
    binding_metadata, target_harnesses = expected_binding_metadata(closure_receipts.get("harness-binding-closure"))
    closure_gates = build_closure_gates(
        closure_receipts,
        active_blockers,
        selector_metadata,
        binding_metadata,
        target_harnesses,
    )
    closure_status_counts = Counter(str(item["status"]) for item in closure_gates.values())
    complete = (
        len(source_by_url) == EXPECTED_TARGET_COUNT
        and len(artifacts) == EXPECTED_RUNTIME_COUNT
        and dict(sorted(kind_counts.items())) == EXPECTED_KIND_COUNTS
        and not active_blockers
        and all(item["status"] == "accepted" for item in closure_gates.values())
    )
    return {
        "version": 1,
        "generated_at": generated_at,
        "assurance_kind": "candidate-runtime-activation",
        "requested_full_usability": complete,
        "source_target_count": len(source_by_url),
        "runtime_artifact_count": len(artifacts),
        "minimum_runtime_artifact_count": EXPECTED_RUNTIME_COUNT,
        "expected_runtime_artifact_count": EXPECTED_RUNTIME_COUNT,
        "canonical_runtime_artifact_ids": canonical_runtime_ids(specs),
        "artifacts": artifacts,
        "closure_gates": closure_gates,
        "totals": {
            "status_counts": dict(sorted(status_counts.items())),
            "kind_counts": dict(sorted(kind_counts.items())),
            "closure_gate_status_counts": dict(sorted(closure_status_counts.items())),
            "active_blocker_count": len(active_blockers),
        },
        "active_blockers": active_blockers,
        "notes": (
            "This activation ledger fails closed. Historical path/config/dry-run evidence is not imported as an "
            "accepted runtime receipt."
        ),
    }


def structural_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("source_target_count") != EXPECTED_TARGET_COUNT:
        errors.append("activation assurance must cover 289 normalized targets")
    if payload.get("minimum_runtime_artifact_count") != EXPECTED_RUNTIME_COUNT:
        errors.append("activation assurance minimum runtime artifact count must be 65")
    artifacts = payload.get("artifacts", [])
    if not isinstance(artifacts, list) or len(artifacts) != EXPECTED_RUNTIME_COUNT:
        errors.append("activation assurance must contain exactly 65 runtime artifacts")
        return errors
    ids = [str(item.get("artifact_id") or "") for item in artifacts if isinstance(item, dict)]
    if len(ids) != len(set(ids)) or any(not value for value in ids):
        errors.append("runtime artifact IDs must be non-empty and unique")
    expected_ids = canonical_runtime_ids(runtime_specs())
    if sorted(ids) != expected_ids or payload.get("canonical_runtime_artifact_ids") != expected_ids:
        errors.append("runtime artifact IDs do not exactly match the canonical inventory")
    kind_counts = Counter(str(item.get("kind") or "") for item in artifacts if isinstance(item, dict))
    if dict(sorted(kind_counts.items())) != EXPECTED_KIND_COUNTS:
        errors.append("runtime artifact kinds must exactly match 30 CLI, 1 library, 17 MCP, and 17 plugin")
    accepted = sum(1 for item in artifacts if item.get("status") == "accepted")
    if payload.get("requested_full_usability") is True and accepted != len(artifacts):
        errors.append("full usability cannot be true with incomplete artifacts")
    if payload.get("requested_full_usability") is True and payload.get("active_blockers"):
        errors.append("full usability cannot be true with active blockers")
    closure_gates = payload.get("closure_gates")
    if not isinstance(closure_gates, dict) or set(closure_gates) != set(REQUIRED_CLOSURE_GATES):
        errors.append("activation assurance must contain exactly the five required closure gates")
    elif payload.get("requested_full_usability") is True and any(
        not isinstance(gate, dict) or gate.get("status") != "accepted" or gate.get("errors")
        for gate in closure_gates.values()
    ):
        errors.append("full usability cannot be true with incomplete closure gates")
    expected_complete = (
        len(artifacts) == EXPECTED_RUNTIME_COUNT
        and sorted(ids) == expected_ids
        and dict(sorted(kind_counts.items())) == EXPECTED_KIND_COUNTS
        and accepted == len(artifacts)
        and not payload.get("active_blockers")
        and isinstance(closure_gates, dict)
        and set(closure_gates) == set(REQUIRED_CLOSURE_GATES)
        and all(
            isinstance(gate, dict) and gate.get("status") == "accepted" and not gate.get("errors")
            for gate in closure_gates.values()
        )
    )
    if payload.get("requested_full_usability") is not expected_complete:
        errors.append("requested_full_usability does not match artifact and closure-gate evidence")
    return errors


def canonical_payload(payload: dict[str, Any]) -> str:
    stable = dict(payload)
    stable.pop("generated_at", None)
    return json.dumps(stable, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()

    payload = build_assurance()
    errors = structural_errors(payload)
    if args.check:
        if not OUTPUT.is_file():
            errors.append(f"stored activation assurance is missing: {OUTPUT}")
        elif canonical_payload(load_json(OUTPUT)) != canonical_payload(payload):
            errors.append("stored activation assurance is stale; run with --apply")
    if args.apply:
        OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    summary = {
        "ok": not errors,
        "requested_full_usability": payload.get("requested_full_usability"),
        "source_target_count": payload.get("source_target_count"),
        "runtime_artifact_count": payload.get("runtime_artifact_count"),
        "totals": payload.get("totals"),
        "structural_errors": errors,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    if errors or (args.require_complete and payload.get("requested_full_usability") is not True):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
