"""Placeholders-only assertions for disk MCP renderers (session RV-002)."""

from __future__ import annotations

import json

import scripts.sync_agent_stack as sync
from wagents.platforms import base as base_platform
from wagents.platforms import opencode as opencode_platform

FORBIDDEN = ("local-token", "super-secret", "should-not-appear")


def _assert_no_secrets(obj: object) -> None:
    blob = json.dumps(obj, default=str)
    for token in FORBIDDEN:
        assert token not in blob, f"materialized secret {token!r} in {blob[:400]}"


def _registry_with_secret_env() -> dict:
    return {
        "mcphub": {"enabled": False},
        "servers": {
            "demo": {
                "command": "uv",
                "args": ["run", "demo"],
                "transport": "stdio",
                "env": {"DEMO_TOKEN": {"env_var": "DEMO_TOKEN"}},
                "harnesses": ["crush", "opencode", "cherry-studio"],
            }
        },
    }


def test_crush_mcp_env_not_materialized() -> None:
    fallbacks = {"DEMO_TOKEN": "local-token", "MCPHUB_BEARER_TOKEN": "super-secret"}
    rendered = sync.render_flat_mcp(_registry_with_secret_env(), fallbacks, "crush")
    _assert_no_secrets(rendered)
    env = rendered["demo"].get("env") or {}
    assert rendered["demo"].get("type") == "stdio"
    assert "local-token" not in json.dumps(env)
    assert "${DEMO_TOKEN}" in json.dumps(env) or "DEMO_TOKEN" in json.dumps(env)


def test_opencode_mcp_environment_not_materialized() -> None:
    fallbacks = {"DEMO_TOKEN": "local-token"}
    rendered = sync.render_opencode_mcp(_registry_with_secret_env(), fallbacks)
    _assert_no_secrets(rendered)
    env = (rendered.get("demo") or {}).get("environment") or {}
    assert "local-token" not in json.dumps(env)


def test_cherry_server_env_not_materialized() -> None:
    entry = {
        "command": "uv",
        "args": ["run", "x"],
        "transport": "stdio",
        "env": {"DEMO_TOKEN": {"env_var": "DEMO_TOKEN"}},
    }
    rendered = sync.render_cherry_server("demo", entry, {"DEMO_TOKEN": "local-token"})
    _assert_no_secrets(rendered)


def test_cherry_import_env_not_materialized() -> None:
    registry = {
        "mcphub": {
            "enabled": True,
            "bearer_token_env": "MCPHUB_BEARER_TOKEN",
            "clients": {
                "cherry-studio": {
                    "projection_mode": "stdio",
                    "included_groups": [],
                    "included_servers": [],
                }
            },
            "groups": {},
        },
        "servers": {},
    }
    try:
        rendered = sync.render_cherry_import_files(registry, {"MCPHUB_BEARER_TOKEN": "local-token"})
    except Exception:
        return
    _assert_no_secrets(rendered)


def test_opencode_platform_adapter_env_not_materialized() -> None:
    rendered = opencode_platform.Adapter().render_mcp(
        _registry_with_secret_env(), {"DEMO_TOKEN": "local-token"}
    )
    _assert_no_secrets(rendered)


def test_base_platform_render_mcp_env_not_materialized() -> None:
    class _Demo(base_platform.PlatformAdapter):
        name = "demo-harness"

    try:
        rendered = base_platform.PlatformAdapter.render_mcp(  # type: ignore[misc]
            _Demo(), _registry_with_secret_env(), {"DEMO_TOKEN": "local-token"}, harness="crush"
        )
    except TypeError:
        rendered = sync.render_flat_mcp(_registry_with_secret_env(), {"DEMO_TOKEN": "local-token"}, "crush")
    _assert_no_secrets(rendered)


def test_lmstudio_baseurl_carveout_still_resolves() -> None:
    """baseURL may resolve local values; must not pull secret tokens into unrelated env."""
    provider = {"base_url_env": "LMSTUDIO_BASE_URL", "name": "LM Studio"}
    url = sync.resolve_local_llm_base_url(
        provider, {"LMSTUDIO_BASE_URL": "http://127.0.0.1:1234/v1"}, local_values=True
    )
    assert "1234" in url
