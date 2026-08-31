"""Hermetic contract tests for the manifest-driven Things core adapter."""

# ruff: noqa: E402

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

REPO_ROOT = Path(__file__).resolve().parents[2]
for package_root in (REPO_ROOT / "packages" / "things-common", REPO_ROOT / "mcp" / "things-core"):
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

from things_common import (
    MutationCoordinator,
    SecureRuntimePaths,
    SecurityViolation,
    canonical_schema_sha256,
    canonical_sha256,
)
from things_core.adapter import ThingsCoreAdapter, _bounded_payload, _diagnostic_payload, _identity
from things_core.backend import (
    UpstreamContractError,
    UpstreamThingsBackend,
    read_safe_auth_token,
    verify_live_tool_contract,
)
from things_core.contracts import (
    CoreContractError,
    adapted_input_schema,
    adapted_output_schema,
    load_contracts,
    public_description,
    validate_arguments,
    validate_frozen_contract,
)
from things_core.provenance import ProvenanceError, verify_distribution_artifacts, verify_installed_distribution
from things_core.server import build_server


class MockBackend:
    """Synthetic backend that never imports or invokes Things."""

    def __init__(self, payload: Any | None = None) -> None:
        self.state = 0
        self.payload = {"success": True} if payload is None else payload
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def call(self, tool: str, arguments: dict[str, Any]) -> Any:
        self.calls.append((tool, arguments))
        if tool in {contract.name for contract in load_contracts() if contract.mutating}:
            self.state += 1
        return self.payload

    async def read_state(self, tool: str, arguments: dict[str, Any]) -> Any:
        return {"tool": tool, "version": self.state, "targets": arguments.get("todo_ids") or arguments.get("id")}

    async def verify(self, tool: str, arguments: dict[str, Any], before: Any, result: Any) -> dict[str, Any]:
        after = await self.read_state(tool, arguments)
        assert after != before
        target_count = len(str(arguments.get("todo_ids", "")).split(",")) if arguments.get("todo_ids") else 1
        return {"changed": target_count, "skipped": 0, "failed": 0, "ambiguous": 0, "readbackVerified": True}


class PartialBackend(MockBackend):
    async def verify(self, tool: str, arguments: dict[str, Any], before: Any, result: Any) -> dict[str, Any]:
        return {"changed": 1, "skipped": 0, "failed": 1, "ambiguous": 0, "readbackVerified": True}


def _coordinator(tmp_path: Path) -> MutationCoordinator:
    return MutationCoordinator(SecureRuntimePaths.create(tmp_path / "runtime"), receipt_ttl_seconds=30)


def _context(*, resource: str = "http://127.0.0.1:46683/mcp/things") -> Any:
    meta = SimpleNamespace(
        model_extra={
            "w4w.dev/thingsPrincipal": "synthetic-principal",
            "w4w.dev/thingsClientId": "synthetic-client",
            "w4w.dev/thingsResource": resource,
        }
    )
    return SimpleNamespace(request_context=SimpleNamespace(meta=meta))


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


def _assert_arrays_bounded(schema: Any) -> None:
    if isinstance(schema, dict):
        if schema.get("type") == "array":
            assert schema["maxItems"] <= 25
        for value in schema.values():
            _assert_arrays_bounded(value)
    elif isinstance(schema, list):
        for value in schema:
            _assert_arrays_bounded(value)


def test_frozen_contract_is_exact_and_hash_verified() -> None:
    contracts = validate_frozen_contract()
    manifest = json.loads((REPO_ROOT / "mcp/things-core/things_core/core_manifest.json").read_text())
    assert len(contracts) == len({contract.name for contract in contracts}) == 41
    assert (
        canonical_sha256([contract.name for contract in contracts]) == manifest["provenance"]["orderedToolNamesSha256"]
    )
    assert (
        canonical_sha256(sorted(contract.name for contract in contracts))
        == manifest["provenance"]["sortedToolNamesSha256"]
    )
    for contract in contracts:
        assert canonical_schema_sha256(contract.upstream_input_schema) == contract.audited_input_sha256
        assert canonical_schema_sha256(contract.upstream_output_schema) == contract.audited_output_sha256


