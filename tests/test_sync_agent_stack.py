"""Tests for sync_agent_stack rendering and merge helpers."""

import json

import pytest

from scripts import sync_agent_stack
from scripts.sync_agent_stack import (
    SyncContext,
    deploy_opencode_plugin,
    generate_project_opencode_config,
    merge_cherry_studio_config,
    merge_codex_config,
    merge_copilot_config,
    merge_opencode_config,
    merge_server_root_config,
    render_cherry_import_files,
    render_cherry_server,
    render_codex_config,
    render_codex_mcp_block,
    render_copilot_hooks,
    render_copilot_mcp,
    render_gemini_mcp,
    render_opencode_mcp,
    render_repo_mcp,
    render_standard_hooks,
    sync_codex_entrypoint,
    sync_copilot_subagent_env,
    sync_generated_json_directory,
    sync_repo_targets,
)
from wagents.platforms import base as platform_base
from wagents.platforms import cursor as cursor_platform
from wagents.platforms import opencode as opencode_platform
from wagents.platforms import vscode as vscode_platform


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


def test_chrome_devtools_renderers_use_generic_headed_persistent_profile():
    registry = {
        "servers": {
            "chrome-devtools": {
                "command": "npx",
                "args": [
                    "-y",
                    "chrome-devtools-mcp@latest",
                    "--user-data-dir=/Users/ww/.cache/chrome-devtools-mcp-login",
                    "--headless=false",
                ],
                "enabled": True,
                "startup_timeout_sec": 90,
                "timeout_ms": 600000,
                "tools": ["*"],
            }
        }
    }

    rendered_text = json.dumps(
        {
            "repo": render_repo_mcp(registry),
            "copilot": render_copilot_mcp(registry, {}),
            "gemini": render_gemini_mcp(registry, {}),
            "opencode": render_opencode_mcp(registry, {}),
            "codex": render_codex_mcp_block(registry),
        }
    )

    assert "--user-data-dir=/Users/ww/.cache/chrome-devtools-mcp-login" in rendered_text
    assert "--headless=false" in rendered_text
    assert "--browserUrl" not in rendered_text
    assert "--browser-url" not in rendered_text
    assert "--autoConnect" not in rendered_text
    assert "--auto-connect" not in rendered_text
    assert "--wsEndpoint" not in rendered_text
    assert "--ws-endpoint" not in rendered_text
    assert "--isolated" not in rendered_text


def test_docling_renderers_use_upstream_stdio_launch_shape():
    registry = {
        "servers": {
            "docling": {
                "command": "uvx",
                "args": ["--from", "docling-mcp", "docling-mcp-server", "--transport", "stdio"],
                "enabled": True,
                "transport": "stdio",
                "startup_timeout_sec": 90,
                "timeout_ms": 600000,
                "tools": ["*"],
            }
        }
    }

    repo = render_repo_mcp(registry)["mcpServers"]["docling"]
    copilot = render_copilot_mcp(registry, {})["mcpServers"]["docling"]
    gemini = render_gemini_mcp(registry, {})["docling"]
    opencode = render_opencode_mcp(registry, {})["docling"]
    codex = render_codex_mcp_block(registry)

    expected_args = ["--from", "docling-mcp", "docling-mcp-server", "--transport", "stdio"]
    assert repo["args"] == expected_args
    assert copilot["args"] == expected_args
    assert gemini["args"] == expected_args
    assert opencode["command"] == ["uvx", *expected_args]
    assert 'args = ["--from", "docling-mcp", "docling-mcp-server", "--transport", "stdio"]' in codex
    assert "docling-mcp==" not in json.dumps(
        {"repo": repo, "copilot": copilot, "gemini": gemini, "opencode": opencode, "codex": codex}
    )


