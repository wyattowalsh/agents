"""Portable path rendering and resolution for OSS-friendly sync surfaces."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
REPO_ROOT_TOKEN = "${REPO_ROOT}"


def render_portable_path(path: Path, *, repo_root: Path = REPO_ROOT, home: Path = HOME) -> str:
    """Render a path as ``${REPO_ROOT}/...`` or ``~/...`` for committed config."""
    resolved = path.expanduser().resolve()
    repo = repo_root.resolve()
    try:
        rel = resolved.relative_to(repo)
        return f"{REPO_ROOT_TOKEN}/{rel.as_posix()}"
    except ValueError:
        pass
    home_resolved = home.resolve()
    try:
        rel_home = resolved.relative_to(home_resolved)
        return f"~/{rel_home.as_posix()}"
    except ValueError:
        return str(resolved)


def resolve_portable_path(
    value: str,
    *,
    repo_root: Path = REPO_ROOT,
    home: Path = HOME,
) -> str:
    """Resolve portable sync-manifest paths to absolute filesystem paths."""
    if not isinstance(value, str):
        return str(value)
    text = value.strip()
    if text == REPO_ROOT_TOKEN:
        return str(repo_root.resolve())
    if text.startswith(f"{REPO_ROOT_TOKEN}/"):
        suffix = text[len(REPO_ROOT_TOKEN) + 1 :]
        return str((repo_root / suffix).resolve())
    if text == "~":
        return str(home.resolve())
    if text.startswith("~/"):
        return str((home / text[2:]).resolve())
    if text.startswith("/"):
        return str(Path(text).resolve())
    return str((repo_root / text).resolve())


def migrate_absolute_path(value: str, *, repo_root: Path = REPO_ROOT, home: Path = HOME) -> str:
    """Convert legacy absolute maintainer paths to portable form."""
    if not isinstance(value, str):
        return value
    text = value.strip()
    repo = repo_root.resolve()
    home_resolved = home.resolve()
    try:
        path = Path(text).expanduser().resolve()
        try:
            rel = path.relative_to(repo)
            return f"{REPO_ROOT_TOKEN}/{rel.as_posix()}"
        except ValueError:
            pass
        try:
            rel_home = path.relative_to(home_resolved)
            return f"~/{rel_home.as_posix()}"
        except ValueError:
            return text
    except OSError:
        return text


def contains_maintainer_absolute_path(text: str, *, home: Path = HOME) -> bool:
    """Return True when text embeds a user-specific absolute path leak."""
    return f"/Users/{home.name}/" in text