def test_adapted_schemas_are_closed_bounded_and_separate() -> None:
    output = adapted_output_schema()
    assert output["additionalProperties"] is False
    payload_object = output["properties"]["payload"]["anyOf"][0]
    assert payload_object["additionalProperties"] is False
    assert set(payload_object["properties"]) == {"sourceKind", "entries"}
    entry_schema = payload_object["properties"]["entries"]["items"]
    assert entry_schema["additionalProperties"] is False
    assert set(entry_schema["properties"]) == {"path", "value"}
    assert canonical_schema_sha256(output) != load_contracts()[0].audited_output_sha256
    for contract in load_contracts():
        schema = adapted_input_schema(contract)
        assert schema["additionalProperties"] is False
        _assert_arrays_bounded(schema)
        assert "command" not in schema["properties"]
        assert "url" not in schema["properties"]
        if contract.mutating:
            assert schema["required"].count("mutationPhase") == 1
            assert "mutationReceipt" in schema["properties"]
        else:
            assert "mutationPhase" not in schema["properties"]
    get_todos = next(contract for contract in load_contracts() if contract.name == "get_todos")
    mode = adapted_input_schema(get_todos)["properties"]["mode"]["anyOf"][0]
    assert "raw" not in mode["enum"]


def test_fastmcp_exposes_exact_names_annotations_scopes_and_schemas() -> None:
    server = build_server(ThingsCoreAdapter(MockBackend()))
    tools = _run(server.list_tools(run_middleware=False))
    contracts = load_contracts()
    assert [tool.name for tool in tools] == [contract.name for contract in contracts]
    for tool, contract in zip(tools, contracts, strict=True):
        assert tool.parameters == adapted_input_schema(contract)
        assert tool.output_schema == adapted_output_schema()
        assert tool.annotations.readOnlyHint is (contract.scope == "things.read")
        assert tool.annotations.destructiveHint is contract.annotations["destructiveHint"]
        assert tool.meta["thingsMinimumScope"] == contract.scope
        assert tool.meta["securitySchemes"] == [{"type": "oauth2", "scopes": [contract.scope]}]


def test_dynamic_tool_invocation_uses_mock_backend_without_live_things() -> None:
    backend = MockBackend({"title": "Synthetic task", "count": 1})
    server = build_server(ThingsCoreAdapter(backend))

    async def call() -> Any:
        async with Client(server) as client:
            return await client.call_tool("get_todos", {"limit": 1}, raise_on_error=True)

    result = _run(call())
    assert result.data.tool == "get_todos"
    assert result.data.status == "read"
    assert {entry["path"]: entry["value"] for entry in result.structured_content["payload"]["entries"]}[
        "$/title"
    ] == "Synthetic task"
    assert backend.calls[0][0] == "get_todos"
    assert backend.calls[0][1]["limit"] == 1


def test_two_phase_write_is_bound_and_verified(tmp_path: Path) -> None:
    backend = MockBackend()
    adapter = ThingsCoreAdapter(backend, coordinator=_coordinator(tmp_path))
    preview = _run(
        adapter.call("update_todo", {"id": "todo-1", "title": "New", "mutationPhase": "preview"}, _context())
    )
    assert preview.status == "previewed"
    assert preview.mutation_receipt
    execute = _run(
        adapter.call(
            "update_todo",
            {"id": "todo-1", "title": "New", "mutationPhase": "execute", "mutationReceipt": preview.mutation_receipt},
            _context(),
        )
    )
    assert execute.status == "changed"
    assert execute.changed_count == 1
    assert execute.readback_verified is True
    assert backend.calls == [("update_todo", {"id": "todo-1", "title": "New"})]
    with pytest.raises(ToolError, match="things_mutation_receipt_invalid"):
        _run(
            adapter.call(
                "update_todo",
                {
                    "id": "todo-1",
                    "title": "New",
                    "mutationPhase": "execute",
                    "mutationReceipt": preview.mutation_receipt,
                },
                _context(),
            )
        )


