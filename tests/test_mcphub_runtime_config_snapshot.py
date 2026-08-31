"""Hermetic tests for the non-secret MCPHub runtime/config snapshot helper."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

import pytest

from scripts.mcphub.runtime_config_snapshot import (
    SnapshotError,
    TargetSpec,
    create_snapshot,
    restore_snapshot,
    verify_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path


def _private(path: Path) -> Path:
    path.mkdir(mode=0o700)
    path.chmod(0o700)
    return path


def test_exact_snapshot_records_absence_and_restores_exact_bytes(tmp_path: Path) -> None:
    tmp_path.chmod(0o700)
    target_parent = _private(tmp_path / "targets")
    config = target_parent / "client.toml"
    absent = target_parent / "absent.json"
    original = b'bearer_token_env_var = "MCPHUB_BEARER_TOKEN"\nmode = "local"\n'
    config.write_bytes(original)
    config.chmod(0o640)
    backup = tmp_path / "backup"

    assert create_snapshot(
        backup,
        [TargetSpec(config, "exact-file"), TargetSpec(absent, "exact-file")],
    ) == {"operation": "snapshot", "entryCount": 2}
    assert verify_snapshot(backup) == {"operation": "verify", "entryCount": 2}

    manifest = json.loads((backup / "snapshot.json").read_text(encoding="utf-8"))
    present, missing = manifest["entries"]
    assert present["state"] == "present"
    assert present["sourceSize"] == len(original)
    assert present["owner"] == os.getuid()
    assert present["mode"] == 0o640
    assert missing == {"kind": "exact-file", "state": "absent", "target": str(absent)}
    assert (backup / present["artifact"]).read_bytes() == original
    assert (backup / "snapshot.json").stat().st_mode & 0o077 == 0

    config.write_text('mode = "changed"\n', encoding="utf-8")
    assert restore_snapshot(backup) == {"operation": "restore", "entryCount": 2}
    assert config.read_bytes() == original
    assert config.stat().st_mode & 0o777 == 0o640


def test_plugin_identifier_round_trips_exactly_without_weakening_secret_scan(tmp_path: Path) -> None:
    tmp_path.chmod(0o700)
    target_parent = _private(tmp_path / "targets")
    config = target_parent / "config.toml"
    original = b'[plugins."secret-guard@candidate-corpus-local"]\nenabled = true\n'
    config.write_bytes(original)
    config.chmod(0o640)
    backup = tmp_path / "backup"

    assert create_snapshot(backup, [TargetSpec(config, "exact-file")]) == {
        "operation": "snapshot",
        "entryCount": 1,
    }
    assert verify_snapshot(backup) == {"operation": "verify", "entryCount": 1}

    manifest = json.loads((backup / "snapshot.json").read_text(encoding="utf-8"))
    artifact = backup / manifest["entries"][0]["artifact"]
    assert artifact.read_bytes() == original
    assert artifact.stat().st_mode & 0o077 == 0

    config.write_text('[plugins."replacement"]\nenabled = false\n', encoding="utf-8")
    config.chmod(0o600)
    assert restore_snapshot(backup) == {"operation": "restore", "entryCount": 1}
    assert config.read_bytes() == original
    assert config.stat().st_mode & 0o777 == 0o640


@pytest.mark.parametrize("sensitive_key", ["token", "client_secret", "api_key", "authorization", "private_key"])
def test_plugin_options_still_reject_literal_credentials(tmp_path: Path, sensitive_key: str) -> None:
    tmp_path.chmod(0o700)
    target_parent = _private(tmp_path / "targets")
    config = target_parent / "config.json"
    config.write_text(
        json.dumps({"plugins": {"secret-guard@candidate-corpus-local": {sensitive_key: "literal-value"}}}),
        encoding="utf-8",
    )
    config.chmod(0o600)
    backup = tmp_path / f"backup-{sensitive_key}"

    with pytest.raises(SnapshotError, match=rf"embedded credential value is forbidden at .*\.{sensitive_key}"):
        create_snapshot(backup, [TargetSpec(config, "exact-file")])
    assert not backup.exists()


def test_structural_settings_exclude_auth_and_preserve_current_auth_on_restore(tmp_path: Path) -> None:
    tmp_path.chmod(0o700)
    target_parent = _private(tmp_path / "targets")
    settings = target_parent / "settings.json"
    settings.write_text(
        json.dumps({
            "port": 46683,
            "groups": {"things": {"enabled": True}},
            "bearerKeys": [{"value": "old-private-value"}],
            "oauthClients": [{"clientSecret": "old-oauth-value"}],
        }),
        encoding="utf-8",
    )
    settings.chmod(0o600)
    backup = tmp_path / "backup"

    create_snapshot(backup, [TargetSpec(settings, "structural-settings")])
    manifest = json.loads((backup / "snapshot.json").read_text(encoding="utf-8"))
    artifact = (backup / manifest["entries"][0]["artifact"]).read_text(encoding="utf-8")
    assert "old-private-value" not in artifact
    assert "old-oauth-value" not in artifact
    assert set(manifest["entries"][0]["excludedCollections"]) == {
        "bearerKeys",
        "oauthClients",
        "oauthTokens",
        "users",
    }

    settings.write_text(
        json.dumps({
            "port": 9999,
            "groups": {},
            "bearerKeys": [{"value": "current-private-value"}],
            "oauthClients": [{"clientSecret": "current-oauth-value"}],
        }),
        encoding="utf-8",
    )
    restore_snapshot(backup)
    restored = json.loads(settings.read_text(encoding="utf-8"))
    assert restored["port"] == 46683
    assert restored["groups"] == {"things": {"enabled": True}}
    assert restored["bearerKeys"] == [{"value": "current-private-value"}]
    assert restored["oauthClients"] == [{"clientSecret": "current-oauth-value"}]


def test_pointer_restore_is_exact_and_absent_restore_never_deletes(tmp_path: Path) -> None:
    tmp_path.chmod(0o700)
    target_parent = _private(tmp_path / "targets")
    digest = "sha256-" + "a" * 64
    (target_parent / digest).mkdir(mode=0o700)
    pointer = target_parent / "current"
    pointer.symlink_to(digest)
    missing = target_parent / "future.json"
    backup = tmp_path / "backup"
    create_snapshot(backup, [TargetSpec(pointer, "symlink"), TargetSpec(missing, "exact-file")])

    pointer.unlink()
    pointer.symlink_to("sha256-" + "b" * 64)
    missing.write_text("{}\n", encoding="utf-8")
    with pytest.raises(SnapshotError, match="refuses to delete"):
        restore_snapshot(backup)
    assert os.readlink(pointer) == "sha256-" + "b" * 64
    assert missing.exists()

    missing.unlink()
    restore_snapshot(backup)
    assert os.readlink(pointer) == digest


def test_snapshot_fails_closed_for_credential_paths_and_embedded_values(tmp_path: Path) -> None:
    tmp_path.chmod(0o700)
    target_parent = _private(tmp_path / "targets")
    embedded = target_parent / "client.json"
    embedded.write_text(json.dumps({"api_key": "private-value"}), encoding="utf-8")
    embedded.chmod(0o600)
    with pytest.raises(SnapshotError, match="embedded credential"):
        create_snapshot(tmp_path / "backup-a", [TargetSpec(embedded, "exact-file")])
    assert not (tmp_path / "backup-a").exists()

    embedded.write_text(json.dumps({"api_key": "ABC123"}), encoding="utf-8")
    with pytest.raises(SnapshotError, match="embedded credential"):
        create_snapshot(tmp_path / "backup-uppercase", [TargetSpec(embedded, "exact-file")])
    assert not (tmp_path / "backup-uppercase").exists()

    excluded = target_parent / ".env.mcphub"
    excluded.write_text("MCPHUB_BEARER_TOKEN=private-value\n", encoding="utf-8")
    excluded.chmod(0o600)
    with pytest.raises(SnapshotError, match="excluded"):
        create_snapshot(tmp_path / "backup-b", [TargetSpec(excluded, "exact-file")])
    assert not (tmp_path / "backup-b").exists()


def test_snapshot_detects_artifact_tampering(tmp_path: Path) -> None:
    tmp_path.chmod(0o700)
    target_parent = _private(tmp_path / "targets")
    config = target_parent / "client.json"
    config.write_text('{"enabled":true}\n', encoding="utf-8")
    config.chmod(0o600)
    backup = tmp_path / "backup"
    create_snapshot(backup, [TargetSpec(config, "exact-file")])
    manifest = json.loads((backup / "snapshot.json").read_text(encoding="utf-8"))
    artifact_path = backup / manifest["entries"][0]["artifact"]
    artifact_path.write_text('{"enabled":false}\n', encoding="utf-8")
    artifact_path.chmod(0o600)

    with pytest.raises(SnapshotError, match="digest or size mismatch"):
        verify_snapshot(backup)
