#!/usr/bin/env python3
"""Single-URL trafilatura CLI wrapper with JSON result envelope."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any


def _trafilatura_binary() -> str:
    binary = shutil.which("trafilatura")
    if not binary:
        raise RuntimeError(
            "trafilatura binary not found on PATH; install with pipx install trafilatura or pip install trafilatura"
        )
    return binary


def _build_command(
    url: str,
    *,
    output_format: str,
    with_metadata: bool,
    precision: bool,
    recall: bool,
    archived: bool,
    fast: bool,
    no_comments: bool,
    no_tables: bool,
) -> list[str]:
    binary = _trafilatura_binary()
    command = [binary, "-u", url]

    format_flags = {
        "txt": [],
        "markdown": ["--markdown"],
        "json": ["--json"],
        "xml": ["--xml"],
        "html": ["--html"],
        "csv": ["--csv"],
        "xmltei": ["--xmltei"],
    }
    if output_format not in format_flags:
        raise ValueError(f"unsupported output format: {output_format}")
    command.extend(format_flags[output_format])

    if with_metadata:
        command.append("--with-metadata")
    if precision:
        command.append("--precision")
    if recall:
        command.append("--recall")
    if archived:
        command.append("--archived")
    if fast:
        command.append("--fast")
    if no_comments:
        command.append("--no-comments")
    if no_tables:
        command.append("--no-tables")

    return command


def _parse_json_metadata(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def extract_url(
    url: str,
    *,
    output_format: str = "markdown",
    with_metadata: bool = False,
    precision: bool = False,
    recall: bool = False,
    archived: bool = False,
    fast: bool = False,
    no_comments: bool = False,
    no_tables: bool = False,
    timeout: int = 120,
) -> dict[str, Any]:
    command = _build_command(
        url,
        output_format=output_format,
        with_metadata=with_metadata,
        precision=precision,
        recall=recall,
        archived=archived,
        fast=fast,
        no_comments=no_comments,
        no_tables=no_tables,
    )

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "url": url,
            "command": command,
            "error": f"timeout after {timeout}s",
            "stdout": (exc.stdout or "").strip() if exc.stdout else "",
            "stderr": (exc.stderr or "").strip() if exc.stderr else "",
        }

    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    ok = result.returncode == 0 and bool(stdout)

    envelope: dict[str, Any] = {
        "ok": ok,
        "url": url,
        "output_format": output_format,
        "command": command,
        "exit_code": result.returncode,
        "text": stdout,
        "text_length": len(stdout),
        "stderr": stderr,
    }

    if output_format == "json" and stdout:
        meta = _parse_json_metadata(stdout)
        envelope["metadata"] = {
            "title": meta.get("title"),
            "author": meta.get("author"),
            "date": meta.get("date"),
            "url": meta.get("url") or url,
            "hostname": meta.get("hostname"),
        }

    return envelope


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract a single URL via trafilatura CLI")
    parser.add_argument("--url", required=True, help="URL to extract")
    parser.add_argument(
        "--output-format",
        choices=("txt", "markdown", "json", "xml", "html", "csv", "xmltei"),
        default="markdown",
    )
    parser.add_argument("--with-metadata", action="store_true")
    parser.add_argument("--precision", action="store_true")
    parser.add_argument("--recall", action="store_true")
    parser.add_argument("--archived", action="store_true")
    parser.add_argument("--fast", action="store_true")
    parser.add_argument("--no-comments", action="store_true")
    parser.add_argument("--no-tables", action="store_true")
    parser.add_argument("--format", choices=("json",), default="json")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args(argv)

    try:
        report = extract_url(
            args.url,
            output_format=args.output_format,
            with_metadata=args.with_metadata,
            precision=args.precision,
            recall=args.recall,
            archived=args.archived,
            fast=args.fast,
            no_comments=args.no_comments,
            no_tables=args.no_tables,
            timeout=args.timeout,
        )
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.format == "json":
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")

    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())