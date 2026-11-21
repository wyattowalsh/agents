"""Exact-map local execution and recovery for Files Buddy.

The caller owns consent. A plan digest binds that consent to bytes; it is not an
identity or permission mechanism. One state document is the execution authority.
Filesystem changes and that document are deliberately not described as atomic.
"""

from __future__ import annotations

import contextlib
import ctypes
import errno
import fcntl
import hashlib
import json
import os
import platform
import re
import stat
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

VERSION = "2.0"
POLICY = "local-regular-v1"
MAX_OPERATIONS = 1000
MAX_STATE_BYTES = 16 * 1024 * 1024
OPERATIONS = frozenset({"copy", "move", "rename"})
STATES = frozenset({"planned", "prepared", "applied", "verified", "failed", "uncertain", "conflict"})
RUN_STATES = frozenset({"planned", "running", "completed", "partial", "failed", "undone"})
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
BLOCKED = (
    "/System",
    "/Library",
    "/usr",
    "/bin",
    "/sbin",
    "/var",
    "/etc",
    "/private",
    "/Applications",
    "/dev",
    "/proc",
    "/sys",
    "/run",
    "/boot",
)
SENSITIVE = frozenset({".git", ".ssh", ".gnupg", ".aws", ".kube", ".config", "keyrings"})
MANAGED_STORES = frozenset(
    {
        "library",
        ".cache",
        ".ollama",
        ".lmstudio",
        ".huggingface",
        ".docker",
        ".npm",
        ".pnpm-store",
        ".cargo",
        ".rustup",
        ".gradle",
        ".m2",
        ".yarn",
        ".conda",
        ".virtualenvs",
        "backups.backupdb",
    }
)
BUNDLES = (
    ".app",
    ".photoslibrary",
    ".musiclibrary",
    ".library",
    ".logicx",
    ".band",
    ".vmwarevm",
    ".pvm",
    ".sparsebundle",
)
PROJECT_MARKERS = (".git", "pyproject.toml", "package.json", "Cargo.toml", "go.mod", ".env")
ROOT_FIELDS = {"path", "device", "inode", "provider"}
PARENT_FIELDS = {"device", "inode"}
SNAPSHOT_FIELDS = {
    "kind",
    "device",
    "inode",
    "size_bytes",
    "mode",
    "uid",
    "gid",
    "nlink",
    "mtime_ns",
    "ctime_ns",
    "sha256",
}
OP_FIELDS = {
    "operation_id",
    "type",
    "source",
    "destination",
    "before",
    "source_parent",
    "destination_parent",
    "recovery",
}
PLAN_FIELDS = {
    "schema_version",
    "policy_version",
    "plan_id",
    "created_at",
    "intent",
    "source_roots",
    "destination_roots",
    "local_only_attested",
    "hash_algorithm",
    "failure_policy",
    "operations",
}
RECORD_FIELDS = {"operation_id", "status", "updated_at", "after", "error"}
STATE_FIELDS = {
    "schema_version",
    "run_id",
    "created_at",
    "updated_at",
    "status",
    "plan",
    "plan_digest",
    "approval",
    "operations",
    "undo",
}


class ContractError(ValueError):
    """Reject malformed, stale, unsupported, or unsafe input."""


def now() -> str:
    return datetime.now(UTC).isoformat()


def canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    ).hexdigest()


def load_json(text: str) -> Any:
    """Reject duplicate keys and non-JSON numeric constants before validation."""

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ContractError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def constant(value: str) -> None:
        raise ContractError(f"Invalid JSON constant: {value}")

    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, RecursionError) as exc:
        raise ContractError(f"Invalid JSON: {exc}") from exc


