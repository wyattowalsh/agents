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
        "_candidate_plugin_canaries",
        ROOT / "scripts" / "run_candidate_plugin_canaries.py",
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


def test_enabled_plugin_probe_partition_is_exact() -> None:
    module = _module()
    expected = {
        "brooks-lint@awesome-codex-plugins",
        "codebase-recon@awesome-codex-plugins",
        "commit-narrator@candidate-corpus-local",
        "env-lint@candidate-corpus-local",
        "roadmapsmith@awesome-codex-plugins",
        "secret-guard@candidate-corpus-local",
        "universal-design-principles@awesome-codex-plugins",
        "unslop@awesome-codex-plugins",
    }

    assert expected == module.EXPECTED_ENABLED_PLUGINS
    assert set(module.SCRIPT_PLUGINS).isdisjoint(module.MODEL_PLUGINS)
    assert set(module.SCRIPT_PLUGINS | module.MODEL_PLUGINS) == expected


def test_runtime_specs_match_enabled_plugin_probe_partition() -> None:
    module = _module()
    assert set(module.enabled_plugin_specs()) == module.EXPECTED_ENABLED_PLUGINS


def test_sanitized_env_strips_secret_shaped_names(monkeypatch) -> None:
    module = _module()
    monkeypatch.setenv("PLUGIN_PROBE_API_KEY", "do-not-copy")
    monkeypatch.setenv("PLUGIN_PROBE_TOKEN", "do-not-copy")
    monkeypatch.setenv("PLUGIN_PROBE_SAFE", "kept")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "do-not-copy")
    monkeypatch.setenv("DATABASE_URL", "do-not-copy")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/private/credential.json")
    monkeypatch.setenv("LANG", "en_US.UTF-8")

    env = module.sanitized_env()

    assert "PLUGIN_PROBE_API_KEY" not in env
    assert "PLUGIN_PROBE_TOKEN" not in env
    assert "PLUGIN_PROBE_SAFE" not in env
    assert "AWS_SECRET_ACCESS_KEY" not in env
    assert "DATABASE_URL" not in env
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in env
    assert env["LANG"] == "en_US.UTF-8"
    assert env["PATH"] == module.FIXED_PATH
    assert Path(env["BASH"]).is_absolute()


def test_process_launch_identity_is_unique_even_if_pid_freshness_is_separate(tmp_path: Path) -> None:
    module = _module()
    env = module.sandbox_environment(
        module.sanitized_env(),
        read_roots=(Path(sys.prefix), Path(sys.base_prefix), module.PYTHON_EXECUTABLE),
        write_roots=(tmp_path,),
        network_policy="none",
    )
    first = module.run([str(module.PYTHON_EXECUTABLE), "-c", "pass"], cwd=tmp_path, env=env)
    second = module.run([str(module.PYTHON_EXECUTABLE), "-c", "pass"], cwd=tmp_path, env=env)

    assert first.pid > 0
    assert second.pid > 0
    assert len(first.launch_id) == 32
    assert len(second.launch_id) == 32
    assert first.launch_id != second.launch_id
    assert first.started_at_ns > 0
    assert second.started_at_ns >= first.started_at_ns


def test_run_fails_closed_without_sandbox_or_exact_trusted_operation(tmp_path: Path) -> None:
    module = _module()
    env = module.sanitized_env()

    with pytest.raises(RuntimeError, match="requires a declared sandbox"):
        module.run([str(module.PYTHON_EXECUTABLE), "--version"], cwd=tmp_path, env=env)
    with pytest.raises(RuntimeError, match="does not match"):
        module.run(
            [str(module.PYTHON_EXECUTABLE), "-c", "pass"],
            cwd=tmp_path,
            env=env,
            trusted_harness_operation="trusted-harness-fixed-version-probe",
        )
    with pytest.raises(RuntimeError, match="absolute executable"):
        module.run(["python3", "--version"], cwd=tmp_path, env=env)

    result = module.run(
        [str(module.PYTHON_EXECUTABLE), "--version"],
        cwd=tmp_path,
        env=env,
        trusted_harness_operation="trusted-harness-fixed-version-probe",
    )
    assert result.returncode == 0


