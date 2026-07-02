"""Canonical MCPHub endpoint projection from config/mcp-registry.json."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

from wagents.context import get_repo_root
from wagents.repo_paths import render_portable_path

MCPHUB_DEFAULT_URL = "http://127.0.0.1:46683/mcp"
MCPHUB_PROJECTION_MODES = {"http", "remote-stdio"}


def _server_enabled_for_harness(entry: dict[str, Any], harness: str | None) -> bool:
    if entry.get("enabled") is False:
        return False
    return not (harness and harness in set(entry.get("exclude_from_harnesses", [])))


def enabled_registry_servers(registry: dict[str, Any], harness: str | None = None) -> dict[str, Any]:
    return {
        name: entry
        for name, entry in registry.get("servers", {}).items()
        if _server_enabled_for_harness(entry, harness)
    }


def registry_server_ids(registry: dict[str, Any]) -> set[str]:
    return {
        name
        for name, entry in registry.get("servers", {}).items()
        if isinstance(entry, dict)
    }


def mcphub_remote_stdio() -> Path:
    return get_repo_root() / "scripts" / "mcphub" / "remote-stdio.sh"


def mcphub_config(registry: dict[str, Any]) -> dict[str, Any]:
    config = registry.get("mcphub")
    return config if isinstance(config, dict) else {}


def mcphub_enabled(registry: dict[str, Any]) -> bool:
    return mcphub_config(registry).get("enabled") is True


def mcphub_mcp_url(raw_url: str) -> str:
    url = raw_url.rstrip("/")
    return url if url.endswith("/mcp") else f"{url}/mcp"


def mcphub_url(registry: dict[str, Any], harness: str | None = None) -> str:
    config = mcphub_config(registry)
    client = mcphub_client_config(registry, harness)
    client_url = client.get("url") if isinstance(client, dict) else None
    if isinstance(client_url, str) and client_url:
        return mcphub_mcp_url(client_url)
    if client.get("url_source") == "public":
        public_url = config.get("public_url")
        if isinstance(public_url, str) and public_url:
            return mcphub_mcp_url(public_url)
    raw_url = config.get("url")
    if isinstance(raw_url, str) and raw_url:
        return mcphub_mcp_url(raw_url)
    base_url = str(config.get("base_url", MCPHUB_DEFAULT_URL.removesuffix("/mcp"))).rstrip("/")
    return mcphub_mcp_url(base_url)


def mcphub_projection_mode(registry: dict[str, Any], harness: str | None, default: str) -> str:
    config = mcphub_config(registry)
    adapters = config.get("projection_adapters")
    raw_mode = adapters.get(harness) if isinstance(adapters, dict) and harness else None
    if raw_mode is None:
        raw_mode = config.get("mode", default)
    mode = str(raw_mode)
    return mode if mode in MCPHUB_PROJECTION_MODES else default


def mcphub_bearer_env_var(registry: dict[str, Any]) -> str:
    return str(mcphub_config(registry).get("bearer_token_env_var", "MCPHUB_BEARER_TOKEN"))


def mcphub_client_config(registry: dict[str, Any], harness: str | None) -> dict[str, Any]:
    clients = mcphub_config(registry).get("clients")
    if not isinstance(clients, dict):
        return {}
    default = clients.get("default")
    config = clients.get(harness) if harness else None
    merged: dict[str, Any] = default.copy() if isinstance(default, dict) else {}
    if isinstance(config, dict):
        merged.update(config)
    return merged


def mcphub_endpoint_name(registry: dict[str, Any], harness: str | None, kind: str, name: str = "") -> str:
    client = mcphub_client_config(registry, harness)
    if kind == "server" and client.get("server_endpoint_name_style") == "base":
        return name
    if kind == "group":
        return f"mcphub_group_{name}"
    if kind == "server":
        return f"mcphub_server_{name}"
    if kind == "smart":
        return f"mcphub_smart_group_{name}" if name else "mcphub_smart_all"
    return "mcphub_all"


def mcphub_spec_enabled_for_harness(registry: dict[str, Any], harness: str | None, spec: dict[str, Any]) -> bool:
    if harness != "opencode":
        return bool(spec["enabled"])
    client = mcphub_client_config(registry, harness)
    endpoint_kinds = client.get("enabled_endpoint_kinds")
    enabled_kinds = set(endpoint_kinds) if isinstance(endpoint_kinds, list) else {"all", "group"}
    kind = str(spec.get("kind", ""))
    if kind == "server" and client.get("enable_server_endpoints") is False:
        return False
    if kind == "group":
        enabled_groups_raw = client.get("enabled_groups")
        enabled_groups = set(enabled_groups_raw) if isinstance(enabled_groups_raw, list) else set()
        if enabled_groups and spec.get("group") not in enabled_groups:
            return False
    return bool(spec["enabled"]) and kind in enabled_kinds


def mcphub_endpoint_enabled(registry: dict[str, Any], harness: str | None, kind: str, name: str = "") -> bool:
    client = mcphub_client_config(registry, harness)
    enabled_raw = client.get("enabled_endpoint_kinds")
    enabled_kinds = set(enabled_raw) if isinstance(enabled_raw, list) else {"all", "group"}
    if kind not in enabled_kinds:
        return False
    if kind == "server" and client.get("enable_server_endpoints") is False:
        return False
    if kind == "group":
        enabled_groups_raw = client.get("enabled_groups")
        enabled_groups = set(enabled_groups_raw) if isinstance(enabled_groups_raw, list) else set()
        if enabled_groups and name not in enabled_groups:
            return False
    return True


def mcphub_workflow_group_ids(registry: dict[str, Any]) -> list[str]:
    groups = mcphub_config(registry).get("groups", {})
    if not isinstance(groups, dict):
        return []
    return sorted(
        name
        for name, group in groups.items()
        if isinstance(group, dict) and group.get("enabled") is not False
    )


def mcphub_full_fleet_client_config(registry: dict[str, Any]) -> dict[str, Any]:
    workflow_groups = mcphub_workflow_group_ids(registry)
    return {
        "included_endpoint_kinds": ["all", "group", "server"],
        "included_groups": workflow_groups,
        "enabled_endpoint_kinds": ["all", "group", "server"],
        "enabled_groups": workflow_groups,
        "enable_server_endpoints": True,
    }


def mcphub_groups(registry: dict[str, Any], harness: str | None = None) -> dict[str, dict[str, Any]]:
    groups = mcphub_config(registry).get("groups", {})
    if not isinstance(groups, dict):
        return {}
    server_ids = registry_server_ids(registry)
    rendered: dict[str, dict[str, Any]] = {}
    for name, group in groups.items():
        if not isinstance(group, dict) or group.get("enabled") is False:
            continue
        servers = []
        for server in group.get("servers", []):
            server_name = server if isinstance(server, str) else server.get("name") if isinstance(server, dict) else None
            if server_name in server_ids:
                servers.append(server)
        rendered[str(name)] = {**group, "servers": servers}
    return rendered


def mcphub_smart_routing_enabled(registry: dict[str, Any]) -> bool:
    smart = mcphub_config(registry).get("smart_routing", {})
    return isinstance(smart, dict) and smart.get("enabled") is True


def mcphub_endpoint_specs(registry: dict[str, Any], harness: str | None = None) -> list[dict[str, Any]]:
    if not mcphub_enabled(registry):
        return []
    client = mcphub_client_config(registry, harness)
    included_raw = client.get("included_endpoint_kinds")
    included = set(included_raw) if isinstance(included_raw, list) else None

    def should_include(kind: str) -> bool:
        return included is None or kind in included

    hub_url = mcphub_url(registry, harness)
    included_groups_raw = client.get("included_groups")
    included_groups = set(included_groups_raw) if isinstance(included_groups_raw, list) else None
    included_servers_raw = client.get("included_servers")
    included_servers = set(included_servers_raw) if isinstance(included_servers_raw, list) else None
    enabled_servers = set(enabled_registry_servers(registry, harness))
    server_ids = registry_server_ids(registry)

    specs: list[dict[str, Any]] = []
    if should_include("all"):
        specs.append({
            "name": mcphub_endpoint_name(registry, harness, "all"),
            "url": hub_url,
            "enabled": mcphub_endpoint_enabled(registry, harness, "all"),
            "kind": "all",
        })
    for group_name in sorted(mcphub_groups(registry, harness)):
        if not should_include("group"):
            continue
        if included_groups is not None and group_name not in included_groups:
            continue
        specs.append({
            "name": mcphub_endpoint_name(registry, harness, "group", group_name),
            "url": f"{hub_url}/{group_name}",
            "enabled": mcphub_endpoint_enabled(registry, harness, "group", group_name),
            "kind": "group",
            "group": group_name,
        })
    for server in sorted(server_ids):
        if not should_include("server"):
            continue
        if included_servers is not None and server not in included_servers:
            continue
        specs.append({
            "name": mcphub_endpoint_name(registry, harness, "server", server),
            "url": f"{hub_url}/{server}",
            "enabled": server in enabled_servers and mcphub_endpoint_enabled(registry, harness, "server", server),
            "kind": "server",
            "server": server,
        })
    if should_include("smart") and mcphub_smart_routing_enabled(registry):
        smart = mcphub_config(registry).get("smart_routing", {})
        smart_path = str(smart.get("path", smart.get("base_path", "$smart"))).strip("/")
        if smart_path.startswith("mcp/"):
            smart_path = smart_path.removeprefix("mcp/")
        specs.append({
            "name": mcphub_endpoint_name(registry, harness, "smart"),
            "url": f"{hub_url}/{smart_path}",
            "enabled": mcphub_endpoint_enabled(registry, harness, "smart"),
            "kind": "smart",
        })
        for spec in list(specs):
            if spec["kind"] != "group":
                continue
            specs.append({
                "name": mcphub_endpoint_name(registry, harness, "smart", spec["group"]),
                "url": f"{hub_url}/{smart_path}/{spec['group']}",
                "enabled": mcphub_endpoint_enabled(registry, harness, "smart", spec["group"]),
                "kind": "smart",
                "group": spec["group"],
            })
    return specs


def render_mcphub_stdio_server(
    registry: dict[str, Any],
    url: str,
    *,
    enabled: bool = True,
    fallbacks: dict[str, str] | None = None,
    local_values: bool = True,
    render_env_value: Any | None = None,
) -> dict[str, Any]:
    token_env = mcphub_bearer_env_var(registry)
    if fallbacks is not None and render_env_value is not None:
        return {
            "command": render_portable_path(mcphub_remote_stdio()),
            "args": [url],
            "env": {token_env: render_env_value({"env_var": token_env}, fallbacks, local_values=local_values)},
            "disabled": not enabled,
        }
    repo_root = get_repo_root()
    return {
        "command": f"${repo_root}/scripts/mcphub/remote-stdio.sh",
        "args": [url],
        "env": {token_env: "${" + token_env + "}"},
        "disabled": not enabled,
    }
