#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
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
RESEARCH_PROMPT_RE = re.compile(r"(?i)(^|\s)(/research|agents:research|deep research|research skill)\b")
URL_RE = re.compile(r"https?://[^\s\"'<>)]{6,}")


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
    tool_name = str(payload.get("tool_name") or payload.get("toolName") or payload.get("original_request_name") or "")
    command = str(
        tool_input.get("command")
        or tool_input.get("cmd")
        or tool_input.get("shell_command")
        or tool_args.get("command")
        or ""
    )
    file_path = str(
        tool_input.get("file_path")
        or tool_input.get("filePath")
        or tool_input.get("path")
        or tool_input.get("target_file")
        or tool_args.get("file_path")
        or tool_args.get("path")
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


def _now() -> datetime:
    return datetime.now(UTC)


def _write_state(payload: NormalizedPayload) -> None:
    path = _state_path(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "active": True,
        "session_id_hash": path.stem,
        "updated_at": _now().isoformat(),
        "cwd": payload.cwd,
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o600)


def _state_active(payload: NormalizedPayload) -> bool:
    if os.environ.get("WAGENTS_RESEARCH_ACTIVE") == "1":
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


def _is_research_prompt(prompt: str) -> bool:
    return bool(RESEARCH_PROMPT_RE.search(prompt))


def _emit_json(data: dict[str, Any]) -> int:
    json.dump(data, sys.stdout, separators=(",", ":"))
    print()
    return 0


def _additional_context(payload: NormalizedPayload, message: str) -> int:
    if payload.harness == "github-copilot":
        return 0
    if payload.harness == "gemini-cli":
        return _emit_json({"hookSpecificOutput": {"additionalContext": message}, "suppressOutput": True})
    event = payload.event or "UserPromptSubmit"
    return _emit_json({"hookSpecificOutput": {"hookEventName": event, "additionalContext": message}})


def _deny(payload: NormalizedPayload, reason: str) -> int:
    if payload.harness == "github-copilot":
        return _emit_json({"permissionDecision": "deny", "permissionDecisionReason": reason})
    if payload.harness == "codex":
        return _emit_json(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    if payload.harness == "gemini-cli":
        return _emit_json({"decision": "deny", "reason": reason, "suppressOutput": True})
    print(reason, file=sys.stderr)
    return 2


def _stop_retry(payload: NormalizedPayload, reason: str) -> int:
    if payload.harness == "codex":
        return _emit_json({"continue": False, "stopReason": reason, "systemMessage": reason})
    if payload.harness == "gemini-cli":
        return _emit_json({"decision": "deny", "reason": reason, "suppressOutput": True})
    print(reason, file=sys.stderr)
    return 2


def _tool_name(payload: NormalizedPayload) -> str:
    return payload.tool_name.strip().lower()


def _policy_prompt_triage(payload: NormalizedPayload) -> int:
    if not _is_research_prompt(payload.prompt):
        return 0
    _write_state(payload)
    return _additional_context(
        payload,
        (
            "Research hook active: triage before retrieval, keep source-file writes blocked, "
            "cross-validate claims before confidence >= 0.7, and disclose degraded mode if retrieval tools fail."
        ),
    )


def _policy_readonly_write_guard(payload: NormalizedPayload) -> int:
    if not _state_active(payload):
        return 0
    name = _tool_name(payload)
    if name in WRITE_TOOL_NAMES or any(token in name for token in ("edit", "write", "replace", "create")):
        return _deny(
            payload,
            "Research sessions are read-only for source files; use journal-store.py for research journals.",
        )
    if name in SHELL_TOOL_NAMES and _shell_writes_source(payload.command):
        return _deny(
            payload,
            "Research shell command appears to write source files; journals must stay under the research state dir.",
        )
    return 0


def _shell_writes_source(command: str) -> bool:
    if not command:
        return False
    allowed = (
        "journal-store.py",
        "/research/",
        ".codex/research",
        ".claude/research",
        ".gemini/research",
        ".copilot/research",
    )
    if any(token in command for token in allowed):
        return False
    write_patterns = [
        r"(^|\s)(cat|printf|echo)\b.*>\s*(?!/dev/null)",
        r"(^|\s)(python|python3|node|ruby|perl)\b.*\b(open|write|write_text)\b",
        r"(^|\s)(sed|perl)\s+-i\b",
        r"(^|\s)(tee|touch|mv|cp)\b",
    ]
    return any(re.search(pattern, command) for pattern in write_patterns)


def _policy_dangerous_shell_guard(payload: NormalizedPayload) -> int:
    if not _state_active(payload) or _tool_name(payload) not in SHELL_TOOL_NAMES:
        return 0
    command = payload.command
    checks = [
        (
            r"(sudo\s+)?rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive\s+--force)",
            "Destructive recursive remove blocked during research.",
        ),
        (r"\bgit\s+reset\s+--hard\b", "git reset --hard is blocked during research."),
        (r"\bgit\s+clean\s+-[a-zA-Z]*f", "git clean -f is blocked during research."),
        (r"\b(curl|wget)\b.*\|\s*(ba)?sh\b", "Piping remote scripts to shell is blocked during research."),
        (
            r"\b(npm|pnpm|yarn|brew|pip|uv)\b.*\b(-g|--global|install)\b",
            "Package/global installs are blocked during research.",
        ),
    ]
    for pattern, reason in checks:
        if re.search(pattern, command):
            return _deny(payload, reason)
    return 0


def _extract_urls(value: Any, limit: int = 20) -> list[str]:
    text = json.dumps(value, ensure_ascii=True) if not isinstance(value, str) else value
    seen: list[str] = []
    for match in URL_RE.finditer(text):
        url = match.group(0).rstrip(".,")
        if url not in seen:
            seen.append(url)
        if len(seen) >= limit:
            break
    return seen


def _policy_evidence_ledger(payload: NormalizedPayload) -> int:
    if not _state_active(payload):
        return 0
    urls = _extract_urls(payload.raw.get("tool_response") or payload.raw.get("toolResult") or payload.raw)
    if not urls and not payload.tool_name:
        return 0
    path = _agent_home(payload.harness) / "hook-ledger" / f"{_state_path(payload).stem}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": _now().isoformat(),
        "tool": payload.tool_name or "unknown",
        "url_count": len(urls),
        "urls": urls[:10],
        "cwd": payload.cwd,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    path.chmod(0o600)
    return 0


def _policy_stop_verifier(payload: NormalizedPayload) -> int:
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
    "research-prompt-triage-context": _policy_prompt_triage,
    "research-readonly-write-guard": _policy_readonly_write_guard,
    "research-dangerous-shell-guard": _policy_dangerous_shell_guard,
    "research-evidence-ledger": _policy_evidence_ledger,
    "research-stop-verifier": _policy_stop_verifier,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run repo-managed wagents hook policies.")
    parser.add_argument("policy_id", choices=sorted(POLICIES))
    parser.add_argument("--harness", default="auto")
    args = parser.parse_args(argv)

    raw = _load_payload()
    harness = _detect_harness(raw, args.harness)
    payload = _normalize(raw, harness)
    return POLICIES[args.policy_id](payload)


if __name__ == "__main__":
    raise SystemExit(main())
