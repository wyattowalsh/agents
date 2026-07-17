#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from scripts.mcphub.group_validation import (
    enabled_settings_server_ids,
    registry_server_ids,
    render_group_server,
    validate_enabled_registry_group,
    validate_group_server_entries,
)

SECRET_KEY_RE = re.compile(r"(TOKEN|SECRET|PASSWORD|API_KEY|AUTH_KEY|JWT)", re.I)
PLACEHOLDER_RE = re.compile(r"^\$\{[A-Z_][A-Z0-9_]*\}$")
BAD_LITERALS = {"changeme", "change-me", "secret", "password", "token", "your-token", "your-secret"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_settings(settings: dict[str, Any], registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    registry_servers = registry.get("servers", {})
    if not isinstance(registry_servers, dict):
        registry_servers = {}
    servers = settings.get("mcpServers")
    if not isinstance(servers, dict) or not servers:
        errors.append("mcpServers must be a non-empty object")
        settings_server_ids: set[str] = set()
        settings_enabled_server_ids: set[str] = set()
    else:
        settings_servers: dict[str, Any] = {str(name): entry for name, entry in servers.items()}
        settings_server_ids = set(settings_servers)
        settings_enabled_server_ids = enabled_settings_server_ids(settings_servers)
        registry_ids = registry_server_ids(registry_servers)
        missing = sorted(registry_ids - settings_server_ids)
        extra = sorted(settings_server_ids - set(registry_servers))
        if missing:
            errors.append("mcp_settings.json is missing registry servers: " + ", ".join(missing))
        if extra:
            errors.append("mcp_settings.json has servers not in registry: " + ", ".join(extra))

    groups_raw = settings.get("groups", {})
    groups: dict[str, Any] = {}
    if isinstance(groups_raw, list):
        for entry in groups_raw:
            if not isinstance(entry, dict):
                errors.append("groups entries must be objects")
                continue
            group_name = entry.get("name")
            if not isinstance(group_name, str) or not group_name:
                errors.append("groups entries require a non-empty name")
                continue
            groups[group_name] = entry
    elif isinstance(groups_raw, dict):
        groups = groups_raw
    else:
        errors.append("groups must be an array or object")
        groups_raw = {}

    if isinstance(groups, dict) and isinstance(servers, dict):
        for group_name, group in groups.items():
            if not isinstance(group, dict):
                errors.append(f"group {group_name} must be an object")
                continue
            errors.extend(
                validate_group_server_entries(
                    str(group_name),
                    group,
                    all_server_ids=settings_server_ids,
                    enabled_server_ids=settings_enabled_server_ids,
                    source_prefix="groups",
                )
            )

    registry_groups = registry.get("mcphub", {}).get("groups", {})
    if isinstance(registry_groups, dict) and isinstance(groups, dict):
        expected_group_names = {
            name
            for name, group in registry_groups.items()
            if isinstance(group, dict) and group.get("enabled") is not False
        }
        actual_group_names = set(groups)
        missing_groups = sorted(expected_group_names - actual_group_names)
        extra_groups = sorted(actual_group_names - expected_group_names)
        if missing_groups:
            errors.append("mcp_settings.json is missing registry groups: " + ", ".join(missing_groups))
        if extra_groups:
            errors.append("mcp_settings.json has groups not in registry: " + ", ".join(extra_groups))
        registry_group_errors: dict[str, list[str]] = {}
        for group_name in sorted(expected_group_names):
            registry_group = registry_groups.get(group_name, {})
            if not isinstance(registry_group, dict):
                message = f"mcphub.groups.{group_name} must be an object"
                registry_group_errors[group_name] = [message]
                errors.append(message)
                continue
            group_errors = validate_enabled_registry_group(str(group_name), registry_group, registry_servers)
            if group_errors:
                registry_group_errors[group_name] = group_errors
                errors.extend(group_errors)
        for group_name in sorted(expected_group_names & actual_group_names):
            if registry_group_errors.get(group_name):
                continue
            registry_group = registry_groups.get(group_name, {})
            settings_group = groups.get(group_name, {})
            if not isinstance(registry_group, dict) or not isinstance(settings_group, dict):
                continue
            expected_servers = [render_group_server(server) for server in registry_group.get("servers", [])]
            settings_servers = settings_group.get("servers", [])
            if expected_servers != settings_servers:
                errors.append(f"group {group_name} server membership drift vs registry")

    system_config = settings.get("systemConfig", {})
    if not isinstance(system_config, dict):
        errors.append("systemConfig must be an object")
        system_config = {}

    smart_routing = system_config.get("smartRouting", {})
    if isinstance(smart_routing, dict) and smart_routing.get("enabled") is not False:
        errors.append("systemConfig.smartRouting.enabled must be false in tracked settings")

    compression = system_config.get("toolResultCompression", {})
    if compression not in ({}, None) and not isinstance(compression, dict):
        errors.append("systemConfig.toolResultCompression must be an object when present")

    routing = system_config.get("routing", {})
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
