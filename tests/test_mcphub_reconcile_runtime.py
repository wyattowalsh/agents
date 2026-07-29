from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mcphub" / "reconcile_runtime_settings.py"


def _module():
    spec = importlib.util.spec_from_file_location("_mcphub_reconcile_runtime", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_merge_preserves_all_local_auth_and_refreshes_tracked_settings() -> None:
    module = _module()
    tracked = {"mcpServers": {"current": {}}, "systemConfig": {"theme": "dark"}}
    current = {
        "mcpServers": {"stale": {}},
        "bearerKeys": [{"token": "bearer-secret"}],
        "oauthClients": [{"clientSecret": "client-secret"}],
        "oauthTokens": [{"accessToken": "oauth-secret"}],
        "users": [{"passwordHash": "user-secret"}],
    }

    merged = module.merge_runtime_settings(tracked, current, bearer_token="unused")

    assert merged["mcpServers"] == {"current": {}}
    assert "stale" not in merged["mcpServers"]
    for name in module.LOCAL_AUTH_COLLECTIONS:
        assert merged[name] == current[name]


def test_merge_rejects_malformed_local_auth_collection() -> None:
    module = _module()

    with pytest.raises(ValueError, match="runtime oauthTokens must be a JSON array"):
        module.merge_runtime_settings({}, {"oauthTokens": {}}, bearer_token="")


def test_cli_writes_private_file_without_printing_secret(tmp_path: Path) -> None:
    tracked = tmp_path / "tracked.json"
    runtime = tmp_path / "runtime.json"
    tracked.write_text(json.dumps({"mcpServers": {"candidate": {}}}), encoding="utf-8")
    runtime.write_text(
        json.dumps(
            {
                "oauthClients": [{"clientSecret": "client-secret"}],
                "oauthTokens": [{"accessToken": "oauth-secret"}],
                "users": [{"passwordHash": "user-secret"}],
            }
        ),
        encoding="utf-8",
    )
    token = "runtime-bearer-secret"

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--tracked", str(tracked), "--runtime", str(runtime)],
        env={**os.environ, "MCPHUB_BEARER_TOKEN": token},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(runtime.read_text(encoding="utf-8"))
    assert payload["bearerKeys"][0]["token"] == token
    assert payload["oauthClients"][0]["clientSecret"] == "client-secret"
    assert payload["oauthTokens"][0]["accessToken"] == "oauth-secret"
    assert payload["users"][0]["passwordHash"] == "user-secret"
    assert runtime.stat().st_mode & 0o777 == 0o600
    combined_output = result.stdout + result.stderr
    for secret in (token, "client-secret", "oauth-secret", "user-secret"):
        assert secret not in combined_output
