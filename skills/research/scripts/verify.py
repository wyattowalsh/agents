#!/usr/bin/env python3
"""Safety checks for the research skill hooks.

The research skill is read-only with respect to repository source files. This
script is intentionally small: it only verifies that tracked files under the
repo-owned research skill directory were not modified during a research run.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _read_hook_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _git_root() -> Path | None:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return Path(proc.stdout.strip())


def _tracked_status(root: Path, pathspec: str) -> str:
    proc = subprocess.run(
        ["git", "status", "--short", "--untracked-files=no", "--", pathspec],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def cmd_stop(_args: argparse.Namespace) -> int:
    payload = _read_hook_payload()
    if payload.get("stop_hook_active") is True:
        json.dump({"ok": True, "skipped": "stop_hook_active"}, sys.stdout)
        print()
        return 0

    root = _git_root()
    if root is None:
        json.dump({"ok": True, "skipped": "not_git_repo"}, sys.stdout)
        print()
        return 0

    status = _tracked_status(root, "skills/research")
    if status:
        print(
            "research skill modified tracked source files; expected journals only",
            file=sys.stderr,
        )
        json.dump({"ok": False, "dirty": status.splitlines()}, sys.stdout, indent=2)
        print()
        return 1

    json.dump({"ok": True, "checked": "skills/research"}, sys.stdout)
    print()
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify research skill hook invariants.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("stop", help="Run Stop-hook checks.")
    args = parser.parse_args()

    raise SystemExit(cmd_stop(args))


if __name__ == "__main__":
    main()
