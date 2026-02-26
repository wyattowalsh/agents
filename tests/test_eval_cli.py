"""Tests for wagents eval CLI commands."""

import json

import pytest
from typer.testing import CliRunner

from wagents.cli import app

runner = CliRunner()


@pytest.fixture
def patched_repo(tmp_path, monkeypatch):
    """Create a minimal repo skeleton in tmp_path and monkeypatch all ROOT refs."""
    for mod in ["wagents", "wagents.cli", "wagents.catalog", "wagents.rendering"]:
        monkeypatch.setattr(f"{mod}.ROOT", tmp_path)
    monkeypatch.setattr("wagents.rendering.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr("wagents.docs.ROOT", tmp_path)
    monkeypatch.setattr("wagents.docs.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.docs.DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr("wagents.catalog.RELATED_SKILLS", {})
    monkeypatch.setattr("wagents.cli.RELATED_SKILLS", {})
    (tmp_path / "skills").mkdir()
    (tmp_path / "agents").mkdir()
    (tmp_path / "mcp").mkdir()
    (tmp_path / ".claude").mkdir()
    return tmp_path


def _make_skill_with_eval(repo, name, eval_data):
    """Helper: create a minimal skill with an eval file."""
    skill_dir = repo / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Test skill\n---\n\n# {name}\n\nBody.\n")
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir(exist_ok=True)
    (evals_dir / "test.json").write_text(json.dumps(eval_data, indent=2))


class TestEvalList:
    def test_no_evals(self, patched_repo):
        result = runner.invoke(app, ["eval", "list"])
        assert result.exit_code == 0
        assert "No evals found" in result.output

    def test_with_evals(self, patched_repo):
        _make_skill_with_eval(
            patched_repo,
            "test-skill",
            {
                "skills": ["test-skill"],
                "query": "/test-skill hello",
                "expected_behavior": ["Says hello"],
            },
        )
        result = runner.invoke(app, ["eval", "list"])
        assert result.exit_code == 0
        assert "test-skill" in result.output
        assert "1" in result.output

    @staticmethod
    def test_real_repo():
        """List evals from the actual repo."""
        result = runner.invoke(app, ["eval", "list"])
        assert result.exit_code == 0
        assert "skill-creator" in result.output


class TestEvalValidate:
    def test_valid_eval(self, patched_repo):
        _make_skill_with_eval(
            patched_repo,
            "test-skill",
            {
                "skills": ["test-skill"],
                "query": "/test-skill hello",
                "expected_behavior": ["Says hello"],
            },
        )
        result = runner.invoke(app, ["eval", "validate"])
        assert result.exit_code == 0
        assert "All evals valid" in result.output

    def test_missing_skills_field(self, patched_repo):
        _make_skill_with_eval(
            patched_repo,
            "test-skill",
            {
                "query": "/test-skill hello",
                "expected_behavior": ["Says hello"],
            },
        )
        result = runner.invoke(app, ["eval", "validate"])
        assert result.exit_code == 1
        assert "missing required field 'skills'" in result.output

    def test_missing_query_field(self, patched_repo):
        _make_skill_with_eval(
            patched_repo,
            "test-skill",
            {
                "skills": ["test-skill"],
                "expected_behavior": ["Says hello"],
            },
        )
        result = runner.invoke(app, ["eval", "validate"])
        assert result.exit_code == 1
        assert "missing required field 'query'" in result.output

    def test_missing_expected_behavior(self, patched_repo):
        _make_skill_with_eval(
            patched_repo,
            "test-skill",
            {
                "skills": ["test-skill"],
                "query": "/test-skill hello",
            },
        )
        result = runner.invoke(app, ["eval", "validate"])
        assert result.exit_code == 1
        assert "missing required field 'expected_behavior'" in result.output

    def test_empty_expected_behavior(self, patched_repo):
        _make_skill_with_eval(
            patched_repo,
            "test-skill",
            {
                "skills": ["test-skill"],
                "query": "/test-skill hello",
                "expected_behavior": [],
            },
        )
        result = runner.invoke(app, ["eval", "validate"])
        assert result.exit_code == 1
        assert "expected_behavior" in result.output

    def test_nonexistent_skill_reference(self, patched_repo):
        _make_skill_with_eval(
            patched_repo,
            "test-skill",
            {
                "skills": ["nonexistent-skill"],
                "query": "/nonexistent-skill hello",
                "expected_behavior": ["Does something"],
            },
        )
        result = runner.invoke(app, ["eval", "validate"])
        assert result.exit_code == 1
        assert "nonexistent-skill" in result.output

    def test_invalid_json(self, patched_repo):
        skill_dir = patched_repo / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: test-skill\ndescription: Test\n---\n\n# Test\n\nBody.\n")
        evals_dir = skill_dir / "evals"
        evals_dir.mkdir()
        (evals_dir / "bad.json").write_text("{invalid json")
        result = runner.invoke(app, ["eval", "validate"])
        assert result.exit_code == 1

    @staticmethod
    def test_real_repo():
        """Validate evals from the actual repo."""
        result = runner.invoke(app, ["eval", "validate"])
        assert result.exit_code == 0
        assert "All evals valid" in result.output


class TestEvalCoverage:
    def test_no_skills(self, patched_repo):
        result = runner.invoke(app, ["eval", "coverage"])
        assert result.exit_code == 0

    def test_mixed_coverage(self, patched_repo):
        # Skill with evals
        _make_skill_with_eval(
            patched_repo,
            "has-evals",
            {
                "skills": ["has-evals"],
                "query": "/has-evals test",
                "expected_behavior": ["Works"],
            },
        )
        # Skill without evals
        no_eval_dir = patched_repo / "skills" / "no-evals"
        no_eval_dir.mkdir(parents=True)
        (no_eval_dir / "SKILL.md").write_text(
            "---\nname: no-evals\ndescription: No evals\n---\n\n# No Evals\n\nBody.\n"
        )
        result = runner.invoke(app, ["eval", "coverage"])
        assert result.exit_code == 0
        assert "has-evals" in result.output
        assert "no-evals" in result.output
        assert "Yes" in result.output
        assert "No" in result.output
