#!/usr/bin/env python3
"""Check local readiness for docling-graph workflows."""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import os
import shutil
import sys
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class Check:
    name: str
    status: str
    detail: str


def _package_version() -> tuple[str | None, str]:
    try:
        return importlib.metadata.version("docling-graph"), "installed"
    except importlib.metadata.PackageNotFoundError:
        try:
            return importlib.metadata.version("docling_graph"), "installed"
        except importlib.metadata.PackageNotFoundError:
            return None, "missing"


def _check_python() -> Check:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):
        return Check("python", "ok", version)
    return Check("python", "error", f"{version}; Python 3.10+ required")


def _check_import() -> Check:
    spec = importlib.util.find_spec("docling_graph")
    if spec is None:
        return Check("docling_graph_import", "missing", "module docling_graph not importable")
    return Check("docling_graph_import", "ok", "module docling_graph importable")


def _check_package() -> Check:
    version, status = _package_version()
    if version:
        return Check("docling_graph_package", "ok", version)
    return Check("docling_graph_package", status, "package metadata not found")


def _check_cli() -> Check:
    path = shutil.which("docling-graph")
    if path:
        return Check("docling_graph_cli", "ok", path)
    return Check("docling_graph_cli", "missing", "docling-graph executable not on PATH")


def _check_template(dotted_path: str) -> Check:
    module_name, sep, attr = dotted_path.rpartition(".")
    if not sep or not module_name or not attr:
        return Check("template_import", "error", "template must be a dotted path like package.module.Class")
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - report import diagnostics without hiding type.
        return Check("template_import", "error", f"module import failed: {type(exc).__name__}: {exc}")
    if not hasattr(module, attr):
        return Check("template_import", "error", f"{module_name} imports but has no attribute {attr}")
    return Check("template_import", "ok", dotted_path)


def _check_env_var(name: str) -> Check:
    if os.environ.get(name):
        return Check(f"env:{name}", "ok", "present")
    return Check(f"env:{name}", "missing", "not set")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    checks = [_check_python(), _check_package(), _check_import(), _check_cli()]
    for env_name in args.provider_env:
        checks.append(_check_env_var(env_name))
    if args.template:
        checks.append(_check_template(args.template))

    statuses = [check.status for check in checks]
    if "error" in statuses:
        overall = "error"
    elif "missing" in statuses:
        overall = "warning"
    else:
        overall = "ok"

    return {
        "tool": "docling-graph check-env",
        "overall_status": overall,
        "checks": [asdict(check) for check in checks],
        "notes": [
            "Secret values are never printed; provider environment checks only report presence.",
            "Missing docling-graph is acceptable for planning-only use, but live convert/API validation will not run.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check local docling-graph readiness")
    parser.add_argument("--template", help="Optional dotted template import path to validate")
    parser.add_argument(
        "--provider-env",
        action="append",
        default=[],
        help="Provider environment variable name to check; may be repeated",
    )
    parser.add_argument("--format", choices=["json", "pretty"], default="json")
    args = parser.parse_args()

    report = build_report(args)
    if args.format == "pretty":
        for check in report["checks"]:
            print(f"{check['status']:7} {check['name']}: {check['detail']}")
        print(f"overall: {report['overall_status']}")
    else:
        print(json.dumps(report, indent=2, sort_keys=True))

    if report["overall_status"] == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