def test_run_timeout_reports_only_digests(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _module()
    secret = "candidate-timeout-secret-value"

    class FakeProcess:
        returncode = -9
        pid = 123
        calls = 0

        def communicate(self, **_kwargs):
            self.calls += 1
            if self.calls == 1:
                raise subprocess.TimeoutExpired(cmd="probe", timeout=1)
            raise AssertionError("timeout cleanup must own the final pipe drain")

    def fake_popen(*_args, **kwargs):
        assert kwargs["start_new_session"] is True
        return FakeProcess()

    monkeypatch.setattr(module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(
        module,
        "prepare_sandboxed_subprocess",
        lambda argv, *, cwd, env: (argv, env),
    )
    monkeypatch.setattr(
        module,
        "terminate_process_group",
        lambda _process: (f"stdout {secret}", f"stderr {secret}"),
    )
    env = {module.SANDBOX_REQUIRED_ENV: "1"}

    with pytest.raises(RuntimeError) as raised:
        module.run(
            [str(module.PYTHON_EXECUTABLE), "--version"],
            cwd=tmp_path,
            env=env,
            timeout=1,
        )

    message = str(raised.value)
    assert secret not in message
    assert "stdout_sha256=" in message
    assert "stderr_sha256=" in message


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
        "prepare_sandboxed_subprocess",
        lambda argv, *, cwd, env: (argv, env),
    )
    _force_timeout_after_process_tree_ready(module, monkeypatch, ready_path)

    def tracked_signal(process_group_id: int, signal_number: int) -> None:
        signalled.append(signal_number)
        real_signal(process_group_id, signal_number)

    monkeypatch.setattr(process_lifecycle, "_send_process_group_signal", tracked_signal)
    env = {module.SANDBOX_REQUIRED_ENV: "1"}

    with pytest.raises(RuntimeError, match="plugin canary timed out"):
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
            env=env,
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
        "prepare_sandboxed_subprocess",
        lambda argv, *, cwd, env: (argv, env),
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
    env = {module.SANDBOX_REQUIRED_ENV: "1"}

    with pytest.raises(RuntimeError, match="plugin canary timed out"):
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
            env=env,
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
        [sys.executable, "-c", "print('later-plugin-probe')"],
        cwd=tmp_path,
        env=env,
    )
    assert later.stdout == "later-plugin-probe\n"
    assert later.stderr == ""


