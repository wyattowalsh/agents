"""CLI failure-path tests — exit codes and actionable errors on bad input."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wagents.cli import app

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATE_REPO = REPO_ROOT / "scripts" / "validate" / "validate_repo.py"


def _run_validate_repo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATE_REPO), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class TestTyperFailurePaths:
    def test_unknown_top_level_command_exits_nonzero(self) -> None:
        result = runner.invoke(app, ["no-such-command"])
        assert result.exit_code != 0
        assert "No such command" in result.output

    def test_new_skill_invalid_name_exits_one(self, patched_repo) -> None:
        result = runner.invoke(app, ["new", "skill", "BadName", "--no-docs"])
        assert result.exit_code == 1
        assert "kebab-case" in result.output

    def test_new_agent_invalid_name_exits_one(self, patched_repo) -> None:
        result = runner.invoke(app, ["new", "agent", "Bad_Agent", "--no-docs"])
        assert result.exit_code == 1
        assert "kebab-case" in result.output

    def test_new_mcp_invalid_name_exits_one(self, patched_repo) -> None:
        result = runner.invoke(app, ["new", "mcp", "BadMcp"])
        assert result.exit_code == 1
        assert "kebab-case" in result.output

    def test_validate_unknown_format_via_cli(self, patched_repo) -> None:
        bad_skill = patched_repo / "skills" / "bad-skill"
        bad_skill.mkdir()
        (bad_skill / "SKILL.md").write_text(
            "---\ndescription: missing name\n---\n\n# Bad\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["validate", "--format", "sarif"])
        assert result.exit_code == 1
        payload = json.loads(result.output)
        assert payload["version"] == "2.1.0"
        assert payload["runs"][0]["results"]


class TestValidateRepoFailurePaths:
    def test_invalid_format_choice_exits_two(self) -> None:
        result = _run_validate_repo("--format", "bogus")
        assert result.returncode == 2
        assert "invalid choice" in result.stderr

    def test_sarif_success_shape(self, tmp_path: Path) -> None:
        (tmp_path / "skills").mkdir()
        (tmp_path / "agents").mkdir()
        (tmp_path / "mcp").mkdir()
        result = _run_validate_repo("--format", "sarif", "--repo-root", str(tmp_path))
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["version"] == "2.1.0"
        assert payload["runs"][0]["results"] == []

    def test_sarif_failure_includes_results(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "skills" / "broken"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\ndescription: missing name\n---\n\nBody.\n",
            encoding="utf-8",
        )
        (tmp_path / "agents").mkdir()
        (tmp_path / "mcp").mkdir()
        result = _run_validate_repo("--format", "sarif", "--repo-root", str(tmp_path))
        assert result.returncode == 1
        payload = json.loads(result.stdout)
        assert len(payload["runs"][0]["results"]) >= 1
        assert payload["runs"][0]["results"][0]["ruleId"] == "asset-validation"


@pytest.fixture
def patched_repo(tmp_path, monkeypatch):
    """Minimal repo skeleton with validate script dependencies."""
    import shutil

    for mod in ["wagents", "wagents.cli", "wagents.catalog", "wagents.rendering"]:
        monkeypatch.setattr(f"{mod}.ROOT", tmp_path)
    monkeypatch.setattr("wagents.rendering.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr("wagents.docs.ROOT", tmp_path)
    monkeypatch.setattr("wagents.docs.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.docs.DOCS_DIR", tmp_path / "docs")
    (tmp_path / "skills").mkdir()
    (tmp_path / "agents").mkdir()
    (tmp_path / "mcp").mkdir()
    pyproject = '[project]\nname = "wagents"\nrequires-python = ">=3.13"\n'
    (tmp_path / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    shutil.copytree(REPO_ROOT / "scripts" / "validate", tmp_path / "scripts" / "validate")
    shutil.copytree(REPO_ROOT / "skills" / "skill-creator", tmp_path / "skills" / "skill-creator")
    shutil.copytree(REPO_ROOT / "wagents", tmp_path / "wagents")
    (tmp_path / "config").mkdir(exist_ok=True)
    for rel in (
        "config/mcp-registry.json",
        "config/sync-manifest.json",
        "config/tooling-policy.json",
        "config/harness-surface-registry.json",
        "planning/manifests/security-quarantine-register.json",
        "AGENTS.md",
    ):
        src = REPO_ROOT / rel
        if src.is_file():
            dest = tmp_path / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    monkeypatch.setenv("WAGENTS_REPO_ROOT", str(tmp_path))
    return tmp_path
