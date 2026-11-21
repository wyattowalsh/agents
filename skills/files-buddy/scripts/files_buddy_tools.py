"""Versioned observation adapters; no adapter grants permission to mutate files."""

from __future__ import annotations

import json
import math
import os
import re
import selectors
import shutil
import signal
import string
import subprocess
import time
from contextlib import suppress
from pathlib import Path
from typing import Any, Literal, cast, overload

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "assets" / "tool-registry.json"
MAX_OUTPUT_BYTES = 8 * 1024 * 1024
MAX_ROWS = 10_000
SCAN_STATES = {"complete", "partial", "unavailable"}


class ToolError(ValueError):
    """An unsupported capability or invalid observation."""


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ToolError(f"{label} must be an object")
    return cast("dict[str, Any]", value)


def _array(value: object, label: str) -> list[Any]:
    if not isinstance(value, list) or len(value) > MAX_ROWS:
        raise ToolError(f"{label} must be an array of at most {MAX_ROWS} rows")
    return value


def _string(value: object, label: str, *, empty: bool = False) -> str:
    if not isinstance(value, str) or (not value and not empty) or "\0" in value:
        raise ToolError(f"{label} must be a {'possibly empty ' if empty else ''}string without NUL")
    return value


@overload
def _integer(value: object, label: str, *, nullable: Literal[False] = False) -> int: ...


@overload
def _integer(value: object, label: str, *, nullable: Literal[True]) -> int | None: ...


def _integer(value: object, label: str, *, nullable: bool = False) -> int | None:
    if value is None and nullable:
        return None
    if type(value) is not int or value < 0:
        raise ToolError(f"{label} must be a nonnegative integer")
    return value