def test_main_fails_when_execution_is_required(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _module()
    plugin_id = "unslop@awesome-codex-plugins"
    url = "https://example.invalid/unslop"
    seed = {
        "kind": "plugin",
        "plugin_id": plugin_id,
        "plugin_enabled": True,
        "package_manager": "codex-plugin",
        "package_name": "unslop",
        "version": "1.0.0",
    }
    root = tmp_path / "plugin"
    root.mkdir()
    monkeypatch.setattr(module, "RECEIPTS", tmp_path / "receipts.json")
    monkeypatch.setattr(module, "RUNTIME_STATE", tmp_path / "state")
    monkeypatch.setattr(module, "all_plugin_specs", lambda: {plugin_id: (url, seed)})
    monkeypatch.setattr(module, "enabled_plugin_specs", lambda specs=None: {plugin_id: (url, seed)})
    monkeypatch.setattr(
        module,
        "activation_module",
        lambda: type("Activation", (), {"artifact_id": staticmethod(lambda _url, _seed: "artifact")})(),
    )
    monkeypatch.setattr(module, "source_shas", lambda: {url: "a" * 40})
    provenance = {"plugin_id": plugin_id}
    monkeypatch.setattr(module, "verified_provenance_lock", lambda _specs: {plugin_id: provenance})
    monkeypatch.setattr(
        module,
        "codex_plugin_live_state",
        lambda *_args: {
            "plugin_id": plugin_id,
            "installed": True,
            "enabled": True,
            "version": "1.0.0",
            "installed_path": str(root),
        },
    )
    monkeypatch.setattr(module, "marketplace_plugin_source", lambda *_args: root)
    monkeypatch.setattr(module, "verify_marketplace_checkout", lambda *_args: None)
    monkeypatch.setattr(module, "verify_plugin_content", lambda *_args, **_kwargs: "a" * 64)
    monkeypatch.setattr(module, "plugin_root", lambda _seed: root)
    receipts = tmp_path / "receipts.json"
    receipts.write_text(
        json.dumps({"version": 2, "revision": 0, "receipts": [], "closure_receipts": []}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_candidate_plugin_canaries.py", "--apply", "--plugin", plugin_id],
    )

    assert module.main() == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["applied"] is False
    assert payload["pending_execution"] is True
    assert payload["results"][0]["status"] == "execution-required"
    assert json.loads(receipts.read_text(encoding="utf-8"))["revision"] == 0


def test_model_sandbox_uses_public_system_ca_bundle(tmp_path: Path) -> None:
    module = _module()
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    env = module.isolated_env(tmp_path / "control")

    sandboxed = module.model_sandbox_env(env, fixture)

    assert sandboxed["SSL_CERT_FILE"] == "/etc/ssl/cert.pem"


def test_file_digest_ignores_runtime_caches(tmp_path: Path) -> None:
    module = _module()
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    source = plugin / "SKILL.md"
    source.write_text("one\n", encoding="utf-8")
    before = module.file_digest([plugin])

    cache = plugin / "__pycache__"
    cache.mkdir()
    bytecode = cache / "probe.pyc"
    bytecode.write_bytes(b"one")
    assert module.file_digest([plugin]) == before

    source.write_text("two\n", encoding="utf-8")
    assert module.file_digest([plugin]) != before


def test_file_digest_detects_mode_and_directory_symlink_changes(tmp_path: Path) -> None:
    module = _module()
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    executable = plugin / "probe.sh"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    first_target = plugin / "first"
    second_target = plugin / "second"
    first_target.mkdir()
    second_target.mkdir()
    link = plugin / "current"
    link.symlink_to(first_target.name, target_is_directory=True)
    before = module.file_digest([plugin])

    executable.chmod(0o755)
    after_mode = module.file_digest([plugin])
    assert after_mode != before

    link.unlink()
    link.symlink_to(second_target.name, target_is_directory=True)
    assert module.file_digest([plugin]) != after_mode


def test_model_prompts_do_not_echo_source_only_skill_evidence() -> None:
    module = _module()
    assert set(module.DISCOVERY_SPECS) == module.EXPECTED_ENABLED_PLUGINS
    for plugin_id, (selector, _request, evidence) in module.DISCOVERY_SPECS.items():
        prompt = module._model_prompt(plugin_id)
        assert selector in prompt
        assert evidence not in prompt
    assert "Put the exact requested H1 only in skill_evidence" in module._model_prompt(
        "brooks-lint@awesome-codex-plugins"
    )


def test_git_runtime_roots_include_homebrew_system_config_when_present() -> None:
    module = _module()
    system_config = Path("/opt/homebrew/etc/gitconfig")
    if system_config.is_file():
        assert system_config in module.executable_runtime_roots("git")


def test_model_event_parser_rejects_tools_and_named_unavailable_skill_context() -> None:
    module = _module()
    with pytest.raises(RuntimeError, match="forbidden tool"):
        module.parse_model_events(json.dumps({"type": "item.completed", "item": {"type": "command_execution"}}))
    events = module.parse_model_events(
        json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "skills context budget"}})
    )
    assert events
    budget_events = module.parse_model_events(
        json.dumps({
            "type": "item.completed",
            "item": {
                "type": "error",
                "message": "Skill descriptions were shortened to fit the 2% skills context budget.",
            },
        })
    )
    assert budget_events
    with pytest.raises(RuntimeError, match="error item"):
        module.parse_model_events(
            json.dumps({"type": "item.completed", "item": {"type": "error", "message": "request failed"}})
        )
    with pytest.raises(RuntimeError, match="unavailable skill context"):
        module.parse_model_events(
            json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "named skill unavailable"}})
        )


