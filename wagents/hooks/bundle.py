"""Bundle dispatch: run several registry policy ids in one process.

This module is loaded two ways:

1. By ``hooks/wagents-hook.py`` via ``importlib.util.spec_from_file_location``
   (the dispatcher deliberately avoids importing the installed ``wagents``
   package so it keeps working under a bare trusted system ``python3``; see
   the module docstring in that file). For that reason this file stays
   stdlib-only and never imports another ``wagents.*`` submodule.
2. As a normal package import (``from wagents.hooks.bundle import
   run_bundle``) from tests and other in-repo tooling.

``run_bundle`` intercepts the dispatcher's single stdout chokepoint
(``_emit_json``) so a chain of N policy functions produces exactly one
harness-shaped stdout payload for the whole bundle instead of N, while still
recording every policy's real audit-ledger decision via ``_record_decision``.
See ``openspec/changes/fleet-hooks-performance/design.md`` ("Bundle contract
(G2)") for the full behavioral contract this implements.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Protocol, cast

BUNDLE_MODES: tuple[str, ...] = ("enforce-chain", "context-chain", "mixed")
DEFAULT_BUNDLE_TIMEOUT_SECONDS = 30.0
# Small safety margin subtracted from the remaining budget before starting the
# next policy so a policy that starts just under budget cannot itself run
# unbounded past the harness's own outer process timeout.
_BUDGET_SAFETY_MARGIN_SECONDS = 0.05
_IMPLICIT_ALLOW_LEDGER_EXCLUDED_POLICY_IDS = frozenset({"research-evidence-ledger"})


class Dispatcher(Protocol):
    """Structural type for the ``hooks/wagents-hook.py`` module surface bundle.py depends on."""

    POLICIES: dict[str, Any]
    ENFORCE_POLICY_IDS: Any
    CURSOR_FAIL_CLOSED_ALLOW_POLICIES: Any
    _STDOUT_EMITTED: bool

    def _emit_json(self, data: dict[str, Any]) -> int: ...
    def _record_decision(self, payload: Any, policy_id: str, decision: str, reason: str = "") -> int: ...
    def _deny(self, payload: Any, reason: str, policy_id: str = "policy-deny") -> int: ...
    def _additional_context(self, payload: Any, message: str, policy_id: str = "...") -> int: ...


@dataclass
class _Captured:
    code: int = 0
    emitted: dict[str, Any] | None = None
    decision: str | None = None
    reason: str = ""
    ran: bool = False


@dataclass
class BundleResult:
    code: int
    decisions: list[tuple[str, str]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def _run_one_captured(dispatcher: Dispatcher, policy_id: str, payload: Any) -> _Captured:
    """Run one policy function, capturing its emitted payload instead of printing it.

    The real ``_record_decision`` still runs (audit ledger + ``decision_recorded``
    flag stay authentic); only ``_emit_json`` is diverted so the caller can decide
    whether this policy's output becomes the bundle's single winning payload.
    """
    policy_fn = dispatcher.POLICIES.get(policy_id)
    if policy_fn is None:
        return _Captured(code=0, ran=False)

    captured = _Captured(ran=True)
    dispatcher_any = cast("Any", dispatcher)
    original_emit_json = dispatcher_any._emit_json
    original_record_decision = dispatcher_any._record_decision

    def _fake_emit_json(data: dict[str, Any]) -> int:
        captured.emitted = data
        return 0

    def _fake_record_decision(pl: Any, pid: str, decision: str, reason: str = "") -> int:
        captured.decision = decision
        captured.reason = reason
        return original_record_decision(pl, pid, decision, reason)

    dispatcher_any._emit_json = _fake_emit_json
    dispatcher_any._record_decision = _fake_record_decision
    try:
        captured.code = policy_fn(payload)
    finally:
        dispatcher_any._emit_json = original_emit_json
        dispatcher_any._record_decision = original_record_decision
    return captured


def _extract_context_message(data: dict[str, Any] | None) -> str | None:
    if not isinstance(data, dict):
        return None
    if isinstance(data.get("additional_context"), str):
        return data["additional_context"]
    hook_specific = data.get("hookSpecificOutput")
    if isinstance(hook_specific, dict) and isinstance(hook_specific.get("additionalContext"), str):
        return hook_specific["additionalContext"]
    return None


def _fail_closed_timeout_skip(dispatcher: Dispatcher, payload: Any, policy_id: str) -> int:
    reason = (
        f"Bundle timeout budget exhausted before '{policy_id}' could run; "
        "blocking as fail-closed enforce tier."
    )
    dispatcher._record_decision(payload, policy_id, "bundle-timeout-skip", reason)
    return dispatcher._deny(payload, reason, policy_id)


def _record_implicit_allow_if_needed(
    dispatcher: Dispatcher,
    payload: Any,
    policy_id: str,
    captured: _Captured,
) -> None:
    if (
        captured.ran
        and captured.code == 0
        and captured.decision is None
        and policy_id not in _IMPLICIT_ALLOW_LEDGER_EXCLUDED_POLICY_IDS
    ):
        try:
            dispatcher._record_decision(payload, policy_id, "allow")
        except AttributeError:
            if hasattr(payload, "decision_recorded"):
                raise
        else:
            captured.decision = "allow"


def _run_enforce_chain(
    dispatcher: Dispatcher,
    policy_ids: list[str],
    payload: Any,
    *,
    deadline: float,
    result: BundleResult,
) -> tuple[bool, int]:
    """Run an enforce-tier chain. Returns ``(denied, code)``; ``denied`` short-circuits mixed mode."""
    for policy_id in policy_ids:
        if time.monotonic() >= deadline - _BUDGET_SAFETY_MARGIN_SECONDS:
            result.skipped.append(policy_id)
            if policy_id in dispatcher.ENFORCE_POLICY_IDS:
                return True, _fail_closed_timeout_skip(dispatcher, payload, policy_id)
            dispatcher._record_decision(payload, policy_id, "bundle-timeout-skip", "Bundle timeout budget exhausted.")
            continue
        captured = _run_one_captured(dispatcher, policy_id, payload)
        if not captured.ran:
            continue
        _record_implicit_allow_if_needed(dispatcher, payload, policy_id, captured)
        result.decisions.append((policy_id, captured.decision or "allow"))
        if captured.decision == "deny":
            if captured.emitted is not None:
                dispatcher._emit_json(captured.emitted)
            return True, captured.code
    return False, 0


def _run_context_chain(
    dispatcher: Dispatcher,
    policy_ids: list[str],
    payload: Any,
    *,
    deadline: float,
    result: BundleResult,
) -> int:
    messages: list[str] = []
    last_policy_id = policy_ids[-1] if policy_ids else "bundle-context-chain"
    for policy_id in policy_ids:
        if time.monotonic() >= deadline - _BUDGET_SAFETY_MARGIN_SECONDS:
            result.skipped.append(policy_id)
            dispatcher._record_decision(payload, policy_id, "bundle-timeout-skip", "Bundle timeout budget exhausted.")
            continue
        captured = _run_one_captured(dispatcher, policy_id, payload)
        if not captured.ran:
            continue
        _record_implicit_allow_if_needed(dispatcher, payload, policy_id, captured)
        result.decisions.append((policy_id, captured.decision or "allow"))
        message = _extract_context_message(captured.emitted)
        if message:
            messages.append(message)
    if not messages:
        return 0
    merged = "\n".join(dict.fromkeys(messages))
    return dispatcher._additional_context(payload, merged, last_policy_id)


def run_bundle(
    policy_ids: list[str],
    harness: str,
    payload: Any,
    *,
    mode: str = "enforce-chain",
    timeout_seconds: float = DEFAULT_BUNDLE_TIMEOUT_SECONDS,
    dispatcher: Dispatcher,
) -> int:
    """Run ``policy_ids`` in one process per ``mode`` and emit exactly one stdout payload.

    ``dispatcher`` is the already-loaded ``hooks/wagents-hook.py`` module (passed
    in explicitly rather than imported, since that module may itself be loaded
    by file path outside a normal package context).
    """
    if mode not in BUNDLE_MODES:
        raise ValueError(f"unknown bundle mode: {mode!r} (expected one of {BUNDLE_MODES})")
    if not policy_ids:
        return 0

    result = BundleResult(code=0)
    deadline = time.monotonic() + max(timeout_seconds, 0.0)

    if mode == "context-chain":
        return _run_context_chain(dispatcher, policy_ids, payload, deadline=deadline, result=result)

    enforce_ids = policy_ids if mode == "enforce-chain" else [
        pid for pid in policy_ids if pid in dispatcher.ENFORCE_POLICY_IDS
    ]
    context_ids = [] if mode == "enforce-chain" else [pid for pid in policy_ids if pid not in enforce_ids]

    denied, code = _run_enforce_chain(dispatcher, enforce_ids, payload, deadline=deadline, result=result)
    if denied:
        return code

    if context_ids:
        code = _run_context_chain(dispatcher, context_ids, payload, deadline=deadline, result=result)
        if code:
            return code

    if (
        harness == "cursor"
        and not dispatcher._STDOUT_EMITTED
        and any(pid in dispatcher.CURSOR_FAIL_CLOSED_ALLOW_POLICIES for pid in policy_ids)
    ):
        return dispatcher._emit_json({"permission": "allow"})
    return 0
