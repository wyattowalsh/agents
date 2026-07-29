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

# Buckets emitted by skills sync (legacy lists or compact count/sample objects).
# Optional keys are validated when present so Wave 1b+ compact JSON stays compatible.
REQUIRED_BUCKET_KEYS = ("missing", "already_present", "unresolved", "skipped")
OPTIONAL_BUCKET_KEYS = (
    "projection_ensure",
    "projection_blocked",
    "store_missing",
    "internal_projection",
    "pin_blocked",
)


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


def _bucket_shape_error(label: str, value: Any) -> str | None:
    """Return an error if value is neither a legacy list nor a compact bucket object."""
    if isinstance(value, list):
        if not all(isinstance(item, str) for item in value):
            return f"{label} list items must be strings"
        return None

    if isinstance(value, dict):
        count = value.get("count")
        if not isinstance(count, int) or count < 0:
            return f"{label} compact bucket requires non-negative int 'count'"

        # Default compact JSON: {count, sample, truncated}
        if "sample" in value:
            sample = value.get("sample")
            truncated = value.get("truncated")
            if not isinstance(sample, list) or not all(isinstance(item, str) for item in sample):
                return f"{label} compact bucket 'sample' must be a list of strings"
            if not isinstance(truncated, int) or truncated < 0:
                return f"{label} compact bucket requires non-negative int 'truncated'"
            return None

        # Verbose object form (if ever emitted): {count, items}
        if "items" in value:
            items = value.get("items")
            if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
                return f"{label} compact bucket 'items' must be a list of strings"
            return None

        return f"{label} compact bucket must include 'sample' (+ 'truncated') or 'items'"

    return f"{label} must be a list or compact {{count,sample,truncated}} object"


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

        for key in REQUIRED_BUCKET_KEYS:
            message = _bucket_shape_error(f"{label}.{key}", row.get(key))
            if message:
                errors.append(message)

        for key in OPTIONAL_BUCKET_KEYS:
            if key not in row:
                continue
            message = _bucket_shape_error(f"{label}.{key}", row.get(key))
            if message:
                errors.append(message)

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
