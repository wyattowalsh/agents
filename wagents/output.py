"""Shared structured output helpers for wagents commands."""

from __future__ import annotations

import json
from typing import Any

import typer

OUTPUT_FORMATS = ("text", "json", "jsonl")


def normalize_output_format(format_: str) -> str:
    """Normalize and validate a requested output format."""
    normalized = format_.lower()
    if normalized not in OUTPUT_FORMATS:
        typer.echo(
            f"Error: unsupported format '{format_}'. Use one of: {', '.join(OUTPUT_FORMATS)}",
            err=True,
        )
        raise typer.Exit(code=1)
    return normalized


def emit_structured_output(
    format_: str,
    *,
    text_lines: list[str] | None = None,
    json_data: dict[str, Any] | list[Any] | None = None,
    jsonl_records: list[dict[str, Any]] | None = None,
) -> None:
    """Emit command output in text, json, or jsonl format."""
    normalized = normalize_output_format(format_)
    if normalized == "text":
        for line in text_lines or []:
            typer.echo(line)
        return
    if normalized == "json":
        typer.echo(json.dumps(json_data, indent=2))
        return
    for record in jsonl_records or []:
        typer.echo(json.dumps(record))