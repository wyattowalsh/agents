#!/usr/bin/env python3
"""Observe storage, parse reviewed OSS reports, and build bounded review queues."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

from files_buddy_inventory import ScanOptions, _open_directory, artifact_path, dedupe, scan, watch
from files_buddy_report import MAX_REPORT_BYTES, new_report, normalize_report
from files_buddy_tools import (
    MAX_OUTPUT_BYTES,
    ToolError,
    observe,
    parse_json,
    parse_observation,
    tool_inventory,
    validate_organize_rules,
)


def read_bounded(path: str, max_bytes: int = MAX_OUTPUT_BYTES) -> str:
    if path == "-":
        data = sys.stdin.buffer.read(max_bytes + 1)
    else:
        with Path(path).expanduser().open("rb") as handle:
            data = handle.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError(f"Input exceeds {max_bytes} bytes")
    return data.decode("utf-8")


def write_output(data: object, output: str | None) -> None:
    raw = json.dumps(data, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    if len(raw.encode()) > MAX_REPORT_BYTES:
        raise ValueError("Summary exceeds report budget; reduce --max-rows")
    if output:
        path = artifact_path(Path(output))
        raw_scopes: object = data.get("scope", []) if isinstance(data, dict) else []
        scopes: list[object] = [raw_scopes] if isinstance(raw_scopes, str) else []
        if isinstance(raw_scopes, list):
            scopes = cast("list[object]", raw_scopes)
        for scope in scopes:
            if isinstance(scope, str) and Path(scope).is_absolute():
                artifact_path(path, root=Path(scope))
        parent_fd = _open_directory(path.parent, create=True)
        try:
            fd = os.open(
                path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=parent_fd
            )
        finally:
            os.close(parent_fd)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(raw)
        print(json.dumps({"report": str(path), "run_id": data.get("run_id") if isinstance(data, dict) else None}))
    else:
        print(raw, end="")


def observation_report(observation: dict[str, Any], path: str | None) -> dict[str, Any]:
    scope = path or observation.get("path") or observation.get("base_dir")
    report = new_report("observe", [scope] if scope else [])
    report["status"] = "completed"
    report["coverage"] = {"status": observation["coverage"], "omissions": observation.get("warnings", [])}
    report["observation"] = observation
    if "entries" in observation:
        report["files"] = [entry for entry in observation["entries"] if not entry["is_dir"]]
        report["directories"] = [entry for entry in observation["entries"] if entry["is_dir"]]
    for key in ("duplicates", "directories"):
        if key in observation:
            report[key] = observation[key]
    if observation["tool"] == "rclone":
        report["cloud"] = observation["files"]
    if "mappings" in observation:
        report["operations"] = observation["mappings"]
    for key in ("logical_bytes", "trash_retained_bytes"):
        if key in observation:
            report["savings"][key] = observation[key]
    if observation.get("files_seen") is not None:
        report["counts"]["files_seen"] = observation["files_seen"]
    if observation.get("stats") is not None:
        report["savings"]["candidate_bytes"] = observation["stats"]["redundant_file_size"]
        report["counts"]["duplicate_groups"] = observation["stats"]["group_count"]
    return normalize_report(report)


def scan_options(args: argparse.Namespace) -> ScanOptions:
    return ScanOptions(
        include_hidden=args.include_hidden,
        cross_filesystems=args.cross_filesystems,
        excludes=tuple(args.exclude),
        cloud_roots=tuple(args.cloud_root),
        max_entries=args.max_entries,
        max_seconds=args.max_seconds,
        max_rows=args.max_rows,
        max_depth=args.max_depth,
    )


def _scan_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", type=Path, help="One explicit metadata-only directory scope")
    parser.add_argument("--database", required=True, type=Path, help="SQLite inventory outside the observed tree")
    parser.add_argument(
        "--include-hidden", action="store_true", help="Include dotfiles; .git and managed internals still excluded"
    )
    parser.add_argument("--cross-filesystems", action="store_true", help="Observe mounted descendants explicitly")
    parser.add_argument("--exclude", action="append", default=[], help="Explicit relative-path glob (repeatable)")
    parser.add_argument(
        "--cloud-root", action="append", default=[], help="Additional provider root; content reads excluded"
    )
    parser.add_argument("--max-entries", type=int, default=100_000)
    parser.add_argument("--max-seconds", type=float, default=60)
    parser.add_argument("--max-rows", type=int, default=500)
    parser.add_argument("--max-depth", type=int, default=64)
    parser.add_argument("--output", help="New JSON report file; existing files are never overwritten")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    scanner = commands.add_parser("scan", help="Metadata-only bounded inventory")
    _scan_arguments(scanner)
    scanner.add_argument(
        "--resume", action="store_true", help="Reuse cache only after re-statting objects; scope/policy must match"
    )
    duplicates = commands.add_parser("dedupe", help="Explicit local-content exact duplicate review, never deletion")
    duplicates.add_argument("--database", required=True, type=Path)
    duplicates.add_argument(
        "--read-content", action="store_true", help="Acknowledge content reads for eligible local files"
    )
    duplicates.add_argument("--max-bytes", type=int, default=2 * 1024**3)
    duplicates.add_argument("--max-seconds", type=float, default=60)
    duplicates.add_argument("--max-rows", type=int, default=500)
    duplicates.add_argument("--output")
    tools = commands.add_parser("tools", help="Find optional executables without executing or installing them")
    tools.add_argument("--output")
    observer = commands.add_parser("observe", help="Import versioned JSON or run an allowlisted metadata command")
    observer.add_argument("tool", choices=["mole", "fclones", "dust", "f2", "rclone"])
    observer.add_argument("operation", help="analyze/status/history, group, tree, preview, or lsjson")
    source = observer.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="Existing JSON report or '-' for stdin; no source tool is executed")
    source.add_argument(
        "--execute", action="store_true", help="Run the fixed allowlisted command after an exact version probe"
    )
    observer.add_argument("--version", help="Required source version for imports; not a claim of native execution")
    observer.add_argument("--path", help="Explicit local directory or configured remote:path")
    observer.add_argument("--limit", type=int, default=20)
    observer.add_argument("--timeout", type=float, default=30)
    observer.add_argument("--output")
    rules = commands.add_parser(
        "validate-rules", help="Validate constrained organize proposals without executing sim or run"
    )
    rules.add_argument("config", help="JSON or safe YAML file")
    rules.add_argument("--root", required=True, type=Path)
    rules.add_argument("--output")
    watcher = commands.add_parser("watch", help="Finite foreground metadata observations; proposal-only")
    _scan_arguments(watcher)
    watcher.add_argument("--cycles", type=int, default=3)
    watcher.add_argument("--interval", type=float, default=2)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.output:
            scope = args.path if args.command in {"scan", "watch"} else None
            artifact_path(Path(args.output), root=scope)
        if args.command == "scan":
            data = scan(args.path, args.database, options=scan_options(args), resume=args.resume)
        elif args.command == "dedupe":
            data = dedupe(
                args.database,
                read_content=args.read_content,
                max_bytes=args.max_bytes,
                max_seconds=args.max_seconds,
                max_rows=args.max_rows,
            )
        elif args.command == "tools":
            data = tool_inventory()
        elif args.command == "observe":
            if args.input:
                if not args.version:
                    raise ToolError("Imported reports require --version")
                observation = parse_observation(
                    args.tool, args.operation, args.version, parse_json(read_bounded(args.input))
                )
            else:
                if args.version:
                    raise ToolError("--version is for imports; execution observes the actual installed version")
                observation = observe(args.tool, args.operation, path=args.path, limit=args.limit, timeout=args.timeout)
            data = observation_report(observation, args.path)
        elif args.command == "validate-rules":
            raw = read_bounded(args.config, 1024 * 1024)
            if Path(args.config).suffix.lower() == ".json":
                rules = parse_json(raw)
            else:
                try:
                    import yaml
                except ImportError as exc:
                    raise ValueError(
                        "YAML input needs declared PyYAML; install skill dependencies or provide JSON"
                    ) from exc
                try:
                    rules = yaml.safe_load(raw)
                except yaml.YAMLError as exc:
                    raise ValueError(f"Invalid safe YAML: {exc}") from exc
            data = validate_organize_rules(rules, args.root)
        else:
            data = watch(
                args.path, args.database, cycles=args.cycles, interval=args.interval, options=scan_options(args)
            )
        write_output(data, args.output)
        return 0
    except (ValueError, OSError, sqlite3.Error, subprocess.SubprocessError, RecursionError) as exc:
        print(json.dumps({"error": str(exc), "command": args.command}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
