#!/usr/bin/env python3
"""Research skill hook policies for read-only source enforcement and stop verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
RESEARCH_STATE_TTL = timedelta(hours=12)
WRITE_TOOL_NAMES = {
    "write",
    "edit",
    "multiedit",
    "apply_patch",
    "create",
    "replace",
    "write_file",
    "edit_file",
}
SHELL_TOOL_NAMES = {"bash", "run_shell_command", "shell", "terminal"}


@dataclass
class NormalizedPayload:
    harness: str
    event: str
    tool_name: str
    tool_input: dict[str, Any]
    command: str
    file_path: str
    prompt: str
    cwd: str
    session_id: str
    stop_hook_active: bool
    raw: dict[str, Any]
    decision_recorded: bool = False


def _load_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _loads_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _detect_harness(payload: dict[str, Any], requested: str) -> str:
    if requested != "auto":
        return requested
    if "toolName" in payload or "toolArgs" in payload:
        return "github-copilot"
    event = str(payload.get("hook_event_name") or "")
    if event in {"BeforeTool", "AfterTool", "BeforeAgent", "AfterAgent"}:
        return "gemini-cli"
    return "codex"


def _normalize(payload: dict[str, Any], harness: str) -> NormalizedPayload:
    tool_args = _loads_object(payload.get("toolArgs"))
    tool_input = _loads_object(payload.get("tool_input")) or tool_args
    tool_name = str(
        payload.get("tool_name")
        or payload.get("toolName")
        or payload.get("original_request_name")
        or payload.get("tool")
        or payload.get("request_tool_name")
        or ""
    )
    command = str(
        tool_input.get("command")
        or tool_input.get("cmd")
        or tool_input.get("shell_command")
        or tool_args.get("command")
        or payload.get("command")
        or payload.get("cmd")
        or payload.get("shell_command")
        or ""
    )
    file_path = str(
        tool_input.get("file_path")
        or tool_input.get("filePath")
        or tool_input.get("path")
        or tool_input.get("target_file")
        or tool_args.get("file_path")
        or tool_args.get("path")
        or payload.get("file_path")
        or payload.get("filePath")
        or payload.get("path")
        or ""
    )
    return NormalizedPayload(
        harness=harness,
        event=str(payload.get("hook_event_name") or payload.get("event") or ""),
        tool_name=tool_name,
        tool_input=tool_input,
        command=command,
        file_path=file_path,
        prompt=str(payload.get("prompt") or payload.get("userPrompt") or ""),
        cwd=str(payload.get("cwd") or os.getcwd()),
        session_id=str(payload.get("session_id") or payload.get("sessionId") or "default"),
        stop_hook_active=payload.get("stop_hook_active") is True,
        raw=payload,
    )


def _agent_home(harness: str) -> Path:
    folder = {
        "codex": ".codex",
        "claude-code": ".claude",
        "github-copilot": ".copilot",
        "gemini-cli": ".gemini",
    }.get(harness, ".agents")
    return Path.home() / folder / "research"


def _state_path(payload: NormalizedPayload) -> Path:
    digest = hashlib.sha256(payload.session_id.encode("utf-8")).hexdigest()[:24]
    return _agent_home(payload.harness) / "hook-state" / f"{digest}.json"


def _audit_path(payload: NormalizedPayload) -> Path:
    return _agent_home(payload.harness) / "hook-ledger" / f"{_state_path(payload).stem}.jsonl"


def _record_decision(payload: NormalizedPayload, policy_id: str, decision: str, reason: str = "") -> None:
    path = _audit_path(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": _now().isoformat(),
        "policy": policy_id,
        "decision": decision,
        "reason": reason[:500],
        "event": payload.event,
        "tool": payload.tool_name or "unknown",
        "cwd": payload.cwd,
        "session_id_hash": _state_path(payload).stem,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    path.chmod(0o600)
    payload.decision_recorded = True


def _now() -> datetime:
    return datetime.now(UTC)


def _state_active(payload: NormalizedPayload) -> bool:
    if os.environ.get("RESEARCH_SKILL_ACTIVE") == "1":
        return True
    path = _state_path(payload)
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        updated = datetime.fromisoformat(str(data.get("updated_at")))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=UTC)
    return bool(data.get("active")) and _now() - updated <= RESEARCH_STATE_TTL


def _emit_json(data: dict[str, Any]) -> int:
    json.dump(data, sys.stdout, separators=(",", ":"))
    print()
    return 0


def _deny(payload: NormalizedPayload, reason: str, policy_id: str = "policy-deny") -> int:
    _record_decision(payload, policy_id, "deny", reason)
    if payload.harness == "github-copilot":
        return _emit_json({"permissionDecision": "deny", "permissionDecisionReason": reason})
    if payload.harness == "codex":
        return _emit_json({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        })
    if payload.harness == "gemini-cli":
        return _emit_json({"decision": "deny", "reason": reason, "suppressOutput": True})
    print(reason, file=sys.stderr)
    return 2


def _stop_retry(payload: NormalizedPayload, reason: str) -> int:
    if payload.harness == "codex":
        return _emit_json({"decision": "block", "reason": reason})
    if payload.harness == "gemini-cli":
        return _emit_json({"decision": "deny", "reason": reason, "suppressOutput": True})
    print(reason, file=sys.stderr)
    return 2


def _tool_name(payload: NormalizedPayload) -> str:
    return payload.tool_name.strip().lower()


def _split_shell(command: str) -> list[str]:
    try:
        return shlex.split(command, comments=False)
    except ValueError:
        return []


def _is_allowed_research_target(target: str, cwd: str) -> bool:
    target = target.strip().strip("'\"")
    if not target or target in {"/dev/null", "&1", "&2"}:
        return target == "/dev/null"
    raw_path = Path(target).expanduser()
    if not raw_path.is_absolute():
        raw_path = Path(cwd).expanduser() / raw_path
    try:
        resolved = raw_path.resolve(strict=False)
    except OSError:
        return False
    allowed_roots = [
        Path.home() / ".codex" / "research",
        Path.home() / ".claude" / "research",
        Path.home() / ".gemini" / "research",
        Path.home() / ".copilot" / "research",
    ]
    return any(resolved == root or root in resolved.parents for root in allowed_roots)


def _redirection_targets(command: str) -> list[str]:
    pattern = re.compile(r"(?:^|\s)(?:\d?>{1,2}|&>|>{1,2})\s*(?!&)(?P<target>[^\s;&|]+)")
    return [match.group("target") for match in pattern.finditer(command)]


def _journal_store_invocation(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        path = Path(token)
        if path.name != "journal-store.py":
            continue
        if "-c" in tokens[:index]:
            return False
        parts = set(path.parts)
        return {"skills", "research", "scripts"}.issubset(parts)
    return False


def _tee_targets(tokens: list[str]) -> list[str]:
    targets: list[str] = []
    for index, token in enumerate(tokens):
        if Path(token).name != "tee":
            continue
        for candidate in tokens[index + 1 :]:
            if candidate in {"&&", "||", ";", "|"}:
                break
            if not candidate.startswith("-"):
                targets.append(candidate)
    return targets


def _copy_move_targets(tokens: list[str]) -> list[str]:
    targets: list[str] = []
    for index, token in enumerate(tokens):
        command_name = Path(token).name
        if command_name not in {"cp", "mv", "touch"}:
            continue
        args: list[str] = []
        for candidate in tokens[index + 1 :]:
            if candidate in {"&&", "||", ";", "|"}:
                break
            if not candidate.startswith("-"):
                args.append(candidate)
        if command_name == "touch":
            targets.extend(args)
        elif args:
            targets.append(args[-1])
    return targets


def _shell_writes_source(command: str, cwd: str) -> bool:
    if not command:
        return False
    tokens = _split_shell(command)
    redirection_targets = _redirection_targets(command)
    if any(not _is_allowed_research_target(target, cwd) for target in redirection_targets):
        return True
    if re.search(r"(^|\s)(sed|perl)\s+-i\b", command):
        return True
    tee_targets = _tee_targets(tokens)
    if tee_targets:
        return any(not _is_allowed_research_target(target, cwd) for target in tee_targets)
    copy_move_targets = _copy_move_targets(tokens)
    if copy_move_targets:
        return any(not _is_allowed_research_target(target, cwd) for target in copy_move_targets)
    if re.search(r"(^|\s)(python|python3|node|ruby|perl)\b.*\b(open|write|write_text)\b", command):
        return not _journal_store_invocation(tokens)
    return False


def readonly_write_guard(payload: NormalizedPayload) -> int:
    if not _state_active(payload):
        return 0
    name = _tool_name(payload)
    if name in WRITE_TOOL_NAMES or any(token in name for token in ("edit", "write", "replace", "create")):
        return _deny(
            payload,
            "Research sessions are read-only for source files; use journal-store.py for research journals.",
            policy_id="research-readonly-write-guard",
        )
    if name in SHELL_TOOL_NAMES and _shell_writes_source(payload.command, payload.cwd):
        return _deny(
            payload,
            "Research shell command appears to write source files; journals must stay under the research state dir.",
            policy_id="research-readonly-write-guard",
        )
    return 0


def stop_verifier(payload: NormalizedPayload) -> int:
    if payload.stop_hook_active or not _state_active(payload):
        return 0
    script = REPO_ROOT / "skills" / "research" / "scripts" / "verify.py"
    command = ["uv", "run", "python", str(script), "stop"]
    proc = subprocess.run(
        command,
        input=json.dumps(payload.raw),
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )
    if proc.returncode == 0:
        return 0
    reason = (proc.stderr or proc.stdout or "Research stop verifier failed.").strip()
    return _stop_retry(payload, reason)


POLICIES = {
    "research-readonly-write-guard": readonly_write_guard,
    "research-stop-verifier": stop_verifier,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run research skill hook policies.")
    parser.add_argument("policy_id", choices=sorted(POLICIES))
    parser.add_argument("--harness", default="auto")
    args = parser.parse_args(argv)

    raw = _load_payload()
    harness = _detect_harness(raw, args.harness)
    payload = _normalize(raw, harness)
    code = POLICIES[args.policy_id](payload)
    if code == 0 and not payload.decision_recorded:
        _record_decision(payload, args.policy_id, "allow")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
