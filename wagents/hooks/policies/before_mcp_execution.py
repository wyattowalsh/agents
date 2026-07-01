"""Guard MCP tool calls (Cursor ``beforeMCPExecution`` surface).

Cursor fires ``beforeMCPExecution`` before an MCP server tool runs. This guard
denies obviously destructive MCP operations (shell/exec passthroughs carrying
dangerous commands, filesystem deletes outside the workspace) while otherwise
allowing the call.
"""

from __future__ import annotations

import re
from typing import Any

_DANGEROUS_COMMAND_RE = re.compile(
    r"(?:(?:sudo\s+)?rm\s+-[a-zA-Z]*r[a-zA-Z]*f|\bmkfs\b|\bdd\s+if=|:\(\)\s*\{|"
    r"\bgit\s+push\b[^\n|;&]*\s(?:--force\b(?!-with-lease)|-f\b))"
)
_SHELL_TOOL_HINT_RE = re.compile(r"(?:^|[._-])(?:shell|exec|command|run|bash|terminal)\b", re.IGNORECASE)
_DELETE_TOOL_HINT_RE = re.compile(r"(?:^|[._-])(?:delete|remove|rm|unlink|destroy)\b", re.IGNORECASE)

_COMMAND_KEYS = ("command", "cmd", "shell_command", "script", "args", "arguments")
_PATH_KEYS = ("path", "file", "filepath", "file_path", "target", "target_file")


def _collect_command_text(params: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in _COMMAND_KEYS:
        value = params.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
    return " ".join(parts)


def evaluate_before_mcp_execution(tool_name: str, params: dict[str, Any] | None) -> str | None:
    """Return a deny reason for a dangerous MCP tool call, else ``None``."""
    params = params or {}
    name = tool_name or ""

    command_text = _collect_command_text(params)
    if command_text and _DANGEROUS_COMMAND_RE.search(command_text):
        return (
            f"MCP tool '{name or 'unknown'}' was asked to run a destructive command. "
            "Blocked to prevent data loss; run it explicitly outside the MCP passthrough if intended."
        )

    if _SHELL_TOOL_HINT_RE.search(name) and command_text and _DANGEROUS_COMMAND_RE.search(command_text):
        return f"MCP shell tool '{name}' carries a destructive command and was blocked."

    if _DELETE_TOOL_HINT_RE.search(name):
        for key in _PATH_KEYS:
            value = params.get(key)
            if isinstance(value, str) and (value.startswith("/") or ".." in value.replace("\\", "/").split("/")):
                return (
                    f"MCP delete tool '{name}' targets an absolute or traversal path ('{value}'). "
                    "Blocked; restrict deletes to the workspace."
                )

    return None
