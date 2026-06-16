"""Collect MCP registry contributor-safety validation errors."""

from __future__ import annotations

import json
from pathlib import Path


def collect_mcp_registry_errors(repo_root: Path) -> list[dict[str, str]]:
    """Validate contributor-safe MCP tool policy in the registry."""
    path = repo_root / "config/mcp-registry.json"
    if not path.is_file():
        return []

    # Load inline (no _load_registry helper)
    registry = json.loads(path.read_text(encoding="utf-8"))
    errors: list[dict[str, str]] = []
    defaults = registry.get("contributor_defaults")
    if not isinstance(defaults, dict):
        errors.append({
            "source": "config/mcp-registry.json",
            "message": "Missing contributor_defaults block (tools_policy deny-by-default)",
        })
        wildcard_requires_opt_in = False
    else:
        if defaults.get("tools_policy") != "deny-by-default":
            errors.append({
                "source": "config/mcp-registry.json",
                "message": "contributor_defaults.tools_policy must be 'deny-by-default'",
            })
        wildcard_requires_opt_in = defaults.get("wildcard_requires_explicit_opt_in") is True

    # Continue server scan even if contributor_defaults missing (no early return)
    servers = registry.get("servers", {})
    if not isinstance(servers, dict):
        servers = {}

    for name, server in servers.items():
        if not isinstance(server, dict):
            continue
        tools = server.get("tools")
        if tools == ["*"] and wildcard_requires_opt_in and server.get("tools_allow_all") is not True:
            errors.append({
                "source": f"config/mcp-registry.json:servers.{name}",
                "message": "tools: ['*'] requires explicit tools_allow_all: true for maintainer opt-in",
            })
        if tools is None:
            errors.append({
                "source": f"config/mcp-registry.json:servers.{name}",
                "message": "tools field is required (use [] for deny-by-default)",
            })

    return errors
