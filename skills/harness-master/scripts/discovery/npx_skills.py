#!/usr/bin/env python3
"""Bounded npx skills find/list with timeout and normalized JSON output."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from schemas import write_json

DEFAULT_TIMEOUT_SEC = 45


def _run_command(cmd: list[str], *, timeout_sec: int) -> dict[str, Any]:
    stdout_fd, stdout_path = tempfile.mkstemp(prefix="discover-npx-", suffix=".out", text=True)
    stderr_fd, stderr_path = tempfile.mkstemp(prefix="discover-npx-", suffix=".err", text=True)
    os.close(stdout_fd)
    os.close(stderr_fd)
    started = time.monotonic()
    try:
        with open(stdout_path, "w", encoding="utf-8") as out, open(stderr_path, "w", encoding="utf-8") as err:
            proc = subprocess.Popen(
                cmd,
                stdout=out,
                stderr=err,
                start_new_session=True,
                text=True,
            )
            try:
                proc.wait(timeout=timeout_sec)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(timeout=2)
                return {
                    "ok": False,
                    "error": f"Timed out after {timeout_sec}s",
                    "command": cmd,
                    "duration_ms": int((time.monotonic() - started) * 1000),
                }

        stdout = Path(stdout_path).read_text(encoding="utf-8", errors="replace")
        stderr = Path(stderr_path).read_text(encoding="utf-8", errors="replace")
        return {
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "command": cmd,
            "duration_ms": int((time.monotonic() - started) * 1000),
        }
    finally:
        for path in (stdout_path, stderr_path):
            with contextlib.suppress(OSError):
                Path(path).unlink(missing_ok=True)


LINE_RE = re.compile(
    r"(?P<name>[a-z0-9][a-z0-9-]*)\s+"
    r"(?P<source>[^\s]+)\s+"
    r"(?:(?P<installs>\d+)\s+installs?)?",
    re.IGNORECASE,
)


def parse_find_output(stdout: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = LINE_RE.search(stripped)
        if match:
            installs = match.group("installs")
            candidates.append({
                "name": match.group("name"),
                "source": match.group("source"),
                "install_count": int(installs) if installs else None,
                "raw_line": stripped,
            })
        else:
            candidates.append({"raw_line": stripped})
    return candidates


def cmd_find(query: str, *, timeout_sec: int, retries: int) -> dict[str, Any]:
    command = ["npx", "-y", "skills", "find", query]
    last: dict[str, Any] = {}
    for attempt in range(retries + 1):
        last = _run_command(command, timeout_sec=timeout_sec)
        last["attempt"] = attempt + 1
        if last.get("ok"):
            break
    stdout = str(last.get("stdout", ""))
    return {
        "version": 1,
        "query": query,
        "ok": bool(last.get("ok")),
        "error": last.get("error"),
        "duration_ms": last.get("duration_ms"),
        "candidates": parse_find_output(stdout),
        "raw_stdout": stdout,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run npx skills find with timeout")
    sub = parser.add_subparsers(dest="command", required=True)

    find_p = sub.add_parser("find")
    find_p.add_argument("query")
    find_p.add_argument("--timeout-sec", type=int, default=DEFAULT_TIMEOUT_SEC)
    find_p.add_argument("--retries", type=int, default=1)
    find_p.add_argument("-o", "--output", type=Path, default=None)

    args = parser.parse_args(argv)

    if args.command == "find":
        result = cmd_find(args.query, timeout_sec=args.timeout_sec, retries=args.retries)
        if args.output:
            write_json(args.output, result)
        else:
            print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
