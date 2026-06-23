"""Tests for harness-master discovery schemas.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "harness-master" / "scripts" / "discovery"


def _load():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    path = SCRIPTS / "schemas.py"
    spec = importlib.util.spec_from_file_location("schemas", path)
    assert spec
    assert spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
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


def test_hook_scout_role_valid() -> None:
    mod = _load()
    assert "hook-scout" in mod.SCOUT_ROLES
    # validate accepts hook-scout in wave manifest
    manifest = {
        "session_id": "s",
        "wave": 2,
        "expected_count": 1,
        "tasks": [
            {
                "id": "W2-HK-00",
                "role": "hook-scout",
                "outputs": {"artifact": "/tmp/x.json"},
            }
        ],
    }
    errs = mod.validate_wave_manifest(manifest)
    assert errs == [] or all("invalid role" not in e for e in errs)
