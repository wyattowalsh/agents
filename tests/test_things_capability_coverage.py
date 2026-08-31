"""Semantic closure for every declared Things++ capability test identifier."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CHANGE_ROOT = REPO_ROOT / "openspec" / "changes" / "replace-supathings-with-things-plus-plus"
MANIFEST = json.loads((CHANGE_ROOT / "capability-manifest.json").read_text(encoding="utf-8"))
EVAL_DOCUMENT = json.loads(
    (REPO_ROOT / "skills" / "things-manager" / "evals" / "evals.json").read_text(encoding="utf-8")
)

TOOL_ROWS: list[dict[str, Any]] = MANIFEST["tools"]
SUPA_ROWS: list[dict[str, Any]] = MANIFEST["supaOutcomes"]
WORKFLOW_ROWS: list[dict[str, Any]] = MANIFEST["workflows"]
LEGACY_EVAL_ROWS: list[dict[str, Any]] = MANIFEST["legacyEvals"]
NEW_EVAL_ROWS: list[dict[str, Any]] = MANIFEST["newEvals"]
EVALS_BY_ID = {row["id"]: row for row in EVAL_DOCUMENT["evals"]}


def _contract_test_id(row: dict[str, Any]) -> str:
    return f"{row['server']}-{row['serverToolName'].replace('_', '-')}-contract"


def _toolset_test_id(server: str) -> str:
    return f"{server}-toolset-exact"


def _outcome_test_id(row: dict[str, Any]) -> str:
    return f"coverage-supa-{row['supaToolName'].replace('_', '-')}"


def _workflow_test_id(row: dict[str, Any]) -> str:
    return f"workflow-{row['workflowId']}"


@pytest.mark.parametrize("row", TOOL_ROWS, ids=[_contract_test_id(row) for row in TOOL_ROWS])
def test_capability_contract_test_id_resolves_to_executable_case(row: dict[str, Any]) -> None:
    assert row["testIds"] == [_toolset_test_id(row["server"]), _contract_test_id(row)]
    assert row["qualifiedCapabilityId"] == f"{row['server']}/{row['serverToolName']}"
    assert row["expectedMcphubQualifiedName"] == row["publicToolName"]
    assert row["minimumIndependentScope"] in {"things.read", "things.write", "things.admin"}
    assert row["schemaContractId"]


@pytest.mark.parametrize(
    "server",
    sorted({row["server"] for row in TOOL_ROWS}),
    ids=[_toolset_test_id(server) for server in sorted({row["server"] for row in TOOL_ROWS})],
)
def test_toolset_exact_test_id_resolves_to_executable_case(server: str) -> None:
    rows = [row for row in TOOL_ROWS if row["server"] == server]
    assert rows
    assert len({row["serverToolName"] for row in rows}) == len(rows)
    assert all(_toolset_test_id(server) in row["testIds"] for row in rows)


@pytest.mark.parametrize("row", SUPA_ROWS, ids=[_outcome_test_id(row) for row in SUPA_ROWS])
def test_supa_outcome_test_id_resolves_to_executable_case(row: dict[str, Any]) -> None:
    capability_ids = {tool["qualifiedCapabilityId"] for tool in TOOL_ROWS}
    workflow_ids = {workflow["workflowId"] for workflow in WORKFLOW_ROWS}
    assert row["testIds"] == [_outcome_test_id(row)]
    assert row["status"] == "mapped"
    assert row["targetCapabilityIds"] or row["workflowIds"]
    assert set(row["targetCapabilityIds"]) <= capability_ids
    assert set(row["workflowIds"]) <= workflow_ids


def test_supa_json_outcome_uses_exact_safe_typed_routes() -> None:
    row = next(row for row in SUPA_ROWS if row["supaToolName"] == "json")

    assert row["mappingKind"] == "safe-replacement"
    assert set(row["targetCapabilityIds"]) == {
        "things-shortcuts/create_todos",
        "things-shortcuts/create_structured_project",
    }
    assert set(row["workflowIds"]) == {
        "quick-capture",
        "project-planning",
        "bulk-update-with-approval",
    }
    assert row["status"] == "mapped"
    assert row["testIds"] == ["coverage-supa-json"]


@pytest.mark.parametrize("row", WORKFLOW_ROWS, ids=[_workflow_test_id(row) for row in WORKFLOW_ROWS])
def test_workflow_test_id_resolves_to_executable_case(row: dict[str, Any]) -> None:
    capability_ids = {tool["qualifiedCapabilityId"] for tool in TOOL_ROWS}
    assert row["testIds"] == [_workflow_test_id(row)]
    assert row["status"] == "mapped"
    assert row["targetCapabilityIds"]
    assert set(row["targetCapabilityIds"]) <= capability_ids


@pytest.mark.parametrize(
    ("eval_id", "test_id"),
    [
        *[(row["replacementEvalId"], row["testIds"][0]) for row in LEGACY_EVAL_ROWS],
        *[(row["evalId"], row["testIds"][0]) for row in NEW_EVAL_ROWS],
    ],
    ids=[
        *[row["testIds"][0] for row in LEGACY_EVAL_ROWS],
        *[row["testIds"][0] for row in NEW_EVAL_ROWS],
    ],
)
def test_eval_test_id_resolves_to_actual_eval(eval_id: str, test_id: str) -> None:
    assert test_id == f"eval-{eval_id}"
    actual = EVALS_BY_ID[eval_id]
    assert actual["prompt"]
    assert actual["expected_output"]
    assert actual["assertions"]


def test_every_declared_test_id_has_a_known_executable_or_eval_resolution() -> None:
    declared = {
        test_id
        for collection in (TOOL_ROWS, SUPA_ROWS, WORKFLOW_ROWS, LEGACY_EVAL_ROWS, NEW_EVAL_ROWS)
        for row in collection
        for test_id in row["testIds"]
    }
    resolved = {
        *(_contract_test_id(row) for row in TOOL_ROWS),
        *(_toolset_test_id(row["server"]) for row in TOOL_ROWS),
        *(_outcome_test_id(row) for row in SUPA_ROWS),
        *(_workflow_test_id(row) for row in WORKFLOW_ROWS),
        *(f"eval-{row['replacementEvalId']}" for row in LEGACY_EVAL_ROWS),
        *(f"eval-{row['evalId']}" for row in NEW_EVAL_ROWS),
    }
    assert declared == resolved
    assert len(EVALS_BY_ID) == len(LEGACY_EVAL_ROWS) + len(NEW_EVAL_ROWS) == 41
    assert MANIFEST["counts"] == {
        "coreTools": 41,
        "legacyEvalIds": 25,
        "nativeTools": 8,
        "newEvalIds": 16,
        "shortcutTools": 21,
        "supaOutcomes": 37,
        "tools": 70,
        "workflows": 17,
    }