def _object(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ContractError(f"{label} must contain exactly: {', '.join(sorted(fields))}")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\0" in value:
        raise ContractError(f"{label} must be a nonempty string without NUL")
    return value


def _integer(value: Any, label: str, *, nonnegative: bool = True) -> int:
    if type(value) is not int or (nonnegative and value < 0):
        raise ContractError(f"{label} must be {'a nonnegative' if nonnegative else 'an'} integer")
    return value


def _timestamp(value: Any, label: str) -> None:
    try:
        parsed = datetime.fromisoformat(_text(value, label))
    except ValueError as exc:
        raise ContractError(f"{label} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ContractError(f"{label} must include a timezone")


def _identifier(value: Any, label: str) -> str:
    if not ID.fullmatch(_text(value, label)):
        raise ContractError(f"Invalid {label}")
    return value


def _path(value: Any, label: str) -> Path:
    raw = _text(value, label)
    path = Path(raw)
    if not path.is_absolute() or str(path) != raw or ".." in path.parts:
        raise ContractError(f"{label} must be a normalized absolute path")
    return path


def _within(path: Path, root: Path) -> bool:
    return path != root and path.is_relative_to(root)


def _policy_path(path: Path) -> None:
    # Apply conservative policy comparisons independently of the volume's case
    # sensitivity. Keep the original spelling for all filesystem operations.
    policy_path = Path(str(path).casefold())
    if policy_path == Path("/") or any(policy_path.is_relative_to(p.casefold()) for p in BLOCKED):
        raise ContractError(f"Protected path: {path}")
    if any(part.casefold() in SENSITIVE or part.casefold().endswith(BUNDLES) for part in path.parts):
        raise ContractError(f"Sensitive or app-managed path: {path}")
    if any(
        part.casefold() in {"cloudstorage", "mobile documents", "google drive", "dropbox"}
        or part.casefold().startswith(("onedrive", "googledrive"))
        for part in path.parts
    ):
        raise ContractError(f"Cloud-managed path: {path}")
    if any(part.casefold() in MANAGED_STORES for part in path.parts) or path.suffix.casefold() in {
        ".qcow",
        ".qcow2",
        ".vmdk",
        ".vdi",
        ".vhdx",
    }:
        raise ContractError(f"Owner-managed stores and VM disks require native review: {path}")
    if path.name.casefold() in {".gitignore", ".gitmodules", ".env"} or path.name.casefold().startswith(".env."):
        raise ContractError(f"Project or secret metadata: {path}")


@contextlib.contextmanager
def open_directory(path: Path) -> Iterator[int]:
    """Anchor every directory component and refuse symlink traversal."""
    _path(str(path), "directory")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open("/", flags)
    try:
        for component in path.parts[1:]:
            next_descriptor = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        yield descriptor
    finally:
        os.close(descriptor)


def _owned_directory(descriptor: int) -> os.stat_result:
    info = os.fstat(descriptor)
    if info.st_uid != os.getuid() or info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise ContractError(
            "Execution roots and parents must be owned by the current user and not group/world writable"
        )
    if platform.system() == "Darwin" and not _mac_acl_absent(descriptor):
        raise ContractError("Directory ACL permissions require native review; mode bits alone do not prove privacy")
    return info


def _identity(info: os.stat_result) -> dict[str, int]:
    return {"device": info.st_dev, "inode": info.st_ino}


def _root(path: Path) -> dict[str, Any]:
    _policy_path(path)
    with open_directory(path) as descriptor:
        info = _owned_directory(descriptor)
    return {"path": str(path), **_identity(info), "provider": "local-declared"}


def _project_check(path: Path) -> None:
    for parent in (path.parent, *path.parent.parents):
        if parent == Path("/"):
            break
        if any(os.path.lexists(parent / marker) for marker in PROJECT_MARKERS):
            raise ContractError(f"Project/app/secret dependency requires manual review: {parent}")


def _mac_acl_absent(descriptor: int) -> bool:
    """Inspect extended ACLs on Darwin; unknown native responses are unsupported.

    API: Apple's acl_get(3), acl_get_entry(3), and Libc sys/acl.h. Libc source
    71bbe350ab79eef58113991d817ccc6165061a64, posix1e/acl_file.c,
    posix1e/acl_entry.c and gen/filesec.c establish NULL/ENOENT for absent ACL
    and -1/EINVAL for first entry of a valid zero-entry ACL.
    """
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        get_acl = libc.acl_get_fd_np
        entry = libc.acl_get_entry
        free = libc.acl_free
    except AttributeError as exc:
        raise ContractError("Native ACL inspection is unavailable") from exc
    get_acl.argtypes, get_acl.restype = [ctypes.c_int, ctypes.c_int], ctypes.c_void_p
    entry.argtypes, entry.restype = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)], ctypes.c_int
    free.argtypes, free.restype = [ctypes.c_void_p], ctypes.c_int
    ctypes.set_errno(0)
    acl = get_acl(descriptor, 0x100)  # ACL_TYPE_EXTENDED
    if not acl:
        if ctypes.get_errno() == errno.ENOENT:
            return True
        raise ContractError("Unable to establish absence of a native extended ACL")
    try:
        pointer = ctypes.c_void_p()
        ctypes.set_errno(0)
        result = entry(acl, 0, ctypes.byref(pointer))  # ACL_FIRST_ENTRY
        if result == 0:
            return False
        if ctypes.get_errno() == errno.EINVAL:
            return True
        raise ContractError("Unable to inspect native ACL entries")
    finally:
        free(acl)


def _plain_file(descriptor: int, info: os.stat_result) -> None:
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
        raise ContractError("Only owned, singly-linked regular files are supported")
    if info.st_mode & (stat.S_ISUID | stat.S_ISGID | stat.S_ISVTX) or getattr(info, "st_flags", 0):
        raise ContractError("Special permission bits or filesystem flags require native review")
    if info.st_size and info.st_blocks * 512 < info.st_size:
        raise ContractError("Sparse/compressed files require native metadata qualification")
    try:
        if os.listxattr(descriptor):
            raise ContractError("Extended attributes/resource forks/ACLs require native review")
    except OSError as exc:
        raise ContractError(f"Cannot establish extended-attribute safety: {exc}") from exc
    if platform.system() == "Darwin" and not _mac_acl_absent(descriptor):
        raise ContractError("Extended ACLs require native review")


def snapshot(descriptor: int) -> dict[str, Any]:
    before = os.fstat(descriptor)
    _plain_file(descriptor, before)
    os.lseek(descriptor, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    remaining = before.st_size
    while remaining:
        block = os.read(descriptor, min(remaining, 1024 * 1024))
        if not block:
            raise ContractError("File shrank while collecting evidence")
        digest.update(block)
        remaining -= len(block)
    if os.read(descriptor, 1):
        raise ContractError("File grew while collecting evidence")
    after = os.fstat(descriptor)
    keys = ("st_dev", "st_ino", "st_size", "st_mode", "st_uid", "st_gid", "st_nlink", "st_mtime_ns", "st_ctime_ns")
    if any(getattr(before, key) != getattr(after, key) for key in keys):
        raise ContractError("File changed while collecting evidence")
    return {
        "kind": "regular",
        "device": before.st_dev,
        "inode": before.st_ino,
        "size_bytes": before.st_size,
        "mode": before.st_mode,
        "uid": before.st_uid,
        "gid": before.st_gid,
        "nlink": before.st_nlink,
        "mtime_ns": before.st_mtime_ns,
        "ctime_ns": before.st_ctime_ns,
        "sha256": digest.hexdigest(),
    }


def _read_file(parent_fd: int, name: str) -> int:
    return os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent_fd)


