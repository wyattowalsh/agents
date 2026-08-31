"""Hermetic contract tests for the Things Shortcuts MCP server."""

from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest
from fastmcp import Client
from pydantic import ValidationError

from things_common import MutationCoordinator, SecureRuntimePaths
from things_shortcuts import bridge, mutations
from things_shortcuts.app import mcp
from things_shortcuts.models import (
    AGENT_BRIDGE_NAME,
    DESTRUCTIVE_BRIDGE_NAME,
    DESTRUCTIVE_OPERATIONS,
    BridgeIdentity,
    BridgeOperation,
    BridgeOperationResult,
    ClosedModel,
    CreateStructuredProjectRequest,
    CreateTodoRequest,
    CreateTodosRequest,
    DeleteItemsRequest,
    DuplicateItemsRequest,
    EditItemsRequest,
    GetItemsRequest,
    GetSelectedItemsRequest,
    ItemReceipt,
    MutationRequest,
    OperationResult,
    QuickEntryRequest,
)

EXPECTED_TOOLS = {
    "shortcuts_health",
    "create_todo",
    "create_todos",
    "create_todo_with_quick_entry",
    "create_heading",
    "create_project",
    "create_structured_project",
    "find_items",
    "get_items",
    "get_selected_items",
    "edit_items",
    "edit_heading",
    "edit_checklist",
    "append_checklist",
    "prepend_checklist",
    "duplicate_items",
    "delete_items",
    "delete_items_immediately",
    "delete_heading",
    "open_list",
    "show_items",
}

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MANUAL_BRIDGE_ROOT = REPOSITORY_ROOT / "shortcuts" / "things-plus-plus"
CAPABILITY_MANIFEST = (
    REPOSITORY_ROOT / "openspec" / "changes" / "replace-supathings-with-things-plus-plus" / "capability-manifest.json"
)


@pytest.mark.anyio
async def test_exact_toolset_annotations_and_scope_metadata() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()
    assert {tool.name for tool in tools} == EXPECTED_TOOLS
    by_name = {tool.name: tool for tool in tools}
    for tool in tools:
        assert tool.annotations is not None
        assert tool.annotations.openWorldHint is False
        assert tool.meta is not None
        assert tool.meta["thingsMinimumScope"] in {
            "things.read",
            "things.write",
            "things.admin",
        }
        assert tool.meta["securitySchemes"][0]["scopes"] == [tool.meta["thingsMinimumScope"]]
    for name in {"delete_items", "delete_items_immediately", "delete_heading"}:
        assert by_name[name].annotations.destructiveHint is True
        assert by_name[name].meta["thingsMinimumScope"] == "things.admin"
    assert by_name["create_todo_with_quick_entry"].annotations.readOnlyHint is True

    manifest = json.loads(CAPABILITY_MANIFEST.read_text(encoding="utf-8"))
    expected = {row["serverToolName"]: row for row in manifest["tools"] if row["server"] == "things-shortcuts"}
    assert set(expected) == EXPECTED_TOOLS
    for name, tool in by_name.items():
        row = expected[name]
        assert tool.meta["thingsMinimumScope"] == row["minimumIndependentScope"]
        assert tool.meta["thingsRisk"] == row["risk"]
        assert tool.meta["thingsSchemaContractId"] == row["schemaContractId"]
        assert tool.annotations.readOnlyHint is row["annotations"]["readOnlyHint"]
        assert tool.annotations.destructiveHint is row["annotations"]["destructiveHint"]
        assert tool.annotations.idempotentHint is row["annotations"]["idempotentHint"]
        assert tool.annotations.openWorldHint is row["annotations"]["openWorldHint"]


