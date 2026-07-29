from __future__ import annotations

import importlib.util
import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "_run_candidate_mcp_canaries",
        ROOT / "scripts/run_candidate_mcp_canaries.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_semantic_probe_matrix_covers_every_keyless_local_candidate_mcp() -> None:
    module = _module()
    activation = module.load_module("_candidate_mcp_test_activation", module.ACTIVATION_SCRIPT)

    assert len(module.PROBES) == module.EXPECTED_SEMANTIC_PROBE_COUNT == 15
    specs = module.all_mcp_specs(activation)
    assert len(specs) == module.EXPECTED_MCP_ARTIFACT_COUNT == 17
    assert set(specs) == set(module.PROBES) | {"langfuse-mcp", "papersflow"}
    assert module.BLOCKED_MCP_REASONS == {
        "langfuse-mcp": "credentialed-runtime-probe-prohibited",
        "papersflow": "hosted-oauth-runtime-unavailable",
    }


def test_probe_environment_is_secret_free(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    monkeypatch.setenv("MCPHUB_BEARER_TOKEN", "secret")
    monkeypatch.setenv("AUTHORIZATION", "secret")

    env = module.sanitized_env(tmp_path)

    assert "OPENAI_API_KEY" not in env
    assert "MCPHUB_BEARER_TOKEN" not in env
    assert "AUTHORIZATION" not in env
    assert env["HOME"] == str(tmp_path)


def test_blocked_auth_probe_reports_only_presence_not_secret_values(monkeypatch) -> None:
    module = _module()
    secret = "candidate-langfuse-secret-value"
    monkeypatch.setenv("LANGFUSE_HOST", "https://example.invalid")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "public")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", secret)
    activation = module.load_module("_candidate_mcp_blocked_test_activation", module.ACTIVATION_SCRIPT)
    url, seed = module.all_mcp_specs(activation)["langfuse-mcp"]
    monkeypatch.setattr(module, "installed_paths", lambda _seed, _cli: [])

    report = module.blocked_mcp_result(
        "langfuse-mcp",
        url,
        seed,
        activation,
        object(),
    )

    rendered = json.dumps(report, sort_keys=True)
    assert secret not in rendered
    assert report["credential_presence"] == {
        "LANGFUSE_HOST": True,
        "LANGFUSE_PUBLIC_KEY": True,
        "LANGFUSE_SECRET_KEY": True,
    }
    assert report["network_probe_performed"] is False
    assert report["secret_value_recorded"] is False
    assert report["status"] == "blocked"


def test_antv_probe_uses_a_loopback_fixture_contract() -> None:
    module = _module()
    probe = module.PROBES["antv-chart"]
    failure = module.FAILURE_CONTRACTS["antv-chart"]

    assert probe.expected_text == "http://127.0.0.1:"
    assert "VIS_REQUEST_SERVER" not in dict(probe.environment)
    assert failure.tool == "generate_bar_chart"
    assert failure.tool != module.DENIAL_TOOL
    assert failure.expected_error_code == -32603
    assert failure.expected_marker == module.ANTV_FAILURE_MARKER


def test_mcp_stdio_boundary_wraps_required_candidate_sandbox(tmp_path: Path) -> None:
    module = _module()
    probe = module.Probe(Path(sys.executable), (), "probe", {}, "probe")
    fixture = tmp_path / "denied"
    fixture.mkdir()
    home = fixture / "home"
    home.mkdir()

    parameters = module._sandboxed_server_parameters(
        "probe",
        probe,
        fixture,
        [],
        module.sanitized_env(home),
    )

    assert Path(parameters.command).name == "sandbox-exec"
    assert parameters.args[0] == "-p"
    assert "(deny network*)" in parameters.args[1]


def test_mcp_stdio_boundary_preserves_validated_lexical_clone_path(tmp_path: Path) -> None:
    module = _module()
    target = tmp_path / "target"
    target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    target.chmod(0o755)
    clone = tmp_path / "clone"
    clone.symlink_to(target)
    probe = module.Probe(clone, (), "probe", {}, "probe")
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    home = fixture / "home"
    home.mkdir()

    parameters, launch_path, launch_realpath = module._sandboxed_server_envelope(
        "probe",
        probe,
        fixture,
        [],
        module.sanitized_env(home),
    )

    assert str(clone) in parameters.args
    assert str(target) not in parameters.args
    assert launch_path == str(clone)
    assert launch_realpath == str(target)
    assert clone.resolve(strict=True) == target


