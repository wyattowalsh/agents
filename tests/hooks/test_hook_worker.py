"""Tests for optional ``hooks/wagents-hook-worker.py`` warm-process worker."""

from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKER_PATH = REPO_ROOT / "hooks" / "wagents-hook-worker.py"
CLIENT_PATH = REPO_ROOT / "hooks" / "wagents-hook-client.py"
HOOK_PATH = REPO_ROOT / "hooks" / "wagents-hook.py"
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "hooks"


def _load_wagents_hook_module():
    spec = importlib.util.spec_from_file_location("wagents_hook_worker_tests_hook", HOOK_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_hook_client_module():
    spec = importlib.util.spec_from_file_location("wagents_hook_client_worker_tests", CLIENT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_worker_oneshot_bundle_denies_destructive_shell():
    payload = json.loads((FIXTURES_DIR / "cursor-bash-destructive.json").read_text(encoding="utf-8"))
    completed = subprocess.run(
        [
            sys.executable,
            str(WORKER_PATH),
            "--bundle",
            "cursor-destructive-shell-guard,cursor-protected-file-guard",
            "--harness",
            "cursor",
        ],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert completed.returncode == 0
    decision = json.loads(completed.stdout)
    assert decision["permission"] == "deny"


def test_worker_serve_ndjson_round_trip():
    request = {
        "policy_id": "cursor-destructive-shell-guard",
        "harness": "cursor",
        "payload": json.loads((FIXTURES_DIR / "cursor-bash-benign.json").read_text(encoding="utf-8")),
    }
    completed = subprocess.run(
        [sys.executable, str(WORKER_PATH), "--serve"],
        input=json.dumps(request) + "\n",
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert completed.returncode == 0
    line = completed.stdout.strip().splitlines()[-1]
    response = json.loads(line)
    assert response["exit_code"] == 0


def test_worker_serve_cursor_allow_matches_cli_dispatch():
    """RV-005: worker single-policy path must emit the identical Cursor allow sentinel as the CLI."""
    payload = json.loads((FIXTURES_DIR / "cursor-bash-benign.json").read_text(encoding="utf-8"))

    cli = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "hooks" / "wagents-hook.py"),
            "cursor-destructive-shell-guard",
            "--harness",
            "cursor",
        ],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )
    request = {"policy_id": "cursor-destructive-shell-guard", "harness": "cursor", "payload": payload}
    worker = subprocess.run(
        [sys.executable, str(WORKER_PATH), "--serve"],
        input=json.dumps(request) + "\n",
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert cli.returncode == 0
    assert worker.returncode == 0
    cli_payload = json.loads(cli.stdout.strip())
    worker_response = json.loads(worker.stdout.strip().splitlines()[-1])
    assert worker_response["exit_code"] == 0
    worker_payload = json.loads(worker_response["stdout"].strip())
    assert cli_payload == {"permission": "allow"}
    assert worker_payload == cli_payload


def _wait_for_socket(path: Path, proc: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if path.exists():
            return
        if proc.poll() is not None:
            break
        time.sleep(0.05)
    if proc.poll() is None:
        proc.terminate()
        try:
            _stdout, stderr = proc.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            proc.kill()
            _stdout, stderr = proc.communicate(timeout=1)
    else:
        stderr = proc.stderr.read() if proc.stderr is not None else ""
    raise AssertionError(f"worker socket did not start; returncode={proc.poll()} stderr={stderr}")


def _short_socket_path() -> Path:
    return Path("/tmp") / f"wagents-hook-{os.getpid()}-{time.time_ns()}.sock"


def test_dispatcher_worker_socket_round_trip():
    socket_path = _short_socket_path()
    benign_payload = json.loads((FIXTURES_DIR / "cursor-bash-benign.json").read_text(encoding="utf-8"))
    destructive_payload = json.loads((FIXTURES_DIR / "cursor-bash-destructive.json").read_text(encoding="utf-8"))
    worker = subprocess.Popen(
        [sys.executable, str(WORKER_PATH), "--serve", "--socket", str(socket_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=REPO_ROOT,
    )
    try:
        _wait_for_socket(socket_path, worker)
        allow = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "hooks" / "wagents-hook.py"),
                "--worker-socket",
                str(socket_path),
                "cursor-destructive-shell-guard",
                "--harness",
                "cursor",
            ],
            input=json.dumps(benign_payload),
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
            check=False,
        )
        deny = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "hooks" / "wagents-hook.py"),
                "--worker-socket",
                str(socket_path),
                "--bundle",
                "cursor-destructive-shell-guard,cursor-protected-file-guard",
                "--harness",
                "cursor",
            ],
            input=json.dumps(destructive_payload),
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
            check=False,
        )
    finally:
        worker.terminate()
        try:
            worker.wait(timeout=5)
        except subprocess.TimeoutExpired:
            worker.kill()
            worker.wait(timeout=5)
        socket_path.unlink(missing_ok=True)

    assert allow.returncode == 0
    assert json.loads(allow.stdout) == {"permission": "allow"}
    assert deny.returncode == 0
    assert json.loads(deny.stdout)["permission"] == "deny"


