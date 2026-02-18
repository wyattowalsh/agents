#!/usr/bin/env python3
"""Normalize honest-review findings into structured JSON for Judge reconciliation.

Reads finding text from stdin, outputs a JSON array to stdout.
Supports block format (Individual Finding Format) and compact format.

Usage: cat findings.txt | python finding-formatter.py [--mode session|audit]
"""
import argparse, json, re, sys
from typing import Any

# Block: "P0 — src/auth.py:45 Security"
BLOCK_HDR = re.compile(
    r"^([PS]\d)\s*[—\-]+\s*(\S+?)(?::(\d+))?\s+(.+?)\s*$"
)
FIELD = re.compile(
    r"^\s+(Level|Confidence|Description|Evidence|Impact|Fix|Effort):\s*(.+)$",
    re.IGNORECASE,
)
# Compact: "P1: [file:line] desc — evidence: cite. Fix: approach. (Level)"
COMPACT = re.compile(
    r"^([PS]\d):\s*\[([^\]]+)\]\s*(.+?)\s*"
    r"(?:[—\-]+\s*evidence:\s*(.+?))?"
    r"(?:\.\s*Fix:\s*(.+?))?"
    r"(?:\.\s*\((\w+)\))?\s*$"
)


def parse_blocks(lines: list[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    for line in lines:
        m = BLOCK_HDR.match(line)
        if m:
            if cur:
                findings.append(cur)
            loc = f"{m[2]}:{m[3]}" if m[3] else m[2]
            cur = {"priority": m[1], "location": loc, "category": m[4].strip()}
            continue
        if cur is None:
            continue
        fm = FIELD.match(line)
        if fm:
            key, val = fm[1].lower(), fm[2].strip()
            cur[key] = float(val) if key == "confidence" and _is_float(val) else val
    if cur:
        findings.append(cur)
    return findings


def parse_compact(lines: list[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for line in lines:
        m = COMPACT.match(line.strip())
        if not m:
            continue
        f: dict[str, Any] = {"priority": m[1], "location": m[2].strip()}
        if m[3]:
            f["description"] = m[3].strip().rstrip("—-").strip()
        if m[4]:
            f["evidence"] = m[4].strip().rstrip(".")
        if m[5]:
            f["fix"] = m[5].strip().rstrip(".")
        if m[6]:
            f["level"] = m[6].strip()
        findings.append(f)
    return findings


def _is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def normalize(f: dict[str, Any], fid: str) -> dict[str, Any]:
    return {
        "id": fid,
        "priority": f.get("priority", ""),
        "location": f.get("location", "").strip("[] "),
        "category": f.get("category", ""),
        "level": f.get("level", ""),
        "confidence": f.get("confidence") if isinstance(f.get("confidence"), float) else None,
        "description": f.get("description", ""),
        "evidence": f.get("evidence", ""),
        "impact": f.get("impact", ""),
        "fix": f.get("fix", ""),
        "effort": f.get("effort", ""),
    }


def make_id(mode: str, seq: int) -> str:
    prefix = "A" if mode == "audit" else "S"
    return f"HR-{prefix}-{seq:03d}"


def main() -> None:
    ap = argparse.ArgumentParser(description="Normalize review findings to JSON.")
    ap.add_argument("--mode", choices=["session", "audit"], default="session")
    args = ap.parse_args()

    raw = sys.stdin.read()
    if not raw.strip():
        json.dump([], sys.stdout, indent=2)
        print()
        return

    lines = raw.splitlines()
    findings = parse_blocks(lines)
    if not findings:
        findings = parse_compact(lines)
    # Mixed input: also capture compact lines interleaved with block findings
    elif any(COMPACT.match(l.strip()) for l in lines if not BLOCK_HDR.match(l)):
        findings.extend(parse_compact(
            [l for l in lines if not BLOCK_HDR.match(l) and not FIELD.match(l)]
        ))

    out = [normalize(f, make_id(args.mode, i + 1)) for i, f in enumerate(findings)]
    json.dump(out, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
