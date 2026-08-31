"""Hermetic tests for atomic, non-starting MCPHub LaunchAgent installation."""

from __future__ import annotations

import json
import os
import plistlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mcphub" / "install_launch_agent.py"
TEMPLATE = ROOT / "config" / "launchd" / "com.wyattowalsh.mcphub.plist"


def _repo(tmp_path: Path, *, payload: dict[str, object] | None = None) -> Path:
    repo = tmp_path / "repo"
    source = repo / "config" / "launchd" / TEMPLATE.name
    runner = repo / "scripts" / "mcphub" / "launch-agent-run.sh"
    source.parent.mkdir(parents=True)
    runner.parent.mkdir(parents=True)
    if payload is None:
        source.write_bytes(TEMPLATE.read_bytes())
    else:
        source.write_bytes(plistlib.dumps(payload, fmt=plistlib.FMT_XML, sort_keys=False))
    runner.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    return repo


def _run(repo: Path, destination: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo-root",
            str(repo),
            "--destination",
            str(destination),
            *extra,
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_install_is_atomic_private_exact_and_never_starts_service(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    destination_parent = tmp_path / "LaunchAgents"
    destination_parent.mkdir(mode=0o700)
    destination = destination_parent / TEMPLATE.name

    completed = _run(repo, destination)

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "status": "installed",
        "service": "com.wyattowalsh.mcphub",
        "started": False,
    }
    expected = TEMPLATE.read_bytes().replace(b"/path/to/agents", os.fsencode(repo))
    assert destination.read_bytes() == expected
    assert destination.stat().st_mode & 0o777 == 0o600
    assert sorted(path.name for path in destination_parent.iterdir()) == [destination.name]
    source = SCRIPT.read_text(encoding="utf-8")
    assert "launchctl" not in source
    assert "subprocess" not in source

    checked = _run(repo, destination, "--check")
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["status"] == "current"


def test_check_reports_drift_without_replacing_bytes(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    destination_parent = tmp_path / "LaunchAgents"
    destination_parent.mkdir(mode=0o700)
    destination = destination_parent / TEMPLATE.name
    destination.write_text("drift\n", encoding="utf-8")
    destination.chmod(0o600)
    before = destination.read_bytes()

    completed = _run(repo, destination, "--check")

    assert completed.returncode == 1
    assert json.loads(completed.stdout)["reasonCode"] == "MCPHUB_LAUNCH_AGENT_INSTALL_FAILED"
    assert destination.read_bytes() == before


def test_install_rejects_symlink_destination_and_unsafe_parent(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    destination_parent = tmp_path / "LaunchAgents"
    destination_parent.mkdir(mode=0o700)
    target = destination_parent / "target.plist"
    target.write_text("preserve\n", encoding="utf-8")
    target.chmod(0o600)
    destination = destination_parent / TEMPLATE.name
    destination.symlink_to(target)

    symlink_result = _run(repo, destination)
    assert symlink_result.returncode == 1
    assert target.read_text(encoding="utf-8") == "preserve\n"

    destination.unlink()
    destination_parent.chmod(0o777)
    unsafe_parent_result = _run(repo, destination)
    assert unsafe_parent_result.returncode == 1
    assert not destination.exists()


def test_install_rejects_environment_values_in_template(tmp_path: Path) -> None:
    payload = plistlib.loads(TEMPLATE.read_bytes())
    payload["EnvironmentVariables"] = {"MCPHUB_BEARER_TOKEN": "must-not-ship"}
    repo = _repo(tmp_path, payload=payload)
    destination_parent = tmp_path / "LaunchAgents"
    destination_parent.mkdir(mode=0o700)
    destination = destination_parent / TEMPLATE.name

    completed = _run(repo, destination)

    assert completed.returncode == 1
    assert "must-not-ship" not in completed.stdout + completed.stderr
    assert not destination.exists()


def test_justfile_keeps_install_and_start_as_separate_explicit_steps() -> None:
    source = (ROOT / "justfile").read_text(encoding="utf-8")
    install_block = source.split("mcphub-install-launch-agent:\n", 1)[1].split("mcphub-install-launch-agent-check:", 1)[
        0
    ]
    start_block = source.split("mcphub-start-launch-agent:\n", 1)[1].split("mcphub-uninstall-launch-agent:", 1)[0]

    assert "install_launch_agent.py" in install_block
    assert "launchctl" not in install_block
    assert "launchctl bootstrap" in start_block
    assert "launchctl bootout" not in start_block
    assert "install_launch_agent.py" not in start_block
