"""Closed public response envelopes for the Things core adapter."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

NormalizedScalar = str | bool | int | float | None


class NormalizedPayloadEntry(BaseModel):
    """One deterministic JSON-pointer/value pair from an upstream result."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    path: str = Field(min_length=1, max_length=2_048, pattern=r"^[^\x00\x7f]+$")
    value: NormalizedScalar = Field(union_mode="left_to_right")


class NormalizedPayload(BaseModel):
    """Closed, bounded normalization shared by all audited operations."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, populate_by_name=True)

    source_kind: Literal["object", "array", "scalar", "null"] = Field(alias="sourceKind")
    entries: tuple[NormalizedPayloadEntry, ...] = Field(default=(), max_length=500)


class CoreToolResult(BaseModel):
    """One bounded, content-safe adapter response."""

    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)

    tool: str = Field(pattern=r"^[a-z0-9][a-z0-9_]{0,127}$")
    status: Literal["read", "previewed", "changed", "skipped", "failed", "ambiguous"]
    mutation_receipt: str | None = Field(default=None, alias="mutationReceipt", min_length=43, max_length=128)
    receipt_id: str | None = Field(default=None, alias="receiptId", pattern=r"^[0-9a-f]{16}$")
    target_count: int = Field(default=0, alias="targetCount", ge=0, le=25)
    changed_count: int = Field(default=0, alias="changedCount", ge=0, le=25)
    skipped_count: int = Field(default=0, alias="skippedCount", ge=0, le=25)
    failed_count: int = Field(default=0, alias="failedCount", ge=0, le=25)
    ambiguous_count: int = Field(default=0, alias="ambiguousCount", ge=0, le=25)
    readback_verified: bool = Field(default=False, alias="readbackVerified")
    truncated: bool = False
    payload: NormalizedPayload | None = None
    message_code: str = Field(default="things_core_ok", alias="messageCode", pattern=r"^[a-z0-9][a-z0-9_.-]{0,95}$")