def parse_json(raw: str) -> Any:
    """Reject ambiguous keys, non-finite numbers, oversized and recursive input."""
    if len(raw.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise ToolError("Observation JSON exceeds its byte budget")

    def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ToolError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise ToolError(f"Non-finite JSON value: {value}")

    def finite_float(value: str) -> float:
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ToolError("Non-finite JSON number")
        return parsed

    try:
        return json.loads(raw, object_pairs_hook=unique_pairs, parse_constant=reject_constant, parse_float=finite_float)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ToolError("Invalid observation JSON") from exc


def _boolean(value: object, label: str) -> bool:
    if type(value) is not bool:
        raise ToolError(f"{label} must be a boolean")
    return value


def load_registry() -> dict[str, Any]:
    registry = _object(json.loads(REGISTRY_PATH.read_text()), "registry")
    if registry.get("schema_version") != "1.0":
        raise ToolError("Unsupported tool registry version")
    return registry


def capability(tool: str, operation: str, version: str) -> dict[str, Any]:
    registry = load_registry()
    tool_record = registry["tools"].get(tool)
    if tool_record is None:
        raise ToolError(f"Unknown tool: {tool}")
    version = version.removeprefix("v").removeprefix("V")
    if version not in tool_record["fixture_versions"]:
        raise ToolError(f"Unqualified {tool} version {version}; import manually or add a versioned fixture")
    operation_record = tool_record["operations"].get(operation)
    if operation_record is None:
        raise ToolError(f"Unsupported observation: {tool} {operation}; mutation commands are not adapters")
    return {**tool_record, **operation_record, "version": version, "tool": tool, "operation": operation}


def tool_inventory() -> dict[str, Any]:
    """Discover executables without invoking them or installing anything."""
    registry = load_registry()
    rows = []
    for name, record in registry["tools"].items():
        rows.append(
            {
                "tool": name,
                "executable": shutil.which(record["executable"]),
                "observed_version": None,
                "fixture_versions": record["fixture_versions"],
                "operations": record["operations"],
                "source": record["source"],
                "license": record["license"],
            }
        )
    return {"tools": rows, "notes": ["Discovery does not execute --version or prove native compatibility."]}


def parse_observation(tool: str, operation: str, version: str, data: object) -> dict[str, Any]:
    """Validate a tagged format and retain unknown evidence instead of guessing."""
    spec = capability(tool, operation, version)
    parsers = {
        ("mole", "analyze"): _mole_analyze,
        ("mole", "status"): _mole_status,
        ("mole", "history"): _mole_history,
        ("fclones", "group"): _fclones,
        ("dust", "tree"): _dust,
        ("f2", "preview"): _f2,
        ("rclone", "lsjson"): _rclone,
    }
    result = parsers[(tool, operation)](data)
    return {
        "schema_version": "1.0",
        "tool": tool,
        "operation": operation,
        "version": spec["version"],
        "parser_version": spec["parser_version"],
        "provenance": "imported-report",
        "source": spec["source"],
        "side_effects": spec["side_effects"],
        "authorizes_mutation": False,
        **result,
    }


def _mole_analyze(data: object) -> dict[str, Any]:
    obj = _object(data, "Mole analyze")
    state = obj.get("scan_status")
    if not isinstance(state, str) or state not in SCAN_STATES:
        raise ToolError("Mole analyze requires complete/partial/unavailable scan_status")
    entries = []
    for raw in _array(obj.get("entries"), "entries"):
        row = _object(raw, "entry")
        entry_state = row.get("scan_status")
        if not isinstance(entry_state, str) or entry_state not in SCAN_STATES:
            raise ToolError("Mole entry has unknown scan_status")
        size = None if entry_state == "unavailable" else _integer(row.get("size"), "entry.size")
        entries.append(
            {
                "path": _string(row.get("path"), "entry.path"),
                "name": _string(row.get("name"), "entry.name"),
                "size": size,
                "is_dir": _boolean(row.get("is_dir"), "entry.is_dir"),
                "coverage": entry_state,
                "size_is_lower_bound": entry_state == "partial",
                "tool_cleanable_hint": _boolean(row.get("cleanable", False), "entry.cleanable"),
                "risk": "unknown",
                "action": "review",
            }
        )
    if state == "complete" and any(row["coverage"] != "complete" for row in entries):
        state = "partial"
    return {
        "coverage": state,
        "path": _string(obj.get("path"), "path"),
        "overview": _boolean(obj.get("overview"), "overview"),
        "logical_bytes": None if state == "unavailable" else _integer(obj.get("total_size"), "total_size"),
        "files_seen": _integer(obj.get("total_files"), "total_files", nullable=True),
        "size_is_lower_bound": state == "partial",
        "entries": entries,
        "warnings": ["Mole cleanable hints are classification, not permission or a frozen cleanup plan."],
    }


def _mole_status(data: object) -> dict[str, Any]:
    obj = _object(data, "Mole status")
    disks = []
    for raw in _array(obj.get("disks"), "disks"):
        row = _object(raw, "disk")
        disks.append(
            {
                "path": _string(row.get("mount"), "disk.mount"),
                "total_bytes": _integer(row.get("total"), "disk.total"),
                "used_bytes": _integer(row.get("used"), "disk.used"),
                "filesystem": _string(row.get("fstype"), "disk.fstype", empty=True),
            }
        )
    memory = _object(obj.get("memory"), "memory")
    return {
        "coverage": "unknown",  # A collector snapshot does not attest complete filesystem coverage.
        "collected_at": _string(obj.get("collected_at"), "collected_at"),
        "disks": disks,
        "trash_retained_bytes": _integer(obj.get("trash_size"), "trash_size", nullable=True),
        "trash_approximate": _boolean(obj.get("trash_approx", True), "trash_approx"),
        "memory": {
            key: _integer(memory.get(key), f"memory.{key}", nullable=True) for key in ("used", "total", "available")
        },
        "warnings": ["Process commands, host/network identity, and health-score advice are not imported."],
    }


def _mole_history(data: object) -> dict[str, Any]:
    obj = _object(data, "Mole history")
    sessions = []
    for raw in _array(obj.get("sessions"), "sessions"):
        row = _object(raw, "session")
        actions = _object(row.get("actions"), "actions")
        sessions.append(
            {
                "command": _string(row.get("command"), "session.command"),
                "run_id": _string(row.get("run_id"), "session.run_id", empty=True),
                "attribution": _string(row.get("attribution"), "session.attribution"),
                "started_at": _string(row.get("started_at"), "session.started_at", empty=True),
                "ended_at": _string(row.get("ended_at"), "session.ended_at", empty=True),
                "size_display": _string(row.get("size"), "session.size", empty=True),
                "actions": {
                    name: _integer(actions.get(name), f"actions.{name}")
                    for name in ("removed", "trashed", "skipped", "failed", "rebuilt", "other")
                },
            }
        )
    deletions = []
    for raw in _array(obj.get("deletions"), "deletions"):
        row = _object(raw, "deletion")
        deletions.append(
            {
                "path": _string(row.get("path"), "deletion.path"),
                "mode": _string(row.get("mode"), "deletion.mode"),
                "status": _string(row.get("status"), "deletion.status"),
                "timestamp": _string(row.get("timestamp"), "deletion.timestamp"),
                "size_kb": _integer(row.get("size_kb"), "deletion.size_kb", nullable=True),
                "restore_verified": False,
            }
        )
    return {
        "coverage": "partial",
        "limit": _integer(obj.get("limit"), "limit"),
        "sessions": sessions,
        "deletions": deletions,
        "warnings": ["Bounded external history is supplementary evidence, not a Files Buddy undo manifest."],
    }


def _fclones(data: object) -> dict[str, Any]:
    obj = _object(data, "fclones report")
    header = _object(obj.get("header"), "header")
    if header.get("version") != "0.35.0":
        raise ToolError("fclones header.version does not match parser 0.35.0")
    stats_raw = header.get("stats")
    stats = None
    if stats_raw is not None:
        stats = _object(stats_raw, "header.stats")
        for key in (
            "group_count",
            "total_file_count",
            "total_file_size",
            "redundant_file_count",
            "redundant_file_size",
            "missing_file_count",
            "missing_file_size",
        ):
            _integer(stats.get(key), f"header.stats.{key}")
    groups = []
    path_count = 0
    for raw in _array(obj.get("groups"), "groups"):
        row = _object(raw, "group")
        paths = [_string(value, "group file") for value in _array(row.get("files"), "group.files")]
        path_count += len(paths)
        if path_count > MAX_ROWS:
            raise ToolError("fclones report exceeds its total path-row budget")
        if len(paths) < 2 or len(set(paths)) != len(paths):
            raise ToolError("A fclones duplicate group must name at least two distinct paths")
        size = _integer(row.get("file_len"), "group.file_len")
        groups.append(
            {
                "files": paths,
                "size": size,
                "hash": _string(row.get("file_hash"), "group.file_hash"),
                "hash_algorithm": "fclones-reported-unknown",  # Do not relabel an upstream hash.
                "kind": "exact",
                "review_only": True,
                "risk": "unknown",
                "keeper": None,
                "candidate_bytes": (len(paths) - 1) * size,
                "dependency_evidence": ["Content groups require fresh local identity, metadata, and ownership review."],
            }
        )
    return {
        "coverage": "partial" if stats is None or stats["missing_file_count"] else "complete",
        "base_dir": _string(header.get("base_dir"), "header.base_dir"),
        "duplicates": groups,
        "stats": stats,
        "warnings": ["Imported groups do not establish eligibility, a keeper, or reclaimable physical bytes."],
    }


def _dust(data: object) -> dict[str, Any]:
    root = _object(data, "dust root DisplayNode")
    rows = []
    pending = [(root, 0)]
    while pending:
        node, depth = pending.pop()
        if len(rows) >= MAX_ROWS or depth > 64:
            raise ToolError("dust tree exceeds row/depth budget")
        rows.append(
            {
                "path": _string(node.get("name"), "dust.name"),
                "size_display": _string(node.get("size"), "dust.size"),
                "bytes": None,  # Formatted/rounded sizes cannot drive exact byte accounting.
                "depth": depth,
            }
        )
        for raw in _array(node.get("children"), "dust.children"):
            pending.append((_object(raw, "dust child"), depth + 1))
    return {
        "coverage": "unknown",
        "directories": rows,
        "warnings": ["dust DisplayNode sizes are formatted strings; byte accounting remains unknown."],
    }


def _f2(data: object) -> dict[str, Any]:
    rows = []
    destinations: set[str] = set()
    for raw in _array(data, "F2 preview"):
        row = _object(raw, "F2 row")
        source = _string(row.get("source"), "F2.source")
        target = _string(row.get("target"), "F2.target")
        base = _string(row.get("base_dir"), "F2.base_dir", empty=True)
        target_dir = _string(row.get("target_dir"), "F2.target_dir", empty=True)
        status = _string(row.get("status"), "F2.status")
        destination = str(Path(target_dir) / target)
        conflict = destination in destinations or status not in {"ok", "unchanged"}
        destinations.add(destination)
        rows.append(
            {
                "source": str(Path(base) / source),
                "destination": destination,
                "tool_status": status,
                "conflict": conflict,
                "is_dir": _boolean(row.get("is_dir"), "F2.is_dir"),
                "review_only": True,
            }
        )
    return {
        "coverage": "unknown",
        "mappings": rows,
        "warnings": [
            "Preview mappings require absolute scope resolution, collision checks, fresh fingerprints, and approval."
        ],
    }


def _rclone(data: object) -> dict[str, Any]:
    files = []
    for raw in _array(data, "rclone lsjson"):
        row = _object(raw, "rclone row")
        size = row.get("Size")
        if size == -1:
            size = None  # Some backends cannot report object/directory size.
        size = _integer(size, "rclone.Size", nullable=True)
        files.append(
            {
                "path": _string(row.get("Path"), "rclone.Path", empty=True),
                "name": _string(row.get("Name"), "rclone.Name", empty=True),
                "size": size,
                "is_dir": _boolean(row.get("IsDir"), "rclone.IsDir"),
                "provider_id": _string(row["ID"], "rclone.ID") if row.get("ID") is not None else None,
                "modified_at": _string(row["ModTime"], "rclone.ModTime", empty=True)
                if row.get("ModTime") is not None
                else None,
                "content_verified": False,
            }
        )
    return {
        "coverage": "unknown",
        "files": files,
        "warnings": [
            "A listing does not prove sync completion, content equality, local residency, or independent backup."
        ],
    }


def run_bounded(argv: list[str], *, timeout: float = 30, max_output_bytes: int = MAX_OUTPUT_BYTES) -> dict[str, Any]:
    """Run a fixed argv, bound both pipes, and stop the whole subprocess group."""
    if not argv or not 0 < timeout <= 300 or not 0 < max_output_bytes <= MAX_OUTPUT_BYTES:
        raise ToolError("Invalid subprocess budget")
    started = time.monotonic()
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    proc = subprocess.Popen(
        argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True
    )
    assert proc.stdout is not None
    assert proc.stderr is not None
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(proc.stdout, selectors.EVENT_READ, "stdout")
            selector.register(proc.stderr, selectors.EVENT_READ, "stderr")
            total = 0
            while selector.get_map():
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    raise ToolError("Observation exceeded its time budget")
                for key, _ in selector.select(min(remaining, 0.1)):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    total += len(chunk)
                    if total > max_output_bytes:
                        raise ToolError("Observation exceeded its combined stdout/stderr byte budget")
                    buffers[key.data].extend(chunk)
            remaining = max(0.001, timeout - (time.monotonic() - started))
            proc.wait(timeout=remaining)
    except BaseException:
        with suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        raise
    finally:
        proc.stdout.close()
        proc.stderr.close()
    return {
        "argv": argv,
        "exit_code": proc.returncode,
        "stdout": buffers["stdout"].decode("utf-8", errors="strict"),
        "stderr": buffers["stderr"].decode("utf-8", errors="replace"),
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def _local_observation_path(value: str | None) -> str:
    if not value:
        raise ToolError("An explicit local scope is required")
    path = Path(value).expanduser().absolute()
    if ".." in path.parts:
        raise ToolError("Local observation scope must be normalized without parent traversal")
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ToolError("External tool scopes cannot contain symlink components")
    if not path.is_dir():
        raise ToolError("Observation scope must be an existing directory")
    if any(
        part.casefold() in {"cloudstorage", "mobile documents", ".git", "dropbox", "google drive"}
        or part.casefold().startswith(("onedrive", "googledrive"))
        for part in path.parts
    ):
        raise ToolError("Use metadata inventory for cloud or protected paths")
    policy_path = Path(str(path).casefold())
    if path == Path("/") or any(
        policy_path == p or p in policy_path.parents
        for p in map(Path, ("/system", "/library", "/usr", "/bin", "/sbin", "/etc", "/private"))
    ):
        raise ToolError("External tool scope is protected")
    return str(path)


def observe(
    tool: str, operation: str, *, path: str | None = None, limit: int = 20, timeout: float = 30
) -> dict[str, Any]:
    """Execute only allowlisted metadata observations; all other adapters import."""
    registry = load_registry()["tools"]
    if tool not in registry or operation not in registry[tool]["operations"]:
        raise ToolError("Unsupported tool operation")
    record = registry[tool]
    op = record["operations"][operation]
    if not op["execute"]:
        raise ToolError("This adapter imports reviewed JSON only; native execution is not qualified")
    executable = shutil.which(record["executable"])
    if executable is None:
        raise ToolError(f"Missing optional tool: {record['executable']}; no installation was attempted")
    if tool == "mole" and operation == "analyze":
        args = ["analyze", "--json", _local_observation_path(path)]
    elif tool == "mole" and operation == "history":
        if not 1 <= limit <= 200:
            raise ToolError("Mole history limit must be 1..200")
        args = ["history", "--json", "--limit", str(limit)]
    elif tool == "mole" and operation == "status":
        args = ["status", "--json"]
    elif tool == "rclone" and operation == "lsjson":
        if not path or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_. -]*:[^\x00-\x1f]*", path):
            raise ToolError("Use an explicit configured rclone remote:path, not an on-the-fly backend")
        args = ["lsjson", path]
    else:
        raise ToolError("No live observation command for this capability")
    version_receipt = run_bounded([executable, *record["version_argv"]], timeout=min(timeout, 10))
    if version_receipt["exit_code"]:
        raise ToolError("Version probe failed")
    match = re.search(r"\b[vV]?(\d+\.\d+\.\d+)\b", version_receipt["stdout"])
    if not match:
        raise ToolError("Could not identify the installed version")
    version = match.group(1)
    capability(tool, operation, version)  # Fail before the observation on unknown versions.
    receipt = run_bounded([executable, *args], timeout=timeout)
    if receipt["exit_code"] not in op["accepted_exit_codes"]:
        raise ToolError(f"Observation failed with exit code {receipt['exit_code']}")
    data = parse_json(receipt["stdout"])
    result = parse_observation(tool, operation, version, data)
    result.update(
        provenance="executed-observation",
        executable=executable,
        argv=receipt["argv"],
        exit_code=receipt["exit_code"],
        elapsed_seconds=receipt["elapsed_seconds"],
        stderr_present=bool(receipt["stderr"]),
    )
    return result


def validate_organize_rules(data: object, root: Path) -> dict[str, Any]:
    """Accept a deliberately small declarative subset before any simulation."""
    root = Path(_local_observation_path(str(root)))
    obj = _object(data, "rules document")
    if set(obj) != {"rules"}:
        raise ToolError("Rules document accepts only 'rules'")
    rules = _array(obj["rules"], "rules")
    if not 1 <= len(rules) <= 128:
        raise ToolError("Use 1..128 bounded rules")
    normalized = []
    for raw in rules:
        rule = _object(raw, "rule")
        if set(rule) - {"name", "locations", "filters", "actions"}:
            raise ToolError("Executable/custom organize settings are not allowed")
        locations = _array(rule.get("locations"), "locations")
        if len(locations) != 1 or Path(_local_observation_path(_string(locations[0], "location"))) != root:
            raise ToolError("Each rule must name the single approved root exactly")
        filters = _array(rule.get("filters"), "filters")
        if len(filters) != 1:
            raise ToolError("Only one extension filter per rule is supported")
        extension_filter = _object(filters[0], "extension filter")
        if set(extension_filter) != {"extension"}:
            raise ToolError("Only a literal extension filter is allowed")
        extensions = _array(extension_filter["extension"], "extensions")
        if not extensions or any(
            not isinstance(ext, str) or not re.fullmatch(r"[A-Za-z0-9]{1,16}", ext) for ext in extensions
        ):
            raise ToolError("Extensions must be nonempty literal alphanumeric strings")
        actions = _array(rule.get("actions"), "actions")
        if len(actions) != 1:
            raise ToolError("Exactly one move/copy proposal per rule is supported")
        action = _object(actions[0], "action")
        if len(action) != 1 or next(iter(action)) not in {"move", "copy"}:
            raise ToolError("Only move/copy proposals are allowed; shell/python/delete/custom actions are rejected")
        kind, value = next(iter(action.items()))
        template = _string(value, "destination template")
        literal = template.replace("{name}", "").replace("{extension}", "")
        if "{" in literal or "}" in literal:
            raise ToolError("Template expressions and escaped braces are not allowed")
        try:
            for _, field, format_spec, conversion in string.Formatter().parse(template):
                if field is not None and (field not in {"name", "extension"} or format_spec or conversion):
                    raise ToolError("Only literal {name} and {extension} placeholders are allowed")
        except ValueError as exc:
            raise ToolError(f"Invalid destination template: {exc}") from exc
        destination = Path(template.replace("{name}", "example").replace("{extension}", "txt")).expanduser()
        destination = destination if destination.is_absolute() else root / destination
        if ".." in destination.parts or not destination.is_relative_to(root) or destination == root:
            raise ToolError("Destination must be strictly inside the approved root without traversal")
        for ancestor in destination.parents:
            if ancestor.is_symlink():
                raise ToolError("Destination cannot traverse a symlink")
        normalized.append({"extensions": sorted(set(extensions)), "action": kind, "destination_template": template})
    return {
        "valid": True,
        "scope": str(root),
        "rules": normalized,
        "execution_allowed": False,
        "next_step": "Build exact mappings, check dependency exclusions/collisions, and obtain approval.",
    }
