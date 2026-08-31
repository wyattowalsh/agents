"""Closed input and output models for Things native operations."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, model_validator

NativeOperation = Literal[
    "open_search",
    "log_completed",
    "empty_trash",
    "delete_area",
    "rename_tag",
    "delete_tag",
    "set_tag_parent",
]

_URI_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def _validate_identifier(value: str) -> str:
    """Reject URL and filesystem-path shapes while preserving opaque IDs."""
    if _URI_SCHEME.match(value) or "/" in value or "\\" in value or value in {".", ".."} or value.startswith("~"):
        raise ValueError("identifier must not be a URI or filesystem path")
    return value


Identifier = Annotated[
    str,
    Field(
        min_length=1,
        max_length=256,
        pattern=r"^[^\x00-\x1f\x7f]+$",
        description="Opaque Things identifier; never a title, URL, or script fragment.",
    ),
    AfterValidator(_validate_identifier),
]
ShortText = Annotated[
    str,
    Field(
        min_length=1,
        max_length=512,
        pattern=r"^[^\x00-\x1f\x7f]+$",
        description="Bounded single-line text value.",
    ),
]


class ClosedModel(BaseModel):
    """Base model that rejects undeclared fields and type coercion."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, strict=True)


class MutationPhase(StrEnum):
    """Two-phase mutation state."""

    PREVIEW = "preview"
    EXECUTE = "execute"


def _parse_mutation_phase(value: object) -> MutationPhase:
    """Decode the exact public phase string without accepting other coercions."""
    if isinstance(value, MutationPhase):
        return value
    if type(value) is not str:
        raise ValueError("mutationPhase must be preview or execute")
    try:
        return MutationPhase(value)
    except ValueError as exc:
        raise ValueError("mutationPhase must be preview or execute") from exc


PublicMutationPhase = Annotated[MutationPhase, BeforeValidator(_parse_mutation_phase)]


class MutationRequest(ClosedModel):
    """Common preview/execute envelope for native mutations."""

    mutation_phase: Annotated[
        PublicMutationPhase,
        Field(alias="mutationPhase", description="Preview or execute this exact mutation."),
    ]
    mutation_receipt: Annotated[
        str | None,
        Field(
            alias="mutationReceipt",
            default=None,
            min_length=43,
            max_length=128,
            description="Opaque receipt returned by preview; required only for execute.",
        ),
    ] = None

    @model_validator(mode="after")
    def validate_receipt_phase(self) -> MutationRequest:
        """Require an opaque receipt exactly for execute."""
        if self.mutation_phase is MutationPhase.EXECUTE and not self.mutation_receipt:
            raise ValueError("mutationReceipt is required for execute")
        if self.mutation_phase is MutationPhase.PREVIEW and self.mutation_receipt is not None:
            raise ValueError("mutationReceipt is not accepted during preview")
        return self


class OpenSearchRequest(ClosedModel):
    """Optional literal text for the fixed Things search URL."""

    query: Annotated[
        str | None,
        Field(
            default=None,
            min_length=1,
            max_length=512,
            description="Optional literal search text; never a URL.",
        ),
    ] = None


class LogCompletedRequest(MutationRequest):
    """Preview or run Things log-completed maintenance."""


class EmptyTrashRequest(MutationRequest):
    """Preview or irreversibly empty Things Trash."""


class DeleteAreaRequest(MutationRequest):
    """Preview or delete one area and report its child cascade."""

    area_id: Annotated[Identifier, Field(alias="areaId", description="Target area ID.")]


class RenameTagRequest(MutationRequest):
    """Preview or rename one tag."""

    tag_id: Annotated[Identifier, Field(alias="tagId", description="Target tag ID.")]
    new_name: Annotated[ShortText, Field(alias="newName", description="Replacement tag name.")]


class DeleteTagRequest(MutationRequest):
    """Preview or delete one tag and report impacted tagged items."""

    tag_id: Annotated[Identifier, Field(alias="tagId", description="Target tag ID.")]


class SetTagParentRequest(MutationRequest):
    """Preview or assign one tag to a different parent tag."""

    tag_id: Annotated[Identifier, Field(alias="tagId", description="Child tag ID.")]
    parent_tag_id: Annotated[
        Identifier,
        Field(
            alias="parentTagId",
            description="Parent tag ID; detach/null is unsupported.",
        ),
    ]

    @model_validator(mode="after")
    def reject_self_parent(self) -> SetTagParentRequest:
        """Reject an immediate tag-parent cycle."""
        if self.tag_id == self.parent_tag_id:
            raise ValueError("a tag cannot be its own parent")
        return self


class NativeHealthResult(ClosedModel):
    """Static bundle health that never sends an AppleEvent."""

    status: Annotated[
        Literal["ready_static", "app_absent", "sdef_missing", "bundle_mismatch"],
        Field(description="Static native bundle readiness."),
    ]
    app_version: Annotated[
        str | None,
        Field(
            alias="appVersion",
            max_length=64,
            description="Installed Things version, if readable.",
        ),
    ]
    sdef_present: Annotated[
        bool,
        Field(alias="sdefPresent", description="Whether the fixed Things SDEF is present."),
    ]
    script_bundle_verified: Annotated[
        bool,
        Field(
            alias="scriptBundleVerified",
            description="Whether all fixed source hashes match.",
        ),
    ]
    tcc_status: Annotated[
        Literal["unproven"],
        Field(alias="tccStatus", description="TCC is intentionally not probed by health."),
    ]
    invokes_apple_event: Annotated[
        Literal[False],
        Field(
            default=False,
            alias="invokesAppleEvent",
            description="Health never sends an AppleEvent.",
        ),
    ] = False
    message_code: Annotated[
        str,
        Field(
            alias="messageCode",
            min_length=1,
            max_length=64,
            pattern=r"^[a-z0-9_-]+$",
            description="Content-free health code.",
        ),
    ]


class NativeOperationResult(ClosedModel):
    """Content-free native operation result."""

    operation: Annotated[
        NativeOperation,
        Field(description="Fixed native operation name."),
    ]
    status: Annotated[
        Literal["previewed", "changed", "skipped", "failed", "ambiguous", "ui_handoff"],
        Field(description="Operation outcome."),
    ]
    mutation_receipt: Annotated[
        str | None,
        Field(
            alias="mutationReceipt",
            default=None,
            max_length=128,
            description="Opaque execute receipt for a preview.",
        ),
    ] = None
    affected_count: Annotated[
        int,
        Field(
            alias="affectedCount",
            default=0,
            ge=0,
            le=100_000,
            description="Number of directly affected records.",
        ),
    ] = 0
    cascade_count: Annotated[
        int,
        Field(
            alias="cascadeCount",
            default=0,
            ge=0,
            le=100_000,
            description="Number of child records in a delete cascade.",
        ),
    ] = 0
    readback_verified: Annotated[
        bool,
        Field(
            alias="readbackVerified",
            default=False,
            description="Whether state was freshly verified after execution.",
        ),
    ] = False
    ui_handoff: Annotated[
        bool,
        Field(
            alias="uiHandoff",
            default=False,
            description="Whether completion was handed to Things UI.",
        ),
    ] = False
    undoable: Annotated[
        bool | None,
        Field(
            default=None,
            description="Whether the operation is expected to be undoable.",
        ),
    ] = None
    message_code: Annotated[
        str,
        Field(
            alias="messageCode",
            min_length=1,
            max_length=64,
            pattern=r"^[a-z0-9_-]+$",
            description="Content-free outcome code.",
        ),
    ]
