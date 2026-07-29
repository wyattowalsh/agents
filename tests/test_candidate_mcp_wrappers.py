from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NODE_WRAPPER = ROOT / "scripts" / "mcphub" / "wrappers" / "candidate-node"
UV_WRAPPER = ROOT / "scripts" / "mcphub" / "wrappers" / "candidate-uv-tool"


def _fake_executable(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nprintf '%s\\n' \"$*\"\n", encoding="utf-8")
    path.chmod(0o755)


@pytest.mark.parametrize(
    ("server", "expected_args"),
    [
        ("mcp-server-chart", ""),
        ("axiom-mcp", ""),
        ("better-icons", "mcp"),
        ("designer-skill-mcp", ""),
        ("mcp-dashboards", "--stdio"),
        ("mcp-excalidraw-server", ""),
        ("mcp-server-mobile", "--stdio"),
        ("nullcost-plugin", "mcp-server"),
        ("p2a", ""),
        ("semiotic-mcp", ""),
    ],
)
def test_candidate_node_wrapper_runs_only_allowlisted_managed_binary(
    tmp_path: Path, server: str, expected_args: str
) -> None:
    install_root = tmp_path / ".local/share/wagents/candidate-runtime/npm"
    target = install_root / "packages" / server
    _fake_executable(target)
    bin_path = install_root / "node_modules/.bin" / server
    bin_path.parent.mkdir(parents=True, exist_ok=True)
    bin_path.symlink_to(target)

    result = subprocess.run(
        [NODE_WRAPPER, server],
        env={**os.environ, "HOME": str(tmp_path)},
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.strip() == expected_args


def test_candidate_node_wrapper_pins_openspec_repo_argument(tmp_path: Path) -> None:
    install_root = tmp_path / ".local/share/wagents/candidate-runtime/npm"
    target = install_root / "packages/openspec-mcp"
    _fake_executable(target)
    bin_path = install_root / "node_modules/.bin/openspec-mcp"
    bin_path.parent.mkdir(parents=True, exist_ok=True)
    bin_path.symlink_to(target)

    result = subprocess.run(
        [NODE_WRAPPER, "openspec-mcp"],
        env={**os.environ, "HOME": str(tmp_path)},
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.strip() == str(ROOT)


@pytest.mark.parametrize(
    ("package", "server", "expected_args"),
    [
        ("charted", "charted-mcp", ""),
        ("csvglow", "csvglow", "--mcp"),
        ("geo-optimizer-skill", "geo-mcp", ""),
        ("langfuse-mcp", "langfuse-mcp", ""),
        ("paper-search-mcp", "paper-search-mcp", ""),
    ],
)
def test_candidate_uv_wrapper_runs_only_allowlisted_managed_binary(
    tmp_path: Path, package: str, server: str, expected_args: str
) -> None:
    executable = tmp_path / ".local/share/uv/tools" / package / "bin" / server
    _fake_executable(executable)

    result = subprocess.run(
        [UV_WRAPPER, package, server],
        env={**os.environ, "HOME": str(tmp_path)},
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.strip() == expected_args


@pytest.mark.parametrize(
    ("argv", "expected_error"),
    [
        ([NODE_WRAPPER, "unknown"], "unsupported managed server"),
        ([NODE_WRAPPER, "better-icons", "unexpected"], "usage:"),
        ([UV_WRAPPER, "charted", "unknown"], "unsupported managed package/server pair"),
        ([UV_WRAPPER, "charted", "charted-mcp", "unexpected"], "usage:"),
    ],
)
def test_candidate_wrappers_reject_unknown_or_extra_arguments(
    tmp_path: Path, argv: list[Path | str], expected_error: str
) -> None:
    result = subprocess.run(
        argv,
        env={**os.environ, "HOME": str(tmp_path)},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 64
    assert expected_error in result.stderr


@pytest.mark.parametrize(
    "argv",
    [
        [NODE_WRAPPER, "better-icons"],
        [UV_WRAPPER, "charted", "charted-mcp"],
    ],
)
def test_candidate_wrappers_fail_closed_when_managed_binary_is_missing(
    tmp_path: Path, argv: list[Path | str]
) -> None:
    result = subprocess.run(
        argv,
        env={**os.environ, "HOME": str(tmp_path)},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 127
    assert "managed executable is missing" in result.stderr
