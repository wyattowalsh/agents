"""Hermetic regressions for serialized MCPHub local startup readiness."""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / "scripts" / "mcphub" / "common.sh"
ENV_EXAMPLE = ROOT / ".env.mcphub.example"


def _run(body: str, *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", "-c", f"source {shlex.quote(str(COMMON))}; {body}"],
        check=False,
        text=True,
        capture_output=True,
        timeout=10,
        env={"HOME": "/tmp", "PATH": "/usr/bin:/bin", "LANG": "C", **env},
    )


def test_direct_background_launch_is_hup_safe_and_stdin_detached(tmp_path: Path) -> None:
    script_dir = tmp_path / "scripts"
    run_dir = tmp_path / "run"
    script_dir.mkdir()
    start_server = script_dir / "start-server.sh"
    start_server.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
if IFS= read -r inherited; then
  printf '%s\n' "${inherited}" >"${TEST_INHERITED_STDIN}"
fi
: >"${TEST_CHILD_READY}"
while true; do sleep 0.1; done
""",
        encoding="utf-8",
    )
    start_server.chmod(0o700)

    child_ready = tmp_path / "child-ready"
    inherited_stdin = tmp_path / "inherited-stdin"
    body = r"""
MCPHUB_REPO_ROOT="${TEST_ROOT}"
MCPHUB_SCRIPT_DIR="${TEST_SCRIPT_DIR}"
MCPHUB_RUN_DIR="${TEST_RUN_DIR}"
MCPHUB_PID_FILE="${MCPHUB_RUN_DIR}/mcphub.pid"
MCPHUB_LOG_FILE="${MCPHUB_RUN_DIR}/mcphub.log"
MCPHUB_INSTANCE_LOCK="${MCPHUB_RUN_DIR}/instance.lock"
MCPHUB_DOWNSTREAM_RUNTIME_ROOT="${MCPHUB_RUN_DIR}/downstream"
mcphub_prepare_run_directory() { mkdir -p "${MCPHUB_RUN_DIR}"; }
mcphub_runtime_is_mode_ready() { return 1; }
mcphub_distribution_is_selected() { return 0; }
mcphub_launch_agent_loaded() { return 1; }
mcphub_acquire_instance_lock() { return 0; }
mcphub_release_instance_lock() { return 0; }
mcphub_pid_file_running() { return 1; }
mcphub_wait_mode_ready() {
  local attempt
  for attempt in {1..100}; do
    [[ -f "${TEST_CHILD_READY}" ]] && return 0
    sleep 0.01
  done
  return 1
}
mcphub_start_local
"""
    environment = {
        "TEST_ROOT": str(tmp_path),
        "TEST_SCRIPT_DIR": str(script_dir),
        "TEST_RUN_DIR": str(run_dir),
        "TEST_CHILD_READY": str(child_ready),
        "TEST_INHERITED_STDIN": str(inherited_stdin),
    }
    process = subprocess.run(
        ["/bin/bash", "-c", f"source {shlex.quote(str(COMMON))}; {body}"],
        check=False,
        text=True,
        input="must-not-reach-runtime\n",
        capture_output=True,
        timeout=10,
        env={"HOME": "/tmp", "PATH": "/usr/bin:/bin", "LANG": "C", **environment},
    )
    assert process.returncode == 0, process.stderr
    child_pid = int((run_dir / "mcphub.pid").read_text(encoding="utf-8").strip())
    try:
        assert not inherited_stdin.exists()
        os.kill(child_pid, 1)
        time.sleep(0.1)
        os.kill(child_pid, 0)
    finally:
        try:
            os.kill(child_pid, 15)
        except ProcessLookupError:
            pass


def test_lifecycle_examples_do_not_embed_a_maintainer_home() -> None:
    common = COMMON.read_text(encoding="utf-8")
    env_example = ENV_EXAMPLE.read_text(encoding="utf-8")
    assert "/Users/ww" not in common
    assert "/Users/ww" not in env_example
    assert "MCPHUB_TUNNEL_CREDENTIALS_FILE=${HOME}/.cloudflared/" in env_example


def test_new_runtime_keeps_instance_lock_until_readiness(tmp_path: Path) -> None:
    script_dir = tmp_path / "scripts"
    run_dir = tmp_path / "run"
    script_dir.mkdir()
    start_server = script_dir / "start-server.sh"
    start_server.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    start_server.chmod(0o700)

    body = r"""
