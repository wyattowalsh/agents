"""Read-only path allowlist guard shared by every repo-authored MCP server.

Every `mcp/<name>/server.py` that exposes filesystem reads to a model must
route through :func:`resolve_read_only_path` instead of resolving paths
itself, so the traversal/allowlist policy lives in exactly one place.
"""

from __future__ import annotations

from pathlib import Path

from wagents import ROOT

# Prefixes are relative to the repo root and matched against the resolved,
# traversal-free candidate path. Keep this list narrow — every new repo
# surface that should be MCP-readable must be added explicitly.
DEFAULT_ALLOWED_PREFIXES: tuple[str, ...] = (
    "skills",
    "agents",
    "mcp",
    "docs/src/content/docs",
    "docs/src/authoring",
    "docs/public/generated-reports",
    "docs/public/generated-registries",
    "docs/public/generated-skill-indexes",
    "config",
    "openspec",
    "planning/manifests",
    "kb/wiki",
    "README.md",
    "AGENTS.md",
)


class PathNotAllowedError(PermissionError):
    """Raised when a requested relative path falls outside the read-only allowlist."""


def resolve_read_only_path(
    relative_path: str,
    *,
    allowed_prefixes: tuple[str, ...] = DEFAULT_ALLOWED_PREFIXES,
    repo_root: Path | None = None,
) -> Path:
    """Resolve *relative_path* under the repo root, enforcing the read-only allowlist.

    Rejects absolute paths, `..` traversal segments, symlink/resolve escapes
    outside *repo_root*, and any path whose repo-relative form does not start
    with one of *allowed_prefixes*. Returns the resolved absolute path on
    success; raises :class:`PathNotAllowedError` otherwise. Existence is not
    checked here — callers should handle `FileNotFoundError` themselves.
    """
    root = (repo_root or ROOT).resolve()
    if not isinstance(relative_path, str) or not relative_path or relative_path != relative_path.strip():
        raise PathNotAllowedError(f"Invalid path: {relative_path!r}")

    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise PathNotAllowedError(f"Absolute paths are not allowed: {relative_path!r}")
    if ".." in candidate.parts:
        raise PathNotAllowedError(f"Path traversal is not allowed: {relative_path!r}")

    resolved = (root / candidate).resolve()
    try:
        rel = resolved.relative_to(root)
    except ValueError as exc:
        raise PathNotAllowedError(f"Path escapes the repository root: {relative_path!r}") from exc

    rel_str = rel.as_posix()
    allowed = any(rel_str == prefix or rel_str.startswith(f"{prefix.rstrip('/')}/") for prefix in allowed_prefixes)
    if not allowed:
        raise PathNotAllowedError(f"Path is outside the read-only allowlist: {relative_path!r}")
    return resolved


def is_read_only_path_allowed(
    relative_path: str,
    *,
    allowed_prefixes: tuple[str, ...] = DEFAULT_ALLOWED_PREFIXES,
    repo_root: Path | None = None,
) -> bool:
    """Return whether *relative_path* would be accepted by :func:`resolve_read_only_path`."""
    try:
        resolve_read_only_path(relative_path, allowed_prefixes=allowed_prefixes, repo_root=repo_root)
    except PathNotAllowedError:
        return False
    return True


def read_text_within_allowlist(
    relative_path: str,
    *,
    allowed_prefixes: tuple[str, ...] = DEFAULT_ALLOWED_PREFIXES,
    repo_root: Path | None = None,
    max_bytes: int = 2_000_000,
) -> str:
    """Read a UTF-8 text file within the allowlist, bounded to *max_bytes*.

    Raises :class:`PathNotAllowedError` for disallowed paths, `FileNotFoundError`
    for missing files, and `IsADirectoryError` for directories.
    """
    resolved = resolve_read_only_path(relative_path, allowed_prefixes=allowed_prefixes, repo_root=repo_root)
    if not resolved.exists():
        raise FileNotFoundError(relative_path)
    if resolved.is_dir():
        raise IsADirectoryError(relative_path)
    raw = resolved.read_bytes()[: max_bytes + 1]
    if len(raw) > max_bytes:
        raise ValueError(f"File exceeds max_bytes={max_bytes}: {relative_path!r}")
    return raw.decode("utf-8", errors="replace")
