"""Editor vs Agent CLI discover-surface split."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "harness-master" / "scripts"


def _load():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    path = SCRIPTS / "discover_surfaces.py"
    spec = importlib.util.spec_from_file_location("discover_surfaces", path)
    assert spec
    assert spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _paths(entries: list[dict[str, str]]) -> set[str]:
    return {entry["path"] for entry in entries}


def test_editor_discover_omits_cli_only_files():
    mod = _load()
    editor_paths = _paths(mod.PROJECT_SURFACES["cursor"]) | _paths(mod.GLOBAL_SURFACES["cursor"])
    assert ".cursor/cli.json" not in editor_paths
    assert "~/.cursor/cli-config.json" not in editor_paths


def test_cursor_cli_discover_keeps_cli_only_files():
    mod = _load()
    cli_paths = _paths(mod.PROJECT_SURFACES["cursor-cli"]) | _paths(mod.GLOBAL_SURFACES["cursor-cli"])
    assert ".cursor/cli.json" in cli_paths
    assert "~/.cursor/cli-config.json" in cli_paths
