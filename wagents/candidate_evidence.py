"""Deterministic filesystem and receipt evidence for candidate activation."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable

FILESYSTEM_DIGEST_ALGORITHM = "lstat-tree-v1"
RUNTIME_PREDICATE_VERSION = "candidate-runtime-v2"
RUNTIME_DIGEST_IGNORED_DIRS = frozenset({".cache", ".git", ".pytest_cache", "__pycache__"})


def _digest_field(digest: Any, label: str, value: str | bytes) -> None:
    digest.update(label.encode("utf-8"))
    digest.update(b"\0")
    digest.update(value if isinstance(value, bytes) else value.encode("utf-8"))
    digest.update(b"\0")


def _entry_digest(digest: Any, path: Path, relative: str, ignored_dirs: frozenset[str]) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        _digest_field(digest, "missing", relative)
        return

    mode = metadata.st_mode
    _digest_field(digest, "entry", relative)
    _digest_field(digest, "mode", format(stat.S_IMODE(mode), "04o"))
    if stat.S_ISLNK(mode):
        _digest_field(digest, "type", "symlink")
        _digest_field(digest, "target", os.readlink(path))
        return
    if stat.S_ISREG(mode):
        _digest_field(digest, "type", "file")
        _digest_field(digest, "content", path.read_bytes())
        return
    if stat.S_ISDIR(mode):
        _digest_field(digest, "type", "directory")
        for child in sorted(path.iterdir(), key=lambda item: item.name):
            if child.name in ignored_dirs:
                try:
                    child_mode = child.lstat().st_mode
                except FileNotFoundError:
                    child_mode = 0
                if stat.S_ISDIR(child_mode):
                    continue
            child_relative = child.name if relative == "." else f"{relative}/{child.name}"
            _entry_digest(digest, child, child_relative, ignored_dirs)
        return
    _digest_field(digest, "type", f"special:{stat.S_IFMT(mode):o}")


def filesystem_digest(paths: Iterable[str | Path], *, ignored_dirs: Iterable[str] = ()) -> str:
    """Hash live filesystem state without following symlinks."""

    digest = hashlib.sha256()
    ignored = frozenset(str(value) for value in ignored_dirs)
    normalized = sorted({Path(value).expanduser().absolute() for value in paths}, key=str)
    for root in normalized:
        _digest_field(digest, "root", str(root))
        _entry_digest(digest, root, ".", ignored)
    return digest.hexdigest()


def receipt_input_digest(
    *,
    artifact_id: str,
    phase: str,
    source_commit_sha: str,
    package_id: str,
    resolved_version: str,
    installed_digest: str,
) -> str:
    payload = {
        "artifact_id": artifact_id,
        "installed_digest": installed_digest,
        "package_id": package_id,
        "phase": phase,
        "resolved_version": resolved_version,
        "source_commit_sha": source_commit_sha,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def receipt_metadata(
    *,
    artifact_id: str,
    phase: str,
    source_commit_sha: str,
    package_id: str,
    resolved_version: str,
    installed_digest: str,
    recorded_at: str | None = None,
) -> dict[str, str]:
    return {
        "source_commit_sha": source_commit_sha,
        "input_digest": receipt_input_digest(
            artifact_id=artifact_id,
            phase=phase,
            source_commit_sha=source_commit_sha,
            package_id=package_id,
            resolved_version=resolved_version,
            installed_digest=installed_digest,
        ),
        "predicate_version": RUNTIME_PREDICATE_VERSION,
        "recorded_at": recorded_at or datetime.now(UTC).isoformat(),
    }
