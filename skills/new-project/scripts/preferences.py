#!/usr/bin/env python3
"""Preference catalog helper for the new-project skill."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def capabilities() -> list[dict]:
    return load_json(DATA_DIR / "capabilities.json").get("capabilities", [])


def presets() -> list[dict]:
    return load_json(DATA_DIR / "presets.json").get("presets", [])


def list_preferences() -> dict:
    grouped: dict[str, list[dict]] = {}
    for capability in capabilities():
        grouped.setdefault(capability["category"], []).append(
            {"id": capability["id"], "label": capability["label"], "risk_level": capability["risk_level"]}
        )
    return {"ok": True, "categories": grouped}


def resolve_preset(preset_id: str) -> dict:
    capability_by_id = {capability["id"]: capability for capability in capabilities()}
    preset_by_id = {preset["id"]: preset for preset in presets()}
    if preset_id not in preset_by_id:
        return {"ok": False, "errors": [f"unknown preset: {preset_id}"]}

    preset = preset_by_id[preset_id]
    selected_ids = list(dict.fromkeys(preset.get("capabilities", []) + preset.get("optional_capabilities", [])))
    selected = [capability_by_id[item] for item in selected_ids if item in capability_by_id]
    missing = [item for item in selected_ids if item not in capability_by_id]
    return {"ok": not missing, "preset": preset, "capabilities": selected, "missing": missing}


def explain_add(capability_id: str) -> dict:
    return {
        "ok": True,
        "id": capability_id,
        "steps": [
            "Add a stable dotted capability id to data/capabilities.json.",
            "Add dependencies, conflicts, implied capabilities, risk level, commands, artifacts, validation, "
            "and docs sources.",
            "Attach the capability to one or more presets in data/presets.json.",
            "Add a reference note only if catalog metadata is not enough.",
            "Add or update evals for routing, conflict, and safety behavior.",
            "Run validate_catalog.py, preferences.py validate, wagents eval validate, and the skill audit.",
        ],
    }


def validate() -> dict:
    script = BASE_DIR / "scripts" / "validate_catalog.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--format", "json"],
        check=False,
        text=True,
        capture_output=True,
    )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        result = {"ok": False, "errors": ["validate_catalog.py did not emit JSON"], "stderr": completed.stderr}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect and validate new-project preferences.")
    parser.add_argument(
        "command", choices=["list", "validate", "resolve", "merge", "explain-add"], nargs="?", default="list"
    )
    parser.add_argument("value", nargs="?", help="Preset or capability id")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()

    if args.command == "list":
        result = list_preferences()
    elif args.command == "validate":
        result = validate()
    elif args.command == "resolve":
        result = resolve_preset(args.value or "recommended")
    elif args.command == "merge":
        result = {"ok": False, "errors": ["merge is reserved for future project-local preference files"]}
    else:
        result = explain_add(args.value or "category.example")

    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("ok" if result.get("ok") else "failed")
        for error in result.get("errors", []):
            print(f"error: {error}", file=sys.stderr)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
