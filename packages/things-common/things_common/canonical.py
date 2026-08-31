"""Canonical encodings used by schema, argument, state, and artifact receipts."""

from __future__ import annotations

import hashlib
import json
import math
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def _json_ready(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _json_ready(value.model_dump(mode="json", by_alias=True, exclude_none=False))
    if isinstance(value, Enum):
        return _json_ready(value.value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("Canonical JSON objects require string keys.")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Canonical JSON rejects non-finite numbers.")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"Unsupported canonical JSON value: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    """Encode *value* as compact, sorted-key UTF-8 JSON."""
    return json.dumps(
        _json_ready(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Return the SHA-256 digest of the canonical JSON encoding."""
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def canonical_schema_sha256(schema: dict[str, Any]) -> str:
    """Hash a JSON Schema using the frozen Things++ canonical encoding."""
    return canonical_sha256(schema)
