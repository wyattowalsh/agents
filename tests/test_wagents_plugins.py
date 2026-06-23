"""Tests for wagents plugin loading."""

import typer

from wagents.plugins._example import example_app, register_commands


def test_example_plugin_registers_commands():
    app = typer.Typer()
    register_commands(app)
    command_names = {command.name for command in example_app.registered_commands}
    assert "ping" in command_names
