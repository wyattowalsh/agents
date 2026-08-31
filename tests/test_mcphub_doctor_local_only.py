"""Hermetic cloudflared-process proofs for local-only MCPHub doctor mode."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCTOR = ROOT / "scripts" / "mcphub" / "doctor.sh"


def _process_state(*, pids: str, pgrep_status: int, managed_pids: str = "") -> tuple[int, str]:
    script = r"""
set -euo pipefail
export MCPHUB_DOCTOR_LIBRARY_ONLY=true
source "$1"
pgrep() {
  [[ "$1" == "-x" && "$2" == "cloudflared" ]] || return 64
  if [[ -n "${TEST_PIDS}" ]]; then
    printf '%s\n' "${TEST_PIDS}"
  fi
  return "${TEST_PGREP_STATUS}"
}
mcphub_is_managed_tunnel_pid() {
  case ",${TEST_MANAGED_PIDS}," in
    *",$1,"*) return 0 ;;
    *) return 1 ;;
  esac
}
state=""
if state="$(mcphub_cloudflared_process_state)"; then
  status=0
else
  status=$?
fi
printf '%s|%s\n' "${status}" "${state}"
"""
    completed = subprocess.run(
        ["bash", "-c", script, "doctor-test", str(DOCTOR)],
        cwd=ROOT,
        env={
            **os.environ,
            "TEST_PIDS": pids,
            "TEST_PGREP_STATUS": str(pgrep_status),
            "TEST_MANAGED_PIDS": managed_pids,
        },
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    status, state = completed.stdout.strip().split("|", 1)
    return int(status), state


def test_cloudflared_absence_is_an_explicit_success() -> None:
    assert _process_state(pids="", pgrep_status=1) == (0, "absent")


@pytest.mark.parametrize(
    ("pids", "managed_pids", "expected"),
    [
        ("101", "101", "managed-present"),
        ("202", "", "unmanaged-present"),
        ("101\n202", "101", "managed-and-unmanaged-present"),
    ],
)
def test_any_managed_or_unmanaged_cloudflared_process_fails_local_only_proof(
    pids: str,
    managed_pids: str,
    expected: str,
) -> None:
    assert _process_state(pids=pids, pgrep_status=0, managed_pids=managed_pids) == (1, expected)


@pytest.mark.parametrize(("pids", "pgrep_status"), [("", 2), ("not-a-pid", 0)])
def test_cloudflared_inspection_errors_fail_closed(pids: str, pgrep_status: int) -> None:
    assert _process_state(pids=pids, pgrep_status=pgrep_status) == (2, "inspection-failed")


def test_local_only_doctor_requires_process_receipt_and_activation_absence() -> None:
    source = DOCTOR.read_text(encoding="utf-8")

    assert "cloudflared process:" in source
    assert "tunnel pid receipt:" in source
    assert "remote activation receipt:" in source
    assert "MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH" in source
    assert "mcphub_remote_activation_mode" in source
    assert "MCPHUB_CAPTURE_RECEIPT_VALID" not in source
    assert "MCPHUB_FINAL_STAMP_VALID" not in source