def test_fixed_bridge_routing_and_no_caller_selected_name() -> None:
    assert bridge.bridge_for_operation(BridgeOperation.CREATE_TODO).value == AGENT_BRIDGE_NAME
    assert bridge.bridge_for_operation(BridgeOperation.DELETE_ITEMS).value == DESTRUCTIVE_BRIDGE_NAME
    assert bridge.bridge_for_operation(BridgeOperation.DELETE_ITEMS_IMMEDIATELY).value == DESTRUCTIVE_BRIDGE_NAME
    assert bridge.bridge_for_operation(BridgeOperation.DELETE_HEADING).value == DESTRUCTIVE_BRIDGE_NAME
    schema = CreateTodoRequest.model_json_schema(by_alias=True)

    def property_names(value: object) -> set[str]:
        names: set[str] = set()
        if isinstance(value, dict):
            properties = value.get("properties")
            if isinstance(properties, dict):
                for name in properties:
                    if isinstance(name, str):
                        names.add(name)
            for item in value.values():
                names.update(property_names(item))
        elif isinstance(value, list):
            for item in value:
                names.update(property_names(item))
        return names

    forbidden = {"shortcut", "path", "url", "applescript", "shell", "json"}
    assert not ({name.casefold() for name in property_names(schema)} & forbidden)


def test_python_field_names_preserve_shortcut_public_json_aliases() -> None:
    request_properties = CreateTodoRequest.model_json_schema(by_alias=True)["properties"]
    assert set(request_properties) == {"mutationPhase", "mutationReceipt", "todo"}
    assert "mutation_phase" not in request_properties
    assert "mutation_receipt" not in request_properties

    public_result_properties = OperationResult.model_json_schema(by_alias=True)["properties"]
    for alias in {
        "mutationReceipt",
        "affectedCount",
        "cascadeCount",
        "changedCount",
        "readbackVerified",
        "uiHandoff",
        "messageCode",
    }:
        assert alias in public_result_properties
    assert "mutation_receipt" not in public_result_properties

    internal = BridgeOperationResult(
        operation=BridgeOperation.DELETE_HEADING,
        status="previewed",
        affected_count=1,
        cascade_count=0,
        items=[],
        receipts=[],
        readback_verified=False,
        undoable=False,
        message_code="synthetic_preview",
        target_state=["heading:id-1"],
        cascade_observed=True,
    )
    encoded = internal.model_dump(by_alias=True, mode="json")
    assert encoded["affectedCount"] == 1
    assert encoded["cascadeCount"] == 0
    assert encoded["targetState"] == ["heading:id-1"]
    assert encoded["cascadeObserved"] is True
    assert "affected_count" not in encoded


def test_shortcuts_closed_models_reject_python_coercion() -> None:
    assert ClosedModel.model_config["strict"] is True
    assert DeleteItemsRequest.model_config["strict"] is True
    assert BridgeOperationResult.model_config["strict"] is True

    accepted = DeleteItemsRequest.model_validate({
        "mutationPhase": "preview",
        "itemIds": ["id-1"],
    })
    assert accepted.item_ids == ["id-1"]
    with pytest.raises(ValidationError):
        DeleteItemsRequest.model_validate({
            "mutationPhase": b"preview",
            "itemIds": ["id-1"],
        })
    with pytest.raises(ValidationError):
        GetSelectedItemsRequest.model_validate({"limit": "25"})
    with pytest.raises(ValidationError):
        BridgeOperationResult.model_validate({
            "operation": "find_items",
            "status": "shown",
            "affectedCount": "0",
            "messageCode": "synthetic_read",
        })


@pytest.mark.parametrize(
    ("request_type", "extra_fields"),
    [
        (EditItemsRequest, {"patch": {"title": "Updated"}}),
        (DuplicateItemsRequest, {}),
        (DeleteItemsRequest, {}),
    ],
)
def test_every_plural_mutation_rejects_duplicate_ids_and_declares_uniqueness(
    request_type: type[MutationRequest],
    extra_fields: dict[str, object],
) -> None:
    plural_mutation_models = {model for model in MutationRequest.__subclasses__() if "item_ids" in model.model_fields}
    assert plural_mutation_models == {
        EditItemsRequest,
        DuplicateItemsRequest,
        DeleteItemsRequest,
    }

    duplicate_payload: dict[str, object] = {
        "mutationPhase": "preview",
        "itemIds": ["id-1", "id-1"],
        **extra_fields,
    }
    with pytest.raises(ValidationError, match="unique identifiers"):
        request_type.model_validate(duplicate_payload)

    valid_payload = {
        **duplicate_payload,
        "itemIds": ["id-1", "id-2"],
    }
    validated = request_type.model_validate(valid_payload)
    assert validated.model_dump(by_alias=True, mode="json")["itemIds"] == ["id-1", "id-2"]
    schema = request_type.model_json_schema(by_alias=True)
    assert schema["properties"]["itemIds"]["uniqueItems"] is True


