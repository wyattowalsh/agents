"""Tests for review skill check.py portable validation helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK_PATH = ROOT / "skills" / "review" / "scripts" / "check.py"


def _load_check_module():
    spec = importlib.util.spec_from_file_location("review_check_for_tests", CHECK_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_package_script_prefers_bundled_toolkit():
    check = _load_check_module()
    toolkit = check._toolkit_path()
    package = check._package_script(toolkit)
    assert package is not None
    assert package.name == "package.py"
    assert package.parent.name == "asset_toolkit"


def test_audit_script_none_in_portable_ci(monkeypatch):
    check = _load_check_module()
    monkeypatch.setenv("SKILL_PORTABLE_CI", "1")
    assert check._audit_script() is None


def test_audit_script_returns_repo_sibling_when_available(monkeypatch):
    check = _load_check_module()
    monkeypatch.delenv("SKILL_PORTABLE_CI", raising=False)
    monkeypatch.delenv("PORTABLE_CI", raising=False)
    audit = check._audit_script()
    if (ROOT / "skills" / "skill-creator" / "scripts" / "audit.py").is_file():
        assert audit is not None
        assert audit.name == "audit.py"
    else:
        assert audit is None


def test_audit_script_stderr_when_skill_creator_missing(monkeypatch, capsys, tmp_path):
    check = _load_check_module()
    fake_skill_dir = tmp_path / "review"
    fake_skill_dir.mkdir()
    monkeypatch.setattr(check, "SKILL_DIR", fake_skill_dir)
    monkeypatch.delenv("SKILL_PORTABLE_CI", raising=False)
    monkeypatch.delenv("PORTABLE_CI", raising=False)

    result = check._audit_script()
    assert result is None
    captured = capsys.readouterr()
    assert "audit skipped" in captured.err


def test_portable_ci_env_aliases(monkeypatch):
    check = _load_check_module()
    monkeypatch.delenv("SKILL_PORTABLE_CI", raising=False)
    monkeypatch.setenv("PORTABLE_CI", "1")
    assert check._portable_ci() is True

    monkeypatch.delenv("PORTABLE_CI", raising=False)
    monkeypatch.setenv("SKILL_PORTABLE_CI", "1")
    assert check._portable_ci() is True

    monkeypatch.delenv("SKILL_PORTABLE_CI", raising=False)
    assert check._portable_ci() is False
