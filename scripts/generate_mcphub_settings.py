#!/usr/bin/env python3
"""Generate tracked MCPHub settings from config/mcp-registry.json."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any

from scripts.mcphub.group_validation import render_group_server, validate_enabled_registry_group
from scripts.sync_agent_stack import render_env_value, replace_arg_placeholders

DEFAULT_ROUTING: dict[str, Any] = {
    "enableGlobalRoute": True,
    "enableGroupNameRoute": True,
    "enableBearerAuth": True,
    "bearerAuthHeaderName": "Authorization",
    "jsonBodyLimit": "5mb",
    "skipAuth": False,
}

DEFAULT_SMART_ROUTING: dict[str, Any] = {
    "enabled": False,
    "embeddingProvider": "${SMART_ROUTING_EMBEDDING_PROVIDER}",
    "embeddingModel": "${EMBEDDING_MODEL}",
    "progressiveDisclosure": "${SMART_ROUTING_PROGRESSIVE_DISCLOSURE}",
}

DEFAULT_TOOL_RESULT_COMPRESSION: dict[str, Any] = {
    "enabled": False,
    "minTokens": 2000,
    "maxOutputTokens": 1200,
    "strategy": "auto",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


HTTP_TRANSPORTS = frozenset({"streamable-http", "sse"})
SUPPORTED_TRANSPORTS = frozenset({"stdio", "sse", "streamable-http", "openapi"})
PASSTHROUGH_FIELDS = (
    "description",
    "owner",
    "options",
    "proxy",
    "oauth",
    "passthroughHeaders",
    "enableKeepAlive",
    "keepAliveInterval",
)


def render_url_value(url: str) -> str:
    return url


def render_header_value(value: Any) -> str:
    if isinstance(value, dict):
        return render_env_value(value, {}, local_values=False)
    return str(value)


def copy_optional_fields(entry: dict[str, Any], server: dict[str, Any]) -> None:
    if entry.get("headers"):
        server["headers"] = {key: render_header_value(value) for key, value in entry["headers"].items()}
    for field in PASSTHROUGH_FIELDS:
        if field in entry:
            server[field] = entry[field]


def render_server_entry(entry: dict[str, Any]) -> dict[str, Any]:
    transport = str(entry.get("transport", "stdio"))
    server: dict[str, Any] = {}

    if transport not in SUPPORTED_TRANSPORTS:
        raise ValueError(f"unsupported MCPHub server transport: {transport}")

    if transport == "stdio":
        server["command"] = entry["command"]
        if "args" in entry:
            server["args"] = replace_arg_placeholders(entry.get("args", []), {}, local_values=False)
    elif transport in HTTP_TRANSPORTS:
        server["type"] = transport
        server["url"] = render_url_value(str(entry["url"]))
    elif transport == "openapi":
        server["type"] = "openapi"
        openapi = dict(entry["openapi"])
        if "url" in openapi:
            openapi["url"] = render_url_value(str(openapi["url"]))
        server["openapi"] = openapi

    if entry.get("env"):
        server["env"] = {key: render_env_value(value, {}, local_values=False) for key, value in entry["env"].items()}
    copy_optional_fields(entry, server)
    if entry.get("timeout_ms"):
        server["timeout"] = entry["timeout_ms"]
    if entry.get("enabled") is False:
        server["disabled"] = True
    return server


def group_id_for_name(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"agents-mcphub-group:{name}"))


def render_groups(mcphub_groups: dict[str, Any], registry_servers: dict[str, Any]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for name in sorted(mcphub_groups):
        group = mcphub_groups[name]
        if not isinstance(group, dict):
            raise ValueError(f"mcphub.groups.{name} must be an object")
        if group.get("enabled") is False:
            continue
        errors = validate_enabled_registry_group(name, group, registry_servers)
        if errors:
            raise ValueError("; ".join(errors))
        groups.append(
            {
                "id": group_id_for_name(name),
                "name": name,
                "description": str(group.get("description", "")),
                "servers": [render_group_server(server) for server in group.get("servers", [])],
            }
        )
    return groups


def generate_settings(registry: dict[str, Any]) -> dict[str, Any]:
    mcp_servers: dict[str, Any] = {}
    for name, entry in sorted(registry.get("servers", {}).items()):
        if not isinstance(entry, dict):
            continue
        try:
            mcp_servers[name] = render_server_entry(entry)
        except ValueError as exc:
            raise ValueError(f"servers.{name}: {exc}") from exc

    mcphub = registry.get("mcphub", {})
    mcphub_groups = mcphub.get("groups", {})
    groups = render_groups(
        mcphub_groups if isinstance(mcphub_groups, dict) else {},
        registry.get("servers", {}) if isinstance(registry.get("servers", {}), dict) else {},
    )

    return {
        "mcpServers": mcp_servers,
        "groups": groups,
        "systemConfig": {
            "routing": DEFAULT_ROUTING.copy(),
            "smartRouting": DEFAULT_SMART_ROUTING.copy(),
            "toolResultCompression": DEFAULT_TOOL_RESULT_COMPRESSION.copy(),
        },
    }


def serialize_settings(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def repo_paths(repo_root: Path) -> tuple[Path, Path]:
    return (
        repo_root / "config" / "mcp-registry.json",
        repo_root / "mcp" / "mcphub" / "mcp_settings.json",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate MCPHub settings from the MCP registry.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (defaults to parent of scripts/).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when generated output would change the tracked settings file.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Write generated JSON to stdout instead of the settings file.",
    )
    args = parser.parse_args(argv)

    registry_path, settings_path = repo_paths(args.repo_root)
    registry = load_json(registry_path)
    try:
        generated = generate_settings(registry)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    rendered = serialize_settings(generated)

    if args.stdout:
        sys.stdout.write(rendered)
        return 0

    if args.check:
        if not settings_path.exists():
            print(f"error: missing settings file: {settings_path}", file=sys.stderr)
            return 1
        current = settings_path.read_text(encoding="utf-8")
        if current != rendered:
            print("error: mcp/mcphub/mcp_settings.json is stale; run generate_mcphub_settings.py", file=sys.stderr)
            return 1
        print("ok")
        return 0

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(rendered, encoding="utf-8")
    print(f"wrote {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
