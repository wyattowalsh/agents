"""FastMCP server exposing exactly eight fixed Things native tools."""

from __future__ import annotations

import asyncio
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from .models import (
    DeleteAreaRequest,
    DeleteTagRequest,
    EmptyTrashRequest,
    LogCompletedRequest,
    NativeHealthResult,
    NativeOperationResult,
    OpenSearchRequest,
    RenameTagRequest,
    SetTagParentRequest,
)
from .mutations import call_mutating
from .runner import (
    NativeArtifactError,
    NativeExecutionError,
    NativeTimeoutError,
    NativeUnavailableError,
    open_search_url,
    static_health,
)

mcp = FastMCP(
    "Things Native",
    instructions=(
        "Use only fixed official Things AppleScript outcomes and the internally "
        "built things:///search URL. Never accept script, shell, URL, path, SQL, "
        "recurrence, or reorder input."
    ),
    mask_error_details=True,
)

# FastMCP resolves these annotations at runtime while generating tool schemas.
_RUNTIME_SCHEMA_TYPES = (
    DeleteAreaRequest,
    DeleteTagRequest,
    EmptyTrashRequest,
    LogCompletedRequest,
    NativeHealthResult,
    NativeOperationResult,
    OpenSearchRequest,
    RenameTagRequest,
    SetTagParentRequest,
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
        "thingsSchemaContractId": f"things-native/{name}@v1",
    }


@mcp.tool(annotations=_READ_ONLY, meta=_meta("native_health", "things.read", "read-only"))
def native_health() -> NativeHealthResult:
    """Inspect Things app, SDEF, version, and fixed-script bundle statically.

    Use before native operations or when the app bundle may have changed. This
    function reads only fixed bundle paths and never sends an AppleEvent, opens
    Things, or triggers TCC. Returns static readiness with TCC explicitly
    unproven rather than claiming live authorization.
    """
    return static_health()


@mcp.tool(annotations=_UI_VISIBLE, meta=_meta("open_search", "things.read", "ui-visible"))
async def open_search(
    request: Annotated[
        OpenSearchRequest,
        Field(description="Optional literal query for the fixed Things search command."),
    ],
) -> NativeOperationResult:
    """Open only the fixed Things search UI with optional encoded literal text.

    Use for an explicit UI-visible search handoff. The caller cannot supply a
    URL; this server builds things:///search and percent-encodes the query
    internally. Returns ui_handoff without claiming Things data changed.
    """
    try:
        return await asyncio.to_thread(open_search_url, request.query)
    except NativeUnavailableError as exc:
        raise ToolError("things_native_absent") from exc
    except NativeTimeoutError as exc:
        raise ToolError("things_native_timeout") from exc
    except (NativeArtifactError, NativeExecutionError) as exc:
        raise ToolError("things_native_open_search_failed") from exc


@mcp.tool(
    annotations=_DESTRUCTIVE,
    meta=_meta("log_completed", "things.admin", "destructive-write"),
)
async def log_completed(
    request: Annotated[
        LogCompletedRequest,
        Field(description="Log-completed preview/execute envelope."),
    ],
    ctx: Context | None = None,
) -> NativeOperationResult:
    """Preview or run the official Things log-completed-now command.

    Use only when Things is configured for manual logging and after explicit
    maintenance approval. It selects fixed AppleScript source and serializes no
    code through input. Returns a receipt or verified maintenance outcome.
    """
    return await call_mutating(
        "log_completed",
        "log_completed",
        request,
        ctx=ctx,
        minimum_scope="things.admin",
        target_ids=("log-completed-outcome",),
        outcome_count=1,
        script_arguments=[],
        undoable=False,
    )


