"""Closed protocol and MCP models for the Things++ Shortcuts bridge."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, model_validator

MAX_BATCH_ITEMS = 25
PROTOCOL_VERSION = "1"
AGENT_BRIDGE_NAME = "Things++ Agent Bridge"
DESTRUCTIVE_BRIDGE_NAME = "Things++ Destructive Bridge"

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
        description="Opaque Things item identifier; never a title or URL.",
    ),
    AfterValidator(_validate_identifier),
]
BoundedText = Annotated[
    str,
    Field(
        min_length=1,
        max_length=4096,
        pattern=r"^[^\x00\x7f]+$",
        description="Bounded text value with NUL and DEL characters rejected.",
    ),
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
    """Base model that rejects undeclared protocol fields and coercion."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, strict=True)


class MutationPhase(StrEnum):
    """Two-phase mutation state."""

    PREVIEW = "preview"
    EXECUTE = "execute"


class BridgeIdentity(StrEnum):
    """Only bridge identities accepted by the protocol."""

    AGENT = AGENT_BRIDGE_NAME
    DESTRUCTIVE = DESTRUCTIVE_BRIDGE_NAME


class BridgeOperation(StrEnum):
    """Fixed operation universe implemented by the two Shortcuts."""

    PROTOCOL_HEALTH = "protocol_health"
    CREATE_TODO = "create_todo"
    CREATE_TODOS = "create_todos"
    CREATE_TODO_WITH_QUICK_ENTRY = "create_todo_with_quick_entry"
    CREATE_HEADING = "create_heading"
    CREATE_PROJECT = "create_project"
    CREATE_STRUCTURED_PROJECT = "create_structured_project"
    FIND_ITEMS = "find_items"
    GET_ITEMS = "get_items"
    GET_SELECTED_ITEMS = "get_selected_items"
    EDIT_ITEMS = "edit_items"
    EDIT_HEADING = "edit_heading"
    EDIT_CHECKLIST = "edit_checklist"
    APPEND_CHECKLIST = "append_checklist"
    PREPEND_CHECKLIST = "prepend_checklist"
    DUPLICATE_ITEMS = "duplicate_items"
    DELETE_ITEMS = "delete_items"
    DELETE_ITEMS_IMMEDIATELY = "delete_items_immediately"
    DELETE_HEADING = "delete_heading"
    OPEN_LIST = "open_list"
    SHOW_ITEMS = "show_items"


DESTRUCTIVE_OPERATIONS = frozenset({
    BridgeOperation.DELETE_ITEMS,
    BridgeOperation.DELETE_ITEMS_IMMEDIATELY,
    BridgeOperation.DELETE_HEADING,
})


class ItemKind(StrEnum):
    """Things item kinds returned by native Shortcut actions."""

    TODO = "todo"
    PROJECT = "project"
    HEADING = "heading"
    AREA = "area"


class ItemStatus(StrEnum):
    """Supported Things item states."""

    OPEN = "open"
    COMPLETED = "completed"
    CANCELED = "canceled"


class BuiltinList(StrEnum):
    """Fixed built-in Things lists that may be opened or targeted."""

    INBOX = "inbox"
    TODAY = "today"
    UPCOMING = "upcoming"
    ANYTIME = "anytime"
    SOMEDAY = "someday"
    LOGBOOK = "logbook"
    TRASH = "trash"


def _parse_public_string_enum[StringEnumT: StrEnum](
    value: object,
    enum_type: type[StringEnumT],
) -> StringEnumT:
    """Decode an exact public string enum without accepting other coercions."""
    if isinstance(value, enum_type):
        return value
    if type(value) is not str:
        raise ValueError("value must be an exact string enum member")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError("value must be an exact string enum member") from exc


def _parse_mutation_phase(value: object) -> MutationPhase:
    return _parse_public_string_enum(value, MutationPhase)


def _parse_bridge_identity(value: object) -> BridgeIdentity:
    return _parse_public_string_enum(value, BridgeIdentity)


def _parse_bridge_operation(value: object) -> BridgeOperation:
    return _parse_public_string_enum(value, BridgeOperation)


