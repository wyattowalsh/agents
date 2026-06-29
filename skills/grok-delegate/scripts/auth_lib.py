"""OAuth and API-key auth evaluation for grok-delegate preflight (no secret logging)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

OAUTH_KEY_PREFIX = "https://auth.x.ai::"
ALLOW_API_KEY_ENV = "GROK_DELEGATE_ALLOW_API_KEY"


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


def auth_file_path(home: Path | None = None) -> Path:
    return (home or Path.home()) / ".grok" / "auth.json"


def load_auth_document(home: Path | None = None) -> dict[str, Any] | None:
    path = auth_file_path(home)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def find_oauth_principal(data: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    for key, value in data.items():
        if not isinstance(key, str) or not key.startswith(OAUTH_KEY_PREFIX):
            continue
        if isinstance(value, dict) and value.get("refresh_token"):
            return key, value
    return None


def oauth_expiry_status(principal: dict[str, Any]) -> tuple[str, str]:
    expires_at = principal.get("expires_at")
    if expires_at is None:
        return "fail", "OAuth principal has no expires_at; run grok login before dispatch"
    try:
        expiry = float(expires_at)
    except (TypeError, ValueError):
        return "fail", "OAuth expires_at is not numeric; run grok login before dispatch"
    now = time.time()
    if expiry <= now:
        return "fail", "OAuth access token expired; refresh required before dispatch"
    return "ok", "OAuth token expiry is in the future"


def api_key_opted_in() -> bool:
    return os.environ.get(ALLOW_API_KEY_ENV, "").strip() in {"1", "true", "yes"}


def collect_auth_checks(*, home: Path | None = None) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    data = load_auth_document(home)

    if data is None:
        checks.append(
            _make_check(
                "grok-auth-file",
                "fail",
                f"Auth file missing at {auth_file_path(home)}",
                "Run grok login (or grok login --device-auth in headless contexts).",
            )
        )
        checks.append(
            _make_check(
                "grok-auth-oauth",
                "fail",
                "No OAuth principal in auth store",
                "Run grok login to authenticate with SuperGrok OAuth.",
            )
        )
        checks.append(
            _make_check(
                "grok-auth-policy",
                "fail",
                "OAuth login required; API key fallback not configured",
                "Run grok login. Set XAI_API_KEY only when the user explicitly requests API-key billing.",
            )
        )
        return checks

    checks.append(_make_check("grok-auth-file", "ok", f"Auth file present at {auth_file_path(home)}"))

    oauth = find_oauth_principal(data)
    if oauth:
        _, principal = oauth
        checks.append(
            _make_check(
                "grok-auth-oauth",
                "ok",
                "OAuth principal with refresh_token present",
            )
        )
        expiry_status, expiry_summary = oauth_expiry_status(principal)
        checks.append(
            _make_check(
                "grok-auth-expiry",
                expiry_status,
                expiry_summary,
                "Run grok login to refresh OAuth tokens." if expiry_status != "ok" else None,
            )
        )
        checks.append(_make_check("grok-auth-mode", "ok", "auth mode: oauth"))
        checks.append(_make_check("grok-auth-policy", "ok", "OAuth-primary policy satisfied"))
        return checks

    has_api_key = bool(os.environ.get("XAI_API_KEY", "").strip())
    if has_api_key and api_key_opted_in():
        checks.append(
            _make_check(
                "grok-auth-oauth",
                "warn",
                "No OAuth principal; using explicit API-key fallback",
                "Prefer grok login for SuperGrok OAuth billing.",
            )
        )
        checks.append(_make_check("grok-auth-expiry", "ok", "API-key mode (no OAuth expiry)"))
        checks.append(_make_check("grok-auth-mode", "ok", "auth mode: api_key_fallback"))
        checks.append(
            _make_check(
                "grok-auth-policy",
                "ok",
                f"API-key fallback allowed via {ALLOW_API_KEY_ENV}",
            )
        )
        return checks

    if has_api_key:
        checks.append(
            _make_check(
                "grok-auth-oauth",
                "fail",
                "XAI_API_KEY is set but OAuth principal is missing",
                "Run grok login for OAuth, or set GROK_DELEGATE_ALLOW_API_KEY=1 only when the user explicitly requests API-key billing.",
            )
        )
    else:
        checks.append(
            _make_check(
                "grok-auth-oauth",
                "fail",
                "No OAuth principal in auth store",
                "Run grok login (or grok login --device-auth).",
            )
        )

    checks.append(
        _make_check(
            "grok-auth-expiry",
            "fail",
            "Cannot evaluate expiry without OAuth principal",
            "Run grok login.",
        )
    )
    checks.append(_make_check("grok-auth-mode", "fail", "auth mode: unauthenticated"))
    checks.append(
        _make_check(
            "grok-auth-policy",
            "fail",
            "OAuth login required; API key fallback not opted in",
            "Run grok login. API key only when the user explicitly requests it.",
        )
    )
    return checks