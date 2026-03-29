#!/usr/bin/env python3
"""Manifest CRUD manager for files-buddy. Manages operation manifests in ~/.files-buddy/manifests/."""

import argparse
import glob
import json
import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

STATE_DIR = Path.home() / ".files-buddy"
MANIFESTS_DIR = STATE_DIR / "manifests"
RECOVERY_LOG = STATE_DIR / "recovery.log"

REQUIRED_FIELDS = {"version", "created", "mode", "intent", "target_path", "status", "operations", "summary"}
FINAL_OPERATION_STATUSES = {"completed", "failed"}


def output_json(data):
    print(json.dumps(data, indent=2, default=str))


def output_error(message):
    print(json.dumps({"error": message}))
    sys.exit(1)


def validate_manifest_path(path):
    """Reject paths outside the manifests directory."""
    try:
        resolved = Path(path).resolve()
        manifests_resolved = MANIFESTS_DIR.resolve()
        if resolved != manifests_resolved and manifests_resolved not in resolved.parents:
            output_error(f"Path outside manifests directory: {path}")
    except (OSError, ValueError) as exc:
        output_error(f"Invalid path: {exc}")


def get_operation_source(operation):
    return operation.get("source") or operation.get("path")


def get_operation_destination(operation):
    return operation.get("destination") or operation.get("target")


def get_operation_hash(operation):
    return operation.get("blake3") or operation.get("hash")


def get_operation_size(operation):
    op_bytes = operation.get("size_bytes", operation.get("bytes"))
    if isinstance(op_bytes, bool) or not isinstance(op_bytes, (int, float)):
        return None
    return int(op_bytes)


def summarize_operations(operations):
    summary = {"total_ops": len(operations)}
    total_bytes = 0
    saw_bytes = False
    for operation in operations:
        if not isinstance(operation, dict):
            continue
        op_type = operation.get("type", "unknown")
        summary[op_type] = summary.get(op_type, 0) + 1
        op_bytes = get_operation_size(operation)
        if op_bytes is not None:
            total_bytes += op_bytes
            saw_bytes = True
    if saw_bytes:
        summary["total_bytes"] = total_bytes
    return summary


def validate_operation_record(operation, index=None):
    prefix = f"Operation {index}: " if index is not None else "Operation: "
    errors = []

    if not isinstance(operation, dict):
        return [f"{prefix}must be a JSON object"]

    op_type = operation.get("type")
    if not isinstance(op_type, str) or not op_type:
        errors.append(f"{prefix}missing required field 'type'")

    status = operation.get("status")
    if status not in FINAL_OPERATION_STATUSES:
        errors.append(
            f"{prefix}invalid status '{status}'; manifest-manager only records finalized rows "
            f"({', '.join(sorted(FINAL_OPERATION_STATUSES))})"
        )
        return errors

    if not operation.get("timestamp"):
        errors.append(f"{prefix}missing required field 'timestamp'")

    if status == "completed":
        destination = get_operation_destination(operation)
        if not destination:
            errors.append(f"{prefix}missing destination/target")

        if op_type != "mkdir" and not get_operation_source(operation):
            errors.append(f"{prefix}missing source/path")

        if op_type != "mkdir" and not get_operation_hash(operation):
            errors.append(f"{prefix}missing blake3/hash")

    return errors


def atomic_write(path, data):
    """Write JSON atomically via tmp file + rename."""
    tmp_path = str(path) + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2, default=str)
        f.write("\n")
    os.rename(tmp_path, str(path))


def read_manifest(path):
    """Read and parse a manifest file with corruption recovery."""
    validate_manifest_path(path)
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        with open(RECOVERY_LOG, "a") as log:
            log.write(f"{datetime.now(UTC).isoformat()} CORRUPT {path}: {exc}\n")
        output_error(f"Corrupt manifest {path}: {exc}")
    except FileNotFoundError:
        output_error(f"Manifest not found: {path}")


