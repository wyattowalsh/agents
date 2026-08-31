#!/usr/bin/env python3
"""Validate the static Things++ ChatGPT reference bundle."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import jsonschema

BUNDLE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = BUNDLE_ROOT.parents[2]
SOURCE_CAPABILITIES = REPO_ROOT / "skills" / "things-manager" / "references" / "capabilities.md"
GENERATED_CAPABILITIES = BUNDLE_ROOT / "CAPABILITY_MATRIX.md"
JSON_SCHEMA_PAIRS = (
    ("bundle.json", "bundle.schema.json"),
    ("registration-reference.json", "registration-reference.schema.json"),
    ("observed-wire-record.template.json", "observed-wire-record.schema.json"),
)
RFC3339_DATE_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
FORMAT_CHECKER = jsonschema.FormatChecker()
OWNED_SOURCE_DOCS = {
    "operator": REPO_ROOT / "docs" / "ai-tools" / "mcphub.md",
    "runtime": REPO_ROOT / "mcp" / "mcphub" / "README.md",
    "authoring": REPO_ROOT / "docs" / "src" / "authoring" / "skills" / "things-manager.mdx",
    "research": REPO_ROOT / "docs" / "src" / "skill-research" / "things-manager.md",
    "knowledge": REPO_ROOT / "kb" / "raw" / "sources" / "mcphub-control-plane-source.md",
}


@FORMAT_CHECKER.checks("date-time")
def _is_rfc3339_date_time(value: object) -> bool:
    if not isinstance(value, str):
        return True
    if RFC3339_DATE_TIME.fullmatch(value) is None:
        return False
    normalized = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return True


@FORMAT_CHECKER.checks("uri")
def _is_uri(value: object) -> bool:
    if not isinstance(value, str):
        return True
    if not value or any(character.isspace() for character in value):
        return False
    parsed = urlsplit(value)
    if not parsed.scheme:
        return False
    return parsed.scheme not in {"http", "https"} or bool(parsed.netloc)


EXPECTED_DOCUMENTS = {
    "APP_SETUP.md",
    "CAPABILITY_MATRIX.md",
    "PROJECT_INSTRUCTIONS.md",
    "README.md",
    "SAFETY.md",
    "TEST_PROMPTS.md",
}
PROHIBITED_BUNDLE_TEXT = {
    "/mcp/tunnel",
    "SupaThings",
    "supathings",
    "things_json",
    "/mcp/things-core",
    "/mcp/things-shortcuts",
    "/mcp/things-native",
}


class BundleError(ValueError):
    """Raised when the static ChatGPT bundle violates its frozen contract."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise BundleError(f"invalid or missing JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise BundleError(f"JSON root must be an object: {path}")
    return payload


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BundleError(message)


def _validate_json_references() -> None:
    for path in BUNDLE_ROOT.glob("*.json"):
        payload = _load_json(path)
        schema_ref = payload.get("$schema")
        if schema_ref is None or str(path).endswith(".schema.json"):
            continue
        _require(isinstance(schema_ref, str), f"$schema must be a string: {path.name}")
        _require(not schema_ref.startswith(("/", "..")), f"unsafe schema reference: {path.name}")
        _require((BUNDLE_ROOT / schema_ref).is_file(), f"missing schema for {path.name}: {schema_ref}")


def _validate_json_schemas() -> None:
    for instance_name, schema_name in JSON_SCHEMA_PAIRS:
        instance = _load_json(BUNDLE_ROOT / instance_name)
        schema = _load_json(BUNDLE_ROOT / schema_name)
        try:
            jsonschema.Draft202012Validator.check_schema(schema)
            jsonschema.Draft202012Validator(
                schema,
                format_checker=FORMAT_CHECKER,
            ).validate(instance)
        except jsonschema.exceptions.SchemaError as exc:
            raise BundleError(f"invalid JSON Schema {schema_name}: {exc.message}") from exc
        except jsonschema.ValidationError as exc:
            location = ".".join(str(part) for part in exc.absolute_path) or "<root>"
            raise BundleError(f"{instance_name} violates {schema_name} at {location}: {exc.message}") from exc