def test_receipt_rejects_identity_resource_and_argument_substitution(tmp_path: Path) -> None:
    adapter = ThingsCoreAdapter(MockBackend(), coordinator=_coordinator(tmp_path))
    preview = _run(adapter.call("delete_todo", {"todo_id": "todo-1", "mutationPhase": "preview"}, _context()))
    assert preview.mutation_receipt
    with pytest.raises(ToolError, match="things_resource_mismatch"):
        _run(
            adapter.call(
                "delete_todo",
                {"todo_id": "todo-1", "mutationPhase": "execute", "mutationReceipt": preview.mutation_receipt},
                _context(resource="https://invalid.example/mcp/things"),
            )
        )
    with pytest.raises(ToolError, match="things_mutation_receipt_invalid"):
        _run(
            adapter.call(
                "delete_todo",
                {"todo_id": "todo-2", "mutationPhase": "execute", "mutationReceipt": preview.mutation_receipt},
                _context(),
            )
        )


def test_stale_state_fails_before_backend_write(tmp_path: Path) -> None:
    backend = MockBackend()
    adapter = ThingsCoreAdapter(backend, coordinator=_coordinator(tmp_path))
    preview = _run(
        adapter.call("update_area", {"id": "area-1", "title": "Name", "mutationPhase": "preview"}, _context())
    )
    backend.state = 7
    with pytest.raises(ToolError, match="things_mutation_stale_state"):
        _run(
            adapter.call(
                "update_area",
                {
                    "id": "area-1",
                    "title": "Name",
                    "mutationPhase": "execute",
                    "mutationReceipt": preview.mutation_receipt,
                },
                _context(),
            )
        )
    assert backend.calls == []


def test_partial_failure_counts_are_truthful(tmp_path: Path) -> None:
    adapter = ThingsCoreAdapter(PartialBackend(), coordinator=_coordinator(tmp_path))
    args = {"todo_ids": "one,two", "title": "Synthetic", "mutationPhase": "preview"}
    preview = _run(adapter.call("bulk_update_todos", args, _context()))
    execute = _run(
        adapter.call(
            "bulk_update_todos",
            {**args, "mutationPhase": "execute", "mutationReceipt": preview.mutation_receipt},
            _context(),
        )
    )
    assert (execute.status, execute.changed_count, execute.failed_count) == ("changed", 1, 1)


def test_checklist_verification_requires_exact_variant() -> None:
    backend = UpstreamThingsBackend()

    async def after(*_args: Any) -> Any:
        await asyncio.sleep(0)
        return [{"checklist": [{"title": "A"}, {"title": "B"}]}]

    backend.read_state = cast("Any", after)
    result = _run(
        backend.verify(
            "add_checklist_items",
            {"todo_id": "todo-1", "items": ["B"]},
            [{"checklist": [{"title": "A"}]}],
            {"success": True},
        )
    )
    assert result["changed"] == 1

    async def wrong(*_args: Any) -> Any:
        await asyncio.sleep(0)
        return [{"checklist": [{"title": "B"}, {"title": "A"}]}]

    backend.read_state = cast("Any", wrong)
    mismatch = _run(
        backend.verify(
            "add_checklist_items",
            {"todo_id": "todo-1", "items": ["B"]},
            [{"checklist": [{"title": "A"}]}],
            {"success": True},
        )
    )
    assert mismatch["ambiguous"] == 1
    assert mismatch["changed"] == mismatch["skipped"] == mismatch["failed"] == 0
    assert mismatch["readbackVerified"] is False


@pytest.mark.parametrize(
    ("tool", "reader", "envelope", "target_id"),
    [
        ("update_project", "get_projects", "projects", "project-1"),
        ("update_area", "get_areas", "areas", "area-1"),
    ],
)
def test_read_state_dispatches_typed_collection_before_todo_lookup(
    tool: str,
    reader: str,
    envelope: str,
    target_id: str,
) -> None:
    backend = UpstreamThingsBackend()
    calls: list[tuple[str, dict[str, Any]]] = []

    async def call(name: str, arguments: dict[str, Any]) -> Any:
        await asyncio.sleep(0)
        calls.append((name, arguments))
        return {
            envelope: [
                {"id": target_id, "title": "Before"},
                {"id": "unrelated", "title": "Do not return"},
            ]
        }

    backend.call = cast("Any", call)
    snapshot = _run(backend.read_state(tool, {"id": target_id}))
    assert calls == [(reader, {"include_items": False, "mode": "minimal"})]
    assert snapshot == [{"id": target_id, "title": "Before"}]


