"""Tests for skills/research/scripts/verify.py stop-hook checks."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_verify():
    path = ROOT / "skills" / "research" / "scripts" / "verify.py"
    spec = importlib.util.spec_from_file_location("research_verify", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verify = _load_verify()


def test_stop_skips_when_stop_hook_active(monkeypatch, capsys):
    fake_stdin = type("stdin", (), {"read": lambda self: json.dumps({"stop_hook_active": True})})()
    monkeypatch.setattr(verify.sys, "stdin", fake_stdin)

    code = verify.cmd_stop(argparse_namespace())

    out = json.loads(capsys.readouterr().out)
    assert code == 0
    assert out["ok"] is True
    assert out["skipped"] == "stop_hook_active"


def test_stop_skips_outside_git_repo(monkeypatch, capsys):
    monkeypatch.setattr(verify.sys, "stdin", type("stdin", (), {"read": lambda self: "{}"})())
    monkeypatch.setattr(verify, "_git_root", lambda: None)

    code = verify.cmd_stop(argparse_namespace())

    out = json.loads(capsys.readouterr().out)
    assert code == 0
    assert out["skipped"] == "not_git_repo"


def test_stop_passes_when_research_skill_is_clean(monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(verify.sys, "stdin", type("stdin", (), {"read": lambda self: "{}"})())
    monkeypatch.setattr(verify, "_git_root", lambda: tmp_path)
    monkeypatch.setattr(verify, "_tracked_status", lambda root, pathspec: "")

    code = verify.cmd_stop(argparse_namespace())

    out = json.loads(capsys.readouterr().out)
    assert code == 0
    assert out == {"ok": True, "checked": "skills/research"}


def test_stop_fails_when_research_skill_is_dirty(monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(verify.sys, "stdin", type("stdin", (), {"read": lambda self: "{}"})())
    monkeypatch.setattr(verify, "_git_root", lambda: tmp_path)
    monkeypatch.setattr(
        verify,
        "_tracked_status",
        lambda root, pathspec: " M skills/research/SKILL.md",
    )

    code = verify.cmd_stop(argparse_namespace())

    err = capsys.readouterr()
    out = json.loads(err.out)
    assert code == 1
    assert "modified tracked source files" in err.err
    assert out["ok"] is False
    assert out["dirty"] == [" M skills/research/SKILL.md"]


def argparse_namespace():
    import argparse

    return argparse.Namespace()
