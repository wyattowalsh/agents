#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import py_compile
import random
import re
import shlex
import stat
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_policy_attr(module_name: str, attr: str):
    """Load a stdlib-only decision function from ``wagents/hooks/policies/<module>.py``.

    This dispatcher runs under a trusted system ``python3`` where the ``wagents``
    distribution is not installed, so importing the package normally fails
    (``wagents/__init__`` resolves the installed version). The policy modules are
    deliberately dependency-free, so we load them by file path to share logic with
    the unit tests without triggering the package import chain. Returns ``None`` on
    any failure so the dispatcher fails open.

    Loaded modules are cached in ``sys.modules`` keyed by module name so a
    ``--bundle`` run that resolves the same underlying module for more than one
    policy id (or re-enters this loader for any reason within one process)
    reuses the already-executed module instead of re-reading and re-exec'ing
    the file from disk.
    """
    import importlib.util

    cache_key = f"_wagents_policy_{module_name}"
    module = sys.modules.get(cache_key)
    if module is not None:
        return getattr(module, attr, None)
    path = REPO_ROOT / "wagents" / "hooks" / "policies" / f"{module_name}.py"
    try:
        spec = importlib.util.spec_from_file_location(cache_key, path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[cache_key] = module
        return getattr(module, attr, None)
    except Exception:  # pragma: no cover - keep the dispatcher standalone-safe
        return None


evaluate_git_commit_push = _load_policy_attr("git_commit_push_guard", "evaluate_git_commit_push")
evaluate_before_read_file = _load_policy_attr("before_read_file_guard", "evaluate_before_read_file")
evaluate_before_mcp_execution = _load_policy_attr("before_mcp_execution", "evaluate_before_mcp_execution")
subagent_start_context = _load_policy_attr("subagent_start", "subagent_start_context")
_grok_deny_payload = _load_policy_attr("grok_deny_adapter", "grok_deny_payload")


@lru_cache(maxsize=1)
def _load_enforce_policy_ids() -> frozenset[str]:
    path = REPO_ROOT / "config" / "hook-registry.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return frozenset()
    return frozenset(
        str(entry["id"])
        for entry in data.get("hooks", [])
        if isinstance(entry, dict) and entry.get("mode") == "enforce" and entry.get("id")
    )


class _LazyEnforcePolicyIds:
    """Argv fast-path: defer the registry disk read+parse until first membership check.

    ``config/hook-registry.json`` is only consulted on the rare
    module-load-failure path (``_enforce_module_load_failure``); the vast
    majority of hook invocations never touch it. Behaves like a ``frozenset``
    for the ``in`` operator and iteration so existing call sites (including
    ``wagents_hook.ENFORCE_POLICY_IDS`` introspection in tests) keep working
    without any disk I/O until something actually asks a membership question.
    """

    def __contains__(self, item: object) -> bool:
        return item in _load_enforce_policy_ids()

    def __iter__(self):
        return iter(_load_enforce_policy_ids())

    def __len__(self) -> int:
        return len(_load_enforce_policy_ids())

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return repr(_load_enforce_policy_ids())


ENFORCE_POLICY_IDS = _LazyEnforcePolicyIds()

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
RESEARCH_IMPLEMENTATION_HANDOFF_PATTERNS = (
    re.compile(r"(?i)\b(?:implement|execute)\s+(?:the\s+)?(?:approved\s+)?(?:plan|implementation|fix(?:es)?|findings)\b"),
    re.compile(r"(?i)\bapply\s+(?:the\s+)?approved\s+(?:plan|finding(?:s)?|fix(?:es)?)\b"),
    re.compile(
        r"(?i)\b(?:continue|resume|retry|go on)\b(?:(?!\bresearch(?:ing)?\b).){0,100}"
        r"\b(?:fix(?:ing|es|ed)?|implement(?:ing|ed)?|patch(?:ing|ed)?)\b"
    ),
)
URL_RE = re.compile(r"https?://[^\s\"'<>)]{6,}")
PATH_KEY_NAMES = {
    "file",
    "file_path",
    "filepath",
    "filename",
    "image",
    "image_path",
    "img",
    "input_image",
    "media",
    "path",
    "target",
    "target_file",
}
PATH_LIST_KEY_NAMES = {
    "attachments",
    "files",
    "file_paths",
    "filepaths",
    "image_paths",
    "images",
    "media",
    "paths",
    "target_files",
}
IMAGE_INPUT_EXTENSIONS = {
    ".bmp",
    ".gif",
    ".heic",
    ".heif",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}
IMAGE_CONSUMER_TOOL_NAMES = {
    "analyze_image",
    "attach_image",
    "screenshot",
    "upload_image",
    "view_image",
}
GENERIC_IMAGE_PATH_TOOLS = {"read"}
IMAGE_TOOL_NAME_HINTS = ("image", "vision", "screenshot", "attach", "upload")
ALLOWED_SYMLINK_COMPONENTS = {
    Path("/private/tmp"),
    Path("/private/var"),
    Path("/tmp"),
    Path("/var"),
}
IMAGE_REWRITE_HARNESSES = {"claude-code"}
IMAGE_OPTIMIZER_POLICY_ID = "image-input-optimizer-guard"
IMAGE_OPTIMIZER_TIMEOUT_SECONDS = 50
IMAGE_OPTIMIZER_MAX_CANDIDATES = 2
IMAGE_OPTIMIZER_REGISTRY_TIMEOUT_SECONDS = 60
IMAGE_OPTIMIZER_ALLOWED_ENV = {
    "HOME",
    "LANG",
    "LC_ALL",
    "LOGNAME",
    "NO_COLOR",
    "PATH",
    "REQUESTS_CA_BUNDLE",
    "SSL_CERT_FILE",
    "TERM",
    "TMPDIR",
    "USER",
    "UV_NO_PROGRESS",
}
IMAGE_OPTIMIZER_DANGEROUS_ENV_PREFIXES = ("DYLD_", "LD_")
IMAGE_OPTIMIZER_DANGEROUS_ENV_NAMES = {
    "BASH_ENV",
    "ENV",
    "NODE_OPTIONS",
    "PYTHONHOME",
    "PYTHONPATH",
    "UV_TOOL_BIN_DIR",
}
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

# Cursor evaluates ``preToolUse``/``beforeShellExecution``/``beforeReadFile``/
# ``beforeMCPExecution`` enforce hooks as fail-closed: empty stdout (or a crash)
# is treated as a *block*. These permission-decision policies therefore must
# emit an explicit ``{"permission": "allow"}`` when they allow an action so a
# clean pass does not silently block the tool call. The image optimizer is
# intentionally excluded (see ``CURSOR_FAIL_OPEN_HOOK_IDS`` in
# ``wagents/hooks/render.py``) so it fails open with empty stdout regardless
# of matcher shape.
CURSOR_FAIL_CLOSED_ALLOW_POLICIES = {
    "cursor-destructive-shell-guard",
    "cursor-protected-file-guard",
    "cursor-before-read-file-guard",
    "cursor-before-shell-execution-guard",
    "cursor-before-mcp-execution-guard",
    "git-commit-push-guard",
    "research-readonly-write-guard",
    "research-dangerous-shell-guard",
}

_STDOUT_EMITTED = False

HOOK_TIMING_ENV = "WAGENTS_HOOK_TIMING"
HOOK_TIMING_PATH = Path.home() / ".cache" / "wagents" / "hook-timing.jsonl"


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


@dataclass
class ImageCandidate:
    path: Path
    raw_paths: list[str]
    identity: dict[str, int]


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


AUDIT_SAMPLE_ENV = "WAGENTS_HOOK_AUDIT_SAMPLE"
# Decisions that always bypass sampling regardless of WAGENTS_HOOK_AUDIT_SAMPLE:
# denies/blocks and content rewrites are the audit trail's whole point, so only
# routine "allow" records are ever eligible for sampling.
_AUDIT_ALWAYS_RECORD_DECISIONS = frozenset({"deny", "rewrite"})


def _audit_sample_rate() -> float:
    raw = os.environ.get(AUDIT_SAMPLE_ENV)
    if not raw:
        return 1.0
    try:
        rate = float(raw)
    except ValueError:
        return 1.0
    return min(max(rate, 0.0), 1.0)


def _should_record_audit(decision: str) -> bool:
    """Return True when this decision should be written to the audit ledger.

    Unset (default) ``WAGENTS_HOOK_AUDIT_SAMPLE`` records everything, matching
    today's behavior exactly. Setting it to a value in ``[0, 1)`` samples only
    routine "allow"/"context" records to cut disk I/O under high-frequency
    context hooks (e.g. session-start git status) while every deny/rewrite is
    always recorded for the audit trail.
    """
    if decision in _AUDIT_ALWAYS_RECORD_DECISIONS:
        return True
    rate = _audit_sample_rate()
    if rate >= 1.0:
        return True
    if rate <= 0.0:
        return False
    return random.random() < rate


def _best_effort_os() -> contextlib.AbstractContextManager[None]:
    """Swallow ``OSError`` from best-effort disk I/O (mkdir/open/write/chmod).

    Mirrors the try/except guard already used by ``_record_hook_timing``: a
    write failure (read-only filesystem, permission error, disk full,
    concurrent writers) must never raise out of a policy function and must
    never change the hook's stdout or exit code. Callers that need a flag such
    as ``decision_recorded`` to be set even when the guarded write fails must
    set that flag *before* entering this context manager.
    """
    return contextlib.suppress(OSError)


def _record_decision(payload: NormalizedPayload, policy_id: str, decision: str, reason: str = "") -> None:
    payload.decision_recorded = True
    if not _should_record_audit(decision):
        return
    with _best_effort_os():
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


def _now() -> datetime:
    return datetime.now(UTC)


def _write_state(payload: NormalizedPayload) -> None:
    path = _state_path(payload)
    data = {
        "active": True,
        "session_id_hash": path.stem,
        "updated_at": _now().isoformat(),
        "cwd": payload.cwd,
    }
    with _best_effort_os():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        path.chmod(0o600)


def _clear_state(payload: NormalizedPayload) -> None:
    path = _state_path(payload)
    with _best_effort_os():
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        data.update({
            "active": False,
            "cleared_at": _now().isoformat(),
            "clear_reason": "implementation-handoff",
        })
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        path.chmod(0o600)


def _forced_research_active() -> bool:
    return os.environ.get("RESEARCH_SKILL_ACTIVE") == "1" or os.environ.get("WAGENTS_RESEARCH_ACTIVE") == "1"


def _stored_state_active(payload: NormalizedPayload) -> bool:
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


def _state_active(payload: NormalizedPayload) -> bool:
    return _forced_research_active() or _stored_state_active(payload)


def _is_research_prompt(prompt: str) -> bool:
    return bool(RESEARCH_PROMPT_RE.search(prompt))


def _is_implementation_handoff_prompt(prompt: str) -> bool:
    if not prompt.strip() or _is_research_prompt(prompt):
        return False
    return any(pattern.search(prompt) for pattern in RESEARCH_IMPLEMENTATION_HANDOFF_PATTERNS)


def _emit_json(data: dict[str, Any]) -> int:
    global _STDOUT_EMITTED
    json.dump(data, sys.stdout, separators=(",", ":"))
    print()
    _STDOUT_EMITTED = True
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
    if payload.harness == "grok-build":
        if _grok_deny_payload is not None:
            return _emit_json(_grok_deny_payload(reason, policy_id=policy_id))
        return _emit_json({"decision": "block", "reason": reason})
    if payload.harness == "opencode":
        return _emit_json({
            "permission": "deny",
            "user_message": reason,
            "reason": reason,
            "hookSpecificOutput": {"policyId": policy_id, "permission": "deny"},
        })
    print(reason, file=sys.stderr)
    return 2


def _enforce_module_load_failure(payload: NormalizedPayload, policy_id: str) -> int:
    if policy_id not in ENFORCE_POLICY_IDS:
        return 0
    return _deny(
        payload,
        f"Policy module for '{policy_id}' failed to load; blocking as fail-closed enforce tier.",
        policy_id,
    )


def _tool_may_consume_image(payload: NormalizedPayload) -> bool:
    tool_name = _tool_name(payload)
    if tool_name in WRITE_TOOL_NAMES or tool_name in SHELL_TOOL_NAMES:
        return False
    if not tool_name:
        return False
    if tool_name in IMAGE_CONSUMER_TOOL_NAMES:
        return True
    if any(hint in tool_name for hint in IMAGE_TOOL_NAME_HINTS):
        return True
    if tool_name in GENERIC_IMAGE_PATH_TOOLS:
        return _payload_has_probable_image_paths(payload)
    return False


def _payload_has_probable_image_paths(payload: NormalizedPayload) -> bool:
    for raw_path in _candidate_paths(payload):
        lexical_path = _resolve_payload_path(raw_path, payload.cwd)
        if lexical_path is None or not lexical_path.is_file():
            continue
        if _looks_like_image_file(lexical_path):
            return True
    return False


def _resolve_payload_path(raw_path: str, cwd: str) -> Path | None:
    cleaned = raw_path.strip().strip("'\"")
    if not cleaned or re.match(r"(?i)^[a-z][a-z0-9+.-]*:", cleaned):
        return None
    path = Path(cleaned).expanduser()
    if not path.is_absolute():
        path = Path(cwd or os.getcwd()).expanduser() / path
    return path


def _is_allowed_system_symlink(path: Path) -> bool:
    try:
        resolved = path.resolve(strict=False)
    except OSError:
        return False
    return path in ALLOWED_SYMLINK_COMPONENTS or resolved in ALLOWED_SYMLINK_COMPONENTS


def _has_symlink_component(path: Path) -> bool:
    current = Path(path.anchor) if path.is_absolute() else Path()
    parts = path.parts[1:] if path.is_absolute() else path.parts
    for part in parts:
        current = current / part
        try:
            if current.is_symlink() and not _is_allowed_system_symlink(current):
                return True
        except OSError:
            return True
    return False


def _image_source_identity(path: Path) -> dict[str, int] | None:
    try:
        source_stat = path.stat(follow_symlinks=False)
    except OSError:
        return None
    if not stat.S_ISREG(source_stat.st_mode):
        return None
    return {
        "device": int(source_stat.st_dev),
        "inode": int(source_stat.st_ino),
        "size": int(source_stat.st_size),
        "mtimeNs": int(source_stat.st_mtime_ns),
    }


def _path_is_inside(path: Path, root: Path) -> bool:
    try:
        resolved_path = path.resolve(strict=False)
        resolved_root = root.expanduser().resolve(strict=False)
    except OSError:
        return False
    return resolved_path == resolved_root or resolved_root in resolved_path.parents


def _broad_image_root_reason(path: Path) -> str | None:
    try:
        resolved = path.expanduser().resolve(strict=True)
    except OSError:
        return f"Image input root does not exist or cannot be inspected: {path}"
    if not resolved.is_dir():
        return f"Image input root is not a directory: {path}"
    if resolved.is_symlink():
        return f"Image input root is a symlink: {path}"
    home = Path.home()
    broad_roots = {
        Path("/").resolve(strict=False),
        home.expanduser().resolve(strict=False),
        Path("/Users").resolve(strict=False),
    }
    if resolved in broad_roots:
        return f"Image input root is too broad: {resolved}"
    return None


def _safe_image_root(raw_root: Path) -> tuple[Path | None, str | None]:
    try:
        root = raw_root.expanduser()
    except OSError as exc:
        return None, f"Image input root cannot be expanded: {raw_root}: {exc}"
    reason = _broad_image_root_reason(root)
    if reason is not None:
        return None, reason
    try:
        return root.resolve(strict=True), None
    except OSError as exc:
        return None, f"Image input root cannot be resolved: {raw_root}: {exc}"


def _image_input_roots(payload: NormalizedPayload) -> tuple[list[Path], list[str]]:
    root_inputs = [
        Path(payload.cwd or os.getcwd()),
        REPO_ROOT,
        Path.home() / "Desktop",
        Path.home() / "Documents",
        Path.home() / "Downloads",
        Path.home() / "Pictures",
    ]
    tmpdir = os.environ.get("TMPDIR")
    if tmpdir:
        root_inputs.append(Path(tmpdir))
    deduped: list[Path] = []
    errors: list[str] = []
    for raw_root in root_inputs:
        root, error = _safe_image_root(raw_root)
        if error is not None:
            if raw_root == Path(payload.cwd or os.getcwd()) or (tmpdir and raw_root == Path(tmpdir)):
                errors.append(error)
            continue
        if root is not None and root not in deduped:
            deduped.append(root)
    return deduped, errors


def _looks_like_image_file(path: Path) -> bool:
    if path.suffix.lower() in IMAGE_INPUT_EXTENSIONS:
        return True
    try:
        with path.open("rb") as handle:
            header = handle.read(16)
    except OSError:
        return False
    return (
        header.startswith(b"\xff\xd8\xff")
        or header.startswith(b"\x89PNG\r\n\x1a\n")
        or header.startswith((b"GIF87a", b"GIF89a", b"BM"))
        or header.startswith((b"II*\x00", b"MM\x00*"))
        or (header.startswith(b"RIFF") and header[8:12] == b"WEBP")
    )


def _image_candidate_paths(payload: NormalizedPayload) -> tuple[list[ImageCandidate], list[str]]:
    raw_paths = _candidate_paths(payload)
    roots, root_errors = _image_input_roots(payload)
    candidates: list[ImageCandidate] = []
    by_path: dict[Path, ImageCandidate] = {}
    for raw_path in raw_paths:
        lexical_path = _resolve_payload_path(raw_path, payload.cwd)
        if lexical_path is None or not lexical_path.exists() or not lexical_path.is_file():
            continue
        if not _looks_like_image_file(lexical_path):
            continue
        if _has_symlink_component(lexical_path):
            return [], [f"Image input path contains a symlink component: {lexical_path}"]
        try:
            resolved = lexical_path.resolve(strict=True)
        except OSError:
            continue
        if _path_block_reason(str(resolved)):
            continue
        if not roots:
            return [], root_errors or ["No trusted image roots available"]
        if not any(_path_is_inside(resolved, root) for root in roots):
            return [], root_errors or [f"Image input path is outside trusted roots: {resolved}"]
        identity = _image_source_identity(resolved)
        if identity is None:
            continue
        if _image_source_identity(resolved) != identity:
            return [], [f"Image input path changed while it was being inspected: {resolved}"]
        existing = by_path.get(resolved)
        if existing is None:
            candidate = ImageCandidate(path=resolved, raw_paths=[raw_path], identity=identity)
            by_path[resolved] = candidate
            candidates.append(candidate)
        elif raw_path not in existing.raw_paths:
            existing.raw_paths.append(raw_path)
    return candidates, []


def _image_optimizer_context(payload: NormalizedPayload, candidates: list[ImageCandidate]) -> str:
    context = {
        "tool_name": payload.tool_name,
        "event": payload.event,
        "filenames": sorted({candidate.path.name for candidate in candidates}),
        "input_keys": sorted(str(key) for key in payload.tool_input),
    }
    return _truncate(_json_text(context), 1200)


def _trusted_uv_path(path: str | None) -> str | None:
    if not path:
        return None
    raw = Path(path).expanduser()
    try:
        raw_parent = raw.parent.resolve(strict=False)
        resolved = raw.resolve(strict=True)
    except OSError:
        return None
    if resolved.name != "uv" or not resolved.is_file():
        return None
    home = Path.home().expanduser().resolve(strict=False)
    trusted_dirs = {
        home / ".local" / "bin",
        home / ".cargo" / "bin",
        Path("/opt/homebrew/bin"),
        Path("/usr/local/bin"),
        Path("/usr/bin"),
        Path("/bin"),
    }
    homebrew_symlink_target = raw_parent in {Path("/opt/homebrew/bin"), Path("/usr/local/bin")} and (
        _path_is_inside(resolved, Path("/opt/homebrew/Cellar"))
        or _path_is_inside(resolved, Path("/usr/local/Cellar"))
    )
    try:
        if _path_is_inside(resolved, REPO_ROOT) or _path_is_inside(resolved, Path("/tmp")) or _path_is_inside(
            resolved, Path("/private/tmp")
        ):
            return None
    except OSError:
        return None
    if raw_parent not in trusted_dirs and resolved.parent not in trusted_dirs:
        return None
    try:
        path_stat = resolved.stat()
    except OSError:
        return None
    if hasattr(os, "getuid") and path_stat.st_uid not in {0, os.getuid()}:
        return None
    for parent in [resolved.parent, *resolved.parent.parents]:
        if parent == parent.parent:
            break
        try:
            parent_stat = parent.stat()
        except OSError:
            return None
        if parent_stat.st_mode & 0o002:
            return None
        if parent_stat.st_mode & 0o020 and not homebrew_symlink_target:
            return None
        if hasattr(os, "getuid") and parent_stat.st_uid not in {0, os.getuid()}:
            return None
        if parent in {home, Path("/opt"), Path("/usr"), Path("/")}:
            break
    return str(resolved)


def _uv_executable() -> str | None:
    home = Path.home().expanduser()
    candidates = [
        Path("/opt/homebrew/bin/uv"),
        Path("/usr/local/bin/uv"),
        Path("/usr/bin/uv"),
        Path("/bin/uv"),
        home / ".local" / "bin" / "uv",
        home / ".cargo" / "bin" / "uv",
    ]
    for candidate in candidates:
        trusted = _trusted_uv_path(str(candidate))
        if trusted is not None:
            return trusted
    return None


def _image_optimizer_command(uv: str | None = None) -> tuple[list[str] | None, str | None]:
    uv = uv or _uv_executable()
    if uv is None:
        return (
            None,
            (
                "Image input optimizer requires a trusted uv executable to run repo dependencies. "
                f"Install uv and run `uv sync` from {REPO_ROOT}."
            ),
        )
    return (
        [
            uv,
            "run",
            "--project",
            str(REPO_ROOT),
            "python",
            "-m",
            "wagents.image_inputs",
            "--batch-json-stdin",
        ],
        None,
    )


def _image_optimizer_env(uv_path: str | None = None) -> dict[str, str]:
    env: dict[str, str] = {}
    for key, value in os.environ.items():
        if key in IMAGE_OPTIMIZER_DANGEROUS_ENV_NAMES:
            continue
        if key.startswith(IMAGE_OPTIMIZER_DANGEROUS_ENV_PREFIXES):
            continue
        if key in IMAGE_OPTIMIZER_ALLOWED_ENV:
            env[key] = value
    path_dirs = [str(Path(uv_path).parent)] if uv_path else []
    path_dirs.extend(["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin", "/usr/sbin", "/sbin"])
    env["PATH"] = os.pathsep.join(dict.fromkeys(path_dirs))
    env["MISE_NO_CONFIG"] = "1"
    env["MISE_NO_ENV"] = "1"
    env["MISE_NO_HOOKS"] = "1"
    env["UV_NO_SYNC"] = "1"
    repo_venv = REPO_ROOT / ".venv"
    if repo_venv.is_dir():
        env["UV_PROJECT_ENVIRONMENT"] = str(repo_venv)
    tmpdir = os.environ.get("TMPDIR")
    if tmpdir:
        tmp_root, tmp_error = _safe_image_root(Path(tmpdir))
        if tmp_error is None and tmp_root is not None:
            env["TMPDIR"] = str(tmp_root)
        else:
            env.pop("TMPDIR", None)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return env


def _redact_optimizer_message(text: str) -> str:
    redacted = re.sub(r"(?i)(authorization|token|api[_-]?key|secret|password)[^,\s;]*", r"\1=<redacted>", text)
    redacted = re.sub(r"(?i)bearer\s+[a-z0-9._~+/=-]+", "Bearer <redacted>", redacted)
    return _truncate(redacted, 1200)


def _image_optimizer_batch_payload(payload: NormalizedPayload, candidates: list[ImageCandidate]) -> str:
    context = _image_optimizer_context(payload, candidates)
    batch = {
        "profile": "auto",
        "images": [
            {
                "path": str(candidate.path),
                "context": context,
                "identity": candidate.identity,
            }
            for candidate in candidates
        ],
    }
    return json.dumps(batch, separators=(",", ":"))


def _run_image_optimizer_batch_inprocess(
    candidates: list[ImageCandidate],
    payload: NormalizedPayload,
) -> tuple[list[dict[str, Any]] | None, str | None]:
    """Try in-process batch optimization before falling back to ``uv run``."""
    try:
        from wagents.image_inputs import ImageOptimizationError, optimize_image_batch_inprocess
    except ImportError:
        return None, None
    started = time.monotonic()
    try:
        data = optimize_image_batch_inprocess(json.loads(_image_optimizer_batch_payload(payload, candidates)))
    except ImageOptimizationError as exc:
        return None, str(exc)
    except Exception:
        return None, None
    elapsed = time.monotonic() - started
    if elapsed >= IMAGE_OPTIMIZER_TIMEOUT_SECONDS:
        return None, "Image optimizer exhausted the hook execution budget."
    if isinstance(data, dict) and data.get("status") != "error":
        results = data.get("results")
        if isinstance(results, list) and all(isinstance(result, dict) for result in results):
            return results, None
    if isinstance(data, dict):
        return None, _redact_optimizer_message(str(data.get("message") or data))
    return None, None


def _run_image_optimizer_batch(
    candidates: list[ImageCandidate],
    payload: NormalizedPayload,
) -> tuple[list[dict[str, Any]] | None, str | None]:
    uv = _uv_executable()
    env = _image_optimizer_env(uv)
    command, command_error = _image_optimizer_command(uv)
    if command_error is not None or command is None:
        return None, command_error
    started = time.monotonic()
    try:
        proc = subprocess.run(
            command,
            input=_image_optimizer_batch_payload(payload, candidates),
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=IMAGE_OPTIMIZER_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "Timed out while optimizing image input batch."

    elapsed = time.monotonic() - started
    if elapsed >= IMAGE_OPTIMIZER_TIMEOUT_SECONDS:
        return None, "Image optimizer exhausted the hook execution budget."

    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    if stdout:
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return None, f"Image optimizer returned invalid JSON: {_redact_optimizer_message(stdout)}"
        if isinstance(data, dict) and data.get("status") != "error":
            results = data.get("results")
            if isinstance(results, list) and all(isinstance(result, dict) for result in results):
                return results, None
            return None, "Image optimizer returned a malformed batch result."
        if isinstance(data, dict):
            return None, _redact_optimizer_message(str(data.get("message") or data))
    if stderr:
        try:
            data = json.loads(stderr)
        except json.JSONDecodeError:
            return None, f"Image optimizer failed: {_redact_optimizer_message(stderr)}"
        if isinstance(data, dict):
            return None, _redact_optimizer_message(str(data.get("message") or data))
    return None, f"Image optimizer failed with exit code {proc.returncode}."


def _replace_image_paths(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, str):
        cleaned = value.strip().strip("'\"")
        return replacements.get(value) or replacements.get(cleaned) or value
    if isinstance(value, list):
        return [_replace_image_paths(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _replace_image_paths(child, replacements) for key, child in value.items()}
    return value


def _allow_image_rewrite(payload: NormalizedPayload, updated_input: dict[str, Any], reason: str) -> int:
    _record_decision(payload, IMAGE_OPTIMIZER_POLICY_ID, "rewrite", reason)
    return _emit_json({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": reason,
            "updatedInput": updated_input,
        }
    })


def _image_retry_reason(results: list[dict[str, Any]]) -> str:
    lines = []
    for result in results:
        lines.append(
            "{source} -> {optimized} ({width}x{height}, {bytes} bytes)".format(
                source=result.get("sourcePath"),
                optimized=result.get("optimizedPath"),
                width=result.get("optimizedWidth"),
                height=result.get("optimizedHeight"),
                bytes=result.get("optimizedBytes"),
            )
        )
    return (
        "Image input optimizer created cache-sized derivatives, but this harness cannot be safely rewritten "
        "in-place. Retry the tool call with the optimized image path(s): "
        + "; ".join(lines)
    )


def _policy_image_input_optimizer_guard(payload: NormalizedPayload) -> int:
    if not _tool_may_consume_image(payload):
        return 0
    # Fast-exit before any filesystem stat/resolve work (and well before the
    # `uv run` subprocess): a tool call with zero path-shaped values anywhere
    # in its payload cannot possibly reference an image, so skip
    # `_image_candidate_paths()`'s per-candidate stat/symlink/root checks
    # entirely rather than discovering that after doing the filesystem work.
    if not _candidate_paths(payload):
        return 0
    candidates, candidate_errors = _image_candidate_paths(payload)
    if candidate_errors:
        return _deny(
            payload,
            "Image input optimizer rejected unsafe image root(s): " + "; ".join(candidate_errors),
            IMAGE_OPTIMIZER_POLICY_ID,
        )
    if not candidates:
        return 0
    if len(candidates) > IMAGE_OPTIMIZER_MAX_CANDIDATES:
        return _deny(
            payload,
            (
                "Image input optimizer found "
                f"{len(candidates)} image candidates, exceeding the per-tool limit of "
                f"{IMAGE_OPTIMIZER_MAX_CANDIDATES}. Optimize images first with "
                "`uv run wagents media optimize-image <path>` and retry with the cache path(s)."
            ),
            IMAGE_OPTIMIZER_POLICY_ID,
        )

    replacements: dict[str, str] = {}
    changed_results: list[dict[str, Any]] = []
    results, error = _run_image_optimizer_batch_inprocess(candidates, payload)
    if results is None and error is None:
        results, error = _run_image_optimizer_batch(candidates, payload)
    if error is not None or results is None:
        return _deny(
            payload,
            (
                "Image input optimizer could not prepare this image before consumption. "
                f"{error or 'Unknown optimizer failure'}"
            ),
            IMAGE_OPTIMIZER_POLICY_ID,
        )
    if len(results) != len(candidates):
        return _deny(
            payload,
            "Image input optimizer returned a result count that did not match the candidate count.",
            IMAGE_OPTIMIZER_POLICY_ID,
        )
    for candidate, result in zip(candidates, results, strict=True):
        if not result.get("fits", False):
            return _deny(
                payload,
                (
                    "Image input optimizer could not reduce this image below the configured input ceiling. "
                    f"Best cache path: {result.get('optimizedPath') or 'none'}"
                ),
                IMAGE_OPTIMIZER_POLICY_ID,
            )
        if not result.get("changed"):
            continue
        optimized_path = str(result.get("optimizedPath") or "")
        if not optimized_path:
            continue
        for raw_path in candidate.raw_paths:
            replacements[raw_path] = optimized_path
            replacements[raw_path.strip().strip("'\"")] = optimized_path
        replacements[str(candidate.path)] = optimized_path
        replacements[str(candidate.path.resolve(strict=False))] = optimized_path
        changed_results.append(result)

    if not changed_results:
        return 0

    if payload.harness not in IMAGE_REWRITE_HARNESSES:
        return _deny(payload, _image_retry_reason(changed_results), IMAGE_OPTIMIZER_POLICY_ID)

    updated_input = _replace_image_paths(payload.tool_input, replacements)
    reason = "Optimized oversized image input(s) before consumption: " + ", ".join(
        str(result.get("optimizedPath")) for result in changed_results
    )
    return _allow_image_rewrite(payload, updated_input, reason)


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
    if payload.harness == "grok-build":
        if _grok_deny_payload is not None:
            return _emit_json(_grok_deny_payload(reason, policy_id="stop-truth-gate"))
        return _emit_json({"decision": "block", "reason": reason})
    if payload.harness == "cursor":
        return _emit_json({"followup_message": reason, "user_message": reason})
    if payload.harness == "gemini-cli":
        return _emit_json({"decision": "deny", "reason": reason, "suppressOutput": True})
    if payload.harness == "opencode":
        return _emit_json({
            "permission": "deny",
            "reason": reason,
            "hookSpecificOutput": {"hookEventName": "Stop", "permission": "deny"},
        })
    print(reason, file=sys.stderr)
    return 2


def _tool_name(payload: NormalizedPayload) -> str:
    return payload.tool_name.strip().lower()


def _policy_prompt_triage(payload: NormalizedPayload) -> int:
    if not _is_research_prompt(payload.prompt):
        if (
            not _forced_research_active()
            and _stored_state_active(payload)
            and _is_implementation_handoff_prompt(payload.prompt)
        ):
            _clear_state(payload)
            return _additional_context(
                payload,
                (
                    "Research hook inactive: explicit implementation handoff detected, so source-file "
                    "writes are no longer blocked by the research read-only guard for this session."
                ),
            )
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
    """Return de-duplicated candidate path strings found anywhere in ``payload``.

    Memoized on the payload instance: several policy/context functions (the
    protected-file guard, quality-check path resolution, image-candidate
    scanning) each call this for the same normalized payload, and a bundled
    chain runs more than one of them per process. The payload walk itself
    (recursive dict/list traversal plus patch-text regex scanning) is the
    expensive part, so caching it here is pure upside with no correctness
    change since the payload is never mutated after normalization.
    """
    cached = getattr(payload, "_candidate_paths_cache", None)
    if cached is not None:
        return cached
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
    payload._candidate_paths_cache = deduped
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


@lru_cache(maxsize=8)
def _git_session_context(cwd: str) -> str:
    """Return a one-line git status summary for ``cwd``, cached per process.

    ``lru_cache`` only helps within a single dispatcher run (e.g. a
    ``--bundle`` chain that touches session-start *and* subagent-start
    context for the same cwd), never across process spawns; the underlying
    ``git status`` subprocess is unavoidable for a fresh process either way.
    """
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


@lru_cache(maxsize=8)
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
    label = "Cursor" if payload.harness == "cursor" else "Codex"
    message = (
        f"{label} post-edit quality context: inspect the diff and run focused validation before final claims; "
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


def _policy_cursor_before_read_file_guard(payload: NormalizedPayload) -> int:
    if evaluate_before_read_file is None:
        return _enforce_module_load_failure(payload, "cursor-before-read-file-guard")
    reason = evaluate_before_read_file(payload.file_path)
    if reason:
        return _deny(payload, reason, "cursor-before-read-file-guard")
    return 0


_SHELL_GIT_DANGEROUS_RE = re.compile(
    r"\bgit\s+(?:push|commit|reset|rebase|filter-branch|filter-repo)\b",
    re.I,
)


def _policy_cursor_before_shell_execution_guard(payload: NormalizedPayload) -> int:
    if _tool_name(payload) not in SHELL_TOOL_NAMES and not payload.command:
        return 0
    reason = _destructive_shell_reason(payload.command)
    if not reason:
        if evaluate_git_commit_push is None:
            if _SHELL_GIT_DANGEROUS_RE.search(payload.command or ""):
                return _enforce_module_load_failure(
                    payload, "cursor-before-shell-execution-guard"
                )
        else:
            reason = evaluate_git_commit_push(payload.command)
    if reason:
        return _deny(payload, reason, "cursor-before-shell-execution-guard")
    return 0


def _policy_cursor_before_mcp_execution_guard(payload: NormalizedPayload) -> int:
    if evaluate_before_mcp_execution is None:
        return _enforce_module_load_failure(payload, "cursor-before-mcp-execution-guard")
    reason = evaluate_before_mcp_execution(payload.tool_name, payload.tool_input)
    if reason:
        return _deny(payload, reason, "cursor-before-mcp-execution-guard")
    return 0


def _policy_cursor_subagent_start_context(payload: NormalizedPayload) -> int:
    git_context = _git_session_context(payload.cwd)
    if subagent_start_context is None:
        message = f"Subagent session context: {git_context}; managed hooks source=config/hook-registry.json."
    else:
        message = subagent_start_context(git_context)
    return _additional_context(payload, message, "cursor-subagent-start-context")


def _policy_git_commit_push_guard(payload: NormalizedPayload) -> int:
    if evaluate_git_commit_push is None:
        return _enforce_module_load_failure(payload, "git-commit-push-guard")
    if _tool_name(payload) not in SHELL_TOOL_NAMES and not payload.command:
        return 0
    reason = evaluate_git_commit_push(payload.command)
    if reason:
        return _deny(payload, reason, "git-commit-push-guard")
    return 0


POLICIES = {
    "codex-session-start-context": _policy_codex_session_start_context,
    "codex-destructive-shell-guard": _policy_codex_destructive_shell_guard,
    "codex-protected-file-guard": _policy_codex_protected_file_guard,
    "codex-permission-request-guard": _policy_codex_permission_request_guard,
    "codex-post-tool-verify-context": _policy_codex_post_tool_verify_context,
    "codex-stop-truth-gate": _policy_codex_stop_truth_gate,
    "image-input-optimizer-guard": _policy_image_input_optimizer_guard,
    "cursor-session-start-context": _policy_codex_session_start_context,
    "cursor-destructive-shell-guard": _policy_codex_destructive_shell_guard,
    "cursor-protected-file-guard": _policy_codex_protected_file_guard,
    "cursor-post-tool-verify-context": _policy_codex_post_tool_verify_context,
    "cursor-after-file-edit-context": _policy_codex_post_tool_verify_context,
    "cursor-before-read-file-guard": _policy_cursor_before_read_file_guard,
    "before-read-file-guard": _policy_cursor_before_read_file_guard,
    "cursor-before-shell-execution-guard": _policy_cursor_before_shell_execution_guard,
    "cursor-before-mcp-execution-guard": _policy_cursor_before_mcp_execution_guard,
    "cursor-subagent-start-context": _policy_cursor_subagent_start_context,
    "cursor-stop-truth-gate": _policy_codex_stop_truth_gate,
    "git-commit-push-guard": _policy_git_commit_push_guard,
    "research-prompt-triage-context": _policy_prompt_triage,
    "research-readonly-write-guard": _policy_readonly_write_guard,
    "research-dangerous-shell-guard": _policy_dangerous_shell_guard,
    "research-evidence-ledger": _policy_evidence_ledger,
    "research-stop-verifier": _policy_stop_verifier,
}


def _hook_timing_enabled() -> bool:
    return os.environ.get(HOOK_TIMING_ENV) == "1"


def _record_hook_timing(
    policy_id: str,
    harness: str,
    event: str,
    duration_ms: float,
    exit_code: int,
    *,
    degraded: str | None = None,
    forwarded: bool = False,
) -> None:
    """Append one best-effort timing record when ``WAGENTS_HOOK_TIMING=1``.

    Purely observational: any failure (missing cache dir, permission error,
    concurrent writers) is swallowed so this never changes a hook's stdout or
    exit code. Behavior-neutral by default because the env var is unset in
    every rendered harness command.
    """
    if not _hook_timing_enabled():
        return
    record = {
        "timestamp": _now().isoformat(),
        "policy_id": policy_id,
        "harness": harness,
        "event": event,
        "duration_ms": round(duration_ms, 3),
        "exit_code": exit_code,
    }
    if degraded:
        record["degraded"] = degraded
    if forwarded:
        record["forwarded"] = True
    try:
        HOOK_TIMING_PATH.parent.mkdir(parents=True, exist_ok=True)
        with HOOK_TIMING_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    except OSError:
        pass


def _finalize_single_policy_dispatch(
    payload: NormalizedPayload,
    policy_id: str,
    *,
    harness: str,
    code: int,
) -> int:
    """Shared post-policy tail for a single (non-bundle) dispatch.

    Both the CLI dispatcher (``main()``) and the warm-process worker
    (``hooks/wagents-hook-worker.py::_run_request``) must apply the exact same
    tail after a single policy function returns: record an implicit "allow"
    decision when the policy did not already record one, then emit an
    explicit ``{"permission": "allow"}`` on Cursor's fail-closed
    pre-execution events when nothing was already written to stdout.
    Centralizing it here keeps the dispatcher and the worker from drifting
    (RV-005) the way they previously did with two independently maintained
    copies of this logic.
    """
    if code == 0 and not payload.decision_recorded and policy_id != "research-evidence-ledger":
        _record_decision(payload, policy_id, "allow")
    if (
        code == 0
        and harness == "cursor"
        and not _STDOUT_EMITTED
        and policy_id in CURSOR_FAIL_CLOSED_ALLOW_POLICIES
    ):
        _emit_json({"permission": "allow"})
    return code


def _load_bundle_module():
    """Load ``wagents/hooks/bundle.py`` by file path, mirroring ``_load_policy_attr``.

    Cached in ``sys.modules`` for the lifetime of the process (there is only
    ever one bundle CLI invocation per process, but caching keeps the loader
    consistent with every other by-path module load in this file).
    """
    import importlib.util

    cache_key = "_wagents_hooks_bundle"
    module = sys.modules.get(cache_key)
    if module is not None:
        return module
    path = REPO_ROOT / "wagents" / "hooks" / "bundle.py"
    spec = importlib.util.spec_from_file_location(cache_key, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load bundle module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[cache_key] = module
    spec.loader.exec_module(module)
    return module


def _load_worker_client_module():
    """Load ``hooks/wagents-hook-client.py`` by file path for standalone dispatch."""
    import importlib.util

    cache_key = "_wagents_hook_client"
    module = sys.modules.get(cache_key)
    if module is not None:
        return module
    path = REPO_ROOT / "hooks" / "wagents-hook-client.py"
    spec = importlib.util.spec_from_file_location(cache_key, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[cache_key] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(cache_key, None)
        return None
    return module


_FORWARD_TIMEOUT_MARGIN_SECONDS = 1.0


def _forward_to_worker(
    *,
    socket_path: str | None,
    request: dict[str, Any],
    timeout: float | None = None,
) -> dict[str, Any] | None:
    if socket_path is None:
        return None
    client = _load_worker_client_module()
    if client is None:
        return None
    try:
        default_timeout = float(getattr(client, "DEFAULT_FORWARD_TIMEOUT_SECONDS", 5.0))
        return client.forward_request(
            socket_path,
            request,
            timeout=default_timeout if timeout is None else timeout,
        )
    except Exception:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run repo-managed wagents hook policies.")
    parser.add_argument("policy_id", nargs="?", default=None, choices=sorted(POLICIES))
    parser.add_argument(
        "--bundle",
        default=None,
        metavar="ID1,ID2,...",
        help="Comma-separated registry policy ids to run as a single bundled dispatch.",
    )
    parser.add_argument(
        "--bundle-mode",
        default="enforce-chain",
        choices=("enforce-chain", "context-chain", "mixed"),
        help="Bundle chain semantics; see wagents/hooks/bundle.py.",
    )
    parser.add_argument(
        "--bundle-timeout",
        type=float,
        default=30.0,
        help="Wall-clock budget (seconds) for the whole --bundle chain.",
    )
    parser.add_argument(
        "--worker-socket",
        nargs="?",
        const="",
        default=None,
        help="Optional warm worker Unix socket; falls back to local dispatch when unavailable.",
    )
    parser.add_argument(
        "--forward-timeout",
        type=float,
        default=None,
        help="Registry-derived forward budget (seconds) for single-policy --worker-socket forwards.",
    )
    parser.add_argument("--harness", default="auto")
    args = parser.parse_args(argv)

    if bool(args.policy_id) == bool(args.bundle):
        parser.error("provide exactly one of a positional policy_id or --bundle")

    global _STDOUT_EMITTED
    _STDOUT_EMITTED = False
    raw = _load_payload()
    harness = _detect_harness(raw, args.harness)
    payload = _normalize(raw, harness)
    started = time.monotonic()

    if args.bundle:
        policy_ids = [token.strip() for token in args.bundle.split(",") if token.strip()]
        forwarded = _forward_to_worker(
            socket_path=args.worker_socket,
            request={
                "bundle": policy_ids,
                "harness": harness,
                "payload": raw,
                "bundle_mode": args.bundle_mode,
                "bundle_timeout": args.bundle_timeout,
            },
            timeout=float(args.bundle_timeout) + _FORWARD_TIMEOUT_MARGIN_SECONDS,
        )
        if forwarded is not None:
            stdout = str(forwarded.get("stdout") or "")
            if stdout:
                sys.stdout.write(stdout if stdout.endswith("\n") else stdout + "\n")
            code = int(forwarded.get("exit_code") or 0)
            _record_hook_timing(
                "bundle:" + "+".join(policy_ids),
                harness,
                payload.event,
                (time.monotonic() - started) * 1000,
                code,
                forwarded=True,
            )
            return code
        bundle_module = _load_bundle_module()
        code = bundle_module.run_bundle(
            policy_ids,
            harness,
            payload,
            mode=args.bundle_mode,
            timeout_seconds=args.bundle_timeout,
            dispatcher=sys.modules[__name__],
        )
        _record_hook_timing(
            "bundle:" + "+".join(policy_ids), harness, payload.event, (time.monotonic() - started) * 1000, code
        )
        return code

    forwarded = _forward_to_worker(
        socket_path=args.worker_socket,
        request={"policy_id": args.policy_id, "harness": harness, "payload": raw},
        timeout=(
            float(args.forward_timeout) + _FORWARD_TIMEOUT_MARGIN_SECONDS
            if args.forward_timeout is not None
            else None
        ),
    )
    if forwarded is not None:
        stdout = str(forwarded.get("stdout") or "")
        if stdout:
            sys.stdout.write(stdout if stdout.endswith("\n") else stdout + "\n")
        code = int(forwarded.get("exit_code") or 0)
        _record_hook_timing(
            args.policy_id,
            harness,
            payload.event,
            (time.monotonic() - started) * 1000,
            code,
            forwarded=True,
        )
        return code

    code = POLICIES[args.policy_id](payload)
    code = _finalize_single_policy_dispatch(payload, args.policy_id, harness=harness, code=code)
    _record_hook_timing(args.policy_id, harness, payload.event, (time.monotonic() - started) * 1000, code)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
