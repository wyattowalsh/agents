"""Fail-closed redaction and content-free event helpers."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

_TOKEN = re.compile(
    r"(?i)(?:api[-_]?key|auth[-_]?token|access[-_]?token|refresh[-_]?token|"
    r"bearer[-_]?token|client[-_]?secret|password|bearer|token)"
    r"(?:\s+|\s*[=:]\s*)[^\s&,;]+"
)
_THINGS_URL = re.compile(r"(?i)things://[^\s\]\[\"'<>]*")
_FILE_URL = re.compile(r"(?i)file://[^\s\]\[\"'<>]*")
_LOCAL_PATH = re.compile(r"(?:(?:/Users|/Library|/private|/var/folders|/tmp)/[^\s\]\[\"'<>]*)")
_TILDE_PATH = re.compile(r"(?<![A-Za-z0-9_])~/[^\s\]\[\"'<>]*")
_RELATIVE_AUTH_PATH = re.compile(r"(?i)(?<![A-Za-z0-9_.-])(?:\.things-auth|things-auth\.txt)(?![A-Za-z0-9_.-])")
_PRIVATE_KEYS = frozenset({
    "title",
    "name",
    "notes",
    "note",
    "checklist",
    "checklist_items",
    "items",
    "todo",
    "todos",
    "project",
    "projects",
    "area",
    "areas",
    "tag",
    "tags",
    "query",
    "search",
    "content",
    "text",
    "url",
    "path",
    "arguments",
    "environment",
    "process_args",
})
_SECRET_KEYS = frozenset({
    "token",
    "authtoken",
    "accesstoken",
    "refreshtoken",
    "bearertoken",
    "authorization",
    "secret",
    "clientsecret",
    "apikey",
    "password",
    "receipt",
    "mutationreceipt",
    "credential",
    "credentials",
})


def _normalized_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def redact_text(value: str) -> str:
    """Remove token, Things URL, file URL, and local-path material."""
    redacted = _TOKEN.sub("<redacted:token>", value)
    redacted = _THINGS_URL.sub("<redacted:things-url>", redacted)
    redacted = _FILE_URL.sub("<redacted:file-url>", redacted)
    redacted = _LOCAL_PATH.sub("<redacted:local-path>", redacted)
    redacted = _TILDE_PATH.sub("<redacted:local-path>", redacted)
    return _RELATIVE_AUTH_PATH.sub("<redacted:auth-path>", redacted)


def redact_value(value: Any, *, private_keys: frozenset[str] = _PRIVATE_KEYS) -> Any:
    """Recursively redact private fields while preserving safe result shape."""
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        normalized_private_keys = {_normalized_key(item) for item in private_keys}
        for raw_key, item in value.items():
            key = str(raw_key)
            normalized = _normalized_key(key)
            if normalized in _SECRET_KEYS:
                result[key] = "<redacted:secret>"
            elif normalized in normalized_private_keys:
                result[key] = "<redacted:private-content>"
            else:
                result[key] = redact_value(item, private_keys=private_keys)
        return result
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact_value(item, private_keys=private_keys) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return f"<redacted:{type(value).__name__.casefold()}>"


def content_free_event(
    event: str, /, **metrics: bool | int | float | None
) -> dict[str, bool | int | float | str | None]:
    """Build a log-safe event containing only a code and scalar metrics."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,95}", event):
        raise ValueError("Event codes must be short lowercase identifiers.")
    if any(isinstance(value, str) for value in metrics.values()):
        raise TypeError("Content-free event metrics cannot contain strings.")
    return {"event": event, **metrics}
