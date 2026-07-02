#!/usr/bin/env python3
"""Optional warm-process hook worker (``WAGENTS_HOOK_PERF_TIER=worker``).

Supports one-shot bundle/single-policy execution (stdin payload, stdout JSON) and
an NDJSON request/response loop for persistent sessions:

Request line::
    {"bundle": ["policy-a", "policy-b"], "harness": "cursor", "payload": {...}}
    {"policy_id": "cursor-destructive-shell-guard", "harness": "cursor", "payload": {...}}

Response line::
    {"stdout": "<json>", "exit_code": 0}
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import socket
import stat
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "hooks" / "wagents-hook.py"


def _load_dispatcher():
    spec = importlib.util.spec_from_file_location("wagents_hook_worker_dispatcher", HOOK_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load dispatcher from {HOOK_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_request(dispatcher: Any, request: dict[str, Any]) -> dict[str, Any]:
    # RV-NEW-001: each warm-process request must start with a clean stdout-emission
    # flag, matching cold ``main()`` so Cursor fail-closed allow sentinels fire on
    # every request, not only the first in a persistent worker session.
    dispatcher._STDOUT_EMITTED = False
    harness = str(request.get("harness") or "auto")
    payload = request.get("payload")
    if not isinstance(payload, dict):
        payload = {}

    buffer = io.StringIO()
    stdin_backup = sys.stdin
    code = 0
    try:
        sys.stdin = io.StringIO(json.dumps(payload))
        with redirect_stdout(buffer):
            if isinstance(request.get("bundle"), list):
                policy_ids = [str(item) for item in request["bundle"] if str(item)]
                bundle_module = dispatcher._load_bundle_module()
                code = bundle_module.run_bundle(
                    policy_ids,
                    harness,
                    dispatcher._normalize(payload, harness),
                    mode=str(request.get("bundle_mode") or "enforce-chain"),
                    timeout_seconds=float(request.get("bundle_timeout") or 30.0),
                    dispatcher=dispatcher,
                )
            else:
                policy_id = str(request.get("policy_id") or "")
                if policy_id not in dispatcher.POLICIES:
                    return {"stdout": "", "exit_code": 2}
                normalized = dispatcher._normalize(payload, harness)
                code = dispatcher.POLICIES[policy_id](normalized)
                # RV-005: share the exact allow-record + Cursor fail-closed-allow-emit
                # finalize steps with the CLI dispatcher's single-policy path instead of
                # a hand-duplicated copy that could silently drift from it.
                code = dispatcher._finalize_single_policy_dispatch(
                    normalized,
                    policy_id,
                    harness=harness,
                    code=code,
                )
    finally:
        sys.stdin = stdin_backup
    return {"stdout": buffer.getvalue(), "exit_code": int(code)}


def _serve_stream(dispatcher: Any, input_stream: Any, output_stream: Any) -> int:
    for line in input_stream:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            request = json.loads(stripped)
        except json.JSONDecodeError:
            response = {"stdout": "", "exit_code": 2, "error": "invalid-json"}
        else:
            response = _run_request(dispatcher, request if isinstance(request, dict) else {})
        output_stream.write(json.dumps(response, separators=(",", ":")) + "\n")
        output_stream.flush()
    return 0


def _read_socket_request_line(conn: socket.socket) -> str:
    """Read the first NDJSON line from a socket client that may half-close after send."""
    chunks: list[bytes] = []
    while True:
        chunk = conn.recv(65536)
        if not chunk:
            break
        chunks.append(chunk)
        if b"\n" in chunk:
            break
    if not chunks:
        return ""
    return b"".join(chunks).decode("utf-8", errors="replace").splitlines()[0]


def _serve_socket_connection(dispatcher: Any, conn: socket.socket) -> None:
    stripped = _read_socket_request_line(conn).strip()
    if not stripped:
        response: dict[str, Any] = {"stdout": "", "exit_code": 2, "error": "empty-request"}
    else:
        try:
            request = json.loads(stripped)
        except json.JSONDecodeError:
            response = {"stdout": "", "exit_code": 2, "error": "invalid-json"}
        else:
            response = _run_request(dispatcher, request if isinstance(request, dict) else {})
    conn.sendall((json.dumps(response, separators=(",", ":")) + "\n").encode("utf-8"))


def _serve(dispatcher: Any) -> int:
    return _serve_stream(dispatcher, sys.stdin, sys.stdout)


def _is_socket_path(path: Path) -> bool:
    try:
        return stat.S_ISSOCK(path.stat().st_mode)
    except OSError:
        return False


def _serve_socket(dispatcher: Any, socket_path: str) -> int:
    path = Path(socket_path).expanduser()
    if not str(path):
        raise ValueError("--socket requires a non-empty path")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if not _is_socket_path(path):
            raise RuntimeError(f"refusing to replace non-socket path: {path}")
        path.unlink()

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        server.bind(str(path))
        path.chmod(0o600)
        server.listen()
        while True:
            conn, _addr = server.accept()
            with conn:
                _serve_socket_connection(dispatcher, conn)
    finally:
        server.close()
        if _is_socket_path(path):
            path.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Warm-process wagents hook worker.")
    parser.add_argument("policy_id", nargs="?", default=None)
    parser.add_argument("--bundle", default=None, metavar="ID1,ID2,...")
    parser.add_argument("--bundle-mode", default="enforce-chain")
    parser.add_argument("--bundle-timeout", type=float, default=30.0)
    parser.add_argument("--harness", default="auto")
    parser.add_argument("--serve", action="store_true", help="Run NDJSON request loop on stdin.")
    parser.add_argument("--socket", default=None, help="Serve NDJSON requests over a Unix socket path.")
    args = parser.parse_args(argv)

    dispatcher = _load_dispatcher()
    if args.serve:
        if args.socket:
            return _serve_socket(dispatcher, args.socket)
        return _serve(dispatcher)

    raw = dispatcher._load_payload()
    harness = dispatcher._detect_harness(raw, args.harness)
    request: dict[str, Any] = {"harness": harness, "payload": raw}
    if args.bundle:
        request["bundle"] = [token.strip() for token in args.bundle.split(",") if token.strip()]
        request["bundle_mode"] = args.bundle_mode
        request["bundle_timeout"] = args.bundle_timeout
    elif args.policy_id:
        request["policy_id"] = args.policy_id
    else:
        parser.error("provide policy_id, --bundle, or --serve")

    response = _run_request(dispatcher, request)
    stdout = str(response.get("stdout") or "")
    if stdout:
        sys.stdout.write(stdout if stdout.endswith("\n") else stdout + "\n")
    return int(response.get("exit_code") or 0)


if __name__ == "__main__":
    raise SystemExit(main())
