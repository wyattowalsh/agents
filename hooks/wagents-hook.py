#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import py_compile
import re
import shlex
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
RESEARCH_HOOK_PATH = REPO_ROOT / "skills" / "research" / "scripts" / "research_hook.py"
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
PATH_KEY_NAMES = {
    "file",
    "file_path",
    "filepath",
    "filename",
    "path",
    "target",
    "target_file",
}
PATH_LIST_KEY_NAMES = {"files", "file_paths", "filepaths", "paths", "target_files"}
SECRET_BASENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.staging",
    ".env.development",
    ".env.test",
    "credentials.json",
    "secrets.json",
    "service-account.json",
    "token.pickle",
}
PRIVATE_KEY_BASENAMES = {"id_rsa", "id_ed25519", "id_ecdsa", "id_dsa"}
PRIVATE_KEY_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
LOCKFILE_RE = re.compile(
    r"(?i)(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb|uv\.lock|poetry\.lock|cargo\.lock|gemfile\.lock)$"
)
STRONG_CODE_WORK_CLAIM_RE = re.compile(
    r"(?i)\b(implemented|fixed|refactored|patched|wired|ran|validated|verified|tests?\s+pass(?:ed)?)\b"
)
GENERIC_CHANGE_CLAIM_RE = re.compile(r"(?i)\b(updated|modified|changed|added|removed|created)\b")
CODE_CONTEXT_RE = re.compile(
    r"(?i)(`[^`]+`|(?:^|\s)[\w./-]+\.(?:py|json|toml|md|yaml|yml|js|jsx|ts|tsx|sh|rs|go|rb|java|kt|swift|lock)\b|\b(code|repo|repository|file|files|path|paths|diff|hook|hooks|config|script|test|tests|docs?|readme|openspec|registry|lockfile)\b)"
)
VALIDATION_EVIDENCE_RE = re.compile(
    r"(?i)\b(test(?:ed|s)?|pytest|unittest|vitest|npm\s+test|pnpm\s+test|uv\s+run|validate(?:d|ion)?|lint(?:ed)?|typecheck|mypy|ruff|py_compile|build|git\s+diff\s+--check|not\s+run|not\s+executed|could\s+not\s+run|couldn't\s+run|unable\s+to\s+run|skipped)\b"
)
TRUTH_GATE_SKIP_RE = re.compile(
    r"(?i)\b(blocked|not\s+complete|not\s+completed|unable\s+to\s+complete|no\s+code\s+changes)\b"
)
QUALITY_FILE_LIMIT = 1_000_000
QUALITY_PATH_LIMIT = 8


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
        "cursor": ".cursor",
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
    if os.environ.get("RESEARCH_SKILL_ACTIVE") == "1" or os.environ.get("WAGENTS_RESEARCH_ACTIVE") == "1":
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


def _additional_context(
    payload: NormalizedPayload, message: str, policy_id: str = "research-prompt-triage-context"
) -> int:
    if payload.harness == "github-copilot":
        return 0
    _record_decision(payload, policy_id, "context", message)
    if payload.harness == "cursor":
        return _emit_json({"additional_context": message, "user_message": message})
    if payload.harness == "gemini-cli":
        return _emit_json({"hookSpecificOutput": {"additionalContext": message}, "suppressOutput": True})
    event = payload.event or "UserPromptSubmit"
    return _emit_json({"hookSpecificOutput": {"hookEventName": event, "additionalContext": message}})


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
    if payload.harness == "cursor":
        return _emit_json({"permission": "deny", "user_message": reason, "agent_message": reason})
    if payload.harness == "gemini-cli":
        return _emit_json({"decision": "deny", "reason": reason, "suppressOutput": True})
    print(reason, file=sys.stderr)
    return 2


def _codex_permission_deny(payload: NormalizedPayload, reason: str, policy_id: str) -> int:
    _record_decision(payload, policy_id, "deny", reason)
    return _emit_json({
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {"behavior": "deny", "message": reason},
        }
    })


def _stop_retry(payload: NormalizedPayload, reason: str) -> int:
    if payload.harness == "codex":
        return _emit_json({"decision": "block", "reason": reason})
    if payload.harness == "cursor":
        return _emit_json({"followup_message": reason, "user_message": reason})
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