def _validate_manifest() -> None:
    manifest = _load_json(BUNDLE_ROOT / "bundle.json")
    _require(manifest.get("kind") == "static-registration-reference", "bundle kind drifted")
    _require(manifest.get("secretFree") is True, "bundle must be secret-free")
    _require(manifest.get("createsChatGptState") is False, "bundle must not create ChatGPT state")
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise BundleError("bundle files must be an object")
    expected_paths = {
        "APP_SETUP.md",
        "CAPABILITY_MATRIX.md",
        "PROJECT_INSTRUCTIONS.md",
        "README.md",
        "registration-reference.json",
        "SAFETY.md",
        "TEST_PROMPTS.md",
        "observed-wire-record.template.json",
    }
    _require(set(files.values()) == expected_paths, "bundle file inventory drifted")
    _require(
        {path.name for path in BUNDLE_ROOT.glob("*.md")} == EXPECTED_DOCUMENTS,
        "Markdown artifact inventory drifted from the exact six-file contract",
    )
    for filename in expected_paths - {"CAPABILITY_MATRIX.md"}:
        _require((BUNDLE_ROOT / filename).is_file(), f"missing hand-authored bundle file: {filename}")
    generated = manifest.get("generatedFiles", {}).get("CAPABILITY_MATRIX.md", {})
    _require(
        generated.get("source") == "skills/things-manager/references/capabilities.md",
        "generated capability source drifted",
    )
    _require(
        generated.get("generator") == "skills/things-manager/scripts/render_capabilities.py",
        "generated capability owner drifted",
    )


def _validate_registration() -> None:
    reference = _load_json(BUNDLE_ROOT / "registration-reference.json")
    connector = reference.get("connector", {})
    _require(connector.get("group") == "things", "ChatGPT must use the sole things group")
    _require(
        connector.get("publicResource") == "https://mcp.w4w.dev/mcp/things",
        "public resource drifted",
    )
    _require(
        connector.get("localBearerResource") == "http://127.0.0.1:46683/mcp/things",
        "local bearer route drifted",
    )
    _require(
        connector.get("remoteOAuthOrigin") == "http://127.0.0.1:46684/mcp/things",
        "remote OAuth route drifted",
    )
    _require(connector.get("toolCount") == 70, "tool coverage contracted")
    _require(
        connector.get("backendToolCounts") == {"things-core": 41, "things-shortcuts": 21, "things-native": 8},
        "backend partition drifted",
    )
    _require(connector.get("alternateThingsRoutesAllowed") is False, "alternate Things route enabled")

    oauth = reference.get("oauth", {})
    _require(
        oauth.get("requiredIndependentScopes") == ["things.read", "things.write", "things.admin"],
        "independent OAuth scopes drifted",
    )
    _require(oauth.get("scopeImplication") == "none", "OAuth scopes must imply none of one another")
    _require(
        oauth.get("refreshCapabilityScope") == "offline_access",
        "offline_access refresh capability drifted",
    )
    _require(
        oauth.get("refreshCapabilityRequirement") == "required-for-durable-chatgpt-profile",
        "durable ChatGPT profile must request offline_access",
    )
    _require(
        oauth.get("refreshCapabilitySemantics") == "refresh-only-no-things-authorization",
        "offline_access must never grant Things authorization",
    )
    _require(oauth.get("pkceCodeChallengeMethods") == ["S256"], "PKCE must be S256-only")
    _require(oauth.get("resourceIndicatorsRequired") is True, "resource indicator must be required")
    _require(oauth.get("authorizationResponseIssuerRequired") is True, "RFC 9207 issuer must be required")
    registration = oauth.get("registration", {})
    _require(registration.get("primary") == "client-id-metadata-document", "CIMD must remain primary")
    _require(
        registration.get("fallback") == "dynamic-client-registration-only-after-observation",
        "DCR must remain observation-gated fallback",
    )
    _require(registration.get("observedMode") is None, "bundle falsely claims an observed registration mode")
    _require(
        registration.get("candidateApprovalStatus") == "not-observed-not-approved",
        "documented registration candidates were falsely approved",
    )

    activation = reference.get("activation", {})
    _require(activation.get("remoteDefault") == "disabled", "remote ingress must default disabled")
    _require(activation.get("toolDispatchDefault") == "disabled", "tool dispatch must default disabled")
    _require(activation.get("observedWireStatus") == "not-observed", "bundle falsely claims wire evidence")
    _require(activation.get("mayCreateChatGptApp") is False, "bundle must not authorize app creation")
    _require(activation.get("mayEnablePublicIngress") is False, "bundle must not authorize ingress")


