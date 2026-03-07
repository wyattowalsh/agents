#!/usr/bin/env python3
"""Summarize git diff statistics for PR descriptions.

Usage:
    git diff --stat | python diff-summarizer.py
    git diff main...HEAD --stat | python diff-summarizer.py
    python diff-summarizer.py < diff-stat-output.txt

Input: git diff --stat output
Output: JSON to stdout with structured change summary
"""

import json
import re
import sys

STAT_LINE_PATTERN = re.compile(
    r"^\s*(?P<path>.+?)\s*\|\s*(?P<changes>\d+)\s*(?P<chart>[+-]*)\s*$"
)

BINARY_PATTERN = re.compile(
    r"^\s*(?P<path>.+?)\s*\|\s*Bin\s+(?P<before>\d+)\s*->\s*(?P<after>\d+)\s+bytes\s*$"
)

SUMMARY_PATTERN = re.compile(
    r"^\s*(?P<files>\d+)\s+files?\s+changed"
    r"(?:,\s*(?P<insertions>\d+)\s+insertions?\(\+\))?"
    r"(?:,\s*(?P<deletions>\d+)\s+deletions?\(-\))?"
)

RENAME_PATTERN = re.compile(r"\{(.+?) => (.+?)\}|(.+) => (.+)")


def classify_change(path: str, insertions: int, deletions: int) -> str:
    """Classify the type of change based on insertions/deletions ratio."""
    total = insertions + deletions
    if total == 0:
        return "unchanged"
    if insertions > 0 and deletions == 0:
        return "added"
    if deletions > 0 and insertions == 0:
        return "deleted"
    ratio = insertions / total
    if ratio > 0.8:
        return "mostly_added"
    if ratio < 0.2:
        return "mostly_deleted"
    return "modified"


def classify_file_type(path: str) -> str:
    """Classify file by its type/purpose."""
    path_lower = path.lower()

    if any(p in path_lower for p in ["test", "spec", "__test__", ".test.", "_test."]):
        return "test"
    if any(p in path_lower for p in [".md", "readme", "docs/", "doc/"]):
        return "documentation"
    if any(p in path_lower for p in [
        ".yml", ".yaml", ".toml", ".json", ".ini", ".cfg", ".conf", ".env",
        "dockerfile", ".docker", "makefile", ".github/", ".gitlab-ci",
        "jenkinsfile", ".circleci",
    ]):
        return "configuration"
    if any(p in path_lower for p in [
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "uv.lock",
        "poetry.lock", "cargo.lock", "go.sum", "gemfile.lock",
    ]):
        return "lockfile"
    return "source"


def parse_stat_line(line: str) -> dict | None:
    """Parse a single stat line."""
    binary_match = BINARY_PATTERN.match(line)
    if binary_match:
        return {
            "path": binary_match.group("path").strip(),
            "binary": True,
            "before_bytes": int(binary_match.group("before")),
            "after_bytes": int(binary_match.group("after")),
            "insertions": 0,
            "deletions": 0,
            "change_type": "binary",
            "file_type": classify_file_type(binary_match.group("path").strip()),
        }

    stat_match = STAT_LINE_PATTERN.match(line)
    if stat_match:
        path = stat_match.group("path").strip()
        chart = stat_match.group("chart")
        insertions = chart.count("+")
        deletions = chart.count("-")
        return {
            "path": path,
            "binary": False,
            "insertions": insertions,
            "deletions": deletions,
            "change_type": classify_change(path, insertions, deletions),
            "file_type": classify_file_type(path),
        }

    return None


def generate_summary(files: list[dict], total_insertions: int, total_deletions: int) -> str:
    """Generate a human-readable summary of the changes."""
    if not files:
        return "No changes detected."

    parts = []

    # Group by file type
    by_type: dict[str, list[dict]] = {}
    for f in files:
        ft = f["file_type"]
        by_type.setdefault(ft, []).append(f)

    type_order = ["source", "test", "configuration", "documentation", "lockfile"]
    for ft in type_order:
        group = by_type.get(ft, [])
        if group:
            parts.append(f"{len(group)} {ft} file{'s' if len(group) != 1 else ''}")

    # Overall character
    if total_insertions > total_deletions * 3:
        character = "primarily additive (new code)"
    elif total_deletions > total_insertions * 3:
        character = "primarily subtractive (cleanup/removal)"
    elif total_insertions > 0 and total_deletions > 0:
        character = "mixed modifications"
    else:
        character = "minimal changes"

    summary = f"Changes across {len(files)} files ({', '.join(parts)}). {character.capitalize()}."
    return summary


def main():
    text = sys.stdin.read()
    if not text.strip():
        json.dump({
            "files_changed": 0,
            "insertions": 0,
            "deletions": 0,
            "files": [],
            "summary": "No changes detected.",
        }, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return

    files = []
    total_insertions = 0
    total_deletions = 0

    for line in text.strip().split("\n"):
        # Check for summary line
        summary_match = SUMMARY_PATTERN.match(line)
        if summary_match:
            total_insertions = int(summary_match.group("insertions") or 0)
            total_deletions = int(summary_match.group("deletions") or 0)
            continue

        parsed = parse_stat_line(line)
        if parsed:
            files.append(parsed)

    # If no summary line was found, sum from individual files
    if total_insertions == 0 and total_deletions == 0:
        total_insertions = sum(f["insertions"] for f in files)
        total_deletions = sum(f["deletions"] for f in files)

    result = {
        "files_changed": len(files),
        "insertions": total_insertions,
        "deletions": total_deletions,
        "files": files,
        "summary": generate_summary(files, total_insertions, total_deletions),
    }

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
