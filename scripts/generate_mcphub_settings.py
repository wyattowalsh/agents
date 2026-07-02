#!/usr/bin/env python3
"""Generate tracked MCPHub settings from config/mcp-registry.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

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


def render_server_entry(entry: dict[str, Any]) -> dict[str, Any]:
    server: dict[str, Any] = {
        "command": entry["command"],
        "args": replace_arg_placeholders(entry.get("args", []), {}, local_values=False),
    }
    if entry.get("env"):
        server["env"] = {
            key: render_env_value(value, {}, local_values=False) for key, value in entry["env"].items()
        }
    if entry.get("timeout_ms"):
        server["timeout"] = entry["timeout_ms"]
    return server


def render_groups(mcphub_groups: dict[str, Any], enabled_servers: set[str]) -> dict[str, Any]:
    groups: dict[str, Any] = {}
    for name in sorted(mcphub_groups):
        group = mcphub_groups[name]
        if not isinstance(group, dict) or group.get("enabled") is False:
            continue
        servers = [server for server in group.get("servers", []) if server in enabled_servers]
        if not servers:
            continue
        groups[name] = {
            "name": name,
            "description": str(group.get("description", "")),
            "servers": servers,
        }
    return groups


def generate_settings(registry: dict[str, Any]) -> dict[str, Any]:
    mcp_servers: dict[str, Any] = {}
    for name, entry in sorted(registry.get("servers", {}).items()):
        if not isinstance(entry, dict) or entry.get("enabled") is False:
            continue
        mcp_servers[name] = render_server_entry(entry)

    mcphub = registry.get("mcphub", {})
    mcphub_groups = mcphub.get("groups", {})
    groups = render_groups(mcphub_groups if isinstance(mcphub_groups, dict) else {}, set(mcp_servers))

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
    generated = generate_settings(registry)
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