"""Tests for wagents.rendering — page renderers and utilities."""

from wagents.catalog import CatalogEdge, CatalogNode
from wagents.rendering import (
    read_raw_content,
    render_agent_page,
    render_mcp_page,
    render_page,
    render_skill_page,
    render_tabs,
    scaffold_doc_page,
)

# ---------------------------------------------------------------------------
# render_tabs
# ---------------------------------------------------------------------------


class TestRenderTabs:
    def test_empty_returns_empty(self):
        assert render_tabs([]) == []

    def test_single_tab_becomes_heading(self):
        result = render_tabs([("General", "content")])
        assert "### General" in result
        assert "content" in result
        assert "<Tabs>" not in result

    def test_multiple_tabs(self):
        result = render_tabs([("A", "a-content"), ("B", "b-content")])
        text = "\n".join(result)
        assert "<Tabs>" in text
        assert '<TabItem label="A">' in text
        assert '<TabItem label="B">' in text
        assert "</Tabs>" in text


# ---------------------------------------------------------------------------
# render_page dispatch
# ---------------------------------------------------------------------------


def _make_node(kind, **overrides):
    defaults = {
        "kind": kind,
        "id": f"test-{kind}",
        "title": f"Test {kind.title()}",
        "description": "A test description",
        "metadata": {"name": f"test-{kind}", "description": "A test description"},
        "body": f"# Test\n\nBody for {kind}.",
        "source_path": f"skills/test-{kind}/SKILL.md" if kind == "skill" else f"agents/test-{kind}.md",
        "source": "custom",
    }
    defaults.update(overrides)
    return CatalogNode(**defaults)


class TestRenderPage:
    def test_dispatch_skill(self, tmp_repo):
        node = _make_node("skill")
        # Create the source file so read_raw_content works
        skill_dir = tmp_repo / "skills" / "test-skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test-skill\ndescription: A test description\n---\n\n# Test\n\nBody for skill.\n"
        )
        result = render_page(node, [], [node])
        assert 'title: "test-skill"' in result
        assert "A test description" in result

    def test_dispatch_agent(self, tmp_repo):
        node = _make_node("agent", source_path="agents/test-agent.md")
        result = render_page(node, [], [node])
        assert 'title: "test-agent"' in result

    def test_dispatch_mcp(self, tmp_repo):
        node = _make_node(
            "mcp",
            metadata={
                "project": {
                    "name": "mcp-test",
                    "version": "0.1.0",
                    "requires-python": ">=3.13",
                    "dependencies": ["fastmcp>=2"],
                },
                "fastmcp_config": {},
            },
            source_path="mcp/test-mcp/server.py",
        )
        result = render_page(node, [], [node])
        assert 'title: "test-mcp"' in result
        assert "MCP" in result

    def test_dispatch_unknown_returns_empty(self, tmp_repo):
        node = _make_node("unknown")
        assert render_page(node, [], [node]) == ""


# ---------------------------------------------------------------------------
# render_skill_page
# ---------------------------------------------------------------------------


class TestRenderSkillPage:
    def test_basic_output(self, tmp_repo):
        node = _make_node("skill")
        skill_dir = tmp_repo / "skills" / "test-skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test-skill\ndescription: A test description\n---\n\n# Test\n\nBody for skill.\n"
        )
        result = render_skill_page(node, [], [node])
        assert "## What It Does" in result
        assert "Quick Start" in result
        assert "View Full SKILL.md" in result
        assert "View source on GitHub" in result

    def test_badges(self, tmp_repo):
        node = _make_node(
            "skill",
            metadata={
                "name": "test-skill",
                "description": "A test description",
                "license": "MIT",
                "model": "sonnet",
                "metadata": {"version": "1.0", "author": "tester"},
            },
        )
        skill_dir = tmp_repo / "skills" / "test-skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text("---\nname: test-skill\ndescription: A test\n---\n\n# X\n\nBody.\n")
        result = render_skill_page(node, [], [node])
        assert "MIT" in result
        assert "sonnet" in result
        assert "v1.0" in result
        assert "tester" in result

    def test_used_by_edges(self, tmp_repo):
        skill_node = _make_node("skill")
        agent_node = _make_node("agent", id="my-agent", description="Agent desc")
        edge = CatalogEdge(from_id="agent:my-agent", to_id="skill:test-skill", relation="uses-skill")
        skill_dir = tmp_repo / "skills" / "test-skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text("---\nname: test-skill\ndescription: A test\n---\n\n# X\n\nBody.\n")
        result = render_skill_page(skill_node, [edge], [skill_node, agent_node])
        assert "## Used By" in result
        assert "my-agent" in result

    def test_installed_skill_badge(self, tmp_repo):
        node = _make_node("skill", source="installed", source_path="/tmp/fake/SKILL.md")
        result = render_skill_page(node, [], [node])
        assert "Installed" in result
        # No "View source on GitHub" for installed
        assert "View source on GitHub" not in result


