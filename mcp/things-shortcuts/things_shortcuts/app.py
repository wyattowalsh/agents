"""FastMCP server exposing exactly 21 typed Things Shortcut tools."""

from __future__ import annotations

import asyncio
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from pydantic import Field

from .bridge import (
    BridgeExecutionError,
    BridgeProtocolError,
    BridgeTimeoutError,
    BridgeUnavailableError,
    list_fixed_bridges,
    probe_bridge,
)

# Import the concrete models separately to keep every public tool signature
# explicit for FastMCP schema generation.
from .models import (
    PROTOCOL_VERSION,
    BridgeHealth,
    BridgeIdentity,
    BridgeOperation,
    ChecklistMutationRequest,
    CreateHeadingRequest,
    CreateProjectRequest,
    CreateStructuredProjectRequest,
    CreateTodoRequest,
    CreateTodosRequest,
    DeleteHeadingRequest,
    DeleteItemsRequest,
    DuplicateItemsRequest,
    EditHeadingRequest,
    EditItemsRequest,
    FindItemsRequest,
    GetItemsRequest,
    GetSelectedItemsRequest,
    OpenListRequest,
    OperationResult,
    QuickEntryRequest,
    ShortcutsHealthResult,
    ShowItemsRequest,
)
from .mutations import (
    MinimumScope,
    call_mutating,
    call_non_mutating,
    target_ids_from_request,
)

mcp = FastMCP(
    "Things Shortcuts",
    instructions=(
        "Use only the fixed typed Things++ Shortcuts bridge. Never accept a "
        "Shortcut name, path, URL, shell, AppleScript, or raw JSON payload."
    ),
    mask_error_details=True,
)

_READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}
_UI_VISIBLE = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": False,
    "openWorldHint": False,
}
_WRITE = {
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": False,
    "openWorldHint": False,
}
_DESTRUCTIVE = {
    "readOnlyHint": False,
    "destructiveHint": True,
    "idempotentHint": False,
    "openWorldHint": False,
}


def _meta(name: str, scope: str, risk: str) -> dict[str, Any]:
    """Return independent OAuth-scope and risk metadata for MCPHub policy."""
    return {
        "securitySchemes": [{"type": "oauth2", "scopes": [scope]}],
        "thingsMinimumScope": scope,
        "thingsRisk": risk,
        "thingsSchemaContractId": f"things-shortcuts/{name}@v1",
    }


@mcp.tool(annotations=_READ_ONLY, meta=_meta("shortcuts_health", "things.read", "read-only"))
async def shortcuts_health() -> ShortcutsHealthResult:
    """Inspect both fixed bridge names and their protocol-v1 handshake.

    Use this before any Shortcut-backed operation or when a prerequisite may be
    missing. The protocol-health branch must not execute a Things action or
    provoke a Things TCC prompt. Returns typed absent, protocol_mismatch,
    tcc_degraded, or ready state without exposing other Shortcut names.
    """
    try:
        present = await asyncio.to_thread(list_fixed_bridges)
    except (
        BridgeUnavailableError,
        BridgeTimeoutError,
        BridgeProtocolError,
        UnicodeDecodeError,
    ):
        present = set()
    rows: list[BridgeHealth] = []
    protocol_mismatch = False
    tcc_degraded = False
    for identity in BridgeIdentity:
        if identity not in present:
            rows.append(
                BridgeHealth(
                    bridge=identity,
                    present=False,
                    protocol_match=False,
                    tcc_ready=False,
                    code="bridge_absent",
                )
            )
            continue
        try:
            response = await asyncio.to_thread(probe_bridge, identity)
        except BridgeProtocolError:
            protocol_mismatch = True
            rows.append(
                BridgeHealth(
                    bridge=identity,
                    present=True,
                    protocol_match=False,
                    tcc_ready=False,
                    code="protocol_mismatch",
                )
            )
        except (BridgeUnavailableError, BridgeTimeoutError, BridgeExecutionError):
            tcc_degraded = True
            rows.append(
                BridgeHealth(
                    bridge=identity,
                    present=True,
                    protocol_match=True,
                    tcc_ready=False,
                    code="tcc_degraded",
                )
            )
        else:
            tcc_degraded = tcc_degraded or not response.tcc_ready
            rows.append(
                BridgeHealth(
                    bridge=identity,
                    present=True,
                    protocol_match=True,
                    tcc_ready=response.tcc_ready,
                    code="bridge_ready" if response.tcc_ready else "tcc_degraded",
                )
            )
    if len(present) != 2:
        status = "absent"
        code = "fixed_bridge_absent"
    elif protocol_mismatch:
        status = "protocol_mismatch"
        code = "fixed_bridge_protocol_mismatch"
    elif tcc_degraded:
        status = "tcc_degraded"
        code = "fixed_bridge_tcc_degraded"
    else:
        status = "ready"
        code = "fixed_bridges_ready"
    return ShortcutsHealthResult(
        status=status,
        protocol_version=PROTOCOL_VERSION,
        bridges=rows,
        message_code=code,
    )