@pytest.mark.parametrize(
    "resource",
    [
        "http://127.0.0.1:46683/mcp/things",
        "https://mcp.w4w.dev/mcp/things",
    ],
)
def test_shortcuts_identity_accepts_only_exact_canonical_resources(
    resource: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mutations,
        "_metadata",
        lambda _ctx: {
            "w4w.dev/thingsPrincipal": "principal-1",
            "w4w.dev/thingsClientId": "client-1",
            "w4w.dev/thingsResource": resource,
        },
    )
    assert mutations._identity(None) == ("principal-1", "client-1", resource)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("phase", "receipt"),
    [
        ("preview", None),
        ("execute", "r" * 43),
    ],
)
async def test_wrong_resource_is_rejected_before_shortcuts_preview_or_execute_receipt_use(
    phase: str,
    receipt: str | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mutations,
        "_metadata",
        lambda _ctx: {
            "w4w.dev/thingsPrincipal": "principal-1",
            "w4w.dev/thingsClientId": "client-1",
            "w4w.dev/thingsResource": "https://mcp.w4w.dev/mcp/alternate",
        },
    )

    def forbidden_coordinator() -> None:
        raise AssertionError("wrong resource reached the receipt coordinator")

    def forbidden_bridge(
        _operation: BridgeOperation,
        _payload: dict[str, object],
    ) -> BridgeOperationResult:
        raise AssertionError("wrong resource reached the user-owned Shortcut")

    monkeypatch.setattr(mutations, "_get_coordinator", forbidden_coordinator)
    monkeypatch.setattr(mutations, "_safe_bridge_call", forbidden_bridge)
    payload: dict[str, object] = {
        "mutationPhase": phase,
        "itemIds": ["id-1"],
    }
    if receipt is not None:
        payload["mutationReceipt"] = receipt
    request = DeleteItemsRequest.model_validate(payload)
    with pytest.raises(Exception, match="things_resource_mismatch"):
        await mutations.call_mutating(
            BridgeOperation.DELETE_ITEMS,
            request,
            ctx=None,
            minimum_scope="things.admin",
            target_ids=("id-1",),
        )


def test_manual_bridge_contract_matches_runtime_schemas_and_vectors() -> None:
    manifest = json.loads((MANUAL_BRIDGE_ROOT / "manifest.json").read_text(encoding="utf-8"))
    request_schema = json.loads((MANUAL_BRIDGE_ROOT / "schemas" / "request.schema.json").read_text(encoding="utf-8"))
    response_schema = json.loads((MANUAL_BRIDGE_ROOT / "schemas" / "response.schema.json").read_text(encoding="utf-8"))

    assert request_schema == bridge.REQUEST_SCHEMA
    assert response_schema == bridge.RESPONSE_SCHEMA
    assert manifest == {
        "protocolVersion": "1",
        "bridges": {
            "agent": AGENT_BRIDGE_NAME,
            "destructive": DESTRUCTIVE_BRIDGE_NAME,
        },
        "requestSchemaSha256": bridge.REQUEST_SCHEMA_SHA256,
        "responseSchemaSha256": bridge.RESPONSE_SCHEMA_SHA256,
        "agentOperations": manifest["agentOperations"],
        "destructiveOperations": manifest["destructiveOperations"],
    }
    assert set(manifest["agentOperations"]) == {
        operation.value for operation in BridgeOperation if operation not in DESTRUCTIVE_OPERATIONS
    }
    assert set(manifest["destructiveOperations"]) == {
        BridgeOperation.PROTOCOL_HEALTH.value,
        *(operation.value for operation in DESTRUCTIVE_OPERATIONS),
    }

    for stem, identity in (
        ("agent-health", BridgeIdentity.AGENT),
        ("destructive-health", BridgeIdentity.DESTRUCTIVE),
    ):
        request = bridge.BridgeRequest.model_validate_json(
            (MANUAL_BRIDGE_ROOT / "test-vectors" / f"{stem}.request.json").read_bytes()
        )
        response = bridge.BridgeResponse.model_validate_json(
            (MANUAL_BRIDGE_ROOT / "test-vectors" / f"{stem}.response.json").read_bytes()
        )
        assert request.bridge_identity is identity
        assert response.bridge_identity is identity
        assert request.request_id == response.request_id
        assert request.request_schema_sha256 == response.request_schema_sha256 == bridge.REQUEST_SCHEMA_SHA256
        assert request.response_schema_sha256 == response.response_schema_sha256 == bridge.RESPONSE_SCHEMA_SHA256


