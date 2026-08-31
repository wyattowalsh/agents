"""Frozen upstream inventory and adapted public schema policy."""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from importlib.resources import files
from typing import Any, Literal

from things_common import canonical_schema_sha256, canonical_sha256

MAX_BATCH_ITEMS = 25
MAX_RESULT_KEYS = 100
Scope = Literal["things.read", "things.write", "things.admin"]
_EXPECTED_PACKAGE = "mcp-server-things"
_EXPECTED_VERSION = "1.9.0"
_DIAGNOSTIC_TOOLS = frozenset({
    "context_stats",
    "get_server_capabilities",
    "get_usage_recommendations",
    "health_check",
    "queue_status",
})
_UNSAFE_FIELD_NAMES = frozenset({
    "applescript",
    "command",
    "config",
    "environment",
    "executable",
    "file",
    "path",
    "payload",
    "raw",
    "script",
    "shell",
    "shortcut",
    "sql",
    "url",
})
_IDENTIFIER_FIELDS = frozenset({
    "area",
    "area_id",
    "id",
    "list_id",
    "project_id",
    "project_uuid",
    "record_ids",
    "todo_id",
    "todo_ids",
})
_IDENTIFIER_LIST_FIELDS = frozenset({"record_ids", "todo_ids"})
_LIST_FIELDS = frozenset({"checklist_items", "items", "tags", "todo_ids"})
_URI_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_TEXT_LIMITS = {
    "notes": 20_000,
    "todos": 20_000,
    "query": 1_024,
    "title": 512,
    "list_title": 512,
    "area_title": 512,
    "heading": 512,
    "tag": 512,
    "tag_name": 512,
    "destination": 512,
    "operation": 128,
    "mode": 32,
    "period": 32,
    "status": 32,
    "type": 32,
    "when": 128,
    "deadline": 128,
    "start_date": 128,
}
_MODE_VALUES = ["auto", "summary", "minimal", "standard", "detailed"]
_PHASE_SCHEMA: dict[str, Any] = {
    "description": "Preview or execute this exact mutation.",
    "enum": ["preview", "execute"],
    "type": "string",
}
_RECEIPT_SCHEMA: dict[str, Any] = {
    "anyOf": [
        {"minLength": 43, "maxLength": 128, "pattern": r"^[A-Za-z0-9_-]+$", "type": "string"},
        {"type": "null"},
    ],
    "default": None,
    "description": "Opaque receipt returned by preview; required for execute.",
}


class CoreContractError(ValueError):
    """A frozen contract, adapted schema, or request violates policy."""


@dataclass(frozen=True, slots=True)
class ToolContract:
    """One audited upstream tool plus its public security policy."""

    name: str
    description: str
    scope: Scope
    risk: str
    annotations: dict[str, bool]
    schema_contract_id: str
    upstream_input_schema: dict[str, Any]
    upstream_output_schema: dict[str, Any]
    audited_input_sha256: str
    audited_output_sha256: str

    @property
    def mutating(self) -> bool:
        return self.scope != "things.read"

    @property
    def diagnostic(self) -> bool:
        return self.name in _DIAGNOSTIC_TOOLS


def _read_json(name: str) -> dict[str, Any]:
    resource = files("things_core").joinpath(name)
    return json.loads(resource.read_text(encoding="utf-8"))


def load_contracts() -> tuple[ToolContract, ...]:
    """Load contracts in the audited upstream registration order."""
    upstream = _read_json("upstream_contract.json")
    manifest = _read_json("core_manifest.json")
    rows = {row["name"]: row for row in manifest["tools"]}
    contracts: list[ToolContract] = []
    for tool in upstream["tools"]:
        row = rows.get(tool["name"])
        if row is None:
            raise CoreContractError("Frozen upstream tool is absent from the capability manifest.")
        hashes = row["auditedUpstreamSchemaHashes"]
        contracts.append(
            ToolContract(
                name=tool["name"],
                description=tool.get("description") or f"Audited upstream Things operation {tool['name']}.",
                scope=row["scope"],
                risk=row["risk"],
                annotations=dict(row["annotations"]),
                schema_contract_id=row["schemaContractId"],
                upstream_input_schema=tool["inputSchema"],
                upstream_output_schema=tool["outputSchema"],
                audited_input_sha256=hashes["inputSchemaSha256"],
                audited_output_sha256=hashes["outputSchemaSha256"],
            )
        )
    return tuple(contracts)