async def _mutate(
    operation: BridgeOperation,
    request: Any,
    ctx: Context | None,
    scope: MinimumScope,
) -> OperationResult:
    """Delegate one closed mutation request through the shared receipt layer."""
    return await call_mutating(
        operation,
        request,
        ctx=ctx,
        minimum_scope=scope,
        target_ids=target_ids_from_request(operation, request),
    )


@mcp.tool(annotations=_WRITE, meta=_meta("create_todo", "things.write", "single-write"))
async def create_todo(
    request: Annotated[
        CreateTodoRequest,
        Field(description="Closed single-to-do request with mutation envelope."),
    ],
    ctx: Context | None = None,
) -> OperationResult:
    """Preview or create one typed Things to-do through the fixed agent bridge.

    Use for one bounded, non-arbitrary create. Do not use for Quick Entry or a
    raw Things URL/JSON payload. Returns preview receipt or verified per-item
    changed/skipped/failed/ambiguous counts.
    """
    return await _mutate(BridgeOperation.CREATE_TODO, request, ctx, "things.write")


@mcp.tool(annotations=_WRITE, meta=_meta("create_todos", "things.write", "bulk-write"))
async def create_todos(
    request: Annotated[
        CreateTodosRequest,
        Field(description="Closed one-to-25-to-do request with mutation envelope."),
    ],
    ctx: Context | None = None,
) -> OperationResult:
    """Preview or create up to 25 independently typed Things to-dos.

    Use for bounded multi-create when every item is already known. Do not use
    for an unbounded import or raw payload. Returns a per-item structured
    receipt and aggregate verified outcome counts.
    """
    return await _mutate(BridgeOperation.CREATE_TODOS, request, ctx, "things.write")


@mcp.tool(
    annotations=_UI_VISIBLE,
    meta=_meta("create_todo_with_quick_entry", "things.write", "ui-handoff"),
)
async def create_todo_with_quick_entry(
    request: Annotated[
        QuickEntryRequest,
        Field(description="Typed Quick Entry prefill; headings cannot be targeted."),
    ],
) -> OperationResult:
    """Open Things Quick Entry with typed optional prefill as a UI handoff.

    Use only when the user will review and save in Things. This cannot target a
    heading and is intentionally exempt from mutation receipts because the
    server does not perform the final write. Returns ui_handoff, never changed.
    """
    result = await call_non_mutating(
        BridgeOperation.CREATE_TODO_WITH_QUICK_ENTRY,
        request.model_dump(by_alias=True, mode="json"),
    )
    if result.status != "ui_handoff" or result.changed_count != 0:
        from fastmcp.exceptions import ToolError

        raise ToolError("things_quick_entry_result_invalid")
    return result


@mcp.tool(annotations=_WRITE, meta=_meta("create_heading", "things.write", "single-write"))
async def create_heading(
    request: Annotated[
        CreateHeadingRequest,
        Field(description="Typed heading create request with project ID and mutation envelope."),
    ],
    ctx: Context | None = None,
) -> OperationResult:
    """Preview or create one heading in an existing Things project.

    Use with an exact project ID. Do not pass a project title or attempt
    positional reordering. Returns a preview receipt or verified outcome.
    """
    return await _mutate(BridgeOperation.CREATE_HEADING, request, ctx, "things.write")


@mcp.tool(annotations=_WRITE, meta=_meta("create_project", "things.write", "single-write"))
async def create_project(
    request: Annotated[
        CreateProjectRequest,
        Field(description="Typed project create request with mutation envelope."),
    ],
    ctx: Context | None = None,
) -> OperationResult:
    """Preview or create one typed Things project.

    Use for a project without a nested structured plan. Do not use for raw URL
    or JSON creation; use create_structured_project for bounded headings and
    children. Returns preview or verified create evidence.
    """
    return await _mutate(BridgeOperation.CREATE_PROJECT, request, ctx, "things.write")


@mcp.tool(
    annotations=_WRITE,
    meta=_meta("create_structured_project", "things.write", "bulk-write"),
)
async def create_structured_project(
    request: Annotated[
        CreateStructuredProjectRequest,
        Field(description="Typed bounded project, headings, and child to-dos."),
    ],
    ctx: Context | None = None,
) -> OperationResult:
    """Preview or create a project with typed headings and at most 25 to-dos.

    Use as the safe replacement for SupaThings structured JSON creation. It
    never accepts raw JSON, a URL, or positional-reorder directives. Returns a
    preview receipt or verified bulk outcome.
    """
    return await _mutate(BridgeOperation.CREATE_STRUCTURED_PROJECT, request, ctx, "things.write")