MCPHUB_REPO_ROOT="${TEST_ROOT}"
MCPHUB_SCRIPT_DIR="${TEST_SCRIPT_DIR}"
MCPHUB_RUN_DIR="${TEST_RUN_DIR}"
MCPHUB_PID_FILE="${MCPHUB_RUN_DIR}/mcphub.pid"
MCPHUB_LOG_FILE="${MCPHUB_RUN_DIR}/mcphub.log"
MCPHUB_INSTANCE_LOCK="${MCPHUB_RUN_DIR}/instance.lock"
MCPHUB_DOWNSTREAM_RUNTIME_ROOT="${MCPHUB_RUN_DIR}/downstream"
PORT=46683
mcphub_runtime_is_ready() { return 1; }
mcphub_distribution_is_selected() { return 0; }
mcphub_launch_agent_loaded() { return 1; }
mcphub_pid_file_running() { return 1; }
mcphub_wait_mode_ready() {
  [[ -f "${MCPHUB_INSTANCE_LOCK}" ]]
  [[ "$(sed -n '1p' "${MCPHUB_INSTANCE_LOCK}")" == "$$" ]]
  printf 'waited-under-lock\n'
}
mcphub_start_local
[[ ! -e "${MCPHUB_INSTANCE_LOCK}" ]]
"""
    result = _run(
        body,
        env={
            "TEST_ROOT": str(tmp_path),
            "TEST_SCRIPT_DIR": str(script_dir),
            "TEST_RUN_DIR": str(run_dir),
        },
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "waited-under-lock\n"


def test_transient_probe_reuses_starting_tracked_runtime(tmp_path: Path) -> None:
    body = r"""
MCPHUB_RUN_DIR="${TEST_RUN_DIR}"
MCPHUB_PID_FILE="${MCPHUB_RUN_DIR}/mcphub.pid"
MCPHUB_LOG_FILE="${MCPHUB_RUN_DIR}/mcphub.log"
MCPHUB_INSTANCE_LOCK="${MCPHUB_RUN_DIR}/instance.lock"
MCPHUB_DOWNSTREAM_RUNTIME_ROOT="${MCPHUB_RUN_DIR}/downstream"
mkdir -p "${MCPHUB_RUN_DIR}"
printf '4242\n' >"${MCPHUB_PID_FILE}"
mcphub_runtime_is_ready() { return 1; }
mcphub_distribution_is_selected() { return 0; }
mcphub_launch_agent_loaded() { return 1; }
mcphub_pid_file_running() { return 0; }
mcphub_pid_file_managed_running() { return 0; }
mcphub_managed_local_identity() { printf '4242|test-start:100\n'; }
mcphub_wait_mode_ready() { printf 'reused-starting-runtime\n'; return 0; }
mcphub_stop_managed_local() { printf 'unexpected-stop\n'; return 97; }
mcphub_start_local
[[ ! -e "${MCPHUB_INSTANCE_LOCK}" ]]
"""
    result = _run(body, env={"TEST_RUN_DIR": str(tmp_path / "run")})

    assert result.returncode == 0, result.stderr
    assert result.stdout == "reused-starting-runtime\n"


def test_changed_pid_receipt_is_never_stopped_after_failed_wait(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    counter = tmp_path / "read-count"
    body = r"""
