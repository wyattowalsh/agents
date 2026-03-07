#!/usr/bin/env python3
"""Parse textual cProfile/pstats output into structured JSON."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CPROFILE_HEADER_RE = re.compile(
    r"^\s*(\d+)\s+function\s+calls?\s+(?:\((\d+)\s+primitive\s+calls?\)\s+)?in\s+([\d.]+)\s+seconds"
)
CPROFILE_ROW_RE = re.compile(
    r"^\s*([\d/]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(.+)$"
)
PYSPY_RE = re.compile(
    r"^\s*([\d.]+)%\s+([\d.]+)s\s+(.+?)(?:\s+\((.+?):(\d+)\))?$"
)
PERF_RE = re.compile(
    r"^\s*([\d.]+)%\s+(\S+)\s+\[(\S+)\]\s+(.+)$"
)


def parse_cprofile(text: str) -> dict:
    """Parse cProfile/pstats cumulative or tottime output."""
    lines = text.strip().splitlines()
    header_info = {"total_calls": 0, "primitive_calls": 0, "total_time": 0.0}
    functions: list[dict] = []

    for line in lines:
        hm = CPROFILE_HEADER_RE.match(line)
        if hm:
            header_info["total_calls"] = int(hm.group(1))
            header_info["primitive_calls"] = int(hm.group(2) or hm.group(1))
            header_info["total_time"] = float(hm.group(3))
            continue

        rm = CPROFILE_ROW_RE.match(line)
        if rm:
            calls_str = rm.group(1)
            if "/" in calls_str:
                ncalls, pcalls = calls_str.split("/")
                calls = int(ncalls)
                primitive = int(pcalls)
            else:
                calls = int(calls_str)
                primitive = calls

            functions.append({
                "name": rm.group(6).strip(),
                "calls": calls,
                "primitive_calls": primitive,
                "total_time": float(rm.group(2)),
                "total_per_call": float(rm.group(3)),
                "cumulative_time": float(rm.group(4)),
                "cumulative_per_call": float(rm.group(5)),
            })

    functions.sort(key=lambda f: f["cumulative_time"], reverse=True)
    hotspots = functions[:10]

    return {
        "format": "cprofile",
        "header": header_info,
        "functions": functions,
        "hotspots": [
            {
                "rank": i + 1,
                "name": f["name"],
                "cumulative_time": f["cumulative_time"],
                "calls": f["calls"],
                "time_per_call": f["cumulative_per_call"],
                "category": _categorize(f),
            }
            for i, f in enumerate(hotspots)
        ],
        "total_functions": len(functions),
    }


def parse_pyspy(text: str) -> dict:
    """Parse py-spy top-like output."""
    functions: list[dict] = []
    for line in text.strip().splitlines():
        m = PYSPY_RE.match(line)
        if m:
            functions.append({
                "name": m.group(3).strip(),
                "percent": float(m.group(1)),
                "total_time": float(m.group(2)),
                "file": m.group(4) or "",
                "line": int(m.group(5)) if m.group(5) else 0,
            })
    functions.sort(key=lambda f: f["percent"], reverse=True)
    return {
        "format": "py-spy",
        "functions": functions,
        "hotspots": [
            {"rank": i + 1, "name": f["name"], "percent": f["percent"],
             "total_time": f["total_time"], "file": f["file"]}
            for i, f in enumerate(functions[:10])
        ],
        "total_functions": len(functions),
    }


def parse_perf(text: str) -> dict:
    """Parse Linux perf report output."""
    functions: list[dict] = []
    for line in text.strip().splitlines():
        m = PERF_RE.match(line)
        if m:
            functions.append({
                "name": m.group(4).strip(),
                "percent": float(m.group(1)),
                "command": m.group(2),
                "shared_object": m.group(3),
            })
    functions.sort(key=lambda f: f["percent"], reverse=True)
    return {
        "format": "perf",
        "functions": functions,
        "hotspots": [
            {"rank": i + 1, "name": f["name"], "percent": f["percent"],
             "command": f["command"]}
            for i, f in enumerate(functions[:10])
        ],
        "total_functions": len(functions),
    }


def _categorize(func: dict) -> str:
    """Categorize a function as CPU-bound, I/O-bound, or overhead."""
    name = func["name"].lower()
    if any(kw in name for kw in ("read", "write", "send", "recv", "socket", "open", "close", "wait", "sleep")):
        return "io-bound"
    if func["calls"] > 1000 and func["total_per_call"] < 0.0001:
        return "overhead"
    return "cpu-bound"


def detect_format(text: str) -> str:
    """Auto-detect profiler output format."""
    if CPROFILE_HEADER_RE.search(text) or "ncalls" in text[:500]:
        return "cprofile"
    if "py-spy" in text[:200] or PYSPY_RE.search(text):
        return "pyspy"
    if "perf report" in text[:200] or PERF_RE.search(text):
        return "perf"
    return "cprofile"


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse profiler output to structured JSON")
    parser.add_argument("--input", "-i", required=True, help="Path to profiler output file")
    parser.add_argument("--format", "-f", choices=["cprofile", "pyspy", "perf", "auto"],
                        default="auto", help="Profiler output format (default: auto-detect)")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(json.dumps({"error": f"File not found: {args.input}"}))
        sys.exit(1)

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        msg = f"Binary file detected: {args.input}. This tool parses textual profiler output only."
        print(json.dumps({"error": msg}))
        sys.exit(1)
    fmt = args.format if args.format != "auto" else detect_format(text)

    parsers = {"cprofile": parse_cprofile, "pyspy": parse_pyspy, "perf": parse_perf}
    result = parsers[fmt](text)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
