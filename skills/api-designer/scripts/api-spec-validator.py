#!/usr/bin/env python3
"""Validate OpenAPI 3.x specs for completeness, consistency, and best practices.

Output JSON to stdout: {spec_version, paths_count, issues: [{path, method, rule, severity, message}]}
Warnings to stderr.
"""

import argparse
import json
import sys
from pathlib import Path


def load_spec(path: str) -> dict:
    """Load an OpenAPI spec from YAML or JSON."""
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
            # Fall back to basic YAML-like parsing for simple specs
            print("Warning: PyYAML not installed, attempting JSON parse", file=sys.stderr)
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


def validate_spec(spec: dict) -> dict:
    """Validate an OpenAPI spec and return results."""
    issues = []
    spec_version = ""
    paths_count = 0

    # Check OpenAPI version
    if "openapi" in spec:
        spec_version = spec["openapi"]
        if not spec_version.startswith("3."):
            issues.append({
                "path": "/",
                "method": "-",
                "rule": "openapi-version",
                "severity": "critical",
                "message": f"Expected OpenAPI 3.x, found {spec_version}",
            })
    elif "swagger" in spec:
        spec_version = f"swagger-{spec['swagger']}"
        issues.append({
            "path": "/",
            "method": "-",
            "rule": "openapi-version",
            "severity": "critical",
            "message": f"Swagger {spec['swagger']} detected. Upgrade to OpenAPI 3.1.",
        })
    else:
        issues.append({
            "path": "/",
            "method": "-",
            "rule": "openapi-version",
            "severity": "critical",
            "message": "No openapi or swagger version field found",
        })

    # Check info object
    info = spec.get("info", {})
    if not info.get("title"):
        issues.append({
            "path": "/info",
            "method": "-",
            "rule": "info-title",
            "severity": "warning",
            "message": "Missing info.title",
        })
    if not info.get("version"):
        issues.append({
            "path": "/info",
            "method": "-",
            "rule": "info-version",
            "severity": "warning",
            "message": "Missing info.version",
        })
    if not info.get("description"):
        issues.append({
            "path": "/info",
            "method": "-",
            "rule": "info-description",
            "severity": "info",
            "message": "Missing info.description",
        })

    # Check paths
    paths = spec.get("paths", {})
    paths_count = len(paths)

    if paths_count == 0:
        issues.append({
            "path": "/paths",
            "method": "-",
            "rule": "paths-not-empty",
            "severity": "critical",
            "message": "No paths defined",
        })

    http_methods = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}

    for path_str, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        # Check path naming conventions
        if path_str != "/" and path_str.endswith("/"):
            issues.append({
                "path": path_str,
                "method": "-",
                "rule": "no-trailing-slash",
                "severity": "warning",
                "message": "Path should not have trailing slash",
            })

        segments = [s for s in path_str.split("/") if s and not s.startswith("{")]
        for seg in segments:
            if seg != seg.lower():
                issues.append({
                    "path": path_str,
                    "method": "-",
                    "rule": "lowercase-paths",
                    "severity": "warning",
                    "message": f"Path segment '{seg}' should be lowercase",
                })
            if "_" in seg:
                issues.append({
                    "path": path_str,
                    "method": "-",
                    "rule": "kebab-case-paths",
                    "severity": "info",
                    "message": f"Path segment '{seg}' uses underscores; prefer hyphens",
                })

        for method in http_methods:
            operation = path_item.get(method)
            if not operation or not isinstance(operation, dict):
                continue

            # Check operationId
            if not operation.get("operationId"):
                issues.append({
                    "path": path_str,
                    "method": method.upper(),
                    "rule": "operation-id",
                    "severity": "warning",
                    "message": "Missing operationId",
                })

            # Check description or summary
            if not operation.get("summary") and not operation.get("description"):
                issues.append({
                    "path": path_str,
                    "method": method.upper(),
                    "rule": "operation-description",
                    "severity": "warning",
                    "message": "Missing summary and description",
                })

            # Check responses
            responses = operation.get("responses", {})
            if not responses:
                issues.append({
                    "path": path_str,
                    "method": method.upper(),
                    "rule": "responses-defined",
                    "severity": "critical",
                    "message": "No responses defined",
                })
            else:
                # Check for error responses
                has_error = any(
                    str(code).startswith(("4", "5")) or code == "default"
                    for code in responses
                )
                if not has_error:
                    issues.append({
                        "path": path_str,
                        "method": method.upper(),
                        "rule": "error-response",
                        "severity": "warning",
                        "message": "No error response (4xx/5xx) defined",
                    })

                # Check for success response content
                for code, resp in responses.items():
                    if isinstance(resp, dict) and str(code).startswith("2"):
                        if method != "delete" and not resp.get("content") and not resp.get("$ref"):
                            issues.append({
                                "path": path_str,
                                "method": method.upper(),
                                "rule": "response-content",
                                "severity": "info",
                                "message": f"Response {code} has no content schema",
                            })

            # Check request body for POST/PUT/PATCH
            if method in ("post", "put", "patch") and not operation.get("requestBody"):
                issues.append({
                    "path": path_str,
                    "method": method.upper(),
                    "rule": "request-body",
                    "severity": "info",
                    "message": f"{method.upper()} without requestBody",
                })

            # Check GET/DELETE should not have requestBody
            if method in ("get", "delete") and operation.get("requestBody"):
                issues.append({
                    "path": path_str,
                    "method": method.upper(),
                    "rule": "no-body-get-delete",
                    "severity": "warning",
                    "message": f"{method.upper()} should not have requestBody",
                })

            # Check tags
            if not operation.get("tags"):
                issues.append({
                    "path": path_str,
                    "method": method.upper(),
                    "rule": "operation-tags",
                    "severity": "info",
                    "message": "Missing tags for grouping",
                })

    # Check security schemes
    components = spec.get("components", {})
    security_schemes = components.get("securitySchemes", {})
    global_security = spec.get("security", [])

    if not security_schemes and not global_security:
        issues.append({
            "path": "/components/securitySchemes",
            "method": "-",
            "rule": "security-defined",
            "severity": "warning",
            "message": "No security schemes defined",
        })

    # Check servers
    if not spec.get("servers"):
        issues.append({
            "path": "/servers",
            "method": "-",
            "rule": "servers-defined",
            "severity": "info",
            "message": "No servers defined",
        })

    return {
        "spec_version": spec_version,
        "paths_count": paths_count,
        "issues": issues,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate OpenAPI 3.x specs")
    parser.add_argument("spec_path", help="Path to OpenAPI spec file (YAML or JSON)")
    args = parser.parse_args()

    spec = load_spec(args.spec_path)
    if not spec:
        result = {
            "spec_version": "",
            "paths_count": 0,
            "issues": [{
                "path": "/",
                "method": "-",
                "rule": "parse-error",
                "severity": "critical",
                "message": f"Could not parse spec file: {args.spec_path}",
            }],
        }
    else:
        result = validate_spec(spec)

    json.dump(result, sys.stdout, indent=2)
    print()
    if any(i.get("severity") == "critical" for i in result.get("issues", [])):
        sys.exit(1)


if __name__ == "__main__":
    main()