def _validate_observation_template() -> None:
    template = _load_json(BUNDLE_ROOT / "observed-wire-record.template.json")
    _require(template.get("schemaVersion") == "1.1.0", "observed-wire schema version drifted")
    _require(template.get("status") == "not-observed", "checked-in observation template must fail closed")
    _require(template.get("capturedAt") is None, "template must not claim a capture time")
    _require(template.get("expiresAt") is None, "template must not claim an expiry")
    _require(template.get("registrationMode") is None, "template must not claim a registration mode")
    _require(template.get("redirectUri") is None, "template must not approve a redirect URI")
    _require(template.get("redirectUriSha256") is None, "template must not claim a callback digest")
    _require(template.get("mcpProtocolVersion") is None, "template must not claim an MCP era")
    _require(template.get("modernDiscoveryObserved") is False, "template must not claim modern discovery")
    _require(
        template.get("requiredIndependentScopes") == ["things.read", "things.write", "things.admin"],
        "observation template Things scopes drifted",
    )
    _require(template.get("offlineAccessRequested") is False, "template must not claim offline_access")
    _require(
        template.get("offlineAccessSemantics") == "refresh-only-no-things-authorization",
        "observation template offline_access semantics drifted",
    )
    _require(template.get("resourceIndicatorObserved") is False, "template must not claim a resource indicator")
    _require(template.get("pkceS256Observed") is False, "template must not claim PKCE S256")
    _require(template.get("captureReceiptSha256") is None, "template must not claim a capture receipt")
    _require(
        template.get("routeStatuses")
        == {
            "mcp": None,
            "protectedResourceMetadata": None,
            "authorizationServerMetadata": None,
            "authorization": None,
            "registration": None,
        },
        "template must not claim observed route statuses",
    )
    _require(template.get("secretFree") is True, "observation template must be secret-free")
    _require(template.get("redactionsVerified") is False, "template must not claim redaction review")
    _require(template.get("prohibitedDataAbsent") is True, "template must contain no prohibited data")
    _require(template.get("evidenceDigestSha256") is None, "template must not carry an evidence digest")
    _require("notes" not in template, "observation template must not admit free-form notes")


def _validate_documentation() -> None:
    texts = {name: (BUNDLE_ROOT / name).read_text(encoding="utf-8") for name in EXPECTED_DOCUMENTS}
    aggregate = "\n".join(texts.values())
    for prohibited in PROHIBITED_BUNDLE_TEXT:
        _require(prohibited not in aggregate, f"prohibited bundle guidance survives: {prohibited}")
    for required in (
        "https://mcp.w4w.dev/mcp/things",
        "`things`",
        "70",
        "41",
        "21",
        "8",
        "offline_access",
        "Scan Tools",
        "things.read",
        "things.write",
        "things.admin",
        "S256",
    ):
        _require(required in aggregate, f"bundle documentation lacks required contract: {required}")
    _require(
        "do not hand-edit `capability_matrix.md`" in texts["README.md"].lower(),
        "generated ownership unclear",
    )
    _require("not-observed" in texts["README.md"], "README must disclose missing wire evidence")
    setup = texts["APP_SETUP.md"]
    for required in (
        "exact `/mcp/things` endpoint",
        "local-only",
        "remote ingress disabled",
        "Authorized OAuth rollout",
        "Local refresh and test",
        "Emergency disable",
        "Manual prerequisites",
        "Account and workspace limits",
        "typed unavailable/degraded result",
        "does not create a ChatGPT app",
    ):
        _require(required in setup, f"APP_SETUP.md lacks required operator contract: {required}")
    _require(
        "Remote contract (implementation/apply authorized; activation evidence gated)" in texts["CAPABILITY_MATRIX.md"],
        "CAPABILITY_MATRIX.md must label remote implementation as authorized and activation as evidence-gated",
    )


