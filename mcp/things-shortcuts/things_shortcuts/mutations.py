"""Things-common receipt integration for typed Shortcut mutations."""

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING, Any, Literal

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
    canonical_sha256,
)

from .bridge import (
    BridgeExecutionError,
    BridgeProtocolError,
    BridgeTimeoutError,
    BridgeUnavailableError,
    invoke_bridge,
)
from .models import (
    DESTRUCTIVE_OPERATIONS,
    BridgeOperation,
    BridgeOperationResult,
    CreateStructuredProjectRequest,
    CreateTodosRequest,
    MutationPhase,
    MutationRequest,
    OperationResult,
)

if TYPE_CHECKING:
    from fastmcp import Context

_META_PRINCIPAL = "w4w.dev/thingsPrincipal"
_META_CLIENT_ID = "w4w.dev/thingsClientId"
_META_RESOURCE = "w4w.dev/thingsResource"
_LOCAL_RESOURCE = "http://127.0.0.1:46683/mcp/things"
_REMOTE_RESOURCE = "https://mcp.w4w.dev/mcp/things"
_CANONICAL_RESOURCES = frozenset({_LOCAL_RESOURCE, _REMOTE_RESOURCE})
_RESERVED_BRIDGE_PAYLOAD_KEYS = frozenset({
    "mutationReceipt",
    _META_PRINCIPAL,
    _META_CLIENT_ID,
    _META_RESOURCE,
})
_UI_HANDOFF_OPERATIONS = frozenset({
    BridgeOperation.CREATE_TODO_WITH_QUICK_ENTRY,
    BridgeOperation.OPEN_LIST,
    BridgeOperation.SHOW_ITEMS,
})
_READ_OPERATIONS = frozenset({
    BridgeOperation.FIND_ITEMS,
    BridgeOperation.GET_ITEMS,
    BridgeOperation.GET_SELECTED_ITEMS,
})
_PER_ITEM_RECEIPT_OPERATIONS = frozenset({
    BridgeOperation.CREATE_TODOS,
    BridgeOperation.CREATE_STRUCTURED_PROJECT,
    BridgeOperation.EDIT_ITEMS,
    BridgeOperation.DUPLICATE_ITEMS,
    BridgeOperation.DELETE_ITEMS,
    BridgeOperation.DELETE_ITEMS_IMMEDIATELY,
})
_NON_UNDOABLE_OPERATIONS = DESTRUCTIVE_OPERATIONS | {
    BridgeOperation.EDIT_ITEMS,
}
MinimumScope = Literal["things.read", "things.write", "things.admin"]
OutcomeStatus = Literal["changed", "skipped", "failed", "ambiguous"]
_coordinator: MutationCoordinator | None = None


def _get_coordinator() -> MutationCoordinator:
    """Create one coordinator over the stack-wide default secure runtime root."""
    global _coordinator
    if _coordinator is None:
        _coordinator = MutationCoordinator(SecureRuntimePaths.create())
    return _coordinator


def _metadata(ctx: Context | None) -> dict[str, Any]:
    """Extract only reserved metadata that MCPHub must overwrite and attest."""
    if ctx is not None and ctx.request_context is not None and ctx.request_context.meta is not None:
        extra = ctx.request_context.meta.model_extra or {}
        if isinstance(extra, dict):
            return extra
    return {}


def _identity(ctx: Context | None) -> tuple[str, str, str]:
    """Return the attested per-call identity or fail closed."""
    meta = _metadata(ctx)
    principal = meta.get(_META_PRINCIPAL)
    client_id = meta.get(_META_CLIENT_ID)
    resource = meta.get(_META_RESOURCE)
    if resource is not None and (not isinstance(resource, str) or resource not in _CANONICAL_RESOURCES):
        raise ToolError("things_resource_mismatch")
    if (
        isinstance(principal, str)
        and principal
        and isinstance(client_id, str)
        and client_id
        and isinstance(resource, str)
        and resource in _CANONICAL_RESOURCES
    ):
        return principal, client_id, resource
    if os.environ.get("THINGS_MCP_ALLOW_LOCAL_IDENTITY_FALLBACK") == "1":
        return (
            os.environ.get("THINGS_MCP_LOCAL_PRINCIPAL", "local-user"),
            os.environ.get("THINGS_MCP_LOCAL_CLIENT_ID", "local-mcphub"),
            _LOCAL_RESOURCE,
        )
    raise ToolError("things_identity_missing")


def _public_result(result: BridgeOperationResult) -> OperationResult:
    """Remove receipt-binding evidence from the public MCP response."""
    return OperationResult.model_validate(
        result.model_dump(
            by_alias=True,
            mode="json",
            exclude={"target_state", "cascade_observed"},
        )
    )


