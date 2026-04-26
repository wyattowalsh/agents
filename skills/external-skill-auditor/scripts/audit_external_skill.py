#!/usr/bin/env python3
"""Static first-pass audit for local Agent Skill directories.

Outputs JSON to stdout and warnings to stderr. This scanner intentionally does
not execute candidate scripts or commands.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


RISK_PATTERNS: list[tuple[str, str, str]] = [
    ("destructive", r"\brm\s+-rf\b|\bgit\s+reset\b|\bgit\s+clean\b|\bsudo\b", "high"),
    ("network", r"\bcurl\b|\bwget\b|\bfetch\b|https?://", "medium"),
    ("package-install", r"\bnpm\s+install\b|\bpip\s+install\b|\buv\s+add\b|\bbun\s+install\b", "medium"),
    ("credential", r"\b[A-Z0-9_]*(TOKEN|SECRET|KEY|PASSWORD|CREDENTIAL)[A-Z0-9_]*\b|\.env\b", "high"),
    ("home-write", r"~/|/Users/|/home/", "medium"),
    ("github-write", r"\bgh\s+(api|pr|repo|workflow)\b", "medium"),
    ("chmod", r"\bchmod\b|\bchown\b", "medium"),
]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"warning: failed to read {path}: {exc}", file=sys.stderr)
        return ""


def scan_file(path: Path, root: Path) -> list[dict[str, object]]:
    text = read_text(path)
    findings: list[dict[str, object]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for kind, pattern, severity in RISK_PATTERNS:
            if re.search(pattern, line, flags=re.IGNORECASE):
                findings.append(
                    {
                        "kind": kind,
                        "severity": severity,
                        "file": str(path.relative_to(root)),
                        "line": line_no,
                        "excerpt": line.strip()[:180],
                    }
                )
    return findings


def audit_skill(path: Path) -> dict[str, object]:
    root = path.resolve()
    if root.is_file():
        root = root.parent

    skill_file = root / "SKILL.md"
    files = [p for p in root.rglob("*") if p.is_file()]
    findings: list[dict[str, object]] = []
    for file_path in files:
        if file_path.name.startswith("."):
            continue
        findings.extend(scan_file(file_path, root))

    scripts = sorted(str(p.relative_to(root)) for p in (root / "scripts").rglob("*") if p.is_file()) if (root / "scripts").is_dir() else []
    hooks_present = "hooks:" in read_text(skill_file) if skill_file.exists() else False
    allowed_tools_present = "allowed-tools:" in read_text(skill_file) if skill_file.exists() else False

    high = sum(1 for f in findings if f["severity"] == "high")
    medium = sum(1 for f in findings if f["severity"] == "medium")
    if high:
        recommendation = "inspect then install"
    elif medium or scripts or hooks_present or allowed_tools_present:
        recommendation = "inspect then install"
    else:
        recommendation = "no static blockers"

    return {
        "path": str(root),
        "skill_file_exists": skill_file.exists(),
        "files_scanned": len(files),
        "scripts": scripts,
        "hooks_present": hooks_present,
        "allowed_tools_present": allowed_tools_present,
        "finding_counts": {"high": high, "medium": medium, "total": len(findings)},
        "findings": findings,
        "recommendation": recommendation,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Static first-pass audit for an Agent Skill directory")
    parser.add_argument("path", help="Path to a skill directory or SKILL.md")
    args = parser.parse_args()

    report = audit_skill(Path(args.path))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
