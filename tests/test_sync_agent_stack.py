"""Tests for sync_agent_stack rendering and merge helpers."""

import json
import tomllib

import pytest

from scripts import sync_agent_stack
from scripts.mcphub.validate_settings import validate_settings
from scripts.sync_agent_stack import (
    SyncContext,
    deploy_opencode_plugin,
    generate_project_opencode_config,
    merge_cherry_studio_config,
    merge_codex_config,
    merge_opencode_config,
    merge_server_maps,
    merge_server_root_config,
    render_cherry_import_files,
    render_cherry_server,
    render_client_mcp,
    render_codex_config,
    render_codex_hooks,
    render_codex_mcp_block,
    render_flat_mcp,
    render_opencode_mcp,
    render_repo_mcp,
    render_standard_hooks,
    strip_managed_opencode_mcphub_entries,
    sync_codex_entrypoint,
    sync_generated_json_directory,
    sync_opencode_notifier_config,
    sync_repo_targets,
)
from wagents.platforms import base as platform_base
from wagents.platforms import codex as codex_platform
from wagents.platforms import cursor as cursor_platform
from wagents.platforms import opencode as opencode_platform
from wagents.platforms import vscode as vscode_platform
from wagents.platforms.grok import render_grok_mcp_block


def assert_opencode_model_matrix(payload: dict) -> None:
    assert payload["model"] == "openai/gpt-5.5"
    assert payload["small_model"] == "openai/gpt-5.4-mini"
    for agent_name in ("build", "plan", "explore", "general"):
        agent = payload["agent"][agent_name]
        assert agent["model"] == "openai/gpt-5.5"
        assert agent["variant"] == "xhigh"
        assert agent["options"] == {"reasoningEffort": "xhigh"}

    providers = payload.get("provider", {})
    assert set(providers).isdisjoint({"vercel", "opencode-go", "kimi-for-coding"})
    openai = providers["openai"]
    assert openai["options"]["reasoningEffort"] == "xhigh"
    assert openai["options"]["websearch_cited"] == {"model": "gpt-5.5"}
    assert set(openai["models"]) == {"gpt-5.5", "gpt-5.4-mini", "gpt-5.3-codex-spark"}
    for model in openai["models"].values():
        assert model["variants"]["high"] == {
            "include": ["reasoning.encrypted_content"],
            "reasoningEffort": "high",
            "reasoningSummary": None,
            "textVerbosity": "low",
        }
        assert model["variants"]["xhigh"] == {
            "include": ["reasoning.encrypted_content"],
            "reasoningEffort": "xhigh",
            "reasoningSummary": None,
            "textVerbosity": "low",
        }
        assert model["variants"]["medium"] == {
            "include": ["reasoning.encrypted_content"],
            "reasoningEffort": "medium",
            "reasoningSummary": None,
        }
        assert '"reasoningSummary": "auto"' not in json.dumps(model)


def group_server_name(server: object) -> str:
    if isinstance(server, str):
        return server
    if isinstance(server, dict):
        name = server.get("name")
        if isinstance(name, str):
            return name
    raise AssertionError(f"invalid group server entry: {server!r}")


def group_server_names(group: dict) -> list[str]:
    return [group_server_name(server) for server in group["servers"]]


def mcphub_registry():
    return {
        "mcphub": {
            "enabled": True,
            "base_url": "http://127.0.0.1:46683",
            "bearer_token_env_var": "MCPHUB_BEARER_TOKEN",
            "startup_timeout_sec": 90,
            "tool_timeout_sec": 90,
            "smart_routing": {"enabled": True, "path": "$smart"},
            "groups": {
                "code": {"enabled": True, "servers": ["foo"]},
                "research": {"enabled": True, "servers": ["bar"]},
            },
            "clients": {
                "codex": {
                    "included_endpoint_kinds": ["all"],
                    "enabled_endpoint_kinds": ["all"],
                    "enable_server_endpoints": False,
                },
                "opencode": {
                    "included_endpoint_kinds": ["all"],
                    "enabled_endpoint_kinds": ["all"],
                    "enable_server_endpoints": False,
                    "server_endpoint_name_style": "base",
                },
            },
        },
        "servers": {
            "foo": {"command": "uvx", "args": ["foo-mcp"], "enabled": True, "env": {}},
            "bar": {"command": "uvx", "args": ["bar-mcp"], "enabled": True, "env": {}},
        },
    }


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
            "environment": {"FOO_TOKEN": "${FOO_TOKEN}"},
        }
    }


def test_render_codex_mcp_block_projects_mcphub_http_endpoints():
    rendered = render_codex_mcp_block(mcphub_registry())

    assert "[mcp_servers.mcphub_all]" in rendered
    assert 'url = "http://127.0.0.1:46683/mcp"' in rendered
    assert 'bearer_token_env_var = "MCPHUB_BEARER_TOKEN"' in rendered
    assert "startup_timeout_sec = 90" in rendered
    assert "tool_timeout_sec = 90" in rendered
    assert "[mcp_servers.mcphub_group_code]" not in rendered
    assert "[mcp_servers.mcphub_smart_group_code]" not in rendered
    assert "enabled = true" in rendered


def test_render_client_mcp_projects_remote_stdio_bridge_for_stdio_clients(monkeypatch):
    monkeypatch.delenv("MCPHUB_BEARER_TOKEN", raising=False)
    rendered = render_client_mcp(mcphub_registry(), {}, "claude-desktop")["mcpServers"]

    assert rendered["mcphub_all"]["command"].endswith("scripts/mcphub/remote-stdio.sh")
    assert rendered["mcphub_all"]["args"] == ["http://127.0.0.1:46683/mcp"]
    assert rendered["mcphub_all"]["env"] == {"MCPHUB_BEARER_TOKEN": "${MCPHUB_BEARER_TOKEN}"}
    assert rendered["mcphub_smart_all"]["disabled"] is True


def test_vscode_repo_mcp_keeps_mcphub_token_placeholder(monkeypatch):
    monkeypatch.setenv("MCPHUB_BEARER_TOKEN", "local-secret")

    rendered = vscode_platform.Adapter().render_mcp(mcphub_registry(), {}, harness="repo-mcp")["mcpServers"]

    assert rendered["mcphub_all"]["env"] == {"MCPHUB_BEARER_TOKEN": "${MCPHUB_BEARER_TOKEN}"}
    assert "local-secret" not in json.dumps(rendered)


def test_render_client_mcp_can_project_public_mcphub_url_for_chatgpt(monkeypatch):
    monkeypatch.delenv("MCPHUB_BEARER_TOKEN", raising=False)
    registry = mcphub_registry()
    registry["mcphub"]["public_url"] = "https://mcp.w4w.dev/mcp"
    registry["mcphub"]["clients"]["chatgpt"] = {
        "url_source": "public",
        "included_endpoint_kinds": ["all"],
        "enabled_endpoint_kinds": ["all"],
        "enable_server_endpoints": False,
    }

    rendered = render_client_mcp(registry, {}, "chatgpt")["mcpServers"]

    assert list(rendered) == ["mcphub_all"]
    assert rendered["mcphub_all"]["args"] == ["https://mcp.w4w.dev/mcp"]
    assert rendered["mcphub_all"]["env"] == {"MCPHUB_BEARER_TOKEN": "${MCPHUB_BEARER_TOKEN}"}


def test_render_opencode_mcp_projects_remote_mcphub_entries(monkeypatch):
    monkeypatch.delenv("MCPHUB_BEARER_TOKEN", raising=False)
    rendered = render_opencode_mcp(mcphub_registry(), {})

    assert list(rendered) == ["mcphub_all"]
    assert rendered["mcphub_all"] == {
        "type": "remote",
        "url": "http://127.0.0.1:46683/mcp",
        "enabled": True,
        "oauth": False,
        "headers": {"Authorization": "Bearer {file:~/.config/opencode/secrets/mcphub-bearer-token}"},
    }


def test_render_opencode_mcp_keeps_bearer_token_as_file_placeholder_for_home_config():
    rendered = render_opencode_mcp(mcphub_registry(), {"MCPHUB_BEARER_TOKEN": "local-token"})

    assert rendered["mcphub_all"]["headers"] == {
        "Authorization": "Bearer {file:~/.config/opencode/secrets/mcphub-bearer-token}"
    }
    assert "local-token" not in json.dumps(rendered)


def test_opencode_adapter_keeps_bearer_token_as_file_placeholder_for_home_config():
    rendered = opencode_platform.Adapter().render_mcp(mcphub_registry(), {"MCPHUB_BEARER_TOKEN": "local-token"})

    assert rendered["mcphub_all"]["headers"] == {
        "Authorization": "Bearer {file:~/.config/opencode/secrets/mcphub-bearer-token}"
    }
    assert "local-token" not in json.dumps(rendered)


def test_repo_opencode_mcp_projects_configured_groups_and_server_endpoints():
    registry = json.loads((sync_agent_stack.REPO_ROOT / "config/mcp-registry.json").read_text(encoding="utf-8"))
    rendered = render_opencode_mcp(registry, {})
    client = registry["mcphub"]["clients"]["opencode"]
    group_names = sorted(client["included_groups"])
    server_names = sorted(registry["servers"])

    assert sorted(name for name in rendered if name.startswith("mcphub_group_")) == [
        f"mcphub_group_{name}" for name in group_names
    ]
    assert "mcphub_all" not in rendered
    assert rendered["mcphub_group_harness"]["enabled"] is True
    assert rendered["mcphub_group_harness"]["url"] == "http://127.0.0.1:46683/mcp/harness"
    assert all(name in rendered for name in server_names)
    assert all(rendered[name]["enabled"] is False for name in server_names)


