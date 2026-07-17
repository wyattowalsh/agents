#!/usr/bin/env python3
"""Package skills into portable ZIP files for skill distribution.

Runs portability checks, generates a manifest.json, and creates a
<name>-v<version>.skill.zip bundle. JSON to stdout, warnings to stderr.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import stat
import sys
import tempfile
import unicodedata
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from _shared import (
    ABSOLUTE_PATH_RE,
    find_nonportable_body_operator_lines,
    find_nonportable_frontmatter_commands,
    format_body_operator_issues,
    format_frontmatter_command_issues,
    parse_frontmatter,
)

SCRIPT_DIR = Path(__file__).resolve().parent
# The canonical script lives directly under ``scripts/`` while portable copies
# live inside ``scripts/asset_toolkit/``.  In either layout, resolve the seven
# modules from the directory that actually owns the toolkit bundle.
ASSET_TOOLKIT_SRC = SCRIPT_DIR if SCRIPT_DIR.name == "asset_toolkit" else SCRIPT_DIR / "asset_toolkit"
PORTABLE_TOOLKIT_MODULES = frozenset({
    "__init__.py",
    "_shared.py",
    "common.py",
    "package.py",
    "validate_skill.py",
    "validate_evals.py",
    "validate_hooks.py",
})
WAGENTS_RE = re.compile(r"\bwagents\b", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_ARCHIVE_FILES = 2_048
MAX_ARCHIVE_DEPTH = 24
MAX_ARCHIVE_FILE_BYTES = 32 * 1024 * 1024
MAX_ARCHIVE_TOTAL_BYTES = 128 * 1024 * 1024
MAX_MANIFEST_NAME_BYTES = 64
MAX_MANIFEST_VERSION_BYTES = 128
MAX_MANIFEST_DESCRIPTION_BYTES = 1_024
MAX_MANIFEST_LICENSE_BYTES = 128
MAX_MANIFEST_AUTHOR_BYTES = 256
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)

WINDOWS_RESERVED_BASENAMES = frozenset({
    "AUX",
    "CON",
    "CONIN$",
    "CONOUT$",
    "NUL",
    "PRN",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
})
WINDOWS_FORBIDDEN_CHARACTERS = frozenset('<>:"|?*')

EXCLUDE_PATTERNS = {"*.pyc", "*.pyo", "*.tmp", "*.skill.zip", ".coverage*"}
EXCLUDE_DIRS = {
    "__pycache__",
    ".cache",
    ".eggs",
    ".git",
    ".hypothesis",
    ".ipynb_checkpoints",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".pytype",
    ".ruff_cache",
    ".tox",
    ".ty",
    ".venv",
    "build",
    "dist",
    "htmlcov",
    "node_modules",
    "venv",
}
EXCLUDE_EXTENSIONS = {".pyc", ".pyo", ".tmp"}
EXCLUDE_NAMES = {".DS_Store", "AGENTS.md", "coverage.xml", "manifest.json"}

# Regex: @ imports at the start of a line (repo-specific path assumptions)
AT_IMPORT_RE = re.compile(r"^@\S+", re.MULTILINE)

# Regex: packaged resource mentions in SKILL.md body, optionally prefixed with skills/<name>/
RESOURCE_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])((?:skills/[a-z0-9-]+/)?(?:references|scripts|templates|assets|reports)/[A-Za-z0-9_./-]*[A-Za-z0-9_-]\.[A-Za-z0-9_-]+)"
)


def _warn(msg: str) -> None:
    print(f"[package] {msg}", file=sys.stderr)


def _source_date_epoch() -> int | None:
    raw = os.environ.get("SOURCE_DATE_EPOCH")
    if raw is None:
        return None
    try:
        epoch = int(raw, 10)
    except ValueError as exc:
        raise PackageSafetyError("SOURCE_DATE_EPOCH must be a non-negative integer") from exc
    if epoch < 0:
        raise PackageSafetyError("SOURCE_DATE_EPOCH must be a non-negative integer")
    return epoch


def _now() -> str:
    epoch = _source_date_epoch()
    if epoch is None:
        return datetime.now(UTC).isoformat()
    try:
        return datetime.fromtimestamp(epoch, UTC).isoformat()
    except (OverflowError, OSError, ValueError) as exc:
        raise PackageSafetyError("SOURCE_DATE_EPOCH is outside the supported timestamp range") from exc


def _zip_timestamp() -> tuple[int, int, int, int, int, int]:
    epoch = _source_date_epoch()
    if epoch is None:
        return ZIP_TIMESTAMP
    # The ZIP timestamp format supports 1980-01-01 through 2107-12-31 and
    # stores seconds at two-second resolution.
    clamped = min(max(epoch, 315_532_800), 4_354_819_199)
    value = datetime.fromtimestamp(clamped, UTC)
    return (value.year, value.month, value.day, value.hour, value.minute, value.second // 2 * 2)


class PackageSafetyError(ValueError):
    """Raised when an input cannot be packaged without crossing a safety boundary."""


@dataclass(frozen=True)
class ArchiveMember:
    """A snapshotted regular file and its normalized archive-relative name."""

    source: Path
    trusted_root: Path
    archive_path: str
    device: int
    inode: int
    size: int
    mtime_ns: int


# ---------------------------------------------------------------------------
# File filtering
# ---------------------------------------------------------------------------


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
        raise PackageSafetyError(f"cannot inspect archive path for junctions {path}: {exc}") from exc


def _is_link_or_reparse_point(path: Path, observed: os.stat_result) -> bool:
    return stat.S_ISLNK(observed.st_mode) or _stat_is_reparse_point(observed) or _path_is_junction(path)


def _normalize_portable_segment(segment: str, *, label: str) -> str:
    normalized = unicodedata.normalize("NFC", segment)
    if not normalized or normalized in {".", ".."}:
        raise PackageSafetyError(f"invalid {label}: {segment!r}")
    if any(unicodedata.category(character) == "Cc" for character in normalized):
        raise PackageSafetyError(f"control character is forbidden in {label}: {segment!r}")
    if any(character in WINDOWS_FORBIDDEN_CHARACTERS for character in normalized):
        raise PackageSafetyError(f"Windows-forbidden character is present in {label}: {segment!r}")
    if normalized.endswith((" ", ".")):
        raise PackageSafetyError(f"trailing dot or space is forbidden in {label}: {segment!r}")
    basename = normalized.split(".", 1)[0].upper()
    if basename in WINDOWS_RESERVED_BASENAMES:
        raise PackageSafetyError(f"Windows-reserved name is forbidden in {label}: {segment!r}")
    return normalized


def _is_reports_file(path: Path) -> bool:
    return bool(path.parts) and path.parts[0] == "reports"


def _mentioned_resource_paths(skill_dir: Path, body: str) -> set[str]:
    mentioned: set[str] = set()
    skill_prefix = f"skills/{skill_dir.name}/"
    for match in RESOURCE_PATH_RE.finditer(body):
        raw_path = match.group(1).rstrip("`.,:;)]}")
        if raw_path.startswith(skill_prefix):
            raw_path = raw_path[len(skill_prefix) :]
        elif raw_path.startswith("skills/"):
            # Cross-skill repo tooling references are validation commands, not
            # resources that must be bundled inside the current skill archive.
            continue
        mentioned.add(raw_path)
    return mentioned


def _referenced_report_files(skill_dir: Path, body: str) -> set[Path]:
    return {
        Path(rel_path) for rel_path in _mentioned_resource_paths(skill_dir, body) if _is_reports_file(Path(rel_path))
    }


def _should_exclude(path: Path, referenced_report_files: set[Path] | None = None) -> bool:
    """Return True if the path should be excluded from the ZIP."""
    if path.name in EXCLUDE_NAMES:
        return True
    if path.suffix in EXCLUDE_EXTENSIONS:
        return True
    if any(fnmatch.fnmatchcase(path.name, pattern) for pattern in EXCLUDE_PATTERNS):
        return True
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return True
    if any(part.endswith(".egg-info") for part in path.parts):
        return True
    return _is_reports_file(path) and path not in (referenced_report_files or set())


def _should_prune_dir(path: Path) -> bool:
    """Return True if directory traversal should not descend into path."""
    return any(part in EXCLUDE_DIRS or part.endswith(".egg-info") for part in path.parts)


def _normalize_member_name(path: str | Path) -> str:
    """Return a safe, NFC-normalized POSIX ZIP member name."""
    raw = path.as_posix() if isinstance(path, Path) else path
    if not raw or "\\" in raw or "\x00" in raw:
        raise PackageSafetyError(f"unsafe archive member name: {raw!r}")
    if raw.startswith("/"):
        raise PackageSafetyError(f"absolute archive member path is forbidden: {raw!r}")
    raw_parts = raw.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise PackageSafetyError(f"archive path traversal is forbidden: {raw!r}")
    normalized = "/".join(_normalize_portable_segment(part, label="archive member segment") for part in raw_parts)
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise PackageSafetyError(f"archive path traversal is forbidden: {raw!r}")
    return pure.as_posix()


def _ensure_unique_member_names(names: list[str]) -> None:
    """Reject exact, Unicode-normalized, and case-insensitive member collisions."""
    normalized_seen: dict[str, str] = {}
    casefold_seen: dict[str, str] = {}
    for raw_name in names:
        normalized = _normalize_member_name(raw_name)
        if previous := normalized_seen.get(normalized):
            raise PackageSafetyError(f"duplicate normalized archive member names: {previous!r} and {raw_name!r}")
        normalized_seen[normalized] = raw_name
        folded = normalized.casefold()
        if previous := casefold_seen.get(folded):
            raise PackageSafetyError(f"case-insensitive archive member collision: {previous!r} and {raw_name!r}")
        casefold_seen[folded] = raw_name


def _assert_directory_no_follow(path: Path, *, label: str) -> None:
    try:
        path_stat = path.lstat()
    except OSError as exc:
        raise PackageSafetyError(f"cannot inspect {label} {path}: {exc}") from exc
    if _is_link_or_reparse_point(path, path_stat):
        raise PackageSafetyError(f"symbolic link, junction, or reparse point is forbidden for {label}: {path}")
    if not stat.S_ISDIR(path_stat.st_mode):
        raise PackageSafetyError(f"expected directory for {label}: {path}")


def _assert_no_symlink_ancestors(trusted_root: Path, source: Path) -> None:
    """Revalidate every archive-local parent without following symlinks."""
    try:
        relative = source.relative_to(trusted_root)
    except ValueError as exc:
        raise PackageSafetyError(f"archive source escapes trusted root: {source}") from exc

    _assert_directory_no_follow(trusted_root, label="trusted root")
    current = trusted_root
    for part in relative.parts[:-1]:
        current = current / part
        _assert_directory_no_follow(current, label="archive parent")


def _snapshot_regular_file(source: Path, trusted_root: Path, archive_path: str | Path) -> ArchiveMember:
    """Capture immutable identity fields for a regular, non-linked input file."""
    normalized = _normalize_member_name(archive_path)
    if len(PurePosixPath(normalized).parts) > MAX_ARCHIVE_DEPTH:
        raise PackageSafetyError(f"archive depth limit exceeded for {normalized!r}: maximum is {MAX_ARCHIVE_DEPTH}")
    _assert_no_symlink_ancestors(trusted_root, source)
    try:
        source_stat = source.lstat()
    except OSError as exc:
        raise PackageSafetyError(f"cannot inspect archive input {source}: {exc}") from exc
    if _is_link_or_reparse_point(source, source_stat):
        raise PackageSafetyError(
            f"symbolic link, junction, or reparse point is forbidden in skill package: {normalized}"
        )
    if not stat.S_ISREG(source_stat.st_mode):
        raise PackageSafetyError(f"non-regular file is forbidden in skill package: {normalized}")
    if source_stat.st_nlink > 1:
        raise PackageSafetyError(
            f"hard-linked file is forbidden in skill package: {normalized} has {source_stat.st_nlink} links"
        )
    if source_stat.st_size > MAX_ARCHIVE_FILE_BYTES:
        raise PackageSafetyError(
            f"per-file byte limit exceeded for {normalized!r}: {source_stat.st_size} > {MAX_ARCHIVE_FILE_BYTES}"
        )
    return ArchiveMember(
        source=source,
        trusted_root=trusted_root,
        archive_path=normalized,
        device=source_stat.st_dev,
        inode=source_stat.st_ino,
        size=source_stat.st_size,
        mtime_ns=source_stat.st_mtime_ns,
    )


def _validate_archive_members(
    members: list[ArchiveMember],
    *,
    generated_file_count: int = 0,
    generated_bytes: int = 0,
) -> None:
    file_count = len(members) + generated_file_count
    if file_count > MAX_ARCHIVE_FILES:
        raise PackageSafetyError(f"archive file-count limit exceeded: {file_count} > {MAX_ARCHIVE_FILES}")
    _ensure_unique_member_names([member.archive_path for member in members])
    total_bytes = sum(member.size for member in members) + generated_bytes
    if total_bytes > MAX_ARCHIVE_TOTAL_BYTES:
        raise PackageSafetyError(f"archive total byte limit exceeded: {total_bytes} > {MAX_ARCHIVE_TOTAL_BYTES}")


def _collect_files(
    skill_dir: Path,
    referenced_report_files: set[Path] | None = None,
) -> tuple[list[ArchiveMember], list[Path]]:
    """Collect non-excluded files from the skill directory.

    Returns snapshotted included members and excluded paths relative to skill_dir.
    """
    included: list[ArchiveMember] = []
    excluded: list[Path] = []
    included_bytes = 0

    def walk(directory: Path) -> None:
        nonlocal included_bytes
        try:
            children = sorted(directory.iterdir(), key=lambda item: unicodedata.normalize("NFC", item.name))
        except OSError as exc:
            raise PackageSafetyError(f"cannot enumerate skill directory {directory}: {exc}") from exc
        for path in children:
            rel = path.relative_to(skill_dir)
            if _should_prune_dir(rel):
                excluded.append(rel)
                continue
            try:
                path_stat = path.lstat()
            except OSError as exc:
                raise PackageSafetyError(f"cannot inspect skill entry {rel.as_posix()}: {exc}") from exc
            if _is_link_or_reparse_point(path, path_stat):
                raise PackageSafetyError(
                    f"symbolic link, junction, or reparse point is forbidden in skill package: {rel.as_posix()}"
                )
            if stat.S_ISDIR(path_stat.st_mode):
                if len(rel.parts) > MAX_ARCHIVE_DEPTH:
                    raise PackageSafetyError(
                        f"archive depth limit exceeded for {rel.as_posix()!r}: maximum is {MAX_ARCHIVE_DEPTH}"
                    )
                walk(path)
                continue
            if _should_exclude(rel, referenced_report_files=referenced_report_files):
                excluded.append(rel)
                continue
            if not stat.S_ISREG(path_stat.st_mode):
                raise PackageSafetyError(f"non-regular file is forbidden in skill package: {rel.as_posix()}")
            member = _snapshot_regular_file(path, skill_dir, rel)
            included.append(member)
            if len(included) > MAX_ARCHIVE_FILES:
                raise PackageSafetyError(f"archive file-count limit exceeded: {len(included)} > {MAX_ARCHIVE_FILES}")
            included_bytes += member.size
            if included_bytes > MAX_ARCHIVE_TOTAL_BYTES:
                raise PackageSafetyError(
                    f"archive total byte limit exceeded: {included_bytes} > {MAX_ARCHIVE_TOTAL_BYTES}"
                )

    walk(skill_dir)

    return included, excluded


# ---------------------------------------------------------------------------
# Portability checks
# ---------------------------------------------------------------------------


def check_frontmatter_fields(fm: dict) -> list[dict]:
    """Check cross-platform frontmatter fields are populated."""
    checks = []
    meta = fm.get("metadata", {}) if isinstance(fm.get("metadata"), dict) else {}

    license_val = fm.get("license", "")
    checks.append({
        "check": "frontmatter_license",
        "passed": bool(license_val),
        "details": str(license_val) if license_val else "Missing license field",
    })

    author_val = meta.get("author", "")
    checks.append({
        "check": "frontmatter_author",
        "passed": bool(author_val),
        "details": str(author_val) if author_val else "Missing metadata.author field",
    })

    version_val = meta.get("version", "")
    checks.append({
        "check": "frontmatter_version",
        "passed": bool(version_val),
        "details": str(version_val) if version_val else "Missing metadata.version field",
    })

    return checks


def check_no_absolute_paths(body: str) -> dict:
    """Check for absolute filesystem paths in the body."""
    matches = []
    for i, line in enumerate(body.splitlines(), 1):
        for m in ABSOLUTE_PATH_RE.finditer(line):
            matches.append(f"line {i}: {m.group(0)}")
    return {
        "check": "no_absolute_paths",
        "passed": len(matches) == 0,
        "details": "; ".join(matches[:5]) if matches else "No absolute paths found",
    }


def check_referenced_files(skill_dir: Path, body: str) -> dict:
    """Check that referenced packaged resources in the body exist on disk."""
    mentioned = _mentioned_resource_paths(skill_dir, body)

    missing = []
    for rel_path in sorted(mentioned):
        if not (skill_dir / rel_path).is_file():
            missing.append(rel_path)
    if not mentioned:
        return {
            "check": "referenced_files_exist",
            "passed": True,
            "details": "No packaged resource mentions found in body",
        }
    return {
        "check": "referenced_files_exist",
        "passed": len(missing) == 0,
        "details": (
            f"Missing: {', '.join(missing)}" if missing else f"All {len(mentioned)} packaged resource paths resolve"
        ),
    }


def check_frontmatter_commands_portable(fm: dict) -> dict:
    """Check executable frontmatter commands for repo-root path assumptions."""
    issues = find_nonportable_frontmatter_commands(fm)
    return {
        "check": "frontmatter_commands_portable",
        "passed": len(issues) == 0,
        "details": format_frontmatter_command_issues(issues),
    }


def check_body_operator_paths_portable(body: str) -> dict:
    """Check body prose for repo-root skill script path assumptions."""
    issues = find_nonportable_body_operator_lines(body)
    return {
        "check": "body_operator_paths_portable",
        "passed": len(issues) == 0,
        "details": format_body_operator_issues(issues),
    }


def check_no_wagents_reference(body: str) -> dict:
    """Check for wagents CLI references in skill body (outside code fences)."""
    matches = []
    in_code_block = False
    for i, line in enumerate(body.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if WAGENTS_RE.search(line):
            matches.append(f"line {i}: {line.strip()}")
    return {
        "check": "no_wagents_reference",
        "passed": len(matches) == 0,
        "details": "; ".join(matches[:5]) if matches else "No wagents references found",
    }


def check_no_at_imports(body: str) -> dict:
    """Check for @ imports or repo-specific path assumptions.

    Skips lines inside fenced code blocks (``` ... ```) since those
    commonly contain Python decorators like @mcp.tool.
    """
    matches = []
    in_code_block = False
    for i, line in enumerate(body.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if AT_IMPORT_RE.match(line):
            matches.append(f"line {i}: {line.strip()}")
    return {
        "check": "no_at_imports",
        "passed": len(matches) == 0,
        "details": "; ".join(matches[:5]) if matches else "No @ imports found",
    }


def check_name_directory_match(fm: dict, dir_name: str) -> dict:
    """Check that frontmatter name matches the directory name."""
    fm_name = fm.get("name", "")
    return {
        "check": "name_directory_match",
        "passed": fm_name == dir_name,
        "details": (
            f"OK ({fm_name})" if fm_name == dir_name else f"Mismatch: frontmatter '{fm_name}' != directory '{dir_name}'"
        ),
    }


def check_required_fields(fm: dict) -> list[dict]:
    """Check that required frontmatter fields (name, description) are present."""
    checks = []
    for field in ("name", "description"):
        val = fm.get(field, "")
        checks.append({
            "check": f"required_{field}",
            "passed": bool(val),
            "details": f"OK ({val[:60]})" if val else f"Missing required field: {field}",
        })
    return checks


def run_portability_checks(skill_dir: Path, fm: dict, body: str) -> list[dict]:
    """Run all portability checks and return results."""
    checks: list[dict] = []
    checks.extend(check_required_fields(fm))
    checks.extend(check_frontmatter_fields(fm))
    checks.append(check_frontmatter_commands_portable(fm))
    checks.append(check_no_absolute_paths(body))
    checks.append(check_referenced_files(skill_dir, body))
    checks.append(check_body_operator_paths_portable(body))
    checks.append(check_no_wagents_reference(body))
    checks.append(check_no_at_imports(body))
    checks.append(check_name_directory_match(fm, skill_dir.name))
    return checks


# ---------------------------------------------------------------------------
# Manifest generation
# ---------------------------------------------------------------------------


def _bounded_manifest_string(value: object, *, label: str, max_bytes: int) -> str:
    if not isinstance(value, str):
        raise PackageSafetyError(f"manifest field {label} must be a string")
    normalized = unicodedata.normalize("NFC", value)
    size = len(normalized.encode("utf-8"))
    if size > max_bytes:
        raise PackageSafetyError(f"manifest field {label} exceeds its byte limit: {size} > {max_bytes}")
    return normalized


def _validated_manifest_metadata(fm: dict, *, fallback_name: str) -> dict[str, str]:
    metadata = fm.get("metadata", {})
    if not isinstance(metadata, dict):
        raise PackageSafetyError("frontmatter metadata must be an object")
    name = _bounded_manifest_string(
        fm.get("name", fallback_name),
        label="name",
        max_bytes=MAX_MANIFEST_NAME_BYTES,
    )
    version = _bounded_manifest_string(
        metadata.get("version", "0.0.0"),
        label="version",
        max_bytes=MAX_MANIFEST_VERSION_BYTES,
    )
    return {
        "name": _validate_archive_component(name, label="skill name"),
        "version": _validate_archive_component(version, label="skill version"),
        "description": _bounded_manifest_string(
            fm.get("description", ""),
            label="description",
            max_bytes=MAX_MANIFEST_DESCRIPTION_BYTES,
        ),
        "license": _bounded_manifest_string(
            fm.get("license", ""),
            label="license",
            max_bytes=MAX_MANIFEST_LICENSE_BYTES,
        ),
        "author": _bounded_manifest_string(
            metadata.get("author", ""),
            label="author",
            max_bytes=MAX_MANIFEST_AUTHOR_BYTES,
        ),
    }


def generate_manifest(
    fm: dict,
    files: list[ArchiveMember],
    *,
    fallback_name: str = "unknown",
) -> dict[str, object]:
    """Generate a validated manifest.json dict for the ZIP bundle."""
    metadata = _validated_manifest_metadata(fm, fallback_name=fallback_name)
    return {
        **metadata,
        "files": sorted(file.archive_path for file in files),
        "created_at": _now(),
        "packaged_by": "package.py",
    }


def _encode_manifest(manifest: dict[str, object]) -> bytes:
    try:
        return (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise PackageSafetyError(f"manifest cannot be encoded as UTF-8 JSON: {exc}") from exc


def _existing_toolkit_paths(included: list[ArchiveMember]) -> set[str]:
    prefix = "scripts/asset_toolkit/"
    return {member.archive_path.removeprefix(prefix) for member in included if member.archive_path.startswith(prefix)}


def _validate_existing_toolkit(included: list[ArchiveMember]) -> bool:
    existing = _existing_toolkit_paths(included)
    if not existing:
        return False
    expected = set(PORTABLE_TOOLKIT_MODULES)
    if existing != expected:
        missing = sorted(expected - existing)
        unexpected = sorted(existing - expected)
        details: list[str] = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected: {', '.join(unexpected)}")
        raise PackageSafetyError(
            "existing scripts/asset_toolkit must contain exactly the seven portable modules ("
            + "; ".join(details)
            + ")"
        )
    return True


# ---------------------------------------------------------------------------
# ZIP creation
# ---------------------------------------------------------------------------


def _asset_toolkit_files(included: list[ArchiveMember]) -> list[ArchiveMember]:
    """Return canonical portable toolkit members when the skill has no local bundle."""
    if _validate_existing_toolkit(included):
        return []
    _assert_directory_no_follow(ASSET_TOOLKIT_SRC, label="vendored toolkit root")
    members: list[ArchiveMember] = []
    for module_name in sorted(PORTABLE_TOOLKIT_MODULES):
        src = ASSET_TOOLKIT_SRC / module_name
        try:
            src.lstat()
        except FileNotFoundError as exc:
            raise PackageSafetyError(f"missing vendored toolkit module: {src}") from exc
        except OSError as exc:
            raise PackageSafetyError(f"cannot inspect vendored toolkit module {src}: {exc}") from exc
        archive_path = Path("scripts") / "asset_toolkit" / module_name
        members.append(_snapshot_regular_file(src, ASSET_TOOLKIT_SRC, archive_path))
    return members


def _validate_archive_component(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise PackageSafetyError(f"{label} must be a string")
    raw = unicodedata.normalize("NFC", value)
    if not raw or raw in {".", ".."} or "/" in raw or "\\" in raw or "\x00" in raw:
        raise PackageSafetyError(f"unsafe {label} for archive publication: {raw!r}")
    return _normalize_portable_segment(raw, label=label)


def _stat_matches_snapshot(member: ArchiveMember, observed: os.stat_result) -> bool:
    return (
        stat.S_ISREG(observed.st_mode)
        and not _stat_is_reparse_point(observed)
        and observed.st_nlink == 1
        and observed.st_dev == member.device
        and observed.st_ino == member.inode
        and observed.st_size == member.size
        and observed.st_mtime_ns == member.mtime_ns
    )


def _read_regular_file_no_follow(member: ArchiveMember) -> bytes:
    """Read a snapshotted member while rejecting link swaps and mutations."""
    _assert_no_symlink_ancestors(member.trusted_root, member.source)
    try:
        before = member.source.lstat()
    except OSError as exc:
        raise PackageSafetyError(f"cannot revalidate archive input {member.archive_path}: {exc}") from exc
    if not _stat_matches_snapshot(member, before):
        raise PackageSafetyError(f"archive input changed after collection: {member.archive_path}")

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(member.source, flags)
    except OSError as exc:
        raise PackageSafetyError(
            f"cannot open archive input without following links: {member.archive_path}: {exc}"
        ) from exc

    try:
        opened = os.fstat(descriptor)
        if not _stat_matches_snapshot(member, opened):
            raise PackageSafetyError(f"archive input changed while opening: {member.archive_path}")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            payload = handle.read(member.size + 1)
        if len(payload) != member.size:
            raise PackageSafetyError(f"archive input changed while reading: {member.archive_path}")
        after = os.fstat(descriptor)
        if not _stat_matches_snapshot(member, after):
            raise PackageSafetyError(f"archive input changed while reading: {member.archive_path}")
        return payload
    finally:
        os.close(descriptor)


def _zip_info(filename: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(filename, date_time=_zip_timestamp())
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    return info


def _write_zip(path: Path, archive_root: str, files: list[ArchiveMember], manifest_json: bytes) -> None:
    entries = [(f"{archive_root}/{member.archive_path}", _read_regular_file_no_follow(member)) for member in files]
    entries.append((f"{archive_root}/manifest.json", manifest_json))
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for filename, payload in sorted(entries, key=lambda entry: entry[0]):
            archive.writestr(_zip_info(filename), payload)


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _fsync_directory(path: Path) -> None:
    """Persist a directory entry update where directory fsync is supported."""
    if os.name == "nt":
        return
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write_text(path: Path, content: str) -> None:
    """Publish a UTF-8 text artifact through a sibling temporary file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, 0o644)
        os.replace(temp_path, path)
        _fsync_directory(path.parent)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def create_zip(
    skill_dir: Path,
    output_dir: Path,
    files: list[ArchiveMember],
    manifest: dict,
    manifest_json: bytes | None = None,
) -> tuple[Path, list[str]]:
    """Create the .skill.zip bundle and return (path, errors)."""
    del skill_dir  # Member records retain their trusted source roots.
    name = _validate_archive_component(manifest["name"], label="skill name")
    version = _validate_archive_component(manifest["version"], label="skill version")
    manifest_payload = manifest_json if manifest_json is not None else _encode_manifest(manifest)
    zip_name = f"{name}-v{version}.skill.zip"
    zip_path = output_dir / zip_name

    output_dir.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{zip_name}.", suffix=".tmp", dir=output_dir)
    os.close(descriptor)
    temp_path = Path(temp_name)
    try:
        _write_zip(temp_path, name, files, manifest_payload)
        os.chmod(temp_path, 0o644)
        _fsync_file(temp_path)
        os.replace(temp_path, zip_path)
        _fsync_directory(output_dir)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    return zip_path, []


