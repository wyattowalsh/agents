#!/usr/bin/env python3
"""Persist only verified Things core artifact paths in the private MCPHub env."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path

WHEEL_NAME = "mcp_server_things-1.9.0-py3-none-any.whl"
SDIST_NAME = "mcp_server_things-1.9.0.tar.gz"
WHEEL_SHA256 = "720f27aaabe76c3daddd2d92d4fd15bed0111b9eb390dca4b56284f950b9ce2c"
SDIST_SHA256 = "99a6f630a0b80fe12a95ccf36a727b1dbc667ce60a6cc30ad1d391f4071e9bd0"
MAX_ARTIFACT_BYTES = 20_000_000
MAX_ENV_BYTES = 1_048_576
SAFE_PATH = re.compile(r"^/[A-Za-z0-9._/-]+$")
ASSIGNMENT = re.compile(
    rb"^(?P<prefix>export[ \t]+)?(?P<key>THINGS_CORE_(?:WHEEL|SDIST)_PATH)=(?P<value>[^\r\n]*)(?P<ending>\r?\n)?$"
)


class ArtifactConfigurationError(RuntimeError):
    """The private env update cannot be proven safe."""


@dataclass(frozen=True, slots=True)
class StableFile:
    path: Path
    bytes: bytes
    device: int
    inode: int
    mode: int


def _absolute(path: Path, label: str) -> Path:
    if not path.is_absolute() or path != Path(os.path.normpath(path)):
        raise ArtifactConfigurationError(f"{label} must be normalized and absolute")
    return path


def _validate_parent(path: Path, label: str) -> None:
    parent = _absolute(path.parent, f"{label} parent")
    metadata = parent.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or parent.is_symlink():
        raise ArtifactConfigurationError(f"{label} parent must be a real directory")
    if metadata.st_uid != os.getuid() or metadata.st_mode & 0o022:
        raise ArtifactConfigurationError(f"{label} parent ownership or mode is unsafe")


def _read_stable(path: Path, *, label: str, maximum_bytes: int, owner_only: bool) -> StableFile:
    _absolute(path, label)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or path.is_symlink() or before.st_nlink != 1:
        raise ArtifactConfigurationError(f"{label} must be one regular file")
    if before.st_uid != os.getuid() or before.st_mode & 0o022:
        raise ArtifactConfigurationError(f"{label} ownership or mode is unsafe")
    if owner_only and before.st_mode & 0o077:
        raise ArtifactConfigurationError(f"{label} must be owner-only")
    if before.st_size < 1 or before.st_size > maximum_bytes:
        raise ArtifactConfigurationError(f"{label} size is invalid")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino, opened.st_size) != (
            before.st_dev,
            before.st_ino,
            before.st_size,
        ):
            raise ArtifactConfigurationError(f"{label} identity changed")
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining:
            chunk = os.read(descriptor, min(1_048_576, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        after = path.lstat()
        if (after.st_dev, after.st_ino, after.st_size) != (opened.st_dev, opened.st_ino, opened.st_size) or len(
            payload
        ) != opened.st_size:
            raise ArtifactConfigurationError(f"{label} changed while reading")
        return StableFile(path, payload, opened.st_dev, opened.st_ino, stat.S_IMODE(opened.st_mode))
    finally:
        os.close(descriptor)


def _verify_artifact(path: Path, expected_sha256: str, label: str) -> None:
    artifact = _read_stable(path, label=label, maximum_bytes=MAX_ARTIFACT_BYTES, owner_only=False)
    if hashlib.sha256(artifact.bytes).hexdigest() != expected_sha256:
        raise ArtifactConfigurationError(f"{label} digest mismatch")


def _path_assignment(key: bytes, value: Path, ending: bytes = b"\n") -> bytes:
    encoded = os.fsencode(value)
    if not SAFE_PATH.fullmatch(os.fsdecode(encoded)):
        raise ArtifactConfigurationError("artifact path contains unsafe dotenv characters")
    return key + b"=" + encoded + ending


def _updated_env(payload: bytes, *, wheel: Path, sdist: Path) -> bytes:
    try:
        payload.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ArtifactConfigurationError("private env is not strict UTF-8") from exc
    expected = {
        b"THINGS_CORE_WHEEL_PATH": wheel,
        b"THINGS_CORE_SDIST_PATH": sdist,
    }
    seen: set[bytes] = set()
    output: list[bytes] = []
    for line in payload.splitlines(keepends=True):
        match = ASSIGNMENT.fullmatch(line)
        if match is None:
            output.append(line)
            continue
        key = match.group("key")
        if key in seen:
            raise ArtifactConfigurationError("private env contains duplicate Things core path keys")
        seen.add(key)
        output.append(_path_assignment(key, expected[key], match.group("ending") or b"\n"))
    missing = [key for key in expected if key not in seen]
    if missing:
        if output and not output[-1].endswith((b"\n", b"\r")):
            output.append(b"\n")
        output.extend(_path_assignment(key, expected[key]) for key in missing)
    return b"".join(output)


def _same_file(snapshot: StableFile) -> bool:
    try:
        current = _read_stable(
            snapshot.path,
            label="private env publication source",
            maximum_bytes=MAX_ENV_BYTES,
            owner_only=True,
        )
    except (ArtifactConfigurationError, OSError):
        return False
    return (current.device, current.inode, current.mode) == (
        snapshot.device,
        snapshot.inode,
        snapshot.mode,
    ) and current.bytes == snapshot.bytes


def _replace_private_env(path: Path, original: StableFile, updated: bytes) -> None:
    _validate_parent(path, "private env")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.things-core-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(updated)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        if not _same_file(original):
            raise ArtifactConfigurationError("private env changed before publication")
        os.replace(temporary, path)
        published = _read_stable(path, label="published private env", maximum_bytes=MAX_ENV_BYTES, owner_only=True)
        if published.bytes != updated or published.mode != 0o600:
            raise ArtifactConfigurationError("private env publication verification failed")
    finally:
        temporary.unlink(missing_ok=True)


def configure(env_path: Path, artifact_directory: Path, *, check: bool) -> dict[str, object]:
    env_path = _absolute(env_path, "private env")
    artifact_directory = _absolute(artifact_directory, "artifact directory")
    _validate_parent(artifact_directory / WHEEL_NAME, "artifact")
    wheel = artifact_directory / WHEEL_NAME
    sdist = artifact_directory / SDIST_NAME
    _verify_artifact(wheel, WHEEL_SHA256, "Things core wheel")
    _verify_artifact(sdist, SDIST_SHA256, "Things core sdist")
    original = _read_stable(env_path, label="private env", maximum_bytes=MAX_ENV_BYTES, owner_only=True)
    updated = _updated_env(original.bytes, wheel=wheel, sdist=sdist)
    changed = updated != original.bytes
    if check and changed:
        raise ArtifactConfigurationError("Things core artifact paths are not configured")
    if not check and changed:
        _replace_private_env(env_path, original, updated)
    return {
        "status": "verified",
        "changed": changed,
        "wheelSha256": WHEEL_SHA256,
        "sdistSha256": SDIST_SHA256,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=Path, required=True)
    parser.add_argument("--artifact-directory", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        report = configure(args.env, args.artifact_directory, check=args.check)
    except (ArtifactConfigurationError, OSError, ValueError):
        print('{"status":"error","reasonCode":"THINGS_CORE_ARTIFACT_CONFIGURATION_INVALID"}')
        return 1
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