def test_repo_mcphub_projects_harness_to_managed_harnesses():
    registry = json.loads((sync_agent_stack.REPO_ROOT / "config/mcp-registry.json").read_text(encoding="utf-8"))
    server_names = sorted(registry["servers"])
    prefixed_server_names = [f"mcphub_server_{name}" for name in server_names]

    codex = render_codex_mcp_block(registry)
    codex_payload = tomllib.loads(codex)
    assert "[mcp_servers.mcphub_all]" not in codex
    assert "[mcp_servers.mcphub_group_harness]" in codex
    assert 'url = "http://127.0.0.1:46683/mcp/harness"' in codex
    assert sorted(name for name in codex_payload["mcp_servers"] if name.startswith("mcphub_server_")) == sorted(
        prefixed_server_names
    )
    assert codex_payload["mcp_servers"]["mcphub_group_harness"]["enabled"] is True
    assert all(codex_payload["mcp_servers"][name]["enabled"] is False for name in prefixed_server_names)

    claude = render_client_mcp(registry, {}, "claude-desktop")["mcpServers"]
    assert list(claude) == ["mcphub_group_harness", "mcphub_group_nlm", *prefixed_server_names]
    assert claude["mcphub_group_harness"]["disabled"] is False
    assert all(claude[name]["disabled"] is True for name in prefixed_server_names)

    chatgpt = render_client_mcp(registry, {}, "chatgpt")["mcpServers"]
    assert list(chatgpt) == ["mcphub_group_tunnel"]
    assert chatgpt["mcphub_group_tunnel"]["args"] == ["https://mcp.w4w.dev/mcp/tunnel"]
    assert chatgpt["mcphub_group_tunnel"]["disabled"] is False

    grok = render_grok_mcp_block(registry)
    grok_payload = tomllib.loads(grok)
    assert "[mcp_servers.mcphub_all]" not in grok
    assert "[mcp_servers.mcphub_group_harness]" in grok
    assert '"Authorization" = "Bearer ${MCPHUB_BEARER_TOKEN}"' in grok
    assert sorted(name for name in grok_payload["mcp_servers"] if name.startswith("mcphub_server_")) == sorted(
        prefixed_server_names
    )
    assert grok_payload["mcp_servers"]["mcphub_group_harness"]["enabled"] is True
    assert all(grok_payload["mcp_servers"][name]["enabled"] is False for name in prefixed_server_names)


def test_repo_workflow_groups_and_bounded_clients():
    registry = json.loads((sync_agent_stack.REPO_ROOT / "config/mcp-registry.json").read_text(encoding="utf-8"))

    harness_group = registry["mcphub"]["groups"]["harness"]
    assert group_server_names(harness_group) == [
        "brave-search",
        "duckduckgo-search",
        "ddgs",
        "context7",
        "deepwiki",
        "llms-txt-explorer",
        "fetch",
        "fetcher",
        "package-version-check-mcp",
        "chrome-devtools",
        "penpot",
    ]
    assert {"name": "fetcher", "tools": ["fetch_urls"]} in harness_group["servers"]
    assert {
        "name": "llms-txt-explorer",
        "tools": ["list_websites"],
    } in harness_group["servers"]
    assert group_server_names(registry["mcphub"]["groups"]["daily"]) == [
        "brave-search",
        "duckduckgo-search",
        "ddgs",
        "context7",
        "deepwiki",
        "llms-txt-explorer",
        "fetch",
        "fetcher",
        "package-version-check-mcp",
        "trafilatura",
        "repomix",
        "chrome-devtools",
    ]
    assert registry["mcphub"]["groups"]["reasoning"]["servers"] == [
        "sequential-thinking",
        "cascade-thinking",
        "structured-thinking",
    ]
    assert "harness-safe" not in registry["mcphub"]["groups"]
    assert {"coding", "research", "review", "release", "shared-read", "credentialed", "heavy"}.issubset(
        registry["mcphub"]["groups"]
    )
    enabled_servers = {
        server_name
        for server_name, server_config in registry["servers"].items()
        if server_config.get("enabled", True) is True
    }
    for group_name, group_config in registry["mcphub"]["groups"].items():
        if group_config.get("enabled", True) is not True:
            continue
        assert set(group_server_names(group_config)).issubset(enabled_servers), group_name
    expected_client = {
        "included_endpoint_kinds": ["group", "server"],
        "included_groups": ["harness", "nlm"],
        "enabled_endpoint_kinds": ["group"],
        "enabled_groups": ["harness", "nlm"],
        "enable_server_endpoints": True,
    }
    for name in ("default", "codex", "grok", "opencode"):
        client = registry["mcphub"]["clients"][name]
        for key, value in expected_client.items():
            assert client[key] == value
    assert registry["mcphub"]["clients"]["chatgpt"]["included_endpoint_kinds"] == ["group"]
    assert registry["mcphub"]["clients"]["chatgpt"]["included_groups"] == ["tunnel"]
    assert "included_servers" not in registry["mcphub"]["clients"]["opencode"]


def test_opencode_adapter_group_only_mcphub_projection_excludes_all_and_smart():
    registry = mcphub_registry()
    registry["mcphub"]["clients"]["opencode"] = {
        "included_endpoint_kinds": ["group"],
        "enabled_endpoint_kinds": ["group"],
        "enabled_groups": ["code"],
        "enable_server_endpoints": False,
    }

    rendered = opencode_platform.Adapter().render_mcp(registry, {})

    assert set(rendered) == {"mcphub_group_code", "mcphub_group_research"}
    assert rendered["mcphub_group_code"]["enabled"] is True
    assert rendered["mcphub_group_research"]["enabled"] is False


def test_strip_managed_opencode_mcphub_entries_preserves_unrelated_mcp():
    existing = {
        "mcphub_group_code": {"type": "remote"},
        "mcphub_server_fetch": {"type": "remote"},
        "custom-local": {"type": "local"},
    }

    assert strip_managed_opencode_mcphub_entries(existing) == {"custom-local": {"type": "local"}}


def test_merge_server_maps_strips_stale_mcphub_namespace_entries():
    rendered = {"mcphub_group_harness": {"type": "remote"}}
    existing = {
        "mcphub_all": {"type": "remote"},
        "mcphub_group_code": {"type": "remote"},
        "mcphub_server_fetch": {"type": "remote"},
        "custom-local": {"type": "local"},
    }
    known = set(rendered)

    merged = merge_server_maps(rendered, existing, known)
    platform_merged = platform_base.merge_server_maps(rendered, existing, known)

    for payload in (merged, platform_merged):
        assert [name for name in payload if name.startswith("mcphub")] == ["mcphub_group_harness"]
        assert payload["custom-local"] == {"type": "local"}


def test_parse_args_default_targets_is_repo_only():
    from scripts.sync_agent_stack import parse_args

    args = parse_args(["--check"])
    assert args.targets == "repo"


def test_merge_client_mcp_config_preserves_local_only_servers(tmp_path, monkeypatch):
    from scripts import sync_agent_stack as sas

    path = tmp_path / "claude_desktop_config.json"
    path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "user-local-only": {"command": "echo", "args": ["hi"]},
                    "will-be-managed": {"command": "old"},
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(sas, "CLAUDE_DESKTOP_CONFIG_PATH", path)

    rendered = {"will-be-managed": {"command": "new", "args": []}}
    monkeypatch.setattr(
        sas,
        "render_client_mcp",
        lambda registry, fallbacks, harness=None: {"mcpServers": rendered},
    )
    ctx = sas.SyncContext(apply=True)
    sas.merge_client_mcp_config(ctx, path, {}, {}, "claude-desktop")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["mcpServers"]["user-local-only"]["command"] == "echo"
    assert payload["mcpServers"]["will-be-managed"]["command"] == "new"


def test_render_opencode_mcp_can_use_base_names_for_server_endpoint_templates():
    registry = mcphub_registry()
    registry["mcphub"]["clients"]["opencode"] = {
        "included_endpoint_kinds": ["server"],
        "enabled_endpoint_kinds": [],
        "server_endpoint_name_style": "base",
    }

    rendered = render_opencode_mcp(registry, {})

    assert set(rendered) == {"foo", "bar"}
    assert rendered["foo"]["url"].endswith("/mcp/foo")


def test_render_cherry_import_files_include_mcphub_all_group_and_server_entries():
    rendered = render_cherry_import_files(mcphub_registry(), {})

    assert "all.json" in rendered
    assert "group-code.json" in rendered
    assert "server-foo.json" in rendered
    assert "smart-code.json" in rendered
    assert rendered["all.json"]["mcpServers"]["mcphub_all"]["baseUrl"] == "http://127.0.0.1:46683/mcp"
    assert rendered["group-code.json"]["mcpServers"]["mcphub_group_code"]["baseUrl"].endswith("/mcp/code")
    assert rendered["server-foo.json"]["mcpServers"]["mcphub_server_foo"]["baseUrl"].endswith("/mcp/foo")


def test_validate_settings_catches_unknown_group_servers_and_real_looking_secrets():
    settings = {
        "mcpServers": {
            "foo": {
                "command": "uvx",
                "args": ["foo-mcp"],
                "env": {"FOO_API_KEY": "sk-real-looking"},
            }
        },
        "groups": {"bad": {"servers": ["missing"]}},
        "systemConfig": {
            "routing": {
                "enableGlobalRoute": True,
                "enableGroupNameRoute": True,
                "enableBearerAuth": True,
                "bearerAuthHeaderName": "Authorization",
                "jsonBodyLimit": "5mb",
                "skipAuth": False,
            }
        },
    }

    errors = validate_settings(settings, {"servers": {"foo": {}}})

    assert "groups.bad.servers[0] references missing server 'missing'" in errors
    assert any("FOO_API_KEY" in error for error in errors)


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


