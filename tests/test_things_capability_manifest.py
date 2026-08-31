"""Closure and source-parity tests for the Things++ skill capability ledger."""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import jsonschema
import pytest

if TYPE_CHECKING:
    from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
CHANGE = ROOT / "openspec" / "changes" / "replace-supathings-with-things-plus-plus"
SOURCE = CHANGE / "capability-manifest.json"
SCHEMA = CHANGE / "capability-manifest.schema.json"
SKILL = ROOT / "skills" / "things-manager"
CAPABILITIES = SKILL / "references" / "capabilities.json"
CAPABILITIES_MD = SKILL / "references" / "capabilities.md"
RENDERER = SKILL / "scripts" / "render_capabilities.py"
EVALS = SKILL / "evals" / "evals.json"
SCHEMA_FREEZER = ROOT / "scripts" / "freeze_things_capability_schemas.py"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

EXPECTED_WORKFLOWS = {
    "intake",
    "quick-capture",
    "inbox-triage",
    "today-planning",
    "weekly-review",
    "project-planning",
    "project-structuring",
    "task-placement",
    "project-summary",
    "tag-taxonomy-audit",
    "deadline-and-reminder-review",
    "quick-entry-handoff",
    "ui-handoff",
    "search-and-audit",
    "cleanup",
    "bulk-update-with-approval",
    "read-only-report",
}

EXPECTED_LEGACY_EVALS = {
    "empty-args-menu",
    "implicit-trigger-read-only-today-plan",
    "bulk-update-requires-approval",
    "ambiguous-deadline-handling",
    "quick-capture-multiple-tasks",
    "inbox-triage-preview",
    "negative-control-non-things-manager",
    "scope-refusal-calendar-only",
    "intake-ambiguous-project-target",
    "read-only-report-deadline-audit",
    "scope-refusal-mcp-server-setup",
    "scope-refusal-direct-database-edit",
    "semantic-headings-new-project",
    "existing-project-heading-limitation",
    "suggest-task-placement-preview",
    "project-summary-read-only",
    "compact-read-before-full-detail",
    "quick-entry-human-review",
    "tag-inheritance-audit",
    "reminder-evening-deadline-distinction",
    "raw-json-bulk-preview-required",
    "empty-trash-destructive-confirmation",
    "log-completed-destructive-confirmation",
    "things-content-is-untrusted-data",
    "missing-tag-or-area-does-not-infer-create",
}

EXPECTED_ADDITIVE_EVALS = {
    "things-single-group-routing",
    "things-local-remote-endpoint-parity",
    "things-qualified-seventy-tool-closure",
    "things-core-first-routing",
    "things-shortcut-fixed-name-enforcement",
    "things-native-fixed-script-enforcement",
    "things-shortcut-unavailable-degrades",
    "things-native-unavailable-degrades",
    "things-cross-backend-serialization",
    "things-stale-preview-receipt-rejected",
    "things-create-todos-batch-bound",
    "things-structured-project-no-raw-json",
    "things-immediate-delete-two-phase",
    "things-tag-area-destructive-confirmation",
    "things-recurrence-reorder-unsupported",
    "things-cross-backend-content-injection",
}


def _json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _renderer() -> ModuleType:
    spec = importlib.util.spec_from_file_location("things_manager_capabilities", RENDERER)
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_openspec_manifest_is_schema_valid() -> None:
    schema = _json(SCHEMA)
    source = _json(SOURCE)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(source)


def test_all_seventy_adapted_tool_schemas_are_frozen_sha256_values() -> None:
    tools = _json(SOURCE)["tools"]

    assert len(tools) == 70
    for row in tools:
        hashes = row["adaptedSchemaHashes"]
        assert hashes["status"] == "frozen"
        assert SHA256_PATTERN.fullmatch(hashes["inputSchemaSha256"])
        assert SHA256_PATTERN.fullmatch(hashes["outputSchemaSha256"])


