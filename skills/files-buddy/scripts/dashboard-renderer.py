#!/usr/bin/env python3
"""Inject JSON data into the dashboard HTML template and optionally open it."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path


def get_agent_dir(skill_name: str) -> Path:
    """Get the base directory for a skill based on the active agent."""
    agent = os.environ.get("AGENT_NAME", "").lower()
    for cli, folder in [("GEMINI_CLI", ".gemini"), ("COPILOT_CLI", ".copilot"), ("CODEX_CLI", ".codex")]:
        if os.environ.get(cli) == "1" or folder.strip(".") in agent:
            return Path.home() / folder / skill_name
    return Path.home() / ".claude" / skill_name



def error_exit(msg: str) -> None:
    """Print an error JSON object and exit with code 1."""
    print(json.dumps({"error": msg}))
    sys.exit(1)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a files-buddy dashboard")
    parser.add_argument(
        "--data",
        required=True,
        help='Path to JSON file, or "-" for stdin',
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output HTML path (default: ~/.claude/files-buddy/{date}-dashboard.html)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        dest="open_browser",
        help="Open the rendered dashboard in the default browser",
    )
    parser.add_argument(
        "--template",
        default=None,
        help="Path to the HTML template (default: ../templates/dashboard.html)",
    )
    parser.add_argument(
        "--progress",
        default=None,
        help="Optional progress JSON path to embed for live-refresh dashboards",
    )
    return parser.parse_args(argv)


def resolve_template(template_arg: str | None) -> Path:
    if template_arg:
        return Path(template_arg)
    return Path(__file__).resolve().parent.parent / "templates" / "dashboard.html"


def resolve_output(output_arg: str | None) -> Path:
    if output_arg:
        return Path(output_arg)
    today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
    return get_agent_dir("files-buddy") / f"{today}-dashboard.html"


def render_data_script(data: object) -> str:
    """Encode JSON safely for embedding inside a script tag."""
    safe_json = (
        json.dumps(data)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    return f'<script id="data" type="application/json">{safe_json}</script>'


def render_progress_script(progress_path: str | None) -> str:
    payload = {"progress_path": str(Path(progress_path).expanduser())} if progress_path else {}
    safe_json = json.dumps(payload).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    return f'<script id="progress-config" type="application/json">{safe_json}</script>'


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    # --- template ---
    template_path = resolve_template(args.template)
    if not template_path.is_file():
        error_exit(f"Template not found: {template_path}")
    template_html = template_path.read_text(encoding="utf-8")

    # --- data ---
    if args.data == "-":
        raw = sys.stdin.read()
    else:
        data_path = Path(args.data)
        if not data_path.is_file():
            error_exit(f"Data file not found: {data_path}")
        raw = data_path.read_text(encoding="utf-8")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        error_exit(f"Invalid JSON: {exc}")

    # --- render ---
    placeholder = '<script id="data" type="application/json">{}</script>'
    if placeholder not in template_html:
        error_exit("Template missing dashboard data placeholder")
    rendered = template_html.replace(
        placeholder,
        render_data_script(data),
    )
    progress_placeholder = '<script id="progress-config" type="application/json">{}</script>'
    if progress_placeholder in rendered:
        rendered = rendered.replace(progress_placeholder, render_progress_script(args.progress))

    # --- write ---
    output_path = resolve_output(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")

    # --- open ---
    opened = False
    if args.open_browser:
        import subprocess  # noqa: PLC0415

        cmd = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.run([cmd, str(output_path)], check=False)  # noqa: S603
        opened = True

    print(json.dumps({"output": str(output_path), "opened": opened}))


if __name__ == "__main__":
    main()
