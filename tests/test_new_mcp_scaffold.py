"""Dry-run tests for skills/mcp-creator/scripts/scaffold_mcp.py."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAFFOLD_SCRIPT = REPO_ROOT / "skills" / "mcp-creator" / "scripts" / "scaffold_mcp.py"


def _load_scaffold_module():
    spec = importlib.util.spec_from_file_location("scaffold_mcp", SCAFFOLD_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dry_run_prints_scaffold_artifacts(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "skills").mkdir()
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "wagents"\n', encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    module = _load_scaffold_module()
    path = module.scaffold_mcp(tmp_path, "example-server", dry_run=True)
    assert path == tmp_path / "mcp" / "example-server"
    assert not path.exists()


def test_dry_run_cli_exits_zero(tmp_path: Path) -> None:
    (tmp_path / "skills").mkdir()
    result = subprocess.run(
        [sys.executable, str(SCAFFOLD_SCRIPT), "--dry-run", "example-server"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "FastMCP" in result.stdout
    assert "pyproject.toml" in result.stdout
    assert "fastmcp.json" in result.stdout


def test_invalid_name_exits_one(tmp_path: Path) -> None:
    (tmp_path / "skills").mkdir()
    result = subprocess.run(
        [sys.executable, str(SCAFFOLD_SCRIPT), "--dry-run", "BadName"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "kebab-case" in result.stderr


def test_existing_directory_exits_one(tmp_path: Path) -> None:
    (tmp_path / "skills").mkdir()
    existing = tmp_path / "mcp" / "dup-server"
    existing.mkdir(parents=True)
    (existing / "server.py").write_text("# existing\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCAFFOLD_SCRIPT), "dup-server"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "already exists" in result.stderr
