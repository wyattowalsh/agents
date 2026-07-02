#!/usr/bin/env python3
"""Read-only yt-dlp URL probe via --dump-json (no media download)."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _yt_dlp_binary() -> str:
    binary = shutil.which("yt-dlp")
    if not binary:
        raise RuntimeError(
            "yt-dlp binary not found on PATH; install with pipx install yt-dlp or brew install yt-dlp"
        )
    return binary


def _validate_cookies(path: Path) -> None:
    if not path.is_file():
        raise ValueError(f"cookie file not found: {path}")
    if not path.is_absolute():
        raise ValueError(f"cookie path must be absolute: {path}")
    if not os_access_readable(path):
        raise ValueError(f"cookie file not readable: {path}")


def os_access_readable(path: Path) -> bool:
    try:
        with path.open("rb"):
            return True
    except OSError:
        return False


def _subtitle_summary(info: dict[str, Any]) -> dict[str, list[str]]:
    manual = sorted((info.get("subtitles") or {}).keys())
    automatic = sorted((info.get("automatic_captions") or {}).keys())
    return {"manual": manual, "automatic": automatic}


def _summarize_info(info: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": info.get("id"),
        "title": info.get("title"),
        "webpage_url": info.get("webpage_url") or info.get("original_url"),
        "duration": info.get("duration"),
        "uploader": info.get("uploader"),
        "channel": info.get("channel"),
        "upload_date": info.get("upload_date"),
        "live_status": info.get("live_status"),
        "availability": info.get("availability"),
        "extractor": info.get("extractor"),
        "extractor_key": info.get("extractor_key"),
        "format_id": info.get("format_id"),
        "ext": info.get("ext"),
        "subtitles": _subtitle_summary(info),
        "playlist_count": info.get("playlist_count"),
        "playlist_index": info.get("playlist_index"),
        "playlist_title": info.get("playlist_title"),
    }


def probe_url(
    url: str,
    *,
    cookies: Path | None = None,
    allow_playlist: bool = False,
    timeout: int = 120,
) -> dict[str, Any]:
    binary = _yt_dlp_binary()
    command = [
        binary,
        "--dump-json",
        "--no-download",
        "--no-warnings",
        "--no-progress",
    ]
    if not allow_playlist:
        command.append("--no-playlist")
    if cookies is not None:
        _validate_cookies(cookies)
        command.extend(["--cookies", str(cookies)])
    command.append(url)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"yt-dlp probe timed out after {timeout}s") from exc

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        detail = stderr or stdout or f"exit code {result.returncode}"
        raise RuntimeError(f"yt-dlp probe failed: {detail}")

    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("yt-dlp probe returned no JSON output")

    entries: list[dict[str, Any]] = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"yt-dlp returned invalid JSON: {exc}") from exc

    if len(entries) == 1:
        info = entries[0]
        return {
            "ok": True,
            "url": url,
            "entry_count": 1,
            "info": info,
            "summary": _summarize_info(info),
        }

    return {
        "ok": True,
        "url": url,
        "entry_count": len(entries),
        "entries": [_summarize_info(entry) for entry in entries],
        "info": entries[0],
        "summary": _summarize_info(entries[0]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only yt-dlp URL probe")
    parser.add_argument("--url", required=True, help="Video or playlist URL to probe")
    parser.add_argument(
        "--cookies",
        type=Path,
        default=None,
        help="Absolute path to user-owned Netscape cookies.txt",
    )
    parser.add_argument(
        "--allow-playlist",
        action="store_true",
        help="Allow playlist URLs to return multiple entries",
    )
    parser.add_argument("--format", choices=("json",), default="json")
    parser.add_argument("--timeout", type=int, default=120, help="Probe timeout in seconds")
    args = parser.parse_args(argv)

    if args.format != "json":
        print("Only --format json is supported", file=sys.stderr)
        return 2

    cookies: Path | None = None
    if args.cookies is not None:
        cookies = args.cookies.expanduser().resolve()

    try:
        payload = probe_url(
            args.url,
            cookies=cookies,
            allow_playlist=args.allow_playlist,
            timeout=args.timeout,
        )
    except (RuntimeError, ValueError) as exc:
        json.dump({"ok": False, "url": args.url, "error": str(exc)}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 1

    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())