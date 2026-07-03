#!/usr/bin/env python3
"""Portable MCPHub operator preflight (registry + tracked settings)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def _make_check(name: str, status: str, summary: str, remediation: str | None = None) -> dict[str, str]:
    check = {"name": name, "status": status, "summary": summary}
    if remediation:
        check["remediation"] = remediation
    return check


def _workflow_group_ids(registry: dict[str, Any]) -> list[str]:
    groups = registry.get("mcphub", {}).get("groups", {})
    if not isinstance(groups, dict):
        return []
    return sorted(
        name
        for name, group in groups.items()
        if isinstance(group, dict) and group.get("enabled") is not False
    )


def _find_repo_root(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / "config" / "mcp-registry.json").is_file() and (candidate / "pyproject.toml").is_file():
            return candidate
    return None


def collect_checks(*, cwd: Path) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    repo_root = _find_repo_root(cwd)
    if repo_root is None:
        checks.append(
            _make_check(
                "repo-root",
                "fail",
                "Could not locate agents repo root from cwd",
                "Run from the repo or pass --cwd pointing at the clone.",
            )
        )
        return checks

    checks.append(_make_check("repo-root", "ok", f"Using repo root {repo_root}"))

    registry_path = repo_root / "config" / "mcp-registry.json"
    settings_path = repo_root / "mcp" / "mcphub" / "mcp_settings.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    mcphub = registry.get("mcphub", {})
    if not isinstance(mcphub, dict) or mcphub.get("enabled") is not True:
        checks.append(_make_check("mcphub-enabled", "warn", "MCPHub disabled in registry"))
        return checks

    checks.append(_make_check("mcphub-enabled", "ok", "MCPHub enabled in registry"))

    sys.path.insert(0, str(repo_root))
    try:
        from scripts.generate_mcphub_settings import generate_settings, serialize_settings
        from scripts.mcphub.validate_settings import validate_settings
    except ImportError as exc:
        checks.append(
            _make_check(
                "imports",
                "fail",
                f"Unable to import repo MCPHub helpers: {exc}",
                "Run from a dev clone with uv sync completed.",
            )
        )
        return checks

    generated = generate_settings(registry)
    smart = generated.get("systemConfig", {}).get("smartRouting", {})
    if isinstance(smart, dict) and smart.get("enabled") is False:
        checks.append(_make_check("smart-routing-off", "ok", "Tracked smartRouting.enabled is false"))
    else:
        checks.append(
            _make_check(
                "smart-routing-off",
                "fail",
                "Tracked settings must keep smartRouting.enabled false",
                "Regenerate settings: just mcphub-generate",
            )
        )

    if settings_path.is_file():
        committed = json.loads(settings_path.read_text(encoding="utf-8"))
        if serialize_settings(generated) == serialize_settings(committed):
            checks.append(_make_check("settings-parity", "ok", "mcp_settings.json matches registry generator"))
        else:
            checks.append(
                _make_check(
                    "settings-parity",
                    "fail",
                    "mcp_settings.json is stale vs registry",
                    "Run: just mcphub-generate",
                )
            )
        validation_errors = validate_settings(committed, registry)
        if validation_errors:
            checks.append(
                _make_check(
                    "settings-validate",
                    "fail",
                    "; ".join(validation_errors[:3]),
                    "Run: just mcphub-validate",
                )
            )
        else:
            checks.append(_make_check("settings-validate", "ok", "validate_settings passed"))
    else:
        checks.append(
            _make_check(
                "settings-parity",
                "fail",
                "Missing mcp/mcphub/mcp_settings.json",
                "Run: just mcphub-generate",
            )
        )

    workflow_groups = _workflow_group_ids(registry)
    checks.append(
        _make_check(
            "workflow-groups",
            "ok",
            f"{len(workflow_groups)} workflow groups defined",
        )
    )

    chatgpt = mcphub.get("clients", {}).get("chatgpt", {})
    if isinstance(chatgpt, dict) and chatgpt.get("included_groups") == ["tunnel"]:
        checks.append(_make_check("chatgpt-tunnel-only", "ok", "ChatGPT client restricted to tunnel group"))
    else:
        checks.append(
            _make_check(
                "chatgpt-tunnel-only",
                "fail",
                "ChatGPT client must include only tunnel group",
                "Edit config/mcp-registry.json mcphub.clients.chatgpt",
            )
        )

    token = os.environ.get("MCPHUB_BEARER_TOKEN", "")
    if token and not token.startswith("replace-with-local"):
        checks.append(_make_check("bearer-env", "ok", "MCPHUB_BEARER_TOKEN present in environment"))
    else:
        checks.append(
            _make_check(
                "bearer-env",
                "warn",
                "MCPHUB_BEARER_TOKEN not loaded (expected until .env.mcphub is sourced)",
                "Copy .env.mcphub.example and run just mcphub-up before smoke tests.",
            )
        )

    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MCPHub operator preflight doctor")
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args(argv)

    checks = collect_checks(cwd=args.cwd.resolve())
    failed = [check for check in checks if check["status"] == "fail"]
    payload: dict[str, Any] = {"ok": not failed, "checks": checks}

    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        for check in checks:
            print(f"{check['name']}: {check['status']} — {check['summary']}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())