def test_chrome_devtools_renderers_use_attached_browser_launcher():
    registry = {
        "servers": {
            "chrome-devtools": {
                "command": "bash",
                "args": ["/Users/ww/dev/projects/agents/scripts/mcphub/chrome-devtools-browser-url.sh"],
                "enabled": True,
                "startup_timeout_sec": 90,
                "timeout_ms": 600000,
                "tools": ["*"],
            }
        }
    }

    rendered_text = json.dumps({
        "repo": render_repo_mcp(registry),
        "crush": render_flat_mcp(registry, {}, "crush"),
        "opencode": render_opencode_mcp(registry, {}),
        "codex": render_codex_mcp_block(registry),
    })

    assert "/Users/ww/dev/projects/agents/scripts/mcphub/chrome-devtools-browser-url.sh" in rendered_text
    assert "--browserUrl" not in rendered_text
    assert "--browser-url" not in rendered_text
    assert "--autoConnect" not in rendered_text
    assert "--auto-connect" not in rendered_text
    assert "--wsEndpoint" not in rendered_text
    assert "--ws-endpoint" not in rendered_text
    assert "--user-data-dir" not in rendered_text
    assert "--headless" not in rendered_text
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
    crush = render_flat_mcp(registry, {}, "crush")["docling"]
    opencode = render_opencode_mcp(registry, {})["docling"]
    codex = render_codex_mcp_block(registry)

    expected_args = ["--from", "docling-mcp", "docling-mcp-server", "--transport", "stdio"]
    assert repo["args"] == expected_args
    assert crush["args"] == expected_args
    assert opencode["command"] == ["uvx", *expected_args]
    assert 'args = ["--from", "docling-mcp", "docling-mcp-server", "--transport", "stdio"]' in codex
    assert "docling-mcp==" not in json.dumps({
        "repo": repo,
        "crush": crush,
        "opencode": opencode,
        "codex": codex,
    })


def test_standard_hook_renderers_use_supported_harness_events():
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
                "description": "Block research writes.",
                "harnesses": ["codex", "claude-code"],
            }
        ],
    }

    codex = render_codex_hooks(hook_registry)
    claude = sync_agent_stack.render_standard_hooks(hook_registry, "claude-code")

    assert "PreToolUse" in codex["hooks"]
    assert "--harness codex" in codex["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    assert codex["hooks"]["PreToolUse"][0]["hooks"][0]["timeout"] == 5
    assert codex["hooks"]["PreToolUse"][0]["hooks"][0]["statusMessage"] == "Block research writes."
    assert "PreToolUse" in claude["hooks"]
    assert "--harness claude-code" in claude["hooks"]["PreToolUse"][0]["hooks"][0]["command"]


def test_image_optimizer_hook_command_uses_portable_runner_placeholder():
    registry = json.loads((sync_agent_stack.REPO_ROOT / "config" / "hook-registry.json").read_text(encoding="utf-8"))
    [hook] = [entry for entry in registry["hooks"] if entry["id"] == "image-input-optimizer-guard"]

    assert hook["command"] == "{hook_runner} image-input-optimizer-guard --harness {harness}"
    codex = render_codex_hooks({"hooks": [hook]}, repo_relative=True)
    command = codex["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    assert command == "./hooks/run-wagents-hook image-input-optimizer-guard --harness codex"


def test_image_optimizer_hook_projects_to_all_declared_repo_surfaces():
    registry = json.loads((sync_agent_stack.REPO_ROOT / "config" / "hook-registry.json").read_text(encoding="utf-8"))
    [hook] = [entry for entry in registry["hooks"] if entry["id"] == "image-input-optimizer-guard"]
    expected = {
        "codex": sync_agent_stack.REPO_ROOT / ".codex" / "hooks.json",
        "claude-code": sync_agent_stack.REPO_ROOT / ".claude" / "settings.json",
        "cursor": sync_agent_stack.REPO_ROOT / ".cursor" / "hooks.json",
    }

    assert set(hook["harnesses"]) == set(expected)
    for harness, path in expected.items():
        payload = json.loads(path.read_text(encoding="utf-8"))
        commands = json.dumps(payload)
        assert f"image-input-optimizer-guard --harness {harness}" in commands

    for harness in expected:
        path = sync_agent_stack.REPO_ROOT / ".apm" / "hooks" / f"{harness}.json"
        assert path.exists(), f"missing APM hook bundle for {harness}"
        assert f"image-input-optimizer-guard --harness {harness}" in path.read_text(encoding="utf-8")


def test_codex_hook_renderer_supports_current_official_events():
    registry = {
        "version": 1,
        "hooks": [
            {
                "id": event.lower(),
                "logical_event": event,
                "command": "python3 {repo_root}/hooks/wagents-hook.py research-evidence-ledger --harness {harness}",
                "harnesses": ["codex"],
            }
            for event in [
                "SessionStart",
                "UserPromptSubmit",
                "PreToolUse",
                "PermissionRequest",
                "PostToolUse",
                "PreCompact",
                "PostCompact",
                "SubagentStart",
                "SubagentStop",
                "Stop",
            ]
        ],
    }

    rendered = render_codex_hooks(registry)

    assert set(rendered["hooks"]) == {
        "SessionStart",
        "UserPromptSubmit",
        "PreToolUse",
        "PermissionRequest",
        "PostToolUse",
        "PreCompact",
        "PostCompact",
        "SubagentStart",
        "SubagentStop",
        "Stop",
    }


def test_codex_hook_renderer_emits_only_official_command_fields():
    registry = {
        "version": 1,
        "hooks": [
            {
                "id": "codex-permission-request-guard",
                "logical_event": "PermissionRequest",
                "command": (
                    "python3 {repo_root}/hooks/wagents-hook.py codex-permission-request-guard --harness {harness}"
                ),
                "timeout": 7,
                "status_message": "Checking approval request safety",
                "command_windows": (
                    "py {repo_root}/hooks/wagents-hook.py codex-permission-request-guard --harness {harness}"
                ),
                "async": True,
                "suppressOutput": True,
                "agent": "unsupported",
                "harnesses": ["codex"],
            }
        ],
    }

    rendered = render_codex_hooks(registry)

    handler = rendered["hooks"]["PermissionRequest"][0]["hooks"][0]
    assert handler == {
        "type": "command",
        "command": (
            f"python3 {sync_agent_stack.REPO_ROOT}/hooks/wagents-hook.py codex-permission-request-guard --harness codex"
        ),
        "timeout": 7,
        "statusMessage": "Checking approval request safety",
        "commandWindows": (
            f"py {sync_agent_stack.REPO_ROOT}/hooks/wagents-hook.py codex-permission-request-guard --harness codex"
        ),
    }


def test_merge_codex_hooks_preserves_local_and_replaces_generated(tmp_path, monkeypatch):
    hooks_path = tmp_path / "hooks.json"
    hooks_path.write_text(
        json.dumps({
            "hooks": {
                "UserPromptSubmit": [{"hooks": [{"command": "echo local"}]}],
                "PreToolUse": [{"hooks": [{"command": "python3 /old/hooks/wagents-hook.py old"}]}],
            }
        })
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
    assert str(sync_agent_stack.REPO_ROOT) in payload["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    assert "/old/hooks/wagents-hook.py" not in json.dumps(payload)


def test_codex_repo_adapter_renders_absolute_hook_commands(monkeypatch):
    calls: list[dict[str, object]] = []

    monkeypatch.setattr("scripts.sync_agent_stack.generate_codex_global_instructions", lambda _ctx: None)

    def fake_merge_codex_hooks(_ctx, _hook_registry, **kwargs):
        calls.append(kwargs)

    monkeypatch.setattr("scripts.sync_agent_stack.merge_codex_hooks", fake_merge_codex_hooks)

    codex_platform.Adapter().sync_repo(platform_base.SyncContext(apply=False), {}, {}, {})

    assert calls == [{"path": codex_platform.CODEX_REPO_HOOKS_PATH}]


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
                "env": {"DUCK_TOKEN": "${DUCK_TOKEN}"},
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
                "env": {"DUCK_TOKEN": "${DUCK_TOKEN}"},
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
                "harnesses": ["codex", "claude-code"],
            },
            {
                "id": "research-stop-verifier",
                "logical_event": "Stop",
                "command": "python3 {repo_root}/hooks/wagents-hook.py research-stop-verifier --harness {harness}",
                "timeout": 30,
                "harnesses": ["codex"],
            },
        ],
    }

    codex = render_standard_hooks(registry, "codex")
    claude = render_standard_hooks(registry, "claude-code")

    codex_command = codex["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    claude_command = claude["hooks"]["PreToolUse"][0]["hooks"][0]["command"]

    assert "research-readonly-write-guard --harness codex" in codex_command
    assert str(sync_agent_stack.REPO_ROOT) in codex_command
    assert "research-readonly-write-guard --harness claude-code" in claude_command
    assert claude["hooks"]["PreToolUse"][0]["hooks"][0]["timeout"] == 5000
    assert "Stop" in codex["hooks"]


def test_render_codex_config_enables_hooks_feature():
    registry = {"servers": {}}
    policy = {"model_defaults": {"codex": {"model": "gpt-5.5", "reasoning_effort": "high", "personality": "pragmatic"}}}

    rendered = render_codex_config("", registry, policy, include_local_extras=False)

    assert "\n[features]\n" in rendered
    assert "hooks = true" in rendered
    assert "codex_hooks" not in rendered


def test_render_codex_config_uses_live_web_search_per_latest_docs():
    import tomllib

    registry = {"servers": {}}
    policy = {"model_defaults": {"codex": {"model": "gpt-5.5", "reasoning_effort": "high", "personality": "pragmatic"}}}

    rendered = render_codex_config("", registry, policy, include_local_extras=False)
    data = tomllib.loads(rendered)

    assert data["web_search"] == "live"
    assert all(profile["web_search"] == "live" for name, profile in data["profiles"].items() if "web_search" in profile)
    assert data["tools"]["web_search"]["context_size"] == "high"
    assert data["tools"]["web_search"]["location"]["country"] == "US"
    assert "web_search_cached" not in rendered
    assert "web_search_request" not in rendered


def test_repair_codex_config_text_deduplicates_managed_mcphub_servers():
    import tomllib

    registry = json.loads((sync_agent_stack.REPO_ROOT / "config/mcp-registry.json").read_text(encoding="utf-8"))
    current = """
[mcp_servers.mcphub_group_harness]
url = "http://127.0.0.1:46683/mcp/harness"
enabled = true

# BEGIN MANAGED BY sync_agent_stack.py: MCP_SERVERS

[mcp_servers.mcphub_group_harness]
url = "http://127.0.0.1:46683/mcp/harness"
enabled = true

# END MANAGED BY sync_agent_stack.py: MCP_SERVERS
"""
    repaired = sync_agent_stack.repair_codex_config_text(current, registry)
    data = tomllib.loads(repaired)

    assert repaired.count("[mcp_servers.mcphub_group_harness]") == 0
    assert "mcphub_group_harness" not in data.get("mcp_servers", {})


def test_render_codex_config_drops_preserved_managed_mcphub_servers():
    import tomllib

    registry = mcphub_registry()
    policy = {"model_defaults": {"codex": {"model": "gpt-5.5", "reasoning_effort": "high", "personality": "pragmatic"}}}
    current = """
[mcp_servers.mcphub_group_harness]
url = "http://127.0.0.1:46683/mcp/harness"
enabled = true

[mcp_servers.mcphub_server_brave-search]
url = "http://127.0.0.1:46683/mcp/brave-search"
enabled = false
"""

    rendered = render_codex_config(current, registry, policy, include_local_extras=True)
    data = tomllib.loads(rendered)
    harness_blocks = rendered.count("[mcp_servers.mcphub_group_harness]")
    brave_blocks = rendered.count("[mcp_servers.mcphub_server_brave-search]")

    assert harness_blocks == 1
    assert brave_blocks == 1
    assert "mcphub_group_harness" in data["mcp_servers"]


def test_render_codex_config_drops_preserved_features_multi_agent_v2_table():
    import tomllib

    registry = {"servers": {}}
    policy = {"model_defaults": {"codex": {"model": "gpt-5.5", "reasoning_effort": "high", "personality": "pragmatic"}}}
    current = """
[features.multi_agent_v2]
enabled = true
max_concurrent_threads_per_session = 512
"""

    rendered = render_codex_config(current, registry, policy, include_local_extras=True)
    data = tomllib.loads(rendered)

    assert data["features"]["multi_agent_v2"] is True
    assert "[features.multi_agent_v2]" not in rendered


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
        json.dumps({
            "instructions": ["~/.config/opencode/rules/shared.md"],
            "skills": {"paths": ["~/.config/opencode/skills"]},
            "mcp": {"custom": {"type": "local", "enabled": True}},
        })
    )

    monkeypatch.setattr(sync_agent_stack, "HOME", home_dir)
    monkeypatch.setattr(sync_agent_stack, "REPO_ROOT", repo_root)
    monkeypatch.setattr(sync_agent_stack, "GLOBAL_MD", repo_root / "instructions" / "global.md")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_GLOBAL_MD", repo_root / "instructions" / "opencode-global.md")
    monkeypatch.setattr(
        sync_agent_stack, "OPENCODE_AGENTS_OVERLAY_MD", repo_root / "instructions" / "opencode-agents-overlay.md"
    )
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
        "~/dev/projects/agents/instructions/opencode-agents-overlay.md",
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
        json.dumps({
            "instructions": [
                str((repo_root / "instructions" / "global.md").resolve()),
                str((repo_root / "instructions" / "opencode-global.md").resolve()),
                str((repo_root / "instructions" / "opencode-agents-overlay.md").resolve()),
            ],
            "skills": {"paths": [str((repo_root / "skills").resolve())]},
        })
    )

    monkeypatch.setattr(sync_agent_stack, "HOME", home_dir)
    monkeypatch.setattr(sync_agent_stack, "REPO_ROOT", repo_root)
    monkeypatch.setattr(sync_agent_stack, "GLOBAL_MD", repo_root / "instructions" / "global.md")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_GLOBAL_MD", repo_root / "instructions" / "opencode-global.md")
    monkeypatch.setattr(
        sync_agent_stack, "OPENCODE_AGENTS_OVERLAY_MD", repo_root / "instructions" / "opencode-agents-overlay.md"
    )
    monkeypatch.setattr(sync_agent_stack, "SKILLS_DIR", repo_root / "skills")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_CONFIG_PATH", config_path)

    ctx = SyncContext(apply=True)
    with pytest.raises(platform_base.ConfigDropError, match="sync would remove local config entries"):
        merge_opencode_config(ctx, {"servers": {}}, {})