def _validate_owned_source_docs() -> None:
    try:
        texts = {name: path.read_text(encoding="utf-8") for name, path in OWNED_SOURCE_DOCS.items()}
    except FileNotFoundError as exc:
        raise BundleError(f"missing owned source documentation: {exc.filename}") from exc
    aggregate = "\n".join(texts.values())
    for prohibited in PROHIBITED_BUNDLE_TEXT:
        _require(prohibited not in aggregate, f"prohibited source guidance survives: {prohibited}")

    for name in ("operator", "runtime"):
        text = texts[name]
        normalized = " ".join(text.split())
        for required in (
            "http://127.0.0.1:46683/mcp/things",
            "http://127.0.0.1:46684/mcp/things",
            "https://mcp.w4w.dev/mcp/things",
            "41",
            "21",
            "8",
            "things.read",
            "things.write",
            "things.admin",
            "S256",
        ):
            _require(required in text, f"{name} source lacks Things++ contract: {required}")
        _require("default disabled" in normalized, f"{name} source must keep remote activation fail-closed")
        _require("Client ID Metadata" in normalized, f"{name} source must document CIMD primary registration")
        _require("Dynamic Client Registration" in normalized, f"{name} source must document DCR fallback")

    _require(
        "GENERATED-AUTHORING: source=skills/things-manager/SKILL.md" in texts["authoring"],
        "Things Manager authoring projection lost its source marker",
    )
    _require("sole Things++ MCPHub" in texts["authoring"], "Things Manager authoring source is not v2")
    _require("exact catalog is 70 qualified tools" in texts["research"], "Things Manager research is stale")
    _require("runtime has been locally applied" in texts["knowledge"], "KB must separate source from runtime proof")


def _validate_generated_capabilities() -> None:
    try:
        source = SOURCE_CAPABILITIES.read_bytes()
        generated = GENERATED_CAPABILITIES.read_bytes()
    except FileNotFoundError as exc:
        raise BundleError("generated ChatGPT CAPABILITY_MATRIX.md is missing") from exc
    _require(generated == source, "generated ChatGPT capability matrix drifted from the canonical ledger")
    text = generated.decode("utf-8")
    _require("exactly 70 public tools" in text, "generated capability copy lacks exact tool closure")
    _require("Group: `things`" in text, "generated capability copy lacks sole-group contract")


def validate_bundle(*, require_generated_capabilities: bool = False) -> None:
    """Validate the hand-authored bundle and optionally the generated ledger copy."""
    _validate_json_references()
    _validate_json_schemas()
    _validate_manifest()
    _validate_registration()
    _validate_observation_template()
    _validate_documentation()
    _validate_owned_source_docs()
    if require_generated_capabilities:
        _validate_generated_capabilities()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-generated-capabilities",
        action="store_true",
        help="Also require CAPABILITY_MATRIX.md to be an exact copy of the canonical generated ledger",
    )
    args = parser.parse_args()
    try:
        validate_bundle(require_generated_capabilities=args.require_generated_capabilities)
    except BundleError as exc:
        print(f"things-plus-plus ChatGPT bundle invalid: {exc}")
        return 1
    print("things-plus-plus ChatGPT bundle valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
