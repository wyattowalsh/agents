from __future__ import annotations

import json
import socket
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from wagents import candidate_sandbox


def test_profile_is_deny_by_default_and_network_is_tiered(tmp_path: Path) -> None:
    read_root = tmp_path / "runtime"
    write_root = tmp_path / "fixture"
    read_root.mkdir()
    write_root.mkdir()

    denied = candidate_sandbox.macos_sandbox_profile(
        read_roots=(read_root,),
        write_roots=(write_root,),
        network_policy="none",
    )
    loopback = candidate_sandbox.macos_sandbox_profile(
        read_roots=(read_root,),
        write_roots=(write_root,),
        network_policy="loopback",
    )
    external = candidate_sandbox.macos_sandbox_profile(
        read_roots=(read_root,),
        write_roots=(write_root,),
        network_policy="external",
    )

    assert "(deny default)" in denied
    assert "(deny network*)" in denied
    assert '(allow network-inbound (local ip "localhost:*"))' in loopback
    assert '(allow network-outbound (remote ip "localhost:*"))' in loopback
    assert "(allow network-outbound)" in external
    assert "(allow network-inbound)" not in external
    assert "(allow process*)" not in denied
    assert "(allow process-fork)" in denied
    assert "(allow process-exec " in denied
    assert str(read_root.resolve()) in denied
    assert str(write_root.resolve()) in denied
    assert f'(literal "{tmp_path.parent}")' in denied
    assert "(allow file-read*)" not in denied
    assert "(allow file-write*)" not in denied
    assert "com.apple.FSEvents" not in denied


def test_file_watch_capability_is_explicit_and_stripped_from_child_env(tmp_path: Path) -> None:
    executable = Path(sys.executable).resolve()
    env = candidate_sandbox.sandbox_environment(
        {"PATH": "/usr/bin:/bin"},
        read_roots=(Path(sys.prefix),),
        write_roots=(tmp_path,),
        allow_file_watch=True,
    )

    argv, child_env = candidate_sandbox.prepare_sandboxed_subprocess(
        [str(executable), "-c", "pass"], cwd=tmp_path, env=env
    )

    assert '(allow mach-lookup (global-name "com.apple.FSEvents"))' in argv[2]
    assert candidate_sandbox.SANDBOX_FILE_WATCH_ENV not in child_env


