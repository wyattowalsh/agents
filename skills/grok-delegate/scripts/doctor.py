#!/usr/bin/env python3
"""Portable Grok Build preflight doctor for grok-delegate (bundled, no wagents)."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

GROK_ENV_VARS = (
    ("GROK_WEB_FETCH", "grok-env-grok_web_fetch"),
    ("GROK_MEMORY", "grok-env-grok_memory"),
    ("GROK_SUBAGENTS", "grok-env-grok_subagents"),
    ("GROK_LSP_TOOLS", "grok-env-grok_lsp_tools"),
)


def _make_check(
    name: str,
    status: str,
    summary: str,
    remediation: str | None = None,
) -> dict[str, str]:
    check = {"name": name, "status": status, "summary": summary}
    if remediation:
        check["remediation"] = remediation
    return check


def _grok_binary_path() -> str | None:
    found = shutil.which("grok")
    if found:
        return found
    home_bin = Path.home() / ".grok" / "bin" / "grok"
    if home_bin.is_file() and os.access(home_bin, os.X_OK):
        return str(home_bin)
    return None


def collect_checks(*, cwd: Path) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    binary = _grok_binary_path()
    if binary:
        checks.append(_make_check("grok-binary", "ok", f"Found at {binary}"))
    else:
        checks.append(
            _make_check(
                "grok-binary",
                "fail",
                "Grok CLI binary not found",
                "Install Grok Build: https://docs.x.ai/build/overview",
            )
        )

    home_config = Path.home() / ".grok" / "config.toml"
    if home_config.is_file():
        checks.append(_make_check("grok-home-config", "ok", f"Home config present at {home_config}"))
    else:
        checks.append(
            _make_check(
                "grok-home-config",
                "fail",
                f"Home config missing at {home_config}",
                "Create ~/.grok/config.toml or sync Grok harness config.",
            )
        )

    target_config = cwd.resolve() / ".grok" / "config.toml"
    if target_config.is_file():
        checks.append(_make_check("grok-target-config", "ok", f"Target config present at {target_config}"))
    else:
        checks.append(
            _make_check(
                "grok-target-config",
                "warn",
                f"Target config missing at {target_config}",
                "Add project .grok/config.toml when delegating into this repo.",
            )
        )

    if binary:
        try:
            result = subprocess.run(
                [binary, "version"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if result.returncode == 0:
                version = (result.stdout or result.stderr).strip().splitlines()[0]
                checks.append(_make_check("grok-cli-smoke", "ok", f"version ok: {version}"))
            else:
                checks.append(
                    _make_check(
                        "grok-cli-smoke",
                        "warn",
                        "grok version command failed",
                        "Run grok login or verify XAI_API_KEY.",
                    )
                )
        except (OSError, subprocess.TimeoutExpired) as exc:
            checks.append(
                _make_check(
                    "grok-cli-smoke",
                    "warn",
                    f"grok version smoke failed: {exc}",
                    "Verify Grok CLI install and auth.",
                )
            )

    for env_name, check_name in GROK_ENV_VARS:
        if os.environ.get(env_name):
            checks.append(_make_check(check_name, "ok", f"{env_name} is set"))
        else:
            checks.append(
                _make_check(
                    check_name,
                    "warn",
                    f"{env_name} is unset",
                    f"Export {env_name} for experimental Grok features (see config/grok-env.sh in agents repo).",
                )
            )

    return checks


def build_report(checks: list[dict[str, str]]) -> dict[str, Any]:
    ok_count = sum(1 for c in checks if c["status"] == "ok")
    warn_count = sum(1 for c in checks if c["status"] == "warn")
    fail_count = sum(1 for c in checks if c["status"] == "fail")
    return {
        "ok": fail_count == 0,
        "summary": {
            "total": len(checks),
            "ok": ok_count,
            "warn": warn_count,
            "fail": fail_count,
        },
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Portable Grok Build doctor for grok-delegate")
    parser.add_argument("--format", choices=("json",), default="json")
    parser.add_argument("--cwd", type=Path, default=Path.cwd(), help="Target project for .grok/config.toml")
    args = parser.parse_args(argv)

    if args.format != "json":
        print("Only --format json is supported", file=sys.stderr)
        return 2

    report = build_report(collect_checks(cwd=args.cwd))
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())