def test_standard_hook_renderers_use_harness_specific_events():
    hook_registry = {
        "version": 1,
        "hooks": [
            {
                "id": "research-readonly-write-guard",
                "logical_event": "PreToolUse",
                "matcher": "Write|Edit",
                "command": (
                    "python3 {repo_root}/hooks/wagents-hook.py research-readonly-write-guard --harness {harness}"
                ),
                "timeout": 5,
                "harnesses": ["codex", "gemini-cli"],
            }
        ],
    }

    codex = sync_agent_stack.render_standard_hooks(hook_registry, "codex")
    gemini = sync_agent_stack.render_standard_hooks(hook_registry, "gemini-cli")

    assert "PreToolUse" in codex["hooks"]
    assert "--harness codex" in codex["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    assert "BeforeTool" in gemini["hooks"]
    assert "--harness gemini-cli" in gemini["hooks"]["BeforeTool"][0]["hooks"][0]["command"]
    assert "PreToolUse" not in gemini["hooks"]


def test_merge_codex_hooks_preserves_local_and_replaces_generated(tmp_path, monkeypatch):
    hooks_path = tmp_path / "hooks.json"
    hooks_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "UserPromptSubmit": [{"hooks": [{"command": "echo local"}]}],
                    "PreToolUse": [{"hooks": [{"command": "python3 /old/hooks/wagents-hook.py old"}]}],
                }
            }
        )
    )
    hook_registry = {
        "version": 1,
        "hooks": [
            {
                "id": "research-readonly-write-guard",
                "logical_event": "PreToolUse",
                "matcher": "Write|Edit",
                "command": (
                    "python3 {repo_root}/hooks/wagents-hook.py research-readonly-write-guard --harness {harness}"
                ),
                "timeout": 5,
                "harnesses": ["codex"],
            }
        ],
    }

    monkeypatch.setattr(sync_agent_stack, "CODEX_HOOKS_PATH", hooks_path)
    ctx = SyncContext(apply=True)
    sync_agent_stack.merge_codex_hooks(ctx, hook_registry)

    payload = json.loads(hooks_path.read_text(encoding="utf-8"))
    assert payload["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"] == "echo local"
    assert len(payload["hooks"]["PreToolUse"]) == 1
    assert "--harness codex" in payload["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    assert "/old/hooks/wagents-hook.py" not in json.dumps(payload)


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


def test_hook_registry_renders_research_hooks_for_supported_harnesses():
    registry = {
        "version": 1,
        "hooks": [
            {
                "id": "research-readonly-write-guard",
                "logical_event": "PreToolUse",
                "matcher": "Write|Edit|MultiEdit",
                "command": (
                    "python3 {repo_root}/hooks/wagents-hook.py research-readonly-write-guard --harness {harness}"
                ),
                "timeout": 5,
                "description": "Block research writes.",
                "harnesses": ["codex", "claude-code", "github-copilot", "gemini-cli"],
            },
            {
                "id": "research-stop-verifier",
                "logical_event": "Stop",
                "command": "python3 {repo_root}/hooks/wagents-hook.py research-stop-verifier --harness {harness}",
                "timeout": 30,
                "harnesses": ["codex", "gemini-cli"],
            },
        ],
    }

    codex = render_standard_hooks(registry, "codex")
    gemini = render_standard_hooks(registry, "gemini-cli")
    copilot = render_copilot_hooks(registry)

    codex_command = codex["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    gemini_command = gemini["hooks"]["BeforeTool"][0]["hooks"][0]["command"]
    copilot_command = copilot["hooks"]["preToolUse"][0]["bash"]

    assert "research-readonly-write-guard --harness codex" in codex_command
    assert str(sync_agent_stack.REPO_ROOT) in codex_command
    assert "research-readonly-write-guard --harness gemini-cli" in gemini_command
    assert gemini["hooks"]["BeforeTool"][0]["hooks"][0]["timeout"] == 5000
    assert "research-readonly-write-guard --harness github-copilot" in copilot_command
    assert "./hooks/wagents-hook.py" in copilot_command
    assert "Stop" in codex["hooks"]
    assert "AfterAgent" in gemini["hooks"]


def test_render_codex_config_enables_hooks_feature():
    registry = {"servers": {}}
    policy = {"model_defaults": {"codex": {"model": "gpt-5.5", "reasoning_effort": "high", "personality": "pragmatic"}}}

    rendered = render_codex_config("", registry, policy, include_local_extras=False)

    assert "\n[features]\n" in rendered
    assert "codex_hooks = true" in rendered


def test_render_codex_config_adds_lmstudio_provider_profile():
    registry = {"servers": {}}
    policy = {
        "local_llm_providers": {
            "lmstudio": {
                "name": "LM Studio (local)",
                "base_url_env": "LM_STUDIO_API_BASE",
                "base_url_env_aliases": ["LMSTUDIO_API_BASE"],
                "default_base_url": "http://127.0.0.1:1234/v1",
                "default_model": "local-model",
                "codex": {"provider_id": "local-lmstudio", "profile": "local-lmstudio", "wire_api": "responses"},
            }
        }
    }

    rendered = render_codex_config("", registry, policy, include_local_extras=False)

    assert "\n[model_providers.local-lmstudio]\n" in rendered
    assert 'name = "LM Studio (local)"' in rendered
    assert 'base_url = "http://127.0.0.1:1234/v1"' in rendered
    assert 'wire_api = "responses"' in rendered
    assert "\n[profiles.local-lmstudio]\n" in rendered
    assert 'model = "local-model"' in rendered
    assert 'model_provider = "local-lmstudio"' in rendered


def test_render_codex_config_uses_lmstudio_env_for_home_config(monkeypatch):
    registry = {"servers": {}}
    policy = {
        "local_llm_providers": {
            "lmstudio": {
                "base_url_env": "LM_STUDIO_API_BASE",
                "base_url_env_aliases": ["LMSTUDIO_API_BASE"],
                "default_base_url": "http://127.0.0.1:1234/v1",
                "default_model": "local-model",
            }
        }
    }
    monkeypatch.setenv("LM_STUDIO_API_BASE", "http://localhost:1234/v1")

    home_config = render_codex_config("", registry, policy, include_local_extras=True)
    repo_config = render_codex_config("", registry, policy, include_local_extras=False)

    assert 'base_url = "http://localhost:1234/v1"' in home_config
    assert 'base_url = "http://127.0.0.1:1234/v1"' in repo_config


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


def test_merge_opencode_config_adds_lmstudio_provider_and_preserves_custom_models(tmp_path, monkeypatch):
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
                "provider": {
                    "lmstudio": {
                        "models": {"custom-model": {"name": "Custom Local Model"}},
                        "options": {"headers": {"X-Local": "1"}},
                    }
                },
                "mcp": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(sync_agent_stack, "HOME", home_dir)
    monkeypatch.setattr(sync_agent_stack, "REPO_ROOT", repo_root)
    monkeypatch.setattr(sync_agent_stack, "GLOBAL_MD", repo_root / "instructions" / "global.md")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_GLOBAL_MD", repo_root / "instructions" / "opencode-global.md")
    monkeypatch.setattr(sync_agent_stack, "SKILLS_DIR", repo_root / "skills")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_CONFIG_PATH", config_path)

    policy = {
        "local_llm_providers": {
            "lmstudio": {
                "name": "LM Studio (local)",
                "base_url_env": "LM_STUDIO_API_BASE",
                "default_base_url": "http://127.0.0.1:1234/v1",
                "default_model": "local-model",
                "opencode": {
                    "npm": "@ai-sdk/openai-compatible",
                    "models": {"local-model": {"name": "LM Studio Local Model"}},
                },
            }
        }
    }

    ctx = SyncContext(apply=True)
    merge_opencode_config(ctx, {"servers": {}}, {"LM_STUDIO_API_BASE": "http://localhost:9999/v1"}, policy)
    payload = json.loads(config_path.read_text(encoding="utf-8"))

    provider = payload["provider"]["lmstudio"]
    assert provider["npm"] == "@ai-sdk/openai-compatible"
    assert provider["name"] == "LM Studio (local)"
    assert provider["options"]["baseURL"] == "http://localhost:9999/v1"
    assert provider["options"]["headers"] == {"X-Local": "1"}
    assert provider["models"]["local-model"] == {"name": "LM Studio Local Model"}
    assert provider["models"]["custom-model"] == {"name": "Custom Local Model"}


def test_merge_opencode_config_preserves_existing_model_settings(tmp_path, monkeypatch):
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
                "model": "user/model",
                "small_model": "user/small-model",
                "mode": {
                    "build": {"model": "user/build-model"},
                    "plan": {"model": "user/plan-model"},
                },
                "agent": {
                    "build": {"model": "user/agent-build-model"},
                    "plan": {"model": "user/agent-plan-model"},
                },
            }
        )
    )

    monkeypatch.setattr(sync_agent_stack, "HOME", home_dir)
    monkeypatch.setattr(sync_agent_stack, "REPO_ROOT", repo_root)
    monkeypatch.setattr(sync_agent_stack, "GLOBAL_MD", repo_root / "instructions" / "global.md")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_GLOBAL_MD", repo_root / "instructions" / "opencode-global.md")
    monkeypatch.setattr(sync_agent_stack, "SKILLS_DIR", repo_root / "skills")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_CONFIG_PATH", config_path)

    policy = {
        "model_defaults": {
            "opencode": {
                "model": "repo/default-should-not-apply",
                "small_model": "repo/small-default-should-not-apply",
            }
        }
    }

    ctx = SyncContext(apply=True)
    merge_opencode_config(ctx, {"servers": {}}, {}, policy)
    payload = json.loads(config_path.read_text())

    assert payload["model"] == "user/model"
    assert payload["small_model"] == "user/small-model"
    assert payload["mode"]["build"]["model"] == "user/build-model"
    assert payload["mode"]["plan"]["model"] == "user/plan-model"
    assert payload["agent"]["build"]["model"] == "user/agent-build-model"
    assert payload["agent"]["plan"]["model"] == "user/agent-plan-model"


