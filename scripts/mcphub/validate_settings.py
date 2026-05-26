#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SECRET_KEY_RE = re.compile(r"(TOKEN|SECRET|PASSWORD|API_KEY|AUTH_KEY|JWT)", re.I)
PLACEHOLDER_RE = re.compile(r"^\$\{[A-Z_][A-Z0-9_]*\}$")
BAD_LITERALS = {"changeme", "change-me", "secret", "password", "token", "your-token", "your-secret"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_settings(settings: dict[str, Any], registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    servers = settings.get("mcpServers")
    if not isinstance(servers, dict) or not servers:
        errors.append("mcpServers must be a non-empty object")
    else:
        missing = sorted(set(registry.get("servers", {})) - set(servers))
        extra = sorted(set(servers) - set(registry.get("servers", {})))
        if missing:
            errors.append("mcp_settings.json is missing registry servers: " + ", ".join(missing))
        if extra:
            errors.append("mcp_settings.json has servers not in registry: " + ", ".join(extra))

    groups = settings.get("groups", {})
    if isinstance(groups, dict) and isinstance(servers, dict):
        for group_name, group in groups.items():
            if not isinstance(group, dict):
                errors.append(f"group {group_name} must be an object")
                continue
            for server in group.get("servers", []):
                if server not in servers:
                    errors.append(f"group {group_name} references unknown server {server}")

    routing = settings.get("systemConfig", {}).get("routing", {})
    expected = {
        "enableGlobalRoute": True,
        "enableGroupNameRoute": True,
        "enableBearerAuth": True,
        "bearerAuthHeaderName": "Authorization",
        "jsonBodyLimit": "5mb",
        "skipAuth": False,
    }
    for key, value in expected.items():
        if routing.get(key) != value:
            errors.append(f"systemConfig.routing.{key} must be {value!r}")

    def walk(value: Any, path: list[str]) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "bearerAuthKey" and isinstance(child, str) and child and not PLACEHOLDER_RE.match(child):
                    errors.append("systemConfig.routing.bearerAuthKey must not contain a tracked literal")
                walk(child, [*path, str(key)])
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, [*path, str(index)])
        elif isinstance(value, str):
            joined = ".".join(path)
            lowered = value.lower()
            if SECRET_KEY_RE.search(joined) and value and not PLACEHOLDER_RE.match(value):
                errors.append(f"{joined} must use an env placeholder, not a tracked literal")
            if lowered in BAD_LITERALS or value.startswith("sk-") or value.startswith("ghp_"):
                errors.append(f"{joined} looks like a real or placeholder secret that should not be tracked")

    walk(settings, [])
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate tracked MCPHub settings.")
    parser.add_argument("--settings", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    args = parser.parse_args()

    errors = validate_settings(load_json(args.settings), load_json(args.registry))
    if errors:
        for error in errors:
            print(f"error: {error}")
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