@mcp.tool(
    annotations=_DESTRUCTIVE,
    meta=_meta("empty_trash", "things.admin", "destructive-write"),
)
async def empty_trash(
    request: Annotated[EmptyTrashRequest, Field(description="Empty-Trash preview/execute envelope.")],
    ctx: Context | None = None,
) -> NativeOperationResult:
    """Preview or irreversibly empty the Things Trash.

    Use only after explicit approval of the reported Trash count. It cannot
    target any other list and is non-undoable. Returns cascade scope plus
    verified changed or ambiguous state.
    """
    return await call_mutating(
        "empty_trash",
        "empty_trash",
        request,
        ctx=ctx,
        minimum_scope="things.admin",
        target_ids=("empty-trash-outcome",),
        outcome_count=1,
        script_arguments=[],
        undoable=False,
    )


@mcp.tool(
    annotations=_DESTRUCTIVE,
    meta=_meta("delete_area", "things.admin", "destructive-write"),
)
async def delete_area(
    request: Annotated[
        DeleteAreaRequest,
        Field(description="Exact area ID plus preview/execute envelope."),
    ],
    ctx: Context | None = None,
) -> NativeOperationResult:
    """Preview or delete one Things area by opaque ID.

    The preview reports the number of child to-dos moved to Trash by the area
    cascade. Use only after explicit approval of that scope; never target an
    area by title. Returns verified deletion evidence.
    """
    return await call_mutating(
        "delete_area",
        "delete_area",
        request,
        ctx=ctx,
        minimum_scope="things.admin",
        target_ids=(request.area_id,),
        outcome_count=1,
        script_arguments=[request.area_id],
        undoable=False,
    )


@mcp.tool(annotations=_WRITE, meta=_meta("rename_tag", "things.write", "single-write"))
async def rename_tag(
    request: Annotated[
        RenameTagRequest,
        Field(description="Exact tag ID, new name, and preview/execute envelope."),
    ],
    ctx: Context | None = None,
) -> NativeOperationResult:
    """Preview or rename one Things tag by opaque ID.

    Use after a fresh tag lookup and duplicate-name review. The replacement is
    passed only as one argv value, never interpolated into AppleScript source.
    Returns verified change evidence.
    """
    return await call_mutating(
        "rename_tag",
        "rename_tag",
        request,
        ctx=ctx,
        minimum_scope="things.write",
        target_ids=(request.tag_id,),
        outcome_count=1,
        script_arguments=[request.tag_id, request.new_name],
        undoable=None,
    )


@mcp.tool(
    annotations=_DESTRUCTIVE,
    meta=_meta("delete_tag", "things.admin", "destructive-write"),
)
async def delete_tag(
    request: Annotated[
        DeleteTagRequest,
        Field(description="Exact tag ID plus preview/execute envelope."),
    ],
    ctx: Context | None = None,
) -> NativeOperationResult:
    """Preview or delete one Things tag by opaque ID.

    Use only after explicit approval of the reported number of tagged items
    affected. The operation cannot delete arbitrary objects or execute dynamic
    source. Returns verified tag deletion evidence.
    """
    return await call_mutating(
        "delete_tag",
        "delete_tag",
        request,
        ctx=ctx,
        minimum_scope="things.admin",
        target_ids=(request.tag_id,),
        outcome_count=1,
        script_arguments=[request.tag_id],
        undoable=False,
    )


@mcp.tool(annotations=_WRITE, meta=_meta("set_tag_parent", "things.write", "single-write"))
async def set_tag_parent(
    request: Annotated[
        SetTagParentRequest,
        Field(description="Exact child and parent tag IDs plus mutation envelope."),
    ],
    ctx: Context | None = None,
) -> NativeOperationResult:
    """Preview or assign one tag to one parent tag by opaque IDs.

    Use after validating both IDs and hierarchy intent. This version supports
    assignment only: detach/null, arbitrary hierarchy operations, and reorder
    are intentionally not representable. Returns verified parent assignment.
    """
    return await call_mutating(
        "set_tag_parent",
        "set_tag_parent",
        request,
        ctx=ctx,
        minimum_scope="things.write",
        target_ids=(request.tag_id,),
        outcome_count=1,
        script_arguments=[request.tag_id, request.parent_tag_id],
        undoable=None,
    )