def test_batch_caps_and_quick_entry_heading_refusal() -> None:
    todo = {"title": "Synthetic"}
    with pytest.raises(ValidationError):
        CreateTodosRequest.model_validate({"mutationPhase": "preview", "todos": [todo] * 26})
    headings = [{"title": f"H{i}", "todos": [todo, todo]} for i in range(13)]
    with pytest.raises(ValidationError):
        CreateStructuredProjectRequest.model_validate({
            "mutationPhase": "preview",
            "project": {"title": "P"},
            "headings": headings,
        })
    boundary = CreateStructuredProjectRequest.model_validate({
        "mutationPhase": "preview",
        "project": {"title": "P"},
        "headings": [{"title": f"H{i}", "todos": []} for i in range(24)],
    })
    assert len(mutations.target_ids_from_request(BridgeOperation.CREATE_STRUCTURED_PROJECT, boundary)) == 25
    with pytest.raises(ValidationError):
        CreateStructuredProjectRequest.model_validate({
            "mutationPhase": "preview",
            "project": {"title": "P"},
            "headings": [{"title": f"H{i}", "todos": []} for i in range(25)],
        })
    with pytest.raises(ValidationError):
        QuickEntryRequest.model_validate({"todo": {"title": "Synthetic", "headingId": "heading-1"}})
    with pytest.raises(ValidationError):
        CreateTodoRequest.model_validate({
            "mutationPhase": "preview",
            "todo": {"title": "Synthetic"},
            "url": "things:///add",
        })


def test_mutation_receipt_phase_is_closed() -> None:
    with pytest.raises(ValidationError):
        DeleteItemsRequest.model_validate({"mutationPhase": "execute", "itemIds": ["id-1"]})