def validate_frozen_contract() -> tuple[ToolContract, ...]:
    """Fail closed if frozen names or audited schemas differ from the manifest."""
    upstream = _read_json("upstream_contract.json")
    manifest = _read_json("core_manifest.json")
    provenance = manifest["provenance"]
    if upstream.get("package") != _EXPECTED_PACKAGE or manifest.get("package") != _EXPECTED_PACKAGE:
        raise CoreContractError("Frozen upstream package identity mismatch.")
    if upstream.get("version") != _EXPECTED_VERSION or manifest.get("version") != _EXPECTED_VERSION:
        raise CoreContractError("Frozen upstream version mismatch.")
    contracts = load_contracts()
    if len(contracts) != 41 or len({item.name for item in contracts}) != 41:
        raise CoreContractError("Things core must expose exactly 41 unique tools.")
    ordered_names = [item.name for item in contracts]
    if canonical_sha256(ordered_names) != provenance["orderedToolNamesSha256"]:
        raise CoreContractError("Audited upstream ordered tool-name digest mismatch.")
    if canonical_sha256(sorted(ordered_names)) != provenance["sortedToolNamesSha256"]:
        raise CoreContractError("Audited upstream sorted tool-name digest mismatch.")
    if set(ordered_names) != {row["name"] for row in manifest["tools"]}:
        raise CoreContractError("Frozen upstream and manifest tool sets differ.")
    for contract in contracts:
        if canonical_schema_sha256(contract.upstream_input_schema) != contract.audited_input_sha256:
            raise CoreContractError(f"Audited input schema mismatch for {contract.name}.")
        if canonical_schema_sha256(contract.upstream_output_schema) != contract.audited_output_sha256:
            raise CoreContractError(f"Audited output schema mismatch for {contract.name}.")
        if contract.audited_output_sha256 != provenance["commonOutputSchemaSha256"]:
            raise CoreContractError(f"Unexpected upstream output schema for {contract.name}.")
        if contract.scope not in {"things.read", "things.write", "things.admin"}:
            raise CoreContractError(f"Invalid independent scope for {contract.name}.")
        if contract.annotations.get("readOnlyHint") != (contract.scope == "things.read"):
            raise CoreContractError(f"Read-only annotation mismatch for {contract.name}.")
    return contracts


def _nullable_branch(schema: dict[str, Any]) -> dict[str, Any] | None:
    branches = schema.get("anyOf")
    if not isinstance(branches, list):
        return None
    for branch in branches:
        if isinstance(branch, dict) and branch.get("type") != "null":
            return branch
    return None


def _apply_string_bound(schema: dict[str, Any], field_name: str) -> None:
    limit = 256 if field_name in _IDENTIFIER_FIELDS else _TEXT_LIMITS.get(field_name, 4_096)
    schema["maxLength"] = min(int(schema.get("maxLength", limit)), limit)
    if field_name in _IDENTIFIER_FIELDS:
        schema["minLength"] = max(int(schema.get("minLength", 0)), 1)
    schema.setdefault("pattern", r"^[^\x00\x7f]*$")


def _adapt_property(field_name: str, raw: dict[str, Any]) -> dict[str, Any]:
    schema = copy.deepcopy(raw)
    branch = _nullable_branch(schema)
    target = branch if branch is not None else schema
    value_type = target.get("type")
    if field_name == "mode":
        target.clear()
        target.update({"enum": _MODE_VALUES, "type": "string"})
    elif field_name == "limit":
        target.update({"type": "integer", "minimum": 1, "maximum": MAX_BATCH_ITEMS})
        if isinstance(schema.get("default"), int) and schema["default"] > MAX_BATCH_ITEMS:
            schema["default"] = MAX_BATCH_ITEMS
    elif field_name == "offset":
        target.update({"type": "integer", "minimum": 0, "maximum": 10_000})
    elif field_name == "days":
        target.update({"type": "integer", "minimum": 1, "maximum": 365})
    elif field_name == "max_concurrent":
        target.update({"type": "integer", "minimum": 1, "maximum": 10})
    elif value_type == "array":
        target["maxItems"] = min(int(target.get("maxItems", MAX_BATCH_ITEMS)), MAX_BATCH_ITEMS)
        target.setdefault("items", {"type": "string", "maxLength": 512})
        if isinstance(target.get("items"), dict) and target["items"].get("type") == "string":
            _apply_string_bound(target["items"], field_name)
    elif value_type == "object":
        target["additionalProperties"] = False
        for nested_name, nested in list(target.get("properties", {}).items()):
            target["properties"][nested_name] = _adapt_property(nested_name, nested)
    elif value_type == "string" or value_type is None:
        target.setdefault("type", "string")
        _apply_string_bound(target, field_name)
    if field_name in _LIST_FIELDS and target.get("type") == "string":
        target["maxLength"] = min(target.get("maxLength", 8_192), 8_192)
    schema["description"] = f"Closed typed {field_name.replace('_', ' ')} input for this audited operation."
    return schema