@mcp.tool(annotations=_READ_ONLY, meta=_meta("find_items", "things.read", "read-only"))
async def find_items(
    request: Annotated[
        FindItemsRequest,
        Field(description="Literal bounded native Things search criteria."),
    ],
) -> OperationResult:
    """Find up to 25 Things items with native typed search filters.

    Use for native item lookup where core search is not schema-equivalent. Do
    not pass a query language, URL, or retrieved instruction. Returns typed
    private item data directly to the caller without logging it.
    """
    return await call_non_mutating(BridgeOperation.FIND_ITEMS, request.model_dump(by_alias=True, mode="json"))


@mcp.tool(annotations=_READ_ONLY, meta=_meta("get_items", "things.read", "read-only"))
async def get_items(
    request: Annotated[GetItemsRequest, Field(description="One to 25 exact Things item IDs.")],
) -> OperationResult:
    """Read a bounded explicit set of Things items by opaque ID.

    Use for ID-first inspection and read-after-write checks. Do not target by
    title or return more than 25 items. Returns closed typed item objects.
    """
    return await call_non_mutating(BridgeOperation.GET_ITEMS, request.model_dump(by_alias=True, mode="json"))


@mcp.tool(annotations=_READ_ONLY, meta=_meta("get_selected_items", "things.read", "read-only"))
async def get_selected_items(
    request: Annotated[
        GetSelectedItemsRequest,
        Field(description="Bound for reading the current Things selection."),
    ],
) -> OperationResult:
    """Read up to 25 items currently selected in the Things UI.

    Use only when the active selection is relevant and user-visible. Do not
    infer a selection or mutate it. Returns typed selected items without
    persisting their private content.
    """
    return await call_non_mutating(
        BridgeOperation.GET_SELECTED_ITEMS,
        request.model_dump(by_alias=True, mode="json"),
    )


@mcp.tool(annotations=_WRITE, meta=_meta("edit_items", "things.write", "bulk-write"))
async def edit_items(
    request: Annotated[
        EditItemsRequest,
        Field(description="One closed patch for one to 25 explicit IDs."),
    ],
    ctx: Context | None = None,
) -> OperationResult:
    """Preview or apply one non-undoable typed patch to up to 25 items.

    Use only after ID-first review and explicit bulk approval. Do not pass a raw
    update object or attempt recurrence/reordering. Returns verified per-item
    outcomes and reports undoable=false.
    """
    return await _mutate(BridgeOperation.EDIT_ITEMS, request, ctx, "things.write")


@mcp.tool(annotations=_WRITE, meta=_meta("edit_heading", "things.write", "single-write"))
async def edit_heading(
    request: Annotated[EditHeadingRequest, Field(description="Exact heading ID and replacement title.")],
    ctx: Context | None = None,
) -> OperationResult:
    """Preview or rename one existing Things heading by ID.

    Use for a known heading after a fresh project read. Do not use it for
    positional reordering or identify a heading by title. Returns preview or
    verified change evidence.
    """
    return await _mutate(BridgeOperation.EDIT_HEADING, request, ctx, "things.write")


async def _checklist(
    operation: BridgeOperation, request: ChecklistMutationRequest, ctx: Context | None
) -> OperationResult:
    return await _mutate(operation, request, ctx, "things.write")


@mcp.tool(annotations=_WRITE, meta=_meta("edit_checklist", "things.write", "single-write"))
async def edit_checklist(
    request: Annotated[
        ChecklistMutationRequest,
        Field(description="Replacement checklist for one exact item ID."),
    ],
    ctx: Context | None = None,
) -> OperationResult:
    """Preview or replace one Things checklist with up to 25 typed entries.

    Use when replacement semantics are intended. Do not use for append or
    prepend behavior and never pass a raw list payload. Returns verified change
    evidence.
    """
    return await _checklist(BridgeOperation.EDIT_CHECKLIST, request, ctx)


@mcp.tool(annotations=_WRITE, meta=_meta("append_checklist", "things.write", "single-write"))
async def append_checklist(
    request: Annotated[
        ChecklistMutationRequest,
        Field(description="Checklist entries to append to one exact item ID."),
    ],
    ctx: Context | None = None,
) -> OperationResult:
    """Preview or append up to 25 entries to one Things checklist.

    Use only for append semantics on an exact ID. Do not replace existing
    entries or infer a target from its title. Returns verified change evidence.
    """
    return await _checklist(BridgeOperation.APPEND_CHECKLIST, request, ctx)


