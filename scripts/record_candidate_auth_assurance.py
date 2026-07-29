#!/usr/bin/env python3
"""Record secret-free, fail-closed auth readiness for candidate runtimes."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

from wagents.candidate_evidence import receipt_metadata
from wagents.candidate_receipts import ReceiptStore

ROOT = Path(__file__).resolve().parents[1]
ACTIVATION_SCRIPT = ROOT / "scripts" / "record_candidate_runtime_activation.py"
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
RECEIPTS = MANIFEST_DIR / "runtime-activation-receipts.json"
RUNTIME_STATE = Path.home() / ".local" / "share" / "wagents" / "candidate-runtime"
EXPECTED_AUTH_ARTIFACT_COUNT = 2


def activation_module():
    spec = importlib.util.spec_from_file_location("_candidate_auth_activation", ACTIVATION_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {ACTIVATION_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def auth_specs(module: Any) -> dict[str, tuple[str, dict[str, Any]]]:
    result: dict[str, tuple[str, dict[str, Any]]] = {}
    for url, specs in module.runtime_specs().items():
        for seed in specs:
            if seed.get("auth_required") is not True:
                continue
            provider = str(seed.get("auth_provider") or "")
            if not provider:
                raise ValueError(f"auth-required candidate omitted auth_provider: {url}")
            if provider in result:
                raise ValueError(f"duplicate candidate auth provider: {provider}")
            result[provider] = (url, seed)
    if len(result) != EXPECTED_AUTH_ARTIFACT_COUNT:
        raise ValueError(
            f"expected {EXPECTED_AUTH_ARTIFACT_COUNT} auth-required artifacts, found {len(result)}"
        )
    return result


def _fingerprint_secret_values(provider: str, names: list[str], env: dict[str, str]) -> str:
    if not names or not all(env.get(name) for name in names):
        return "unavailable"
    digest = hashlib.sha256()
    digest.update(provider.encode())
    for name in names:
        digest.update(b"\0")
        digest.update(name.encode())
        digest.update(b"\0")
        digest.update(env[name].encode())
    return f"sha256:{digest.hexdigest()}"


def redacted_auth_state(seed: dict[str, Any], env: dict[str, str] | None = None) -> dict[str, Any]:
    source = os.environ if env is None else env
    names = sorted({str(value) for value in seed.get("auth_env_names", [])})
    provider = str(seed.get("auth_provider") or "")
    presence = {name: bool(source.get(name)) for name in names}
    contract = {
        "auth_mode": str(seed.get("auth_mode") or ""),
        "auth_provider": provider,
        "storage_backend": str(seed.get("auth_storage_backend") or ""),
        "env_names": names,
        "minimum_scopes": sorted({str(value) for value in seed.get("minimum_scopes", [])}),
    }
    contract_fingerprint = hashlib.sha256(
        json.dumps(contract, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()
    return {
        **contract,
        "credential_presence": presence,
        "credentials_present": bool(presence) and all(presence.values()),
        "principal_fingerprint": _fingerprint_secret_values(provider, names, source),
        "contract_fingerprint": f"sha256:{contract_fingerprint}",
        "secret_value_recorded": False,
    }


def build_auth_receipt(
    *,
    module: Any,
    url: str,
    seed: dict[str, Any],
    source_commit_sha: str,
    installed_digest: str,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    artifact_id = module.artifact_id(url, seed)
    package_id = f"{seed.get('package_manager')}:{seed.get('package_name')}"
    resolved_version = str(seed.get("version") or "")
    receipt = {
        "artifact_id": artifact_id,
        "phase": "auth",
        "auth_required": True,
        **redacted_auth_state(seed, env),
        "auth_negative_status": "blocked",
        "auth_positive_status": "blocked",
        "logout_or_revoke_status": "blocked",
        "probe_kind": "secret-free-local-auth-contract",
        "network_probe_performed": False,
        "status": "incomplete",
        "blockers": [
            "credentialed positive auth was not exercised",
            "credentialed negative auth was not exercised",
            "logout or revoke was not exercised",
        ],
    }
    receipt.update(
        receipt_metadata(
            artifact_id=artifact_id,
            phase="auth",
            source_commit_sha=source_commit_sha,
            package_id=package_id,
            resolved_version=resolved_version,
            installed_digest=installed_digest,
        )
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--provider", action="append")
    args = parser.parse_args()

    module = activation_module()
    specs = auth_specs(module)
    requested = set(args.provider or specs)
    unknown = sorted(requested - set(specs))
    if unknown:
        raise ValueError(f"unknown candidate auth providers: {unknown}")

    source_shas = module.inspected_source_shas()
    store = ReceiptStore(RECEIPTS, RUNTIME_STATE)
    artifact_keys = {
        (module.artifact_id(specs[provider][0], specs[provider][1]), phase)
        for provider in requested
        for phase in ("identity", "install", "auth")
    }
    snapshot = store.snapshot(artifact_keys=artifact_keys)
    upserts: dict[tuple[str, str], dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    for provider in sorted(requested):
        url, seed = specs[provider]
        artifact_id = module.artifact_id(url, seed)
        install = snapshot.artifact_rows.get((artifact_id, "install"), {})
        installed_digest = str(install.get("installed_digest") or "unavailable")
        receipt = build_auth_receipt(
            module=module,
            url=url,
            seed=seed,
            source_commit_sha=str(seed.get("source_commit_sha") or source_shas.get(url.lower()) or ""),
            installed_digest=installed_digest,
        )
        existing = snapshot.artifact_rows.get((artifact_id, "auth"))
        if existing is None:
            upserts[artifact_id, "auth"] = receipt
        results.append({
            "artifact_id": artifact_id,
            "auth_provider": provider,
            "status": "incomplete",
            "credential_presence": receipt["credential_presence"],
            "credentials_present": receipt["credentials_present"],
            "principal_fingerprint": receipt["principal_fingerprint"],
            "network_probe_performed": False,
            "secret_value_recorded": False,
            "existing_receipt_preserved": existing is not None,
            "blockers": receipt["blockers"],
        })
    if args.apply and upserts:
        store.commit(snapshot, artifact_upserts=upserts)
    print(
        json.dumps(
            {
                "ok": False,
                "applied": args.apply,
                "artifact_count": len(results),
                "incomplete_count": len(results),
                "results": results,
            },
            indent=2,
            ensure_ascii=True,
        )
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
