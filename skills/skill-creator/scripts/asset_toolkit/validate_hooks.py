#!/usr/bin/env python3
"""Validate hooks in skills, agents, and settings."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

_SCRIPT_ROOT = Path(__file__).resolve().parent.parent
if str(_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_ROOT))

from asset_toolkit.common import (
    KNOWN_HOOK_EVENTS,
    emit_validation_output,
    find_repo_root,
    parse_frontmatter,
)


def _validate_hooks(source: str, hooks_dict: dict, add_error) -> None:
    if not isinstance(hooks_dict, dict):
        add_error(source, "hooks must be a mapping")
        return
    for event, entries in hooks_dict.items():
        if event not in KNOWN_HOOK_EVENTS:
            add_error(source, f"unknown hook event '{event}'")
        if not isinstance(entries, list):
            add_error(source, f"entries for '{event}' must be a list")
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                add_error(source, f"each entry in '{event}' must be a mapping")
                continue
            hook_list = entry.get("hooks", [])
            if isinstance(hook_list, list) and hook_list:
                for hook_def in hook_list:
                    if not isinstance(hook_def, dict):
                        add_error(source, "each hook definition must be a mapping")
                        continue
                    handler_type = hook_def.get("type", "command")
                    if handler_type not in ("command", "prompt", "agent"):
                        add_error(source, f"unknown handler type '{handler_type}' in '{event}'")
                    if handler_type == "command" and not hook_def.get("command"):
                        add_error(source, f"command handler in '{event}' has empty command")
                    if handler_type in ("prompt", "agent") and not hook_def.get("prompt"):
                        add_error(source, f"{handler_type} handler in '{event}' has empty prompt")
            elif not isinstance(hook_list, list):
                add_error(source, f"'hooks' in '{event}' entry must be a list")
            elif "command" in entry or "prompt" in entry:
                handler_type = entry.get("type", "command")
                if handler_type not in ("command", "prompt", "agent"):
                    add_error(source, f"unknown handler type '{handler_type}' in '{event}'")
                if handler_type == "command" and not entry.get("command"):
                    add_error(source, f"command handler in '{event}' has empty command")
                if handler_type in ("prompt", "agent") and not entry.get("prompt"):
                    add_error(source, f"{handler_type} handler in '{event}' has empty prompt")


def validate_hooks(repo_root: Path) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []

    def add_error(source: str, message: str) -> None:
        errors.append({"source": source, "message": message})

    for settings_name in ["settings.json", "settings.local.json"]:
        settings_file = repo_root / ".claude" / settings_name
        if not settings_file.exists():
            continue
        try:
            data = json.loads(settings_file.read_text(encoding="utf-8"))
            hooks_dict = data.get("hooks", {})
            if hooks_dict:
                _validate_hooks(settings_name, hooks_dict, add_error)
        except json.JSONDecodeError as exc:
            add_error(settings_name, f"invalid JSON: {exc}")

    skills_dir = repo_root / "skills"
    if skills_dir.is_dir():
        for skill_dir in sorted(skills_dir.iterdir()):
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.is_file():
                continue
            try:
                frontmatter, _ = parse_frontmatter(skill_file.read_text(encoding="utf-8"))
                hooks_dict = frontmatter.get("hooks", {})
                if hooks_dict:
                    _validate_hooks(f"skill:{skill_dir.name}", cast(dict, hooks_dict), add_error)
            except Exception:
                pass

    agents_dir = repo_root / "agents"
    if agents_dir.is_dir():
        for agent_file in sorted(agents_dir.glob("*.md")):
            try:
                frontmatter, _ = parse_frontmatter(agent_file.read_text(encoding="utf-8"))
                hooks_dict = frontmatter.get("hooks", {})
                if hooks_dict:
                    _validate_hooks(f"agent:{agent_file.stem}", cast(dict, hooks_dict), add_error)
            except Exception:
                pass

    hook_registry_file = repo_root / "config" / "hook-registry.json"
    if hook_registry_file.is_file():
        try:
            data = json.loads(hook_registry_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            add_error("hook-registry.json", f"invalid JSON: {exc}")
        else:
            supported_harnesses = {"codex", "claude-code", "github-copilot", "gemini-cli"}
            hooks = data.get("hooks", [])
            if not isinstance(hooks, list):
                add_error("hook-registry.json", "hooks must be a list")
            else:
                for index, hook in enumerate(hooks, 1):
                    source = f"hook-registry.json[{index}]"
                    if not isinstance(hook, dict):
                        add_error(source, "hook entry must be a mapping")
                        continue
                    hook_dict = cast(dict[str, object], hook)
                    hook_id = hook_dict.get("id")
                    if not isinstance(hook_id, str) or not hook_id:
                        add_error(source, "hook id is required")
                    event = hook_dict.get("logical_event")
                    if event not in KNOWN_HOOK_EVENTS:
                        add_error(source, f"unknown logical_event '{event}'")
                    harnesses = hook_dict.get("harnesses")
                    if not isinstance(harnesses, list) or not harnesses:
                        add_error(source, "harnesses must be a non-empty list")
                    else:
                        unknown = sorted({str(item) for item in harnesses} - supported_harnesses)
                        if unknown:
                            add_error(source, f"unsupported harnesses: {', '.join(unknown)}")
                    command = hook_dict.get("command")
                    hook_runner = "wagents-hook.py"
                    if not isinstance(command, str) or not command:
                        add_error(source, "command is required")
                    elif f"hooks/{hook_runner}" in command and not (repo_root / "hooks" / hook_runner).exists():
                        add_error(source, f"command references missing hooks/{hook_runner}")
                    elif isinstance(command, str) and command.startswith("./hooks/"):
                        script_name = command.split()[0].removeprefix("./hooks/")
                        if not (repo_root / "hooks" / script_name).exists():
                            add_error(source, f"command references missing hooks/{script_name}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate skill and agent hooks")
    parser.add_argument("--format", choices=["text", "json", "jsonl"], default="text")
    args = parser.parse_args(argv)

    repo_root = find_repo_root()
    if repo_root is None:
        print("Could not find repo root", file=sys.stderr)
        return 1

    errors = validate_hooks(repo_root)
    emit_validation_output(
        args.format,
        errors,
        ok_message="All hooks valid",
        fail_message="Hook validation failed",
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())