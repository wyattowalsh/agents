"""Verify candidate Codex plugins against an immutable provenance lock."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
import tomllib
from pathlib import Path
from typing import Any

PLUGIN_CONTENT_DIGEST_ALGORITHM = "plugin-content-tree-v1"
PLUGIN_CONTENT_IGNORED_DIRS = (".git",)
PLUGIN_PROVENANCE_LOCK_VERSION = 1

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_RELATIVE_PART_RE = re.compile(r"^[A-Za-z0-9._@+-]+$")
_REQUIRED_ENTRY_FIELDS = frozenset({
    "plugin_id",
    "registry_id",
    "normalized_url",
    "resolved_version",
    "audited_source_commit_sha",
    "upstream_subpath",
    "upstream_git_tree_oid",
    "source_projection",
    "marketplace",
    "marketplace_path",
    "marketplace_snapshot_kind",
    "marketplace_commit_sha",
    "marketplace_git_subpath",
    "marketplace_git_tree_oid",
    "approved_content_sha256",
    "digest_algorithm",
    "ignored_dirs",
})
_TOP_LEVEL_FIELDS = frozenset({"version", "plugins"})


def canonical_json_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _safe_relative_path(value: str, *, allow_dot: bool = False) -> bool:
    if allow_dot and value == ".":
        return True
    candidate = Path(value)
    return (
        bool(value)
        and not candidate.is_absolute()
        and value == candidate.as_posix()
        and all(part not in {"", ".", ".."} and _SAFE_RELATIVE_PART_RE.fullmatch(part) for part in candidate.parts)
    )


def _digest_record(digest: Any, *parts: str | bytes) -> None:
    for part in parts:
        encoded = part if isinstance(part, bytes) else part.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)


def plugin_content_sha256(root: Path) -> str:
    """Hash a plugin tree without binding the digest to its absolute install path."""

    if root.is_symlink():
        raise ValueError(f"plugin provenance root must not be a symlink: {root}")
    try:
        root_metadata = root.lstat()
    except OSError as error:
        raise ValueError(f"plugin provenance root is unavailable: {root}") from error
    if not stat.S_ISDIR(root_metadata.st_mode):
        raise ValueError(f"plugin provenance root must be a directory: {root}")

    digest = hashlib.sha256()
    _digest_record(digest, PLUGIN_CONTENT_DIGEST_ALGORITHM, "root", "directory")

    def visit(directory: Path, relative: Path) -> None:
        try:
            children = sorted(os.scandir(directory), key=lambda item: os.fsencode(item.name))
        except OSError as error:
            raise ValueError(f"could not scan plugin provenance tree: {directory}") from error
        for child in children:
            if child.name in PLUGIN_CONTENT_IGNORED_DIRS and child.is_dir(follow_symlinks=False):
                continue
            child_relative = relative / child.name
            relative_text = child_relative.as_posix()
            try:
                metadata = child.stat(follow_symlinks=False)
            except OSError as error:
                raise ValueError(f"could not inspect plugin provenance path: {child.path}") from error
            mode = f"{stat.S_IMODE(metadata.st_mode):04o}"
            if stat.S_ISDIR(metadata.st_mode):
                _digest_record(digest, "directory", relative_text, mode)
                visit(Path(child.path), child_relative)
            elif stat.S_ISREG(metadata.st_mode):
                try:
                    content = Path(child.path).read_bytes()
                except OSError as error:
                    raise ValueError(f"could not read plugin provenance path: {child.path}") from error
                _digest_record(digest, "file", relative_text, mode, content)
            elif stat.S_ISLNK(metadata.st_mode):
                raise ValueError(f"plugin provenance tree contains a symlink: {child.path}")
            else:
                raise ValueError(f"plugin provenance tree contains a special file: {child.path}")

    visit(root, Path())
    return digest.hexdigest()


def _validate_entry(raw: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(_REQUIRED_ENTRY_FIELDS - set(raw))
    if missing:
        raise ValueError(f"plugin provenance lock entry omitted fields: {missing}")
    entry = dict(raw)
    for field in (
        "plugin_id",
        "registry_id",
        "normalized_url",
        "resolved_version",
        "marketplace",
    ):
        if not isinstance(entry[field], str) or not entry[field]:
            raise ValueError(f"plugin provenance lock {field} must be a nonempty string")
    if "@" not in entry["plugin_id"]:
        raise ValueError("plugin provenance lock plugin_id must include a marketplace")
    if set(entry) != _REQUIRED_ENTRY_FIELDS:
        raise ValueError(
            "plugin provenance lock entry fields drifted: "
            f"expected {sorted(_REQUIRED_ENTRY_FIELDS)}, found {sorted(entry)}"
        )
    if entry["plugin_id"].count("@") != 1:
        raise ValueError("plugin provenance lock plugin_id must contain exactly one marketplace separator")
    plugin_name, plugin_marketplace = entry["plugin_id"].split("@", 1)
    for label, value in (
        ("plugin name", plugin_name),
        ("plugin marketplace", plugin_marketplace),
        ("resolved version", entry["resolved_version"]),
    ):
        if not isinstance(value, str) or not _SAFE_RELATIVE_PART_RE.fullmatch(value) or value in {".", ".."}:
            raise ValueError(f"plugin provenance lock {label} must be a safe path component")
    if plugin_marketplace != entry["marketplace"]:
        raise ValueError("plugin provenance lock marketplace does not match plugin_id")
    if not str(entry["normalized_url"]).startswith("https://github.com/"):
        raise ValueError("plugin provenance lock normalized_url must be a GitHub URL")
    for field in ("audited_source_commit_sha", "marketplace_commit_sha"):
        if not isinstance(entry[field], str) or not _SHA1_RE.fullmatch(entry[field]):
            raise ValueError(f"plugin provenance lock {field} must be a lowercase 40-character SHA")
    for field in ("upstream_git_tree_oid", "marketplace_git_tree_oid"):
        if not isinstance(entry[field], str) or not _SHA1_RE.fullmatch(entry[field]):
            raise ValueError(f"plugin provenance lock {field} must be a lowercase Git tree OID")
    if not isinstance(entry["approved_content_sha256"], str) or not _SHA256_RE.fullmatch(
        entry["approved_content_sha256"]
    ):
        raise ValueError("plugin provenance lock approved_content_sha256 must be a lowercase SHA-256")
    if entry["digest_algorithm"] != PLUGIN_CONTENT_DIGEST_ALGORITHM:
        raise ValueError("plugin provenance lock uses an unsupported content digest algorithm")
    if entry["ignored_dirs"] != list(PLUGIN_CONTENT_IGNORED_DIRS):
        raise ValueError("plugin provenance lock uses an unsupported ignored-directory policy")
    for field in ("upstream_subpath", "marketplace_path", "marketplace_git_subpath"):
        if not isinstance(entry[field], str) or not _safe_relative_path(
            entry[field],
            allow_dot=field == "upstream_subpath",
        ):
            raise ValueError(f"plugin provenance lock {field} must be a safe relative path")
    if entry["marketplace_snapshot_kind"] not in {"git-checkout", "reviewed-local-projection"}:
        raise ValueError("plugin provenance lock marketplace_snapshot_kind is unsupported")
    projection = entry["source_projection"]
    if not isinstance(projection, dict) or set(projection) != {"mode", "paths"}:
        raise ValueError("plugin provenance lock source_projection must declare mode and paths")
    mode = projection["mode"]
    paths = projection["paths"]
    if mode not in {"all", "include", "exclude"}:
        raise ValueError("plugin provenance lock source_projection mode is unsupported")
    if not isinstance(paths, list) or paths != sorted(set(paths)):
        raise ValueError("plugin provenance lock source_projection paths must be sorted and unique")
    if not all(isinstance(value, str) and _safe_relative_path(value) for value in paths):
        raise ValueError("plugin provenance lock source_projection contains an unsafe path")
    if (mode == "all" and paths) or (mode != "all" and not paths):
        raise ValueError("plugin provenance lock source_projection paths do not match its mode")
    return entry


def load_plugin_provenance_lock(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("version") != PLUGIN_PROVENANCE_LOCK_VERSION:
        raise ValueError("candidate plugin provenance lock has an unsupported version")
    if set(payload) != _TOP_LEVEL_FIELDS:
        raise ValueError(
            "candidate plugin provenance lock fields drifted: "
            f"expected {sorted(_TOP_LEVEL_FIELDS)}, found {sorted(payload)}"
        )
    rows = payload.get("plugins")
    if not isinstance(rows, list) or not rows:
        raise ValueError("candidate plugin provenance lock must contain plugin rows")
    result: dict[str, dict[str, Any]] = {}
    for raw in rows:
        if not isinstance(raw, dict):
            raise ValueError("candidate plugin provenance lock rows must be objects")
        entry = _validate_entry(raw)
        plugin_id = str(entry["plugin_id"])
        if plugin_id in result:
            raise ValueError(f"duplicate candidate plugin provenance lock entry: {plugin_id}")
        result[plugin_id] = entry
    if list(result) != sorted(result):
        raise ValueError("candidate plugin provenance lock rows must be sorted by plugin_id")
    return result


def plugin_lock_entry_sha256(entry: dict[str, Any]) -> str:
    return canonical_json_sha256(_validate_entry(entry))


def verify_plugin_content(root: Path, entry: dict[str, Any], *, label: str) -> str:
    actual = plugin_content_sha256(root)
    expected = str(entry["approved_content_sha256"])
    if actual != expected:
        raise ValueError(f"{label} content does not match the immutable plugin provenance lock")
    return actual


def _git_executable() -> Path:
    for candidate in (Path("/usr/bin/git"), Path("/opt/homebrew/bin/git")):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise ValueError("an audited absolute Git executable is unavailable")


def _git_env() -> dict[str, str]:
    return {
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "HOME": str(Path.home()),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
    }


def _run_git(checkout: Path, *args: str, timeout: int = 10) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            str(_git_executable()),
            "-c",
            "core.hooksPath=/dev/null",
            "-C",
            str(checkout),
            *args,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_git_env(),
    )


def _run_git_bytes(checkout: Path, *args: str, timeout: int = 10) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [
            str(_git_executable()),
            "-c",
            "core.hooksPath=/dev/null",
            "-C",
            str(checkout),
            *args,
        ],
        check=False,
        capture_output=True,
        timeout=timeout,
        env=_git_env(),
    )


def verify_marketplace_checkout(source_root: Path, entry: dict[str, Any]) -> None:
    result = _run_git(source_root, "rev-parse", "--show-toplevel", "HEAD")
    lines = result.stdout.splitlines()
    if result.returncode != 0 or len(lines) != 2:
        raise ValueError("plugin marketplace source is not inside the locked Git checkout")
    checkout_root = Path(lines[0]).resolve(strict=True)
    checkout_head = lines[1].strip()
    if checkout_head != entry["marketplace_commit_sha"]:
        raise ValueError("plugin marketplace checkout commit does not match the provenance lock")
    actual_subpath = source_root.resolve(strict=True).relative_to(checkout_root).as_posix()
    if actual_subpath != entry["marketplace_git_subpath"]:
        raise ValueError("plugin marketplace checkout path does not match the provenance lock")
    tree_result = _run_git(
        checkout_root,
        "rev-parse",
        f"{entry['marketplace_commit_sha']}:{entry['marketplace_git_subpath']}",
    )
    if tree_result.returncode != 0 or tree_result.stdout.strip() != entry["marketplace_git_tree_oid"]:
        raise ValueError("plugin marketplace Git tree does not match the provenance lock")


def resolve_locked_marketplace_source(
    marketplace_root: Path,
    entry: dict[str, Any],
) -> Path:
    manifest_path = marketplace_root / ".agents" / "plugins" / "marketplace.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = payload.get("plugins") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("plugin marketplace manifest must contain plugin rows")
    plugin_name = str(entry["plugin_id"]).rsplit("@", 1)[0]
    matches = [row for row in rows if isinstance(row, dict) and row.get("name") == plugin_name]
    if len(matches) != 1:
        raise ValueError("plugin marketplace manifest did not resolve the locked plugin exactly once")
    source = matches[0].get("source")
    if not isinstance(source, dict) or source.get("source") != "local":
        raise ValueError("plugin marketplace manifest source is not local")
    relative = source.get("path")
    if not isinstance(relative, str) or not relative:
        raise ValueError("plugin marketplace manifest omitted its source path")
    normalized = Path(relative).as_posix().removeprefix("./")
    if normalized != entry["marketplace_path"]:
        raise ValueError("plugin marketplace manifest path does not match the provenance lock")
    lexical = marketplace_root / relative
    if not lexical.absolute().is_relative_to(marketplace_root.absolute()):
        raise ValueError("plugin marketplace manifest path escapes lexically")
    resolved = lexical.resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError("plugin marketplace source is not a directory")
    verify_marketplace_checkout(resolved, entry)
    verify_plugin_content(resolved, entry, label=f"marketplace source for {entry['plugin_id']}")
    return resolved


def plugin_cache_path(cache_root: Path, plugin_id: str, version: str) -> Path:
    if plugin_id.count("@") != 1:
        raise ValueError("plugin id must contain exactly one marketplace separator")
    name, marketplace = plugin_id.split("@", 1)
    for label, value in (("plugin name", name), ("plugin marketplace", marketplace), ("version", version)):
        if not _SAFE_RELATIVE_PART_RE.fullmatch(value) or value in {".", ".."}:
            raise ValueError(f"{label} must be a safe path component")
    resolved_cache = cache_root.expanduser().resolve(strict=True)
    candidate = resolved_cache / marketplace / name / version
    if not candidate.is_relative_to(resolved_cache):
        raise ValueError("plugin cache root escaped the managed Codex cache")
    return candidate


def codex_plugin_cache_root(cache_root: Path, entry: dict[str, Any]) -> Path:
    validated = _validate_entry(entry)
    return plugin_cache_path(
        cache_root,
        str(validated["plugin_id"]),
        str(validated["resolved_version"]),
    )


def codex_plugin_live_state(
    config_path: Path,
    cache_root: Path,
    entry: dict[str, Any],
) -> dict[str, Any]:
    validated = _validate_entry(entry)
    payload = tomllib.loads(config_path.read_text(encoding="utf-8"))
    plugins = payload.get("plugins")
    if not isinstance(plugins, dict):
        raise ValueError("Codex config must contain a plugin table")
    plugin_id = str(validated["plugin_id"])
    configuration = plugins.get(plugin_id)
    enabled = isinstance(configuration, dict) and configuration.get("enabled") is True
    root = codex_plugin_cache_root(cache_root, validated)
    installed = root.is_dir() and not root.is_symlink()
    return {
        "plugin_id": plugin_id,
        "version": str(validated["resolved_version"]),
        "enabled": enabled,
        "installed": installed,
        "installed_path": str(root),
    }


def _projection_includes(relative: Path, projection: dict[str, Any]) -> bool:
    mode = str(projection["mode"])
    paths = [Path(value) for value in projection["paths"]]
    if mode == "all":
        return True
    if mode == "include":
        return any(
            relative == selected or relative.is_relative_to(selected) or selected.is_relative_to(relative)
            for selected in paths
        )
    return not any(relative == selected or relative.is_relative_to(selected) for selected in paths)


def verify_upstream_projection(checkout_root: Path, entry: dict[str, Any]) -> str:
    validated = _validate_entry(entry)
    checkout_root = checkout_root.expanduser()
    if checkout_root.is_symlink():
        raise ValueError("upstream provenance checkout must be a real directory")
    checkout_root = checkout_root.resolve(strict=True)
    if not checkout_root.is_dir():
        raise ValueError("upstream provenance checkout must be a real directory")
    head = _run_git(checkout_root, "rev-parse", "--show-toplevel", "HEAD")
    lines = head.stdout.splitlines()
    if head.returncode != 0 or len(lines) != 2 or Path(lines[0]).resolve(strict=True) != checkout_root:
        raise ValueError("upstream provenance path is not the root of a Git checkout")
    if lines[1].strip() != validated["audited_source_commit_sha"]:
        raise ValueError("upstream provenance checkout HEAD does not match the audited source commit")
    tree_spec = (
        f"{validated['audited_source_commit_sha']}^{{tree}}"
        if validated["upstream_subpath"] == "."
        else f"{validated['audited_source_commit_sha']}:{validated['upstream_subpath']}"
    )
    tree_result = _run_git(checkout_root, "rev-parse", tree_spec)
    if tree_result.returncode != 0 or tree_result.stdout.strip() != validated["upstream_git_tree_oid"]:
        raise ValueError("upstream provenance Git tree does not match the lock")
    projection = validated["source_projection"]
    listing = _run_git_bytes(checkout_root, "ls-tree", "-r", "-z", tree_spec)
    if listing.returncode != 0:
        raise ValueError("could not enumerate the locked upstream Git tree")
    with tempfile.TemporaryDirectory(prefix="wagents-plugin-upstream-projection-") as raw:
        destination = Path(raw) / "plugin"
        destination.mkdir(mode=0o755)
        for record in listing.stdout.split(b"\0"):
            if not record:
                continue
            metadata, separator, raw_relative = record.partition(b"\t")
            fields = metadata.split()
            if not separator or len(fields) != 3:
                raise ValueError("upstream Git tree emitted an invalid record")
            raw_mode, object_type, raw_oid = fields
            try:
                relative = Path(raw_relative.decode("utf-8"))
                oid = raw_oid.decode("ascii")
            except UnicodeDecodeError as error:
                raise ValueError("upstream Git tree contains an unsupported path or object id") from error
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("upstream Git tree contains an unsafe path")
            if not _projection_includes(relative, projection):
                continue
            if object_type != b"blob" or raw_mode not in {b"100644", b"100755"}:
                raise ValueError(f"upstream plugin projection contains an unsupported Git object: {relative}")
            content = _run_git_bytes(checkout_root, "cat-file", "blob", oid)
            if content.returncode != 0:
                raise ValueError(f"could not read upstream Git blob: {relative}")
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
            target.write_bytes(content.stdout)
            target.chmod(0o755 if raw_mode == b"100755" else 0o644)
        return verify_plugin_content(
            destination,
            validated,
            label=f"upstream projection for {validated['plugin_id']}",
        )


def plugin_installed_package_origin(
    entry: dict[str, Any],
    *,
    source_content_sha256: str,
    installed_content_sha256: str,
) -> dict[str, Any]:
    origin = {
        "origin_kind": "codex-plugin-provenance-lock",
        "plugin_id": entry["plugin_id"],
        "registry_id": entry["registry_id"],
        "normalized_url": entry["normalized_url"],
        "marketplace": entry["marketplace"],
        "marketplace_path": entry["marketplace_path"],
        "marketplace_commit_sha": entry["marketplace_commit_sha"],
        "marketplace_git_tree_oid": entry["marketplace_git_tree_oid"],
        "audited_source_commit_sha": entry["audited_source_commit_sha"],
        "upstream_subpath": entry["upstream_subpath"],
        "upstream_git_tree_oid": entry["upstream_git_tree_oid"],
        "approved_content_sha256": entry["approved_content_sha256"],
        "source_content_sha256": source_content_sha256,
        "installed_content_sha256": installed_content_sha256,
        "digest_algorithm": entry["digest_algorithm"],
        "lock_entry_sha256": plugin_lock_entry_sha256(entry),
    }
    origin["origin_digest"] = canonical_json_sha256(origin)
    return origin
