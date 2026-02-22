"""Tests for wagents.docs — index pages, sidebar, and docs subcommands."""

from wagents.catalog import CatalogNode
from wagents.docs import (
    write_agents_index,
    write_cli_page,
    write_index_page,
    write_mcp_index,
    write_sidebar,
    write_skills_index,
)


def _make_node(kind, id_suffix="test", **overrides):
    defaults = {
        "kind": kind,
        "id": f"{id_suffix}-{kind}" if kind != "mcp" else id_suffix,
        "title": f"Test {kind.title()}",
        "description": f"A test {kind} description",
        "metadata": {"name": f"{id_suffix}-{kind}"},
        "body": f"# Test\n\nBody for {kind}.",
        "source_path": f"skills/{id_suffix}-{kind}/SKILL.md",
        "source": "custom",
    }
    defaults.update(overrides)
    return CatalogNode(**defaults)


# ---------------------------------------------------------------------------
# write_index_page
# ---------------------------------------------------------------------------


class TestWriteIndexPage:
    def test_creates_index_file(self, tmp_repo):
        content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
        content_dir.mkdir(parents=True, exist_ok=True)
        nodes = [
            _make_node("skill"),
            _make_node("agent", source_path="agents/test-agent.md"),
            _make_node(
                "mcp",
                id_suffix="test-mcp",
                metadata={"project": {}},
                source_path="mcp/test-mcp/server.py",
            ),
        ]
        write_index_page(nodes)
        idx = content_dir / "index.mdx"
        assert idx.exists()
        text = idx.read_text()
        assert "template: splash" in text
        assert "Featured Skills" in text
        assert "Agents" in text
        assert "MCP Servers" in text

    def test_no_skills_no_featured_section(self, tmp_repo):
        content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
        content_dir.mkdir(parents=True, exist_ok=True)
        write_index_page([])
        text = (content_dir / "index.mdx").read_text()
        assert "Featured Skills" not in text
        # "## Agents" section shouldn't appear (title: Agents is the page title)
        assert "## Agents" not in text

    def test_stats_bar_with_installed(self, tmp_repo):
        content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
        content_dir.mkdir(parents=True, exist_ok=True)
        nodes = [
            _make_node("skill"),
            _make_node("skill", id_suffix="installed", source="installed"),
        ]
        write_index_page(nodes)
        text = (content_dir / "index.mdx").read_text()
        assert "Custom Skills" in text
        assert "Installed Skills" in text


# ---------------------------------------------------------------------------
# write_cli_page
# ---------------------------------------------------------------------------


class TestWriteCliPage:
    def test_creates_cli_page(self, tmp_repo):
        content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
        content_dir.mkdir(parents=True, exist_ok=True)
        write_cli_page()
        cli_page = content_dir / "cli.mdx"
        assert cli_page.exists()
        text = cli_page.read_text()
        assert "CLI Reference" in text
        assert "wagents new skill" in text
        assert "<FileTree>" in text


# ---------------------------------------------------------------------------
# write_skills_index
# ---------------------------------------------------------------------------


class TestWriteSkillsIndex:
    def test_creates_skills_index(self, tmp_repo):
        content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
        content_dir.mkdir(parents=True, exist_ok=True)
        nodes = [_make_node("skill")]
        write_skills_index(nodes)
        idx = content_dir / "skills" / "index.mdx"
        assert idx.exists()
        text = idx.read_text()
        assert "User-Invocable (1)" in text

    def test_installed_skills_section(self, tmp_repo):
        content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
        content_dir.mkdir(parents=True, exist_ok=True)
        nodes = [
            _make_node("skill"),
            _make_node("skill", id_suffix="ext", source="installed"),
        ]
        write_skills_index(nodes)
        text = (content_dir / "skills" / "index.mdx").read_text()
        assert "Installed Skills (1)" in text


# ---------------------------------------------------------------------------
# write_agents_index
# ---------------------------------------------------------------------------


class TestWriteAgentsIndex:
    def test_creates_agents_index(self, tmp_repo):
        content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
        content_dir.mkdir(parents=True, exist_ok=True)
        nodes = [_make_node("agent", source_path="agents/test-agent.md")]
        write_agents_index(nodes)
        idx = content_dir / "agents" / "index.mdx"
        assert idx.exists()
        text = idx.read_text()
        assert "1 agents available" in text


# ---------------------------------------------------------------------------
# write_mcp_index
# ---------------------------------------------------------------------------


class TestWriteMcpIndex:
    def test_creates_mcp_index(self, tmp_repo):
        content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
        content_dir.mkdir(parents=True, exist_ok=True)
        nodes = [
            _make_node(
                "mcp",
                id_suffix="test-mcp",
                metadata={"project": {}},
                source_path="mcp/test-mcp/server.py",
            )
        ]
        write_mcp_index(nodes)
        idx = content_dir / "mcp" / "index.mdx"
        assert idx.exists()
        text = idx.read_text()
        assert "1 MCP servers available" in text


# ---------------------------------------------------------------------------
# write_sidebar
# ---------------------------------------------------------------------------


class TestWriteSidebar:
    def test_creates_sidebar_file(self, tmp_repo):
        docs_src = tmp_repo / "docs" / "src"
        docs_src.mkdir(parents=True, exist_ok=True)
        nodes = [
            _make_node("skill"),
            _make_node("agent", source_path="agents/test-agent.md"),
        ]
        write_sidebar(nodes)
        sidebar = docs_src / "generated-sidebar.mjs"
        assert sidebar.exists()
        text = sidebar.read_text()
        assert "navLinks" in text
        assert "Skills" in text
        assert "Agents" in text
        assert "CLI Reference" in text

    def test_sidebar_without_agents_or_mcp(self, tmp_repo):
        docs_src = tmp_repo / "docs" / "src"
        docs_src.mkdir(parents=True, exist_ok=True)
        nodes = [_make_node("skill")]
        write_sidebar(nodes)
        text = (docs_src / "generated-sidebar.mjs").read_text()
        assert "Skills" in text
        # No agents or mcp sections
        assert "Agents" not in text or "autogenerate" not in text

    def test_sidebar_with_guides(self, tmp_repo):
        content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
        guides_dir = content_dir / "guides"
        guides_dir.mkdir(parents=True, exist_ok=True)
        (guides_dir / "my-guide.mdx").write_text("---\ntitle: Guide\n---\n")
        write_sidebar([_make_node("skill")])
        text = (tmp_repo / "docs" / "src" / "generated-sidebar.mjs").read_text()
        assert "Guides" in text
        assert "my-guide" in text