@pytest.mark.parametrize(
    ("tool", "reader", "envelope", "target_id"),
    [
        ("update_project", "get_projects", "projects", "project-1"),
        ("update_area", "get_areas", "areas", "area-1"),
    ],
)
def test_typed_collection_readback_verifies_exact_postcondition(
    tool: str,
    reader: str,
    envelope: str,
    target_id: str,
) -> None:
    backend = UpstreamThingsBackend()
    calls: list[tuple[str, dict[str, Any]]] = []

    async def call(name: str, arguments: dict[str, Any]) -> Any:
        await asyncio.sleep(0)
        calls.append((name, arguments))
        return {envelope: [{"id": target_id, "title": "After"}]}

    backend.call = cast("Any", call)
    result = _run(
        backend.verify(
            tool,
            {"id": target_id, "title": "After"},
            [{"id": target_id, "title": "Before"}],
            {"success": True},
        )
    )
    assert calls == [(reader, {"include_items": False, "mode": "minimal"})]
    assert (result["changed"], result["skipped"], result["failed"], result["ambiguous"]) == (1, 0, 0, 0)
    assert result["readbackVerified"] is True


def test_read_state_keeps_todo_updates_on_the_exact_id_reader() -> None:
    backend = UpstreamThingsBackend()
    calls: list[tuple[str, dict[str, Any]]] = []

    async def call(name: str, arguments: dict[str, Any]) -> Any:
        await asyncio.sleep(0)
        calls.append((name, arguments))
        return {"id": "todo-1", "title": "Before"}

    backend.call = cast("Any", call)
    snapshot = _run(backend.read_state("update_todo", {"id": "todo-1"}))
    assert calls == [("get_todo_by_id", {"todo_id": "todo-1"})]
    assert snapshot == [{"id": "todo-1", "title": "Before"}]


def test_redaction_bounds_reads_and_sanitizes_diagnostics() -> None:
    payload, truncated = _bounded_payload({
        "title": "Synthetic private title",
        "token": "secret-value",
        "link": "things:///show?id=private",
        "trace": "/Users/synthetic/project/file.py",
        "items": list(range(30)),
    })
    entries = {entry.path: entry.value for entry in payload.entries}
    assert payload.source_kind == "object"
    assert entries["$/title"] == "Synthetic private title"
    assert entries["$/token"] == "<redacted:secret>"
    assert entries["$/link"] == "<redacted:things-url>"
    assert entries["$/trace"] == "<redacted:local-path>"
    assert len([path for path in entries if path.startswith("$/items/")]) == 25
    assert truncated is True
    diagnostic = _diagnostic_payload({
        "status": "healthy",
        "tool_count": 41,
        "environment": "SECRET=x",
        "title": "private",
        "path": "/tmp/x",
    })
    assert diagnostic == {"status": "healthy", "tool_count": 41}


def test_invalid_raw_arbitrary_and_overbound_requests_are_rejected() -> None:
    get_todos = next(contract for contract in load_contracts() if contract.name == "get_todos")
    with pytest.raises(CoreContractError):
        validate_arguments(get_todos, {"mode": "raw"})
    with pytest.raises(CoreContractError):
        validate_arguments(get_todos, {"command": "osascript"})
    bulk = next(contract for contract in load_contracts() if contract.name == "bulk_update_todos")
    with pytest.raises(CoreContractError):
        validate_arguments(
            bulk, {"todo_ids": ",".join(f"id-{index}" for index in range(26)), "mutationPhase": "preview"}
        )
    with pytest.raises(CoreContractError):
        validate_arguments(bulk, {"todo_ids": "same,same", "mutationPhase": "preview"})
    add_project = next(contract for contract in load_contracts() if contract.name == "add_project")
    with pytest.raises(CoreContractError, match="at most 25"):
        validate_arguments(
            add_project,
            {
                "title": "Synthetic project",
                "todos": "\n".join(f"Task {index}" for index in range(26)),
                "mutationPhase": "preview",
            },
        )
    validate_arguments(
        add_project,
        {
            "title": "Synthetic project",
            "todos": "\n".join(["Repeated task"] * 25),
            "mutationPhase": "preview",
        },
    )


