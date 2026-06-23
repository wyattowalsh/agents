"""Example wagents command plugin (not registered by default)."""

from __future__ import annotations

import typer

example_app = typer.Typer(help="Example plugin commands", hidden=True)


@example_app.command("ping")
def example_ping() -> None:
    """No-op example used by plugin loader tests."""
    typer.echo("pong")


def register_commands(app: typer.Typer) -> None:
    app.add_typer(example_app, name="example-plugin")
