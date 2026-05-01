"""Compatibility bridge to the original script modules."""

from __future__ import annotations

import sys
from importlib import resources
from pathlib import Path
from types import ModuleType

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SOURCE_SCRIPTS_DIR = PACKAGE_ROOT / "scripts"


def scripts_dir() -> Path:
    """Return the source-tree or wheel-packaged legacy script directory."""
    if SOURCE_SCRIPTS_DIR.is_dir():
        return SOURCE_SCRIPTS_DIR
    packaged_scripts = resources.files("nerdbot").joinpath("scripts")
    with resources.as_file(packaged_scripts) as path:
        return path


def ensure_scripts_path() -> None:
    """Make the legacy script directory importable for compatibility imports."""
    scripts_path = str(scripts_dir())
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)


def load_script_module(name: str) -> ModuleType:
    """Import a legacy `kb_*` script module by name."""
    ensure_scripts_path()
    return __import__(name)


def kb_bootstrap() -> ModuleType:
    """Return the legacy bootstrap module."""
    return load_script_module("kb_bootstrap")


def kb_inventory() -> ModuleType:
    """Return the legacy inventory module."""
    return load_script_module("kb_inventory")


def kb_lint() -> ModuleType:
    """Return the legacy lint module."""
    return load_script_module("kb_lint")
