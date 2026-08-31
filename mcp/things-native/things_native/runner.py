"""Fixed-artifact native execution with no dynamic code or URL surface."""

from __future__ import annotations

import hashlib
import hmac
import os
import plistlib
import signal
import stat
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal
from urllib.parse import quote

from pydantic import Field

from things_common import SecurityViolation, verify_artifact

from .models import ClosedModel, NativeHealthResult, NativeOperationResult

if TYPE_CHECKING:
    from collections.abc import Sequence

OSASCRIPT_EXECUTABLE = Path("/usr/bin/osascript")
OPEN_EXECUTABLE = Path("/usr/bin/open")
THINGS_APP_PATHS = (
    Path("/Applications/Things3.app"),
    Path.home() / "Applications" / "Things3.app",
)
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_OUTPUT_BYTES = 256_000
SCRIPT_DIRECTORY = Path(__file__).with_name("scripts")
_SUBPROCESS_ENV_KEYS = ("HOME", "TMPDIR", "LANG", "LC_ALL", "__CF_USER_TEXT_ENCODING")
SCRIPT_SHA256 = {
    "delete_area": "9cababa2f7d1c06f9548f41ad9c23b0c886017c7500e9a50e033b30cb604b709",
    "delete_tag": "3d284ad8254b8d354e49aeda1c5e432c4f9354fe41b007780e09ff77864c3e8f",
    "empty_trash": "e0bec57f9bb338b9a72706e824c2e6afc255d88d2c65f423a4dc3935e06d38c6",
    "log_completed": "7edfa89bdb359d4df9be7504907332b37e4aa9bc0ab787c6c0a880c1484e839c",
    "rename_tag": "d3df520a2848fcc2b276e0e7bfe1a6e8de872f1deb77b853cd0c98f2d53b408d",
    "set_tag_parent": "ba5d2a308983bb07ed5bbb8edd16ce9aa04cae99913aef6f6152953502a091e4",
}

StateRecord = Annotated[
    str,
    Field(
        min_length=1,
        max_length=4096,
        pattern=r"^[^\x00\x7f]+$",
        description="Deterministic target-state record used only for receipt binding.",
    ),
]


class NativeUnavailableError(RuntimeError):
    """A fixed native prerequisite is absent."""


class NativeArtifactError(RuntimeError):
    """A fixed native artifact failed exact-byte verification."""


class NativeTimeoutError(RuntimeError):
    """A fixed native process exceeded its timeout."""


class NativeExecutionError(RuntimeError):
    """A fixed native operation failed without exposing content."""


class NativeBackendResult(ClosedModel):
    """Exact content-free result emitted by every fixed AppleScript."""

    status: Annotated[
        Literal["previewed", "changed", "skipped", "failed", "ambiguous"],
        Field(description="Backend outcome."),
    ]
    affected_count: Annotated[
        int,
        Field(
            alias="affectedCount",
            ge=0,
            le=100_000,
            description="Directly affected records.",
        ),
    ]
    cascade_count: Annotated[
        int,
        Field(alias="cascadeCount", ge=0, le=100_000, description="Child cascade records."),
    ]
    cascade_observed: Annotated[
        bool,
        Field(
            alias="cascadeObserved",
            description="Whether cascadeCount was explicitly observed from target state.",
        ),
    ]
    target_state: Annotated[
        list[StateRecord],
        Field(
            alias="targetState",
            min_length=1,
            max_length=10_000,
            description="Deterministic target-state records excluded from public results.",
        ),
    ]
    readback_verified: Annotated[
        bool,
        Field(
            alias="readbackVerified",
            description="Whether the fixed script verified state.",
        ),
    ]
    message_code: Annotated[
        str,
        Field(
            alias="messageCode",
            min_length=1,
            max_length=64,
            pattern=r"^[a-z0-9_-]+$",
            description="Content-free result code.",
        ),
    ]


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    """Terminate then kill only the child process group."""
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


