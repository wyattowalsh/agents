#!/usr/bin/env python3
"""Rehearse exact rollback of non-Node candidate CLI activation surfaces."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from wagents.candidate_evidence import (
    FILESYSTEM_DIGEST_ALGORITHM,
    RUNTIME_DIGEST_IGNORED_DIRS,
    receipt_metadata,
)
from wagents.candidate_receipts import ReceiptStore

ROOT = Path(__file__).resolve().parents[1]
ACTIVATION_SCRIPT = ROOT / "scripts" / "record_candidate_runtime_activation.py"
CANARY_SCRIPT = ROOT / "scripts" / "run_candidate_cli_canaries.py"
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
RECEIPTS = MANIFEST_DIR / "runtime-activation-receipts.json"
RUNTIME_STATE = Path.home() / ".local" / "share" / "wagents" / "candidate-runtime"
LOCK_PATH = RUNTIME_STATE / "locks" / "non-node-cli-rollback.lock"
JOURNAL_KIND = "candidate-non-node-cli-rollback"
TRANSCRIPT_DIR = MANIFEST_DIR / "runtime-evidence" / "cli-rollback"
EXPECTED_ARTIFACT_COUNT = 12
ALLOWED_MANAGERS = {"cargo", "go", "skill-bundled", "standalone", "uv-tool", "uv-tool-git"}
REHEARSAL_KIND = "isolated-entrypoint-root-detach"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def xattr_digest(path: Path) -> str | None:
    executable = Path("/usr/bin/xattr")
    if not executable.is_file():
        return None
    argv = [str(executable), "-lx", str(path)]
    if path.is_symlink():
        argv.insert(1, "-s")
    result = subprocess.run(argv, check=True, capture_output=True)
    return sha256_bytes(result.stdout)


def path_snapshot(path: Path) -> dict[str, Any]:
    metadata = path.lstat()
    common: dict[str, Any] = {
        "mode": stat.S_IMODE(metadata.st_mode),
        "xattrs_sha256": xattr_digest(path),
    }
    if path.is_symlink():
        return {**common, "kind": "symlink", "target": os.readlink(path)}
    if path.is_file():
        return {
            **common,
            "kind": "file",
            "size": metadata.st_size,
            "sha256": sha256_file(path),
        }
    raise ValueError(f"unsupported activation surface: {path}")


def surface_snapshot(paths: list[Path]) -> dict[str, dict[str, Any]]:
    return {str(path): path_snapshot(path) for path in sorted(paths, key=str)}


def named_surface_snapshot(paths: list[Path]) -> dict[str, dict[str, Any]]:
    if len({path.name for path in paths}) != len(paths):
        raise ValueError("isolated entrypoint names must be unique")
    return {path.name: path_snapshot(path) for path in sorted(paths, key=lambda item: item.name)}


def snapshot_digest(snapshot: dict[str, dict[str, Any]]) -> str:
    encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(encoded)


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


def public_entrypoints(seed: dict[str, Any]) -> list[Path]:
    paths: list[Path] = []
    manager = str(seed.get("package_manager") or "")
    allowed_root = (Path.home() / ".cargo" / "bin" if manager == "cargo" else Path.home() / ".local" / "bin").resolve()
    for raw_name in seed.get("executables", []):
        name = str(raw_name)
        if not name or "/" in name or name in {".", ".."}:
            raise ValueError(f"invalid candidate executable name: {name!r}")
        resolved = shutil.which(name)
        if resolved is None:
            raise ValueError(f"candidate executable is not discoverable: {name}")
        path = Path(os.path.abspath(resolved))
        if path.parent.resolve() != allowed_root:
            raise ValueError(f"candidate executable is outside the managed public bin: {path}")
        which_all = subprocess.run(
            ["which", "-a", name],
            check=True,
            text=True,
            capture_output=True,
        )
        discovered = list(
            dict.fromkeys(str(Path(os.path.abspath(line))) for line in which_all.stdout.splitlines() if line)
        )
        if discovered != [str(path)]:
            raise ValueError(f"candidate executable has shadow copies: {name}: {discovered}")
        paths.append(path)
    if not paths:
        raise ValueError(f"candidate artifact has no public executables: {seed.get('package_name')}")
    return paths


def fresh_absence(names: list[str], isolated_bin: Path) -> tuple[int, dict[str, str | None], str]:
    code = "import json,shutil,sys; print(json.dumps({name: shutil.which(name) for name in sys.argv[1:]}))"
    process = subprocess.Popen(
        [sys.executable, "-c", code, *names],
        cwd=ROOT,
        env={"PATH": str(isolated_bin)},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = process.communicate(timeout=30)
    if process.returncode != 0:
        raise RuntimeError(f"fresh absence probe failed: {stderr}")
    payload = json.loads(stdout)
    if not isinstance(payload, dict) or any(value is not None for value in payload.values()):
        raise RuntimeError(f"detached entrypoint remained discoverable: {payload}")
    normalized = {str(key): value for key, value in payload.items()}
    return process.pid, normalized, sha256_bytes(json.dumps(normalized, sort_keys=True).encode())


def controlled_path(isolated_bin: Path, excluded: set[Path]) -> str:
    support = []
    for raw in os.environ.get("PATH", "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin").split(
        os.pathsep
    ):
        if not raw:
            continue
        candidate = Path(raw).expanduser().resolve()
        if candidate not in excluded and raw not in support:
            support.append(raw)
    return os.pathsep.join([str(isolated_bin), *support])


def run_restored_canary(probe: str, canaries: Any, executable_map: dict[str, Path]) -> Any:
    result = canaries.repeat_probe(probe, canaries.PROBES[probe], executable_map)
    expected_paths = {str(path) for path in executable_map.values()}
    if len(result.launch_paths) != 2 or any(path not in expected_paths for path in result.launch_paths):
        raise RuntimeError(f"restored canary did not launch through the isolated executable map: {probe}")
    expected_realpaths = {str(path.resolve(strict=True)) for path in executable_map.values()}
    if len(result.launch_realpaths) != 2 or any(path not in expected_realpaths for path in result.launch_realpaths):
        raise RuntimeError(f"restored canary realpath evidence drifted: {probe}")
    return result


def validate_process_evidence(
    absence_pid: int,
    restored_pid: int,
    absence_output_sha256: str,
    restored_output_sha256: str,
) -> None:
    if absence_pid <= 0 or restored_pid <= 0:
        raise RuntimeError("rollback evidence requires positive process IDs")
    if absence_pid == restored_pid:
        raise RuntimeError("rollback absence and restored-use probes reused a process ID")
    for label, value in {
        "absence": absence_output_sha256,
        "restored-use": restored_output_sha256,
    }.items():
        if len(value) != 64:
            raise RuntimeError(f"rollback {label} output digest is not SHA256")
        try:
            int(value, 16)
        except ValueError as error:
            raise RuntimeError(f"rollback {label} output digest is not SHA256") from error


def clone_entrypoints(entrypoints: list[Path], isolated_bin: Path) -> list[Path]:
    isolated_bin.mkdir(parents=True)
    clones: list[Path] = []
    for entrypoint in entrypoints:
        target = entrypoint.resolve(strict=True)
        clone = isolated_bin / entrypoint.name
        if clone.exists() or clone.is_symlink():
            raise ValueError(f"isolated entrypoint collision: {clone.name}")
        clone.symlink_to(target)
        clones.append(clone)
    return clones


def rehearse_isolated_surface(
    live_entrypoints: list[Path],
    names: list[str],
    isolated_bin: Path,
    transaction_id: str,
    *,
    absence_probe: Callable[[list[str], Path], tuple[int, dict[str, str | None], str]] = fresh_absence,
) -> dict[str, Any]:
    live_preimage = surface_snapshot(live_entrypoints)
    clones = clone_entrypoints(live_entrypoints, isolated_bin)
    preimage = named_surface_snapshot(clones)
    preimage_digest = snapshot_digest(preimage)
    staged = {path: path.with_name(f".wagents-rollback-{transaction_id}-{path.name}") for path in clones}
    if any(path.exists() or path.is_symlink() for path in staged.values()):
        raise ValueError("isolated rollback staging collision")

    detached: list[Path] = []
    try:
        for path in clones:
            os.replace(path, staged[path])
            detached.append(path)
        absence_pid, absence, absence_output_sha256 = absence_probe(names, isolated_bin)
    finally:
        for path in reversed(detached):
            if path.exists() or path.is_symlink():
                raise RuntimeError(f"isolated rollback restore path became occupied: {path.name}")
            os.replace(staged[path], path)

    rollback = named_surface_snapshot(clones)
    rollback_digest = snapshot_digest(rollback)
    live_postimage = surface_snapshot(live_entrypoints)
    if rollback != preimage:
        raise RuntimeError("isolated rollback did not restore the exact preimage")
    if live_postimage != live_preimage:
        raise RuntimeError("live entrypoints changed during isolated rollback")
    if any(path.exists() or path.is_symlink() for path in staged.values()):
        raise RuntimeError("isolated rollback staging remnants remain")
    return {
        "clones": clones,
        "preimage": preimage,
        "preimage_digest": preimage_digest,
        "rollback": rollback,
        "rollback_digest": rollback_digest,
        "live_preimage": live_preimage,
        "live_postimage": live_postimage,
        "live_entrypoint_digest": snapshot_digest(live_preimage),
        "fresh_absence": absence,
        "fresh_absence_process_id": absence_pid,
        "fresh_absence_output_sha256": absence_output_sha256,
    }


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
    return str(path), sha256_file(path)


def candidate_artifacts() -> list[tuple[str, dict[str, Any], str, str]]:
    activation = load_module("_candidate_non_node_activation", ACTIVATION_SCRIPT)
    canaries = load_module("_candidate_non_node_canaries", CANARY_SCRIPT)
    result: list[tuple[str, dict[str, Any], str, str]] = []
    for url, specs in sorted(activation.runtime_specs().items()):
        for seed in specs:
            manager = str(seed.get("package_manager") or "")
            binding = (url, str(seed.get("kind") or ""))
            probe = canaries.PROBE_BINDINGS.get(binding)
            if manager not in ALLOWED_MANAGERS or probe is None:
                continue
            result.append((activation.artifact_id(url, seed), seed, str(probe), url))
    if len(result) != EXPECTED_ARTIFACT_COUNT:
        raise ValueError(f"expected {EXPECTED_ARTIFACT_COUNT} non-Node CLI artifacts, found {len(result)}")
    artifact_ids = [artifact_id for artifact_id, _seed, _probe, _url in result]
    if len(artifact_ids) != len(set(artifact_ids)):
        raise ValueError("non-Node CLI rollback artifact ids must be unique")
    return result


def read_receipt_document() -> dict[str, Any]:
    return ReceiptStore(RECEIPTS, RUNTIME_STATE).load()


def read_receipts() -> dict[tuple[str, str], dict[str, Any]]:
    payload = read_receipt_document()
    rows = payload.get("receipts", [])
    if not isinstance(rows, list):
        raise ValueError("runtime receipts must be a list")
    return {(str(row["artifact_id"]), str(row["phase"])): row for row in rows}


def write_receipts(rows: dict[tuple[str, str], dict[str, Any]]) -> None:
    store = ReceiptStore(RECEIPTS, RUNTIME_STATE)
    snapshot = store.snapshot(artifact_keys=set(rows))
    store.commit(snapshot, artifact_upserts=rows)


def rehearse_artifact(
    artifact_id: str,
    seed: dict[str, Any],
    probe: str,
    url: str,
    rows: dict[tuple[str, str], dict[str, Any]],
    journal: dict[str, Any],
    journal_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    canaries = load_module("_candidate_non_node_canary_runtime", CANARY_SCRIPT)
    install = rows.get((artifact_id, "install"))
    identity = rows.get((artifact_id, "identity"))
    if install is None:
        raise ValueError(f"missing install receipt for {artifact_id}")
    if identity is None:
        raise ValueError(f"missing identity receipt for {artifact_id}")
    expected_installed_digest = str(install.get("installed_digest") or "")
    live_executable_map = canaries.resolve_managed_executables([seed])
    installed_paths = canaries.installed_paths(seed, live_executable_map)
    if not installed_paths:
        raise ValueError(f"installed paths missing for {artifact_id}")
    if canaries.file_digest(installed_paths) != expected_installed_digest:
        raise ValueError(f"installed digest drift before rollback for {artifact_id}")

    entrypoint_names = [str(name) for name in seed.get("executables", [])]
    entrypoints = public_entrypoints(seed)
    transaction_id = uuid.uuid4().hex
    record: dict[str, Any] = {
        "artifact_id": artifact_id,
        "normalized_url": url,
        "transaction_id": transaction_id,
        "status": "isolating",
        "rehearsal_kind": REHEARSAL_KIND,
        "live_entrypoints": [str(path) for path in entrypoints],
    }
    journal["artifacts"].append(record)
    atomic_json(journal_path, journal)

    with tempfile.TemporaryDirectory(prefix=f"wagents-cli-rollback-{artifact_id}-") as raw:
        isolated_bin = Path(raw) / "bin"
        evidence = rehearse_isolated_surface(
            entrypoints,
            entrypoint_names,
            isolated_bin,
            transaction_id,
        )
        clones_by_name = {path.name: path for path in evidence["clones"]}
        if set(clones_by_name) != set(entrypoint_names) or set(live_executable_map) != set(entrypoint_names):
            raise RuntimeError(f"isolated executable map does not exactly cover {artifact_id}")
        restored_executable_map: dict[str, Path] = {}
        for name in entrypoint_names:
            clone = clones_by_name[name]
            if clone.parent != isolated_bin:
                raise RuntimeError(f"isolated executable escaped its rollback root: {clone}")
            if clone.resolve(strict=True) != live_executable_map[name].resolve(strict=True):
                raise RuntimeError(f"isolated executable target drifted: {name}")
            restored_executable_map[name] = clone
        restored_map_evidence = {
            name: {
                "launch_path": str(path),
                "realpath": str(path.resolve(strict=True)),
            }
            for name, path in restored_executable_map.items()
        }
        canary = run_restored_canary(probe, canaries, restored_executable_map)
        canary_pid = int(canary.fresh_pid)
        canary_output_sha256 = str(canary.output_sha256)
        launch_paths = list(canary.launch_paths)
        launch_realpaths = list(canary.launch_realpaths)
        if any(Path(path).parent != isolated_bin for path in launch_paths):
            raise RuntimeError(f"restored canary bypassed the isolated rollback root: {artifact_id}")
        if any(path in {str(entrypoint) for entrypoint in entrypoints} for path in launch_paths):
            raise RuntimeError(f"restored canary launched a live public entrypoint: {artifact_id}")
        validate_process_evidence(
            int(evidence["fresh_absence_process_id"]),
            canary_pid,
            str(evidence["fresh_absence_output_sha256"]),
            canary_output_sha256,
        )
        live_after_canary = surface_snapshot(entrypoints)
        if live_after_canary != evidence["live_preimage"]:
            raise RuntimeError(f"live entrypoints changed during restored canary for {artifact_id}")
        if canaries.file_digest(canaries.installed_paths(seed, live_executable_map)) != expected_installed_digest:
            raise RuntimeError(f"installed digest drift after rollback for {artifact_id}")

        transcript = {
            "version": 1,
            "artifact_id": artifact_id,
            "normalized_url": url,
            "transaction_id": transaction_id,
            "rehearsal_kind": REHEARSAL_KIND,
            "live_entrypoint_digest": evidence["live_entrypoint_digest"],
            "live_entrypoint_unchanged": True,
            "isolated_preimage_digest": evidence["preimage_digest"],
            "isolated_rollback_digest": evidence["rollback_digest"],
            "fresh_absence": evidence["fresh_absence"],
            "fresh_absence_process_id": evidence["fresh_absence_process_id"],
            "fresh_absence_output_sha256": evidence["fresh_absence_output_sha256"],
            "restored_use_process_id": canary_pid,
            "restored_use_output_sha256": canary_output_sha256,
            "restored_use_launch_paths": launch_paths,
            "restored_use_launch_realpaths": launch_realpaths,
            "restored_executable_map": restored_map_evidence,
            "installed_digest": expected_installed_digest,
            "status": "passed",
        }
        transcript_path, transcript_sha256 = write_transcript(artifact_id, transcript)

    record.update({
        "status": "passed",
        "preimage_digest": evidence["preimage_digest"],
        "rollback_digest": evidence["rollback_digest"],
        "live_entrypoint_digest": evidence["live_entrypoint_digest"],
        "live_entrypoint_unchanged": True,
        "fresh_absence": evidence["fresh_absence"],
        "fresh_absence_process_id": evidence["fresh_absence_process_id"],
        "fresh_absence_output_sha256": evidence["fresh_absence_output_sha256"],
        "restored_use_process_id": canary_pid,
        "restored_use_output_sha256": canary_output_sha256,
        "restored_use_launch_paths": launch_paths,
        "restored_use_launch_realpaths": launch_realpaths,
        "restored_executable_map": restored_map_evidence,
        "transcript_path": transcript_path,
        "transcript_sha256": transcript_sha256,
    })
    atomic_json(journal_path, journal)
    receipt = {
        "artifact_id": artifact_id,
        "phase": "rollback",
        "preimage_digest": evidence["preimage_digest"],
        "rollback_digest": evidence["rollback_digest"],
        "promoted_final_digest": expected_installed_digest,
        "fresh_absence_status": "passed",
        "promoted_final_status": "passed",
        "rehearsal_kind": REHEARSAL_KIND,
        "live_entrypoint_paths": [str(path) for path in entrypoints],
        "live_entrypoint_digest": evidence["live_entrypoint_digest"],
        "live_entrypoint_unchanged": True,
        "isolated_entrypoint_snapshot": evidence["preimage"],
        "detached_without_delete": True,
        "fresh_absence_process_id": evidence["fresh_absence_process_id"],
        "fresh_absence_output_sha256": evidence["fresh_absence_output_sha256"],
        "restored_discovery_status": "passed",
        "restored_canary_status": "passed",
        "restored_canary_process_id": canary_pid,
        "restored_canary_output_sha256": canary_output_sha256,
        "restored_use_status": "passed",
        "restored_use_process_id": canary_pid,
        "restored_use_output_sha256": canary_output_sha256,
        "restored_use_launch_paths": launch_paths,
        "restored_use_launch_realpaths": launch_realpaths,
        "restored_executable_map": restored_map_evidence,
        "transaction_id": transaction_id,
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
            installed_digest=expected_installed_digest,
        )
    )
    receipt["digest_algorithm"] = FILESYSTEM_DIGEST_ALGORITHM
    receipt["digest_ignored_dirs"] = sorted(RUNTIME_DIGEST_IGNORED_DIRS)
    return receipt, record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    artifacts = candidate_artifacts()
    preview = [
        {
            "artifact_id": artifact_id,
            "normalized_url": url,
            "package_manager": seed.get("package_manager"),
            "package_name": seed.get("package_name"),
            "probe": probe,
            "entrypoints": [str(path) for path in public_entrypoints(seed)],
        }
        for artifact_id, seed, probe, url in artifacts
    ]
    if not args.apply:
        print(json.dumps({"ok": True, "mode": "preview", "artifacts": preview}, indent=2))
        return 0

    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        store = ReceiptStore(RECEIPTS, RUNTIME_STATE)
        owned_keys = {
            (artifact_id, phase)
            for artifact_id, _seed, _probe, _url in artifacts
            for phase in ("identity", "install", "rollback")
        }
        snapshot = store.snapshot(artifact_keys=owned_keys)
        rows = snapshot.artifact_rows
        run_id = uuid.uuid4().hex
        staging_path = RUNTIME_STATE / "receipts" / ".staging" / JOURNAL_KIND / f"{run_id}.json"
        journal: dict[str, Any] = {
            "version": 2,
            "transaction_id": run_id,
            "kind": "cli",
            "receipt_revision_preimage": snapshot.revision,
            "started_at": datetime.now(UTC).isoformat(),
            "status": "running",
            "artifacts": [],
        }
        atomic_json(staging_path, journal)
        pending: list[dict[str, Any]] = []
        try:
            for artifact_id, seed, probe, url in artifacts:
                receipt, _ = rehearse_artifact(
                    artifact_id,
                    seed,
                    probe,
                    url,
                    rows,
                    journal,
                    staging_path,
                )
                pending.append(receipt)
            expected_artifact_ids = sorted(artifact_id for artifact_id, _seed, _probe, _url in artifacts)
            pending_artifact_ids = sorted(str(receipt["artifact_id"]) for receipt in pending)
            journal_artifact_ids = sorted(str(record["artifact_id"]) for record in journal["artifacts"])
            if pending_artifact_ids != expected_artifact_ids or journal_artifact_ids != expected_artifact_ids:
                raise RuntimeError("CLI rollback transaction artifact sets do not match")
        except BaseException as error:
            for record in journal["artifacts"]:
                if record.get("status") != "passed":
                    record["status"] = "failed"
            journal["status"] = "failed"
            journal["failed_at"] = datetime.now(UTC).isoformat()
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
        journal["status"] = "commit-pending"
        journal["completed_at"] = datetime.now(UTC).isoformat()
        atomic_json(staging_path, journal)
        journal_path = store.write_immutable_json(
            kind=JOURNAL_KIND,
            transaction_id=run_id,
            payload=journal,
        )
        staging_path.unlink(missing_ok=True)
        journal_sha256 = sha256_file(journal_path)
        upserts: dict[tuple[str, str], dict[str, Any]] = {}
        for receipt in pending:
            receipt["journal_sha256"] = journal_sha256
            receipt["journal_path"] = str(journal_path)
            receipt["journal_transaction_id"] = run_id
            key = (str(receipt["artifact_id"]), "rollback")
            upserts[key] = receipt
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
        commit_sha256 = sha256_file(commit_path)

    print(
        json.dumps(
            {
                "ok": True,
                "mode": "applied",
                "artifact_count": len(pending),
                "transaction_id": run_id,
                "journal_path": str(journal_path),
                "journal_sha256": journal_sha256,
                "commit_marker": str(commit_path),
                "commit_marker_sha256": commit_sha256,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
