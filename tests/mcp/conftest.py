"""Shared helpers for loading `mcp/<name>/server.py` modules under test.

Each repo-authored MCP server directory is an independent uv workspace
member whose `server.py` shares the same filename across directories, so
tests load each one under a unique `sys.modules` key via
`importlib.util.spec_from_file_location` instead of a normal package import.
"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_server_module(server_name: str) -> ModuleType:
    """Import `mcp/<server_name>/server.py` under a unique, cached module name."""
    module_name = f"_test_mcp_server_{server_name.replace('-', '_')}"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    path = REPO_ROOT / "mcp" / server_name / "server.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def run_async[T](coro: Coroutine[Any, Any, T]) -> T:
    """Run an async FastMCP `Client` call from a synchronous pytest test."""
    return asyncio.run(coro)
