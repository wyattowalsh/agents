#!/usr/bin/env python3
"""Run wagents skills sync --dry-run and validate JSON report shape."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

REQUIRED_TOP_KEYS = frozenset({"ok", "mode", "inventory_count", "include_installed", "agents"})
REQUIRED_AGENT_KEYS = frozenset({"agent", "missing", "already_present", "unresolved", "skipped"})


def _find_repo_root() -> Path:
    candidate = REPO_ROOT
    if (candidate / "pyproject.toml").is_file() and (candidate / "skills").is_dir():
        return candidate
    raise SystemExit("Could not locate repository root")


def _run_sync(repo_root: Path, *, agent: str | None) -> dict[str, Any]:
    command = [
        "uv",
        "run",
        "wagents",
        "skills",
        "sync",
        "--dry-run",
        "--format",
        "json",
    ]
    if agent:
        command.extend(["--agent", agent])

    result = subprocess.run(
        command,
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        print(result.stderr or result.stdout, file=sys.stderr)
        raise SystemExit(result.returncode or 1)

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON from skills sync: {exc}", file=sys.stderr)
        print(result.stdout[:2000], file=sys.stderr)
        raise SystemExit(1) from exc

    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    missing_top = sorted(REQUIRED_TOP_KEYS - set(payload))
    if missing_top:
        errors.append(f"missing top-level keys: {', '.join(missing_top)}")

    if payload.get("mode") != "dry-run":
        errors.append(f"expected mode 'dry-run', got {payload.get('mode')!r}")

    agents = payload.get("agents")
    if not isinstance(agents, list):
        errors.append("'agents' must be a list")
        return errors

    for index, row in enumerate(agents):
        label = f"agents[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label} must be an object")
            continue
        missing_agent = sorted(REQUIRED_AGENT_KEYS - set(row))
        if missing_agent:
            errors.append(f"{label} missing keys: {', '.join(missing_agent)}")
            continue
        if not isinstance(row.get("agent"), str) or not row["agent"].strip():
            errors.append(f"{label}.agent must be a non-empty string")
        for key in ("missing", "already_present", "unresolved", "skipped"):
            value = row.get(key)
            if not isinstance(value, list):
                errors.append(f"{label}.{key} must be a list")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate skills sync dry-run JSON")
    parser.add_argument("--agent", default="codex", help="Single harness to probe (default: codex)")
    parser.add_argument("--repo-root", default="", help="Repository root override")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else _find_repo_root()
    payload = _run_sync(repo_root, agent=args.agent or None)
    errors = validate_payload(payload)

    summary = {
        "ok": not errors and bool(payload.get("ok", False)),
        "mode": payload.get("mode"),
        "inventory_count": payload.get("inventory_count"),
        "agent_count": len(payload.get("agents") or []),
        "errors": errors,
        "sync_ok": bool(payload.get("ok", False)),
    }
    print(json.dumps(summary, indent=2))

    if errors:
        for message in errors:
            print(message, file=sys.stderr)
        return 1
    if not payload.get("ok", False):
        print("skills sync reported ok=false", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