def _run_worker_socket_policy(
    socket_path: Path,
    policy_args: list[str],
    payload: dict,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "hooks" / "wagents-hook.py"),
            "--worker-socket",
            str(socket_path),
            *policy_args,
            "--harness",
            "cursor",
        ],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )


def test_worker_socket_sequential_single_policy_allows():
    """RV-NEW-001: warm socket must emit allow JSON on every benign request, not only the first."""
    socket_path = _short_socket_path()
    benign_payload = json.loads((FIXTURES_DIR / "cursor-bash-benign.json").read_text(encoding="utf-8"))
    worker = subprocess.Popen(
        [sys.executable, str(WORKER_PATH), "--serve", "--socket", str(socket_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=REPO_ROOT,
    )
    try:
        _wait_for_socket(socket_path, worker)
        first = _run_worker_socket_policy(socket_path, ["cursor-destructive-shell-guard"], benign_payload)
        second = _run_worker_socket_policy(socket_path, ["cursor-destructive-shell-guard"], benign_payload)
    finally:
        worker.terminate()
        try:
            worker.wait(timeout=5)
        except subprocess.TimeoutExpired:
            worker.kill()
            worker.wait(timeout=5)
        socket_path.unlink(missing_ok=True)

    assert first.returncode == 0
    assert json.loads(first.stdout) == {"permission": "allow"}
    assert second.returncode == 0
    assert json.loads(second.stdout) == {"permission": "allow"}


def test_worker_socket_allow_after_bundle_allow():
    """RV-NEW-001: bundle allow must not suppress a later single-policy allow on the same socket."""
    socket_path = _short_socket_path()
    benign_payload = json.loads((FIXTURES_DIR / "cursor-bash-benign.json").read_text(encoding="utf-8"))
    worker = subprocess.Popen(
        [sys.executable, str(WORKER_PATH), "--serve", "--socket", str(socket_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=REPO_ROOT,
    )
    try:
        _wait_for_socket(socket_path, worker)
        bundle = _run_worker_socket_policy(
            socket_path,
            [
                "--bundle",
                "cursor-destructive-shell-guard,cursor-protected-file-guard",
            ],
            benign_payload,
        )
        single = _run_worker_socket_policy(socket_path, ["cursor-destructive-shell-guard"], benign_payload)
    finally:
        worker.terminate()
        try:
            worker.wait(timeout=5)
        except subprocess.TimeoutExpired:
            worker.kill()
            worker.wait(timeout=5)
        socket_path.unlink(missing_ok=True)

    assert bundle.returncode == 0
    assert json.loads(bundle.stdout) == {"permission": "allow"}
    assert single.returncode == 0
    assert json.loads(single.stdout) == {"permission": "allow"}


def test_dispatcher_worker_socket_missing_falls_back(tmp_path: Path):
    payload = json.loads((FIXTURES_DIR / "cursor-bash-destructive.json").read_text(encoding="utf-8"))
    completed = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "hooks" / "wagents-hook.py"),
            "--worker-socket",
            str(tmp_path / "missing.sock"),
            "cursor-destructive-shell-guard",
            "--harness",
            "cursor",
        ],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert completed.returncode == 0
    assert json.loads(completed.stdout)["permission"] == "deny"


def test_worker_client_rejects_malformed_response():
    socket_path = _short_socket_path()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(socket_path))
    server.listen(1)

    def serve_once() -> None:
        conn, _addr = server.accept()
        with conn:
            conn.recv(4096)
            conn.sendall(b'{"stdout":"","exit_code":"cursor"}\n')

    thread = threading.Thread(target=serve_once)
    thread.start()
    try:
        spec = importlib.util.spec_from_file_location("wagents_hook_client_under_test", CLIENT_PATH)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.forward_request(socket_path, {"payload": {}}, timeout=1.0) is None
    finally:
        thread.join(timeout=1)
        server.close()
        socket_path.unlink(missing_ok=True)


def test_worker_module_loads_dispatcher():
    spec = importlib.util.spec_from_file_location("wagents_hook_worker_under_test", WORKER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    dispatcher = module._load_dispatcher()
    assert "cursor-destructive-shell-guard" in dispatcher.POLICIES


def test_worker_client_forward_request_round_trip():
    """Socket clients must receive a response without makefile half-close deadlock."""
    socket_path = _short_socket_path()
    benign_payload = json.loads((FIXTURES_DIR / "cursor-bash-benign.json").read_text(encoding="utf-8"))
    request = {"policy_id": "cursor-destructive-shell-guard", "harness": "cursor", "payload": benign_payload}
    worker = subprocess.Popen(
        [sys.executable, str(WORKER_PATH), "--serve", "--socket", str(socket_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=REPO_ROOT,
    )
    try:
        _wait_for_socket(socket_path, worker)
        spec = importlib.util.spec_from_file_location("wagents_hook_client_round_trip", CLIENT_PATH)
        assert spec is not None
        assert spec.loader is not None
        client = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(client)
        response = client.forward_request(socket_path, request)
        assert response is not None
        assert response["exit_code"] == 0
        assert json.loads(response["stdout"]) == {"permission": "allow"}
    finally:
        worker.terminate()
        try:
            worker.wait(timeout=5)
        except subprocess.TimeoutExpired:
            worker.kill()
            worker.wait(timeout=5)
        socket_path.unlink(missing_ok=True)


def _forward_ndjson_to_worker(worker: subprocess.Popen[str], request: dict) -> dict:
    assert worker.stdin is not None
    assert worker.stdout is not None
    worker.stdin.write(json.dumps(request) + "\n")
    worker.stdin.flush()
    line = worker.stdout.readline()
    assert line.strip(), "worker closed stdout before responding"
    response = json.loads(line)
    assert response.get("exit_code") == 0
    return response


def test_worker_soft_gate_warm_ndjson_faster_than_cold_spawn():
    """T-070e: warm ``--serve`` NDJSON worker should beat repeated cold dispatcher spawns."""
    iterations = 20
    benign_payload = json.loads((FIXTURES_DIR / "cursor-bash-benign.json").read_text(encoding="utf-8"))
    cold_cmd = [
        sys.executable,
        str(REPO_ROOT / "hooks" / "wagents-hook.py"),
        "cursor-destructive-shell-guard",
        "--harness",
        "cursor",
    ]
    cold_input = json.dumps(benign_payload)
    warm_request = {
        "policy_id": "cursor-destructive-shell-guard",
        "harness": "cursor",
        "payload": benign_payload,
    }

    worker = subprocess.Popen(
        [sys.executable, str(WORKER_PATH), "--serve"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        cwd=REPO_ROOT,
    )
    try:
        for _ in range(3):
            _forward_ndjson_to_worker(worker, warm_request)

        cold_started = time.monotonic()
        for _ in range(iterations):
            subprocess.run(
                cold_cmd,
                input=cold_input,
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
                check=True,
            )
        cold_elapsed = time.monotonic() - cold_started

        warm_started = time.monotonic()
        for _ in range(iterations):
            _forward_ndjson_to_worker(worker, warm_request)
        warm_elapsed = time.monotonic() - warm_started
    finally:
        if worker.stdin is not None:
            worker.stdin.close()
        worker.terminate()
        try:
            worker.wait(timeout=5)
        except subprocess.TimeoutExpired:
            worker.kill()
            worker.wait(timeout=5)

    assert warm_elapsed > 0
    speedup = cold_elapsed / warm_elapsed
    assert speedup >= 1.5, f"expected warm worker >=1.5x faster than cold spawn; got {speedup:.2f}x"


def test_forward_default_timeout_single_policy_succeeds():
    """RV-S-004: production default forward timeout works after worker warmup."""
    socket_path = _short_socket_path()
    benign_payload = json.loads((FIXTURES_DIR / "cursor-bash-benign.json").read_text(encoding="utf-8"))
    request = {"policy_id": "cursor-destructive-shell-guard", "harness": "cursor", "payload": benign_payload}
    worker = subprocess.Popen(
        [sys.executable, str(WORKER_PATH), "--serve", "--socket", str(socket_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=REPO_ROOT,
    )
    client = _load_hook_client_module()
    try:
        _wait_for_socket(socket_path, worker)
        for _ in range(3):
            assert client.forward_request(socket_path, request) is not None
        response = client.forward_request(socket_path, request)
        assert response is not None
        assert response["exit_code"] == 0
        assert json.loads(response["stdout"]) == {"permission": "allow"}
    finally:
        worker.terminate()
        try:
            worker.wait(timeout=5)
        except subprocess.TimeoutExpired:
            worker.kill()
            worker.wait(timeout=5)
        socket_path.unlink(missing_ok=True)


def test_forward_bundle_uses_derived_timeout(monkeypatch):
    """RV-S-004: bundle worker forwards wait bundle_timeout + safety margin."""
    wagents_hook = _load_wagents_hook_module()
    captured: dict[str, float] = {}

    def _capture_forward(socket_path, request, timeout=5.0):
        captured["timeout"] = timeout
        return {"stdout": '{"permission":"allow"}\n', "exit_code": 0}

    class _FakeClient:
        DEFAULT_FORWARD_TIMEOUT_SECONDS = 5.0

        @staticmethod
        def forward_request(socket_path, request, timeout=5.0):
            return _capture_forward(socket_path, request, timeout=timeout)

    monkeypatch.setattr(wagents_hook, "_load_worker_client_module", lambda: _FakeClient())
    result = wagents_hook._forward_to_worker(
        socket_path="/tmp/fake.sock",
        request={"bundle": ["cursor-destructive-shell-guard"], "bundle_timeout": 30.0},
        timeout=30.0 + wagents_hook._FORWARD_TIMEOUT_MARGIN_SECONDS,
    )
    assert result is not None
    assert captured["timeout"] == 31.0


def test_forward_single_policy_uses_derived_timeout(monkeypatch):
    """RV-S-009: single-policy worker forwards wait forward_timeout + safety margin."""
    wagents_hook = _load_wagents_hook_module()
    captured: dict[str, float | None] = {}
    registry_timeout = float(wagents_hook.IMAGE_OPTIMIZER_REGISTRY_TIMEOUT_SECONDS)

    def _capture_forward(*, socket_path, request, timeout=None):
        captured["timeout"] = timeout
        return {"stdout": '{"permission":"allow"}\n', "exit_code": 0}

    monkeypatch.setattr(wagents_hook, "_forward_to_worker", _capture_forward)
    monkeypatch.setattr(
        wagents_hook,
        "_load_payload",
        lambda: json.loads((FIXTURES_DIR / "cursor-bash-benign.json").read_text(encoding="utf-8")),
    )
    code = wagents_hook.main(
        [
            "image-input-optimizer-guard",
            "--harness",
            "cursor",
            "--worker-socket",
            "/tmp/fake.sock",
            "--forward-timeout",
            str(registry_timeout),
        ]
    )
    assert code == 0
    assert captured["timeout"] == registry_timeout + wagents_hook._FORWARD_TIMEOUT_MARGIN_SECONDS


def test_worker_soft_gate_warm_socket_faster_than_cold_spawn():
    """T-070e / RV-S-003: Unix socket forwards should beat repeated cold spawns."""
    iterations = 20
    benign_payload = json.loads((FIXTURES_DIR / "cursor-bash-benign.json").read_text(encoding="utf-8"))
    cold_cmd = [
        sys.executable,
        str(HOOK_PATH),
        "cursor-destructive-shell-guard",
        "--harness",
        "cursor",
    ]
    cold_input = json.dumps(benign_payload)
    warm_request = {
        "policy_id": "cursor-destructive-shell-guard",
        "harness": "cursor",
        "payload": benign_payload,
    }
    client = _load_hook_client_module()
    socket_path = _short_socket_path()
    worker = subprocess.Popen(
        [sys.executable, str(WORKER_PATH), "--serve", "--socket", str(socket_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=REPO_ROOT,
    )
    try:
        _wait_for_socket(socket_path, worker)
        for _ in range(3):
            assert client.forward_request(socket_path, warm_request) is not None

        cold_started = time.monotonic()
        for _ in range(iterations):
            subprocess.run(
                cold_cmd,
                input=cold_input,
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
                check=True,
            )
        cold_elapsed = time.monotonic() - cold_started

        warm_started = time.monotonic()
        for _ in range(iterations):
            assert client.forward_request(socket_path, warm_request) is not None
        warm_elapsed = time.monotonic() - warm_started
    finally:
        worker.terminate()
        try:
            worker.wait(timeout=5)
        except subprocess.TimeoutExpired:
            worker.kill()
            worker.wait(timeout=5)
        socket_path.unlink(missing_ok=True)

    assert warm_elapsed > 0
    speedup = cold_elapsed / warm_elapsed
    assert speedup >= 1.5, f"expected warm socket >=1.5x faster than cold spawn; got {speedup:.2f}x"
