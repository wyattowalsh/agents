from __future__ import annotations

from typing import Any, cast

GROUP_SERVER_FIELDS = ("name", "alias", "tools", "prompts", "resources")


def group_server_name(server: Any) -> str | None:
    if isinstance(server, str) and server:
        return server
    if isinstance(server, dict) and isinstance(server.get("name"), str) and server["name"]:
        return server["name"]
    return None


def group_server_names(group: dict[str, Any]) -> list[str]:
    names: list[str] = []
    servers = group.get("servers", [])
    if not isinstance(servers, list):
        return names
    for server in servers:
        name = group_server_name(server)
        if name is not None:
            names.append(name)
    return names


def render_group_server(server: Any) -> str | dict[str, Any]:
    if isinstance(server, str):
        return server
    return {field: server[field] for field in GROUP_SERVER_FIELDS if field in server}


def registry_server_ids(registry_servers: dict[str, Any]) -> set[str]:
    return {name for name, entry in registry_servers.items() if isinstance(entry, dict)}


def enabled_registry_server_ids(registry_servers: dict[str, Any]) -> set[str]:
    return {
        name
        for name, entry in registry_servers.items()
        if isinstance(entry, dict) and entry.get("enabled", True) is True
    }


def enabled_settings_server_ids(settings_servers: dict[str, Any]) -> set[str]:
    return {
        name
        for name, entry in settings_servers.items()
        if not isinstance(entry, dict) or (entry.get("disabled") is not True and entry.get("enabled") is not False)
    }


def validate_group_server_entries(
    group_name: str,
    group: dict[str, Any],
    *,
    all_server_ids: set[str],
    enabled_server_ids: set[str] | None = None,
    source_prefix: str = "groups",
) -> list[str]:
    errors: list[str] = []
    servers = group.get("servers", [])
    if not isinstance(servers, list):
        return [f"{source_prefix}.{group_name}.servers must be a list"]

    seen: set[str] = set()
    for index, server in enumerate(servers):
        path = f"{source_prefix}.{group_name}.servers[{index}]"
        if isinstance(server, dict):
            server_entry = cast("dict[str, Any]", server)
            unknown_fields = sorted(set(server_entry) - set(GROUP_SERVER_FIELDS))
            if unknown_fields:
                errors.append(f"{path} has unsupported fields: {unknown_fields}")
            alias = server_entry.get("alias")
            if alias is not None and (not isinstance(alias, str) or not alias):
                errors.append(f"{path}.alias must be a nonempty string")
            for field in ("tools", "prompts", "resources"):
                if field not in server_entry:
                    continue
                values = server_entry[field]
                if (
                    not isinstance(values, list)
                    or not values
                    or any(not isinstance(value, str) or not value for value in values)
                ):
                    errors.append(f"{path}.{field} must be a nonempty list of nonempty strings")
        name = group_server_name(server)
        if name is None:
            errors.append(f"{path} must be a server name string or object with string name")
            continue
        if name in seen:
            errors.append(f"{path} duplicates server {name!r}")
        else:
            seen.add(name)
        if name not in all_server_ids:
            errors.append(f"{path} references missing server {name!r}")
        elif enabled_server_ids is not None and name not in enabled_server_ids:
            errors.append(f"{path} references disabled server {name!r}")
    return errors


def validate_enabled_registry_group(
    group_name: str,
    group: dict[str, Any],
    registry_servers: dict[str, Any],
    *,
    source_prefix: str = "mcphub.groups",
) -> list[str]:
    return validate_group_server_entries(
        group_name,
        group,
        all_server_ids=registry_server_ids(registry_servers),
        enabled_server_ids=enabled_registry_server_ids(registry_servers),
        source_prefix=source_prefix,
    )
