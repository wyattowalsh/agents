"""Filesystem and path-safety primitives for Nerdbot workflows."""

from __future__ import annotations

import os
import stat
import tempfile
from collections.abc import Iterable
from contextlib import suppress
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import TextIO

WINDOWS_REPARSE_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)


def normalize_vault_relative_path(path: str, *, allowed_roots: Iterable[str] | None = None) -> str:
    """Return a normalized POSIX vault-relative path or raise ``ValueError``.

    Obsidian vault paths are stored as POSIX-style relative paths even on Windows.
    This rejects absolute paths, drive-qualified paths, UNC paths, traversal, and
    NUL bytes before any caller can use the value for reads, writes, or indexes.
    """
    if "\0" in path:
        raise ValueError("Vault path contains a NUL byte")
    normalized = path.replace("\\", "/").strip()
    if not normalized:
        raise ValueError("Vault path is empty")
    if normalized.startswith("//"):
        raise ValueError(f"Vault path must be relative, got UNC-like path: {path}")
    windows_path = PureWindowsPath(path)
    if windows_path.drive or windows_path.is_absolute():
        raise ValueError(f"Vault path must be relative, got Windows path: {path}")
    posix_path = PurePosixPath(normalized)
    if posix_path.is_absolute():
        raise ValueError(f"Vault path must be relative, got absolute path: {path}")
    parts = posix_path.parts
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"Vault path must not contain traversal segments: {path}")
    roots = tuple(allowed_roots or ())
    if roots and (not parts or parts[0] not in roots):
        allowed = ", ".join(sorted(roots))
        raise ValueError(f"Vault path must start with one of: {allowed}; got {path}")
    return posix_path.as_posix()


def is_windows_reparse_point(path: Path) -> bool:
    """Return whether an existing path is a Windows junction/reparse point."""
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & WINDOWS_REPARSE_ATTRIBUTE)


def normalize_requested_root(root_arg: str) -> Path:
    """Resolve a requested root while rejecting symlink roots or ancestors."""
    supplied = Path(root_arg).expanduser()
    candidate = supplied if supplied.is_absolute() else Path.cwd() / supplied
    reject_indirect_path_component(candidate)
    return candidate.resolve()


def ensure_descendant(root: Path, target: Path) -> Path:
    """Return target relative path or reject a root escape."""
    try:
        return target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Target escapes requested root: {target}") from exc


def ensure_safe_target(root: Path, target: Path) -> None:
    """Reject target paths that escape root or traverse indirect path components."""
    relative = ensure_descendant(root, target)
    current = root
    for part in relative.parts:
        current = current / part
        if os.path.lexists(current) and (current.is_symlink() or is_windows_reparse_point(current)):
            raise RuntimeError(f"Refusing to follow symlinked path component or reparse-point: {current}")


def reject_indirect_path_component(path: Path) -> None:
    """Reject symlink or reparse-point components in an existing path chain."""
    candidate = path if path.is_absolute() else Path.cwd() / path
    for ancestor in (candidate, *candidate.parents):
        if os.path.lexists(ancestor) and (ancestor.is_symlink() or is_windows_reparse_point(ancestor)):
            raise RuntimeError(f"Refusing to use symlinked path component or reparse-point: {ancestor}")


def reject_hardlinked_file(path: Path) -> None:
    """Reject mutating a regular file with multiple hardlinks."""
    if not path.exists() or path.is_symlink() or not path.is_file():
        return
    try:
        link_count = path.stat().st_nlink
    except OSError:
        return
    if link_count > 1:
        raise RuntimeError(f"Refusing to mutate hardlinked file with {link_count} links: {path}")


def reject_hardlinked_overwrite(path: Path) -> None:
    """Compatibility alias for legacy script callers."""
    reject_hardlinked_file(path)


def fsync_parent_directory(path: Path) -> None:
    """Best-effort fsync of a parent directory after file create/replace."""
    try:
        directory_fd = os.open(path.parent, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    except OSError:
        pass
    finally:
        os.close(directory_fd)


def open_text_no_follow(path: Path, *, overwrite: bool) -> TextIO:
    """Open a file for text writing without following the final path component."""
    reject_indirect_path_component(path.parent)
    if overwrite:
        reject_hardlinked_file(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    flags |= os.O_TRUNC if overwrite else os.O_EXCL
    fd = os.open(path, flags, 0o644)
    return os.fdopen(fd, "w", encoding="utf-8")


def read_text_no_follow(path: Path) -> str:
    """Read text without following indirect path components or final symlinks."""
    reject_indirect_path_component(path.parent)
    if path.is_symlink() or is_windows_reparse_point(path):
        raise RuntimeError(f"Refusing to read through symlinked path component or reparse-point: {path}")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags)
    with os.fdopen(fd, "r", encoding="utf-8") as handle:
        return handle.read()


def write_bytes_atomic_no_follow(path: Path, content: bytes, *, overwrite: bool = True) -> None:
    """Atomically replace bytes without following symlink targets."""
    reject_indirect_path_component(path.parent)
    reject_hardlinked_file(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if path.is_symlink() or is_windows_reparse_point(path):
            raise RuntimeError(f"Refusing to write through indirect file: {path}")
        os.replace(temp_path, path)
        fsync_parent_directory(path)
    except Exception:
        with suppress(FileNotFoundError):
            temp_path.unlink()
        raise


def append_text_no_follow(path: Path, text: str) -> None:
    """Append text to a log file without following final symlinks."""
    reject_indirect_path_component(path.parent)
    reject_hardlinked_file(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o644)
    try:
        with os.fdopen(fd, "a", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        fsync_parent_directory(path)


def write_text_atomic_no_follow(path: Path, text: str, *, overwrite: bool = False) -> None:
    """Write text atomically without following indirect path components."""
    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    write_bytes_atomic_no_follow(path, text.encode("utf-8"), overwrite=True)
