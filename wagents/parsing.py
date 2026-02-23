"""Frontmatter parsing, fence tracking, and text transforms."""

import re
from dataclasses import dataclass

import yaml


def to_title(name: str) -> str:
    """Convert kebab-case name to Title Case."""
    return name.replace("-", " ").title()


def truncate_sentence(text: str, max_len: int) -> str:
    """Truncate at sentence boundary before max_len; fall back to word boundary with ellipsis.

    If truncation leaves an unclosed parenthesis, backs up to before the
    opening ``(`` so the result never ends mid-parenthetical.
    """
    if len(text) <= max_len:
        return text
    chunk = text[:max_len]
    # Find last sentence boundary
    result: str | None = None
    for i in range(len(chunk) - 1, -1, -1):
        if chunk[i] in ".!?":
            result = chunk[: i + 1]
            break
    # Fall back to word boundary
    if result is None:
        last_space = chunk.rfind(" ")
        result = chunk[:last_space] + "\u2026" if last_space > 0 else chunk[: max_len - 1] + "\u2026"
    # Fix unbalanced parentheses — back up to before the last unmatched '('
    if result.count("(") > result.count(")"):
        idx = result.rfind("(")
        if idx > 0:
            trimmed = result[:idx].rstrip()
            result = trimmed + "\u2026" if trimmed else result
    return result


def strip_relative_md_links(text: str) -> str:
    """Convert relative .md links [text](file.md) to just `text` (no link)."""
    return re.sub(
        r"\[([^\]]+)\]\((?!https?://|/)[^)]*\.md(?:[#?][^)]*)?\)",
        r"`\1`",
        text,
    )


class FenceTracker:
    """Track fenced code block state for fence-aware markdown processing."""

    def __init__(self) -> None:
        self._char: str | None = None
        self._count: int = 0

    @property
    def inside_fence(self) -> bool:
        return self._char is not None

    def update(self, line: str) -> bool:
        """Update state for *line*. Returns True if the line is a fence boundary."""
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent <= 3 and (stripped.startswith("```") or stripped.startswith("~~~")):
            char = stripped[0]
            count = len(stripped) - len(stripped.lstrip(char))
            if self._char is None:
                self._char = char
                self._count = count
                return True
            if char == self._char and count >= self._count:
                self._char = None
                self._count = 0
                return True
        return False


def shift_headings(body: str, levels: int = 1) -> str:
    """Shift all markdown headings down by `levels` (e.g. # -> ## when levels=1).

    Fence-aware: skips headings inside fenced code blocks.
    """
    extra = "#" * levels
    lines = body.split("\n")
    result = []
    fence = FenceTracker()

    for line in lines:
        if fence.update(line) or fence.inside_fence:
            result.append(line)
        else:
            result.append(re.sub(r"^(#{1,5})", lambda m: extra + m.group(1), line))

    return "\n".join(result)


def escape_attr(text: str) -> str:
    """Escape text for use in HTML/MDX attribute values."""
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter and return (frontmatter_dict, body)."""
    if not content.startswith("---\n"):
        raise ValueError("Invalid frontmatter: must start with '---'")
    rest = content[4:]
    end_idx = rest.find("\n---\n")
    if end_idx == -1:
        # Handle case where --- is at very end of file
        if rest.endswith("\n---"):
            end_idx = len(rest) - 3
        else:
            raise ValueError("Invalid frontmatter: missing closing '---'")
    frontmatter = yaml.safe_load(rest[:end_idx])
    body = rest[end_idx + 5 :].strip() if end_idx + 5 <= len(rest) else ""
    return frontmatter, body


# ---------------------------------------------------------------------------
# Hook extraction
# ---------------------------------------------------------------------------

KNOWN_HOOK_EVENTS = {
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PermissionRequest",
    "PostToolUse",
    "PostToolUseFailure",
    "Notification",
    "SubagentStart",
    "SubagentStop",
    "Stop",
    "TeammateIdle",
    "TaskCompleted",
    "ConfigChange",
    "WorktreeCreate",
    "WorktreeRemove",
    "PreCompact",
    "SessionEnd",
}


@dataclass
class Hook:
    """Represents a single hook definition from any source."""

    source: str  # skill/agent name or "settings.json"/"settings.local.json"
    event: str  # e.g., "PreToolUse", "PostToolUse", "Stop"
    matcher: str  # tool name pattern (empty string for "match all")
    handler_type: str  # "command", "prompt", or "agent"
    command: str  # shell command (for type=command)
    prompt: str  # prompt text (for type=prompt or type=agent)


def extract_hooks(source_name: str, hooks_dict: dict) -> list[Hook]:
    """Extract Hook objects from a hooks dictionary.

    Supports two formats per entry:

    **Standard format** (nested ``hooks`` list)::

        EventName:
          - matcher: ToolPattern
            hooks:
              - type: command
                command: "..."

    **Shorthand format** (``command``/``prompt`` directly on entry)::

        EventName:
          - matcher: ToolPattern
            command: "..."
    """
    results: list[Hook] = []
    if not isinstance(hooks_dict, dict):
        return results

    for event, entries in hooks_dict.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            matcher = str(entry.get("matcher", ""))

            # Standard format: nested "hooks" list
            hook_list = entry.get("hooks", [])
            if isinstance(hook_list, list) and hook_list:
                for hook_def in hook_list:
                    if not isinstance(hook_def, dict):
                        continue
                    handler_type = str(hook_def.get("type", "command"))
                    command = str(hook_def.get("command", ""))
                    prompt = str(hook_def.get("prompt", ""))
                    results.append(
                        Hook(
                            source=source_name,
                            event=event,
                            matcher=matcher,
                            handler_type=handler_type,
                            command=command,
                            prompt=prompt,
                        )
                    )
            # Shorthand format: command/prompt directly on the entry
            elif "command" in entry or "prompt" in entry:
                handler_type = str(entry.get("type", "command"))
                command = str(entry.get("command", ""))
                prompt = str(entry.get("prompt", ""))
                results.append(
                    Hook(
                        source=source_name,
                        event=event,
                        matcher=matcher,
                        handler_type=handler_type,
                        command=command,
                        prompt=prompt,
                    )
                )
    return results