def _parse_item_kind(value: object) -> ItemKind:
    return _parse_public_string_enum(value, ItemKind)


def _parse_item_status(value: object) -> ItemStatus:
    return _parse_public_string_enum(value, ItemStatus)


def _parse_builtin_list(value: object) -> BuiltinList:
    return _parse_public_string_enum(value, BuiltinList)


PublicMutationPhase = Annotated[MutationPhase, BeforeValidator(_parse_mutation_phase)]
PublicBridgeIdentity = Annotated[BridgeIdentity, BeforeValidator(_parse_bridge_identity)]
PublicBridgeOperation = Annotated[BridgeOperation, BeforeValidator(_parse_bridge_operation)]
PublicItemKind = Annotated[ItemKind, BeforeValidator(_parse_item_kind)]
PublicItemStatus = Annotated[ItemStatus, BeforeValidator(_parse_item_status)]
PublicBuiltinList = Annotated[BuiltinList, BeforeValidator(_parse_builtin_list)]


class MutationRequest(ClosedModel):
    """Common preview/execute envelope for server-executed mutations."""

    mutation_phase: Annotated[
        PublicMutationPhase,
        Field(alias="mutationPhase", description="Preview or execute this exact mutation."),
    ]
    mutation_receipt: Annotated[
        str | None,
        Field(
            alias="mutationReceipt",
            min_length=43,
            max_length=128,
            description="Opaque receipt returned by preview; required only for execute.",
        ),
    ] = None

    @model_validator(mode="after")
    def validate_receipt_phase(self) -> MutationRequest:
        """Require receipts exactly for execute requests."""
        if self.mutation_phase is MutationPhase.EXECUTE and not self.mutation_receipt:
            raise ValueError("mutationReceipt is required for execute")
        if self.mutation_phase is MutationPhase.PREVIEW and self.mutation_receipt is not None:
            raise ValueError("mutationReceipt is not accepted during preview")
        return self


class ChecklistEntry(ClosedModel):
    """A closed checklist entry."""

    title: ShortText
    completed: Annotated[
        bool,
        Field(default=False, description="Whether the checklist entry is complete."),
    ] = False


class TodoDraft(ClosedModel):
    """Typed fields accepted when creating a to-do without raw URL or JSON input."""

    title: ShortText
    notes: Annotated[
        str | None,
        Field(default=None, max_length=20_000, description="Optional Things notes text."),
    ] = None
    destination_list: Annotated[
        PublicBuiltinList | None,
        Field(
            default=None,
            alias="list",
            description="Optional built-in destination list.",
        ),
    ] = None
    project_id: Annotated[
        Identifier | None,
        Field(default=None, alias="projectId", description="Optional target project ID."),
    ] = None
    heading_id: Annotated[
        Identifier | None,
        Field(default=None, alias="headingId", description="Optional target heading ID."),
    ] = None
    tag_names: Annotated[
        list[ShortText],
        Field(
            default_factory=list,
            alias="tagNames",
            max_length=MAX_BATCH_ITEMS,
            description="Existing tag names.",
        ),
    ]
    when: Annotated[
        str | None,
        Field(
            default=None,
            max_length=128,
            description="Optional Things start value or ISO date.",
        ),
    ] = None
    deadline: Annotated[
        str | None,
        Field(default=None, max_length=128, description="Optional ISO deadline value."),
    ] = None
    reminder: Annotated[
        str | None,
        Field(default=None, max_length=128, description="Optional ISO reminder value."),
    ] = None
    checklist: Annotated[
        list[ChecklistEntry],
        Field(
            default_factory=list,
            max_length=MAX_BATCH_ITEMS,
            description="Initial checklist entries.",
        ),
    ]

    @model_validator(mode="after")
    def validate_destination(self) -> TodoDraft:
        """Reject contradictory destination selectors."""
        if self.destination_list is not None and (self.project_id is not None or self.heading_id is not None):
            raise ValueError("list cannot be combined with projectId or headingId")
        if self.heading_id is not None and self.project_id is None:
            raise ValueError("headingId requires projectId")
        return self


