from __future__ import annotations

import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

import wagents.process_lifecycle as process_lifecycle

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "_candidate_cli_canaries",
        ROOT / "scripts" / "run_candidate_cli_canaries.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _assert_pid_gone(pid: int) -> None:
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.01)
    pytest.fail(f"process {pid} survived lifecycle cleanup")


def _timeout_process_sources(*, ignore_term: bool = True) -> tuple[str, str]:
    term_handler = "signal.signal(signal.SIGTERM, signal.SIG_IGN)" if ignore_term else ""
    child_term_handler = (
        ""
        if ignore_term
        else """
def exit_after_descendant(_signal_number, _frame):
    descendant_process.wait()
    raise SystemExit(0)

signal.signal(signal.SIGTERM, exit_after_descendant)
"""
    )
    descendant_source = f"""
import os
from pathlib import Path
import signal
import sys
import time

{term_handler}
print("descendant-stdout", flush=True)
print("descendant-stderr", file=sys.stderr, flush=True)
Path(sys.argv[1]).write_text(str(os.getpid()), encoding="utf-8")
while True:
    time.sleep(1)
"""
    child_source = f"""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

child_pid_path = Path(sys.argv[1])
descendant_pid_path = Path(sys.argv[2])
ready_path = Path(sys.argv[3])
child_pid_path.write_text(str(os.getpid()), encoding="utf-8")
descendant_process = subprocess.Popen([sys.executable, "-c", {descendant_source!r}, str(descendant_pid_path)])
{child_term_handler}
deadline = time.monotonic() + 5
while not descendant_pid_path.exists() and time.monotonic() < deadline:
    time.sleep(0.01)
if not descendant_pid_path.exists():
    raise SystemExit(2)
print("child-stdout", flush=True)
print("child-stderr", file=sys.stderr, flush=True)
ready_path.write_text("ready", encoding="utf-8")
while True:
    time.sleep(1)
"""
    return child_source, descendant_source


def _force_timeout_after_process_tree_ready(
    module,
    monkeypatch: pytest.MonkeyPatch,
    ready_path: Path,
) -> None:
    real_popen = subprocess.Popen
    launch_count = 0

    class ReadyTimeoutProcess:
        def __init__(self, process: subprocess.Popen[str]) -> None:
            self._process = process
            self._first_communicate = True

        @property
        def pid(self) -> int:
            return self._process.pid

        @property
        def returncode(self) -> int | None:
            return self._process.returncode

        def communicate(self, *args, **kwargs):
            if self._first_communicate:
                self._first_communicate = False
                deadline = time.monotonic() + 30
                while not ready_path.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                raise subprocess.TimeoutExpired(self._process.args, kwargs.get("timeout", 0))
            return self._process.communicate(*args, **kwargs)

        def poll(self) -> int | None:
            return self._process.poll()

        def wait(self, *args, **kwargs) -> int:
            return self._process.wait(*args, **kwargs)

    def tracked_popen(*args, **kwargs):
        nonlocal launch_count
        process = real_popen(*args, **kwargs)
        launch_count += 1
        if launch_count == 1:
            assert kwargs["start_new_session"] is True
            return ReadyTimeoutProcess(process)
        return process

    monkeypatch.setattr(module.subprocess, "Popen", tracked_popen)


def test_every_binding_references_a_probe() -> None:
    module = _module()
    assert module.PROBE_BINDINGS
    assert set(module.PROBE_BINDINGS.values()) <= set(module.PROBES)


def test_every_runtime_cli_has_a_semantic_probe() -> None:
    module = _module()
    activation = module.activation_module()
    expected = {
        (url, str(seed["kind"]))
        for url, rows in activation.runtime_specs().items()
        for seed in rows
        if seed.get("kind") in {"cli", "library"}
    }
    assert len([item for item in expected if item[1] == "cli"]) == 30
    assert expected == set(module.PROBE_BINDINGS)


def test_sanitized_env_strips_secret_shaped_names(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    monkeypatch.setenv("EXAMPLE_API_KEY", "do-not-copy")
    monkeypatch.setenv("EXAMPLE_TOKEN", "do-not-copy")
    monkeypatch.setenv("SAFE_VALUE", "do-not-copy")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "do-not-copy")
    monkeypatch.setenv("DATABASE_URL", "do-not-copy")

    env = module.sanitized_env(home=tmp_path)

    assert "EXAMPLE_API_KEY" not in env
    assert "EXAMPLE_TOKEN" not in env
    assert "SAFE_VALUE" not in env
    assert "AWS_SECRET_ACCESS_KEY" not in env
    assert "DATABASE_URL" not in env
    assert env["HOME"] == str(tmp_path)


