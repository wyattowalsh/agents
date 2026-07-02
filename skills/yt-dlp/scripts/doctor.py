#!/usr/bin/env python3
"""Portable yt-dlp preflight doctor (binary, version, optional ffmpeg)."""

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
    check: dict[str, str] = {"name": name, "status": status, "summary": summary}
    if remediation:
        check["remediation"] = remediation
    return check


def _yt_dlp_binary() -> str | None:
    return shutil.which("yt-dlp")


def _ffmpeg_binary() -> str | None:
    return shutil.which("ffmpeg")


def _run_version(binary: str, args: list[str], *, timeout: int = 15) -> tuple[int, str]:
    try:
        result = subprocess.run(
            [binary, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    output = (result.stdout or result.stderr).strip()
    first_line = output.splitlines()[0] if output else ""
    return result.returncode, first_line


def collect_checks() -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    binary = _yt_dlp_binary()
    if binary:
        checks.append(_make_check("yt-dlp-binary", "ok", f"Found at {binary}"))
        code, version_line = _run_version(binary, ["--version"])
        if code == 0 and version_line:
            checks.append(_make_check("yt-dlp-version", "ok", version_line))
        else:
            checks.append(
                _make_check(
                    "yt-dlp-version",
                    "fail",
                    "yt-dlp --version failed",
                    "Reinstall yt-dlp: pipx install yt-dlp, brew install yt-dlp, or pip install -U yt-dlp",
                )
            )
    else:
        checks.append(
            _make_check(
                "yt-dlp-binary",
                "fail",
                "yt-dlp binary not found on PATH",
                "Install yt-dlp: pipx install yt-dlp, brew install yt-dlp, or pip install -U yt-dlp",
            )
        )

    ffmpeg = _ffmpeg_binary()
    if ffmpeg:
        code, version_line = _run_version(ffmpeg, ["-version"])
        if code == 0 and version_line:
            checks.append(_make_check("ffmpeg-binary", "ok", version_line))
        else:
            checks.append(
                _make_check(
                    "ffmpeg-binary",
                    "warn",
                    "ffmpeg found but -version failed",
                    "Reinstall ffmpeg for mux/merge support (brew install ffmpeg).",
                )
            )
    else:
        checks.append(
            _make_check(
                "ffmpeg-binary",
                "warn",
                "ffmpeg not found on PATH",
                "Install ffmpeg when downloading separate video+audio streams (brew install ffmpeg).",
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
    parser = argparse.ArgumentParser(description="Portable yt-dlp doctor")
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