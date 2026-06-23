"""Plugin contracts for extending wagents."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import typer


class CommandPlugin(Protocol):
    """Register additional Typer commands on the root app."""

    def register_commands(self, app: typer.Typer) -> None: ...


RegisterCommands = Callable[["typer.Typer"], None]
