"""Contract tests for grok-delegate preflight.sh and bundled doctor.py."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = REPO_ROOT / "skills" / "grok-delegate" / "scripts" / "preflight.sh"
DOCTOR = REPO_ROOT / "skills" / "grok-delegate" / "scripts" / "doctor.py"
BASH = "/bin/bash"
_ISOLATED_PATH_PREFIX = "/usr/bin:/bin"


def _run_preflight(
    *,
    env: dict[str, str] | None = None,
    cwd: Path | str = REPO_ROOT,
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    merged.setdefault("PATH", _ISOLATED_PATH_PREFIX)
    if env:
        merged.update(env)
    return subprocess.run(
        [BASH, str(PREFLIGHT), *(extra_args or [])],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
        env=merged,
    )


def _isolated_path(bin_dir: Path) -> str:
    return f"{bin_dir}:{_ISOLATED_PATH_PREFIX}"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _minimal_home(tmp_path: Path) -> Path:
    """Fake HOME with no Grok install so bundled doctor reports hard fails."""
    home = tmp_path / "home"
    home.mkdir()
    return home


def test_doctor_ok_false_exits_one(tmp_path: Path) -> None:
    home = _minimal_home(tmp_path)
    target = tmp_path / "target"
    target.mkdir()
    result = _run_preflight(
        env={"HOME": str(home), "PATH": _ISOLATED_PATH_PREFIX},
        cwd=target,
        extra_args=["--cwd", str(target)],
    )
    assert result.returncode == 1, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert any(c["name"] == "grok-binary" and c["status"] == "fail" for c in payload["checks"])


def test_preflight_finds_grok_on_path(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    grok = bin_dir / "grok"
    _write_executable(
        grok,
        """#!/bin/bash
if [[ "${1:-}" == "version" ]]; then
  echo "grok test-stub"
  exit 0
fi
echo grok
exit 0
""",
    )
    home = _minimal_home(tmp_path)
    home_config = home / ".grok"
    home_config.mkdir()
    (home_config / "config.toml").write_text("[dummy]\n", encoding="utf-8")
    target = tmp_path / "target"
    target.mkdir()
    result = _run_preflight(
        env={"HOME": str(home), "PATH": _isolated_path(bin_dir)},
        cwd=target,
        extra_args=["--cwd", str(target)],
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    binary_check = next(c for c in payload["checks"] if c["name"] == "grok-binary")
    assert binary_check["status"] == "ok"
    assert str(bin_dir) in binary_check["summary"]


def test_stdout_is_json_only(tmp_path: Path) -> None:
    home = _minimal_home(tmp_path)
    target = tmp_path / "target"
    target.mkdir()
    result = _run_preflight(
        env={"HOME": str(home), "PATH": _ISOLATED_PATH_PREFIX},
        cwd=target,
        extra_args=["--cwd", str(target)],
    )
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert "ok" in payload
    assert "checks" in payload
    assert isinstance(payload["checks"], list)


def test_preflight_from_foreign_cwd() -> None:
    result = _run_preflight(cwd="/tmp", extra_args=["--cwd", str(REPO_ROOT)])
    assert result.returncode in (0, 1), result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert "ok" in payload
    assert payload["checks"]
    target_check = next(c for c in payload["checks"] if c["name"] == "grok-target-config")
    assert str(REPO_ROOT) in target_check["summary"]


def test_doctor_direct_matches_preflight_contract(tmp_path: Path) -> None:
    home = _minimal_home(tmp_path)
    target = tmp_path / "target"
    target.mkdir()
    env = {**os.environ, "HOME": str(home), "PATH": _ISOLATED_PATH_PREFIX}
    result = subprocess.run(
        ["python3", str(DOCTOR), "--format", "json", "--cwd", str(target)],
        cwd=str(target),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["summary"]["fail"] >= 1