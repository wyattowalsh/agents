#!/usr/bin/env python3
"""Check ffmpeg and ffprobe availability for the ffmpeg skill."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any


def _make_check(
    name: str,
    status: str,
    summary: str,
    remediation: str | None = None,
) -> dict[str, str]:
    check = {"name": name, "status": status, "summary": summary}
    if remediation:
        check["remediation"] = remediation
    return check


def _binary_version(binary: str) -> str | None:
    try:
        result = subprocess.run(
            [binary, "-version"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    for line in (result.stdout or result.stderr).splitlines():
        if line.strip():
            return line.strip()
    return None


def collect_checks() -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    for tool in ("ffmpeg", "ffprobe"):
        path = shutil.which(tool)
        if path:
            version = _binary_version(path)
            summary = f"Found at {path}"
            if version:
                summary = f"{summary}; {version}"
            checks.append(_make_check(f"{tool}-binary", "ok", summary))
        else:
            checks.append(
                _make_check(
                    f"{tool}-binary",
                    "fail",
                    f"{tool} not found on PATH",
                    "Install ffmpeg (includes ffprobe): brew install ffmpeg",
                )
            )

    return checks


def build_report(checks: list[dict[str, str]]) -> dict[str, Any]:
    ok_count = sum(1 for check in checks if check["status"] == "ok")
    warn_count = sum(1 for check in checks if check["status"] == "warn")
    fail_count = sum(1 for check in checks if check["status"] == "fail")
    return {
        "ok": fail_count == 0,
        "summary": {
            "total": len(checks),
            "ok": ok_count,
            "warn": warn_count,
            "fail": fail_count,
        },
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ffmpeg/ffprobe PATH doctor for ffmpeg skill")
    parser.add_argument("--format", choices=("json",), default="json")
    args = parser.parse_args(argv)

    if args.format != "json":
        print("Only --format json is supported", file=sys.stderr)
        return 2

    report = build_report(collect_checks())
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())