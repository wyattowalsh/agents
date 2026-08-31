"""Owner-checked, non-symlink runtime files and cross-process locking."""

from __future__ import annotations

import errno
import fcntl
import os
import stat
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


class SecurityViolation(RuntimeError):
    """A filesystem object violates the Things++ runtime trust boundary."""


class LockTimeoutError(TimeoutError):
    """The shared mutation lock could not be acquired before its deadline."""


class LockCancelledError(RuntimeError):
    """Lock acquisition was cancelled by the caller."""


def _open_flags(*, directory: bool = False) -> int:
    flags = os.O_RDONLY if directory else os.O_RDWR
    for name in ("O_CLOEXEC", "O_NOFOLLOW"):
        flags |= getattr(os, name, 0)
    if directory:
        flags |= getattr(os, "O_DIRECTORY", 0)
    return flags


def _assert_fd_matches_path(path: Path, fd: int, *, mode: int, directory: bool) -> os.stat_result:
    before = path.lstat()
    current = os.fstat(fd)
    after = path.lstat()
    if stat.S_ISLNK(before.st_mode) or stat.S_ISLNK(after.st_mode):
        raise SecurityViolation("Symlinks are forbidden for Things++ runtime state.")
    expected_kind = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected_kind(current.st_mode):
        raise SecurityViolation("Things++ runtime state has the wrong file type.")
    if current.st_uid != os.getuid():
        raise SecurityViolation("Things++ runtime state is not owned by the current user.")
    if stat.S_IMODE(current.st_mode) != mode:
        raise SecurityViolation(f"Things++ runtime state must have mode {mode:04o}.")
    inode = (current.st_dev, current.st_ino)
    if inode != (before.st_dev, before.st_ino) or inode != (after.st_dev, after.st_ino):
        raise SecurityViolation("Things++ runtime state changed during verification.")
    return current


def ensure_secure_runtime_root(path: Path) -> Path:
    """Create or validate one exact owner-only runtime directory."""
    path = Path(path)
    try:
        path.mkdir(mode=0o700, parents=False, exist_ok=False)
    except FileExistsError:
        pass
    except FileNotFoundError as exc:
        raise SecurityViolation("The runtime-root parent does not exist.") from exc
    fd = os.open(path, _open_flags(directory=True))
    try:
        _assert_fd_matches_path(path, fd, mode=0o700, directory=True)
    finally:
        os.close(fd)
    return path


@dataclass(frozen=True, slots=True)
class SecureRuntimePaths:
    """Canonical shared paths used by every Things++ backend."""

    root: Path
    lock_file: Path
    receipts_db: Path
    receipt_key: Path

    @classmethod
    def create(cls, root: Path | None = None) -> SecureRuntimePaths:
        if root is None:
            root = Path(tempfile.gettempdir()) / f"things-plus-plus-{os.getuid()}"
        secure_root = ensure_secure_runtime_root(Path(root))
        return cls(
            root=secure_root,
            lock_file=secure_root / "mutation.lock",
            receipts_db=secure_root / "receipts.sqlite3",
            receipt_key=secure_root / "receipt.key",
        )


def _translate_open_error(exc: OSError) -> None:
    if exc.errno == errno.ELOOP:
        raise SecurityViolation("Symlinks are forbidden for Things++ runtime files.") from exc
    raise exc


def _open_secure_file(path: Path, *, create: bool) -> int:
    flags = _open_flags()
    created = False
    try:
        if create:
            try:
                fd = os.open(path, flags | os.O_CREAT | os.O_EXCL, 0o600)
                created = True
            except FileExistsError:
                fd = os.open(path, flags)
        else:
            fd = os.open(path, flags)
    except OSError as exc:
        _translate_open_error(exc)
    try:
        if created:
            os.fchmod(fd, 0o600)
        _assert_fd_matches_path(path, fd, mode=0o600, directory=False)
    except BaseException:
        os.close(fd)
        raise
    return fd