@lru_cache(maxsize=1)
def _load_research_hook_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("research_hook", RESEARCH_HOOK_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load research hook module from {RESEARCH_HOOK_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _research_payload(payload: NormalizedPayload, research_hook):
    return research_hook.NormalizedPayload(
        harness=payload.harness,
        event=payload.event,
        tool_name=payload.tool_name,
        tool_input=payload.tool_input,
        command=payload.command,
        file_path=payload.file_path,
        prompt=payload.prompt,
        cwd=payload.cwd,
        session_id=payload.session_id,
        stop_hook_active=payload.stop_hook_active,
        raw=payload.raw,
        decision_recorded=payload.decision_recorded,
    )


def _policy_readonly_write_guard(payload: NormalizedPayload) -> int:
    research_hook = _load_research_hook_module()
    research_payload = _research_payload(payload, research_hook)
    code = research_hook.readonly_write_guard(research_payload)
    payload.decision_recorded = research_payload.decision_recorded
    return code


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


def _json_text(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    except TypeError:
        return str(value)


def _walk_path_values(value: Any) -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_normalized = str(key).replace("-", "_").lower()
            if key_normalized in PATH_KEY_NAMES and isinstance(child, str):
                paths.append(child)
            elif key_normalized in PATH_LIST_KEY_NAMES and isinstance(child, list):
                paths.extend(str(item) for item in child if isinstance(item, str))
            paths.extend(_walk_path_values(child))
    elif isinstance(value, list):
        for child in value:
            paths.extend(_walk_path_values(child))
    return paths


def _patch_paths(text: str) -> list[str]:
    paths: list[str] = []
    patterns = [
        r"^\*\*\* (?:Add|Update|Delete) File: (?P<path>.+)$",
        r"^\+\+\+ b/(?P<path>.+)$",
        r"^--- a/(?P<path>.+)$",
    ]
    for line in text.splitlines():
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                paths.append(match.group("path").strip())
                break
    return paths


def _candidate_paths(payload: NormalizedPayload) -> list[str]:
    paths = []
    if payload.file_path:
        paths.append(payload.file_path)
    paths.extend(_walk_path_values(payload.tool_input))
    paths.extend(_walk_path_values(payload.raw))
    for patch_value in (payload.tool_input.get("patch"), payload.raw.get("patch")):
        if isinstance(patch_value, str):
            paths.extend(_patch_paths(patch_value))
    raw_text = _json_text(payload.raw)
    paths.extend(_patch_paths(raw_text))
    deduped: list[str] = []
    for path in paths:
        cleaned = path.strip().strip("'\"")
        if cleaned and cleaned not in deduped:
            deduped.append(cleaned)
    return deduped


def _path_block_reason(path: str) -> str | None:
    cleaned = path.strip().strip("'\"")
    if not cleaned:
        return None
    if re.search(r"(^|/)\.\.(/|$)", cleaned):
        return f"Path traversal detected: {cleaned}"
    parts = Path(cleaned).parts
    if ".git" in parts:
        return f"Protected git internal path: {cleaned}"
    basename = Path(cleaned).name
    if basename in SECRET_BASENAMES:
        return f"Protected secret-bearing file: {cleaned}"
    if basename in PRIVATE_KEY_BASENAMES or Path(cleaned).suffix.lower() in PRIVATE_KEY_SUFFIXES:
        return f"Protected private key file: {cleaned}"
    if LOCKFILE_RE.search(cleaned):
        return f"Lock files should not be edited directly: {cleaned}"
    return None


def _protected_payload_reason(payload: NormalizedPayload) -> str | None:
    for path in _candidate_paths(payload):
        reason = _path_block_reason(path)
        if reason:
            return reason
    if _tool_name(payload) in SHELL_TOOL_NAMES and payload.command:
        targets = [
            *_redirection_targets(payload.command),
            *_tee_targets(_split_shell(payload.command)),
            *_copy_move_targets(_split_shell(payload.command)),
        ]
        for target in targets:
            reason = _path_block_reason(target)
            if reason:
                return reason
        if re.search(r"(^|\s)(sed|perl)\s+-i\b", payload.command):
            for token in _split_shell(payload.command):
                reason = _path_block_reason(token)
                if reason:
                    return reason
    return None


def _destructive_shell_reason(command: str) -> str | None:
    if not command:
        return None
    checks = [
        (
            r"(sudo\s+)?rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive\s+--force|-[a-zA-Z]*f[a-zA-Z]*r)\s+(/|~|\$HOME|/Users|/System|/Library|/etc|/var|/usr|\.\.|\./?$)",
            "rm -rf on a critical path is blocked.",
        ),
        (r"\bgit\s+reset\s+--hard\b", "git reset --hard is blocked because it destroys uncommitted work."),
        (r"\bgit\s+clean\s+-[a-zA-Z]*f", "git clean -f is blocked because it permanently removes untracked files."),
        (r"\b(curl|wget)\b.*\|\s*(ba)?sh\b", "Piping a remote script to shell is blocked."),
        (
            r"\bgit\s+push\b(?=.*\s(--force(\s|$)|-f(\s|$)))(?=.*\s(main|master)(\s|$))(?!.*--force-with-lease)",
            "Force push to main/master is blocked. Use --force-with-lease after review.",
        ),
    ]
    for pattern, reason in checks:
        if re.search(pattern, command):
            return reason
    return None


def _git_session_context(cwd: str) -> str:
    repo_cwd = cwd or str(REPO_ROOT)
    proc = subprocess.run(
        ["git", "status", "--short", "--branch"],
        cwd=repo_cwd,
        text=True,
        capture_output=True,
        timeout=2,
        check=False,
    )
    if proc.returncode != 0:
        return f"cwd={repo_cwd}; git=unavailable"
    lines = proc.stdout.splitlines()
    branch = lines[0].removeprefix("## ") if lines else "unknown"
    dirty_count = max(len(lines) - 1, 0)
    return f"cwd={repo_cwd}; branch={branch}; dirty_paths={dirty_count}"


def _display_paths(paths: list[str], limit: int = 5) -> str:
    if not paths:
        return "none detected"
    shown = paths[:limit]
    suffix = "" if len(paths) <= limit else f"; +{len(paths) - limit} more"
    return ", ".join(shown) + suffix


def _truncate(text: str, limit: int = 400) -> str:
    compact = " ".join(text.strip().split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _repo_root_for_cwd(cwd: str) -> Path:
    start = Path(cwd or os.getcwd()).expanduser()
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        text=True,
        capture_output=True,
        timeout=2,
        check=False,
    )
    if proc.returncode == 0 and proc.stdout.strip():
        return Path(proc.stdout.strip()).resolve(strict=False)
    return start.resolve(strict=False)


def _quality_paths(payload: NormalizedPayload) -> tuple[Path, list[Path]]:
    repo_root = _repo_root_for_cwd(payload.cwd)
    paths: list[Path] = []
    for raw_path in _candidate_paths(payload):
        candidate = Path(raw_path).expanduser()
        if not candidate.is_absolute():
            candidate = repo_root / candidate
        resolved = candidate.resolve(strict=False)
        if resolved != repo_root and repo_root not in resolved.parents:
            continue
        if resolved not in paths:
            paths.append(resolved)
        if len(paths) >= QUALITY_PATH_LIMIT:
            break
    return repo_root, paths


def _run_text_parse_check(label: str, path: Path) -> str | None:
    try:
        if path.stat().st_size > QUALITY_FILE_LIMIT:
            return f"skip {label}: {path.name} is larger than {QUALITY_FILE_LIMIT} bytes"
        text = path.read_text(encoding="utf-8")
        if label == "json":
            json.loads(text)
        elif label == "toml":
            tomllib.loads(text)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        return f"{label} failed for {path.name}: {_truncate(str(exc))}"
    return None


def _run_fast_quality_checks(repo_root: Path, paths: list[Path]) -> tuple[list[str], list[str]]:
    passed: list[str] = []
    failures: list[str] = []
    existing_files = [path for path in paths if path.exists() and path.is_file()]
    relative_paths = [str(path.relative_to(repo_root)) for path in paths if path.exists() or path.parent.exists()]
    if relative_paths:
        proc = subprocess.run(
            ["git", "diff", "--check", "--", *relative_paths],
            cwd=repo_root,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
        if proc.returncode == 0:
            passed.append("git diff --check")
        elif proc.returncode != 129:
            failures.append(f"git diff --check failed: {_truncate(proc.stderr or proc.stdout)}")
    for path in existing_files:
        suffix = path.suffix.lower()
        if suffix == ".json":
            failure = _run_text_parse_check("json", path)
            failures.append(failure) if failure else passed.append(f"json:{path.name}")
        elif suffix == ".toml":
            failure = _run_text_parse_check("toml", path)
            failures.append(failure) if failure else passed.append(f"toml:{path.name}")
        elif suffix == ".py":
            try:
                py_compile.compile(str(path), cfile=os.devnull, doraise=True)
            except (OSError, py_compile.PyCompileError) as exc:
                failures.append(f"py_compile failed for {path.name}: {_truncate(str(exc))}")
            else:
                passed.append(f"py_compile:{path.name}")
    return passed, failures


def _last_assistant_message(payload: NormalizedPayload) -> str:
    for key in ("last_assistant_message", "lastAssistantMessage", "assistant_message", "message"):
        value = payload.raw.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _has_code_work_claim(message: str) -> bool:
    if STRONG_CODE_WORK_CLAIM_RE.search(message):
        return True
    return bool(GENERIC_CHANGE_CLAIM_RE.search(message) and CODE_CONTEXT_RE.search(message))


def _policy_codex_session_start_context(payload: NormalizedPayload) -> int:
    label = "Cursor" if payload.harness == "cursor" else "Codex"
    message = (
        f"{label} session context: {_git_session_context(payload.cwd)}; managed hooks source=config/hook-registry.json."
    )
    return _additional_context(payload, message, "codex-session-start-context")


def _policy_codex_destructive_shell_guard(payload: NormalizedPayload) -> int:
    if _tool_name(payload) not in SHELL_TOOL_NAMES and not payload.command:
        return 0
    reason = _destructive_shell_reason(payload.command)
    if reason:
        return _deny(payload, reason, "codex-destructive-shell-guard")
    return 0


def _policy_codex_protected_file_guard(payload: NormalizedPayload) -> int:
    reason = _protected_payload_reason(payload)
    if reason:
        return _deny(payload, reason, "codex-protected-file-guard")
    return 0


def _policy_codex_permission_request_guard(payload: NormalizedPayload) -> int:
    reason = _destructive_shell_reason(payload.command) or _protected_payload_reason(payload)
    if reason:
        return _codex_permission_deny(payload, reason, "codex-permission-request-guard")
    return 0


def _policy_codex_post_tool_verify_context(payload: NormalizedPayload) -> int:
    repo_root, quality_paths = _quality_paths(payload)
    paths = [str(path.relative_to(repo_root)) for path in quality_paths] or _candidate_paths(payload)
    if not paths and not payload.command:
        return 0
    passed, failures = _run_fast_quality_checks(repo_root, quality_paths) if quality_paths else ([], [])
    quality_context = ""
    if failures:
        quality_context = f" Fast quality checks found issues: {'; '.join(failures[:3])}."
    elif passed:
        quality_context = f" Fast quality checks passed: {', '.join(passed[:5])}."
    elif paths:
        quality_context = " No lightweight file-type checks were available for these paths."
    message = (
        "Codex post-edit quality context: inspect the diff and run focused validation before final claims; "
        f"touched paths: {_display_paths(paths)}.{quality_context}"
    )
    return _additional_context(payload, message, "codex-post-tool-verify-context")


def _policy_codex_stop_truth_gate(payload: NormalizedPayload) -> int:
    if payload.stop_hook_active:
        return 0
    message = _last_assistant_message(payload)
    if not message or TRUTH_GATE_SKIP_RE.search(message):
        return 0
    if not _has_code_work_claim(message):
        return 0
    if VALIDATION_EVIDENCE_RE.search(message):
        return 0
    reason = (
        "Stop-time truth gate: the final message claims code or repo work changed, "
        "but it does not cite validation evidence or explicitly say validation was not run. "
        "Do one focused verification pass, then final-answer with touched files and validation status."
    )
    return _stop_retry(payload, reason)


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
    path = _audit_path(payload)
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
    research_hook = _load_research_hook_module()
    research_payload = _research_payload(payload, research_hook)
    code = research_hook.stop_verifier(research_payload)
    payload.decision_recorded = research_payload.decision_recorded
    return code


POLICIES = {
    "codex-session-start-context": _policy_codex_session_start_context,
    "codex-destructive-shell-guard": _policy_codex_destructive_shell_guard,
    "codex-protected-file-guard": _policy_codex_protected_file_guard,
    "codex-permission-request-guard": _policy_codex_permission_request_guard,
    "codex-post-tool-verify-context": _policy_codex_post_tool_verify_context,
    "codex-stop-truth-gate": _policy_codex_stop_truth_gate,
    "cursor-session-start-context": _policy_codex_session_start_context,
    "cursor-destructive-shell-guard": _policy_codex_destructive_shell_guard,
    "cursor-protected-file-guard": _policy_codex_protected_file_guard,
    "cursor-post-tool-verify-context": _policy_codex_post_tool_verify_context,
    "cursor-stop-truth-gate": _policy_codex_stop_truth_gate,
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
    code = POLICIES[args.policy_id](payload)
    if code == 0 and not payload.decision_recorded and args.policy_id != "research-evidence-ledger":
        _record_decision(payload, args.policy_id, "allow")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
