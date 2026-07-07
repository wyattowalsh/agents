"""Contract tests for safety-sensitive just recipes."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
JUSTFILE = ROOT / "justfile"


def _resolve_just() -> str | None:
    candidates = [
        shutil.which("just"),
        "/opt/homebrew/bin/just",
        "/usr/local/bin/just",
        "/usr/bin/just",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and "mise/shims" not in candidate:
            return candidate
    return candidates[0]


JUST = _resolve_just()


pytestmark = pytest.mark.skipif(JUST is None, reason="just is not installed")


def _run_just(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    assert JUST is not None
    return subprocess.run(
        [JUST, *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_justfile_parses() -> None:
    result = _run_just("--summary")

    assert result.returncode == 0, result.stderr
    assert "install-agent" in result.stdout
    assert "mcphub-reconcile-runtime" in result.stdout


def test_argument_recipes_reject_shell_metacharacters_before_execution() -> None:
    for args in [
        ("--dry-run", "install-agent", "--agent", "codex;printf-JUST-INJECTION-PROBE"),
        ("--dry-run", "install-skill", "--skill", "review;printf-JUST-INJECTION-PROBE"),
    ]:
        result = _run_just(*args)

        assert result.returncode != 0
        assert "does not match pattern" in result.stderr


def test_user_arguments_are_not_interpolated_into_shell_source() -> None:
    text = JUSTFILE.read_text(encoding="utf-8")

    assert "{{ agent }}" not in text
    assert "{{ skill }}" not in text
    assert "{{FLAGS}}" not in text
    assert ' -a "$1" ' in text
    assert '--skill "$1"' in text
    assert 'reconcile-runtime.sh "$@"' in text


@pytest.mark.parametrize("recipe", ["apm-materialize", "apm-install", "apm-compile", "apm-audit"])
def test_apm_recipes_fail_nonzero_when_apm_is_missing(recipe: str, tmp_path: Path) -> None:
    if JUST and "mise/shims" in JUST:
        pytest.skip("PATH-sensitive recipe test requires a real just binary, not a mise shim")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for executable in ("npx", "uv"):
        path = bin_dir / executable
        path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        path.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:/bin:/usr/bin"
    result = _run_just(recipe, env=env)

    if shutil.which("apm", path=env["PATH"]):
        pytest.skip("apm is installed in the minimal test PATH")

    assert result.returncode != 0
    assert "apm CLI not found" in result.stderr
