"""Self-management commands for globally installed wagents."""

from __future__ import annotations

import shutil
import subprocess
import sys

import typer

from wagents import VERSION
from wagents.context import (
    DEFAULT_GIT_SOURCE,
    REPO_ROOT_ENV,
    bootstrap_cli_context,
    detect_install_mode,
    get_repo_root_optional,
)
from wagents.output import emit_structured_output

self_app = typer.Typer(help="Install, upgrade, and diagnose the wagents CLI itself")
GIT_SOURCE = DEFAULT_GIT_SOURCE


def _require_uv() -> None:
    if shutil.which("uv") is None:
        typer.echo("Error: uv is required. Install from https://docs.astral.sh/uv/", err=True)
        raise typer.Exit(code=2)


def _run_command(cmd: list[str], *, dry_run: bool, echo_dry_run: bool = True) -> int:
    if dry_run:
        if echo_dry_run:
            typer.echo(f"Would run: {' '.join(cmd)}")
        return 0
    result = subprocess.run(cmd, check=False)
    return result.returncode


def _finish_self_command(
    *,
    record_type: str,
    cmd: list[str],
    dry_run: bool,
    format_: str,
) -> None:
    code = _run_command(cmd, dry_run=dry_run, echo_dry_run=False)
    payload = {"command": cmd, "dry_run": dry_run, "exit_code": code}
    text_lines = [f"Would run: {' '.join(cmd)}", f"exit={code}"] if dry_run else [f"exit={code}"]
    emit_structured_output(
        format_,
        text_lines=text_lines,
        json_data=payload,
        jsonl_records=[{"type": record_type, **payload}],
    )
    raise typer.Exit(code=code)


def _resolve_install_source(*, source: str | None, local: bool) -> str:
    if local:
        bootstrap_cli_context(None)
        repo_root = get_repo_root_optional()
        if repo_root is None:
            typer.echo(
                f"Error: --local requires an agents repository. Run inside the clone or set {REPO_ROOT_ENV}.",
                err=True,
            )
            raise typer.Exit(code=2)
        return str(repo_root)
    return source or GIT_SOURCE


@self_app.command("install")
def self_install(
    source: str | None = typer.Option(None, "--from", help="uv tool install source spec (default: Git remote)"),
    local: bool = typer.Option(
        False,
        "--local",
        help="Install from the discovered agents repository (maintainer workflow)",
    ),
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="Print or execute install"),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
) -> None:
    """Install wagents globally with uv tool install."""
    _require_uv()
    resolved_source = _resolve_install_source(source=source, local=local)
    _finish_self_command(
        record_type="self-install",
        cmd=["uv", "tool", "install", "wagents", "--from", resolved_source, "--force"],
        dry_run=dry_run,
        format_=format_,
    )


@self_app.command("upgrade")
def self_upgrade(
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="Print or execute upgrade"),
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
) -> None:
    """Upgrade the globally installed wagents binary."""
    _require_uv()
    _finish_self_command(
        record_type="self-upgrade",
        cmd=["uv", "tool", "upgrade", "wagents"],
        dry_run=dry_run,
        format_=format_,
    )


def _apm_self_doctor_checks(repo_root) -> list[dict[str, str]]:
    """Non-fatal APM CLI + repo surface rows for wagents self doctor."""
    rows: list[dict[str, str]] = []
    apm_path = shutil.which("apm")
    if apm_path:
        try:
            proc = subprocess.run(
                ["apm", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            raw = (proc.stdout or proc.stderr).strip()
            version_line = raw.splitlines()[0] if raw else "unknown"
        except (OSError, subprocess.TimeoutExpired):
            version_line = "unknown"
        rows.append({
            "name": "apm-cli",
            "status": "ok",
            "summary": f"{apm_path} — {version_line}",
        })
    else:
        rows.append({
            "name": "apm-cli",
            "status": "warn",
            "summary": "apm not on PATH; install with: pip install apm-cli (or pipx install apm-cli)",
        })

    if repo_root is not None and (repo_root / "apm.yml").exists():
        from wagents.apm import doctor as apm_surface_doctor

        surface = apm_surface_doctor(repo_root)
        rows.append({
            "name": "apm-surface",
            "status": "ok" if surface.get("ok") else "warn",
            "summary": "apm.yml + .apm/ OK"
            if surface.get("ok")
            else ("apm surface drift; run: uv run wagents apm materialize && uv run wagents apm doctor (hard gate)"),
        })
    return rows


@self_app.command("doctor")
def self_doctor(
    format_: str = typer.Option("text", "--format", help="Output format: text, json, jsonl"),
) -> None:
    """Report wagents install mode, PATH presence, and repo discovery."""
    bootstrap_cli_context(None)
    wagents_path = shutil.which("wagents")
    repo_root = get_repo_root_optional()
    checks = [
        {
            "name": "wagents-binary",
            "status": "ok" if wagents_path else "warn",
            "summary": f"Found at {wagents_path}" if wagents_path else "wagents is not on PATH",
        },
        {
            "name": "install-mode",
            "status": "ok",
            "summary": detect_install_mode(),
        },
        {
            "name": "python-executable",
            "status": "ok",
            "summary": sys.executable,
        },
        {
            "name": "wagents-version",
            "status": "ok",
            "summary": VERSION,
        },
        {
            "name": "repo-discovery",
            "status": "ok" if repo_root else "warn",
            "summary": str(repo_root) if repo_root else f"No repo found; set {REPO_ROOT_ENV} or run inside clone",
        },
    ]
    checks.extend(_apm_self_doctor_checks(repo_root))
    emit_structured_output(
        format_,
        text_lines=[f"{item['name']}: {item['status']} — {item['summary']}" for item in checks],
        json_data={"checks": checks},
        jsonl_records=[{"type": "self-doctor-check", **item} for item in checks],
    )


@self_app.command("completion")
def self_completion(
    shell: str = typer.Option("zsh", "--shell", help="Shell name for Typer completion install"),
) -> None:
    """Print instructions for enabling shell completion."""
    typer.echo(f"Run: wagents --install-completion {shell}")
    typer.echo("For local development, prefer: wagents self install --local --apply")
