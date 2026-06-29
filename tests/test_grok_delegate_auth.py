"""Unit tests for grok-delegate auth_lib.py."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = REPO_ROOT / "skills" / "grok-delegate" / "scripts"
FIXTURES = REPO_ROOT / "skills" / "grok-delegate" / "fixtures"


@pytest.fixture
def auth_module():
    import sys

    sys.path.insert(0, str(SKILL_SCRIPTS))
    import importlib

    module = importlib.import_module("auth_lib")
    yield module
    sys.path.pop(0)
    sys.modules.pop("auth_lib", None)


def _home_with_fixture(tmp_path: Path, fixture_name: str) -> Path:
    home = tmp_path / "home"
    grok_dir = home / ".grok"
    grok_dir.mkdir(parents=True)
    shutil.copy(FIXTURES / fixture_name, grok_dir / "auth.json")
    return home


def test_oauth_valid_passes(auth_module, tmp_path: Path) -> None:
    home = _home_with_fixture(tmp_path, "auth-oauth-valid.json")
    checks = auth_module.collect_auth_checks(home=home)
    by_name = {c["name"]: c for c in checks}
    assert by_name["grok-auth-oauth"]["status"] == "ok"
    assert by_name["grok-auth-policy"]["status"] == "ok"


def test_oauth_missing_expiry_fails(auth_module, tmp_path: Path) -> None:
    home = _home_with_fixture(tmp_path, "auth-oauth-missing-expiry.json")
    checks = auth_module.collect_auth_checks(home=home)
    expiry = next(c for c in checks if c["name"] == "grok-auth-expiry")
    assert expiry["status"] == "fail"


def test_oauth_expired_fails(auth_module, tmp_path: Path) -> None:
    home = _home_with_fixture(tmp_path, "auth-oauth-expired.json")
    checks = auth_module.collect_auth_checks(home=home)
    expiry = next(c for c in checks if c["name"] == "grok-auth-expiry")
    assert expiry["status"] == "fail"


def test_oauth_iso_expiry_passes(auth_module) -> None:
    principal = {
        "refresh_token": "fixture-refresh-token",
        "expires_at": "2099-01-01T00:00:00.000000Z",
    }
    status, summary = auth_module.oauth_expiry_status(principal)
    assert status == "ok"
    assert "future" in summary


def test_oauth_malformed_expiry_fails(auth_module) -> None:
    principal = {
        "refresh_token": "fixture-refresh-token",
        "expires_at": "not-a-date",
    }
    status, summary = auth_module.oauth_expiry_status(principal)
    assert status == "fail"
    assert "malformed" in summary


def test_missing_auth_fails(auth_module, tmp_path: Path) -> None:
    home = tmp_path / "empty-home"
    home.mkdir()
    checks = auth_module.collect_auth_checks(home=home)
    assert any(c["name"] == "grok-auth-file" and c["status"] == "fail" for c in checks)


def test_api_key_without_opt_in_fails(auth_module, tmp_path: Path, monkeypatch) -> None:
    home = _home_with_fixture(tmp_path, "auth-api-key-only.json")
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.delenv("GROK_DELEGATE_ALLOW_API_KEY", raising=False)
    checks = auth_module.collect_auth_checks(home=home)
    policy = next(c for c in checks if c["name"] == "grok-auth-policy")
    assert policy["status"] == "fail"


def test_auth_verify_stderr_redacts_secrets() -> None:
    import re

    raw = "refresh_token: super-secret-value bearer abc123"
    patterns = [
        r"(?i)(bearer\s+)\S+",
        r"(?i)(refresh_token|access_token|api[_-]?key|xai[_-]?api[_-]?key)\s*[:=]\s*\S+",
    ]
    redacted = raw
    for pattern in patterns:
        redacted = re.sub(pattern, r"\1[REDACTED]", redacted)
    assert "super-secret-value" not in redacted
    assert "[REDACTED]" in redacted


def test_api_key_with_opt_in_ok(auth_module, tmp_path: Path, monkeypatch) -> None:
    home = _home_with_fixture(tmp_path, "auth-api-key-only.json")
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.setenv("GROK_DELEGATE_ALLOW_API_KEY", "1")
    checks = auth_module.collect_auth_checks(home=home)
    policy = next(c for c in checks if c["name"] == "grok-auth-policy")
    assert policy["status"] == "ok"
