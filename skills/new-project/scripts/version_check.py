#!/usr/bin/env python3
"""Return version-check commands for selected packages."""

from __future__ import annotations

import argparse
import json
import shlex

from catalog_utils import resolve_package_alias, valid_package_name


def build_check(package: str, ecosystem: str) -> tuple[dict | None, str | None]:
    alias = resolve_package_alias(package)
    resolved_package = alias["package"]
    if not resolved_package:
        return None, f"{package}: {alias.get('notes') or 'package name must be verified'}"
    if not valid_package_name(resolved_package, ecosystem):
        return None, f"{package}: invalid {ecosystem} package name"

    if ecosystem == "npm":
        argv = ["npm", "view", resolved_package, "version"]
    else:
        argv = ["uvx", "--from", "pip-index", "pip-index", "versions", resolved_package]

    check = {
        "input": package,
        "package": resolved_package,
        "argv": argv,
        "display": shlex.join(argv),
    }
    if alias.get("notes"):
        check["notes"] = alias["notes"]
    return check, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Suggest package registry checks for current versions.")
    parser.add_argument("packages", nargs="*", help="Package names to check")
    parser.add_argument("--ecosystem", choices=["npm", "pypi"], default="npm")
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args()

    checks: list[dict] = []
    warnings: list[str] = []
    errors: list[str] = []
    for package in args.packages:
        check, warning = build_check(package, args.ecosystem)
        if check:
            checks.append(check)
        elif warning:
            if "invalid" in warning:
                errors.append(warning)
            else:
                warnings.append(warning)

    result = {
        "ok": not errors,
        "ecosystem": args.ecosystem,
        "checks": checks,
        "commands": [check["display"] for check in checks],
        "warnings": warnings,
        "errors": errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
