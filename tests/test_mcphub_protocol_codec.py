"""Hermetic conformance checks for the MCPHub Things dual-era public codec."""

from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import cast

from fastmcp import Client, FastMCP
from jsonschema import Draft202012Validator, ValidationError

from things_core.server import build_server
from things_native.app import mcp as native_mcp
from things_shortcuts.app import mcp as shortcuts_mcp

ROOT = Path(__file__).resolve().parents[1]
DOWNSTREAM = ROOT / "mcp" / "mcphub" / "downstream"
PROTOCOL_SOURCE = DOWNSTREAM / "src" / "protocol"
PROTOCOL_FIXTURES = DOWNSTREAM / "fixtures" / "protocol"
CAPABILITY_MANIFEST = (
    ROOT / "openspec" / "changes" / "replace-supathings-with-things-plus-plus" / "capability-manifest.json"
)
REPORT_SCHEMA = ROOT / "config" / "schemas" / "mcphub-downstream-conformance.schema.json"
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
CONFORMANCE_CASE_IDS = [
    "modern-discover",
    "modern-list",
    "modern-call",
    "legacy-initialize",
    "legacy-list",
    "auth-absent-modern",
    "auth-absent-legacy",
    "scope-missing",
    "scope-extra",
    "resource-mismatch",
    "credential-class-mismatch",
    "principal-invalid",
    "client-invalid",
    "session-id-forbidden",
    "last-event-id-forbidden",
    "get-method-forbidden",
    "method-mismatch",
    "name-mismatch",
    "missing-client-capabilities",
    "unsupported-version",
    "unknown-modern-method",
    "parse-error",
]


def _json(path: Path) -> dict[str, object]:
    return _object(json.loads(path.read_text(encoding="utf-8")))


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise TypeError("expected string-keyed object")
    return cast("dict[str, object]", value)


def _object_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise TypeError("expected object list")
    return [_object(entry) for entry in value]


