#!/usr/bin/env python3
"""Typer CLI for the prospector dashboard server."""

from __future__ import annotations

import os
import signal
from pathlib import Path

import typer

from .db import DB_PATH, PID_PATH, init_db

app = typer.Typer(help="Prospector dashboard server management")


@app.command()
def serve(
    port: int = typer.Option(8765, min=1024, max=65535, help="Port to listen on"),
    db: str = typer.Option(str(DB_PATH), help="Path to SQLite database"),
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
) -> None:
    """Start the prospector dashboard server."""
    db_path = Path(db)
    if not db_path.exists():
        typer.echo(f"Database not found at {db_path}, initializing...")
        init_db(db_path)

    # Write PID file
    PID_PATH.parent.mkdir(parents=True, exist_ok=True)
    PID_PATH.write_text(str(os.getpid()))

    typer.echo(f"Starting Prospector Dashboard on http://{host}:{port}")
    typer.echo(f"Database: {db_path}")

    try:
        import uvicorn

        from .api import create_app

        api_app = create_app(db)
        uvicorn.run(api_app, host=host, port=port)
    except KeyboardInterrupt:
        pass
    finally:
        if PID_PATH.exists():
            PID_PATH.unlink(missing_ok=True)


@app.command()
def stop() -> None:
    """Stop the running prospector dashboard server."""
    if not PID_PATH.exists():
        typer.echo("No running server found (no PID file).")
        raise typer.Exit(1)

    pid = int(PID_PATH.read_text().strip())
    try:
        os.kill(pid, signal.SIGTERM)
        typer.echo(f"Sent SIGTERM to process {pid}.")
    except ProcessLookupError:
        typer.echo(f"Process {pid} not found (already stopped).")
    finally:
        PID_PATH.unlink(missing_ok=True)


@app.command()
def status() -> None:
    """Check if the prospector dashboard server is running."""
    if not PID_PATH.exists():
        typer.echo("Server is not running (no PID file).")
        raise typer.Exit(1)

    pid = int(PID_PATH.read_text().strip())
    try:
        os.kill(pid, 0)
        typer.echo(f"Server is running (PID {pid}).")
    except ProcessLookupError:
        typer.echo(f"Server is not running (stale PID file for {pid}).")
        PID_PATH.unlink(missing_ok=True)
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
