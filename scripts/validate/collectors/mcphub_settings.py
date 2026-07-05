"""Collect MCPHub settings parity and client-profile validation errors."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_mcphub_settings_errors(repo_root: Path) -> list[dict[str, str]]:
    """Validate tracked MCPHub settings and registry client profiles."""
    registry_path = repo_root / "config" / "mcp-registry.json"
    settings_path = repo_root / "mcp" / "mcphub" / "mcp_settings.json"
    if not registry_path.is_file():
        return []

    registry = _load_json(registry_path)
    mcphub = registry.get("mcphub", {})
    if not isinstance(mcphub, dict) or mcphub.get("enabled") is not True:
        return []

    errors: list[dict[str, str]] = []

    try:
        from scripts.generate_mcphub_settings import generate_settings, serialize_settings
        from scripts.mcphub.group_validation import group_server_names
        from scripts.mcphub.validate_settings import validate_settings
    except ImportError as exc:
        errors.append({
            "source": "mcphub-settings",
            "message": f"Unable to import MCPHub validation helpers: {exc}",
        })
        return errors

    try:
        generated = generate_settings(registry)
    except ValueError as exc:
        generated = None
        errors.append({
            "source": "config/mcp-registry.json",
            "message": f"MCPHub settings generation failed: {exc}",
        })
    if settings_path.is_file():
        committed = _load_json(settings_path)
        if generated is not None and serialize_settings(generated) != serialize_settings(committed):
            errors.append({
                "source": "mcp/mcphub/mcp_settings.json",
                "message": "Stale vs registry; run: just mcphub-generate",
            })
        errors.extend({
            "source": "mcp/mcphub/mcp_settings.json",
            "message": message,
        } for message in validate_settings(committed, registry))
    else:
        errors.append({
            "source": "mcp/mcphub/mcp_settings.json",
            "message": "Missing tracked MCPHub settings file",
        })

    expected_harness_servers = [
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
    groups = mcphub.get("groups", {})
    if isinstance(groups, dict):
        harness_group = groups.get("harness", {})
        if isinstance(harness_group, dict) and group_server_names(harness_group) != expected_harness_servers:
            errors.append({
                "source": "config/mcp-registry.json:mcphub.groups.harness",
                "message": "harness must stay the minimal default server set",
            })
        reasoning = groups.get("reasoning", {})
        if isinstance(reasoning, dict) and len(reasoning.get("servers", [])) > 3:
            errors.append({
                "source": "config/mcp-registry.json:mcphub.groups.reasoning",
                "message": "reasoning group must contain at most three servers",
            })

    clients = mcphub.get("clients", {})
    if isinstance(clients, dict):
        chatgpt = clients.get("chatgpt", {})
        if isinstance(chatgpt, dict):
            chatgpt_expectations = {
                "included_endpoint_kinds": ["group"],
                "included_groups": ["tunnel"],
                "enabled_endpoint_kinds": ["group"],
                "enabled_groups": ["tunnel"],
                "enable_server_endpoints": False,
            }
            for key, expected in chatgpt_expectations.items():
                if chatgpt.get(key) != expected:
                    errors.append({
                        "source": "config/mcp-registry.json:mcphub.clients.chatgpt",
                        "message": f"chatgpt {key} must be {expected!r}",
                    })

        bounded_client_expectations = {
            "included_endpoint_kinds": ["group", "server"],
            "included_groups": ["harness"],
            "enabled_endpoint_kinds": ["group"],
            "enabled_groups": ["harness"],
            "enable_server_endpoints": True,
        }
        for harness in ("default", "codex", "grok", "opencode"):
            client = clients.get(harness, {})
            if not isinstance(client, dict):
                continue
            for key, expected in bounded_client_expectations.items():
                if client.get(key) != expected:
                    errors.append({
                        "source": f"config/mcp-registry.json:mcphub.clients.{harness}",
                        "message": f"{key} must be {expected!r} for bounded harness projection",
                    })

    return errors