@mcp.tool(annotations=_WRITE, meta=_meta("prepend_checklist", "things.write", "single-write"))
async def prepend_checklist(
    request: Annotated[
        ChecklistMutationRequest,
        Field(description="Checklist entries to prepend to one exact item ID."),
    ],
    ctx: Context | None = None,
) -> OperationResult:
    """Preview or prepend up to 25 entries to one Things checklist.

    Use only for prepend semantics on an exact ID. Do not replace existing
    entries or request positional reordering. Returns verified change evidence.
    """
    return await _checklist(BridgeOperation.PREPEND_CHECKLIST, request, ctx)


@mcp.tool(annotations=_WRITE, meta=_meta("duplicate_items", "things.write", "bulk-write"))
async def duplicate_items(
    request: Annotated[DuplicateItemsRequest, Field(description="One to 25 explicit source item IDs.")],
    ctx: Context | None = None,
) -> OperationResult:
    """Preview or duplicate up to 25 exact Things items.

    Use only after reviewing the source IDs and duplicate risk. Do not use as an
    unbounded copy/import mechanism. Returns per-item verified outcomes.
    """
    return await _mutate(BridgeOperation.DUPLICATE_ITEMS, request, ctx, "things.write")


@mcp.tool(
    annotations=_DESTRUCTIVE,
    meta=_meta("delete_items", "things.admin", "destructive-write"),
)
async def delete_items(
    request: Annotated[
        DeleteItemsRequest,
        Field(description="One to 25 item IDs to move to Things Trash."),
    ],
    ctx: Context | None = None,
) -> OperationResult:
    """Preview or move up to 25 exact Things items to Trash.

    Use only after explicit destructive approval. This always routes through
    the fixed destructive bridge and never accepts titles or raw commands.
    Returns verified per-item outcomes.
    """
    return await _mutate(BridgeOperation.DELETE_ITEMS, request, ctx, "things.admin")


@mcp.tool(
    annotations=_DESTRUCTIVE,
    meta=_meta("delete_items_immediately", "things.admin", "destructive-write"),
)
async def delete_items_immediately(
    request: Annotated[
        DeleteItemsRequest,
        Field(description="One to 25 exact item IDs for immediate deletion."),
    ],
    ctx: Context | None = None,
) -> OperationResult:
    """Preview or immediately delete up to 25 exact Things items.

    Use only after explicit irreversible-operation approval. It always uses the
    destructive bridge and is non-undoable. Returns verified per-item outcomes
    with undoable=false.
    """
    return await _mutate(BridgeOperation.DELETE_ITEMS_IMMEDIATELY, request, ctx, "things.admin")


@mcp.tool(
    annotations=_DESTRUCTIVE,
    meta=_meta("delete_heading", "things.admin", "destructive-write"),
)
async def delete_heading(
    request: Annotated[
        DeleteHeadingRequest,
        Field(description="Exact heading ID with mutation envelope."),
    ],
    ctx: Context | None = None,
) -> OperationResult:
    """Preview or delete one heading through the destructive bridge.

    The preview must report the child cascade count before approval. Do not
    execute when that count is absent or ambiguous. Returns verified deletion
    evidence and the same cascade scope.
    """
    return await _mutate(BridgeOperation.DELETE_HEADING, request, ctx, "things.admin")


@mcp.tool(annotations=_UI_VISIBLE, meta=_meta("open_list", "things.read", "ui-visible"))
async def open_list(
    request: Annotated[OpenListRequest, Field(description="One fixed built-in Things list.")],
) -> OperationResult:
    """Open one fixed built-in list in the Things UI.

    Use only for a deliberate UI-visible handoff. The list is a closed enum, so
    this tool cannot open a URL or arbitrary target. Returns shown status, not a
    mutation result.
    """
    return await call_non_mutating(BridgeOperation.OPEN_LIST, request.model_dump(by_alias=True, mode="json"))


@mcp.tool(annotations=_UI_VISIBLE, meta=_meta("show_items", "things.read", "ui-visible"))
async def show_items(
    request: Annotated[
        ShowItemsRequest,
        Field(description="One to 25 exact item IDs to show in Things."),
    ],
) -> OperationResult:
    """Show a bounded explicit item set in the Things UI.

    Use after ID-first selection when a UI-visible handoff is wanted. Do not
    pass titles, URLs, or more than 25 IDs. Returns shown status without
    claiming that Things data changed.
    """
    return await call_non_mutating(BridgeOperation.SHOW_ITEMS, request.model_dump(by_alias=True, mode="json"))