def test_merge_opencode_config_adds_lmstudio_provider_and_preserves_custom_models(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    repo_root = home_dir / "dev" / "projects" / "agents"
    config_path = home_dir / ".config" / "opencode" / "opencode.json"

    repo_root.mkdir(parents=True)
    config_path.parent.mkdir(parents=True)
    (repo_root / "instructions").mkdir()
    (repo_root / "skills").mkdir()

    config_path.write_text(
        json.dumps({
            "provider": {
                "lmstudio": {
                    "models": {"custom-model": {"name": "Custom Local Model"}},
                    "options": {"headers": {"X-Local": "1"}},
                }
            },
            "mcp": {},
        })
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(sync_agent_stack, "HOME", home_dir)
    monkeypatch.setattr(sync_agent_stack, "REPO_ROOT", repo_root)
    monkeypatch.setattr(sync_agent_stack, "GLOBAL_MD", repo_root / "instructions" / "global.md")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_GLOBAL_MD", repo_root / "instructions" / "opencode-global.md")
    monkeypatch.setattr(
        sync_agent_stack, "OPENCODE_AGENTS_OVERLAY_MD", repo_root / "instructions" / "opencode-agents-overlay.md"
    )
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


def test_merge_opencode_config_enforces_requested_model_matrix(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    repo_root = home_dir / "dev" / "projects" / "agents"
    config_path = home_dir / ".config" / "opencode" / "opencode.json"

    repo_root.mkdir(parents=True)
    config_path.parent.mkdir(parents=True)
    (repo_root / "instructions").mkdir()
    (repo_root / "skills").mkdir()

    config_path.write_text(
        json.dumps({
            "model": "user/model",
            "small_model": "user/small-model",
            "mode": {
                "build": {"model": "user/build-model"},
                "plan": {"model": "user/plan-model"},
            },
            "agent": {
                "build": {"model": "user/agent-build-model", "description": "keep build description"},
                "plan": {"model": "user/agent-plan-model", "description": "keep plan description"},
            },
        })
    )

    monkeypatch.setattr(sync_agent_stack, "HOME", home_dir)
    monkeypatch.setattr(sync_agent_stack, "REPO_ROOT", repo_root)
    monkeypatch.setattr(sync_agent_stack, "GLOBAL_MD", repo_root / "instructions" / "global.md")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_GLOBAL_MD", repo_root / "instructions" / "opencode-global.md")
    monkeypatch.setattr(
        sync_agent_stack, "OPENCODE_AGENTS_OVERLAY_MD", repo_root / "instructions" / "opencode-agents-overlay.md"
    )
    monkeypatch.setattr(sync_agent_stack, "SKILLS_DIR", repo_root / "skills")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_CONFIG_PATH", config_path)
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_REPO_CONFIG_PATH", repo_root / "opencode.json")

    policy = {
        "model_defaults": {
            "opencode": {
                "provider_model": "openai/gpt-5.5",
            }
        }
    }

    ctx = SyncContext(apply=True)
    merge_opencode_config(ctx, {"servers": {}}, {}, policy)
    payload = json.loads(config_path.read_text())

    assert_opencode_model_matrix(payload)
    assert payload["autoupdate"] == "notify"
    assert payload["provider"]["openai"]["models"]["gpt-5.3-codex-spark"]["variants"]["high"] == {
        "include": ["reasoning.encrypted_content"],
        "reasoningEffort": "high",
        "reasoningSummary": None,
        "textVerbosity": "low",
    }
    assert set(payload["formatter"]) == {"biome", "prettier", "ruff", "shell", "toml", "just", "gofmt", "rustfmt"}
    assert payload["formatter"]["ruff"]["command"] == ["ruff", "format", "$FILE"]
    assert payload["lsp"]["ruff"]["command"] == ["ruff", "server"]
    assert payload["lsp"]["ty"]["command"] == ["ty", "server"]
    assert payload["watcher"]["ignore"] == sync_agent_stack.OPENCODE_DEFAULT_WATCHER_IGNORES
    assert payload["tool_output"] == {"max_lines": 4000, "max_bytes": 120000}
    assert payload["experimental"] == {
        "disable_paste_summary": False,
        "batch_tool": True,
        "openTelemetry": True,
        "continue_loop_on_deny": True,
        "mcp_timeout": 120000,
    }
    assert payload["permission"]["lsp"] == "allow"
    assert payload["mode"]["build"]["model"] == "user/build-model"
    assert payload["mode"]["plan"]["model"] == "user/plan-model"
    assert payload["agent"]["build"]["description"] == "keep build description"
    assert payload["agent"]["plan"]["description"] == "keep plan description"


def test_merge_opencode_config_preserves_custom_agent_models(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    repo_root = home_dir / "dev" / "projects" / "agents"
    config_path = home_dir / ".config" / "opencode" / "opencode.json"

    repo_root.mkdir(parents=True)
    config_path.parent.mkdir(parents=True)
    (repo_root / "instructions").mkdir()
    (repo_root / "skills").mkdir()

    config_path.write_text(
        json.dumps({
            "agent": {
                "custom-agent-1": {"model": "user/custom-model"},
                "custom-agent-2": {"model": "user/another-model", "other": "value"},
            },
        })
    )

    monkeypatch.setattr(sync_agent_stack, "HOME", home_dir)
    monkeypatch.setattr(sync_agent_stack, "REPO_ROOT", repo_root)
    monkeypatch.setattr(sync_agent_stack, "GLOBAL_MD", repo_root / "instructions" / "global.md")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_GLOBAL_MD", repo_root / "instructions" / "opencode-global.md")
    monkeypatch.setattr(
        sync_agent_stack, "OPENCODE_AGENTS_OVERLAY_MD", repo_root / "instructions" / "opencode-agents-overlay.md"
    )
    monkeypatch.setattr(sync_agent_stack, "SKILLS_DIR", repo_root / "skills")
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_CONFIG_PATH", config_path)
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_REPO_CONFIG_PATH", repo_root / "opencode.json")

    policy = {"model_defaults": {"opencode": {"provider_model": "openai/gpt-5.5"}}}

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
        json.dumps({
            "$schema": "https://raw.githubusercontent.com/Opencode-DCP/opencode-dynamic-context-pruning/master/dcp.schema.json",
            "enabled": True,
            "debug": False,
            "compress": {
                "mode": "range",
                "maxContextLimit": "85%",
                "minContextLimit": "55%",
            },
        })
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
        json.dumps({
            "$schema": "schema",
            "enabled": True,
            "compress": {
                "mode": "range",
                "showCompression": False,
                "maxContextLimit": "85%",
            },
        })
        + "\n",
        encoding="utf-8",
    )
    dcp_path.write_text(
        json.dumps({
            "$schema": "schema",
            "enabled": False,
            "customKey": "preserve",
            "compress": {
                "showCompression": True,
            },
        })
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
    assert "model" not in payload
    assert "agent" not in payload


def test_merge_opencode_config_errors_before_dropping_dcp_entries(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    config_path = home_dir / ".config" / "opencode" / "opencode.json"
    dcp_path = home_dir / ".config" / "opencode" / "dcp.jsonc"
    template_path = tmp_path / "opencode-dcp.jsonc"

    dcp_path.parent.mkdir(parents=True)
    template_path.write_text(json.dumps({"compress": {"mode": "range"}}) + "\n", encoding="utf-8")
    dcp_path.write_text(
        json.dumps({
            "small_model": "local/model",
            "compress": {
                "modelMaxLimits": {"openai/gpt-5.5": 200000},
            },
        })
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(sync_agent_stack, "OPENCODE_CONFIG_PATH", config_path)
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_DCP_CONFIG_PATH", dcp_path)
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_DCP_TEMPLATE_PATH", template_path)

    ctx = SyncContext(apply=True)
    with pytest.raises(platform_base.ConfigDropError, match=r"\$\.small_model"):
        merge_opencode_config(ctx, {"servers": {}}, {}, {})


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


def test_sync_opencode_notifier_config_copies_template(tmp_path, monkeypatch):
    template_path = tmp_path / "repo" / "config" / "opencode-notifier.json"
    notifier_path = tmp_path / "home" / ".config" / "opencode" / "opencode-notifier.json"
    expected = {
        "notificationSystem": "ghostty",
        "showProjectName": False,
        "showIcon": False,
        "customIconPath": None,
    }
    template_path.parent.mkdir(parents=True)
    notifier_path.parent.mkdir(parents=True)
    template_path.write_text(json.dumps(expected) + "\n", encoding="utf-8")

    monkeypatch.setattr(sync_agent_stack, "OPENCODE_NOTIFIER_CONFIG_PATH", notifier_path)
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_NOTIFIER_TEMPLATE_PATH", template_path)

    ctx = SyncContext(apply=True)
    sync_opencode_notifier_config(ctx)

    assert json.loads(notifier_path.read_text(encoding="utf-8")) == expected


def test_sync_opencode_notifier_config_errors_before_dropping_local_entries(tmp_path, monkeypatch):
    template_path = tmp_path / "repo" / "config" / "opencode-notifier.json"
    notifier_path = tmp_path / "home" / ".config" / "opencode" / "opencode-notifier.json"
    template_path.parent.mkdir(parents=True)
    notifier_path.parent.mkdir(parents=True)
    template_path.write_text(json.dumps({"showIcon": False}) + "\n", encoding="utf-8")
    notifier_path.write_text(json.dumps({"showIcon": True, "localOnly": True}) + "\n", encoding="utf-8")

    monkeypatch.setattr(sync_agent_stack, "OPENCODE_NOTIFIER_CONFIG_PATH", notifier_path)
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_NOTIFIER_TEMPLATE_PATH", template_path)

    ctx = SyncContext(apply=True)
    with pytest.raises(platform_base.ConfigDropError, match=r"\$\.localOnly"):
        sync_opencode_notifier_config(ctx)

    assert json.loads(notifier_path.read_text(encoding="utf-8"))["localOnly"] is True


def test_sync_opencode_octto_config_copies_template(tmp_path, monkeypatch):
    template_path = tmp_path / "repo" / "config" / "opencode-octto.json"
    octto_path = tmp_path / "home" / ".config" / "opencode" / "octto.json"
    expected = {
        "port": 3765,
        "agents": {
            "octto": {"variant": "xhigh"},
            "bootstrapper": {"model": "openai/gpt-5.5", "variant": "xhigh"},
            "probe": {"model": "openai/gpt-5.5", "variant": "xhigh"},
        },
    }
    template_path.parent.mkdir(parents=True)
    octto_path.parent.mkdir(parents=True)
    template_path.write_text(json.dumps(expected) + "\n", encoding="utf-8")

    monkeypatch.setattr(sync_agent_stack, "OPENCODE_OCTTO_CONFIG_PATH", octto_path)
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_OCTTO_TEMPLATE_PATH", template_path)

    ctx = SyncContext(apply=True)
    sync_agent_stack.sync_opencode_octto_config(ctx)

    assert json.loads(octto_path.read_text(encoding="utf-8")) == expected


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
    assert payload["instructions"] == [
        "AGENTS.md",
        "instructions/opencode-global.md",
        "instructions/opencode-agents-overlay.md",
    ]
    assert payload["skills"]["paths"] == ["skills"]
    assert_opencode_model_matrix(payload)
    assert set(payload["formatter"]) == {"biome", "prettier", "ruff", "shell", "toml", "just", "gofmt", "rustfmt"}
    assert payload["formatter"]["ruff"]["command"] == ["ruff", "format", "$FILE"]
    assert payload["formatter"]["ruff"]["extensions"] == [".py", ".pyi"]
    assert payload["lsp"]["ruff"]["command"] == ["ruff", "server"]
    assert payload["lsp"]["ty"]["command"] == ["ty", "server"]
    assert payload["experimental"] == {
        "disable_paste_summary": False,
        "batch_tool": True,
        "openTelemetry": True,
        "continue_loop_on_deny": True,
        "mcp_timeout": 120000,
    }
    assert payload["permission"] == {"lsp": "allow"}
    assert "mode" not in payload
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
    assert called == ["vscode", "cursor", "codex", "claude-code", "opencode", "grok"]


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


def test_vscode_adapter_render_mcphub_mcp_preserves_env_placeholders(monkeypatch):
    monkeypatch.setenv("MCPHUB_BEARER_TOKEN", "real-secret")
    adapter = vscode_platform.Adapter()
    registry = {
        "servers": {
            "example": {
                "command": "uvx",
                "args": ["example-mcp"],
                "enabled": True,
            }
        },
        "mcphub": {
            "enabled": True,
            "base_url": "http://127.0.0.1:46683",
            "bearer_token_env_var": "MCPHUB_BEARER_TOKEN",
            "clients": {
                "default": {
                    "included_endpoint_kinds": ["group"],
                    "included_groups": ["safe"],
                    "enabled_endpoint_kinds": ["group"],
                    "enabled_groups": ["safe"],
                }
            },
            "groups": {
                "safe": {
                    "enabled": True,
                    "servers": ["example"],
                }
            },
        },
    }

    rendered = adapter.render_mcp(registry, {}, harness="repo-mcp")
    payload = json.dumps(rendered)

    assert "real-secret" not in payload
    assert rendered["mcpServers"]["mcphub_group_safe"]["env"] == {"MCPHUB_BEARER_TOKEN": "${MCPHUB_BEARER_TOKEN}"}


def test_cursor_adapter_render_mcphub_mcp_uses_native_placeholders(monkeypatch):
    monkeypatch.setenv("MCPHUB_BEARER_TOKEN", "real-secret")
    adapter = cursor_platform.Adapter()
    registry = {
        "servers": {
            "example": {
                "command": "uvx",
                "args": ["example-mcp"],
                "enabled": True,
            }
        },
        "mcphub": {
            "enabled": True,
            "base_url": "http://127.0.0.1:46683",
            "bearer_token_env_var": "MCPHUB_BEARER_TOKEN",
            "clients": {
                "default": {
                    "included_endpoint_kinds": ["group", "server"],
                    "included_groups": ["harness"],
                    "enabled_endpoint_kinds": ["group"],
                    "enabled_groups": ["harness"],
                }
            },
            "groups": {
                "harness": {
                    "enabled": True,
                    "servers": ["example"],
                }
            },
        },
    }

    rendered = adapter.render_mcp(registry, {}, harness="cursor")
    payload = json.dumps(rendered)

    assert "real-secret" not in payload
    assert rendered == {
        "mcpServers": {
            "mcphub_group_harness": {
                "type": "http",
                "url": "http://127.0.0.1:46683/mcp/harness",
                "headers": {"Authorization": "Bearer ${env:MCPHUB_BEARER_TOKEN}"},
            }
        }
    }


def test_cursor_adapter_render_stdio_mcp_uses_workspace_and_env_interpolation():
    adapter = cursor_platform.Adapter()
    registry = {
        "servers": {
            "example": {
                "transport": "stdio",
                "command": "${REPO_ROOT}/scripts/example-mcp.sh",
                "args": ["--repo", "${REPO_ROOT}", "--token", "${EXAMPLE_TOKEN}"],
                "enabled": True,
                "env": {"TOKEN": {"env_var": "EXAMPLE_TOKEN"}},
                "startup_timeout_sec": 90,
                "timeout_ms": 5000,
                "tools": ["*"],
                "tool_approvals": {},
                "platform_overrides": {},
            }
        }
    }

    rendered = adapter.render_mcp(registry, {}, harness="cursor")

    assert rendered["mcpServers"]["example"] == {
        "type": "stdio",
        "command": "${workspaceFolder}/scripts/example-mcp.sh",
        "args": ["--repo", "${workspaceFolder}", "--token", "${env:EXAMPLE_TOKEN}"],
        "env": {"TOKEN": "${env:EXAMPLE_TOKEN}"},
        "timeout": 5000,
    }


def test_cursor_adapter_permissions_and_cli_do_not_override_ui_allowlists():
    adapter = cursor_platform.Adapter()

    permissions = adapter.render_permissions({})
    cli_config = adapter.render_cli_config({})

    assert "mcpAllowlist" not in permissions
    assert "terminalAllowlist" not in permissions
    assert set(permissions) == {"autoRun"}
    assert set(cli_config) == {"permissions"}
    assert "deny" in cli_config["permissions"]
    assert "allow" in cli_config["permissions"]


def test_cursor_adapter_render_hooks_uses_native_event_names():
    adapter = cursor_platform.Adapter()
    hook_registry = {
        "hooks": [
            {
                "id": "cursor-destructive-shell-guard",
                "logical_event": "PreToolUse",
                "matcher": "Bash",
                "mode": "enforce",
                "command": (
                    "python3 {repo_root}/hooks/wagents-hook.py cursor-destructive-shell-guard --harness {harness}"
                ),
                "timeout": 5,
                "harnesses": ["cursor"],
            }
        ]
    }

    rendered = adapter.render_hooks(hook_registry)

    assert rendered == {
        "version": 1,
        "hooks": {
            "preToolUse": [
                {
                    "command": (
                        '"$CURSOR_PROJECT_DIR/hooks/run-wagents-hook" '
                        "cursor-destructive-shell-guard --harness cursor"
                    ),
                    "matcher": "Bash",
                    "timeout": 5,
                    "failClosed": True,
                }
            ]
        },
    }


def test_cursor_agent_overlay_matches_portable_agents():
    overlays = {
        entry["name"]
        for entry in json.loads((sync_agent_stack.REPO_ROOT / "config" / "cursor-agents.json").read_text())["agents"]
    }
    agents = {path.stem for path in (sync_agent_stack.REPO_ROOT / "agents").glob("*.md") if path.name != "README.md"}

    assert overlays == agents


def test_opencode_agent_overlay_matches_portable_agents():
    overlays = set(opencode_platform._load_opencode_agent_overlays().keys())
    agents = {path.stem for path in (sync_agent_stack.REPO_ROOT / "agents").glob("*.md") if path.name != "README.md"}

    assert overlays == agents


def test_opencode_managed_agent_contract_errors_valid_agent():
    content = (
        "---\n"
        "name: reviewer\n"
        "description: Review code.\n"
        "mode: subagent\n"
        "temperature: 0.1\n"
        "color: primary\n"
        "permission:\n"
        "  edit: deny\n"
        "---\n\n"
        "<!-- Managed by wagents sync from agents/ + config/opencode-agents.json -->\n"
        "Review only.\n"
    )
    assert opencode_platform.opencode_managed_agent_contract_errors(content) == []


def test_opencode_managed_agent_contract_errors_rejects_tools():
    content = (
        "---\n"
        "name: reviewer\n"
        "description: Review code.\n"
        "tools: all\n"
        "mode: subagent\n"
        "permission:\n"
        "  edit: deny\n"
        "---\n\n"
        "<!-- Managed by wagents sync from agents/ + config/opencode-agents.json -->\n"
    )
    errors = opencode_platform.opencode_managed_agent_contract_errors(content)
    assert any("tools" in err for err in errors)


def test_opencode_managed_agent_contract_errors_rejects_missing_permission():
    content = (
        "---\n"
        "name: reviewer\n"
        "description: Review code.\n"
        "mode: subagent\n"
        "---\n\n"
        "<!-- Managed by wagents sync from agents/ + config/opencode-agents.json -->\n"
    )
    errors = opencode_platform.opencode_managed_agent_contract_errors(content)
    assert any("permission" in err for err in errors)


def test_opencode_managed_agent_contract_errors_rejects_malformed_frontmatter():
    content = "<!-- Managed by wagents sync from agents/ + config/opencode-agents.json -->\n"
    errors = opencode_platform.opencode_managed_agent_contract_errors(content)
    assert errors


def test_check_opencode_managed_agents_dir_requires_overlay_parity(tmp_path):
    agents_dir = tmp_path / ".opencode" / "agents"
    agents_dir.mkdir(parents=True)
    config_path = tmp_path / "config" / "opencode-agents.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps({
            "version": 1,
            "agents": [
                {
                    "name": "reviewer",
                    "mode": "subagent",
                    "temperature": 0.1,
                    "color": "primary",
                    "permission": {"edit": "deny"},
                },
                {
                    "name": "planner",
                    "mode": "subagent",
                    "temperature": 0.1,
                    "color": "primary",
                    "permission": {"edit": "deny"},
                },
            ],
        }),
        encoding="utf-8",
    )
    (agents_dir / "reviewer.md").write_text(
        "---\nname: reviewer\ndescription: Review.\nmode: subagent\npermission:\n  edit: deny\n---\n\n"
        "<!-- Managed by wagents sync from agents/ + config/opencode-agents.json -->\n",
        encoding="utf-8",
    )

    errors = opencode_platform.check_opencode_managed_agents_dir(agents_dir, config_path=config_path)
    assert any("planner.md" in err for err in errors)


def test_render_opencode_agents_use_permission_not_portable_tools():
    rendered = opencode_platform._render_opencode_agents()
    agent_names = {
        f"{path.stem}.md"
        for path in (sync_agent_stack.REPO_ROOT / "agents").glob("*.md")
        if path.name != "README.md"
    }

    assert set(rendered) == agent_names
    for name, content in rendered.items():
        frontmatter = content.split("---", 2)[1]
        assert "tools:" not in frontmatter, f"{name} must not project portable tools into OpenCode"
        assert "permissionMode:" not in frontmatter, f"{name} must not project permissionMode into OpenCode"
        assert "mode: subagent" in frontmatter, f"{name} must include OpenCode subagent mode"
        assert "permission:" in frontmatter, f"{name} must include OpenCode permission rules"
        assert opencode_platform.OPENCODE_MANAGED_AGENT_MARKER.strip() in content


def _mini_opencode_sync_repo(tmp_path):
    repo = tmp_path / "repo"
    agents = repo / "agents"
    agents.mkdir(parents=True)
    (repo / "config").mkdir(parents=True)
    (repo / "instructions").mkdir()
    (repo / "skills").mkdir()
    (agents / "reviewer.md").write_text(
        "---\nname: reviewer\ndescription: Review code.\ntools: all\npermissionMode: default\n---\n\nReview only.\n",
        encoding="utf-8",
    )
    overlay = {
        "version": 1,
        "agents": [
            {
                "name": "reviewer",
                "mode": "subagent",
                "temperature": 0.1,
                "color": "primary",
                "permission": {"edit": "deny", "bash": "ask", "webfetch": "allow"},
            }
        ],
    }
    (repo / "config" / "opencode-agents.json").write_text(json.dumps(overlay), encoding="utf-8")
    return repo


def _patch_opencode_sync_repo(monkeypatch, repo):
    agents_dir = repo / ".opencode" / "agents"
    monkeypatch.setattr(opencode_platform, "REPO_ROOT", repo)
    monkeypatch.setattr(opencode_platform, "OPENCODE_AGENTS_DIR", agents_dir)
    monkeypatch.setattr(opencode_platform, "OPENCODE_AGENTS_CONFIG_PATH", repo / "config" / "opencode-agents.json")
    monkeypatch.setattr(opencode_platform, "OPENCODE_REPO_CONFIG_PATH", repo / "opencode.json")
    return agents_dir


def test_opencode_sync_repo_writes_managed_agents(tmp_path, monkeypatch):
    repo = _mini_opencode_sync_repo(tmp_path)
    agents_dir = _patch_opencode_sync_repo(monkeypatch, repo)
    adapter = opencode_platform.Adapter()
    ctx = platform_base.SyncContext(apply=True)
    adapter.sync_repo(ctx, {"servers": {}}, {"hooks": []}, {"model_defaults": {}})

    out = agents_dir / "reviewer.md"
    assert out.exists()
    errors = opencode_platform.opencode_managed_agent_contract_errors(out.read_text(encoding="utf-8"))
    assert errors == []


def test_opencode_sync_repo_check_idempotent(tmp_path, monkeypatch):
    repo = _mini_opencode_sync_repo(tmp_path)
    _patch_opencode_sync_repo(monkeypatch, repo)
    adapter = opencode_platform.Adapter()
    policy = {"model_defaults": {}}
    adapter.sync_repo(platform_base.SyncContext(apply=True), {"servers": {}}, {"hooks": []}, policy)
    ctx = platform_base.SyncContext(apply=False)
    adapter.sync_repo(ctx, {"servers": {}}, {"hooks": []}, policy)
    agent_changes = [c for c in ctx.changes if ".opencode/agents/reviewer.md" in c]
    assert agent_changes == []


def test_opencode_sync_repo_check_detects_corruption(tmp_path, monkeypatch):
    repo = _mini_opencode_sync_repo(tmp_path)
    agents_dir = _patch_opencode_sync_repo(monkeypatch, repo)
    adapter = opencode_platform.Adapter()
    policy = {"model_defaults": {}}
    adapter.sync_repo(platform_base.SyncContext(apply=True), {"servers": {}}, {"hooks": []}, policy)
    (agents_dir / "reviewer.md").write_text(
        "---\nname: reviewer\ntools: all\n---\n\n",
        encoding="utf-8",
    )
    ctx = platform_base.SyncContext(apply=False)
    adapter.sync_repo(ctx, {"servers": {}}, {"hooks": []}, policy)
    assert any(".opencode/agents/reviewer.md" in c for c in ctx.changes)


def test_cursor_adapter_sync_home_preserves_existing_unknown_mcp_servers(tmp_path, monkeypatch):
    home_cursor = tmp_path / ".cursor"
    home_cursor.mkdir(parents=True)
    config_path = home_cursor / "mcp.json"
    hooks_path = home_cursor / "hooks.json"
    config_path.write_text(
        json.dumps({
            "mcpServers": {"custom": {"command": "custom-mcp"}},
            "other": True,
        })
        + "\n",
        encoding="utf-8",
    )
    hooks_path.write_text(
        json.dumps({
            "version": 1,
            "hooks": {
                "preToolUse": [
                    {
                        "matcher": "exit_plan_mode|ExitPlanMode",
                        "hooks": [{"type": "command", "command": "/old/plannotator", "timeout": 1}],
                    },
                    {"command": "/usr/local/bin/custom-hook.sh"},
                ]
            },
        })
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cursor_platform, "CURSOR_HOME_MCP_PATH", config_path)
    monkeypatch.setattr(cursor_platform, "CURSOR_HOME_HOOKS_PATH", hooks_path)
    monkeypatch.setattr(
        cursor_platform,
        "render_cursor_global_hooks",
        lambda **_: {
            "version": 1,
            "hooks": {
                "preToolUse": [
                    {
                        "matcher": "exit_plan_mode|ExitPlanMode",
                        "command": "/new/plannotator",
                        "timeout": 345600,
                    }
                ]
            },
        },
    )

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
    hooks_payload = json.loads(hooks_path.read_text(encoding="utf-8"))

    assert payload["other"] is True
    assert payload["mcpServers"] == {
        "custom": {
            "command": "custom-mcp",
        },
        "managed": {
            "type": "stdio",
            "command": "uvx",
            "args": ["managed-mcp"],
        },
    }
    commands = [entry["command"] for entry in hooks_payload["hooks"]["preToolUse"]]
    assert commands == ["/usr/local/bin/custom-hook.sh", "/new/plannotator"]
    for entry in hooks_payload["hooks"]["preToolUse"]:
        assert "hooks" not in entry


def test_opencode_adapter_sync_home_adds_lmstudio_provider_and_preserves_custom_models(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    repo_root = home_dir / "dev" / "projects" / "agents"
    config_path = home_dir / ".config" / "opencode" / "opencode.json"

    repo_root.mkdir(parents=True)
    config_path.parent.mkdir(parents=True)
    (repo_root / "instructions").mkdir()
    (repo_root / "skills").mkdir()

    config_path.write_text(
        json.dumps({
            "provider": {
                "lmstudio": {
                    "models": {"custom-model": {"name": "Custom Local Model"}},
                    "options": {"headers": {"X-Local": "1"}},
                },
            },
            "agent": {
                "plan": {"model": "openai/gpt-5.5", "variant": "xhigh"},
            },
            "mcp": {},
        })
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(platform_base, "HOME", home_dir)
    monkeypatch.setattr(opencode_platform, "OPENCODE_CONFIG_PATH", config_path)
    monkeypatch.setattr(opencode_platform, "GLOBAL_MD", repo_root / "instructions" / "global.md")
    monkeypatch.setattr(opencode_platform, "OPENCODE_GLOBAL_MD", repo_root / "instructions" / "opencode-global.md")
    monkeypatch.setattr(
        opencode_platform, "OPENCODE_AGENTS_OVERLAY_MD", repo_root / "instructions" / "opencode-agents-overlay.md"
    )
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

    assert_opencode_model_matrix(payload)
    assert payload["agent"]["plan"]["variant"] == "xhigh"
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
        json.dumps({
            "$schema": "https://raw.githubusercontent.com/Opencode-DCP/opencode-dynamic-context-pruning/master/dcp.schema.json",
            "enabled": True,
            "compress": {
                "mode": "range",
                "maxContextLimit": "85%",
                "minContextLimit": "55%",
            },
        })
        + "\n",
        encoding="utf-8",
    )
    dcp_path.write_text(
        json.dumps({
            "customKey": "preserve",
            "compress": {
                "showCompression": True,
            },
        })
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
    assert payload["compress"]["showCompression"] is True


def test_opencode_adapter_sync_home_errors_before_dropping_dcp_entries(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    repo_root = home_dir / "dev" / "projects" / "agents"
    config_path = home_dir / ".config" / "opencode" / "opencode.json"
    dcp_path = home_dir / ".config" / "opencode" / "dcp.jsonc"
    template_path = repo_root / "config" / "opencode-dcp.jsonc"

    config_path.parent.mkdir(parents=True)
    template_path.parent.mkdir(parents=True)
    config_path.write_text("{}\n", encoding="utf-8")
    template_path.write_text(json.dumps({"compress": {"mode": "range"}}) + "\n", encoding="utf-8")
    dcp_path.write_text(json.dumps({"small_model": "remove-me"}) + "\n", encoding="utf-8")

    monkeypatch.setattr(opencode_platform, "OPENCODE_CONFIG_PATH", config_path)
    monkeypatch.setattr(opencode_platform, "OPENCODE_DCP_CONFIG_PATH", dcp_path)
    monkeypatch.setattr(opencode_platform, "OPENCODE_DCP_TEMPLATE_PATH", template_path)
    monkeypatch.setattr(opencode_platform.Adapter, "_deploy_plugins", lambda self, ctx: None)

    adapter = opencode_platform.Adapter()
    ctx = opencode_platform.SyncContext(apply=True)
    with pytest.raises(platform_base.ConfigDropError, match=r"\$\.small_model"):
        adapter.sync_home(ctx, {"servers": {}}, {}, {}, {})


def test_opencode_adapter_sync_home_merges_repo_runtime_plugins(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    repo_root = home_dir / "dev" / "projects" / "agents"
    config_path = home_dir / ".config" / "opencode" / "opencode.json"
    dcp_path = home_dir / ".config" / "opencode" / "dcp.jsonc"
    image_optimizer_path = home_dir / ".config" / "opencode" / "large-image-optimizer.json"
    octto_path = home_dir / ".config" / "opencode" / "octto.json"
    repo_config_path = repo_root / "opencode.json"
    image_optimizer_template_path = repo_root / "config" / "opencode-large-image-optimizer.json"
    octto_template_path = repo_root / "config" / "opencode-octto.json"

    repo_root.mkdir(parents=True)
    config_path.parent.mkdir(parents=True)
    image_optimizer_template_path.parent.mkdir(parents=True)
    (repo_root / "instructions").mkdir()
    (repo_root / "skills").mkdir()
    image_optimizer_template_path.write_text(
        json.dumps({"providers": {"anthropic": True, "google": True, "openai": True}, "defaultPolicy": True}) + "\n",
        encoding="utf-8",
    )
    octto_template_path.write_text(
        json.dumps({
            "port": 3765,
            "agents": {
                "octto": {"variant": "xhigh"},
                "bootstrapper": {"model": "openai/gpt-5.5", "variant": "xhigh"},
                "probe": {"model": "openai/gpt-5.5", "variant": "xhigh"},
            },
        })
        + "\n",
        encoding="utf-8",
    )
    repo_config_path.write_text(
        json.dumps({
            "plugin": [
                "@tarquinen/opencode-dcp@latest",
                [
                    "@plannotator/opencode@latest",
                    {"workflow": "plan-agent", "planningAgents": ["plan"]},
                ],
            ]
        })
        + "\n",
        encoding="utf-8",
    )
    config_path.write_text(
        json.dumps({
            "plugin": [
                "user-plugin@latest",
                "custom-runtime-plugin@latest",
            ],
            "mcp": {
                "custom-local": {
                    "type": "local",
                    "command": ["custom-mcp"],
                    "enabled": True,
                },
            },
        })
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(opencode_platform, "OPENCODE_CONFIG_PATH", config_path)
    monkeypatch.setattr(opencode_platform, "OPENCODE_DCP_CONFIG_PATH", dcp_path)
    monkeypatch.setattr(opencode_platform, "OPENCODE_LARGE_IMAGE_OPTIMIZER_CONFIG_PATH", image_optimizer_path)
    monkeypatch.setattr(opencode_platform, "OPENCODE_OCTTO_CONFIG_PATH", octto_path)
    monkeypatch.setattr(opencode_platform, "OPENCODE_DCP_TEMPLATE_PATH", repo_root / "config" / "opencode-dcp.jsonc")
    monkeypatch.setattr(
        opencode_platform,
        "OPENCODE_LARGE_IMAGE_OPTIMIZER_TEMPLATE_PATH",
        image_optimizer_template_path,
    )
    monkeypatch.setattr(opencode_platform, "OPENCODE_OCTTO_TEMPLATE_PATH", octto_template_path)
    monkeypatch.setattr(opencode_platform, "OPENCODE_REPO_CONFIG_PATH", repo_config_path)
    monkeypatch.setattr(opencode_platform, "GLOBAL_MD", repo_root / "instructions" / "global.md")
    monkeypatch.setattr(opencode_platform, "OPENCODE_GLOBAL_MD", repo_root / "instructions" / "opencode-global.md")
    monkeypatch.setattr(
        opencode_platform, "OPENCODE_AGENTS_OVERLAY_MD", repo_root / "instructions" / "opencode-agents-overlay.md"
    )
    monkeypatch.setattr(opencode_platform, "SKILLS_DIR", repo_root / "skills")
    monkeypatch.setattr(opencode_platform.Adapter, "_sync_dcp_config", lambda self, ctx: None)
    monkeypatch.setattr(opencode_platform.Adapter, "_sync_large_image_optimizer_config", lambda self, ctx: None)
    monkeypatch.setattr(
        opencode_platform.Adapter, "_sync_json_template", lambda self, ctx, template_path, target_path: None
    )
    monkeypatch.setattr(opencode_platform.Adapter, "_sync_tui_config", lambda self, ctx: None)
    monkeypatch.setattr(opencode_platform.Adapter, "_deploy_plugins", lambda self, ctx: None)

    adapter = opencode_platform.Adapter()
    ctx = opencode_platform.SyncContext(apply=True)
    adapter.sync_home(ctx, mcphub_registry(), {}, {"MCPHUB_BEARER_TOKEN": "local-token"}, {})
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    plugins = payload["plugin"]
    plugin_names = [plugin_spec if isinstance(plugin_spec, str) else plugin_spec[0] for plugin_spec in plugins]

    assert plugin_names == [
        "@tarquinen/opencode-dcp@latest",
        "@plannotator/opencode@latest",
        "./plugins/opencode-context-cache.mjs",
        "./plugins/octto-primary-inherit.mjs",
        "./plugins/opencode-incomplete-resume.mjs",
        "user-plugin@latest",
        "custom-runtime-plugin@latest",
    ]
    assert plugins[1] == ["@plannotator/opencode@latest", {"workflow": "plan-agent", "planningAgents": ["plan"]}]
    assert "local-token" not in json.dumps(payload)
    assert payload["mcp"]["mcphub_all"]["headers"] == {
        "Authorization": "Bearer {file:~/.config/opencode/secrets/mcphub-bearer-token}"
    }
    assert payload["mcp"]["custom-local"] == {
        "type": "local",
        "command": ["custom-mcp"],
        "enabled": True,
    }


def test_opencode_adapter_sync_tui_preserves_existing_managed_plugin_options(tmp_path, monkeypatch):
    tui_config_path = tmp_path / "home" / ".config" / "opencode" / "tui.json"
    template_path = tmp_path / "repo" / "config" / "opencode-tui-plugins.json"
    tui_config_path.parent.mkdir(parents=True)
    template_path.parent.mkdir(parents=True)
    tui_config_path.write_text(
        json.dumps({
            "keybinds": {"command_list": "ctrl+p"},
            "plugin": [
                ["@slkiser/opencode-quota@latest", {"custom": True}],
            ],
        })
        + "\n",
        encoding="utf-8",
    )
    template_path.write_text(json.dumps(["@slkiser/opencode-quota@latest"]) + "\n")

    monkeypatch.setattr(opencode_platform, "OPENCODE_TUI_CONFIG_PATH", tui_config_path)
    monkeypatch.setattr(opencode_platform, "OPENCODE_TUI_PLUGINS_TEMPLATE_PATH", template_path)

    ctx = opencode_platform.SyncContext(apply=True)
    opencode_platform.Adapter._sync_tui_config(ctx)

    payload = json.loads(tui_config_path.read_text(encoding="utf-8"))
    assert payload["plugin"] == [
        ["@slkiser/opencode-quota@latest", {"custom": True}],
    ]
    assert payload["keybinds"] == {"command_list": "ctrl+p"}


def test_opencode_adapter_sync_home_errors_before_dropping_runtime_entries(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    repo_root = home_dir / "dev" / "projects" / "agents"
    config_path = home_dir / ".config" / "opencode" / "opencode.json"
    repo_config_path = repo_root / "opencode.json"

    config_path.parent.mkdir(parents=True)
    repo_config_path.parent.mkdir(parents=True)
    (repo_root / "instructions").mkdir()
    (repo_root / "skills").mkdir()
    repo_config_path.write_text(json.dumps({"plugin": ["managed@latest"]}) + "\n", encoding="utf-8")
    config_path.write_text(
        json.dumps({
            "plugin": ["opencode-auto-resume@latest"],
            "mcp": {"mcphub_group_all": {"type": "remote", "url": "http://127.0.0.1:46683/mcp/group/all"}},
        })
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(opencode_platform, "OPENCODE_CONFIG_PATH", config_path)
    monkeypatch.setattr(opencode_platform, "OPENCODE_REPO_CONFIG_PATH", repo_config_path)
    monkeypatch.setattr(opencode_platform, "GLOBAL_MD", repo_root / "instructions" / "global.md")
    monkeypatch.setattr(opencode_platform, "OPENCODE_GLOBAL_MD", repo_root / "instructions" / "opencode-global.md")
    monkeypatch.setattr(
        opencode_platform, "OPENCODE_AGENTS_OVERLAY_MD", repo_root / "instructions" / "opencode-agents-overlay.md"
    )
    monkeypatch.setattr(opencode_platform, "SKILLS_DIR", repo_root / "skills")
    monkeypatch.setattr(opencode_platform.Adapter, "_deploy_plugins", lambda self, ctx: None)

    adapter = opencode_platform.Adapter()
    ctx = opencode_platform.SyncContext(apply=True)
    with pytest.raises(platform_base.ConfigDropError, match=r"\$\.plugin\[0\]"):
        adapter.sync_home(ctx, mcphub_registry(), {}, {}, {})


def test_legacy_opencode_tui_merge_preserves_existing_managed_plugin_options(tmp_path, monkeypatch):
    tui_config_path = tmp_path / "home" / ".config" / "opencode" / "tui.json"
    template_path = tmp_path / "repo" / "config" / "opencode-tui-plugins.json"
    tui_config_path.parent.mkdir(parents=True)
    template_path.parent.mkdir(parents=True)
    tui_config_path.write_text(
        json.dumps({
            "keymap": {
                "leader": "ctrl+x",
                "sections": {
                    "global": {
                        "command.palette.show": "ctrl+p",
                        "model.list": "<leader>m",
                    },
                },
            },
            "keybinds": {
                "command_list": "ctrl+shift+p",
            },
            "plugin": [
                ["@slkiser/opencode-quota@latest", {"custom": True}],
                "opencode-subagent-statusline@latest",
                "@thiagos1lva/opencode-token-usage-chart@latest",
            ],
        })
        + "\n",
        encoding="utf-8",
    )
    template_path.write_text(json.dumps(["@slkiser/opencode-quota@latest"]) + "\n")

    monkeypatch.setattr(sync_agent_stack, "OPENCODE_TUI_CONFIG_PATH", tui_config_path)
    monkeypatch.setattr(sync_agent_stack, "OPENCODE_TUI_PLUGINS_TEMPLATE_PATH", template_path)

    ctx = SyncContext(apply=True)
    with pytest.raises(platform_base.ConfigDropError, match=r"\$\.keymap"):
        sync_agent_stack.merge_opencode_tui_config(ctx)

    payload = json.loads(tui_config_path.read_text(encoding="utf-8"))
    assert "keymap" in payload


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
        "\n".join([
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
        ]),
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
            "package-version-check-mcp": {
                "command": "bash",
                "args": ["${REPO_ROOT}/scripts/mcphub/package-version-check-mcp.sh"],
                "enabled": True,
                "startup_timeout_sec": 90,
                "tools": ["get_latest_package_versions"],
            },
        }
    }

    rendered = render_codex_mcp_block(registry)

    assert 'type = "stdio"' not in rendered
    assert 'env_vars = ["CONTEXT7_API_KEY"]' in rendered
    assert "--api-key" not in rendered
    assert "tool_timeout_sec = 600" in rendered
    assert 'enabled_tools = ["get_latest_package_versions"]' in rendered


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
    assert "multi_agent_v2 = true" in home_config
    assert "[features.multi_agent_v2]" not in home_config
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


def test_load_json_raises_for_missing_required_file(tmp_path):
    missing = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        sync_agent_stack.load_json(missing)


def test_merge_claude_settings_creates_missing_settings_file(tmp_path, monkeypatch):
    settings_path = tmp_path / ".claude" / "settings.json"
    monkeypatch.setattr(sync_agent_stack, "CLAUDE_SETTINGS_PATH", settings_path)

    ctx = SyncContext(apply=True)
    sync_agent_stack.merge_claude_settings(ctx, {"docs_domains": ["docs.example.com"]}, {"hooks": []})

    rendered = json.loads(settings_path.read_text(encoding="utf-8"))
    assert rendered["permissions"]["allow"] == ["WebFetch(domain:docs.example.com)"]
    assert rendered["hooks"] == {}


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


def test_platform_filter_allows_shared_grok_only():
    from scripts.sync_agent_stack import platform_filter_allows

    assert platform_filter_allows({"grok"}, "shared") is False
    assert platform_filter_allows({"grok"}, "grok") is True
    assert platform_filter_allows({"grok"}, "opencode") is False
    assert platform_filter_allows(None, "opencode") is True


def test_sync_platforms_grok_only_skips_opencode(monkeypatch):
    from scripts.sync_agent_stack import SyncContext, sync_home_targets

    called: list[str] = []

    def fake_sync(name, ctx, registry, policy, fallbacks, hook_registry):
        called.append(name)

    monkeypatch.setattr("scripts.sync_agent_stack.sync_platform_home_target", fake_sync)
    ctx = SyncContext(apply=False)
    sync_home_targets(ctx, {}, {}, {}, {}, platforms_filter={"grok"})
    assert called == ["grok"]
    assert "opencode" not in called
