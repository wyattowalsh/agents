#!/usr/bin/env python3
"""Review exact file-operation plans, execute approved mappings, and reconcile state."""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

from files_buddy_execution import (
    ContractError,
    StateStore,
    canonical_digest,
    create_state,
    execute,
    inspect_legacy,
    load_json,
    make_plan,
    reconcile,
    reverse_plan,
    validate_outcomes,
    validate_state,
)
from files_buddy_report import ReportError, new_report, normalize_report


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--state-dir",
        type=Path,
        default=Path.home() / ".files-buddy",
        help="Private state/coordination directory; all cooperating invocations must share it",
    )
    commands = result.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan", help="Capture exact mapping and evidence; writes state only")
    plan.add_argument(
        "--mapping", required=True, type=Path, help="JSON array of {type, source, destination}; absolute paths"
    )
    plan.add_argument("--source-root", action="append", required=True, type=Path)
    plan.add_argument("--destination-root", action="append", required=True, type=Path)
    plan.add_argument("--intent", required=True)
    plan.add_argument(
        "--local-only", action="store_true", help="Attest roots are local, outside all provider sync folders"
    )
    show = commands.add_parser("show", aliases=["inspect"], help="Inspect state; persisted v1 ledgers are read-only")
    show.add_argument("manifest")
    report = commands.add_parser(
        "report", help="Export a derived dashboard report; no execution authority or state write"
    )
    report.add_argument("manifest")
    listing = commands.add_parser("list", help="List contained regular state files only")
    listing.add_argument("--status")
    search = commands.add_parser("search", help="Search contained state records without following symlinks")
    search.add_argument("query")
    validate = commands.add_parser(
        "validate", help="Validate schema and current filesystem evidence; invalid returns nonzero"
    )
    validate.add_argument("manifest")
    validate.add_argument("--schema-only", action="store_true")
    run = commands.add_parser(
        "execute", help="Execute one exact reviewed local plan on macOS; never replays started work"
    )
    run.add_argument("manifest")
    run.add_argument("--approve", required=True, help="Exact digest approved by the user through the trusted caller")
    recovery = commands.add_parser("reconcile", help="Observe interrupted effects without replaying mutations")
    recovery.add_argument("manifest")
    undo = commands.add_parser("undo", help="Preview reverse plan; --approve executes its exact digest on macOS")
    undo.add_argument("manifest")
    undo.add_argument("--approve", help="Exact reverse digest approved by the user")
    return result


def _emit(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False))


def _absolute(path: Path) -> Path:
    # Do not resolve away symlinks; core traversal must reject them.
    return Path(os.path.abspath(path.expanduser()))


def _summary(path: Path, state: dict[str, Any]) -> dict[str, Any]:
    if state.get("version") == "1.0":
        inspection = inspect_legacy(state)
        if not inspection["valid"]:
            raise ContractError("Invalid legacy manifest: " + "; ".join(inspection["errors"]))
        return {
            "manifest": str(path),
            "legacy": True,
            "valid": inspection["valid"],
            "status": state["status"],
            "intent": state["intent"],
            "execution_supported": False,
        }
    validate_state(state)
    return {
        "manifest": str(path),
        "run_id": state["run_id"],
        "status": state["status"],
        "intent": state["plan"]["intent"],
        "plan_digest": state["plan_digest"],
        "operation_count": len(state["operations"]),
    }


def _mutation_platform() -> None:
    if platform.system() != "Darwin":
        raise ContractError("Filesystem mutation is macOS-only; no platform override is exposed")