def test_mcp_envelope_rejects_wrapper_that_rewrites_candidate_command(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    target = tmp_path / "target"
    target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    target.chmod(0o755)
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    home = fixture / "home"
    home.mkdir()

    def rewrite(_argv, *, cwd, env):
        del cwd
        return ["sandbox-exec", "-p", "profile", str(target.resolve())], env

    monkeypatch.setattr(module, "prepare_sandboxed_subprocess", rewrite)
    probe = module.Probe(target, ("--probe",), "probe", {}, "probe")

    with pytest.raises(RuntimeError, match="did not preserve the candidate command envelope"):
        module._sandboxed_server_envelope("probe", probe, fixture, ["--probe"], module.sanitized_env(home))


def test_mcp_network_policies_separate_owned_loopback_and_exact_external_probe() -> None:
    module = _module()
    assert module.PROBE_NETWORK_POLICIES == {
        "antv-chart": "loopback",
        "better-icons": "external",
        "nullcost": "loopback",
        "paper-search-mcp": "external",
    }


def test_default_probe_selection_excludes_blocked_and_external_network_candidates() -> None:
    module = _module()

    requested = module.requested_probe_names(None, allow_external_network=False)

    assert requested == set(module.PROBES) - {"better-icons", "paper-search-mcp"}
    assert not requested & set(module.BLOCKED_MCP_REASONS)
    assert module.requested_probe_names(None, allow_external_network=True) == set(module.PROBES)


def test_failure_and_denial_paths_select_distinct_safe_tools() -> None:
    module = _module()
    happy = SimpleNamespace(
        name="catalog",
        inputSchema={"type": "object", "properties": {}, "required": []},
        annotations=SimpleNamespace(destructiveHint=False),
    )
    unsafe = SimpleNamespace(
        name="delete",
        inputSchema={"type": "object", "required": ["target"]},
        annotations=SimpleNamespace(destructiveHint=True),
    )
    safe_failure = SimpleNamespace(
        name="lookup",
        inputSchema={"type": "object", "required": ["id"]},
        annotations=SimpleNamespace(destructiveHint=False),
    )
    probe = module.Probe(Path(sys.executable), (), "catalog", {}, "catalog")

    contract = module._failure_call(
        "probe",
        SimpleNamespace(tools=[happy, unsafe, safe_failure]),
        probe,
    )

    assert contract.tool == "lookup"
    assert contract.tool != module.DENIAL_TOOL
    assert contract.arguments == {"id": {"__wagents_invalid__": True}}


@pytest.mark.parametrize(
    ("error_code", "message", "expected_error"),
    [
        (-32601, "wagents-owned-antv-failure", "failure error code"),
        (-32603, "different validation error", "expected failure marker"),
    ],
)
def test_failure_contract_rejects_wrong_code_or_marker(
    error_code: int,
    message: str,
    expected_error: str,
) -> None:
    module = _module()
    contract = module.FAILURE_CONTRACTS["antv-chart"]

    class FailingSession:
        async def call_tool(self, _tool: str, _arguments: dict[str, object]) -> None:
            raise module.McpError(SimpleNamespace(code=error_code, message=message))

    with pytest.raises(RuntimeError, match=expected_error):
        module.anyio.run(module._assert_failure_path, FailingSession(), contract)


def test_unknown_tool_content_marker_is_recorded_as_a_denial_encoding() -> None:
    module = _module()

    class ContentMarkerSession:
        async def call_tool(self, _tool: str, _arguments: dict[str, object]) -> SimpleNamespace:
            return SimpleNamespace(
                isError=False,
                content=[SimpleNamespace(text=f"Unknown tool: {module.DENIAL_TOOL}")],
            )

    text, encoding, tool = module.anyio.run(module._assert_denial_path, ContentMarkerSession())

    assert text == f"Unknown tool: {module.DENIAL_TOOL}"
    assert encoding == "content-marker"
    assert tool == module.DENIAL_TOOL


def test_unknown_tool_not_found_tool_error_is_a_denial_encoding() -> None:
    module = _module()

    class ToolErrorSession:
        async def call_tool(self, _tool: str, _arguments: dict[str, object]) -> SimpleNamespace:
            return SimpleNamespace(
                isError=True,
                content=[SimpleNamespace(text=f"MCP error -32602: Tool {module.DENIAL_TOOL} not found")],
            )

    _text, encoding, tool = module.anyio.run(module._assert_denial_path, ToolErrorSession())

    assert encoding == "tool-error"
    assert tool == module.DENIAL_TOOL


def test_unknown_tool_non_error_without_exact_marker_is_rejected() -> None:
    module = _module()

    class AmbiguousSession:
        async def call_tool(self, _tool: str, _arguments: dict[str, object]) -> SimpleNamespace:
            return SimpleNamespace(isError=False, content=[SimpleNamespace(text="request completed")])

    with pytest.raises(RuntimeError, match="denial marker"):
        module.anyio.run(module._assert_denial_path, AmbiguousSession())


def test_excalidraw_uses_explicit_no_autostart_dependency_gate() -> None:
    module = _module()
    contract = module.DENIAL_CONTRACTS["mcp-excalidraw"]

    class DependencyGateSession:
        async def call_tool(self, tool: str, arguments: dict[str, object]) -> SimpleNamespace:
            assert tool == "describe_scene"
            assert arguments == {}
            return SimpleNamespace(
                isError=True,
                content=[
                    SimpleNamespace(
                        text=(
                            "Error: Canvas server is not reachable at http://127.0.0.1:3000 "
                            "(auto-start disabled by EXCALIDRAW_NO_AUTOSTART=1)."
                        )
                    )
                ],
            )

    _text, encoding, tool = module.anyio.run(
        module._assert_denial_path,
        DependencyGateSession(),
        contract,
    )

    assert encoding == "dependency-gate"
    assert tool == "describe_scene"


def test_canaries_require_sdk_bounded_process_group_shutdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module()
    monkeypatch.setattr(module, "direct_child_pids", lambda: {1234})
    monkeypatch.setattr(module.os, "getpgid", lambda pid: pid)
    monkeypatch.setattr(module.os, "getpgrp", lambda: 4321)

    assert frozenset(module.PROBES) == module.BOUNDED_SHUTDOWN_PROBES
    assert module._owned_process_group(1234) == 1234


def test_owned_process_group_rejects_the_current_process() -> None:
    module = _module()

    with pytest.raises(RuntimeError, match="refusing to inspect"):
        module._owned_process_group(module.os.getpid())


def test_owned_process_group_rejects_unowned_or_unsafe_process_groups(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module()
    monkeypatch.setattr(module, "direct_child_pids", lambda: set())

    with pytest.raises(RuntimeError, match="unowned"):
        module._owned_process_group(1234)

    monkeypatch.setattr(module, "direct_child_pids", lambda: {1234})
    monkeypatch.setattr(module.os, "getpgid", lambda _pid: 1235)
    monkeypatch.setattr(module.os, "getpgrp", lambda: 4321)

    with pytest.raises(RuntimeError, match="unsafe"):
        module._owned_process_group(1234)


def test_process_group_leak_cleanup_is_guarded_and_group_scoped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module()
    calls: list[tuple[int, int]] = []
    monkeypatch.setattr(module.os, "getpgrp", lambda: 4321)
    monkeypatch.setattr(module.os, "killpg", lambda pgid, sig: calls.append((pgid, sig)))

    module._terminate_owned_process_group(1234, 1234)

    assert calls == [(1234, module.signal.SIGTERM), (1234, module.signal.SIGKILL)]
    with pytest.raises(RuntimeError, match="unsafe"):
        module._terminate_owned_process_group(1234, 1235)


@pytest.mark.parametrize("times_out", [False, True])
def test_execute_once_finishes_sdk_teardown_outside_protocol_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    times_out: bool,
) -> None:
    module = _module()
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    events: list[str] = []
    state = {"stdio_active": False}

    @asynccontextmanager
    async def fake_stdio_client(_parameters, *, errlog):
        del errlog
        state["stdio_active"] = True
        events.append("stdio-enter")
        try:
            yield object(), object()
        finally:
            events.append("stdio-exit-start")
            await module.anyio.sleep(0)
            state["stdio_active"] = False
            events.append("stdio-exit-complete")

    class FakeSession:
        def __init__(self, _read, _write):
            pass

        async def __aenter__(self):
            events.append("session-enter")
            return self

        async def __aexit__(self, *_args):
            events.append("session-exit")

        async def initialize(self):
            if times_out:
                await module.anyio.sleep_forever()

        async def list_tools(self):
            return SimpleNamespace(tools=[SimpleNamespace(name="happy")])

        async def call_tool(self, _tool, _arguments):
            return SimpleNamespace(isError=False, content=[SimpleNamespace(text="happy")])

    async def fake_failure(_session, _contract):
        await module.anyio.sleep(0)
        return "failure"

    async def fake_denial(_session, _contract):
        await module.anyio.sleep(0)
        return "denial", "tool-error", "missing"

    def child_pids():
        return {1234} if state["stdio_active"] else set()

    def group_exists(_pgid):
        events.append("group-check")
        return False

    monkeypatch.setattr(module, "stdio_client", fake_stdio_client)
    monkeypatch.setattr(module, "ClientSession", FakeSession)
    monkeypatch.setattr(module, "direct_child_pids", child_pids)
    monkeypatch.setattr(module, "_owned_process_group", lambda _pid: 1234)
    monkeypatch.setattr(module, "_process_group_exists", group_exists)
    monkeypatch.setattr(
        module,
        "_sandboxed_server_envelope",
        lambda *_args: (object(), "/tmp/server", "/tmp/server"),
    )
    monkeypatch.setattr(module, "_failure_call", lambda *_args: SimpleNamespace(tool="failure"))
    monkeypatch.setattr(module, "_assert_failure_path", fake_failure)
    monkeypatch.setattr(module, "_assert_denial_path", fake_denial)
    monkeypatch.setattr(
        module.os,
        "killpg",
        lambda *_args: pytest.fail("normal SDK teardown must not use fallback signaling"),
    )
    probe = module.Probe(Path("/tmp/server"), (), "happy", {}, "happy")

    if times_out:
        with pytest.raises(TimeoutError):
            module.anyio.run(module.execute_once, "probe", probe, fixture, 0.01)
    else:
        result = module.anyio.run(module.execute_once, "probe", probe, fixture, 1.0)
        assert result[0] == 1234
        assert result[7] == "mcp-sdk-bounded-process-group-shutdown"

    assert events == [
        "stdio-enter",
        "session-enter",
        "session-exit",
        "stdio-exit-start",
        "stdio-exit-complete",
        "group-check",
    ]


def test_external_probe_apply_requires_explicit_network_authorization(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _module()
    receipts = tmp_path / "receipts.json"
    receipts.write_text(
        json.dumps({"version": 2, "revision": 0, "receipts": [], "closure_receipts": []}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "RECEIPTS", receipts)
    monkeypatch.setattr(module, "RUNTIME_STATE", tmp_path / "state")
    monkeypatch.setattr(
        module,
        "run_twice",
        lambda *_args, **_kwargs: pytest.fail("external candidate process must not launch"),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_candidate_mcp_canaries.py", "--apply", "--probe", "better-icons"],
    )

    assert module.main() == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["applied"] is False
    assert payload["execution_required_count"] == 1
    assert payload["probes"][0]["status"] == "execution-required"
    assert json.loads(receipts.read_text(encoding="utf-8"))["revision"] == 0


def test_receipt_writer_is_deterministic(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    output = tmp_path / "receipts.json"
    monkeypatch.setattr(module, "RECEIPTS", output)
    monkeypatch.setattr(module, "RUNTIME_STATE", tmp_path / "state")
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

    payload = module.json.loads(output.read_text(encoding="utf-8"))
    assert [(row["artifact_id"], row["phase"]) for row in payload["receipts"]] == [
        ("a", "behavior"),
        ("b", "install"),
    ]
    assert payload["closure_receipts"] == [{"gate_id": "docs-closure"}]


def test_uv_tool_version_probe_preserves_virtualenv_interpreter_path(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _module()
    tool_root = tmp_path / "example"
    python = tool_root / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.symlink_to(Path(sys.executable).resolve())
    captured: list[str] = []

    def fake_prepare(argv, *, cwd, env):
        del cwd
        captured.append(argv[0])
        return [sys.executable, "-c", "print('1.2.3')"], env

    monkeypatch.setattr(module, "UV_TOOLS", tmp_path)
    monkeypatch.setattr(module, "prepare_sandboxed_subprocess", fake_prepare)

    version = module.installed_version(
        {"package_manager": "uv-tool", "package_name": "example"},
        [tool_root],
    )

    assert version == "1.2.3"
    assert captured == [str(python)]
