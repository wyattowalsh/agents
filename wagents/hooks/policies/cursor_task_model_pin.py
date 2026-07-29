"""Pin Cursor Task / subagent launches to ``cursor-grok-4.5-high``.

Phase A (``preToolUse`` / Task): rewrite ``model`` via ``updated_input`` (fail-open).
Phase B (``subagentStart``): deny when an explicit model is outside the allowlist.
"""

from __future__ import annotations

from typing import Any

CURSOR_PINNED_MODEL = "cursor-grok-4.5-high"
CURSOR_MODEL_ALLOWLIST = frozenset({CURSOR_PINNED_MODEL})

_TASK_TOOL_NAMES = frozenset({"task"})
_TOOL_INPUT_MODEL_ALT_KEYS = ("modelId", "model_name")


def _normalize_tool_name(tool_name: str) -> str:
    return tool_name.strip().lower()


def is_task_tool(tool_name: str) -> bool:
    return _normalize_tool_name(tool_name) in _TASK_TOOL_NAMES


def extract_model(tool_input: dict[str, Any] | None, raw: dict[str, Any] | None = None) -> str | None:
    """Return an explicit model string from tool input or raw hook payload, if any."""
    candidates: list[Any] = []
    if isinstance(tool_input, dict):
        candidates.extend(
            [
                tool_input.get("model"),
                tool_input.get("modelId"),
                tool_input.get("model_name"),
            ]
        )
    if isinstance(raw, dict):
        candidates.extend(
            [
                raw.get("model"),
                raw.get("modelId"),
                raw.get("model_name"),
                raw.get("subagent_model"),
            ]
        )
        nested = raw.get("subagent")
        if isinstance(nested, dict):
            candidates.extend([nested.get("model"), nested.get("modelId")])
        model_config = raw.get("modelConfig")
        if isinstance(model_config, dict):
            candidates.append(model_config.get("modelName"))
    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def rewrite_task_input(tool_input: dict[str, Any] | None) -> tuple[dict[str, Any], bool, str]:
    """Return updated Task input, whether it changed, and a short reason.

    Clears alternate keys (``modelId``, ``model_name``), sets canonical ``model``,
    and reports ``changed=True`` whenever alts were cleared (RV-S-009).
    No-op only when already High and no alts were present.
    """
    updated = dict(tool_input or {})
    prior = extract_model(updated, None)

    alts_cleared = False
    for key in _TOOL_INPUT_MODEL_ALT_KEYS:
        if key in updated:
            del updated[key]
            alts_cleared = True

    if prior == CURSOR_PINNED_MODEL and not alts_cleared:
        return updated, False, f"Task model already pinned to {CURSOR_PINNED_MODEL}"

    updated["model"] = CURSOR_PINNED_MODEL
    if alts_cleared and prior == CURSOR_PINNED_MODEL:
        reason = f"Cleared alternate model keys; kept pin {CURSOR_PINNED_MODEL}"
    elif prior is None:
        reason = f"Pinned omitted Task model to {CURSOR_PINNED_MODEL}"
    else:
        reason = f"Rewrote Task model {prior!r} -> {CURSOR_PINNED_MODEL}"
    return updated, True, reason


def evaluate_subagent_model_allowlist(
    tool_input: dict[str, Any] | None,
    raw: dict[str, Any] | None = None,
) -> str | None:
    """Return a deny reason when an explicit model is outside the allowlist."""
    model = extract_model(tool_input, raw)
    if model is None:
        # Inherit / frontmatter / parent-default paths stay open; Phase A Task rewrite
        # is responsible for forcing an explicit high pin on Task launches.
        return None
    if model in CURSOR_MODEL_ALLOWLIST:
        return None
    return (
        f"Subagent model {model!r} is not allowed. "
        f"Use model: {CURSOR_PINNED_MODEL} (or omit model to inherit a High parent)."
    )
