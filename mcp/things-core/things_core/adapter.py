"""Central security, receipt, redaction, and verification adapter."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Literal, Protocol

from fastmcp.exceptions import ToolError

from things_common import (
    MutationAmbiguousError,
    MutationBusyError,
    MutationCoordinator,
    MutationError,
    MutationIntent,
    MutationReceiptError,
    MutationStateError,
    SecureRuntimePaths,
    redact_text,
)

from .backend import UpstreamThingsBackend
from .contracts import (
    MAX_BATCH_ITEMS,
    CoreContractError,
    ToolContract,
    upstream_arguments,
    validate_arguments,
    validate_frozen_contract,
)
from .models import CoreToolResult, NormalizedPayload, NormalizedPayloadEntry

if TYPE_CHECKING:
    from fastmcp import Context

_META_PRINCIPAL = "w4w.dev/thingsPrincipal"
_META_CLIENT_ID = "w4w.dev/thingsClientId"
_META_RESOURCE = "w4w.dev/thingsResource"
_LOCAL_RESOURCE = "http://127.0.0.1:46683/mcp/things"
_REMOTE_RESOURCE = "https://mcp.w4w.dev/mcp/things"
_ALLOWED_RESOURCES = frozenset({_LOCAL_RESOURCE, _REMOTE_RESOURCE})
_SECRET_KEYS = frozenset({
    "accesstoken",
    "apikey",
    "authtoken",
    "authorization",
    "bearertoken",
    "clientsecret",
    "credential",
    "credentials",
    "environment",
    "mutationreceipt",
    "password",
    "processargs",
    "receipt",
    "refreshtoken",
    "secret",
    "serverconfig",
    "token",
})
_DIAGNOSTIC_SAFE_KEYS = frozenset({
    "active",
    "available",
    "capabilities",
    "code",
    "count",
    "enabled",
    "framework",
    "healthy",
    "limit",
    "max_size",
    "operation",
    "pending",
    "queue_size",
    "registered_tools",
    "running",
    "status",
    "success",
    "tool_count",
    "version",
})
_SAFE_DIAGNOSTIC_TEXT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_. -]{0,127}$")


class CoreBackend(Protocol):
    """Mockable boundary; production delegates to the pinned upstream MCP."""

    async def call(self, tool: str, arguments: dict[str, Any]) -> Any: ...

    async def read_state(self, tool: str, arguments: dict[str, Any]) -> Any: ...

    async def verify(self, tool: str, arguments: dict[str, Any], before: Any, result: Any) -> dict[str, Any]: ...


def _metadata(ctx: Context | None) -> dict[str, Any]:
    if ctx is None or ctx.request_context is None or ctx.request_context.meta is None:
        return {}
    extra = ctx.request_context.meta.model_extra or {}
    return extra if isinstance(extra, dict) else {}


def _identity(ctx: Context | None) -> tuple[str, str, str]:
    """Use only MCPHub-reserved identity metadata, with one explicit local escape hatch."""
    meta = _metadata(ctx)
    principal = meta.get(_META_PRINCIPAL)
    client_id = meta.get(_META_CLIENT_ID)
    resource = meta.get(_META_RESOURCE)
    if (
        isinstance(principal, str)
        and principal
        and isinstance(client_id, str)
        and client_id
        and isinstance(resource, str)
        and resource
    ):
        if resource not in _ALLOWED_RESOURCES:
            raise ToolError("things_resource_mismatch")
        return principal, client_id, resource
    if os.environ.get("THINGS_MCP_ALLOW_LOCAL_IDENTITY_FALLBACK") == "1":
        return (
            os.environ.get("THINGS_MCP_LOCAL_PRINCIPAL", "local-user"),
            os.environ.get("THINGS_MCP_LOCAL_CLIENT_ID", "local-mcphub"),
            _LOCAL_RESOURCE,
        )
    raise ToolError("things_identity_missing")


def _target_ids(arguments: dict[str, Any]) -> tuple[str, ...]:
    values: list[str] = []
    for field in ("id", "todo_id", "todo_ids", "project_id", "project_uuid", "record_ids"):
        value = arguments.get(field)
        if isinstance(value, str):
            values.extend(item.strip() for item in value.split(",") if item.strip())
        elif isinstance(value, list):
            values.extend(item for item in value if isinstance(item, str) and item)
    return tuple(dict.fromkeys(values))[:MAX_BATCH_ITEMS]


def _normalized_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _source_kind(value: Any) -> Literal["object", "array", "scalar", "null"]:
    if isinstance(value, Mapping):
        return "object"
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return "array"
    if value is None:
        return "null"
    return "scalar"


def _bounded_payload(value: Any) -> tuple[NormalizedPayload, bool]:
    """Flatten arbitrary upstream JSON into one closed deterministic shape."""
    entries: list[NormalizedPayloadEntry] = []
    truncated = False

    def append(path: str, item: Any) -> None:
        nonlocal truncated
        if len(entries) >= 500:
            truncated = True
            return
        safe_path = re.sub(r"[\x00\x7f]", "?", path)
        if len(safe_path) > 2_048:
            safe_path = safe_path[:2_048]
            truncated = True
        if isinstance(item, str):
            scalar: str | bool | int | float | None = redact_text(item)
            if len(scalar) > 20_000:
                scalar = scalar[:20_000]
                truncated = True
        elif item is None or isinstance(item, (bool, int, float)):
            scalar = item
        else:
            scalar = f"<redacted:{type(item).__name__.casefold()}>"
        entries.append(NormalizedPayloadEntry(path=safe_path, value=scalar))

    def visit(item: Any, path: str, depth: int) -> None:
        nonlocal truncated
        if depth > 12:
            append(path, "<redacted:depth-limit>")
            truncated = True
            return
        if isinstance(item, Mapping):
            ordered = sorted(item.items(), key=lambda pair: str(pair[0]))
            if len(ordered) > 100:
                truncated = True
            for raw_key, child in ordered[:100]:
                key = str(raw_key)
                if len(key) > 128:
                    key = key[:128]
                    truncated = True
                pointer_key = key.replace("~", "~0").replace("/", "~1")
                child_path = f"{path}/{pointer_key}"
                if _normalized_key(key) in _SECRET_KEYS:
                    append(child_path, "<redacted:secret>")
                else:
                    visit(child, child_path, depth + 1)
            return
        if isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            values = list(item)
            if len(values) > MAX_BATCH_ITEMS:
                truncated = True
            for index, child in enumerate(values[:MAX_BATCH_ITEMS]):
                visit(child, f"{path}/{index}", depth + 1)
            return
        append(path, item)

    visit(value, "$", 0)
    return NormalizedPayload(sourceKind=_source_kind(value), entries=tuple(entries)), truncated


def _diagnostic_payload(value: Any) -> dict[str, Any]:
    """Allow only operational scalars from the five upstream diagnostics."""
    result: dict[str, Any] = {}
    if not isinstance(value, Mapping):
        return {"status": "available"}
    for raw_key, item in value.items():
        key = str(raw_key)
        normalized = key.casefold().replace("-", "_")
        if normalized not in _DIAGNOSTIC_SAFE_KEYS:
            continue
        if item is None or isinstance(item, (bool, int, float)):
            result[key] = item
        elif isinstance(item, str):
            redacted = redact_text(item)
            if _SAFE_DIAGNOSTIC_TEXT.fullmatch(redacted) and "<redacted:" not in redacted:
                result[key] = redacted
        elif isinstance(item, list) and normalized == "capabilities":
            safe = [entry for entry in item if isinstance(entry, str) and re.fullmatch(r"[a-z0-9_]{1,128}", entry)]
            result[key] = safe[:MAX_BATCH_ITEMS]
    result.setdefault("status", "available")
    return result


class ThingsCoreAdapter:
    """Apply one security protocol to all 41 manifest-defined upstream tools."""

    def __init__(
        self,
        backend: CoreBackend | None = None,
        *,
        coordinator: MutationCoordinator | None = None,
    ) -> None:
        contracts = validate_frozen_contract()
        self.contracts = {contract.name: contract for contract in contracts}
        self.backend: CoreBackend = backend or UpstreamThingsBackend()
        self._coordinator = coordinator

    @property
    def coordinator(self) -> MutationCoordinator:
        if self._coordinator is None:
            self._coordinator = MutationCoordinator(SecureRuntimePaths.create())
        return self._coordinator

    def contract(self, name: str) -> ToolContract:
        try:
            return self.contracts[name]
        except KeyError as exc:
            raise ToolError("things_core_tool_not_manifested") from exc

    async def call(self, name: str, arguments: dict[str, Any], ctx: Context | None = None) -> CoreToolResult:
        """Validate and dispatch one exact tool without guessing aliases."""
        contract = self.contract(name)
        try:
            public_arguments = validate_arguments(contract, arguments)
        except CoreContractError as exc:
            raise ToolError("things_core_invalid_arguments") from exc
        domain_arguments = upstream_arguments(contract, public_arguments)
        if not contract.mutating:
            try:
                raw_result = await self.backend.call(name, domain_arguments)
            except Exception as exc:
                raise ToolError("things_core_upstream_read_failed") from exc
            if contract.diagnostic:
                diagnostic_payload = _diagnostic_payload(raw_result)
                payload, normalized_truncated = _bounded_payload(diagnostic_payload)
                truncated = normalized_truncated or diagnostic_payload != raw_result
            else:
                payload, truncated = _bounded_payload(raw_result)
            return CoreToolResult(
                tool=name,
                status="read",
                payload=payload,
                truncated=truncated,
                messageCode="things_core_read_ok",
            )

        principal, client_id, resource = _identity(ctx)
        targets = _target_ids(domain_arguments)
        intent = MutationIntent(
            principal=principal,
            client_id=client_id,
            resource=resource,
            tool=name,
            target_ids=targets,
            arguments=domain_arguments,
            minimum_scope=contract.scope,
        )
        if public_arguments["mutationPhase"] == "preview":
            try:
                preview = await self.coordinator.apreview(
                    intent, lambda: self.backend.read_state(name, domain_arguments)
                )
            except MutationBusyError as exc:
                raise ToolError("things_mutation_busy") from exc
            except MutationError as exc:
                raise ToolError("things_mutation_preview_failed") from exc
            return CoreToolResult(
                tool=name,
                status="previewed",
                mutationReceipt=preview.mutation_receipt,
                receiptId=preview.receipt_id,
                targetCount=preview.target_count,
                payload=_bounded_payload({"risk": contract.risk, "minimumScope": contract.scope})[0],
                messageCode="things_mutation_previewed",
            )

        receipt = public_arguments.get("mutationReceipt")
        if not isinstance(receipt, str):
            raise ToolError("things_mutation_receipt_required")
        captured_before: list[Any] = []
        captured_result: list[Any] = []

        async def read_state() -> Any:
            state = await self.backend.read_state(name, domain_arguments)
            captured_before.append(state)
            return state

        async def mutate() -> Any:
            result = await self.backend.call(name, domain_arguments)
            captured_result.append(result)
            return result

        async def verify(result: Any) -> dict[str, Any]:
            if not captured_before:
                raise RuntimeError("things_core_missing_prewrite_state")
            return await self.backend.verify(name, domain_arguments, captured_before[-1], result)

        try:
            execution = await self.coordinator.aexecute(intent, receipt, read_state, mutate, verify)
        except MutationStateError as exc:
            raise ToolError("things_mutation_stale_state") from exc
        except MutationReceiptError as exc:
            raise ToolError("things_mutation_receipt_invalid") from exc
        except MutationAmbiguousError:
            return CoreToolResult(
                tool=name,
                status="ambiguous",
                targetCount=max(1, len(targets)),
                ambiguousCount=max(1, len(targets)),
                payload=None,
                messageCode="things_mutation_ambiguous",
            )
        except MutationError as exc:
            raise ToolError("things_mutation_execute_failed") from exc
        payload, truncated = _bounded_payload(captured_result[-1] if captured_result else None)
        return CoreToolResult(
            tool=name,
            status=execution.status,
            receiptId=execution.receipt_id,
            targetCount=max(1, len(targets)),
            changedCount=execution.changed,
            skippedCount=execution.skipped,
            failedCount=execution.failed,
            ambiguousCount=execution.ambiguous,
            readbackVerified=execution.status != "ambiguous",
            truncated=truncated,
            payload=payload,
            messageCode="things_mutation_verified" if execution.status != "ambiguous" else "things_mutation_ambiguous",
        )


__all__ = ["CoreBackend", "ThingsCoreAdapter"]
