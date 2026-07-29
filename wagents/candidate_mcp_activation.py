"""Shared MCPHub activation evidence helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def normalized_projection(entry: dict[str, Any], *, registry: bool) -> dict[str, Any]:
    raw_env = entry.get("env", {})
    if not isinstance(raw_env, dict):
        raw_env = {}
    env: dict[str, Any] = {}
    for name, value in raw_env.items():
        normalized = value
        if registry and isinstance(value, dict):
            if "value" in value:
                normalized = value["value"]
            elif isinstance(value.get("env_var"), str):
                normalized = f"${{{value['env_var']}}}"
        env[str(name)] = normalized
    timeout = entry.get("timeout_ms") if registry else entry.get("timeout")
    transport = entry.get("transport") if registry else entry.get("type")
    if transport is None and entry.get("command"):
        transport = "stdio"
    return {
        "args": entry.get("args", []),
        "command": entry.get("command"),
        "enabled": entry.get("enabled") is not False,
        "env": env,
        "oauth": entry.get("oauth"),
        "timeout": timeout,
        "transport": transport,
        "url": entry.get("url"),
    }


def configured_tools(entry: dict[str, Any]) -> tuple[list[str], bool]:
    values = entry.get("tools", [])
    tools = sorted({str(value) for value in values if isinstance(value, str) and value})
    allow_all = entry.get("tools_allow_all") is True or "*" in tools
    return [value for value in tools if value != "*"], allow_all


def mcphub_exposed_tool_names(server_id: str, configured_names: list[str]) -> list[str]:
    """Project registry-native tool names into MCPHub's server-qualified namespace."""
    return sorted({f"{server_id}-{name}" for name in configured_names if name})


def bearer_token_looks_usable(value: str) -> bool:
    token = value.strip()
    if not token or token != value:
        return False
    lowered = token.lower()
    placeholder_fragments = (
        "change-me",
        "changeme",
        "example",
        "placeholder",
        "replace-with-local",
        "replace-me",
        "your-token",
        "your_token",
    )
    return not (
        token.startswith("${")
        or token.startswith("<")
        or token.endswith(">")
        or any(fragment in lowered for fragment in placeholder_fragments)
    )