def _file_snapshot(path: Path) -> dict[str, Any]:
    with open_directory(path.parent) as parent_fd:
        _owned_directory(parent_fd)
        descriptor = _read_file(parent_fd, path.name)
        try:
            return snapshot(descriptor)
        finally:
            os.close(descriptor)


def _absent(parent_fd: int, name: str) -> None:
    try:
        os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    raise ContractError(f"Destination is occupied: {name}")


def _validate_snapshot(value: Any) -> None:
    data = _object(value, SNAPSHOT_FIELDS, "file evidence")
    if data["kind"] != "regular" or data["nlink"] != 1:
        raise ContractError("Only singly-linked regular file evidence is supported")
    for key in SNAPSHOT_FIELDS - {"kind", "sha256", "mtime_ns", "ctime_ns"}:
        _integer(data[key], key)
    for key in ("mtime_ns", "ctime_ns"):
        _integer(data[key], key, nonnegative=False)
    if not stat.S_ISREG(data["mode"]) or not HEX64.fullmatch(_text(data["sha256"], "sha256")):
        raise ContractError("Invalid regular-file mode or SHA256 evidence")


def _validate_parent(value: Any) -> None:
    parent = _object(value, PARENT_FIELDS, "parent identity")
    for key in PARENT_FIELDS:
        _integer(parent[key], key)


def validate_plan(value: Any) -> dict[str, Any]:
    plan = _object(value, PLAN_FIELDS, "plan")
    if plan["schema_version"] != VERSION or plan["policy_version"] != POLICY:
        raise ContractError("Unsupported plan schema or policy version")
    _identifier(plan["plan_id"], "plan ID")
    _timestamp(plan["created_at"], "created_at")
    _text(plan["intent"], "intent")
    if (
        plan["local_only_attested"] is not True
        or plan["hash_algorithm"] != "sha256"
        or plan["failure_policy"] != "stop"
    ):
        raise ContractError("Plan must attest local-only scope, SHA256 evidence, and stop-on-error")
    roots: dict[str, list[Path]] = {}
    for field in ("source_roots", "destination_roots"):
        if not isinstance(plan[field], list) or not 1 <= len(plan[field]) <= MAX_OPERATIONS:
            raise ContractError(f"Invalid {field}")
        roots[field] = []
        for item in plan[field]:
            root = _object(item, ROOT_FIELDS, "root identity")
            path = _path(root["path"], "root")
            _policy_path(path)
            if root["provider"] != "local-declared":
                raise ContractError("Only explicitly declared local providers are supported")
            _integer(root["device"], "device")
            _integer(root["inode"], "inode")
            roots[field].append(path)
        if len(set(roots[field])) != len(roots[field]):
            raise ContractError("Duplicate scope root")
    if not isinstance(plan["operations"], list) or not 1 <= len(plan["operations"]) <= MAX_OPERATIONS:
        raise ContractError(f"Plan must contain 1..{MAX_OPERATIONS} exact operations")
    ids, sources, destinations = set(), set(), set()
    for operation in plan["operations"]:
        op = _object(operation, OP_FIELDS, "operation")
        identifier = _identifier(op["operation_id"], "operation ID")
        if identifier in ids or not isinstance(op["type"], str) or op["type"] not in OPERATIONS:
            raise ContractError("Duplicate operation ID or unsupported operation type")
        ids.add(identifier)
        source = _path(op["source"], "source")
        destination = _path(op["destination"], "destination")
        _policy_path(source)
        _policy_path(destination)
        if not any(_within(source, root) for root in roots["source_roots"]) or not any(
            _within(destination, root) for root in roots["destination_roots"]
        ):
            raise ContractError("Operation is outside approved source/destination roots")
        if source == destination or str(source).casefold() in sources or str(destination).casefold() in destinations:
            raise ContractError("Duplicate source, duplicate destination, or identical mapping")
        sources.add(str(source).casefold())
        destinations.add(str(destination).casefold())
        _validate_snapshot(op["before"])
        _validate_parent(op["source_parent"])
        _validate_parent(op["destination_parent"])
        if (
            op["before"]["device"] != op["source_parent"]["device"]
            or op["before"]["device"] != op["destination_parent"]["device"]
        ):
            raise ContractError("Cross-volume operations require native qualification")
        expected_recovery = "quarantine-copy" if op["type"] == "copy" else "reverse-move"
        if op["recovery"] != expected_recovery:
            raise ContractError("Unsupported recovery contract")
    if sources & destinations:
        raise ContractError("Dependent/cyclic name mappings require a new independent plan")
    return plan


def _records(plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"operation_id": op["operation_id"], "status": "planned", "updated_at": now(), "after": None, "error": None}
        for op in plan["operations"]
    ]


def _validate_records(records: Any, plan: dict[str, Any]) -> None:
    if not isinstance(records, list) or len(records) != len(plan["operations"]):
        raise ContractError("Execution records must match exact planned operations")
    for record, op in zip(records, plan["operations"], strict=True):
        row = _object(record, RECORD_FIELDS, "execution record")
        if (
            row["operation_id"] != op["operation_id"]
            or not isinstance(row["status"], str)
            or row["status"] not in STATES
        ):
            raise ContractError("Invalid operation record identity or status")
        _timestamp(row["updated_at"], "record timestamp")
        if row["after"] is not None:
            _validate_snapshot(row["after"])
        if row["error"] is not None:
            _text(row["error"], "error")
        if row["status"] == "verified" and row["after"] is None:
            raise ContractError("Verified operations require outcome evidence")