MCPHUB_RUN_DIR="${TEST_RUN_DIR}"
MCPHUB_PID_FILE="${MCPHUB_RUN_DIR}/mcphub.pid"
MCPHUB_LOG_FILE="${MCPHUB_RUN_DIR}/mcphub.log"
MCPHUB_INSTANCE_LOCK="${MCPHUB_RUN_DIR}/instance.lock"
MCPHUB_DOWNSTREAM_RUNTIME_ROOT="${MCPHUB_RUN_DIR}/downstream"
mkdir -p "${MCPHUB_RUN_DIR}"
printf '111\n' >"${MCPHUB_PID_FILE}"
mcphub_runtime_is_ready() { return 1; }
mcphub_distribution_is_selected() { return 0; }
mcphub_launch_agent_loaded() { return 1; }
mcphub_pid_file_running() { return 0; }
mcphub_pid_file_managed_running() { return 0; }
mcphub_managed_local_identity() { printf '111|test-start:100\n'; }
mcphub_process_identity() { printf '%s|test-start:100\n' "$1"; }
mcphub_read_pid_file() {
  local count=0
  [[ -f "${TEST_COUNTER}" ]] && count="$(tr -d '[:space:]' <"${TEST_COUNTER}")"
  count="$((count + 1))"
  printf '%s\n' "${count}" >"${TEST_COUNTER}"
  if [[ "${count}" -eq 1 ]]; then printf '111\n'; else printf '222\n'; fi
}
mcphub_wait_mode_ready() { return 1; }
mcphub_stop_managed_local() { printf 'unexpected-stop\n'; return 97; }
if mcphub_start_local; then
  exit 88
fi
[[ ! -e "${MCPHUB_INSTANCE_LOCK}" ]]
"""
    result = _run(
        body,
        env={"TEST_RUN_DIR": str(run_dir), "TEST_COUNTER": str(counter)},
    )

    assert result.returncode == 0, result.stderr
    assert "unexpected-stop" not in result.stdout
    assert "pid receipt or process identity changed while waiting" in result.stderr
    assert counter.read_text(encoding="utf-8") == "2\n"
    assert os.path.lexists(run_dir / "mcphub.pid")


def test_atomic_lock_publication_allows_exactly_one_contender(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    gate = tmp_path / "gate"
    worker = tmp_path / "lock-worker.sh"
    worker.write_text(
        """#!/bin/bash
set -euo pipefail
source "$COMMON"
MCPHUB_RUN_DIR="$RUN_DIR"
MCPHUB_INSTANCE_LOCK="$RUN_DIR/instance.lock"
mcphub_process_identity() { printf '%s|test-start:%s\\n' "$1" "$1"; }
while [[ ! -e "$GATE" ]]; do sleep 0.01; done
if mcphub_acquire_instance_lock; then
  printf 'acquired\\n'
  sleep 0.5
  mcphub_release_instance_lock
else
  printf 'held\\n'
fi
""",
        encoding="utf-8",
    )
    worker.chmod(0o700)
    env = {
        "HOME": "/tmp",
        "PATH": "/usr/bin:/bin",
        "LANG": "C",
        "COMMON": str(COMMON),
        "RUN_DIR": str(run_dir),
        "GATE": str(gate),
    }
    contenders = [
        subprocess.Popen(
            ["/bin/bash", str(worker)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        for _ in range(2)
    ]
    time.sleep(0.05)
    gate.touch()
    results = [contender.communicate(timeout=5) for contender in contenders]

    assert [contender.returncode for contender in contenders] == [0, 0], results
    assert sorted(stdout for stdout, _ in results) == ["acquired\n", "held\n"]
    assert all(stderr == "" for _, stderr in results)
    assert not os.path.lexists(run_dir / "instance.lock")


def test_same_pid_with_new_start_identity_is_never_stopped(tmp_path: Path) -> None:
    counter = tmp_path / "identity-count"
    body = r"""