@pytest.mark.parametrize(
    "identifier",
    [
        "things:///show?id=1",
        "file:/tmp/item",
        "https://example.test/item",
        "mailto:item@example.test",
        "custom+scheme:value",
        "/tmp/item",
        "../item",
        r"..\item",
        "./item",
        "~/item",
        ".",
        "..",
    ],
)
def test_core_opaque_identifiers_reject_uri_and_path_shapes(identifier: str) -> None:
    update_area = next(contract for contract in load_contracts() if contract.name == "update_area")
    with pytest.raises(CoreContractError, match="opaque identifier"):
        validate_arguments(
            update_area,
            {"id": identifier, "title": "Synthetic", "mutationPhase": "preview"},
        )
    bulk_update = next(contract for contract in load_contracts() if contract.name == "bulk_update_todos")
    with pytest.raises(CoreContractError, match="opaque identifier"):
        validate_arguments(
            bulk_update,
            {"todo_ids": identifier, "title": "Synthetic", "mutationPhase": "preview"},
        )


def test_core_opaque_identifiers_allow_dotted_tokens_without_restricting_text() -> None:
    update_area = next(contract for contract in load_contracts() if contract.name == "update_area")
    validated = validate_arguments(
        update_area,
        {
            "id": "THG-7f8d_opaque.42",
            "title": "https://example.test/title-is-text",
            "mutationPhase": "preview",
        },
    )
    assert validated["id"] == "THG-7f8d_opaque.42"
    assert validated["title"] == "https://example.test/title-is-text"


def test_public_descriptions_are_sanitized_and_do_not_advertise_escape_hatches() -> None:
    forbidden = (
        "raw mode",
        ".things-auth",
        "auth file",
        "auth token",
        "auth-file search",
        "caller-supplied path",
        "url scheme",
        "url-scheme",
    )
    for contract in load_contracts():
        description = public_description(contract)
        assert description
        assert not any(term in description.casefold() for term in forbidden)
        serialized_schema = json.dumps(adapted_input_schema(contract), sort_keys=True).casefold()
        assert not any(term in serialized_schema for term in forbidden)


def test_per_target_field_readback_never_infers_bulk_success_from_digest_change() -> None:
    backend = UpstreamThingsBackend()
    before = [
        {"item": {"id": "one", "title": "Old", "notes": "Before"}},
        {"item": {"id": "two", "title": "Old", "notes": "Before"}},
    ]

    async def partial_after(*_args: Any) -> Any:
        await asyncio.sleep(0)
        return [
            {"item": {"id": "one", "title": "New", "notes": "After"}},
            {"item": {"id": "two", "title": "Old", "notes": "Unrelated digest change"}},
        ]

    backend.read_state = cast("Any", partial_after)
    result = _run(
        backend.verify(
            "bulk_update_todos",
            {"todo_ids": "one,two", "title": "New"},
            before,
            {"success": True},
        )
    )
    assert (result["changed"], result["skipped"], result["failed"], result["ambiguous"]) == (1, 0, 0, 1)
    assert result["readbackVerified"] is False
    assert sum(result[key] for key in ("changed", "skipped", "failed", "ambiguous")) == 2


def test_per_field_readback_requires_every_requested_field() -> None:
    backend = UpstreamThingsBackend()

    async def incomplete_after(*_args: Any) -> Any:
        await asyncio.sleep(0)
        return [{"item": {"id": "one", "title": "New"}}]

    backend.read_state = cast("Any", incomplete_after)
    result = _run(
        backend.verify(
            "update_todo",
            {"id": "one", "title": "New", "notes": "Required evidence"},
            [{"item": {"id": "one", "title": "Old", "notes": "Before"}}],
            {"success": True},
        )
    )
    assert result["ambiguous"] == 1
    assert result["changed"] == result["skipped"] == result["failed"] == 0