def _is_zero_effect_ui_result(result: BridgeOperationResult) -> bool:
    """Return whether a backend result is a content-free UI handoff."""
    return (
        result.mutation_receipt is None
        and result.affected_count == 0
        and result.cascade_count == 0
        and result.changed_count == 0
        and result.skipped_count == 0
        and result.failed_count == 0
        and result.ambiguous_count == 0
        and not result.items
        and not result.receipts
        and not result.readback_verified
        and result.ui_handoff
        and result.undoable is None
        and result.target_state is None
        and result.cascade_observed is None
    )


def _logical_outcome_count(operation: BridgeOperation, payload: dict[str, Any]) -> int:
    """Return the bounded logical result count, separate from referenced IDs."""
    if operation is BridgeOperation.CREATE_TODOS:
        todos = payload.get("todos")
        return len(todos) if isinstance(todos, list) else 0
    if operation is BridgeOperation.CREATE_STRUCTURED_PROJECT:
        headings = payload.get("headings")
        unheaded = payload.get("unheadedTodos")
        if not isinstance(headings, list) or not isinstance(unheaded, list):
            return 0
        child_count = 0
        for heading in headings:
            if not isinstance(heading, dict) or not isinstance(heading.get("todos"), list):
                return 0
            child_count += len(heading["todos"])
        return 1 + len(headings) + len(unheaded) + child_count
    item_ids = payload.get("itemIds")
    if isinstance(item_ids, list):
        return len(item_ids)
    return 1


def _outcome_counts(result: BridgeOperationResult) -> dict[str, int]:
    """Return coordinator-normalized outcome keys from a bridge result."""
    return {
        "changed": result.changed_count,
        "skipped": result.skipped_count,
        "failed": result.failed_count,
        "ambiguous": result.ambiguous_count,
    }


def _derived_status(counts: dict[str, int]) -> OutcomeStatus:
    """Mirror the shared coordinator's four-way status derivation."""
    if counts["ambiguous"]:
        return "ambiguous"
    if counts["failed"] and not counts["changed"]:
        return "failed"
    if counts["changed"]:
        return "changed"
    return "skipped"


def _validate_read_result(result: BridgeOperationResult) -> None:
    """Require an explicitly non-mutating shape for all three read operations."""
    if (
        result.status != "shown"
        or result.affected_count != len(result.items)
        or result.cascade_count != 0
        or result.changed_count != 0
        or result.skipped_count != 0
        or result.failed_count != 0
        or result.ambiguous_count != 0
        or result.receipts
        or result.readback_verified
        or result.ui_handoff
        or result.undoable is not None
        or result.target_state is not None
        or result.cascade_observed is not None
    ):
        raise ToolError("things_shortcuts_read_result_invalid")


def _validate_result_shape(
    operation: BridgeOperation,
    payload: dict[str, Any],
    result: BridgeOperationResult,
) -> None:
    """Enforce operation-specific backend invariants before issuing receipts."""
    if result.operation is not operation:
        raise ToolError("things_shortcuts_operation_mismatch")
    if result.mutation_receipt is not None:
        raise ToolError("things_shortcuts_backend_receipt_forbidden")

    if operation is BridgeOperation.CREATE_TODO_WITH_QUICK_ENTRY:
        if result.status != "ui_handoff" or not _is_zero_effect_ui_result(result):
            raise ToolError("things_quick_entry_result_invalid")
        return
    if operation in {BridgeOperation.OPEN_LIST, BridgeOperation.SHOW_ITEMS}:
        if result.status != "shown" or not _is_zero_effect_ui_result(result):
            raise ToolError("things_ui_handoff_result_invalid")
        return
    if operation in _READ_OPERATIONS:
        _validate_read_result(result)
        return

    mutation_phase = payload.get("mutationPhase")
    if mutation_phase in {"preview", "execute"}:
        outcome_count = _logical_outcome_count(operation, payload)
        if not 1 <= outcome_count <= 25:
            raise ToolError("things_shortcuts_outcome_count_invalid")
        if not result.target_state:
            raise ToolError("things_shortcuts_target_state_missing")
        expected_statuses = (
            {"previewed", "skipped"} if mutation_phase == "preview" else {"changed", "skipped", "failed", "ambiguous"}
        )
        if result.status not in expected_statuses:
            raise ToolError("things_shortcuts_mutation_result_invalid")
        if result.ui_handoff or result.items:
            raise ToolError("things_shortcuts_mutation_result_invalid")
        if operation in _NON_UNDOABLE_OPERATIONS and result.undoable is not False:
            raise ToolError("things_shortcuts_undoability_invalid")
        if operation is BridgeOperation.DELETE_HEADING and (
            result.cascade_observed is not True or "cascade_count" not in result.model_fields_set
        ):
            raise ToolError("things_heading_cascade_missing")
        if operation is not BridgeOperation.DELETE_HEADING and (
            result.cascade_count != 0 or result.cascade_observed is not None
        ):
            raise ToolError("things_shortcuts_cascade_evidence_invalid")

        counts = _outcome_counts(result)
        if mutation_phase == "preview":
            expected_skipped = outcome_count if result.status == "skipped" else 0
            if (
                result.readback_verified
                or result.receipts
                or counts
                != {
                    "changed": 0,
                    "skipped": expected_skipped,
                    "failed": 0,
                    "ambiguous": 0,
                }
            ):
                raise ToolError("things_shortcuts_preview_result_invalid")
            return

        if sum(counts.values()) != outcome_count or result.status != _derived_status(counts):
            raise ToolError("things_shortcuts_outcome_counts_invalid")
        if result.status == "ambiguous":
            if result.readback_verified:
                raise ToolError("things_shortcuts_mutation_result_invalid")
        elif not result.readback_verified:
            raise ToolError("things_shortcuts_mutation_result_invalid")
        if operation in _PER_ITEM_RECEIPT_OPERATIONS and len(result.receipts) != outcome_count:
            raise ToolError("things_shortcuts_item_receipts_missing")
        if result.receipts:
            receipt_counts = dict.fromkeys(counts, 0)
            for receipt in result.receipts:
                receipt_counts[receipt.status] += 1
            if receipt_counts != counts:
                raise ToolError("things_shortcuts_item_receipts_invalid")


