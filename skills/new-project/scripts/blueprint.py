#!/usr/bin/env python3
"""Build a safe project setup blueprint from catalog presets."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from catalog_utils import (
    capability_index,
    classify_command,
    preset_index,
    required_approvals_for_commands,
    resolve_capabilities,
)

BASE_DIR = Path(__file__).resolve().parents[1]


def preflight(path: Path) -> dict:
    script = BASE_DIR / "scripts" / "preflight.py"
    result = subprocess.run(
        [sys.executable, str(script), "--path", str(path), "--format", "json"],
        check=False,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def build_blueprint(target: Path, preset_id: str, with_ids: list[str], without_ids: list[str]) -> dict:
    capabilities = capability_index()
    presets = preset_index()
    if preset_id not in presets:
        return {"ok": False, "errors": [f"unknown preset: {preset_id}"]}

    preset = presets[preset_id]
    requested_ids = list(dict.fromkeys(preset.get("capabilities", []) + with_ids))
    resolution = resolve_capabilities(requested_ids, without_ids, capabilities)
    selected_ids = resolution["capabilities"]
    selected = [capabilities[item] for item in selected_ids if item in capabilities]
    missing = [item for item in selected_ids if item not in capabilities]
    commands = [command for item in selected for command in item.get("commands", [])]
    approval_required = set(required_approvals_for_commands(commands))
    for item in selected:
        if item.get("mutates_files"):
            approval_required.add("mutate-files")
        if item.get("runs_install"):
            approval_required.add("package-install")
        if item.get("external_side_effects"):
            approval_required.add("external-side-effect")
    validation = [check for item in selected for check in item.get("validation", [])]
    artifacts = [artifact for item in selected for artifact in item.get("artifacts", [])]
    external = [item["id"] for item in selected if item.get("external_side_effects")]
    risks = [item["id"] for item in selected if item.get("risk_level") == "high"]
    command_categories = {command: classify_command(command) for command in commands}
    command_errors = [
        f"blocked command in blueprint: {command}"
        for command, categories in command_categories.items()
        if "blocked_destructive" in categories or "secret_read" in categories
    ]
    errors = list(dict.fromkeys(resolution["errors"] + missing + command_errors))

    return {
        "ok": not errors,
        "errors": errors,
        "mode": "plan",
        "target": str(target),
        "preset": preset_id,
        "capabilities": selected_ids,
        "requested_capabilities": resolution["requested_capabilities"],
        "auto_added_capabilities": resolution["auto_added_capabilities"],
        "capability_reasons": resolution["reasons"],
        "conflicts": resolution["conflicts"],
        "missing_capabilities": missing,
        "files_to_create": sorted(set(artifacts)),
        "commands_to_run": commands,
        "command_categories": command_categories,
        "approval_required": sorted(approval_required),
        "external_side_effects": external,
        "validation": sorted(set(validation)),
        "risks": sorted(set(risks)),
        "preflight": preflight(target),
    }


def split_ids(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a new-project JSON blueprint.")
    parser.add_argument("--target", default=".", help="Target project path")
    parser.add_argument("--preset", default="recommended", help="Preset id")
    parser.add_argument("--with", dest="with_ids", default="", help="Comma-separated capability ids to add")
    parser.add_argument("--without", dest="without_ids", default="", help="Comma-separated capability ids to remove")
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args()

    result = build_blueprint(
        Path(args.target).resolve(), args.preset, split_ids(args.with_ids), split_ids(args.without_ids)
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
