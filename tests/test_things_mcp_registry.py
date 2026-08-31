"""Closed topology, policy, and projection tests for the Things++ MCP group."""

from __future__ import annotations

import copy
import json
import tomllib
from pathlib import Path

import jsonschema
import pytest

from scripts.generate_mcphub_settings import generate_settings
from scripts.sync_agent_stack import repair_codex_config_text
from wagents.mcphub.endpoints import mcphub_endpoint_specs
from wagents.mcphub.things_contract import (
    THINGS_COUNTS,
    THINGS_GROUP,
    THINGS_GROUP_ID,
    THINGS_NORMALIZED_CATALOG_SHA256,
    THINGS_SERVERS,
    ThingsContractError,
    approval_mode_for_tool,
    assert_things_registry_contract,
    load_things_manifest,
    retired_projection_ids,
    validate_things_registry_contract,
)
from wagents.plugin_mcp import render_native_mcp_profile_pack, resolve_mcp_profile

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "config" / "mcp-registry.json"
REGISTRY_SCHEMA_PATH = ROOT / "config" / "schemas" / "mcp-registry.schema.json"


@pytest.fixture
def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _member_name(member: object) -> str | None:
    if isinstance(member, str):
        return member
    if isinstance(member, dict):
        name = member.get("name")
        if isinstance(name, str):
            return name
    return None


