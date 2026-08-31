"""Hermetic proofs for MCPHub public activation, teardown, and artifact setup."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import stat
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.mcphub import configure_things_core_artifacts as artifact_config

ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / "scripts" / "mcphub" / "common.sh"
DOWN = ROOT / "scripts" / "mcphub" / "down.sh"
ACTIVATION = ROOT / "scripts" / "mcphub" / "remote-activation.mjs"
REMOTE_CONTROL = ROOT / "scripts" / "mcphub" / "remote-control.sh"
ACTIVATION_GUARD = ROOT / "scripts" / "mcphub" / "activation-expiry-guard.sh"
ENSURE_RUNNING = ROOT / "scripts" / "mcphub" / "ensure-running.sh"
ENV_EXAMPLE = ROOT / ".env.mcphub.example"
CONFORMANCE = ROOT / "mcp" / "mcphub" / "downstream" / "fixtures" / "protocol" / "conformance-report.json"


def _private_directory(path: Path) -> Path:
    path.mkdir(mode=0o700)
    path.chmod(0o700)
    return path


def _private_file(path: Path, payload: bytes) -> Path:
    path.write_bytes(payload)
    path.chmod(0o600)
    return path


def _run_activation(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", str(ACTIVATION), *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )


def _observed_wire_record(
    *,
    capture_receipt_sha256: str = "c" * 64,
    captured_at: datetime | None = None,
    evidence_ttl: timedelta = timedelta(hours=24),
    modern_discovery_observed: bool = True,
    protocol_version: str = "2026-07-28",
    registration_mode: str = "client-id-metadata-document",
) -> bytes:
    captured_at = captured_at or datetime.now(UTC)
    record: dict[str, object] = {
        "$schema": "./observed-wire-record.schema.json",
        "schemaVersion": "1.1.0",
        "status": "observed-pass",
        "capturedAt": captured_at.isoformat().replace("+00:00", "Z"),
        "expiresAt": (captured_at + evidence_ttl).isoformat().replace("+00:00", "Z"),
        "publicResource": "https://mcp.w4w.dev/mcp/things",
        "registrationMode": registration_mode,
        "redirectUri": "https://chatgpt.com/connector_platform_oauth_redirect",
        "redirectUriSha256": hashlib.sha256(b"https://chatgpt.com/connector_platform_oauth_redirect").hexdigest(),
        "mcpProtocolVersion": protocol_version,
        "modernDiscoveryObserved": modern_discovery_observed,
        "requiredIndependentScopes": ["things.read", "things.write", "things.admin"],
        "offlineAccessRequested": True,
        "offlineAccessSemantics": "refresh-only-no-things-authorization",
        "resourceIndicatorObserved": True,
        "pkceS256Observed": True,
        "captureReceiptSha256": capture_receipt_sha256,
        "routeStatuses": {
            "mcp": 401,
            "protectedResourceMetadata": 200,
            "authorizationServerMetadata": 200,
            "authorization": 503,
            "registration": None if registration_mode == "client-id-metadata-document" else 503,
        },
        "secretFree": True,
        "redactionsVerified": True,
        "prohibitedDataAbsent": True,
    }
    record["evidenceDigestSha256"] = hashlib.sha256(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _activation_fixture(tmp_path: Path) -> dict[str, Path | str]:
    tmp_path.chmod(0o700)
    runtime_root = _private_directory(tmp_path / "downstream")
    digest = "sha256-" + "a" * 64
    distribution = _private_directory(runtime_root / digest)
    _private_file(distribution / "audit-manifest.json", b'{"schemaVersion":1,"status":"sealed"}\n')
    _private_file(distribution / "things-capability-manifest.json", b'{"schemaVersion":1,"tools":[]}\n')
    (runtime_root / "current").symlink_to(digest)
    settings = _private_file(tmp_path / "mcp_settings.json", b'{"groups":[],"mcpServers":{}}\n')
    credentials = _private_file(tmp_path / "cloudflared-credentials.json", b'{"account":"redacted"}\n')
    cloudflared_config = tmp_path / "cloudflared.yml"
    rendered = _run_activation(
        "render-config",
        "--output",
        str(cloudflared_config),
        "--tunnel-name",
        "mcphub",
        "--credentials-file",
        str(credentials),
    )
    assert rendered.returncode == 0, rendered.stderr
    conformance = tmp_path / "conformance-report.json"
    conformance.write_bytes(CONFORMANCE.read_bytes())
    conformance.chmod(0o600)
    policy = _private_file(tmp_path / "oauth-policy.json", b'{"schemaVersion":1}\n')
    login = _private_file(tmp_path / "oauth-login.json", b'{"username":"opaque"}\n')
    observed = _private_file(tmp_path / "observed-wire.json", b"{}\n")
    return {
        "runtime_root": runtime_root,
        "digest": digest,
        "settings": settings,
        "credentials": credentials,
        "cloudflared_config": cloudflared_config,
        "conformance": conformance,
        "policy": policy,
        "login": login,
        "observed": observed,
    }


def _base_receipt_arguments(fixture: dict[str, Path | str], receipt: Path) -> list[str]:
    return [
        "--receipt",
        str(receipt),
        "--runtime-root",
        str(fixture["runtime_root"]),
        "--settings",
        str(fixture["settings"]),
        "--cloudflared-config",
        str(fixture["cloudflared_config"]),
        "--conformance-result",
        str(fixture["conformance"]),
    ]


def _capture_receipt_snapshot(
    fixture: dict[str, Path | str],
) -> tuple[Path, dict[str, object], str]:
    directory = Path(fixture["settings"]).parent
    receipt = directory / "capture-active.json"
    archive = directory / "capture-snapshot.json"
    issued = _run_activation(
        "issue",
        "--mode",
        "capture",
        "--ttl-seconds",
        "1800",
        "--tunnel-name",
        "mcphub",
        "--credentials-file",
        str(fixture["credentials"]),
        *(_base_receipt_arguments(fixture, receipt)),
    )
    assert issued.returncode == 0, issued.stderr
    snapshotted = _run_activation(
        "snapshot-capture",
        "--receipt",
        str(receipt),
        "--output",
        str(archive),
        "--runtime-root",
        str(fixture["runtime_root"]),
        "--settings",
        str(fixture["settings"]),
        "--cloudflared-config",
        str(fixture["cloudflared_config"]),
        "--conformance-result",
        str(fixture["conformance"]),
    )
    assert snapshotted.returncode == 0, snapshotted.stderr
    assert archive.read_bytes() == receipt.read_bytes()
    return archive, json.loads(receipt.read_text(encoding="utf-8")), hashlib.sha256(archive.read_bytes()).hexdigest()


def _capture_window(payload: dict[str, object]) -> tuple[int, int]:
    created_at = payload.get("createdAt")
    expires_at = payload.get("expiresAt")
    assert isinstance(created_at, int)
    assert isinstance(expires_at, int)
    return created_at, expires_at


def test_cloudflared_manifest_is_exact_private_and_46684_only(tmp_path: Path) -> None:
    fixture = _activation_fixture(tmp_path)
    config = Path(fixture["cloudflared_config"])
    payload = config.read_text(encoding="utf-8")

    assert config.stat().st_mode & 0o777 == 0o600
    assert "service: http://127.0.0.1:46684" in payload
    assert "127.0.0.1:46683" not in payload
    assert payload.count("  - hostname:") == 1
    assert payload.endswith("  - service: http_status:404\n")

    verified = _run_activation(
        "verify-config",
        "--input",
        str(config),
        "--tunnel-name",
        "mcphub",
        "--credentials-file",
        str(fixture["credentials"]),
    )
    assert verified.returncode == 0, verified.stderr

    config.write_text(
        payload.replace("  - service: http_status:404\n", "  - service: http://example.invalid\n"),
        encoding="utf-8",
    )
    config.chmod(0o600)
    rejected = _run_activation(
        "verify-config",
        "--input",
        str(config),
        "--tunnel-name",
        "mcphub",
        "--credentials-file",
        str(fixture["credentials"]),
    )
    assert rejected.returncode == 1


def test_capture_receipt_is_owner_only_expiring_and_digest_bound(tmp_path: Path) -> None:
    fixture = _activation_fixture(tmp_path)
    receipt = tmp_path / "capture.json"
    issued = _run_activation(
        "issue",
        "--mode",
        "capture",
        "--ttl-seconds",
        "1800",
        "--tunnel-name",
        "mcphub",
        "--credentials-file",
        str(fixture["credentials"]),
        *(_base_receipt_arguments(fixture, receipt)),
    )
    assert issued.returncode == 0, issued.stderr
    assert receipt.stat().st_mode & 0o777 == 0o600
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert payload["mode"] == "capture"
    assert payload["remotePublicReady"] is False
    assert payload["toolDispatchEnabled"] is False
    assert payload["expiresAt"] - payload["createdAt"] == 1_800_000
    assert payload["bindings"]["distributionDigest"] == fixture["digest"]
    assert payload["bindings"]["observedWireEvidenceSha256"] == "0" * 64

    verified = _run_activation("verify", *(_base_receipt_arguments(fixture, receipt)))
    assert verified.returncode == 0, verified.stderr
    assert verified.stdout == "capture\n"

    Path(fixture["settings"]).write_text('{"groups":[{"name":"drift"}]}\n', encoding="utf-8")
    Path(fixture["settings"]).chmod(0o600)
    rejected = _run_activation("verify", *(_base_receipt_arguments(fixture, receipt)))
    assert rejected.returncode == 1


def test_unexpired_poll_survives_live_runtime_settings_rewrites(tmp_path: Path) -> None:
    fixture = _activation_fixture(tmp_path)
    receipt = tmp_path / "capture.json"
    issued = _run_activation(
        "issue",
        "--mode",
        "capture",
        "--ttl-seconds",
        "1800",
        "--tunnel-name",
        "mcphub",
        "--credentials-file",
        str(fixture["credentials"]),
        *(_base_receipt_arguments(fixture, receipt)),
    )
    assert issued.returncode == 0, issued.stderr

    unexpired = _run_activation(
        "unexpired",
        "--receipt",
        str(receipt),
        "--expect-mode",
        "capture",
    )
    assert unexpired.returncode == 0, unexpired.stderr
    assert unexpired.stdout.strip() == "capture"

    settings = Path(fixture["settings"])
    settings.write_bytes(b'{"groups":[],"mcpServers":{},"oauthTokens":{"rewritten":true}}\n')
    settings.chmod(0o600)

    still_unexpired = _run_activation(
        "unexpired",
        "--receipt",
        str(receipt),
        "--expect-mode",
        "capture",
    )
    assert still_unexpired.returncode == 0, still_unexpired.stderr
    assert still_unexpired.stdout.strip() == "capture"

    drifted = _run_activation(
        "verify",
        "--expect-mode",
        "capture",
        *(_base_receipt_arguments(fixture, receipt)),
    )
    assert drifted.returncode == 1


def test_public_receipt_requires_and_rechecks_every_live_binding(tmp_path: Path) -> None:
    fixture = _activation_fixture(tmp_path)
    capture_receipt, capture_payload, capture_sha256 = _capture_receipt_snapshot(fixture)
    captured_at = datetime.now(UTC)
    capture_created_at, capture_expires_at = _capture_window(capture_payload)
    assert capture_created_at <= int(captured_at.timestamp() * 1000) <= capture_expires_at
    observed_path = Path(fixture["observed"])
    valid_observed = _observed_wire_record(
        capture_receipt_sha256=capture_sha256,
        captured_at=captured_at,
    )
    observed_path.write_bytes(valid_observed)
    observed_path.chmod(0o600)
    receipt = tmp_path / "public.json"
    issue_arguments = [
        "issue",
        "--mode",
        "public",
        "--ttl-seconds",
        "3600",
        "--registration-mode",
        "cimd",
        "--tunnel-name",
        "mcphub",
        "--credentials-file",
        str(fixture["credentials"]),
        "--oauth-policy",
        str(fixture["policy"]),
        "--oauth-login-credential",
        str(fixture["login"]),
        "--observed-wire-evidence",
        str(fixture["observed"]),
        "--capture-receipt",
        str(capture_receipt),
        *(_base_receipt_arguments(fixture, receipt)),
    ]
    observed_path.write_bytes(b'{"status":"passed"}\n')
    observed_path.chmod(0o600)
    assert _run_activation(*issue_arguments).returncode == 1
    assert not receipt.exists()
    observed_path.write_bytes(valid_observed)
    observed_path.chmod(0o600)
    issued = _run_activation(*issue_arguments)
    assert issued.returncode == 0, issued.stderr
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert payload["registrationMode"] == "cimd"
    assert payload["remotePublicReady"] is True
    assert payload["toolDispatchEnabled"] is True
    assert payload["tunnelAllowed"] is True
    assert payload["bindings"]["routeManifestSha256"] == (
        "2608092f8992d45176f378e04f8b68a1802d49283539b032bcebf8b3d5b3f173"
    )
    assert all(value != "0" * 64 for key, value in payload["bindings"].items() if key != "distributionDigest")

    verification_arguments = [
        "verify",
        "--expect-mode",
        "public",
        "--oauth-policy",
        str(fixture["policy"]),
        "--oauth-login-credential",
        str(fixture["login"]),
        "--observed-wire-evidence",
        str(fixture["observed"]),
        "--capture-receipt",
        str(capture_receipt),
        *(_base_receipt_arguments(fixture, receipt)),
    ]
    verified = _run_activation(*verification_arguments)
    assert verified.returncode == 0, verified.stderr
    Path(fixture["observed"]).write_text('{"status":"changed"}\n', encoding="utf-8")
    Path(fixture["observed"]).chmod(0o600)
    assert _run_activation(*verification_arguments).returncode == 1


def _issue_public_from_capture(
    fixture: dict[str, Path | str],
    *,
    capture_receipt: Path,
    receipt: Path,
    ttl_seconds: int,
    registration_mode: str = "cimd",
) -> subprocess.CompletedProcess[str]:
    return _run_activation(
        "issue",
        "--mode",
        "public",
        "--ttl-seconds",
        str(ttl_seconds),
        "--registration-mode",
        registration_mode,
        "--tunnel-name",
        "mcphub",
        "--credentials-file",
        str(fixture["credentials"]),
        "--oauth-policy",
        str(fixture["policy"]),
        "--oauth-login-credential",
        str(fixture["login"]),
        "--observed-wire-evidence",
        str(fixture["observed"]),
        "--capture-receipt",
        str(capture_receipt),
        *(_base_receipt_arguments(fixture, receipt)),
    )


def test_public_receipt_uses_23_hour_default_inside_24_hour_evidence_window(tmp_path: Path) -> None:
    fixture = _activation_fixture(tmp_path)
    capture_receipt, capture_payload, capture_sha256 = _capture_receipt_snapshot(fixture)
    captured_at = datetime.now(UTC)
    capture_created_at, capture_expires_at = _capture_window(capture_payload)
    assert capture_created_at <= int(captured_at.timestamp() * 1000) <= capture_expires_at
    observed = Path(fixture["observed"])
    observed.write_bytes(_observed_wire_record(capture_receipt_sha256=capture_sha256, captured_at=captured_at))
    observed.chmod(0o600)

    too_long = _issue_public_from_capture(
        fixture,
        capture_receipt=capture_receipt,
        receipt=tmp_path / "public-24h.json",
        ttl_seconds=86_400,
    )
    assert too_long.returncode == 1
    accepted_receipt = tmp_path / "public-23h.json"
    accepted = _issue_public_from_capture(
        fixture,
        capture_receipt=capture_receipt,
        receipt=accepted_receipt,
        ttl_seconds=82_800,
    )
    assert accepted.returncode == 0, accepted.stderr
    assert json.loads(accepted_receipt.read_text(encoding="utf-8"))["expiresAt"] <= int(
        (captured_at + timedelta(hours=24)).timestamp() * 1000
    )
    assert 'ttl_seconds="${ttl_seconds:-82800}"' in REMOTE_CONTROL.read_text(encoding="utf-8")


def test_public_evidence_accepts_legacy_discovery_and_rejects_fabricated_capture_binding(
    tmp_path: Path,
) -> None:
    fixture = _activation_fixture(tmp_path)
    capture_receipt, capture_payload, capture_sha256 = _capture_receipt_snapshot(fixture)
    captured_at = datetime.now(UTC)
    capture_created_at, capture_expires_at = _capture_window(capture_payload)
    assert capture_created_at <= int(captured_at.timestamp() * 1000) <= capture_expires_at
    observed = Path(fixture["observed"])
    observed.write_bytes(
        _observed_wire_record(
            capture_receipt_sha256=capture_sha256,
            captured_at=captured_at,
            modern_discovery_observed=False,
            protocol_version="2025-11-25",
        )
    )
    observed.chmod(0o600)
    accepted = _issue_public_from_capture(
        fixture,
        capture_receipt=capture_receipt,
        receipt=tmp_path / "legacy.json",
        ttl_seconds=600,
    )
    assert accepted.returncode == 0, accepted.stderr

    observed.write_bytes(
        _observed_wire_record(
            capture_receipt_sha256="f" * 64,
            captured_at=captured_at,
            modern_discovery_observed=False,
            protocol_version="2025-11-25",
        )
    )
    observed.chmod(0o600)
    rejected = _issue_public_from_capture(
        fixture,
        capture_receipt=capture_receipt,
        receipt=tmp_path / "fabricated.json",
        ttl_seconds=600,
    )
    assert rejected.returncode == 1


def test_public_evidence_rejects_more_than_24_hours_of_freshness(tmp_path: Path) -> None:
    fixture = _activation_fixture(tmp_path)
    capture_receipt, capture_payload, capture_sha256 = _capture_receipt_snapshot(fixture)
    captured_at = datetime.now(UTC)
    capture_created_at, capture_expires_at = _capture_window(capture_payload)
    assert capture_created_at <= int(captured_at.timestamp() * 1000) <= capture_expires_at
    observed = Path(fixture["observed"])
    observed.write_bytes(
        _observed_wire_record(
            capture_receipt_sha256=capture_sha256,
            captured_at=captured_at,
            evidence_ttl=timedelta(hours=24, seconds=1),
        )
    )
    observed.chmod(0o600)
    rejected = _issue_public_from_capture(
        fixture,
        capture_receipt=capture_receipt,
        receipt=tmp_path / "too-fresh.json",
        ttl_seconds=600,
    )
    assert rejected.returncode == 1


def _run_common(body: str, *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", "-c", f"source {shlex.quote(str(COMMON))}; {body}"],
        check=False,
        text=True,
        capture_output=True,
        timeout=10,
        env={"HOME": "/tmp", "PATH": "/usr/bin:/bin", "LANG": "C", **env},
    )


def test_requested_remote_mode_must_match_verified_receipt_mode(tmp_path: Path) -> None:
    body = r"""
MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH="${TEST_ROOT}/remote-activation.json"
MCPHUB_REMOTE_MODE=capture
: >"${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}"
mcphub_remote_activation_mode() { printf 'public\n'; }
if mcphub_resolve_remote_mode; then exit 88; fi
[[ "${MCPHUB_REMOTE_MODE}" == "capture" ]]
"""
    result = _run_common(body, env={"TEST_ROOT": str(tmp_path)})

    assert result.returncode == 0, result.stderr


def test_disabled_remote_mode_ignores_leftover_activation_receipt(tmp_path: Path) -> None:
    body = r"""
MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH="${TEST_ROOT}/remote-activation.json"
MCPHUB_REMOTE_MODE=disabled
MCPHUB_TUNNEL_ENABLED=true
: >"${MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH}"
mcphub_remote_activation_mode() { return 1; }
mcphub_resolve_remote_mode
[[ "${MCPHUB_REMOTE_MODE}" == "disabled" ]]
[[ "${MCPHUB_TUNNEL_ENABLED}" == "false" ]]
"""
    result = _run_common(body, env={"TEST_ROOT": str(tmp_path)})

    assert result.returncode == 0, result.stderr


def test_command_scoped_remote_request_survives_dotenv_reload(tmp_path: Path) -> None:
    env_path = _private_file(
        tmp_path / ".env.mcphub",
        b"MCPHUB_REMOTE_MODE=disabled\n"
        b"MCPHUB_REMOTE_MODE_OVERRIDE=from-file\n"
        b"MCPHUB_REMOTE_OBSERVED_WIRE_EVIDENCE_PATH=/from-file.json\n",
    )
    body = r"""