class QuickEntryDraft(ClosedModel):
    """Quick Entry fields; headings are intentionally not representable."""

    title: Annotated[
        str | None,
        Field(default=None, max_length=512, description="Optional prefilled title."),
    ] = None
    notes: Annotated[
        str | None,
        Field(default=None, max_length=20_000, description="Optional prefilled notes."),
    ] = None
    project_id: Annotated[
        Identifier | None,
        Field(
            default=None,
            alias="projectId",
            description="Optional project destination; headings are unsupported.",
        ),
    ] = None
    tag_names: Annotated[
        list[ShortText],
        Field(
            default_factory=list,
            alias="tagNames",
            max_length=MAX_BATCH_ITEMS,
            description="Existing tag names to prefill.",
        ),
    ]


class ProjectDraft(ClosedModel):
    """Typed fields accepted when creating a Things project."""

    title: ShortText
    notes: Annotated[
        str | None,
        Field(default=None, max_length=20_000, description="Optional project notes."),
    ] = None
    area_id: Annotated[
        Identifier | None,
        Field(default=None, alias="areaId", description="Optional owning area ID."),
    ] = None
    tag_names: Annotated[
        list[ShortText],
        Field(
            default_factory=list,
            alias="tagNames",
            max_length=MAX_BATCH_ITEMS,
            description="Existing project tag names.",
        ),
    ]
    deadline: Annotated[
        str | None,
        Field(default=None, max_length=128, description="Optional ISO deadline."),
    ] = None


class HeadingDraft(ClosedModel):
    """A heading and its bounded child to-do drafts."""

    title: ShortText
    todos: Annotated[
        list[TodoDraft],
        Field(
            default_factory=list,
            max_length=MAX_BATCH_ITEMS,
            description="Child to-dos for this heading.",
        ),
    ]


class ItemPatch(ClosedModel):
    """Closed set of supported Things item edits."""

    title: Annotated[
        str | None,
        Field(default=None, min_length=1, max_length=512, description="Replacement title."),
    ] = None
    notes: Annotated[
        str | None,
        Field(default=None, max_length=20_000, description="Replacement notes."),
    ] = None
    project_id: Annotated[
        Identifier | None,
        Field(default=None, alias="projectId", description="Replacement project ID."),
    ] = None
    heading_id: Annotated[
        Identifier | None,
        Field(default=None, alias="headingId", description="Replacement heading ID."),
    ] = None
    when: Annotated[
        str | None,
        Field(
            default=None,
            max_length=128,
            description="Replacement start value or ISO date.",
        ),
    ] = None
    deadline: Annotated[
        str | None,
        Field(default=None, max_length=128, description="Replacement ISO deadline."),
    ] = None
    reminder: Annotated[
        str | None,
        Field(default=None, max_length=128, description="Replacement ISO reminder."),
    ] = None
    status: Annotated[PublicItemStatus | None, Field(default=None, description="Replacement item status.")] = None
    tag_names: Annotated[
        list[ShortText] | None,
        Field(
            default=None,
            alias="tagNames",
            max_length=MAX_BATCH_ITEMS,
            description="Complete replacement tag-name set.",
        ),
    ] = None

    @model_validator(mode="after")
    def require_edit(self) -> ItemPatch:
        """Reject empty patches and unsupported heading-only destinations."""
        if not self.model_fields_set:
            raise ValueError("at least one edit field is required")
        if self.heading_id is not None and self.project_id is None:
            raise ValueError("headingId requires projectId")
        return self


class CreateTodoRequest(MutationRequest):
    """Create one typed to-do."""

    todo: TodoDraft


class CreateTodosRequest(MutationRequest):
    """Create a bounded collection of typed to-dos."""

    todos: Annotated[
        list[TodoDraft],
        Field(min_length=1, max_length=MAX_BATCH_ITEMS, description="One to 25 to-dos."),
    ]


class QuickEntryRequest(ClosedModel):
    """Open Things Quick Entry as a user-controlled handoff."""

    todo: QuickEntryDraft


class CreateHeadingRequest(MutationRequest):
    """Create one heading in an existing project."""

    project_id: Annotated[Identifier, Field(alias="projectId", description="Owning project ID.")]
    title: ShortText


class CreateProjectRequest(MutationRequest):
    """Create one typed project."""

    project: ProjectDraft


