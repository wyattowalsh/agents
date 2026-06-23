"""Tests for wagents runtime repo discovery."""

from pathlib import Path

from wagents.context import (
    REPO_ROOT_ENV,
    bootstrap_cli_context,
    find_repo_root_from,
    resolve_repo_root,
)


def test_find_repo_root_from_markers(tmp_path: Path):
    (tmp_path / "skills").mkdir()
    (tmp_path / "agents").mkdir()
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "wagents"\n', encoding="utf-8")

    assert find_repo_root_from(tmp_path / "nested" / "dir") == tmp_path.resolve()


def test_resolve_repo_root_from_env(tmp_path: Path, monkeypatch):
    (tmp_path / "skills").mkdir()
    (tmp_path / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    monkeypatch.setenv(REPO_ROOT_ENV, str(tmp_path))

    assert resolve_repo_root() == tmp_path.resolve()


def test_bootstrap_prefers_monkeypatched_root(tmp_path: Path, monkeypatch):
    (tmp_path / "skills").mkdir()
    (tmp_path / "agents").mkdir()
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "wagents"\n', encoding="utf-8")
    monkeypatch.setattr("wagents.ROOT", tmp_path)

    ctx = bootstrap_cli_context(None)
    assert ctx.repo_root == tmp_path.resolve()


def test_resolve_repo_root_returns_none_outside_repo(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("wagents.ROOT", tmp_path)
    monkeypatch.setattr("wagents.context._package_install_root", lambda: tmp_path)
    assert resolve_repo_root() is None