def resolve_manifest(name_or_path):
    """Resolve a manifest argument to an absolute path."""
    candidate = Path(name_or_path)
    if candidate.is_absolute() and candidate.exists():
        return candidate
    in_dir = MANIFESTS_DIR / name_or_path
    if in_dir.exists():
        return in_dir
    matches = sorted(MANIFESTS_DIR.glob(f"*{name_or_path}*"))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        output_error(f"Ambiguous manifest '{name_or_path}': {[str(m.name) for m in matches]}")
    output_error(f"Manifest not found: {name_or_path}")


def cmd_create(args):
    """Create a new operation manifest."""
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)

    short_id = uuid.uuid4().hex[:8]
    now = datetime.now(UTC)
    timestamp = now.strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"{timestamp}-{short_id}-{args.mode}.json"
    filepath = MANIFESTS_DIR / filename

    manifest = {
        "version": "1.0",
        "created": now.isoformat(),
        "mode": args.mode,
        "intent": args.intent,
        "target_path": str(Path(args.path).resolve()),
        "cloud_tagged": args.cloud_tagged,
        "status": "open",
        "tools_used": args.tool_used,
        "operations": [],
        "summary": {},
    }

    atomic_write(filepath, manifest)
    output_json({"manifest": str(filepath), "id": short_id})


def cmd_append(args):
    """Append an operation to an existing manifest."""
    filepath = resolve_manifest(args.manifest)
    manifest = read_manifest(filepath)

    if manifest["status"] != "open":
        output_error(f"Cannot append to manifest with status '{manifest['status']}'")

    try:
        operation = json.loads(args.op)
    except json.JSONDecodeError as exc:
        output_error(f"Invalid JSON in --op: {exc}")

    operation_errors = validate_operation_record(operation)
    if operation_errors:
        output_error("; ".join(operation_errors))

    manifest["operations"].append(operation)
    manifest["summary"] = summarize_operations(manifest["operations"])

    atomic_write(filepath, manifest)
    output_json({"appended": True, "total_ops": len(manifest["operations"])})


