from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_module():
    path = Path(__file__).parents[1] / "scripts" / "retire_harness_targets.py"
    spec = importlib.util.spec_from_file_location("retire_harness_targets", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


retire = _load_module()


def test_rewrite_authoring_text_preserves_body_and_is_idempotent() -> None:
    original = (
        "---\n"
        'name: "demo"\n'
        'install_command: "npx skills add owner/repo --skill demo -y -g -a '
        'antigravity claude-code codex gemini-cli github-copilot opencode"\n'
        'target_agents: ["antigravity", "claude-code", "codex", "gemini-cli", '
        '"github-copilot", "opencode"]\n'
        'unsupported_target_agents: ["gemini-cli", "other"]\n'
        "---\n\n"
        "Body with github-copilot historical evidence.\n"
    )
    rewritten = retire.rewrite_authoring_text(original)
    assert (
        'install_command: "npx skills add owner/repo --skill demo -y -g -a claude-code codex opencode"'
        in rewritten
    )
    assert 'target_agents: ["claude-code", "codex", "opencode"]' in rewritten
    assert 'unsupported_target_agents: ["other"]' in rewritten
    assert rewritten.endswith("\nBody with github-copilot historical evidence.\n")
    assert retire.rewrite_authoring_text(rewritten) == rewritten


def test_rewrite_authoring_text_retires_body_commands_but_keeps_historical_prose() -> None:
    original = (
        "---\n"
        'name: "demo"\n'
        'install_command: "npx skills add owner/repo --skill demo -y -g -a claude-code codex '
        'crush cursor grok opencode"\n'
        'target_agents: ["claude-code", "codex", "crush", "cursor", "grok", "opencode"]\n'
        "---\n\n"
        "- Install command: `npx skills add owner/repo --skill demo -y -g -a antigravity "
        "claude-code codex crush cursor gemini-cli github-copilot grok opencode`\n"
        "- Historical review covered github-copilot and gemini-cli metadata.\n\n"
        "```bash\n"
        "npx skills add owner/repo --skill demo -y -g -a antigravity claude-code codex crush "
        "cursor gemini-cli github-copilot grok opencode\n"
        "```\n"
    )
    rewritten = retire.rewrite_authoring_text(original)
    command = "npx skills add owner/repo --skill demo -y -g -a claude-code codex crush cursor grok opencode"
    assert f"`{command}`" in rewritten
    assert f"\n{command}\n" in rewritten
    assert "Historical review covered github-copilot and gemini-cli metadata." in rewritten
    assert retire.rewrite_authoring_text(rewritten) == rewritten


def test_rewrite_mcp_registry_preserves_candidate_servers() -> None:
    payload = {
        "servers": {
            "chrome-devtools": {
                "exclude_from_harnesses": ["claude-code", "gemini-cli", "github-copilot-web"],
                "ownership": {
                    "plugin": ["claude-code", "github-copilot-web"],
                    "extension": ["gemini-cli"],
                    "repo_mcp": ["codex", "github-copilot-cli", "antigravity", "crush"],
                },
            },
            "candidate-node": {"command": "candidate-node"},
        },
        "mcphub": {
            "clients": {
                "stdio_bridge": {
                    "clients": ["cursor", "gemini-cli", "antigravity", "github-copilot-cli", "crush"]
                }
            }
        },
    }
    retire.rewrite_registry("config/mcp-registry.json", payload)
    assert payload["servers"]["candidate-node"] == {"command": "candidate-node"}
    chrome = payload["servers"]["chrome-devtools"]
    assert chrome["exclude_from_harnesses"] == ["claude-code"]
    assert chrome["ownership"]["plugin"] == ["claude-code"]
    assert chrome["ownership"]["extension"] == []
    assert chrome["ownership"]["repo_mcp"] == ["codex", "crush"]
    assert payload["mcphub"]["clients"]["stdio_bridge"]["clients"] == ["cursor", "crush"]


def test_rewrite_hook_registry_drops_retired_only_rows() -> None:
    payload = {
        "hooks": [
            {"id": "retired", "harnesses": ["github-copilot"]},
            {"id": "shared", "harnesses": ["codex", "gemini-cli"]},
        ]
    }
    retire.rewrite_registry("config/hook-registry.json", payload)
    assert payload == {"hooks": [{"id": "shared", "harnesses": ["codex"]}]}


def test_rewrite_sync_manifest_drops_only_owned_retired_paths() -> None:
    payload = {
        "managed": [
            {"path": "${REPO_ROOT}/.github/hooks", "mode": "generated"},
            {"path": "~/.gemini/settings.json", "mode": "merged"},
            {"path": "${REPO_ROOT}/scripts/mcphub/wrappers/candidate-node", "mode": "canonical"},
        ]
    }
    retire.rewrite_registry("config/sync-manifest.json", payload)
    assert payload["managed"] == [
        {"path": "${REPO_ROOT}/scripts/mcphub/wrappers/candidate-node", "mode": "canonical"}
    ]


def test_rewrite_agent_bundle_removes_all_retired_targets() -> None:
    payload = {
        "adapters": {
            "agent-skills-cli": {
                "install": "npx skills add source --all --agent antigravity --agent codex --agent gemini-cli",
                "supportedAgents": ["antigravity", "codex", "gemini-cli", "github-copilot"],
            },
            "openspec": {
                "toolMapping": {
                    "antigravity": "antigravity",
                    "codex": "codex",
                    "gemini-cli": "gemini",
                    "github-copilot": "github-copilot",
                }
            },
        }
    }
    retire.rewrite_registry("agent-bundle.json", payload)
    encoded = json.dumps(payload)
    assert "antigravity" not in encoded
    assert "gemini-cli" not in encoded
    assert "github-copilot" not in encoded
    assert payload["adapters"]["agent-skills-cli"]["supportedAgents"] == ["codex"]
    assert payload["adapters"]["agent-skills-cli"]["install"] == (
        "npx skills add source --all --agent codex"
    )


def test_rewrite_promotion_overrides_removes_only_active_retired_targets() -> None:
    command = (
        "npx skills add owner/repo --skill demo -y -g -a "
        "antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode"
    )
    payload = {
        "overrides": [
            {
                "skill_name": "demo",
                "target_agents": [
                    "antigravity",
                    "claude-code",
                    "codex",
                    "crush",
                    "cursor",
                    "gemini-cli",
                    "github-copilot",
                    "grok",
                    "opencode",
                ],
                "install_command": command,
                "executed_commands": [command],
            }
        ]
    }
    retire.rewrite_registry(
        "planning/manifests/candidate-corpus-jul2026/promotion-overrides.json",
        payload,
    )
    row = payload["overrides"][0]
    assert row["target_agents"] == ["claude-code", "codex", "crush", "cursor", "grok", "opencode"]
    assert row["install_command"] == (
        "npx skills add owner/repo --skill demo -y -g -a claude-code codex crush cursor grok opencode"
    )
    assert row["executed_commands"] == [command]


def test_rewrite_install_command_preserves_multi_target_agent_group() -> None:
    command = (
        "npx skills add owner/repo --skill demo -y -g -a "
        "antigravity claude-code codex gemini-cli github-copilot opencode"
    )
    assert retire._rewrite_install_command(command) == (
        "npx skills add owner/repo --skill demo -y -g -a claude-code codex opencode"
    )


def test_remove_markdown_h2_sections_renumbers_contents() -> None:
    original = (
        "# Guide\n\n"
        "## Contents\n\n"
        "1. [Keep](#keep)\n"
        "2. [Retire](#retire)\n"
        "3. [Also Keep](#also-keep)\n\n"
        "## Keep\n\nA\n\n"
        "## Retire\n\nB\n\n"
        "## Also Keep\n\nC\n"
    )
    rewritten = retire.remove_markdown_h2_sections(original, frozenset({"Retire"}))
    assert "Retire" not in rewritten
    assert "1. [Keep](#keep)" in rewritten
    assert "2. [Also Keep](#also-keep)" in rewritten
    assert "\nA\n" in rewritten
    assert "\nC\n" in rewritten
