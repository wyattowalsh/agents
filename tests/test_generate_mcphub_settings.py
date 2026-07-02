"""Tests for MCPHub settings generation."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest

from scripts.generate_mcphub_settings import generate_settings, render_groups, render_server_entry, serialize_settings
from scripts.mcphub.validate_settings import validate_settings


def group_server_name(server):
    return server if isinstance(server, str) else server["name"]


def valid_system_config():
    return {
        "routing": {
            "enableGlobalRoute": True,
            "enableGroupNameRoute": True,
            "enableBearerAuth": True,
            "bearerAuthHeaderName": "Authorization",
            "jsonBodyLimit": "5mb",
            "skipAuth": False,
        },
        "smartRouting": {"enabled": False},
        "toolResultCompression": {"enabled": False},
    }


def minimal_registry_with_harness(servers):
    return {
        "servers": servers,
        "mcphub": {
            "groups": {
                "harness": {
                    "enabled": True,
                    "servers": ["fetcher"],
                }
            }
        },
    }


def test_generate_settings_matches_registry_servers_and_groups():
    repo_root = Path(__file__).resolve().parents[1]
    registry = json.loads((repo_root / "config" / "mcp-registry.json").read_text(encoding="utf-8"))
    settings = json.loads((repo_root / "mcp" / "mcphub" / "mcp_settings.json").read_text(encoding="utf-8"))

    generated = generate_settings(registry)

    assert set(generated["mcpServers"]) == set(registry["servers"])
    assert generated["systemConfig"]["smartRouting"]["enabled"] is False
    assert generated["systemConfig"]["toolResultCompression"] == {
        "enabled": False,
        "minTokens": 2000,
        "maxOutputTokens": 1200,
        "strategy": "auto",
    }

    registry_groups = registry["mcphub"]["groups"]
    assert set(generated["groups"]) == {
        name for name, group in registry_groups.items() if group.get("enabled") is not False
    }
    for group_name, group in generated["groups"].items():
        registry_servers = registry_groups[group_name]["servers"]
        assert group["servers"] == registry_servers

    assert validate_settings(generated, registry) == []
    assert validate_settings(settings, registry) == []


def test_generate_settings_preserves_group_tool_filters():
    registry = {
        "servers": {
            "fetcher": {"transport": "stdio", "command": "npx", "args": ["fetcher-mcp"], "enabled": True},
            "other": {"transport": "stdio", "command": "npx", "args": ["other-mcp"], "enabled": True},
        },
        "mcphub": {
            "groups": {
                "harness": {
                    "enabled": True,
                    "servers": [
                        {"name": "fetcher", "tools": ["fetch_urls"]},
                        "other",
                    ],
                }
            }
        },
    }

    generated = generate_settings(registry)

    assert generated["groups"]["harness"]["servers"] == [
        {"name": "fetcher", "tools": ["fetch_urls"]},
        "other",
    ]
    assert validate_settings(generated, registry) == []


def test_render_groups_rejects_unknown_group_server():
    registry = minimal_registry_with_harness({
        "fetcher": {"transport": "stdio", "command": "npx", "args": ["fetcher-mcp"], "enabled": True},
    })
    registry["mcphub"]["groups"]["harness"]["servers"].append("missing")

    with pytest.raises(ValueError, match=r"mcphub\.groups\.harness\.servers\[1\] references missing server 'missing'"):
        render_groups(registry["mcphub"]["groups"], registry["servers"])


def test_render_groups_rejects_disabled_group_server():
    registry = minimal_registry_with_harness({
        "fetcher": {"transport": "stdio", "command": "npx", "args": ["fetcher-mcp"], "enabled": True},
        "ffmpeg": {"transport": "stdio", "command": "uv", "args": ["run", "ffmpeg-mcp"], "enabled": False},
    })
    registry["mcphub"]["groups"]["harness"]["servers"].append("ffmpeg")

    with pytest.raises(ValueError, match=r"mcphub\.groups\.harness\.servers\[1\] references disabled server 'ffmpeg'"):
        render_groups(registry["mcphub"]["groups"], registry["servers"])


def test_render_groups_rejects_duplicate_group_server_names():
    registry = minimal_registry_with_harness({
        "fetcher": {"transport": "stdio", "command": "npx", "args": ["fetcher-mcp"], "enabled": True},
    })
    registry["mcphub"]["groups"]["harness"]["servers"] = [
        {"name": "fetcher", "tools": ["fetch_urls"]},
        "fetcher",
    ]

    with pytest.raises(ValueError, match=r"mcphub\.groups\.harness\.servers\[1\] duplicates server 'fetcher'"):
        render_groups(registry["mcphub"]["groups"], registry["servers"])


def test_validate_settings_rejects_invalid_registry_group_membership():
    registry = minimal_registry_with_harness({
        "fetcher": {"enabled": True},
        "ffmpeg": {"enabled": False},
    })
    registry["mcphub"]["groups"]["harness"]["servers"] = [
        {"name": "fetcher", "tools": ["fetch_urls"]},
        "fetcher",
        "ffmpeg",
        "missing",
    ]
    settings = {
        "mcpServers": {"fetcher": {}, "ffmpeg": {"disabled": True}},
        "groups": {"harness": {"servers": [{"name": "fetcher", "tools": ["fetch_urls"]}]}},
        "systemConfig": valid_system_config(),
    }

    errors = validate_settings(settings, registry)

    assert "mcphub.groups.harness.servers[1] duplicates server 'fetcher'" in errors
    assert "mcphub.groups.harness.servers[2] references disabled server 'ffmpeg'" in errors
    assert "mcphub.groups.harness.servers[3] references missing server 'missing'" in errors


def test_render_server_entry_emits_streamable_http_type_and_url():
    rendered = render_server_entry({
        "transport": "streamable-http",
        "url": "https://mcp.deepwiki.com/mcp",
        "timeout_ms": 600000,
    })

    assert rendered == {
        "type": "streamable-http",
        "url": "https://mcp.deepwiki.com/mcp",
        "timeout": 600000,
    }


def test_render_server_entry_emits_stdio_command_and_args():
    rendered = render_server_entry({
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "mcp-remote", "https://mcp.context7.com/mcp/oauth"],
        "timeout_ms": 600000,
    })

    assert rendered == {
        "command": "npx",
        "args": ["-y", "mcp-remote", "https://mcp.context7.com/mcp/oauth"],
        "timeout": 600000,
    }


def test_render_server_entry_allows_stdio_without_args():
    rendered = render_server_entry({
        "transport": "stdio",
        "command": "uvx",
    })

    assert rendered == {
        "command": "uvx",
    }


def test_render_server_entry_emits_openapi_config():
    rendered = render_server_entry({
        "transport": "openapi",
        "openapi": {"url": "https://api.example.test/openapi.json"},
        "headers": {"X-Api-Key": {"env_var": "EXAMPLE_API_KEY"}},
        "passthroughHeaders": ["x-request-id"],
        "timeout_ms": 120000,
    })

    assert rendered == {
        "type": "openapi",
        "openapi": {"url": "https://api.example.test/openapi.json"},
        "headers": {"X-Api-Key": "${EXAMPLE_API_KEY}"},
        "passthroughHeaders": ["x-request-id"],
        "timeout": 120000,
    }


def test_render_server_entry_rejects_unknown_transport():
    with pytest.raises(ValueError, match="unsupported MCPHub server transport"):
        render_server_entry({"transport": "streamable-http-typo", "command": "npx"})


def test_mcp_registry_schema_rejects_unknown_server_transport():
    repo_root = Path(__file__).resolve().parents[1]
    registry = json.loads((repo_root / "config" / "mcp-registry.json").read_text(encoding="utf-8"))
    schema = json.loads((repo_root / "config" / "schemas" / "mcp-registry.schema.json").read_text(encoding="utf-8"))
    invalid = deepcopy(registry)
    invalid["servers"]["deepwiki"]["transport"] = "streamable-http-typo"

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(invalid)


def test_serialize_settings_is_stable_json():
    repo_root = Path(__file__).resolve().parents[1]
    registry = json.loads((repo_root / "config" / "mcp-registry.json").read_text(encoding="utf-8"))
    generated = generate_settings(registry)
    assert serialize_settings(generated).endswith("\n")
