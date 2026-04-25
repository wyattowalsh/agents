#!/usr/bin/env python3
"""Parse host-panel invocation arguments into a stable JSON contract."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from typing import Any


FORMATS = {"roundtable", "oxford", "socratic"}
DEFAULT_FORMAT = "roundtable"
DEFAULT_COUNT = 4
MIN_COUNT = 2
MAX_COUNT = 6


def _tokens_from_args(raw_args: list[str]) -> tuple[list[str], bool]:
    if not raw_args:
        return [], False
    if len(raw_args) == 1:
        quoted_topic = raw_args[0].lstrip().startswith(("'", '"'))
        try:
            return shlex.split(raw_args[0]), quoted_topic
        except ValueError:
            return raw_args, quoted_topic
    return raw_args, " " in raw_args[0]


def parse(raw_args: list[str]) -> dict[str, Any]:
    tokens, quoted_topic = _tokens_from_args(raw_args)
    errors: list[str] = []
    warnings: list[str] = []

    if not tokens:
        return {
            "topic": "",
            "format": DEFAULT_FORMAT,
            "count": DEFAULT_COUNT,
            "explicit_format": False,
            "explicit_count": False,
            "errors": [],
            "warnings": ["empty arguments"],
        }

    explicit_format = False
    explicit_count = False
    panel_format = DEFAULT_FORMAT
    count = DEFAULT_COUNT

    remaining = list(tokens)

    if remaining and remaining[-1].isdigit():
        explicit_count = True
        count = int(remaining.pop())
        if count < MIN_COUNT or count > MAX_COUNT:
            errors.append(f"expert count must be between {MIN_COUNT} and {MAX_COUNT}")

    format_positions = [index for index, token in enumerate(remaining) if token.lower() in FORMATS]
    if format_positions:
        explicit_format = True
        index = format_positions[-1]
        panel_format = remaining.pop(index).lower()

    trailing_unknowns: list[str] = []
    if quoted_topic and len(remaining) > 1:
        topic = remaining[0].strip()
        trailing_unknowns = remaining[1:]
    else:
        topic = " ".join(remaining).strip()

    if not topic:
        errors.append("topic is required")
    elif not quoted_topic and len(remaining) > 1 and not any(" " in arg for arg in raw_args):
        warnings.append("topic appears unquoted; prefer /host-panel \"topic\" [format] [num-experts]")

    if trailing_unknowns:
        errors.append(f"unsupported format or extra argument: {' '.join(trailing_unknowns)}")

    return {
        "topic": topic,
        "format": panel_format,
        "count": count,
        "explicit_format": explicit_format,
        "explicit_count": explicit_count,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse host-panel arguments as JSON.")
    parser.add_argument("arguments", nargs=argparse.REMAINDER, help="Host-panel arguments")
    args = parser.parse_args()
    json.dump(parse(args.arguments), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