def _target_state_fingerprint(operation: BridgeOperation, result: BridgeOperationResult) -> dict[str, str]:
    """Hash canonical target-state records instead of aggregate outcome counts."""
    if not result.target_state:
        raise ToolError("things_shortcuts_target_state_missing")
    state: dict[str, Any] = {
        "operation": operation.value,
        "records": sorted(result.target_state),
    }
    if operation is BridgeOperation.DELETE_HEADING:
        if result.cascade_observed is not True:
            raise ToolError("things_heading_cascade_missing")
        state["cascadeCount"] = result.cascade_count
    return {"targetStateSha256": canonical_sha256(state)}


def _safe_bridge_call(operation: BridgeOperation, payload: dict[str, Any]) -> BridgeOperationResult:
    """Invoke and validate one bridge result while exposing content-free failures."""
    try:
        response = invoke_bridge(operation, payload)
    except BridgeUnavailableError as exc:
        raise ToolError("things_shortcuts_absent") from exc
    except BridgeProtocolError as exc:
        raise ToolError("things_shortcuts_protocol_mismatch") from exc
    except BridgeTimeoutError as exc:
        raise ToolError("things_shortcuts_timeout") from exc
    except BridgeExecutionError as exc:
        raise ToolError("things_shortcuts_tcc_degraded_or_failed") from exc
    if not response.tcc_ready:
        raise ToolError("things_shortcuts_tcc_degraded")
    try:
        result = BridgeOperationResult.model_validate(response.result)
    except Exception as exc:
        raise ToolError("things_shortcuts_result_invalid") from exc
    _validate_result_shape(operation, payload, result)
    return result


async def call_non_mutating(operation: BridgeOperation, payload: dict[str, Any]) -> OperationResult:
    """Call a read or explicit UI-handoff operation without a mutation receipt."""
    result = await asyncio.to_thread(_safe_bridge_call, operation, payload)
    return _public_result(result)


