#!/usr/bin/env python3
"""Parse git log output into structured JSON with conventional commit classification.

Usage:
    git log --oneline HEAD~10..HEAD | python commit-parser.py
    git log --format='%H %s' main..HEAD | python commit-parser.py
    python commit-parser.py --format=full < git-log-output.txt
    python commit-parser.py --input git-log-output.txt

Input: git log output (one commit per line, hash + subject minimum)
Output: JSON to stdout with classified commits
"""

import argparse
import json
import re
import sys

CONVENTIONAL_PATTERN = re.compile(
    r"^(?P<type>feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(?:\((?P<scope>[^)]+)\))?"
    r"(?P<breaking>!)?"
    r":\s*(?P<subject>.+)$"
)

ONELINE_PATTERN = re.compile(r"^(?P<hash>[0-9a-f]{7,40})\s+(?P<subject>.+)$")

FULL_PATTERN = re.compile(
    r"^commit\s+(?P<hash>[0-9a-f]{40})"
)

AUTHOR_PATTERN = re.compile(r"^Author:\s+(?P<author>.+)$")
DATE_PATTERN = re.compile(r"^Date:\s+(?P<date>.+)$")


def parse_conventional(subject: str) -> dict:
    """Parse a subject line for conventional commit format."""
    match = CONVENTIONAL_PATTERN.match(subject.strip())
    if match:
        return {
            "conventional": True,
            "type": match.group("type"),
            "scope": match.group("scope"),
            "breaking": match.group("breaking") == "!",
            "subject": match.group("subject").strip(),
        }
    return {
        "conventional": False,
        "type": "unknown",
        "scope": None,
        "breaking": False,
        "subject": subject.strip(),
    }


def parse_oneline(lines: list[str]) -> list[dict]:
    """Parse git log --oneline output."""
    commits = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = ONELINE_PATTERN.match(line)
        if match:
            h = match.group("hash")
            subj = match.group("subject")
            parsed = parse_conventional(subj)
            commits.append({
                "hash": h,
                "author": None,
                "date": None,
                "body": None,
                **parsed,
            })
        else:
            # Fallback: treat entire line as subject
            parsed = parse_conventional(line)
            commits.append({
                "hash": None,
                "author": None,
                "date": None,
                "body": None,
                **parsed,
            })
    return commits


def parse_full(text: str) -> list[dict]:
    """Parse git log (full format) output."""
    commits = []
    current = None
    body_lines = []

    for line in text.split("\n"):
        commit_match = FULL_PATTERN.match(line)
        if commit_match:
            if current:
                current["body"] = "\n".join(body_lines).strip() or None
                if current["body"] and "BREAKING CHANGE:" in current["body"]:
                    current["breaking"] = True
                commits.append(current)
            current = {
                "hash": commit_match.group("hash"),
                "author": None,
                "date": None,
                "body": None,
            }
            body_lines = []
            continue

        if current is None:
            continue

        author_match = AUTHOR_PATTERN.match(line)
        if author_match:
            current["author"] = author_match.group("author").strip()
            continue

        date_match = DATE_PATTERN.match(line)
        if date_match:
            current["date"] = date_match.group("date").strip()
            continue

        # Subject line (first non-empty indented line after headers)
        stripped = line.strip()
        if stripped and "subject" not in current:
            parsed = parse_conventional(stripped)
            current.update(parsed)
        elif stripped:
            body_lines.append(stripped)

    if current:
        current["body"] = "\n".join(body_lines).strip() or None
        if current.get("body") and "BREAKING CHANGE:" in current["body"]:
            current["breaking"] = True
        commits.append(current)

    return commits


def summarize(commits: list[dict]) -> dict:
    """Generate summary statistics."""
    types = {}
    for c in commits:
        t = c.get("type", "unknown")
        types[t] = types.get(t, 0) + 1

    conventional_count = sum(1 for c in commits if c.get("conventional"))
    breaking_count = sum(1 for c in commits if c.get("breaking"))

    return {
        "total_commits": len(commits),
        "conventional_count": conventional_count,
        "non_conventional_count": len(commits) - conventional_count,
        "breaking_count": breaking_count,
        "types": types,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Parse git log into structured JSON with conventional commit classification"
    )
    parser.add_argument(
        "--format",
        choices=["oneline", "full", "auto"],
        default="auto",
        help="Input format (default: auto-detect)",
    )
    parser.add_argument(
        "--input", "-i",
        help="Input file (default: stdin)",
    )
    args = parser.parse_args()

    if args.input:
        with open(args.input, encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()
    if not text.strip():
        json.dump({"commits": [], "summary": summarize([])}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return

    fmt = args.format
    if fmt == "auto":
        fmt = "full" if text.strip().startswith("commit ") else "oneline"

    if fmt == "full":
        commits = parse_full(text)
    else:
        commits = parse_oneline(text.strip().split("\n"))

    result = {
        "commits": commits,
        "summary": summarize(commits),
    }

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
