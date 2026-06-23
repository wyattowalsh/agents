"""Collect MCP layout validation errors."""

from __future__ import annotations

from _mcp_local import is_local_mcp_dir
from _toolkit import ensure_validate_importable

ensure_validate_importable()

from typing import TYPE_CHECKING

from asset_toolkit.common import KEBAB_CASE_PATTERN

if TYPE_CHECKING:
    from pathlib import Path


def collect_mcp_errors(repo_root: Path) -> list[dict[str, str]]:
    """Collect MCP layout validation errors."""
    errors: list[dict[str, str]] = []

    def add_error(source: str, message: str) -> None:
        errors.append({"source": source, "message": message})

    mcp_dir = repo_root / "mcp"
    if not mcp_dir.is_dir():
        return errors

    for mcp_subdir in mcp_dir.iterdir():
        if not mcp_subdir.is_dir():
            continue
        if is_local_mcp_dir(mcp_subdir, repo_root):
            continue
        dir_name = mcp_subdir.name
        if not KEBAB_CASE_PATTERN.match(dir_name):
            add_error(f"mcp/{dir_name}", "directory name must be kebab-case")
        package_json = mcp_subdir / "package.json"
        if package_json.exists():
            continue
        server_py = mcp_subdir / "server.py"
        if not server_py.exists():
            add_error(f"mcp/{dir_name}", "missing server.py")
        else:
            server_text = server_py.read_text(encoding="utf-8")
            if "FastMCP" not in server_text:
                add_error(f"mcp/{dir_name}", "server.py does not reference FastMCP")
        pyproject = mcp_subdir / "pyproject.toml"
        if not pyproject.exists():
            add_error(f"mcp/{dir_name}", "missing pyproject.toml")
        else:
            pyproject_text = pyproject.read_text(encoding="utf-8")
            if "fastmcp" not in pyproject_text:
                add_error(f"mcp/{dir_name}", "pyproject.toml missing fastmcp dependency")
        fastmcp_json = mcp_subdir / "fastmcp.json"
        if not fastmcp_json.exists():
            add_error(f"mcp/{dir_name}", "missing fastmcp.json")

    return errors


def collect_mcp_validation_errors(repo_root: Path) -> list[dict[str, str]]:
    """Return MCP validation errors for the repository."""
    return collect_mcp_errors(repo_root)