def _integer(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("expected integer")
    return value


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode()


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _manifest_projection(manifest: dict[str, object]) -> dict[str, object]:
    group = _object(manifest["group"])
    counts = _object(manifest["counts"])
    rows = _object_list(manifest["tools"])
    return {
        "schemaVersion": 1,
        "group": {
            key: group[key] for key in ("name", "localPath", "remotePath", "localResource", "remoteResource", "servers")
        },
        "counts": {
            key: counts[key]
            for key in (
                "tools",
                "coreTools",
                "shortcutTools",
                "nativeTools",
                "supaOutcomes",
                "workflows",
                "legacyEvalIds",
                "newEvalIds",
            )
        },
        "tools": [
            {
                **{
                    key: row[key]
                    for key in (
                        "server",
                        "serverToolName",
                        "publicToolName",
                        "expectedMcphubQualifiedName",
                        "qualifiedCapabilityId",
                        "minimumIndependentScope",
                        "risk",
                        "annotations",
                        "schemaContractId",
                        "adaptedSchemaHashes",
                        "backendPrerequisites",
                        "implementationKind",
                        "testIds",
                    )
                },
                "auditedUpstreamSchemaHashes": row.get("auditedUpstreamSchemaHashes"),
            }
            for row in rows
        ],
    }


async def _source_tools() -> dict[str, list[dict[str, object]]]:
    servers: dict[str, FastMCP] = {
        "things-core": build_server(),
        "things-shortcuts": shortcuts_mcp,
        "things-native": native_mcp,
    }
    result: dict[str, list[dict[str, object]]] = {}
    for name, server in servers.items():
        async with Client(server) as client:
            tools = await client.list_tools()
        result[name] = [_object(tool.model_dump(by_alias=True, exclude_none=True)) for tool in tools]
    return result


def test_exact_seventy_tool_provider_catalog_matches_the_frozen_manifest() -> None:
    manifest = _json(CAPABILITY_MANIFEST)
    rows = _object_list(manifest["tools"])
    source = asyncio.run(_source_tools())
    assert {server: len(tools) for server, tools in source.items()} == {
        "things-core": 41,
        "things-shortcuts": 21,
        "things-native": 8,
    }

    source_by_identity: dict[tuple[object, object], dict[str, object]] = {}
    for server in ("things-core", "things-shortcuts", "things-native"):
        manifest_rows = [row for row in rows if row["server"] == server]
        tools = source[server]
        assert {tool["name"] for tool in tools} == {row["serverToolName"] for row in manifest_rows}
        source_by_identity.update({(server, tool["name"]): tool for tool in tools})

    normalized_catalog: list[dict[str, object]] = []
    missing_schema_contract_metadata: list[object] = []
    for row in rows:
        tool = source_by_identity[row["server"], row["serverToolName"]]
        assert set(tool) == {"_meta", "annotations", "description", "inputSchema", "name", "outputSchema"}
        input_schema = _object(tool["inputSchema"])
        output_schema = _object(tool["outputSchema"])
        metadata = _object(tool["_meta"])
        assert input_schema["type"] == "object"
        assert input_schema["additionalProperties"] is False
        assert output_schema["type"] == "object"
        assert output_schema["additionalProperties"] is False
        hashes = _object(row["adaptedSchemaHashes"])
        assert _sha256(input_schema) == hashes["inputSchemaSha256"]
        assert _sha256(output_schema) == hashes["outputSchemaSha256"]
        assert tool["annotations"] == row["annotations"]
        assert metadata["thingsMinimumScope"] == row["minimumIndependentScope"]
        assert metadata["thingsRisk"] == row["risk"]
        if "thingsSchemaContractId" not in metadata:
            missing_schema_contract_metadata.append(row["qualifiedCapabilityId"])
        else:
            assert metadata["thingsSchemaContractId"] == row["schemaContractId"]
        security_schemes = _object_list(metadata["securitySchemes"])
        assert any(
            scheme.get("type") == "oauth2" and scheme.get("scopes") == [row["minimumIndependentScope"]]
            for scheme in security_schemes
        )
        normalized_catalog.append({**tool, "name": row["publicToolName"]})

    assert len(normalized_catalog) == 70
    assert len({tool["name"] for tool in normalized_catalog}) == 70
    assert missing_schema_contract_metadata == []
    assert SHA256_PATTERN.fullmatch(_sha256(normalized_catalog))


def test_protocol_fixtures_freeze_exact_modern_legacy_and_error_shapes() -> None:
    modern_request = _json(PROTOCOL_FIXTURES / "modern-discover.request.json")
    modern_response = _json(PROTOCOL_FIXTURES / "modern-discover.response.json")
    legacy_request = _json(PROTOCOL_FIXTURES / "legacy-initialize.request.json")
    legacy_response = _json(PROTOCOL_FIXTURES / "legacy-initialize.response.json")
    error_matrix = _json(PROTOCOL_FIXTURES / "error-matrix.json")

    modern_headers = _object(modern_request["headers"])
    modern_body = _object(modern_request["body"])
    assert modern_headers == {
        "content-type": "application/json",
        "mcp-method": "server/discover",
        "mcp-protocol-version": "2026-07-28",
    }
    modern_params = _object(modern_body["params"])
    modern_meta = _object(modern_params["_meta"])
    assert modern_meta["io.modelcontextprotocol/protocolVersion"] == "2026-07-28"
    assert modern_meta["io.modelcontextprotocol/clientCapabilities"] == {}
    modern_result = _object(modern_response["result"])
    assert modern_result["supportedVersions"] == ["2026-07-28"]
    assert {key: modern_result[key] for key in ("resultType", "ttlMs", "cacheScope")} == {
        "resultType": "complete",
        "ttlMs": 0,
        "cacheScope": "private",
    }

    legacy_headers = _object(legacy_request["headers"])
    legacy_result = _object(legacy_response["result"])
    assert legacy_headers["mcp-protocol-version"] == "2025-11-25"
    assert "text/event-stream" in str(legacy_headers["accept"])
    assert legacy_result["protocolVersion"] == "2025-11-25"
    assert not {"resultType", "ttlMs", "cacheScope"} & legacy_result.keys()

    cases = _object_list(error_matrix["cases"])
    assert [case["id"] for case in cases] == [
        "method-mismatch",
        "name-mismatch",
        "missing-client-capabilities",
        "unsupported-version",
        "unknown-modern-method",
        "parse-error",
    ]
    assert {(case["status"], case["code"]) for case in cases} == {
        (400, -32020),
        (400, -32021),
        (400, -32022),
        (404, -32601),
        (400, -32700),
    }
    assert all(not case["providerDispatch"] for case in cases)


def test_conformance_report_schema_is_closed_and_digest_bound() -> None:
    schema = _json(REPORT_SCHEMA)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    manifest = _json(CAPABILITY_MANIFEST)
    projection = _manifest_projection(manifest)
    rows = _object_list(projection["tools"])
    source = asyncio.run(_source_tools())
    by_identity: dict[tuple[object, object], dict[str, object]] = {
        (server, tool["name"]): tool for server, tools in source.items() for tool in tools
    }
    normalized_catalog = [
        {
            **by_identity[row["server"], row["serverToolName"]],
            "name": row["publicToolName"],
        }
        for row in rows
    ]
    report = _json(PROTOCOL_FIXTURES / "conformance-report.json")
    validator.validate(report)
    report_catalog = _object(report["catalog"])
    assert report_catalog["catalogSha256"] == _sha256(normalized_catalog)
    assert report_catalog["scopeMapSha256"] == _sha256([
        {"name": row["publicToolName"], "minimumScope": row["minimumIndependentScope"]} for row in rows
    ])
    assert report_catalog["manifestProjectionSha256"] == _sha256(projection)
    execution = _object(report["execution"])
    cases = _object_list(execution["cases"])
    assert execution["status"] == "passed"
    assert execution["caseCount"] == len(CONFORMANCE_CASE_IDS) == 22
    assert execution["passedCaseCount"] == len(CONFORMANCE_CASE_IDS)
    assert execution["caseIds"] == CONFORMANCE_CASE_IDS
    assert [case["id"] for case in cases] == CONFORMANCE_CASE_IDS
    assert all(case["status"] == "passed" for case in cases)
    assert all(SHA256_PATTERN.fullmatch(str(case["resultSha256"])) for case in cases)
    assert execution["sdkDispatchCount"] == sum(_integer(case["sdkDispatchCount"]) for case in cases) == 6
    assert execution["providerDispatchCount"] == sum(_integer(case["providerDispatchCount"]) for case in cases) == 1
    error_matrix = _json(PROTOCOL_FIXTURES / "error-matrix.json")
    matrix_rows = _object_list(error_matrix["cases"])
    assert execution["errorMatrixSha256"] == _sha256(error_matrix)
    cases_by_id = {case["id"]: case for case in cases}
    actual_matrix = [
        {
            "id": cases_by_id[row["id"]]["id"],
            "httpStatus": cases_by_id[row["id"]]["httpStatus"],
            "jsonRpcCode": cases_by_id[row["id"]]["jsonRpcCode"],
            "sdkDispatchCount": cases_by_id[row["id"]]["sdkDispatchCount"],
            "providerDispatchCount": cases_by_id[row["id"]]["providerDispatchCount"],
        }
        for row in matrix_rows
    ]
    assert execution["errorMatrixResultsSha256"] == _sha256(actual_matrix)
    assert execution["resultBundleSha256"] == _sha256(cases)
    for row in matrix_rows:
        result = cases_by_id[row["id"]]
        assert result["httpStatus"] == row["status"]
        assert result["jsonRpcCode"] == row["code"]
        assert result["sdkDispatchCount"] == int(bool(row["sdkDispatch"]))
        assert result["providerDispatchCount"] == int(bool(row["providerDispatch"]))

    invalid_reports: list[tuple[str, dict[str, object]]] = []
    missing_execution = copy.deepcopy(report)
    del missing_execution["execution"]
    invalid_reports.append(("missing-execution", missing_execution))
    skipped = copy.deepcopy(report)
    _object_list(_object(skipped["execution"])["cases"])[0]["status"] = "skipped"
    invalid_reports.append(("skipped-case", skipped))
    missing_case = copy.deepcopy(report)
    cast("list[object]", _object(missing_case["execution"])["cases"]).pop()
    invalid_reports.append(("missing-case", missing_case))
    reordered = copy.deepcopy(report)
    reordered_ids = cast("list[object]", _object(reordered["execution"])["caseIds"])
    reordered_ids[0], reordered_ids[1] = reordered_ids[1], reordered_ids[0]
    invalid_reports.append(("reordered-case-ids", reordered))
    bad_digest = copy.deepcopy(report)
    _object(bad_digest["execution"])["resultBundleSha256"] = "0" * 63
    invalid_reports.append(("bad-digest", bad_digest))
    incomplete = copy.deepcopy(report)
    _object(incomplete["execution"])["passedCaseCount"] = 21
    invalid_reports.append(("incomplete-count", incomplete))
    invalid_reports.append(("extra-root-field", {**report, "unexpected": True}))
    for label, invalid in invalid_reports:
        try:
            validator.validate(invalid)
        except ValidationError:
            pass
        else:
            raise AssertionError(f"conformance report schema accepted invalid evidence: {label}")


def test_protocol_lane_uses_exact_v2_sdk_and_has_static_v1_import_isolation() -> None:
    package = _json(DOWNSTREAM / "package.json")
    dependencies = _object(package["dependencies"])
    assert dependencies["@modelcontextprotocol/server"] == "2.0.0"
    assert dependencies["@modelcontextprotocol/sdk"] == "1.29.0"
    sources = {path.name: path.read_text(encoding="utf-8") for path in sorted(PROTOCOL_SOURCE.glob("*.ts"))}
    assert sources
    assert all("@modelcontextprotocol/sdk" not in source for source in sources.values())
    public_imports = {
        match
        for source in sources.values()
        for match in re.findall(r'from\s+["\'](@modelcontextprotocol/[^"\']+)["\']', source)
    }
    assert public_imports == {"@modelcontextprotocol/server"}


def test_conformance_client_proves_discover_then_list_without_server_sequence_state() -> None:
    source = (PROTOCOL_SOURCE / "conformance.ts").read_text(encoding="utf-8")
    discover_call = 'modernRequest(modernBody(1, "server/discover"))'
    list_call = 'modernRequest(modernBody(2, "tools/list"))'
    assert source.index(discover_call) < source.index(list_call)
    assert "export function buildProtocolConformanceReport" not in source
    server_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (PROTOCOL_SOURCE / "handler.ts", PROTOCOL_SOURCE / "server-factory.ts")
    )
    assert "discoverRequired" not in server_sources
    assert "discoveredClients" not in server_sources
    assert "sessionIdGenerator" not in server_sources