# ---------------------------------------------------------------------------
# Package a single skill
# ---------------------------------------------------------------------------


def package_skill(skill_dir: Path, output_dir: Path, dry_run: bool = False, force: bool = False) -> dict:
    """Package a single skill and return a result dict."""
    skill_dir = Path(os.path.abspath(skill_dir))
    skill_md = skill_dir / "SKILL.md"

    result: dict = {
        "skill": skill_dir.name,
        "description": "",
        "version": "0.0.0",
        "output_path": None,
        "files_included": [],
        "files_excluded": [],
        "portability_checks": [],
        "portable": True,
        "blocked": False,
        "warnings": [],
        "errors": [],
    }

    if not skill_dir.exists():
        result["errors"].append(f"SKILL.md not found in {skill_dir}")
        return result

    try:
        _assert_directory_no_follow(skill_dir, label="skill root")
        skill_member = _snapshot_regular_file(skill_md, skill_dir, "SKILL.md")
        content = _read_regular_file_no_follow(skill_member).decode("utf-8", errors="replace")
    except PackageSafetyError as exc:
        result["blocked"] = True
        result["errors"].append(str(exc))
        return result

    fm, body = parse_frontmatter(content)

    try:
        manifest_metadata = _validated_manifest_metadata(fm, fallback_name=skill_dir.name)
    except PackageSafetyError as exc:
        result["blocked"] = True
        result["errors"].append(str(exc))
        return result
    archive_name = manifest_metadata["name"]
    archive_version = manifest_metadata["version"]
    result["version"] = archive_version
    result["description"] = manifest_metadata["description"]
    result["output_path"] = str(output_dir / f"{archive_name}-v{archive_version}.skill.zip")

    # Portability checks
    checks = run_portability_checks(skill_dir, fm, body)
    result["portability_checks"] = checks

    failed = [c for c in checks if not c["passed"]]
    result["portable"] = not failed
    for c in failed:
        result["warnings"].append(f"{c['check']}: {c['details']}")

    # Collect files
    referenced_report_files = _referenced_report_files(skill_dir, body)
    try:
        source_members, excluded = _collect_files(
            skill_dir,
            referenced_report_files=referenced_report_files,
        )
        included = [*source_members, *_asset_toolkit_files(source_members)]
        manifest = generate_manifest(fm, included, fallback_name=skill_dir.name)
        manifest_json = _encode_manifest(manifest)
        _validate_archive_members(
            included,
            generated_file_count=1,
            generated_bytes=len(manifest_json),
        )
    except PackageSafetyError as exc:
        result["blocked"] = True
        result["errors"].append(str(exc))
        return result
    result["files_included"] = sorted(member.archive_path for member in included)
    result["files_excluded"] = sorted(_normalize_member_name(path) for path in excluded)

    if failed and not force:
        result["blocked"] = True
        if not dry_run:
            result["errors"].append("Packaging blocked by portability failures. Re-run with --force to override.")
        return result

    if dry_run:
        if failed and force:
            result["warnings"].append("Portability failures overridden with --force during dry run")
        return result

    try:
        zip_path, zip_errors = create_zip(
            skill_dir,
            output_dir,
            included,
            manifest,
            manifest_json,
        )
    except (PackageSafetyError, OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        result["blocked"] = True
        result["errors"].append(str(exc))
        return result
    result["output_path"] = str(zip_path)
    result["errors"].extend(zip_errors)
    if failed and force:
        result["warnings"].append("Portability failures overridden with --force")

    return result


# ---------------------------------------------------------------------------
# Package all skills
# ---------------------------------------------------------------------------


def package_all(skills_dir: Path, output_dir: Path, dry_run: bool = False, force: bool = False) -> dict:
    """Package all skills under skills_dir and return a summary dict."""
    skills_dir = skills_dir.resolve()
    results: list[dict] = []

    if not skills_dir.is_dir():
        _warn(f"Skills directory not found: {skills_dir}")
        return {"skills": [], "created_at": _now(), "errors": ["Skills directory not found"]}

    for d in sorted(skills_dir.iterdir()):
        if d.is_dir() and (d / "SKILL.md").is_file():
            result = package_skill(d, output_dir, dry_run=dry_run, force=force)
            results.append(result)

    # Generate top-level manifest (unless dry-run)
    top_manifest = {
        "skills": [
            {
                "name": r["skill"],
                "version": r["version"],
                "description": r.get("description", ""),
                "zip": (
                    Path(r["output_path"]).name
                    if (not dry_run and not r.get("blocked") and r.get("output_path"))
                    else None
                ),
            }
            for r in results
        ],
        "created_at": _now(),
    }

    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / "manifest.json"
        _atomic_write_text(manifest_path, json.dumps(top_manifest, indent=2) + "\n")

    return {"results": results, "manifest": top_manifest}


# ---------------------------------------------------------------------------
# Table formatters
# ---------------------------------------------------------------------------


def _format_human_path(path_value: str) -> str:
    """Render absolute paths relative to cwd when possible for human output."""
    try:
        path = Path(path_value)
        if path.is_absolute():
            return str(path.resolve().relative_to(Path.cwd().resolve()))
    except (OSError, ValueError):
        pass
    return path_value


def _format_excluded_path(path_value: str) -> str:
    path = Path(path_value)
    if path.name in EXCLUDE_DIRS:
        return f"{path_value}/"
    return path_value


def format_table(result: dict) -> str:
    """Format a single skill package result as a human-readable table."""
    out = [f"Package: {result['skill']}", "=" * 40]
    out.append(f"Version: {result['version']}")
    if result["output_path"]:
        out.append(f"Output:  {_format_human_path(result['output_path'])}")
    out.append("")

    out.append(f"{'Check':<28} {'Result':>6}  Details")
    out.append("\u2500" * 70)
    for c in result.get("portability_checks", []):
        status = "PASS" if c["passed"] else "FAIL"
        out.append(f"{c['check']:<28} {status:>6}  {c['details']}")

    out.append("")
    out.append(f"Files included: {len(result.get('files_included', []))}")
    excluded_files = result.get("files_excluded", [])
    out.append(f"Files excluded: {len(excluded_files)}")
    if excluded_files:
        out.append("files_excluded:")
        for file_path in excluded_files:
            out.append(f"  - {_format_excluded_path(file_path)}")
    out.append(f"Portable: {'yes' if result.get('portable', True) else 'no'}")
    if result.get("blocked"):
        out.append("Blocked:  portability failures (use --force to override)")

    if result.get("warnings"):
        out.append("")
        out.append("Warnings:")
        for w in result["warnings"]:
            out.append(f"  - {w}")
    if result.get("errors"):
        out.append("")
        out.append("Errors:")
        for e in result["errors"]:
            out.append(f"  - {e}")

    all_passed = all(c["passed"] for c in result.get("portability_checks", []))
    out.append("")
    out.append(f"Overall: {'PASS' if all_passed and not result.get('errors') else 'FAIL'}")
    return "\n".join(out)


def format_all_table(data: dict) -> str:
    """Format all-skills package results as a summary table."""
    results = data.get("results", [])
    out = ["Skill Package Report", "=" * 20, ""]

    hdr = f"{'Skill':<22} {'Version':>8}  {'Files':>5}  {'Checks':>8}  {'Status':>6}"
    out.append(hdr)
    out.append("\u2500" * len(hdr))

    for r in results:
        checks = r.get("portability_checks", [])
        passed = sum(1 for c in checks if c["passed"])
        total = len(checks)
        has_errors = bool(r.get("errors"))
        all_ok = passed == total and not has_errors
        fc = len(r.get("files_included", []))
        out.append(
            f"{r['skill']:<22} {r['version']:>8}  {fc:>5}  {passed}/{total:>3}  {'PASS' if all_ok else 'FAIL':>6}"
        )

    out.append("")
    out.append(f"Total skills: {len(results)}")
    pass_count = sum(
        1 for r in results if all(c["passed"] for c in r.get("portability_checks", [])) and not r.get("errors")
    )
    out.append(f"Passing: {pass_count}/{len(results)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Package skills into portable ZIP files")
    parser.add_argument("path", nargs="?", help="Path to skill directory")
    parser.add_argument("--all", action="store_true", help="Package all skills under skills/")
    parser.add_argument("--output", "-o", default=None, help="Output directory (default: dist/)")
    parser.add_argument("--dry-run", action="store_true", help="Run portability checks only, do not create ZIP")
    parser.add_argument("--force", action="store_true", help="Override portability failures and package anyway")
    parser.add_argument("--format", choices=["json", "table"], default="json", dest="output_format")
    args = parser.parse_args()

    if not args.path and not args.all:
        parser.error("Provide a skill path or use --all")

    if args.path and args.all:
        parser.error("Cannot use both a path and --all; choose one")

    # Resolve output directory
    if args.output:
        output_dir = Path(args.output).resolve()
    else:
        # Default: dist/ relative to repo root (two levels up from this script)
        script_dir = Path(__file__).resolve().parent
        repo_root = script_dir.parent.parent.parent
        output_dir = repo_root / "dist"

    if args.all:
        script_dir = Path(__file__).resolve().parent
        skills_dir = script_dir.parent.parent  # skills/skill-creator/scripts -> skills/
        if not skills_dir.is_dir():
            skills_dir = Path.cwd() / "skills"
        data = package_all(skills_dir, output_dir, dry_run=args.dry_run, force=args.force)
        if args.output_format == "table":
            print(format_all_table(data))
        else:
            json.dump(data, sys.stdout, indent=2)
            sys.stdout.write("\n")
        if any(r.get("blocked") or r.get("errors") for r in data.get("results", [])):
            sys.exit(1)
    else:
        result = package_skill(Path(args.path), output_dir, dry_run=args.dry_run, force=args.force)
        if args.output_format == "table":
            print(format_table(result))
        else:
            json.dump(result, sys.stdout, indent=2)
            sys.stdout.write("\n")
        if result.get("blocked") or result.get("errors"):
            sys.exit(1)


if __name__ == "__main__":
    main()
