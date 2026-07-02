#!/usr/bin/env python3
"""Bridge consistency guard: discovery + hook parity across harness projections."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BRIDGE_FILES = (
    "AGENTS.md",
    "instructions/global.md",
    "config/hook-registry.json",
    "config/harness-surface-registry.json",
    "config/hook-surface-registry.json",
)


def _run_script(script: Path, repo_root: Path, extra: list[str] | None = None) -> tuple[int, str]:
    command = [sys.executable, str(script), "--repo-root", str(repo_root)]
    if extra:
        command.extend(extra)
    proc = subprocess.run(command, text=True, capture_output=True, check=False)
    output = (proc.stdout or proc.stderr).strip()
    return proc.returncode, output


def _missing_bridge_files(repo_root: Path) -> list[str]:
    return [name for name in BRIDGE_FILES if not (repo_root / name).is_file()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bridge consistency parity guard")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    checks: list[dict[str, object]] = []
    ok = True

    missing = _missing_bridge_files(args.repo_root)
    checks.append({"id": "bridge-files", "ok": not missing, "missing": missing})
    ok = ok and not missing

    for script_name, extra in (
        ("check_discovery_parity.py", None),
        ("check_hook_discovery_parity.py", ["--check-tiers"]),
    ):
        script = args.repo_root / "scripts" / script_name
        if not script.is_file():
            checks.append({"id": script_name, "ok": False, "error": "script missing"})
            ok = False
            continue
        code, output = _run_script(script, args.repo_root, extra)
        checks.append({"id": script_name, "ok": code == 0, "output": output[:500]})
        ok = ok and code == 0

    payload = {"ok": ok, "checks": checks}
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print("bridge consistency:", "ok" if ok else "FAILED")
        for row in checks:
            status = "ok" if row.get("ok") else "FAIL"
            print(f"  [{status}] {row.get('id')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
