#!/usr/bin/env python3
"""Compare two OpenAPI specs for breaking changes.

Output JSON to stdout: {breaking: [{path, method, change_type, description}], non_breaking: [...], summary}
Warnings to stderr.
"""

import argparse
import json
import sys
from pathlib import Path


def load_spec(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"Warning: File not found: {path}", file=sys.stderr)
        return {}
    text = p.read_text(encoding="utf-8")
    if p.suffix in (".yaml", ".yml"):
        try:
            import yaml
            return yaml.safe_load(text) or {}
        except ImportError:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                print("Warning: Cannot parse YAML without PyYAML", file=sys.stderr)
                return {}
    else:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {path}", file=sys.stderr)
            return {}


def compare_specs(old: dict, new: dict) -> dict:
    """Compare two OpenAPI specs and classify changes."""
    breaking = []
    non_breaking = []

    old_paths = old.get("paths", {})
    new_paths = new.get("paths", {})
    http_methods = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}

    # Removed paths
    for path_str in old_paths:
        if path_str not in new_paths:
            # Check all methods in the removed path
            path_item = old_paths[path_str]
            if isinstance(path_item, dict):
                for method in http_methods:
                    if path_item.get(method):
                        breaking.append({
                            "path": path_str,
                            "method": method.upper(),
                            "change_type": "endpoint-removed",
                            "description": f"Endpoint {method.upper()} {path_str} was removed",
                        })

    # Added paths
    for path_str in new_paths:
        if path_str not in old_paths:
            path_item = new_paths[path_str]
            if isinstance(path_item, dict):
                for method in http_methods:
                    if path_item.get(method):
                        non_breaking.append({
                            "path": path_str,
                            "method": method.upper(),
                            "change_type": "endpoint-added",
                            "description": f"New endpoint {method.upper()} {path_str}",
                        })

    # Changed paths
    for path_str in old_paths:
        if path_str not in new_paths:
            continue

        old_item = old_paths[path_str]
        new_item = new_paths[path_str]
        if not isinstance(old_item, dict) or not isinstance(new_item, dict):
            continue

        for method in http_methods:
            old_op = old_item.get(method)
            new_op = new_item.get(method)

            if old_op and not new_op:
                breaking.append({
                    "path": path_str,
                    "method": method.upper(),
                    "change_type": "method-removed",
                    "description": f"Method {method.upper()} removed from {path_str}",
                })
                continue

            if not old_op and new_op:
                non_breaking.append({
                    "path": path_str,
                    "method": method.upper(),
                    "change_type": "method-added",
                    "description": f"Method {method.upper()} added to {path_str}",
                })
                continue

            if not old_op or not new_op:
                continue

            if not isinstance(old_op, dict) or not isinstance(new_op, dict):
                continue

            # Check parameters
            old_params = {
                (p.get("name"), p.get("in")): p
                for p in old_op.get("parameters", [])
                if isinstance(p, dict)
            }
            new_params = {
                (p.get("name"), p.get("in")): p
                for p in new_op.get("parameters", [])
                if isinstance(p, dict)
            }

            # Removed parameters
            for key in old_params:
                if key not in new_params:
                    param = old_params[key]
                    name = key[0]
                    location = key[1]
                    if param.get("required"):
                        breaking.append({
                            "path": path_str,
                            "method": method.upper(),
                            "change_type": "required-param-removed",
                            "description": f"Required parameter '{name}' (in {location}) removed",
                            "severity": "high",
                        })
                    else:
                        non_breaking.append({
                            "path": path_str,
                            "method": method.upper(),
                            "change_type": "optional-param-removed",
                            "description": f"Optional parameter '{key[0]}' in {key[1]} removed",
                        })

            # Added required parameters
            for key in new_params:
                if key not in old_params:
                    param = new_params[key]
                    if param.get("required"):
                        breaking.append({
                            "path": path_str,
                            "method": method.upper(),
                            "change_type": "required-param-added",
                            "description": f"New required parameter '{key[0]}' in {key[1]}",
                        })
                    else:
                        non_breaking.append({
                            "path": path_str,
                            "method": method.upper(),
                            "change_type": "optional-param-added",
                            "description": f"New optional parameter '{key[0]}' in {key[1]}",
                        })

            # Parameter made required
            for key in old_params:
                if key in new_params:
                    was_required = old_params[key].get("required", False)
                    is_required = new_params[key].get("required", False)
                    if not was_required and is_required:
                        breaking.append({
                            "path": path_str,
                            "method": method.upper(),
                            "change_type": "param-made-required",
                            "description": f"Parameter '{key[0]}' in {key[1]} changed from optional to required",
                        })

            # Check response codes removed
            old_responses = set(str(c) for c in old_op.get("responses", {}).keys())
            new_responses = set(str(c) for c in new_op.get("responses", {}).keys())

            for code in old_responses - new_responses:
                if code.startswith("2"):
                    breaking.append({
                        "path": path_str,
                        "method": method.upper(),
                        "change_type": "success-response-removed",
                        "description": f"Success response {code} removed",
                    })
                else:
                    non_breaking.append({
                        "path": path_str,
                        "method": method.upper(),
                        "change_type": "error-response-removed",
                        "description": f"Error response {code} removed",
                    })

            for code in new_responses - old_responses:
                non_breaking.append({
                    "path": path_str,
                    "method": method.upper(),
                    "change_type": "response-added",
                    "description": f"New response {code} added",
                })

    # Summary
    summary = {
        "breaking_count": len(breaking),
        "non_breaking_count": len(non_breaking),
        "old_paths_count": len(old_paths),
        "new_paths_count": len(new_paths),
        "verdict": "BREAKING" if breaking else "COMPATIBLE",
    }

    return {
        "breaking": breaking,
        "non_breaking": non_breaking,
        "summary": summary,
    }


def main():
    parser = argparse.ArgumentParser(description="Compare two OpenAPI specs for breaking changes")
    parser.add_argument("old_spec", help="Path to old OpenAPI spec")
    parser.add_argument("new_spec", help="Path to new OpenAPI spec")
    args = parser.parse_args()

    old = load_spec(args.old_spec)
    new = load_spec(args.new_spec)

    if not old:
        print(f"Warning: Could not load old spec: {args.old_spec}", file=sys.stderr)
    if not new:
        print(f"Warning: Could not load new spec: {args.new_spec}", file=sys.stderr)

    result = compare_specs(old, new)
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
