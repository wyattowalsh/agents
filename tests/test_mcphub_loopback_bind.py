"""Static proofs for the owned loopback listeners and retired bind shim."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "mcphub"
DOWNSTREAM = ROOT / "mcp" / "mcphub" / "downstream"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_bind_preload_is_absent_and_typescript_owns_both_loopback_listeners() -> None:
    assert not (SCRIPTS / "bind-loopback.cjs").exists()

    constants = _read(DOWNSTREAM / "src" / "ingress" / "constants.ts")
    main = _read(DOWNSTREAM / "src" / "runtime" / "main.ts")
    assert constants.count('host: "127.0.0.1"') == 2
    assert "port: 46683" in constants
    assert "port: 46684" in constants
    assert 'resource: "http://127.0.0.1:46683/mcp/things"' in constants
    assert 'resource: "https://mcp.w4w.dev/mcp/things"' in constants
    assert "createServer(upstreamApplication)" in main
    assert "createThingsIngressRequestListener" in main


def test_launcher_executes_only_the_selected_sealed_distribution() -> None:
    start = _read(SCRIPTS / "start-server.sh")
    assert 'exec node --disallow-code-generation-from-strings "${MCPHUB_DOWNSTREAM_LAUNCHER}"' in start
    assert '--runtime-root "${MCPHUB_DOWNSTREAM_RUNTIME_ROOT}"' in start
    assert "mcphub_distribution_is_selected" in start
    assert "npx" not in start
    assert "MCPHUB_PACKAGE_VERSION" not in start
    assert "bind-loopback" not in start
    assert "mcphub-esm-" not in start


def test_readiness_requires_fixed_loopback_endpoints_owned_by_the_tracked_pid() -> None:
    common = _read(SCRIPTS / "common.sh")
    assert 'PORT="${PORT:-46683}"' in common
    assert 'MCPHUB_REMOTE_PORT="${MCPHUB_REMOTE_PORT:-46684}"' in common
    assert 'MCPHUB_BIND_HOST="${MCPHUB_BIND_HOST:-127.0.0.1}"' in common
    assert "mcphub_listener_is_loopback" in common
    assert "mcphub_listener_owned_by_pid" in common
    assert "mcphub_pid_file_managed_running" in common
    assert '"${MCPHUB_BASE_URL}/mcp/things"' in common
    assert "MCPHUB_STATUS:405" in common
    assert "MCPHUB_SIZE:0" in common


def test_remote_tunnel_targets_only_the_owned_46684_route_manifest() -> None:
    common = _read(SCRIPTS / "common.sh")
    activation = _read(SCRIPTS / "remote-activation.mjs")
    assert "service: http://127.0.0.1:46684" in activation
    assert "127.0.0.1:46683" not in activation
    assert "mcp/things" in activation
    assert "oauth-protected-resource/mcp/things" in activation
    assert "oauth-authorization-server" in activation
    assert "oauth/session/logout" in activation
    assert "http_status:404" in activation
    assert "verify-config" in common
    assert "token-only Cloudflare launch" in common
