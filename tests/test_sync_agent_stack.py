"""Tests for sync_agent_stack rendering and merge helpers."""

import json

from scripts import sync_agent_stack
from scripts.sync_agent_stack import (
    SyncContext,
    merge_codex_config,
    merge_opencode_config,
    merge_server_root_config,
    render_cherry_import_files,
    render_cherry_server,
    render_codex_config,
    render_codex_mcp_block,
    render_opencode_mcp,
    sync_codex_entrypoint,
    sync_generated_json_directory,
)


def test_render_opencode_mcp_renders_local_servers():
    registry = {
        "servers": {
            "foo": {
                "command": "uvx",
                "args": ["foo-mcp"],
                "enabled": True,
                "env": {
                    "FOO_TOKEN": {"env_var": "FOO_TOKEN"},
                },
            },
        }
    }
    fallbacks = {"FOO_TOKEN": "secret"}

    rendered = render_opencode_mcp(registry, fallbacks)

    assert rendered == {
        "foo": {
            "type": "local",
            "command": ["uvx", "foo-mcp"],
            "enabled": True,
            "environment": {"FOO_TOKEN": "secret"},
        }
    }


def test_render_opencode_mcp_renders_remote_servers():
    registry = {
        "servers": {
            "remote": {
                "command": "npx",
                "args": ["-y", "mcp-remote", "https://example.com/mcp"],
                "enabled": True,
            }
        }
    }

    rendered = render_opencode_mcp(registry, {})

    assert rendered == {
        "remote": {
            "type": "remote",
            "url": "https://example.com/mcp",
            "enabled": True,
        }
    }


def test_merge_server_root_config_uses_opencode_mcp_root(tmp_path):
    opencode_config = tmp_path / "opencode.json"
    opencode_config.write_text(json.dumps({"mcp": {"custom": {"type": "local", "enabled": True}}}))

    ctx = SyncContext(apply=True)
    rendered = {
        "managed": {
            "type": "local",
            "command": ["uvx", "managed-mcp"],
            "enabled": True,
        }
    }

    merge_server_root_config(ctx, opencode_config, "mcp", rendered)
    payload = json.loads(opencode_config.read_text())

    assert "mcp" in payload
    assert "managed" in payload["mcp"]
    assert "custom" in payload["mcp"]
    assert "mcpServers" not in payload


def test_render_cherry_server_renders_streamable_http_remote_servers():
    entry = {
        "command": "npx",
        "args": ["-y", "mcp-remote", "https://example.com/mcp"],
    }

    rendered = render_cherry_server("remote", entry, {})

    assert rendered == {
        "type": "streamableHttp",
        "baseUrl": "https://example.com/mcp",
    }


def test_render_cherry_import_files_writes_all_and_per_server_files():
    registry = {
        "servers": {
            "deepwiki": {
                "command": "npx",
                "args": ["-y", "mcp-remote", "https://mcp.deepwiki.com/mcp"],
                "enabled": True,
            },
            "duckduckgo": {
                "transport": "stdio",
                "command": "uvx",
                "args": ["duckduckgo-mcp-server"],
                "enabled": True,
                "env": {"DUCK_TOKEN": {"env_var": "DUCK_TOKEN"}},
            },
        }
    }

    rendered = render_cherry_import_files(registry, {"DUCK_TOKEN": "secret"})

    assert set(rendered) == {"all.json", "deepwiki.json", "duckduckgo.json"}
    assert rendered["deepwiki.json"] == {
        "mcpServers": {
            "deepwiki": {
                "type": "streamableHttp",
                "baseUrl": "https://mcp.deepwiki.com/mcp",
            }
        }
    }
    assert rendered["duckduckgo.json"] == {
        "mcpServers": {
            "duckduckgo": {
                "type": "stdio",
                "command": "uvx",
                "args": ["duckduckgo-mcp-server"],
                "env": {"DUCK_TOKEN": "secret"},
            }
        }
    }
    assert rendered["all.json"] == {
        "mcpServers": {
            "deepwiki": {
                "type": "streamableHttp",
                "baseUrl": "https://mcp.deepwiki.com/mcp",
            },
            "duckduckgo": {
                "type": "stdio",
                "command": "uvx",
                "args": ["duckduckgo-mcp-server"],
                "env": {"DUCK_TOKEN": "secret"},
            },
        }
    }


