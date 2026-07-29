from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "_candidate_mcp_activation",
        ROOT / "scripts" / "record_candidate_mcp_activation.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_candidate_mcp_activation_inventory_is_exact() -> None:
    module = _module()
    activation = module.load_module("_candidate_mcp_runtime_specs_test", module.ACTIVATION_SCRIPT)

    specs = module.candidate_specs(activation)

    assert len(specs) == module.EXPECTED_MCP_COUNT == 17
    assert set(specs) == {
        "antv-chart",
        "axiom-mcp",
        "better-icons",
        "charted",
        "csvglow",
        "designer-skill-mcp",
        "geo-mcp",
        "langfuse-mcp",
        "mcp-dashboards",
        "mcp-excalidraw",
        "mobile-mcp",
        "nullcost",
        "openspec-mcp",
        "paper-search-mcp",
        "papersflow",
        "prompt-to-asset",
        "semiotic",
    }


@pytest.mark.parametrize(
    "value",
    (
        "",
        " change-me",
        "change-me",
        "${MCPHUB_BEARER_TOKEN}",
        "<token>",
        "replace-with-local-bearer-token",
        "your_token_here",
    ),
)
def test_placeholder_bearer_tokens_are_rejected(value: str) -> None:
    module = _module()

    assert module.bearer_token_looks_usable(value) is False


def test_registry_projection_normalizes_env_and_timeout() -> None:
    module = _module()
    registry = {
        "command": "candidate",
        "args": ["serve"],
        "enabled": True,
        "env": {"MODE": {"value": "safe"}},
        "timeout_ms": 90_000,
    }
    projected = {
        "command": "candidate",
        "args": ["serve"],
        "enabled": True,
        "env": {"MODE": "safe"},
        "timeout": 90_000,
    }

    assert module.normalized_projection(registry, registry=True) == module.normalized_projection(
        projected,
        registry=False,
    )


def test_registry_projection_normalizes_env_var_and_http_transport() -> None:
    module = _module()
    registry = {
        "enabled": True,
        "env": {"TOKEN": {"env_var": "API_TOKEN"}},
        "oauth": {"enabled": True},
        "timeout_ms": 90_000,
        "transport": "streamable-http",
        "url": "https://example.test/mcp",
    }
    projected = {
        "enabled": True,
        "env": {"TOKEN": "${API_TOKEN}"},
        "oauth": {"enabled": True},
        "timeout": 90_000,
        "type": "streamable-http",
        "url": "https://example.test/mcp",
    }

    assert module.normalized_projection(registry, registry=True) == module.normalized_projection(
        projected,
        registry=False,
    )


def test_revocation_receipt_overwrites_activation_phase_without_secret() -> None:
    module = _module()

    receipt = module.revocation_receipt({
        "artifact_id": "candidate-artifact-test",
        "mcp_server": "candidate",
        "blocker": "mcp-disabled:registry",
    })

    assert receipt["phase"] == "activation"
    assert receipt["status"] == "revoked"
    assert receipt["revocation_reason"] == "mcp-disabled:registry"
    assert receipt["secret_value_recorded"] is False


def test_unauthenticated_denial_requires_http_auth_failure() -> None:
    module = _module()
    denied = httpx.MockTransport(lambda _request: httpx.Response(401))
    allowed = httpx.MockTransport(lambda _request: httpx.Response(200))

    assert module.probe_unauthenticated_denial("http://example.test/mcp/server", 1, denied) == 401
    with pytest.raises(RuntimeError, match="did not deny"):
        module.probe_unauthenticated_denial("http://example.test/mcp/server", 1, allowed)


@pytest.mark.parametrize(
    ("server_id", "configured_names", "exposed_names"),
    (
        (
            "better-icons",
            ["search_icons", "search_icons", "get_icon"],
            ["better-icons-get_icon", "better-icons-search_icons"],
        ),
        (
            "openspec-mcp",
            ["openspec_list_changes"],
            ["openspec-mcp-openspec_list_changes"],
        ),
        (
            "semiotic",
            ["suggestChart"],
            ["semiotic-suggestChart"],
        ),
    ),
)
def test_mcphub_tool_names_are_projected_into_the_exact_server_namespace(
    server_id: str,
    configured_names: list[str],
    exposed_names: list[str],
) -> None:
    module = _module()

    assert module.mcphub_exposed_tool_names(server_id, configured_names) == exposed_names


