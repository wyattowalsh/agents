"""Exact-byte artifact and installed-distribution verification."""

from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import os
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .security import SecurityViolation


@dataclass(frozen=True, slots=True)
class ArtifactVerification:
    path_name: str
    sha256: str
    size: int


@dataclass(frozen=True, slots=True)
class RecordVerification:
    record_sha256: str
    entries_verified: int
    entries_total: int


def _safe_read_artifact(path: Path, *, max_bytes: int | None = None) -> tuple[bytes, os.stat_result]:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise SecurityViolation(f"Artifact could not be opened safely: {path.name}") from exc
    try:
        before = path.lstat()
        opened = os.fstat(fd)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(opened.st_mode):
            raise SecurityViolation(f"Artifact is not a regular non-symlink file: {path.name}")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, 65_536)
            if not chunk:
                break
            total += len(chunk)
            if max_bytes is not None and total > max_bytes:
                raise SecurityViolation(f"Artifact exceeds its maximum allowed size: {path.name}")
            chunks.append(chunk)
        after = path.lstat()
        if stat.S_ISLNK(after.st_mode):
            raise SecurityViolation(f"Artifact changed to a symlink while being verified: {path.name}")
        inode = (opened.st_dev, opened.st_ino)
        if inode != (before.st_dev, before.st_ino) or inode != (after.st_dev, after.st_ino):
            raise SecurityViolation(f"Artifact changed while it was being verified: {path.name}")
        return b"".join(chunks), opened
    finally:
        os.close(fd)


def verify_artifact(path: Path, expected_sha256: str, *, max_bytes: int | None = None) -> ArtifactVerification:
    """Verify an exact regular, non-symlink artifact immediately before use."""
    path = Path(path)
    data, opened = _safe_read_artifact(path, max_bytes=max_bytes)
    actual = hashlib.sha256(data).hexdigest()
    if not hmac.compare_digest(actual, expected_sha256.casefold()):
        raise SecurityViolation(f"Artifact digest mismatch: {path.name}")
    return ArtifactVerification(path_name=path.name, sha256=actual, size=opened.st_size)


def _record_digest(encoded: str) -> bytes:
    algorithm, separator, value = encoded.partition("=")
    if separator != "=" or algorithm != "sha256" or not value:
        raise SecurityViolation("Installed RECORD contains an unsupported digest.")
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(value + padding)
    except ValueError as exc:
        raise SecurityViolation("Installed RECORD contains a malformed digest.") from exc


def verify_record_tree(
    distribution_root: Path,
    record_relative_path: str,
    expected_record_sha256: str,
    *,
    expected_entries: int,
) -> RecordVerification:
    """Verify every hashed file in an installed wheel RECORD without following symlinks."""
    root = Path(distribution_root).resolve(strict=True)
    record_parts = PurePosixPath(record_relative_path)
    if record_parts.is_absolute() or ".." in record_parts.parts:
        raise SecurityViolation("Installed RECORD path escapes the distribution root.")
    record_path = root.joinpath(*record_parts.parts)
    record_bytes, _ = _safe_read_artifact(record_path, max_bytes=2_000_000)
    actual_record = hashlib.sha256(record_bytes).hexdigest()
    if not hmac.compare_digest(actual_record, expected_record_sha256.casefold()):
        raise SecurityViolation("Installed RECORD digest mismatch.")

    verified = 0
    total = 0
    rows = csv.reader(record_bytes.decode("utf-8").splitlines())
    for row in rows:
        if len(row) != 3:
            raise SecurityViolation("Installed RECORD contains a malformed row.")
        relative, encoded_digest, encoded_size = row
        parts = PurePosixPath(relative)
        if parts.is_absolute() or ".." in parts.parts:
            raise SecurityViolation("Installed RECORD entry escapes the distribution root.")
        total += 1
        if not encoded_digest:
            if relative != record_relative_path or encoded_size:
                raise SecurityViolation("Only RECORD itself may omit a digest and size.")
            continue
        payload, opened = _safe_read_artifact(root.joinpath(*parts.parts))
        if opened.st_size != int(encoded_size):
            raise SecurityViolation(f"Installed RECORD size mismatch: {parts.name}")
        expected = _record_digest(encoded_digest)
        if not hmac.compare_digest(hashlib.sha256(payload).digest(), expected):
            raise SecurityViolation(f"Installed RECORD digest mismatch: {parts.name}")
        verified += 1
    if verified != expected_entries:
        raise SecurityViolation("Installed RECORD verified-entry count mismatch.")
    if total != expected_entries + 1:
        raise SecurityViolation("Installed RECORD total-entry count mismatch.")
    return RecordVerification(actual_record, verified, total)
