"""Manifest-driven FastMCP registration for the 41-tool core adapter."""

from __future__ import annotations

import argparse
import inspect
import json
from typing import Any, cast

from fastmcp import Context, FastMCP
from fastmcp.tools import FunctionTool

from .adapter import ThingsCoreAdapter
from .backend import auth_doctor
from .contracts import adapted_input_schema, adapted_output_schema, public_description, validate_frozen_contract
from .models import CoreToolResult
from .provenance import provenance_doctor


def _meta(scope: str, risk: str, contract_id: str) -> dict[str, Any]:
    return {
        "securitySchemes": [{"type": "oauth2", "scopes": [scope]}],
        "thingsMinimumScope": scope,
        "thingsRisk": risk,
        "thingsSchemaContractId": contract_id,
    }


def _annotation_for(schema: dict[str, Any]) -> Any:
    branches = schema.get("anyOf")
    if isinstance(branches, list):
        non_null = next((branch for branch in branches if branch.get("type") != "null"), {})
        base = _annotation_for(non_null)
        return base | None
    return {
        "array": list[Any],
        "boolean": bool,
        "integer": int,
        "number": float,
        "object": dict[str, Any],
        "string": str,
    }.get(schema.get("type"), Any)


def _make_tool(adapter: ThingsCoreAdapter, contract: Any) -> FunctionTool:
    schema = adapted_input_schema(contract)
    description = public_description(contract)

    async def invoke(**kwargs: Any) -> CoreToolResult:
        ctx = kwargs.pop("ctx")
        return await adapter.call(contract.name, kwargs, ctx)

    parameters: list[inspect.Parameter] = []
    annotations: dict[str, Any] = {}
    required = set(schema.get("required", []))
    for name, property_schema in schema["properties"].items():
        annotation = _annotation_for(property_schema)
        annotations[name] = annotation
        default = inspect.Parameter.empty if name in required else property_schema.get("default", None)
        parameters.append(
            inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY, default=default, annotation=annotation)
        )
    annotations["ctx"] = Context
    annotations["return"] = CoreToolResult
    parameters.append(inspect.Parameter("ctx", inspect.Parameter.KEYWORD_ONLY, annotation=Context))
    invoke.__name__ = contract.name
    invoke.__qualname__ = contract.name
    invoke.__doc__ = description
    invoke.__annotations__ = annotations
    cast("Any", invoke).__signature__ = inspect.Signature(parameters, return_annotation=CoreToolResult)
    tool = FunctionTool.from_function(
        invoke,
        name=contract.name,
        description=description,
        annotations=contract.annotations,
        output_schema=adapted_output_schema(),
        meta=_meta(contract.scope, contract.risk, contract.schema_contract_id),
        timeout=120,
    )
    tool.parameters = schema
    return tool


def build_server(adapter: ThingsCoreAdapter | None = None) -> FastMCP:
    """Build exactly the audited toolset without importing upstream code."""
    contracts = validate_frozen_contract()
    active_adapter = adapter or ThingsCoreAdapter()
    server = FastMCP(
        "Things Core",
        instructions=(
            "Audited security adapter for mcp-server-things 1.9.0. "
            "Mutations require preview then execute with the returned receipt."
        ),
        mask_error_details=True,
        strict_input_validation=True,
    )
    for contract in contracts:
        server.add_tool(_make_tool(active_adapter, contract))
    return server


mcp = build_server()


def doctor() -> dict[str, Any]:
    """Return actionable prerequisite codes without paths, tokens, or private data."""
    provenance = provenance_doctor()
    auth = auth_doctor()
    ready = provenance["status"] == "ready" and auth["status"] != "blocked"
    return {
        "status": "ready" if ready else "blocked",
        "code": "things_core_ready" if ready else "things_core_prerequisite_failed",
        "provenance": provenance,
        "auth": auth,
        "toolCount": 41,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run or diagnose the Things core MCP adapter.")
    parser.add_argument("--doctor", action="store_true", help="Print a redacted prerequisite report and exit.")
    args = parser.parse_args(argv)
    if args.doctor:
        report = doctor()
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
        if report["status"] != "ready":
            raise SystemExit(1)
        return
    mcp.run()


if __name__ == "__main__":
    main()
