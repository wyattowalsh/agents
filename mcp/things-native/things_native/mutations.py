"""Things-common receipt integration for fixed native mutations."""

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

from .models import (
    MutationPhase,
    MutationRequest,
    NativeOperation,
    NativeOperationResult,
)
from .runner import (
    NativeArtifactError,
    NativeBackendResult,
    NativeExecutionError,
    NativeTimeoutError,
    NativeUnavailableError,
    run_script,
)

if TYPE_CHECKING:
    from fastmcp import Context

_META_PRINCIPAL = "w4w.dev/thingsPrincipal"
_META_CLIENT_ID = "w4w.dev/thingsClientId"
_META_RESOURCE = "w4w.dev/thingsResource"
_LOCAL_RESOURCE = "http://127.0.0.1:46683/mcp/things"
_REMOTE_RESOURCE = "https://mcp.w4w.dev/mcp/things"
_CANONICAL_RESOURCES = frozenset({_LOCAL_RESOURCE, _REMOTE_RESOURCE})
_CASCADE_OPERATIONS = frozenset({"empty_trash", "delete_area", "delete_tag"})
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
    """Extract only reserved identity metadata attested by MCPHub."""
    if ctx is not None and ctx.request_context is not None and ctx.request_context.meta is not None:
        model_extra = ctx.request_context.meta.model_extra
        if isinstance(model_extra, dict):
            return model_extra
    return {}


def _identity(ctx: Context | None) -> tuple[str, str, str]:
    """Extract MCPHub-attested identity metadata or fail closed."""
    extra = _metadata(ctx)
    principal = extra.get(_META_PRINCIPAL)
    client_id = extra.get(_META_CLIENT_ID)
    resource = extra.get(_META_RESOURCE)
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


def _safe_run(script_name: str, arguments: list[str]) -> NativeBackendResult:
    """Run a fixed script and expose only content-free error codes."""
    try:
        return run_script(script_name, arguments)
    except NativeUnavailableError as exc:
        raise ToolError("things_native_absent") from exc
    except NativeArtifactError as exc:
        raise ToolError("things_native_bundle_mismatch") from exc
    except NativeTimeoutError as exc:
        raise ToolError("things_native_timeout") from exc
    except NativeExecutionError as exc:
        raise ToolError("things_native_tcc_degraded_or_failed") from exc


def _to_result(
    operation: NativeOperation,
    backend: NativeBackendResult,
    *,
    receipt: str | None = None,
    undoable: bool | None,
    normalized_status: OutcomeStatus | None = None,
) -> NativeOperationResult:
    """Convert a closed backend result without adding private content."""
    return NativeOperationResult(
        operation=operation,
        status=backend.status if normalized_status is None else normalized_status,
        mutation_receipt=receipt,
        affected_count=backend.affected_count,
        cascade_count=backend.cascade_count,
        readback_verified=backend.readback_verified,
        ui_handoff=False,
        undoable=undoable,
        message_code=backend.message_code,
    )


def _validate_backend_result(
    operation: NativeOperation,
    phase: MutationPhase,
    result: NativeBackendResult,
) -> None:
    """Reject missing state/cascade proof and impossible phase outcomes."""
    expected_statuses = (
        {"previewed", "skipped"} if phase is MutationPhase.PREVIEW else {"changed", "skipped", "failed", "ambiguous"}
    )
    if result.status not in expected_statuses:
        raise ToolError("things_native_mutation_result_invalid")
    if operation in _CASCADE_OPERATIONS and not result.cascade_observed:
        raise ToolError("things_native_cascade_evidence_missing")
    if operation not in _CASCADE_OPERATIONS and result.cascade_observed:
        raise ToolError("things_native_cascade_evidence_invalid")
    if (
        operation == "log_completed"
        and phase is MutationPhase.EXECUTE
        and (result.status != "ambiguous" or result.readback_verified)
    ):
        raise ToolError("things_native_log_completed_verification_invalid")


def _target_state_fingerprint(operation: NativeOperation, result: NativeBackendResult) -> dict[str, str]:
    """Hash canonical target records rather than aggregate counts or statuses."""
    state: dict[str, Any] = {
        "operation": operation,
        "records": sorted(result.target_state),
    }
    if operation in _CASCADE_OPERATIONS:
        if not result.cascade_observed:
            raise ToolError("things_native_cascade_evidence_missing")
        state["cascadeCount"] = result.cascade_count
    return {"targetStateSha256": canonical_sha256(state)}


