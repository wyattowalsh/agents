#!/usr/bin/env python3
"""Phase 2 install smoke using a disposable temp HOME directory."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _require_gate() -> None:
    if os.environ.get("INSTALL_SMOKE") != "1":
        print("Refusing phase 2 smoke: set INSTALL_SMOKE=1", file=sys.stderr)
        raise SystemExit(2)


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)


def main() -> int:
    _require_gate()

    if not (REPO_ROOT / "pyproject.toml").is_file():
        print("Could not locate repository root", file=sys.stderr)
        return 1

    temp_home = tempfile.mkdtemp(prefix="install-smoke-home-")
    env = os.environ.copy()
    env["HOME"] = temp_home
    env.setdefault("WAGENTS_REPO_ROOT", str(REPO_ROOT))

    results: dict[str, object] = {"home": temp_home, "steps": []}
    exit_code = 0

    try:
        validate = _run(["uv", "run", "wagents", "validate"], cwd=REPO_ROOT, env=env)
        results["steps"].append(
            {
                "name": "wagents-validate",
                "exit_code": validate.returncode,
                "stderr": (validate.stderr or "").strip()[:500],
            }
        )
        exit_code = validate.returncode or exit_code

        sync = _run(
            [
                "uv",
                "run",
                "wagents",
                "skills",
                "sync",
                "--dry-run",
                "--format",
                "json",
                "--agent",
                "codex",
            ],
            cwd=REPO_ROOT,
            env=env,
        )
        sync_ok = False
        sync_errors: list[str] = []
        if sync.returncode in (0, 1) and sync.stdout.strip():
            try:
                payload = json.loads(sync.stdout)
                sync_ok = bool(payload.get("ok"))
                if not sync_ok:
                    sync_errors.append("skills sync ok=false")
            except json.JSONDecodeError:
                sync_errors.append("skills sync returned invalid JSON")
        else:
            sync_errors.append((sync.stderr or sync.stdout or "skills sync failed").strip()[:500])

        results["steps"].append(
            {
                "name": "skills-sync-dry-run",
                "exit_code": sync.returncode,
                "ok": sync_ok,
                "errors": sync_errors,
            }
        )
        if sync.returncode not in (0, 1) or not sync_ok:
            exit_code = 1
    finally:
        shutil.rmtree(temp_home, ignore_errors=True)

    results["ok"] = exit_code == 0
    print(json.dumps(results, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