def _approval(value: Any, digest: str) -> None:
    if value is None:
        return
    item = _object(value, {"plan_digest", "received_at", "source"}, "approval receipt")
    if item["plan_digest"] != digest or item["source"] != "trusted-invoker-cli":
        raise ContractError("Approval receipt does not match plan")
    _timestamp(item["received_at"], "approval time")


def validate_state(value: Any) -> dict[str, Any]:
    state = _object(value, STATE_FIELDS, "state")
    if state["schema_version"] != VERSION or not isinstance(state["status"], str) or state["status"] not in RUN_STATES:
        raise ContractError("Unsupported state schema or status")
    _identifier(state["run_id"], "run ID")
    _timestamp(state["created_at"], "created_at")
    _timestamp(state["updated_at"], "updated_at")
    plan = validate_plan(state["plan"])
    if state["plan_digest"] != canonical_digest(plan) or state["run_id"] != plan["plan_id"]:
        raise ContractError("Plan digest or run identity mismatch")
    _approval(state["approval"], state["plan_digest"])
    _validate_records(state["operations"], plan)
    if state["status"] == "completed" and any(row["status"] != "verified" for row in state["operations"]):
        raise ContractError("Completed state requires verified outcomes")
    if any(row["status"] != "planned" for row in state["operations"]) and state["approval"] is None:
        raise ContractError("Execution evidence requires an approval receipt")
    if state["undo"] is not None:
        undo = _object(state["undo"], {"plan", "plan_digest", "approval", "operations"}, "undo state")
        validate_plan(undo["plan"])
        if undo["plan_digest"] != canonical_digest(undo["plan"]):
            raise ContractError("Reverse plan digest mismatch")
        _approval(undo["approval"], undo["plan_digest"])
        _validate_records(undo["operations"], undo["plan"])
        if any(row["status"] != "planned" for row in undo["operations"]) and undo["approval"] is None:
            raise ContractError("Reverse execution requires an approval receipt")
    if state["status"] == "undone" and (
        state["undo"] is None or any(row["status"] != "verified" for row in state["undo"]["operations"])
    ):
        raise ContractError("Undone state requires verified reverse outcomes")
    return state


