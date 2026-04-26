#!/usr/bin/env python3
"""Check local readiness for Docling Graph workflows."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TARGET_DOCLING_GRAPH_VERSION = "1.5.0"
PYTHON_MIN = (3, 10)


PROVIDER_ENV: dict[str, list[tuple[str, bool]]] = {
    "openai": [("OPENAI_API_KEY", True)],
    "mistral": [("MISTRAL_API_KEY", True)],
    "gemini": [("GOOGLE_API_KEY", False), ("GEMINI_API_KEY", False)],
    "watsonx": [
        ("WATSONX_APIKEY", True),
        ("WATSONX_URL", True),
        ("WATSONX_PROJECT_ID", True),
    ],
    "ollama": [("OLLAMA_HOST", False)],
    "vllm": [("VLLM_API_BASE", False), ("OPENAI_API_BASE", False)],
    "lmstudio": [("LM_STUDIO_API_BASE", False), ("LMSTUDIO_API_BASE", False), ("OPENAI_API_BASE", False)],
}


EXTRAS_HINTS = {
    "vlm": "Install the docling-graph VLM extra when local vision-language model extraction is required.",
    "delta-resolvers": "Install resolver extras when delta extraction depends on advanced entity resolution.",
}


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    severity: str = "info"

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ok": self.ok,
            "severity": self.severity,
            "detail": self.detail,
        }


def parse_version(value: str | None) -> tuple[int, ...] | None:
    if not value:
        return None
    parts: list[int] = []
    for raw in value.split("."):
        digits = ""
        for char in raw:
            if char.isdigit():
                digits += char
            else:
                break
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts) if parts else None


def installed_version() -> str | None:
    for package in ("docling-graph", "docling_graph"):
        try:
            return importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            continue
    return None


def check_python() -> Check:
    current = sys.version_info[:3]
    ok = current >= PYTHON_MIN and current[0] < 4
    detail = f"Python {current[0]}.{current[1]}.{current[2]} detected; expected >=3.10,<4"
    return Check("python", ok, detail, "error" if not ok else "info")


def check_package() -> Check:
    version = installed_version()
    if not version:
        return Check(
            "package",
            False,
            "docling-graph package is not installed in this environment",
            "warning",
        )

    parsed = parse_version(version)
    target = parse_version(TARGET_DOCLING_GRAPH_VERSION)
    if parsed and target and parsed >= target:
        return Check("package", True, f"docling-graph {version} installed")
    return Check(
        "package",
        False,
        f"docling-graph {version} installed; skill references {TARGET_DOCLING_GRAPH_VERSION}+ behavior",
        "warning",
    )


def check_module() -> Check:
    try:
        importlib.import_module("docling_graph")
    except Exception as exc:  # pragma: no cover - exact import failures are environment-specific
        return Check("module", False, f"cannot import docling_graph: {exc}", "warning")
    return Check("module", True, "docling_graph imports successfully")


def check_cli(check_help: bool) -> Check:
    cli = shutil.which("docling-graph")
    if not cli:
        return Check("cli", False, "docling-graph executable not found on PATH", "warning")
    if not check_help:
        return Check("cli", True, f"docling-graph executable found at {cli}")
    try:
        result = subprocess.run(
            [cli, "--help"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - shell availability is environment-specific
        return Check("cli", False, f"found {cli}, but --help failed: {exc}", "warning")

    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode == 0 and "docling" in output.lower():
        return Check("cli", True, f"docling-graph executable found at {cli}; --help works")
    return Check(
        "cli",
        False,
        f"found {cli}, but --help exited {result.returncode}",
        "warning",
    )


def check_template(template: str | None) -> Check | None:
    if not template:
        return None

    module_name, sep, object_name = template.partition(":")
    if not sep or not module_name or not object_name:
        return Check(
            "template",
            False,
            "template must use module:RootModel format",
            "error",
        )

    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        return Check("template", False, f"cannot import {module_name}: {exc}", "error")

    if not hasattr(module, object_name):
        return Check("template", False, f"{module_name} has no attribute {object_name}", "error")

    return Check("template", True, f"{template} imports successfully")


def env_status(name: str) -> str:
    value = os.environ.get(name)
    if value:
        return "set"
    return "missing"


def check_provider(provider: str) -> dict[str, Any]:
    envs = PROVIDER_ENV[provider]
    required = [name for name, is_required in envs if is_required]
    optional = [name for name, is_required in envs if not is_required]
    statuses = {name: env_status(name) for name, _ in envs}

    if not required:
        ok = True
        detail = "no required environment variables; optional base URL variables are reported as set/missing"
    elif provider == "gemini":
        ok = any(os.environ.get(name) for name in ("GOOGLE_API_KEY", "GEMINI_API_KEY"))
        detail = "one of GOOGLE_API_KEY or GEMINI_API_KEY must be set for Gemini"
    else:
        ok = all(os.environ.get(name) for name in required)
        detail = "required environment variables are set" if ok else "missing required environment variables"

    return {
        "provider": provider,
        "ok": ok,
        "required": required,
        "optional": optional,
        "env": statuses,
        "detail": detail,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    checks = [
        check_python(),
        check_package(),
        check_module(),
        check_cli(args.check_cli_help),
    ]

    template_check = check_template(args.template)
    if template_check:
        checks.append(template_check)

    provider_reports = [check_provider(provider) for provider in args.provider]

    legacy_provider_env = []
    for item in args.provider_env:
        legacy_provider_env.append(
            {
                "name": item,
                "ok": bool(os.environ.get(item)),
                "status": env_status(item),
            }
        )

    ok = all(check.ok or check.severity != "error" for check in checks)
    ok = ok and all(report["ok"] for report in provider_reports)

    return {
        "ok": ok,
        "target_docling_graph_version": TARGET_DOCLING_GRAPH_VERSION,
        "checks": [check.as_dict() for check in checks],
        "providers": provider_reports,
        "provider_env": legacy_provider_env,
        "extras_hints": EXTRAS_HINTS,
        "notes": [
            "Provider secrets are reported only as set/missing.",
            "Run docling-graph inspect on real output directories before declaring graph quality.",
        ],
    }


def print_pretty(report: dict[str, Any]) -> None:
    status = "OK" if report["ok"] else "CHECK"
    print(f"Docling Graph environment: {status}")
    for check in report["checks"]:
        mark = "ok" if check["ok"] else check["severity"]
        print(f"- {check['name']}: {mark} - {check['detail']}")
    for provider in report["providers"]:
        mark = "ok" if provider["ok"] else "warning"
        print(f"- provider {provider['provider']}: {mark} - {provider['detail']}")
        for name, state in provider["env"].items():
            print(f"  - {name}: {state}")
    if report["provider_env"]:
        print("- explicit provider env checks:")
        for item in report["provider_env"]:
            mark = "ok" if item["ok"] else "missing"
            print(f"  - {item['name']}: {mark}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", help="Optional template import path in module:RootModel form")
    parser.add_argument(
        "--provider",
        action="append",
        choices=sorted(PROVIDER_ENV),
        default=[],
        help="Provider preset to check; repeat for multiple providers",
    )
    parser.add_argument(
        "--provider-env",
        action="append",
        default=[],
        help="Additional environment variable to check without printing its value",
    )
    parser.add_argument(
        "--no-cli-help",
        dest="check_cli_help",
        action="store_false",
        help="Only check for the CLI path; do not run docling-graph --help",
    )
    parser.set_defaults(check_cli_help=True)
    parser.add_argument("--format", choices=("pretty", "json"), default="pretty")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = build_report(args)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_pretty(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