class CreateStructuredProjectRequest(MutationRequest):
    """Create a project with typed headings and a bounded to-do set."""

    project: ProjectDraft
    headings: Annotated[
        list[HeadingDraft],
        Field(max_length=MAX_BATCH_ITEMS, description="Zero to 25 typed headings."),
    ]
    unheaded_todos: Annotated[
        list[TodoDraft],
        Field(
            default_factory=list,
            alias="unheadedTodos",
            max_length=MAX_BATCH_ITEMS,
            description="Project to-dos outside headings.",
        ),
    ]

    @model_validator(mode="after")
    def validate_total_items(self) -> CreateStructuredProjectRequest:
        """Cap the project, headings, and all child to-dos together."""
        total = 1 + len(self.headings) + len(self.unheaded_todos) + sum(len(heading.todos) for heading in self.headings)
        if total > MAX_BATCH_ITEMS:
            raise ValueError(f"structured project may create at most {MAX_BATCH_ITEMS} objects")
        return self


class FindItemsRequest(ClosedModel):
    """Bounded native Things search criteria."""

    query: Annotated[
        str,
        Field(
            min_length=1,
            max_length=512,
            description="Literal Things search text; not a URL or query language.",
        ),
    ]
    kinds: Annotated[
        list[PublicItemKind],
        Field(
            default_factory=list,
            max_length=4,
            description="Optional item-kind filters.",
        ),
    ]
    statuses: Annotated[
        list[PublicItemStatus],
        Field(default_factory=list, max_length=3, description="Optional status filters."),
    ]
    limit: Annotated[
        int,
        Field(default=25, ge=1, le=MAX_BATCH_ITEMS, description="Maximum returned items."),
    ] = MAX_BATCH_ITEMS


class GetItemsRequest(ClosedModel):
    """Fetch a bounded explicit set of Things IDs."""

    item_ids: Annotated[
        list[Identifier],
        Field(
            alias="itemIds",
            min_length=1,
            max_length=MAX_BATCH_ITEMS,
            description="One to 25 IDs.",
        ),
    ]


class GetSelectedItemsRequest(ClosedModel):
    """Read the currently selected Things items."""

    limit: Annotated[
        int,
        Field(
            default=25,
            ge=1,
            le=MAX_BATCH_ITEMS,
            description="Maximum selected items returned.",
        ),
    ] = MAX_BATCH_ITEMS


def _require_unique_item_ids(item_ids: list[str]) -> list[str]:
    """Reject ambiguous plural mutation targets while preserving caller order."""
    if len(item_ids) != len(set(item_ids)):
        raise ValueError("itemIds must contain unique identifiers")
    return item_ids


UniqueMutationItemIds = Annotated[
    list[Identifier],
    AfterValidator(_require_unique_item_ids),
]


class EditItemsRequest(MutationRequest):
    """Apply one non-undoable patch to a bounded item set."""

    item_ids: Annotated[
        UniqueMutationItemIds,
        Field(
            alias="itemIds",
            min_length=1,
            max_length=MAX_BATCH_ITEMS,
            json_schema_extra={"uniqueItems": True},
            description="One to 25 target IDs.",
        ),
    ]
    patch: ItemPatch


class EditHeadingRequest(MutationRequest):
    """Rename one heading."""

    heading_id: Annotated[Identifier, Field(alias="headingId", description="Target heading ID.")]
    title: ShortText


class ChecklistMutationRequest(MutationRequest):
    """Replace, append, or prepend one bounded checklist."""

    item_id: Annotated[Identifier, Field(alias="itemId", description="Target to-do ID.")]
    entries: Annotated[
        list[ChecklistEntry],
        Field(max_length=MAX_BATCH_ITEMS, description="Zero to 25 checklist entries."),
    ]


class DuplicateItemsRequest(MutationRequest):
    """Duplicate a bounded item set."""

    item_ids: Annotated[
        UniqueMutationItemIds,
        Field(
            alias="itemIds",
            min_length=1,
            max_length=MAX_BATCH_ITEMS,
            json_schema_extra={"uniqueItems": True},
            description="One to 25 source IDs.",
        ),
    ]


