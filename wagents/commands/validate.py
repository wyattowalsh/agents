"""Validate command registration."""

from __future__ import annotations

import subprocess
import sys

import typer

from wagents import KEBAB_CASE_PATTERN
from wagents.context import get_repo_root, resolve_repo_script


def validate_name(name: str) -> None:
    """Validate asset name is kebab-case and within length limit."""
    if not KEBAB_CASE_PATTERN.match(name):
        typer.echo(f"Error: name must be kebab-case (got '{name}')", err=True)
        raise typer.Exit(code=1)
    if len(name) > 64:
        typer.echo("Error: name exceeds 64 characters", err=True)
        raise typer.Exit(code=1)


def _run_python_script(script, args: list[str]) -> int:
    repo_root = get_repo_root()
    result = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=repo_root,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        sys.stdout.write(result.stdout)
        if not result.stdout.endswith("\n"):
            sys.stdout.write("\n")
    if result.stderr:
        sys.stderr.write(result.stderr)
        if not result.stderr.endswith("\n"):
            sys.stderr.write("\n")
    return result.returncode


def register_validate_commands(app: typer.Typer) -> None:
    """Register the validate command on *app*."""

    @app.command()
    def validate(
        format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
    ):
        """Validate all skills and agents."""
        script = resolve_repo_script("scripts/validate/validate_repo.py")
        raise typer.Exit(
            code=_run_python_script(
                script,
                ["--format", format_, "--repo-root", str(get_repo_root())],
            )
        )
