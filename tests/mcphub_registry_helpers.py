"""Shared helpers for MCP registry group membership tests."""

from __future__ import annotations


def group_server_name(server: str | dict) -> str:
    if isinstance(server, dict):
        return server["name"]
    return server


def group_server_names(group: dict) -> list[str]:
    return [group_server_name(server) for server in group["servers"]]


def group_server_entry(group: dict, name: str) -> str | dict | None:
    for server in group["servers"]:
        if group_server_name(server) == name:
            return server
    return None