def test_operation_specific_backend_result_invariants_fail_closed() -> None:
    quick_entry = BridgeOperationResult(
        operation=BridgeOperation.CREATE_TODO_WITH_QUICK_ENTRY,
        status="ui_handoff",
        changed_count=0,
        items=[],
        receipts=[],
        readback_verified=False,
        ui_handoff=False,
        message_code="synthetic_handoff",
    )
    with pytest.raises(Exception, match="things_quick_entry_result_invalid"):
        mutations._validate_result_shape(BridgeOperation.CREATE_TODO_WITH_QUICK_ENTRY, {}, quick_entry)

    open_list = BridgeOperationResult(
        operation=BridgeOperation.OPEN_LIST,
        status="shown",
        affected_count=1,
        items=[],
        receipts=[],
        readback_verified=False,
        ui_handoff=True,
        message_code="synthetic_shown",
    )
    with pytest.raises(Exception, match="things_ui_handoff_result_invalid"):
        mutations._validate_result_shape(BridgeOperation.OPEN_LIST, {}, open_list)

    delete_items = BridgeOperationResult(
        operation=BridgeOperation.DELETE_ITEMS,
        status="previewed",
        affected_count=1,
        items=[],
        receipts=[],
        target_state=["todo:id-1:open"],
        readback_verified=False,
        undoable=None,
        message_code="synthetic_preview",
    )
    with pytest.raises(Exception, match="things_shortcuts_undoability_invalid"):
        mutations._validate_result_shape(
            BridgeOperation.DELETE_ITEMS,
            {"mutationPhase": "preview"},
            delete_items,
        )

    missing_cascade = BridgeOperationResult(
        operation=BridgeOperation.DELETE_HEADING,
        status="previewed",
        affected_count=1,
        cascade_observed=True,
        items=[],
        receipts=[],
        target_state=["heading:id-1:open"],
        readback_verified=False,
        undoable=False,
        message_code="synthetic_preview",
    )
    with pytest.raises(Exception, match="things_heading_cascade_missing"):
        mutations._validate_result_shape(
            BridgeOperation.DELETE_HEADING,
            {"mutationPhase": "preview"},
            missing_cascade,
        )

    explicit_zero_cascade = missing_cascade.model_copy(update={"cascade_count": 0})
    explicit_zero_cascade.model_fields_set.add("cascade_count")
    mutations._validate_result_shape(
        BridgeOperation.DELETE_HEADING,
        {"mutationPhase": "preview"},
        explicit_zero_cascade,
    )
    with pytest.raises(ValidationError):
        DeleteItemsRequest.model_validate({
            "mutationPhase": "preview",
            "mutationReceipt": "x" * 43,
            "itemIds": ["id-1"],
        })


@pytest.mark.parametrize(
    ("operation", "payload"),
    [
        (BridgeOperation.FIND_ITEMS, {"query": "Synthetic", "limit": 25}),
        (BridgeOperation.GET_ITEMS, {"itemIds": ["id-1"]}),
        (BridgeOperation.GET_SELECTED_ITEMS, {"limit": 25}),
    ],
)
def test_read_operations_require_explicit_non_mutation_shape(
    operation: BridgeOperation,
    payload: dict[str, object],
) -> None:
    valid = BridgeOperationResult(
        operation=operation,
        status="shown",
        items=[],
        receipts=[],
        readback_verified=False,
        ui_handoff=False,
        message_code="synthetic_read",
    )
    mutations._validate_result_shape(operation, payload, valid)

    mutation_shaped = BridgeOperationResult(
        operation=operation,
        status="shown",
        changed_count=1,
        items=[],
        receipts=[],
        target_state=["todo:id-1:changed"],
        readback_verified=True,
        ui_handoff=False,
        message_code="synthetic_invalid_read",
    )
    with pytest.raises(Exception, match="things_shortcuts_read_result_invalid"):
        mutations._validate_result_shape(operation, payload, mutation_shaped)


@pytest.mark.parametrize(
    "value",
    [
        "things:///show?id=1",
        "file:/tmp/item",
        "/tmp/item",
        "../item",
        r"..\item",
        "./item",
        "~/item",
        ".",
        "..",
    ],
)
def test_identifier_fields_reject_uri_and_path_shapes(value: str) -> None:
    with pytest.raises(ValidationError):
        GetItemsRequest.model_validate({"itemIds": [value]})

    accepted = GetItemsRequest.model_validate({"itemIds": ["THG-7f8d_opaque.42"]})
    assert accepted.item_ids == ["THG-7f8d_opaque.42"]
    ordinary_text = CreateTodoRequest.model_validate({
        "mutationPhase": "preview",
        "todo": {"title": "https://example.test/a/path"},
    })
    assert ordinary_text.todo.title == "https://example.test/a/path"