def secure_read_bytes(path: Path, *, max_bytes: int = 1_048_576) -> bytes:
    """Read a small owner-only regular file without following symlinks."""
    fd = _open_secure_file(Path(path), create=False)
    try:
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, min(65_536, max_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise SecurityViolation("Secure file exceeds its maximum allowed size.")
        _assert_fd_matches_path(Path(path), fd, mode=0o600, directory=False)
        return b"".join(chunks)
    finally:
        os.close(fd)


def secure_write_bytes(path: Path, data: bytes, *, exclusive: bool = False) -> None:
    """Write an owner-only state file through an O_NOFOLLOW descriptor."""
    path = Path(path)
    try:
        if exclusive:
            fd = os.open(path, _open_flags() | os.O_CREAT | os.O_EXCL, 0o600)
            created = True
        else:
            try:
                fd = os.open(path, _open_flags() | os.O_CREAT | os.O_EXCL, 0o600)
                created = True
            except FileExistsError:
                fd = os.open(path, _open_flags())
                created = False
    except OSError as exc:
        _translate_open_error(exc)
    try:
        if created:
            os.fchmod(fd, 0o600)
        _assert_fd_matches_path(path, fd, mode=0o600, directory=False)
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
        _assert_fd_matches_path(path, fd, mode=0o600, directory=False)
    finally:
        os.close(fd)


def secure_read_from_descriptor(path: Path, fd: int, *, max_bytes: int = 1_048_576) -> bytes:
    """Read through an already verified descriptor and retain pathname identity."""
    path = Path(path)
    _assert_fd_matches_path(path, fd, mode=0o600, directory=False)
    os.lseek(fd, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = os.read(fd, min(65_536, max_bytes + 1 - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > max_bytes:
            raise SecurityViolation("Secure file exceeds its maximum allowed size.")
    _assert_fd_matches_path(path, fd, mode=0o600, directory=False)
    return b"".join(chunks)


def secure_write_to_descriptor(path: Path, fd: int, data: bytes) -> None:
    """Write through an already verified descriptor without reopening its path."""
    path = Path(path)
    _assert_fd_matches_path(path, fd, mode=0o600, directory=False)
    os.ftruncate(fd, 0)
    os.lseek(fd, 0, os.SEEK_SET)
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        view = view[written:]
    os.fsync(fd)
    _assert_fd_matches_path(path, fd, mode=0o600, directory=False)


@dataclass(slots=True)
class AdvisoryMutationLock:
    """One owner-checked flock shared by all Things++ mutation backends."""

    path: Path
    timeout_seconds: float = 5.0
    poll_seconds: float = 0.025
    cancelled: Callable[[], bool] | None = None
    _fd: int | None = None

    def acquire(self) -> AdvisoryMutationLock:
        if self._fd is not None:
            raise RuntimeError("Mutation lock is already held by this instance.")
        fd = _open_secure_file(Path(self.path), create=True)
        deadline = time.monotonic() + self.timeout_seconds
        try:
            while True:
                if self.cancelled is not None and self.cancelled():
                    raise LockCancelledError("Mutation lock acquisition was cancelled.")
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise LockTimeoutError("Timed out acquiring the shared Things++ mutation lock.") from None
                    time.sleep(self.poll_seconds)
            _assert_fd_matches_path(Path(self.path), fd, mode=0o600, directory=False)
            self._fd = fd
            return self
        except BaseException:
            os.close(fd)
            raise

    def release(self) -> None:
        fd, self._fd = self._fd, None
        if fd is None:
            return
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    def __enter__(self) -> AdvisoryMutationLock:
        return self.acquire()

    def __exit__(self, *_exc: object) -> None:
        self.release()


@contextmanager
def secure_file_descriptor(path: Path) -> Iterator[int]:
    """Yield a verified read descriptor and recheck its inode on exit."""
    fd = _open_secure_file(Path(path), create=False)
    try:
        yield fd
        _assert_fd_matches_path(Path(path), fd, mode=0o600, directory=False)
    finally:
        os.close(fd)
