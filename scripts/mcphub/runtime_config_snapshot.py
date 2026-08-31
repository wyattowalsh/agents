#!/usr/bin/env python3
"""Snapshot and restore exact non-secret MCPHub runtime/config targets."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import re
import shutil
import stat
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

AUTH_COLLECTIONS = ("bearerKeys", "oauthClients", "oauthTokens", "users")
SNAPSHOT_KIND = "mcphub-runtime-config-snapshot"
SNAPSHOT_VERSION = 1
MAX_CONFIG_BYTES = 16 * 1024 * 1024
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
DIGEST_POINTER_PATTERN = re.compile(r"^sha256-[a-f0-9]{64}$")
FORBIDDEN_COMPONENT_PATTERN = re.compile(
    r"(?:^|[._-])(oauth|token|secret|credential|cookie|session|receipt|log|pid|wal|shm)(?:[._-]|$)",
    re.IGNORECASE,
)
SENSITIVE_KEY_PATTERN = re.compile(
    r"password|secret|token|credential|cookie|authorization|api[_-]?key|private[_-]?key",
    re.IGNORECASE,
)
ENV_FIELD_PATTERN = re.compile(r"(?:^|[_-])env(?:ironment)?(?:[_-]vars?)?$", re.IGNORECASE)
ENV_REFERENCE_PATTERN = re.compile(
    r"(?:\$\{[A-Z][A-Z0-9_]*\}|\{env:[A-Z][A-Z0-9_]*\}|env:[A-Z][A-Z0-9_]*|"
    r"Bearer (?:\$\{[A-Z][A-Z0-9_]*\}|\{env:[A-Z][A-Z0-9_]*\}|\{file:[^\r\n]+\}))"
)
PLUGIN_IDENTIFIER_CONTAINER = "$.plugins"

TargetKind = Literal["exact-file", "structural-settings", "symlink"]


class SnapshotError(ValueError):
    """Raised when a snapshot or restore cannot remain exact and non-secret."""


@dataclass(frozen=True)
class TargetSpec:
    path: Path
    kind: TargetKind


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _current_uid() -> int:
    if not hasattr(os, "getuid"):
        raise SnapshotError("owner validation requires a POSIX runtime")
    return os.getuid()


def _require_absolute(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise SnapshotError(f"{label} must be absolute")
    return path


def _validate_directory(path: Path, label: str, *, owner_only: bool) -> os.stat_result:
    _require_absolute(path, label)
    try:
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise SnapshotError(f"{label} is missing") from exc
    if not stat.S_ISDIR(metadata.st_mode) or path.is_symlink():
        raise SnapshotError(f"{label} must be a non-symlink directory")
    if metadata.st_uid != _current_uid():
        raise SnapshotError(f"{label} owner mismatch")
    if metadata.st_mode & 0o022:
        raise SnapshotError(f"{label} must not be group- or other-writable")
    if owner_only and metadata.st_mode & 0o077:
        raise SnapshotError(f"{label} must be owner-only")
    if path.resolve(strict=True) != path:
        raise SnapshotError(f"{label} must not traverse a symlink")
    return metadata


def _reject_forbidden_path(path: Path) -> None:
    _require_absolute(path, "target path")
    for component in path.parts:
        lowered = component.lower()
        if lowered.startswith(".env") or lowered == ".things-auth" or FORBIDDEN_COMPONENT_PATTERN.search(component):
            raise SnapshotError("credential, OAuth, receipt, PID, WAL, or log paths are excluded")
    _validate_directory(path.parent, "target parent", owner_only=False)


def _open_regular_bytes(path: Path) -> tuple[bytes, os.stat_result]:
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or path.is_symlink():
        raise SnapshotError("snapshot file target must be a non-symlink regular file")
    if before.st_uid != _current_uid() or before.st_mode & 0o022:
        raise SnapshotError("snapshot file target has unsafe ownership or mode")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise SnapshotError("snapshot file identity changed while opening")
        if opened.st_size < 0 or opened.st_size > MAX_CONFIG_BYTES:
            raise SnapshotError("snapshot file size exceeds the bounded config limit")
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                raise SnapshotError("snapshot file ended before its recorded size")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks), opened
    finally:
        os.close(descriptor)


def _safe_reference(value: Any, key: str) -> bool:
    if value in (None, "") or isinstance(value, (bool, int, float)):
        return True
    if isinstance(value, str):
        stripped = value.strip()
        if ENV_REFERENCE_PATTERN.fullmatch(stripped) is not None:
            return True
        return ENV_FIELD_PATTERN.search(key) is not None and re.fullmatch(r"[A-Z][A-Z0-9_]*", stripped) is not None
    if isinstance(value, list):
        return all(_safe_reference(item, key) for item in value)
    return False


def _assert_no_embedded_secrets(value: Any, location: str = "$") -> None:
    if isinstance(value, dict):
        keys_are_plugin_identifiers = location == PLUGIN_IDENTIFIER_CONTAINER
        for key, child in value.items():
            key_text = str(key)
            if (
                not keys_are_plugin_identifiers
                and SENSITIVE_KEY_PATTERN.search(key_text)
                and not _safe_reference(child, key_text)
            ):
                raise SnapshotError(f"embedded credential value is forbidden at {location}.{key_text}")
            _assert_no_embedded_secrets(child, f"{location}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_embedded_secrets(child, f"{location}[{index}]")


def _parse_public_config(path: Path, data: bytes) -> Any:
    try:
        if path.suffix == ".toml":
            return tomllib.loads(data.decode("utf-8"))
        if path.suffix == ".json":
            return json.loads(data)
        if path.suffix == ".plist":
            return plistlib.loads(data)
    except (UnicodeDecodeError, tomllib.TOMLDecodeError, json.JSONDecodeError, plistlib.InvalidFileException) as exc:
        raise SnapshotError("config target does not parse as its declared format") from exc
    raise SnapshotError("exact-file targets must be JSON, TOML, or plist config")


def _non_secret_exact_bytes(path: Path, data: bytes) -> bytes:
    parsed = _parse_public_config(path, data)
    _assert_no_embedded_secrets(parsed)
    return data


def _structural_settings_bytes(data: bytes) -> bytes:
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise SnapshotError("structural settings must contain valid JSON") from exc
    if not isinstance(payload, dict):
        raise SnapshotError("structural settings must contain a JSON object")
    structural = {key: value for key, value in payload.items() if key not in AUTH_COLLECTIONS}
    _assert_no_embedded_secrets(structural)
    return (json.dumps(structural, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()


def _write_private_exclusive(path: Path, data: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(descriptor)
    os.chmod(path, 0o600)


def _write_private_atomic(path: Path, data: bytes, mode: int) -> None:
    _validate_directory(path.parent, "restore target parent", owner_only=False)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _entry_artifact(index: int) -> str:
    return f"entry-{index:04d}.bin"


def _capture_target(backup_root: Path, index: int, spec: TargetSpec) -> dict[str, Any]:
    path = _require_absolute(spec.path, "target path")
    _reject_forbidden_path(path)
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return {"target": str(path), "kind": spec.kind, "state": "absent"}

    if spec.kind == "symlink":
        if not stat.S_ISLNK(metadata.st_mode) or metadata.st_uid != _current_uid():
            raise SnapshotError("symlink target has unsafe type or owner")
        link_target = os.readlink(path)
        if DIGEST_POINTER_PATTERN.fullmatch(link_target) is None:
            raise SnapshotError("only an exact content-addressed runtime pointer may be snapshotted")
        _validate_directory(path.parent / link_target, "runtime pointer target", owner_only=True)
        link_bytes = link_target.encode()
        return {
            "target": str(path),
            "kind": spec.kind,
            "state": "present",
            "sha256": _sha256(link_bytes),
            "size": len(link_bytes),
            "owner": metadata.st_uid,
            "mode": stat.S_IMODE(metadata.st_mode),
            "linkTarget": link_target,
        }

    data, opened = _open_regular_bytes(path)
    artifact_bytes = (
        _structural_settings_bytes(data) if spec.kind == "structural-settings" else _non_secret_exact_bytes(path, data)
    )
    artifact = _entry_artifact(index)
    _write_private_exclusive(backup_root / artifact, artifact_bytes)
    entry: dict[str, Any] = {
        "target": str(path),
        "kind": spec.kind,
        "state": "present",
        "artifact": artifact,
        "sha256": _sha256(artifact_bytes),
        "size": len(artifact_bytes),
        "sourceSize": opened.st_size,
        "sourceSha256": _sha256(data),
        "owner": opened.st_uid,
        "mode": stat.S_IMODE(opened.st_mode),
    }
    if spec.kind == "structural-settings":
        entry["excludedCollections"] = list(AUTH_COLLECTIONS)
    return entry


def _validate_entry(entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise SnapshotError("snapshot entry must be an object")
    target = entry.get("target")
    kind = entry.get("kind")
    state = entry.get("state")
    if not isinstance(target, str) or not Path(target).is_absolute():
        raise SnapshotError("snapshot entry target must be absolute")
    if kind not in {"exact-file", "structural-settings", "symlink"} or state not in {"absent", "present"}:
        raise SnapshotError("snapshot entry kind or state is invalid")
    _reject_forbidden_path(Path(target))
    if state == "present":
        digest = entry.get("sha256")
        size = entry.get("size")
        if not isinstance(digest, str) or SHA256_PATTERN.fullmatch(digest) is None or not isinstance(size, int):
            raise SnapshotError("snapshot entry digest or size is invalid")
        if kind == "symlink":
            if DIGEST_POINTER_PATTERN.fullmatch(str(entry.get("linkTarget"))) is None:
                raise SnapshotError("snapshot pointer target is invalid")
        elif not isinstance(entry.get("artifact"), str):
            raise SnapshotError("snapshot file artifact is missing")
    return entry


def _load_snapshot(backup_root: Path) -> dict[str, Any]:
    _validate_directory(backup_root, "backup root", owner_only=True)
    manifest_path = backup_root / "snapshot.json"
    data, metadata = _open_regular_bytes(manifest_path)
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise SnapshotError("snapshot manifest must be owner-only")
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise SnapshotError("snapshot manifest is invalid JSON") from exc
    if not isinstance(payload, dict) or set(payload) != {"schemaVersion", "kind", "entries"}:
        raise SnapshotError("snapshot manifest contract is invalid")
    if payload["schemaVersion"] != SNAPSHOT_VERSION or payload["kind"] != SNAPSHOT_KIND:
        raise SnapshotError("snapshot manifest identity is invalid")
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        raise SnapshotError("snapshot manifest must contain entries")
    payload["entries"] = [_validate_entry(entry) for entry in entries]
    return payload


def _artifact_bytes(backup_root: Path, entry: dict[str, Any]) -> bytes:
    artifact_name = entry.get("artifact")
    if not isinstance(artifact_name, str) or Path(artifact_name).name != artifact_name:
        raise SnapshotError("snapshot artifact name is invalid")
    data, metadata = _open_regular_bytes(backup_root / artifact_name)
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise SnapshotError("snapshot artifact must be owner-only")
    if len(data) != entry["size"] or _sha256(data) != entry["sha256"]:
        raise SnapshotError("snapshot artifact digest or size mismatch")
    return data


def _prove_isolated_restore(backup_root: Path, payload: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory(prefix=".mcphub-snapshot-proof-", dir=backup_root.parent) as temporary_name:
        proof_root = Path(temporary_name)
        proof_root.chmod(0o700)
        _validate_directory(proof_root, "proof root", owner_only=True)
        for index, entry in enumerate(payload["entries"]):
            destination = proof_root / f"target-{index:04d}"
            if entry["state"] == "absent":
                if destination.exists() or destination.is_symlink():
                    raise SnapshotError("absent target appeared during restore proof")
                continue
            if entry["kind"] == "symlink":
                destination.symlink_to(entry["linkTarget"])
                if not destination.is_symlink() or os.readlink(destination) != entry["linkTarget"]:
                    raise SnapshotError("pointer restore proof failed")
                continue
            data = _artifact_bytes(backup_root, entry)
            _write_private_atomic(destination, data, int(entry["mode"]))
            restored, _ = _open_regular_bytes(destination)
            if restored != data:
                raise SnapshotError("file restore proof failed")
            if entry["kind"] == "structural-settings":
                parsed = json.loads(restored)
                if any(name in parsed for name in AUTH_COLLECTIONS):
                    raise SnapshotError("structural restore proof retained auth collections")


def create_snapshot(backup_root: Path, targets: list[TargetSpec]) -> dict[str, Any]:
    backup_root = _require_absolute(backup_root, "backup root")
    if not targets:
        raise SnapshotError("at least one exact target is required")
    if len({spec.path for spec in targets}) != len(targets):
        raise SnapshotError("snapshot targets must be unique")
    _validate_directory(backup_root.parent, "backup parent", owner_only=True)
    try:
        backup_root.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise SnapshotError("backup root already exists") from exc
    backup_root.chmod(0o700)
    try:
        entries = [_capture_target(backup_root, index, spec) for index, spec in enumerate(targets)]
        payload = {"schemaVersion": SNAPSHOT_VERSION, "kind": SNAPSHOT_KIND, "entries": entries}
        _write_private_exclusive(
            backup_root / "snapshot.json",
            (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode(),
        )
        verified = _load_snapshot(backup_root)
        _prove_isolated_restore(backup_root, verified)
        return {"operation": "snapshot", "entryCount": len(entries)}
    except Exception:
        shutil.rmtree(backup_root)
        raise


def verify_snapshot(backup_root: Path) -> dict[str, Any]:
    payload = _load_snapshot(backup_root)
    for entry in payload["entries"]:
        if entry["state"] == "present" and entry["kind"] != "symlink":
            _artifact_bytes(backup_root, entry)
    _prove_isolated_restore(backup_root, payload)
    return {"operation": "verify", "entryCount": len(payload["entries"])}


def _merge_current_auth(structural: bytes, current: bytes | None) -> tuple[bytes, dict[str, Any]]:
    structural_payload = json.loads(structural)
    if not isinstance(structural_payload, dict):
        raise SnapshotError("structural backup must contain an object")
    current_payload: dict[str, Any] = {}
    if current is not None:
        parsed = json.loads(current)
        if not isinstance(parsed, dict):
            raise SnapshotError("current structural settings must contain an object")
        current_payload = parsed
    preserved = {name: current_payload[name] for name in AUTH_COLLECTIONS if name in current_payload}
    structural_payload.update(preserved)
    restored = (json.dumps(structural_payload, indent=2, ensure_ascii=True) + "\n").encode()
    return restored, preserved


def restore_snapshot(backup_root: Path) -> dict[str, Any]:
    payload = _load_snapshot(backup_root)
    prepared: list[tuple[dict[str, Any], bytes | None, dict[str, Any] | None]] = []
    for entry in payload["entries"]:
        target = Path(entry["target"])
        _reject_forbidden_path(target)
        if entry["state"] == "absent":
            if target.exists() or target.is_symlink():
                raise SnapshotError("restore refuses to delete a target recorded as absent")
            prepared.append((entry, None, None))
            continue
        if entry["kind"] == "symlink":
            if target.exists() and not target.is_symlink():
                raise SnapshotError("restore refuses to replace a non-symlink pointer")
            _validate_directory(target.parent / entry["linkTarget"], "runtime pointer target", owner_only=True)
            prepared.append((entry, None, None))
            continue
        artifact = _artifact_bytes(backup_root, entry)
        if entry["kind"] == "structural-settings":
            current = _open_regular_bytes(target)[0] if target.exists() else None
            restored, preserved = _merge_current_auth(artifact, current)
            prepared.append((entry, restored, preserved))
        else:
            if target.exists():
                _open_regular_bytes(target)
            prepared.append((entry, artifact, None))

    for entry, data, preserved in prepared:
        target = Path(entry["target"])
        if entry["state"] == "absent":
            continue
        if entry["kind"] == "symlink":
            temporary = target.with_name(f".{target.name}.restore-{os.getpid()}")
            if temporary.exists() or temporary.is_symlink():
                raise SnapshotError("temporary restore pointer already exists")
            try:
                temporary.symlink_to(entry["linkTarget"])
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
            if not target.is_symlink() or os.readlink(target) != entry["linkTarget"]:
                raise SnapshotError("restored pointer readback failed")
            continue
        assert data is not None
        _write_private_atomic(target, data, int(entry["mode"]))
        readback, _ = _open_regular_bytes(target)
        if entry["kind"] == "structural-settings":
            readback_payload = json.loads(readback)
            readback_structural = {key: value for key, value in readback_payload.items() if key not in AUTH_COLLECTIONS}
            expected_structural = json.loads(_artifact_bytes(backup_root, entry))
            if readback_structural != expected_structural:
                raise SnapshotError("structural settings restore readback failed")
            if {name: readback_payload[name] for name in AUTH_COLLECTIONS if name in readback_payload} != preserved:
                raise SnapshotError("current auth collections changed during structural restore")
        elif readback != _artifact_bytes(backup_root, entry):
            raise SnapshotError("exact config restore readback failed")
    return {"operation": "restore", "entryCount": len(payload["entries"])}


def _target_specs(args: argparse.Namespace) -> list[TargetSpec]:
    specs: list[TargetSpec] = []
    specs.extend(TargetSpec(Path(value), "exact-file") for value in args.file or [])
    specs.extend(TargetSpec(Path(value), "structural-settings") for value in args.structural_settings or [])
    specs.extend(TargetSpec(Path(value), "symlink") for value in args.symlink or [])
    return specs


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    snapshot = subparsers.add_parser("snapshot")
    snapshot.add_argument("--backup-root", type=Path, required=True)
    snapshot.add_argument("--file", action="append")
    snapshot.add_argument("--structural-settings", action="append")
    snapshot.add_argument("--symlink", action="append")
    for operation in ("verify", "restore"):
        command = subparsers.add_parser(operation)
        command.add_argument("--backup-root", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        if args.operation == "snapshot":
            report = create_snapshot(args.backup_root, _target_specs(args))
        elif args.operation == "verify":
            report = verify_snapshot(args.backup_root)
        else:
            report = restore_snapshot(args.backup_root)
    except (OSError, SnapshotError, ValueError, json.JSONDecodeError):
        print('{"status":"error","reasonCode":"MCPHUB_RUNTIME_SNAPSHOT_FAILED"}')
        return 1
    print(json.dumps({"status": "ok", **report}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