def _run_process(
    argv: Sequence[str],
    timeout_seconds: float,
    *,
    capture_stdout: bool,
    stdin_bytes: bytes | None = None,
) -> tuple[int, bytes]:
    """Run fixed argv without a shell and discard all error content."""
    process = subprocess.Popen(
        list(argv),
        stdin=subprocess.PIPE if stdin_bytes is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE if capture_stdout else subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
        env=_subprocess_environment(),
    )
    try:
        stdout, _ = process.communicate(input=stdin_bytes, timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        _terminate_process_group(process)
        raise NativeTimeoutError("native_timeout") from exc
    raw = stdout or b""
    if len(raw) > MAX_OUTPUT_BYTES:
        raise NativeExecutionError("native_output_too_large")
    return process.returncode, raw


def _safe_static_read(path: Path, *, max_bytes: int) -> bytes:
    """Read a fixed regular non-symlink bundle file with inode recheck."""
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
            raise NativeArtifactError("native_bundle_file_invalid")
        raw = os.read(descriptor, max_bytes + 1)
        after = os.fstat(descriptor)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise NativeArtifactError("native_bundle_file_changed")
    finally:
        os.close(descriptor)
    if len(raw) > max_bytes:
        raise NativeArtifactError("native_bundle_file_too_large")
    return raw


def verify_script_bundle() -> bool:
    """Verify every fixed AppleScript exact byte immediately before use."""
    try:
        for script_name, digest in SCRIPT_SHA256.items():
            verify_artifact(
                SCRIPT_DIRECTORY / f"{script_name}.applescript",
                digest,
                max_bytes=128_000,
            )
    except (FileNotFoundError, SecurityViolation):
        return False
    return True


def static_health() -> NativeHealthResult:
    """Inspect fixed app/SDEF/version/script artifacts without an AppleEvent."""
    scripts_ok = verify_script_bundle()
    app_path = next(
        (path for path in THINGS_APP_PATHS if path.is_dir() and not path.is_symlink()),
        None,
    )
    if app_path is None:
        return NativeHealthResult(
            status="app_absent",
            app_version=None,
            sdef_present=False,
            script_bundle_verified=scripts_ok,
            tcc_status="unproven",
            message_code="things_app_absent",
        )
    info_path = app_path / "Contents" / "Info.plist"
    sdef_path = app_path / "Contents" / "Resources" / "Things.sdef"
    sdef_present = sdef_path.is_file() and not sdef_path.is_symlink()
    try:
        info = plistlib.loads(_safe_static_read(info_path, max_bytes=2_000_000))
        version_value = info.get("CFBundleShortVersionString") if isinstance(info, dict) else None
        version = version_value if isinstance(version_value, str) and len(version_value) <= 64 else None
    except (FileNotFoundError, NativeArtifactError, plistlib.InvalidFileException):
        version = None
    if not scripts_ok or version is None:
        status = "bundle_mismatch"
        code = "native_bundle_mismatch"
    elif not sdef_present:
        status = "sdef_missing"
        code = "things_sdef_missing"
    else:
        status = "ready_static"
        code = "native_static_ready"
    return NativeHealthResult(
        status=status,
        app_version=version,
        sdef_present=sdef_present,
        script_bundle_verified=scripts_ok,
        tcc_status="unproven",
        message_code=code,
    )


def run_script(script_name: str, arguments: Sequence[str]) -> NativeBackendResult:
    """Run one allowlisted fixed script with arguments serialized only through argv."""
    expected = SCRIPT_SHA256.get(script_name)
    if expected is None:
        raise NativeArtifactError("native_script_not_allowlisted")
    if not OSASCRIPT_EXECUTABLE.is_file():
        raise NativeUnavailableError("osascript_absent")
    script_path = SCRIPT_DIRECTORY / f"{script_name}.applescript"
    try:
        script_source = _safe_static_read(script_path, max_bytes=128_000)
    except (OSError, NativeArtifactError) as exc:
        raise NativeArtifactError("native_script_mismatch") from exc
    if not hmac.compare_digest(hashlib.sha256(script_source).hexdigest(), expected):
        raise NativeArtifactError("native_script_mismatch")
    return_code, stdout = _run_process(
        (str(OSASCRIPT_EXECUTABLE), "-", *arguments),
        DEFAULT_TIMEOUT_SECONDS,
        capture_stdout=True,
        stdin_bytes=script_source,
    )
    if return_code != 0:
        raise NativeExecutionError("native_tcc_degraded_or_failed")
    try:
        return NativeBackendResult.model_validate_json(stdout)
    except Exception as exc:
        raise NativeExecutionError("native_result_invalid") from exc


def build_search_url(query: str | None) -> str:
    """Build only the fixed Things search command with an encoded optional query."""
    if query is None:
        return "things:///search"
    return f"things:///search?query={quote(query, safe='')}"


def open_search_url(query: str | None) -> NativeOperationResult:
    """Open the internally built Things search URL without returning it."""
    if not OPEN_EXECUTABLE.is_file():
        raise NativeUnavailableError("open_absent")
    url = build_search_url(query)
    return_code, _ = _run_process(
        (str(OPEN_EXECUTABLE), "-u", url),
        DEFAULT_TIMEOUT_SECONDS,
        capture_stdout=False,
    )
    if return_code != 0:
        raise NativeExecutionError("open_search_failed")
    return NativeOperationResult(
        operation="open_search",
        status="ui_handoff",
        affected_count=0,
        cascade_count=0,
        readback_verified=False,
        ui_handoff=True,
        undoable=None,
        message_code="search_ui_handoff",
    )


__all__ = [
    "SCRIPT_SHA256",
    "NativeArtifactError",
    "NativeBackendResult",
    "NativeExecutionError",
    "NativeTimeoutError",
    "NativeUnavailableError",
    "build_search_url",
    "open_search_url",
    "run_script",
    "static_health",
    "verify_script_bundle",
]
