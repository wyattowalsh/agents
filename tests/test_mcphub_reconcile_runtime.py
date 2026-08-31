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


def _tracked_contract() -> dict[str, object]:
    return {
        "mcpServers": {
            "things-core": {
                "groupOnly": True,
                "tools": ["get_projects"],
                "toolApprovals": {"get_projects": "never"},
            }
        },
        "groups": [
            {
                "name": "things",
                "servers": [{"name": "things-core"}],
                "contract": {"toolCount": 70},
            }
        ],
        "thingsContract": {
            "version": 1,
            "group": "things",
            "tools": [{"publicToolName": "things_get_projects"}],
        },
        "systemConfig": {"theme": "dark"},
    }


def test_merge_replaces_old_bearers_and_preserves_non_bearer_auth() -> None:
    module = _module()
    tracked = _tracked_contract()
    tracked["bearerKeys"] = [{"token": "tracked-old-bearer"}]
    current = {
        "mcpServers": {"stale": {}},
        "thingsContract": {"version": 0},
        "bearerKeys": [{"token": "runtime-old-bearer"}, {"token": "another-old-bearer"}],
        "oauthClients": [{"clientSecret": "client-secret"}],
        "oauthTokens": [{"accessToken": "oauth-secret"}],
        "users": [{"passwordHash": "user-secret"}],
    }

    merged = module.merge_runtime_settings(tracked, current, bearer_token="current-bearer")

    assert merged["mcpServers"] == tracked["mcpServers"]
    assert merged["groups"] == tracked["groups"]
    assert merged["thingsContract"] == tracked["thingsContract"]
    assert "stale" not in merged["mcpServers"]
    assert merged["bearerKeys"] == [
        {
            "id": module.LOCAL_BEARER_KEY_ID,
            "name": "local-control-plane",
            "token": "current-bearer",
            "enabled": True,
            "kind": "system",
            "accessType": "all",
            "allowedGroups": [],
            "allowedServers": [],
        }
    ]
    for name in module.PRESERVED_AUTH_COLLECTIONS:
        assert merged[name] == current[name]
    serialized = json.dumps(merged)
    for old_bearer in ("tracked-old-bearer", "runtime-old-bearer", "another-old-bearer"):
        assert old_bearer not in serialized


def test_merge_rejects_malformed_local_auth_collection() -> None:
    module = _module()

    with pytest.raises(ValueError, match="runtime oauthTokens must be a JSON array"):
        module.merge_runtime_settings({}, {"oauthTokens": {}}, bearer_token="current-bearer")


@pytest.mark.parametrize("token", ["", "   ", "replace-with-local-secret", "${MCPHUB_BEARER_TOKEN}"])
def test_merge_requires_a_current_non_placeholder_bearer(token: str) -> None:
    module = _module()

    with pytest.raises(ValueError, match="current local bearer token is required"):
        module.merge_runtime_settings(_tracked_contract(), {}, bearer_token=token)


def test_empty_runtime_bootstraps_one_local_control_plane_bearer() -> None:
    module = _module()
    merged = module.merge_runtime_settings(
        _tracked_contract(),
        {},
        bearer_token="runtime-bearer-secret",
    )

    keys = merged["bearerKeys"]
    assert len(keys) == 1
    assert keys[0]["token"] == "runtime-bearer-secret"
    assert keys[0]["accessType"] == "all"
    assert keys[0]["enabled"] is True