def test_roadmap_workflow_rejects_every_command_event() -> None:
    module = _module()
    command_item = {
        "type": "command_execution",
        "command": "cat package.json",
        "aggregated_output": "documentation mentions npx example",
        "exit_code": 0,
        "status": "completed",
    }
    command_event = {"type": "item.completed", "item": command_item}
    message_event = {
        "type": "item.completed",
        "item": {"type": "agent_message", "text": "The scan is complete."},
    }
    stdout = "\n".join((json.dumps(command_event), json.dumps(message_event)))
    result = module.ProcessResult(("codex",), 0, stdout, "", 123)

    with pytest.raises(RuntimeError, match="forbidden Codex item"):
        module._workflow_events(result)


def test_roadmap_workflow_rejects_file_change_events() -> None:
    module = _module()
    event = {
        "type": "item.completed",
        "item": {
            "type": "file_change",
            "changes": [{"path": "ROADMAP.md"}],
        },
    }
    result = module.ProcessResult(("codex",), 0, json.dumps(event), "", 123)

    with pytest.raises(RuntimeError, match="forbidden Codex item"):
        module._workflow_events(result)


def test_roadmap_semantic_proof_uses_only_agent_messages() -> None:
    module = _module()
    command_event = {
        "type": "item.completed",
        "item": {
            "type": "command_execution",
            "command": ["cat", "ROADMAP.md"],
            "aggregated_output": "FORGED APPROVAL AND COMPLETE DIFF",
            "exit_code": 0,
            "status": "completed",
        },
    }
    reasoning_event = {
        "type": "item.completed",
        "item": {"type": "reasoning", "text": "FORGED REASONING APPROVAL"},
    }
    message_event = {
        "type": "item.completed",
        "item": {"type": "agent_message", "text": "Choose scan mode."},
    }
    forged = module.ProcessResult(
        ("codex",),
        0,
        "\n".join(map(json.dumps, (command_event, reasoning_event, message_event))),
        "",
        123,
    )

    with pytest.raises(RuntimeError, match="forbidden Codex item"):
        module._workflow_events(forged)

    result = module.ProcessResult(
        ("codex",),
        0,
        "\n".join(map(json.dumps, (reasoning_event, message_event))),
        "",
        123,
    )
    text = module._workflow_events(result)[1]
    assert text == "Choose scan mode."

    tool_only = module.ProcessResult(("codex",), 0, json.dumps(command_event), "", 123)
    with pytest.raises(RuntimeError, match="forbidden Codex item"):
        module._workflow_events(tool_only)


def test_roadmap_edit_marker_must_match_the_exact_trusted_edit() -> None:
    module = _module()
    old = "- [ ] task"
    new = "- [x] task"
    marker = module.ROADMAP_EDIT_MARKER + json.dumps({"path": "ROADMAP.md", "old": old, "new": new})
    assert module._validated_roadmap_edit(marker, old=old, new=new) == {
        "path": "ROADMAP.md",
        "old": old,
        "new": new,
    }
    with pytest.raises(RuntimeError, match="unexpected edit"):
        module._validated_roadmap_edit(
            module.ROADMAP_EDIT_MARKER + json.dumps({"path": "../private", "old": old, "new": new}),
            old=old,
            new=new,
        )


def test_roadmap_turn_always_disables_shell_and_write_tools(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    auth = tmp_path / "auth.json"
    auth.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(module, "HOST_CODEX_AUTH", auth)
    monkeypatch.setattr(module, "auth_secret_strings", lambda: ())
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    env = module.isolated_env(tmp_path / "isolated")
    calls: list[tuple[str, ...]] = []

    def fake_run(argv, **_kwargs):
        calls.append(tuple(argv))
        stdout = "\n".join((
            json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
            json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "ok"}}),
        ))
        return module.ProcessResult(tuple(argv), 0, stdout, "", 123 + len(calls))

    monkeypatch.setattr(module, "run", fake_run)
    module._roadmap_turn(fixture, env, "question")
    module._roadmap_turn(fixture, env, "approved", session_id="thread-1")

    for call in calls:
        assert 'sandbox_mode="read-only"' in call
        assert "shell_tool" in call
        assert "unified_exec" in call
        assert "workspace-write" not in call
    assert calls[0][calls[0].index("-s") + 1] == "read-only"
    assert "-s" not in calls[1]
    destination = Path(env["CODEX_HOME"]) / "auth.json"
    assert destination.is_symlink()
    assert destination.resolve() == auth.resolve()