MCPHUB_ENV_FILE="${TEST_ENV}"
MCPHUB_REMOTE_MODE=public
MCPHUB_REMOTE_MODE_OVERRIDE=command-scope
MCPHUB_REMOTE_OBSERVED_WIRE_EVIDENCE_PATH="${TEST_ROOT}/observed.json"
export MCPHUB_REMOTE_MODE MCPHUB_REMOTE_MODE_OVERRIDE MCPHUB_REMOTE_OBSERVED_WIRE_EVIDENCE_PATH
mcphub_load_env
[[ "${MCPHUB_REMOTE_MODE}" == "public" ]]
[[ "${MCPHUB_REMOTE_MODE_OVERRIDE}" == "command-scope" ]]
[[ "${MCPHUB_REMOTE_OBSERVED_WIRE_EVIDENCE_PATH}" == "${TEST_ROOT}/observed.json" ]]
"""
    result = _run_common(
        body,
        env={"TEST_ENV": str(env_path), "TEST_ROOT": str(tmp_path)},
    )

    assert result.returncode == 0, result.stderr


def test_runtime_receipt_parent_is_forced_owner_private_and_rejects_symlinks(tmp_path: Path) -> None:
    run_directory = tmp_path / "runtime"
    run_directory.mkdir(mode=0o755)
    body = r"""
