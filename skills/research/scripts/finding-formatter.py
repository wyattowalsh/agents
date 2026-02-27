#!/usr/bin/env python3
"""Normalize research findings into structured JSON for the research skill.

Reads raw findings from stdin or a file, normalizes them with IDs and
validation, and outputs in JSON, Markdown, or HTML format.

Usage:
  cat findings.json | python finding-formatter.py
  python finding-formatter.py --input findings.json --format markdown
  python finding-formatter.py --input - --format html
  echo '[{"claim":"test","confidence":0.8,"evidence":[]}]' | python finding-formatter.py
"""
import argparse
import html
import json
import sys
from typing import Any


def load_findings(source: str | None) -> list[dict[str, Any]]:
    """Load raw findings from a file path, stdin ('-' or None)."""
    if source is None or source == "-":
        raw = sys.stdin.read()
    else:
        try:
            with open(source) as fh:
                raw = fh.read()
        except FileNotFoundError:
            print(f"Error: file not found: {source}", file=sys.stderr)
            sys.exit(1)
        except OSError as exc:
            print(f"Error reading file: {exc}", file=sys.stderr)
            sys.exit(1)

    if not raw or not raw.strip():
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON input: {exc}", file=sys.stderr)
        sys.exit(1)

    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        print("Error: JSON input must be an array of finding objects or a single object.", file=sys.stderr)
        sys.exit(1)
    return data


def validate_finding(finding: dict[str, Any], index: int) -> list[str]:
    """Validate a raw finding and return a list of warnings."""
    warnings: list[str] = []
    if not finding.get("claim"):
        warnings.append(f"Finding {index}: missing required field 'claim'")
    conf = finding.get("confidence")
    if conf is None:
        warnings.append(f"Finding {index}: missing required field 'confidence'")
    elif not isinstance(conf, (int, float)) or conf < 0.0 or conf > 1.0:
        warnings.append(f"Finding {index}: 'confidence' must be a number between 0.0 and 1.0, got {conf}")
    evidence = finding.get("evidence")
    if not evidence or not isinstance(evidence, list) or len(evidence) == 0:
        warnings.append(f"Finding {index}: must have at least 1 evidence item")
    return warnings


def normalize_finding(finding: dict[str, Any], seq: int) -> dict[str, Any]:
    """Normalize a raw finding into the output schema with an assigned ID."""
    evidence = finding.get("evidence", [])
    if not isinstance(evidence, list):
        evidence = []
    evidence = [e for e in evidence if isinstance(e, dict)]

    raw_conf = finding.get("confidence")
    conf = max(0.0, min(1.0, float(raw_conf))) if isinstance(raw_conf, (int, float)) else 0.0

    return {
        "id": f"RR-{seq:03d}",
        "claim": finding.get("claim", ""),
        "confidence": conf,
        "evidence": evidence,
        "cross_validation": finding.get("cross_validation", "unknown"),
        "bias_markers": finding.get("bias_markers", []),
        "gaps": finding.get("gaps", []),
        "source_count": len(evidence),
    }


def format_json(findings: list[dict[str, Any]]) -> str:
    return json.dumps(findings, indent=2)


def format_markdown(findings: list[dict[str, Any]]) -> str:
    """Format findings using the evidence chain template from SKILL.md."""
    lines: list[str] = []
    for f in findings:
        lines.append(f"FINDING {f['id']}: {f['claim']}")
        lines.append(f"  CONFIDENCE: {f['confidence']}")
        lines.append("  EVIDENCE:")
        for i, ev in enumerate(f["evidence"], 1):
            tool = ev.get("tool", "unknown")
            url = ev.get("url", "N/A")
            ts = ev.get("timestamp", "N/A")
            excerpt = ev.get("excerpt", "N/A")
            lines.append(f"    {i}. [{tool}] {url} [{ts}] -- {excerpt}")
        cv = f.get("cross_validation", "unknown")
        sc = f.get("source_count", 0)
        lines.append(f"  CROSS-VALIDATION: {cv} across {sc} independent sources")
        bias = f.get("bias_markers", [])
        lines.append(f"  BIAS MARKERS: {', '.join(bias) if bias else 'none'}")
        gaps = f.get("gaps", [])
        lines.append(f"  GAPS: {', '.join(gaps) if gaps else 'none'}")
        lines.append("")
    return "\n".join(lines)


def format_html(findings: list[dict[str, Any]]) -> str:
    """Format findings as an HTML table."""
    rows: list[str] = []
    rows.append("<table>")
    rows.append("  <thead>")
    rows.append("    <tr>")
    rows.append("      <th>ID</th>")
    rows.append("      <th>Claim</th>")
    rows.append("      <th>Confidence</th>")
    rows.append("      <th>Sources</th>")
    rows.append("      <th>Cross-Validation</th>")
    rows.append("      <th>Bias Markers</th>")
    rows.append("      <th>Gaps</th>")
    rows.append("    </tr>")
    rows.append("  </thead>")
    rows.append("  <tbody>")
    for f in findings:
        fid = html.escape(f["id"])
        claim = html.escape(f["claim"])
        conf = f["confidence"]
        sc = f["source_count"]
        cv = html.escape(str(f.get("cross_validation", "unknown")))
        bias = html.escape(", ".join(f.get("bias_markers", [])) or "none")
        gaps = html.escape(", ".join(f.get("gaps", [])) or "none")
        rows.append("    <tr>")
        rows.append(f"      <td>{fid}</td>")
        rows.append(f"      <td>{claim}</td>")
        rows.append(f"      <td>{conf:.2f}</td>")
        rows.append(f"      <td>{sc}</td>")
        rows.append(f"      <td>{cv}</td>")
        rows.append(f"      <td>{bias}</td>")
        rows.append(f"      <td>{gaps}</td>")
        rows.append("    </tr>")
    rows.append("  </tbody>")
    rows.append("</table>")
    return "\n".join(rows)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Normalize research findings into structured JSON. "
        "Assigns IDs (RR-001, RR-002, ...), validates required fields, "
        "and sorts by confidence descending.",
    )
    ap.add_argument(
        "--input",
        metavar="PATH",
        default=None,
        help="Path to a JSON file of raw findings, or '-' for stdin (default: stdin).",
    )
    ap.add_argument(
        "--format",
        choices=["json", "markdown", "html"],
        default="json",
        dest="output_format",
        help="Output format: json (default), markdown (evidence chain template), html (table).",
    )
    args = ap.parse_args()

    raw_findings = load_findings(args.input)

    if not raw_findings:
        if args.output_format == "json":
            print("[]")
        return

    # Validate and warn
    for i, f in enumerate(raw_findings, 1):
        warnings = validate_finding(f, i)
        for w in warnings:
            print(f"Warning: {w}", file=sys.stderr)

    # Normalize
    normalized = [normalize_finding(f, i) for i, f in enumerate(raw_findings, 1)]

    # Sort by confidence descending
    normalized.sort(key=lambda f: f["confidence"], reverse=True)

    # Re-assign IDs after sorting
    for i, f in enumerate(normalized, 1):
        f["id"] = f"RR-{i:03d}"

    # Output
    if args.output_format == "json":
        print(format_json(normalized))
    elif args.output_format == "markdown":
        print(format_markdown(normalized))
    elif args.output_format == "html":
        print(format_html(normalized))


if __name__ == "__main__":
    main()