def cmd_list(args):
    """List manifests, optionally filtered by status."""
    if not MANIFESTS_DIR.exists():
        output_json([])
        return

    results = []
    for path in sorted(glob.glob(str(MANIFESTS_DIR / "*.json")), reverse=True):
        try:
            with open(path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        if args.status and data.get("status") != args.status:
            continue

        total_bytes = sum(get_operation_size(op) or 0 for op in data.get("operations", []))
        results.append({
            "path": path,
            "created": data.get("created"),
            "mode": data.get("mode"),
            "intent": data.get("intent"),
            "status": data.get("status"),
            "total_ops": len(data.get("operations", [])),
            "total_bytes": total_bytes,
        })

    output_json(results)


def cmd_search(args):
    """Search manifests for operations matching a query string."""
    if not MANIFESTS_DIR.exists():
        output_json([])
        return

    query = args.query.lower()
    matches = []

    for path in sorted(glob.glob(str(MANIFESTS_DIR / "*.json"))):
        try:
            with open(path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        for i, op in enumerate(data.get("operations", [])):
            searchable = json.dumps(op).lower()
            if query in searchable:
                matches.append({
                    "manifest": path,
                    "operation_index": i,
                    "original_path": op.get("source", op.get("path", "")),
                    "current_location": op.get("destination", op.get("target", "")),
                })

    output_json(matches)


def verify_hash(filepath, expected_hash):
    """Verify a recorded BLAKE3 hash using b3sum."""
    if not Path(filepath).exists():
        return False, "file missing"

    try:
        result = subprocess.run(
            ["b3sum", "--no-names", str(filepath)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            actual = result.stdout.strip()
            if actual == expected_hash:
                return True, None
            return False, f"hash mismatch: expected {expected_hash}, got {actual}"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, "b3sum unavailable; cannot verify recorded BLAKE3 hash"
    return False, "b3sum failed to compute hash"


def cmd_validate(args):
    """Validate a manifest's schema and verify completed operations."""
    filepath = resolve_manifest(args.manifest)
    manifest = read_manifest(filepath)

    errors = []
    warnings = []

    missing = REQUIRED_FIELDS - set(manifest.keys())
    if missing:
        errors.append(f"Missing required fields: {sorted(missing)}")

    if manifest.get("version") != "1.0":
        warnings.append(f"Unknown version: {manifest.get('version')}")

    if manifest.get("status") not in {"open", "closed", "partial", "undone"}:
        errors.append(f"Invalid status: {manifest.get('status')}")

    operations = manifest.get("operations", [])
    if not isinstance(operations, list):
        errors.append("Operations field must be a list")
        operations = []

    for i, op in enumerate(operations):
        op_errors = validate_operation_record(op, i)
        errors.extend(op_errors)
        if op_errors or op.get("status") != "completed":
            continue

        dest = get_operation_destination(op)
        if dest and not Path(dest).exists():
            errors.append(f"Operation {i}: file missing at {dest}")
            continue

        if op.get("type") == "mkdir":
            continue

        recorded_hash = get_operation_hash(op)
        ok, msg = verify_hash(dest, recorded_hash)
        if not ok:
            errors.append(f"Operation {i}: {msg}")

    output_json({
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    })


def cmd_close(args):
    """Close a manifest, setting final status based on operation outcomes."""
    filepath = resolve_manifest(args.manifest)
    manifest = read_manifest(filepath)

    if manifest["status"] != "open":
        output_error(f"Cannot close manifest with status '{manifest['status']}'")

    operations = manifest.get("operations", [])
    if not isinstance(operations, list):
        output_error("Cannot close manifest with non-list operations field")

    operation_errors = []
    for i, op in enumerate(operations):
        operation_errors.extend(validate_operation_record(op, i))
    if operation_errors:
        output_error(f"Cannot close invalid manifest: {'; '.join(operation_errors)}")

    completed = sum(1 for op in operations if op.get("status") == "completed")
    failed = sum(1 for op in operations if op.get("status") == "failed")
    total = len(operations)

    if failed > 0 or completed < total:
        manifest["status"] = "partial"
    else:
        manifest["status"] = "closed"

    created_dt = datetime.fromisoformat(manifest["created"])
    now = datetime.now(UTC)
    duration_seconds = (now - created_dt).total_seconds()

    summary = summarize_operations(operations)
    summary["completed_ops"] = completed
    summary["failed_ops"] = failed
    summary["duration_seconds"] = round(duration_seconds, 2)
    summary["closed_at"] = now.isoformat()
    manifest["summary"] = summary

    atomic_write(filepath, manifest)
    output_json({
        "closed": True,
        "status": manifest["status"],
        "completed": completed,
        "failed": failed,
        "duration_seconds": summary["duration_seconds"],
    })


def main():
    parser = argparse.ArgumentParser(description="Manifest CRUD manager for files-buddy")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    create_parser = subparsers.add_parser("create", help="Create a new manifest")
    create_parser.add_argument("--mode", required=True, help="Operation mode (e.g. move, copy, archive)")
    create_parser.add_argument("--path", required=True, help="Target path for operations")
    create_parser.add_argument("--intent", required=True, help="Description of intended operations")
    create_parser.add_argument("--cloud-tagged", action="store_true", help="Mark the manifest as cloud-backed")
    create_parser.add_argument(
        "--tool-used",
        action="append",
        default=[],
        help="Tool name used by the operation (repeatable)",
    )

    # append
    append_parser = subparsers.add_parser("append", help="Append an operation to a manifest")
    append_parser.add_argument("manifest", help="Manifest filename, path, or partial match")
    append_parser.add_argument("--op", required=True, help="Operation as JSON string")

    # list
    list_parser = subparsers.add_parser("list", help="List manifests")
    list_parser.add_argument("--status", choices=["open", "closed", "partial", "undone"], help="Filter by status")

    # search
    search_parser = subparsers.add_parser("search", help="Search manifests for matching operations")
    search_parser.add_argument("query", help="Search string (case-insensitive substring)")

    # validate
    validate_parser = subparsers.add_parser("validate", help="Validate a manifest")
    validate_parser.add_argument("manifest", help="Manifest filename, path, or partial match")

    # close
    close_parser = subparsers.add_parser("close", help="Close an open manifest")
    close_parser.add_argument("manifest", help="Manifest filename, path, or partial match")

    args = parser.parse_args()

    commands = {
        "create": cmd_create,
        "append": cmd_append,
        "list": cmd_list,
        "search": cmd_search,
        "validate": cmd_validate,
        "close": cmd_close,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
