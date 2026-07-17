#!/usr/bin/env python3
"""Build fail-closed runtime activation state for the July 2026 corpus."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from wagents.candidate_predicates import evaluate_predicate

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
OUTPUT = MANIFEST_DIR / "runtime-activation-assurance.json"
RECEIPTS = MANIFEST_DIR / "runtime-activation-receipts.json"
LEGACY_SCRIPT = ROOT / "scripts" / "record_candidate_non_skill_assurance.py"
EXPECTED_TARGET_COUNT = 289
EXPECTED_RUNTIME_FLOOR = 65
PHASE_PREDICATES = (
    ("identity", "package-identity"),
    ("install", "install-receipt"),
    ("behavior", "behavior-probe"),
    ("fresh_process", "fresh-process"),
    ("rollback", "rollback"),
)


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
    return {
        str(url): [dict(item) for item in rows]
        for url, rows in module.RUNTIME_SPECS.items()
    }


def runtime_specs() -> dict[str, list[dict[str, Any]]]:
    specs = load_legacy_specs()
    agentkits_url = "https://github.com/aitytech/agentkits-marketing"
    specs[agentkits_url].append(
        {
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
        }
    )
    openspec_mcp_url = "https://github.com/lumiaqian/openspec-mcp"
    specs[openspec_mcp_url][0]["executables"] = ["openspec-mcp"]
    prompt_to_asset_url = "https://github.com/mohamedabdallah-14/prompt-to-asset"
    prompt_mcp = next(item for item in specs[prompt_to_asset_url] if item.get("kind") == "mcp")
    prompt_mcp["auth_env_names"] = sorted(
        {*prompt_mcp.get("auth_env_names", []), "HORDE_API_KEY"}
    )
    specs["https://github.com/openags/paper-search-mcp"][0]["auth_env_names"] = [
        "PAPER_SEARCH_MCP_CORE_API_KEY",
        "PAPER_SEARCH_MCP_SEMANTIC_SCHOLAR_API_KEY",
        "PAPER_SEARCH_MCP_UNPAYWALL_EMAIL",
        "PAPER_SEARCH_MCP_ZENODO_ACCESS_TOKEN",
    ]
    specs["https://github.com/antvis/mcp-server-chart"][0]["auth_env_names"] = []

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
                "sha512-fYfRUZGMztcxiJGqOT+ELgHzH74HeGu04jm4IjlSmiKkjjvD+"
                "tLk17GRiI5QcUweMz8RKQWXmcBy6Kj9rHa4Fg=="
            ),
        },
        "https://github.com/tanstack/cli": {
            "version": "0.69.6",
            "source_commit_sha": "d7818c3dc0736a3af1e6878ede0f7aaa25e4d34f",
            "integrity": (
                "sha512-Q8Uw54Yrp6Tr9niPBxUkPe35cwC2vLZdduCNtOWRwsbzd2/1"
                "ApJHen5OufDaiRvHiQKD4xuCw2Q/3TYpKfUsWw=="
            ),
        },
        "https://github.com/hardikpandya/stop-slop": {
            "version": "0.7.8",
            "source_commit_sha": "8da1f030185bdfe8471220585162991eaeb970e9",
            "integrity": (
                "sha512-mJ93im3OYUFTbb0/FJrc6pLd89IaNnPRq5a/k9xIqprlhsB5Y"
                "8raQJJWBIScUuoP5QOqFe8tTrXs8olqGi4VuA=="
            ),
        },
        "https://github.com/wxhou/openspec-playwright": {
            "version": "0.3.57",
            "source_commit_sha": "fc951a456d30136e2c74df0f567c9b7815d8a9d5",
            "integrity": (
                "sha512-h7Jv1iEoEPE4zMM/6P+SM/t5aZrPPa4fTjj/FLfwV5uYQ1Q1"
                "xnKDgal079iDZEb+TMR9zxgcX1qipo6i+Vlgpg=="
            ),
        },
        "https://github.com/millionco/react-doctor": {
            "version": "0.7.8",
            "source_commit_sha": "a16e452648eda8a2c05504219d1af66fd428dbf8",
            "integrity": (
                "sha512-G3spmtZJE/gWWPRJ3rpgUWTPRDJpEmdRja7iNZ7RAXlfpEO+N"
                "WVzPTca/cPI9hLwPo2Aq5/BZggo5JDBrwGrlA=="
            ),
        },
        "https://github.com/nteract/semiotic": {
            "version": "3.8.2",
            "source_commit_sha": "0cc4e4c0f5f0cec3a1f28091def66097ebddd5c3",
            "integrity": (
                "sha512-gTfM94TrmlcGpI8RrhYr5crpkKhn6n8gQ6RJjmeJVF0lFMDQ"
                "A0QNjwKwH1KJ0k6+nJKeScF88kjGUBeEH177MQ=="
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
    specs["https://github.com/avivsinai/langfuse-mcp"][0]["auth_required"] = True
    papersflow = specs["https://github.com/papersflow-ai/papersflow-codex-plugin"]
    hosted_papersflow = next(item for item in papersflow if item.get("kind") == "mcp")
    hosted_papersflow.update(
        {
            "auth_required": True,
            "auth_mode": "oauth",
            "auth_env_names": ["PAPERSFLOW_OAUTH_ACCOUNT"],
        }
    )
    specs["https://github.com/octane0411/opencode-plugin-openspec"] = [
        {
            "kind": "plugin",
            "package_manager": "opencode-plugin",
            "package_name": "opencode-plugin-openspec",
            "version": "0.1.4",
            "source_commit_sha": "54864428bd0cb2afeb36f6558ca714b7bbc1203f",
            "integrity": (
                "sha512-g2g4bUvtC1Ovj/lrbAhL1b0befBN6LCCIRyrdXjfX1n8gn5mN4/"
                "z9s6q4wsEPcuk4DtSUZ+2Kig3+2UzASIBBg=="
            ),
            "executables": [],
            "paths": [],
            "probe": [],
            "probe_contains": "",
            "probe_exit_codes": [0],
            "probe_env": {},
            "mcp_server": "",
            "plugin_id": "candidate-opencode-plugin-openspec",
            "plugin_enabled": True,
            "auth_env_names": [],
            "config_surfaces": ["opencode.json", "~/.config/opencode/opencode.json"],
            "notes": "Activation must resolve overlap with the repo-native OpenSpec workflow.",
        }
    ]
    return specs


def artifact_id(url: str, spec: dict[str, Any]) -> str:
    identity = "\0".join(
        (
            url.lower(),
            str(spec.get("kind") or ""),
            str(spec.get("package_manager") or ""),
            str(spec.get("package_name") or ""),
            str(spec.get("mcp_server") or spec.get("plugin_id") or ""),
        )
    )
    suffix = hashlib.sha256(identity.encode()).hexdigest()[:16]
    return f"candidate-artifact-{suffix}"


def load_receipts() -> dict[str, dict[str, dict[str, Any]]]:
    if not RECEIPTS.is_file():
        return {}
    payload = load_json(RECEIPTS)
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


def build_assurance() -> dict[str, Any]:
    specs = runtime_specs()
    receipts = load_receipts()
    source_shas = inspected_source_shas()
    source_targets = load_json(MANIFEST_DIR / "integration-targets.json").get("items", [])
    source_by_url = {
        str(item.get("normalized_url") or "").lower(): item
        for item in source_targets
        if isinstance(item, dict)
    }
    artifacts: list[dict[str, Any]] = []
    for url, rows in sorted(specs.items()):
        source = source_by_url.get(url.lower(), {})
        for seed in rows:
            candidate_id = artifact_id(url, seed)
            phase_rows = receipts.get(candidate_id, {})
            installed_digest = phase_rows.get("install", {}).get("installed_digest")
            phase_results: dict[str, Any] = {}
            phase_errors: list[str] = []
            for phase, predicate_id in PHASE_PREDICATES:
                receipt = phase_rows.get(phase)
                context: dict[str, Any] = {}
                if phase == "identity":
                    context = {
                        "expected_package_id": f"{seed.get('package_manager')}:{seed.get('package_name')}",
                        "expected_source_commit_sha": str(
                            seed.get("source_commit_sha") or source_shas.get(url.lower()) or ""
                        ),
                        "expected_resolved_version": seed.get("version"),
                    }
                    if seed.get("integrity"):
                        context["expected_integrity"] = seed["integrity"]
                elif phase in {"behavior", "fresh_process"}:
                    context = {"expected_installed_digest": installed_digest}
                elif phase == "rollback":
                    context = {"expected_promoted_final_digest": installed_digest}
                errors = (
                    [f"missing {phase} receipt"]
                    if receipt is None
                    else evaluate_predicate(predicate_id, receipt, context)
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
                auth_errors = (
                    ["missing auth receipt"]
                    if auth_receipt is None
                    else evaluate_predicate("auth", auth_receipt)
                )
                phase_results["auth"] = {
                    "predicate": "auth",
                    "status": "accepted" if not auth_errors else "incomplete",
                    "errors": auth_errors,
                }
                phase_errors.extend(f"auth: {error}" for error in auth_errors)

            artifacts.append(
                {
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
                    "phase_results": phase_results,
                    "status": "accepted" if not phase_errors else "incomplete",
                    "errors": phase_errors,
                }
            )

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
    complete = (
        len(source_by_url) == EXPECTED_TARGET_COUNT
        and len(artifacts) >= EXPECTED_RUNTIME_FLOOR
        and not active_blockers
    )
    return {
        "version": 1,
        "generated_at": now(),
        "assurance_kind": "candidate-runtime-activation",
        "requested_full_usability": complete,
        "source_target_count": len(source_by_url),
        "runtime_artifact_count": len(artifacts),
        "minimum_runtime_artifact_count": EXPECTED_RUNTIME_FLOOR,
        "artifacts": artifacts,
        "totals": {
            "status_counts": dict(sorted(status_counts.items())),
            "kind_counts": dict(sorted(kind_counts.items())),
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
    artifacts = payload.get("artifacts", [])
    if not isinstance(artifacts, list) or len(artifacts) < EXPECTED_RUNTIME_FLOOR:
        errors.append("activation assurance must contain at least 65 runtime artifacts")
        return errors
    ids = [str(item.get("artifact_id") or "") for item in artifacts if isinstance(item, dict)]
    if len(ids) != len(set(ids)) or any(not value for value in ids):
        errors.append("runtime artifact IDs must be non-empty and unique")
    accepted = sum(1 for item in artifacts if item.get("status") == "accepted")
    if payload.get("requested_full_usability") is True and accepted != len(artifacts):
        errors.append("full usability cannot be true with incomplete artifacts")
    if payload.get("requested_full_usability") is True and payload.get("active_blockers"):
        errors.append("full usability cannot be true with active blockers")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()

    payload = load_json(OUTPUT) if args.check else build_assurance()
    errors = structural_errors(payload)
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