# ---------------------------------------------------------------------------
# render_agent_page
# ---------------------------------------------------------------------------


class TestRenderAgentPage:
    def test_basic_output(self, tmp_repo):
        node = _make_node("agent", source_path="agents/test-agent.md")
        result = render_agent_page(node, [], [node])
        assert "## System Prompt" in result
        assert "View source on GitHub" in result

    def test_badges_for_model_and_permission(self, tmp_repo):
        node = _make_node(
            "agent",
            source_path="agents/test-agent.md",
            metadata={
                "name": "test-agent",
                "description": "A test",
                "model": "sonnet",
                "permissionMode": "plan",
            },
        )
        result = render_agent_page(node, [], [node])
        assert "sonnet" in result
        assert "plan" in result

    def test_skills_and_mcp_links(self, tmp_repo):
        skill_node = _make_node("skill", id="my-skill", description="Skill desc")
        mcp_node = _make_node(
            "mcp",
            id="my-mcp",
            description="MCP desc",
            metadata={"project": {}, "fastmcp_config": {}},
            source_path="mcp/my-mcp/server.py",
        )
        node = _make_node(
            "agent",
            source_path="agents/test-agent.md",
            metadata={
                "name": "test-agent",
                "description": "A test",
                "skills": ["my-skill"],
                "mcpServers": ["my-mcp"],
            },
        )
        result = render_agent_page(node, [], [node, skill_node, mcp_node])
        assert "## Skills" in result
        assert "my-skill" in result
        assert "## MCP Servers" in result
        assert "my-mcp" in result


# ---------------------------------------------------------------------------
# render_mcp_page
# ---------------------------------------------------------------------------


class TestRenderMcpPage:
    def test_basic_output(self, tmp_repo):
        node = _make_node(
            "mcp",
            metadata={
                "project": {
                    "name": "mcp-test",
                    "version": "0.1.0",
                    "requires-python": ">=3.13",
                    "dependencies": ["fastmcp>=2"],
                },
                "fastmcp_config": {"source": {"path": "server.py"}},
            },
            source_path="mcp/test-mcp/server.py",
        )
        result = render_mcp_page(node, [], [node])
        assert "## Server Source" in result
        assert "claude_desktop_config.json" in result
        assert "View source on GitHub" in result

    def test_used_by_agents(self, tmp_repo):
        mcp_node = _make_node(
            "mcp",
            metadata={"project": {"name": "mcp-test"}, "fastmcp_config": {}},
            source_path="mcp/test-mcp/server.py",
        )
        agent_node = _make_node("agent", id="user-agent", description="Uses MCP")
        edge = CatalogEdge(from_id="agent:user-agent", to_id="mcp:test-mcp", relation="uses-mcp")
        result = render_mcp_page(mcp_node, [edge], [mcp_node, agent_node])
        assert "## Used By" in result
        assert "user-agent" in result


# ---------------------------------------------------------------------------
# read_raw_content
# ---------------------------------------------------------------------------


class TestReadRawContent:
    def test_reads_custom_from_disk(self, tmp_repo):
        skill_dir = tmp_repo / "skills" / "test-skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        raw = "---\nname: test-skill\n---\n\n# Body\n"
        (skill_dir / "SKILL.md").write_text(raw)
        node = _make_node("skill")
        assert read_raw_content(node) == raw

    def test_fallback_when_file_missing(self, tmp_repo):
        node = _make_node("skill", metadata={"name": "test-skill"}, body="# Fallback body")
        result = read_raw_content(node)
        assert "---" in result
        assert "Fallback body" in result


# ---------------------------------------------------------------------------
# scaffold_doc_page
# ---------------------------------------------------------------------------


class TestScaffoldDocPage:
    def test_creates_page_when_content_dir_exists(self, tmp_repo):
        content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
        content_dir.mkdir(parents=True, exist_ok=True)
        skill_dir = tmp_repo / "skills" / "test-skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text("---\nname: test-skill\ndescription: Test\n---\n\n# X\n\nBody.\n")
        node = _make_node("skill")
        scaffold_doc_page(node)
        assert (content_dir / "skills" / "test-skill.mdx").exists()

    def test_noop_when_content_dir_missing(self, tmp_repo):
        node = _make_node("skill")
        scaffold_doc_page(node)  # Should not raise