def test_profile_preserves_lexical_executable_symlink_hops(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    executable = runtime / "candidate"
    executable.symlink_to("/usr/bin/true")

    profile = candidate_sandbox.macos_sandbox_profile(
        read_roots=(executable,),
        write_roots=(tmp_path,),
        network_policy="none",
    )

    assert f'(subpath "{executable}")' in profile
    assert '(subpath "/usr/bin/true")' in profile


def test_macos_wrapper_fails_closed_when_sandbox_exec_is_missing(monkeypatch, tmp_path: Path) -> None:
    executable = Path(sys.executable).resolve()
    monkeypatch.setattr(candidate_sandbox.sys, "platform", "darwin")
    monkeypatch.setattr(candidate_sandbox, "SANDBOX_EXECUTABLE", tmp_path / "missing-sandbox-exec")

    with pytest.raises(RuntimeError, match="sandbox-exec is unavailable"):
        candidate_sandbox.sandboxed_argv(
            [str(executable), "-c", "pass"],
            read_roots=(Path(sys.prefix),),
            write_roots=(tmp_path,),
        )


def test_required_sandbox_fails_closed_on_unsupported_platform(monkeypatch, tmp_path: Path) -> None:
    executable = Path(sys.executable).resolve()
    monkeypatch.setattr(candidate_sandbox.sys, "platform", "linux")

    with pytest.raises(RuntimeError, match="unsupported on platform"):
        candidate_sandbox.sandboxed_argv(
            [str(executable), "-c", "pass"],
            read_roots=(Path(sys.prefix),),
            write_roots=(tmp_path,),
            required=True,
        )

    assert candidate_sandbox.sandboxed_argv(
        [str(executable), "-c", "pass"],
        read_roots=(Path(sys.prefix),),
        write_roots=(tmp_path,),
        required=False,
    ) == [str(executable), "-c", "pass"]


def test_prepare_wraps_and_strips_control_environment(monkeypatch, tmp_path: Path) -> None:
    executable = Path(sys.executable).resolve()
    fake_sandbox = tmp_path / "sandbox-exec"
    fake_sandbox.write_text("#!/bin/sh\n", encoding="utf-8")
    fake_sandbox.chmod(0o755)
    monkeypatch.setattr(candidate_sandbox.sys, "platform", "darwin")
    monkeypatch.setattr(candidate_sandbox, "SANDBOX_EXECUTABLE", fake_sandbox)
    env = candidate_sandbox.sandbox_environment(
        {"PATH": "/usr/bin:/bin", "VISIBLE": "yes"},
        read_roots=(Path(sys.prefix),),
        write_roots=(tmp_path,),
        network_policy="none",
    )

    argv, child_env = candidate_sandbox.prepare_sandboxed_subprocess(
        [str(executable), "-c", "pass"],
        cwd=tmp_path,
        env=env,
    )

    assert argv[0] == str(fake_sandbox)
    assert argv[1] == "-p"
    assert argv[-3:] == [str(executable), "-c", "pass"]
    assert child_env == {"PATH": "/usr/bin:/bin", "VISIBLE": "yes"}
    assert all(key not in child_env for key in candidate_sandbox.SANDBOX_CONTROL_ENV_KEYS)
    assert json.loads(env[candidate_sandbox.SANDBOX_WRITE_ROOTS_ENV]) == [str(tmp_path.resolve())]


def test_selected_javascript_roots_exclude_unrelated_siblings(tmp_path: Path) -> None:
    modules = tmp_path / "node_modules"
    package = modules / "candidate"
    dependency = modules / "owned-dependency"
    sibling = modules / "unrelated-sibling"
    executable = package / "bin/candidate.js"
    executable.parent.mkdir(parents=True)
    dependency.mkdir(parents=True)
    sibling.mkdir(parents=True)
    executable.write_text("#!/usr/bin/env node\n", encoding="utf-8")
    executable.chmod(0o755)
    (package / "package.json").write_text(
        '{"name":"candidate","dependencies":{"owned-dependency":"1.0.0"}}\n', encoding="utf-8"
    )
    (dependency / "package.json").write_text('{"name":"owned-dependency"}\n', encoding="utf-8")
    (sibling / "package.json").write_text('{"name":"unrelated-sibling"}\n', encoding="utf-8")

    roots = candidate_sandbox.selected_javascript_package_roots(executable)

    assert package.resolve() in roots
    assert dependency.resolve() in roots
    assert sibling.resolve() not in roots
    assert modules.resolve() not in roots


def _run_sandboxed_python(
    fixture: Path,
    code: str,
    *,
    network_policy: candidate_sandbox.NetworkPolicy = "none",
) -> subprocess.CompletedProcess[str]:
    fixture.mkdir(parents=True, exist_ok=True)
    home = fixture / "home"
    temporary = fixture / "tmp"
    home.mkdir(exist_ok=True)
    temporary.mkdir(exist_ok=True)
    executable = Path(sys.executable).resolve()
    env = candidate_sandbox.sandbox_environment(
        {
            "HOME": str(home),
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
            "TMPDIR": str(temporary),
        },
        read_roots=(Path(sys.prefix), Path(sys.base_prefix), executable, fixture),
        write_roots=(fixture,),
        network_policy=network_policy,
    )
    argv, child_env = candidate_sandbox.prepare_sandboxed_subprocess(
        [str(executable), "-c", code], cwd=fixture, env=env
    )
    return subprocess.run(argv, cwd=fixture, env=child_env, text=True, capture_output=True, timeout=10)


@pytest.mark.skipif(sys.platform != "darwin", reason="requires macOS Seatbelt")
def test_macos_seatbelt_denies_outside_read_and_write(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret\n", encoding="utf-8")
    attempted_write = tmp_path / "escaped.txt"
    code = f"""
from pathlib import Path
read_denied = write_denied = False
try:
    Path({str(outside)!r}).read_text()
except PermissionError:
    read_denied = True
try:
    Path({str(attempted_write)!r}).write_text('escape')
except PermissionError:
    write_denied = True
Path('inside.txt').write_text('owned')
print(read_denied, write_denied)
"""

    result = _run_sandboxed_python(fixture, code)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "True True"
    assert not attempted_write.exists()
    assert (fixture / "inside.txt").read_text(encoding="utf-8") == "owned"


@pytest.mark.skipif(sys.platform != "darwin", reason="requires macOS Seatbelt")
def test_macos_seatbelt_enforces_network_tiers(tmp_path: Path) -> None:
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    port = listener.getsockname()[1]

    def serve_once() -> None:
        connection, _ = listener.accept()
        with connection:
            connection.sendall(b"ok")

    thread = threading.Thread(target=serve_once, daemon=True)
    thread.start()
    none = _run_sandboxed_python(
        tmp_path / "none",
        f"import socket\ntry: socket.create_connection(('127.0.0.1',{port}))\nexcept PermissionError: print('denied')",
        network_policy="none",
    )
    loopback = _run_sandboxed_python(
        tmp_path / "loopback",
        f"import socket\ns=socket.create_connection(('127.0.0.1',{port})); print(s.recv(2).decode())",
        network_policy="loopback",
    )
    external_denied = _run_sandboxed_python(
        tmp_path / "loopback-external",
        (
            "import socket\ns=socket.socket(); s.settimeout(1)\n"
            "try: s.connect(('1.1.1.1',443))\nexcept PermissionError: print('denied')"
        ),
        network_policy="loopback",
    )
    external_bind = _run_sandboxed_python(
        tmp_path / "external-bind",
        "import socket\ns=socket.socket()\ntry: s.bind(('127.0.0.1',0))\nexcept PermissionError: print('denied')",
        network_policy="external",
    )
    listener.close()
    thread.join(timeout=5)

    assert none.returncode == 0, none.stderr
    assert none.stdout.strip() == "denied"
    assert loopback.returncode == 0, loopback.stderr
    assert loopback.stdout.strip() == "ok"
    assert external_denied.returncode == 0, external_denied.stderr
    assert external_denied.stdout.strip() == "denied"
    assert external_bind.returncode == 0, external_bind.stderr
    assert external_bind.stdout.strip() == "denied"


@pytest.mark.skipif(sys.platform != "darwin", reason="requires macOS Seatbelt")
def test_macos_seatbelt_restrictions_are_inherited_by_children(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret\n", encoding="utf-8")
    executable = str(Path(sys.executable).resolve())
    child = (
        f"from pathlib import Path\ntry: Path({str(outside)!r}).read_text()\n"
        "except PermissionError: print('child-denied')"
    )
    parent = (
        f"import subprocess\nr=subprocess.run([{executable!r},'-c',{child!r}],"
        "text=True,capture_output=True)\nprint(r.returncode, r.stdout.strip())"
    )

    result = _run_sandboxed_python(fixture, parent)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "0 child-denied"


@pytest.mark.skipif(sys.platform != "darwin", reason="requires macOS Seatbelt")
def test_macos_seatbelt_launches_installed_runtime_families(tmp_path: Path) -> None:
    candidates = (
        (Path(sys.executable), ("-c", "print('python-ok')")),
        (Path("/opt/homebrew/bin/node"), ("--version",)),
        (Path("/opt/homebrew/bin/bun"), ("--version",)),
        (Path("/opt/homebrew/bin/go"), ("version",)),
        (Path("/opt/homebrew/bin/cargo"), ("--version",)),
    )
    for candidate, arguments in candidates:
        if not candidate.exists():
            continue
        executable = candidate.resolve(strict=True)
        fixture = tmp_path / executable.name
        fixture.mkdir()
        argv = candidate_sandbox.sandboxed_argv(
            [str(executable), *arguments],
            read_roots=(*candidate_sandbox.selected_macos_runtime_roots(executable), fixture),
            write_roots=(fixture,),
            network_policy="none",
        )
        result = subprocess.run(
            argv,
            cwd=fixture,
            env={"HOME": str(fixture), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "TMPDIR": str(fixture)},
            text=True,
            capture_output=True,
            timeout=10,
        )
        assert result.returncode == 0, f"{candidate}: {result.stderr}"
