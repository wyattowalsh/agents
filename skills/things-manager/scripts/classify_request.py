#!/usr/bin/env python3
"""Classify Things Manager requests into initial mode and risk hints."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    mode: str
    risk: str
    pattern: re.Pattern[str]


RULES = [
    Rule("Quick Entry Handoff", "read-only", re.compile(r"\bquick entry\b", re.I)),
    Rule("Project Summary", "read-only", re.compile(r"\bsummar(?:y|ize)\b.*\bproject\b", re.I)),
    Rule("Task Placement", "bulk-write", re.compile(r"\b(place|move)\b.*\b(tasks?|todos?)\b.*\bheading", re.I)),
    Rule(
        "Project Structuring", "bulk-write", re.compile(r"\b(structure|headings?|phase|milestone)\b.*\bproject\b", re.I)
    ),
    Rule("Tag Taxonomy Audit", "read-only", re.compile(r"\btag\b.*\b(audit|taxonomy|review|cleanup)\b", re.I)),
    Rule(
        "Deadline And Reminder Review",
        "read-only",
        re.compile(r"\b(deadline|reminder|evening|due)\b.*\b(audit|review)\b", re.I),
    ),
    Rule(
        "Cleanup",
        "destructive-write",
        re.compile(r"\b(empty\b.*\btrash|log\b.*\bcompleted|complete all|cancel all|delete|cleanup)\b", re.I),
    ),
    Rule("Bulk Update With Approval", "bulk-write", re.compile(r"\b(all|bulk|every|multiple)\b", re.I)),
    Rule("Quick Capture", "single-write", re.compile(r"\b(capture|add|remind me|create)\b", re.I)),
    Rule("Read-Only Report", "read-only", re.compile(r"\b(report|show|list|find|search|audit|review)\b", re.I)),
]

DESTRUCTIVE_PATTERN = re.compile(r"\b(complete|cancel|delete|empty\b.*\btrash|log\b.*\bcompleted|json)\b", re.I)
AMBIGUOUS_DATE_PATTERN = re.compile(r"\b(soon|asap|next|later|important)\b", re.I)


def classify(request: str) -> dict[str, object]:
    matches = [rule for rule in RULES if rule.pattern.search(request)]
    selected = matches[0] if matches else Rule("Intake", "read-only", re.compile(r""))
    risk = "destructive-write" if DESTRUCTIVE_PATTERN.search(request) else selected.risk

    blockers: list[str] = []
    if risk != "read-only" and AMBIGUOUS_DATE_PATTERN.search(request):
        blockers.append("ambiguous date or urgency language")
    if risk in {"bulk-write", "destructive-write"}:
        blockers.append("preview and exact confirmation required")
    if "database" in request.lower():
        blockers.append("direct Things database access is out of scope")

    return {
        "mode_hint": selected.mode,
        "risk_hint": risk,
        "requires_safety_reference": risk != "read-only" or bool(blockers),
        "requires_workflow_reference": selected.mode not in {"Intake", "Read-Only Report"},
        "write_blockers": blockers,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, help="User request to classify")
    args = parser.parse_args()
    print(json.dumps(classify(args.request), sort_keys=True))


if __name__ == "__main__":
    main()
