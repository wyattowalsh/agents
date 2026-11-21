#!/usr/bin/env python3
"""Validate a report and render a self-contained, explicitly refreshed dashboard."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from contextlib import suppress
from pathlib import Path

from files_buddy_report import MAX_REPORT_BYTES, ReportError, load_report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help='JSON report path, or "-" for stdin')
    parser.add_argument("--output", help="New HTML path; an existing file is never overwritten")
    parser.add_argument(
        "--open", action="store_true", dest="open_browser", help="Open the completed report in a browser"
    )
    parser.add_argument("--template", help="Use an explicitly trusted local template")
    parser.add_argument("--progress", help="Progress JSON path to display for explicit file import; it is not polled")
    return parser.parse_args(argv)


def render_script(identifier: str, data: object) -> str:
    """Encode JSON without allowing data to terminate its script element."""
    encoded = json.dumps(data, ensure_ascii=True, allow_nan=False)
    encoded = encoded.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    return f'<script id="{identifier}" type="application/json">{encoded}</script>'


def render_data_script(data: object) -> str:
    return render_script("data", data)


def render_progress_script(progress_path: str | None) -> str:
    return render_script(
        "progress-config", {"progress_path": str(Path(progress_path).expanduser()) if progress_path else None}
    )


def create_output(output: Path, *, default_output: bool) -> int:
    """Create a private new report, pinning default state directories without symlinks."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    if not default_output:
        # An explicit destination is caller-selected; its existing target is never overwritten.
        output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        return os.open(output, flags, 0o600)
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory_fd = os.open(Path.home().resolve(strict=True), directory_flags)
    try:
        for part in (".files-buddy", "runs", output.parent.name):
            with suppress(FileExistsError):
                os.mkdir(part, mode=0o700, dir_fd=directory_fd)
            child_fd = os.open(part, directory_flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = child_fd
            if os.fstat(directory_fd).st_uid != os.getuid():
                raise ReportError("Default report directories must belong to the current user")
        return os.open(output.name, flags, 0o600, dir_fd=directory_fd)
    finally:
        os.close(directory_fd)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.data == "-":
            raw = sys.stdin.read(MAX_REPORT_BYTES + 1)
        else:
            with Path(args.data).expanduser().open(encoding="utf-8") as handle:
                raw = handle.read(MAX_REPORT_BYTES + 1)
        data = load_report(raw)
        template_path = (
            Path(args.template).expanduser()
            if args.template
            else Path(__file__).resolve().parent.parent / "templates" / "dashboard.html"
        )
        template = template_path.read_text(encoding="utf-8")
        replacements = {
            '<script id="data" type="application/json">{}</script>': render_data_script(data),
            '<script id="progress-config" type="application/json">{}</script>': render_progress_script(args.progress),
            '<script id="report-schema" type="application/json">{}</script>': render_script(
                "report-schema",
                json.loads(
                    (Path(__file__).resolve().parent.parent / "assets" / "report.schema.json").read_text(
                        encoding="utf-8"
                    )
                ),
            ),
        }
        for placeholder, replacement in replacements.items():
            if template.count(placeholder) != 1:
                raise ReportError(
                    "Template must contain exactly one data, progress-config and report-schema placeholder"
                )
            template = template.replace(placeholder, replacement)
        output = (
            Path(args.output).expanduser()
            if args.output
            else Path.home() / ".files-buddy" / "runs" / data["run_id"] / f"dashboard-{uuid.uuid4().hex}.html"
        )
        output = output.absolute()
        descriptor = create_output(output, default_output=args.output is None)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(template)
            handle.flush()
            os.fsync(handle.fileno())
        opened = False
        if args.open_browser:
            import webbrowser

            opened = webbrowser.open(output.as_uri())
        print(
            json.dumps(
                {
                    "output": str(output),
                    "run_id": data["run_id"],
                    "source_digest": data["source_digest"],
                    "opened": opened,
                    "refresh": "explicit-file-import",
                }
            )
        )
        return 0
    except (OSError, UnicodeError, ReportError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
