"""MCP server: agent-catalog.

Read-only access to the repo agent catalog: frontmatter-derived catalog
nodes (`wagents.catalog.collect_nodes`, kind == "agent") plus the
agent -> skill/mcp cross-reference edges derived from agent frontmatter.
No tool in this server mutates the repository.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from wagents.mcp_shared.catalog_readers import edge_to_dict, find_node, list_edges, node_to_dict

mcp = FastMCP("Agent Catalog")

_READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


@mcp.tool(annotations=_READ_ONLY)
def list_agents(query: str = "") -> list[dict[str, Any]]:
    """List repo agents (`agents/<name>.md`) from frontmatter-derived catalog nodes.

    Pass *query* (case-insensitive substring) to filter by id, title, or
    description; leave empty to list every agent. Returns lightweight
    summaries — use `get_agent` for full frontmatter metadata and system
    prompt body on a specific agent.
    """
    from wagents.catalog import collect_nodes

    needle = query.strip().lower()
    results = []
    for node in collect_nodes():
        if node.kind != "agent":
            continue
        haystack = f"{node.id} {node.title} {node.description}".lower()
        if needle and needle not in haystack:
            continue
        results.append({
            "id": node.id,
            "title": node.title,
            "description": node.description,
            "source_path": node.source_path,
        })
    return sorted(results, key=lambda r: r["id"])


@mcp.tool(annotations=_READ_ONLY)
def get_agent(agent_id: str) -> dict[str, Any]:
    """Return full catalog metadata (frontmatter, system prompt body, source path) for one agent.

    *agent_id* is the kebab-case agent name matching `agents/<agent_id>.md`.
    Raises if the agent is not found — call `list_agents` first if the exact
    id is unknown.
    """
    node = find_node("agent", agent_id)
    if node is None:
        raise ValueError(f"No agent found with id={agent_id!r}. Call list_agents() to browse available ids.")
    return node_to_dict(node)


@mcp.tool(annotations=_READ_ONLY)
def agent_skill_edges(agent_id: str = "") -> list[dict[str, Any]]:
    """Return agent -> skill/mcp cross-reference edges derived from agent frontmatter.

    Each edge has `from_id` (e.g. "agent:my-agent"), `to_id` (e.g.
    "skill:review"), and `relation` ("uses-skill" | "uses-mcp"), one per
    declared reference in an agent's `skills` or `mcpServers` frontmatter
    list. Pass *agent_id* to restrict results to edges originating from a
    single agent (matched against `from_id` as "agent:<agent_id>"); leave
    empty to return every edge in the repo. Use this to answer "what does
    agent X depend on?" or "which agents reference skill/mcp Y?" (filter the
    returned list client-side on `to_id` for the latter).
    """
    edges = [edge_to_dict(e) for e in list_edges()]
    if agent_id:
        target = f"agent:{agent_id}"
        edges = [e for e in edges if e.get("from_id") == target]
    return edges


if __name__ == "__main__":
    mcp.run()
