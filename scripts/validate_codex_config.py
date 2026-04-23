#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tomllib
import urllib.request
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_URL = "https://developers.openai.com/codex/config-schema.json"


def load_schema(schema_path: Path | None) -> dict[str, Any]:
    if schema_path is not None:
        return json.loads(schema_path.read_text(encoding="utf-8"))
    with urllib.request.urlopen(SCHEMA_URL, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def validate_config(path: Path, schema: dict[str, Any]) -> list[str]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda error: list(error.path))
    rendered: list[str] = []
    for error in errors:
        location = ".".join(str(part) for part in error.path) or "<root>"
        rendered.append(f"{path}: {location}: {error.message}")
    return rendered


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Codex config.toml files against the official schema.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--schema", type=Path, help="Use a local schema file instead of fetching the official schema.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    schema = load_schema(args.schema)
    failures: list[str] = []
    for path in args.paths:
        failures.extend(validate_config(path, schema))
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
