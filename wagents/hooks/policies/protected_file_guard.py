"""Pure protected file path guard (fleet PreToolUse)."""
from __future__ import annotations

import re
from pathlib import Path

_SECRET_BASENAMES = {
    ".env", ".env.local", ".env.production", ".env.staging", ".env.development", ".env.test",
    "credentials.json", "token.pickle",
}
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
    basename = Path(cleaned).name
    if basename in _SECRET_BASENAMES:
        return f"Protected file: {cleaned}"
    for suffix in _PROTECTED_SUFFIXES:
        if suffix in cleaned:
            return f"Protected path: {cleaned}"
    if _LOCKFILE_RE.search(cleaned):
        return "Lock files should not be edited directly. Use the package manager instead."
    return None
