#!/usr/bin/env python3
"""Validate a new-project blueprint before applying it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from catalog_utils import classify_command

DESTRUCTIVE_MARKERS = ("rm -rf", "git clean", "git reset --hard", "docker compose down -v", "terraform apply")
APPROVAL_BY_CATEGORY = {
    "file_mutation": "mutate-files",
    "package_install": "package-install",
    "external_side_effect": "external-side-effect",
}


def load_plan(path: str | None) -> dict:
    if not path or path == "-":
        return json.load(sys.stdin)
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def validate(plan: dict) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    approvals = set(plan.get("approval_required", []))
    commands = plan.get("commands_to_run", [])
    command_categories = {command: classify_command(command) for command in commands}

    if "preflight" not in plan:
        errors.append("plan must include a preflight summary")
    if plan.get("mode") not in {"plan", "init", "bootstrap", "repair", "docs", "github", "cloud"}:
        warnings.append("plan mode is not one of the canonical apply modes")
    if plan.get("files_to_create") and "mutate-files" not in approvals:
        errors.append("file mutations require mutate-files approval")
    if plan.get("external_side_effects") and "external-side-effect" not in approvals:
        errors.append("external side effects require explicit approval")
    for command in commands:
        lowered = command.lower()
        if any(marker in lowered for marker in DESTRUCTIVE_MARKERS):
            errors.append(f"destructive command is not allowed in blueprint: {command}")
        categories = command_categories[command]
        if "blocked_destructive" in categories:
            errors.append(f"destructive command is not allowed in blueprint: {command}")
        if "secret_read" in categories:
            errors.append(f"secret-like file or token read is not allowed in blueprint: {command}")
        for category, approval in APPROVAL_BY_CATEGORY.items():
            if category in categories and approval not in approvals:
                errors.append(f"{category.replace('_', ' ')} command requires {approval} approval: {command}")

    return {
        "ok": not errors,
        "errors": sorted(set(errors)),
        "warnings": warnings,
        "command_categories": command_categories,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a new-project blueprint JSON document.")
    parser.add_argument("--plan", default="-", help="Path to blueprint JSON, or '-' for stdin")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()

    result = validate(load_plan(args.plan))
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("ok" if result["ok"] else "failed")
        for error in result["errors"]:
            print(f"error: {error}", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