MCPHUB_RUN_DIR="${TEST_RUN_DIR}"
mcphub_prepare_run_directory
[[ "$(mcphub_private_file_mode "${MCPHUB_RUN_DIR}")" == "700" ]]
"""
    result = _run_common(body, env={"TEST_RUN_DIR": str(run_directory)})
    assert result.returncode == 0, result.stderr
    assert stat.S_IMODE(run_directory.stat().st_mode) == 0o700

    target = _private_directory(tmp_path / "target")
    symlink = tmp_path / "symlink-runtime"
    symlink.symlink_to(target, target_is_directory=True)
    rejected = _run_common(body, env={"TEST_RUN_DIR": str(symlink)})
    assert rejected.returncode != 0
    assert stat.S_IMODE(target.stat().st_mode) == 0o700


def test_tunnel_stop_requires_exact_identity_then_waits_for_absence(tmp_path: Path) -> None:
    body = r"""
MCPHUB_TUNNEL_PID_FILE="${TEST_ROOT}/cloudflared.pid"
MCPHUB_TUNNEL_IDENTITY_FILE="${TEST_ROOT}/cloudflared.identity"
MCPHUB_TUNNEL_STOP_WAIT_SECONDS=2
printf '4242\n' >"${MCPHUB_TUNNEL_PID_FILE}"
printf '4242|test-start:100\n' >"${MCPHUB_TUNNEL_IDENTITY_FILE}"
chmod 600 "${MCPHUB_TUNNEL_PID_FILE}" "${MCPHUB_TUNNEL_IDENTITY_FILE}"
mcphub_private_file_mode() { printf '600\n'; }
mcphub_process_identity() {
  [[ ! -e "${TEST_ROOT}/terminated" ]] || return 1
  printf '4242|test-start:100\n'
}
mcphub_is_managed_tunnel_pid() { return 0; }
mcphub_managed_tunnel_process_absent() { [[ -e "${TEST_ROOT}/terminated" ]]; }
kill() {
  [[ "$1" == "-TERM" && "$2" == "4242" ]] || return 64
  printf 'term\n' >"${TEST_ROOT}/terminated"
}
mcphub_stop_tunnel
[[ -f "${TEST_ROOT}/terminated" ]]
[[ ! -e "${MCPHUB_TUNNEL_PID_FILE}" && ! -e "${MCPHUB_TUNNEL_IDENTITY_FILE}" ]]
"""
    result = _run_common(body, env={"TEST_ROOT": str(tmp_path)})

    assert result.returncode == 0, result.stderr


def test_tunnel_identity_mismatch_is_never_signaled_or_unlinked(tmp_path: Path) -> None:
    body = r"""
