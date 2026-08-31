#!/usr/bin/env python3
"""Classify a Things Manager request into safe Things++ routing hints."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    mode: str
    risk: str
    backend: str
    public_tools: tuple[str, ...]
    pattern: re.Pattern[str]


RULES = (
    Rule(
        "Cleanup",
        "destructive-write",
        "things-shortcuts",
        ("things_shortcuts__delete_items_immediately",),
        re.compile(r"\b(delete|remove)\b.*\b(immediately|permanently|without trash)\b", re.I),
    ),
    Rule(
        "Cleanup",
        "destructive-write",
        "things-native",
        ("things_native__empty_trash",),
        re.compile(r"\bempty\b.*\btrash\b", re.I),
    ),
    Rule(
        "Cleanup",
        "destructive-write",
        "things-native",
        ("things_native__log_completed",),
        re.compile(r"\blog\b.*\bcompleted\b", re.I),
    ),
    Rule(
        "Cleanup",
        "destructive-write",
        "things-native",
        ("things_native__delete_area",),
        re.compile(r"\b(delete|remove)\b.*\barea\b", re.I),
    ),
    Rule(
        "Cleanup",
        "destructive-write",
        "things-native",
        ("things_native__delete_tag",),
        re.compile(r"\b(delete|remove)\b.*\btag\b", re.I),
    ),
    Rule(
        "Cleanup",
        "destructive-write",
        "things-shortcuts",
        ("things_shortcuts__delete_heading",),
        re.compile(r"\b(delete|remove)\b.*\bheading\b", re.I),
    ),
    Rule(
        "Tag Taxonomy Audit",
        "single-write",
        "things-native",
        ("things_native__rename_tag",),
        re.compile(r"\b(rename|change)\b.*\btag\b", re.I),
    ),
    Rule(
        "Tag Taxonomy Audit",
        "single-write",
        "things-native",
        ("things_native__set_tag_parent",),
        re.compile(r"\b(set|assign|change)\b.*\btag parent\b", re.I),
    ),
    Rule(
        "Quick Entry Handoff",
        "ui-handoff",
        "things-shortcuts",
        ("things_shortcuts__create_todo_with_quick_entry",),
        re.compile(r"\bquick entry\b", re.I),
    ),
    Rule(
        "UI Handoff",
        "ui-visible",
        "things-native",
        ("things_native__open_search",),
        re.compile(r"\b(open|show)\b.*\b(search|search results)\b", re.I),
    ),
    Rule(
        "UI Handoff",
        "ui-visible",
        "things-shortcuts",
        ("things_shortcuts__open_list", "things_shortcuts__show_items"),
        re.compile(r"\b(open|show)\b.*\b(list|items?|project|today|inbox)\b", re.I),
    ),
    Rule(
        "Project Planning",
        "bulk-write",
        "things-shortcuts",
        ("things_shortcuts__create_structured_project",),
        re.compile(r"\b(create|build|plan)\b.*\b(structured project|project with headings|project phases)\b", re.I),
    ),
    Rule(
        "Project Structuring",
        "single-write",
        "things-shortcuts",
        ("things_shortcuts__create_heading", "things_shortcuts__edit_heading"),
        re.compile(r"\b(create|add|edit|rename)\b.*\bheading\b", re.I),
    ),
    Rule(
        "Bulk Update With Approval",
        "bulk-write",
        "things-shortcuts",
        ("things_shortcuts__duplicate_items",),
        re.compile(r"\bduplicate\b.*\b(items?|todos?|tasks?)\b", re.I),
    ),
    Rule(
        "Search And Audit",
        "read-only",
        "things-shortcuts",
        ("things_shortcuts__get_selected_items",),
        re.compile(r"\b(selected|selection)\b.*\b(items?|todos?|tasks?)\b", re.I),
    ),
    Rule(
        "Project Summary",
        "read-only",
        "things-core",
        (
            "things_core__get_projects",
            "things_core__get_project_headings",
            "things_core__get_todos",
        ),
        re.compile(r"\bsummar(?:y|ize)\b.*\bproject\b", re.I),
    ),
    Rule(
        "Task Placement",
        "bulk-write",
        "things-core",
        ("things_core__get_project_headings", "things_core__move_record"),
        re.compile(r"\b(place|move)\b.*\b(tasks?|todos?)\b.*\b(heading|project)\b", re.I),
    ),
    Rule(
        "Project Structuring",
        "bulk-write",
        "things-shortcuts",
        ("things_shortcuts__create_heading", "things_shortcuts__edit_heading"),
        re.compile(r"\b(structure|headings?|phases?|milestones?)\b.*\bproject\b", re.I),
    ),
    Rule(
        "Tag Taxonomy Audit",
        "read-only",
        "things-core",
        ("things_core__get_tags", "things_core__get_tag_usage", "things_core__get_tagged_items"),
        re.compile(r"\btag\b.*\b(audit|taxonomy|review|cleanup)\b", re.I),
    ),
    Rule(
        "Deadline And Reminder Review",
        "read-only",
        "things-core",
        ("things_core__get_due_in_days", "things_core__get_activating_in_days"),
        re.compile(r"\b(deadline|reminder|evening|due)\b.*\b(audit|review)\b", re.I),
    ),
    Rule(
        "Cleanup",
        "destructive-write",
        "things-core",
        ("things_core__get_trash", "things_core__delete_todo"),
        re.compile(r"\b(complete all|cancel all|delete|cleanup|trash)\b", re.I),
    ),
    Rule(
        "Bulk Update With Approval",
        "bulk-write",
        "things-core",
        ("things_core__bulk_update_todos", "things_core__bulk_move_records"),
        re.compile(r"\b(all|bulk|every|multiple|many)\b", re.I),
    ),
    Rule(
        "Quick Capture",
        "single-write",
        "things-core",
        ("things_core__search_todos", "things_core__add_todo"),
        re.compile(r"\b(capture|add|remind me|create)\b", re.I),
    ),
    Rule(
        "Read-Only Report",
        "read-only",
        "things-core",
        ("things_core__search_todos", "things_core__search_advanced"),
        re.compile(r"\b(report|list|find|search|audit|review)\b", re.I),
    ),
)

FALLBACK_RULE_COUNT = 4

UNSUPPORTED = (
    (
        "recurrence-template editing is unsupported",
        re.compile(
            r"\b(recurrence|recurring|repeat(?:ing)? template|repeat every|every (day|week|month|year))\b", re.I
        ),
    ),
    (
        "deterministic positional reorder is unsupported",
        re.compile(
            r"\b(reorder|re-order|exact position|position \d+|sort.*tasks?|move.*\b(top|bottom|before|after)\b)\b", re.I
        ),
    ),
    (
        "tag-parent detach is unsupported in this version",
        re.compile(r"\b(detach|remove|clear|unset)\b.*\b(tag parent|parent tag)\b", re.I),
    ),
)

PROHIBITED = (
    (
        "raw Things JSON or URL passthrough is prohibited; use a closed typed operation",
        re.compile(r"\b(raw json|things json|things:///|things url|url scheme|raw url)\b", re.I),
    ),
    (
        "generic or caller-selected Shortcut execution is prohibited",
        re.compile(r"\b(run|execute|choose|select)\b.*\b(shortcut|shortcut name)\b", re.I),
    ),
    (
        "arbitrary AppleScript or command execution is prohibited",
        re.compile(r"\b(applescript|osascript|shell command|run shell|command fragment)\b", re.I),
    ),
    (
        "direct Things database, SQL, or filesystem access is prohibited",
        re.compile(r"\b(database|sqlite|sql|filesystem|file path)\b", re.I),
    ),
)

AMBIGUOUS_DATE_PATTERN = re.compile(r"\b(soon|asap|later|important|next)\b", re.I)
RISK_ORDER = {
    "read-only": 0,
    "ui-visible": 1,
    "ui-handoff": 2,
    "single-write": 3,
    "bulk-write": 4,
    "destructive-write": 5,
}


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _refusal(request: str, reason: str, kind: str) -> dict[str, object]:
    return {
        "mcp_group": "things",
        "endpoint_path": "/mcp/things",
        "mode_hint": "Intake",
        "risk_hint": kind,
        "backend_hints": [],
        "public_tool_hints": [],
        "core_first": True,
        "supported": False,
        "refusal_reason": reason,
        "requires_preview": False,
        "requires_exact_confirmation": False,
        "requires_mutation_receipt": False,
        "requires_cross_backend_serialization": False,
        "requires_safety_reference": True,
        "requires_workflow_reference": False,
        "write_blockers": [reason],
        "request_was_empty": not request.strip(),
    }


def classify(request: str) -> dict[str, object]:
    for reason, pattern in UNSUPPORTED:
        if pattern.search(request):
            return _refusal(request, reason, "unsupported")
    for reason, pattern in PROHIBITED:
        if pattern.search(request):
            return _refusal(request, reason, "prohibited")

    specific_matches = [rule for rule in RULES[:-FALLBACK_RULE_COUNT] if rule.pattern.search(request)]
    matches = specific_matches or [rule for rule in RULES[-FALLBACK_RULE_COUNT:] if rule.pattern.search(request)]
    if not matches:
        matches = [
            Rule(
                "Intake",
                "read-only",
                "things-core",
                ("things_core__get_server_capabilities",),
                re.compile(r""),
            )
        ]

    selected = max(matches, key=lambda rule: RISK_ORDER[rule.risk])
    backends = _unique([rule.backend for rule in matches])
    tools = _unique([tool for rule in matches for tool in rule.public_tools])
    mutating = selected.risk in {"single-write", "bulk-write", "destructive-write"}
    cross_backend = mutating and len(backends) > 1

    blockers: list[str] = []
    if mutating and AMBIGUOUS_DATE_PATTERN.search(request):
        blockers.append("ambiguous date or urgency language")
    if selected.risk in {"bulk-write", "destructive-write"}:
        blockers.append("server preview and exact confirmation required")
    if cross_backend:
        blockers.append("serialize and verify one backend mutation before the next preview")

    fixed_contracts: list[str] = []
    if "things-shortcuts" in backends:
        fixed_contracts.extend(["Things++ Agent Bridge", "Things++ Destructive Bridge"])
    if "things-native" in backends:
        fixed_contracts.append("repository-owned fixed native scripts and search URL builder")

    return {
        "mcp_group": "things",
        "endpoint_path": "/mcp/things",
        "mode_hint": selected.mode,
        "risk_hint": selected.risk,
        "backend_hints": backends,
        "public_tool_hints": tools,
        "core_first": True,
        "supported": True,
        "refusal_reason": None,
        "fixed_backend_contracts": fixed_contracts,
        "requires_preview": mutating,
        "requires_exact_confirmation": selected.risk in {"bulk-write", "destructive-write"},
        "requires_mutation_receipt": mutating and selected.risk != "ui-handoff",
        "requires_cross_backend_serialization": cross_backend,
        "requires_safety_reference": selected.risk != "read-only" or bool(blockers),
        "requires_workflow_reference": selected.mode not in {"Intake", "Read-Only Report"},
        "write_blockers": blockers,
        "request_was_empty": not request.strip(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, help="User request to classify")
    args = parser.parse_args()
    print(json.dumps(classify(args.request), sort_keys=True))


if __name__ == "__main__":
    main()
