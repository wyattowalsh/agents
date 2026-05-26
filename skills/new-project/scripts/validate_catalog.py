#!/usr/bin/env python3
"""Validate the new-project capability and preset catalogs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from catalog_utils import capability_index, detect_conflicts, load_data, resolve_capabilities

try:
    from jsonschema import ValidationError
    from jsonschema import validate as validate_schema
except ImportError:  # pragma: no cover - surfaced as a validation error at runtime.
    ValidationError = None
    validate_schema = None

BASE_DIR = Path(__file__).resolve().parents[1]


def validate_document_schema(document_name: str, schema_name: str) -> list[str]:
    if validate_schema is None or ValidationError is None:
        return ["jsonschema is required for catalog schema validation"]
    try:
        validate_schema(load_data(document_name), load_data(schema_name))
    except ValidationError as error:
        path = ".".join(str(part) for part in error.absolute_path)
        location = f" at {path}" if path else ""
        return [f"{document_name}{location}: {error.message}"]
    return []


def validate_catalog() -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(validate_document_schema("capabilities.json", "capabilities.schema.json"))
    errors.extend(validate_document_schema("presets.json", "presets.schema.json"))

    capabilities_doc = load_data("capabilities.json")
    presets_doc = load_data("presets.json")

    capabilities = capabilities_doc.get("capabilities", [])
    presets = presets_doc.get("presets", [])
    capabilities_by_id = capability_index()

    capability_ids: set[str] = set()
    for capability in capabilities:
        capability_id = capability.get("id", "<unknown>")
        if capability_id in capability_ids:
            errors.append(f"duplicate capability id: {capability_id}")
        capability_ids.add(capability_id)

        if capability.get("risk_level") not in {"low", "medium", "high"}:
            errors.append(f"capability {capability_id} has invalid risk_level")
        if not capability.get("validation"):
            errors.append(f"capability {capability_id} must include at least one validation check")
        if capability.get("external_side_effects") and capability.get("risk_level") != "high":
            warnings.append(f"capability {capability_id} has external side effects but is not high risk")

    for capability in capabilities:
        capability_id = capability.get("id", "<unknown>")
        for field in ("requires", "implies", "conflicts"):
            for referenced_id in capability.get(field, []):
                if referenced_id not in capability_ids:
                    errors.append(f"capability {capability_id} references missing {field} id: {referenced_id}")

    preset_ids: set[str] = set()
    for preset in presets:
        preset_id = preset.get("id", "<unknown>")
        if preset_id in preset_ids:
            errors.append(f"duplicate preset id: {preset_id}")
        preset_ids.add(preset_id)

        selected = set(preset.get("capabilities", [])) | set(preset.get("optional_capabilities", []))
        for capability_id in selected:
            if capability_id not in capability_ids:
                errors.append(f"preset {preset_id} references missing capability: {capability_id}")

        default_resolution = resolve_capabilities(preset.get("capabilities", []), capabilities=capabilities_by_id)
        if not default_resolution["ok"]:
            for error in default_resolution["errors"]:
                errors.append(f"preset {preset_id}: {error}")

        optional_conflicts = detect_conflicts(list(selected), capabilities_by_id)
        if optional_conflicts:
            warnings.extend(
                f"preset {preset_id} optional set contains conflict: {', '.join(conflict['capabilities'])}"
                for conflict in optional_conflicts
            )

    references = (
        [path.name for path in (BASE_DIR / "references").glob("*.md")] if (BASE_DIR / "references").exists() else []
    )
    if not references:
        warnings.append("no reference files found yet")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "capability_count": len(capabilities),
        "preset_count": len(presets),
        "reference_count": len(references),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate new-project catalog data.")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()

    result = validate_catalog()
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("ok" if result["ok"] else "failed")
        for error in result["errors"]:
            print(f"error: {error}", file=sys.stderr)
        for warning in result["warnings"]:
            print(f"warning: {warning}", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
