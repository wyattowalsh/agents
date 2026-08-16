"""Cursor Agent CLI doctor checks for ``wagents cursor-cli doctor``."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from wagents import ROOT

AGENT_CLI_TIMEOUT_SECONDS = 15

CLI_CONFIG_TRACKED_KEYS = (
    "version",
    "editor",
    "permissions",
    "approvalMode",
    "sandbox",
    "exploreSubagentModel",
    "model",
)
PROJECT_CLI_ALLOWED_KEYS = frozenset({"permissions"})
ABOUT_PUBLIC_FIELDS = (
    "cliVersion",
    "model",
    "subscriptionTier",
    "osPlatform",
    "osArch",
    "terminalProgram",
    "shell",
)
PRESENCE_SURFACES = (
    (Path(".cursor") / "hooks.json", "cursor-cli-hooks"),
    (Path(".cursor") / "mcp.json", "cursor-cli-mcp"),
    (Path("instructions") / "cursor-cli-global.md", "cursor-cli-instructions"),
    (Path(".cursor") / "rules" / "cursor-cli.mdc", "cursor-cli-rule"),
)

_SENSITIVE_KEY_MARKERS = ("email", "token", "key", "authorization", "password", "secret")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_AUTH_HEADER_RE = re.compile(r"(?i)\bauthorization\s*[:=]\s*\S+")


def _make_check(
    name: str,
    status: str,
    summary: str,
    remediation: str | None = None,
) -> dict[str, str]:
    check = {"name": name, "status": status, "summary": summary}
    if remediation:
        check["remediation"] = remediation
    return _scrub_check(check)


def _sensitive_key(name: str) -> bool:
    lowered = name.lower()
    return any(marker in lowered for marker in _SENSITIVE_KEY_MARKERS)


def _redact_text(text: str) -> str:
    redacted = _EMAIL_RE.sub("<redacted-email>", text)
    return _AUTH_HEADER_RE.sub("Authorization: <redacted>", redacted)


def _scrub_check(check: dict[str, str]) -> dict[str, str]:
    return {key: _redact_text(value) for key, value in check.items()}


def _resolve_path(value: Path | str | None, default: Path | str) -> Path:
    if value is None:
        return Path(default)
    return Path(value)


def _run_agent_cli(binary: str, args: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            [binary, *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=AGENT_CLI_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _command_text(result: subprocess.CompletedProcess[str] | None) -> str:
    if result is None:
        return ""
    return ((result.stdout or "") or (result.stderr or "")).strip()


_VERSION_LINE = re.compile(r"\d")


def _read_version(binary: str) -> str | None:
    result = _run_agent_cli(binary, ["--version"])
    if result is None or result.returncode != 0:
        return None
    text = _redact_text((result.stdout or "").strip())
    if not text:
        return None
    first = text.splitlines()[0].strip()
    if not first or not _VERSION_LINE.search(first):
        return None
    return first


def _load_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, "missing"
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None, "unreadable"
    if not raw.strip():
        return None, "empty"
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None, "invalid JSON"
    if not isinstance(payload, dict):
        return None, "not an object"
    return payload, None


def _omit_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _omit_sensitive(item) for key, item in value.items() if not _sensitive_key(str(key))}
    if isinstance(value, list):
        return [_omit_sensitive(item) for item in value]
    if isinstance(value, str):
        return _redact_text(value)
    return value


def _safe_about_summary(payload: dict[str, Any]) -> str:
    sanitized = _omit_sensitive(payload)
    if not isinstance(sanitized, dict):
        return "about json present"
    parts: list[str] = []
    for field in ABOUT_PUBLIC_FIELDS:
        if field not in sanitized:
            continue
        value = sanitized[field]
        if value is None or isinstance(value, (dict, list)):
            continue
        parts.append(f"{field}={_redact_text(str(value))}")
    return "; ".join(parts) if parts else "about json present (no public fields)"


def _collect_binary_checks() -> tuple[list[dict[str, str]], str | None]:
    checks: list[dict[str, str]] = []
    agent_path = shutil.which("agent")
    cursor_agent_path = shutil.which("cursor-agent")

    if not agent_path and not cursor_agent_path:
        checks.append(
            _make_check(
                "cursor-cli-binary",
                "warn",
                "Neither agent nor cursor-agent found on PATH",
                "Install Cursor Agent CLI (agent / cursor-agent)",
            )
        )
        return checks, None

    if agent_path:
        checks.append(_make_check("cursor-cli-agent", "ok", f"Found at {agent_path}"))
    else:
        checks.append(_make_check("cursor-cli-agent", "warn", "agent not found on PATH"))

    if cursor_agent_path:
        checks.append(_make_check("cursor-cli-cursor-agent", "ok", f"Found at {cursor_agent_path}"))
    else:
        checks.append(_make_check("cursor-cli-cursor-agent", "warn", "cursor-agent not found on PATH"))

    binary = agent_path or cursor_agent_path
    if binary is None:
        return checks, None
    version = _read_version(binary)
    if version:
        checks.append(_make_check("cursor-cli-version", "ok", version))
    else:
        checks.append(
            _make_check(
                "cursor-cli-version",
                "warn",
                "Could not read agent --version",
            )
        )
    return checks, binary


def _collect_about_check(binary: str) -> dict[str, str] | None:
    result = _run_agent_cli(binary, ["about", "--format", "json"])
    if result is None:
        return _make_check(
            "cursor-cli-about",
            "warn",
            "agent about --format json failed to run",
        )
    raw = (result.stdout or "").strip()
    if result.returncode != 0 or not raw:
        return _make_check(
            "cursor-cli-about",
            "warn",
            "agent about --format json did not return JSON",
        )
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return _make_check(
            "cursor-cli-about",
            "warn",
            "agent about --format json was not valid JSON",
        )
    if not isinstance(payload, dict):
        return _make_check(
            "cursor-cli-about",
            "warn",
            "agent about --format json was not an object",
        )
    return _make_check("cursor-cli-about", "ok", _safe_about_summary(payload))


def _collect_project_cli_check(repo_root: Path) -> dict[str, str]:
    path = repo_root / ".cursor" / "cli.json"
    payload, error = _load_json_object(path)
    if error == "missing":
        return _make_check(
            "cursor-cli-project-config",
            "warn",
            f"missing at {path}",
        )
    if error:
        return _make_check(
            "cursor-cli-project-config",
            "warn",
            f"{error} at {path}",
        )
    assert payload is not None
    extra = sorted(key for key in payload if key not in PROJECT_CLI_ALLOWED_KEYS)
    if extra:
        return _make_check(
            "cursor-cli-project-config",
            "warn",
            f"unexpected top-level keys: {', '.join(extra)}",
            "Keep .cursor/cli.json limited to permissions",
        )
    if "permissions" not in payload:
        return _make_check(
            "cursor-cli-project-config",
            "warn",
            f"empty object at {path}",
        )
    return _make_check(
        "cursor-cli-project-config",
        "ok",
        "top-level keys: permissions",
    )


def _collect_home_config_checks(home: Path) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    path = home / ".cursor" / "cli-config.json"
    payload, error = _load_json_object(path)
    if error == "missing":
        checks.append(
            _make_check(
                "cursor-cli-home-config",
                "warn",
                f"missing at {path}",
                "User-owned file; sync will not write ~/.cursor/cli-config.json",
            )
        )
        checks.append(
            _make_check(
                "cursor-cli-explore-subagent-model",
                "warn",
                "exploreSubagentModel missing",
                "Operators SHOULD set exploreSubagentModel to inherit "
                "(user-owned; sync will not write cli-config.json)",
            )
        )
        return checks

    if error:
        checks.append(
            _make_check(
                "cursor-cli-home-config",
                "warn",
                f"{error} at {path}",
            )
        )
        return checks

    assert payload is not None
    checks.append(_make_check("cursor-cli-home-config", "ok", f"present at {path}"))
    present = [key for key in CLI_CONFIG_TRACKED_KEYS if key in payload]
    absent = [key for key in CLI_CONFIG_TRACKED_KEYS if key not in payload]
    checks.append(
        _make_check(
            "cursor-cli-home-config-keys",
            "ok",
            f"present: {', '.join(present) or '(none)'}; absent: {', '.join(absent) or '(none)'}",
        )
    )
    if "exploreSubagentModel" in payload:
        checks.append(
            _make_check(
                "cursor-cli-explore-subagent-model",
                "ok",
                "exploreSubagentModel key present",
            )
        )
    else:
        checks.append(
            _make_check(
                "cursor-cli-explore-subagent-model",
                "warn",
                "exploreSubagentModel missing",
                "Operators SHOULD set exploreSubagentModel to inherit "
                "(user-owned; sync will not write cli-config.json)",
            )
        )
    return checks


def _collect_presence_checks(repo_root: Path) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    for relative, name in PRESENCE_SURFACES:
        path = repo_root / relative
        if path.is_file():
            checks.append(_make_check(name, "ok", f"present at {path}"))
        else:
            checks.append(_make_check(name, "warn", f"missing at {path}"))
    return checks


def collect_cursor_cli_doctor_checks(
    repo_root: Path | str | None = None,
    home: Path | str | None = None,
) -> list[dict[str, str]]:
    """Collect read-only Cursor Agent CLI doctor checks."""
    root = _resolve_path(repo_root, ROOT)
    home_dir = _resolve_path(home, Path.home())
    checks, binary = _collect_binary_checks()
    if binary:
        about_check = _collect_about_check(binary)
        if about_check is not None:
            checks.append(about_check)
    checks.append(_collect_project_cli_check(root))
    checks.extend(_collect_home_config_checks(home_dir))
    checks.extend(_collect_presence_checks(root))
    return checks


def cursor_cli_doctor_report(
    repo_root: Path | str | None = None,
    home: Path | str | None = None,
) -> dict[str, Any]:
    """Build a machine-readable Cursor Agent CLI doctor report."""
    checks = collect_cursor_cli_doctor_checks(repo_root=repo_root, home=home)
    counts = {
        "ok": sum(1 for check in checks if check["status"] == "ok"),
        "warn": sum(1 for check in checks if check["status"] == "warn"),
        "fail": sum(1 for check in checks if check["status"] == "fail"),
    }
    return {
        "ok": counts["fail"] == 0,
        "summary": {"total": len(checks), **counts},
        "checks": checks,
    }
