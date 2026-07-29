"""Frozen acceptance fixtures for Cursor pin Phase A / Phase B (RV-S-009 / RV-S-010).

Contracts:
- Phase A omit → emit High via ``updated_input``
- Phase A modelId-only → emit High; alts cleared
- Phase A High+alt → emit High; alts cleared (A-4b)
- Phase A High-noop → no emit (``changed=False``)
- Phase B modelId deny → explicit non-High ``modelId`` denies
- Phase B omit → allow (inherit High parent)
"""

from __future__ import annotations

from typing import Any

from wagents.hooks.policies.cursor_task_model_pin import CURSOR_PINNED_MODEL

# --- Phase A (preToolUse / Task rewrite) ---

PHASE_A_OMIT: dict[str, Any] = {
    "description": "Investigate pin",
    "prompt": "go",
}

PHASE_A_MODEL_ID_ONLY: dict[str, Any] = {
    "description": "Investigate pin",
    "prompt": "go",
    "modelId": "cursor-grok-4.5-fast",
}

PHASE_A_MODEL_NAME_ONLY: dict[str, Any] = {
    "description": "Investigate pin",
    "prompt": "go",
    "model_name": "composer-1",
}

PHASE_A_HIGH_PLUS_ALT: dict[str, Any] = {
    "description": "Investigate pin",
    "prompt": "go",
    "model": CURSOR_PINNED_MODEL,
    "modelId": "cursor-grok-4.5-fast",
}

PHASE_A_HIGH_PLUS_MODEL_NAME: dict[str, Any] = {
    "description": "Investigate pin",
    "prompt": "go",
    "model": CURSOR_PINNED_MODEL,
    "model_name": "composer-2.5",
}

PHASE_A_HIGH_NOOP: dict[str, Any] = {
    "description": "Investigate pin",
    "prompt": "go",
    "model": CURSOR_PINNED_MODEL,
}

PHASE_A_WRONG_MODEL: dict[str, Any] = {
    "description": "Investigate pin",
    "prompt": "go",
    "model": "cursor-grok-4.5-fast",
}

# --- Phase B (subagentStart allowlist) ---

PHASE_B_OMIT_ALLOW: dict[str, Any] = {
    "description": "Investigate pin",
}

PHASE_B_MODEL_ID_DENY: dict[str, Any] = {
    "description": "Investigate pin",
    "modelId": "composer-1",
}

PHASE_B_HIGH_ALLOW: dict[str, Any] = {
    "description": "Investigate pin",
    "model": CURSOR_PINNED_MODEL,
}

PHASE_B_WRONG_MODEL_DENY: dict[str, Any] = {
    "description": "Investigate pin",
    "model": "cursor-grok-4.5-fast",
}