def test_canonical_registry_is_schema_valid_and_semantically_closed(registry: dict) -> None:
    schema = json.loads(REGISTRY_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(registry)

    manifest = assert_things_registry_contract(registry)

    assert manifest["counts"] == THINGS_COUNTS
    assert len(manifest["tools"]) == 70
    assert validate_things_registry_contract(registry) == ()


def test_only_things_group_contains_the_three_group_only_backends(registry: dict) -> None:
    groups = registry["mcphub"]["groups"]
    assert [name for name in groups if "things" in name.lower()] == [THINGS_GROUP]
    assert groups[THINGS_GROUP]["id"] == THINGS_GROUP_ID
    assert groups[THINGS_GROUP]["tools_allow_all"] is False
    assert [_member_name(member) for member in groups[THINGS_GROUP]["servers"]] == list(THINGS_SERVERS)

    memberships = {
        server: [
            name for name, group in groups.items() if server in {_member_name(member) for member in group["servers"]}
        ]
        for server in THINGS_SERVERS
    }
    assert memberships == {server: [THINGS_GROUP] for server in THINGS_SERVERS}
    assert "supathings" not in registry["servers"]
    assert all("supathings" not in {_member_name(member) for member in group["servers"]} for group in groups.values())


def test_explicit_allowlists_and_approvals_match_every_manifest_tool(registry: dict) -> None:
    manifest = load_things_manifest()
    by_server = {server: [tool for tool in manifest["tools"] if tool["server"] == server] for server in THINGS_SERVERS}
    for server, tools in by_server.items():
        server_entry = registry["servers"][server]
        group_entry = next(
            member for member in registry["mcphub"]["groups"][THINGS_GROUP]["servers"] if member["name"] == server
        )
        names = [tool["serverToolName"] for tool in tools]
        approvals = {tool["serverToolName"]: approval_mode_for_tool(tool) for tool in tools}
        assert server_entry["group_only"] is True
        assert server_entry["tools_allow_all"] is False
        assert server_entry["tools"] == group_entry["tools"] == names
        assert server_entry["tool_approvals"] == approvals
        assert set(approvals.values()) == {"never", "per-call"}
        assert all(
            mode == ("never" if tool["risk"] == "read-only" else "per-call")
            for tool, mode in zip(tools, approvals.values(), strict=True)
        )


def test_generated_settings_bind_all_seventy_exact_tool_contracts(registry: dict) -> None:
    generated = generate_settings(registry)
    contract = generated["thingsContract"]
    group = next(item for item in generated["groups"] if item["name"] == THINGS_GROUP)

    assert contract["groupId"] == group["id"] == THINGS_GROUP_ID
    assert contract["counts"] == THINGS_COUNTS
    assert contract["normalizedCatalogSha256"] == THINGS_NORMALIZED_CATALOG_SHA256
    assert len(contract["tools"]) == len({tool["publicToolName"] for tool in contract["tools"]}) == 70
    assert len({tool["qualifiedCapabilityId"] for tool in contract["tools"]}) == 70
    assert group["contract"] == {
        "groupId": THINGS_GROUP_ID,
        "normalizedCatalogSha256": THINGS_NORMALIZED_CATALOG_SHA256,
        "toolCount": 70,
        "approvalPolicy": {
            "default": "per-call",
            "readOnlyRisk": "never",
            "otherwise": "per-call",
        },
    }
    assert [len(member["tools"]) for member in group["servers"]] == [41, 21, 8]


def test_group_only_backends_never_get_individual_endpoint_specs(registry: dict) -> None:
    local_specs = mcphub_endpoint_specs(registry, "codex")
    remote_specs = mcphub_endpoint_specs(registry, "chatgpt")

    assert not (set(THINGS_SERVERS) & {spec.get("server") for spec in local_specs})
    local_things = [
        (spec["name"], spec["url"], spec["enabled"]) for spec in local_specs if spec.get("group") == THINGS_GROUP
    ]
    assert local_things == [("mcphub_group_things", "http://127.0.0.1:46683/mcp/things", False)]
    assert [(spec["name"], spec["url"], spec["enabled"]) for spec in remote_specs] == [
        ("mcphub_group_things", "https://mcp.w4w.dev/mcp/things", True)
    ]


def test_profile_policy_is_unsupported_opt_in_and_remote_only(registry: dict) -> None:
    assert resolve_mcp_profile(registry, "portable", THINGS_GROUP).state == "unsupported"
    local = resolve_mcp_profile(registry, "codex-native", THINGS_GROUP)
    assert local.state == "opt-in"
    assert local.endpoint_source == "local"
    remote = resolve_mcp_profile(registry, "chatgpt-app", THINGS_GROUP)
    assert remote.state == "remote-only"
    assert remote.endpoint_source == "public"

    chatgpt_pack = render_native_mcp_profile_pack(registry, "chatgpt-app")
    assert [fragment["group"] for fragment in chatgpt_pack["profiles"]] == [THINGS_GROUP]
    assert chatgpt_pack["profiles"][0]["connection"]["url"] == "https://mcp.w4w.dev/mcp/things"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda value: value["servers"]["things-core"]["tools"].pop(),
            "frozen explicit allowlist",
        ),
        (
            lambda value: value["servers"]["things-shortcuts"].update({"tools_allow_all": True}),
            "tools_allow_all must be false",
        ),
        (
            lambda value: value["servers"]["things-native"]["tool_approvals"].update({"native_health": "per-call"}),
            "tool_approvals drift",
        ),
        (
            lambda value: value["mcphub"]["groups"]["daily"]["servers"].append("things-core"),
            "contains group-only Things servers",
        ),
        (
            lambda value: value["mcphub"]["groups"]["things"]["servers"][0].update({"alias": "things_core"}),
            "exact 41/21/8 allowlists",
        ),
        (
            lambda value: value["mcphub"]["groups"].update({"things-admin": {"enabled": True, "servers": []}}),
            "exactly one Things-related group",
        ),
        (
            lambda value: value["mcphub"]["things_contract"].update({"normalized_catalog_sha256": "0" * 64}),
            "things_contract drift",
        ),
    ],
)
def test_contract_rejects_contraction_alias_bypass_and_policy_drift(
    registry: dict,
    mutation,
    message: str,
) -> None:
    invalid = copy.deepcopy(registry)
    mutation(invalid)

    errors = validate_things_registry_contract(invalid)

    assert any(message in error for error in errors)
    with pytest.raises(ThingsContractError):
        generate_settings(invalid)


def test_scoped_retirement_resolves_only_exact_target_and_location(registry: dict) -> None:
    assert retired_projection_ids(registry, target="codex", location="home") == {
        "supathings",
        "mcphub_server_supathings",
        "things",
    }
    assert retired_projection_ids(registry, target="codex", location="repo") == {
        "supathings",
        "mcphub_server_supathings",
    }
    assert retired_projection_ids(registry, target="opencode", location="home") == {
        "supathings",
        "mcphub_server_supathings",
    }


def test_codex_home_tombstone_removes_only_exact_stale_things_entry(registry: dict) -> None:
    current = """
[mcp_servers.things]
command = "stale-direct-things"

[mcp_servers.custom-things-helper]
command = "user-owned"

[mcp_servers.unrelated]
command = "preserve-me"
"""

    repaired = repair_codex_config_text(current, registry)
    parsed = tomllib.loads(repaired)

    assert "things" not in parsed["mcp_servers"]
    assert parsed["mcp_servers"]["custom-things-helper"]["command"] == "user-owned"
    assert parsed["mcp_servers"]["unrelated"]["command"] == "preserve-me"