def test_protocol_digest_handshake_temp_modes_and_cleanup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    executable = tmp_path / "shortcuts"
    executable.write_bytes(b"stub")
    executable.chmod(0o700)
    monkeypatch.setattr(bridge, "SHORTCUTS_EXECUTABLE", executable)
    observed: dict[str, Path] = {}

    def fake_run(argv: tuple[str, ...], _timeout: float, *, capture_stdout: bool = False) -> tuple[int, bytes]:
        assert capture_stdout is False
        assert argv[:3] == (str(executable), "run", AGENT_BRIDGE_NAME)
        assert argv[-2:] == ("--output-type", "public.json")
        request_path = Path(argv[4])
        response_path = Path(argv[6])
        assert stat.S_IMODE(request_path.stat().st_mode) == 0o600
        assert stat.S_IMODE(response_path.stat().st_mode) == 0o600
        request = json.loads(request_path.read_text(encoding="utf-8"))
        observed["request_path"] = request_path
        observed["response_path"] = response_path
        response = {
            "protocolVersion": "1",
            "bridgeIdentity": AGENT_BRIDGE_NAME,
            "requestSchemaSha256": bridge.REQUEST_SCHEMA_SHA256,
            "responseSchemaSha256": bridge.RESPONSE_SCHEMA_SHA256,
            "requestId": request["requestId"],
            "status": "ok",
            "result": {
                "operation": "find_items",
                "status": "shown",
                "affectedCount": 0,
                "cascadeCount": 0,
                "changedCount": 0,
                "skippedCount": 0,
                "failedCount": 0,
                "ambiguousCount": 0,
                "items": [],
                "receipts": [],
                "readbackVerified": False,
                "uiHandoff": False,
                "undoable": None,
                "messageCode": "synthetic_ok",
            },
            "errorCode": None,
            "tccReady": True,
        }
        response_path.write_text(json.dumps(response), encoding="utf-8")
        response_path.chmod(0o600)
        return 0, b""

    monkeypatch.setattr(bridge, "_run_process", fake_run)
    result = bridge.invoke_bridge(BridgeOperation.FIND_ITEMS, {"query": "Synthetic", "limit": 1})
    assert result.bridge_identity is BridgeIdentity.AGENT
    assert not observed["request_path"].exists()
    assert not observed["response_path"].exists()


def test_protocol_mismatch_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    executable = tmp_path / "shortcuts"
    executable.write_bytes(b"stub")
    executable.chmod(0o700)
    monkeypatch.setattr(bridge, "SHORTCUTS_EXECUTABLE", executable)

    def fake_run(argv: tuple[str, ...], _timeout: float, *, capture_stdout: bool = False) -> tuple[int, bytes]:
        request = json.loads(Path(argv[4]).read_text(encoding="utf-8"))
        response = {
            "protocolVersion": "1",
            "bridgeIdentity": AGENT_BRIDGE_NAME,
            "requestSchemaSha256": "0" * 64,
            "responseSchemaSha256": bridge.RESPONSE_SCHEMA_SHA256,
            "requestId": request["requestId"],
            "status": "ok",
            "result": {},
            "errorCode": None,
            "tccReady": True,
        }
        Path(argv[6]).write_text(json.dumps(response), encoding="utf-8")
        Path(argv[6]).chmod(0o600)
        return 0, b""

    monkeypatch.setattr(bridge, "_run_process", fake_run)
    with pytest.raises(bridge.BridgeProtocolError, match="bridge_handshake_mismatch"):
        bridge.invoke_bridge(BridgeOperation.FIND_ITEMS, {"query": "Synthetic"})


def test_process_timeout_kills_child_group() -> None:
    with pytest.raises(bridge.BridgeTimeoutError, match="bridge_timeout"):
        bridge._run_process(("/bin/sleep", "2"), 0.01)


def test_shortcuts_subprocess_environment_is_minimal_and_secret_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MCPHUB_BEARER_TOKEN", "synthetic-secret")
    monkeypatch.setenv("THINGS_PRIVATE_VALUE", "synthetic-private")
    environment = bridge._subprocess_environment()
    assert environment["PATH"] == "/usr/bin:/bin"
    assert set(environment) <= {
        "PATH",
        "HOME",
        "TMPDIR",
        "LANG",
        "LC_ALL",
        "__CF_USER_TEXT_ENCODING",
    }
    assert "MCPHUB_BEARER_TOKEN" not in environment
    assert "THINGS_PRIVATE_VALUE" not in environment


