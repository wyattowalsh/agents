"""Cross-surface contract proofs for the sole Things++ MCPHub ingress."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOWNSTREAM = ROOT / "mcp" / "mcphub" / "downstream"
SOURCE = DOWNSTREAM / "src"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_route_matrix_has_one_things_route_and_exact_frozen_remote_rows() -> None:
    matrix_path = DOWNSTREAM / "fixtures" / "ingress" / "route-matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    allowed = matrix["remoteAllowed"]
    assert len(allowed) == 14
    assert allowed.count(["POST", "/mcp/things"]) == 1
    assert all(path == "/mcp/things" or not path.startswith("/mcp/") for _method, path in allowed)
    assert allowed == [
        ["GET", "/"],
        ["POST", "/mcp/things"],
        ["GET", "/.well-known/oauth-protected-resource/mcp/things"],
        ["GET", "/.well-known/oauth-authorization-server"],
        ["GET", "/.well-known/oauth-authorization-server/mcp/things"],
        ["GET", "/oauth/authorize"],
        ["POST", "/oauth/authorize"],
        ["POST", "/oauth/token"],
        ["POST", "/oauth/register"],
        ["POST", "/oauth/revoke"],
        ["GET", "/oauth/login"],
        ["POST", "/oauth/login"],
        ["POST", "/oauth/session/logout"],
        ["GET", "/oauth/assets/login.css"],
    ]
    denied_paths = {path for _method, path in matrix["alwaysDenied"]}
    assert {
        "/mcp",
        "/mcp/",
        "/mcp/$smart",
        "/mcp/supathings",
        "/mcp/tunnel",
        "/mcp/things-core",
        "/mcp/things-shortcuts",
        "/mcp/things-native",
        "/MCP",
        "/MCP/THINGS",
        "/MCP/things-core",
        "/alice/MCP/things-core",
        "/API/tools/things-core/add_todo",
    } <= denied_paths
    assert {
        "/mcp/%74hings",
        "/mcp/./things",
        "/mcp/x/../things",
        "/mcp\\things",
        "/mcp/things;alternate",
        "/mcp/things?",
        "/mcp/things/",
        "/mcp//things",
    } <= denied_paths


def test_one_local_appserver_listener_intercepts_things_before_upstream_routes() -> None:
    main = _read(SOURCE / "runtime" / "main.ts")
    assert '@samanhappy/mcphub/dist/server.js"' in main
    assert "new McpHubAppServer()" in main
    assert "upstream.getApp()" in main
    assert "installOwnedLocalThingsInterceptor" in main
    assert "await upstream.initialize()" in main
    assert "createServer(upstreamApplication)" in main
    assert ".start(" not in main
    assert main.index("installOwnedLocalThingsInterceptor") < main.index("await upstream.initialize()")


def test_provider_reuses_one_appserver_initialization_and_closes_at_seventy_tools() -> None:
    provider = _read(SOURCE / "runtime" / "provider.ts")
    main = _read(SOURCE / "runtime" / "main.ts")
    assert 'const GROUP = "things"' in provider
    assert "result.tools.length !== 70" in provider
    assert "initUpstreamServers" not in provider
    assert "cleanupAllServers" not in provider
    assert "await provider.initialize()" in main
    assert "await upstream.shutdown()" in main


def test_settings_gate_enforces_group_only_backends_and_exact_contract_digest() -> None:
    settings = _read(SOURCE / "runtime" / "settings-contract.ts")
    assert 'const SERVERS = ["things-core", "things-shortcuts", "things-native"]' in settings
    assert "settings.thingsContract" in settings
    assert "contract.manifestSha256 !== manifestFile.sha256" in settings
    assert "capabilityManifestSha256: manifestFile.sha256" in settings
    assert "settingsSha256: settingsFile.sha256" in settings
    assert "entry.groupOnly !== true" in settings
    assert "entry.toolApprovals" in settings
    assert 'entry.name === "things"' in settings
    assert "SERVERS.includes" in settings


def test_remote_public_and_tool_dispatch_require_verified_receipt_not_env_flags() -> None:
    readiness = _read(SOURCE / "runtime" / "readiness.ts")
    main = _read(SOURCE / "runtime" / "main.ts")
    assert "ValidatedRemoteActivationReceipt" in readiness
    assert "loadRemoteActivationReceipt" in readiness
    assert "readOwnerOnlyRuntimeFile" in readiness
    assert "routeManifestSha256" in readiness
    assert "settingsSha256" in readiness
    assert "capabilityManifestSha256" in readiness
    assert "cloudflaredConfigSha256" in readiness
    assert "capture_mode_not_ready" in readiness
    assert "remote_public_not_ready" in readiness
    assert "MCPHUB_FINAL_STAMP_VALID" not in main
    assert "MCPHUB_CAPTURE_RECEIPT_VALID" not in main
    assert "MCPHUB_TOOL_DISPATCH_ENABLED" not in main


def test_capture_evidence_is_closed_secret_free_and_create_once() -> None:
    recorder = _read(SOURCE / "ingress" / "capture-evidence.ts")
    main = _read(SOURCE / "runtime" / "main.ts")
    assert "const MAX_CAPTURE_TTL_MS = 30 * 60 * 1_000" in recorder
    assert "const EVIDENCE_FRESHNESS_TTL_MS = 24 * 60 * 60 * 1_000" in recorder
    assert "input.expiresAt - input.createdAt > MAX_CAPTURE_TTL_MS" in recorder
    assert "expiresAt: now + EVIDENCE_FRESHNESS_TTL_MS" in recorder
    assert "expiresAt - capturedAt > EVIDENCE_FRESHNESS_TTL_MS" in recorder
    assert "exactKeys(source, TOP_LEVEL_KEYS)" in recorder
    assert "exactKeys(routes, ROUTE_STATUS_KEYS)" in recorder
    assert "source.schemaVersion !== SCHEMA_VERSION" in recorder
    assert "source.offlineAccessSemantics !== OFFLINE_ACCESS_SEMANTICS" in recorder
    assert "THINGS_SCOPES.every((scope, index) => scopes[index] === scope)" in recorder
    assert "source.secretFree !== true" in recorder
    assert "source.redactionsVerified !== true" in recorder
    assert "source.prohibitedDataAbsent !== true" in recorder
    assert "evidenceDigestSha256 !== canonicalSha256(unsigned)" in recorder
    assert "linkSync(temporary, pathname)" in recorder
    assert 'error.code === "EEXIST"' in recorder
    assert "renameSync" not in recorder
    assert "validateCaptureEvidenceForPublic" in main
    assert "bytes: observedFile.bytes" in main


def test_public_receipt_is_bound_to_semantic_capture_evidence_and_live_routes() -> None:
    activation = _read(ROOT / "scripts" / "mcphub" / "remote-activation.mjs")
    assert "const MAX_CAPTURE_TTL_MS = 30 * 60 * 1_000" in activation
    assert "const MAX_PUBLIC_TTL_MS = 24 * 60 * 60 * 1_000" in activation
    assert "validateObservedWireEvidence" in activation
    assert 'record.schemaVersion === "1.1.0" && record.status === "observed-pass"' in activation
    assert "record.publicResource === PUBLIC_RESOURCE" in activation
    assert 'JSON.stringify(["things.read", "things.write", "things.admin"])' in activation
    assert "record.offlineAccessRequested === true" in activation
    assert 'record.offlineAccessSemantics === "refresh-only-no-things-authorization"' in activation
    assert "record.resourceIndicatorObserved === true" in activation
    assert "record.pkceS256Observed === true" in activation
    assert "record.captureReceiptSha256 === captureReceipt.sha256" in activation
    assert "record.routeStatuses.mcp === 401" in activation
    assert "record.routeStatuses.protectedResourceMetadata === 200" in activation
    assert "record.routeStatuses.authorizationServerMetadata === 200" in activation
    assert "record.routeStatuses.authorization === 503" in activation
    assert 'record.routeStatuses.registration === (registrationMode === "dcr" ? 503 : null)' in activation
    assert "record.secretFree === true" in activation
    assert "record.redactionsVerified === true" in activation
    assert "record.prohibitedDataAbsent === true" in activation
    assert "delete evidenceWithoutDigest.evidenceDigestSha256" in activation
    assert "capturedAt >= captureReceipt.receipt.createdAt" in activation
    assert "capturedAt <= captureReceipt.receipt.expiresAt" in activation
    assert "expiresAt - capturedAt <= MAX_PUBLIC_TTL_MS" in activation
    assert "expiresAt >= requiredUntil" in activation
    assert "allow_expired_capture: true" in activation
    assert "computed.observedWireEvidenceSha256 = sha256(observedBytes)" in activation
    assert "computed.cloudflaredConfigSha256" in activation
    assert "settingsSha256: sha256(settingsBytes)" in activation
    assert "routeManifestSha256: sha256" in activation


def test_production_oauth_challenge_and_capture_dispatch_contracts_are_executable() -> None:
    ingress_gate = DOWNSTREAM / "test" / "ingress" / "gate.mjs"
    completed = subprocess.run(
        ["node", str(ingress_gate)],
        cwd=DOWNSTREAM,
        check=False,
        capture_output=True,
        text=True,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "fail 0" in output
    assert "skipped 0" in output
    assert "todo 0" in output
    assert "remote-oauth discovery accepts Cloudflare forwarding headers" in output
    assert "local-bearer rejects Cloudflare forwarding headers" in output
    assert "capture handler keeps interactive OAuth and tools disabled" in output
    assert "capture GET MCP resource returns an OAuth challenge" in output
    assert "RFC 8414 issuer-path authorization-server metadata reaches origin" in output
    assert "apex origin landing is served on GET /" in output
    assert "unauthenticated production MCP returns an OAuth challenge" in output
    assert "production handler serves exact well-known OAuth metadata routes" in output
    assert "production ingress rejects encoded and alternate route forms" in output
    assert "modern and legacy catalogs remain the exact same seventy tools" in output


def test_raw_header_security_and_content_free_failures_are_owned_by_ingress() -> None:
    http = _read(SOURCE / "ingress" / "http.ts")
    security = _read(SOURCE / "security" / "ingress" / "request-security.ts")
    assert "request.rawHeaders" in http
    assert "acceptedSocketIdentity" in http
    assert "rejectForwardingHeaders" in http
    assert (
        'if (options.kind === "local-bearer") {\n        rejectForwardingHeaders(request.rawHeaders);\n      }'
        in http
    )
    assert 'response.setHeader("content-length", "0")' in http
    assert "DEFAULT_MAX_REQUEST_BODY_SIZE" in http
    assert "forwarding_header_forbidden" in security
    assert "socket_listener_mismatch" in security


def test_rfc9207_issuer_has_one_owned_serialization_path() -> None:
    response_source = _read(SOURCE / "ingress" / "oauth-responses.ts")
    other_sources = "\n".join(
        _read(path) for path in sorted((SOURCE / "ingress").glob("*.ts")) if path.name != "oauth-responses.ts"
    )
    ingress_sources = f"{response_source}\n{other_sources}"
    assert ingress_sources.count('searchParams.set("iss", THINGS_ISSUER)') == 1
    assert response_source.count("export function issuerBoundAuthorizationRedirect(") == 1
    assert 'searchParams.set("iss", THINGS_ISSUER)' not in other_sources


def test_shell_and_just_surfaces_probe_only_the_exact_things_group_route() -> None:
    smoke = _read(ROOT / "scripts" / "mcphub" / "smoke.sh")
    env_example = _read(ROOT / ".env.mcphub.example")
    justfile = _read(ROOT / "justfile")
    assert 'ENDPOINT="${MCPHUB_BASE_URL}/mcp/things"' in smoke
    assert "exact 70-tool contract" in smoke
    assert "/mcp/harness" not in smoke
    assert "/mcp/ddgs" not in smoke
    assert "https://mcp.w4w.dev/mcp/things" in env_example
    assert "http://127.0.0.1:46684" in env_example
    assert "MCPHUB_REMOTE_MODE=disabled" in env_example
    assert "stateless /mcp/things route and exact 70-tool group" in justfile


def test_reconcile_check_is_read_only_and_restart_is_apply_only() -> None:
    reconcile = _read(ROOT / "scripts" / "mcphub" / "reconcile-runtime.sh")
    check_start = reconcile.index('if [[ "${CHECK}" -eq 1 ]]; then')
    check_exit = reconcile.index('exit "${check_status}"', check_start)
    command = 'uv run python "${SCRIPT_DIR}/reconcile_runtime_settings.py"'
    apply_call = reconcile.rindex(command)
    assert reconcile.count(command) == 2
    assert "--check" in reconcile[check_start:check_exit]
    assert "mcphub_distribution_is_selected" in reconcile[check_start:check_exit]
    assert "launchctl" not in reconcile[check_start:check_exit]
    assert check_start < check_exit < apply_call
    assert "--check is read-only and cannot be combined with --restart" in reconcile


def test_cloudflare_can_never_target_bearer_port_and_stops_before_origin() -> None:
    common = _read(ROOT / "scripts" / "mcphub" / "common.sh")
    activation = _read(ROOT / "scripts" / "mcphub" / "remote-activation.mjs")
    down = _read(ROOT / "scripts" / "mcphub" / "down.sh")
    assert "MCPHUB_TUNNEL_TARGET_URL:-http://127.0.0.1:46684" in common
    assert '"${MCPHUB_TUNNEL_TARGET_URL}" != "http://127.0.0.1:46684"' in common
    assert "Cloudflare ingress config failed exact 46684-only readback" in common
    assert "http://127.0.0.1:46683" not in activation
    assert "http://127.0.0.1:46684" in activation
    tunnel_stop = down.index("mcphub_stop_tunnel")
    origin_stop = down.index("mcphub_stop_managed_local")
    assert tunnel_stop < origin_stop


def test_remote_disabled_health_does_not_require_the_46684_listener() -> None:
    common = _read(ROOT / "scripts" / "mcphub" / "common.sh")
    doctor = _read(ROOT / "scripts" / "mcphub" / "doctor.sh")
    ensure = _read(ROOT / "scripts" / "mcphub" / "ensure-running.sh")
    smoke = _read(ROOT / "scripts" / "mcphub" / "smoke.sh")
    runtime_ready = common.split("mcphub_runtime_is_ready()", 1)[1].split("}", 1)[0]
    assert "MCPHUB_REMOTE_PORT" not in runtime_ready
    assert "mcphub_distribution_is_selected" not in runtime_ready
    wait_ready = common.split("mcphub_wait_ready()", 1)[1].split("mcphub_stop_managed_local()", 1)[0]
    assert "mcphub_distribution_is_selected" in wait_ready
    assert "mcphub_remote_public_ready" not in ensure
    assert "MCPHUB_REMOTE_PORT" not in ensure
    assert "MCPHUB_REMOTE_PORT" not in smoke
    assert "disabled and absent" in doctor
    assert "unexpected while remote mode is disabled" in doctor
    start_local = _read(ROOT / "scripts" / "mcphub" / "start-local-only.sh")
    assert "export MCPHUB_REMOTE_MODE_OVERRIDE=disabled" in start_local
    assert "local_only_ready" in start_local
