"""Unit tests for the decoupled hook-policy decision modules."""

from __future__ import annotations

from pathlib import Path

import pytest

from wagents.hooks.policies import (
    evaluate_before_mcp_execution,
    evaluate_before_read_file,
    evaluate_git_commit_push,
    grok_deny_payload,
    quality_gate_command,
    subagent_start_context,
    validate_asset_paths,
)


@pytest.mark.parametrize(
    "command",
    [
        "git push --force origin main",
        "git push -f origin master",
        "git commit -m x --no-verify",
        "git push --no-verify",
        "git commit --no-gpg-sign -m x",
    ],
)
def test_git_commit_push_guard_blocks(command: str) -> None:
    assert evaluate_git_commit_push(command) is not None


@pytest.mark.parametrize(
    "command",
    [
        "",
        "git status",
        "git push origin feature/x",
        "git push --force-with-lease origin feature/x",
        "git commit -m 'normal commit'",
        "ls -la",
    ],
)
def test_git_commit_push_guard_allows(command: str) -> None:
    assert evaluate_git_commit_push(command) is None


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        ".env.local",
        "config/.env.production",
        "secrets.json",
        "deploy/service-account.json",
        "/home/u/.ssh/id_rsa",
        "certs/server.key",
        "vault/private.pem",
        "app-token.txt",
    ],
)
def test_before_read_file_guard_blocks(path: str) -> None:
    assert evaluate_before_read_file(path) is not None


@pytest.mark.parametrize(
    "path",
    [
        "",
        "src/main.py",
        "README.md",
        "config/hook-registry.json",
        "docs/index.mdx",
    ],
)
def test_before_read_file_guard_allows(path: str) -> None:
    assert evaluate_before_read_file(path) is None


def test_before_mcp_execution_blocks_destructive_command() -> None:
    assert evaluate_before_mcp_execution("shell.exec", {"command": "rm -rf /"}) is not None
    assert evaluate_before_mcp_execution("run", {"args": ["git", "push", "--force", "main"]}) is not None


def test_before_mcp_execution_blocks_absolute_delete() -> None:
    assert evaluate_before_mcp_execution("fs.delete", {"path": "/etc/hosts"}) is not None


def test_before_mcp_execution_allows_safe_calls() -> None:
    assert evaluate_before_mcp_execution("search", {"query": "rm -rf docs"}) is None
    assert evaluate_before_mcp_execution("shell.exec", {"command": "ls -la"}) is None
    assert evaluate_before_mcp_execution("", {}) is None


def test_grok_deny_payload_shape() -> None:
    payload = grok_deny_payload("nope", policy_id="git-commit-push-guard")
    assert payload["decision"] == "block"
    assert payload["reason"] == "nope"
    assert payload["hookSpecificOutput"]["permission"] == "deny"
    assert payload["hookSpecificOutput"]["policyId"] == "git-commit-push-guard"
    # Empty reason falls back to a default sentence.
    assert grok_deny_payload("")["reason"]


def test_subagent_start_context_includes_state_and_source() -> None:
    message = subagent_start_context("branch main, clean")
    assert "branch main, clean" in message
    assert "config/hook-registry.json" in message
    assert subagent_start_context("   ")  # empty falls back gracefully


def test_validate_asset_paths_selects_assets() -> None:
    paths = [
        "skills/review/SKILL.md",
        "agents/foo.md",
        "mcp/things/server.py",
        "config/hook-registry.json",
        "README.md",
        "docs/index.mdx",
        "skills/review/notes.txt",
    ]
    selected = validate_asset_paths(paths)
    assert selected == [
        "agents/foo.md",
        "config/hook-registry.json",
        "mcp/things/server.py",
        "skills/review/SKILL.md",
    ]
    assert validate_asset_paths([]) == []


def test_quality_gate_command_resolves_repo_script() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    command = quality_gate_command(repo_root)
    if (repo_root / "hooks" / "verify-before-stop.sh").is_file():
        assert command is not None
        assert command[0] == "bash"
        assert command[1].endswith("hooks/verify-before-stop.sh")
    assert quality_gate_command("/nonexistent-root-xyz") is None