class DeleteItemsRequest(MutationRequest):
    """Move or immediately delete a bounded item set."""

    item_ids: Annotated[
        UniqueMutationItemIds,
        Field(
            alias="itemIds",
            min_length=1,
            max_length=MAX_BATCH_ITEMS,
            json_schema_extra={"uniqueItems": True},
            description="One to 25 target IDs.",
        ),
    ]


class DeleteHeadingRequest(MutationRequest):
    """Delete one heading and account for its child cascade."""

    heading_id: Annotated[Identifier, Field(alias="headingId", description="Target heading ID.")]


class OpenListRequest(ClosedModel):
    """Open one fixed Things built-in list."""

    list: Annotated[PublicBuiltinList, Field(description="Fixed built-in list to open.")]


class ShowItemsRequest(ClosedModel):
    """Show a bounded explicit item set in Things."""

    item_ids: Annotated[
        list[Identifier],
        Field(
            alias="itemIds",
            min_length=1,
            max_length=MAX_BATCH_ITEMS,
            description="One to 25 IDs to show.",
        ),
    ]


class ThingItem(ClosedModel):
    """Typed item returned by a Shortcut bridge."""

    id: Identifier
    kind: PublicItemKind
    title: Annotated[str, Field(max_length=4096, description="Things item title.")]
    status: PublicItemStatus
    notes: Annotated[
        str | None,
        Field(default=None, max_length=20_000, description="Optional Things notes."),
    ] = None
    project_id: Annotated[
        Identifier | None,
        Field(
            default=None,
            alias="projectId",
            max_length=256,
            description="Optional parent project ID.",
        ),
    ] = None
    heading_id: Annotated[
        Identifier | None,
        Field(
            default=None,
            alias="headingId",
            max_length=256,
            description="Optional parent heading ID.",
        ),
    ] = None
    tag_names: Annotated[
        list[str],
        Field(
            default_factory=list,
            alias="tagNames",
            max_length=MAX_BATCH_ITEMS,
            description="Item tag names.",
        ),
    ]
    checklist: Annotated[
        list[ChecklistEntry],
        Field(
            default_factory=list,
            max_length=MAX_BATCH_ITEMS,
            description="Item checklist entries.",
        ),
    ]


class ItemReceipt(ClosedModel):
    """Per-item content-free mutation outcome."""

    item_id: Annotated[
        Identifier | None,
        Field(
            default=None,
            alias="itemId",
            max_length=256,
            description="Resulting or target item ID when known.",
        ),
    ] = None
    status: Annotated[
        Literal["changed", "skipped", "failed", "ambiguous"],
        Field(description="Per-item mutation outcome."),
    ]
    code: Annotated[
        str,
        Field(
            min_length=1,
            max_length=64,
            pattern=r"^[a-z0-9_-]+$",
            description="Content-free outcome code.",
        ),
    ]


