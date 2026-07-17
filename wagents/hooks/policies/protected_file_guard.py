"""Pure protected file path guard (fleet PreToolUse)."""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from typing import Any


def _secret_paths() -> Any:
    """Load secret_paths for both package imports and path-loaded dispatcher."""
    try:
        from wagents.hooks.policies import secret_paths as mod

        return mod
    except ImportError:  # pragma: no cover - standalone dispatcher path-load
        cache_key = "_wagents_policy_secret_paths"
        cached = sys.modules.get(cache_key)
        if cached is not None:
            return cached
        path = Path(__file__).with_name("secret_paths.py")
        spec = importlib.util.spec_from_file_location(cache_key, path)
        if spec is None or spec.loader is None:
            raise
        module = importlib.util.module_from_spec(spec)
        sys.modules[cache_key] = module
        spec.loader.exec_module(module)
        return module


_PROTECTED_SUFFIXES = (
    "/.ssh/id_rsa",
    "/.ssh/id_ed25519",
    "/.git/config",
    "/.git/HEAD",
)
_LOCKFILE_RE = re.compile(r"\.(lock|lockb)$|lock\.json$|lock\.yaml$")


def evaluate_protected_file(file_path: str) -> str | None:
    cleaned = (file_path or "").strip()
    if not cleaned:
        return None
    if re.search(r"\.\.(\/|$)", cleaned):
        return "Path traversal detected."
    secret_reason = _secret_paths().protected_basename_reason(cleaned)
    if secret_reason:
        return secret_reason
    for suffix in _PROTECTED_SUFFIXES:
        if suffix in cleaned:
            return f"Protected path: {cleaned}"
    if _LOCKFILE_RE.search(cleaned):
        return "Lock files should not be edited directly. Use the package manager instead."
    return None