MCPHUB_TUNNEL_PID_FILE="${TEST_ROOT}/cloudflared.pid"
MCPHUB_TUNNEL_IDENTITY_FILE="${TEST_ROOT}/cloudflared.identity"
printf '4242\n' >"${MCPHUB_TUNNEL_PID_FILE}"
printf '4242|test-start:100\n' >"${MCPHUB_TUNNEL_IDENTITY_FILE}"
chmod 600 "${MCPHUB_TUNNEL_PID_FILE}" "${MCPHUB_TUNNEL_IDENTITY_FILE}"
mcphub_private_file_mode() { printf '600\n'; }
mcphub_process_identity() { printf '4242|test-start:200\n'; }
mcphub_is_managed_tunnel_pid() { return 0; }
kill() { printf 'unexpected-signal\n'; return 97; }
if mcphub_stop_tunnel; then exit 88; fi
[[ -f "${MCPHUB_TUNNEL_PID_FILE}" && -f "${MCPHUB_TUNNEL_IDENTITY_FILE}" ]]
"""
    result = _run_common(body, env={"TEST_ROOT": str(tmp_path)})

    assert result.returncode == 0, result.stderr
    assert "unexpected-signal" not in result.stdout


def test_activation_guard_stop_is_identity_bound_and_waits_for_absence(tmp_path: Path) -> None:
    body = r"""
