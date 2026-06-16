"""Tests for scripts/validate/validate_repo.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATE_REPO = REPO_ROOT / "scripts" / "validate" / "validate_repo.py"
VALIDATE_MCP = REPO_ROOT / "scripts" / "validate" / "validate_mcp.py"


def _run_validate_repo(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATE_REPO), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=False)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, capture_output=True, check=False)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, capture_output=True, check=False)


@pytest.fixture
def mini_repo(tmp_path: Path) -> Path:
    (tmp_path / "skills").mkdir()
    (tmp_path / "agents").mkdir()
    (tmp_path / "mcp").mkdir()
    _init_git_repo(tmp_path)
    return tmp_path


def test_validate_repo_success_text(mini_repo: Path) -> None:
    result = _run_validate_repo(cwd=mini_repo)
    assert result.returncode == 0, result.stderr
    assert "All validations passed" in result.stdout


def test_validate_repo_success_json(mini_repo: Path) -> None:
    result = _run_validate_repo("--format", "json", cwd=mini_repo)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["errors"] == []


def test_validate_repo_bad_skill_jsonl(mini_repo: Path) -> None:
    bad_skill = mini_repo / "skills" / "bad-skill"
    bad_skill.mkdir()
    (bad_skill / "SKILL.md").write_text(
        "---\ndescription: Missing the name field\n---\n\n# Bad Skill\n\nBody.\n"
    )
    result = _run_validate_repo("--format", "jsonl", cwd=mini_repo)
    assert result.returncode == 1
    records = [json.loads(line) for line in result.stdout.strip().splitlines()]
    assert records[0]["type"] == "error"
    assert records[0]["source"].endswith("bad-skill/SKILL.md")
    assert records[-1]["type"] == "summary"
    assert records[-1]["ok"] is False


def test_validate_repo_bad_hook_event(mini_repo: Path) -> None:
    claude_dir = mini_repo / ".claude"
    claude_dir.mkdir()
    settings = {
        "hooks": {
            "BadEvent": [{"hooks": [{"type": "command", "command": "echo x"}]}],
        }
    }
    (claude_dir / "settings.json").write_text(json.dumps(settings))
    result = _run_validate_repo(cwd=mini_repo)
    assert result.returncode == 1
    assert "unknown hook event" in result.stdout


def test_validate_repo_skips_gitignored_mcp_cache(mini_repo: Path) -> None:
    (mini_repo / ".gitignore").write_text("mcp/cache/\n")
    cache_dir = mini_repo / "mcp" / "cache"
    cache_dir.mkdir()
    servers_dir = mini_repo / "mcp" / "servers" / "missing-files"
    servers_dir.mkdir(parents=True)
    subprocess.run(["git", "add", ".gitignore"], cwd=mini_repo, capture_output=True, check=False)
    result = _run_validate_repo(cwd=mini_repo)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "All validations passed" in result.stdout


def test_validate_mcp_skips_local_dirs(mini_repo: Path) -> None:
    (mini_repo / "mcp" / "cache").mkdir()
    result = subprocess.run(
        [sys.executable, str(VALIDATE_MCP)],
        cwd=mini_repo,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

def test_validate_mcp_respects_cwd(mini_repo: Path) -> None:
    bad_mcp = mini_repo / "mcp" / "Bad_Name"
    bad_mcp.mkdir()
    result = subprocess.run(
        [sys.executable, str(VALIDATE_MCP)],
        cwd=mini_repo,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "Bad_Name" in result.stdout


def test_validate_mcp_repo_root_flag(mini_repo: Path) -> None:
    bad_mcp = mini_repo / "mcp" / "bad-server"
    bad_mcp.mkdir()
    result = subprocess.run(
        [sys.executable, str(VALIDATE_MCP), "--repo-root", str(mini_repo)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "bad-server" in result.stdout


def test_validate_repo_check_index(mini_repo: Path) -> None:
    agent_script = REPO_ROOT / "skills" / "agent-conventions" / "scripts" / "validate_agent.py"
    if not agent_script.is_file():
        pytest.skip("agent validator not available")

    dest = mini_repo / "skills" / "agent-conventions" / "scripts" / "validate_agent.py"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(agent_script.read_text(encoding="utf-8"))

    agent = mini_repo / "agents" / "test-agent.md"
    agent.write_text("---\nname: test-agent\ndescription: Test agent for index validation.\n---\n\nPrompt.\n")
    (mini_repo / "agents" / "README.md").write_text("# Agents\n\n| Name | Description |\n| ---- | ----------- |\n")

    result = _run_validate_repo(cwd=mini_repo)
    assert result.returncode == 1
    assert "missing from README index table" in result.stdout


def test_validate_repo_mcp_registry_wildcard_requires_opt_in(mini_repo: Path) -> None:
    registry_path = mini_repo / "config" / "mcp-registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        """{
  "contributor_defaults": {
    "tools_policy": "deny-by-default",
    "wildcard_requires_explicit_opt_in": true
  },
  "servers": {
    "demo": {
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "demo-mcp"],
      "tools": ["*"]
    }
  }
}
""",
        encoding="utf-8",
    )
    result = _run_validate_repo(cwd=mini_repo)
    assert result.returncode == 1
    assert "tools_allow_all" in result.stdout + result.stderr
