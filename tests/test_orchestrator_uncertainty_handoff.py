"""Tests for orchestrator uncertainty handoff and re-entry policy."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

UNCERTAINTY_HANDOFF = (
    REPO_ROOT / "skills" / "orchestrator" / "references" / "uncertainty-handoff.md"
)
PROGRESS_ACCOUNTING = (
    REPO_ROOT / "skills" / "orchestrator" / "references" / "progress-accounting.md"
)
ORCHESTRATOR_SKILL = REPO_ROOT / "skills" / "orchestrator" / "SKILL.md"

HANDOFF_MARKERS = (
    "blocked-user-pivotal",
    "open_branch",
    "resolved_context",
    "scoped",
)

REENTRY_MARKERS = (
    "upfront and re-entry",
    "blocked-user-pivotal",
    "uncertainty-handoff.md",
)

LADDER_MARKERS = (
    "blocked-user-pivotal",
    "Micro-reversible",
    "scoped `/grill-me`",
)

DELEGATED_AGENT_PATHS = (
    REPO_ROOT / "agents" / "planner.md",
    REPO_ROOT / "agents" / "researcher.md",
    REPO_ROOT / "agents" / "code-reviewer.md",
    REPO_ROOT / "agents" / "docs-writer.md",
    REPO_ROOT / "agents" / "security-auditor.md",
    REPO_ROOT / "agents" / "release-manager.md",
    REPO_ROOT / "agents" / "performance-profiler.md",
)


def test_uncertainty_handoff_reference_exists() -> None:
    assert UNCERTAINTY_HANDOFF.is_file()


@pytest.mark.parametrize("marker", HANDOFF_MARKERS)
def test_uncertainty_handoff_contains_contract_fields(marker: str) -> None:
    text = UNCERTAINTY_HANDOFF.read_text(encoding="utf-8")
    assert marker in text


@pytest.mark.parametrize("marker", REENTRY_MARKERS)
def test_orchestrator_skill_uncertainty_gate_reentry(marker: str) -> None:
    text = ORCHESTRATOR_SKILL.read_text(encoding="utf-8")
    assert marker in text


@pytest.mark.parametrize("marker", LADDER_MARKERS)
def test_progress_accounting_recovery_ladder_classifies_blockers(marker: str) -> None:
    text = PROGRESS_ACCOUNTING.read_text(encoding="utf-8")
    assert marker in text


@pytest.mark.parametrize("path", DELEGATED_AGENT_PATHS)
def test_delegated_agents_document_blocked_user_pivotal_handoff(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert "blocked-user-pivotal" in text
    assert "uncertainty-handoff.md" in text