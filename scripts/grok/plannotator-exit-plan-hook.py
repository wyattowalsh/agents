#!/usr/bin/env python3
"""Grok PreToolUse wrapper for Plannotator plan review.

Grok Build sends camelCase hook JSON on stdin and keeps the plan on disk at
``~/.grok/sessions/<url-encoded-cwd>/<session-id>/plan.md``.

Plannotator's bare CLI (Claude PermissionRequest path) expects:
- stdin JSON with ``tool_input.plan`` (inline markdown)
- stdout decisions shaped as ``hookSpecificOutput.decision.behavior``

This shim:
1. Resolves plan content from the Grok event or session ``plan.md``
2. Feeds a Claude-shaped event to ``plannotator``
3. Maps Plannotator allow/deny/block responses to Grok native decisions
   (``{"decision": "allow"}`` / ``{"decision": "deny", "reason": "..."}``)

Fail-open contract (Grok PreToolUse):
- Empty / missing plan, binary missing, crash with empty stdout, unmapped or
  non-JSON plannotator output → allow (exit 0, no deny JSON).
- Only explicit mapped deny JSON blocks plan exit.
- Never use exit code 2; Grok treats exit 2 as explicit deny.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path
from typing import Any

# Grok session dirs observed as UUID only (8-4-4-4-12). Reject path-like ids.
_SAFE_SESSION_ID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def _plannotator_bin() -> str:
    return os.environ.get("PLANNOTATOR_BIN", os.path.expanduser("~/.local/bin/plannotator"))


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _tool_name(payload: dict[str, Any]) -> str:
    return str(
        payload.get("toolName")
        or payload.get("tool_name")
        or payload.get("tool")
        or ""
    ).strip()


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


def _safe_session_id(raw: str) -> str | None:
    """Return a filesystem-safe Grok session id, or None if unusable."""
    candidate = raw.strip()
    if not candidate:
        return None
    if _SAFE_SESSION_ID_RE.fullmatch(candidate) is None:
        return None
    return candidate


def _session_id(payload: dict[str, Any]) -> str:
    raw = str(
        payload.get("sessionId")
        or payload.get("session_id")
        or os.environ.get("GROK_SESSION_ID")
        or ""
    )
    return _safe_session_id(raw) or ""


def _workspace_cwd(payload: dict[str, Any]) -> str:
    return str(
        payload.get("cwd")
        or payload.get("workspaceRoot")
        or payload.get("workspace_root")
        or os.environ.get("GROK_WORKSPACE_ROOT")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or ""
    ).strip()


def _encode_session_cwd(cwd: str) -> str:
    """Match Grok's session directory slug (URL-encoded absolute path)."""
    try:
        resolved = str(Path(cwd).expanduser().resolve())
    except OSError:
        resolved = cwd
    return urllib.parse.quote(resolved, safe="")


