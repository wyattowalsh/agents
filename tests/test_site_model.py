"""Tests for shared docs site data."""

from wagents.catalog import CatalogNode
from wagents.site_model import (
    SUPPORTED_AGENT_IDS,
    build_install_command,
    render_site_data_module,
    site_data,
)


def test_install_commands_use_shared_supported_agents():
    command = build_install_command(skill="honest-review")

    assert command.startswith("npx skills add github:wyattowalsh/agents --skill honest-review -y -g")
    for agent_id in SUPPORTED_AGENT_IDS:
        assert f"--agent {agent_id}" in command
    assert "claude-code --agent codex --agent gemini-cli" not in command


def test_site_data_derives_counts_from_catalog_nodes():
    nodes = [
        CatalogNode("skill", "one", "One", "Skill", {}, "", "skills/one/SKILL.md"),
        CatalogNode("skill", "two", "Two", "Skill", {}, "", "/tmp/two/SKILL.md", source="installed"),
        CatalogNode("agent", "agent-one", "Agent One", "Agent", {}, "", "agents/agent-one.md"),
    ]

    data = site_data(nodes, mcp_config_count=30, has_mcp_overview=True)

    assert data["counts"] == {
        "customSkills": 1,
        "installedSkills": 1,
        "agents": 1,
        "mcpServers": 30,
    }


def test_render_site_data_module_exports_runtime_constants():
    rendered = render_site_data_module(site_data([]))

    assert "export const siteData =" in rendered
    assert "export const supportedAgents = siteData.supportedAgents;" in rendered
    assert "export const installCommands = siteData.installCommands;" in rendered
