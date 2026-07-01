"""Grok-build deny adapter.

Grok Build consumes JSON hook output. Unlike Cursor (``permission``) or Codex
(``decision``/``permissionDecision``), the Grok fleet projection expects a deny
to be expressed as a ``decision: "block"`` object with a human-readable reason.
This helper centralizes that shape so the dispatcher and the Grok fleet renderer
agree on it.
"""

from __future__ import annotations

from typing import Any


def grok_deny_payload(reason: str, *, policy_id: str = "grok-deny-adapter") -> dict[str, Any]:
    """Return the Grok-build deny payload for ``reason``."""
    reason = reason.strip() or "Blocked by repo-managed policy."
    return {
        "decision": "block",
        "reason": reason,
        "hookSpecificOutput": {
            "hookEventName": "preToolUse",
            "policyId": policy_id,
            "permission": "deny",
        },
    }