@pytest.mark.anyio
async def test_shared_receipt_preview_execute_and_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir(mode=0o700)
    mutations._coordinator = MutationCoordinator(SecureRuntimePaths.create(runtime_root))
    monkeypatch.setenv("THINGS_MCP_ALLOW_LOCAL_IDENTITY_FALLBACK", "1")
    observed_payloads: list[dict[str, object]] = []

    def fake_bridge(operation: BridgeOperation, payload: dict[str, object]):
        observed_payloads.append(payload)
        assert "mutationReceipt" not in payload
        assert "w4w.dev/thingsPrincipal" not in payload
        assert "w4w.dev/thingsClientId" not in payload
        assert "w4w.dev/thingsResource" not in payload
        phase = payload["mutationPhase"]
        if phase == "preview":
            return BridgeOperationResult(
                operation=operation,
                status="previewed",
                affected_count=1,
                items=[],
                receipts=[],
                target_state=["destination:inbox:stable"],
                readback_verified=False,
                message_code="synthetic_preview",
            )
        return BridgeOperationResult(
            operation=operation,
            status="changed",
            affected_count=1,
            changed_count=1,
            items=[],
            receipts=[],
            target_state=["todo:new-id:open"],
            readback_verified=True,
            message_code="synthetic_changed",
        )

    monkeypatch.setattr(mutations, "_safe_bridge_call", fake_bridge)
    preview_request = CreateTodoRequest.model_validate({"mutationPhase": "preview", "todo": {"title": "Synthetic"}})
    preview = await mutations.call_mutating(
        BridgeOperation.CREATE_TODO,
        preview_request,
        ctx=None,
        minimum_scope="things.write",
        target_ids=mutations.target_ids_from_request(BridgeOperation.CREATE_TODO, preview_request),
    )
    assert preview.status == "previewed"
    assert preview.mutation_receipt
    execute_request = CreateTodoRequest.model_validate({
        "mutationPhase": "execute",
        "mutationReceipt": preview.mutation_receipt,
        "todo": {"title": "Synthetic"},
    })
    execute = await mutations.call_mutating(
        BridgeOperation.CREATE_TODO,
        execute_request,
        ctx=None,
        minimum_scope="things.write",
        target_ids=mutations.target_ids_from_request(BridgeOperation.CREATE_TODO, execute_request),
    )
    assert execute.status == "changed"
    assert len(observed_payloads) == 3
    with pytest.raises(Exception, match="things_mutation_receipt_invalid"):
        await mutations.call_mutating(
            BridgeOperation.CREATE_TODO,
            execute_request,
            ctx=None,
            minimum_scope="things.write",
            target_ids=mutations.target_ids_from_request(BridgeOperation.CREATE_TODO, execute_request),
        )
    mutations._coordinator = None


