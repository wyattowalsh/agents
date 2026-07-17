#!/usr/bin/env python3
"""Safely sync portable asset_toolkit modules into skill bundles."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import os
import re
import stat
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
SKILLS_DIR = REPO_ROOT / "skills"

MODULES = (
    "__init__.py",
    "_shared.py",
    "common.py",
    "package.py",
    "validate_skill.py",
    "validate_evals.py",
    "validate_hooks.py",
)
SKILL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class SyncSafetyError(ValueError):
    """Raised when a toolkit sync target cannot be updated safely."""


@dataclass(frozen=True)
class SyncOperation:
    source: Path
    destination: Path
    payload: bytes
    mode: int
    status: str
    destination_snapshot: DestinationSnapshot | None


@dataclass(frozen=True)
class DestinationSnapshot:
    device: int
    inode: int
    size: int
    mtime_ns: int
    payload: bytes


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source(module: str) -> Path:
    if module in {"_shared.py", "package.py"}:
        return SCRIPT_DIR / module
    return SCRIPT_DIR / "asset_toolkit" / module


def _stat_is_reparse_point(observed: os.stat_result) -> bool:
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    attributes = getattr(observed, "st_file_attributes", 0)
    return bool(reparse_flag and attributes & reparse_flag)


def _path_is_junction(path: Path) -> bool:
    checker = getattr(path, "is_junction", None)
    if not callable(checker):
        return False
    try:
        return bool(checker())
    except OSError as exc:
        raise SyncSafetyError(f"cannot inspect path for junctions {path}: {exc}") from exc


def _is_link_or_reparse_point(path: Path, observed: os.stat_result) -> bool:
    return stat.S_ISLNK(observed.st_mode) or _stat_is_reparse_point(observed) or _path_is_junction(path)


def _lstat(path: Path, *, label: str, allow_missing: bool = False) -> os.stat_result | None:
    try:
        observed = path.lstat()
    except FileNotFoundError:
        if allow_missing:
            return None
        raise SyncSafetyError(f"missing {label}: {path}") from None
    except OSError as exc:
        raise SyncSafetyError(f"cannot inspect {label} {path}: {exc}") from exc
    if _is_link_or_reparse_point(path, observed):
        raise SyncSafetyError(f"symbolic link, junction, or reparse point is forbidden for {label}: {path}")
    return observed


def _assert_directory(path: Path, *, label: str, allow_missing: bool = False) -> bool:
    observed = _lstat(path, label=label, allow_missing=allow_missing)
    if observed is None:
        return False
    if not stat.S_ISDIR(observed.st_mode):
        raise SyncSafetyError(f"expected directory for {label}: {path}")
    return True


def _assert_regular_file(path: Path, *, label: str, allow_missing: bool = False) -> os.stat_result | None:
    observed = _lstat(path, label=label, allow_missing=allow_missing)
    if observed is None:
        return None
    if not stat.S_ISREG(observed.st_mode):
        raise SyncSafetyError(f"expected regular file for {label}: {path}")
    return observed


def _read_regular_file_no_follow(path: Path, *, label: str) -> tuple[bytes, os.stat_result]:
    before = _assert_regular_file(path, label=label)
    assert before is not None
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise SyncSafetyError(f"cannot open {label} without following links {path}: {exc}") from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or _stat_is_reparse_point(opened)
            or opened.st_dev != before.st_dev
            or opened.st_ino != before.st_ino
            or opened.st_size != before.st_size
            or opened.st_mtime_ns != before.st_mtime_ns
        ):
            raise SyncSafetyError(f"{label} changed while opening: {path}")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            payload = handle.read(opened.st_size + 1)
        after = os.fstat(descriptor)
        if len(payload) != opened.st_size or after.st_size != opened.st_size or after.st_mtime_ns != opened.st_mtime_ns:
            raise SyncSafetyError(f"{label} changed while reading: {path}")
        return payload, opened
    finally:
        os.close(descriptor)


def _validate_skill_id(skill_id: str) -> None:
    if not SKILL_ID_RE.fullmatch(skill_id):
        raise SyncSafetyError(f"invalid skill id: {skill_id!r}")


def _validate_skill_dir(skill_dir: Path) -> None:
    try:
        skill_dir.relative_to(SKILLS_DIR)
    except ValueError as exc:
        raise SyncSafetyError(f"skill directory escapes skills root: {skill_dir}") from exc
    _assert_directory(skill_dir, label="skill root")
    _assert_regular_file(skill_dir / "SKILL.md", label="skill definition")


def _skill_dirs(skill_ids: list[str] | None) -> list[Path]:
    _assert_directory(SKILLS_DIR, label="skills root")
    if skill_ids is not None:
        if not skill_ids:
            raise SyncSafetyError("--skill-ids requires at least one skill id")
        if len(set(skill_ids)) != len(skill_ids):
            raise SyncSafetyError("--skill-ids contains duplicate values")
        skill_dirs: list[Path] = []
        missing: list[str] = []
        for skill_id in skill_ids:
            _validate_skill_id(skill_id)
            skill_dir = SKILLS_DIR / skill_id
            if not skill_dir.exists():
                missing.append(skill_id)
                continue
            _validate_skill_dir(skill_dir)
            skill_dirs.append(skill_dir)
        if missing:
            raise SyncSafetyError(f"unknown skill ids: {', '.join(sorted(missing))}")
        if not skill_dirs:
            raise SyncSafetyError("skill selection is empty")
        return skill_dirs

    skill_dirs = []
    for candidate in sorted(SKILLS_DIR.iterdir()):
        observed = _lstat(candidate, label="skills entry")
        assert observed is not None
        if not stat.S_ISDIR(observed.st_mode):
            continue
        skill_md = candidate / "SKILL.md"
        if not skill_md.exists():
            continue
        _validate_skill_dir(candidate)
        skill_dirs.append(candidate)
    if not skill_dirs:
        raise SyncSafetyError("no skill directories were discovered")
    return skill_dirs


def _validate_target_parents(skill_dir: Path) -> None:
    _validate_skill_dir(skill_dir)
    scripts_dir = skill_dir / "scripts"
    if not _assert_directory(scripts_dir, label="skill scripts directory", allow_missing=True):
        return
    _assert_directory(
        scripts_dir / "asset_toolkit",
        label="bundled toolkit directory",
        allow_missing=True,
    )


def _build_operations(skill_dirs: list[Path], modules: tuple[str, ...] = MODULES) -> list[SyncOperation]:
    if not skill_dirs:
        raise SyncSafetyError("skill selection is empty")
    if not modules:
        raise SyncSafetyError("module selection is empty")
    if len(set(modules)) != len(modules):
        raise SyncSafetyError("module selection contains duplicate values")
    unknown_modules = sorted(set(modules) - set(MODULES))
    if unknown_modules:
        raise SyncSafetyError(f"unknown toolkit modules: {', '.join(unknown_modules)}")

    sources: dict[str, tuple[Path, bytes, int]] = {}
    for module in modules:
        source = _source(module)
        _assert_directory(source.parent, label="toolkit source directory")
        payload, observed = _read_regular_file_no_follow(source, label="toolkit source module")
        sources[module] = (source, payload, stat.S_IMODE(observed.st_mode))

    operations: list[SyncOperation] = []
    for skill_dir in skill_dirs:
        _validate_target_parents(skill_dir)
        destination_dir = skill_dir / "scripts" / "asset_toolkit"
        for module in modules:
            source, payload, mode = sources[module]
            destination = destination_dir / module
            existing = _assert_regular_file(
                destination,
                label="bundled toolkit module",
                allow_missing=True,
            )
            if existing is None:
                status = "missing"
                destination_snapshot = None
            else:
                current, observed = _read_regular_file_no_follow(destination, label="bundled toolkit module")
                status = "current" if current == payload else "stale"
                destination_snapshot = DestinationSnapshot(
                    device=observed.st_dev,
                    inode=observed.st_ino,
                    size=observed.st_size,
                    mtime_ns=observed.st_mtime_ns,
                    payload=current,
                )
            operations.append(SyncOperation(source, destination, payload, mode, status, destination_snapshot))
    return operations


def _mismatches(skill_dirs: list[Path], modules: tuple[str, ...] = MODULES) -> list[str]:
    issues: list[str] = []
    for operation in _build_operations(skill_dirs, modules):
        if operation.status == "current":
            continue
        skill_id = operation.destination.parents[2].name
        module = operation.destination.name
        issues.append(f"{skill_id}: {operation.status} scripts/asset_toolkit/{module}")
    return issues


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _ensure_target_directory(skill_dir: Path) -> Path:
    _validate_skill_dir(skill_dir)
    current = skill_dir
    for part in ("scripts", "asset_toolkit"):
        candidate = current / part
        if not candidate.exists():
            with contextlib.suppress(FileExistsError):
                candidate.mkdir(mode=0o755)
            _fsync_directory(current)
        _assert_directory(candidate, label="toolkit destination directory")
        current = candidate
    return current


def _atomic_publish(operation: SyncOperation) -> None:
    skill_dir = operation.destination.parents[2]
    destination_dir = _ensure_target_directory(skill_dir)
    if operation.destination.parent != destination_dir:
        raise SyncSafetyError(f"toolkit destination escapes expected directory: {operation.destination}")
    existing = _assert_regular_file(
        operation.destination,
        label="bundled toolkit module",
        allow_missing=True,
    )
    expected = operation.destination_snapshot
    if expected is None:
        if existing is not None:
            raise SyncSafetyError(f"bundled toolkit module appeared after preflight: {operation.destination}")
    else:
        if existing is None:
            raise SyncSafetyError(f"bundled toolkit module disappeared after preflight: {operation.destination}")
        current, observed = _read_regular_file_no_follow(
            operation.destination,
            label="bundled toolkit module",
        )
        if (
            observed.st_dev != expected.device
            or observed.st_ino != expected.inode
            or observed.st_size != expected.size
            or observed.st_mtime_ns != expected.mtime_ns
            or current != expected.payload
        ):
            raise SyncSafetyError(f"bundled toolkit module changed after preflight: {operation.destination}")
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{operation.destination.name}.",
        suffix=".tmp",
        dir=destination_dir,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(operation.payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, operation.mode)
        os.replace(temp_path, operation.destination)
        _fsync_directory(destination_dir)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def sync_skill(skill_dir: Path, modules: tuple[str, ...] = MODULES) -> None:
    operations = _build_operations([skill_dir], modules)
    for operation in operations:
        if operation.status != "current":
            _atomic_publish(operation)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync bundled asset_toolkit into skills")
    parser.add_argument("--skill-ids", nargs="+", default=None)
    parser.add_argument(
        "--modules",
        nargs="+",
        choices=MODULES,
        default=None,
        help="Sync only the named toolkit modules (default: all modules)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    modules = tuple(args.modules) if args.modules is not None else MODULES
    try:
        skill_dirs = _skill_dirs(args.skill_ids)
        # Build and validate the complete operation set before the first write.
        operations = _build_operations(skill_dirs, modules)
    except SyncSafetyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    mismatches = [operation for operation in operations if operation.status != "current"]
    if args.check or not args.apply:
        if mismatches:
            for operation in mismatches:
                skill_id = operation.destination.parents[2].name
                print(
                    f"{skill_id}: {operation.status} scripts/asset_toolkit/{operation.destination.name}",
                    file=sys.stderr,
                )
            return 1
        print(f"OK: {len(skill_dirs)} skills toolkit-synced ({len(modules)} modules each)")
        return 0

    try:
        for operation in mismatches:
            _atomic_publish(operation)
    except (OSError, SyncSafetyError) as exc:
        print(f"ERROR: toolkit sync failed: {exc}", file=sys.stderr)
        return 2
    print(f"OK: updated {len(mismatches)} toolkit modules across {len(skill_dirs)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
