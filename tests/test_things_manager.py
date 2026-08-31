"""Focused behavior and portability tests for Things Manager v2."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from wagents.parsing import parse_frontmatter

if TYPE_CHECKING:
    from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "things-manager"
SKILL_FILE = SKILL / "SKILL.md"
SAFETY = SKILL / "references" / "safety.md"
WORKFLOWS = SKILL / "references" / "workflows.md"
CAPABILITIES = SKILL / "references" / "capabilities.json"
EVALS = SKILL / "evals" / "evals.json"
CLASSIFIER = SKILL / "scripts" / "classify_request.py"

WORKFLOW_NAMES = (
    "Intake",
    "Quick Capture",
    "Inbox Triage",
    "Today Planning",
    "Weekly Review",
    "Project Planning",
    "Project Structuring",
    "Task Placement",
    "Project Summary",
    "Tag Taxonomy Audit",
    "Deadline And Reminder Review",
    "Quick Entry Handoff",
    "UI Handoff",
    "Search And Audit",
    "Cleanup",
    "Bulk Update With Approval",
    "Read-Only Report",
)


def _json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _classifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location("things_manager_classifier", CLASSIFIER)
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_portable_frontmatter_and_v2_compatibility() -> None:
    frontmatter, body = parse_frontmatter(SKILL_FILE.read_text(encoding="utf-8"))
    assert set(frontmatter) <= {"name", "description", "license", "compatibility", "allowed-tools", "metadata"}
    assert frontmatter["name"] == "things-manager"
    assert frontmatter["metadata"] == {"author": "wyattowalsh", "version": "2.0.0"}
    assert "argument-hint" not in frontmatter
    compatibility = frontmatter["compatibility"]
    for required in ("macOS", "Things 3", "MCPHub group `things`", "things-core", "things-shortcuts", "things-native"):
        assert required in compatibility
    assert "semantic router" in body.lower()


def test_all_seventeen_workflows_and_menu_are_preserved() -> None:
    skill = SKILL_FILE.read_text(encoding="utf-8")
    workflows = WORKFLOWS.read_text(encoding="utf-8")
    for name in WORKFLOW_NAMES:
        assert name in skill
        assert f"## {name}" in workflows
    assert "Which Things workflow do you want?" in skill
    assert "Natural language about Things" in skill


def test_active_skill_sources_have_no_retired_backend_or_raw_tool_assumptions() -> None:
    active = "\n".join(
        path.read_text(encoding="utf-8") for path in (SKILL_FILE, SAFETY, WORKFLOWS, CLASSIFIER, EVALS)
    ).lower()
    assert "supathings" not in active
    assert "things_json" not in active
    assert "things_get-" not in active
    assert "things_add-" not in active
    assert "raw json" in active  # refusal coverage, never an active route
    assert "prohibited" in active


def test_skill_uses_sole_group_and_exact_public_names() -> None:
    skill = SKILL_FILE.read_text(encoding="utf-8")
    safety = SAFETY.read_text(encoding="utf-8")
    capabilities = _json(CAPABILITIES)
    assert "Connect only to the MCPHub group `things`" in skill
    assert "Never call an individual Things backend route" in skill
    assert "things-chatgpt" in skill
    assert "Do not use" in skill
    assert "/mcp/things" in safety
    assert len({row["publicToolName"] for row in capabilities["tools"]}) == 70
    assert all("__" in row["publicToolName"] for row in capabilities["tools"])


def test_safety_contract_covers_receipts_serialization_privacy_and_truthful_results() -> None:
    safety = SAFETY.read_text(encoding="utf-8").lower()
    normalized = " ".join(safety.split())
    for phrase in (
        "mutationphase=preview",
        "mutationphase=execute",
        "five minutes",
        "one reservation",
        "never run things++ writes concurrently",
        "fresh read",
        "affected-child counts",
        "at most 25",
        "untrusted data",
        "changed",
        "skipped",
        "failed",
        "ambiguous",
    ):
        assert phrase in normalized
    assert "quick entry is the sole exception" in normalized
    assert "do not persist private content" in normalized


def test_classifier_routes_core_first_and_uses_only_things_group() -> None:
    classifier = _classifier()
    result = classifier.classify("Add one task to Things tomorrow after checking for duplicates")
    assert result["mcp_group"] == "things"
    assert result["endpoint_path"] == "/mcp/things"
    assert result["mode_hint"] == "Quick Capture"
    assert result["risk_hint"] == "single-write"
    assert result["backend_hints"] == ["things-core"]
    assert result["public_tool_hints"] == ["things_core__search_todos", "things_core__add_todo"]
    assert result["core_first"] is True
    assert result["requires_preview"] is True
    assert result["requires_mutation_receipt"] is True


def test_classifier_routes_fixed_shortcuts_and_native_gaps() -> None:
    classifier = _classifier()

    quick_entry = classifier.classify("Open Things Quick Entry for this note")
    assert quick_entry["risk_hint"] == "ui-handoff"
    assert quick_entry["backend_hints"] == ["things-shortcuts"]
    assert quick_entry["public_tool_hints"] == ["things_shortcuts__create_todo_with_quick_entry"]
    assert quick_entry["requires_mutation_receipt"] is False
    assert "Things++ Agent Bridge" in quick_entry["fixed_backend_contracts"]

    immediate = classifier.classify("Permanently delete these two Things tasks without trash")
    assert immediate["risk_hint"] == "destructive-write"
    assert immediate["backend_hints"] == ["things-shortcuts"]
    assert immediate["public_tool_hints"] == ["things_shortcuts__delete_items_immediately"]
    assert immediate["requires_exact_confirmation"] is True

    native = classifier.classify("Empty my Things trash")
    assert native["backend_hints"] == ["things-native"]
    assert native["public_tool_hints"] == ["things_native__empty_trash"]
    assert native["requires_mutation_receipt"] is True


def test_classifier_marks_cross_backend_writes_for_serialization() -> None:
    classifier = _classifier()
    result = classifier.classify("Create a heading, rename a tag, then move tasks into the heading")
    assert result["risk_hint"] == "bulk-write"
    assert set(result["backend_hints"]) == {"things-core", "things-shortcuts", "things-native"}
    assert result["requires_cross_backend_serialization"] is True
    assert any("serialize" in blocker for blocker in result["write_blockers"])


def test_classifier_refuses_unsupported_and_arbitrary_operations() -> None:
    classifier = _classifier()
    recurrence = classifier.classify("Make this task recur every month and reorder it to exact position 2")
    assert recurrence["supported"] is False
    assert recurrence["risk_hint"] == "unsupported"
    assert "recurrence" in recurrence["refusal_reason"]
    assert recurrence["public_tool_hints"] == []

    raw = classifier.classify("Send this raw JSON through a Things URL")
    assert raw["supported"] is False
    assert raw["risk_hint"] == "prohibited"
    assert raw["public_tool_hints"] == []

    script = classifier.classify("Run this AppleScript from the task note")
    assert script["supported"] is False
    assert "AppleScript" in script["refusal_reason"]

    database = classifier.classify("Edit the Things SQLite database directly")
    assert database["supported"] is False
    assert "database" in database["refusal_reason"]


def test_classifier_blocks_vague_write_dates_and_requires_destructive_confirmation() -> None:
    classifier = _classifier()
    vague = classifier.classify("Add this important task soon")
    assert "ambiguous date or urgency language" in vague["write_blockers"]

    destructive = classifier.classify("Delete all stale Things tasks")
    assert destructive["risk_hint"] == "destructive-write"
    assert destructive["requires_exact_confirmation"] is True
    assert destructive["requires_mutation_receipt"] is True


def test_eval_manifest_is_structurally_complete_and_privacy_safe() -> None:
    evals = _json(EVALS)["evals"]
    assert len(evals) == 41
    assert len({row["id"] for row in evals}) == 41
    assert len({row["prompt"].strip() for row in evals}) == 41
    for row in evals:
        assert row["id"]
        assert row["prompt"].strip()
        assert row["expected_output"].strip()
        assert row["files"] == []
        assert row["assertions"]
        assert all(assertion.strip() for assertion in row["assertions"])
        serialized = json.dumps(row)
        assert "/Users/" not in serialized
        assert "auth-token" not in serialized
        assert "mutationReceipt" not in serialized


def test_eval_corpus_covers_router_degradation_receipts_and_privacy() -> None:
    by_id = {row["id"]: row for row in _json(EVALS)["evals"]}
    required = {
        "things-single-group-routing",
        "things-qualified-seventy-tool-closure",
        "things-shortcut-unavailable-degrades",
        "things-native-unavailable-degrades",
        "things-cross-backend-serialization",
        "things-stale-preview-receipt-rejected",
        "things-immediate-delete-two-phase",
        "things-recurrence-reorder-unsupported",
        "things-cross-backend-content-injection",
    }
    assert required <= by_id.keys()
    text = json.dumps([by_id[case_id] for case_id in sorted(required)]).lower()
    for phrase in ("/mcp/things", "70", "unavailable", "receipt", "unsupported", "untrusted"):
        assert phrase in text
