"""Tests for wagents.catalog — node collection, deduplication, and edge extraction."""

from pathlib import Path

from wagents.catalog import (
    RELATED_SKILLS,
    CatalogNode,
    collect_edges,
    collect_installed_skills,
    collect_nodes,
)
from wagents.installed_inventory import HarnessQueryResult, InstalledInventorySnapshot, InstalledSkillInventoryRow

# ---------------------------------------------------------------------------
# collect_nodes
# ---------------------------------------------------------------------------


def test_collect_nodes_returns_all_kinds(tmp_repo):
    """A tmp_repo with 1 skill, 1 agent, and 1 MCP yields 3 nodes of correct types."""
    # Create a valid skill
    skill_dir = tmp_repo / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: test-skill\ndescription: A test skill\n---\n\n# Test Skill\n\nBody.\n"
    )

    # Create a valid agent
    (tmp_repo / "agents" / "test-agent.md").write_text(
        "---\nname: test-agent\ndescription: A test agent\n---\n\n# Test Agent\n\nBody.\n"
    )

    # Create a valid MCP server
    mcp_dir = tmp_repo / "mcp" / "test-mcp"
    mcp_dir.mkdir(parents=True)
    (mcp_dir / "pyproject.toml").write_text(
        '[project]\nname = "mcp-test-mcp"\nversion = "0.1.0"\n'
        'description = "A test MCP server"\nrequires-python = ">=3.13"\n'
        'dependencies = ["fastmcp>=2"]\n'
    )
    (mcp_dir / "server.py").write_text('from fastmcp import FastMCP\n\nmcp = FastMCP("Test Mcp")\n')

    ignored_runtime_dir = tmp_repo / "mcp" / "servers" / "runtime-mcp"
    ignored_runtime_dir.mkdir(parents=True)
    (ignored_runtime_dir / "pyproject.toml").write_text(
        '[project]\nname = "mcp-runtime-mcp"\nversion = "0.1.0"\n'
        'description = "A runtime MCP server"\nrequires-python = ">=3.13"\n'
        'dependencies = ["fastmcp>=2"]\n'
    )
    (ignored_runtime_dir / "server.py").write_text('from fastmcp import FastMCP\n\nmcp = FastMCP("Runtime")\n')

    nodes = collect_nodes()

    assert len(nodes) == 3
    kinds = {n.kind for n in nodes}
    assert kinds == {"skill", "agent", "mcp"}

    # Verify each node's id
    ids_by_kind = {n.kind: n.id for n in nodes}
    assert ids_by_kind["skill"] == "test-skill"
    assert ids_by_kind["agent"] == "test-agent"
    assert ids_by_kind["mcp"] == "test-mcp"
    assert next(n for n in nodes if n.kind == "mcp").source_path == "mcp/test-mcp/server.py"


# ---------------------------------------------------------------------------
# collect_installed_skills — deduplication
# ---------------------------------------------------------------------------


