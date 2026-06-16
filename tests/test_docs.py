"""Tests for wagents.docs — index pages, sidebar, and docs subcommands."""

from wagents.catalog import CatalogNode
from wagents.docs import (
    docs_generate,
    write_agents_index,
    write_all_skills_index,
    write_cli_page,
    write_index_page,
    write_mcp_index,
    write_sidebar,
    write_skill_install_scripts_page,
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
        # Use featured skill IDs so the curated section renders
        nodes = [
            _make_node("skill", id="wargame"),
            _make_node("skill", id="honest-review"),
            _make_node("skill", id="skill-creator"),
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
        assert "CI status" in text
        assert "## Start Here" in text
        assert "## Visual Map" in text
        assert "catalogMeshArt.src" in text
        assert "## Popular Starting Points" in text
        assert 'title="Start Here"' in text
        assert "npx skills add github:wyattowalsh/agents --all -y -g" in text
        assert "OpenCode" in text
        assert "OpenSpec Workflow" in text
        assert "uv run wagents openspec doctor" in text

    def test_no_skills_no_featured_section(self, tmp_repo):
        content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
        content_dir.mkdir(parents=True, exist_ok=True)
        write_index_page([])
        text = (content_dir / "index.mdx").read_text()
        assert "## Popular Starting Points" in text
        assert "## How These Docs Work" in text
        assert "No bundled agent definitions were discovered" in text

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

    def test_skills_index_copy_is_repo_only_without_installed(self, tmp_repo):
        content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
        content_dir.mkdir(parents=True, exist_ok=True)
        write_index_page([_make_node("skill")])
        text = (content_dir / "index.mdx").read_text()
        assert "generated detail pages, and convention-skill context" in text
        assert "local agent directories" not in text

    def test_does_not_duplicate_mcp_overview_when_no_repo_mcp_nodes_exist(self, tmp_repo):
        content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
        mcp_dir = content_dir / "mcp"
        content_dir.mkdir(parents=True, exist_ok=True)
        mcp_dir.mkdir(parents=True, exist_ok=True)
        (mcp_dir / "index.mdx").write_text("---\ntitle: MCP\n---\n")
        (tmp_repo / "mcp.json").write_text('{"mcpServers": {"alpha": {}, "beta": {}}}')

        write_index_page([_make_node("skill")])

        text = (content_dir / "index.mdx").read_text()
        assert text.count('title="MCP Overview"') == 1
        assert "## MCP Servers" not in text


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
        assert "## Boot Sequence" in text
        assert "## Command Map" in text
        assert "wagents new skill" in text
        assert "uv run wagents doctor" in text
        assert "wagents hooks validate" in text
        assert "wagents eval coverage" in text
        assert "## Related Pages" in text
        assert "<FileTree>" in text
        assert "wagents docs generate --include-installed" in text
        assert "local agent skill directories" in text
        assert "~/.config/opencode/skills/" in text
        assert "wagents docs generate --no-installed" in text
        assert "Bundle Manifest" in text
        assert "current bundle surface and generated docs inputs" in text
        assert "wagents skills sync --apply" in text
        assert "wagents skills search" in text
        assert "wagents openspec doctor" in text
        assert "OPENSPEC_TELEMETRY=0" in text
        assert "On-Demand Skill Index" in text


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
        assert "User-Invocable Skills (1)" in text
        assert "## Skill Lanes" in text
        assert "/skills/catalog/test-skill/" in text
        assert "npx skills add github:wyattowalsh/agents --skill honest-review -y -g" in text

    def test_skills_index_is_custom_only(self, tmp_repo):
        content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
        content_dir.mkdir(parents=True, exist_ok=True)
        nodes = [
            _make_node("skill"),
            _make_node("skill", id_suffix="ext", source="installed"),
        ]
        write_skills_index(nodes)
        text = (content_dir / "skills" / "index.mdx").read_text()
        assert "Installed Skills (" not in text
        assert "ext-skill" not in text

    def test_all_skills_index_combines_custom_and_external(self, tmp_repo):
        content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
        content_dir.mkdir(parents=True, exist_ok=True)
        nodes = [_make_node("skill"), _make_node("skill", id_suffix="ext", source="installed")]
        write_all_skills_index(nodes)
        text = (content_dir / "skills" / "all.mdx").read_text()
        assert "/skills/catalog/test-skill/" in text
        assert "Curated External" in text

    def test_install_scripts_page_groups_commands(self, tmp_repo):
        content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
        content_dir.mkdir(parents=True, exist_ok=True)
        write_skill_install_scripts_page()
        text = (content_dir / "skills" / "install.mdx").read_text()
        assert "Skill Install Scripts" in text
        assert "canonical portable install path is `npx skills add`" in text
        assert '<InstallScripts src="/generated-skill-indexes/install-scripts.json" />' in text



class TestDocsGenerate:
    def test_excludes_installed_skills_by_default(self, tmp_repo, monkeypatch):
        custom = _make_node("skill")
        installed = _make_node("skill", id_suffix="ext", source="installed")

        monkeypatch.setattr(
            "wagents.docs.collect_all_doc_nodes",
            lambda **kwargs: [custom, installed] if kwargs.get("include_installed", True) else [custom],
        )
        monkeypatch.setattr("wagents.docs.collect_edges", lambda nodes: [])
        monkeypatch.setattr("wagents.docs.render_page", lambda node, edges, nodes: "---\ntitle: Test\n---\n")

        docs_generate()

        assert (tmp_repo / "docs" / "src" / "generated-visual-assets.css").exists()
        assert not (tmp_repo / "docs" / "src" / "content" / "docs" / "skills" / "catalog" / "ext-skill.mdx").exists()
        assert (tmp_repo / "docs" / "src" / "content" / "docs" / "skills" / "catalog" / "test-skill.mdx").exists()
        assert (tmp_repo / "docs" / "src" / "content" / "docs" / "skills" / "all.mdx").exists()
        assert (tmp_repo / "docs" / "src" / "content" / "docs" / "skills" / "install.mdx").exists()
        assert (tmp_repo / "docs" / "src" / "content" / "docs" / "harness-support.mdx").exists()

    def test_can_include_installed_skills_explicitly(self, tmp_repo, monkeypatch):
        custom = _make_node("skill")
        installed = _make_node("skill", id_suffix="ext", source="installed")

        monkeypatch.setattr(
            "wagents.docs.collect_all_doc_nodes",
            lambda **kwargs: [custom, installed] if kwargs.get("include_installed", False) else [custom],
        )
        monkeypatch.setattr("wagents.docs.collect_edges", lambda nodes: [])
        monkeypatch.setattr("wagents.docs.render_page", lambda node, edges, nodes: "---\ntitle: Test\n---\n")

        docs_generate(include_installed=True)

        assert (tmp_repo / "docs" / "src" / "content" / "docs" / "skills" / "catalog" / "ext-skill.mdx").exists()

    def test_can_exclude_installed_skills_explicitly(self, tmp_repo, monkeypatch):
        custom = _make_node("skill")
        installed = _make_node("skill", id_suffix="ext", source="installed")

        def _collect_all(**kwargs):
            return [custom, installed] if kwargs.get("include_installed", True) else [custom]

        monkeypatch.setattr("wagents.docs.collect_all_doc_nodes", _collect_all)
        monkeypatch.setattr("wagents.docs.collect_edges", lambda nodes: [])
        monkeypatch.setattr("wagents.docs.render_page", lambda node, edges, nodes: "---\ntitle: Test\n---\n")

        docs_generate(include_installed=False)

        assert not (tmp_repo / "docs" / "src" / "content" / "docs" / "skills" / "catalog" / "ext-skill.mdx").exists()
        assert (tmp_repo / "docs" / "src" / "content" / "docs" / "skills" / "catalog" / "test-skill.mdx").exists()

    def test_preserves_hand_maintained_skill_page(self, tmp_repo, monkeypatch):
        monkeypatch.setattr(
            "wagents.docs.collect_all_doc_nodes",
            lambda **kwargs: [_make_node("skill")],
        )
        monkeypatch.setattr("wagents.docs.collect_edges", lambda nodes: [])
        monkeypatch.setattr("wagents.docs.render_page", lambda node, edges, nodes: "---\ntitle: Replaced\n---\n")

        skill_page = tmp_repo / "docs" / "src" / "content" / "docs" / "skills" / "catalog" / "test-skill.mdx"
        skill_page.parent.mkdir(parents=True, exist_ok=True)
        preserved = "---\ntitle: Curated\n---\n\n{/* HAND-MAINTAINED */}\n\nCurated page.\n"
        skill_page.write_text(preserved)

        docs_generate(include_installed=False)

        assert skill_page.read_text() == preserved


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
        assert "Start Here" in text
        assert "Contributing" in text
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

    def test_sidebar_skills_collapsed(self, tmp_repo):
        write_sidebar([_make_node("skill")])
        text = (tmp_repo / "docs" / "src" / "generated-sidebar.mjs").read_text()
        assert "collapsed: true" in text
        assert "autogenerate: { directory: 'skills/catalog' }" in text


class TestSkillHubPages:
    def test_generated_skill_hubs_use_link_cards_not_skill_catalog(self, tmp_repo):
        content_dir = tmp_repo / "docs" / "src" / "content" / "docs"
        content_dir.mkdir(parents=True, exist_ok=True)
        nodes = [_make_node("skill")]
        write_skills_index(nodes)
        write_all_skills_index(nodes)

        for name in ("index.mdx", "all.mdx"):
            text = (content_dir / "skills" / name).read_text()
            assert "SkillCatalog" not in text
            assert "LinkCard" in text
            assert "/skills/catalog/" in text


class TestResearchCoverageTypes:
    def test_all_includes_installed_when_requested(self):
        from wagents.docs import _research_coverage_types

        assert _research_coverage_types("all", include_installed=True) == [
            "custom",
            "curated-external",
            "installed",
        ]

    def test_all_omits_installed_when_disabled(self):
        from wagents.docs import _research_coverage_types

        assert _research_coverage_types("all", include_installed=False) == [
            "custom",
            "curated-external",
        ]

    def test_single_source_type_passthrough(self):
        from wagents.docs import _research_coverage_types

        assert _research_coverage_types("custom", include_installed=True) == ["custom"]


class TestDocsResearchCommand:
    def test_research_skill_filter(self, monkeypatch):
        from typer.testing import CliRunner

        from wagents.cli import app
        from wagents.skill_docs import SkillDocNode

        node = SkillDocNode(
            node=_make_node("skill", id="alpha"),
            source_type="custom",
        )

        monkeypatch.setattr("wagents.docs.collect_skill_doc_nodes", lambda **kwargs: [node])
        monkeypatch.setattr("wagents.docs.research_coverage", lambda *args, **kwargs: (0, 1))
        monkeypatch.setattr("wagents.docs.update_research_manifest", lambda: None)

        runner = CliRunner()
        result = runner.invoke(app, ["docs", "research", "--skill", "alpha", "--dry-run", "--no-installed"])

        assert result.exit_code == 0
        assert "Batch 1: 1 skills — alpha" in result.output

    def test_check_research_exits_when_incomplete(self, monkeypatch):
        from typer.testing import CliRunner

        from wagents.cli import app
        from wagents.skill_docs import SkillDocNode

        node = SkillDocNode(
            node=_make_node("skill", id="alpha"),
            source_type="custom",
        )

        monkeypatch.setattr("wagents.docs.collect_skill_doc_nodes", lambda **kwargs: [node])
        monkeypatch.setattr("wagents.docs.research_coverage", lambda *args, **kwargs: (0, 1))

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["docs", "research", "--check-research", "--source-type", "custom", "--dry-run", "--no-installed"],
        )

        assert result.exit_code == 1
        assert "research cache incomplete" in result.output

    def test_check_research_all_validates_each_source_type(self, monkeypatch):
        from typer.testing import CliRunner

        from wagents.cli import app
        from wagents.skill_docs import SkillDocNode

        node = SkillDocNode(
            node=_make_node("skill", id="alpha"),
            source_type="custom",
        )

        def fake_coverage(doc_nodes, *, source_type: str):
            if source_type == "curated-external":
                return 0, 1
            return 1, 1

        monkeypatch.setattr("wagents.docs.collect_skill_doc_nodes", lambda **kwargs: [node])
        monkeypatch.setattr("wagents.docs.research_coverage", fake_coverage)

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "docs",
                "research",
                "--check-research",
                "--source-type",
                "all",
                "--dry-run",
                "--no-installed",
            ],
        )

        assert result.exit_code == 1
        assert "research cache incomplete for curated-external" in result.output
        assert "Research cache coverage (custom):" in result.output
        assert "Research cache coverage (curated-external):" in result.output
