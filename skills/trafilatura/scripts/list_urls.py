#!/usr/bin/env python3
"""Discovery --list wrapper for trafilatura feed/sitemap/crawl/probe modes."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from typing import Any

_MODE_FLAGS = {
    "feed": "--feed",
    "sitemap": "--sitemap",
    "crawl": "--crawl",
    "probe": "--probe",
}

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def _trafilatura_binary() -> str:
    binary = shutil.which("trafilatura")
    if not binary:
        raise RuntimeError(
            "trafilatura binary not found on PATH; install with pipx install trafilatura or pip install trafilatura"
        )
    return binary


def _parse_urls(stdout: str) -> list[str]:
    urls: list[str] = []
    for line in stdout.splitlines():
        candidate = line.strip()
        if _URL_RE.match(candidate):
            urls.append(candidate)
    return urls


def list_urls(
    url: str,
    *,
    mode: str,
    url_filters: list[str] | None = None,
    target_language: str | None = None,
    timeout: int = 180,
) -> dict[str, Any]:
    if mode not in _MODE_FLAGS:
        raise ValueError(f"unsupported mode: {mode}")

    binary = _trafilatura_binary()
    command = [binary, _MODE_FLAGS[mode], url, "--list"]
    if url_filters:
        command.extend(["--url-filter", *url_filters])
    if target_language:
        command.extend(["--target-language", target_language])

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
            "mode": mode,
            "url": url,
            "command": command,
            "error": f"timeout after {timeout}s",
            "urls": [],
            "url_count": 0,
            "stderr": (exc.stderr or "").strip() if exc.stderr else "",
        }

    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    urls = _parse_urls(stdout)
    ok = result.returncode == 0

    return {
        "ok": ok,
        "mode": mode,
        "url": url,
        "command": command,
        "exit_code": result.returncode,
        "url_count": len(urls),
        "urls": urls,
        "sample_urls": urls[:10],
        "stderr": stderr,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List URLs via trafilatura discovery modes")
    parser.add_argument("--url", required=True)
    parser.add_argument("--mode", choices=sorted(_MODE_FLAGS), required=True)
    parser.add_argument("--url-filter", action="append", default=[])
    parser.add_argument("--target-language")
    parser.add_argument("--format", choices=("json",), default="json")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args(argv)

    try:
        report = list_urls(
            args.url,
            mode=args.mode,
            url_filters=args.url_filter or None,
            target_language=args.target_language,
            timeout=args.timeout,
        )
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())