MCPHUB_ACTIVATION_GUARD_PID_FILE="${TEST_ROOT}/guard.pid"
MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE="${TEST_ROOT}/guard.identity"
MCPHUB_ACTIVATION_GUARD_STOP_WAIT_SECONDS=2
printf '5252\n' >"${MCPHUB_ACTIVATION_GUARD_PID_FILE}"
printf '5252|test-start:100\n' >"${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}"
chmod 600 "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}"
mcphub_private_file_mode() { printf '600\n'; }
mcphub_process_identity() {
  [[ ! -e "${TEST_ROOT}/terminated" ]] || return 1
  printf '5252|test-start:100\n'
}
mcphub_is_activation_guard_pid() { return 0; }
mcphub_managed_activation_guard_process_absent() { [[ -e "${TEST_ROOT}/terminated" ]]; }
kill() {
  [[ "$1" == "-TERM" && "$2" == "5252" ]] || return 64
  printf 'term\n' >"${TEST_ROOT}/terminated"
}
mcphub_stop_activation_guard
[[ -f "${TEST_ROOT}/terminated" ]]
[[ ! -e "${MCPHUB_ACTIVATION_GUARD_PID_FILE}" && ! -e "${MCPHUB_ACTIVATION_GUARD_IDENTITY_FILE}" ]]
"""
    result = _run_common(body, env={"TEST_ROOT": str(tmp_path)})

    assert result.returncode == 0, result.stderr


def test_down_and_rollback_stop_cloudflare_before_runtime_or_selection() -> None:
    down = DOWN.read_text(encoding="utf-8")
    control = REMOTE_CONTROL.read_text(encoding="utf-8")
    env_example = ENV_EXAMPLE.read_text(encoding="utf-8")
    assert down.index("mcphub_stop_tunnel") < down.index("mcphub_stop_managed_local")
    assert down.index("mcphub_stop_tunnel") < down.index("mcphub_stop_activation_guard")
    assert down.index("mcphub_stop_activation_guard") < down.index("mcphub_stop_managed_local")
    rollback = control[control.index("  rollback)") :]
    assert rollback.index("stop_tunnel_first") < rollback.index("downstream-select.mjs")
    assert rollback.index("stop_guard_after_tunnel") < rollback.index("downstream-select.mjs")
    capture = control[control.index("  capture)") : control.index("  activate-public)")]
    assert capture.index("mcphub_wait_remote_ready capture") < capture.index("mcphub_start_tunnel")
    assert capture.index("mcphub_start_tunnel") < capture.index("mcphub_start_activation_guard")
    assert "Cloudflare remains stopped" not in capture
    for legacy_gate in (
        "MCPHUB_CAPTURE_RECEIPT_VALID",
        "MCPHUB_FINAL_STAMP_VALID",
        "MCPHUB_REMOTE_PUBLIC_READY",
        "MCPHUB_TOOL_DISPATCH_ENABLED",
    ):
        assert legacy_gate not in COMMON.read_text(encoding="utf-8")
        assert legacy_gate not in env_example
    for receipt_input in (
        "MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH",
        "MCPHUB_REMOTE_CONFORMANCE_RESULT_PATH",
        "MCPHUB_REMOTE_CAPTURE_EVIDENCE_PATH",
        "MCPHUB_REMOTE_CAPTURE_RECEIPT_PATH",
        "MCPHUB_REMOTE_OBSERVED_WIRE_EVIDENCE_PATH",
        "MCPHUB_OAUTH_POLICY_PATH",
        "MCPHUB_OAUTH_LOGIN_CREDENTIAL_PATH",
    ):
        assert receipt_input in env_example


def test_expired_guard_removes_connector_and_remote_listener_before_local_restore(tmp_path: Path) -> None:
    script_dir = _private_directory(tmp_path / "mcphub")
    guard_copy = script_dir / ACTIVATION_GUARD.name
    guard_copy.write_bytes(ACTIVATION_GUARD.read_bytes())
    guard_copy.chmod(0o700)
    expected_digest = "a" * 64
    fake_common = f"""\
MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH="${{TEST_ROOT}}/remote-activation.json"
MCPHUB_REMOTE_CAPTURE_RECEIPT_PATH="${{TEST_ROOT}}/remote-capture-activation.json"
MCPHUB_REMOTE_ACTIVATION_HELPER="${{TEST_ROOT}}/helper.mjs"
MCPHUB_PID_FILE="${{TEST_ROOT}}/mcphub.pid"
PORT=46683
MCPHUB_REMOTE_PORT=46684
mcphub_load_env() {{ :; }}
mcphub_release_activation_guard_receipts() {{ printf 'guard-release\\n' >>"${{TEST_ROOT}}/events"; }}
mcphub_activation_receipt_digest() {{ printf '{expected_digest}\\n'; }}
mcphub_remote_activation_mode() {{ printf 'capture\\n'; }}
mcphub_activation_receipt_unexpired() {{
  if [[ ! -e "${{TEST_ROOT}}/mode-read" ]]; then
    : >"${{TEST_ROOT}}/mode-read"
    printf 'capture\\n'
  else
    return 1
  fi
}}
mcphub_stop_tunnel() {{ printf 'tunnel-stop\\n' >>"${{TEST_ROOT}}/events"; rm -f "${{TEST_ROOT}}/connector"; }}
mcphub_assert_tunnel_absent() {{ [[ ! -e "${{TEST_ROOT}}/connector" ]]; }}
mcphub_launch_agent_loaded() {{ return 1; }}
mcphub_pid_file_running() {{ return 0; }}
mcphub_stop_managed_local() {{
  printf 'runtime-stop\\n' >>"${{TEST_ROOT}}/events"
  rm -f "${{TEST_ROOT}}/listener-46683" "${{TEST_ROOT}}/listener-46684"
}}
mcphub_listener_is_absent() {{ [[ ! -e "${{TEST_ROOT}}/listener-$1" ]]; }}
mcphub_start_local() {{ printf 'local-start\\n' >>"${{TEST_ROOT}}/events"; : >"${{TEST_ROOT}}/listener-46683"; }}
mcphub_wait_mode_ready() {{ [[ -e "${{TEST_ROOT}}/listener-46683" && ! -e "${{TEST_ROOT}}/listener-46684" ]]; }}
"""
    (script_dir / "common.sh").write_text(fake_common, encoding="utf-8")
    for marker in (
        "connector",
        "listener-46683",
        "listener-46684",
        "mcphub.pid",
        "remote-activation.json",
        "remote-capture-activation.json",
    ):
        (tmp_path / marker).touch()

    fake_bin = _private_directory(tmp_path / "bin")
    fake_node = fake_bin / "node"
    fake_node.write_text(
        "#!/bin/bash\n"
        "receipt=''\n"
        "while [[ $# -gt 0 ]]; do\n"
        '  if [[ "$1" == \'--receipt\' && $# -ge 2 ]]; then receipt="$2"; shift 2; else shift; fi\n'
        "done\n"
        "printf 'receipt-revoke\\n' >>\"${TEST_ROOT}/events\"\n"
        'rm -f "${receipt}"\n',
        encoding="utf-8",
    )
    fake_node.chmod(0o700)
    result = subprocess.run(
        [
            "/bin/bash",
            str(guard_copy),
            "--receipt",
            str(tmp_path / "remote-activation.json"),
            "--receipt-sha256",
            expected_digest,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
        env={
            **os.environ,
            "PATH": f"{fake_bin}:/usr/bin:/bin",
            "TEST_ROOT": str(tmp_path),
        },
    )

    assert result.returncode == 0, result.stderr
    events = (tmp_path / "events").read_text(encoding="utf-8").splitlines()
    assert events.index("tunnel-stop") < events.index("runtime-stop") < events.index("local-start")
    assert "receipt-revoke" in events
    assert not (tmp_path / "connector").exists()
    assert not (tmp_path / "listener-46684").exists()
    assert not (tmp_path / "remote-activation.json").exists()
    assert not (tmp_path / "remote-capture-activation.json").exists()
    assert (tmp_path / "listener-46683").exists()


def test_invalid_receipt_ensure_removes_remote_exposure_before_local_restore(tmp_path: Path) -> None:
    script_dir = _private_directory(tmp_path / "mcphub")
    ensure_copy = script_dir / ENSURE_RUNNING.name
    ensure_copy.write_bytes(ENSURE_RUNNING.read_bytes())
    ensure_copy.chmod(0o700)
    fake_common = """\
