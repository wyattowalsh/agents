#!/usr/bin/env python3
"""Deterministic hook verification for skill-creator.

Reads hook payload JSON from stdin. Emits actionable failures to stderr and
returns exit 2 when validation should block completion.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _warn(msg: str) -> None:
    print(f"[skill-creator verify] {msg}", file=sys.stderr)


def _read_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        _warn(f"Invalid hook JSON: {exc}")
        return {}
    return data if isinstance(data, dict) else {}


def _normalize_path(raw_path: str) -> str:
    if not raw_path:
        return ""
    path = Path(raw_path)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return path.as_posix()
    return path.as_posix().lstrip("./")


def _path_from_payload(payload: dict) -> str:
    tool_input = payload.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return ""
    for key in ("file_path", "path"):
        val = tool_input.get(key)
        if isinstance(val, str) and val:
            return _normalize_path(val)
    return ""


def _run(command: list[str]) -> bool:
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if result.returncode == 0:
        return True
    _warn(f"Command failed ({result.returncode}): {' '.join(command)}")
    if result.stdout.strip():
        print(result.stdout.rstrip(), file=sys.stderr)
    if result.stderr.strip():
        print(result.stderr.rstrip(), file=sys.stderr)
    return False


def _changed_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        _warn("Could not inspect git status")
        if result.stderr.strip():
            print(result.stderr.rstrip(), file=sys.stderr)
        return []
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        raw = line[3:]
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        paths.append(_normalize_path(raw))
    return paths


def _needs_validate(path: str) -> bool:
    return path.startswith("skills/") and path.endswith("/SKILL.md")


def _needs_eval_validate(path: str) -> bool:
    return path.startswith("skills/") and "/evals/" in path and path.endswith(".json")


def _needs_hooks_validate(path: str) -> bool:
    return _needs_validate(path) or path in {
        ".claude/settings.json",
        ".claude/settings.local.json",
    }


def _run_relevant_checks(paths: list[str]) -> int:
    commands: list[list[str]] = []
    if any(_needs_validate(path) for path in paths):
        commands.append(["uv", "run", "wagents", "validate"])
    if any(_needs_eval_validate(path) for path in paths):
        commands.append(["uv", "run", "wagents", "eval", "validate"])
    if any(_needs_hooks_validate(path) for path in paths):
        commands.append(["uv", "run", "wagents", "hooks", "validate"])

    ok = True
    for command in commands:
        ok = _run(command) and ok
    return 0 if ok else 2


def cmd_post_tool_use() -> int:
    path = _path_from_payload(_read_payload())
    if not path:
        return 0
    return _run_relevant_checks([path])


def cmd_stop() -> int:
    payload = _read_payload()
    if payload.get("stop_hook_active") is True:
        return 0
    return _run_relevant_checks(_changed_paths())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify skill-creator hook edits")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("post-tool-use", help="Validate the edited hook file path")
    sub.add_parser("stop", help="Validate dirty skill/eval/hook surfaces before stopping")
    args = parser.parse_args(argv)
    if args.command == "post-tool-use":
        return cmd_post_tool_use()
    if args.command == "stop":
        return cmd_stop()
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
