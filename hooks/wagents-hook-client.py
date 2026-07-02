#!/usr/bin/env python3
"""Stdlib-only forwarder for the optional warm-process hook worker (RV-003).

``hooks/wagents-hook.py`` runs under a trusted bare ``python3`` where the
``wagents`` distribution is not installed (see the constraint documented at
the top of that file), so this module stays dependency-free: standard library
only, no imports from ``wagents.*``. It is loaded by file path (mirroring
``_load_bundle_module()`` in ``wagents-hook.py``) rather than imported as a
package module.

Protocol: connect to a Unix domain socket served by
``hooks/wagents-hook-worker.py --serve --socket PATH``, write one NDJSON
request line, shut down the write half, and read the NDJSON response line(s)
until the server closes the connection. See ``wagents-hook-worker.py`` for the
request/response line shapes.
"""

from __future__ import annotations

import json
import os
import socket
from contextlib import suppress
from pathlib import Path
from typing import Any

DEFAULT_SOCKET_ENV = "WAGENTS_HOOK_WORKER_SOCKET"
DEFAULT_SOCKET_RELATIVE = Path(".cache") / "wagents" / "hook-worker.sock"
DEFAULT_FORWARD_TIMEOUT_SECONDS = 5.0
_RECV_CHUNK_BYTES = 65536


def default_socket_path() -> Path:
    """Resolve the warm-worker socket path.

    ``WAGENTS_HOOK_WORKER_SOCKET`` overrides the default so tests and daemon
    supervisors can point at a non-default location; otherwise resolves to
    ``~/.cache/wagents/hook-worker.sock``, matching the cache-directory
    convention used by ``HOOK_TIMING_PATH`` and ``SYNC_HOOK_HASH_PATH``
    elsewhere in the fleet.
    """
    override = os.environ.get(DEFAULT_SOCKET_ENV)
    if override:
        return Path(override)
    return Path.home() / DEFAULT_SOCKET_RELATIVE


def forward_request(
    socket_path: Path | str,
    request: dict[str, Any],
    *,
    timeout: float = DEFAULT_FORWARD_TIMEOUT_SECONDS,
) -> dict[str, Any] | None:
    """Forward one NDJSON request to the warm worker socket.

    Returns the parsed ``{"stdout": str, "exit_code": int}`` response, or
    ``None`` on any failure: missing socket file, connection refused, a
    timeout, or a malformed/empty response. This function never raises;
    callers (``wagents-hook.py --worker-socket``) must treat ``None`` as
    "fall back to the cold dispatch path" so an unstarted or crashed worker
    never blocks a hook decision.
    """
    path = Path(socket_path)
    if not path.exists():
        return None
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(str(path))
        sock.sendall((json.dumps(request) + "\n").encode("utf-8"))
        with suppress(OSError):
            sock.shutdown(socket.SHUT_WR)
        chunks: list[bytes] = []
        while True:
            chunk = sock.recv(_RECV_CHUNK_BYTES)
            if not chunk:
                break
            chunks.append(chunk)
    except OSError:
        return None
    finally:
        sock.close()

    raw = b"".join(chunks).decode("utf-8", errors="replace").strip()
    if not raw:
        return None
    last_line = raw.splitlines()[-1]
    try:
        parsed = json.loads(last_line)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    stdout = parsed.get("stdout")
    exit_code = parsed.get("exit_code")
    if not isinstance(stdout, str) or type(exit_code) is not int:
        return None
    return parsed