def test_frozen_tool_schemas_match_the_source_defined_servers() -> None:
    result = subprocess.run(
        [sys.executable, str(SCHEMA_FREEZER), "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report == {
        "changed": False,
        "mode": "check",
        "normalizedCatalogSha256": "0c48616453e929a8f9d287bb7a4bb59f0d587df3e7008506bfdd7c52472b066e",
        "ok": True,
        "serverCounts": {"things-core": 41, "things-native": 8, "things-shortcuts": 21},
        "toolCount": 70,
    }


def test_skill_manifest_is_exact_openspec_projection_with_degraded_behavior() -> None:
    renderer = _renderer()
    source = _json(SOURCE)
    capabilities = _json(CAPABILITIES)

    renderer.validate_capabilities(capabilities, source)
    assert renderer._source_projection(capabilities) == source
    assert all(row["degradedBehavior"].strip() for row in capabilities["tools"])
    assert {row["server"]: row["degradedBehavior"] for row in capabilities["tools"]}.keys() == {
        "things-core",
        "things-shortcuts",
        "things-native",
    }


def test_renderer_semantics_reject_missing_shortcuts_adapted_hashes(monkeypatch: pytest.MonkeyPatch) -> None:
    renderer = _renderer()
    source = copy.deepcopy(_json(SOURCE))
    shortcut = next(row for row in source["tools"] if row["server"] == "things-shortcuts")
    shortcut.pop("adaptedSchemaHashes")
    derived = renderer._derived_manifest(source)
    monkeypatch.setattr(renderer, "_validate_source_schema", lambda _source: None)

    with pytest.raises(renderer.CapabilityError, match="lacks the closed adapted schema hash contract"):
        renderer.validate_capabilities(derived, source)


def test_renderer_semantics_reject_invalid_native_adapted_hashes(monkeypatch: pytest.MonkeyPatch) -> None:
    renderer = _renderer()
    source = copy.deepcopy(_json(SOURCE))
    native = next(row for row in source["tools"] if row["server"] == "things-native")
    native["adaptedSchemaHashes"]["inputSchemaSha256"] = "not-a-sha256"
    derived = renderer._derived_manifest(source)
    monkeypatch.setattr(renderer, "_validate_source_schema", lambda _source: None)

    with pytest.raises(renderer.CapabilityError, match="invalid adapted inputSchemaSha256"):
        renderer.validate_capabilities(derived, source)


def test_renderer_schema_rejects_annotation_extensions() -> None:
    renderer = _renderer()
    source = copy.deepcopy(_json(SOURCE))
    source["tools"][0]["annotations"]["unexpectedHint"] = False
    derived = renderer._derived_manifest(source)

    with pytest.raises(renderer.CapabilityError, match="capability manifest violates schema"):
        renderer.validate_capabilities(derived, source)


def test_renderer_schema_rejects_manifest_schema_version_drift() -> None:
    renderer = _renderer()
    source = copy.deepcopy(_json(SOURCE))
    source["schemaVersion"] = "9.9.9"
    derived = renderer._derived_manifest(source)

    with pytest.raises(renderer.CapabilityError, match="capability manifest violates schema"):
        renderer.validate_capabilities(derived, source)


def test_renderer_fails_closed_when_jsonschema_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    renderer = _renderer()
    source = _json(SOURCE)
    derived = renderer._derived_manifest(source)

    def missing_jsonschema(module_name: str) -> None:
        assert module_name == "jsonschema"
        raise ModuleNotFoundError(module_name)

    monkeypatch.setattr(renderer, "import_module", missing_jsonschema)
    with pytest.raises(renderer.CapabilityError, match="jsonschema is required"):
        renderer.validate_capabilities(derived, source)


def test_catalog_access_requires_all_scopes_for_both_protocol_eras() -> None:
    scopes = _json(SOURCE)["scopes"]

    assert scopes["independent"] == ["things.read", "things.write", "things.admin"]
    assert scopes["chatgptRequiredGrant"] == scopes["independent"]
    assert scopes["implication"] == "none"
    rule = scopes["catalogAccessRule"]
    for required_phrase in ("server/discover", "modern", "legacy initialize", "tools/list"):
        assert required_phrase in rule


def test_capability_cardinality_partition_names_and_references_are_closed() -> None:
    data = _json(CAPABILITIES)
    tools = data["tools"]
    outcomes = data["supaOutcomes"]
    workflows = data["workflows"]
    legacy = data["legacyEvals"]
    additive = data["newEvals"]

    assert (len(tools), len(outcomes), len(workflows), len(legacy), len(additive)) == (70, 37, 17, 25, 16)
    assert sum(row["server"] == "things-core" for row in tools) == 41
    assert sum(row["server"] == "things-shortcuts" for row in tools) == 21
    assert sum(row["server"] == "things-native" for row in tools) == 8

    qualified = [row["qualifiedCapabilityId"] for row in tools]
    public = [row["publicToolName"] for row in tools]
    assert len(set(qualified)) == len(qualified) == 70
    assert len(set(public)) == len(public) == 70
    for row in tools:
        expected = f"{row['server'].replace('-', '_')}__{row['serverToolName']}"
        assert row["publicToolName"] == row["expectedMcphubQualifiedName"] == expected
        assert row["minimumIndependentScope"] in {"things.read", "things.write", "things.admin"}
        assert row["risk"] in {
            "read-only",
            "ui-visible",
            "ui-visible-write",
            "single-write",
            "bulk-write",
            "destructive-write",
            "maintenance",
            "ui-handoff",
        }
        assert row["backendPrerequisites"]
        assert row["testIds"]

    qualified_set = set(qualified)
    workflow_ids = {row["workflowId"] for row in workflows}
    assert workflow_ids == EXPECTED_WORKFLOWS
    assert all(row["status"] == "mapped" for row in outcomes)
    classification_by_mapping_kind = {
        "direct": "implemented",
        "composed": "implemented",
        "safe-replacement": "safe-replacement",
        "semantic": "semantic-skill",
    }
    classifications = [classification_by_mapping_kind[row["mappingKind"]] for row in outcomes]
    assert set(classifications) <= {"implemented", "safe-replacement", "semantic-skill"}
    assert len(classifications) == 37
    assert "removed" not in classifications
    assert all(row["targetCapabilityIds"] for row in outcomes)
    assert all(set(row["targetCapabilityIds"]) <= qualified_set for row in outcomes)
    assert all(set(row["workflowIds"]) <= workflow_ids for row in outcomes)
    assert all(row["testIds"] for row in outcomes)
    assert all(row["status"] == "mapped" for row in workflows)
    assert all(set(row["targetCapabilityIds"]) <= qualified_set for row in workflows)
    assert all(row["testIds"] for row in workflows)
    assert data["netNewOutcomeIds"]


def test_sole_group_contract_has_no_split_or_direct_route() -> None:
    group = _json(CAPABILITIES)["group"]
    assert group == {
        "name": "things",
        "deterministicId": "3b94a096-b95f-586c-b2e7-e69ed177eb5a",
        "localPath": "/mcp/things",
        "remotePath": "/mcp/things",
        "localResource": "http://127.0.0.1:46683/mcp/things",
        "remoteResource": "https://mcp.w4w.dev/mcp/things",
        "servers": ["things-core", "things-shortcuts", "things-native"],
    }


def test_eval_ids_preserve_exact_twenty_five_plus_sixteen_partition() -> None:
    capabilities = _json(CAPABILITIES)
    evals = _json(EVALS)["evals"]
    actual = [row["id"] for row in evals]
    legacy = {row["legacyEvalId"] for row in capabilities["legacyEvals"]}
    replacements = {row["replacementEvalId"] for row in capabilities["legacyEvals"]}
    additive = {row["evalId"] for row in capabilities["newEvals"]}

    assert legacy == replacements == EXPECTED_LEGACY_EVALS
    assert additive == EXPECTED_ADDITIVE_EVALS
    assert len(actual) == len(set(actual)) == 41
    assert set(actual) == legacy | additive
    assert all(row["testIds"] for row in capabilities["legacyEvals"])
    assert all(row["testIds"] for row in capabilities["newEvals"])


def test_generated_markdown_exactly_matches_json_renderer() -> None:
    renderer = _renderer()
    capabilities = _json(CAPABILITIES)
    assert CAPABILITIES_MD.read_text(encoding="utf-8") == renderer.render_markdown(capabilities)
    assert renderer.main(["--check"]) == 0


def test_generated_markdown_contains_all_public_names_and_routes() -> None:
    data = _json(CAPABILITIES)
    markdown = CAPABILITIES_MD.read_text(encoding="utf-8")
    for row in data["tools"]:
        assert f"`{row['publicToolName']}`" in markdown
        assert f"`{row['qualifiedCapabilityId']}`" in markdown
        assert row["degradedBehavior"] in markdown
