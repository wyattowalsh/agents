#!/usr/bin/env python3
"""Rehearse candidate plugin remove/re-add rollback in an isolated Codex home."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import secrets
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from wagents.candidate_evidence import (
    FILESYSTEM_DIGEST_ALGORITHM,
    RUNTIME_DIGEST_IGNORED_DIRS,
    receipt_metadata,
)
from wagents.candidate_plugin_provenance import plugin_content_sha256
from wagents.candidate_receipts import ReceiptStore

ROOT = Path(__file__).resolve().parents[1]
CANARY_SCRIPT = ROOT / "scripts" / "run_candidate_plugin_canaries.py"
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
RECEIPTS = MANIFEST_DIR / "runtime-activation-receipts.json"
RUNTIME_STATE = Path.home() / ".local" / "share" / "wagents" / "candidate-runtime"
LOCK_PATH = RUNTIME_STATE / "locks" / "candidate-plugin-rollback.lock"
JOURNAL_KIND = "candidate-plugin-rollback"
TRANSCRIPT_DIR = MANIFEST_DIR / "runtime-evidence" / "plugin-rollback"
MARKETPLACE_ROOTS = {
    "candidate-corpus-local": Path.home() / ".local" / "share" / "wagents" / "candidate-corpus-plugin-marketplace",
    "awesome-codex-plugins": Path.home() / ".codex" / ".tmp" / "marketplaces" / "awesome-codex-plugins",
}
DIGEST_IGNORED_DIRS = set(RUNTIME_DIGEST_IGNORED_DIRS)
DIGEST_ALGORITHM = FILESYSTEM_DIGEST_ALGORITHM
PLUGIN_SCOPE = "user-global-codex"
ROLLBACK_SCOPE = "isolated-codex-home"
REHEARSAL_KIND = "isolated-plugin-root-detach"
PROCESS_ID_FIELDS = (
    "marketplace",
    "initial_add",
    "initial_inventory",
    "remove",
    "fresh_absence",
    "restore",
    "restored_inventory",
    "restored_use_initial",
    "restored_use_fresh",
    "restored_use_discovery",
)
DISTINCT_LAUNCH_PHASES = tuple(value for value in PROCESS_ID_FIELDS if value != "restored_use_discovery")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run(argv: list[str], *, env: dict[str, str], cwd: Path = ROOT, timeout: int = 120) -> tuple[int, str, str, int]:
    process = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        raise RuntimeError(f"rollback command timed out: {argv!r}\n{stdout}\n{stderr}") from None
    return process.returncode, stdout, stderr, process.pid


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.wagents-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def bind_final_journal_sha(
    pending: dict[tuple[str, str], dict[str, Any]],
    journal_path: Path,
) -> str:
    journal_sha256 = hashlib.sha256(journal_path.read_bytes()).hexdigest()
    for receipt in pending.values():
        receipt["journal_sha256"] = journal_sha256
    return journal_sha256


def require_exact_artifact_sets(
    expected: list[str],
    pending: list[str],
    journal: list[str],
) -> list[str]:
    canonical = sorted(expected)
    if len(canonical) != len(set(canonical)):
        raise ValueError("plugin rollback artifact ids must be unique")
    if sorted(pending) != canonical or sorted(journal) != canonical:
        raise RuntimeError("plugin rollback transaction artifact sets do not match")
    return canonical


def content_manifest(root: Path) -> dict[str, tuple[str, int, bytes]]:
    """Capture install-root-independent plugin content without following links."""
    manifest: dict[str, tuple[str, int, bytes]] = {}

    def visit(path: Path, relative: str) -> None:
        metadata = path.lstat()
        mode = stat.S_IMODE(metadata.st_mode)
        if stat.S_ISLNK(metadata.st_mode):
            manifest[relative] = ("symlink", mode, os.readlink(path).encode())
            return
        if stat.S_ISREG(metadata.st_mode):
            manifest[relative] = ("file", mode, path.read_bytes())
            return
        if stat.S_ISDIR(metadata.st_mode):
            if relative != ".":
                manifest[relative] = ("directory", mode, b"")
            for child in sorted(path.iterdir(), key=lambda item: item.name):
                child_metadata = child.lstat()
                if child.name in DIGEST_IGNORED_DIRS and stat.S_ISDIR(child_metadata.st_mode):
                    continue
                child_relative = child.name if relative == "." else f"{relative}/{child.name}"
                visit(child, child_relative)
            return
        manifest[relative] = ("special", mode, f"{metadata.st_rdev}:{metadata.st_size}".encode())

    visit(root, ".")
    return manifest


def content_digest(root: Path) -> str:
    """Hash plugin content with the shared immutable provenance policy."""
    return plugin_content_sha256(root)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _is_launch_id(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 32:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def run_recorded(
    argv: list[str],
    *,
    env: dict[str, str],
    transcript: list[dict[str, Any]],
    phase: str,
    cwd: Path = ROOT,
    timeout: int = 120,
    display_argv: list[str] | None = None,
) -> tuple[int, str, str, int]:
    launch_id = secrets.token_hex(16)
    started_at_ns = time.time_ns()
    result = run(argv, env=env, cwd=cwd, timeout=timeout)
    returncode, stdout, stderr, pid = result
    transcript.append({
        "phase": phase,
        "argv": display_argv or argv,
        "returncode": returncode,
        "process_id": pid,
        "launch_id": launch_id,
        "started_at_ns": started_at_ns,
        "stdout_sha256": _sha256_text(stdout),
        "stderr_sha256": _sha256_text(stderr),
    })
    return result


def isolated_env(canaries, root: Path) -> dict[str, str]:
    env = canaries.sanitized_env()
    codex_home = root / "codex"
    home = root / "home"
    codex_home.mkdir(parents=True)
    home.mkdir(parents=True)
    env.update({
        "CODEX_HOME": str(codex_home),
        "HOME": str(home),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_DATA_HOME": str(home / ".local" / "share"),
    })
    return env


def inventory(
    env: dict[str, str],
    *,
    transcript: list[dict[str, Any]] | None = None,
    phase: str = "inventory",
) -> tuple[dict[str, dict[str, Any]], int]:
    argv = ["codex", "plugin", "list", "--json"]
    if transcript is None:
        returncode, stdout, stderr, pid = run(argv, env=env)
    else:
        returncode, stdout, stderr, pid = run_recorded(argv, env=env, transcript=transcript, phase=phase)
    require(returncode == 0, f"isolated Codex inventory failed: {stderr}")
    payload = json.loads(stdout)
    return {str(item["pluginId"]): item for item in payload.get("installed", [])}, pid


def validate_rollback_receipt(
    receipt: dict[str, Any],
    *,
    expected_artifact_id: str,
    expected_plugin_id: str,
) -> None:
    require(receipt.get("artifact_id") == expected_artifact_id, "rollback receipt has the wrong artifact id")
    require(receipt.get("phase") == "rollback", "rollback receipt has the wrong phase")
    require(receipt.get("plugin_id") == expected_plugin_id, "rollback receipt has the wrong plugin id")
    require(receipt.get("plugin_scope") == PLUGIN_SCOPE, "rollback receipt has the wrong plugin scope")
    require(receipt.get("scope") == ROLLBACK_SCOPE, "rollback receipt has the wrong execution scope")
    require(receipt.get("rehearsal_kind") == REHEARSAL_KIND, "rollback receipt has the wrong rehearsal kind")
    require(receipt.get("live_install_unchanged") is True, "rollback receipt did not prove live install stability")
    require(receipt.get("digest_algorithm") == DIGEST_ALGORITHM, "rollback receipt has the wrong digest algorithm")
    require(
        receipt.get("digest_ignored_dirs") == sorted(DIGEST_IGNORED_DIRS),
        "rollback receipt has the wrong digest exclusions",
    )
    process_ids = receipt.get("process_ids")
    if not isinstance(process_ids, dict):
        raise RuntimeError("rollback receipt omitted process ids")
    require(set(process_ids) == set(PROCESS_ID_FIELDS), "rollback receipt has an incomplete process-id set")
    values = list(process_ids.values())
    require(all(isinstance(value, int) and value > 0 for value in values), "rollback process ids must be positive")
    launch_evidence = receipt.get("launch_evidence")
    if not isinstance(launch_evidence, dict):
        raise RuntimeError("rollback receipt omitted launch evidence")
    require(set(launch_evidence) == set(PROCESS_ID_FIELDS), "rollback receipt has an incomplete launch-evidence set")
    for phase, evidence in launch_evidence.items():
        require(isinstance(evidence, dict), f"rollback launch evidence is invalid: {phase}")
        require(_is_launch_id(evidence.get("launch_id")), f"rollback launch id is invalid: {phase}")
        require(
            isinstance(evidence.get("started_at_ns"), int) and evidence["started_at_ns"] > 0,
            f"rollback launch timestamp is invalid: {phase}",
        )
        require(
            evidence.get("process_id") == process_ids[phase],
            f"rollback launch process id drifted: {phase}",
        )
    distinct_launch_ids = [launch_evidence[phase]["launch_id"] for phase in DISTINCT_LAUNCH_PHASES]
    require(
        len(distinct_launch_ids) == len(set(distinct_launch_ids)),
        "rollback proof reused a launch identity across distinct phases",
    )
    discovery_launch = launch_evidence["restored_use_discovery"]
    initial_launch = launch_evidence["restored_use_initial"]
    if discovery_launch["launch_id"] == initial_launch["launch_id"]:
        require(discovery_launch == initial_launch, "discovery launch alias drifted from initial semantic use")
    else:
        require(
            discovery_launch["launch_id"] not in set(distinct_launch_ids),
            "discovery reused an unrelated launch identity",
        )
    require(_is_sha256(receipt.get("restored_use_output_sha256")), "rollback output digest is invalid")
    require(receipt.get("preimage_digest") == receipt.get("rollback_digest"), "rollback did not restore the preimage")
    require(
        receipt.get("restored_installed_digest") == receipt.get("rollback_digest"),
        "restored-use digest is not bound to the rollback digest",
    )

    raw_path = Path(str(receipt.get("transcript_path") or "")).expanduser()
    require(bool(str(raw_path)) and raw_path.is_absolute(), "rollback transcript path must be absolute")
    transcript_path = raw_path.resolve()
    expected_path = (
        RUNTIME_STATE
        / "receipts"
        / "transcripts"
        / JOURNAL_KIND
        / f"{expected_artifact_id}-{receipt.get('transaction_id')}.json"
    ).resolve()
    require(transcript_path == expected_path, "rollback transcript path does not match its artifact transaction")
    require(transcript_path.is_file(), "rollback transcript is missing")
    transcript_digest = hashlib.sha256(transcript_path.read_bytes()).hexdigest()
    require(receipt.get("transcript_sha256") == transcript_digest, "rollback transcript digest is stale")
    payload = json.loads(transcript_path.read_text(encoding="utf-8"))
    require(payload.get("artifact_id") == expected_artifact_id, "rollback transcript has the wrong artifact id")
    require(payload.get("plugin_id") == expected_plugin_id, "rollback transcript has the wrong plugin id")
    require(
        payload.get("transaction_id") == receipt.get("transaction_id"),
        "rollback transcript has the wrong transaction id",
    )
    require(payload.get("process_ids") == process_ids, "rollback transcript process ids drifted")
    require(payload.get("launch_evidence") == launch_evidence, "rollback transcript launch evidence drifted")
    require(payload.get("live_install_unchanged") is True, "rollback transcript did not bind live install stability")


def read_receipt_document() -> dict[str, Any]:
    return ReceiptStore(RECEIPTS, RUNTIME_STATE).load()


def read_receipts() -> dict[tuple[str, str], dict[str, Any]]:
    rows = read_receipt_document().get("receipts", [])
    return {(str(row["artifact_id"]), str(row["phase"])): row for row in rows}


def write_receipts(rows: dict[tuple[str, str], dict[str, Any]]) -> None:
    store = ReceiptStore(RECEIPTS, RUNTIME_STATE)
    snapshot = store.snapshot(artifact_keys=set(rows))
    store.commit(snapshot, artifact_upserts=rows)


def rollback_plan(canaries: Any, activation: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    specs = canaries.all_plugin_specs()
    enabled_specs = canaries.enabled_plugin_specs(specs)
    for plugin_id, (url, seed) in sorted(specs.items()):
        enabled = plugin_id in enabled_specs
        manager = str(seed.get("package_manager") or "")
        item: dict[str, Any] = {
            "plugin_id": plugin_id,
            "artifact_id": activation.artifact_id(url, seed),
            "package_manager": manager,
            "status": "ready" if enabled else "blocked",
            "blocker": "",
        }
        if enabled:
            marketplace = plugin_id.rsplit("@", 1)[1]
            item.update({
                "live_root": str(canaries.plugin_root(seed)),
                "marketplace_root": str(MARKETPLACE_ROOTS[marketplace]),
            })
        elif manager == "opencode-plugin":
            item["blocker"] = "opencode-plugin-not-configured-and-no-isolated-rollback-adapter"
        else:
            item["blocker"] = "plugin-disabled-by-audited-policy"
        result.append(item)
    return result


def rehearse(
    plugin_id: str,
    url: str,
    seed: dict[str, Any],
    artifact_id: str,
    canaries,
    rows: dict[tuple[str, str], dict[str, Any]],
    provenance: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    install = rows.get((artifact_id, "install"))
    if install is None:
        raise RuntimeError(f"missing install receipt for {plugin_id}")
    expected_live_digest = str(install["installed_digest"])
    behavior = rows.get((artifact_id, "behavior"))
    fresh_process = rows.get((artifact_id, "fresh_process"))
    if behavior is None:
        raise RuntimeError(f"missing behavior receipt for {plugin_id}")
    if fresh_process is None:
        raise RuntimeError(f"missing fresh-process receipt for {plugin_id}")
    require(
        behavior.get("happy_path_status") == "passed" and behavior.get("installed_digest") == expected_live_digest,
        f"missing current passing behavior receipt for {plugin_id}",
    )
    require(
        fresh_process.get("fresh_use_status") == "passed"
        and fresh_process.get("installed_digest") == expected_live_digest,
        f"missing current passing fresh-process receipt for {plugin_id}",
    )
    for phase, receipt in (("install", install), ("behavior", behavior), ("fresh_process", fresh_process)):
        require(receipt.get("digest_algorithm") == DIGEST_ALGORITHM, f"{phase} digest algorithm drifted: {plugin_id}")
        require(
            receipt.get("digest_ignored_dirs") == sorted(DIGEST_IGNORED_DIRS),
            f"{phase} digest exclusions drifted: {plugin_id}",
        )
    live_root = canaries.plugin_root(seed)
    require(live_root.is_dir(), f"live plugin root is missing: {live_root}")
    require(canaries.file_digest([live_root]) == expected_live_digest, f"live plugin digest drifted: {plugin_id}")

    identity = rows.get((artifact_id, "identity"))
    if identity is None:
        raise RuntimeError(f"missing identity receipt for {plugin_id}")
    source_commit_sha = str(identity.get("source_commit_sha") or "")
    package_id = str(identity.get("package_id") or install.get("package_id") or "")
    resolved_version = str(identity.get("resolved_version") or seed.get("version") or "")
    require(
        bool(source_commit_sha and package_id and resolved_version),
        f"identity metadata is incomplete: {plugin_id}",
    )

    _, marketplace = plugin_id.rsplit("@", 1)
    marketplace_root = MARKETPLACE_ROOTS.get(marketplace)
    require(marketplace_root is not None and marketplace_root.is_dir(), f"marketplace snapshot missing: {marketplace}")
    source_root = canaries.marketplace_plugin_source(plugin_id, marketplace_root, provenance)
    canaries.verify_marketplace_checkout(source_root, provenance)
    canaries.verify_plugin_content(source_root, provenance, label=f"rollback marketplace source for {plugin_id}")
    canaries.verify_plugin_content(live_root, provenance, label=f"rollback live install for {plugin_id}")
    canaries.validate_plugin_surfaces(plugin_id, source_root)
    canaries.validate_plugin_surfaces(plugin_id, live_root)
    live_state = canaries.codex_plugin_live_state(
        canaries.HOST_CODEX_HOME / "config.toml",
        canaries.CODEX_CACHE,
        provenance,
    )
    require(live_state["enabled"] is True, f"live plugin is disabled before rollback: {plugin_id}")
    require(live_state["installed"] is True, f"live plugin cache is missing before rollback: {plugin_id}")
    transaction_id = uuid.uuid4().hex

    with tempfile.TemporaryDirectory(prefix=f"wagents-plugin-rollback-{marketplace}-") as raw:
        isolated_root = Path(raw)
        env = isolated_env(canaries, isolated_root)
        command_transcript: list[dict[str, Any]] = []
        add_marketplace = ["codex", "plugin", "marketplace", "add", str(marketplace_root), "--json"]
        returncode, _, stderr, marketplace_pid = run_recorded(
            add_marketplace,
            env=env,
            transcript=command_transcript,
            phase="marketplace-add",
            display_argv=["codex", "plugin", "marketplace", "add", "<marketplace-root>", "--json"],
        )
        require(returncode == 0, f"isolated marketplace add failed for {plugin_id}: {stderr}")

        returncode, add_stdout, add_stderr, initial_add_pid = run_recorded(
            ["codex", "plugin", "add", plugin_id, "--json"],
            env=env,
            transcript=command_transcript,
            phase="initial-add",
        )
        require(returncode == 0, f"isolated plugin add failed for {plugin_id}: {add_stderr}")
        add_payload = json.loads(add_stdout)
        installed_path = Path(str(add_payload["installedPath"]))
        require(installed_path.is_dir(), f"isolated plugin root missing after add: {installed_path}")
        canaries.verify_plugin_content(
            installed_path,
            provenance,
            label=f"rollback initial isolated install for {plugin_id}",
        )
        canaries.validate_plugin_surfaces(plugin_id, installed_path)
        preimage_digest = canaries.file_digest([installed_path])
        before, before_pid = inventory(env, transcript=command_transcript, phase="initial-inventory")
        require(before.get(plugin_id, {}).get("enabled") is True, f"isolated plugin is not enabled: {plugin_id}")

        returncode, _, remove_stderr, remove_pid = run_recorded(
            ["codex", "plugin", "remove", plugin_id, "--json"],
            env=env,
            transcript=command_transcript,
            phase="remove",
        )
        require(returncode == 0, f"isolated plugin removal failed for {plugin_id}: {remove_stderr}")
        absent, absence_pid = inventory(env, transcript=command_transcript, phase="absence-inventory")
        require(
            plugin_id not in absent and not installed_path.exists(),
            f"isolated plugin remained after removal: {plugin_id}",
        )

        returncode, restore_stdout, restore_stderr, restore_pid = run_recorded(
            ["codex", "plugin", "add", plugin_id, "--json"],
            env=env,
            transcript=command_transcript,
            phase="restore",
        )
        require(returncode == 0, f"isolated plugin restoration failed for {plugin_id}: {restore_stderr}")
        restored_path = Path(str(json.loads(restore_stdout)["installedPath"]))
        require(restored_path.resolve() == installed_path.resolve(), f"restored plugin path drifted: {plugin_id}")
        canaries.verify_plugin_content(
            restored_path,
            provenance,
            label=f"rollback restored isolated install for {plugin_id}",
        )
        canaries.validate_plugin_surfaces(plugin_id, restored_path)
        after, after_pid = inventory(env, transcript=command_transcript, phase="restored-inventory")
        require(after.get(plugin_id, {}).get("enabled") is True, f"restored plugin is not enabled: {plugin_id}")
        rollback_digest = canaries.file_digest([restored_path])
        require(rollback_digest == preimage_digest, f"isolated rollback changed plugin bytes: {plugin_id}")
        require(
            canaries.file_digest([live_root]) == expected_live_digest,
            f"isolated rollback changed live plugin: {plugin_id}",
        )
        canaries.verify_plugin_content(
            live_root,
            provenance,
            label=f"rollback unchanged live install for {plugin_id}",
        )
        probe_name = (canaries.MODEL_PLUGINS if plugin_id in canaries.MODEL_PLUGINS else canaries.SCRIPT_PLUGINS)[
            plugin_id
        ]
        restored_probe = canaries.probe_installed_plugin(
            plugin_id,
            probe_name,
            restored_path,
            env,
            isolated_root,
            after_pid,
        )
        canaries.verify_plugin_content(
            restored_path,
            provenance,
            label=f"rollback post-probe isolated install for {plugin_id}",
        )

        process_ids = {
            "marketplace": marketplace_pid,
            "initial_add": initial_add_pid,
            "initial_inventory": before_pid,
            "remove": remove_pid,
            "fresh_absence": absence_pid,
            "restore": restore_pid,
            "restored_inventory": after_pid,
            "restored_use_initial": restored_probe.initial_pid,
            "restored_use_fresh": restored_probe.fresh_pid,
            "restored_use_discovery": restored_probe.discovery_process_id,
        }
        process_values = list(process_ids.values())
        require(
            all(isinstance(value, int) and value > 0 for value in process_values),
            f"rollback process ids must be positive: {plugin_id}",
        )
        require(_is_sha256(restored_probe.output_sha256), f"rollback output digest is invalid: {plugin_id}")

        command_launches = {str(row["phase"]): row for row in command_transcript}

        def command_launch(transcript_phase: str, process_phase: str) -> dict[str, Any]:
            row = command_launches[transcript_phase]
            require(row.get("process_id") == process_ids[process_phase], f"launch PID drifted: {process_phase}")
            return {
                "launch_id": row["launch_id"],
                "started_at_ns": row["started_at_ns"],
                "process_id": row["process_id"],
            }

        launch_evidence = {
            "marketplace": command_launch("marketplace-add", "marketplace"),
            "initial_add": command_launch("initial-add", "initial_add"),
            "initial_inventory": command_launch("initial-inventory", "initial_inventory"),
            "remove": command_launch("remove", "remove"),
            "fresh_absence": command_launch("absence-inventory", "fresh_absence"),
            "restore": command_launch("restore", "restore"),
            "restored_inventory": command_launch("restored-inventory", "restored_inventory"),
            "restored_use_initial": {
                "launch_id": restored_probe.initial_launch_id,
                "started_at_ns": restored_probe.initial_started_at_ns,
                "process_id": restored_probe.initial_pid,
            },
            "restored_use_fresh": {
                "launch_id": restored_probe.fresh_launch_id,
                "started_at_ns": restored_probe.fresh_started_at_ns,
                "process_id": restored_probe.fresh_pid,
            },
            "restored_use_discovery": {
                "launch_id": restored_probe.discovery_launch_id,
                "started_at_ns": restored_probe.discovery_started_at_ns,
                "process_id": restored_probe.discovery_process_id,
            },
        }

        record = {
            "artifact_id": artifact_id,
            "normalized_url": url,
            "plugin_id": plugin_id,
            "transaction_id": transaction_id,
            "scope": ROLLBACK_SCOPE,
            "plugin_scope": PLUGIN_SCOPE,
            "rehearsal_kind": REHEARSAL_KIND,
            "marketplace_root": str(marketplace_root),
            "preimage_digest": preimage_digest,
            "rollback_digest": rollback_digest,
            "promoted_final_digest": expected_live_digest,
            "marketplace_process_id": marketplace_pid,
            "initial_add_process_id": initial_add_pid,
            "initial_inventory_process_id": before_pid,
            "remove_process_id": remove_pid,
            "fresh_absence_process_id": absence_pid,
            "restore_process_id": restore_pid,
            "restored_inventory_process_id": after_pid,
            "restored_use_initial_process_id": restored_probe.initial_pid,
            "restored_use_process_id": restored_probe.fresh_pid,
            "restored_use_discovery_process_id": restored_probe.discovery_process_id,
            "restored_use_output_sha256": restored_probe.output_sha256,
            "restored_installed_digest": rollback_digest,
            "restored_use_status": "passed",
            "live_install_unchanged": True,
            "process_ids": process_ids,
            "launch_evidence": launch_evidence,
            "status": "passed",
        }
        transcript_payload = {
            "version": 1,
            "transaction_id": transaction_id,
            "artifact_id": artifact_id,
            "normalized_url": url,
            "plugin_id": plugin_id,
            "plugin_scope": PLUGIN_SCOPE,
            "scope": ROLLBACK_SCOPE,
            "rehearsal_kind": REHEARSAL_KIND,
            "digest_algorithm": DIGEST_ALGORITHM,
            "digest_ignored_dirs": sorted(DIGEST_IGNORED_DIRS),
            "preimage_digest": preimage_digest,
            "rollback_digest": rollback_digest,
            "promoted_final_digest": expected_live_digest,
            "live_install_unchanged": True,
            "fresh_absence_process_id": absence_pid,
            "restored_use_process_id": restored_probe.fresh_pid,
            "restored_use_output_sha256": restored_probe.output_sha256,
            "process_ids": process_ids,
            "launch_evidence": launch_evidence,
            "commands": command_transcript,
            "restored_probe": {
                "fixture_id": restored_probe.fixture_id,
                "probe_kind": restored_probe.probe_kind,
                "assertions": list(restored_probe.assertions),
                "output_sha256": restored_probe.output_sha256,
                "discovery_output_sha256": restored_probe.discovery_output_sha256,
            },
        }
        transcript_path = ReceiptStore(RECEIPTS, RUNTIME_STATE).write_immutable_json(
            kind=JOURNAL_KIND,
            transaction_id=f"{artifact_id}-{transaction_id}",
            payload=transcript_payload,
            bucket="transcripts",
        )
        transcript_relative = str(transcript_path)
        transcript_sha256 = hashlib.sha256(transcript_path.read_bytes()).hexdigest()
        receipt = {
            "artifact_id": artifact_id,
            "phase": "rollback",
            "preimage_digest": preimage_digest,
            "rollback_digest": rollback_digest,
            "promoted_final_digest": expected_live_digest,
            "fresh_absence_status": "passed",
            "promoted_final_status": "passed",
            "rehearsal_kind": REHEARSAL_KIND,
            "plugin_id": plugin_id,
            "plugin_scope": PLUGIN_SCOPE,
            "scope": ROLLBACK_SCOPE,
            "transaction_id": transaction_id,
            "fresh_absence_process_id": absence_pid,
            "restored_discovery_status": "passed",
            "restored_inventory_process_id": after_pid,
            "restored_use_initial_process_id": restored_probe.initial_pid,
            "restored_use_process_id": restored_probe.fresh_pid,
            "restored_use_discovery_process_id": restored_probe.discovery_process_id,
            "restored_use_output_sha256": restored_probe.output_sha256,
            "restored_installed_digest": rollback_digest,
            "restored_use_status": "passed",
            "live_install_unchanged": True,
            "process_ids": process_ids,
            "launch_evidence": launch_evidence,
            "transcript_path": transcript_relative,
            "transcript_sha256": transcript_sha256,
        }
        receipt.update(
            receipt_metadata(
                artifact_id=artifact_id,
                phase="rollback",
                source_commit_sha=source_commit_sha,
                package_id=package_id,
                resolved_version=resolved_version,
                installed_digest=expected_live_digest,
            )
        )
        receipt["digest_algorithm"] = DIGEST_ALGORITHM
        receipt["digest_ignored_dirs"] = sorted(DIGEST_IGNORED_DIRS)
        validate_rollback_receipt(
            receipt,
            expected_artifact_id=artifact_id,
            expected_plugin_id=plugin_id,
        )
        record["transcript_path"] = transcript_relative
        record["transcript_sha256"] = transcript_sha256
        return receipt, record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--allow-audited-execution", action="store_true")
    parser.add_argument("--allow-model-execution", action="store_true")
    parser.add_argument("--plugin", action="append")
    args = parser.parse_args()

    canaries = load_module("_candidate_plugin_canaries_for_rollback", CANARY_SCRIPT)
    activation = canaries.activation_module()
    specs = canaries.all_plugin_specs()
    enabled_specs = canaries.enabled_plugin_specs(specs)
    provenance_entries = canaries.verified_provenance_lock(enabled_specs)
    requested = set(args.plugin or specs)
    unknown = sorted(requested - set(specs))
    if unknown:
        raise ValueError(f"unknown candidate plugin ids: {unknown}")
    provenance_failures: dict[str, str] = {}
    for plugin_id in sorted(requested & set(enabled_specs)):
        try:
            entry = provenance_entries[plugin_id]
            marketplace = plugin_id.rsplit("@", 1)[1]
            source_root = canaries.marketplace_plugin_source(
                plugin_id,
                MARKETPLACE_ROOTS[marketplace],
                entry,
            )
            live_root = canaries.plugin_root(enabled_specs[plugin_id][1])
            canaries.verify_marketplace_checkout(source_root, entry)
            canaries.verify_plugin_content(
                source_root,
                entry,
                label=f"rollback marketplace source for {plugin_id}",
            )
            canaries.verify_plugin_content(
                live_root,
                entry,
                label=f"rollback live install for {plugin_id}",
            )
            live_state = canaries.codex_plugin_live_state(
                canaries.HOST_CODEX_HOME / "config.toml",
                canaries.CODEX_CACHE,
                entry,
            )
            require(
                live_state["enabled"] is True and live_state["installed"] is True,
                f"live plugin activation is incomplete before rollback: {plugin_id}",
            )
        except (KeyError, OSError, RuntimeError, ValueError) as error:
            provenance_failures[plugin_id] = f"{type(error).__name__}: {error}"
    if provenance_failures:
        print(
            json.dumps(
                {
                    "ok": False,
                    "mode": "provenance-blocked",
                    "artifact_count": len(requested),
                    "provenance_failures": provenance_failures,
                },
                indent=2,
            )
        )
        return 1
    preview = [item for item in rollback_plan(canaries, activation) if item["plugin_id"] in requested]
    blockers = [item for item in preview if item["status"] == "blocked"]
    if blockers:
        print(
            json.dumps(
                {
                    "ok": False,
                    "mode": "blocked",
                    "artifact_count": len(preview),
                    "blocked_count": len(blockers),
                    "artifacts": preview,
                },
                indent=2,
            )
        )
        return 1
    if not args.apply:
        print(json.dumps({"ok": True, "mode": "preview", "artifacts": preview}, indent=2))
        return 0
    unauthorized = [
        {
            "plugin_id": plugin_id,
            "status": "execution-required",
            "requirements": canaries.execution_requirements(plugin_id),
        }
        for plugin_id in sorted(requested)
        if not canaries.execution_authorized(
            plugin_id,
            allow_model_execution=args.allow_model_execution,
            allow_audited_execution=args.allow_audited_execution,
        )
    ]
    if unauthorized:
        print(
            json.dumps(
                {
                    "ok": False,
                    "mode": "execution-required",
                    "artifact_count": len(preview),
                    "pending_execution": unauthorized,
                },
                indent=2,
            )
        )
        return 1

    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        store = ReceiptStore(RECEIPTS, RUNTIME_STATE)
        requested_artifacts = {
            plugin_id: activation.artifact_id(specs[plugin_id][0], specs[plugin_id][1]) for plugin_id in requested
        }
        expected_artifact_ids = require_exact_artifact_sets(
            list(requested_artifacts.values()),
            list(requested_artifacts.values()),
            list(requested_artifacts.values()),
        )
        owned_keys = {
            (artifact_id, phase)
            for artifact_id in requested_artifacts.values()
            for phase in ("identity", "install", "behavior", "fresh_process", "rollback")
        }
        snapshot = store.snapshot(artifact_keys=owned_keys)
        rows = snapshot.artifact_rows
        run_id = uuid.uuid4().hex
        staging_path = RUNTIME_STATE / "receipts" / ".staging" / JOURNAL_KIND / f"{run_id}.json"
        journal: dict[str, Any] = {
            "version": 2,
            "transaction_id": run_id,
            "kind": "plugin",
            "receipt_revision_preimage": snapshot.revision,
            "started_at": datetime.now(UTC).isoformat(),
            "scope": "isolated-codex-home",
            "status": "running",
            "artifacts": [],
        }
        atomic_json(staging_path, journal)
        pending: dict[tuple[str, str], dict[str, Any]] = {}
        try:
            for plugin_id in sorted(requested):
                url, seed = specs[plugin_id]
                artifact_id = requested_artifacts[plugin_id]
                receipt, record = rehearse(
                    plugin_id,
                    url,
                    seed,
                    artifact_id,
                    canaries,
                    rows,
                    provenance_entries[plugin_id],
                )
                pending[artifact_id, "rollback"] = receipt
                journal["artifacts"].append(record)
                atomic_json(staging_path, journal)
            pending_artifact_ids = sorted(str(receipt["artifact_id"]) for receipt in pending.values())
            journal_artifact_ids = sorted(str(record["artifact_id"]) for record in journal["artifacts"])
            require_exact_artifact_sets(expected_artifact_ids, pending_artifact_ids, journal_artifact_ids)
        except BaseException as error:
            journal["status"] = "failed"
            journal["error_type"] = type(error).__name__
            journal["completed_at"] = datetime.now(UTC).isoformat()
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
            journal["completed_at"] = datetime.now(UTC).isoformat()
            atomic_json(staging_path, journal)
            journal_path = store.write_immutable_json(
                kind=JOURNAL_KIND,
                transaction_id=run_id,
                payload=journal,
            )
            staging_path.unlink(missing_ok=True)
            journal_sha256 = bind_final_journal_sha(pending, journal_path)
            for receipt in pending.values():
                receipt["journal_path"] = str(journal_path)
                receipt["journal_transaction_id"] = run_id
            try:
                commit_result = store.commit(snapshot, artifact_upserts=pending)
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

    print(
        json.dumps(
            {
                "ok": True,
                "mode": "isolated-apply",
                "artifact_count": len(pending),
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