def test_collect_installed_skills_skips_existing(tmp_path, monkeypatch):
    """A skill whose ID is already in existing_ids is skipped."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: An installed skill\n---\n\n# My Skill\n\nBody.\n"
    )
    snapshot = InstalledInventorySnapshot(
        rows=(
            InstalledSkillInventoryRow(
                name="my-skill",
                path=str(skill_dir),
                source_path=str(skill_dir / "SKILL.md"),
                scope="global",
                description="An installed skill",
                license="",
                version="",
                author="",
                source="example/skills",
                install_source="example/skills",
                source_url="https://github.com/example/skills",
                install_command="npx skills add example/skills --skill my-skill -y -g",
                provenance_status="installed-external",
                trust_tier="github",
                selector_mode="named",
                installed_agents=("claude-code",),
                discovered_in=("claude-code",),
                target_agents=(),
            ),
        ),
        queries=(HarnessQueryResult(agent_id="claude-code", ok=True, entries=()),),
    )
    monkeypatch.setattr("wagents.catalog.collect_installed_inventory", lambda **kwargs: snapshot)

    # When "my-skill" is in existing_ids, it should be skipped
    existing = {"my-skill"}
    result = collect_installed_skills(existing)
    assert len(result) == 0

    # When "my-skill" is NOT in existing_ids, it should be collected
    result = collect_installed_skills(set())
    assert len(result) == 1
    assert result[0].id == "my-skill"
    assert result[0].source == "installed"


def test_collect_installed_skills_includes_lock_source(tmp_path, monkeypatch):
    """Installed skills carry source metadata from the active skills lock file."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: An installed skill\n---\n\n# My Skill\n\nBody.\n"
    )
    snapshot = InstalledInventorySnapshot(
        rows=(
            InstalledSkillInventoryRow(
                name="my-skill",
                path=str(skill_dir),
                source_path=str(skill_dir / "SKILL.md"),
                scope="global",
                description="An installed skill",
                license="",
                version="",
                author="",
                source="example/skills",
                install_source="example/skills",
                source_url="https://github.com/example/skills",
                install_command="npx skills add example/skills --skill my-skill -y -g",
                provenance_status="installed-external",
                trust_tier="github",
                selector_mode="named",
                installed_agents=("claude-code",),
                discovered_in=("claude-code",),
                target_agents=(),
            ),
        ),
        queries=(HarnessQueryResult(agent_id="claude-code", ok=True, entries=()),),
    )
    monkeypatch.setattr("wagents.catalog.collect_installed_inventory", lambda **kwargs: snapshot)

    result = collect_installed_skills(set())
    assert len(result) == 1
    assert result[0].metadata["_skills_source"] == "example/skills"


# ---------------------------------------------------------------------------
# collect_edges
# ---------------------------------------------------------------------------


def test_collect_edges_from_agent_metadata():
    """An agent with skills: [foo] and mcpServers: [bar] produces 2 edges."""
    agent_node = CatalogNode(
        kind="agent",
        id="my-agent",
        title="My Agent",
        description="Test agent",
        metadata={
            "name": "my-agent",
            "description": "Test agent",
            "skills": ["foo"],
            "mcpServers": ["bar"],
        },
        body="Body content.",
        source_path="agents/my-agent.md",
    )
    # Include a skill and mcp node (they don't produce edges themselves)
    skill_node = CatalogNode(
        kind="skill",
        id="foo",
        title="Foo",
        description="A skill",
        metadata={"name": "foo", "description": "A skill"},
        body="Body.",
        source_path="skills/foo/SKILL.md",
    )
    mcp_node = CatalogNode(
        kind="mcp",
        id="bar",
        title="Bar",
        description="An MCP server",
        metadata={},
        body="",
        source_path="mcp/bar/server.py",
    )

    edges = collect_edges([agent_node, skill_node, mcp_node])

    assert len(edges) == 2
    assert any(e.from_id == "agent:my-agent" and e.to_id == "skill:foo" and e.relation == "uses-skill" for e in edges)
    assert any(e.from_id == "agent:my-agent" and e.to_id == "mcp:bar" and e.relation == "uses-mcp" for e in edges)


# ---------------------------------------------------------------------------
# RELATED_SKILLS validation against the real repo
# ---------------------------------------------------------------------------


def test_related_skills_keys_are_valid_skill_dirs():
    """Every key and value in RELATED_SKILLS must be a real skill directory."""
    repo_root = Path(__file__).resolve().parent.parent
    skills_dir = repo_root / "skills"

    existing_skill_dirs = {d.name for d in skills_dir.iterdir() if d.is_dir()}

    for key, values in RELATED_SKILLS.items():
        assert key in existing_skill_dirs, f"RELATED_SKILLS key '{key}' does not match any skill directory"
        for val in values:
            assert val in existing_skill_dirs, (
                f"RELATED_SKILLS value '{val}' (under key '{key}') does not match any skill directory"
            )