def adapted_input_schema(contract: ToolContract) -> dict[str, Any]:
    """Return the closed, bounded public schema for one upstream operation."""
    source = contract.upstream_input_schema
    properties: dict[str, Any] = {}
    for name, raw in source.get("properties", {}).items():
        if contract.diagnostic and name == "request":
            continue
        if name.casefold() in _UNSAFE_FIELD_NAMES:
            raise CoreContractError(f"Unsafe executable selector field in upstream schema: {contract.name}.{name}")
        properties[name] = _adapt_property(name, raw)
    required = [name for name in source.get("required", []) if name in properties]
    if contract.mutating:
        properties["mutationPhase"] = copy.deepcopy(_PHASE_SCHEMA)
        properties["mutationReceipt"] = copy.deepcopy(_RECEIPT_SCHEMA)
        required.append("mutationPhase")
    return {
        "additionalProperties": False,
        "properties": properties,
        "required": required,
        "type": "object",
    }


def adapted_output_schema() -> dict[str, Any]:
    """Return the one closed result envelope used by all 41 tools."""
    # Kept explicit rather than derived from a framework-specific Pydantic
    # dialect so its digest remains stable across FastMCP releases.
    return {
        "additionalProperties": False,
        "properties": {
            "tool": {"pattern": r"^[a-z0-9][a-z0-9_]{0,127}$", "type": "string"},
            "status": {
                "enum": ["read", "previewed", "changed", "skipped", "failed", "ambiguous"],
                "type": "string",
            },
            "mutationReceipt": {
                "anyOf": [
                    {"minLength": 43, "maxLength": 128, "type": "string"},
                    {"type": "null"},
                ],
                "default": None,
            },
            "receiptId": {
                "anyOf": [{"pattern": r"^[0-9a-f]{16}$", "type": "string"}, {"type": "null"}],
                "default": None,
            },
            "targetCount": {"maximum": 25, "minimum": 0, "type": "integer"},
            "changedCount": {"maximum": 25, "minimum": 0, "type": "integer"},
            "skippedCount": {"maximum": 25, "minimum": 0, "type": "integer"},
            "failedCount": {"maximum": 25, "minimum": 0, "type": "integer"},
            "ambiguousCount": {"maximum": 25, "minimum": 0, "type": "integer"},
            "readbackVerified": {"type": "boolean"},
            "truncated": {"type": "boolean"},
            "payload": {
                "anyOf": [
                    {
                        "additionalProperties": False,
                        "properties": {
                            "sourceKind": {
                                "enum": ["object", "array", "scalar", "null"],
                                "type": "string",
                            },
                            "entries": {
                                "items": {
                                    "additionalProperties": False,
                                    "properties": {
                                        "path": {
                                            "maxLength": 2_048,
                                            "minLength": 1,
                                            "pattern": r"^[^\x00\x7f]+$",
                                            "type": "string",
                                        },
                                        "value": {
                                            "maxLength": 20_000,
                                            "type": ["string", "boolean", "number", "null"],
                                        },
                                    },
                                    "required": ["path", "value"],
                                    "type": "object",
                                },
                                "maxItems": 500,
                                "type": "array",
                            },
                        },
                        "required": ["sourceKind", "entries"],
                        "type": "object",
                    },
                    {"type": "null"},
                ]
            },
            "messageCode": {"pattern": r"^[a-z0-9][a-z0-9_.-]{0,95}$", "type": "string"},
        },
        "required": [
            "tool",
            "status",
            "mutationReceipt",
            "receiptId",
            "targetCount",
            "changedCount",
            "skippedCount",
            "failedCount",
            "ambiguousCount",
            "readbackVerified",
            "truncated",
            "payload",
            "messageCode",
        ],
        "type": "object",
    }


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    return False


