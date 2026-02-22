"""Integration tests for the wagents CLI via typer.testing.CliRunner."""

import pytest
from typer.testing import CliRunner

from wagents.cli import app
from wagents.parsing import parse_frontmatter

runner = CliRunner()


# ---------------------------------------------------------------------------
# Fixture: patched_repo — redirects ROOT and related paths to tmp_path
# ---------------------------------------------------------------------------


@pytest.fixture
def patched_repo(tmp_path, monkeypatch):
    """Create a minimal repo skeleton in tmp_path and monkeypatch all ROOT refs."""
    for mod in ["wagents", "wagents.cli", "wagents.catalog", "wagents.rendering"]:
        monkeypatch.setattr(f"{mod}.ROOT", tmp_path)
    monkeypatch.setattr("wagents.rendering.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.DOCS_DIR", tmp_path / "docs")
    # Also patch docs.py which imports ROOT, CONTENT_DIR, DOCS_DIR at module level
    monkeypatch.setattr("wagents.docs.ROOT", tmp_path)
    monkeypatch.setattr("wagents.docs.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.docs.DOCS_DIR", tmp_path / "docs")
    # Empty RELATED_SKILLS so validate doesn't fail on missing skill dirs
    monkeypatch.setattr("wagents.catalog.RELATED_SKILLS", {})
    monkeypatch.setattr("wagents.cli.RELATED_SKILLS", {})
    (tmp_path / "skills").mkdir()
    (tmp_path / "agents").mkdir()
    (tmp_path / "mcp").mkdir()
    return tmp_path


# ---------------------------------------------------------------------------
# 1. wagents validate — real repo
# ---------------------------------------------------------------------------


def test_validate_real_repo():
    """Running validate against the actual repo should pass with exit code 0."""
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0, f"validate failed:\n{result.output}"
    assert "All validations passed" in result.output


# ---------------------------------------------------------------------------
# 2. wagents readme --check — real repo
# ---------------------------------------------------------------------------


def test_readme_check_real_repo():
    """Regenerate README then verify --check exits 0."""
    # First ensure README is current
    gen_result = runner.invoke(app, ["readme"])
    assert gen_result.exit_code == 0, f"readme generate failed:\n{gen_result.output}"

    # Now --check should confirm it's up to date
    check_result = runner.invoke(app, ["readme", "--check"])
    assert check_result.exit_code == 0, f"readme --check failed:\n{check_result.output}"
    assert "up to date" in check_result.output


# ---------------------------------------------------------------------------
# 3. wagents new skill — tmp_repo
# ---------------------------------------------------------------------------


def test_new_skill(patched_repo):
    """Create a skill in a tmp repo, verify file exists and has valid frontmatter."""
    result = runner.invoke(app, ["new", "skill", "tmp-test-skill", "--no-docs"])
    assert result.exit_code == 0, f"new skill failed:\n{result.output}"
    assert "Created skills/tmp-test-skill/SKILL.md" in result.output

    skill_file = patched_repo / "skills" / "tmp-test-skill" / "SKILL.md"
    assert skill_file.exists()

    content = skill_file.read_text()
    fm, body = parse_frontmatter(content)
    assert fm["name"] == "tmp-test-skill"
    assert "description" in fm
    assert body  # body should be non-empty


# ---------------------------------------------------------------------------
# 4. wagents new agent — tmp_repo
# ---------------------------------------------------------------------------


def test_new_agent(patched_repo):
    """Create an agent in a tmp repo, verify file exists and has valid frontmatter."""
    result = runner.invoke(app, ["new", "agent", "tmp-test-agent", "--no-docs"])
    assert result.exit_code == 0, f"new agent failed:\n{result.output}"
    assert "Created agents/tmp-test-agent.md" in result.output

    agent_file = patched_repo / "agents" / "tmp-test-agent.md"
    assert agent_file.exists()

    content = agent_file.read_text()
    fm, body = parse_frontmatter(content)
    assert fm["name"] == "tmp-test-agent"
    assert "description" in fm


# ---------------------------------------------------------------------------
# 5. wagents new mcp — tmp_repo
# ---------------------------------------------------------------------------


def test_new_mcp(patched_repo):
    """Create an MCP server in a tmp repo, verify all 3 files are scaffolded."""
    # new mcp reads root pyproject.toml to check workspace config
    pyproject = patched_repo / "pyproject.toml"
    pyproject.write_text('[tool.uv.workspace]\nmembers = ["mcp/*"]\n')

    result = runner.invoke(app, ["new", "mcp", "tmp-test-mcp", "--no-docs"])
    assert result.exit_code == 0, f"new mcp failed:\n{result.output}"

    mcp_dir = patched_repo / "mcp" / "tmp-test-mcp"
    assert mcp_dir.is_dir()
    assert (mcp_dir / "server.py").exists()
    assert (mcp_dir / "pyproject.toml").exists()
    assert (mcp_dir / "fastmcp.json").exists()
    assert len(list(mcp_dir.iterdir())) == 3


# ---------------------------------------------------------------------------
# 6. wagents validate with invalid skill — exit code 1
# ---------------------------------------------------------------------------


def test_validate_invalid_skill(patched_repo):
    """A skill missing the required 'name' field should cause validate to fail."""
    bad_skill_dir = patched_repo / "skills" / "bad-skill"
    bad_skill_dir.mkdir()
    (bad_skill_dir / "SKILL.md").write_text("---\ndescription: Missing the name field\n---\n\n# Bad Skill\n\nBody.\n")

    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 1, f"validate should have failed:\n{result.output}"