async def call_mutating(
    operation: BridgeOperation,
    request: MutationRequest,
    *,
    ctx: Context | None,
    minimum_scope: MinimumScope,
    target_ids: tuple[str, ...],
) -> OperationResult:
    """Run preview or execute through the shared serializable receipt protocol."""
    principal, client_id, resource = _identity(ctx)
    raw = request.model_dump(by_alias=True, mode="json", exclude={"mutation_phase", "mutation_receipt"})
    bridge_payload = request.model_dump(by_alias=True, mode="json", exclude={"mutation_receipt"})
    bridge_payload = {key: value for key, value in bridge_payload.items() if key not in _RESERVED_BRIDGE_PAYLOAD_KEYS}
    outcome_count = len(target_ids)
    if not 1 <= outcome_count <= 25:
        raise ToolError("things_shortcuts_outcome_count_invalid")
    raw["_receiptOutcomeCount"] = outcome_count
    intent = MutationIntent(
        principal=principal,
        client_id=client_id,
        resource=resource,
        tool=operation.value,
        target_ids=target_ids,
        arguments=raw,
        minimum_scope=minimum_scope,
    )
    coordinator = _get_coordinator()
    if request.mutation_phase is MutationPhase.PREVIEW:
        captured: list[BridgeOperationResult] = []

        async def read_state() -> dict[str, Any]:
            result = await asyncio.to_thread(_safe_bridge_call, operation, bridge_payload)
            captured.append(result)
            return _target_state_fingerprint(operation, result)

        try:
            preview = await coordinator.apreview(intent, read_state)
        except MutationBusyError as exc:
            raise ToolError("things_mutation_busy") from exc
        except MutationError as exc:
            raise ToolError("things_mutation_preview_failed") from exc
        backend = captured[0]
        public = _public_result(backend)
        return public.model_copy(update={"mutation_receipt": preview.mutation_receipt})

    if request.mutation_receipt is None:
        raise ToolError("things_mutation_receipt_required")
    captured_fresh_preview: list[BridgeOperationResult] = []
    captured_execute: list[BridgeOperationResult] = []

    async def read_state_execute() -> dict[str, Any]:
        preview_payload = dict(bridge_payload)
        preview_payload["mutationPhase"] = "preview"
        result = await asyncio.to_thread(_safe_bridge_call, operation, preview_payload)
        captured_fresh_preview.append(result)
        return _target_state_fingerprint(operation, result)

    async def mutate() -> BridgeOperationResult:
        result = await asyncio.to_thread(_safe_bridge_call, operation, bridge_payload)
        captured_execute.append(result)
        return result

    async def verify(result: BridgeOperationResult) -> dict[str, Any]:
        await asyncio.sleep(0)
        if result.status == "ambiguous" or not result.readback_verified:
            raise RuntimeError("backend_verification_inconclusive")
        if operation is BridgeOperation.DELETE_HEADING and (
            not captured_fresh_preview or result.cascade_count != captured_fresh_preview[0].cascade_count
        ):
            raise RuntimeError("backend_cascade_scope_changed")
        return {
            "operation": result.operation.value,
            "status": result.status,
            "affectedCount": result.affected_count,
            **_outcome_counts(result),
            "cascadeCount": result.cascade_count,
            "readbackVerified": result.readback_verified,
            **_target_state_fingerprint(operation, result),
        }

    try:
        execution = await coordinator.aexecute(intent, request.mutation_receipt, read_state_execute, mutate, verify)
    except MutationStateError as exc:
        raise ToolError("things_mutation_stale_state") from exc
    except MutationReceiptError as exc:
        raise ToolError("things_mutation_receipt_invalid") from exc
    except MutationAmbiguousError:
        return OperationResult(
            operation=operation,
            status="ambiguous",
            cascade_count=(
                captured_fresh_preview[0].cascade_count
                if operation is BridgeOperation.DELETE_HEADING and captured_fresh_preview
                else 0
            ),
            ambiguous_count=outcome_count,
            items=[],
            receipts=[],
            readback_verified=False,
            undoable=False if operation in _NON_UNDOABLE_OPERATIONS else None,
            message_code="things_mutation_ambiguous",
        )
    except MutationError as exc:
        raise ToolError("things_mutation_execute_failed") from exc
    public = _public_result(captured_execute[0])
    return public.model_copy(
        update={
            "status": execution.status,
            "changed_count": execution.changed,
            "skipped_count": execution.skipped,
            "failed_count": execution.failed,
            "ambiguous_count": execution.ambiguous,
        }
    )


def target_ids_from_request(operation: BridgeOperation, request: MutationRequest) -> tuple[str, ...]:
    """Return explicit logical outcomes; references remain argument/state bound."""
    if operation is BridgeOperation.CREATE_TODOS:
        if not isinstance(request, CreateTodosRequest):
            raise ToolError("things_shortcuts_request_type_invalid")
        return tuple(f"create-todo-{index}" for index in range(len(request.todos)))
    if operation is BridgeOperation.CREATE_STRUCTURED_PROJECT:
        if not isinstance(request, CreateStructuredProjectRequest):
            raise ToolError("things_shortcuts_request_type_invalid")
        outcome_count = (
            1
            + len(request.headings)
            + len(request.unheaded_todos)
            + sum(len(heading.todos) for heading in request.headings)
        )
        return tuple(f"create-structured-project-{index}" for index in range(outcome_count))
    if operation in {
        BridgeOperation.CREATE_TODO,
        BridgeOperation.CREATE_HEADING,
        BridgeOperation.CREATE_PROJECT,
    }:
        return (f"{operation.value}-outcome",)

    values: list[str] = []
    for field_name in ("item_ids", "project_id", "heading_id", "item_id"):
        value = getattr(request, field_name, None)
        if isinstance(value, list):
            values.extend(value)
        elif isinstance(value, str):
            values.append(value)
    targets = tuple(dict.fromkeys(values))
    if not targets:
        raise ToolError("things_shortcuts_outcome_targets_missing")
    return targets


__all__ = ["call_mutating", "call_non_mutating", "target_ids_from_request"]
