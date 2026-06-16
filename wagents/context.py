"""Runtime context and repository discovery for globally installed wagents."""

from __future__ import annotations

import os
import sys
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT_ENV = "WAGENTS_REPO_ROOT"
PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_GIT_SOURCE = "git+https://github.com/wyattowalsh/agents"

EXIT_ENV_ERROR = 2


@dataclass(frozen=True)
class CliContext:
    """Per-invocation CLI state."""

    repo_root: Path | None
    explicit_repo_root: bool
    install_mode: str | None = None


_CLI_CONTEXT: ContextVar[CliContext | None] = ContextVar("wagents_cli_context", default=None)


class RepoRootPath:
    """Lazy repo root for legacy ``REPO_ROOT / \"skills\"`` expressions."""

    def __truediv__(self, key: str | Path) -> Path:
        return get_repo_root() / key

    def __str__(self) -> str:
        return str(get_repo_root())

    def __repr__(self) -> str:
        return f"RepoRootPath({get_repo_root()!r})"

    def resolve(self, strict: bool = False) -> Path:
        return get_repo_root().resolve(strict=strict)

    def __fspath__(self) -> str:
        return str(get_repo_root())

    def exists(self) -> bool:
        return get_repo_root().exists()

    def is_dir(self) -> bool:
        return get_repo_root().is_dir()


REPO_ROOT_PROXY = RepoRootPath()


def _package_install_root() -> Path:
    return PACKAGE_DIR.parent


def _is_agents_repo(path: Path) -> bool:
    resolved = path.resolve()
    if not (resolved / "skills").is_dir():
        return False
    if (resolved / "agent-bundle.json").is_file() or (resolved / "AGENTS.md").is_file():
        return True
    return (resolved / "agents").is_dir() and (resolved / "pyproject.toml").is_file()


def find_repo_root_from(start: Path) -> Path | None:
    """Walk parents from *start* for an agents repository root."""
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if _is_agents_repo(candidate):
            return candidate
    return None


def resolve_repo_root(
    *,
    explicit: Path | str | None = None,
    cwd: Path | None = None,
    start: Path | None = None,
) -> Path | None:
    """Resolve the agents repo root using env, explicit flag, cwd walk, then editable fallback."""
    if explicit is not None:
        path = Path(explicit).expanduser()
        if _is_agents_repo(path):
            return path.resolve()
        return None

    env_value = os.environ.get(REPO_ROOT_ENV, "").strip()
    if env_value:
        path = Path(env_value).expanduser()
        if _is_agents_repo(path):
            return path.resolve()

    search_start = cwd or start or Path.cwd()
    found = find_repo_root_from(search_start)
    if found is not None:
        return found

    editable = _package_install_root()
    if _is_agents_repo(editable):
        return editable.resolve()
    return None


def require_repo_root() -> Path:
    """Return the repo root or raise typer.Exit with remediation."""
    root = get_repo_root_optional()
    if root is not None:
        return root
    import typer

    typer.echo(
        "Error: agents repository not found. Clone the repo, run from inside it, "
        f"or set {REPO_ROOT_ENV}.",
        err=True,
    )
    raise typer.Exit(code=EXIT_ENV_ERROR)


def get_repo_root_optional() -> Path | None:
    """Return the resolved repo root when available."""
    ctx = _CLI_CONTEXT.get()
    if ctx is not None and ctx.repo_root is not None:
        return ctx.repo_root
    from wagents import ROOT

    if _is_agents_repo(ROOT):
        return ROOT.resolve()
    resolved = resolve_repo_root()
    return resolved.resolve() if resolved is not None else None


def get_repo_root() -> Path:
    """Return the repo root, exiting when discovery fails."""
    return require_repo_root()


def resolve_repo_script(relative: str | Path) -> Path:
    """Resolve a repo-relative script path under the discovered root."""
    root = require_repo_root()
    script = (root / relative).resolve()
    if not script.is_file():
        import typer

        typer.echo(f"Error: expected repo script missing: {script}", err=True)
        raise typer.Exit(code=EXIT_ENV_ERROR)
    return script


def set_cli_context(
    *,
    repo_root: Path | None,
    explicit_repo_root: bool,
    install_mode: str | None = None,
) -> CliContext:
    """Store per-invocation CLI context and sync module-level paths."""
    ctx = CliContext(
        repo_root=repo_root.resolve() if repo_root is not None else None,
        explicit_repo_root=explicit_repo_root,
        install_mode=install_mode,
    )
    _CLI_CONTEXT.set(ctx)
    if repo_root is not None:
        _sync_module_paths(repo_root.resolve())
    return ctx


def _sync_module_paths(repo_root: Path) -> None:
    import wagents

    wagents.ROOT = repo_root
    wagents.DOCS_DIR = repo_root / "docs"
    wagents.CONTENT_DIR = wagents.DOCS_DIR / "src" / "content" / "docs"


def detect_install_mode() -> str:
    """Classify how the active wagents binary was launched."""
    executable = Path(sys.argv[0]).resolve()
    exe_name = executable.name
    if exe_name == "python" or exe_name.startswith("python"):
        return "uv-run"
    exe_str = str(executable)
    if "uv/tools" in exe_str or "/.local/bin/" in exe_str or exe_str.endswith("/uv"):
        return "uv-tool"
    if "pipx" in exe_str:
        return "pipx"
    if "site-packages" in exe_str:
        return "pip"
    package_parent = _package_install_root()
    if _is_agents_repo(package_parent):
        return "editable"
    return "unknown"


def bootstrap_cli_context(
    repo_root_option: Path | None,
    *,
    cwd: Path | None = None,
) -> CliContext:
    """Initialize CLI context from global options."""
    explicit = repo_root_option is not None
    if explicit:
        resolved = resolve_repo_root(explicit=repo_root_option, cwd=cwd)
    else:
        import wagents

        resolved = (
            wagents.ROOT.resolve()
            if _is_agents_repo(wagents.ROOT)
            else resolve_repo_root(cwd=cwd)
        )
    return set_cli_context(
        repo_root=resolved,
        explicit_repo_root=explicit,
        install_mode=detect_install_mode(),
    )