def test_partial_failure_is_attributed_only_to_the_explicit_target() -> None:
    backend = UpstreamThingsBackend()

    async def after(*_args: Any) -> Any:
        await asyncio.sleep(0)
        return [
            {"item": {"id": "one", "title": "New"}},
            {"item": {"id": "two", "title": "Old"}},
        ]

    backend.read_state = cast("Any", after)
    result = _run(
        backend.verify(
            "bulk_update_todos",
            {"todo_ids": "one,two", "title": "New"},
            [
                {"item": {"id": "one", "title": "Old"}},
                {"item": {"id": "two", "title": "Old"}},
            ],
            {"results": [{"id": "two", "success": False}]},
        )
    )
    assert (result["changed"], result["skipped"], result["failed"], result["ambiguous"]) == (1, 0, 1, 0)
    assert result["readbackVerified"] is True


def test_reserved_identity_is_required_and_caller_resource_is_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("THINGS_MCP_ALLOW_LOCAL_IDENTITY_FALLBACK", raising=False)
    with pytest.raises(ToolError, match="things_identity_missing"):
        _identity(None)
    assert _identity(_context()) == (
        "synthetic-principal",
        "synthetic-client",
        "http://127.0.0.1:46683/mcp/things",
    )
    monkeypatch.setenv("THINGS_MCP_ALLOW_LOCAL_IDENTITY_FALLBACK", "1")
    assert _identity(None)[2] == "http://127.0.0.1:46683/mcp/things"


def test_auth_file_accepts_only_safe_home_file(tmp_path: Path) -> None:
    auth = tmp_path / ".things-auth"
    auth.write_text("THINGS_AUTH_TOKEN=synthetic-token\n")
    auth.chmod(0o600)
    token, trace = read_safe_auth_token(tmp_path)
    assert token == "synthetic-token"
    assert trace == [{"path": "~/.things-auth", "status": "matched"}]
    auth.chmod(0o644)
    with pytest.raises(SecurityViolation):
        read_safe_auth_token(tmp_path)
    auth.unlink()
    target = tmp_path / "target"
    target.write_text("synthetic-token")
    target.chmod(0o600)
    auth.symlink_to(target)
    with pytest.raises(SecurityViolation):
        read_safe_auth_token(tmp_path)


def test_live_contract_verifier_checks_every_name_and_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    import things_core.backend as backend_module

    tools = [
        SimpleNamespace(
            name=contract.name,
            inputSchema=contract.upstream_input_schema,
            outputSchema=contract.upstream_output_schema,
        )
        for contract in load_contracts()
    ]

    class FakeClient:
        def __init__(self, _server: Any) -> None:
            pass

        async def __aenter__(self) -> FakeClient:
            return self

        async def __aexit__(self, *_exc: Any) -> None:
            pass

        async def list_tools(self) -> list[Any]:
            return tools

    monkeypatch.setattr(backend_module, "Client", FakeClient)
    _run(verify_live_tool_contract(object()))
    tools[0] = SimpleNamespace(name="substituted", inputSchema={}, outputSchema={})
    with pytest.raises(UpstreamContractError, match="tool_names_mismatch"):
        _run(verify_live_tool_contract(object()))


def test_distribution_artifacts_and_tunnel_disabled_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import things_core.provenance as provenance

    wheel = tmp_path / "mcp_server_things-1.9.0-py3-none-any.whl"
    sdist = tmp_path / "mcp_server_things-1.9.0.tar.gz"
    wheel.write_bytes(b"synthetic-wheel")
    sdist.write_bytes(b"synthetic-sdist")
    monkeypatch.setattr(provenance, "EXPECTED_WHEEL_SHA256", hashlib.sha256(wheel.read_bytes()).hexdigest())
    monkeypatch.setattr(provenance, "EXPECTED_SDIST_SHA256", hashlib.sha256(sdist.read_bytes()).hexdigest())
    assert verify_distribution_artifacts(wheel, sdist) == (True, True)
    monkeypatch.delenv("THINGS_CORE_WHEEL_PATH", raising=False)
    monkeypatch.delenv("THINGS_CORE_SDIST_PATH", raising=False)
    monkeypatch.setenv("THINGS_CORE_ALLOW_UNVERIFIED_ARTIFACT_CACHE", "1")
    monkeypatch.setenv("MCPHUB_TUNNEL_ENABLED", "false")
    assert verify_distribution_artifacts(allow_tunnel_disabled_development=True) == (False, False)
    monkeypatch.setenv("MCPHUB_TUNNEL_ENABLED", "true")
    with pytest.raises(ProvenanceError, match="artifacts_missing"):
        verify_distribution_artifacts(allow_tunnel_disabled_development=True)


