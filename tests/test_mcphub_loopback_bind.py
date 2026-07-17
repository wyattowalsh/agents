"""Hermetic tests for the MCPHub loopback-only launcher shim."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PRELOAD = REPO_ROOT / "scripts" / "mcphub" / "bind-loopback.cjs"


def _run_probe(*, host: str, explicit_host: str | None = None) -> subprocess.CompletedProcess[str]:
    listen_args = "0"
    if explicit_host is not None:
        listen_args += f", {json.dumps(explicit_host)}"
    source = f"""
const http = require('node:http');
const server = http.createServer((_req, res) => res.end('ok'));
server.listen({listen_args}, () => {{
  console.log(JSON.stringify({{ address: server.address().address, nodeOptions: process.env.NODE_OPTIONS || '' }}));
  server.close();
}});
"""
    env = {
        **os.environ,
        "MCPHUB_BIND_SHIM_FORCE": "1",
        "MCPHUB_BIND_HOST": host,
        "PORT": "0",
    }
    return subprocess.run(
        ["node", "--require", str(PRELOAD), "-e", source],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_bind_shim_injects_loopback_and_clears_child_preload() -> None:
    result = _run_probe(host="127.0.0.1")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {"address": "127.0.0.1", "nodeOptions": ""}


def test_bind_shim_rejects_non_loopback_configuration() -> None:
    result = _run_probe(host="0.0.0.0")

    assert result.returncode != 0
    assert "MCPHUB_BIND_HOST must be loopback-only" in result.stderr


def test_bind_shim_rejects_explicit_wildcard_listen() -> None:
    result = _run_probe(host="127.0.0.1", explicit_host="0.0.0.0")

    assert result.returncode != 0
    assert "refused non-loopback listen host" in result.stderr


def test_launchers_pin_mcphub_and_require_listener_check() -> None:
    start = (REPO_ROOT / "scripts" / "mcphub" / "start-server.sh").read_text(encoding="utf-8")
    common = (REPO_ROOT / "scripts" / "mcphub" / "common.sh").read_text(encoding="utf-8")
    doctor = (REPO_ROOT / "scripts" / "mcphub" / "doctor.sh").read_text(encoding="utf-8")

    assert 'MCPHUB_PACKAGE_VERSION="${MCPHUB_PACKAGE_VERSION:-1.0.24}"' in start
    assert '"@samanhappy/mcphub@${MCPHUB_PACKAGE_VERSION}"' in start
    assert "mcphub_listener_is_loopback" in common
    assert "unsafe non-loopback listener" in doctor
