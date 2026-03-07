#!/usr/bin/env python3
"""Extract endpoint inventory from an OpenAPI spec.

Output JSON to stdout: {endpoints: [{path, method, tag, auth_required, params_count, response_codes}]}
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


def extract_endpoints(spec: dict) -> list[dict]:
    """Extract endpoint inventory from OpenAPI spec."""
    endpoints = []
    paths = spec.get("paths", {})
    global_security = spec.get("security", [])
    http_methods = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}

    for path_str, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        path_params = path_item.get("parameters", [])

        for method in http_methods:
            operation = path_item.get(method)
            if not operation or not isinstance(operation, dict):
                continue

            tags = operation.get("tags", [])
            tag = tags[0] if tags else "untagged"

            # Determine auth requirement
            op_security = operation.get("security", global_security)
            auth_required = bool(op_security and any(s for s in op_security))

            # Count parameters
            op_params = operation.get("parameters", [])
            all_params = path_params + op_params
            params_count = len(all_params)

            # If requestBody exists, count it
            if operation.get("requestBody"):
                params_count += 1

            # Collect response codes
            responses = operation.get("responses", {})
            response_codes = sorted(str(c) for c in responses.keys())

            endpoints.append({
                "path": path_str,
                "method": method.upper(),
                "tag": tag,
                "auth_required": auth_required,
                "params_count": params_count,
                "response_codes": response_codes,
            })

    # Sort by path then method
    endpoints.sort(key=lambda e: (e["path"], e["method"]))
    return endpoints


def main():
    parser = argparse.ArgumentParser(description="Extract endpoint inventory from OpenAPI spec")
    parser.add_argument("spec_path", help="Path to OpenAPI spec file (YAML or JSON)")
    args = parser.parse_args()

    spec = load_spec(args.spec_path)
    if not spec:
        result = {"endpoints": []}
    else:
        result = {"endpoints": extract_endpoints(spec)}

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
