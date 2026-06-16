"""Tests for discover-skills schemas.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "discover-skills" / "scripts"


def _load():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    path = SCRIPTS / "schemas.py"
    spec = importlib.util.spec_from_file_location("schemas", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_agent_targets_load() -> None:
    mod = _load()
    agents = mod.load_agent_targets()
    assert "claude-code" in agents
    assert "grok" in agents


def test_build_install_command() -> None:
    mod = _load()
    cmd = mod.build_install_command("owner/repo", "my-skill", agents=["codex", "cursor"])
    assert "npx skills add owner/repo" in cmd
    assert "--skill my-skill" in cmd
    assert "-a codex" in cmd
    assert "-a cursor" in cmd


def test_dedup_key_stable() -> None:
    mod = _load()
    assert mod.dedup_key("Foo", "Bar/Baz") == "foo@bar/baz"