def _validate_value(value: Any, schema: dict[str, Any], path: str) -> None:
    if "anyOf" in schema:
        errors = 0
        for branch in schema["anyOf"]:
            try:
                _validate_value(value, branch, path)
                return
            except CoreContractError:
                errors += 1
        raise CoreContractError(f"{path} does not match its closed type ({errors} branches checked).")
    expected = schema.get("type")
    if expected is not None and not _matches_type(value, expected):
        raise CoreContractError(f"{path} has the wrong type.")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", len(value)):
            raise CoreContractError(f"{path} violates its length bound.")
        if (pattern := schema.get("pattern")) and re.fullmatch(pattern, value) is None:
            raise CoreContractError(f"{path} violates its format constraint.")
        if schema.get("enum") is not None and value not in schema["enum"]:
            raise CoreContractError(f"{path} is not an allowed value.")
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", len(value)):
            raise CoreContractError(f"{path} violates the 25-item bound.")
        if len({json.dumps(item, sort_keys=True) for item in value}) != len(value) and path.endswith("todo_ids"):
            raise CoreContractError(f"{path} contains duplicate target identifiers.")
        item_schema = schema.get("items", {})
        for index, item in enumerate(value):
            _validate_value(item, item_schema, f"{path}[{index}]")
    elif isinstance(value, dict) and expected == "object":
        allowed = schema.get("properties", {})
        if schema.get("additionalProperties") is False and set(value) - set(allowed):
            raise CoreContractError(f"{path} contains an undeclared field.")
        for required in schema.get("required", []):
            if required not in value:
                raise CoreContractError(f"{path}.{required} is required.")
        for name, item in value.items():
            if name in allowed:
                _validate_value(item, allowed[name], f"{path}.{name}")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if value < schema.get("minimum", value) or value > schema.get("maximum", value):
            raise CoreContractError(f"{path} violates its numeric bound.")


def _validate_opaque_identifier(value: str, field_name: str) -> None:
    candidate = value.strip()
    if (
        _URI_SCHEME.match(candidate)
        or "/" in candidate
        or "\\" in candidate
        or candidate in {".", ".."}
        or candidate.startswith("~")
        or any(token in candidate for token in (";", "`", "$(", "\n", "\r"))
    ):
        raise CoreContractError(f"{field_name} is not a valid opaque identifier.")


def _validate_non_schema_policy(arguments: dict[str, Any]) -> None:
    for name, value in arguments.items():
        if name.casefold() in _UNSAFE_FIELD_NAMES:
            raise CoreContractError("Arbitrary executable selectors are not accepted.")
        if isinstance(value, str):
            if name in _IDENTIFIER_FIELDS:
                identifiers = (
                    [item.strip() for item in re.split(r"[,\n]", value) if item.strip()]
                    if name in _IDENTIFIER_LIST_FIELDS
                    else [value]
                )
                for identifier in identifiers:
                    _validate_opaque_identifier(identifier, name)
            lowered = value.casefold()
            if "things://" in lowered or "file://" in lowered:
                raise CoreContractError(f"{name} may not contain a caller-supplied URL.")
            if name == "todos":
                items = [item.strip() for item in value.splitlines() if item.strip()]
                if len(items) > MAX_BATCH_ITEMS:
                    raise CoreContractError("todos must contain at most 25 newline-delimited entries.")
            elif name in _LIST_FIELDS:
                items = [item.strip() for item in re.split(r"[,\n]", value) if item.strip()]
                if not items or len(items) > MAX_BATCH_ITEMS or len(set(items)) != len(items):
                    raise CoreContractError(f"{name} must contain at most 25 unique values.")
        elif isinstance(value, list) and name in _IDENTIFIER_FIELDS:
            for identifier in value:
                if isinstance(identifier, str):
                    _validate_opaque_identifier(identifier, name)
        elif isinstance(value, dict):
            _validate_non_schema_policy(value)


def validate_arguments(contract: ToolContract, arguments: dict[str, Any]) -> dict[str, Any]:
    """Validate a request against the public schema and cross-field rules."""
    if not isinstance(arguments, dict):
        raise CoreContractError("Tool arguments must be an object.")
    schema = adapted_input_schema(contract)
    _validate_value(arguments, schema, "arguments")
    _validate_non_schema_policy(arguments)
    if contract.mutating:
        phase = arguments["mutationPhase"]
        receipt = arguments.get("mutationReceipt")
        if phase == "preview" and receipt is not None:
            raise CoreContractError("mutationReceipt is forbidden during preview.")
        if phase == "execute" and not receipt:
            raise CoreContractError("mutationReceipt is required during execute.")
    return copy.deepcopy(arguments)


def upstream_arguments(contract: ToolContract, arguments: dict[str, Any]) -> dict[str, Any]:
    """Remove the adapter envelope without changing upstream domain semantics."""
    return {key: value for key, value in arguments.items() if key not in {"mutationPhase", "mutationReceipt"}}


def public_description(contract: ToolContract) -> str:
    """Return a sanitized model-facing description derived from manifest policy."""
    operation = contract.name.replace("_", " ")
    if contract.diagnostic:
        return f"Return bounded, content-free status for the audited {operation} capability."
    if not contract.mutating:
        return f"Run the audited typed {operation} read with closed bounded inputs and normalized redacted output."
    return (
        f"Preview or execute the audited typed {operation} mutation. "
        "Execute requires its matching opaque single-use receipt and conservative read-after-write verification."
    )


def diagnostic_tool_names() -> frozenset[str]:
    return _DIAGNOSTIC_TOOLS
