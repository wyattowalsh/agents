#!/usr/bin/env python3
"""Run ffprobe and emit normalized JSON for a local media file."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _fail(message: str, *, code: int = 1) -> int:
    print(message, file=sys.stderr)
    return code


def _ffprobe_path() -> str | None:
    return shutil.which("ffprobe")


def _run_ffprobe(path: Path) -> dict[str, Any]:
    ffprobe = _ffprobe_path()
    if not ffprobe:
        raise RuntimeError("ffprobe not found on PATH; install ffmpeg")

    command = [
        ffprobe,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "ffprobe failed").strip()
        raise RuntimeError(detail)

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ffprobe returned invalid JSON: {exc}") from exc

    return payload


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_frame_rate(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        if "/" in value:
            num, den = value.split("/", 1)
            try:
                numerator = float(num)
                denominator = float(den)
            except ValueError:
                return None
            return numerator / denominator if denominator else None
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _summarize(payload: dict[str, Any]) -> dict[str, Any]:
    fmt = payload.get("format") or {}
    streams = payload.get("streams") or []

    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    subtitle_streams = [s for s in streams if s.get("codec_type") == "subtitle"]

    duration = fmt.get("duration")
    try:
        duration_seconds = float(duration) if duration is not None else None
    except (TypeError, ValueError):
        duration_seconds = None

    primary_video = video_streams[0] if video_streams else None
    primary_audio = audio_streams[0] if audio_streams else None

    summary: dict[str, Any] = {
        "path": fmt.get("filename"),
        "format_name": fmt.get("format_name"),
        "format_long_name": fmt.get("format_long_name"),
        "duration_seconds": duration_seconds,
        "size_bytes": int(fmt.get("size")) if fmt.get("size") is not None else None,
        "bit_rate": int(fmt.get("bit_rate")) if fmt.get("bit_rate") is not None else None,
        "stream_counts": {
            "video": len(video_streams),
            "audio": len(audio_streams),
            "subtitle": len(subtitle_streams),
            "total": len(streams),
        },
    }

    if primary_video:
        r_frame_rate = primary_video.get("r_frame_rate")
        summary["video"] = {
            "codec": primary_video.get("codec_name"),
            "profile": primary_video.get("profile"),
            "width": _int_or_none(primary_video.get("width")),
            "height": _int_or_none(primary_video.get("height")),
            "pix_fmt": primary_video.get("pix_fmt"),
            "avg_frame_rate": primary_video.get("avg_frame_rate"),
            "r_frame_rate": r_frame_rate,
            "r_frame_rate_fps": _parse_frame_rate(r_frame_rate),
            "bit_rate": _int_or_none(primary_video.get("bit_rate")),
        }

    if primary_audio:
        summary["audio"] = {
            "codec": primary_audio.get("codec_name"),
            "sample_rate": _int_or_none(primary_audio.get("sample_rate")),
            "channels": _int_or_none(primary_audio.get("channels")),
            "channel_layout": primary_audio.get("channel_layout"),
            "bit_rate": _int_or_none(primary_audio.get("bit_rate")),
        }

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe a media file with ffprobe JSON output")
    parser.add_argument("file", type=Path, help="Path to local audio/video file")
    parser.add_argument(
        "--format",
        choices=("json",),
        default="json",
        help="Output format (json only)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Emit raw ffprobe JSON without summary wrapper",
    )
    args = parser.parse_args(argv)

    if args.format != "json":
        return _fail("Only --format json is supported", code=2)

    path = args.file.expanduser()
    if not path.is_file():
        return _fail(f"File not found: {path}")

    try:
        payload = _run_ffprobe(path.resolve())
    except RuntimeError as exc:
        return _fail(str(exc))

    if args.raw:
        json.dump(payload, sys.stdout, indent=2)
    else:
        report = {
            "ok": True,
            "file": str(path.resolve()),
            "summary": _summarize(payload),
            "ffprobe": payload,
        }
        json.dump(report, sys.stdout, indent=2)

    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())