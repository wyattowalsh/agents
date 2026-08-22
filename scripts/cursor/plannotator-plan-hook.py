#!/usr/bin/env python3
"""Cursor preToolUse wrapper for Plannotator plan review (IDE + CLI).

Cursor Agent sends camelCase or snake_case hook JSON on stdin. Plan mode uses
``CreatePlan`` (body in ``plan`` / ``overview``) and ``SwitchMode``
(``target_mode_id``: ``plan`` | ``agent``).

This shim:

1. ``enter`` — run ``plannotator improve-context`` only for ``SwitchMode`` when
   the target mode is ``plan``
2. ``exit`` — feed a Claude-shaped ``PermissionRequest`` / ``ExitPlanMode``
   event with inline ``tool_input.plan`` to ``plannotator``
3. Map allow/deny/block responses to Cursor
   ``{"permission": "allow"|"deny", "agent_message": "..."}``

Fail-open contract (Cursor preToolUse):

- Missing binary, empty plan, crash with empty stdout, unmapped or non-JSON
  plannotator output → allow (exit 0, empty stdout).
- Only explicit mapped deny JSON blocks CreatePlan.
- Never use exit code 2; Cursor treats exit 2 as explicit deny.
- Never scan other projects' ``plan.md`` files.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any

ENTER_TIMEOUT_SECONDS = 5


def _plannotator_bin() -> str:
    return os.environ.get("PLANNOTATOR_BIN", os.path.expanduser("~/.local/bin/plannotator"))


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _tool_name(payload: dict[str, Any]) -> str:
    return str(payload.get("toolName") or payload.get("tool_name") or payload.get("tool") or "").strip()


def _tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("toolInput")
    if raw is None:
        raw = payload.get("tool_input")
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return _as_dict(raw)


def _normalize_tool(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _is_create_plan_tool(name: str) -> bool:
    return _normalize_tool(name) in {"createplan", "create_plan"}


def _is_switch_mode_tool(name: str) -> bool:
    return _normalize_tool(name) in {"switchmode", "switch_mode"}


def _target_mode_id(tool_input: dict[str, Any]) -> str:
    for key in ("target_mode_id", "targetModeId", "target_mode", "targetMode", "mode"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return ""


def _resolve_plan_content(payload: dict[str, Any]) -> str:
    """Return inline plan markdown from CreatePlan input.

    Isolation: only ``plan`` then ``overview`` on this event. Do not read
    ``plan.md`` from disk or other projects.
    """
    tool_input = _tool_input(payload)
    for key in ("plan", "overview"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _build_plannotator_event(payload: dict[str, Any], plan_content: str) -> dict[str, Any]:
    """Claude PermissionRequest-shaped event that bare ``plannotator`` understands."""
    tool_input = dict(_tool_input(payload))
    tool_input["plan"] = plan_content
    event: dict[str, Any] = {
        "hook_event_name": "PermissionRequest",
        "tool_name": "ExitPlanMode",
        "tool_input": tool_input,
        "permission_mode": payload.get("permission_mode") or payload.get("permissionMode") or "default",
    }
    session_id = str(payload.get("sessionId") or payload.get("session_id") or "").strip()
    if session_id:
        event["session_id"] = session_id
    cwd = str(
        payload.get("cwd")
        or payload.get("workspaceRoot")
        or payload.get("workspace_root")
        or os.environ.get("CURSOR_PROJECT_DIR")
        or ""
    ).strip()
    if cwd:
        event["cwd"] = cwd
    return event


def _map_decision(payload: Any) -> dict[str, Any] | None:
    """Map Plannotator/Claude/Codex/Gemini/Copilot hook JSON to allow/deny.

    Returns:
      - ``{"decision": "deny", "reason": "..."}`` to block
      - ``{"decision": "allow"}`` to allow explicitly
      - ``None`` when the payload is empty/unknown (caller must fail-open allow)
    """
    if not isinstance(payload, dict):
        return None

    hook_specific = payload.get("hookSpecificOutput")
    if isinstance(hook_specific, dict):
        nested = hook_specific.get("decision")
        if isinstance(nested, dict):
            behavior = str(nested.get("behavior") or "").lower()
            if behavior == "deny":
                reason = (
                    nested.get("message") or nested.get("reason") or payload.get("reason") or "Plan changes requested"
                )
                return {"decision": "deny", "reason": str(reason)}
            if behavior == "allow":
                return {"decision": "allow"}
        permission = str(hook_specific.get("permission") or "").lower()
        if permission == "deny":
            reason = (
                hook_specific.get("permissionDecisionReason")
                or hook_specific.get("reason")
                or payload.get("reason")
                or "Blocked by Plannotator"
            )
            return {"decision": "deny", "reason": str(reason)}
        if permission == "allow":
            return {"decision": "allow"}

    decision = payload.get("decision")
    if decision in {"block", "deny"}:
        reason = payload.get("reason") or payload.get("message") or "Plan changes requested"
        return {"decision": "deny", "reason": str(reason)}
    if decision == "allow":
        return {"decision": "allow"}

    permission_decision = str(payload.get("permissionDecision") or payload.get("permission") or "").lower()
    if permission_decision == "deny":
        reason = payload.get("permissionDecisionReason") or payload.get("reason") or "Plan changes requested"
        return {"decision": "deny", "reason": str(reason)}
    if permission_decision == "allow":
        return {"decision": "allow"}

    return None


def _cursor_output(mapped: dict[str, Any]) -> dict[str, Any]:
    if mapped.get("decision") == "allow":
        return {"permission": "allow"}
    reason = str(mapped.get("reason") or "Plan changes requested")
    return {
        "permission": "deny",
        "agent_message": reason,
        "user_message": reason,
    }


def _emit_json(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")


def _log_stderr(message: str) -> None:
    print(message, file=sys.stderr)


def _allow() -> int:
    """Fail-open allow: empty stdout, exit 0 (never exit 2)."""
    return 0


def _read_payload() -> dict[str, Any] | None:
    raw_stdin = sys.stdin.read()
    if not raw_stdin.strip():
        return None
    try:
        payload = json.loads(raw_stdin)
    except json.JSONDecodeError:
        _log_stderr("plannotator-plan-hook: non-JSON stdin; allowing")
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _handle_enter(payload: dict[str, Any]) -> int:
    tool_name = _tool_name(payload)
    if tool_name and not _is_switch_mode_tool(tool_name):
        return _allow()
    if _target_mode_id(_tool_input(payload)) != "plan":
        return _allow()

    plannotator = _plannotator_bin()
    if not os.access(plannotator, os.X_OK):
        _log_stderr(f"plannotator binary not found at {plannotator}")
        return _allow()

    try:
        result = subprocess.run(
            [plannotator, "improve-context"],
            capture_output=True,
            text=True,
            check=False,
            timeout=ENTER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        _log_stderr("plannotator-plan-hook: improve-context timed out; allowing")
        return _allow()
    except OSError as exc:
        _log_stderr(f"plannotator-plan-hook: improve-context failed ({exc}); allowing")
        return _allow()

    if result.stderr:
        sys.stderr.write(result.stderr)
    if result.returncode != 0:
        _log_stderr(f"plannotator-plan-hook: improve-context exit {result.returncode}; allowing")
    return _allow()


def _handle_exit(payload: dict[str, Any]) -> int:
    tool_name = _tool_name(payload)
    if tool_name and not _is_create_plan_tool(tool_name):
        return _allow()

    plannotator = _plannotator_bin()
    if not os.access(plannotator, os.X_OK):
        _log_stderr(f"plannotator binary not found at {plannotator}")
        return _allow()

    plan_content = _resolve_plan_content(payload)
    if not plan_content:
        _log_stderr("plannotator-plan-hook: no plan or overview in CreatePlan input; allowing")
        return _allow()

    claude_event = _build_plannotator_event(payload, plan_content)
    try:
        result = subprocess.run(
            [plannotator],
            input=json.dumps(claude_event),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        _log_stderr(f"plannotator-plan-hook: plannotator failed ({exc}); allowing")
        return _allow()

    if result.stderr:
        sys.stderr.write(result.stderr)

    output = (result.stdout or "").strip()
    if not output:
        if result.returncode != 0:
            _log_stderr(f"plannotator-plan-hook: plannotator exit {result.returncode} with empty stdout; allowing")
        return _allow()

    try:
        plannotator_payload = json.loads(output)
    except json.JSONDecodeError:
        snippet = output[:200].replace("\n", " ")
        _log_stderr(f"plannotator-plan-hook: non-JSON plannotator stdout ({snippet!r}); allowing")
        return _allow()

    mapped = _map_decision(plannotator_payload)
    if mapped is None:
        _log_stderr("plannotator-plan-hook: unmapped plannotator decision shape; allowing")
        return _allow()

    _emit_json(_cursor_output(mapped))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    mode = args[0].strip().lower() if args else ""
    if mode not in {"enter", "exit"}:
        _log_stderr(f"plannotator-plan-hook: expected enter|exit, got {mode!r}; allowing")
        return _allow()

    payload = _read_payload()
    if payload is None:
        return _allow()

    if mode == "enter":
        return _handle_enter(payload)
    return _handle_exit(payload)


if __name__ == "__main__":
    raise SystemExit(main())
