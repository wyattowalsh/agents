from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mcphub" / "rotate_bearer_token.py"
SPEC = importlib.util.spec_from_file_location("mcphub_bearer_rotation", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _private_env(path: Path, content: bytes) -> Path:
    path.write_bytes(content)
    path.chmod(0o600)
    return path


def test_rotates_only_the_exact_token_line_without_disclosing_values(tmp_path: Path) -> None:
    env_file = _private_env(
        tmp_path / ".env.mcphub",
        b"PORT=46683\n"
        b"MCPHUB_BEARER_TOKEN=old-private-value\n"
        b"MCPHUB_PUBLIC_URL=https://mcp.w4w.dev/mcp\n"
        b"MCPHUB_TUNNEL_ENABLED=true\n",
    )

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--env-file", str(env_file)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert json.loads(completed.stdout) == {
        "status": "rotated",
        "key": "MCPHUB_BEARER_TOKEN",
        "runtimeMode": "local-disabled",
    }
    assert completed.stderr == ""
    assert "old-private-value" not in completed.stdout
    lines = env_file.read_text().splitlines()
    assert lines[0] == "PORT=46683"
    assert "MCPHUB_PUBLIC_URL=https://mcp.w4w.dev/mcp/things" in lines
    assert "MCPHUB_REMOTE_MODE=disabled" in lines
    assert "MCPHUB_TUNNEL_ENABLED=false" in lines
    key, token = lines[1].split("=", 1)
    assert key == "MCPHUB_BEARER_TOKEN"
    assert token
    assert token != "old-private-value"
    assert env_file.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize(
    "content",
    [
        b"PORT=46683\n",
        b"MCPHUB_BEARER_TOKEN=\n",
        b"MCPHUB_BEARER_TOKEN=one\nMCPHUB_BEARER_TOKEN=two\n",
    ],
)
def test_rejects_missing_empty_or_duplicate_assignments(tmp_path: Path, content: bytes) -> None:
    env_file = _private_env(tmp_path / ".env.mcphub", content)
    before = env_file.read_bytes()

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--env-file", str(env_file)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    assert json.loads(completed.stdout) == {
        "status": "error",
        "reasonCode": "MCPHUB_BEARER_ROTATION_FAILED",
    }
    assert env_file.read_bytes() == before


def test_rejects_symlink_and_non_private_modes(tmp_path: Path) -> None:
    target = _private_env(tmp_path / "target.env", b"MCPHUB_BEARER_TOKEN=private\n")
    symlink = tmp_path / ".env.mcphub"
    symlink.symlink_to(target)
    with pytest.raises(MODULE.RotationError):
        MODULE.rotate_bearer_token(symlink)

    target.chmod(0o640)
    with pytest.raises(MODULE.RotationError):
        MODULE.rotate_bearer_token(target)


def test_rejects_hardlinked_env_without_replacing_either_name(tmp_path: Path) -> None:
    env_file = _private_env(tmp_path / ".env.mcphub", b"MCPHUB_BEARER_TOKEN=private\n")
    sibling = tmp_path / "retained.env"
    os.link(env_file, sibling)
    before = env_file.read_bytes()

    with pytest.raises(MODULE.RotationError):
        MODULE.rotate_bearer_token(env_file)

    assert env_file.read_bytes() == before
    assert sibling.read_bytes() == before


def test_rotation_leaves_no_temporary_file(tmp_path: Path) -> None:
    env_file = _private_env(tmp_path / ".env.mcphub", b"MCPHUB_BEARER_TOKEN=private\n")
    MODULE.rotate_bearer_token(env_file)
    assert sorted(path.name for path in tmp_path.iterdir()) == [env_file.name]
    assert os.stat(env_file).st_mode & 0o777 == 0o600


def test_rejects_duplicate_safe_runtime_assignments_without_writing(tmp_path: Path) -> None:
    env_file = _private_env(
        tmp_path / ".env.mcphub",
        b"MCPHUB_BEARER_TOKEN=private\n"
        b"MCPHUB_PUBLIC_URL=https://mcp.w4w.dev/mcp\n"
        b"MCPHUB_PUBLIC_URL=https://mcp.w4w.dev/mcp/things\n",
    )
    before = env_file.read_bytes()

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--env-file", str(env_file)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    assert env_file.read_bytes() == before
