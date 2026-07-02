"""Tests for scripts/validate/validate_repo.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema
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


def test_cursor_agents_config_matches_schema() -> None:
    schema = json.loads((REPO_ROOT / "config" / "schemas" / "cursor-agents.schema.json").read_text(encoding="utf-8"))
    data = json.loads((REPO_ROOT / "config" / "cursor-agents.json").read_text(encoding="utf-8"))

    jsonschema.Draft202012Validator(schema).validate(data)


def test_opencode_agents_config_matches_schema() -> None:
    schema = json.loads(
        (REPO_ROOT / "config" / "schemas" / "opencode-agents.schema.json").read_text(encoding="utf-8")
    )
    data = json.loads((REPO_ROOT / "config" / "opencode-agents.json").read_text(encoding="utf-8"))

    jsonschema.Draft202012Validator(schema).validate(data)


def test_validate_repo_success_json(mini_repo: Path) -> None:
    result = _run_validate_repo("--format", "json", cwd=mini_repo)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["errors"] == []


def _write_curated_authoring(
    repo: Path,
    *,
    name: str = "demo-external",
    sync_kind: str | None = "skills-cli",
    install_command: str = "npx skills add example/demo-skills --skill demo-external -y -g -a codex",
) -> Path:
    authoring_dir = repo / "docs" / "src" / "authoring" / "skills"
    authoring_dir.mkdir(parents=True, exist_ok=True)
    sync_kind_line = f"sync_kind: {sync_kind}\n" if sync_kind is not None else ""
    path = authoring_dir / f"{name}.mdx"
    path.write_text(
        f"""---
name: {name}
description: Curated external demo skill.
source_kind: curated-external
source: example/demo-skills
install_source: example/demo-skills
status: install-now-after-trust-gate
trust_tier: curated-trust-gated
provenance_status: verified-install-command
source_url: https://github.com/example/demo-skills
target_agents:
  - codex
{sync_kind_line}install_command: {install_command}
---

Audit notes.
""",
        encoding="utf-8",
    )
    return path


def test_validate_repo_accepts_curated_authoring_frontmatter(mini_repo: Path) -> None:
    _write_curated_authoring(mini_repo)
    result = _run_validate_repo(cwd=mini_repo)
    assert result.returncode == 0, result.stdout + result.stderr


def test_validate_repo_rejects_curated_authoring_missing_sync_kind(mini_repo: Path) -> None:
    _write_curated_authoring(mini_repo, sync_kind=None)
    result = _run_validate_repo(cwd=mini_repo)
    assert result.returncode == 1
    assert "Curated external authoring is missing 'sync_kind'" in result.stdout


def test_strict_sync_rejects_same_missing_sync_kind_shape(mini_repo: Path, monkeypatch) -> None:
    from wagents.external_skills import ExternalSkillCatalogError, read_external_skill_entries

    _write_curated_authoring(mini_repo, sync_kind=None)
    authoring_dir = mini_repo / "docs" / "src" / "authoring" / "skills"
    monkeypatch.setattr("wagents.skill_index.AUTHORING_SKILLS_DIR", authoring_dir)
    monkeypatch.setattr("wagents.skill_index.CATALOG_INDEX_PATH", mini_repo / "missing-index.json")

    with pytest.raises(ExternalSkillCatalogError, match="Curated external authoring is missing 'sync_kind'"):
        read_external_skill_entries(strict=True)


def test_validate_repo_rejects_external_tool_with_skills_cli_command(mini_repo: Path) -> None:
    _write_curated_authoring(mini_repo, sync_kind="external-tool")
    result = _run_validate_repo(cwd=mini_repo)
    assert result.returncode == 1
    assert "external-tool authoring rows must not use npx skills add" in result.stdout


def test_validate_repo_bad_skill_jsonl(mini_repo: Path) -> None:
    bad_skill = mini_repo / "skills" / "bad-skill"
    bad_skill.mkdir()
    (bad_skill / "SKILL.md").write_text("---\ndescription: Missing the name field\n---\n\n# Bad Skill\n\nBody.\n")
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


def test_validate_repo_rejects_agent_scaffold_placeholder_text(mini_repo: Path) -> None:
    agent_script = REPO_ROOT / "skills" / "agent-conventions" / "scripts" / "validate_agent.py"
    if not agent_script.is_file():
        pytest.skip("agent validator not available")

    dest = mini_repo / "skills" / "agent-conventions" / "scripts" / "validate_agent.py"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(agent_script.read_text(encoding="utf-8"))

    agent = mini_repo / "agents" / "test-agent.md"
    agent.write_text(
        "---\n"
        "name: test-agent\n"
        "description: Test agent with scaffold body.\n"
        "---\n\n"
        "This is the agent's system prompt. Everything below the frontmatter\n"
        "is treated as instructions.\n\n"
        "Rules and constraints for this agent's behavior.\n",
        encoding="utf-8",
    )
    (mini_repo / "agents" / "README.md").write_text(
        "# Agents\n\n| Name | Description |\n| ---- | ----------- |\n| test-agent | Test agent. |\n",
        encoding="utf-8",
    )

    result = _run_validate_repo(cwd=mini_repo)
    assert result.returncode == 1
    assert "placeholder scaffold text remains" in result.stdout


def test_validate_repo_mcp_registry_rejects_string_tools_allow_all(mini_repo: Path) -> None:
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
      "tools": ["*"],
      "tools_allow_all": "false"
    }
  }
}
""",
        encoding="utf-8",
    )
    result = _run_validate_repo(cwd=mini_repo)
    assert result.returncode == 1
    assert "tools_allow_all" in result.stdout + result.stderr


