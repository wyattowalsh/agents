"""Focused tests for the Things++ ChatGPT static reference bundle."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from wagents.authoring_sync import _render_body_with_marker, _render_frontmatter
from wagents.skill_docs import collect_repo_skill_nodes

if TYPE_CHECKING:
    from collections.abc import Callable

MODULE_PATH = Path(__file__).with_name("validate_bundle.py")
SPEC = importlib.util.spec_from_file_location("things_plus_plus_validate_bundle", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def _schema_rejection(
    monkeypatch: pytest.MonkeyPatch,
    instance_name: str,
    mutate: Callable[[dict[str, Any]], None],
) -> str:
    original_load = VALIDATOR._load_json

    def load_mutated(path: Path) -> dict[str, Any]:
        payload = original_load(path)
        if path.name == instance_name:
            payload = copy.deepcopy(payload)
            mutate(payload)
        return payload

    monkeypatch.setattr(VALIDATOR, "_load_json", load_mutated)
    with pytest.raises(VALIDATOR.BundleError) as exc_info:
        VALIDATOR.validate_bundle()
    return str(exc_info.value)


def _observed_pass_payload() -> dict[str, Any]:
    payload = VALIDATOR._load_json(Path(__file__).with_name("observed-wire-record.template.json"))
    payload.update({
        "status": "observed-pass",
        "capturedAt": "2026-08-28T12:00:00Z",
        "expiresAt": "2026-08-28T12:05:00Z",
        "registrationMode": "client-id-metadata-document",
        "redirectUri": "https://chatgpt.com/connector_platform_oauth_redirect",
        "redirectUriSha256": "1" * 64,
        "mcpProtocolVersion": "2026-07-28",
        "modernDiscoveryObserved": True,
        "offlineAccessRequested": True,
        "resourceIndicatorObserved": True,
        "pkceS256Observed": True,
        "captureReceiptSha256": "2" * 64,
        "routeStatuses": {
            "mcp": 401,
            "protectedResourceMetadata": 200,
            "authorizationServerMetadata": 200,
            "authorization": 503,
            "registration": None,
        },
        "redactionsVerified": True,
        "prohibitedDataAbsent": True,
        "evidenceDigestSha256": "3" * 64,
    })
    return payload


def test_hand_authored_bundle_is_closed_and_fail_closed() -> None:
    VALIDATOR.validate_bundle()


def test_markdown_artifact_contract_is_exact_and_current_state_only() -> None:
    bundle_root = Path(__file__).parent

    assert {path.name for path in bundle_root.glob("*.md")} == {
        "README.md",
        "PROJECT_INSTRUCTIONS.md",
        "APP_SETUP.md",
        "TEST_PROMPTS.md",
        "SAFETY.md",
        "CAPABILITY_MATRIX.md",
    }

    manifest = VALIDATOR._load_json(bundle_root / "bundle.json")
    assert manifest["schemaVersion"] == "2.0.0"
    assert manifest["files"] == {
        "readme": "README.md",
        "appSetup": "APP_SETUP.md",
        "registrationReference": "registration-reference.json",
        "projectInstructions": "PROJECT_INSTRUCTIONS.md",
        "safety": "SAFETY.md",
        "testPrompts": "TEST_PROMPTS.md",
        "observedWireTemplate": "observed-wire-record.template.json",
        "generatedCapabilityMatrix": "CAPABILITY_MATRIX.md",
    }


def test_app_setup_remote_rollout_is_authorized_and_evidence_gated() -> None:
    setup = Path(__file__).with_name("APP_SETUP.md").read_text(encoding="utf-8")

    assert "exact `/mcp/things` endpoint" in setup
    assert "http://127.0.0.1:46683/mcp/things" in setup
    assert "https://mcp.w4w.dev/mcp/things" in setup
    assert "exactly 70 qualified tools" in setup
    assert "41 core, 21 fixed" in setup
    assert "Shortcuts, and 8 fixed native" in setup
    assert "Remote implementation/apply is explicitly authorized" in setup
    assert "remote ingress disabled" in setup
    assert "content/config/route-manifest-bound" in setup
    assert "does not create a ChatGPT app" in setup
    assert "## Local refresh and test" in setup
    assert "## Authorized OAuth rollout" in setup
    assert "## Account and workspace limits" in setup
    assert "## Emergency disable" in setup
    assert "typed unavailable/degraded result" in setup
    assert "unaffected core reads may" in setup
    assert "things-chatgpt" not in setup
    assert "things-admin" not in setup

    matrix = Path(__file__).with_name("CAPABILITY_MATRIX.md").read_text(encoding="utf-8")
    assert "Remote contract (implementation/apply authorized; activation evidence gated)" in matrix


def test_bundle_schema_rejects_schema_version_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["schemaVersion"] = "9.9.9"

    message = _schema_rejection(monkeypatch, "bundle.json", mutate)

    assert "bundle.json violates bundle.schema.json" in message
    assert "schemaVersion" in message


def test_bundle_schema_rejects_extra_properties(monkeypatch: pytest.MonkeyPatch) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["unexpected"] = True

    message = _schema_rejection(monkeypatch, "bundle.json", mutate)

    assert "bundle.json violates bundle.schema.json" in message
    assert "Additional properties" in message


def test_observed_wire_schema_rejects_invalid_date_time_format(monkeypatch: pytest.MonkeyPatch) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["capturedAt"] = "2026-99-99T99:99:99Z"

    message = _schema_rejection(monkeypatch, "observed-wire-record.template.json", mutate)

    assert "observed-wire-record.template.json violates observed-wire-record.schema.json" in message
    assert "capturedAt" in message
    assert "is not a 'date-time'" in message


def test_observed_wire_schema_accepts_only_closed_secret_free_pass_records() -> None:
    schema = VALIDATOR._load_json(Path(__file__).with_name("observed-wire-record.schema.json"))
    validator = VALIDATOR.jsonschema.Draft202012Validator(
        schema,
        format_checker=VALIDATOR.FORMAT_CHECKER,
    )
    payload = _observed_pass_payload()
    validator.validate(payload)

    missing_refresh = copy.deepcopy(payload)
    missing_refresh["offlineAccessRequested"] = False
    with pytest.raises(VALIDATOR.jsonschema.ValidationError):
        validator.validate(missing_refresh)

    secret_bearing = copy.deepcopy(payload)
    secret_bearing["accessToken"] = "forbidden"
    with pytest.raises(VALIDATOR.jsonschema.ValidationError):
        validator.validate(secret_bearing)


def test_registration_schema_rejects_const_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["connector"]["group"] = "things-admin"

    message = _schema_rejection(monkeypatch, "registration-reference.json", mutate)

    assert "registration-reference.json violates registration-reference.schema.json" in message
    assert "connector.group" in message
    assert "'things' was expected" in message


def test_registration_reference_freezes_single_group_and_expanded_catalog() -> None:
    reference = VALIDATOR._load_json(Path(__file__).with_name("registration-reference.json"))

    assert reference["connector"] == {
        "group": "things",
        "publicResource": "https://mcp.w4w.dev/mcp/things",
        "localBearerResource": "http://127.0.0.1:46683/mcp/things",
        "remoteOAuthOrigin": "http://127.0.0.1:46684/mcp/things",
        "toolCount": 70,
        "backendToolCounts": {
            "things-core": 41,
            "things-shortcuts": 21,
            "things-native": 8,
        },
        "alternateThingsRoutesAllowed": False,
    }
    assert reference["activation"]["remoteDefault"] == "disabled"
    assert reference["activation"]["observedWireStatus"] == "not-observed"
    assert reference["oauth"]["requiredIndependentScopes"] == [
        "things.read",
        "things.write",
        "things.admin",
    ]
    assert reference["oauth"]["refreshCapabilityScope"] == "offline_access"
    assert reference["oauth"]["refreshCapabilityRequirement"] == "required-for-durable-chatgpt-profile"
    assert reference["oauth"]["refreshCapabilitySemantics"] == "refresh-only-no-things-authorization"
    assert reference["oauth"]["registration"]["observedMode"] is None


def test_observed_wire_template_cannot_be_mistaken_for_evidence() -> None:
    template = VALIDATOR._load_json(Path(__file__).with_name("observed-wire-record.template.json"))

    assert template["status"] == "not-observed"
    assert template["capturedAt"] is None
    assert template["expiresAt"] is None
    assert template["registrationMode"] is None
    assert template["redirectUri"] is None
    assert template["redirectUriSha256"] is None
    assert template["mcpProtocolVersion"] is None
    assert template["requiredIndependentScopes"] == [
        "things.read",
        "things.write",
        "things.admin",
    ]
    assert template["offlineAccessRequested"] is False
    assert template["offlineAccessSemantics"] == "refresh-only-no-things-authorization"
    assert template["resourceIndicatorObserved"] is False
    assert template["pkceS256Observed"] is False
    assert template["captureReceiptSha256"] is None
    assert set(template["routeStatuses"].values()) == {None}
    assert template["redactionsVerified"] is False
    assert template["prohibitedDataAbsent"] is True
    assert template["evidenceDigestSha256"] is None
    assert "notes" not in template


def test_owned_source_docs_match_the_closed_things_contract() -> None:
    VALIDATOR._validate_owned_source_docs()


def test_things_manager_authoring_projection_matches_skill_source() -> None:
    node = next(item for item in collect_repo_skill_nodes() if item.id == "things-manager")
    metadata = dict(node.metadata) if isinstance(node.metadata, dict) else {}
    metadata.setdefault("name", node.id)
    metadata.setdefault("description", node.description)
    expected = f"{_render_frontmatter(metadata)}\n\n{_render_body_with_marker(node.id, node.body or '')}"
    actual = VALIDATOR.OWNED_SOURCE_DOCS["authoring"].read_text(encoding="utf-8")

    assert actual == expected