def test_merge_opencode_config_preserves_custom_agent_models(tmp_path, monkeypatch):
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
                "agent": {
                    "custom-agent-1": {"model": "user/custom-model"},
                    "custom-agent-2": {"model": "user/another-model", "other": "value"},
                },
            }
        )
    )

    monkeypatch.setattr(sync_agent_stack, "HOME", home_dir)
    monkeypatch.setattr(sync_agent_stack, "REPO_ROOT", repo_root)
    monkeypatch.setattr(sync_agent_stack, "GLOBAL_MD", repo_root / "instructions" / "global.md")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_GLOBAL_MD", repo_root / "instructions" / "opencode-global.md")
    monkeypatch.setattr(sync_agent_stack, "SKILLS_DIR", repo_root / "skills")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_CONFIG_PATH", config_path)

    policy = {"model_defaults": {"opencode": {"model": "repo/default-should-not-apply"}}}

    ctx = SyncContext(apply=True)
    merge_opencode_config(ctx, {"servers": {}}, {}, policy)
    payload = json.loads(config_path.read_text())

    assert payload["agent"]["custom-agent-1"]["model"] == "user/custom-model"
    assert payload["agent"]["custom-agent-2"]["model"] == "user/another-model"
    assert payload["agent"]["custom-agent-2"]["other"] == "value"


