"""Integration tests for the wagents CLI via typer.testing.CliRunner."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wagents.cli import app
from wagents.installed_inventory import HarnessQueryResult, InstalledInventorySnapshot, InstalledSkillInventoryRow
from wagents.parsing import parse_frontmatter

runner = CliRunner()


# ---------------------------------------------------------------------------
# Fixture: patched_repo — redirects ROOT and related paths to tmp_path
# ---------------------------------------------------------------------------


REAL_REPO_ROOT = Path(__file__).resolve().parents[1]


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
    (tmp_path / "skills").mkdir()
    (tmp_path / "agents").mkdir()
    (tmp_path / "mcp").mkdir()
    pyproject = '[project]\nname = "wagents"\nrequires-python = ">=3.13"\n'
    (tmp_path / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    shutil.copytree(REAL_REPO_ROOT / "scripts" / "validate", tmp_path / "scripts" / "validate")
    shutil.copytree(REAL_REPO_ROOT / "skills" / "skill-creator", tmp_path / "skills" / "skill-creator")
    shutil.copytree(REAL_REPO_ROOT / "wagents", tmp_path / "wagents")
    (tmp_path / "config").mkdir(exist_ok=True)
    for rel in (
        "config/mcp-registry.json",
        "config/sync-manifest.json",
        "config/tooling-policy.json",
        "config/harness-surface-registry.json",
        "planning/manifests/security-quarantine-register.json",
        "AGENTS.md",
    ):
        src = REAL_REPO_ROOT / rel
        if src.is_file():
            dest = tmp_path / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    monkeypatch.setenv("WAGENTS_REPO_ROOT", str(tmp_path))
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


def test_validate_skips_gitignored_mcp_cache_dirs(patched_repo):
    """Validate should ignore local MCP cache directories excluded by git."""
    subprocess.run(["git", "init"], cwd=patched_repo, capture_output=True, check=False)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=patched_repo,
        capture_output=True,
        check=False,
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=patched_repo, capture_output=True, check=False)
    (patched_repo / ".gitignore").write_text("mcp/cache/\n")
    (patched_repo / "mcp" / "cache").mkdir()
    (patched_repo / "mcp" / "servers" / "missing-files").mkdir(parents=True)
    subprocess.run(["git", "add", ".gitignore"], cwd=patched_repo, capture_output=True, check=False)

    result = runner.invoke(app, ["validate"])

    assert result.exit_code == 0, f"validate failed:\n{result.output}"
    assert "All validations passed" in result.output


def test_doctor_json_success(patched_repo, monkeypatch):
    """Doctor should emit structured JSON with successful checks when the environment is healthy."""
    (patched_repo / "pyproject.toml").write_text(
        '[project]\nname = "wagents"\nrequires-python = ">=3.13"\n\n'
        "[tool.ruff]\nline-length = 120\n\n"
        '[tool.ty.src]\ninclude = ["wagents"]\n'
    )
    docs_dir = patched_repo / "docs"
    docs_dir.mkdir()
    (docs_dir / "package.json").write_text(
        json.dumps({"packageManager": "pnpm@10.11.1", "engines": {"node": "^22.0.0 || ^24.0.0"}})
    )
    (docs_dir / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
    node_modules = docs_dir / "node_modules"
    node_modules.mkdir()
    (patched_repo / ".pre-commit-config.yaml").write_text("repos: []\n")

    home_dir = patched_repo / "fake-home"
    browser_cache = home_dir / "Library/Caches/ms-playwright/chromium-1234"
    browser_cache.mkdir(parents=True)
    monkeypatch.setattr("wagents.cli.Path.home", lambda: home_dir)
    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr("importlib.util.find_spec", lambda name: object() if name == "playwright" else None)

    def _fake_subprocess_run(cmd, **kwargs):
        if cmd[:2] == ["uv", "run"] and len(cmd) >= 3:
            return subprocess.CompletedProcess(cmd, 0, stdout=f"{cmd[2]} 0.0.0\n", stderr="")
        return subprocess.CompletedProcess(
            cmd,
            0,
            stdout={"node": "v22.12.0\n", "pnpm": "10.11.1\n"}[cmd[0]],
            stderr="",
        )

    monkeypatch.setattr("wagents.cli.subprocess.run", _fake_subprocess_run)

    result = runner.invoke(app, ["doctor", "--format", "json"])
    assert result.exit_code == 0, f"doctor json failed:\n{result.output}"
    payload = json.loads(result.output)
    assert payload["ok"] is True
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["python-version"]["status"] == "ok"
    assert checks["uv"]["status"] == "ok"
    assert checks["node-version"]["status"] == "ok"
    assert checks["pnpm-version"]["status"] == "ok"
    assert checks["docs-deps"]["status"] == "ok"
    assert checks["pre-commit"]["status"] == "ok"
    assert checks["playwright-browsers"]["status"] == "ok"
    assert checks["python-tooling-config"]["status"] == "ok"
    assert checks["ruff-tooling"]["status"] == "ok"
    assert checks["ty-tooling"]["status"] == "ok"


def test_doctor_jsonl_failure_and_warnings(patched_repo, monkeypatch):
    """Doctor should surface failures and warnings with summary records in jsonl mode."""
    (patched_repo / "pyproject.toml").write_text('[project]\nname = "wagents"\nrequires-python = ">=3.13"\n')
    docs_dir = patched_repo / "docs"
    docs_dir.mkdir()
    (docs_dir / "package.json").write_text(
        json.dumps({"packageManager": "pnpm@10.11.1", "engines": {"node": "^22.0.0 || ^24.0.0"}})
    )
    (docs_dir / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
    (patched_repo / ".pre-commit-config.yaml").write_text("repos: []\n")

    monkeypatch.setattr("shutil.which", lambda name: None if name in {"uv", "pre-commit"} else f"/usr/bin/{name}")
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    monkeypatch.setattr("wagents.cli.Path.home", lambda: patched_repo / "fake-home")
    monkeypatch.setattr(
        "wagents.cli.subprocess.run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(
            cmd,
            0,
            stdout={"node": "v20.11.0\n", "pnpm": "10.10.0\n"}[cmd[0]],
            stderr="",
        ),
    )

    result = runner.invoke(app, ["doctor", "--format", "jsonl"])
    assert result.exit_code == 1, "doctor should fail when required checks fail"
    records = [json.loads(line) for line in result.output.strip().splitlines()]
    checks = {record["name"]: record for record in records if record["type"] == "check"}
    assert checks["uv"]["status"] == "fail"
    assert checks["node-version"]["status"] == "warn"
    assert checks["pnpm-version"]["status"] == "warn"
    assert checks["docs-deps"]["status"] == "warn"
    assert checks["pre-commit"]["status"] == "warn"
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
    fm, _body = parse_frontmatter(content)
    assert fm["name"] == "tmp-test-agent"
    assert "description" in fm


# ---------------------------------------------------------------------------
# 5. wagents new mcp — tmp_repo
# ---------------------------------------------------------------------------


def test_new_mcp(patched_repo):
    """Create an MCP server in a tmp repo, verify all 3 files are scaffolded."""
    # new mcp reads root pyproject.toml to check workspace config
    pyproject = patched_repo / "pyproject.toml"
    pyproject.write_text("[tool.uv.workspace]\nmembers = []\n")

    result = runner.invoke(app, ["new", "mcp", "tmp-test-mcp", "--no-docs"])
    assert result.exit_code == 0, f"new mcp failed:\n{result.output}"

    mcp_dir = patched_repo / "mcp" / "tmp-test-mcp"
    assert mcp_dir.is_dir()
    assert (mcp_dir / "server.py").exists()
    assert (mcp_dir / "pyproject.toml").exists()
    assert (mcp_dir / "fastmcp.json").exists()
    assert len(list(mcp_dir.iterdir())) == 3
    assert "Created mcp/tmp-test-mcp/" in result.output
    assert '"mcp/tmp-test-mcp"' in pyproject.read_text()

    (patched_repo / ".gitignore").write_text("/mcp/servers/*\n")
    (patched_repo / "mcp" / "servers" / "tmp-test-mcp").mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=patched_repo, check=True, capture_output=True)
    assert (
        subprocess.run(
            ["git", "check-ignore", "-q", "mcp/servers/tmp-test-mcp"],
            cwd=patched_repo,
            check=False,
        ).returncode
        == 0
    )
    assert (
        subprocess.run(
            ["git", "check-ignore", "-q", "mcp/tmp-test-mcp"],
            cwd=patched_repo,
            check=False,
        ).returncode
        != 0
    )


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


def _mock_npx_available(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda tool: "/usr/bin/npx" if tool == "npx" else None)


class TestInstall:
    def test_install_list_constructs_correct_command(self, monkeypatch):
        """Install --list should pass --list to npx skills add."""
        import subprocess

        calls = []

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)

        _mock_npx_available(monkeypatch)
        monkeypatch.setattr("subprocess.run", mock_run)
        result = runner.invoke(app, ["install", "--list"])
        assert result.exit_code == 0
        assert calls, "subprocess.run was not called"
        assert "--list" in calls[0]
        assert "github:wyattowalsh/agents" in calls[0]

    def test_install_all_default(self, monkeypatch):
        """Install with no args installs all skills to all agents globally."""
        import subprocess

        calls = []

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)

        _mock_npx_available(monkeypatch)
        monkeypatch.setattr("subprocess.run", mock_run)
        result = runner.invoke(app, ["install", "-y"])
        assert result.exit_code == 0
        cmd = calls[0]
        assert "--skill" in cmd
        assert "*" in cmd
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

        _mock_npx_available(monkeypatch)
        monkeypatch.setattr("subprocess.run", mock_run)
        result = runner.invoke(app, ["install", "review", "wargame", "-y"])
        assert result.exit_code == 0
        cmd = calls[0]
        # Should have --skill review --skill wargame
        skill_indices = [i for i, v in enumerate(cmd) if v == "--skill"]
        assert len(skill_indices) == 2
        skill_values = [cmd[i + 1] for i in skill_indices]
        assert "review" in skill_values
        assert "wargame" in skill_values

    def test_install_specific_agent(self, monkeypatch):
        """Install -a claude-code targets only Claude."""
        import subprocess

        calls = []

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)

        _mock_npx_available(monkeypatch)
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

        _mock_npx_available(monkeypatch)
        monkeypatch.setattr("subprocess.run", mock_run)
        result = runner.invoke(app, ["install", "--local", "-y"])
        assert result.exit_code == 0
        assert "-g" not in calls[0]

    def test_install_grok_uses_claude_adapter_and_mirrors(self, monkeypatch):
        import subprocess

        calls: list[list[str]] = []
        mirror_calls: list[object] = []

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)

        def mock_mirror():
            mirror_calls.append(True)
            return 2

        _mock_npx_available(monkeypatch)
        monkeypatch.setattr("subprocess.run", mock_run)
        monkeypatch.setattr("wagents.cli.mirror_grok_skills_from_claude", mock_mirror)

        result = runner.invoke(app, ["install", "review", "-a", "grok", "-y"])

        assert result.exit_code == 0
        assert calls[0].count("-a") >= 1
        assert "claude-code" in calls[0]
        assert "grok" not in calls[0]
        assert mirror_calls
        assert "Mirrored 2 skill(s)" in result.output

    def test_install_requires_npx(self, monkeypatch):
        """Install should fail gracefully when npx is not found."""

        monkeypatch.setattr("shutil.which", lambda x: None)
        result = runner.invoke(app, ["install"])
        assert result.exit_code == 1
        assert "npx not found" in result.output


class TestUpdate:
    def test_update_constructs_correct_command(self, monkeypatch):
        """Update should delegate to npx skills update."""
        import subprocess

        calls = []

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)

        _mock_npx_available(monkeypatch)
        monkeypatch.setattr("subprocess.run", mock_run)
        result = runner.invoke(app, ["update"])
        assert result.exit_code == 0
        assert calls == [["npx", "-y", "skills", "update"]]

    def test_update_requires_npx(self, monkeypatch):
        """Update should fail gracefully when npx is not found."""

        monkeypatch.setattr("shutil.which", lambda x: None)
        result = runner.invoke(app, ["update"])
        assert result.exit_code == 1
        assert "npx not found" in result.output


class TestSkillsSync:
    def _snapshot(self):
        return InstalledInventorySnapshot(
            rows=(
                InstalledSkillInventoryRow(
                    name="repo-skill",
                    path="/tmp/repo-skill",
                    source_path="/tmp/repo-skill/SKILL.md",
                    scope="global",
                    description="Repo skill",
                    license="",
                    version="",
                    author="",
                    source="github:wyattowalsh/agents",
                    install_source="github:wyattowalsh/agents",
                    source_url="https://github.com/wyattowalsh/agents",
                    install_command="npx skills add github:wyattowalsh/agents --skill repo-skill -y -g",
                    provenance_status="repo-owned",
                    trust_tier="repo",
                    selector_mode="named",
                    installed_agents=(),
                    discovered_in=("codex",),
                    target_agents=(),
                ),
                InstalledSkillInventoryRow(
                    name="curated-skill",
                    path="/tmp/curated-skill",
                    source_path="/tmp/curated-skill/SKILL.md",
                    scope="global",
                    description="Curated skill",
                    license="",
                    version="",
                    author="",
                    source="vercel-labs/agent-skills",
                    install_source="vercel-labs/agent-skills",
                    source_url="https://github.com/vercel-labs/agent-skills",
                    install_command="npx skills add vercel-labs/agent-skills --skill curated-skill -y -g",
                    provenance_status="verified-curated-external",
                    trust_tier="curated-trust-gated",
                    selector_mode="named",
                    installed_agents=("codex",),
                    discovered_in=("codex",),
                    target_agents=("codex",),
                ),
                InstalledSkillInventoryRow(
                    name="docs-stripe",
                    path="/tmp/docs-stripe",
                    source_path="/tmp/docs-stripe/SKILL.md",
                    scope="global",
                    description="Needs verification",
                    license="",
                    version="",
                    author="",
                    source="docs.stripe.com",
                    install_source="docs.stripe.com@stripe-best-practices",
                    source_url="https://docs.stripe.com",
                    install_command="",
                    provenance_status="curated-unresolved",
                    trust_tier="global-only-or-avoid",
                    selector_mode="unresolved",
                    installed_agents=(),
                    discovered_in=("codex",),
                    target_agents=("codex",),
                    unresolved_reason="registry syntax and provenance still need verification.",
                ),
                InstalledSkillInventoryRow(
                    name="one-off",
                    path="/tmp/one-off",
                    source_path="/tmp/one-off/SKILL.md",
                    scope="global",
                    description="Optional installed external skill",
                    license="",
                    version="",
                    author="",
                    source="example/skills",
                    install_source="example/skills",
                    source_url="https://github.com/example/skills",
                    install_command="npx skills add example/skills --skill one-off -y -g",
                    provenance_status="installed-external",
                    trust_tier="github",
                    selector_mode="named",
                    installed_agents=(),
                    discovered_in=("codex",),
                    target_agents=(),
                ),
            ),
            queries=(HarnessQueryResult(agent_id="codex", ok=True, entries=()),),
        )

    def _patch_sync_inventory(
        self,
        monkeypatch,
        snapshot: InstalledInventorySnapshot | None = None,
    ) -> InstalledInventorySnapshot:
        """Isolate sync tests from live external-skills desired rows."""
        resolved = snapshot if snapshot is not None else self._snapshot()
        monkeypatch.setattr("wagents.cli.collect_installed_inventory", lambda **kwargs: resolved)
        monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: ())
        return resolved

    def test_sync_dry_run_reports_categories_and_commands(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
        self._patch_sync_inventory(monkeypatch)

        result = runner.invoke(app, ["skills", "sync", "--agent", "codex"])

        assert result.exit_code == 0
        assert "missing (1)" in result.output
        assert "already-present (1)" in result.output
        assert "unresolved (1)" in result.output
        assert "skipped (1)" in result.output
        assert "npx skills add github:wyattowalsh/agents --skill repo-skill -y -g -a codex" in result.output

    def test_sync_dry_run_reports_inventory_fallback_warning(self, monkeypatch):
        base = self._snapshot()
        snapshot = InstalledInventorySnapshot(
            rows=base.rows,
            queries=(
                HarnessQueryResult(
                    agent_id="codex",
                    ok=True,
                    entries=(),
                    error="Fallback local skill-root inventory after timeout: npx skills ls",
                ),
            ),
        )
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
        self._patch_sync_inventory(monkeypatch, snapshot)

        result = runner.invoke(app, ["skills", "sync", "--agent", "codex"])

        assert result.exit_code == 0
        assert "warning: Fallback local skill-root inventory after timeout: npx skills ls" in result.output
        assert "missing (1)" in result.output

    def test_sync_apply_executes_verified_commands_only(self, monkeypatch):
        calls = []
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
        self._patch_sync_inventory(monkeypatch)

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)

        monkeypatch.setattr("subprocess.run", mock_run)

        result = runner.invoke(app, ["skills", "sync", "--agent", "codex", "--apply"])

        assert result.exit_code == 0
        assert calls == [
            ["npx", "skills", "add", "github:wyattowalsh/agents", "--skill", "repo-skill", "-y", "-g", "-a", "codex"]
        ]

    def test_sync_grok_uses_claude_code_adapter_and_mirrors(self, monkeypatch):
        calls: list[list[str]] = []
        mirror_calls: list[dict[str, object]] = []
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
        self._patch_sync_inventory(monkeypatch)

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)

        def mock_mirror(**kwargs):
            mirror_calls.append(kwargs)
            return 2

        monkeypatch.setattr("subprocess.run", mock_run)
        monkeypatch.setattr("wagents.cli.mirror_grok_skills_from_claude", mock_mirror)

        result = runner.invoke(app, ["skills", "sync", "--agent", "grok", "--apply"])

        assert result.exit_code == 0
        assert calls == [
            [
                "npx",
                "skills",
                "add",
                "github:wyattowalsh/agents",
                "--skill",
                "repo-skill",
                "-y",
                "-g",
                "-a",
                "claude-code",
            ]
        ]
        assert mirror_calls == [{}]
        assert "Mirrored 2 skill(s) into ~/.grok/skills" in result.output

    def test_sync_reports_zero_install_copilot_truthfully(self, monkeypatch):
        # Physically possible state: skill discovered in claude-code (installed
        # there), but github-copilot query returned nothing — so the skill is
        # genuinely missing from github-copilot.
        snapshot = InstalledInventorySnapshot(
            rows=(
                InstalledSkillInventoryRow(
                    name="repo-skill",
                    path="/tmp/repo-skill",
                    source_path="/tmp/repo-skill/SKILL.md",
                    scope="global",
                    description="Repo skill",
                    license="",
                    version="",
                    author="",
                    source="github:wyattowalsh/agents",
                    install_source="github:wyattowalsh/agents",
                    source_url="https://github.com/wyattowalsh/agents",
                    install_command="npx skills add github:wyattowalsh/agents --skill repo-skill -y -g",
                    provenance_status="repo-owned",
                    trust_tier="repo",
                    selector_mode="named",
                    installed_agents=("claude-code",),
                    discovered_in=("claude-code",),
                    target_agents=(),
                ),
            ),
            queries=(
                HarnessQueryResult(agent_id="claude-code", ok=True, entries=()),
                HarnessQueryResult(agent_id="github-copilot", ok=True, entries=()),
            ),
        )
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
        self._patch_sync_inventory(monkeypatch, snapshot)

        result = runner.invoke(app, ["skills", "sync", "--agent", "github-copilot"])

        assert result.exit_code == 0
        assert "[github-copilot]" in result.output
        assert "already-present (0)" in result.output
        assert "missing (1)" in result.output
        assert "npx skills add github:wyattowalsh/agents --skill repo-skill -y -g -a github-copilot" in result.output

    def test_targeted_sync_uses_full_cross_harness_inventory(self, monkeypatch):
        """Regression: --agent <id> must compare against the full inventory.

        Before the fix _build_sync_report called collect_installed_inventory with
        agent_ids=target_agents, so skills only visible in OTHER harnesses were
        invisible and never flagged as missing.  After the fix the call has no
        agent_ids filter; the full snapshot is returned and the cross-harness
        skill is correctly reported as missing for the target.
        """
        # Verify the implementation does NOT filter the inventory call.
        inventory_calls: list[dict] = []

        def capture_inventory(**kwargs):
            inventory_calls.append(kwargs)
            # Return a full cross-harness snapshot: repo-skill is installed in
            # claude-code but absent from codex.
            return InstalledInventorySnapshot(
                rows=(
                    InstalledSkillInventoryRow(
                        name="repo-skill",
                        path="/tmp/repo-skill",
                        source_path="/tmp/repo-skill/SKILL.md",
                        scope="global",
                        description="Repo skill",
                        license="",
                        version="",
                        author="",
                        source="github:wyattowalsh/agents",
                        install_source="github:wyattowalsh/agents",
                        source_url="https://github.com/wyattowalsh/agents",
                        install_command="npx skills add github:wyattowalsh/agents --skill repo-skill -y -g",
                        provenance_status="repo-owned",
                        trust_tier="repo",
                        selector_mode="named",
                        installed_agents=("claude-code",),
                        discovered_in=("claude-code",),
                        target_agents=(),
                    ),
                ),
                queries=(
                    HarnessQueryResult(agent_id="claude-code", ok=True, entries=()),
                    HarnessQueryResult(agent_id="codex", ok=True, entries=()),
                ),
            )

        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/npx")
        monkeypatch.setattr("wagents.cli.collect_installed_inventory", capture_inventory)
        monkeypatch.setattr("wagents.cli.collect_desired_sync_rows", lambda **kwargs: ())

        result = runner.invoke(app, ["skills", "sync", "--agent", "codex"])

        assert result.exit_code == 0
        # collect_installed_inventory must have been called without agent_ids.
        assert inventory_calls, "collect_installed_inventory was not called"
        assert "agent_ids" not in inventory_calls[0], (
            "_build_sync_report must not filter the inventory to target agents; got kwargs: " + repr(inventory_calls[0])
        )
        # Cross-harness skill correctly reported as missing for the target.
        assert "missing (1)" in result.output
        assert "npx skills add github:wyattowalsh/agents --skill repo-skill -y -g -a codex" in result.output


class TestGrokDoctor:
    def test_grok_doctor_reports_missing_env(self, monkeypatch, tmp_path):
        grok_cfg = tmp_path / "config.toml"
        grok_cfg.write_text(
            "# BEGIN MANAGED BY sync_agent_stack.py: MCP_SERVERS\n"
            "[mcp_servers.mcphub_group_harness-safe]\nenabled = true\n"
            "# END MANAGED BY sync_agent_stack.py: MCP_SERVERS\n",
            encoding="utf-8",
        )
        monkeypatch.setattr("wagents.platforms.grok.GROK_CONFIG_PATH", grok_cfg)
        monkeypatch.setattr("wagents.platforms.grok.GROK_CONFIG_REPO_PATH", tmp_path / "repo.toml")
        monkeypatch.setattr("wagents.platforms.grok.GROK_CONFIG_POLICY_PATH", tmp_path / "policy.toml")
        monkeypatch.setattr("wagents.platforms.grok.GROK_BINARY_PATH", tmp_path / "grok")

        def fake_which(cmd: str) -> str | None:
            if cmd == "grok":
                return str(tmp_path / "grok")
            return None

        monkeypatch.setattr("shutil.which", fake_which)
        monkeypatch.delenv("GROK_WEB_FETCH", raising=False)

        result = runner.invoke(app, ["grok", "doctor"])
        assert result.exit_code == 0
        assert "GROK_WEB_FETCH" in result.output
        assert "warnings:" in result.output

    def test_grok_doctor_warns_missing_managed_markers(self, monkeypatch, tmp_path):
        grok_cfg = tmp_path / "config.toml"
        grok_cfg.write_text(
            "[mcp_servers.mcphub_group_harness-safe]\nenabled = true\n",
            encoding="utf-8",
        )
        monkeypatch.setattr("wagents.platforms.grok.GROK_CONFIG_PATH", grok_cfg)
        monkeypatch.setattr("wagents.platforms.grok.GROK_CONFIG_REPO_PATH", tmp_path / "repo.toml")
        monkeypatch.setattr("wagents.platforms.grok.GROK_CONFIG_POLICY_PATH", tmp_path / "policy.toml")
        monkeypatch.setattr("wagents.platforms.grok.GROK_BINARY_PATH", tmp_path / "grok")

        def fake_which(cmd: str) -> str | None:
            if cmd == "grok":
                return str(tmp_path / "grok")
            return None

        monkeypatch.setattr("shutil.which", fake_which)

        result = runner.invoke(app, ["grok", "doctor"])
        assert result.exit_code == 0
        assert "managed markers" in result.output or "managed block" in result.output
        assert "warnings:" in result.output