class StateStore:
    """Private per-user state, no-follow discovery, and serialized durable writes.

    Its stable lock serializes state updates. Additional owned-directory inode
    locks coordinate overlapping filesystem scopes across state directories.
    """

    def __init__(self, root: Path):
        self.root = Path(os.path.abspath(root.expanduser()))
        self.manifests = self.root / "manifests"

    def _prepare(self) -> None:
        # Walk before creating descendants: Path.mkdir(parents=True) could write
        # through an existing symlink before a later containment check rejected it.
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        descriptor = os.open("/", flags)
        current = Path("/")
        try:
            for component in self.manifests.parts[1:]:
                try:
                    child = os.open(component, flags, dir_fd=descriptor)
                except FileNotFoundError:
                    with contextlib.suppress(FileExistsError):
                        os.mkdir(component, mode=0o700, dir_fd=descriptor)
                    child = os.open(component, flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = child
                current /= component
                if current in {self.root, self.manifests}:
                    info = _owned_directory(descriptor)
                    if stat.S_IMODE(info.st_mode) & 0o077:
                        raise ContractError(f"State directory must be private (0700): {current}")
        finally:
            os.close(descriptor)
        with open_directory(self.root) as descriptor:
            info = _owned_directory(descriptor)
            if stat.S_IMODE(info.st_mode) & 0o077:
                raise ContractError(f"State directory must be private (0700): {self.root}")

    @contextlib.contextmanager
    def lock(self) -> Iterator[None]:
        self._prepare()
        with open_directory(self.root) as directory:
            descriptor = os.open("execution.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            try:
                info = os.fstat(descriptor)
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_uid != os.getuid()
                    or info.st_nlink != 1
                    or stat.S_IMODE(info.st_mode) & 0o077
                ):
                    raise ContractError("Unsafe execution lock")
                _acquire_lock(descriptor)
                yield
            finally:
                os.close(descriptor)

    def resolve(self, reference: str) -> Path:
        if not self.manifests.exists():
            raise ContractError("No manifests exist")
        # No glob interpolation: literal basename or run ID only.
        supplied = Path(reference)
        candidate = supplied if supplied.is_absolute() else self.manifests / reference
        if candidate.parent != self.manifests or candidate.name in {".", ".."}:
            raise ContractError("Manifest must be an immediate child of the configured state directory")
        if candidate.suffix != ".json":
            candidate = candidate.with_name(candidate.name + ".json")
        with open_directory(self.manifests) as directory:
            descriptor = os.open(candidate.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            try:
                self._file_check(descriptor)
            finally:
                os.close(descriptor)
        return candidate

    @staticmethod
    def _file_check(descriptor: int) -> None:
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_nlink != 1
            or info.st_size > MAX_STATE_BYTES
        ):
            raise ContractError("Manifest must be an owned, singly-linked bounded regular file")
        if stat.S_IMODE(info.st_mode) & 0o022:
            raise ContractError("Manifest cannot be writable by another user/group")

    def read(self, path: Path) -> dict[str, Any]:
        path = self.resolve(str(path))
        with open_directory(self.manifests) as directory:
            descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            try:
                self._file_check(descriptor)
                with os.fdopen(descriptor, "r", encoding="utf-8", closefd=False) as stream:
                    value = load_json(stream.read(MAX_STATE_BYTES + 1))
            finally:
                os.close(descriptor)
        if not isinstance(value, dict):
            raise ContractError("Manifest must be a JSON object")
        if value.get("schema_version") == VERSION and value.get("run_id") != path.stem:
            raise ContractError("State filename does not match its run identity")
        return value

    def write(self, state: dict[str, Any]) -> Path:
        validate_state(state)
        path = self.manifests / f"{state['run_id']}.json"
        encoded = (json.dumps(state, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode()
        if len(encoded) > MAX_STATE_BYTES:
            raise ContractError("State size limit exceeded")
        # Caller holds lock. Unique O_EXCL temporary names prevent writer races.
        with open_directory(self.manifests) as directory:
            temporary = f".{uuid.uuid4().hex}.tmp"
            descriptor = os.open(
                temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory
            )
            try:
                with os.fdopen(descriptor, "wb", closefd=False) as stream:
                    stream.write(encoded)
                    stream.flush()
                    os.fsync(descriptor)
                os.replace(temporary, path.name, src_dir_fd=directory, dst_dir_fd=directory)
                os.fsync(directory)
            finally:
                os.close(descriptor)
                with contextlib.suppress(FileNotFoundError):
                    os.unlink(temporary, dir_fd=directory)  # Only our O_EXCL temporary state file.
        return path

    def discover(self) -> tuple[list[Path], list[dict[str, str]]]:
        """Return contained regular candidates and explicit per-file errors.

        Symlinks and non-regular entries are excluded without opening their
        contents. A rejected or unreadable regular state is never empty success.
        """
        if not self.manifests.exists():
            return [], []
        result: list[Path] = []
        errors: list[dict[str, str]] = []
        with open_directory(self.manifests) as directory, os.scandir(directory) as entries:
            for entry in sorted(entries, key=lambda item: item.name):
                candidate = self.manifests / entry.name
                if candidate.suffix == ".json":
                    try:
                        if not entry.is_file(follow_symlinks=False):
                            continue
                        result.append(self.resolve(str(candidate)))
                    except (OSError, ContractError) as exc:
                        errors.append({"manifest": str(candidate), "error": str(exc)})
        return result, errors


def make_plan(
    mapping: Any, source_roots: list[Path], destination_roots: list[Path], intent: str, *, local_only: bool
) -> dict[str, Any]:
    if local_only is not True:
        raise ContractError("Trusted caller must attest --local-only after checking provider ownership")
    if not isinstance(mapping, list) or not 1 <= len(mapping) <= MAX_OPERATIONS:
        raise ContractError(f"Mapping must be an array of 1..{MAX_OPERATIONS} exact operations")
    plan: dict[str, Any] = {
        "schema_version": VERSION,
        "policy_version": POLICY,
        "plan_id": uuid.uuid4().hex,
        "created_at": now(),
        "intent": _text(intent, "intent"),
        "source_roots": [_root(_path(str(path), "source root")) for path in source_roots],
        "destination_roots": [_root(_path(str(path), "destination root")) for path in destination_roots],
        "local_only_attested": True,
        "hash_algorithm": "sha256",
        "failure_policy": "stop",
        "operations": [],
    }
    for index, value in enumerate(mapping):
        item = _object(value, {"type", "source", "destination"}, "mapping item")
        if not isinstance(item["type"], str) or item["type"] not in OPERATIONS:
            raise ContractError("Only copy, move, and rename mappings are supported")
        source = _path(item["source"], "source")
        destination = _path(item["destination"], "destination")
        _policy_path(source)
        _policy_path(destination)
        _project_check(source)
        _project_check(destination)
        if not any(_within(source, Path(root["path"])) for root in plan["source_roots"]) or not any(
            _within(destination, Path(root["path"])) for root in plan["destination_roots"]
        ):
            raise ContractError("Mapping is outside declared roots")
        with open_directory(source.parent) as source_fd, open_directory(destination.parent) as destination_fd:
            source_info = _owned_directory(source_fd)
            destination_info = _owned_directory(destination_fd)
            _absent(destination_fd, destination.name)
            descriptor = _read_file(source_fd, source.name)
            try:
                before = snapshot(descriptor)
            finally:
                os.close(descriptor)
            if item["type"] == "copy" and (before["gid"] != os.getegid() or before["gid"] != destination_info.st_gid):
                raise ContractError("Copy would require unqualified ownership changes")
            plan["operations"].append(
                {
                    "operation_id": f"op-{index + 1:04d}",
                    "type": item["type"],
                    "source": str(source),
                    "destination": str(destination),
                    "before": before,
                    "source_parent": _identity(source_info),
                    "destination_parent": _identity(destination_info),
                    "recovery": "quarantine-copy" if item["type"] == "copy" else "reverse-move",
                }
            )
    return validate_plan(plan)


def create_state(store: StateStore, plan: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    validate_plan(plan)
    state = {
        "schema_version": VERSION,
        "run_id": plan["plan_id"],
        "created_at": now(),
        "updated_at": now(),
        "status": "planned",
        "plan": plan,
        "plan_digest": canonical_digest(plan),
        "approval": None,
        "operations": _records(plan),
        "undo": None,
    }
    with store.lock():
        for op in plan["operations"]:
            for field in ("source", "destination"):
                target = Path(op[field])
                if target == store.root or target.is_relative_to(store.root):
                    raise ContractError("Execution cannot target its state directory")
        candidate = store.manifests / f"{state['run_id']}.json"
        if os.path.lexists(candidate):
            raise ContractError("Run identity already exists")
        return store.write(state), state


def _roots_current(plan: dict[str, Any]) -> None:
    for root in plan["source_roots"] + plan["destination_roots"]:
        current = _root(Path(root["path"]))
        if current != root:
            raise ContractError("Scope root identity changed after preview")


def _parents_current(op: dict[str, Any], source_fd: int, destination_fd: int) -> None:
    if (
        _identity(_owned_directory(source_fd)) != op["source_parent"]
        or _identity(_owned_directory(destination_fd)) != op["destination_parent"]
    ):
        raise ContractError("Parent directory identity changed after preview")


def _acquire_lock(descriptor: int, timeout: float = 30) -> None:
    deadline = time.monotonic() + timeout
    while True:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except OSError as exc:
            if exc.errno not in {errno.EAGAIN, errno.EWOULDBLOCK, errno.EINTR}:
                raise
            if time.monotonic() >= deadline:
                raise ContractError("Another Files Buddy writer still holds this lock; no action was replayed") from exc
            time.sleep(0.05)


@contextlib.contextmanager
def _scope_locks(plan: dict[str, Any]) -> Iterator[None]:
    """Serialize cooperating executions even with different state directories.

    Lock owned directory inodes from roots through their owned ancestors in a
    stable order. Overlapping roots therefore share a lock. This is advisory;
    Finder, editors, and arbitrary same-user processes need not cooperate.
    """
    with contextlib.ExitStack() as stack:
        descriptors: dict[tuple[int, int], int] = {}
        paths: set[Path] = set()
        for root in plan["source_roots"] + plan["destination_roots"]:
            path = Path(root["path"])
            paths.update((path, *path.parents))
        for path in sorted(paths):
            descriptor = stack.enter_context(open_directory(path))
            info = os.fstat(descriptor)
            if info.st_uid == os.getuid() and not info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
                descriptors[(info.st_dev, info.st_ino)] = descriptor
        for key in sorted(descriptors):
            _acquire_lock(descriptors[key])
        yield


def _rename_exclusive(source_fd: int, source: str, destination_fd: int, destination: str) -> None:
    # Apple's xnu f6217f891ac0bb64f3d375211650a4c1ff8ca1ea bsd/sys/stdio.h:
    # renameatx_np(..., RENAME_EXCL=0x4). Linux uses renameat2/NOREPLACE for tests.
    libc = ctypes.CDLL(None, use_errno=True)
    system = platform.system()
    name, flag = ("renameatx_np", 4) if system == "Darwin" else ("renameat2", 1)
    try:
        function = getattr(libc, name)
    except AttributeError as exc:
        raise ContractError("Native no-clobber rename is unavailable; no unsafe fallback") from exc
    function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    if function(source_fd, os.fsencode(source), destination_fd, os.fsencode(destination), flag) != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), destination)


def _content_matches(actual: dict[str, Any], expected: dict[str, Any], *, identity: bool) -> bool:
    keys = {"kind", "size_bytes", "mode", "uid", "gid", "nlink", "mtime_ns", "sha256"}
    if identity:
        keys |= {"device", "inode"}
    return all(actual[key] == expected[key] for key in keys)


def _effect(op: dict[str, Any], fault: Callable[[str], None]) -> dict[str, Any]:
    source, destination = Path(op["source"]), Path(op["destination"])
    _project_check(source)
    _project_check(destination)
    with open_directory(source.parent) as source_fd, open_directory(destination.parent) as destination_fd:
        _parents_current(op, source_fd, destination_fd)
        _absent(destination_fd, destination.name)
        descriptor = _read_file(source_fd, source.name)
        try:
            if snapshot(descriptor) != op["before"]:
                raise ContractError("Source evidence changed after preview")
            # Open descriptor evidence and entry identity must agree immediately
            # before the native operation. Other same-user apps remain uncooperative.
            if _identity(os.stat(source.name, dir_fd=source_fd, follow_symlinks=False)) != _identity(
                os.fstat(descriptor)
            ):
                raise ContractError("Source directory entry changed")
            fault("before-effect")
            current = os.stat(source.name, dir_fd=source_fd, follow_symlinks=False)
            if (
                _identity(current) != {"device": op["before"]["device"], "inode": op["before"]["inode"]}
                or current.st_size != op["before"]["size_bytes"]
                or current.st_mtime_ns != op["before"]["mtime_ns"]
                or current.st_ctime_ns != op["before"]["ctime_ns"]
            ):
                raise ContractError("Source entry changed at execution boundary")
            if op["type"] == "copy":
                created = os.open(
                    destination.name, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=destination_fd
                )
                try:
                    os.lseek(descriptor, 0, os.SEEK_SET)
                    remaining = op["before"]["size_bytes"]
                    while remaining:
                        block = os.read(descriptor, min(remaining, 1024 * 1024))
                        if not block:
                            raise ContractError("Copy source shrank during execution")
                        view = memoryview(block)
                        while view:
                            written = os.write(created, view)
                            if written <= 0:
                                raise OSError("Copy write made no progress")
                            view = view[written:]
                        remaining -= len(block)
                        fault("copy-chunk")
                    if os.read(descriptor, 1):
                        raise ContractError("Copy source grew beyond the approved byte count")
                    # Only restore ordinary mode/time on the newly created file.
                    os.fchmod(created, stat.S_IMODE(op["before"]["mode"]))
                    os.utime(created, ns=(os.fstat(descriptor).st_atime_ns, op["before"]["mtime_ns"]))
                    os.fsync(created)
                    fault("after-effect")
                    after = snapshot(created)
                    if snapshot(descriptor) != op["before"] or not _content_matches(
                        after, op["before"], identity=False
                    ):
                        raise ContractError("Copy/source content or basic metadata changed during execution")
                    if _identity(os.stat(destination.name, dir_fd=destination_fd, follow_symlinks=False)) != _identity(
                        os.fstat(created)
                    ):
                        raise ContractError("Copy destination entry changed during execution")
                finally:
                    os.close(created)
            else:
                _rename_exclusive(source_fd, source.name, destination_fd, destination.name)
                fault("after-effect")
                after = _file_snapshot(destination)
                _absent(source_fd, source.name)
                if not _content_matches(after, op["before"], identity=True):
                    raise ContractError("Moved object no longer matches approved evidence")
            os.fsync(source_fd)
            os.fsync(destination_fd)
            _parents_current(op, source_fd, destination_fd)
            return after
        finally:
            os.close(descriptor)


def _postcondition(op: dict[str, Any], after: dict[str, Any] | None) -> dict[str, Any]:
    actual = _file_snapshot(Path(op["destination"]))
    expected = after if after is not None else op["before"]
    if not _content_matches(actual, expected, identity=after is not None or op["type"] != "copy"):
        raise ContractError("Destination content, metadata, or identity does not match")
    if op["type"] == "copy":
        if _file_snapshot(Path(op["source"])) != op["before"]:
            raise ContractError("Copy source is no longer the approved source")
    elif os.path.lexists(op["source"]):
        raise ContractError("Original source path is occupied after move")
    return actual


def _save(store: StateStore, state: dict[str, Any]) -> None:
    state["updated_at"] = now()
    store.write(state)


def execute(
    store: StateStore, reference: str, approval: str, *, undo: bool = False, fault: Callable[[str], None] | None = None
) -> dict[str, Any]:
    """Execute core operations. CLI enforces Darwin; tests exercise POSIX fixtures.

    ``fault`` is an in-process test seam, never exposed through CLI/environment.
    Raising BaseException simulates termination across a durable boundary.
    """
    callback = fault or (lambda _boundary: None)
    with store.lock(), contextlib.ExitStack() as scope:
        state = validate_state(store.read(store.resolve(reference)))
        data = state["undo"] if undo else state
        if data is None:
            raise ContractError("Preview a reverse plan with undo before approving it")
        if approval != data["plan_digest"]:
            raise ContractError("Explicit approval must exactly match the displayed plan digest")
        if state["status"] == "undone" or (not undo and state["undo"] is not None):
            raise ContractError("This state has entered recovery and cannot execute forward")
        if any(record["status"] != "planned" for record in data["operations"]):
            raise ContractError("Run already started; reconcile and review a new plan instead of replaying")
        scope.enter_context(_scope_locks(data["plan"]))
        _roots_current(data["plan"])
        data["approval"] = {"plan_digest": approval, "received_at": now(), "source": "trusted-invoker-cli"}
        state["status"] = "running"
        _save(store, state)
        for op, record in zip(data["plan"]["operations"], data["operations"], strict=True):
            record.update(status="prepared", updated_at=now(), error=None)
            _save(store, state)
            callback("prepared")
            try:
                _roots_current(data["plan"])
                after = _effect(op, callback)
                record.update(status="applied", after=after, updated_at=now())
                _save(store, state)
                callback("applied")
                _roots_current(data["plan"])
                verified = _postcondition(op, after)
                record.update(status="verified", after=verified, updated_at=now())
                _save(store, state)
                callback("verified")
            except (OSError, ContractError) as exc:
                # Any failure after prepared may have effects. Never retry from
                # error type alone, and never clean up an ambiguous user path.
                record.update(status="uncertain", error=str(exc), updated_at=now())
                state["status"] = "partial"
                _save(store, state)
                return state
        state["status"] = "undone" if undo else "completed"
        _save(store, state)
        return state


def reconcile(store: StateStore, reference: str) -> dict[str, Any]:
    """Observe interrupted work; never replay a filesystem mutation."""
    with store.lock():
        state = validate_state(store.read(store.resolve(reference)))
        data = state["undo"] if state["undo"] is not None and state["undo"]["approval"] is not None else state
        if data["approval"] is None:
            return state
        _roots_current(data["plan"])
        for op, record in zip(data["plan"]["operations"], data["operations"], strict=True):
            if record["status"] in {"planned", "failed", "conflict"}:
                continue
            try:
                # A copy without a recorded destination inode cannot establish
                # that an identical object was created by this run.
                if op["type"] == "copy" and record["after"] is None:
                    raise ContractError("Copy has no durable destination identity; manual reconciliation required")
                after = _postcondition(op, record["after"])
                record.update(status="verified", after=after, error=None, updated_at=now())
            except (OSError, ContractError) as exc:
                record.update(status="uncertain", error=str(exc), updated_at=now())
        complete = all(record["status"] == "verified" for record in data["operations"])
        state["status"] = ("undone" if data is state["undo"] else "completed") if complete else "partial"
        _save(store, state)
        return state


def reverse_plan(store: StateStore, reference: str) -> dict[str, Any]:
    with store.lock():
        state = validate_state(store.read(store.resolve(reference)))
        if state["undo"] is not None:
            return state
        if state["status"] != "completed" or any(record["status"] != "verified" for record in state["operations"]):
            raise ContractError("Reconcile to fully verified completion before creating a reverse plan")
        _roots_current(state["plan"])
        mapping = []
        for op, record in reversed(list(zip(state["plan"]["operations"], state["operations"], strict=True))):
            _postcondition(op, record["after"])
            destination = Path(op["source"])
            if op["type"] == "copy":
                destination = Path(op["destination"]).with_name(
                    f".files-buddy-undo-{state['run_id']}-{op['operation_id']}"
                )
            mapping.append({"type": "move", "source": op["destination"], "destination": str(destination)})
        roots = {root["path"] for root in state["plan"]["source_roots"] + state["plan"]["destination_roots"]}
        plan = make_plan(
            mapping,
            [Path(root["path"]) for root in state["plan"]["destination_roots"]],
            [Path(root) for root in sorted(roots)],
            f"Reverse {state['run_id']}; created copies are retained in quarantine, not deleted",
            local_only=True,
        )
        state["undo"] = {
            "plan": plan,
            "plan_digest": canonical_digest(plan),
            "approval": None,
            "operations": _records(plan),
        }
        _save(store, state)
        return state


def validate_outcomes(state: dict[str, Any]) -> list[str]:
    validate_state(state)
    errors = []
    data = state["undo"] if state["undo"] is not None and state["undo"]["approval"] is not None else state
    _roots_current(data["plan"])
    for op, record in zip(data["plan"]["operations"], data["operations"], strict=True):
        if record["status"] == "verified":
            try:
                _postcondition(op, record["after"])
            except (OSError, ContractError) as exc:
                errors.append(f"{op['operation_id']}: {exc}")
        elif record["status"] == "planned":
            try:
                source, destination = Path(op["source"]), Path(op["destination"])
                with open_directory(source.parent) as source_fd, open_directory(destination.parent) as destination_fd:
                    _parents_current(op, source_fd, destination_fd)
                    _absent(destination_fd, destination.name)
                if _file_snapshot(source) != op["before"]:
                    raise ContractError("Source evidence changed after preview")
            except (OSError, ContractError) as exc:
                errors.append(f"{op['operation_id']}: {exc}")
        else:
            errors.append(f"{op['operation_id']}: unresolved {record['status']}")
    return errors


def inspect_legacy(value: Any, *, verify_files: bool = False) -> dict[str, Any]:
    """Read persisted v1 ledgers without upgrading their authority or hash meaning."""
    if not isinstance(value, dict) or value.get("version") != "1.0":
        raise ContractError("Unsupported manifest version")
    required = {"version", "created", "mode", "intent", "target_path", "status", "operations", "summary"}
    if (
        not required.issubset(value)
        or not isinstance(value["status"], str)
        or value["status"] not in {"open", "closed", "partial", "undone"}
    ):
        raise ContractError("Malformed legacy ledger")
    _text(value["mode"], "legacy mode")
    _text(value["intent"], "legacy intent")
    if not isinstance(value["summary"], dict):
        raise ContractError("Legacy summary must be an object")
    _timestamp(value["created"], "created")
    scope = _path(value["target_path"], "legacy target_path")
    operations = value["operations"]
    if not isinstance(operations, list) or len(operations) > MAX_OPERATIONS:
        raise ContractError("Invalid legacy operations")
    errors = []
    for index, op in enumerate(operations):
        try:
            if not isinstance(op, dict):
                raise ContractError("Legacy operation must be an object")
            op = cast("dict[str, Any]", op)
            if (
                not isinstance(op.get("type"), str)
                or not isinstance(op.get("status"), str)
                or op.get("type")
                not in {"move", "rename", "copy", "trash", "mkdir", "archive", "cloud-offload", "cache-prune"}
                or op.get("status") not in {"completed", "failed"}
            ):
                raise ContractError("Unknown legacy operation/status")
            _timestamp(op.get("timestamp"), "operation timestamp")
            for key in ("size_bytes", "bytes"):
                if key in op:
                    _integer(op[key], key)
            for key in ("source", "path", "destination", "target"):
                if key in op and not _within(_path(op[key], key), scope):
                    raise ContractError("Legacy operation is outside target_path")
            if op["status"] != "completed":
                continue
            destination = _path(op.get("destination", op.get("target")), "destination")
            if op["type"] != "mkdir":
                _path(op.get("source", op.get("path")), "source")
                recorded = op.get("blake3", op.get("hash"))
                if not isinstance(recorded, str) or not HEX64.fullmatch(recorded):
                    raise ContractError("Legacy completed file operation requires a BLAKE3 digest")
            if not verify_files:
                continue
            if value.get("cloud_tagged") is True:
                raise ContractError("Legacy cloud outcomes require manual provider verification without hydration")
            _policy_path(destination)
            if op["type"] == "mkdir":
                with open_directory(destination):
                    pass
            else:
                with open_directory(destination.parent) as parent_fd:
                    descriptor = _read_file(parent_fd, destination.name)
                    try:
                        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                            raise ContractError("Legacy outcome is not a regular file")
                        with os.fdopen(os.dup(descriptor), "rb") as stream:
                            result = subprocess.run(
                                ["b3sum", "--no-names"],
                                stdin=stream,
                                capture_output=True,
                                text=True,
                                timeout=60,
                                check=False,
                            )
                        if result.returncode or result.stdout.strip() != recorded:
                            raise ContractError("Legacy BLAKE3 outcome verification failed")
                    finally:
                        os.close(descriptor)
        except (OSError, ContractError, subprocess.SubprocessError) as exc:
            errors.append(f"Operation {index}: {exc}")
    return {
        "legacy": True,
        "read_only": True,
        "valid": not errors,
        "errors": errors,
        "hash_algorithm": "blake3",
        "execution_supported": False,
        "data": value,
    }
