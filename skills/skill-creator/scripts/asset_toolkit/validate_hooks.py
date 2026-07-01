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

SUPPORTED_HARNESSES = {"all", "codex", "claude-code", "cursor", "github-copilot", "gemini-cli"}


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


def _validate_cursor_hooks(repo_root: Path, add_error) -> None:
    path = repo_root / ".cursor" / "hooks.json"
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        add_error(".cursor/hooks.json", f"invalid JSON: {exc}")
        return
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        add_error(".cursor/hooks.json", "hooks must be a mapping")
        return
    for event, entries in hooks.items():
        source = f".cursor/hooks.json:{event}"
        if not isinstance(entries, list):
            add_error(source, "entries must be a list")
            continue
        for index, entry in enumerate(entries, 1):
            entry_source = f"{source}[{index}]"
            if not isinstance(entry, dict):
                add_error(entry_source, "entry must be a mapping")
                continue
            if "hooks" in entry:
                add_error(entry_source, "Cursor hook entries must be flat and must not contain nested hooks")
            command = entry.get("command")
            if not isinstance(command, str) or not command:
                add_error(entry_source, "Cursor hook entry command is required")
                continue
            if "${workspaceFolder}" in command:
                add_error(entry_source, "Cursor hook commands must use $CURSOR_PROJECT_DIR, not ${workspaceFolder}")


def validate_hooks(repo_root: Path, *, harness: str = "all") -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []

    def add_error(source: str, message: str) -> None:
        errors.append({"source": source, "message": message})

    if harness not in SUPPORTED_HARNESSES:
        add_error("harness", f"unsupported harness '{harness}'")
        return errors

    if harness in {"all", "claude-code"}:
        for settings_name in ["settings.json", "settings.local.json"]:
            settings_file = repo_root / ".claude" / settings_name
            if not settings_file.exists():
                continue
            try:
                data = json.loads(settings_file.read_text(encoding="utf-8"))
                hooks_dict = data.get("hooks", {})
                if hooks_dict:
                    _validate_hooks(settings_name, hooks_dict, add_error)
                    for event, entries in hooks_dict.items():
                        if not isinstance(entries, list):
                            continue
                        for index, entry in enumerate(entries, 1):
                            if not isinstance(entry, dict):
                                continue
                            entry_source = f"{settings_name}:{event}[{index}]"
                            if entry.get("bash") or entry.get("timeoutSec"):
                                add_error(
                                    entry_source,
                                    "Claude settings must not contain Copilot-style bash hook entries",
                                )
                            if "hooks" not in entry and entry.get("command"):
                                add_error(
                                    entry_source,
                                    "Claude settings must use nested hooks groups, not flat command entries",
                                )
            except json.JSONDecodeError as exc:
                add_error(settings_name, f"invalid JSON: {exc}")

    if harness in {"all", "cursor"}:
        _validate_cursor_hooks(repo_root, add_error)

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
                    _validate_hooks(f"skill:{skill_dir.name}", cast("dict", hooks_dict), add_error)
            except Exception:
                pass

    agents_dir = repo_root / "agents"
    if agents_dir.is_dir():
        for agent_file in sorted(agents_dir.glob("*.md")):
            try:
                frontmatter, _ = parse_frontmatter(agent_file.read_text(encoding="utf-8"))
                hooks_dict = frontmatter.get("hooks", {})
                if hooks_dict:
                    _validate_hooks(f"agent:{agent_file.stem}", cast("dict", hooks_dict), add_error)
            except Exception:
                pass

    hook_registry_file = repo_root / "config" / "hook-registry.json"
    if hook_registry_file.is_file():
        try:
            data = json.loads(hook_registry_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            add_error("hook-registry.json", f"invalid JSON: {exc}")
        else:
            supported_harnesses = SUPPORTED_HARNESSES - {"all"}
            hooks = data.get("hooks", [])
            if not isinstance(hooks, list):
                add_error("hook-registry.json", "hooks must be a list")
            else:
                for index, hook in enumerate(hooks, 1):
                    source = f"hook-registry.json[{index}]"
                    if not isinstance(hook, dict):
                        add_error(source, "hook entry must be a mapping")
                        continue
                    hook_dict = cast("dict[str, object]", hook)
                    harnesses = hook_dict.get("harnesses")
                    if not isinstance(harnesses, list) or not harnesses:
                        add_error(source, "harnesses must be a non-empty list")
                        continue
                    selected_harnesses = {str(item) for item in harnesses}
                    if harness != "all" and harness not in selected_harnesses:
                        continue
                    unknown = sorted(selected_harnesses - supported_harnesses)
                    if unknown:
                        add_error(source, f"unsupported harnesses: {', '.join(unknown)}")
                    hook_id = hook_dict.get("id")
                    if not isinstance(hook_id, str) or not hook_id:
                        add_error(source, "hook id is required")
                    event = hook_dict.get("logical_event")
                    if event not in KNOWN_HOOK_EVENTS:
                        add_error(source, f"unknown logical_event '{event}'")
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
    parser.add_argument("--repo-root", default="", help="Repository root to validate")
    parser.add_argument("--format", choices=["text", "json", "jsonl"], default="text")
    parser.add_argument("--harness", choices=sorted(SUPPORTED_HARNESSES), default="all", help="Harness filter")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else find_repo_root()
    if repo_root is None:
        print("Could not find repo root", file=sys.stderr)
        return 1

    errors = validate_hooks(repo_root, harness=args.harness)
    emit_validation_output(
        args.format,
        errors,
        ok_message="All hooks valid",
        fail_message="Hook validation failed",
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