def test_installed_record_verification_uses_every_hashed_entry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import things_core.provenance as provenance

    package = tmp_path / "things_mcp"
    dist_info = tmp_path / "mcp_server_things-1.9.0.dist-info"
    package.mkdir()
    dist_info.mkdir()
    module = package / "__init__.py"
    module.write_bytes(b"__version__ = '1.9.0'\n")
    digest = base64.urlsafe_b64encode(hashlib.sha256(module.read_bytes()).digest()).decode().rstrip("=")
    record = dist_info / "RECORD"
    record.write_text(
        f"things_mcp/__init__.py,sha256={digest},{module.stat().st_size}\nmcp_server_things-1.9.0.dist-info/RECORD,,\n"
    )
    record.chmod(0o644)

    class FakeDistribution:
        version = "1.9.0"

        @staticmethod
        def locate_file(_relative: str) -> Path:
            return tmp_path

    monkeypatch.setattr(provenance, "_distribution", lambda: FakeDistribution())
    monkeypatch.setattr(provenance, "verify_distribution_artifacts", lambda *_args, **_kwargs: (True, True))
    monkeypatch.setattr(provenance, "EXPECTED_RECORD_SHA256", hashlib.sha256(record.read_bytes()).hexdigest())
    monkeypatch.setattr(provenance, "EXPECTED_RECORD_ENTRIES", 1)
    evidence = verify_installed_distribution()
    assert evidence.record_entries_verified == 1
    module.write_bytes(b"tampered")
    with pytest.raises(ProvenanceError, match="record_mismatch"):
        verify_installed_distribution()


def test_wrapper_is_strict_managed_arm64_and_redacted() -> None:
    path = REPO_ROOT / "scripts/mcphub/things-core-stdio.sh"
    source = path.read_text()
    assert source.startswith("#!/usr/bin/env bash\nset -euo pipefail\n")
    assert os.access(path, os.X_OK)
    assert '--project "${MCPHUB_REPO_ROOT}"' in source
    assert "--package mcp-things-core" in source
    assert "--offline" in source
    assert "--frozen" in source
    assert "--no-sync" in source
    assert "--no-env-file" in source
    assert "--managed-python" in source
    assert "--no-python-downloads" in source
    assert "--python 3.12" in source
    assert '"$(uname -m)" != "arm64"' in source
    assert "MCPHUB_TUNNEL_ENABLED=false" in source
    assert "THINGS_CORE_ALLOW_UNVERIFIED_ARTIFACT_CACHE" in source
    assert "python -m things_core.server" in source
    assert "exec /usr/bin/env -i" in (REPO_ROOT / "scripts/mcphub/common.sh").read_text()
    mode = stat.S_IMODE(path.stat().st_mode)
    assert mode == 0o755


def test_wrapper_has_no_mutable_or_launch_time_resolution_shape() -> None:
    source = (REPO_ROOT / "scripts/mcphub/things-core-stdio.sh").read_text()
    project = (REPO_ROOT / "mcp/things-core/pyproject.toml").read_text()
    for forbidden in (
        "--isolated",
        "--no-project",
        "--with ",
        "fastmcp>=",
        "mcp-server-things==",
        "pydantic>=",
        "uvx ",
        "npx ",
        "pip ",
        "PYTHONPATH",
    ):
        assert forbidden not in source
    assert source.count("--package mcp-things-core") == 1
    assert source.count("--offline") == 1
    assert source.count("--frozen") == 1
    assert source.count("--no-sync") == 1
    assert '"fastmcp>=3.4.7,<4"' in project