@pytest.mark.anyio
@pytest.mark.parametrize("batch_size", [2, 25])
async def test_plural_create_receipt_cardinality_is_two_through_twenty_five(
    batch_size: int,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir(mode=0o700)
    monkeypatch.setattr(
        mutations,
        "_coordinator",
        MutationCoordinator(SecureRuntimePaths.create(runtime_root)),
    )
    monkeypatch.setenv("THINGS_MCP_ALLOW_LOCAL_IDENTITY_FALLBACK", "1")
    observed_phases: list[str] = []

    def fake_bridge(operation: BridgeOperation, payload: dict[str, object]) -> BridgeOperationResult:
        phase = payload["mutationPhase"]
        assert isinstance(phase, str)
        observed_phases.append(phase)
        if phase == "preview":
            return BridgeOperationResult(
                operation=operation,
                status="previewed",
                affected_count=batch_size,
                items=[],
                receipts=[],
                target_state=["destination:inbox:stable"],
                readback_verified=False,
                message_code="synthetic_preview",
            )
        receipts = [
            ItemReceipt(
                item_id=f"created-{index}",
                status="changed",
                code="created",
            )
            for index in range(batch_size)
        ]
        return BridgeOperationResult(
            operation=operation,
            status="changed",
            affected_count=batch_size,
            changed_count=batch_size,
            items=[],
            receipts=receipts,
            target_state=[f"todo:created-{index}:open" for index in range(batch_size)],
            readback_verified=True,
            message_code="synthetic_changed",
        )

    monkeypatch.setattr(mutations, "_safe_bridge_call", fake_bridge)
    preview_request = CreateTodosRequest.model_validate({
        "mutationPhase": "preview",
        "todos": [{"title": f"Synthetic {index}"} for index in range(batch_size)],
    })
    target_ids = mutations.target_ids_from_request(BridgeOperation.CREATE_TODOS, preview_request)
    assert len(target_ids) == batch_size
    preview = await mutations.call_mutating(
        BridgeOperation.CREATE_TODOS,
        preview_request,
        ctx=None,
        minimum_scope="things.write",
        target_ids=target_ids,
    )
    execute_request = CreateTodosRequest.model_validate({
        "mutationPhase": "execute",
        "mutationReceipt": preview.mutation_receipt,
        "todos": [{"title": f"Synthetic {index}"} for index in range(batch_size)],
    })
    execute = await mutations.call_mutating(
        BridgeOperation.CREATE_TODOS,
        execute_request,
        ctx=None,
        minimum_scope="things.write",
        target_ids=mutations.target_ids_from_request(BridgeOperation.CREATE_TODOS, execute_request),
    )
    assert execute.status == "changed"
    assert execute.changed_count == batch_size
    assert execute.skipped_count == 0
    assert execute.failed_count == 0
    assert execute.ambiguous_count == 0
    assert len(execute.receipts) == batch_size
    assert observed_phases == ["preview", "preview", "execute"]


@pytest.mark.anyio
async def test_same_count_different_target_state_rejects_shortcut_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir(mode=0o700)
    mutations._coordinator = MutationCoordinator(SecureRuntimePaths.create(runtime_root))
    monkeypatch.setenv("THINGS_MCP_ALLOW_LOCAL_IDENTITY_FALLBACK", "1")
    preview_reads = 0
    mutation_called = False

    def fake_bridge(operation: BridgeOperation, payload: dict[str, object]) -> BridgeOperationResult:
        nonlocal mutation_called, preview_reads
        if payload["mutationPhase"] == "preview":
            preview_reads += 1
            state = "todo:id-1:title-before" if preview_reads == 1 else "todo:id-1:title-after"
            return BridgeOperationResult(
                operation=operation,
                status="previewed",
                affected_count=1,
                items=[],
                receipts=[],
                target_state=[state],
                readback_verified=False,
                message_code="synthetic_preview",
            )
        mutation_called = True
        return BridgeOperationResult(
            operation=operation,
            status="changed",
            affected_count=1,
            changed_count=1,
            items=[],
            receipts=[],
            target_state=["todo:new-id:open"],
            readback_verified=True,
            message_code="synthetic_changed",
        )

    monkeypatch.setattr(mutations, "_safe_bridge_call", fake_bridge)
    preview_request = CreateTodoRequest.model_validate({"mutationPhase": "preview", "todo": {"title": "Synthetic"}})
    preview = await mutations.call_mutating(
        BridgeOperation.CREATE_TODO,
        preview_request,
        ctx=None,
        minimum_scope="things.write",
        target_ids=mutations.target_ids_from_request(BridgeOperation.CREATE_TODO, preview_request),
    )
    execute_request = CreateTodoRequest.model_validate({
        "mutationPhase": "execute",
        "mutationReceipt": preview.mutation_receipt,
        "todo": {"title": "Synthetic"},
    })
    with pytest.raises(Exception, match="things_mutation_stale_state"):
        await mutations.call_mutating(
            BridgeOperation.CREATE_TODO,
            execute_request,
            ctx=None,
            minimum_scope="things.write",
            target_ids=mutations.target_ids_from_request(BridgeOperation.CREATE_TODO, execute_request),
        )
    assert preview_reads == 2
    assert mutation_called is False
    mutations._coordinator = None