def _sessions_root() -> Path:
    override = os.environ.get("GROK_SESSIONS_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".grok" / "sessions"


def _read_text(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    text = text.strip()
    return text or None


def _find_plan_path(payload: dict[str, Any]) -> Path | None:
    """Locate Grok session plan.md from session id and/or workspace cwd.

    Isolation rules:
    - Prefer exact ``<encoded-cwd>/<session-id>/plan.md``
    - Then any cwd slug with that session id (same session, path drift)
    - Then newest plan under the **same** encoded cwd only
    - Never fall back to newest plan across all projects (cross-session leak)
    """
    sessions = _sessions_root()
    if not sessions.is_dir():
        return None

    session_id = _session_id(payload)
    cwd = _workspace_cwd(payload)

    if session_id and cwd:
        candidate = sessions / _encode_session_cwd(cwd) / session_id / "plan.md"
        if candidate.is_file():
            return candidate

    if session_id:
        matches = sorted(sessions.glob(f"*/{session_id}/plan.md"))
        if matches:
            return matches[0]

    if cwd:
        slug_dir = sessions / _encode_session_cwd(cwd)
        if slug_dir.is_dir():
            plans = sorted(
                (path for path in slug_dir.glob("*/plan.md") if path.is_file()),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
            if plans:
                return plans[0]

    return None


def _resolve_plan_content(payload: dict[str, Any]) -> str:
    tool_input = _tool_input(payload)
    inline = tool_input.get("plan")
    if isinstance(inline, str) and inline.strip():
        return inline

    # Gemini-style absolute plan path if a harness ever sends it through Grok.
    for key in ("plan_path", "planPath", "plan_filename", "planFilename"):
        value = tool_input.get(key)
        if not isinstance(value, str) or not value.strip():
            continue
        path = Path(value).expanduser()
        if path.is_file():
            content = _read_text(path)
            if content:
                return content

    plan_path = _find_plan_path(payload)
    if plan_path is not None:
        content = _read_text(plan_path)
        if content:
            return content
    return ""


def _is_exit_plan_tool(name: str) -> bool:
    normalized = name.strip().lower().replace("-", "_")
    return normalized in {"exit_plan_mode", "exitplanmode"}


def _build_plannotator_event(payload: dict[str, Any], plan_content: str) -> dict[str, Any]:
    """Claude PermissionRequest-shaped event that bare `plannotator` understands."""
    tool_input = dict(_tool_input(payload))
    tool_input["plan"] = plan_content
    event: dict[str, Any] = {
        "hook_event_name": "PermissionRequest",
        "tool_name": "ExitPlanMode",
        "tool_input": tool_input,
        "permission_mode": payload.get("permission_mode")
        or payload.get("permissionMode")
        or "default",
    }
    session_id = _session_id(payload)
    if session_id:
        event["session_id"] = session_id
    cwd = _workspace_cwd(payload)
    if cwd:
        event["cwd"] = cwd
    return event


def _map_to_grok(payload: Any) -> dict[str, Any] | None:
    """Map Plannotator/Claude/Codex/Gemini/Copilot hook JSON to Grok decisions.

    Returns:
      - ``{"decision": "deny", "reason": "..."}`` to block
      - ``{"decision": "allow"}`` to allow explicitly
      - ``None`` when the payload is empty/unknown (caller must fail-open allow)
    """
    if not isinstance(payload, dict):
        return None

    # Claude PermissionRequest: hookSpecificOutput.decision.behavior
    hook_specific = payload.get("hookSpecificOutput")
    if isinstance(hook_specific, dict):
        nested = hook_specific.get("decision")
        if isinstance(nested, dict):
            behavior = str(nested.get("behavior") or "").lower()
            if behavior == "deny":
                reason = (
                    nested.get("message")
                    or nested.get("reason")
                    or payload.get("reason")
                    or "Plan changes requested"
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

    # Claude/Codex annotate --hook / Gemini deny: top-level decision
    decision = payload.get("decision")
    if decision in {"block", "deny"}:
        reason = payload.get("reason") or payload.get("message") or "Plan changes requested"
        return {"decision": "deny", "reason": str(reason)}
    if decision == "allow":
        return {"decision": "allow"}

    # Copilot CLI: permissionDecision
    permission_decision = str(payload.get("permissionDecision") or "").lower()
    if permission_decision == "deny":
        reason = (
            payload.get("permissionDecisionReason")
            or payload.get("reason")
            or "Plan changes requested"
        )
        return {"decision": "deny", "reason": str(reason)}
    if permission_decision == "allow":
        return {"decision": "allow"}

    return None


def _emit_json(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")


def _log_stderr(message: str) -> None:
    print(message, file=sys.stderr)


def _allow() -> int:
    """Fail-open allow: empty stdout, exit 0 (never exit 2)."""
    return 0


def main() -> int:
    plannotator = _plannotator_bin()
    if not os.access(plannotator, os.X_OK):
        _log_stderr(f"plannotator binary not found at {plannotator}")
        return _allow()

    raw_stdin = sys.stdin.read()
    if not raw_stdin.strip():
        return _allow()

    try:
        grok_payload = json.loads(raw_stdin)
    except json.JSONDecodeError:
        # Unexpected non-JSON stdin: do not invent a plan review; fail-open.
        _log_stderr("plannotator-exit-plan-hook: non-JSON stdin; allowing")
        return _allow()

    if not isinstance(grok_payload, dict):
        return _allow()

    tool_name = _tool_name(grok_payload)
    # Only gate exit_plan_mode; other PreToolUse matches should never reach here
    # (matcher filters), but fail-open if they do.
    if tool_name and not _is_exit_plan_tool(tool_name):
        return _allow()

    # Surface ignored unsafe session ids for debugging without blocking.
    raw_session = str(
        grok_payload.get("sessionId")
        or grok_payload.get("session_id")
        or os.environ.get("GROK_SESSION_ID")
        or ""
    ).strip()
    if raw_session and _safe_session_id(raw_session) is None:
        _log_stderr(
            f"plannotator-exit-plan-hook: ignoring unsafe session id {raw_session!r}"
        )

    plan_content = _resolve_plan_content(grok_payload)
    if not plan_content:
        _log_stderr(
            "plannotator-exit-plan-hook: no plan content in tool input or session plan.md; allowing"
        )
        return _allow()

    claude_event = _build_plannotator_event(grok_payload, plan_content)
    result = subprocess.run(
        [plannotator],
        input=json.dumps(claude_event),
        capture_output=True,
        text=True,
        check=False,
    )

    if result.stderr:
        sys.stderr.write(result.stderr)

    output = (result.stdout or "").strip()
    if not output:
        # Empty stdout = allow (annotate --hook protocol). Always exit 0 even if
        # plannotator crashed: Grok treats exit 2 as explicit deny.
        if result.returncode != 0:
            _log_stderr(
                f"plannotator-exit-plan-hook: plannotator exit {result.returncode} "
                "with empty stdout; allowing"
            )
        return _allow()

    try:
        plannotator_payload = json.loads(output)
    except json.JSONDecodeError:
        snippet = output[:200].replace("\n", " ")
        _log_stderr(
            f"plannotator-exit-plan-hook: non-JSON plannotator stdout ({snippet!r}); allowing"
        )
        return _allow()

    mapped = _map_to_grok(plannotator_payload)
    if mapped is None:
        _log_stderr(
            "plannotator-exit-plan-hook: unmapped plannotator decision shape; allowing"
        )
        return _allow()

    if mapped.get("decision") == "allow":
        _emit_json({"decision": "allow"})
        return 0

    _emit_json(mapped)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