MCPHUB_RUN_DIR="${TEST_RUN_DIR}"
MCPHUB_PID_FILE="${MCPHUB_RUN_DIR}/mcphub.pid"
MCPHUB_LOG_FILE="${MCPHUB_RUN_DIR}/mcphub.log"
MCPHUB_INSTANCE_LOCK="${MCPHUB_RUN_DIR}/instance.lock"
MCPHUB_DOWNSTREAM_RUNTIME_ROOT="${MCPHUB_RUN_DIR}/downstream"
mkdir -p "${MCPHUB_RUN_DIR}"
printf '111\n' >"${MCPHUB_PID_FILE}"
mcphub_runtime_is_ready() { return 1; }
mcphub_distribution_is_selected() { return 0; }
mcphub_launch_agent_loaded() { return 1; }
mcphub_pid_file_running() { return 0; }
mcphub_is_managed_local_pid() { return 0; }
mcphub_process_identity() {
  if [[ "$1" != "111" ]]; then
    printf '%s|test-lock-start:%s\n' "$1" "$1"
    return 0
  fi
  local count=0
  [[ -f "${TEST_COUNTER}" ]] && count="$(tr -d '[:space:]' <"${TEST_COUNTER}")"
  count="$((count + 1))"
  printf '%s\n' "${count}" >"${TEST_COUNTER}"
  if [[ "${count}" -le 2 ]]; then printf '111|linux-start-ticks:100\n'; else printf '111|linux-start-ticks:200\n'; fi
}
mcphub_wait_mode_ready() { return 1; }
mcphub_stop_managed_local() { printf 'unexpected-stop\n'; return 97; }
if mcphub_start_local; then
  exit 88
fi
[[ ! -e "${MCPHUB_INSTANCE_LOCK}" ]]
"""
    result = _run(
        body,
        env={"TEST_RUN_DIR": str(tmp_path / "run"), "TEST_COUNTER": str(counter)},
    )

    assert result.returncode == 0, result.stderr
    assert "unexpected-stop" not in result.stdout
    assert "process identity changed while waiting" in result.stderr
    assert counter.read_text(encoding="utf-8") == "3\n"


def test_last_moment_readiness_prevents_replacement_signal(tmp_path: Path) -> None:
    counter = tmp_path / "ready-count"
    body = r"""
MCPHUB_RUN_DIR="${TEST_RUN_DIR}"
MCPHUB_PID_FILE="${MCPHUB_RUN_DIR}/mcphub.pid"
MCPHUB_LOG_FILE="${MCPHUB_RUN_DIR}/mcphub.log"
MCPHUB_INSTANCE_LOCK="${MCPHUB_RUN_DIR}/instance.lock"
MCPHUB_DOWNSTREAM_RUNTIME_ROOT="${MCPHUB_RUN_DIR}/downstream"
mkdir -p "${MCPHUB_RUN_DIR}"
printf '111\n' >"${MCPHUB_PID_FILE}"
mcphub_runtime_is_ready() {
  local count=0
  [[ -f "${TEST_COUNTER}" ]] && count="$(tr -d '[:space:]' <"${TEST_COUNTER}")"
  count="$((count + 1))"
  printf '%s\n' "${count}" >"${TEST_COUNTER}"
  [[ "${count}" -ge 2 ]]
}
mcphub_distribution_is_selected() { return 0; }
mcphub_launch_agent_loaded() { return 1; }
mcphub_pid_file_running() { return 0; }
mcphub_is_managed_local_pid() { return 0; }
mcphub_process_identity() { printf '111|linux-start-ticks:100\n'; }
mcphub_wait_mode_ready() { return 1; }
kill() {
  [[ "$1" == "-0" ]] && return 0
  printf 'unexpected-signal %s\n' "$*"
  return 97
}
mcphub_start_local
[[ ! -e "${MCPHUB_INSTANCE_LOCK}" ]]
"""
    result = _run(
        body,
        env={"TEST_RUN_DIR": str(tmp_path / "run"), "TEST_COUNTER": str(counter)},
    )

    assert result.returncode == 0, result.stderr
    assert "unexpected-signal" not in result.stdout
    assert "runtime became ready; preserving it" in result.stderr
    assert counter.read_text(encoding="utf-8") == "3\n"


def test_dead_owner_hardlink_lock_is_reaped_exactly(tmp_path: Path) -> None:
    body = r"""
