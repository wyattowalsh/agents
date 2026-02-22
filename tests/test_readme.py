"""Tests for the `wagents readme` CLI command."""

from typer.testing import CliRunner

from wagents.cli import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# README generation
# ---------------------------------------------------------------------------


def test_readme_contains_skills_table(tmp_repo):
    """Generated README contains a ## Skills table when a skill exists."""
    skill_dir = tmp_repo / "skills" / "hello-world"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: hello-world\ndescription: Greets the world\n---\n\n# Hello World\n\nBody.\n"
    )

    # Also create a minimal pyproject.toml so the readme command can work
    (tmp_repo / "pyproject.toml").write_text('[project]\nname = "wagents"\nversion = "0.1.0"\n')

    result = runner.invoke(app, ["readme"])
    assert result.exit_code == 0, result.output

    readme_text = (tmp_repo / "README.md").read_text()
    assert "## Skills" in readme_text
    assert "hello-world" in readme_text
    assert "Greets the world" in readme_text


# ---------------------------------------------------------------------------
# --check mode: up to date
# ---------------------------------------------------------------------------


def test_readme_check_passes_when_up_to_date(tmp_repo):
    """--check exits 0 when README matches generated content."""
    skill_dir = tmp_repo / "skills" / "alpha"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: alpha\ndescription: First skill\n---\n\n# Alpha\n\nBody.\n")

    (tmp_repo / "pyproject.toml").write_text('[project]\nname = "wagents"\nversion = "0.1.0"\n')

    # Generate the README first
    gen_result = runner.invoke(app, ["readme"])
    assert gen_result.exit_code == 0, gen_result.output

    # Now check — should pass
    check_result = runner.invoke(app, ["readme", "--check"])
    assert check_result.exit_code == 0, check_result.output
    assert "up to date" in check_result.output


# ---------------------------------------------------------------------------
# --check mode: stale
# ---------------------------------------------------------------------------


def test_readme_check_fails_when_stale(tmp_repo):
    """--check exits 1 when README does not match generated content."""
    skill_dir = tmp_repo / "skills" / "beta"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: beta\ndescription: Second skill\n---\n\n# Beta\n\nBody.\n")

    (tmp_repo / "pyproject.toml").write_text('[project]\nname = "wagents"\nversion = "0.1.0"\n')

    # Generate the README
    gen_result = runner.invoke(app, ["readme"])
    assert gen_result.exit_code == 0, gen_result.output

    # Tamper with it
    readme_file = tmp_repo / "README.md"
    readme_file.write_text("# stale content\n")

    # Now check — should fail
    check_result = runner.invoke(app, ["readme", "--check"])
    assert check_result.exit_code == 1
    assert "stale" in check_result.output.lower()


# ---------------------------------------------------------------------------
# Empty repo — no skills, agents, or MCP
# ---------------------------------------------------------------------------


def test_readme_empty_repo_produces_valid_output(tmp_repo):
    """An empty repo (no skills/agents/mcp) still produces a valid README."""
    (tmp_repo / "pyproject.toml").write_text('[project]\nname = "wagents"\nversion = "0.1.0"\n')

    result = runner.invoke(app, ["readme"])
    assert result.exit_code == 0, result.output

    readme_text = (tmp_repo / "README.md").read_text()
    # Should NOT contain asset sections since directories are empty
    assert "## Skills" not in readme_text
    assert "## Agents" not in readme_text
    assert "## MCP Servers" not in readme_text
    # But should still contain structural sections
    assert "# agents" in readme_text
    assert "## Development" in readme_text
    assert "## License" in readme_text
