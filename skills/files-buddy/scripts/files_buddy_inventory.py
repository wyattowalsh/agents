"""Bounded metadata inventories and explicit local-content duplicate review.

SQLite is an observation cache, never execution or approval state. A resumed
walk re-stats each encountered object; directory timestamps never validate
descendant hashes. The report is a bounded view of the on-disk inventory.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import sqlite3
import stat
import time
import uuid
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict, cast

from files_buddy_report import new_report, normalize_report

if TYPE_CHECKING:
    from collections.abc import Iterator

PROJECT_MARKERS = (".git", "pyproject.toml", "package.json", "Cargo.toml", "go.mod", "CMakeLists.txt")
PACKAGE_SUFFIXES = (
    ".app",
    ".photoslibrary",
    ".photolibrary",
    ".musiclibrary",
    ".logicx",
    ".band",
    ".vmwarevm",
    ".pvm",
    ".sparsebundle",
    ".backupbundle",
    ".backupdb",
)
MODEL_SUFFIXES = {".gguf", ".safetensors", ".ckpt", ".onnx"}
SIDECAR_SUFFIXES = {".xmp", ".aae", ".srt", ".cue"}
ARCHIVE_SUFFIXES = {".zip", ".tar", ".gz", ".xz", ".zst", ".7z", ".rar"}
PROTECTED_COMPONENTS = {".git", ".ssh", ".gnupg", ".aws", ".kube", ".config", "keyrings"}
CACHE_COMPONENTS = {
    "node_modules",
    "caches",
    ".cache",
    ".npm",
    ".pnpm-store",
    ".cargo",
    ".rustup",
    ".gradle",
    ".m2",
    ".yarn",
    ".conda",
}
MODEL_COMPONENTS = {".ollama", ".lmstudio", ".huggingface"}
MANAGED_COMPONENTS = {"library", ".docker", ".virtualenvs", "backups.backupdb"}
NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
DIRECTORY = getattr(os, "O_DIRECTORY", 0)


class InventoryError(ValueError):
    """An invalid scope, stale inventory, or unsupported observation."""


class InventoryPolicy(TypedDict):
    include_hidden: bool
    cross_filesystems: bool
    excludes: list[str]
    cloud_roots: list[str]
    max_depth: int
    gitignore: str


class InventoryMetadata(TypedDict):
    schema_version: str
    run_id: str
    root: str
    root_identity: list[int]
    database: str
    policy: InventoryPolicy
    epoch: int
    updated_at: str
    coverage: str
    errors: int
    skipped: int
    changed_entries: int
    deleted_entries: int
    omissions: list[str]


@dataclass(frozen=True)
class ScanOptions:
    """Explicit inventory policy; budgets are per invocation, not permissions."""

    include_hidden: bool = False
    cross_filesystems: bool = False
    excludes: tuple[str, ...] = ()
    cloud_roots: tuple[str, ...] = ()
    max_entries: int = 100_000
    max_seconds: float = 60.0
    max_rows: int = 500
    max_depth: int = 64

    def validate(self) -> None:
        if not 1 <= self.max_entries <= 10_000_000 or not 0 < self.max_seconds <= 3600:
            raise InventoryError("Inventory budgets must be 1..10000000 entries and 0..3600 seconds")
        if not 1 <= self.max_rows <= 10_000 or not 1 <= self.max_depth <= 64:
            raise InventoryError("Report rows must be 1..10000 and traversal depth 1..64")
        if len(self.excludes) > 128 or len(self.cloud_roots) > 128:
            raise InventoryError("Too many exclusion or cloud-root rules")
        for value in self.cloud_roots:
            path = Path(value).expanduser().absolute()
            if ".." in path.parts or any(part.is_symlink() for part in (path, *path.parents)):
                raise InventoryError("Cloud-root policy paths cannot contain traversal or symlinks")

    def policy(self) -> InventoryPolicy:
        return {
            "include_hidden": self.include_hidden,
            "cross_filesystems": self.cross_filesystems,
            "excludes": list(self.excludes),
            "cloud_roots": list(self.cloud_roots),
            "max_depth": self.max_depth,
            "gitignore": "not interpreted; project trees are report-only",
        }


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _root_path(value: Path) -> Path:
    root = value.expanduser().absolute()
    if ".." in root.parts:
        raise InventoryError("Use a normalized scope without '..'")
    for component in (root, *root.parents):
        if component.is_symlink():
            raise InventoryError("Scope paths cannot traverse symlinks")
    if not root.is_dir() or root == Path("/"):
        raise InventoryError("Use one existing directory, not the filesystem root")
    policy_root = Path(str(root).casefold())
    for protected in map(Path, ("/system", "/library", "/usr", "/bin", "/sbin", "/etc", "/private", "/var")):
        if policy_root == protected or protected in policy_root.parents:
            raise InventoryError("Scope is a protected system subtree")
    return root


def _open_directory(path: Path, *, create: bool = False) -> int:
    """Open a directory from / using non-following handles for every component."""
    if not path.is_absolute() or ".." in path.parts:
        raise InventoryError("Directory handles require an absolute path without traversal")
    fd = os.open("/", os.O_RDONLY | DIRECTORY | NOFOLLOW)
    try:
        for part in path.parts[1:]:
            if create:
                with suppress(FileExistsError):
                    os.mkdir(part, mode=0o700, dir_fd=fd)
            child = os.open(part, os.O_RDONLY | DIRECTORY | NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def artifact_path(value: Path, *, root: Path | None = None) -> Path:
    """Validate an artifact location before any directory or file creation.

    Do not resolve away symlinks or parent traversal. Compare existing parent
    identities as well as path strings, including case aliases on macOS.
    """
    path = value.expanduser().absolute()
    if ".." in path.parts:
        raise InventoryError("Use an observation artifact path without '..'")
    root_identity = None
    if root is not None:
        root = root.expanduser().absolute()
        if path == root or root in path.parents:
            raise InventoryError("Observation artifacts must be outside the observed tree")
        try:
            info = root.stat(follow_symlinks=False)
            root_identity = (info.st_dev, info.st_ino)
        except FileNotFoundError:
            pass
    for component in (path, *path.parents):
        try:
            info = component.stat(follow_symlinks=False)
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode):
            raise InventoryError("Observation artifact paths cannot traverse symlinks")
        if root_identity == (info.st_dev, info.st_ino):
            raise InventoryError("Observation artifacts must be outside the observed tree")
    return path


def _fingerprint(info: os.stat_result) -> str:
    return json.dumps(
        [
            info.st_dev,
            info.st_ino,
            info.st_mode,
            info.st_uid,
            info.st_size,
            info.st_mtime_ns,
            info.st_ctime_ns,
            info.st_nlink,
            getattr(info, "st_flags", 0),
        ],
        separators=(",", ":"),
    )


def _kind(info: os.stat_result) -> str:
    if stat.S_ISREG(info.st_mode):
        return "file"
    if stat.S_ISDIR(info.st_mode):
        return "directory"
    if stat.S_ISLNK(info.st_mode):
        return "symlink"
    return "special"


def _sidecar_names(path: Path) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                base + extension
                for base in (path.stem, path.name)
                for suffix in SIDECAR_SUFFIXES
                for extension in (suffix, suffix.upper())
            }
        )
    )


def _cloud_path(path: Path, cloud_roots: tuple[str, ...]) -> bool:
    if any(
        part.casefold() in {"cloudstorage", "mobile documents", "dropbox", "google drive"}
        or part.casefold().startswith(("onedrive", "googledrive"))
        for part in path.parts
    ):
        return True
    policy_path = Path(str(path).casefold())
    return any(
        policy_path == Path(str(Path(root).expanduser().absolute()).casefold())
        or Path(str(Path(root).expanduser().absolute()).casefold()) in policy_path.parents
        for root in cloud_roots
    )


def _classification(
    path: Path, info: os.stat_result, inherited: str | None, options: ScanOptions
) -> tuple[str, list[str], bool]:
    kind = _kind(info)
    category = inherited or "user-files"
    evidence: list[str] = []
    if any(
        part.casefold() in PROTECTED_COMPONENTS or part.casefold() == ".env" or part.casefold().startswith(".env.")
        for part in path.parts
    ):
        category = "protected"
    elif _cloud_path(path, options.cloud_roots) or path.name.casefold().endswith(".icloud"):
        category = "cloud"
    elif any(part.lower().endswith(PACKAGE_SUFFIXES) for part in path.parts):
        category = "app-managed"
    elif category not in {"project", "protected", "app-managed", "cloud"}:
        if any(part.casefold() in CACHE_COMPONENTS for part in path.parts):
            category = "cache"
        elif path.suffix.lower() in MODEL_SUFFIXES or any(part.casefold() in MODEL_COMPONENTS for part in path.parts):
            category = "model"
        elif any(part.casefold() in MANAGED_COMPONENTS for part in path.parts):
            category = "app-data"
        elif path.suffix.lower() in SIDECAR_SUFFIXES:
            category = "sidecar"
        elif path.suffix.lower() in {".vmdk", ".vhd", ".vhdx", ".qcow2"}:
            category = "vm"
        elif path.suffix.lower() in ARCHIVE_SUFFIXES:
            category = "archive"
    if category != "user-files":
        evidence.append(f"{category} ownership/dependency review required")
    if kind != "file":
        evidence.append(f"{kind} is not an eligible regular-file content candidate")
    if info.st_nlink > 1 and kind == "file":
        evidence.append("multiple hardlinks; identity is (device,inode), not pathname")
    if getattr(info, "st_flags", 0):
        evidence.append("filesystem flags present; residency/metadata semantics require native review")
    if info.st_uid != os.getuid():
        evidence.append("object is not owned by the current user")
    blocks = getattr(info, "st_blocks", None)
    if kind == "file" and blocks is not None and blocks * 512 < info.st_size:
        evidence.append("sparse/compressed/placeholder allocation; physical reclaimability unknown")
    eligible = (
        kind == "file"
        and category in {"user-files", "archive"}
        and not any(phrase for phrase in evidence if not phrase.startswith("archive "))
        and info.st_size > 0
    )
    # Archive identity can be observed, but archive creation/source release is separately gated.
    return category, evidence, eligible


def _directory_context(fd: int, inherited: str | None) -> str | None:
    if inherited in {"cloud", "app-managed", "protected", "project"}:
        return inherited
    for marker in PROJECT_MARKERS:
        try:
            os.stat(marker, dir_fd=fd, follow_symlinks=False)
            return "project"
        except FileNotFoundError:
            pass
    try:
        os.stat(".env", dir_fd=fd, follow_symlinks=False)
        return "protected"
    except FileNotFoundError:
        return inherited


def _ancestor_project(root: Path) -> bool:
    """Recognize an explicitly scoped subdirectory that belongs to a parent project."""
    for parent in root.parents:
        if parent == Path("/"):
            break
        fd = _open_directory(parent)
        try:
            for marker in PROJECT_MARKERS:
                try:
                    os.stat(marker, dir_fd=fd, follow_symlinks=False)
                    return True
                except FileNotFoundError:
                    pass
        finally:
            os.close(fd)
    return False


@contextmanager
def _database(path: Path, root: Path | None = None) -> Iterator[sqlite3.Connection]:
    path = artifact_path(path, root=root)
    for candidate in (path, *(path.with_name(path.name + suffix) for suffix in ("-journal", "-wal", "-shm"))):
        try:
            info = candidate.stat(follow_symlinks=False)
        except FileNotFoundError:
            continue
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise InventoryError("Inventory database and sidecars must be owned, singly linked regular files")
    if path.exists():
        # Dedupe obtains scope from the cache. Inspect it through a read-only
        # connection before opening a writer, so a relocated cache cannot write
        # back into its own source tree through journals or hash updates.
        if root is None:
            readonly = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True, timeout=5)
            try:
                readonly.execute("PRAGMA trusted_schema=OFF")
                tables = {row[0] for row in readonly.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if tables != {"metadata", "entries"}:
                    raise InventoryError("Not a Files Buddy inventory database; refusing to modify it")
                metadata = _read_meta(readonly)
                if metadata is None:
                    raise InventoryError("Inventory database has no scan metadata")
                artifact_path(path, root=_root_path(Path(metadata["root"])))
            finally:
                readonly.close()
    else:
        if root is None:
            raise InventoryError("Inventory database does not exist; scan before duplicate review")
        parent_fd = _open_directory(path.parent, create=True)
        try:
            fd = os.open(path.name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | NOFOLLOW, 0o600, dir_fd=parent_fd)
            os.close(fd)
        finally:
            os.close(parent_fd)
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA trusted_schema=OFF")
        connection.execute("BEGIN IMMEDIATE")
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables and tables != {"metadata", "entries"}:
            raise InventoryError("Not a Files Buddy inventory database; refusing to modify it")
        connection.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.execute("""CREATE TABLE IF NOT EXISTS entries (
            path TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, kind TEXT NOT NULL,
            size INTEGER NOT NULL, allocated INTEGER, device INTEGER NOT NULL,
            inode INTEGER NOT NULL, nlink INTEGER NOT NULL, mtime_ns INTEGER NOT NULL,
            ctime_ns INTEGER NOT NULL, category TEXT NOT NULL, evidence TEXT NOT NULL,
            eligible INTEGER NOT NULL, seen INTEGER NOT NULL,
            sha256 TEXT, hash_fingerprint TEXT)""")
        connection.execute("CREATE INDEX IF NOT EXISTS entries_size ON entries(size, eligible)")
        connection.execute("CREATE INDEX IF NOT EXISTS entries_hash ON entries(sha256)")
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def _read_meta(connection: sqlite3.Connection) -> InventoryMetadata | None:
    row = connection.execute("SELECT value FROM metadata WHERE key='scan'").fetchone()
    if row is None:
        return None
    data = json.loads(row[0])
    if not isinstance(data, dict) or data.get("schema_version") != "1.0":
        raise InventoryError("Unknown inventory schema")
    if set(data) != set(InventoryMetadata.__annotations__):
        raise InventoryError("Inventory metadata has missing or unsupported fields")
    for key in ("run_id", "root", "database", "updated_at", "coverage"):
        if not isinstance(data[key], str) or not data[key]:
            raise InventoryError(f"Invalid inventory metadata {key}")
    for key in ("root", "database"):
        path = Path(data[key])
        if not path.is_absolute() or ".." in path.parts or "\x00" in data[key] or str(path) != data[key]:
            raise InventoryError(f"Stored inventory {key} must be a normalized absolute path")
    for key in ("epoch", "errors", "skipped", "changed_entries", "deleted_entries"):
        if type(data[key]) is not int or data[key] < 0:
            raise InventoryError(f"Invalid inventory counter {key}")
    if data["coverage"] not in {"complete", "partial"}:
        raise InventoryError("Invalid stored inventory coverage")
    if (
        not isinstance(data["root_identity"], list)
        or len(data["root_identity"]) != 2
        or any(type(value) is not int or value < 0 for value in data["root_identity"])
    ):
        raise InventoryError("Invalid stored scope identity")
    if not isinstance(data["omissions"], list) or not all(isinstance(value, str) for value in data["omissions"]):
        raise InventoryError("Invalid stored omissions")
    policy = data["policy"]
    if not isinstance(policy, dict) or set(policy) != set(InventoryPolicy.__annotations__):
        raise InventoryError("Invalid stored inventory policy")
    if type(policy["include_hidden"]) is not bool or type(policy["cross_filesystems"]) is not bool:
        raise InventoryError("Invalid stored boolean policy")
    for key in ("excludes", "cloud_roots"):
        if not isinstance(policy[key], list) or not all(isinstance(value, str) for value in policy[key]):
            raise InventoryError(f"Invalid stored {key}")
    if (
        type(policy["max_depth"]) is not int
        or not 1 <= policy["max_depth"] <= 64
        or not isinstance(policy["gitignore"], str)
    ):
        raise InventoryError("Invalid stored traversal policy")
    return cast("InventoryMetadata", data)


def _save_meta(connection: sqlite3.Connection, value: InventoryMetadata) -> None:
    connection.execute("INSERT OR REPLACE INTO metadata VALUES ('scan', ?)", (json.dumps(value),))


def _row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "path": row["path"],
        "size": row["size"] if row["kind"] == "file" else None,
        "metadata_size_bytes": row["size"],
        "allocated_bytes": row["allocated"],
        "kind": row["kind"],
        "device": row["device"],
        "inode": row["inode"],
        "nlink": row["nlink"],
        "mtime_ns": row["mtime_ns"],
        "ctime_ns": row["ctime_ns"],
        "category": row["category"],
        "content_candidate": bool(row["eligible"]),
        "dependency_evidence": json.loads(row["evidence"]),
    }


def _report(connection: sqlite3.Connection, metadata: InventoryMetadata, max_rows: int) -> dict[str, Any]:
    report = new_report("storage-audit", metadata["root"])
    report.update(run_id=metadata["run_id"], updated_at=metadata["updated_at"], status="completed")
    epoch = metadata["epoch"]
    rows = connection.execute(
        "SELECT * FROM entries WHERE seen=? AND kind!='directory' ORDER BY size DESC,path LIMIT ?", (epoch, max_rows)
    ).fetchall()
    report["files"] = [_row_dict(row) for row in rows]
    report["directories"] = [
        _row_dict(row)
        for row in connection.execute(
            "SELECT * FROM entries WHERE seen=? AND kind='directory' ORDER BY path LIMIT ?", (epoch, max_rows)
        )
    ]
    count_rows = connection.execute("SELECT kind,COUNT(*) AS count FROM entries WHERE seen=? GROUP BY kind", (epoch,))
    by_kind = {row["kind"]: row["count"] for row in count_rows}
    report["counts"] = {
        "files_seen": by_kind.get("file", 0),
        "dirs_seen": by_kind.get("directory", 0),
        "links_seen": by_kind.get("symlink", 0),
        "special_seen": by_kind.get("special", 0),
        "skipped": metadata["skipped"],
        "errors": metadata["errors"],
        "changed_entries": metadata["changed_entries"],
        "deleted_entries": metadata["deleted_entries"],
    }
    totals = connection.execute(
        """SELECT SUM(size),SUM(allocated),COUNT(allocated),COUNT(*) FROM
        (SELECT MAX(size) AS size, MAX(allocated) AS allocated FROM entries
         WHERE seen=? AND kind='file' GROUP BY device,inode)""",
        (epoch,),
    ).fetchone()
    report["savings"] = {
        "logical_bytes": totals[0] or 0,
        "allocated_bytes": (totals[1] or 0) if totals[2] == totals[3] else None,
        "candidate_bytes": None,
        "selected_bytes": None,
        "acted_bytes": 0,
        "quarantined_bytes": 0,
        "trash_retained_bytes": None,
        "verified_reclaimed_bytes": None,
        "observed_free_space_delta_bytes": None,
        "cloud_bytes_affected": None,
    }
    report["coverage"] = {"status": metadata["coverage"], "omissions": metadata["omissions"]}
    report["inventory"] = {
        "policy": metadata["policy"],
        "database": metadata["database"],
        "read_content": False,
        "atomic_snapshot": False,
        "file_rows_truncated": sum(value for key, value in by_kind.items() if key != "directory") > len(rows),
        "directory_rows_truncated": by_kind.get("directory", 0) > max_rows,
        "bytes_are_unique_inode_estimates": True,
        "platform_qualification": "POSIX metadata observed; native APFS/provider semantics not inferred",
    }
    digest = hashlib.sha256()
    for row in connection.execute("SELECT path,fingerprint FROM entries WHERE seen=? ORDER BY path", (epoch,)):
        digest.update(json.dumps(list(row), ensure_ascii=True, separators=(",", ":")).encode())
        digest.update(b"\n")
    report["inventory"]["metadata_digest"] = "sha256:" + digest.hexdigest()
    for category_row in connection.execute(
        """SELECT category,SUM(size),COUNT(*) FROM
           (SELECT CASE WHEN COUNT(DISTINCT category)>1 THEN 'hardlink-shared'
                        ELSE MIN(category) END AS category, MAX(size) AS size
            FROM entries WHERE seen=? AND kind='file' GROUP BY device,inode)
           GROUP BY category""",
        (epoch,),
    ):
        report["categories"].append(
            {"name": category_row[0], "bytes": category_row[1], "count": category_row[2], "risk": "unknown"}
        )
    for row in report["files"]:
        if row["category"] in {"cloud", "cache", "model", "vm", "app-managed", "archive", "sidecar"}:
            report["recommendations"].append(
                {
                    "action": "review",
                    "path": row["path"],
                    "local_bytes": None,
                    "risk": "unknown",
                    "dependency_evidence": row["dependency_evidence"],
                    "repercussions": "Owner/provider/restore evidence is required before changing this object.",
                    "restore_path": None,
                    "qualification": "report-only",
                }
            )
    report["caches"] = [row for row in report["files"] if row["category"] in {"cache", "model"}]
    report["cloud"] = [row for row in report["files"] if row["category"] == "cloud"]
    return normalize_report(report)


def scan(root: Path, database: Path, *, options: ScanOptions | None = None, resume: bool = False) -> dict[str, Any]:
    """Refresh metadata with bounded memory, checkpoints, and no content reads.

    The entry budget counts new or changed objects. On resume, unchanged objects
    are still re-statted but do not spend that budget. A time budget always
    applies to the whole walk. Reusing a directory mtime to skip descendants is
    deliberately unsupported.
    """
    options = options or ScanOptions()
    options.validate()
    root = _root_path(root)
    database = database.expanduser().absolute()
    started = time.monotonic()
    root_fd = _open_directory(root)
    try:
        root_info = os.fstat(root_fd)
        with _database(database, root) as connection:
            previous = _read_meta(connection)
            if previous and not resume:
                raise InventoryError("Database already has an inventory; use --resume to revalidate it")
            identity = [root_info.st_dev, root_info.st_ino]
            if previous and (
                previous["root"] != str(root)
                or previous["root_identity"] != identity
                or previous["policy"] != options.policy()
            ):
                raise InventoryError("Resume scope identity or policy differs from the stored inventory")
            epoch = previous["epoch"] + 1 if previous else 1
            metadata: InventoryMetadata = {
                "schema_version": "1.0",
                "run_id": previous["run_id"] if previous else uuid.uuid4().hex,
                "root": str(root),
                "root_identity": identity,
                "database": str(database),
                "policy": options.policy(),
                "epoch": epoch,
                "updated_at": utc_now(),
                "coverage": "complete",
                "errors": 0,
                "skipped": 0,
                "changed_entries": 0,
                "deleted_entries": 0,
                "omissions": [],
            }

            def omit(message: str, *, error: bool = False, partial: bool = False) -> None:
                metadata["skipped"] += 1
                if error:
                    metadata["errors"] += 1
                if partial or error:
                    metadata["coverage"] = "partial"
                if len(metadata["omissions"]) < 50:
                    metadata["omissions"].append(message)

            def visit(fd: int, directory: Path, depth: int, inherited: str | None) -> bool:
                try:
                    context = _directory_context(fd, inherited)
                    with os.scandir(fd) as entries:
                        for item in entries:
                            if time.monotonic() - started >= options.max_seconds:
                                omit("Time budget reached; resume revalidates observed metadata", partial=True)
                                return False
                            path = directory / item.name
                            relative = str(path.relative_to(root))
                            if item.name.casefold() == ".git" or (
                                not options.include_hidden and item.name.startswith(".")
                            ):
                                omit(f"Policy exclusion: {relative}")
                                continue
                            if any(fnmatch.fnmatchcase(relative, pattern) for pattern in options.excludes):
                                omit(f"Explicit exclusion: {relative}")
                                continue
                            try:
                                info = item.stat(follow_symlinks=False)
                                category, evidence, eligible = _classification(path, info, context, options)
                                if eligible:
                                    for companion in _sidecar_names(path):
                                        try:
                                            os.stat(companion, dir_fd=fd, follow_symlinks=False)
                                            evidence.append(f"sidecar family present: {companion}")
                                            eligible = False
                                            break
                                        except FileNotFoundError:
                                            pass
                                fingerprint = _fingerprint(info)
                                old = connection.execute(
                                    "SELECT fingerprint FROM entries WHERE path=?", (str(path),)
                                ).fetchone()
                                changed = old is None or old[0] != fingerprint
                                if changed and metadata["changed_entries"] >= options.max_entries:
                                    omit(
                                        "Entry budget reached; resume re-stats known objects and continues",
                                        partial=True,
                                    )
                                    return False
                                metadata["changed_entries"] += int(changed)
                                allocated = getattr(info, "st_blocks", None)
                                allocated = allocated * 512 if allocated is not None else None
                                connection.execute(
                                    """INSERT INTO entries
                                    (path,fingerprint,kind,size,allocated,device,inode,nlink,mtime_ns,ctime_ns,
                                     category,evidence,eligible,seen) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                                    ON CONFLICT(path) DO UPDATE SET
                                     fingerprint=excluded.fingerprint,kind=excluded.kind,size=excluded.size,
                                     allocated=excluded.allocated,device=excluded.device,inode=excluded.inode,
                                     nlink=excluded.nlink,mtime_ns=excluded.mtime_ns,ctime_ns=excluded.ctime_ns,
                                     category=excluded.category,evidence=excluded.evidence,eligible=excluded.eligible,
                                     seen=excluded.seen,
                                     sha256=CASE WHEN entries.fingerprint=excluded.fingerprint AND excluded.eligible=1
                                                 THEN entries.sha256 ELSE NULL END,
                                     hash_fingerprint=CASE WHEN entries.fingerprint=excluded.fingerprint AND excluded.eligible=1
                                                           THEN entries.hash_fingerprint ELSE NULL END""",
                                    (
                                        str(path),
                                        fingerprint,
                                        _kind(info),
                                        info.st_size,
                                        allocated,
                                        info.st_dev,
                                        info.st_ino,
                                        info.st_nlink,
                                        info.st_mtime_ns,
                                        info.st_ctime_ns,
                                        category,
                                        json.dumps(evidence),
                                        int(eligible),
                                        epoch,
                                    ),
                                )
                                if _kind(info) != "directory":
                                    continue
                                if category in {"protected", "app-managed"}:
                                    omit(f"Owner-managed subtree not entered: {relative}")
                                    continue
                                if info.st_dev != root_info.st_dev and not options.cross_filesystems:
                                    omit(f"Mount boundary not crossed: {relative}")
                                    continue
                                if depth >= options.max_depth:
                                    omit(f"Depth budget reached: {relative}", partial=True)
                                    continue
                                child_fd = os.open(item.name, os.O_RDONLY | DIRECTORY | NOFOLLOW, dir_fd=fd)
                                try:
                                    child_info = os.fstat(child_fd)
                                    if (child_info.st_dev, child_info.st_ino) != (info.st_dev, info.st_ino):
                                        omit(f"Directory identity changed during scan: {relative}", partial=True)
                                        continue
                                    if not visit(
                                        child_fd, path, depth + 1, category if category != "user-files" else context
                                    ):
                                        return False
                                finally:
                                    os.close(child_fd)
                            except OSError as exc:
                                omit(f"Unavailable {relative}: {exc.__class__.__name__}", error=True)
                    return True
                except OSError as exc:
                    omit(f"Unavailable directory {directory}: {exc.__class__.__name__}", error=True)
                    return True

            root_category, _, _ = _classification(root, root_info, None, options)
            if root_category == "user-files" and _ancestor_project(root):
                root_category = "project"
            if root_category in {"protected", "app-managed"}:
                omit("Requested root is owner-managed/protected; no internal traversal", partial=True)
            else:
                visit(root_fd, root, 1, root_category if root_category != "user-files" else None)
            if metadata["coverage"] == "complete":
                metadata["deleted_entries"] = connection.execute(
                    "SELECT COUNT(*) FROM entries WHERE seen!=?", (epoch,)
                ).fetchone()[0]
                connection.execute("DELETE FROM entries WHERE seen!=?", (epoch,))
            metadata["updated_at"] = utc_now()
            _save_meta(connection, metadata)
            return _report(connection, metadata, options.max_rows)
    finally:
        os.close(root_fd)


@contextmanager
def _open_regular(root: Path, relative: Path, *, options: ScanOptions) -> Iterator[int]:
    """Anchor each path component and never follow a symlink while hashing."""
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise InventoryError("Candidate must be a strictly contained relative path without traversal")
    if len(relative.parts) > options.max_depth:
        raise InventoryError("Candidate exceeds the declared traversal depth")
    for index, part in enumerate(relative.parts, start=1):
        if part.casefold() == ".git" or (not options.include_hidden and part.startswith(".")):
            raise InventoryError("Candidate violates the declared hidden-file policy")
        prefix = str(Path(*relative.parts[:index]))
        if any(fnmatch.fnmatchcase(prefix, pattern) for pattern in options.excludes):
            raise InventoryError("Candidate violates a declared exclusion")
    if _ancestor_project(root):
        raise InventoryError("Candidate belongs to an ancestor project; refresh dependency review")
    fd = _open_directory(root)
    try:
        root_device = os.fstat(fd).st_dev
        if _directory_context(fd, None) in {"project", "protected"}:
            raise InventoryError("New project or sensitive marker requires dependency review")
        for part in relative.parts[:-1]:
            child = os.open(part, os.O_RDONLY | DIRECTORY | NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
            if not options.cross_filesystems and os.fstat(fd).st_dev != root_device:
                raise InventoryError("Candidate crosses a filesystem boundary")
            if _directory_context(fd, None) in {"project", "protected"}:
                raise InventoryError("New project or sensitive marker requires dependency review")
        for companion in _sidecar_names(relative):
            try:
                os.stat(companion, dir_fd=fd, follow_symlinks=False)
                raise InventoryError("New sidecar family requires dependency review")
            except FileNotFoundError:
                pass
        info = os.stat(relative.name, dir_fd=fd, follow_symlinks=False)
        if (not options.cross_filesystems and info.st_dev != root_device) or not _classification(
            root / relative, info, None, options
        )[2]:
            raise InventoryError("Candidate is no longer eligible for local content access")
        file_fd = os.open(relative.name, os.O_RDONLY | NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            if not stat.S_ISREG(os.fstat(file_fd).st_mode):
                raise InventoryError("Content candidate is no longer a regular file")
            yield file_fd
        finally:
            os.close(file_fd)
    finally:
        os.close(fd)


def dedupe(
    database: Path,
    *,
    read_content: bool = False,
    max_bytes: int = 2 * 1024**3,
    max_seconds: float = 60,
    max_rows: int = 500,
) -> dict[str, Any]:
    """Hash explicitly approved local candidates and emit review groups only."""
    if not read_content:
        raise InventoryError(
            "Content hashing requires --read-content; cloud/app-managed/protected candidates remain excluded"
        )
    if not 1 <= max_rows <= 10_000 or max_bytes <= 0 or not 0 < max_seconds <= 3600:
        raise InventoryError("Invalid duplicate-review budget")
    started = time.monotonic()
    bytes_read = 0
    with _database(database) as connection:
        metadata = _read_meta(connection)
        if metadata is None:
            raise InventoryError("Run a metadata scan before duplicate review")
        root = _root_path(Path(metadata["root"]))
        root_info = root.stat()
        if [root_info.st_dev, root_info.st_ino] != metadata["root_identity"]:
            raise InventoryError("Inventory root identity changed")
        epoch = metadata["epoch"]
        omissions = list(metadata["omissions"])
        partial = metadata["coverage"] != "complete"
        policy = metadata["policy"]
        options = ScanOptions(
            include_hidden=policy["include_hidden"],
            cross_filesystems=policy["cross_filesystems"],
            excludes=tuple(policy["excludes"]),
            cloud_roots=tuple(policy["cloud_roots"]),
            max_depth=policy["max_depth"],
        )
        options.validate()
        rows = connection.execute(
            """SELECT * FROM entries WHERE seen=? AND eligible=1 AND size IN
            (SELECT size FROM entries WHERE seen=? AND eligible=1 GROUP BY size HAVING COUNT(*)>1)
            ORDER BY size,path""",
            (epoch, epoch),
        )
        stop = False
        for row in rows:
            stored_path = row["path"]
            try:
                if not isinstance(stored_path, str) or "\x00" in stored_path:
                    raise InventoryError("Cached candidate path is not a valid string")
                path = Path(stored_path)
                if not path.is_absolute() or str(path) != stored_path or ".." in path.parts:
                    raise InventoryError("Cached candidate path must be normalized and absolute without traversal")
                if path == root or not path.is_relative_to(root):
                    raise InventoryError("Cached candidate path is outside the declared scope")
                if time.monotonic() - started >= max_seconds:
                    raise InventoryError("Hash time budget reached")
                with _open_regular(root, path.relative_to(root), options=options) as fd:
                    before = os.fstat(fd)
                    category, _, eligible = _classification(path, before, row["category"], options)
                    if not eligible or category in {"cloud", "project", "protected", "app-managed"}:
                        raise InventoryError("Candidate no longer has eligible local metadata")
                    current = _fingerprint(before)
                    if current != row["fingerprint"]:
                        raise InventoryError("Candidate metadata changed; refresh inventory")
                    if row["sha256"] and row["hash_fingerprint"] == current:
                        continue  # Cache is usable only after this fresh object-specific check.
                    if bytes_read + before.st_size > max_bytes:
                        raise InventoryError("Hash byte budget reached")
                    digest = hashlib.sha256()
                    while True:
                        if time.monotonic() - started >= max_seconds:
                            raise InventoryError("Hash time budget reached")
                        chunk = os.read(fd, 1024 * 1024)
                        if not chunk:
                            break
                        bytes_read += len(chunk)
                        if bytes_read > max_bytes:
                            raise InventoryError("Hash byte budget reached")
                        digest.update(chunk)
                    if _fingerprint(os.fstat(fd)) != current:
                        raise InventoryError("Candidate changed while hashing")
                    connection.execute(
                        "UPDATE entries SET sha256=?,hash_fingerprint=? WHERE path=?",
                        (digest.hexdigest(), current, str(path)),
                    )
            except (OSError, InventoryError) as exc:
                partial = True
                connection.execute("UPDATE entries SET sha256=NULL,hash_fingerprint=NULL WHERE path=?", (stored_path,))
                if len(omissions) < 50:
                    omissions.append(f"Not hashed {stored_path}: {exc}")
                if "budget" in str(exc):
                    stop = True
                    break
        # Clear unchecked cached hashes after a budget stop. They cannot support this report.
        if stop:
            for row in rows:
                connection.execute("UPDATE entries SET sha256=NULL,hash_fingerprint=NULL WHERE path=?", (row["path"],))
        report = _report(connection, metadata, max_rows)
        report.update(mode="dedupe", updated_at=utc_now())
        report["coverage"] = {"status": "partial" if partial else "complete", "omissions": omissions}
        report["duplicates"] = []
        candidate_bytes = 0
        group_count = 0
        remaining_paths = max_rows
        for group in connection.execute(
            """SELECT sha256,size,COUNT(*) AS count FROM entries
            WHERE seen=? AND eligible=1 AND sha256 IS NOT NULL AND hash_fingerprint=fingerprint
            GROUP BY sha256,size HAVING COUNT(DISTINCT device || ':' || inode)>1 ORDER BY size DESC,sha256""",
            (epoch,),
        ):
            group_count += 1
            candidate_bytes += group["size"] * (group["count"] - 1)
            if len(report["duplicates"]) >= max_rows or remaining_paths < 2:
                continue
            paths = [
                row[0]
                for row in connection.execute(
                    "SELECT path FROM entries WHERE seen=? AND sha256=? AND eligible=1 ORDER BY path LIMIT ?",
                    (epoch, group["sha256"], remaining_paths),
                )
            ]
            remaining_paths -= len(paths)
            report["duplicates"].append(
                {
                    "kind": "exact",
                    "hash_algorithm": "sha256",
                    "hash": group["sha256"],
                    "size": group["size"],
                    "files": paths,
                    "file_count": group["count"],
                    "files_truncated": len(paths) != group["count"],
                    "keeper": None,
                    "keeper_candidate": paths[0],
                    "keeper_rationale": "Stable display order only; no keeper selected.",
                    "candidate_bytes": group["size"] * (group["count"] - 1),
                    "risk": "unknown",
                    "review_only": True,
                    "dependency_evidence": [
                        "Exact content equality; metadata, intent, and keeper still require review."
                    ],
                }
            )
        report["savings"]["candidate_bytes"] = candidate_bytes
        report["counts"].update(duplicate_groups=group_count, bytes_hashed=bytes_read)
        report["inventory"].update(
            read_content=True,
            hash_algorithm="sha256",
            duplicate_groups_truncated=group_count > len(report["duplicates"]),
        )
        return normalize_report(report)


def watch(
    root: Path, database: Path, *, cycles: int = 3, interval: float = 2, options: ScanOptions | None = None
) -> dict[str, Any]:
    """Run a finite foreground metadata observer; never execute organizing rules."""
    if not 1 <= cycles <= 100 or not 0.1 <= interval <= 60 or cycles * interval > 3600:
        raise InventoryError("Watch requires 1..100 cycles, 0.1..60 second intervals, and <=1 hour total delay")
    options = options or ScanOptions()
    options.validate()
    if cycles * options.max_seconds + (cycles - 1) * interval > 3600:
        raise InventoryError("Combined watch scan/interval budget exceeds one hour; reduce cycles or --max-seconds")
    events = []
    previous: dict[str, tuple[Any, ...]] = {}
    stability: dict[str, int] = {}
    settled: list[dict[str, Any]] = []
    capped_settlement = False
    report: dict[str, Any] = {}
    for index in range(cycles):
        report = scan(root, database, options=options, resume=database.exists())
        current: dict[str, tuple[Any, ...]] = {}
        next_stability: dict[str, int] = {}
        settled = []
        capped_settlement = capped_settlement or report["inventory"]["file_rows_truncated"]
        for row in report["files"]:
            if row["kind"] != "file" or not row["content_candidate"]:
                continue
            path = row["path"]
            fingerprint = tuple(
                row[key] for key in ("device", "inode", "size", "mtime_ns", "ctime_ns", "nlink", "category")
            )
            current[path] = fingerprint
            count = stability.get(path, 1) + 1 if previous.get(path) == fingerprint else 1
            next_stability[path] = count
            if count >= 2:
                settled.append(
                    {
                        "path": path,
                        "observations": count,
                        "action": "review",
                        "risk": "unknown",
                        "local_bytes": None,
                        "restore_path": None,
                        "dependency_evidence": [
                            "Unchanged eligible metadata in consecutive foreground observations; fresh executor checks still required."
                        ],
                        "qualification": "proposal-only",
                    }
                )
        previous, stability = current, next_stability
        events.append(
            {
                "time": utc_now(),
                "level": "info",
                "message": f"Observation {index + 1}/{cycles}: {report['counts']['changed_entries']} changed metadata entries; no actions executed.",
            }
        )
        if index + 1 < cycles:
            time.sleep(interval)
    report.update(mode="watch", events=events)
    report["watch"] = {
        "cycles": cycles,
        "interval_seconds": interval,
        "proposal_only": True,
        "background_service": False,
        "standing_mutation_approval": False,
        "settled_candidates": settled,
        "settlement_coverage": "partial" if capped_settlement else report["coverage"]["status"],
        "settlement_rule": "same object/version in at least two consecutive observed file-row sets",
    }
    report["counts"]["settled_files"] = len(settled)
    report["recommendations"].extend(settled)
    if capped_settlement:
        report["coverage"]["status"] = "partial"
        report["coverage"]["omissions"].append(
            "Settled-file review is limited to capped exported file rows; unseen files are not settled."
        )
    return normalize_report(report)