async def call_mutating(
    operation: NativeOperation,
    script_name: str,
    request: MutationRequest,
    *,
    ctx: Context | None,
    minimum_scope: MinimumScope,
    target_ids: tuple[str, ...],
    outcome_count: int,
    script_arguments: list[str],
    undoable: bool | None,
) -> NativeOperationResult:
    """Run a fixed native preview or execute under the shared receipt lock."""
    if not 1 <= outcome_count <= 25 or len(target_ids) != outcome_count:
        raise ToolError("things_native_outcome_count_invalid")
    principal, client_id, resource = _identity(ctx)
    semantic_arguments = request.model_dump(by_alias=True, mode="json", exclude={"mutation_phase", "mutation_receipt"})
    semantic_arguments["_receiptOutcomeCount"] = outcome_count
    intent = MutationIntent(
        principal=principal,
        client_id=client_id,
        resource=resource,
        tool=operation,
        target_ids=target_ids,
        arguments=semantic_arguments,
        minimum_scope=minimum_scope,
    )
    coordinator = _get_coordinator()
    if request.mutation_phase is MutationPhase.PREVIEW:
        captured: list[NativeBackendResult] = []

        async def read_state() -> dict[str, Any]:
            result = await asyncio.to_thread(_safe_run, script_name, ["preview", *script_arguments])
            _validate_backend_result(operation, MutationPhase.PREVIEW, result)
            captured.append(result)
            return _target_state_fingerprint(operation, result)

        try:
            preview = await coordinator.apreview(intent, read_state)
        except MutationBusyError as exc:
            raise ToolError("things_mutation_busy") from exc
        except MutationError as exc:
            raise ToolError("things_mutation_preview_failed") from exc
        return _to_result(operation, captured[0], receipt=preview.mutation_receipt, undoable=undoable)

    if request.mutation_receipt is None:
        raise ToolError("things_mutation_receipt_required")
    captured_fresh_preview: list[NativeBackendResult] = []
    captured_execute: list[NativeBackendResult] = []

    async def read_state_execute() -> dict[str, Any]:
        result = await asyncio.to_thread(_safe_run, script_name, ["preview", *script_arguments])
        _validate_backend_result(operation, MutationPhase.PREVIEW, result)
        captured_fresh_preview.append(result)
        return _target_state_fingerprint(operation, result)

    async def mutate() -> NativeBackendResult:
        result = await asyncio.to_thread(_safe_run, script_name, ["execute", *script_arguments])
        captured_execute.append(result)
        _validate_backend_result(operation, MutationPhase.EXECUTE, result)
        return result

    async def verify(result: NativeBackendResult) -> dict[str, Any]:
        await asyncio.sleep(0)
        if result.status == "ambiguous" or not result.readback_verified:
            raise RuntimeError("native_verification_inconclusive")
        if result.status not in {"changed", "skipped", "failed"}:
            raise RuntimeError("native_verification_status_invalid")
        if operation in _CASCADE_OPERATIONS and (
            not captured_fresh_preview or result.cascade_count != captured_fresh_preview[0].cascade_count
        ):
            raise RuntimeError("native_cascade_scope_changed")
        counts = {"changed": 0, "skipped": 0, "failed": 0, "ambiguous": 0}
        counts[result.status] = outcome_count
        return {
            "status": result.status,
            **counts,
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
        backend = captured_execute[0] if captured_execute else None
        return NativeOperationResult(
            operation=operation,
            status="ambiguous",
            affected_count=backend.affected_count if backend is not None else 0,
            cascade_count=backend.cascade_count if backend is not None else 0,
            readback_verified=False,
            ui_handoff=False,
            undoable=undoable,
            message_code="things_mutation_ambiguous",
        )
    except MutationError as exc:
        raise ToolError("things_mutation_execute_failed") from exc
    return _to_result(
        operation,
        captured_execute[0],
        undoable=undoable,
        normalized_status=execution.status,
    )


__all__ = ["call_mutating"]