def test_cli_writes_private_file_without_printing_secret(tmp_path: Path) -> None:
    tracked = tmp_path / "tracked.json"
    runtime = tmp_path / "runtime.json"
    tracked.write_text(json.dumps(_tracked_contract()), encoding="utf-8")
    runtime.write_text(
        json.dumps({
            "bearerKeys": [{"token": "old-runtime-bearer"}],
            "oauthClients": [{"clientSecret": "client-secret"}],
            "oauthTokens": [{"accessToken": "oauth-secret"}],
            "users": [{"passwordHash": "user-secret"}],
        }),
        encoding="utf-8",
    )
    runtime.chmod(0o600)
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
    assert payload["thingsContract"] == _tracked_contract()["thingsContract"]
    assert payload["bearerKeys"][0]["token"] == token
    assert payload["oauthClients"][0]["clientSecret"] == "client-secret"
    assert payload["oauthTokens"][0]["accessToken"] == "oauth-secret"
    assert payload["users"][0]["passwordHash"] == "user-secret"
    assert runtime.stat().st_mode & 0o777 == 0o600
    backup = runtime.with_name(f"{runtime.name}.bak")
    assert not backup.exists()
    assert "old-runtime-bearer" not in runtime.read_text(encoding="utf-8")
    combined_output = result.stdout + result.stderr
    for secret in (token, "old-runtime-bearer", "client-secret", "oauth-secret", "user-secret"):
        assert secret not in combined_output


def test_check_mode_reports_drift_without_writing_or_backing_up(tmp_path: Path) -> None:
    tracked = tmp_path / "tracked.json"
    runtime = tmp_path / "runtime.json"
    tracked.write_text(json.dumps(_tracked_contract()), encoding="utf-8")
    runtime.write_bytes(b'{"mcpServers":{"stale":{}},"bearerKeys":[]}\n')
    runtime.chmod(0o600)
    before = runtime.read_bytes()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--tracked",
            str(tracked),
            "--runtime",
            str(runtime),
            "--check",
        ],
        env={**os.environ, "MCPHUB_BEARER_TOKEN": "current-bearer"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "runtime settings drift detected" in result.stderr
    assert runtime.read_bytes() == before
    assert not runtime.with_name(f"{runtime.name}.bak").exists()


def test_check_mode_accepts_equal_settings_without_replacing_bytes(tmp_path: Path) -> None:
    module = _module()
    tracked = tmp_path / "tracked.json"
    runtime = tmp_path / "runtime.json"
    tracked_payload = _tracked_contract()
    payload = module.merge_runtime_settings(tracked_payload, {}, bearer_token="current-bearer")
    tracked.write_text(json.dumps(tracked_payload), encoding="utf-8")
    runtime.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    runtime.chmod(0o600)
    before = runtime.read_bytes()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--tracked",
            str(tracked),
            "--runtime",
            str(runtime),
            "--check",
        ],
        env={**os.environ, "MCPHUB_BEARER_TOKEN": "current-bearer"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "runtime settings are reconciled" in result.stdout
    assert runtime.read_bytes() == before
    assert not runtime.with_name(f"{runtime.name}.bak").exists()


def test_existing_full_private_backup_blocks_reconcile_without_writing(tmp_path: Path) -> None:
    tracked = tmp_path / "tracked.json"
    runtime = tmp_path / "runtime.json"
    backup = runtime.with_name(f"{runtime.name}.bak")
    tracked.write_text(json.dumps(_tracked_contract()), encoding="utf-8")
    runtime.write_bytes(b'{"bearerKeys":[{"token":"old-runtime-bearer"}]}\n')
    runtime.chmod(0o600)
    before = runtime.read_bytes()
    backup.write_bytes(b'{"bearerKeys":[{"token":"older-backed-up-bearer"}]}\n')
    backup.chmod(0o600)

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--tracked", str(tracked), "--runtime", str(runtime)],
        env={**os.environ, "MCPHUB_BEARER_TOKEN": "current-bearer"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert runtime.read_bytes() == before
    assert "old-runtime-bearer" not in result.stdout + result.stderr
    assert "older-backed-up-bearer" not in result.stdout + result.stderr
    assert backup.exists()


def test_shell_wrapper_requires_current_bearer_and_advertises_no_backup() -> None:
    wrapper = (ROOT / "scripts" / "mcphub" / "reconcile-runtime.sh").read_text(encoding="utf-8")

    assert "mcphub_load_env\nmcphub_require_token" in wrapper
    assert "never writes a full private backup" in wrapper
