#!/usr/bin/env python3
"""Record authenticated MCPHub reachability for enabled candidate MCP servers."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

import anyio
import httpx
from mcp.client.streamable_http import streamablehttp_client

from mcp import ClientSession
from wagents.candidate_evidence import receipt_metadata
from wagents.candidate_mcp_activation import (
    bearer_token_looks_usable,
    canonical_json_sha256,
    configured_tools,
    mcphub_exposed_tool_names,
    normalized_projection,
)
from wagents.candidate_receipts import ReceiptStore

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "planning/manifests/candidate-corpus-jul2026"
RECEIPTS = MANIFEST_DIR / "runtime-activation-receipts.json"
RUNTIME_STATE = Path("~/.local/share/wagents/candidate-runtime").expanduser()
ACTIVATION_SCRIPT = ROOT / "scripts/record_candidate_runtime_activation.py"
MCP_REGISTRY = ROOT / "config/mcp-registry.json"
MCPHUB_SETTINGS = ROOT / "mcp/mcphub/mcp_settings.json"
MCPHUB_LIVE_SETTINGS = ROOT / ".mcphub/runtime/mcp_settings.json"
EXPECTED_MCP_COUNT = 17
MANAGED_BASE_URL = "http://127.0.0.1:46683"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def candidate_specs(activation: Any) -> dict[str, tuple[str, dict[str, Any]]]:
    specs = {
        str(seed.get("mcp_server") or ""): (url, seed)
        for url, rows in activation.runtime_specs().items()
        for seed in rows
        if seed.get("kind") == "mcp"
    }
    if len(specs) != EXPECTED_MCP_COUNT or "" in specs:
        raise ValueError(f"expected {EXPECTED_MCP_COUNT} named candidate MCP artifacts")
    return specs


def projected_enabled(entry: dict[str, Any] | None) -> bool:
    return isinstance(entry, dict) and entry.get("enabled") is not False


async def probe_server(endpoint: str, bearer_token: str, timeout: float) -> list[str]:
    headers = {"Authorization": f"Bearer {bearer_token}"}
    with anyio.fail_after(timeout):
        async with streamablehttp_client(
            endpoint,
            headers=headers,
            timeout=timeout,
            sse_read_timeout=timeout,
        ) as (read, write, _session_id):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
    names = sorted({str(tool.name) for tool in tools.tools if str(tool.name)})
    if not names:
        raise RuntimeError("MCPHub server endpoint returned no tools")
    return names


def probe_unauthenticated_denial(
    endpoint: str,
    timeout: float,
    transport: httpx.BaseTransport | None = None,
) -> int:
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    request = {
        "jsonrpc": "2.0",
        "id": "wagents-activation-denial",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "wagents-activation-denial", "version": "1"},
        },
    }
    with httpx.Client(timeout=timeout, transport=transport) as client:
        response = client.post(endpoint, headers=headers, json=request)
    if response.status_code not in {401, 403}:
        raise RuntimeError("MCPHub endpoint did not deny the unauthenticated request")
    return response.status_code


def revocation_receipt(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": str(report["artifact_id"]),
        "phase": "activation",
        "status": "revoked",
        "mcp_server": str(report["mcp_server"]),
        "revocation_reason": str(report.get("blocker") or "activation-not-proven"),
        "recorded_at": datetime.now(UTC).isoformat(),
        "secret_value_recorded": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--server", action="append")
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()
    if args.timeout <= 0:
        raise ValueError("--timeout must be positive")

    activation = load_module("_candidate_mcp_activation_receipts", ACTIVATION_SCRIPT)
    specs = candidate_specs(activation)
    requested = set(args.server or specs)
    unknown = sorted(requested - set(specs))
    if unknown:
        raise ValueError(f"unknown candidate MCP server ids: {unknown}")

    registry = load_json(MCP_REGISTRY)
    generated = load_json(MCPHUB_SETTINGS)
    live = load_json(MCPHUB_LIVE_SETTINGS) if MCPHUB_LIVE_SETTINGS.is_file() else {}
    registry_servers = registry.get("servers", {})
    generated_servers = generated.get("mcpServers", {})
    live_servers = live.get("mcpServers", {})
    if not all(isinstance(value, dict) for value in (registry_servers, generated_servers, live_servers)):
        raise ValueError("MCP registry, generated settings, and live settings must contain server objects")
    if registry.get("mcphub", {}).get("base_url") != MANAGED_BASE_URL:
        raise ValueError("candidate activation requires the managed loopback MCPHub URL")
    if registry.get("mcphub", {}).get("bearer_token_env_var") != "MCPHUB_BEARER_TOKEN":
        raise ValueError("candidate activation requires the managed MCPHub bearer-token policy")
    bearer_keys = live.get("bearerKeys", [])
    if not isinstance(bearer_keys, list):
        raise ValueError("live MCPHub settings bearerKeys must be a list")

    source_shas = activation.inspected_source_shas()
    store = ReceiptStore(RECEIPTS, RUNTIME_STATE)
    owned_keys = {
        (activation.artifact_id(url, seed), phase)
        for server_id, (url, seed) in specs.items()
        if server_id in requested
        for phase in ("install", "activation")
    }
    snapshot = store.snapshot(artifact_keys=owned_keys)
    rows = snapshot.artifact_rows
    upserts: dict[tuple[str, str], dict[str, Any]] = {}
    reports: list[dict[str, Any]] = []
    bearer_token = os.environ.get("MCPHUB_BEARER_TOKEN", "")

    for server_id in sorted(requested):
        url, seed = specs[server_id]
        artifact_id = activation.artifact_id(url, seed)
        registry_entry = registry_servers.get(server_id)
        generated_entry = generated_servers.get(server_id)
        live_entry = live_servers.get(server_id)
        registry_enabled = isinstance(registry_entry, dict) and registry_entry.get("enabled") is True
        generated_enabled = projected_enabled(generated_entry if isinstance(generated_entry, dict) else None)
        live_enabled = projected_enabled(live_entry if isinstance(live_entry, dict) else None)
        blocker_fields = [
            name
            for name, enabled in (
                ("registry", registry_enabled),
                ("generated", generated_enabled),
                ("live", live_enabled),
            )
            if not enabled
        ]
        if blocker_fields:
            reports.append({
                "artifact_id": artifact_id,
                "mcp_server": server_id,
                "status": "blocked",
                "blocker": "mcp-disabled:" + ",".join(blocker_fields),
                "network_probe_performed": False,
            })
            continue
        if not bearer_token_looks_usable(bearer_token):
            reports.append({
                "artifact_id": artifact_id,
                "mcp_server": server_id,
                "status": "blocked",
                "blocker": "MCPHUB_BEARER_TOKEN-missing-or-placeholder",
                "network_probe_performed": False,
            })
            continue
        if not bearer_keys:
            reports.append({
                "artifact_id": artifact_id,
                "mcp_server": server_id,
                "status": "blocked",
                "blocker": "live-mcphub-bearer-key-not-configured",
                "network_probe_performed": False,
            })
            continue

        registry_projection = normalized_projection(registry_entry, registry=True)
        generated_projection = normalized_projection(generated_entry, registry=False)
        live_projection = normalized_projection(live_entry, registry=False)
        if registry_projection != generated_projection or generated_projection != live_projection:
            reports.append({
                "artifact_id": artifact_id,
                "mcp_server": server_id,
                "status": "blocked",
                "blocker": "mcp-projection-mismatch",
                "network_probe_performed": False,
            })
            continue

        endpoint = f"{MANAGED_BASE_URL}/mcp/{quote(server_id, safe='')}"
        install_receipt = rows.get((artifact_id, "install"))
        installed_digest, install_errors = activation.current_install_digest(install_receipt)
        if install_errors:
            reports.append({
                "artifact_id": artifact_id,
                "mcp_server": server_id,
                "status": "blocked",
                "blocker": "current-install-digest-invalid",
                "network_probe_performed": False,
            })
            continue
        current_digest = str(installed_digest or "unavailable")
        source_commit_sha = str(seed.get("source_commit_sha") or source_shas.get(url.lower()) or "")
        if not source_commit_sha:
            reports.append({
                "artifact_id": artifact_id,
                "mcp_server": server_id,
                "status": "blocked",
                "blocker": "inspected-source-sha-missing",
                "network_probe_performed": False,
            })
            continue
        try:
            unauthenticated_status_code = probe_unauthenticated_denial(endpoint, args.timeout)
            tool_names = anyio.run(probe_server, endpoint, bearer_token, args.timeout)
        except Exception as error:
            reports.append({
                "artifact_id": artifact_id,
                "mcp_server": server_id,
                "status": "failed",
                "blocker": "mcphub-probe-failed",
                "error_type": type(error).__name__,
                "network_probe_performed": True,
            })
            continue
        expected_tools, tools_allow_all = configured_tools(registry_entry)
        expected_exposed_tools = mcphub_exposed_tool_names(server_id, expected_tools)
        if not tools_allow_all and not set(expected_exposed_tools).issubset(tool_names):
            reports.append({
                "artifact_id": artifact_id,
                "mcp_server": server_id,
                "status": "failed",
                "blocker": "configured-tools-not-exposed",
                "network_probe_performed": True,
            })
            continue
        package_id = f"{seed.get('package_manager')}:{seed.get('package_name')}"
        resolved_version = str(seed.get("version") or "")
        receipt = {
            "artifact_id": artifact_id,
            "phase": "activation",
            "status": "passed",
            "mcp_server": server_id,
            "endpoint": endpoint,
            "registry_enabled": True,
            "generated_enabled": True,
            "live_enabled": True,
            "mcphub_reachable": True,
            "registry_entry_sha256": canonical_json_sha256(registry_entry),
            "generated_entry_sha256": canonical_json_sha256(generated_entry),
            "live_entry_sha256": canonical_json_sha256(live_entry),
            "registry_projection_sha256": canonical_json_sha256(registry_projection),
            "generated_projection_sha256": canonical_json_sha256(generated_projection),
            "live_projection_sha256": canonical_json_sha256(live_projection),
            "configured_tool_names": expected_tools,
            "configured_tool_names_sha256": canonical_json_sha256(expected_tools),
            "configured_tools_allow_all": tools_allow_all,
            "tool_count": len(tool_names),
            "tool_names": tool_names,
            "tool_names_sha256": canonical_json_sha256(tool_names),
            "bearer_auth_used": True,
            "mcphub_bearer_key_configured": True,
            "unauthenticated_denied": True,
            "unauthenticated_status_code": unauthenticated_status_code,
            "secret_value_recorded": False,
            "network_probe_performed": True,
        }
        receipt.update(
            receipt_metadata(
                artifact_id=artifact_id,
                phase="activation",
                source_commit_sha=source_commit_sha,
                package_id=package_id,
                resolved_version=resolved_version,
                installed_digest=current_digest,
            )
        )
        upserts[artifact_id, "activation"] = receipt
        reports.append({
            "artifact_id": artifact_id,
            "mcp_server": server_id,
            "status": "passed",
            "tool_count": len(tool_names),
            "network_probe_performed": True,
        })

    applied = False
    if args.apply:
        for report in reports:
            if report["status"] != "passed":
                upserts[report["artifact_id"], "activation"] = revocation_receipt(report)
    if args.apply and upserts:
        store.commit(snapshot, artifact_upserts=upserts)
        applied = True
    complete = len(reports) == len(requested) and all(row["status"] == "passed" for row in reports)
    print(
        json.dumps(
            {
                "ok": complete,
                "applied": applied,
                "inventory_count": len(specs),
                "selected_count": len(requested),
                "passed_count": sum(row["status"] == "passed" for row in reports),
                "blocked_count": sum(row["status"] == "blocked" for row in reports),
                "failed_count": sum(row["status"] == "failed" for row in reports),
                "secret_value_recorded": False,
                "servers": reports,
            },
            indent=2,
            ensure_ascii=True,
        )
    )
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
