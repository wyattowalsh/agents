#!/usr/bin/env python3
"""Rehearse exact rollback of accepted local candidate MCP entrypoints."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sys
import tempfile
import uuid
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import anyio

from wagents.candidate_evidence import (
    FILESYSTEM_DIGEST_ALGORITHM,
    RUNTIME_DIGEST_IGNORED_DIRS,
    receipt_metadata,
)
from wagents.candidate_receipts import ReceiptStore

ROOT = Path(__file__).resolve().parents[1]
ACTIVATION_SCRIPT = ROOT / "scripts/record_candidate_runtime_activation.py"
CLI_CANARY_SCRIPT = ROOT / "scripts/run_candidate_cli_canaries.py"
MCP_CANARY_SCRIPT = ROOT / "scripts/run_candidate_mcp_canaries.py"
CLI_ROLLBACK_SCRIPT = ROOT / "scripts/rehearse_candidate_cli_rollback.py"
MANIFEST_DIR = ROOT / "planning/manifests/candidate-corpus-jul2026"
RECEIPTS = MANIFEST_DIR / "runtime-activation-receipts.json"
RUNTIME_STATE = Path.home() / ".local/share/wagents/candidate-runtime"
LOCK_PATH = RUNTIME_STATE / "locks/candidate-mcp-rollback.lock"
JOURNAL_KIND = "candidate-mcp-rollback"
TRANSCRIPT_DIR = MANIFEST_DIR / "runtime-evidence/mcp-rollback"
EXPECTED_ARTIFACT_COUNT = 17
EXPECTED_REHEARSABLE_ARTIFACT_COUNT = 15
REHEARSAL_KIND = "isolated-entrypoint-root-detach"


def load_module(name: str, path: Path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def now() -> str:
    return datetime.now(UTC).isoformat()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.wagents-{os.getpid()}")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    directory_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def read_receipt_document() -> dict[str, Any]:
    return ReceiptStore(RECEIPTS, RUNTIME_STATE).load()


def read_receipts() -> dict[tuple[str, str], dict[str, Any]]:
    payload = read_receipt_document()
    return {(str(row["artifact_id"]), str(row["phase"])): row for row in payload.get("receipts", [])}


def write_receipts(rows: dict[tuple[str, str], dict[str, Any]]) -> None:
    store = ReceiptStore(RECEIPTS, RUNTIME_STATE)
    snapshot = store.snapshot(artifact_keys=set(rows))
    store.commit(snapshot, artifact_upserts=rows)


def candidate_artifacts() -> list[tuple[str, str, dict[str, Any]]]:
    activation = load_module("_candidate_mcp_rollback_activation", ACTIVATION_SCRIPT)
    result: list[tuple[str, str, dict[str, Any]]] = []
    for url, specs in sorted(activation.runtime_specs().items()):
        for seed in specs:
            name = str(seed.get("mcp_server") or "")
            if seed.get("kind") != "mcp":
                continue
            result.append((activation.artifact_id(url, seed), name, seed))
    if len(result) != EXPECTED_ARTIFACT_COUNT:
        raise ValueError(f"expected {EXPECTED_ARTIFACT_COUNT} MCP artifacts, found {len(result)}")
    artifact_ids = [artifact_id for artifact_id, _name, _seed in result]
    if len(artifact_ids) != len(set(artifact_ids)):
        raise ValueError("MCP rollback artifact ids must be unique")
    return result


def rollback_plan() -> list[dict[str, Any]]:
    canaries = load_module("_candidate_mcp_rollback_canaries_plan", MCP_CANARY_SCRIPT)
    result: list[dict[str, Any]] = []
    for artifact_id, name, seed in candidate_artifacts():
        blocker = canaries.BLOCKED_MCP_REASONS.get(name)
        result.append({
            "artifact_id": artifact_id,
            "mcp_server": name,
            "status": "blocked" if blocker else "ready",
            "blocker": blocker or "",
            "package_manager": str(seed.get("package_manager") or ""),
            "network_policy": canaries.PROBE_NETWORK_POLICIES.get(name, "none"),
            "network_action_required": (
                bool(seed.get("auth_required"))
                or seed.get("package_manager") == "hosted"
                or canaries.PROBE_NETWORK_POLICIES.get(name) == "external"
            ),
        })
    ready_count = sum(item["status"] == "ready" for item in result)
    if ready_count != EXPECTED_REHEARSABLE_ARTIFACT_COUNT:
        raise ValueError(
            f"expected {EXPECTED_REHEARSABLE_ARTIFACT_COUNT} rehearsable MCP artifacts, found {ready_count}"
        )
    return result


def write_transcript(artifact_id: str, payload: dict[str, Any]) -> tuple[str, str]:
    if not artifact_id.replace("-", "").isalnum():
        raise ValueError(f"invalid artifact id for transcript: {artifact_id!r}")
    transaction_id = str(payload.get("transaction_id") or "")
    if not transaction_id.isalnum():
        raise ValueError("rollback transcript requires an alphanumeric transaction id")
    path = ReceiptStore(RECEIPTS, RUNTIME_STATE).write_immutable_json(
        kind=JOURNAL_KIND,
        transaction_id=f"{artifact_id}-{transaction_id}",
        payload=payload,
        bucket="transcripts",
    )
    return str(path), hashlib.sha256(path.read_bytes()).hexdigest()


def recover_stale_staging(store: ReceiptStore) -> list[str]:
    staging_dir = RUNTIME_STATE / "receipts" / ".staging" / JOURNAL_KIND
    recovered: list[str] = []
    if not staging_dir.is_dir():
        return recovered
    for path in sorted(staging_dir.glob("*.json")):
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"unsafe MCP rollback staging artifact: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        transaction_id = str(payload.get("transaction_id") or "")
        if path.stem != transaction_id or not transaction_id.isalnum():
            raise RuntimeError(f"invalid MCP rollback staging transaction: {path}")
        status = str(payload.get("status") or "")
        if status == "commit-pending":
            journal_path = RUNTIME_STATE / "receipts" / "journals" / JOURNAL_KIND / f"{transaction_id}.json"
            if journal_path.is_file() and journal_path.read_bytes() == path.read_bytes():
                path.unlink()
                continue
        if status not in {"running", "commit-pending"}:
            raise RuntimeError(f"unsupported MCP rollback staging status {status!r}: {path}")
        payload["status"] = "failed"
        payload["completed_at"] = now()
        payload["error_type"] = "InterruptedRollback"
        for artifact in payload.get("artifacts", []):
            if artifact.get("status") == "running":
                artifact["status"] = "failed"
                artifact["error_type"] = "InterruptedRollback"
        destination = store.write_immutable_json(
            kind=JOURNAL_KIND,
            transaction_id=transaction_id,
            payload=payload,
            failure=True,
        )
        if not destination.is_file():
            raise RuntimeError(f"failed to recover MCP rollback staging journal: {path}")
        path.unlink()
        recovered.append(transaction_id)
    return recovered


def restored_canary(name: str, canaries: Any, probe: Any) -> tuple[int, str, str, str]:
    with tempfile.TemporaryDirectory(prefix=f"wagents-mcp-rollback-{name}-") as raw:
        (
            pid,
            output_digest,
            _failure_digest,
            _denial_digest,
            failure_tool,
            denial_tool,
            denial_encoding,
            shutdown_mode,
            launch_path,
            launch_realpath,
        ) = anyio.run(
            canaries.execute_once,
            name,
            probe,
            Path(raw),
            90.0,
        )
    if failure_tool == denial_tool:
        raise RuntimeError(f"{name}: restored canary reused one tool for failure and denial")
    if denial_encoding not in {"protocol-error", "tool-error", "content-marker", "dependency-gate"}:
        raise RuntimeError(f"{name}: restored canary returned an unsupported denial encoding")
    if shutdown_mode != "mcp-sdk-bounded-process-group-shutdown":
        raise RuntimeError(f"{name}: restored canary did not use bounded owned-child shutdown")
    return pid, output_digest, launch_path, launch_realpath


def rehearse_artifact(
    artifact_id: str,
    name: str,
    seed: dict[str, Any],
    rows: dict[tuple[str, str], dict[str, Any]],
    transaction_id: str,
    journal: dict[str, Any],
    journal_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cli_helpers = load_module("_candidate_mcp_rollback_cli_helpers", CLI_CANARY_SCRIPT)
    canaries = load_module("_candidate_mcp_rollback_runtime", MCP_CANARY_SCRIPT)
    rollback_helpers = load_module("_candidate_mcp_rollback_helpers", CLI_ROLLBACK_SCRIPT)
    install = rows.get((artifact_id, "install"))
    identity = rows.get((artifact_id, "identity"))
    if install is None:
        raise ValueError(f"missing install receipt for {artifact_id}")
    if identity is None:
        raise ValueError(f"missing identity receipt for {artifact_id}")
    expected_digest = str(install.get("installed_digest") or "")
    installed = canaries.installed_paths(seed, cli_helpers)
    if not installed or cli_helpers.file_digest(installed) != expected_digest:
        raise ValueError(f"installed digest drift before MCP rollback for {artifact_id}")

    names = [str(value) for value in seed.get("executables", [])]
    entrypoints = rollback_helpers.public_entrypoints(seed)
    with tempfile.TemporaryDirectory(prefix=f"wagents-mcp-entrypoint-rollback-{artifact_id}-") as raw:
        isolated_bin = Path(raw) / "bin"
        evidence = rollback_helpers.rehearse_isolated_surface(
            entrypoints,
            names,
            isolated_bin,
            transaction_id,
        )
        isolated_by_name = {path.name: path for path in evidence["clones"]}
        original_probe = canaries.PROBES[name]
        isolated_executable = isolated_by_name.get(original_probe.executable.name)
        if isolated_executable is None:
            raise RuntimeError(
                f"MCP probe executable {original_probe.executable.name!r} is absent from isolated entrypoints"
            )
        restored_pid, output_digest, restored_launch_path, restored_launch_realpath = restored_canary(
            name,
            canaries,
            replace(original_probe, executable=isolated_executable),
        )
        if Path(restored_launch_path) != isolated_executable:
            raise RuntimeError(f"MCP restored canary did not launch the isolated entrypoint for {artifact_id}")
        if Path(restored_launch_path).parent != isolated_bin:
            raise RuntimeError(f"MCP restored canary escaped the isolated entrypoint root for {artifact_id}")
        if Path(restored_launch_realpath) != isolated_executable.resolve(strict=True):
            raise RuntimeError(f"MCP restored canary realpath evidence drifted for {artifact_id}")
        rollback_helpers.validate_process_evidence(
            int(evidence["fresh_absence_process_id"]),
            restored_pid,
            str(evidence["fresh_absence_output_sha256"]),
            output_digest,
        )
        if rollback_helpers.surface_snapshot(entrypoints) != evidence["live_preimage"]:
            raise RuntimeError(f"live MCP entrypoints changed during restored canary for {artifact_id}")
        if cli_helpers.file_digest(installed) != expected_digest:
            raise RuntimeError(f"MCP package digest drift after rollback for {artifact_id}")

        transcript = {
            "version": 1,
            "artifact_id": artifact_id,
            "mcp_server": name,
            "transaction_id": transaction_id,
            "rehearsal_kind": REHEARSAL_KIND,
            "live_entrypoint_digest": evidence["live_entrypoint_digest"],
            "live_entrypoint_unchanged": True,
            "isolated_preimage_digest": evidence["preimage_digest"],
            "isolated_rollback_digest": evidence["rollback_digest"],
            "fresh_absence": evidence["fresh_absence"],
            "fresh_absence_process_id": evidence["fresh_absence_process_id"],
            "fresh_absence_output_sha256": evidence["fresh_absence_output_sha256"],
            "restored_use_process_id": restored_pid,
            "restored_use_output_sha256": output_digest,
            "restored_use_launch_path": restored_launch_path,
            "restored_use_launch_realpath": restored_launch_realpath,
            "installed_digest": expected_digest,
            "status": "passed",
        }
        transcript_path, transcript_sha256 = write_transcript(artifact_id, transcript)

    record = journal_record if journal_record is not None else {}
    record.update({
        "artifact_id": artifact_id,
        "mcp_server": name,
        "transaction_id": transaction_id,
        "rehearsal_kind": REHEARSAL_KIND,
        "live_entrypoints": [str(path) for path in entrypoints],
        "live_entrypoint_digest": evidence["live_entrypoint_digest"],
        "live_entrypoint_unchanged": True,
        "preimage_digest": evidence["preimage_digest"],
        "rollback_digest": evidence["rollback_digest"],
        "fresh_absence_process_id": evidence["fresh_absence_process_id"],
        "fresh_absence_output_sha256": evidence["fresh_absence_output_sha256"],
        "fresh_absence": evidence["fresh_absence"],
        "restored_process_id": restored_pid,
        "restored_output_sha256": output_digest,
        "restored_use_process_id": restored_pid,
        "restored_use_output_sha256": output_digest,
        "restored_use_launch_path": restored_launch_path,
        "restored_use_launch_realpath": restored_launch_realpath,
        "transcript_path": transcript_path,
        "transcript_sha256": transcript_sha256,
        "status": "passed",
    })
    if journal_record is None:
        journal["artifacts"].append(record)
    receipt = {
        "artifact_id": artifact_id,
        "phase": "rollback",
        "preimage_digest": evidence["preimage_digest"],
        "rollback_digest": evidence["rollback_digest"],
        "promoted_final_digest": expected_digest,
        "fresh_absence_status": "passed",
        "promoted_final_status": "passed",
        "rehearsal_kind": REHEARSAL_KIND,
        "live_entrypoint_paths": [str(path) for path in entrypoints],
        "live_entrypoint_digest": evidence["live_entrypoint_digest"],
        "live_entrypoint_unchanged": True,
        "transaction_id": transaction_id,
        "fresh_absence_process_id": evidence["fresh_absence_process_id"],
        "fresh_absence_output_sha256": evidence["fresh_absence_output_sha256"],
        "restored_process_id": restored_pid,
        "restored_output_sha256": output_digest,
        "restored_use_status": "passed",
        "restored_use_process_id": restored_pid,
        "restored_use_output_sha256": output_digest,
        "restored_use_launch_path": restored_launch_path,
        "restored_use_launch_realpath": restored_launch_realpath,
        "transcript_path": transcript_path,
        "transcript_sha256": transcript_sha256,
    }
    receipt.update(
        receipt_metadata(
            artifact_id=artifact_id,
            phase="rollback",
            source_commit_sha=str(identity.get("source_commit_sha") or seed.get("source_commit_sha") or ""),
            package_id=str(install.get("package_id") or ""),
            resolved_version=str(seed.get("version") or identity.get("resolved_version") or ""),
            installed_digest=expected_digest,
        )
    )
    receipt["digest_algorithm"] = FILESYSTEM_DIGEST_ALGORITHM
    receipt["digest_ignored_dirs"] = sorted(RUNTIME_DIGEST_IGNORED_DIRS)
    return receipt


def rehearse_journaled_artifact(
    artifact_id: str,
    name: str,
    seed: dict[str, Any],
    rows: dict[tuple[str, str], dict[str, Any]],
    transaction_id: str,
    journal: dict[str, Any],
    staging_path: Path,
) -> dict[str, Any]:
    journal_record: dict[str, Any] = {
        "artifact_id": artifact_id,
        "mcp_server": name,
        "transaction_id": transaction_id,
        "status": "running",
    }
    journal["artifacts"].append(journal_record)
    atomic_json(staging_path, journal)
    try:
        return rehearse_artifact(
            artifact_id,
            name,
            seed,
            rows,
            transaction_id,
            journal,
            journal_record,
        )
    except BaseException as error:
        journal_record["status"] = "failed"
        journal_record["error_type"] = type(error).__name__
        atomic_json(staging_path, journal)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--allow-external-network", action="store_true")
    parser.add_argument("--mcp", action="append")
    args = parser.parse_args()
    artifacts = candidate_artifacts()
    plan = rollback_plan()
    by_name = {name: (artifact_id, seed) for artifact_id, name, seed in artifacts}
    default_requested = {
        str(item["mcp_server"])
        for item in plan
        if item["status"] == "ready" and item.get("network_policy") != "external"
    }
    requested = set(args.mcp or default_requested)
    unknown = sorted(requested - set(by_name))
    if unknown:
        raise ValueError(f"unknown candidate MCP server ids: {unknown}")
    selected_plan = [item for item in plan if item["mcp_server"] in requested]
    blockers = [item for item in selected_plan if item["status"] == "blocked"]
    external_without_authorization = [
        item for item in selected_plan if item.get("network_policy") == "external" and not args.allow_external_network
    ]
    for item in external_without_authorization:
        item["status"] = "execution-required"
        item["blocker"] = "external-network-authorization-required"
    blockers.extend(external_without_authorization)
    if blockers:
        print(
            json.dumps(
                {
                    "ok": False,
                    "applied": False,
                    "artifact_count": len(selected_plan),
                    "blocked_count": len(blockers),
                    "artifacts": selected_plan,
                },
                indent=2,
                ensure_ascii=True,
            )
        )
        return 1
    artifacts = [(artifact_id, name, seed) for artifact_id, name, seed in artifacts if name in requested]
    if not args.apply:
        print(
            json.dumps(
                {
                    "ok": True,
                    "applied": False,
                    "artifact_count": len(artifacts),
                    "artifacts": [
                        {"artifact_id": artifact_id, "mcp_server": name} for artifact_id, name, _seed in artifacts
                    ],
                },
                indent=2,
                ensure_ascii=True,
            )
        )
        return 0

    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        store = ReceiptStore(RECEIPTS, RUNTIME_STATE)
        recover_stale_staging(store)
        owned_keys = {
            (artifact_id, phase)
            for artifact_id, _name, _seed in artifacts
            for phase in ("identity", "install", "rollback")
        }
        snapshot = store.snapshot(artifact_keys=owned_keys)
        rows = snapshot.artifact_rows
        run_id = uuid.uuid4().hex
        staging_path = RUNTIME_STATE / "receipts" / ".staging" / JOURNAL_KIND / f"{run_id}.json"
        journal: dict[str, Any] = {
            "version": 2,
            "transaction_id": run_id,
            "kind": "mcp",
            "started_at": now(),
            "receipt_revision_preimage": snapshot.revision,
            "status": "running",
            "artifacts": [],
        }
        atomic_json(staging_path, journal)
        pending: list[dict[str, Any]] = []
        try:
            for artifact_id, name, seed in artifacts:
                print(f"[candidate-mcp-rollback] rehearsing {name}", file=sys.stderr, flush=True)
                transaction_id = uuid.uuid4().hex
                receipt = rehearse_journaled_artifact(
                    artifact_id,
                    name,
                    seed,
                    rows,
                    transaction_id,
                    journal,
                    staging_path,
                )
                pending.append(receipt)
                atomic_json(staging_path, journal)
            expected_artifact_ids = sorted(artifact_id for artifact_id, _name, _seed in artifacts)
            pending_artifact_ids = sorted(str(receipt["artifact_id"]) for receipt in pending)
            journal_artifact_ids = sorted(str(record["artifact_id"]) for record in journal["artifacts"])
            if pending_artifact_ids != expected_artifact_ids or journal_artifact_ids != expected_artifact_ids:
                raise RuntimeError("MCP rollback transaction artifact sets do not match")
        except BaseException as error:
            journal["status"] = "failed"
            journal["completed_at"] = now()
            journal["error_type"] = type(error).__name__
            atomic_json(staging_path, journal)
            store.write_immutable_json(
                kind=JOURNAL_KIND,
                transaction_id=run_id,
                payload=journal,
                failure=True,
            )
            staging_path.unlink(missing_ok=True)
            raise
        else:
            journal["status"] = "commit-pending"
            journal["completed_at"] = now()
            atomic_json(staging_path, journal)
            journal_path = store.write_immutable_json(
                kind=JOURNAL_KIND,
                transaction_id=run_id,
                payload=journal,
            )
            staging_path.unlink(missing_ok=True)
            journal_sha256 = hashlib.sha256(journal_path.read_bytes()).hexdigest()
            upserts: dict[tuple[str, str], dict[str, Any]] = {}
            for receipt in pending:
                receipt["journal_sha256"] = journal_sha256
                receipt["journal_path"] = str(journal_path)
                receipt["journal_transaction_id"] = run_id
                upserts[str(receipt["artifact_id"]), "rollback"] = receipt
            try:
                commit_result = store.commit(snapshot, artifact_upserts=upserts)
            except BaseException as error:
                store.write_immutable_json(
                    kind=f"{JOURNAL_KIND}-commit",
                    transaction_id=run_id,
                    payload={
                        "version": 2,
                        "transaction_id": run_id,
                        "status": "failed",
                        "error_type": type(error).__name__,
                        "journal_path": str(journal_path),
                        "journal_sha256": journal_sha256,
                    },
                    failure=True,
                )
                raise
            commit_path = store.write_immutable_json(
                kind=f"{JOURNAL_KIND}-commit",
                transaction_id=run_id,
                payload={
                    "version": 2,
                    "transaction_id": run_id,
                    "status": "passed",
                    "journal_path": str(journal_path),
                    "journal_sha256": journal_sha256,
                    "artifact_ids": expected_artifact_ids,
                    "receipt_revision": commit_result.revision,
                    "receipt_store_transaction_id": commit_result.transaction_id,
                    "receipt_document_sha256": commit_result.document_sha256,
                },
            )
            commit_sha256 = hashlib.sha256(commit_path.read_bytes()).hexdigest()
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    print(
        json.dumps(
            {
                "applied": True,
                "artifact_count": len(artifacts),
                "transaction_id": run_id,
                "journal": str(journal_path),
                "journal_sha256": journal_sha256,
                "commit_marker": str(commit_path),
                "commit_marker_sha256": commit_sha256,
            },
            indent=2,
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