@pytest.mark.skipif(os.name != "posix", reason="requires POSIX process groups")
def test_run_timeout_exits_during_term_grace_without_kill(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _module()
    child_source, _descendant_source = _timeout_process_sources(ignore_term=False)
    child_pid_path = tmp_path / "child.pid"
    descendant_pid_path = tmp_path / "descendant.pid"
    ready_path = tmp_path / "ready"
    signalled: list[int] = []
    real_signal = process_lifecycle._send_process_group_signal

    monkeypatch.setattr(
        module,
        "_prepare_candidate_launch",
        lambda argv, *, cwd, env: (argv, env, argv),
    )
    _force_timeout_after_process_tree_ready(module, monkeypatch, ready_path)

    def tracked_signal(process_group_id: int, signal_number: int) -> None:
        signalled.append(signal_number)
        real_signal(process_group_id, signal_number)

    monkeypatch.setattr(process_lifecycle, "_send_process_group_signal", tracked_signal)

    with pytest.raises(RuntimeError, match="canary timed out"):
        module.run(
            [
                sys.executable,
                "-c",
                child_source,
                str(child_pid_path),
                str(descendant_pid_path),
                str(ready_path),
            ],
            cwd=tmp_path,
            env={},
            timeout=60,
        )

    assert signalled == [signal.SIGTERM]
    _assert_pid_gone(int(child_pid_path.read_text(encoding="utf-8")))
    _assert_pid_gone(int(descendant_pid_path.read_text(encoding="utf-8")))


@pytest.mark.skipif(os.name != "posix", reason="requires POSIX process groups")
def test_run_timeout_cleans_process_group_descendant_and_drains_pipes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _module()
    child_source, _descendant_source = _timeout_process_sources()
    child_pid_path = tmp_path / "child.pid"
    descendant_pid_path = tmp_path / "descendant.pid"
    ready_path = tmp_path / "ready"
    parent_process_group = os.getpgrp()
    cleanup_output: dict[str, tuple[str, str]] = {}
    signalled: list[tuple[int, int]] = []
    real_cleanup = module.terminate_process_group
    real_signal = process_lifecycle._send_process_group_signal

    monkeypatch.setattr(
        module,
        "_prepare_candidate_launch",
        lambda argv, *, cwd, env: (argv, env, argv),
    )
    _force_timeout_after_process_tree_ready(module, monkeypatch, ready_path)

    def checked_signal(process_group_id: int, signal_number: int) -> None:
        assert process_group_id != parent_process_group
        signalled.append((process_group_id, signal_number))
        real_signal(process_group_id, signal_number)

    def tracked_cleanup(process):
        assert os.getpgid(process.pid) == process.pid
        result = real_cleanup(process)
        cleanup_output["streams"] = result
        return result

    monkeypatch.setattr(process_lifecycle, "_send_process_group_signal", checked_signal)
    monkeypatch.setattr(module, "terminate_process_group", tracked_cleanup)

    with pytest.raises(RuntimeError, match="canary timed out"):
        module.run(
            [
                sys.executable,
                "-c",
                child_source,
                str(child_pid_path),
                str(descendant_pid_path),
                str(ready_path),
            ],
            cwd=tmp_path,
            env={},
            timeout=60,
        )

    assert ready_path.exists(), "process tree did not become ready before the bounded timeout"
    child_pid = int(child_pid_path.read_text(encoding="utf-8"))
    descendant_pid = int(descendant_pid_path.read_text(encoding="utf-8"))
    assert child_pid == signalled[0][0]
    assert signalled == [
        (child_pid, signal.SIGTERM),
        (child_pid, signal.SIGKILL),
    ]
    assert os.getpgrp() == parent_process_group
    _assert_pid_gone(child_pid)
    _assert_pid_gone(descendant_pid)
    stdout, stderr = cleanup_output["streams"]
    assert {"child-stdout", "descendant-stdout"} <= set(stdout.splitlines())
    assert {"child-stderr", "descendant-stderr"} <= set(stderr.splitlines())

    later = module.run(
        [sys.executable, "-c", "print('later-cli-probe')"],
        cwd=tmp_path,
        env={},
    )
    assert later.stdout == "later-cli-probe\n"
    assert later.stderr == ""


def test_receipt_writer_is_deterministic(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    output = tmp_path / "receipts.json"
    monkeypatch.setattr(module, "RECEIPTS", output)
    monkeypatch.setattr(module, "RUNTIME_STATE", tmp_path / "state")
    monkeypatch.setattr(
        module,
        "run_after_process_lifecycle_gate",
        lambda operation: operation(),
    )
    rows = {
        ("b", "install"): {"artifact_id": "b", "phase": "install"},
        ("a", "behavior"): {"artifact_id": "a", "phase": "behavior"},
    }

    output.write_text(
        json.dumps({
            "version": 2,
            "revision": 0,
            "receipts": [],
            "closure_receipts": [{"gate_id": "docs-closure"}],
        })
        + "\n",
        encoding="utf-8",
    )
    module.write_receipts(rows)

    assert [row["artifact_id"] for row in module.read_receipts().values()] == ["a", "b"]
    assert module.read_receipt_document()["closure_receipts"] == [{"gate_id": "docs-closure"}]


def test_directory_digest_changes_with_package_content(tmp_path: Path) -> None:
    module = _module()
    package = tmp_path / "package"
    package.mkdir()
    source = package / "index.js"
    source.write_text("one\n", encoding="utf-8")
    before = module.file_digest([package])
    source.write_text("two\n", encoding="utf-8")
    assert module.file_digest([package]) != before

    dependency = package / "node_modules" / "dependency"
    dependency.mkdir(parents=True)
    dependency_file = dependency / "index.js"
    dependency_file.write_text("one\n", encoding="utf-8")
    with_dependency = module.file_digest([package])
    dependency_file.write_text("two\n", encoding="utf-8")
    assert module.file_digest([package]) != with_dependency


def test_installed_version_reads_matching_npm_manifest(tmp_path: Path) -> None:
    module = _module()
    package = tmp_path / "package"
    package.mkdir()
    (package / "package.json").write_text(
        '{"name":"example-tool","version":"2.0.0"}\n',
        encoding="utf-8",
    )
    seed = {"package_manager": "npm", "package_name": "example-tool"}
    assert module.installed_version(seed, [package]) == "2.0.0"


def test_managed_executable_resolution_ignores_host_path_shadowing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = _module()
    runtime = tmp_path / "runtime"
    package = runtime / "node_modules" / "example-tool"
    target = package / "bin" / "example.js"
    target.parent.mkdir(parents=True)
    target.write_text("#!/usr/bin/env node\n", encoding="utf-8")
    target.chmod(0o755)
    binary = runtime / "node_modules" / ".bin" / "example"
    binary.parent.mkdir()
    binary.symlink_to(target)
    poison = tmp_path / "poison"
    poison.mkdir()
    poisoned_binary = poison / "example"
    poisoned_binary.write_text("#!/bin/sh\n", encoding="utf-8")
    poisoned_binary.chmod(0o755)
    monkeypatch.setattr(module, "DEFAULT_NODE_RUNTIME_ROOT", runtime)
    monkeypatch.setenv("PATH", str(poison))

    mapping = module.resolve_managed_executables([
        {"package_manager": "npm", "package_name": "example-tool", "executables": ["example"]}
    ])
    env = module.sanitized_env()
    env[module.EXECUTABLE_MAP_ENV] = json.dumps({"example": str(mapping["example"])})

    assert mapping["example"] == target.resolve()
    assert module.resolve_probe_argv(["example", "--version"], env)[0] == str(target.resolve())
    assert env["PATH"] == module.CONTROLLED_SYSTEM_PATH


def test_resolve_probe_argv_preserves_validated_mapped_symlink_path(tmp_path: Path) -> None:
    module = _module()
    target = tmp_path / "target"
    target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    target.chmod(0o755)
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    clone = isolated / "example"
    clone.symlink_to(target)
    env = {module.EXECUTABLE_MAP_ENV: json.dumps({"example": str(clone)})}

    argv = module.resolve_probe_argv(["example", "--version"], env)

    assert argv == [str(clone), "--version"]
    assert Path(argv[0]).resolve() == target


def test_repeat_probe_records_lexical_launch_and_realpath(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    target = tmp_path / "target"
    target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    target.chmod(0o755)
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    clone = isolated / "example"
    clone.symlink_to(target)
    pids = iter((101, 202))

    monkeypatch.setattr(module, "_candidate_read_roots", lambda _mapping: ())
    monkeypatch.setattr(module, "_trusted_runtime_path", lambda _fixture: (module.CONTROLLED_SYSTEM_PATH, ()))
    monkeypatch.setattr(module, "sandbox_environment", lambda env, **_kwargs: env)

    def fake_probe(_fixture: Path, _env: dict[str, str]) -> module.ProcessResult:
        return module.ProcessResult(
            ("sandbox",),
            0,
            "ok",
            "",
            next(pids),
            candidate_argv=(str(clone), "--version"),
        )

    result = module.repeat_probe("example", fake_probe, {"example": clone})

    assert result.launch_paths == (str(clone), str(clone))
    assert result.launch_realpaths == (str(target), str(target))


def test_refine_probe_launches_managed_cli_and_cleans_foreground_lifecycle(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    calls: list[list[str]] = []

    monkeypatch.setattr(module, "probe_executable", lambda _env, _name: tmp_path / "refine")
    monkeypatch.setattr(module, "free_loopback_port", lambda: 42424)

    def fake_run_server(argv, *, cwd, env, ready_url, assertion):
        calls.append(argv)
        assert cwd == tmp_path
        assert env["REFINE_AGENT_CMD"] == "/usr/bin/false"
        assert ready_url == "http://127.0.0.1:42424/health"
        assertion(200, '{"version":"0.3.34"}')
        return module.ProcessResult(tuple(argv), 0, "ok", "", 101, tuple(argv))

    def fake_run(argv, *, cwd, env, **_kwargs):
        assert cwd == tmp_path
        assert env["REFINE_RELAY_PORT"] == "42424"
        return module.ProcessResult(tuple(argv), 1, "Refine usage", "", 202, tuple(argv))

    monkeypatch.setattr(module, "run_server", fake_run_server)
    monkeypatch.setattr(module, "run", fake_run)
    monkeypatch.setattr(module, "http_get", lambda _url: (404, "missing"))

    result = module.probe_refine(tmp_path, {})

    assert calls == [["refine", "live", "--foreground", "--page", str(tmp_path / "index.html"), "--port", "42424"]]
    assert result.candidate_argv[0] == "refine"
    assert (tmp_path / "index.html").read_text(encoding="utf-8").endswith("<main>Probe</main></body></html>\n")


def test_cli_launch_boundary_wraps_required_candidate_sandbox(tmp_path: Path) -> None:
    module = _module()
    env = module.sandbox_environment(
        module.sanitized_env(home=tmp_path),
        read_roots=(Path(sys.prefix), Path(sys.base_prefix)),
        write_roots=(tmp_path,),
        network_policy="none",
    )

    argv, child_env, candidate_argv = module._prepare_candidate_launch(
        [sys.executable, "-c", "pass"],
        cwd=tmp_path,
        env=env,
    )

    assert Path(argv[0]).name == "sandbox-exec"
    assert "(deny network*)" in argv[2]
    assert candidate_argv == [sys.executable, "-c", "pass"]
    assert module.EXECUTABLE_MAP_ENV not in child_env


def test_cli_network_policies_are_exact_and_probe_scoped() -> None:
    module = _module()
    assert module.PROBE_NETWORK_POLICIES == {
        "better-icons": "external",
        "gws": "external",
        "tanstack": "external",
        "openspec-ui": "loopback",
        "refine": "loopback",
        "specboard": "loopback",
        "tot": "loopback",
    }


def test_cli_file_watch_capability_is_specboard_only(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    captured: list[bool] = []

    def fake_sandbox_environment(env, **kwargs):
        captured.append(bool(kwargs.get("allow_file_watch")))
        return env

    monkeypatch.setattr(module, "sandbox_environment", fake_sandbox_environment)
    monkeypatch.setattr(module, "_candidate_read_roots", lambda _mapping: ())
    monkeypatch.setattr(module, "_trusted_runtime_path", lambda _fixture: (module.CONTROLLED_SYSTEM_PATH, ()))

    def fake_probe(_fixture: Path, _env: dict[str, str]) -> module.ProcessResult:
        return module.ProcessResult(("probe",), 0, "ok", "", len(captured))

    module.repeat_probe("specboard", fake_probe, {})
    module.repeat_probe("tot", fake_probe, {})

    assert captured == [True, True, False, False]


def test_openspec_pw_prerequisite_shims_are_exactly_scoped(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "trusted-bin").mkdir()

    module.write_openspec_pw_prerequisite_shims(tmp_path)

    npm = tmp_path / "trusted-bin" / "npm"
    npx = tmp_path / "trusted-bin" / "npx"
    assert subprocess.run([npm, "--version"], check=False, capture_output=True).returncode == 0
    assert subprocess.run([npx, "openspec", "--version"], check=False, capture_output=True).returncode == 0
    assert subprocess.run([npm, "install"], check=False, capture_output=True).returncode == 64
    assert subprocess.run([npx, "other"], check=False, capture_output=True).returncode == 64


def test_node_promotion_state_must_prove_exact_rollback(tmp_path: Path, monkeypatch) -> None:
    module = _module()
    state = tmp_path / "state.json"
    state.write_text('{"preimage_digest":"before","rollback_digest":"after"}\n')
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_candidate_cli_canaries.py", "--node-promotion-state", str(state)],
    )
    with pytest.raises(ValueError, match="exact rollback"):
        module.main()


def test_fixture_mcp_server_is_valid_python(tmp_path: Path) -> None:
    module = _module()
    server = tmp_path / "server.py"
    module._write_fixture_mcp_server(server)
    compile(server.read_text(encoding="utf-8"), str(server), "exec")
