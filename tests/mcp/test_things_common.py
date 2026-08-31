"""Hermetic security tests for the shared Things++ runtime primitives."""

from __future__ import annotations

import base64
import hashlib
import math
import os
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import cast

import pytest
from pydantic import BaseModel, ConfigDict, Field

import things_common.security as security_module
from things_common import (
    AdvisoryMutationLock,
    LockCancelledError,
    LockTimeoutError,
    SecureRuntimePaths,
    SecurityViolation,
    canonical_bytes,
    canonical_schema_sha256,
    canonical_sha256,
    content_free_event,
    ensure_secure_runtime_root,
    redact_text,
    redact_value,
    secure_read_bytes,
    secure_write_bytes,
    verify_artifact,
    verify_record_tree,
)


class _AliasedModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    display_name: str = Field(alias="displayName")


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.lstat().st_mode)


def _child_environment() -> dict[str, str]:
    repo_root = Path(__file__).resolve().parents[2]
    common_root = str(repo_root / "packages" / "things-common")
    environment = os.environ.copy()
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = common_root if not existing else os.pathsep.join((common_root, existing))
    return environment


def _wait_for_path(path: Path, process: subprocess.Popen[str], *, timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while not path.exists() and process.poll() is None and time.monotonic() < deadline:
        time.sleep(0.01)
    if not path.exists():
        if process.poll() is None:
            process.terminate()
        stdout, stderr = process.communicate(timeout=1)
        pytest.fail(
            "lock-holder subprocess did not become ready "
            f"(returncode={process.returncode}, stdout={stdout!r}, stderr={stderr!r})"
        )


def _record_digest(payload: bytes) -> str:
    encoded = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode("ascii")
    return f"sha256={encoded}"


def test_secure_runtime_paths_create_exact_owner_only_root_and_files(tmp_path: Path) -> None:
    paths = SecureRuntimePaths.create(tmp_path / "runtime")

    assert paths.root == tmp_path / "runtime"
    assert _mode(paths.root) == 0o700
    secure_write_bytes(paths.receipt_key, b"k" * 32, exclusive=True)
    assert secure_read_bytes(paths.receipt_key, max_bytes=32) == b"k" * 32
    assert _mode(paths.receipt_key) == 0o600


def test_runtime_root_rejects_missing_parent_wrong_mode_owner_and_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(SecurityViolation, match="parent"):
        ensure_secure_runtime_root(tmp_path / "missing" / "runtime")

    wrong_mode = tmp_path / "wrong-mode"
    wrong_mode.mkdir(mode=0o700)
    wrong_mode.chmod(0o755)
    with pytest.raises(SecurityViolation, match="0700"):
        ensure_secure_runtime_root(wrong_mode)

    wrong_owner = tmp_path / "wrong-owner"
    wrong_owner.mkdir(mode=0o700)
    real_uid = os.getuid()
    with monkeypatch.context() as owner_patch:
        owner_patch.setattr(security_module.os, "getuid", lambda: real_uid + 1)
        with pytest.raises(SecurityViolation, match="owned"):
            ensure_secure_runtime_root(wrong_owner)

    real_root = tmp_path / "real-root"
    real_root.mkdir(mode=0o700)
    linked_root = tmp_path / "linked-root"
    linked_root.symlink_to(real_root, target_is_directory=True)
    # Some kernels report O_NOFOLLOW|O_DIRECTORY on a directory symlink as
    # ENOTDIR instead of ELOOP; either result is a fail-closed refusal.
    with pytest.raises((SecurityViolation, OSError)):
        ensure_secure_runtime_root(linked_root)
    assert linked_root.is_symlink()


def test_secure_files_reject_wrong_mode_owner_symlinks_and_oversize(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = SecureRuntimePaths.create(tmp_path / "runtime")
    unsafe = paths.root / "unsafe"
    unsafe.write_bytes(b"private")
    unsafe.chmod(0o644)
    with pytest.raises(SecurityViolation, match="0600"):
        secure_read_bytes(unsafe)
    with pytest.raises(SecurityViolation, match="0600"):
        secure_write_bytes(unsafe, b"must-not-truncate")
    assert unsafe.read_bytes() == b"private"

    unsafe.chmod(0o600)
    real_uid = os.getuid()
    with monkeypatch.context() as owner_patch:
        owner_patch.setattr(security_module.os, "getuid", lambda: real_uid + 1)
        with pytest.raises(SecurityViolation, match="owned"):
            secure_read_bytes(unsafe)

    target = paths.root / "target"
    secure_write_bytes(target, b"secret", exclusive=True)
    link = paths.root / "link"
    link.symlink_to(target)
    with pytest.raises(SecurityViolation, match=r"[Ss]ymlink"):
        secure_read_bytes(link)
    with pytest.raises(SecurityViolation, match=r"[Ss]ymlink"):
        secure_write_bytes(link, b"replacement")
    assert target.read_bytes() == b"secret"

    with pytest.raises(SecurityViolation, match="maximum"):
        secure_read_bytes(target, max_bytes=5)


def test_secure_read_detects_inode_replacement_during_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = SecureRuntimePaths.create(tmp_path / "runtime")
    state_path = paths.root / "state"
    secure_write_bytes(state_path, b"original-private-state", exclusive=True)
    displaced_path = paths.root / "state.displaced"
    original_read = security_module.os.read
    swapped = False

    def swapping_read(fd: int, size: int) -> bytes:
        nonlocal swapped
        if not swapped:
            swapped = True
            state_path.rename(displaced_path)
            secure_write_bytes(state_path, b"attacker-replacement", exclusive=True)
        return original_read(fd, size)

    monkeypatch.setattr(security_module.os, "read", swapping_read)
    with pytest.raises(SecurityViolation, match="changed during verification"):
        secure_read_bytes(state_path)
    assert swapped


def test_advisory_lock_times_out_and_honors_cancellation(tmp_path: Path) -> None:
    paths = SecureRuntimePaths.create(tmp_path / "runtime")
    with AdvisoryMutationLock(paths.lock_file), pytest.raises(LockTimeoutError, match="Timed out"):
        AdvisoryMutationLock(paths.lock_file, timeout_seconds=0.05, poll_seconds=0.005).acquire()

    cancelled = AdvisoryMutationLock(paths.lock_file, cancelled=lambda: True)
    with pytest.raises(LockCancelledError, match="cancelled"):
        cancelled.acquire()
    assert cancelled._fd is None
    assert _mode(paths.lock_file) == 0o600


def test_advisory_lock_serializes_independent_processes(tmp_path: Path) -> None:
    paths = SecureRuntimePaths.create(tmp_path / "runtime")
    counter = paths.root / "counter.txt"
    counter.write_text("0", encoding="utf-8")
    script = """
import sys
import time
from pathlib import Path
from things_common import AdvisoryMutationLock

lock_path = Path(sys.argv[1])
counter_path = Path(sys.argv[2])
iterations = int(sys.argv[3])
for _ in range(iterations):
    with AdvisoryMutationLock(lock_path, timeout_seconds=5.0):
        value = int(counter_path.read_text(encoding="utf-8"))
        time.sleep(0.002)
        counter_path.write_text(str(value + 1), encoding="utf-8")
"""
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", script, str(paths.lock_file), str(counter), "10"],
            env=_child_environment(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for _ in range(4)
    ]

    results = [process.communicate(timeout=15) for process in processes]
    observed = [
        (process.returncode, stdout, stderr) for process, (stdout, stderr) in zip(processes, results, strict=True)
    ]
    assert observed == [(0, "", "")] * 4
    assert counter.read_text(encoding="utf-8") == "40"


def test_advisory_lock_descriptor_is_released_after_process_crash(tmp_path: Path) -> None:
    paths = SecureRuntimePaths.create(tmp_path / "runtime")
    marker = paths.root / "crash-ready"
    script = """
import os
import sys
from pathlib import Path
from things_common import AdvisoryMutationLock

lock = AdvisoryMutationLock(Path(sys.argv[1]), timeout_seconds=2.0).acquire()
Path(sys.argv[2]).write_text("locked", encoding="utf-8")
os._exit(23)
"""
    completed = subprocess.run(
        [sys.executable, "-c", script, str(paths.lock_file), str(marker)],
        env=_child_environment(),
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )

    assert completed.returncode == 23
    assert marker.read_text(encoding="utf-8") == "locked"
    with AdvisoryMutationLock(paths.lock_file, timeout_seconds=0.5):
        pass


def test_live_cross_process_holder_blocks_until_exit(tmp_path: Path) -> None:
    paths = SecureRuntimePaths.create(tmp_path / "runtime")
    marker = paths.root / "holder-ready"
    script = """
import sys
import time
from pathlib import Path
from things_common import AdvisoryMutationLock

with AdvisoryMutationLock(Path(sys.argv[1]), timeout_seconds=2.0):
    Path(sys.argv[2]).write_text("locked", encoding="utf-8")
    time.sleep(5)
"""
    holder = subprocess.Popen(
        [sys.executable, "-c", script, str(paths.lock_file), str(marker)],
        env=_child_environment(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        _wait_for_path(marker, holder)
        with pytest.raises(LockTimeoutError):
            AdvisoryMutationLock(paths.lock_file, timeout_seconds=0.05, poll_seconds=0.005).acquire()
    finally:
        holder.terminate()
        holder.communicate(timeout=3)

    with AdvisoryMutationLock(paths.lock_file, timeout_seconds=0.5):
        pass


def test_canonical_json_is_stable_aliased_utf8_and_fail_closed() -> None:
    left = {"z": [3, 2, 1], "model": _AliasedModel(displayName="café"), "enabled": True}
    right = {"enabled": True, "model": {"displayName": "café"}, "z": (3, 2, 1)}

    expected = b'{"enabled":true,"model":{"displayName":"caf\xc3\xa9"},"z":[3,2,1]}'
    assert canonical_bytes(left) == expected
    assert canonical_bytes(right) == expected
    assert canonical_sha256(left) == hashlib.sha256(expected).hexdigest()
    assert canonical_schema_sha256(right) == canonical_sha256(right)

    with pytest.raises(TypeError, match="string keys"):
        canonical_bytes({1: "not allowed"})
    with pytest.raises(ValueError, match="non-finite"):
        canonical_bytes({"value": math.inf})
    with pytest.raises(TypeError, match="Unsupported"):
        canonical_bytes({"value": object()})


def test_redaction_removes_secrets_private_content_urls_and_local_paths() -> None:
    raw = (
        "Bearer super-secret access_token=second-secret "
        "things:///show?id=private-id file:///Users/example/private.txt "
        "/private/tmp/private-state /Library/Application Support/private "
        "~/.things-auth .things-auth things-auth.txt"
    )
    redacted = redact_text(raw)
    for private_fragment in (
        "super-secret",
        "second-secret",
        "private-id",
        "/Users/example",
        "/private/tmp/private-state",
        "/Library/Application Support/private",
        "~/.things-auth",
        ".things-auth",
        "things-auth.txt",
    ):
        assert private_fragment not in redacted
    assert "<redacted:token>" in redacted
    assert "<redacted:things-url>" in redacted
    assert "<redacted:file-url>" in redacted
    assert "<redacted:local-path>" in redacted

    value = {
        "title": "private title",
        "nested": {
            "mutation-receipt": "opaque-but-secret",
            "accessToken": "camel-secret",
            "clientSecret": "client-secret",
            "count": 2,
            "error": "things:///show?id=hidden",
        },
        "items": ["one", "two"],
        "unknown_object": object(),
    }
    sanitized = redact_value(value)
    assert sanitized == {
        "title": "<redacted:private-content>",
        "nested": {
            "mutation-receipt": "<redacted:secret>",
            "accessToken": "<redacted:secret>",
            "clientSecret": "<redacted:secret>",
            "count": 2,
            "error": "<redacted:things-url>",
        },
        "items": "<redacted:private-content>",
        "unknown_object": "<redacted:object>",
    }


def test_content_free_events_accept_only_codes_and_scalar_metrics() -> None:
    assert content_free_event("things.write.completed", changed=2, seconds=0.25, ok=True, missing=None) == {
        "event": "things.write.completed",
        "changed": 2,
        "seconds": 0.25,
        "ok": True,
        "missing": None,
    }
    with pytest.raises(ValueError, match="lowercase"):
        content_free_event("Things Write")
    with pytest.raises(TypeError, match="cannot contain strings"):
        content_free_event("things.write.failed", detail=cast("int", "private title"))


def test_verify_artifact_checks_exact_hash_size_limit_and_symlink(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.whl"
    payload = b"frozen artifact bytes"
    artifact.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()

    result = verify_artifact(artifact, digest, max_bytes=len(payload))
    assert result.path_name == "artifact.whl"
    assert result.sha256 == digest
    assert result.size == len(payload)

    with pytest.raises(SecurityViolation, match="digest mismatch"):
        verify_artifact(artifact, "0" * 64)
    with pytest.raises(SecurityViolation, match="maximum allowed size"):
        verify_artifact(artifact, digest, max_bytes=len(payload) - 1)

    link = tmp_path / "artifact-link.whl"
    link.symlink_to(artifact)
    with pytest.raises(SecurityViolation, match="opened safely"):
        verify_artifact(link, digest)


def test_verify_record_tree_checks_every_entry_and_rejects_tampering(tmp_path: Path) -> None:
    package = tmp_path / "sample_pkg"
    dist_info = tmp_path / "sample_pkg-1.0.dist-info"
    package.mkdir()
    dist_info.mkdir()
    module = package / "module.py"
    payload = b"VALUE = 1\n"
    module.write_bytes(payload)
    record_relative = "sample_pkg-1.0.dist-info/RECORD"
    record = dist_info / "RECORD"
    record_bytes = f"sample_pkg/module.py,{_record_digest(payload)},{len(payload)}\n{record_relative},,\n".encode()
    record.write_bytes(record_bytes)
    record_digest = hashlib.sha256(record_bytes).hexdigest()

    result = verify_record_tree(tmp_path, record_relative, record_digest, expected_entries=1)
    assert result.record_sha256 == record_digest
    assert result.entries_verified == 1
    assert result.entries_total == 2

    module.write_bytes(b"VALUE = 2\n")
    with pytest.raises(SecurityViolation, match="digest mismatch"):
        verify_record_tree(tmp_path, record_relative, record_digest, expected_entries=1)


def test_verify_record_tree_rejects_escape_and_symlink_entries(tmp_path: Path) -> None:
    distribution_root = tmp_path / "distribution"
    distribution_root.mkdir()
    outside = tmp_path / "outside"
    outside.write_bytes(b"outside")
    dist_info = distribution_root / "sample-1.0.dist-info"
    dist_info.mkdir()
    record_relative = "sample-1.0.dist-info/RECORD"
    record = dist_info / "RECORD"
    record_bytes = f"../{outside.name},{_record_digest(b'outside')},7\n{record_relative},,\n".encode()
    record.write_bytes(record_bytes)
    with pytest.raises(SecurityViolation, match="escapes"):
        verify_record_tree(
            distribution_root,
            record_relative,
            hashlib.sha256(record_bytes).hexdigest(),
            expected_entries=1,
        )

    target = distribution_root / "target.py"
    target.write_bytes(b"safe")
    link = distribution_root / "linked.py"
    link.symlink_to(target)
    record_bytes = f"linked.py,{_record_digest(b'safe')},4\n{record_relative},,\n".encode()
    record.write_bytes(record_bytes)
    with pytest.raises(SecurityViolation, match="opened safely"):
        verify_record_tree(
            distribution_root,
            record_relative,
            hashlib.sha256(record_bytes).hexdigest(),
            expected_entries=1,
        )
