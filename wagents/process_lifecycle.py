"""POSIX subprocess-group lifecycle cleanup for bounded command runners."""

from __future__ import annotations

import contextlib
import hashlib
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

TERM_GRACE_SECONDS = 1.0
GROUP_EXIT_GRACE_SECONDS = 2.0
GROUP_EXIT_POLL_SECONDS = 0.01
LIFECYCLE_GATE_TIMEOUT_SECONDS = 300
LIFECYCLE_GATE_NODE_IDS = (
    "tests/test_candidate_cli_canaries.py::test_run_timeout_exits_during_term_grace_without_kill",
    "tests/test_candidate_cli_canaries.py::test_run_timeout_cleans_process_group_descendant_and_drains_pipes",
    "tests/test_candidate_plugin_canaries.py::test_run_timeout_exits_during_term_grace_without_kill",
    "tests/test_candidate_plugin_canaries.py::test_run_timeout_cleans_process_group_descendant_and_drains_pipes",
)
ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE_GATE_SOURCES = (
    Path("wagents/process_lifecycle.py"),
    Path("scripts/run_candidate_cli_canaries.py"),
    Path("scripts/run_candidate_plugin_canaries.py"),
    Path("tests/test_candidate_cli_canaries.py"),
    Path("tests/test_candidate_plugin_canaries.py"),
)


@dataclass(frozen=True)
class ProcessLifecycleProof:
    source_digests: tuple[tuple[str, str], ...]


def _lifecycle_source_digests() -> tuple[tuple[str, str], ...]:
    return tuple((str(path), hashlib.sha256((ROOT / path).read_bytes()).hexdigest()) for path in LIFECYCLE_GATE_SOURCES)


def _process_group_exists(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _send_process_group_signal(process_group_id: int, signal_number: int) -> None:
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process_group_id, signal_number)


def _wait_for_process_group_exit(process_group_id: int) -> bool:
    deadline = time.monotonic() + GROUP_EXIT_GRACE_SECONDS
    while _process_group_exists(process_group_id):
        if time.monotonic() >= deadline:
            return False
        time.sleep(GROUP_EXIT_POLL_SECONDS)
    return True


def _text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def terminate_process_group(process: subprocess.Popen[str]) -> tuple[str, str]:
    """Terminate a dedicated POSIX process group, then reap and drain its leader."""

    process_group_id = process.pid
    if process_group_id <= 0 or process_group_id == os.getpgrp():
        raise RuntimeError("refusing to signal a non-dedicated process group")

    _send_process_group_signal(process_group_id, signal.SIGTERM)
    communication_complete = False
    stdout: str | bytes | None = None
    stderr: str | bytes | None = None
    try:
        stdout, stderr = process.communicate(timeout=TERM_GRACE_SECONDS)
        communication_complete = True
    except subprocess.TimeoutExpired:
        pass

    if not communication_complete or _process_group_exists(process_group_id):
        _send_process_group_signal(process_group_id, signal.SIGKILL)
        if not communication_complete:
            stdout, stderr = process.communicate()
        if not _wait_for_process_group_exit(process_group_id):
            raise RuntimeError(f"process group {process_group_id} survived SIGKILL")

    if process.poll() is None:
        process.wait()
    return _text(stdout), _text(stderr)


def validate_process_lifecycle_proof(proof: ProcessLifecycleProof) -> None:
    """Reject proof if lifecycle implementation or regressions changed."""

    if proof.source_digests != _lifecycle_source_digests():
        raise RuntimeError("behavioral receipt regeneration blocked: process-lifecycle sources changed after proof")


def require_process_lifecycle_gate() -> ProcessLifecycleProof:
    """Run fresh lifecycle regressions before any behavioral receipt write."""

    if os.name != "posix":
        raise RuntimeError(
            "behavioral receipt regeneration blocked: process-lifecycle proof requires POSIX process groups"
        )
    source_digests = _lifecycle_source_digests()
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        *LIFECYCLE_GATE_NODE_IDS,
    ]
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=LIFECYCLE_GATE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(
            "behavioral receipt regeneration blocked: "
            f"fresh process-lifecycle proof could not run ({type(error).__name__})"
        ) from None
    if result.returncode != 0:
        raise RuntimeError(
            "behavioral receipt regeneration blocked: "
            "fresh process-lifecycle regressions did not pass; run "
            "`uv run pytest -q " + " ".join(LIFECYCLE_GATE_NODE_IDS) + "`"
        )
    proof = ProcessLifecycleProof(source_digests=source_digests)
    validate_process_lifecycle_proof(proof)
    return proof


def run_after_process_lifecycle_gate[T](operation: Callable[[], T]) -> T:
    """Run an operation immediately after fresh, unchanged lifecycle proof."""

    proof = require_process_lifecycle_gate()
    validate_process_lifecycle_proof(proof)
    return operation()