class OperationResult(ClosedModel):
    """Closed result shared by typed Shortcut operations."""

    operation: PublicBridgeOperation
    status: Annotated[
        Literal[
            "previewed",
            "changed",
            "skipped",
            "failed",
            "ambiguous",
            "ui_handoff",
            "shown",
        ],
        Field(description="Overall operation state."),
    ]
    mutation_receipt: Annotated[
        str | None,
        Field(
            default=None,
            alias="mutationReceipt",
            max_length=128,
            description="Opaque execute receipt for preview results.",
        ),
    ] = None
    affected_count: Annotated[
        int,
        Field(
            default=0,
            alias="affectedCount",
            ge=0,
            le=MAX_BATCH_ITEMS,
            description="Items in operation scope.",
        ),
    ] = 0
    cascade_count: Annotated[
        int,
        Field(
            default=0,
            alias="cascadeCount",
            ge=0,
            le=100_000,
            description="Children affected by a destructive cascade.",
        ),
    ] = 0
    changed_count: Annotated[
        int,
        Field(
            default=0,
            alias="changedCount",
            ge=0,
            le=MAX_BATCH_ITEMS,
            description="Verified changed items.",
        ),
    ] = 0
    skipped_count: Annotated[
        int,
        Field(
            default=0,
            alias="skippedCount",
            ge=0,
            le=MAX_BATCH_ITEMS,
            description="Skipped items.",
        ),
    ] = 0
    failed_count: Annotated[
        int,
        Field(
            default=0,
            alias="failedCount",
            ge=0,
            le=MAX_BATCH_ITEMS,
            description="Failed items.",
        ),
    ] = 0
    ambiguous_count: Annotated[
        int,
        Field(
            default=0,
            alias="ambiguousCount",
            ge=0,
            le=MAX_BATCH_ITEMS,
            description="Items requiring manual verification.",
        ),
    ] = 0
    items: Annotated[
        list[ThingItem],
        Field(
            default_factory=list,
            max_length=MAX_BATCH_ITEMS,
            description="Typed read results.",
        ),
    ]
    receipts: Annotated[
        list[ItemReceipt],
        Field(
            default_factory=list,
            max_length=MAX_BATCH_ITEMS,
            description="Per-item mutation results.",
        ),
    ]
    readback_verified: Annotated[
        bool,
        Field(
            default=False,
            alias="readbackVerified",
            description="Whether post-mutation state was freshly verified.",
        ),
    ] = False
    ui_handoff: Annotated[
        bool,
        Field(
            default=False,
            alias="uiHandoff",
            description="Whether completion is handed to the user in Things UI.",
        ),
    ] = False
    undoable: Annotated[
        bool | None,
        Field(
            default=None,
            description="Whether Things provides an undo path for the operation.",
        ),
    ] = None
    message_code: Annotated[
        str,
        Field(
            alias="messageCode",
            min_length=1,
            max_length=64,
            pattern=r"^[a-z0-9_-]+$",
            description="Content-free result code.",
        ),
    ]


class BridgeOperationResult(OperationResult):
    """Internal bridge result with canonical target-state evidence.

    ``targetState`` is intentionally excluded from the public MCP result. Each
    entry is a deterministic, content-bearing state record produced by the
    fixed bridge; the server sorts the records and hashes the closed envelope
    before handing it to the shared receipt coordinator.
    """

    target_state: Annotated[
        list[BoundedText] | None,
        Field(
            default=None,
            alias="targetState",
            max_length=10_000,
            description="Deterministic target-state records used only for receipt binding.",
        ),
    ] = None
    cascade_observed: Annotated[
        bool | None,
        Field(
            default=None,
            alias="cascadeObserved",
            description="Whether cascadeCount was explicitly observed from target state.",
        ),
    ] = None


class BridgeHealth(ClosedModel):
    """Health for one fixed Shortcut bridge."""

    bridge: PublicBridgeIdentity
    present: bool
    protocol_match: Annotated[
        bool,
        Field(
            alias="protocolMatch",
            description="Whether protocol and both schema digests match.",
        ),
    ]
    tcc_ready: Annotated[
        bool,
        Field(
            alias="tccReady",
            description="Bridge-reported noninteractive Things authorization readiness.",
        ),
    ]
    code: Annotated[
        str,
        Field(
            min_length=1,
            max_length=64,
            pattern=r"^[a-z0-9_-]+$",
            description="Content-free health code.",
        ),
    ]


class ShortcutsHealthResult(ClosedModel):
    """Typed aggregate health without a Things action or TCC prompt."""

    status: Annotated[
        Literal["ready", "absent", "protocol_mismatch", "tcc_degraded"],
        Field(description="Aggregate fixed-bridge readiness."),
    ]
    protocol_version: Annotated[
        str,
        Field(
            alias="protocolVersion",
            description="Required Things++ bridge protocol version.",
        ),
    ]
    bridges: Annotated[
        list[BridgeHealth],
        Field(min_length=2, max_length=2, description="Health of both fixed bridges."),
    ]
    invokes_things: Annotated[
        Literal[False],
        Field(
            default=False,
            alias="invokesThings",
            description="Health never invokes a Things action.",
        ),
    ] = False
    message_code: Annotated[
        str,
        Field(
            alias="messageCode",
            min_length=1,
            max_length=64,
            pattern=r"^[a-z0-9_-]+$",
            description="Content-free aggregate health code.",
        ),
    ]
