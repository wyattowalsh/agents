"""Grok Build doctor checks for wagents grok doctor."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from wagents.platforms.base import REPO_ROOT
from wagents.platforms.grok import (
    GROK_BINARY_PATH,
    GROK_CONFIG_PATH,
    GROK_CONFIG_POLICY_PATH,
    GROK_CONFIG_REPO_PATH,
    GROK_MCP_BEGIN,
    GROK_PLANNOTATOR_HOOKS_PATH,
    GROK_POLICY_BEGIN,
    PLANNOTATOR_BIN_PATH,
    PLANNOTATOR_CORE_SKILLS,
    missing_plannotator_core_skills,
    resolve_plannotator_binary,
)

GROK_ENV_VARS = ("GROK_WEB_FETCH", "GROK_MEMORY", "GROK_SUBAGENTS", "GROK_LSP_TOOLS")


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


def collect_grok_doctor_checks(home: Path | None = None) -> list[dict[str, str]]:
    """Collect structured Grok Build doctor checks."""
    home = home or Path.home()
    checks: list[dict[str, str]] = []

    binary = shutil.which("grok") or (str(GROK_BINARY_PATH) if GROK_BINARY_PATH.exists() else None)
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

    for label, cfg, check_name in (
        ("home config", GROK_CONFIG_PATH, "grok-home-config"),
        ("repo project config", GROK_CONFIG_REPO_PATH, "grok-repo-config"),
        ("policy template", GROK_CONFIG_POLICY_PATH, "grok-policy-template"),
    ):
        if cfg.exists():
            checks.append(_make_check(check_name, "ok", f"{label} present at {cfg}"))
        else:
            checks.append(
                _make_check(
                    check_name,
                    "warn" if check_name != "grok-home-config" else "fail",
                    f"{label} missing at {cfg}",
                    "Run sync with --platforms grok when appropriate.",
                )
            )

    if GROK_CONFIG_PATH.exists():
        content = GROK_CONFIG_PATH.read_text(encoding="utf-8")
        has_mcp_managed = GROK_MCP_BEGIN in content
        has_policy_managed = GROK_POLICY_BEGIN in content
        has_mcphub = "mcp_servers.mcphub_group_harness-safe" in content

        if has_mcp_managed:
            checks.append(_make_check("grok-mcp-managed-block", "ok", "MCP managed block present"))
        elif has_mcphub:
            checks.append(
                _make_check(
                    "grok-mcp-managed-block",
                    "warn",
                    "MCP tables present without managed markers",
                    "Run sync with --platforms grok --targets home",
                )
            )
        else:
            checks.append(
                _make_check(
                    "grok-mcp-managed-block",
                    "fail",
                    "No MCPHub MCP projection found in ~/.grok/config.toml",
                    "Run sync with --platforms grok --targets home",
                )
            )

        if has_policy_managed:
            checks.append(_make_check("grok-policy-managed-block", "ok", "Policy managed block present"))
        elif has_mcphub:
            checks.append(
                _make_check(
                    "grok-policy-managed-block",
                    "warn",
                    "Policy managed block missing",
                    "Run sync with --platforms grok --targets home",
                )
            )

        if has_mcphub:
            checks.append(
                _make_check(
                    "grok-mcphub-endpoint",
                    "ok",
                    "mcphub harness-safe endpoint configured",
                )
            )

    for env_name in GROK_ENV_VARS:
        value = os.environ.get(env_name)
        if value:
            checks.append(_make_check(f"grok-env-{env_name.lower()}", "ok", f"{env_name} is set"))
        else:
            checks.append(
                _make_check(
                    f"grok-env-{env_name.lower()}",
                    "warn",
                    f"{env_name} is unset",
                    "Source config/grok-env.sh in your shell",
                )
            )

    for skill_root in (home / ".grok" / "skills", home / ".claude" / "skills", REPO_ROOT / ".grok" / "skills"):
        count = len(list(skill_root.glob("*/SKILL.md"))) if skill_root.is_dir() else 0
        checks.append(
            _make_check(
                f"grok-skills-{skill_root.name}",
                "ok" if count else "warn",
                f"{count} skills at {skill_root}",
            )
        )

    preferred_plannotator = resolve_plannotator_binary()
    plannotator_bin = shutil.which("plannotator") or (
        str(preferred_plannotator) if preferred_plannotator.exists() else None
    )
    if plannotator_bin:
        checks.append(_make_check("plannotator-binary", "ok", f"Found at {plannotator_bin}"))
        version_result = subprocess.run(
            [plannotator_bin, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        version = (version_result.stdout or version_result.stderr).strip()
        if version:
            checks.append(_make_check("plannotator-version", "ok", version))
    else:
        checks.append(
            _make_check(
                "plannotator-binary",
                "warn",
                "plannotator CLI missing",
                "Run uv run wagents grok plannotator install",
            )
        )

    missing_core = missing_plannotator_core_skills(home=home)
    if missing_core:
        checks.append(
            _make_check(
                "plannotator-core-skills",
                "warn",
                f"Missing: {', '.join(missing_core)}",
                "Run uv run wagents grok plannotator install or skills sync -a grok --apply",
            )
        )
    else:
        checks.append(
            _make_check(
                "plannotator-core-skills",
                "ok",
                f"Present: {', '.join(PLANNOTATOR_CORE_SKILLS)}",
            )
        )

    if GROK_PLANNOTATOR_HOOKS_PATH.exists():
        checks.append(_make_check("plannotator-hooks", "ok", f"Hooks at {GROK_PLANNOTATOR_HOOKS_PATH}"))
        if not PLANNOTATOR_BIN_PATH.exists() and not shutil.which("plannotator"):
            checks.append(
                _make_check(
                    "plannotator-hooks-binary",
                    "warn",
                    "Plannotator hooks present but CLI binary is missing",
                )
            )
    else:
        checks.append(
            _make_check(
                "plannotator-hooks",
                "warn",
                "Plannotator hooks missing",
                "Run uv run wagents grok plannotator install --hooks",
            )
        )

    return checks


def grok_doctor_report(home: Path | None = None) -> dict[str, Any]:
    """Build machine-readable Grok doctor report."""
    checks = collect_grok_doctor_checks(home=home)
    counts = {
        "ok": sum(1 for check in checks if check["status"] == "ok"),
        "warn": sum(1 for check in checks if check["status"] == "warn"),
        "fail": sum(1 for check in checks if check["status"] == "fail"),
    }
    return {
        "ok": counts["fail"] == 0,
        "summary": {"total": len(checks), **counts},
        "checks": checks,
    }