def test_sync_generated_json_directory_rewrites_managed_json_and_leaves_parent_files_untouched(tmp_path):
    target_dir = tmp_path / "mcp-import"
    managed_dir = target_dir / "managed"
    managed_dir.mkdir(parents=True)
    (target_dir / "custom.json").write_text('{"custom": true}\n', encoding="utf-8")
    (managed_dir / "stale.json").write_text('{"stale": true}\n', encoding="utf-8")
    (managed_dir / "notes.txt").write_text("keep me\n", encoding="utf-8")

    ctx = SyncContext(apply=True)
    rendered = {
        "all.json": {"mcpServers": {"duckduckgo": {"type": "stdio"}}},
        "duckduckgo.json": {"mcpServers": {"duckduckgo": {"type": "stdio"}}},
    }

    sync_generated_json_directory(ctx, managed_dir, rendered)

    assert sorted(path.name for path in managed_dir.iterdir()) == ["all.json", "duckduckgo.json", "notes.txt"]
    assert json.loads((managed_dir / "all.json").read_text(encoding="utf-8")) == rendered["all.json"]
    assert json.loads((managed_dir / "duckduckgo.json").read_text(encoding="utf-8")) == rendered["duckduckgo.json"]
    assert not (managed_dir / "stale.json").exists()
    assert (target_dir / "custom.json").exists()
    assert "remove " in "\n".join(ctx.changes)


def test_sync_generated_json_directory_check_mode_does_not_write_or_delete(tmp_path):
    target_dir = tmp_path / "mcp-import" / "managed"
    target_dir.mkdir(parents=True)
    (target_dir / "stale.json").write_text('{"stale": true}\n', encoding="utf-8")

    ctx = SyncContext(apply=False)
    rendered = {
        "all.json": {"mcpServers": {"duckduckgo": {"type": "stdio"}}},
    }

    sync_generated_json_directory(ctx, target_dir, rendered)

    assert not (target_dir / "all.json").exists()
    assert (target_dir / "stale.json").exists()
    assert any(change.endswith("all.json") for change in ctx.changes)
    assert any(change.endswith("stale.json") for change in ctx.changes)


