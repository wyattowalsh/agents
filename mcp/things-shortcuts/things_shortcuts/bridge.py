"""Secure fixed-name execution for the Things++ Shortcut protocol."""

from __future__ import annotations

import hashlib
import json
import os
import signal
import stat
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from pydantic import Field

from .models import (
    DESTRUCTIVE_OPERATIONS,
    PROTOCOL_VERSION,
    BridgeIdentity,
    BridgeOperation,
    ClosedModel,
    PublicBridgeIdentity,
    PublicBridgeOperation,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

SHORTCUTS_EXECUTABLE = Path("/usr/bin/shortcuts")
SHORTCUT_OUTPUT_UTI = "public.json"
DEFAULT_TIMEOUT_SECONDS = 30.0
HEALTH_TIMEOUT_SECONDS = 8.0
MAX_RESPONSE_BYTES = 1_048_576
_SUBPROCESS_ENV_KEYS = ("HOME", "TMPDIR", "LANG", "LC_ALL", "__CF_USER_TEXT_ENCODING")
_PROTOCOL_DIR = Path(__file__).with_name("protocol")
REQUEST_SCHEMA_PATH = _PROTOCOL_DIR / "request.schema.json"
RESPONSE_SCHEMA_PATH = _PROTOCOL_DIR / "response.schema.json"


class BridgeUnavailableError(RuntimeError):
    """The fixed bridge cannot be invoked."""


class BridgeProtocolError(RuntimeError):
    """The bridge response does not match protocol v1."""


class BridgeTimeoutError(RuntimeError):
    """The fixed bridge exceeded its bounded timeout."""


class BridgeExecutionError(RuntimeError):
    """The fixed bridge returned a content-free failure."""


def _canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic JSON bytes used for protocol digests."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _load_schema(path: Path) -> dict[str, Any]:
    """Load one repository-owned protocol schema without following a symlink."""
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise BridgeProtocolError("protocol_schema_not_regular")
        raw = os.read(descriptor, 512_000)
        after = os.fstat(descriptor)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise BridgeProtocolError("protocol_schema_changed")
    finally:
        os.close(descriptor)
    try:
        parsed = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BridgeProtocolError("protocol_schema_invalid") from exc
    if not isinstance(parsed, dict):
        raise BridgeProtocolError("protocol_schema_invalid")
    return parsed


REQUEST_SCHEMA = _load_schema(REQUEST_SCHEMA_PATH)
RESPONSE_SCHEMA = _load_schema(RESPONSE_SCHEMA_PATH)
REQUEST_SCHEMA_SHA256 = hashlib.sha256(_canonical_json_bytes(REQUEST_SCHEMA)).hexdigest()
RESPONSE_SCHEMA_SHA256 = hashlib.sha256(_canonical_json_bytes(RESPONSE_SCHEMA)).hexdigest()


class BridgeRequest(ClosedModel):
    """Exact request envelope exchanged with a fixed Shortcut."""

    protocol_version: Literal["1"] = Field(alias="protocolVersion")
    bridge_identity: PublicBridgeIdentity = Field(alias="bridgeIdentity")
    request_schema_sha256: str = Field(alias="requestSchemaSha256", pattern=r"^[a-f0-9]{64}$")
    response_schema_sha256: str = Field(alias="responseSchemaSha256", pattern=r"^[a-f0-9]{64}$")
    request_id: str = Field(alias="requestId", pattern=r"^[a-f0-9]{32}$")
    operation: PublicBridgeOperation
    payload: dict[str, Any] = Field(max_length=32)


class BridgeResponse(ClosedModel):
    """Exact response envelope returned by a fixed Shortcut."""

    protocol_version: Literal["1"] = Field(alias="protocolVersion")
    bridge_identity: PublicBridgeIdentity = Field(alias="bridgeIdentity")
    request_schema_sha256: str = Field(alias="requestSchemaSha256", pattern=r"^[a-f0-9]{64}$")
    response_schema_sha256: str = Field(alias="responseSchemaSha256", pattern=r"^[a-f0-9]{64}$")
    request_id: str = Field(alias="requestId", pattern=r"^[a-f0-9]{32}$")
    status: Literal["ok", "error"]
    result: dict[str, Any] = Field(max_length=32)
    error_code: str | None = Field(alias="errorCode", default=None, pattern=r"^[a-z0-9_-]{1,64}$")
    tcc_ready: bool = Field(alias="tccReady")


def bridge_for_operation(operation: BridgeOperation) -> BridgeIdentity:
    """Return the only bridge permitted to handle an operation."""
    if operation in DESTRUCTIVE_OPERATIONS:
        return BridgeIdentity.DESTRUCTIVE
    return BridgeIdentity.AGENT


def _secure_file(path: Path, payload: bytes = b"") -> None:
    """Create a mode-0600 regular file without following an existing path."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        if payload:
            os.write(descriptor, payload)
        os.fsync(descriptor)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o600:
            raise BridgeExecutionError("temporary_file_permissions")
    finally:
        os.close(descriptor)


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    """Terminate then kill the process group without targeting unrelated processes."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=0.5)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    process.wait(timeout=0.5)


def _subprocess_environment() -> dict[str, str]:
    """Return the minimal non-secret environment needed by fixed macOS tools."""
    environment = {"PATH": "/usr/bin:/bin"}
    for key in _SUBPROCESS_ENV_KEYS:
        value = os.environ.get(key)
        if value and "\x00" not in value and len(value) <= 4096:
            environment[key] = value
    return environment


def _run_process(argv: Sequence[str], timeout_seconds: float, *, capture_stdout: bool = False) -> tuple[int, bytes]:
    """Execute fixed argv with a private process group and content-free stderr."""
    process = subprocess.Popen(
        list(argv),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE if capture_stdout else subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
        env=_subprocess_environment(),
    )
    try:
        stdout, _ = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        _terminate_process_group(process)
        raise BridgeTimeoutError("bridge_timeout") from exc
    return process.returncode, stdout or b""


def _read_secure_response(path: Path) -> bytes:
    """Read a bounded mode-0600 response and reject swaps or symlinks."""
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or stat.S_IMODE(before.st_mode) != 0o600:
            raise BridgeProtocolError("response_file_permissions")
        if before.st_size > MAX_RESPONSE_BYTES:
            raise BridgeProtocolError("response_too_large")
        raw = os.read(descriptor, MAX_RESPONSE_BYTES + 1)
        after = os.fstat(descriptor)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise BridgeProtocolError("response_file_changed")
    finally:
        os.close(descriptor)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise BridgeProtocolError("response_too_large")
    return raw


def list_fixed_bridges() -> set[BridgeIdentity]:
    """List only presence of the two fixed names; discard every other Shortcut name."""
    if not SHORTCUTS_EXECUTABLE.is_file():
        return set()
    return_code, stdout = _run_process(
        (str(SHORTCUTS_EXECUTABLE), "list"),
        HEALTH_TIMEOUT_SECONDS,
        capture_stdout=True,
    )
    if return_code != 0:
        raise BridgeUnavailableError("shortcuts_list_failed")
    if len(stdout) > MAX_RESPONSE_BYTES:
        raise BridgeProtocolError("shortcuts_list_too_large")
    names = {line.strip() for line in stdout.decode("utf-8", errors="strict").splitlines()}
    return {identity for identity in BridgeIdentity if identity.value in names}


def invoke_bridge(
    operation: BridgeOperation,
    payload: Mapping[str, Any],
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> BridgeResponse:
    """Invoke one fixed bridge with protocol-v1 digest and identity verification."""
    if not SHORTCUTS_EXECUTABLE.is_file():
        raise BridgeUnavailableError("shortcuts_cli_absent")
    identity = bridge_for_operation(operation)
    request = BridgeRequest(
        protocolVersion=PROTOCOL_VERSION,
        bridgeIdentity=identity,
        requestSchemaSha256=REQUEST_SCHEMA_SHA256,
        responseSchemaSha256=RESPONSE_SCHEMA_SHA256,
        requestId=uuid.uuid4().hex,
        operation=operation,
        payload=dict(payload),
    )
    with tempfile.TemporaryDirectory(prefix="things-plus-plus-") as directory_name:
        directory = Path(directory_name)
        os.chmod(directory, 0o700)
        request_path = directory / "request.json"
        response_path = directory / "response.json"
        _secure_file(
            request_path,
            _canonical_json_bytes(request.model_dump(by_alias=True, mode="json")),
        )
        _secure_file(response_path)
        argv = (
            str(SHORTCUTS_EXECUTABLE),
            "run",
            identity.value,
            "--input-path",
            str(request_path),
            "--output-path",
            str(response_path),
            "--output-type",
            SHORTCUT_OUTPUT_UTI,
        )
        return_code, _ = _run_process(argv, timeout_seconds)
        if return_code != 0:
            raise BridgeExecutionError("bridge_process_failed")
        raw = _read_secure_response(response_path)
    try:
        response = BridgeResponse.model_validate_json(raw)
    except Exception as exc:
        raise BridgeProtocolError("bridge_response_invalid") from exc
    expected = (
        response.protocol_version == PROTOCOL_VERSION
        and response.bridge_identity is identity
        and response.request_schema_sha256 == REQUEST_SCHEMA_SHA256
        and response.response_schema_sha256 == RESPONSE_SCHEMA_SHA256
        and response.request_id == request.request_id
    )
    if not expected:
        raise BridgeProtocolError("bridge_handshake_mismatch")
    if response.status == "error":
        raise BridgeExecutionError(response.error_code or "bridge_operation_failed")
    return response


def probe_bridge(identity: BridgeIdentity) -> BridgeResponse:
    """Run the protocol-only health branch, which must not call a Things action."""
    operation = BridgeOperation.PROTOCOL_HEALTH
    # protocol_health normally routes to the agent bridge, so invoke a fixed
    # identity explicitly for the destructive bridge probe.
    if identity is BridgeIdentity.AGENT:
        return invoke_bridge(operation, {"probe": True}, timeout_seconds=HEALTH_TIMEOUT_SECONDS)
    request_id = uuid.uuid4().hex
    request = BridgeRequest(
        protocolVersion=PROTOCOL_VERSION,
        bridgeIdentity=identity,
        requestSchemaSha256=REQUEST_SCHEMA_SHA256,
        responseSchemaSha256=RESPONSE_SCHEMA_SHA256,
        requestId=request_id,
        operation=operation,
        payload={"probe": True},
    )
    with tempfile.TemporaryDirectory(prefix="things-plus-plus-health-") as directory_name:
        directory = Path(directory_name)
        os.chmod(directory, 0o700)
        request_path = directory / "request.json"
        response_path = directory / "response.json"
        _secure_file(
            request_path,
            _canonical_json_bytes(request.model_dump(by_alias=True, mode="json")),
        )
        _secure_file(response_path)
        return_code, _ = _run_process(
            (
                str(SHORTCUTS_EXECUTABLE),
                "run",
                identity.value,
                "--input-path",
                str(request_path),
                "--output-path",
                str(response_path),
                "--output-type",
                SHORTCUT_OUTPUT_UTI,
            ),
            HEALTH_TIMEOUT_SECONDS,
        )
        if return_code != 0:
            raise BridgeExecutionError("bridge_health_failed")
        raw = _read_secure_response(response_path)
    try:
        response = BridgeResponse.model_validate_json(raw)
    except Exception as exc:
        raise BridgeProtocolError("bridge_response_invalid") from exc
    if (
        response.protocol_version != PROTOCOL_VERSION
        or response.bridge_identity is not identity
        or response.request_schema_sha256 != REQUEST_SCHEMA_SHA256
        or response.response_schema_sha256 != RESPONSE_SCHEMA_SHA256
        or response.request_id != request_id
    ):
        raise BridgeProtocolError("bridge_handshake_mismatch")
    if response.status != "ok":
        raise BridgeExecutionError(response.error_code or "bridge_health_failed")
    return response


__all__ = [
    "REQUEST_SCHEMA_SHA256",
    "RESPONSE_SCHEMA_SHA256",
    "BridgeExecutionError",
    "BridgeProtocolError",
    "BridgeResponse",
    "BridgeTimeoutError",
    "BridgeUnavailableError",
    "invoke_bridge",
    "list_fixed_bridges",
    "probe_bridge",
]
