#!/usr/bin/env python3
"""Run semantic MCP canaries and emit fail-closed runtime receipts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
from contextlib import suppress
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

import anyio
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError

from mcp import ClientSession, StdioServerParameters
from wagents.candidate_evidence import FILESYSTEM_DIGEST_ALGORITHM, receipt_metadata
from wagents.candidate_provenance import package_manager_provenance
from wagents.candidate_receipts import ReceiptStore
from wagents.candidate_sandbox import (
    NetworkPolicy,
    prepare_sandboxed_subprocess,
    sandbox_environment,
    selected_javascript_package_roots,
    selected_macos_runtime_roots,
)

ROOT = Path(__file__).resolve().parents[1]
ACTIVATION_SCRIPT = ROOT / "scripts" / "record_candidate_runtime_activation.py"
CLI_CANARY_SCRIPT = ROOT / "scripts" / "run_candidate_cli_canaries.py"
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
RECEIPTS = MANIFEST_DIR / "runtime-activation-receipts.json"
RUNTIME_STATE = Path("~/.local/share/wagents/candidate-runtime").expanduser()
NODE_BIN = Path.home() / ".local/share/wagents/candidate-runtime/npm/node_modules/.bin"
UV_TOOLS = Path.home() / ".local/share/uv/tools"
EXPECTED_MCP_ARTIFACT_COUNT = 17
EXPECTED_SEMANTIC_PROBE_COUNT = 15
DENIAL_TOOL = "__wagents_missing_tool__"
ANTV_FAILURE_MARKER = "wagents-owned-antv-failure"
CONTROLLED_SYSTEM_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"
BLOCKED_MCP_REASONS = {
    "langfuse-mcp": "credentialed-runtime-probe-prohibited",
    "papersflow": "hosted-oauth-runtime-unavailable",
}
PROBE_NETWORK_POLICIES: dict[str, NetworkPolicy] = {
    "antv-chart": "loopback",
    # Icon search queries Iconify's public catalog without credentials.
    "better-icons": "external",
    "nullcost": "loopback",
    # The semantic probe makes one credential-free arXiv query. Seatbelt grants
    # outbound sockets only; it still denies listening sockets and fixture escapes.
    "paper-search-mcp": "external",
}


@dataclass(frozen=True)
class Probe:
    executable: Path
    arguments: tuple[str, ...]
    tool: str
    tool_arguments: dict[str, Any]
    expected_text: str
    environment: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class FailureContract:
    tool: str
    arguments: dict[str, Any]
    expected_error_code: int | None = None
    expected_marker: str | None = None


@dataclass(frozen=True)
class DenialContract:
    tool: str
    arguments: dict[str, Any]
    expected_markers: tuple[str, ...]
    encoding: str


FAILURE_CONTRACTS: dict[str, FailureContract] = {
    "antv-chart": FailureContract(
        tool="generate_bar_chart",
        arguments={
            "data": [{"category": "A", "value": 1}, {"category": "B", "value": 2}],
            "stack": False,
        },
        expected_error_code=-32603,
        expected_marker=ANTV_FAILURE_MARKER,
    ),
}
DENIAL_CONTRACTS: dict[str, DenialContract] = {
    "mcp-excalidraw": DenialContract(
        tool="describe_scene",
        arguments={},
        expected_markers=(
            "Canvas server is not reachable at http://127.0.0.1:3000",
            "auto-start disabled by EXCALIDRAW_NO_AUTOSTART=1",
        ),
        encoding="dependency-gate",
    ),
}


PROBES: dict[str, Probe] = {
    "antv-chart": Probe(
        NODE_BIN / "mcp-server-chart",
        (),
        "generate_bar_chart",
        {"data": [{"category": "A", "value": 1}, {"category": "B", "value": 2}], "stack": False},
        "http://127.0.0.1:",
    ),
    "axiom-mcp": Probe(NODE_BIN / "axiom-mcp", (), "axiom_get_catalog", {}, "Axiom Skills Catalog"),
    "better-icons": Probe(NODE_BIN / "better-icons", ("mcp",), "search_icons", {"query": "arrow", "limit": 1}, "arrow"),
    "charted": Probe(UV_TOOLS / "charted/bin/charted-mcp", (), "list_chart_types", {}, '"type"'),
    "csvglow": Probe(UV_TOOLS / "csvglow/bin/csvglow", ("--mcp",), "generate_dashboard", {}, '"success": true'),
    "designer-skill-mcp": Probe(
        NODE_BIN / "designer-skill-mcp",
        (),
        "get_preflight_brief",
        {},
        "preflight brief",
        (("NO_UPDATE_NOTIFIER", "1"),),
    ),
    "geo-mcp": Probe(
        UV_TOOLS / "geo-optimizer-skill/bin/geo-mcp",
        (),
        "geo_schema_validate",
        {
            "json_string": json.dumps({
                "@context": "https://schema.org",
                "@type": "WebSite",
                "name": "Probe",
                "url": "https://example.invalid",
            }),
            "schema_type": "WebSite",
        },
        '"valid": true',
    ),
    "mcp-dashboards": Probe(
        NODE_BIN / "mcp-dashboards",
        ("--stdio",),
        "render_bar_chart",
        {
            "title": "Probe",
            "labels": ["A", "B"],
            "datasets": [{"label": "Value", "data": [1, 2]}],
        },
        "Probe",
        (("MCP_DASHBOARDS_DISABLE_PREVIEW", "1"), ("MCP_DASHBOARDS_RETAIN_DAYS", "0")),
    ),
    "mcp-excalidraw": Probe(
        NODE_BIN / "mcp-excalidraw-server",
        (),
        "read_diagram_guide",
        {},
        "Excalidraw Diagram Design Guide",
        (("EXCALIDRAW_NO_AUTOSTART", "1"),),
    ),
    "mobile-mcp": Probe(
        NODE_BIN / "mcp-server-mobile",
        ("--stdio",),
        "mobile_list_available_devices",
        {},
        '"devices"',
        (("MOBILEMCP_DISABLE_TELEMETRY", "1"),),
    ),
    "nullcost": Probe(
        NODE_BIN / "nullcost-plugin",
        ("mcp-server",),
        "search_providers",
        {"query": "database", "limit": 1},
        "OwnedDB",
    ),
    "openspec-mcp": Probe(NODE_BIN / "openspec-mcp", (), "openspec_list_changes", {}, "[]"),
    "paper-search-mcp": Probe(
        UV_TOOLS / "paper-search-mcp/bin/paper-search-mcp",
        (),
        "search_papers",
        {"query": "model context protocol", "max_results_per_source": 1, "sources": "arxiv"},
        '"arxiv": 1',
    ),
    "prompt-to-asset": Probe(
        NODE_BIN / "p2a", (), "asset_doctor", {"check_data": True, "auto_fix": False}, '"runtime"'
    ),
    "semiotic": Probe(
        NODE_BIN / "semiotic-mcp",
        (),
        "suggestChart",
        {"data": [{"month": "Jan", "revenue": 120}, {"month": "Feb", "revenue": 180}]},
        "BarChart",
    ),
}
BOUNDED_SHUTDOWN_PROBES = frozenset(PROBES)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sanitized_env(home: Path, extra: tuple[tuple[str, str], ...] = ()) -> dict[str, str]:
    env = {
        "PATH": CONTROLLED_SYSTEM_PATH,
        "HOME": str(home),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_DATA_HOME": str(home / ".local/share"),
        "CI": "1",
        "DO_NOT_TRACK": "1",
        "NO_COLOR": "1",
        "NO_UPDATE_NOTIFIER": "1",
        "npm_config_update_notifier": "false",
    }
    for key in ("LANG", "LC_ALL", "TMPDIR"):
        if value := os.environ.get(key):
            env[key] = value
    env.update(dict(extra))
    return env


def _trusted_runtime_path(fixture: Path) -> tuple[str, tuple[Path, ...]]:
    trusted_bin = fixture / "trusted-bin"
    trusted_bin.mkdir()
    roots: list[Path] = [trusted_bin]
    for name, candidates in {
        "node": (Path("/opt/homebrew/bin/node"), Path("/usr/local/bin/node"), Path("/usr/bin/node")),
        "bun": (Path.home() / ".bun" / "bin" / "bun", Path("/opt/homebrew/bin/bun")),
    }.items():
        available = [candidate.resolve(strict=True) for candidate in candidates if candidate.exists()]
        if not available:
            continue
        target = available[0]
        if not target.is_file() or not os.access(target, os.X_OK):
            raise RuntimeError(f"trusted MCP runtime is not executable: {target}")
        (trusted_bin / name).symlink_to(target)
        roots.extend(selected_macos_runtime_roots(target))
        if name == "node":
            openssl_config = Path("/opt/homebrew/etc/openssl@3")
            if openssl_config.is_dir():
                roots.append(openssl_config)
    return f"{trusted_bin}:{CONTROLLED_SYSTEM_PATH}", tuple(roots)


def _mcp_read_roots(probe: Probe) -> tuple[Path, ...]:
    executable = probe.executable.resolve(strict=True)
    roots: set[Path] = set(selected_javascript_package_roots(executable))
    uv_root = UV_TOOLS.resolve(strict=False)
    if executable.is_relative_to(uv_root):
        relative = executable.relative_to(uv_root)
        tool_root = uv_root / relative.parts[0]
        roots.add(tool_root)
        tool_python = tool_root / "bin/python"
        if tool_python.exists():
            roots.add(tool_python)
            roots.update(selected_macos_runtime_roots(tool_python.resolve(strict=True)))
    return tuple(sorted(roots, key=str))


def _sandboxed_server_envelope(
    name: str,
    probe: Probe,
    fixture: Path,
    args: list[str],
    env: dict[str, str],
) -> tuple[StdioServerParameters, str, str]:
    launch_path = probe.executable.expanduser()
    if not launch_path.is_absolute():
        raise ValueError(f"{name}: MCP executable path must be absolute")
    resolved_launch_path = launch_path.resolve(strict=True)
    if not resolved_launch_path.is_file() or not os.access(resolved_launch_path, os.X_OK):
        raise ValueError(f"{name}: MCP executable is not runnable: {resolved_launch_path}")
    runtime_path, runtime_roots = _trusted_runtime_path(fixture)
    temporary = fixture / "tmp"
    temporary.mkdir()
    env = dict(env)
    env["PATH"] = runtime_path
    env["TMPDIR"] = str(temporary)
    network_policy = PROBE_NETWORK_POLICIES.get(name, "none")
    if network_policy == "external":
        env["SSL_CERT_FILE"] = "/etc/ssl/cert.pem"
    env = sandbox_environment(
        env,
        read_roots=(*_mcp_read_roots(probe), *runtime_roots, fixture),
        write_roots=(fixture,),
        network_policy=network_policy,
    )
    candidate_argv = [str(launch_path), *args]
    argv, child_env = prepare_sandboxed_subprocess(
        candidate_argv,
        cwd=fixture,
        env=env,
    )
    if len(argv) < len(candidate_argv) or argv[-len(candidate_argv) :] != candidate_argv:
        raise RuntimeError(f"{name}: sandbox wrapper did not preserve the candidate command envelope")
    parameters = StdioServerParameters(command=argv[0], args=argv[1:], env=child_env, cwd=fixture)
    return parameters, candidate_argv[0], str(resolved_launch_path)


def _sandboxed_server_parameters(
    name: str,
    probe: Probe,
    fixture: Path,
    args: list[str],
    env: dict[str, str],
) -> StdioServerParameters:
    parameters, _launch_path, _launch_realpath = _sandboxed_server_envelope(name, probe, fixture, args, env)
    return parameters


def direct_child_pids() -> set[int]:
    result = subprocess.run(
        ["ps", "-axo", "pid=,ppid=,command="],
        check=True,
        text=True,
        capture_output=True,
    )
    parent = os.getpid()
    children: set[int] = set()
    for line in result.stdout.splitlines():
        fields = line.strip().split(maxsplit=2)
        if len(fields) < 2:
            continue
        pid, ppid = int(fields[0]), int(fields[1])
        command = fields[2] if len(fields) == 3 else ""
        if ppid == parent and "ps -axo pid=,ppid=,command=" not in command:
            children.add(pid)
    return children


def _owned_process_group(pid: int) -> int:
    if pid <= 1 or pid == os.getpid():
        raise RuntimeError(f"refusing to inspect non-child canary PID {pid}")
    if pid not in direct_child_pids():
        raise RuntimeError(f"refusing to inspect unowned canary PID {pid}")
    pgid = os.getpgid(pid)
    if pgid != pid or pgid == os.getpgrp():
        raise RuntimeError(f"refusing unsafe canary process group {pgid} for PID {pid}")
    return pgid


def _process_group_exists(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    return True


def _terminate_owned_process_group(pid: int, pgid: int) -> None:
    if pgid != pid or pgid == os.getpgrp():
        raise RuntimeError(f"refusing to terminate unsafe canary process group {pgid} for PID {pid}")
    with suppress(ProcessLookupError):
        os.killpg(pgid, signal.SIGTERM)
    with suppress(ProcessLookupError):
        os.killpg(pgid, signal.SIGKILL)


class _AntvFixtureHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        self.rfile.read(int(self.headers.get("content-length", "0")))
        port = int(cast("tuple[str, int]", self.server.server_address)[1])
        server = cast("Any", self.server)
        request_count = int(getattr(server, "request_count", 0)) + 1
        server.request_count = request_count
        if request_count == 1:
            payload = {
                "success": True,
                "resultObj": f"http://127.0.0.1:{port}/probe.png",
                "errorMessage": "",
            }
        else:
            payload = {
                "success": False,
                "resultObj": None,
                "errorMessage": ANTV_FAILURE_MARKER,
            }
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        del format, args
        return


class _NullcostFixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = json.dumps({
            "providers": [
                {
                    "name": "OwnedDB",
                    "slug": "owned-db",
                    "website": "https://example.invalid/owned-db",
                    "category": "database",
                    "freeTier": "Owned local fixture",
                }
            ]
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        del format, args
        return


def result_text(result: Any) -> str:
    return " ".join(str(getattr(item, "text", "")) for item in result.content)


def _invalid_schema_value(schema: Any) -> Any:
    if not isinstance(schema, dict):
        return {"__wagents_invalid__": True}
    schema_type = schema.get("type")
    if schema_type == "array":
        return {"__wagents_invalid__": True}
    if schema_type == "object":
        return ["__wagents_invalid__"]
    if schema_type in {"number", "integer"}:
        return "__wagents_invalid__"
    if schema_type == "boolean":
        return "__wagents_invalid__"
    if schema_type == "string":
        return {"__wagents_invalid__": True}
    return {"__wagents_invalid__": True}


def _failure_call(name: str, tools: Any, probe: Probe) -> FailureContract:
    by_name = {tool.name: tool for tool in tools.tools}
    override = FAILURE_CONTRACTS.get(name)
    if override is not None:
        tool = by_name.get(override.tool)
        if tool is None:
            raise RuntimeError(f"{name}: failure-contract tool is missing: {override.tool}")
        annotations = getattr(tool, "annotations", None)
        if bool(getattr(annotations, "destructiveHint", False)):
            raise RuntimeError(f"{name}: failure-contract tool is destructive: {override.tool}")
        return override
    ordered = [by_name[probe.tool], *[tool for tool in tools.tools if tool.name != probe.tool]]
    for tool in ordered:
        schema = tool.inputSchema if isinstance(tool.inputSchema, dict) else {}
        required = schema.get("required")
        annotations = getattr(tool, "annotations", None)
        destructive = bool(getattr(annotations, "destructiveHint", False))
        if isinstance(required, list) and required and not destructive:
            field = str(required[0])
            properties = schema.get("properties")
            field_schema = properties.get(field) if isinstance(properties, dict) else None
            return FailureContract(
                tool=str(tool.name),
                arguments={field: _invalid_schema_value(field_schema)},
            )
    raise RuntimeError(f"{probe.tool}: no safe required-argument tool exists for the failure-path probe")


async def _assert_failure_path(session: ClientSession, contract: FailureContract) -> str:
    try:
        result = await session.call_tool(contract.tool, contract.arguments)
    except McpError as error:
        text = str(error)
        if contract.expected_error_code is not None and int(error.error.code) != contract.expected_error_code:
            raise RuntimeError(
                f"{contract.tool}: failure error code {int(error.error.code)} != {contract.expected_error_code}"
            ) from error
        if contract.expected_marker is not None and contract.expected_marker not in text:
            raise RuntimeError(f"{contract.tool}: expected failure marker was not preserved") from error
        return text
    text = result_text(result)
    if not result.isError:
        raise RuntimeError(f"{contract.tool}: invalid-input failure path did not fail closed")
    if contract.expected_error_code is not None:
        raise RuntimeError(f"{contract.tool}: expected an MCP protocol error with a verifiable code")
    if contract.expected_marker is not None and contract.expected_marker not in text:
        raise RuntimeError(f"{contract.tool}: expected failure marker was not preserved")
    return text


def _is_unknown_tool_denial(text: str) -> bool:
    folded = text.casefold()
    tool = DENIAL_TOOL.casefold()
    return tool in folded and ("unknown tool" in folded or f"tool {tool} not found" in folded)


async def _assert_denial_path(
    session: ClientSession,
    contract: DenialContract | None = None,
) -> tuple[str, str, str]:
    tool = contract.tool if contract is not None else DENIAL_TOOL
    arguments = contract.arguments if contract is not None else {}
    try:
        result = await session.call_tool(tool, arguments)
    except McpError as error:
        text = str(error)
        if contract is not None:
            if not all(marker in text for marker in contract.expected_markers):
                raise RuntimeError(f"{tool}: source-specific denial markers were not preserved") from error
            return text, contract.encoding, tool
        if not _is_unknown_tool_denial(text):
            raise RuntimeError("unexpected missing-tool denial error") from error
        return text, "protocol-error", tool
    text = result_text(result)
    if contract is not None:
        if not result.isError:
            raise RuntimeError(f"{tool}: source-specific denial did not fail closed")
        if not all(marker in text for marker in contract.expected_markers):
            raise RuntimeError(f"{tool}: source-specific denial markers were not preserved")
        return text, contract.encoding, tool
    if not _is_unknown_tool_denial(text):
        raise RuntimeError("unknown-tool denial marker was not preserved")
    if result.isError:
        return text, "tool-error", tool
    return text, "content-marker", tool


def prepare_fixture(name: str, fixture: Path, probe: Probe) -> tuple[list[str], dict[str, Any]]:
    args = list(probe.arguments)
    tool_arguments = dict(probe.tool_arguments)
    if name == "openspec-mcp":
        project = fixture / "project"
        (project / "openspec").mkdir(parents=True)
        (project / "openspec/config.yaml").write_text("schema: spec-driven\n", encoding="utf-8")
        args.append(str(project))
    elif name == "csvglow":
        source = fixture / "fixture.csv"
        output = fixture / "fixture.html"
        source.write_text("name,value\nA,1\nB,2\n", encoding="utf-8")
        tool_arguments = {"file_path": str(source), "output_path": str(output), "open_browser": False}
    return args, tool_arguments


async def execute_once(
    name: str,
    probe: Probe,
    fixture: Path,
    timeout: float,
) -> tuple[int, str, str, str, str, str, str, str, str, str]:
    home = fixture / "home"
    home.mkdir()
    args, tool_arguments = prepare_fixture(name, fixture, probe)
    env = sanitized_env(home, probe.environment)
    fixture_server: ThreadingHTTPServer | None = None
    fixture_thread: threading.Thread | None = None
    if name == "antv-chart":
        fixture_server = ThreadingHTTPServer(("127.0.0.1", 0), _AntvFixtureHandler)
        env["VIS_REQUEST_SERVER"] = f"http://127.0.0.1:{fixture_server.server_port}/render"
    elif name == "nullcost":
        fixture_server = ThreadingHTTPServer(("127.0.0.1", 0), _NullcostFixtureHandler)
        tool_arguments["baseUrl"] = f"http://127.0.0.1:{fixture_server.server_port}"
    if fixture_server is not None:
        fixture_thread = threading.Thread(target=fixture_server.serve_forever, daemon=True)
        fixture_thread.start()
    parameters, launch_path, launch_realpath = _sandboxed_server_envelope(name, probe, fixture, args, env)
    before = direct_child_pids()
    child_pid: int | None = None
    child_pgid: int | None = None
    result: tuple[int, str, str, str, str, str, str, str, str, str] | None = None
    protocol_error: BaseException | None = None
    try:
        with Path(os.devnull).open("w", encoding="utf-8") as errlog:
            try:
                async with stdio_client(
                    parameters,
                    errlog=errlog,
                ) as (read, write):
                    active = direct_child_pids() - before
                    if len(active) != 1:
                        raise RuntimeError(f"{name}: expected one MCP child process, found {sorted(active)}")
                    child_pid = next(iter(active))
                    child_pgid = _owned_process_group(child_pid)
                    with anyio.fail_after(timeout):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            tools = await session.list_tools()
                            if probe.tool not in {tool.name for tool in tools.tools}:
                                raise RuntimeError(f"{name}: expected tool is missing: {probe.tool}")
                            happy = await session.call_tool(probe.tool, tool_arguments)
                            happy_text = result_text(happy)
                            if happy.isError or probe.expected_text.lower() not in happy_text.lower():
                                raise RuntimeError(f"{name}: semantic assertion failed: {happy_text[:1000]!r}")
                            if name == "csvglow":
                                output = fixture / "fixture.html"
                                rendered = output.read_text(encoding="utf-8") if output.is_file() else ""
                                if "A" not in rendered or "B" not in rendered:
                                    raise RuntimeError("csvglow: generated dashboard omitted fixture rows")
                            failure_contract = _failure_call(name, tools, probe)
                            failure_text = await _assert_failure_path(session, failure_contract)
                            failure_tool = failure_contract.tool
                            denial_text, denial_encoding, denial_tool = await _assert_denial_path(
                                session,
                                DENIAL_CONTRACTS.get(name),
                            )
                            happy_digest = hashlib.sha256(happy_text.encode()).hexdigest()
                            failure_digest = hashlib.sha256(failure_text.encode()).hexdigest()
                            denial_digest = hashlib.sha256(denial_text.encode()).hexdigest()
                            digest = hashlib.sha256(
                                (happy_digest + "\0" + failure_digest + "\0" + denial_digest).encode()
                            ).hexdigest()
                            result = (
                                child_pid,
                                digest,
                                failure_digest,
                                denial_digest,
                                failure_tool,
                                denial_tool,
                                denial_encoding,
                                "mcp-sdk-bounded-process-group-shutdown",
                                launch_path,
                                launch_realpath,
                            )
            except BaseException as error:
                protocol_error = error
            if child_pid is None or child_pgid is None:
                if protocol_error is not None:
                    raise protocol_error
                raise RuntimeError(f"{name}: MCP canary did not capture complete process evidence")
            if child_pid in direct_child_pids() or _process_group_exists(child_pgid):
                _terminate_owned_process_group(child_pid, child_pgid)
                raise RuntimeError(f"{name}: MCP SDK teardown left an owned process group running")
            if protocol_error is not None:
                raise protocol_error
            if result is None:
                raise RuntimeError(f"{name}: MCP canary did not capture complete process evidence")
            return result
    finally:
        if fixture_server is not None:
            fixture_server.shutdown()
            fixture_server.server_close()
        if fixture_thread is not None:
            fixture_thread.join(timeout=5)


def run_twice(name: str, probe: Probe, timeout: float) -> tuple[int, int, str, str, str, str, str, str, str]:
    pids: list[int] = []
    digests: list[str] = []
    failure_digests: list[str] = []
    denial_digests: list[str] = []
    failure_tools: list[str] = []
    denial_tools: list[str] = []
    denial_encodings: list[str] = []
    shutdown_modes: list[str] = []
    for _ in range(2):
        with tempfile.TemporaryDirectory(prefix=f"wagents-mcp-{name}-") as raw:
            (
                pid,
                digest,
                failure_digest,
                denial_digest,
                failure_tool,
                denial_tool,
                denial_encoding,
                shutdown_mode,
                _launch_path,
                _launch_realpath,
            ) = anyio.run(execute_once, name, probe, Path(raw), timeout)
            pids.append(pid)
            digests.append(digest)
            failure_digests.append(failure_digest)
            denial_digests.append(denial_digest)
            failure_tools.append(failure_tool)
            denial_tools.append(denial_tool)
            denial_encodings.append(denial_encoding)
            shutdown_modes.append(shutdown_mode)
    if pids[0] == pids[1]:
        raise RuntimeError(f"{name}: fresh process reused PID {pids[0]}")
    if failure_tools[0] != failure_tools[1]:
        raise RuntimeError(f"{name}: failure-path tool selection drifted across fresh processes")
    if denial_tools[0] != denial_tools[1]:
        raise RuntimeError(f"{name}: denial-path tool selection drifted across fresh processes")
    if denial_encodings[0] != denial_encodings[1]:
        raise RuntimeError(f"{name}: denial-path encoding drifted across fresh processes")
    if shutdown_modes[0] != shutdown_modes[1]:
        raise RuntimeError(f"{name}: shutdown mode drifted across fresh processes")
    combined = hashlib.sha256("\0".join(digests).encode()).hexdigest()
    combined_failure = hashlib.sha256("\0".join(failure_digests).encode()).hexdigest()
    combined_denial = hashlib.sha256("\0".join(denial_digests).encode()).hexdigest()
    return (
        pids[0],
        pids[1],
        combined,
        combined_failure,
        combined_denial,
        failure_tools[0],
        denial_tools[0],
        denial_encodings[0],
        shutdown_modes[0],
    )


def installed_paths(seed: dict[str, Any], cli_module: Any) -> list[Path]:
    executable_map = cli_module.resolve_managed_executables([seed])
    paths = list(cli_module.installed_paths(seed, executable_map))
    manager = str(seed.get("package_manager") or "")
    package = str(seed.get("package_name") or "").split("[", 1)[0]
    if manager in {"uv-tool", "uvx"} and package:
        tool_root = UV_TOOLS / package
        if tool_root.is_dir():
            paths.append(tool_root)
    return sorted({path.resolve() for path in paths}, key=str)


def installed_version(seed: dict[str, Any], paths: list[Path]) -> str:
    manager = str(seed.get("package_manager") or "")
    package = str(seed.get("package_name") or "").split("[", 1)[0]
    if manager == "npm":
        for path in paths:
            manifest = path / "package.json"
            if manifest.is_file():
                payload = json.loads(manifest.read_text(encoding="utf-8"))
                if payload.get("name") == package:
                    return str(payload.get("version") or "")
    if manager in {"uv-tool", "uvx"}:
        python = UV_TOOLS / package / "bin/python"
        with tempfile.TemporaryDirectory(prefix="wagents-mcp-version-") as raw:
            fixture = Path(raw)
            home = fixture / "home"
            home.mkdir()
            env = sandbox_environment(
                sanitized_env(home),
                read_roots=(UV_TOOLS / package, python, python.resolve(strict=True).parent.parent),
                write_roots=(fixture,),
                network_policy="none",
            )
            argv, child_env = prepare_sandboxed_subprocess(
                [
                    str(python),
                    "-c",
                    "import importlib.metadata,sys; print(importlib.metadata.version(sys.argv[1]))",
                    package,
                ],
                cwd=fixture,
                env=env,
            )
            result = subprocess.run(
                argv,
                check=True,
                text=True,
                capture_output=True,
                cwd=fixture,
                env=child_env,
            )
        return result.stdout.strip()
    raise ValueError(f"cannot resolve installed version for {manager}:{package}")


def all_mcp_specs(activation: Any) -> dict[str, tuple[str, dict[str, Any]]]:
    result = {
        str(seed.get("mcp_server") or ""): (url, seed)
        for url, specs in activation.runtime_specs().items()
        for seed in specs
        if seed.get("kind") == "mcp"
    }
    if len(result) != EXPECTED_MCP_ARTIFACT_COUNT:
        raise ValueError(f"expected {EXPECTED_MCP_ARTIFACT_COUNT} MCP artifacts, found {len(result)}")
    if set(result) != set(PROBES) | set(BLOCKED_MCP_REASONS):
        raise ValueError(
            "MCP canary inventory drifted: "
            f"expected {sorted(set(PROBES) | set(BLOCKED_MCP_REASONS))}, found {sorted(result)}"
        )
    return result


def requested_probe_names(explicit: list[str] | None, *, allow_external_network: bool) -> set[str]:
    if explicit:
        return set(explicit)
    external = {name for name, policy in PROBE_NETWORK_POLICIES.items() if policy == "external"}
    return set(PROBES) if allow_external_network else set(PROBES) - external


def credential_presence(seed: dict[str, Any], env: dict[str, str] | None = None) -> dict[str, bool]:
    source = os.environ if env is None else env
    return {
        str(name): bool(source.get(str(name)))
        for name in sorted({str(value) for value in seed.get("auth_env_names", [])})
    }


def blocked_mcp_result(
    name: str,
    url: str,
    seed: dict[str, Any],
    activation: Any,
    cli_module: Any,
) -> dict[str, Any]:
    manager = str(seed.get("package_manager") or "")
    paths: list[Path] = []
    version = ""
    install_error = ""
    if manager != "hosted":
        try:
            paths = installed_paths(seed, cli_module)
            if paths:
                version = installed_version(seed, paths)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            install_error = f"{type(error).__name__}: {error}"
    return {
        "artifact_id": activation.artifact_id(url, seed),
        "mcp_server": name,
        "status": "blocked",
        "blocker": BLOCKED_MCP_REASONS[name],
        "package_manager": manager,
        "auth_required": seed.get("auth_required") is True,
        "credential_presence": credential_presence(seed),
        "local_install_present": bool(paths),
        "installed_version": version,
        "expected_version": str(seed.get("version") or ""),
        "install_probe_error": install_error,
        "network_probe_performed": False,
        "secret_value_recorded": False,
    }


def read_receipt_document() -> dict[str, Any]:
    return ReceiptStore(RECEIPTS, RUNTIME_STATE).load()


def read_receipts() -> dict[tuple[str, str], dict[str, Any]]:
    payload = read_receipt_document()
    return {(str(row["artifact_id"]), str(row["phase"])): row for row in payload.get("receipts", [])}


def write_receipts(rows: dict[tuple[str, str], dict[str, Any]]) -> None:
    store = ReceiptStore(RECEIPTS, RUNTIME_STATE)
    snapshot = store.snapshot(artifact_keys=set(rows))
    store.commit(snapshot, artifact_upserts=rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--allow-external-network", action="store_true")
    parser.add_argument("--probe", action="append")
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args()

    activation = load_module("_candidate_mcp_activation", ACTIVATION_SCRIPT)
    cli_module = load_module("_candidate_mcp_cli_helpers", CLI_CANARY_SCRIPT)
    source_shas = cli_module.source_shas()
    mcp_specs = all_mcp_specs(activation)
    external_probes = {name for name, policy in PROBE_NETWORK_POLICIES.items() if policy == "external"}
    requested = requested_probe_names(args.probe, allow_external_network=args.allow_external_network)
    unknown = sorted(requested - set(mcp_specs))
    if unknown:
        raise ValueError(f"unknown candidate MCP server ids: {unknown}")
    report: list[dict[str, Any]] = []
    owned_keys = {
        (activation.artifact_id(mcp_specs[name][0], mcp_specs[name][1]), phase)
        for name in requested
        if name in PROBES
        for phase in ("identity", "install", "behavior", "fresh_process")
    }
    store = ReceiptStore(RECEIPTS, RUNTIME_STATE)
    snapshot = store.snapshot(artifact_keys=owned_keys)
    rows = snapshot.artifact_rows
    updated_keys: set[tuple[str, str]] = set()
    applied = False
    if len(PROBES) != EXPECTED_SEMANTIC_PROBE_COUNT:
        raise ValueError(f"expected {EXPECTED_SEMANTIC_PROBE_COUNT} semantic MCP probes")
    for name in sorted(requested):
        url, seed = mcp_specs[name]
        if name not in PROBES:
            report.append(blocked_mcp_result(name, url, seed, activation, cli_module))
            continue
        if name in external_probes and not args.allow_external_network:
            report.append({
                "artifact_id": activation.artifact_id(url, seed),
                "mcp_server": name,
                "status": "execution-required",
                "blocker": "external-network-authorization-required",
                "network_probe_performed": False,
            })
            continue
        paths = installed_paths(seed, cli_module)
        if not paths:
            raise ValueError(f"{name}: installed paths are missing")
        print(f"[candidate-mcp] probing {name}", file=sys.stderr, flush=True)
        digest = cli_module.file_digest(paths)
        version = installed_version(seed, paths)
        expected_version = str(seed.get("version") or "")
        if version != expected_version:
            raise ValueError(f"{name}: installed version {version!r} != {expected_version!r}")
        (
            first_pid,
            fresh_pid,
            output_digest,
            failure_digest,
            denial_digest,
            failure_tool,
            denial_tool,
            denial_encoding,
            shutdown_mode,
        ) = run_twice(name, PROBES[name], args.timeout)
        artifact_id = activation.artifact_id(url, seed)
        package_id = f"{seed.get('package_manager')}:{seed.get('package_name')}"
        source_commit_sha = str(seed.get("source_commit_sha") or source_shas[url.lower()])
        resolved_version = str(version)
        provenance = package_manager_provenance(
            seed,
            runtime_state=RUNTIME_STATE,
            uv_tools=UV_TOOLS,
        )
        identity = {
            "artifact_id": artifact_id,
            "phase": "identity",
            "package_id": package_id,
            "source_commit_sha": source_commit_sha,
            "audited_source_commit_sha": source_commit_sha,
            "resolved_version": version,
            "integrity": provenance["integrity"],
            "installed_package_origin": provenance,
            "install_root": str(paths[0]),
        }
        install = {
            "artifact_id": artifact_id,
            "phase": "install",
            "package_id": package_id,
            "installed_digest": digest,
            "installed_realpaths": [str(path) for path in paths],
            "install_status": "passed",
            "evidence_kind": "package-manager-live-install",
            "installed_package_origin_digest": provenance["origin_digest"],
        }
        behavior = {
            "artifact_id": artifact_id,
            "phase": "behavior",
            "fixture_id": f"candidate-mcp-{name}-v1",
            "semantic_assertions": [
                f"{PROBES[name].tool} completed against an owned bounded fixture",
                (
                    f"{failure_tool} preserved the owned loopback failure marker"
                    if name == "antv-chart"
                    else f"{failure_tool} rejected invalid required arguments"
                ),
                (
                    f"{denial_tool} was denied by the explicit no-autostart dependency gate"
                    if denial_encoding == "dependency-gate"
                    else f"{denial_tool} was denied as an unknown tool"
                ),
            ],
            "installed_digest": digest,
            "happy_path_status": "passed",
            "failure_path_status": "passed",
            "denial_path_status": "passed",
            "failure_path_tool": failure_tool,
            "failure_path_output_sha256": failure_digest,
            "denial_path_tool": denial_tool,
            "denial_path_output_sha256": denial_digest,
            "denial_path_encoding": denial_encoding,
            "probe_kind": "semantic-mcp-tool-call",
            "mock_only": False,
            "output_sha256": output_digest,
        }
        fresh = {
            "artifact_id": artifact_id,
            "phase": "fresh_process",
            "initial_process_id": str(first_pid),
            "fresh_process_id": str(fresh_pid),
            "installed_digest": digest,
            "fresh_discovery_status": "passed",
            "fresh_use_status": "passed",
            "shutdown_mode": shutdown_mode,
        }
        for receipt in (identity, install, behavior, fresh):
            receipt.update(
                receipt_metadata(
                    artifact_id=artifact_id,
                    phase=str(receipt["phase"]),
                    source_commit_sha=source_commit_sha,
                    package_id=package_id,
                    resolved_version=resolved_version,
                    installed_digest=digest,
                )
            )
            receipt["digest_algorithm"] = FILESYSTEM_DIGEST_ALGORITHM
            receipt["digest_ignored_dirs"] = sorted(cli_module.DIGEST_IGNORED_DIRS)
            key = (artifact_id, str(receipt["phase"]))
            rows[key] = receipt
            updated_keys.add(key)
        report.append({
            "artifact_id": artifact_id,
            "mcp_server": name,
            "resolved_version": version,
            "installed_digest": digest,
            "initial_process_id": first_pid,
            "fresh_process_id": fresh_pid,
            "status": "passed",
        })
    apply_ok = all(item["status"] == "passed" for item in report)
    if args.apply and apply_ok and updated_keys:
        store.commit(
            snapshot,
            artifact_upserts={key: rows[key] for key in updated_keys},
        )
        applied = True
    print(
        json.dumps(
            {
                "ok": apply_ok,
                "applied": applied,
                "inventory_count": len(mcp_specs),
                "selected_probe_count": len(requested),
                "artifact_count": len(report),
                "semantic_probe_count": sum(item["status"] == "passed" for item in report),
                "blocked_count": sum(item["status"] == "blocked" for item in report),
                "execution_required_count": sum(item["status"] == "execution-required" for item in report),
                "inventory_blockers": [
                    {
                        "mcp_server": name,
                        "blocker": reason,
                    }
                    for name, reason in sorted(BLOCKED_MCP_REASONS.items())
                    if name not in requested
                ],
                "probes": report,
            },
            indent=2,
            ensure_ascii=True,
        )
    )
    return 0 if apply_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