def test_merge_opencode_config_adds_managed_instructions_and_skills_path(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    repo_root = home_dir / "dev" / "projects" / "agents"
    config_path = home_dir / ".config" / "opencode" / "opencode.json"

    repo_root.mkdir(parents=True)
    config_path.parent.mkdir(parents=True)
    (repo_root / "instructions").mkdir()
    (repo_root / "skills").mkdir()

    config_path.write_text(
        json.dumps(
            {
                "instructions": ["~/.config/opencode/rules/shared.md"],
                "skills": {"paths": ["~/.config/opencode/skills"]},
                "mcp": {"custom": {"type": "local", "enabled": True}},
            }
        )
    )

    monkeypatch.setattr(sync_agent_stack, "HOME", home_dir)
    monkeypatch.setattr(sync_agent_stack, "REPO_ROOT", repo_root)
    monkeypatch.setattr(sync_agent_stack, "GLOBAL_MD", repo_root / "instructions" / "global.md")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_GLOBAL_MD", repo_root / "instructions" / "opencode-global.md")
    monkeypatch.setattr(sync_agent_stack, "SKILLS_DIR", repo_root / "skills")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_CONFIG_PATH", config_path)

    registry = {
        "servers": {
            "managed": {
                "command": "uvx",
                "args": ["managed-mcp"],
                "enabled": True,
            }
        }
    }

    ctx = SyncContext(apply=True)
    merge_opencode_config(ctx, registry, {})
    payload = json.loads(config_path.read_text())

    assert payload["instructions"] == [
        "~/dev/projects/agents/instructions/global.md",
        "~/dev/projects/agents/instructions/opencode-global.md",
        "~/.config/opencode/rules/shared.md",
    ]
    assert payload["skills"]["paths"] == [
        "~/dev/projects/agents/skills",
        "~/.config/opencode/skills",
    ]
    assert "managed" in payload["mcp"]
    assert "custom" in payload["mcp"]


def test_merge_opencode_config_dedupes_equivalent_paths(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    repo_root = home_dir / "dev" / "projects" / "agents"
    config_path = home_dir / ".config" / "opencode" / "opencode.json"

    repo_root.mkdir(parents=True)
    config_path.parent.mkdir(parents=True)
    (repo_root / "instructions").mkdir()
    (repo_root / "skills").mkdir()

    config_path.write_text(
        json.dumps(
            {
                "instructions": [
                    str((repo_root / "instructions" / "global.md").resolve()),
                    str((repo_root / "instructions" / "opencode-global.md").resolve()),
                ],
                "skills": {"paths": [str((repo_root / "skills").resolve())]},
            }
        )
    )

    monkeypatch.setattr(sync_agent_stack, "HOME", home_dir)
    monkeypatch.setattr(sync_agent_stack, "REPO_ROOT", repo_root)
    monkeypatch.setattr(sync_agent_stack, "GLOBAL_MD", repo_root / "instructions" / "global.md")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_GLOBAL_MD", repo_root / "instructions" / "opencode-global.md")
    monkeypatch.setattr(sync_agent_stack, "SKILLS_DIR", repo_root / "skills")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_CONFIG_PATH", config_path)

    ctx = SyncContext(apply=True)
    merge_opencode_config(ctx, {"servers": {}}, {})
    payload = json.loads(config_path.read_text())

    assert payload["instructions"] == [
        "~/dev/projects/agents/instructions/global.md",
        "~/dev/projects/agents/instructions/opencode-global.md",
    ]
    assert payload["skills"]["paths"] == ["~/dev/projects/agents/skills"]


def test_merge_codex_config_removes_legacy_duckduckgo_alias_but_keeps_other_extras(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_copy_path = tmp_path / "codex-config.toml"
    config_path.write_text(
        "\n".join(
            [
                'model = "gpt-5.4"',
                "",
                "[mcp_servers.duckduckgo-search]",
                'command = "uvx"',
                'args = ["duckduckgo-mcp-server"]',
                "",
                "[mcp_servers.custom-extra]",
                'command = "uvx"',
                'args = ["custom-mcp"]',
                "",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(sync_agent_stack, "CODEX_CONFIG_PATH", config_path)
    monkeypatch.setattr(sync_agent_stack, "CODEX_CONFIG_COPY_PATH", config_copy_path)

    registry = {
        "servers": {
            "duckduckgo": {
                "command": "uvx",
                "args": ["duckduckgo-mcp-server"],
                "enabled": True,
                "env": {},
                "startup_timeout_sec": 90,
                "transport": "stdio",
            }
        }
    }
    policy = {
        "model_defaults": {"codex": {"model": "gpt-5.4", "reasoning_effort": "xhigh", "personality": "pragmatic"}}
    }

    ctx = SyncContext(apply=True)
    merge_codex_config(ctx, registry, policy, {})
    rendered = config_path.read_text(encoding="utf-8")

    assert "[mcp_servers.duckduckgo-search]" not in rendered
    assert rendered.count("[mcp_servers.duckduckgo]") == 1
    assert "[mcp_servers.custom-extra]" in rendered


def test_render_codex_mcp_block_uses_current_schema_shape():
    registry = {
        "servers": {
            "context7": {
                "command": "npx",
                "args": ["-y", "@upstash/context7-mcp", "--api-key", "${CONTEXT7_API_KEY}"],
                "enabled": True,
                "env": {"CONTEXT7_API_KEY": {"env_var": "CONTEXT7_API_KEY"}},
                "startup_timeout_sec": 90,
                "timeout_ms": 600000,
                "tools": ["*"],
            },
            "package-version": {
                "command": "/Users/ww/go/bin/mcp-package-version",
                "args": [],
                "enabled": True,
                "startup_timeout_sec": 90,
                "tools": ["check_npm_versions"],
            },
        }
    }

    rendered = render_codex_mcp_block(registry)

    assert 'type = "stdio"' not in rendered
    assert 'env_vars = ["CONTEXT7_API_KEY"]' in rendered
    assert "--api-key" not in rendered
    assert 'tool_timeout_sec = 600' in rendered
    assert 'enabled_tools = ["check_npm_versions"]' in rendered


def test_render_codex_config_adds_multi_agent_v2_without_legacy_agent_limits_or_secrets():
    registry = {
        "servers": {
            "brave-search": {
                "command": "npx",
                "args": ["-y", "@brave/brave-search-mcp-server"],
                "enabled": True,
                "env": {"BRAVE_API_KEY": {"env_var": "BRAVE_API_KEY"}},
                "startup_timeout_sec": 90,
                "timeout_ms": 600000,
                "tools": ["*"],
            }
        }
    }
    policy = {
        "model_defaults": {"codex": {"model": "gpt-5.5", "reasoning_effort": "high", "personality": "pragmatic"}}
    }
    current = """
notify = ["/tmp/notifier"]

[mcp_servers.ronin]
url = "http://localhost:8000/mcp/"

[mcp_servers.ronin.http_headers]
Authorization = "Bearer local-secret"

[projects."/private/work"]
trust_level = "trusted"

[plugins."secret-local@dev"]
enabled = true
"""

    home_config = render_codex_config(current, registry, policy, include_local_extras=True)
    repo_config = render_codex_config(current, registry, policy, include_local_extras=False)

    assert home_config.startswith("#:schema https://developers.openai.com/codex/config-schema.json")
    assert 'approvals_reviewer = "guardian_subagent"' in home_config
    assert "[features.multi_agent_v2]" in home_config
    assert "\n[features.multi_agent_v2]\nenabled = true\n" in home_config
    assert "[agents]" not in home_config
    assert "max_depth" not in home_config
    assert "max_threads" not in home_config
    assert "job_max_runtime_seconds" not in home_config
    assert 'model = "gpt-5.5"' in home_config
    assert 'model_reasoning_effort = "high"' in home_config
    assert 'plan_mode_reasoning_effort = "high"' in home_config
    assert 'model_reasoning_effort = "xhigh"' in home_config
    assert "local-secret" in home_config
    assert 'notify = ["/tmp/notifier"]' in home_config
    assert '[projects."/private/work"]' in home_config
    assert '[plugins."secret-local@dev"]' in home_config
    assert "local-secret" not in repo_config
    assert 'notify = ["/tmp/notifier"]' not in repo_config
    assert "[mcp_servers.ronin]" not in repo_config
    assert "[projects." not in repo_config
    assert "[plugins." not in repo_config
    assert "[agents]" not in repo_config
    assert "max_depth" not in repo_config
    assert "max_threads" not in repo_config
    assert "job_max_runtime_seconds" not in repo_config
    assert 'env_vars = ["BRAVE_API_KEY"]' in repo_config


def test_sync_codex_entrypoint_targets_codex_global_bridge(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    repo_root = home_dir / "dev" / "projects" / "agents"
    codex_home = home_dir / ".codex"
    codex_home.mkdir(parents=True)
    (repo_root / "instructions").mkdir(parents=True)

    monkeypatch.setattr(sync_agent_stack, "CODEX_ENTRYPOINT_PATH", codex_home / "AGENTS.md")
    monkeypatch.setattr(sync_agent_stack, "CODEX_GLOBAL_MD", repo_root / "instructions" / "codex-global.md")

    ctx = SyncContext(apply=True)
    sync_codex_entrypoint(ctx)

    assert (codex_home / "AGENTS.md").is_symlink()
    assert (codex_home / "AGENTS.md").readlink() == repo_root / "instructions" / "codex-global.md"