def _report(path: Path, state: dict[str, Any]) -> dict[str, Any]:
    """Derive a report from recorded state; do not claim fresh disk measurements."""
    validate_state(state)
    reversing = state["undo"] is not None and state["undo"]["approval"] is not None
    data = state["undo"] if reversing else state
    plan = data["plan"]
    scope = sorted({root["path"] for root in plan["source_roots"] + plan["destination_roots"]})
    report = new_report("undo" if reversing else "execute", scope)
    report["run_id"] = state["run_id"]
    report["updated_at"] = state["updated_at"]
    report["started_at"] = state["created_at"]
    report["status"] = {
        "planned": "waiting-for-approval",
        "running": "executing",
        "completed": "completed",
        "undone": "completed",
        "partial": "partial",
        "failed": "failed",
    }[state["status"]]
    uncertain = any(row["status"] in {"prepared", "uncertain"} for row in data["operations"])
    report["coverage"] = {
        "status": "partial" if uncertain else "complete",
        "omissions": [
            "Covers only the exact operation plan; not a disk inventory.",
            "No physical reclaimed-space or cloud-quota measurement.",
        ],
    }
    report["counts"] = {"operations_total": len(data["operations"])}
    for status_name in sorted({row["status"] for row in data["operations"]}):
        report["counts"][f"operations_{status_name}"] = sum(row["status"] == status_name for row in data["operations"])
    total = sum(op["before"]["size_bytes"] for op in plan["operations"])
    report["savings"]["logical_bytes"] = total
    report["savings"]["selected_bytes"] = total if data["approval"] is not None else None
    report["savings"]["acted_bytes"] = (
        None
        if uncertain
        else sum(
            op["before"]["size_bytes"]
            for op, row in zip(plan["operations"], data["operations"], strict=True)
            if row["status"] in {"applied", "verified"}
        )
    )
    quarantine_bytes: int | None = 0
    if reversing:
        if uncertain:
            quarantine_bytes = None
        else:
            for original in state["plan"]["operations"]:
                if original["type"] != "copy":
                    continue
                quarantine = str(
                    Path(original["destination"]).with_name(
                        f".files-buddy-undo-{state['run_id']}-{original['operation_id']}"
                    )
                )
                for op, row in zip(plan["operations"], data["operations"], strict=True):
                    if op["destination"] == quarantine and row["status"] == "verified":
                        quarantine_bytes += op["before"]["size_bytes"]
    report["savings"]["quarantined_bytes"] = quarantine_bytes
    report["manifest"] = {
        "path": str(path),
        "run_id": state["run_id"],
        "plan_digest": data["plan_digest"],
        "state_digest": "sha256:" + canonical_digest(state),
    }
    report["operations"] = [
        {
            "operation_id": op["operation_id"],
            "type": op["type"],
            "source": op["source"],
            "destination": op["destination"],
            "size_bytes": op["before"]["size_bytes"],
            "status": row["status"],
            "recovery": op["recovery"],
            "error": row["error"],
        }
        for op, row in zip(plan["operations"], data["operations"], strict=True)
    ]
    report["normalization_warnings"].append(
        "Execution receipts are historical; run validate for fresh filesystem verification. Reports cannot authorize execution."
    )
    return normalize_report(report)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    store = StateStore(args.state_dir)
    try:
        if args.command == "plan":
            if args.mapping.stat().st_size > 16 * 1024 * 1024:
                raise ContractError("Mapping exceeds 16 MiB input limit")
            mapping = load_json(args.mapping.read_text(encoding="utf-8"))
            plan = make_plan(
                mapping,
                [_absolute(root) for root in args.source_root],
                [_absolute(root) for root in args.destination_root],
                args.intent,
                local_only=args.local_only,
            )
            path, state = create_state(store, plan)
            _emit({"manifest": str(path), "plan_digest": state["plan_digest"], "plan": plan, "approval_required": True})
        elif args.command in {"list", "search"}:
            results = []
            candidates, errors = store.discover()
            for path in candidates:
                try:
                    state = store.read(path)
                    summary = _summary(path, state)
                except (OSError, ContractError, UnicodeError) as exc:
                    errors.append({"manifest": str(path), "error": str(exc)})
                    continue
                if args.command == "list":
                    if args.status is None or state["status"] == args.status:
                        results.append(summary)
                elif args.query.casefold() in json.dumps(state).casefold():
                    results.append(summary)
            _emit({"valid": not errors, "results": results, "errors": errors})
            return 0 if not errors else 1
        elif args.command in {"show", "inspect", "validate", "report"}:
            path = store.resolve(args.manifest)
            state = store.read(path)
            if state.get("version") == "1.0":
                if args.command == "report":
                    raise ContractError("Legacy ledgers are inspect-only; they have no v2 execution evidence")
                result = inspect_legacy(state, verify_files=args.command == "validate" and not args.schema_only)
                _emit(result)
                return 0 if result["valid"] else 1
            validate_state(state)
            if args.command == "report":
                _emit(_report(path, state))
            elif args.command in {"show", "inspect"}:
                _emit(state)
            else:
                errors = [] if args.schema_only else validate_outcomes(state)
                _emit(
                    {
                        "valid": not errors,
                        "schema_valid": True,
                        "checked": "schema" if args.schema_only else "schema-and-current-filesystem",
                        "authorization_checked": False,
                        "errors": errors,
                    }
                )
                return 0 if not errors else 1
        elif args.command == "execute":
            _mutation_platform()
            state = execute(store, args.manifest, args.approve)
            _emit(state)
            return 0 if state["status"] == "completed" else 1
        elif args.command == "reconcile":
            state = reconcile(store, args.manifest)
            _emit(state)
            return 0 if state["status"] in {"planned", "completed", "undone"} else 1
        elif args.command == "undo":
            if args.approve is None:
                state = reverse_plan(store, args.manifest)
                _emit(
                    {
                        "manifest": str(store.resolve(args.manifest)),
                        "reverse_plan": state["undo"],
                        "approval_required": True,
                        "copies_retained_in_quarantine": True,
                    }
                )
            else:
                _mutation_platform()
                state = execute(store, args.manifest, args.approve, undo=True)
                _emit(state)
                return 0 if state["status"] == "undone" else 1
        return 0
    except (ContractError, ReportError, OSError, UnicodeError) as exc:
        _emit({"valid": False, "error": str(exc)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