def test_prepare_model_auth_uses_read_only_link_without_copy(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    auth = tmp_path / "host-auth.json"
    auth.write_text('{"tokens":{"access_token":"fixture-secret"}}\n', encoding="utf-8")
    auth.chmod(0o600)
    monkeypatch.setattr(module, "HOST_CODEX_AUTH", auth)
    env = module.isolated_env(tmp_path / "isolated")

    before = module._auth_fingerprint()
    assert module.prepare_model_auth(env) == before

    destination = Path(env["CODEX_HOME"]) / "auth.json"
    assert destination.is_symlink()
    assert destination.resolve() == auth.resolve()
    assert module._auth_fingerprint() == before


def _write_minimal_plugin(root: Path, *, name: str) -> None:
    manifest = root / ".codex-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"name": name, "version": "1.0.0", "skills": "./skills/"}) + "\n")
    skill = root / "skills" / name / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(f"---\nname: {name}\ndescription: Fixture\n---\n\nFixture.\n")


def test_plugin_surface_gate_rejects_hooks_startup_and_unexpected_executables(tmp_path: Path) -> None:
    module = _module()
    plugin_id = "codebase-recon@awesome-codex-plugins"
    plugin = tmp_path / "plugin"
    _write_minimal_plugin(plugin, name="codebase-recon")
    module.validate_plugin_surfaces(plugin_id, plugin)

    hook = plugin / "hooks" / "start.sh"
    hook.parent.mkdir()
    hook.write_text("#!/bin/sh\n")
    hook.chmod(0o755)
    with pytest.raises(RuntimeError, match=r"(?:command or hook directory|shell executable)"):
        module.validate_plugin_surfaces(plugin_id, plugin)

    hook.unlink()
    hook.parent.rmdir()
    package = plugin / "package.json"
    package.write_text(json.dumps({"scripts": {"postinstall": "touch escaped"}}) + "\n")
    with pytest.raises(RuntimeError, match="lifecycle scripts"):
        module.validate_plugin_surfaces(plugin_id, plugin)


def test_plugin_surface_gate_rejects_manifest_mcp_before_model_execution(tmp_path: Path) -> None:
    module = _module()
    plugin_id = "codebase-recon@awesome-codex-plugins"
    plugin = tmp_path / "plugin"
    _write_minimal_plugin(plugin, name="codebase-recon")
    manifest = plugin / ".codex-plugin" / "plugin.json"
    payload = json.loads(manifest.read_text())
    payload["mcpServers"] = "./mcp.json"
    manifest.write_text(json.dumps(payload) + "\n")

    with pytest.raises(RuntimeError, match="startup keys"):
        module.validate_plugin_surfaces(plugin_id, plugin)


def test_trusted_roadmap_write_rejects_symlink_substitution(tmp_path: Path) -> None:
    module = _module()
    target = tmp_path / "target.md"
    target.write_text("before\n", encoding="utf-8")
    roadmap = tmp_path / "ROADMAP.md"
    roadmap.symlink_to(target.name)

    with pytest.raises(RuntimeError, match="not regular"):
        module._trusted_replace_regular_file(roadmap, expected="before\n", replacement="after\n")
    assert target.read_text(encoding="utf-8") == "before\n"


def test_direct_plugin_run_boundary_executes_inside_required_sandbox(tmp_path: Path) -> None:
    module = _module()
    env = module.sandbox_environment(
        module.sanitized_env(),
        read_roots=(Path(sys.prefix), Path(sys.base_prefix), Path(sys.executable)),
        write_roots=(tmp_path,),
        network_policy="none",
    )

    result = module.run(
        [sys.executable, "-c", "print('sandboxed-plugin-probe')"],
        cwd=tmp_path,
        env=env,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "sandboxed-plugin-probe"
    assert Path(result.argv[0]).name == "sandbox-exec"


def test_model_schemas_are_source_specific() -> None:
    module = _module()
    universal = module._model_schema("universal-design-principles@awesome-codex-plugins")
    brooks = module._model_schema("brooks-lint@awesome-codex-plugins")

    assert {"accessibility", "perception", "cognition", "interaction"} <= set(universal["required"])
    assert {"severity", "symptom", "source", "consequence", "remedy", "citation"} <= set(brooks["required"])
    assert "skill_nonces" in universal["required"]
    assert "runtime_nonce" not in universal["required"]
    assert "runtime_nonce" in brooks["required"]
    nonce_schema = universal["properties"]["skill_nonces"]
    assert set(nonce_schema["required"]) == set(module.UNIVERSAL_DESIGN_SKILL_SELECTORS)
    for field, source_selector in module.UNIVERSAL_DESIGN_FINDING_SOURCES.items():
        finding_schema = universal["properties"][field]
        assert finding_schema["minItems"] == finding_schema["maxItems"] == 1
        item = finding_schema["items"]
        assert set(item["required"]) == {
            "issue",
            "remediation",
            "principle_or_source_skill",
            "fixture_signal",
        }
        assert item["properties"]["issue"]["minLength"] == 1
        assert item["properties"]["remediation"]["minLength"] == 1
        assert item["properties"]["principle_or_source_skill"]["enum"] == [source_selector]
        assert item["properties"]["fixture_signal"]["enum"] == [module.UNIVERSAL_DESIGN_FIXTURE_SIGNALS[field]]


def test_universal_design_model_prompt_separates_source_evidence_from_findings() -> None:
    module = _module()

    prompt = module._model_prompt("universal-design-principles@awesome-codex-plugins")

    assert all(selector in prompt for selector in module.UNIVERSAL_DESIGN_SKILL_SELECTORS)
    assert "skill_nonces" in prompt
    assert "exact requested sentence only in skill_evidence" in prompt
    assert "review findings only in those structured arrays" in prompt


def _universal_design_payload(module):
    nonces = {
        selector: f"wagents-runtime-probe-fixture-{index}"
        for index, selector in enumerate(module.UNIVERSAL_DESIGN_SKILL_SELECTORS)
    }
    findings = {
        "accessibility": (
            "The empty aria-label leaves the icon button without an accessible name.",
            "Give the button a descriptive accessible name.",
        ),
        "perception": (
            "The red Failed text uses color as the only error cue.",
            "Add an icon and explicit error status in addition to color.",
        ),
        "cognition": (
            "Twelve navigation choices increase decision load.",
            "Group the choices and progressively disclose secondary navigation.",
        ),
        "interaction": (
            "The onclick div is a non-semantic click target without keyboard behavior.",
            "Use a button element with keyboard and focus behavior.",
        ),
    }
    payload = {"skill_nonces": dict(nonces)}
    for field, (issue, remediation) in findings.items():
        payload[field] = [
            {
                "issue": issue,
                "remediation": remediation,
                "principle_or_source_skill": module.UNIVERSAL_DESIGN_FINDING_SOURCES[field],
                "fixture_signal": module.UNIVERSAL_DESIGN_FIXTURE_SIGNALS[field],
            }
        ]
    return payload, nonces


def test_universal_design_payload_accepts_exact_selector_bound_evidence() -> None:
    module = _module()
    payload, nonces = _universal_design_payload(module)

    module._validate_universal_design_payload(payload, nonces)


def test_universal_design_payload_rejects_omitted_skill_nonce() -> None:
    module = _module()
    payload, nonces = _universal_design_payload(module)
    reported = payload["skill_nonces"]
    assert isinstance(reported, dict)
    reported.pop(module.UNIVERSAL_DESIGN_SKILL_SELECTORS[-1])

    with pytest.raises(RuntimeError, match="omitted or added a selector"):
        module._validate_universal_design_payload(payload, nonces)


def test_universal_design_payload_rejects_swapped_skill_nonces() -> None:
    module = _module()
    payload, nonces = _universal_design_payload(module)
    reported = payload["skill_nonces"]
    assert isinstance(reported, dict)
    first, second = module.UNIVERSAL_DESIGN_SKILL_SELECTORS[:2]
    reported[first], reported[second] = reported[second], reported[first]

    with pytest.raises(RuntimeError, match="nonce did not match selector"):
        module._validate_universal_design_payload(payload, nonces)


def test_universal_design_payload_rejects_generic_findings() -> None:
    module = _module()
    payload, nonces = _universal_design_payload(module)
    accessibility = payload["accessibility"]
    assert isinstance(accessibility, list)
    accessibility[0]["issue"] = "The design is bad."
    accessibility[0]["remediation"] = "Make the design better."

    with pytest.raises(RuntimeError, match="not grounded in its fixture signal"):
        module._validate_universal_design_payload(payload, nonces)


def test_universal_design_payload_rejects_duplicate_findings() -> None:
    module = _module()
    payload, nonces = _universal_design_payload(module)
    duplicate_issue = "The empty aria-label, red color, twelve navigation choices, and onclick div need review."
    duplicate_remediation = "Replace each fixture problem with an appropriate semantic control."
    for field in module.UNIVERSAL_DESIGN_FINDING_SOURCES:
        findings = payload[field]
        assert isinstance(findings, list)
        findings[0]["issue"] = duplicate_issue
        findings[0]["remediation"] = duplicate_remediation

    with pytest.raises(RuntimeError, match="duplicate issue/remediation findings"):
        module._validate_universal_design_payload(payload, nonces)


def test_universal_design_payload_rejects_blank_structured_fields() -> None:
    module = _module()
    payload, nonces = _universal_design_payload(module)
    interaction = payload["interaction"]
    assert isinstance(interaction, list)
    interaction[0]["remediation"] = "   "

    with pytest.raises(RuntimeError, match="omitted nonblank remediation"):
        module._validate_universal_design_payload(payload, nonces)


def test_universal_design_probe_injects_distinct_nonces_into_every_requested_skill(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    installed_root = tmp_path / "installed"
    originals = {}
    for selector in module.UNIVERSAL_DESIGN_SKILL_SELECTORS:
        skill_name = selector.split(":", 1)[1]
        skill_path = installed_root / "skills" / skill_name / "SKILL.md"
        skill_path.parent.mkdir(parents=True)
        original = f"---\nname: {skill_name}\ndescription: Fixture\n---\n\n{skill_name}.\n".encode()
        skill_path.write_bytes(original)
        originals[skill_path] = original
    control_root = tmp_path / "control"
    control_root.mkdir()
    calls = []

    monkeypatch.setattr(module, "validate_plugin_surfaces", lambda *_args: None)

    def fake_probe(plugin_id, fixture, env, runtime_evidence):
        assert plugin_id == module.UNIVERSAL_DESIGN_PLUGIN_ID
        assert fixture.is_dir()
        assert env == {}
        assert isinstance(runtime_evidence, dict)
        assert set(runtime_evidence) == set(module.UNIVERSAL_DESIGN_SKILL_SELECTORS)
        assert len(set(runtime_evidence.values())) == len(module.UNIVERSAL_DESIGN_SKILL_SELECTORS)
        for selector, nonce in runtime_evidence.items():
            skill_name = selector.split(":", 1)[1]
            source = (installed_root / "skills" / skill_name / "SKILL.md").read_text()
            assert f"## Runtime Probe Nonce\n\n{nonce}\n" in source
        calls.append(dict(runtime_evidence))
        index = len(calls)
        return (
            module.ProcessResult(
                ("codex",),
                0,
                f"probe-{index}",
                "",
                100 + index,
                launch_id=f"launch-{index}",
                started_at_ns=index,
            ),
            f"digest-{index}",
        )

    monkeypatch.setattr(module, "probe_model_discovery", fake_probe)

    result = module.probe_installed_plugin(
        module.UNIVERSAL_DESIGN_PLUGIN_ID,
        "universal-design-principles",
        installed_root,
        {},
        control_root,
        99,
    )

    assert len(calls) == 2
    assert calls[0] == calls[1]
    assert result.initial_pid == 101
    assert result.fresh_pid == 102
    for skill_path, original in originals.items():
        assert skill_path.read_bytes() == original


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

    assert list(module.read_receipts()) == [("a", "behavior"), ("b", "install")]
    assert module.read_receipt_document()["closure_receipts"] == [{"gate_id": "docs-closure"}]
