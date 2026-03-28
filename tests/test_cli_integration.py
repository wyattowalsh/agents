"""Integration tests for the wagents CLI via typer.testing.CliRunner."""

import json

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


def test_validate_json_success(patched_repo):
    """Validate should emit structured JSON on success."""
    result = runner.invoke(app, ["validate", "--format", "json"])
    assert result.exit_code == 0, f"validate json failed:\n{result.output}"
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["error_count"] == 0
    assert payload["errors"] == []


def test_validate_jsonl_failure(patched_repo):
    """Validate should emit error and summary records in jsonl mode."""
    bad_skill_dir = patched_repo / "skills" / "bad-skill"
    bad_skill_dir.mkdir()
    (bad_skill_dir / "SKILL.md").write_text("---\ndescription: Missing the name field\n---\n\n# Bad Skill\n\nBody.\n")

    result = runner.invoke(app, ["validate", "--format", "jsonl"])
    assert result.exit_code == 1, "validate jsonl should fail for invalid input"
    records = [json.loads(line) for line in result.output.strip().splitlines()]
    assert records[0]["type"] == "error"
    assert records[0]["source"].endswith("bad-skill/SKILL.md")
    assert records[-1]["type"] == "summary"
    assert records[-1]["ok"] is False


def test_doctor_json_success(patched_repo, monkeypatch):
    """Doctor should emit structured JSON with successful checks when the environment is healthy."""
    (patched_repo / "pyproject.toml").write_text('[project]\nname = "wagents"\nrequires-python = ">=3.13"\n')
    docs_dir = patched_repo / "docs"
    docs_dir.mkdir()
    (docs_dir / "package.json").write_text("{}\n")
    (docs_dir / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
    node_modules = docs_dir / "node_modules"
    node_modules.mkdir()

    home_dir = patched_repo / "fake-home"
    browser_cache = home_dir / "Library/Caches/ms-playwright/chromium-1234"
    browser_cache.mkdir(parents=True)
    monkeypatch.setattr("wagents.cli.Path.home", lambda: home_dir)
    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr("importlib.util.find_spec", lambda name: object() if name == "playwright" else None)

    result = runner.invoke(app, ["doctor", "--format", "json"])
    assert result.exit_code == 0, f"doctor json failed:\n{result.output}"
    payload = json.loads(result.output)
    assert payload["ok"] is True
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["python-version"]["status"] == "ok"
    assert checks["uv"]["status"] == "ok"
    assert checks["docs-deps"]["status"] == "ok"
    assert checks["playwright-browsers"]["status"] == "ok"


def test_doctor_jsonl_failure_and_warnings(patched_repo, monkeypatch):
    """Doctor should surface failures and warnings with summary records in jsonl mode."""
    (patched_repo / "pyproject.toml").write_text('[project]\nname = "wagents"\nrequires-python = ">=3.13"\n')
    docs_dir = patched_repo / "docs"
    docs_dir.mkdir()
    (docs_dir / "package.json").write_text("{}\n")
    (docs_dir / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")

    monkeypatch.setattr("shutil.which", lambda name: None if name == "uv" else f"/usr/bin/{name}")
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    monkeypatch.setattr("wagents.cli.Path.home", lambda: patched_repo / "fake-home")

    result = runner.invoke(app, ["doctor", "--format", "jsonl"])
    assert result.exit_code == 1, "doctor should fail when required checks fail"
    records = [json.loads(line) for line in result.output.strip().splitlines()]
    checks = {record["name"]: record for record in records if record["type"] == "check"}
    assert checks["uv"]["status"] == "fail"
    assert checks["docs-deps"]["status"] == "warn"
    assert checks["playwright-python"]["status"] == "warn"
    assert records[-1]["type"] == "summary"
    assert records[-1]["ok"] is False


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


# ---------------------------------------------------------------------------
# 7. wagents package --dry-run — real repo
# ---------------------------------------------------------------------------


def test_package_dry_run_real_repo():
    """Package --all --dry-run against the real repo should succeed."""
    result = runner.invoke(app, ["package", "--all", "--dry-run"])
    assert result.exit_code == 0, f"package --all --dry-run failed:\n{result.output}"


# ---------------------------------------------------------------------------
# 8. wagents install — command construction
# ---------------------------------------------------------------------------


class TestInstall:
    def test_install_list_constructs_correct_command(self, monkeypatch):
        """Install --list should pass --list to npx skills add."""
        import subprocess

        calls = []

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)

        monkeypatch.setattr("subprocess.run", mock_run)
        result = runner.invoke(app, ["install", "--list"])
        assert result.exit_code == 0
        assert calls, "subprocess.run was not called"
        assert "--list" in calls[0]
        assert "wyattowalsh/agents" in calls[0]

    def test_install_all_default(self, monkeypatch):
        """Install with no args installs all skills to all agents globally."""
        import subprocess

        calls = []

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)

        monkeypatch.setattr("subprocess.run", mock_run)
        result = runner.invoke(app, ["install", "-y"])
        assert result.exit_code == 0
        cmd = calls[0]
        assert "--skill" in cmd and "*" in cmd
        assert "--agent" in cmd
        assert "-g" in cmd
        assert "-y" in cmd

    def test_install_specific_skills(self, monkeypatch):
        """Install with skill names passes --skill for each."""
        import subprocess

        calls = []

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)

        monkeypatch.setattr("subprocess.run", mock_run)
        result = runner.invoke(app, ["install", "honest-review", "wargame", "-y"])
        assert result.exit_code == 0
        cmd = calls[0]
        # Should have --skill honest-review --skill wargame
        skill_indices = [i for i, v in enumerate(cmd) if v == "--skill"]
        assert len(skill_indices) == 2
        skill_values = [cmd[i + 1] for i in skill_indices]
        assert "honest-review" in skill_values
        assert "wargame" in skill_values

    def test_install_specific_agent(self, monkeypatch):
        """Install -a claude-code targets only Claude."""
        import subprocess

        calls = []

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)

        monkeypatch.setattr("subprocess.run", mock_run)
        result = runner.invoke(app, ["install", "-a", "claude-code", "-y"])
        assert result.exit_code == 0
        cmd = calls[0]
        assert "-a" in cmd
        assert "claude-code" in cmd
        # Should NOT have --agent '*' since specific agent given
        assert cmd.count("--agent") == 0

    def test_install_local_flag(self, monkeypatch):
        """Install --local should not pass -g."""
        import subprocess

        calls = []

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)

        monkeypatch.setattr("subprocess.run", mock_run)
        result = runner.invoke(app, ["install", "--local", "-y"])
        assert result.exit_code == 0
        assert "-g" not in calls[0]

    def test_install_requires_npx(self, monkeypatch):
        """Install should fail gracefully when npx is not found."""

        monkeypatch.setattr("shutil.which", lambda x: None)
        result = runner.invoke(app, ["install"])
        assert result.exit_code == 1
        assert "npx not found" in result.output
