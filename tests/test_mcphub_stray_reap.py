"""Hermetic proof that runtime lifecycle scripts touch only tracked processes."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / "scripts" / "mcphub" / "common.sh"
REAP = ROOT / "scripts" / "mcphub" / "reap-strays.sh"
DOWN = ROOT / "scripts" / "mcphub" / "down.sh"
LAUNCH = ROOT / "scripts" / "mcphub" / "launch-agent-run.sh"
PLIST = ROOT / "config" / "launchd" / "com.wyattowalsh.mcphub.plist"
JUSTFILE = ROOT / "justfile"


def _source_and_match(command: str) -> bool:
    body = (
        f"source {shlex.quote(str(COMMON))}; "
        "MCPHUB_DOWNSTREAM_RUNTIME_ROOT=/tmp/mcphub-runtime; "
        "mcphub_process_command() { printf '%s\\n' \"${MOCK_COMMAND}\"; }; "
        "if mcphub_is_managed_local_pid 123; then printf yes; else printf no; fi"
    )
    result = subprocess.run(
        ["/bin/bash", "-c", body],
        check=False,
        text=True,
        capture_output=True,
        timeout=10,
        env={
            "HOME": "/tmp",
            "PATH": "/usr/bin:/bin",
            "LANG": "C",
            "MOCK_COMMAND": command,
        },
    )
    assert result.returncode == 0, result.stderr
    return result.stdout == "yes"


def test_managed_pid_matcher_accepts_only_the_exact_selected_launcher() -> None:
    launcher = ROOT / "scripts" / "mcphub" / "downstream-launch.mjs"
    selected = f"node --disallow-code-generation-from-strings {launcher} --runtime-root /tmp/mcphub-runtime"
    assert _source_and_match(selected)
    assert _source_and_match(f"/opt/homebrew/bin/node {selected.removeprefix('node ')}")
    assert not _source_and_match(f"node {launcher} --runtime-root /tmp/mcphub-runtime")
    assert not _source_and_match("npx -y @samanhappy/mcphub@1.0.32")
    assert not _source_and_match(f"bash {ROOT}/scripts/mcphub/launch-agent-run.sh")
    assert not _source_and_match(f"node {launcher} --runtime-root /tmp/other")


def test_reaper_only_validates_or_removes_one_tracked_pid_receipt() -> None:
    text = REAP.read_text(encoding="utf-8")
    assert 'mcphub_read_pid_file "${MCPHUB_PID_FILE}"' in text
    assert "removed one stale MCPHub runtime pid receipt" in text
    assert "mcphub_is_managed_local_pid" in text
    assert "no stray process scan is performed" in text
    for forbidden in ("pgrep", "pkill", "ps ax", "kill -TERM", "kill -KILL"):
        assert forbidden not in text


def test_down_stops_only_receipt_validated_local_and_tunnel_processes() -> None:
    text = DOWN.read_text(encoding="utf-8")
    assert "mcphub_stop_managed_local" in text
    assert "mcphub_stop_tunnel" in text
    assert "mcphub_reap" not in text
    assert "pgrep" not in text
    assert "pkill" not in text


def test_launch_agent_execs_the_single_selected_process_without_child_tracking() -> None:
    text = LAUNCH.read_text(encoding="utf-8")
    assert 'printf \'%s\\n\' "$$" >"${MCPHUB_PID_FILE}"' in text
    assert 'exec bash "${SCRIPT_DIR}/start-server.sh"' in text
    for forbidden in ("CHILD_PID", "spawn_in_new_session", "wait ", "trap ", "reap_stray"):
        assert forbidden not in text


def test_launchd_and_justfile_expose_bounded_restart_and_reap_semantics() -> None:
    plist = PLIST.read_text(encoding="utf-8")
    justfile = JUSTFILE.read_text(encoding="utf-8")
    assert "<key>SuccessfulExit</key>" in plist
    assert "<key>ThrottleInterval</key>" in plist
    assert "<key>KeepAlive</key>\n  <true/>" not in plist
    assert "mcphub-reap-strays:" in justfile
    assert "never scan unrelated processes" in justfile
