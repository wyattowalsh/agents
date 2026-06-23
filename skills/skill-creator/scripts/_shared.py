"""Shared utilities for skill-creator scripts."""

from __future__ import annotations

import re
import sys

import yaml

ABSOLUTE_PATH_RE = re.compile(r"(?<!:/)(/(?:usr|tmp|home|etc|var|opt|Users|mnt|root|private)[^\s)*\]]*)")
FRONTMATTER_COMMAND_KEYS = frozenset({"command", "cmd", "entrypoint", "run", "shell"})
FRONTMATTER_COMMAND_CONTAINER_KEYS = frozenset({"commands"})
FRONTMATTER_SKILLS_PATH_RE = re.compile(r"(?<![A-Za-z0-9_./-])(?:\./)?skills/[a-z0-9][a-z0-9-]*/[^\s'\"`)]*")
FRONTMATTER_WORKSPACE_TOKEN_RE = re.compile(r"\{repo_root\}|\$\{workspaceFolder\}")


def _warn(msg: str) -> None:
    print(f"[skill-creator] {msg}", file=sys.stderr)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML between --- delimiters and the body text below."""
    if not content.startswith("---"):
        return {}, content
    m = re.search(r"\n---\s*\n", content[3:])
    if m is None:
        return {}, content
    end = 3 + m.start() + 1  # +1 for the leading \n
    try:
        fm = yaml.safe_load(content[3:end].strip())
        if not isinstance(fm, dict):
            fm = {}
    except yaml.YAMLError as exc:
        _warn(f"YAML parse error: {exc}")
        fm = {}
    return fm, content[end + 3 :].strip()


def _is_command_key(key: object) -> bool:
    normalized = str(key).replace("-", "_").lower()
    return normalized in FRONTMATTER_COMMAND_KEYS or normalized.endswith("_command") or normalized.endswith("_cmd")


def iter_frontmatter_command_strings(
    value: object,
    path: tuple[object, ...] = (),
    *,
    in_commands_container: bool = False,
):
    """Yield executable command strings from nested frontmatter values."""
    if isinstance(value, str):
        if in_commands_container or (path and _is_command_key(path[-1])):
            yield path, value
        return

    if isinstance(value, dict):
        for key, child in value.items():
            key_str = str(key)
            child_path = (*path, key_str)
            yield from iter_frontmatter_command_strings(
                child,
                child_path,
                in_commands_container=(
                    in_commands_container or key_str.replace("-", "_").lower() in FRONTMATTER_COMMAND_CONTAINER_KEYS
                ),
            )
        return

    if isinstance(value, list):
        for idx, child in enumerate(value):
            yield from iter_frontmatter_command_strings(
                child,
                (*path, idx),
                in_commands_container=in_commands_container,
            )


def format_frontmatter_path(path: tuple[object, ...]) -> str:
    """Format a nested frontmatter path for diagnostics."""
    rendered = "frontmatter"
    for part in path:
        if isinstance(part, int):
            rendered += f"[{part}]"
        else:
            rendered += f".{part}"
    return rendered


def _shorten_command(command: str, limit: int = 96) -> str:
    compact = " ".join(command.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def find_nonportable_frontmatter_commands(fm: dict) -> list[dict]:
    """Return non-portable executable command strings found in frontmatter."""
    issues: list[dict] = []
    for path, command in iter_frontmatter_command_strings(fm):
        reasons: list[str] = []
        for match in FRONTMATTER_SKILLS_PATH_RE.finditer(command):
            reasons.append(f"repo-root skill path `{match.group(0)}`")
        for match in FRONTMATTER_WORKSPACE_TOKEN_RE.finditer(command):
            reasons.append(f"workspace token `{match.group(0)}`")
        for match in ABSOLUTE_PATH_RE.finditer(command):
            reasons.append(f"absolute path `{match.group(0)}`")

        if reasons:
            issues.append({
                "path": format_frontmatter_path(path),
                "command": command,
                "summary": _shorten_command(command),
                "reasons": reasons,
            })
    return issues


def format_frontmatter_command_issues(issues: list[dict], limit: int = 5) -> str:
    """Format non-portable frontmatter command issues for check output."""
    if not issues:
        return "No non-portable frontmatter command paths found"
    rendered = []
    for issue in issues[:limit]:
        reasons = ", ".join(issue.get("reasons", []))
        rendered.append(f"{issue.get('path')}: {reasons} ({issue.get('summary')})")
    if len(issues) > limit:
        rendered.append(f"{len(issues) - limit} more")
    return "; ".join(rendered)
