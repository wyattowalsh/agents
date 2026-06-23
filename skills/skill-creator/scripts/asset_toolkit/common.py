"""Shared helpers for portable skill asset tooling."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

KEBAB_CASE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")

KNOWN_HOOK_EVENTS = {
    "SessionStart",
    "sessionStart",
    "UserPromptSubmit",
    "beforeSubmitPrompt",
    "userPromptSubmitted",
    "PreToolUse",
    "PermissionRequest",
    "PostToolUse",
    "PostToolUseFailure",
    "Notification",
    "SubagentStart",
    "SubagentStop",
    "Stop",
    "stop",
    "TeammateIdle",
    "TaskCompleted",
    "ConfigChange",
    "WorktreeCreate",
    "WorktreeRemove",
    "PreCompact",
    "SessionEnd",
}


def _warn(msg: str) -> None:
    print(f"[asset-toolkit] {msg}", file=sys.stderr)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML between --- delimiters and the body text below."""
    if not content.startswith("---"):
        return {}, content
    match = re.search(r"\n---\s*\n", content[3:])
    if match is None:
        return {}, content
    end = 3 + match.start() + 1
    try:
        frontmatter = yaml.safe_load(content[3:end].strip())
        if not isinstance(frontmatter, dict):
            frontmatter = {}
    except yaml.YAMLError as exc:
        _warn(f"YAML parse error: {exc}")
        frontmatter = {}
    return frontmatter, content[end + 3 :].strip()


def find_repo_root(start: Path | None = None) -> Path | None:
    """Walk parents for a repo root containing skills/."""
    current = (start or Path.cwd()).resolve()
    for path in [current, *current.parents]:
        skills_dir = path / "skills"
        if skills_dir.is_dir():
            return path
    return None


def to_title(name: str) -> str:
    return name.replace("-", " ").title()


def format_error(source: str, message: str) -> str:
    """Render a validation-style error for text output."""
    return f"{source}: {message}"


def emit_validation_output(
    format_: str,
    errors: list[dict[str, str]],
    *,
    ok_message: str = "All validations passed",
    fail_message: str = "Validation failed",
) -> None:
    """Emit validation results in text, json, or jsonl format."""
    normalized = format_.lower()
    message = ok_message if not errors else fail_message
    if normalized == "json":
        payload: dict[str, Any] = {
            "ok": not errors,
            "error_count": len(errors),
            "errors": errors,
            "message": message,
        }
        print(json.dumps(payload, indent=2))
        return
    if normalized == "jsonl":
        for error in errors:
            print(json.dumps({"type": "error", **error}))
        print(
            json.dumps({
                "type": "summary",
                "ok": not errors,
                "error_count": len(errors),
                "message": message,
            })
        )
        return
    if errors:
        for error in errors:
            print(format_error(error["source"], error["message"]))
    else:
        print(ok_message)
