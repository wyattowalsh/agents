"""Fail-closed policy for the July 2026 candidate MCP runtime set."""

from __future__ import annotations

from typing import Any

CANDIDATE_MCP_SERVERS = frozenset({
    "antv-chart",
    "axiom-mcp",
    "better-icons",
    "charted",
    "csvglow",
    "designer-skill-mcp",
    "geo-mcp",
    "langfuse-mcp",
    "mcp-dashboards",
    "mcp-excalidraw",
    "mobile-mcp",
    "nullcost",
    "openspec-mcp",
    "paper-search-mcp",
    "papersflow",
    "prompt-to-asset",
    "semiotic",
})
CREDENTIAL_BLOCKED_CANDIDATE_MCPS = frozenset({"langfuse-mcp", "papersflow"})
ENABLED_CANDIDATE_MCPS = CANDIDATE_MCP_SERVERS - CREDENTIAL_BLOCKED_CANDIDATE_MCPS


def candidate_mcp_enabled_set(registry: dict[str, Any]) -> frozenset[str]:
    """Validate and return the exact enabled candidate MCP partition."""
    servers = registry.get("servers")
    groups = registry.get("mcphub", {}).get("groups")
    if not isinstance(servers, dict) or not isinstance(groups, dict):
        raise ValueError("MCP registry must contain server and MCPHub group objects")
    group = groups.get("candidate-corpus")
    if not isinstance(group, dict) or group.get("enabled") is not True:
        raise ValueError("candidate-corpus MCPHub group must exist and be enabled")
    group_servers = group.get("servers")
    if not isinstance(group_servers, list):
        raise ValueError("candidate-corpus MCPHub group servers must be a list")
    names = [str(item.get("name") or "") for item in group_servers if isinstance(item, dict)]
    if len(names) != len(set(names)) or set(names) != ENABLED_CANDIDATE_MCPS:
        raise ValueError("candidate-corpus MCPHub group must contain the exact 15-server enabled partition")
    for name in CANDIDATE_MCP_SERVERS:
        entry = servers.get(name)
        if not isinstance(entry, dict):
            raise ValueError(f"candidate MCP registry entry is missing: {name}")
        expected_enabled = name in ENABLED_CANDIDATE_MCPS
        if entry.get("enabled") is not expected_enabled:
            raise ValueError(f"candidate MCP enabled state does not match policy: {name}")
    return frozenset(names)