def test_path_leak_other_user(mini_repo: Path) -> None:
    """Other-user absolute path in tracked config must fail validate (portability leak)."""
    leak_path = mini_repo / "config" / "tooling-policy.json"
    leak_path.parent.mkdir(parents=True, exist_ok=True)
    leak_path.write_text('{"note": "see /Users/otheruser/secret/project"}', encoding="utf-8")
    result = _run_validate_repo(cwd=mini_repo)
    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "Portable-path leak" in combined


def test_quarantine_slug_in_catalog_index(mini_repo: Path) -> None:
    """Hard-quarantined repo slug in catalog index must fail validate."""
    qreg = mini_repo / "planning" / "manifests" / "security-quarantine-register.json"
    qreg.parent.mkdir(parents=True, exist_ok=True)
    qreg.write_text(
        json.dumps({
            "external_repo_records": [
                {
                    "repo": "snailsploit/claude-red",
                    "default_action": "quarantine",
                }
            ]
        }),
        encoding="utf-8",
    )
    index_dir = mini_repo / "docs" / "public" / "generated-registries"
    index_dir.mkdir(parents=True, exist_ok=True)
    index_dir.joinpath("skills-catalog-index.json").write_text(
        json.dumps({
            "externalSkillIndex": [
                {
                    "name": "foo",
                    "source": "snailsploit/claude-red",
                    "installSource": "snailsploit/claude-red",
                }
            ]
        }),
        encoding="utf-8",
    )
    result = _run_validate_repo(cwd=mini_repo)
    assert result.returncode == 1
    combined = (result.stdout + result.stderr).lower()
    assert "quarantined" in combined or "snailsploit/claude-red" in combined


def test_quarantine_slug_in_authoring_mdx(mini_repo: Path) -> None:
    """Hard-quarantined repo slug in authoring MDX must fail validate even without index."""
    qreg = mini_repo / "planning" / "manifests" / "security-quarantine-register.json"
    qreg.parent.mkdir(parents=True, exist_ok=True)
    qreg.write_text(
        json.dumps({
            "external_repo_records": [
                {
                    "repo": "snailsploit/claude-red",
                    "default_action": "quarantine",
                }
            ]
        }),
        encoding="utf-8",
    )
    authoring_dir = mini_repo / "docs" / "src" / "authoring" / "skills"
    authoring_dir.mkdir(parents=True, exist_ok=True)
    authoring_dir.joinpath("bad-skill.mdx").write_text(
        """---
name: bad-skill
description: test
source_kind: curated-external
source: snailsploit/claude-red
install_source: snailsploit/claude-red
status: avoid
trust_tier: curated-trust-gated
provenance_status: verified-install-command
source_url: https://example.com
sync_kind: skills-cli
target_agents: [claude-code]
---
body
""",
        encoding="utf-8",
    )
    result = _run_validate_repo(cwd=mini_repo)
    assert result.returncode == 1
    combined = (result.stdout + result.stderr).lower()
    assert "quarantined" in combined or "snailsploit/claude-red" in combined


def test_quarantine_register_rejects_undeclared_trigger(mini_repo: Path) -> None:
    """Every quarantine record trigger must be declared in quarantine_triggers."""
    qreg = mini_repo / "planning" / "manifests" / "security-quarantine-register.json"
    qreg.parent.mkdir(parents=True, exist_ok=True)
    qreg.write_text(
        json.dumps({
            "quarantine_triggers": ["credential-sharing"],
            "external_repo_records": [
                {
                    "id": "EXT-TEST",
                    "repo": "example/repo",
                    "trigger": "credential reuse",
                    "default_action": "local-user-owned-reference-only",
                }
            ],
        }),
        encoding="utf-8",
    )
    result = _run_validate_repo(cwd=mini_repo)
    assert result.returncode == 1
    assert "undeclared trigger" in result.stdout + result.stderr


def test_quarantine_register_invalid_json_reports_validation_error(mini_repo: Path) -> None:
    """Invalid quarantine-register JSON must not traceback during validation."""
    qreg = mini_repo / "planning" / "manifests" / "security-quarantine-register.json"
    qreg.parent.mkdir(parents=True, exist_ok=True)
    qreg.write_text("{not json", encoding="utf-8")

    result = _run_validate_repo(cwd=mini_repo)

    combined = result.stdout + result.stderr
    assert result.returncode == 1
    assert "Invalid quarantine register JSON" in combined
    assert "Traceback" not in combined


def test_quarantine_register_rejects_missing_trigger(mini_repo: Path) -> None:
    """Every quarantine record must include a non-blank trigger."""
    qreg = mini_repo / "planning" / "manifests" / "security-quarantine-register.json"
    qreg.parent.mkdir(parents=True, exist_ok=True)
    qreg.write_text(
        json.dumps({
            "quarantine_triggers": ["credential-sharing"],
            "external_repo_records": [
                {
                    "id": "EXT-TEST",
                    "repo": "example/repo",
                    "trigger": " ",
                    "default_action": "local-user-owned-reference-only",
                }
            ],
        }),
        encoding="utf-8",
    )

    result = _run_validate_repo(cwd=mini_repo)

    assert result.returncode == 1
    assert "missing a trigger" in result.stdout + result.stderr


def test_mcp_missing_defaults_and_tools(mini_repo: Path) -> None:
    """Missing contributor_defaults + missing tools field aggregates 2+ errors."""
    reg = mini_repo / "config" / "mcp-registry.json"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(
        """{
  "servers": {
    "demo": {
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "demo-mcp"]
    }
  }
}
""",
        encoding="utf-8",
    )
    result = _run_validate_repo("--format", "json", cwd=mini_repo)
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert len(payload["errors"]) >= 2
    sources = [e["source"] for e in payload["errors"]]
    assert any("mcp-registry.json" in s for s in sources)