MCPHUB_PID_FILE="${TEST_ROOT}/mcphub.pid"
mcphub_load_env() { :; }
mcphub_resolve_remote_mode() { return 1; }
mcphub_stop_tunnel() { printf 'tunnel-stop\n' >>"${TEST_ROOT}/events"; rm -f "${TEST_ROOT}/connector"; }
mcphub_assert_tunnel_absent() { [[ ! -e "${TEST_ROOT}/connector" ]]; }
mcphub_stop_activation_guard() { printf 'guard-stop\n' >>"${TEST_ROOT}/events"; rm -f "${TEST_ROOT}/guard"; }
mcphub_assert_activation_guard_absent() { [[ ! -e "${TEST_ROOT}/guard" ]]; }
mcphub_launch_agent_loaded() { return 1; }
mcphub_pid_file_running() { return 0; }
mcphub_stop_managed_local() {
  printf 'runtime-stop\n' >>"${TEST_ROOT}/events"
  rm -f "${TEST_ROOT}/listener-46683" "${TEST_ROOT}/listener-46684"
}
mcphub_runtime_listeners_are_absent() {
  [[ ! -e "${TEST_ROOT}/listener-46683" && ! -e "${TEST_ROOT}/listener-46684" ]]
}
mcphub_start_local() { printf 'local-start\n' >>"${TEST_ROOT}/events"; : >"${TEST_ROOT}/listener-46683"; }
mcphub_wait_mode_ready() { [[ -e "${TEST_ROOT}/listener-46683" && ! -e "${TEST_ROOT}/listener-46684" ]]; }
mcphub_remote_listener_is_absent() { [[ ! -e "${TEST_ROOT}/listener-46684" ]]; }
"""
    (script_dir / "common.sh").write_text(fake_common, encoding="utf-8")
    for marker in ("connector", "guard", "listener-46683", "listener-46684", "mcphub.pid"):
        (tmp_path / marker).touch()

    result = subprocess.run(
        ["/bin/bash", str(ensure_copy)],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "TEST_ROOT": str(tmp_path)},
    )

    assert result.returncode == 1
    events = (tmp_path / "events").read_text(encoding="utf-8").splitlines()
    assert events.index("tunnel-stop") < events.index("guard-stop") < events.index("runtime-stop")
    assert events.index("runtime-stop") < events.index("local-start")
    assert not (tmp_path / "connector").exists()
    assert not (tmp_path / "guard").exists()
    assert not (tmp_path / "listener-46684").exists()
    assert (tmp_path / "listener-46683").exists()


def test_things_core_artifact_updater_preserves_secret_lines_byte_for_byte(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tmp_path.chmod(0o700)
    artifacts = _private_directory(tmp_path / "artifacts")
    wheel_bytes = b"audited-wheel"
    sdist_bytes = b"audited-sdist"
    _private_file(artifacts / artifact_config.WHEEL_NAME, wheel_bytes)
    _private_file(artifacts / artifact_config.SDIST_NAME, sdist_bytes)
    monkeypatch.setattr(artifact_config, "WHEEL_SHA256", hashlib.sha256(wheel_bytes).hexdigest())
    monkeypatch.setattr(artifact_config, "SDIST_SHA256", hashlib.sha256(sdist_bytes).hexdigest())
    env_path = _private_file(
        tmp_path / ".env.mcphub",
        b"MCPHUB_BEARER_TOKEN=do-not-print-or-change\n"
        b"THINGS_CORE_WHEEL_PATH=/old/wheel\n"
        b"OTHER_SECRET=also-byte-stable\n",
    )

    report = artifact_config.configure(env_path, artifacts, check=False)
    payload = env_path.read_bytes()
    assert report["changed"] is True
    assert env_path.stat().st_mode & 0o777 == 0o600
    assert b"MCPHUB_BEARER_TOKEN=do-not-print-or-change\n" in payload
    assert b"OTHER_SECRET=also-byte-stable\n" in payload
    assert f"THINGS_CORE_WHEEL_PATH={artifacts / artifact_config.WHEEL_NAME}\n".encode() in payload
    assert f"THINGS_CORE_SDIST_PATH={artifacts / artifact_config.SDIST_NAME}\n".encode() in payload
    assert artifact_config.configure(env_path, artifacts, check=True)["changed"] is False


def test_things_core_artifact_contract_matches_frozen_core_manifest() -> None:
    manifest_path = ROOT / "mcp" / "things-core" / "things_core" / "core_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["provenance"]["wheelSha256"] == artifact_config.WHEEL_SHA256
    assert manifest["provenance"]["sdistSha256"] == artifact_config.SDIST_SHA256
    wrapper = (ROOT / "scripts" / "mcphub" / "things-core-stdio.sh").read_text(encoding="utf-8")
    assert "THINGS_CORE_WHEEL_PATH" in wrapper
    assert "THINGS_CORE_SDIST_PATH" in wrapper
    assert "mcphub_exec_clean" in wrapper


def test_things_core_artifact_updater_rejects_duplicate_keys_without_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tmp_path.chmod(0o700)
    artifacts = _private_directory(tmp_path / "artifacts")
    wheel_bytes = b"wheel"
    sdist_bytes = b"sdist"
    _private_file(artifacts / artifact_config.WHEEL_NAME, wheel_bytes)
    _private_file(artifacts / artifact_config.SDIST_NAME, sdist_bytes)
    monkeypatch.setattr(artifact_config, "WHEEL_SHA256", hashlib.sha256(wheel_bytes).hexdigest())
    monkeypatch.setattr(artifact_config, "SDIST_SHA256", hashlib.sha256(sdist_bytes).hexdigest())
    original = b"THINGS_CORE_WHEEL_PATH=/first\nTHINGS_CORE_WHEEL_PATH=/second\nSECRET=stable\n"
    env_path = _private_file(tmp_path / ".env.mcphub", original)

    with pytest.raises(artifact_config.ArtifactConfigurationError, match="duplicate"):
        artifact_config.configure(env_path, artifacts, check=False)
    assert env_path.read_bytes() == original
    assert stat.S_IMODE(env_path.stat().st_mode) == 0o600


def test_things_core_artifact_updater_detects_same_size_env_race(tmp_path: Path) -> None:
    env_path = _private_file(tmp_path / ".env.mcphub", b"SECRET=one\n")
    snapshot = artifact_config._read_stable(
        env_path,
        label="private env",
        maximum_bytes=artifact_config.MAX_ENV_BYTES,
        owner_only=True,
    )
    env_path.write_bytes(b"SECRET=two\n")
    env_path.chmod(0o600)

    assert artifact_config._same_file(snapshot) is False
