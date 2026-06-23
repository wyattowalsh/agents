#!/usr/bin/env python3
"""Normalize review findings into structured JSON for Judge reconciliation.

Reads finding text from stdin, outputs a JSON array to stdout.
Supports block format (Individual Finding Format), compact format, and JSON input.

Usage:
  cat findings.txt | python finding-formatter.py [--mode session|audit]
  python finding-formatter.py --input findings.json [--mode audit]
  cat findings.json | python finding-formatter.py --input - [--mode session]
"""

import argparse
import json
import re
import sys
from typing import Any

# Block:
#   "P0 — src/auth.py:45 Security"
#   "P0 — RV-S-005 src/auth.py:45-52 Security"
FINDING_ID = re.compile(r"^RV-[A-Z]+-\d{3}$")
BLOCK_HDR = re.compile(
    r"^([PS]\d)\s*[—\-]+\s+"
    r"(?:(RV-[A-Z]+-\d{3})\s+)?"
    r"(\S+?)(?::(\d+(?:-\d+)?))?\s+(.+?)\s*$"
)
FIELD = re.compile(
    r"^\s+(Level|Confidence|Description|Evidence|Impact|Fix|Effort|Reasoning):\s*(.+)$",
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
            loc = f"{m[3]}:{m[4]}" if m[4] else m[3]
            cur = {"priority": m[1], "location": loc, "category": m[5].strip()}
            if m[2]:
                cur["source_id"] = m[2]
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


_CITE_RANGE = re.compile(r":(\d+)-(\d+)$")


def _validate_citation_anchor(location: str) -> None:
    """Warn to stderr if a file:start-end citation has invalid range values."""
    m = _CITE_RANGE.search(location)
    if not m:
        return
    start, end = int(m[1]), int(m[2])
    if start <= 0 or end <= 0:
        print(
            f"Warning: non-positive line numbers in citation '{location}' (start={start}, end={end})",
            file=sys.stderr,
        )
    elif start > end:
        print(
            f"Warning: start > end in citation '{location}' (start={start}, end={end})",
            file=sys.stderr,
        )


_KNOWN_KEYS = {
    "id",
    "source_id",
    "priority",
    "location",
    "category",
    "level",
    "confidence",
    "description",
    "evidence",
    "impact",
    "fix",
    "effort",
    "reasoning",
}


def _coerce_confidence(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and _is_float(value):
        return float(value)
    return None


def normalize(f: dict[str, Any], fid: str) -> dict[str, Any]:
    location = f.get("location", "").strip("[] ")
    _validate_citation_anchor(location)
    source_id = f.get("source_id")
    if not source_id and isinstance(f.get("id"), str) and FINDING_ID.match(f["id"]):
        source_id = f["id"]
    out: dict[str, Any] = {
        "id": fid,
        "priority": f.get("priority", ""),
        "location": location,
        "category": f.get("category", ""),
        "level": f.get("level", ""),
        "confidence": _coerce_confidence(f.get("confidence")),
        "description": f.get("description", ""),
        "evidence": f.get("evidence", ""),
        "impact": f.get("impact", ""),
        "fix": f.get("fix", ""),
        "effort": f.get("effort", ""),
        "reasoning": f.get("reasoning") or None,
    }
    if source_id:
        out["source_id"] = source_id
    # Preserve unknown keys for forward compatibility.
    for key, val in f.items():
        if key not in _KNOWN_KEYS:
            out[key] = val
    return out


def make_id(mode: str, seq: int) -> str:
    prefix_map = {
        "audit": "A",
        "pr": "PR",
        "range": "R",
        "source": "SRC",
        "simplify": "SIM",
    }
    prefix = prefix_map.get(mode, "S")
    return f"RV-{prefix}-{seq:03d}"


def _sarif_level(priority: str) -> str:
    return {
        "P0": "error",
        "S0": "error",
        "P1": "warning",
        "S1": "warning",
        "P2": "note",
        "S2": "note",
        "P3": "note",
        "S3": "note",
    }.get(priority, "note")


def _sarif_rank(confidence: Any) -> int:
    value = _coerce_confidence(confidence)
    if value is None:
        value = 0.5
    return max(0, min(100, int(value * 100)))


def _sarif_location(location: str) -> dict[str, Any] | None:
    if not location:
        return None
    if ":" not in location:
        return {
            "physicalLocation": {
                "artifactLocation": {"uri": location},
                "region": {"startLine": 1},
            }
        }
    path, raw_line = location.rsplit(":", 1)
    raw_start = raw_line.split("-", 1)[0]
    try:
        start_line = int(raw_start)
    except ValueError:
        raise SystemExit(f"Invalid SARIF location line in '{location}'") from None
    return {
        "physicalLocation": {
            "artifactLocation": {"uri": path},
            "region": {"startLine": max(1, start_line)},
        }
    }


def _json_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "ReviewFinding",
        "description": "Pre-Judge normalized finding object; final review findings add the full finding-contract fields.",
        "type": "object",
        "required": ["id", "priority", "location", "description"],
        "properties": {
            "id": {"type": "string", "pattern": r"^RV-[A-Z]+-\d{3}$"},
            "source_id": {"type": "string"},
            "priority": {"type": "string", "pattern": r"^[PS]\d$"},
            "location": {"type": "string"},
            "category": {"type": "string"},
            "level": {"type": "string"},
            "confidence": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
            "description": {"type": "string"},
            "evidence": {"type": "string"},
            "impact": {"type": "string"},
            "fix": {"type": "string"},
            "effort": {"type": "string"},
            "reasoning": {"type": ["string", "null"]},
        },
        "additionalProperties": True,
    }


def load_json_input(source: str) -> list[dict[str, Any]]:
    """Load findings from a JSON file path or stdin (when source is '-').

    Expects either a JSON array of finding objects or a single finding object.
    Returns an empty list for empty input.
    """
    if source == "-":
        raw = sys.stdin.read()
    else:
        with open(source) as fh:
            raw = fh.read()
    if not raw or not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON input: {exc}") from None
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise SystemExit("JSON input must be an array of finding objects or a single object.")
    return data


def main() -> None:
    ap = argparse.ArgumentParser(description="Normalize review findings to JSON.")
    ap.add_argument(
        "--mode",
        choices=["session", "audit", "pr", "range", "source", "simplify"],
        default="session",
    )
    ap.add_argument(
        "--input",
        metavar="PATH",
        default=None,
        help="Path to a JSON file of findings, or '-' for stdin JSON.",
    )
    ap.add_argument(
        "--format",
        choices=["json", "sarif", "json-schema", "conventional"],
        default="json",
        dest="output_format",
        help=(
            "Output format: json (default), sarif (SARIF v2.1), "
            "json-schema (verbose schema), conventional (human-readable)."
        ),
    )
    args = ap.parse_args()

    # JSON input mode — bypass text parsing entirely.
    if args.input is not None:
        findings = load_json_input(args.input)
        out = [normalize(f, make_id(args.mode, i + 1)) for i, f in enumerate(findings)]
    else:
        # Text input mode (original behavior).
        raw = sys.stdin.read()
        if not raw.strip():
            json.dump([], sys.stdout, indent=2)
            print()
            return
        lines = raw.splitlines()
        findings = parse_blocks(lines)
        if not findings:
            findings = parse_compact(lines)
        elif any(COMPACT.match(ln.strip()) for ln in lines if not BLOCK_HDR.match(ln)):
            findings.extend(parse_compact([ln for ln in lines if not BLOCK_HDR.match(ln) and not FIELD.match(ln)]))
        out = [normalize(f, make_id(args.mode, i + 1)) for i, f in enumerate(findings)]

    if args.output_format == "json-schema":
        json.dump(_json_schema(), sys.stdout, indent=2)
        print()
        return

    if args.output_format == "conventional":
        LABEL_MAP = {
            "P0": "issue (blocking)",
            "S0": "issue (blocking)",
            "P1": "issue (non-blocking)",
            "S1": "issue (non-blocking)",
            "P2": "suggestion (non-blocking)",
            "S2": "suggestion (non-blocking)",
            "P3": "nitpick (if-minor)",
            "S3": "nitpick (if-minor)",
        }
        for f in out:
            priority = f.get("priority", "")
            label = LABEL_MAP.get(priority, "finding")
            decoration = f.get("category", "") or f.get("level", "") or priority
            fid = f.get("id", "")
            location = f.get("location", "")
            level = f.get("level", "") or priority
            confidence = f.get("confidence")
            confidence_str = f"{confidence}" if confidence is not None else "N/A"
            reasoning = f.get("reasoning") or "N/A"
            description = f.get("description", "")
            evidence = f.get("evidence", "") or "N/A"
            fix = f.get("fix", "") or "N/A"
            print(f"{label} ({decoration}): {description}")
            print()
            print(f"**[{fid}]** [{location}] | Level: {level} | Confidence: {confidence_str}")
            print()
            print(f"**Reasoning:** {reasoning}")
            print()
            print(f"**Finding:** {description}")
            print()
            print(f"**Evidence:** {evidence}")
            print(f"**Fix:** {fix}")
            print()
        return

    if args.output_format == "sarif":
        sarif = {
            "version": "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/sarif-2.1/schema/sarif-schema-2.1.0.json",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "review",
                            "version": "5.0",
                            "informationUri": "https://github.com/wyattowalsh/agents",
                            "rules": [
                                {"id": f["id"], "shortDescription": {"text": f.get("description", "")[:200]}}
                                for f in out
                            ],
                        }
                    },
                    "results": [
                        {
                            "ruleId": f["id"],
                            "level": _sarif_level(f.get("priority", "")),
                            "message": {"text": f.get("description", "")},
                            "locations": [_sarif_location(f.get("location", ""))]
                            if _sarif_location(f.get("location", ""))
                            else [],
                            "rank": _sarif_rank(f.get("confidence")),
                        }
                        for f in out
                    ],
                }
            ],
        }
        json.dump(sarif, sys.stdout, indent=2)
    else:
        json.dump(out, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