def test_disabled_candidate_mcp_preview_is_fail_closed_without_network_or_secret(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    module = _module()
    _configure_main(module, monkeypatch, tmp_path, enabled=False)
    monkeypatch.delenv("MCPHUB_BEARER_TOKEN", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        ["record_candidate_mcp_activation.py", "--server", "better-icons"],
    )

    assert module.main() == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["applied"] is False
    assert payload["selected_count"] == 1
    assert payload["blocked_count"] == 1
    assert payload["failed_count"] == 0
    assert payload["secret_value_recorded"] is False
    assert payload["servers"] == [
        {
            "artifact_id": "candidate-artifact-86b9df2d26726ed5",
            "mcp_server": "better-icons",
            "status": "blocked",
            "blocker": "mcp-disabled:registry,generated,live",
            "network_probe_performed": False,
        }
    ]


def _configure_main(
    module: Any,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    enabled: bool,
) -> tuple[Path, str]:
    registry_entry = {
        "args": [],
        "command": "candidate",
        "enabled": enabled,
        "env": {},
        "timeout_ms": 90_000,
        "tools": ["search_icons"],
        "transport": "stdio",
    }
    projected_entry = {
        "args": [],
        "command": "candidate",
        "enabled": enabled,
        "timeout": 90_000,
    }
    registry = {
        "mcphub": {
            "base_url": module.MANAGED_BASE_URL,
            "bearer_token_env_var": "MCPHUB_BEARER_TOKEN",
        },
        "servers": {"better-icons": registry_entry},
    }
    generated = {"mcpServers": {"better-icons": projected_entry}}
    live = {
        "mcpServers": {"better-icons": projected_entry},
        "bearerKeys": [{"name": "configured"}],
    }
    paths = {
        "MCP_REGISTRY": tmp_path / "mcp-registry.json",
        "MCPHUB_SETTINGS": tmp_path / "generated-settings.json",
        "MCPHUB_LIVE_SETTINGS": tmp_path / "live-settings.json",
    }
    for name, path in paths.items():
        payload = registry if name == "MCP_REGISTRY" else generated if name == "MCPHUB_SETTINGS" else live
        path.write_text(json.dumps(payload), encoding="utf-8")
        monkeypatch.setattr(module, name, path)
    receipts = tmp_path / "receipts.json"
    monkeypatch.setattr(module, "RECEIPTS", receipts)
    monkeypatch.setattr(module, "RUNTIME_STATE", tmp_path / "runtime-state")
    artifact_id = "candidate-artifact-86b9df2d26726ed5"
    return receipts, artifact_id


def test_apply_commits_authenticated_activation_without_recording_token(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    module = _module()
    receipts, artifact_id = _configure_main(module, monkeypatch, tmp_path, enabled=True)
    observed: dict[str, str] = {}

    async def fake_probe(endpoint: str, bearer_token: str, timeout: float) -> list[str]:
        await module.anyio.sleep(0)
        observed.update(endpoint=endpoint, bearer_token=bearer_token, timeout=str(timeout))
        return ["better-icons-search_icons"]

    monkeypatch.setattr(module, "probe_server", fake_probe)
    monkeypatch.setattr(module, "probe_unauthenticated_denial", lambda *_args: 401)
    monkeypatch.setenv("MCPHUB_BEARER_TOKEN", "unit-test-private-bearer-7b1f")
    monkeypatch.setattr(
        sys,
        "argv",
        ["record_candidate_mcp_activation.py", "--server", "better-icons", "--apply"],
    )

    assert module.main() == 0
    output = capsys.readouterr().out
    payload = json.loads(output)
    ledger = json.loads(receipts.read_text(encoding="utf-8"))
    receipt = next(row for row in ledger["receipts"] if row["artifact_id"] == artifact_id)

    assert payload["ok"] is True
    assert payload["applied"] is True
    assert receipt["phase"] == "activation"
    assert receipt["status"] == "passed"
    assert receipt["unauthenticated_status_code"] == 401
    assert receipt["tool_names"] == ["better-icons-search_icons"]
    assert observed["bearer_token"] == "unit-test-private-bearer-7b1f"
    assert "unit-test-private-bearer-7b1f" not in receipts.read_text(encoding="utf-8")
    assert "unit-test-private-bearer-7b1f" not in output


def test_apply_revokes_stale_activation_when_server_is_disabled(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    module = _module()
    receipts, artifact_id = _configure_main(module, monkeypatch, tmp_path, enabled=False)
    receipts.write_text(
        json.dumps({
            "version": 2,
            "revision": 1,
            "receipts": [
                {
                    "artifact_id": artifact_id,
                    "phase": "activation",
                    "status": "passed",
                }
            ],
            "closure_receipts": [],
        }),
        encoding="utf-8",
    )
    monkeypatch.delenv("MCPHUB_BEARER_TOKEN", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        ["record_candidate_mcp_activation.py", "--server", "better-icons", "--apply"],
    )

    assert module.main() == 1
    payload = json.loads(capsys.readouterr().out)
    ledger = json.loads(receipts.read_text(encoding="utf-8"))
    receipt = next(row for row in ledger["receipts"] if row["artifact_id"] == artifact_id)

    assert payload["ok"] is False
    assert payload["applied"] is True
    assert receipt["phase"] == "activation"
    assert receipt["status"] == "revoked"
    assert receipt["revocation_reason"] == "mcp-disabled:registry,generated,live"