MCPHUB_RUN_DIR="${TEST_RUN_DIR}"
MCPHUB_INSTANCE_LOCK="${MCPHUB_RUN_DIR}/instance.lock"
mkdir -p "${MCPHUB_RUN_DIR}"
dead_pid=999999
receipt="${MCPHUB_INSTANCE_LOCK}.owner.${dead_pid}.123"
mkdir "${receipt}"
printf '%s\n%s\n%s\n' "${dead_pid}" "${dead_pid}|test-dead:1" "${receipt}" >"${receipt}/claim"
ln "${receipt}/claim" "${MCPHUB_INSTANCE_LOCK}"
mcphub_reap_stale_instance_lock
[[ ! -e "${MCPHUB_INSTANCE_LOCK}" && ! -e "${receipt}" ]]
"""
    result = _run(body, env={"TEST_RUN_DIR": str(tmp_path / "run")})

    assert result.returncode == 0, result.stderr


def test_live_owner_lock_is_never_reaped(tmp_path: Path) -> None:
    body = r"""
MCPHUB_RUN_DIR="${TEST_RUN_DIR}"
MCPHUB_INSTANCE_LOCK="${MCPHUB_RUN_DIR}/instance.lock"
mkdir -p "${MCPHUB_RUN_DIR}"
owner_pid="${BASHPID:-$$}"
receipt="${MCPHUB_INSTANCE_LOCK}.owner.${owner_pid}.123"
mkdir "${receipt}"
printf '%s\n%s\n%s\n' "${owner_pid}" "${owner_pid}|test-live:1" "${receipt}" >"${receipt}/claim"
ln "${receipt}/claim" "${MCPHUB_INSTANCE_LOCK}"
if mcphub_reap_stale_instance_lock; then exit 88; fi
[[ "${MCPHUB_INSTANCE_LOCK}" -ef "${receipt}/claim" ]]
"""
    result = _run(body, env={"TEST_RUN_DIR": str(tmp_path / "run")})

    assert result.returncode == 0, result.stderr


def test_stale_lock_with_non_hardlinked_claim_is_preserved(tmp_path: Path) -> None:
    body = r"""
MCPHUB_RUN_DIR="${TEST_RUN_DIR}"
MCPHUB_INSTANCE_LOCK="${MCPHUB_RUN_DIR}/instance.lock"
mkdir -p "${MCPHUB_RUN_DIR}"
dead_pid=999999
receipt="${MCPHUB_INSTANCE_LOCK}.owner.${dead_pid}.123"
mkdir "${receipt}"
printf '%s\n%s\n%s\n' "${dead_pid}" "${dead_pid}|test-dead:1" "${receipt}" >"${receipt}/claim"
cp "${receipt}/claim" "${MCPHUB_INSTANCE_LOCK}"
if mcphub_reap_stale_instance_lock; then exit 88; fi
[[ -f "${MCPHUB_INSTANCE_LOCK}" && -f "${receipt}/claim" ]]
"""
    result = _run(body, env={"TEST_RUN_DIR": str(tmp_path / "run")})

    assert result.returncode == 0, result.stderr


def test_acquire_reaps_one_proven_dead_owner_then_publishes_current_lock(tmp_path: Path) -> None:
    body = r"""
MCPHUB_RUN_DIR="${TEST_RUN_DIR}"
MCPHUB_INSTANCE_LOCK="${MCPHUB_RUN_DIR}/instance.lock"
mkdir -p "${MCPHUB_RUN_DIR}"
dead_pid=999999
receipt="${MCPHUB_INSTANCE_LOCK}.owner.${dead_pid}.123"
mkdir "${receipt}"
printf '%s\n%s\n%s\n' "${dead_pid}" "${dead_pid}|test-dead:1" "${receipt}" >"${receipt}/claim"
ln "${receipt}/claim" "${MCPHUB_INSTANCE_LOCK}"
mcphub_process_identity() { printf '%s|test-current:%s\n' "$1" "$1"; }
mcphub_acquire_instance_lock
[[ "$(sed -n '1p' "${MCPHUB_INSTANCE_LOCK}")" == "${BASHPID:-$$}" ]]
mcphub_release_instance_lock
[[ ! -e "${MCPHUB_INSTANCE_LOCK}" ]]
"""
    result = _run(body, env={"TEST_RUN_DIR": str(tmp_path / "run")})

    assert result.returncode == 0, result.stderr