def test_merge_opencode_config_creates_model_neutral_dcp_config(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    config_path = home_dir / ".config" / "opencode" / "opencode.json"
    dcp_path = home_dir / ".config" / "opencode" / "dcp.jsonc"
    template_path = tmp_path / "opencode-dcp.jsonc"

    dcp_path.parent.mkdir(parents=True)
    template_path.write_text(
        json.dumps(
            {
                "$schema": "https://raw.githubusercontent.com/Opencode-DCP/opencode-dynamic-context-pruning/master/dcp.schema.json",
                "enabled": True,
                "debug": False,
                "compress": {
                    "mode": "range",
                    "maxContextLimit": "85%",
                    "minContextLimit": "55%",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(sync_agent_stack, "OPENCODE_CONFIG_PATH", config_path)
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_DCP_CONFIG_PATH", dcp_path)
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_DCP_TEMPLATE_PATH", template_path)

    ctx = SyncContext(apply=True)
    merge_opencode_config(ctx, {"servers": {}}, {}, {"model_defaults": {"opencode": {"model": "ignored"}}})
    payload = json.loads(dcp_path.read_text(encoding="utf-8"))

    assert not config_path.exists()
    assert payload["enabled"] is True
    assert payload["compress"]["mode"] == "range"
    assert payload["compress"]["maxContextLimit"] == "85%"
    assert "modelMaxLimits" not in payload["compress"]
    assert "modelMinLimits" not in payload["compress"]
    assert "model" not in payload
    assert "small_model" not in payload
    assert "mode" not in payload
    assert "agent" not in payload


def test_merge_opencode_config_preserves_safe_dcp_overrides(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    config_path = home_dir / ".config" / "opencode" / "opencode.json"
    dcp_path = home_dir / ".config" / "opencode" / "dcp.jsonc"
    template_path = tmp_path / "opencode-dcp.jsonc"

    dcp_path.parent.mkdir(parents=True)
    template_path.write_text(
        json.dumps(
            {
                "$schema": "schema",
                "enabled": True,
                "compress": {
                    "mode": "range",
                    "showCompression": False,
                    "maxContextLimit": "85%",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    dcp_path.write_text(
        json.dumps(
            {
                "$schema": "schema",
                "enabled": False,
                "customKey": "preserve",
                "model": "remove-me",
                "agent": {"custom": {"model": "remove-me"}},
                "compress": {
                    "showCompression": True,
                    "modelMaxLimits": {"openai/gpt-5.5": 200000},
                    "modelMinLimits": {"openai/gpt-5.5": 100000},
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(sync_agent_stack, "OPENCODE_CONFIG_PATH", config_path)
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_DCP_CONFIG_PATH", dcp_path)
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_DCP_TEMPLATE_PATH", template_path)

    ctx = SyncContext(apply=True)
    merge_opencode_config(ctx, {"servers": {}}, {}, {})
    payload = json.loads(dcp_path.read_text(encoding="utf-8"))

    assert payload["enabled"] is False
    assert payload["customKey"] == "preserve"
    assert payload["compress"]["mode"] == "range"
    assert payload["compress"]["showCompression"] is True
    assert "modelMaxLimits" not in payload["compress"]
    assert "modelMinLimits" not in payload["compress"]
    assert "model" not in payload
    assert "agent" not in payload


def test_repo_opencode_dcp_config_uses_proactive_thresholds():
    payload = json.loads(sync_agent_stack.OPENCODE_DCP_TEMPLATE_PATH.read_text(encoding="utf-8"))

    compress = payload["compress"]
    assert compress["mode"] == "range"
    assert compress["maxContextLimit"] == "70%"
    assert compress["minContextLimit"] == "40%"
    assert compress["nudgeFrequency"] == 2
    assert compress["iterationNudgeThreshold"] == 8
    assert compress["nudgeForce"] == "strong"
    assert "modelMaxLimits" not in compress
    assert "modelMinLimits" not in compress


def test_deploy_opencode_plugin_copies_file(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    plugins_dir = repo_root / "platforms" / "opencode" / "plugins"
    plugins_dir.mkdir(parents=True)
    (plugins_dir / "approval-notify.ts").write_text("export const Plugin = {}", encoding="utf-8")

    home_dir = tmp_path / "home"
    opencode_plugins = home_dir / ".config" / "opencode" / "plugins"

    monkeypatch.setattr(sync_agent_stack, "REPO_ROOT", repo_root)
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_PLUGINS_DIR", opencode_plugins)

    ctx = SyncContext(apply=True)
    deploy_opencode_plugin(ctx, "approval-notify.ts")
    dest = opencode_plugins / "approval-notify.ts"

    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "export const Plugin = {}"


def test_generate_project_opencode_config_creates_file(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    config_path = repo_root / "opencode.json"

    monkeypatch.setattr(sync_agent_stack, "REPO_ROOT", repo_root)
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_REPO_CONFIG_PATH", config_path)

    ctx = SyncContext(apply=True)
    generate_project_opencode_config(ctx)
    payload = json.loads(config_path.read_text())

    assert payload["$schema"] == "https://opencode.ai/config.json"
    assert payload["instructions"] == ["AGENTS.md", "instructions/opencode-global.md"]
    assert payload["skills"]["paths"] == ["skills"]
    assert "model" not in payload
    assert "small_model" not in payload
    assert "mode" not in payload
    assert "agent" not in payload
    assert "steps" not in payload


def test_opencode_agents_do_not_enforce_model_or_steps():
    agents_dir = sync_agent_stack.REPO_ROOT / "agents"

    for agent_path in sorted(agents_dir.glob("*.md")):
        content = agent_path.read_text(encoding="utf-8")
        frontmatter = content.split("---", 2)[1]

        assert "model:" not in frontmatter, f"{agent_path.name} must inherit the runtime model"
        assert "steps:" not in frontmatter, f"{agent_path.name} must not enforce a step cap"


def test_sync_repo_targets_delegates_vscode_and_opencode_adapters(tmp_path, monkeypatch):
    registry_path = tmp_path / "config" / "mcp-registry.json"
    hook_path = tmp_path / "config" / "hook-registry.json"
    called: list[str] = []

    monkeypatch.setattr(sync_agent_stack, "MCP_REGISTRY_PATH", registry_path)
    monkeypatch.setattr(sync_agent_stack, "HOOK_REGISTRY_PATH", hook_path)
    monkeypatch.setattr(sync_agent_stack, "generate_codex_global_instructions", lambda ctx: None)
    monkeypatch.setattr(sync_agent_stack, "generate_copilot_repo_instructions", lambda ctx: None)
    monkeypatch.setattr(sync_agent_stack, "generate_copilot_rule_instructions", lambda ctx: None)
    monkeypatch.setattr(sync_agent_stack, "generate_copilot_hooks", lambda ctx, hook_registry: None)
    monkeypatch.setattr(
        sync_agent_stack,
        "sync_platform_repo_target",
        lambda name, ctx, registry, hook_registry, policy: called.append(name),
    )

    registry = {"servers": {}}
    hook_registry = {"hooks": []}
    policy = {"model_defaults": {}}

    ctx = SyncContext(apply=True)
    sync_repo_targets(ctx, registry, hook_registry, policy)

    assert json.loads(registry_path.read_text(encoding="utf-8")) == registry
    assert json.loads(hook_path.read_text(encoding="utf-8")) == hook_registry
    assert called == ["vscode", "opencode"]


def test_vscode_adapter_render_mcp_preserves_env_placeholders(monkeypatch):
    monkeypatch.setenv("EXAMPLE_TOKEN", "real-secret")
    adapter = vscode_platform.Adapter()
    registry = {
        "servers": {
            "example": {
                "command": "uvx",
                "args": ["example-mcp", "${EXAMPLE_TOKEN}"],
                "enabled": True,
                "env": {"TOKEN": {"env_var": "EXAMPLE_TOKEN"}},
                "timeout_ms": 5000,
            }
        }
    }

    rendered = adapter.render_mcp(registry, {})

    assert rendered == {
        "mcpServers": {
            "example": {
                "command": "uvx",
                "args": ["example-mcp", "${EXAMPLE_TOKEN}"],
                "env": {"TOKEN": "${EXAMPLE_TOKEN}"},
                "timeout": 5000,
            }
        }
    }


def test_cursor_adapter_sync_home_preserves_existing_unknown_mcp_servers(tmp_path, monkeypatch):
    config_path = tmp_path / "mcp.json"
    config_path.write_text(
        json.dumps(
            {
                "mcpServers": {"custom": {"command": "custom-mcp"}},
                "other": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cursor_platform, "CURSOR_MCP_PATH", config_path)

    adapter = cursor_platform.Adapter()
    ctx = cursor_platform.SyncContext(apply=True)
    registry = {
        "servers": {
            "managed": {
                "command": "uvx",
                "args": ["managed-mcp"],
                "enabled": True,
            }
        }
    }

    adapter.sync_home(ctx, registry, {}, {}, {})
    payload = json.loads(config_path.read_text(encoding="utf-8"))

    assert payload["other"] is True
    assert payload["mcpServers"] == {
        "custom": {
            "command": "custom-mcp",
        },
        "managed": {
            "command": "uvx",
            "args": ["managed-mcp"],
        },
    }


def test_opencode_adapter_sync_home_adds_lmstudio_provider_and_preserves_custom_models(tmp_path, monkeypatch):
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
                "provider": {
                    "lmstudio": {
                        "models": {"custom-model": {"name": "Custom Local Model"}},
                        "options": {"headers": {"X-Local": "1"}},
                    }
                },
                "mcp": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(platform_base, "HOME", home_dir)
    monkeypatch.setattr(opencode_platform, "OPENCODE_CONFIG_PATH", config_path)
    monkeypatch.setattr(opencode_platform, "GLOBAL_MD", repo_root / "instructions" / "global.md")
    monkeypatch.setattr(opencode_platform, "OPENCODE_GLOBAL_MD", repo_root / "instructions" / "opencode-global.md")
    monkeypatch.setattr(opencode_platform, "SKILLS_DIR", repo_root / "skills")
    monkeypatch.setattr(opencode_platform.Adapter, "_deploy_plugins", lambda self, ctx: None)

    policy = {
        "local_llm_providers": {
            "lmstudio": {
                "name": "LM Studio (local)",
                "base_url_env": "LM_STUDIO_API_BASE",
                "default_base_url": "http://127.0.0.1:1234/v1",
                "default_model": "local-model",
                "opencode": {
                    "npm": "@ai-sdk/openai-compatible",
                    "models": {"local-model": {"name": "LM Studio Local Model"}},
                },
            }
        }
    }

    adapter = opencode_platform.Adapter()
    ctx = opencode_platform.SyncContext(apply=True)
    adapter.sync_home(ctx, {"servers": {}}, policy, {"LM_STUDIO_API_BASE": "http://localhost:9999/v1"}, {})
    payload = json.loads(config_path.read_text(encoding="utf-8"))

    provider = payload["provider"]["lmstudio"]
    assert provider["npm"] == "@ai-sdk/openai-compatible"
    assert provider["name"] == "LM Studio (local)"
    assert provider["options"]["baseURL"] == "http://localhost:9999/v1"
    assert provider["options"]["headers"] == {"X-Local": "1"}
    assert provider["models"]["local-model"] == {"name": "LM Studio Local Model"}
    assert provider["models"]["custom-model"] == {"name": "Custom Local Model"}


def test_opencode_adapter_sync_home_manages_dcp_config_without_model_limits(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    repo_root = home_dir / "dev" / "projects" / "agents"
    config_path = home_dir / ".config" / "opencode" / "opencode.json"
    dcp_path = home_dir / ".config" / "opencode" / "dcp.jsonc"
    template_path = repo_root / "config" / "opencode-dcp.jsonc"

    repo_root.mkdir(parents=True)
    config_path.parent.mkdir(parents=True)
    template_path.parent.mkdir(parents=True)
    config_path.write_text("{}\n", encoding="utf-8")
    template_path.write_text(
        json.dumps(
            {
                "$schema": "https://raw.githubusercontent.com/Opencode-DCP/opencode-dynamic-context-pruning/master/dcp.schema.json",
                "enabled": True,
                "compress": {
                    "mode": "range",
                    "maxContextLimit": "85%",
                    "minContextLimit": "55%",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    dcp_path.write_text(
        json.dumps(
            {
                "customKey": "preserve",
                "small_model": "remove-me",
                "compress": {
                    "modelMaxLimits": {"openai/gpt-5.5": 200000},
                    "modelMinLimits": {"openai/gpt-5.5": 100000},
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(opencode_platform, "OPENCODE_CONFIG_PATH", config_path)
    monkeypatch.setattr(opencode_platform, "OPENCODE_DCP_CONFIG_PATH", dcp_path)
    monkeypatch.setattr(opencode_platform, "OPENCODE_DCP_TEMPLATE_PATH", template_path)
    monkeypatch.setattr(opencode_platform.Adapter, "_deploy_plugins", lambda self, ctx: None)

    adapter = opencode_platform.Adapter()
    ctx = opencode_platform.SyncContext(apply=True)
    adapter.sync_home(ctx, {"servers": {}}, {}, {}, {})
    payload = json.loads(dcp_path.read_text(encoding="utf-8"))

    assert payload["enabled"] is True
    assert payload["customKey"] == "preserve"
    assert payload["compress"]["mode"] == "range"
    assert payload["compress"]["maxContextLimit"] == "85%"
    assert "modelMaxLimits" not in payload["compress"]
    assert "modelMinLimits" not in payload["compress"]
    assert "small_model" not in payload


def test_merge_cherry_studio_config_no_op_when_missing(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    cherry_dir = home_dir / "Library" / "Application Support" / "CherryStudio"

    monkeypatch.setattr(sync_agent_stack, "HOME", home_dir)
    monkeypatch.setattr(sync_agent_stack, "CHERRY_STUDIO_DIR", cherry_dir)

    ctx = SyncContext(apply=True)
    merge_cherry_studio_config(ctx)
    assert not cherry_dir.exists()


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
    assert "tool_timeout_sec = 600" in rendered
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
    policy = {"model_defaults": {"codex": {"model": "gpt-5.5", "reasoning_effort": "high", "personality": "pragmatic"}}}
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
    assert 'approval_policy = "never"' in home_config
    assert 'approvals_reviewer = "user"' in home_config
    assert 'sandbox_mode = "danger-full-access"' in home_config
    assert '[profiles.deep]\napproval_policy = "on-request"\napprovals_reviewer = "guardian_subagent"' in home_config
    assert 'model = "gpt-5.5"' in home_config
    assert 'model_reasoning_effort = "high"' in home_config
    assert 'plan_mode_reasoning_effort = "high"' in home_config
    assert 'model_reasoning_effort = "xhigh"' in home_config
    assert "[skills]" in home_config
    assert "include_instructions = false" in home_config
    assert 'status_line = ["model-with-reasoning", "context-remaining", "current-dir"]' in home_config
    assert 'status_line = ["model", "approval", "sandbox", "cwd"]' not in home_config
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


def test_merge_copilot_config_preserves_camel_case_settings_keys(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "trustedFolders": ["/Users/ww"],
                "model": "old-model",
                "effortLevel": "medium",
                "allowed_urls": ["https://docs.github.com"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sync_agent_stack, "COPILOT_SETTINGS_PATH", config_path)
    policy = {
        "trusted_roots": ["/Users/ww/dev/projects"],
        "docs_domains": ["docs.github.com", "modelcontextprotocol.io"],
        "model_defaults": {
            "copilot": {
                "model": "gpt-5.4",
                "effort_level": "high",
                "continue_on_auto_mode": False,
            }
        },
    }

    ctx = SyncContext(apply=True)
    merge_copilot_config(ctx, policy)

    rendered = json.loads(config_path.read_text(encoding="utf-8"))
    assert rendered["trustedFolders"] == ["/Users/ww", "/Users/ww/dev/projects"]
    assert "trusted_folders" not in rendered
    assert "allowed_urls" not in rendered
    assert rendered["allowedUrls"] == ["https://docs.github.com", "https://modelcontextprotocol.io"]
    assert rendered["model"] == "gpt-5.4"
    assert rendered["effortLevel"] == "high"
    assert rendered["continueOnAutoMode"] is False


def test_merge_copilot_config_creates_missing_settings_file(tmp_path, monkeypatch):
    config_path = tmp_path / "settings.json"
    monkeypatch.setattr(sync_agent_stack, "COPILOT_SETTINGS_PATH", config_path)
    policy = {
        "trusted_roots": ["/Users/ww/dev/projects"],
        "docs_domains": ["docs.github.com", "modelcontextprotocol.io"],
        "model_defaults": {
            "copilot": {
                "model": "gpt-5.4",
                "effort_level": "high",
                "continue_on_auto_mode": False,
            }
        },
    }

    ctx = SyncContext(apply=True)
    merge_copilot_config(ctx, policy)

    rendered = json.loads(config_path.read_text(encoding="utf-8"))
    assert rendered == {
        "model": "gpt-5.4",
        "effortLevel": "high",
        "continueOnAutoMode": False,
        "trustedFolders": ["/Users/ww/dev/projects"],
        "allowedUrls": ["https://docs.github.com", "https://modelcontextprotocol.io"],
    }


def test_load_json_raises_for_missing_required_file(tmp_path):
    missing = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        sync_agent_stack.load_json(missing)


def test_sync_copilot_subagent_env_writes_bounded_limits(tmp_path, monkeypatch):
    env_path = tmp_path / "copilot-subagents.env"
    monkeypatch.setattr(sync_agent_stack, "COPILOT_SUBAGENTS_ENV_PATH", env_path)
    policy = {
        "model_defaults": {
            "copilot": {
                "subagent_limits": {
                    "max_concurrent": 2,
                    "max_depth": 1,
                }
            }
        }
    }

    ctx = SyncContext(apply=True)
    sync_copilot_subagent_env(ctx, policy)

    assert env_path.read_text(encoding="utf-8") == (
        "# Managed by /Users/ww/dev/projects/agents/scripts/sync_agent_stack.py.\n"
        'export COPILOT_SUBAGENT_MAX_CONCURRENT="2"\n'
        'export COPILOT_SUBAGENT_MAX_DEPTH="1"\n'
    )


def test_sync_copilot_subagent_env_unsets_limits_when_unbounded(tmp_path, monkeypatch):
    env_path = tmp_path / "copilot-subagents.env"
    monkeypatch.setattr(sync_agent_stack, "COPILOT_SUBAGENTS_ENV_PATH", env_path)
    policy = {"model_defaults": {"copilot": {"model": "gpt-5.4"}}}

    ctx = SyncContext(apply=True)
    sync_copilot_subagent_env(ctx, policy)

    assert env_path.read_text(encoding="utf-8") == (
        "# Managed by /Users/ww/dev/projects/agents/scripts/sync_agent_stack.py.\n"
        "unset COPILOT_SUBAGENT_MAX_CONCURRENT\n"
        "unset COPILOT_SUBAGENT_MAX_DEPTH\n"
    )


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
    assert (codex_home / "AGENTS.md").resolve() == repo_root / "instructions" / "codex-global.md"
