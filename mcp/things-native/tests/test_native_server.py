"""Hermetic contract tests for the fixed Things native MCP server."""

from __future__ import annotations

import hashlib
import json
import plistlib
from pathlib import Path

import pytest
from fastmcp import Client
from pydantic import ValidationError

from things_common import MutationCoordinator, SecureRuntimePaths
from things_native import mutations, runner
from things_native.app import mcp
from things_native.models import (
    ClosedModel,
    DeleteAreaRequest,
    EmptyTrashRequest,
    NativeOperationResult,
    RenameTagRequest,
    SetTagParentRequest,
)

EXPECTED_TOOLS = {
    "native_health",
    "open_search",
    "log_completed",
    "empty_trash",
    "delete_area",
    "rename_tag",
    "delete_tag",
    "set_tag_parent",
}

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
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
    for name in {"log_completed", "empty_trash", "delete_area", "delete_tag"}:
        assert by_name[name].annotations.destructiveHint is True
        assert by_name[name].meta["thingsMinimumScope"] == "things.admin"
    assert by_name["open_search"].annotations.readOnlyHint is True

    manifest = json.loads(CAPABILITY_MANIFEST.read_text(encoding="utf-8"))
    expected = {row["serverToolName"]: row for row in manifest["tools"] if row["server"] == "things-native"}
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


def test_open_search_builds_only_fixed_encoded_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[tuple[str, ...]] = []

    def fake_run(argv: tuple[str, ...], _timeout: float, *, capture_stdout: bool) -> tuple[int, bytes]:
        observed.append(argv)
        assert capture_stdout is False
        return 0, b""

    monkeypatch.setattr(runner, "_run_process", fake_run)
    result = runner.open_search_url("x&url=things:///add?title=Injected")
    assert result.status == "ui_handoff"
    assert observed == [
        (
            "/usr/bin/open",
            "-u",
            "things:///search?query=x%26url%3Dthings%3A%2F%2F%2Fadd%3Ftitle%3DInjected",
        )
    ]
    assert runner.build_search_url(None) == "things:///search"


def test_python_field_names_preserve_native_public_json_aliases() -> None:
    request_properties = DeleteAreaRequest.model_json_schema(by_alias=True)["properties"]
    assert set(request_properties) == {
        "mutationPhase",
        "mutationReceipt",
        "areaId",
    }
    assert "mutation_phase" not in request_properties
    assert "area_id" not in request_properties

    result_properties = NativeOperationResult.model_json_schema(by_alias=True)["properties"]
    for alias in {
        "mutationReceipt",
        "affectedCount",
        "cascadeCount",
        "readbackVerified",
        "uiHandoff",
        "messageCode",
    }:
        assert alias in result_properties
    assert "mutation_receipt" not in result_properties

    internal = runner.NativeBackendResult(
        status="previewed",
        affected_count=1,
        cascade_count=0,
        cascade_observed=True,
        target_state=["area:area-1"],
        readback_verified=False,
        message_code="delete_area_preview",
    )
    encoded = internal.model_dump(by_alias=True, mode="json")
    assert encoded["affectedCount"] == 1
    assert encoded["cascadeCount"] == 0
    assert encoded["cascadeObserved"] is True
    assert encoded["targetState"] == ["area:area-1"]
    assert "affected_count" not in encoded


def test_native_closed_models_reject_python_coercion() -> None:
    assert ClosedModel.model_config["strict"] is True
    assert DeleteAreaRequest.model_config["strict"] is True
    assert runner.NativeBackendResult.model_config["strict"] is True

    accepted = DeleteAreaRequest.model_validate({
        "mutationPhase": "preview",
        "areaId": "area-1",
    })
    assert accepted.area_id == "area-1"
    with pytest.raises(ValidationError):
        DeleteAreaRequest.model_validate({
            "mutationPhase": b"preview",
            "areaId": "area-1",
        })
    with pytest.raises(ValidationError):
        runner.NativeBackendResult.model_validate({
            "status": "previewed",
            "affectedCount": "1",
            "cascadeCount": 0,
            "cascadeObserved": True,
            "targetState": ["area:area-1"],
            "readbackVerified": False,
            "messageCode": "delete_area_preview",
        })
    with pytest.raises(ValidationError):
        NativeOperationResult.model_validate({
            "operation": "delete_area",
            "status": "previewed",
            "readbackVerified": 0,
            "messageCode": "delete_area_preview",
        })


@pytest.mark.parametrize(
    "resource",
    [
        "http://127.0.0.1:46683/mcp/things",
        "https://mcp.w4w.dev/mcp/things",
    ],
)
def test_native_identity_accepts_only_exact_canonical_resources(
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
async def test_wrong_resource_is_rejected_before_native_preview_or_execute_receipt_use(
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
            "w4w.dev/thingsResource": "http://127.0.0.1:46683/mcp/alternate",
        },
    )

    def forbidden_coordinator() -> None:
        raise AssertionError("wrong resource reached the receipt coordinator")

    def forbidden_run(
        _script_name: str,
        _arguments: list[str],
    ) -> runner.NativeBackendResult:
        raise AssertionError("wrong resource reached osascript")

    monkeypatch.setattr(mutations, "_get_coordinator", forbidden_coordinator)
    monkeypatch.setattr(mutations, "_safe_run", forbidden_run)
    payload: dict[str, object] = {
        "mutationPhase": phase,
        "areaId": "area-1",
    }
    if receipt is not None:
        payload["mutationReceipt"] = receipt
    request = DeleteAreaRequest.model_validate(payload)
    with pytest.raises(Exception, match="things_resource_mismatch"):
        await mutations.call_mutating(
            "delete_area",
            "delete_area",
            request,
            ctx=None,
            minimum_scope="things.admin",
            target_ids=("area-1",),
            outcome_count=1,
            script_arguments=["area-1"],
            undoable=False,
        )


def test_fixed_scripts_execute_verified_bytes_and_argv_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, object] = {}
    source = (runner.SCRIPT_DIRECTORY / "rename_tag.applescript").read_bytes()
    executable = tmp_path / "osascript"
    executable.write_bytes(b"stub")
    executable.chmod(0o700)
    monkeypatch.setattr(runner, "OSASCRIPT_EXECUTABLE", executable)

    def fake_run(
        argv: tuple[str, ...],
        _timeout: float,
        *,
        capture_stdout: bool,
        stdin_bytes: bytes | None = None,
    ) -> tuple[int, bytes]:
        observed["argv"] = argv
        observed["stdin"] = stdin_bytes
        assert capture_stdout is True
        return (
            0,
            b'{"status":"changed","affectedCount":1,"cascadeCount":0,'
            b'"cascadeObserved":false,"targetState":["tag:tag-1:new"],'
            b'"readbackVerified":true,"messageCode":"rename_tag_changed"}',
        )

    monkeypatch.setattr(runner, "_run_process", fake_run)
    result = runner.run_script("rename_tag", ["execute", "tag-1", 'Name " ; do shell script "bad"'])
    assert result.status == "changed"
    assert observed["stdin"] == source
    assert observed["argv"] == (
        str(executable),
        "-",
        "execute",
        "tag-1",
        'Name " ; do shell script "bad"',
    )


def test_script_path_inode_swap_cannot_change_executed_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = b'on run argv\nreturn "{}"\nend run\n'
    replacement = b'on run argv\nerror "swapped"\nend run\n'
    script_path = tmp_path / "rename_tag.applescript"
    script_path.write_bytes(original)
    executable = tmp_path / "osascript"
    executable.write_bytes(b"stub")
    executable.chmod(0o700)
    monkeypatch.setattr(runner, "SCRIPT_DIRECTORY", tmp_path)
    monkeypatch.setattr(
        runner,
        "SCRIPT_SHA256",
        {"rename_tag": hashlib.sha256(original).hexdigest()},
    )
    monkeypatch.setattr(runner, "OSASCRIPT_EXECUTABLE", executable)

    def fake_run(
        argv: tuple[str, ...],
        _timeout: float,
        *,
        capture_stdout: bool,
        stdin_bytes: bytes | None = None,
    ) -> tuple[int, bytes]:
        swapped_path = tmp_path / "swapped.applescript"
        swapped_path.write_bytes(replacement)
        swapped_path.replace(script_path)
        assert argv == (str(executable), "-", "execute", "tag-1", "new")
        assert capture_stdout is True
        assert stdin_bytes == original
        return (
            0,
            b'{"status":"changed","affectedCount":1,"cascadeCount":0,'
            b'"cascadeObserved":false,"targetState":["tag:tag-1:new"],'
            b'"readbackVerified":true,"messageCode":"rename_tag_changed"}',
        )

    monkeypatch.setattr(runner, "_run_process", fake_run)
    result = runner.run_script("rename_tag", ["execute", "tag-1", "new"])
    assert result.status == "changed"
    assert script_path.read_bytes() == replacement


def test_unknown_script_and_detach_or_self_parent_are_rejected() -> None:
    with pytest.raises(runner.NativeArtifactError, match="native_script_not_allowlisted"):
        runner.run_script("caller_selected", [])
    with pytest.raises(ValidationError):
        SetTagParentRequest.model_validate({"mutationPhase": "preview", "tagId": "tag-1", "parentTagId": None})
    with pytest.raises(ValidationError):
        SetTagParentRequest.model_validate({"mutationPhase": "preview", "tagId": "tag-1", "parentTagId": "tag-1"})
    with pytest.raises(ValidationError):
        SetTagParentRequest.model_validate({
            "mutationPhase": "preview",
            "tagId": "tag-1",
            "parentTagId": "tag-2",
            "detach": True,
        })


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
def test_native_identifier_fields_reject_uri_and_path_shapes(value: str) -> None:
    with pytest.raises(ValidationError):
        DeleteAreaRequest.model_validate({"mutationPhase": "preview", "areaId": value})

    accepted = DeleteAreaRequest.model_validate({"mutationPhase": "preview", "areaId": "THG-7f8d_opaque.42"})
    assert accepted.area_id == "THG-7f8d_opaque.42"
    ordinary_text = RenameTagRequest.model_validate({
        "mutationPhase": "preview",
        "tagId": "tag-1",
        "newName": "https://example.test/a/path",
    })
    assert ordinary_text.new_name == "https://example.test/a/path"


def test_native_subprocess_environment_is_minimal_and_secret_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MCPHUB_BEARER_TOKEN", "synthetic-secret")
    monkeypatch.setenv("THINGS_PRIVATE_VALUE", "synthetic-private")
    environment = runner._subprocess_environment()
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


def test_script_bundle_hashes_match_and_forbid_hidden_surfaces() -> None:
    assert set(runner.SCRIPT_SHA256) == {
        "delete_area",
        "delete_tag",
        "empty_trash",
        "log_completed",
        "rename_tag",
        "set_tag_parent",
    }
    for script_name, expected in runner.SCRIPT_SHA256.items():
        path = runner.SCRIPT_DIRECTORY / f"{script_name}.applescript"
        payload = path.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == expected
        lowered = payload.decode("utf-8").casefold()
        assert "do shell script" not in lowered
        assert "run script" not in lowered
        assert "_private_experimental_" not in lowered
        assert "reorder" not in lowered
        assert "recurr" not in lowered
        assert "on run argv" in lowered


def test_static_health_never_executes_or_sends_apple_event(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app = tmp_path / "Things3.app"
    resources = app / "Contents" / "Resources"
    resources.mkdir(parents=True)
    (app / "Contents" / "Info.plist").write_bytes(plistlib.dumps({"CFBundleShortVersionString": "9.9-test"}))
    (resources / "Things.sdef").write_text("synthetic", encoding="utf-8")
    monkeypatch.setattr(runner, "THINGS_APP_PATHS", (app,))
    monkeypatch.setattr(runner, "verify_script_bundle", lambda: True)

    def forbidden_process(*_args: object, **_kwargs: object):
        raise AssertionError("health must not start a process")

    monkeypatch.setattr(runner, "_run_process", forbidden_process)
    result = runner.static_health()
    assert result.status == "ready_static"
    assert result.app_version == "9.9-test"
    assert result.tcc_status == "unproven"
    assert result.invokes_apple_event is False


def test_delete_area_requires_receipt_for_execute_and_rejects_raw_fields() -> None:
    with pytest.raises(ValidationError):
        DeleteAreaRequest.model_validate({"mutationPhase": "execute", "areaId": "area-1"})


def test_native_cascade_and_log_completed_evidence_fail_closed() -> None:
    with pytest.raises(ValidationError):
        runner.NativeBackendResult.model_validate({
            "status": "previewed",
            "affectedCount": 1,
            "cascadeCount": 0,
            "targetState": ["area:area-1"],
            "readbackVerified": False,
            "messageCode": "delete_area_preview",
        })

    explicit_zero = runner.NativeBackendResult(
        status="previewed",
        affected_count=1,
        cascade_count=0,
        cascade_observed=True,
        target_state=["area:area-1"],
        readback_verified=False,
        message_code="delete_area_preview",
    )
    mutations._validate_backend_result("delete_area", mutations.MutationPhase.PREVIEW, explicit_zero)

    false_verified_log = runner.NativeBackendResult(
        status="changed",
        affected_count=1,
        cascade_count=0,
        cascade_observed=False,
        target_state=["completed-todo:id-1"],
        readback_verified=True,
        message_code="log_completed_changed",
    )
    with pytest.raises(Exception, match="things_native_log_completed_verification_invalid"):
        mutations._validate_backend_result("log_completed", mutations.MutationPhase.EXECUTE, false_verified_log)

    log_source = (runner.SCRIPT_DIRECTORY / "log_completed.applescript").read_text(encoding="utf-8")
    assert r"\"status\":\"ambiguous\"" in log_source
    assert r"\"readbackVerified\":false" in log_source
    assert r"\"status\":\"changed\"" not in log_source
    with pytest.raises(ValidationError):
        DeleteAreaRequest.model_validate({
            "mutationPhase": "preview",
            "areaId": "area-1",
            "script": "delete every area",
        })


@pytest.mark.anyio
async def test_shared_receipt_preview_execute_and_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir(mode=0o700)
    mutations._coordinator = MutationCoordinator(SecureRuntimePaths.create(runtime_root))
    monkeypatch.setenv("THINGS_MCP_ALLOW_LOCAL_IDENTITY_FALLBACK", "1")

    def fake_run(_script_name: str, arguments: list[str]):
        if arguments[0] == "preview":
            return runner.NativeBackendResult(
                status="previewed",
                affected_count=1,
                cascade_count=3,
                cascade_observed=True,
                target_state=["area:area-1", "todo:child-1", "todo:child-2"],
                readback_verified=False,
                message_code="delete_area_preview",
            )
        return runner.NativeBackendResult(
            status="changed",
            affected_count=1,
            cascade_count=3,
            cascade_observed=True,
            target_state=["area-absent:area-1"],
            readback_verified=True,
            message_code="delete_area_changed",
        )

    monkeypatch.setattr(mutations, "_safe_run", fake_run)
    preview_request = DeleteAreaRequest.model_validate({"mutationPhase": "preview", "areaId": "area-1"})
    preview = await mutations.call_mutating(
        "delete_area",
        "delete_area",
        preview_request,
        ctx=None,
        minimum_scope="things.admin",
        target_ids=("area-1",),
        outcome_count=1,
        script_arguments=["area-1"],
        undoable=False,
    )
    assert preview.status == "previewed"
    assert preview.cascade_count == 3
    assert preview.mutation_receipt
    execute_request = DeleteAreaRequest.model_validate({
        "mutationPhase": "execute",
        "mutationReceipt": preview.mutation_receipt,
        "areaId": "area-1",
    })
    execute = await mutations.call_mutating(
        "delete_area",
        "delete_area",
        execute_request,
        ctx=None,
        minimum_scope="things.admin",
        target_ids=("area-1",),
        outcome_count=1,
        script_arguments=["area-1"],
        undoable=False,
    )
    assert execute.status == "changed"
    assert execute.cascade_count == 3
    with pytest.raises(Exception, match="things_mutation_receipt_invalid"):
        await mutations.call_mutating(
            "delete_area",
            "delete_area",
            execute_request,
            ctx=None,
            minimum_scope="things.admin",
            target_ids=("area-1",),
            outcome_count=1,
            script_arguments=["area-1"],
            undoable=False,
        )
    mutations._coordinator = None


@pytest.mark.anyio
@pytest.mark.parametrize("affected_count", [0, 1, 25])
async def test_empty_trash_preserves_zero_one_many_impact_with_one_receipt_outcome(
    affected_count: int,
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
    pre_state = (
        ["trash-empty"] if affected_count == 0 else [f"trash-todo:{index}:stable" for index in range(affected_count)]
    )

    def fake_run(_script_name: str, arguments: list[str]) -> runner.NativeBackendResult:
        if arguments[0] == "preview":
            return runner.NativeBackendResult(
                status="previewed",
                affected_count=affected_count,
                cascade_count=affected_count,
                cascade_observed=True,
                target_state=pre_state,
                readback_verified=False,
                message_code="empty_trash_preview",
            )
        return runner.NativeBackendResult(
            status="skipped" if affected_count == 0 else "changed",
            affected_count=affected_count,
            cascade_count=affected_count,
            cascade_observed=True,
            target_state=["trash-empty"],
            readback_verified=True,
            message_code=("empty_trash_empty" if affected_count == 0 else "empty_trash_changed"),
        )

    monkeypatch.setattr(mutations, "_safe_run", fake_run)
    preview_request = EmptyTrashRequest.model_validate({"mutationPhase": "preview"})
    preview = await mutations.call_mutating(
        "empty_trash",
        "empty_trash",
        preview_request,
        ctx=None,
        minimum_scope="things.admin",
        target_ids=("empty-trash-outcome",),
        outcome_count=1,
        script_arguments=[],
        undoable=False,
    )
    assert preview.affected_count == affected_count
    assert preview.cascade_count == affected_count
    execute_request = EmptyTrashRequest.model_validate({
        "mutationPhase": "execute",
        "mutationReceipt": preview.mutation_receipt,
    })
    execute = await mutations.call_mutating(
        "empty_trash",
        "empty_trash",
        execute_request,
        ctx=None,
        minimum_scope="things.admin",
        target_ids=("empty-trash-outcome",),
        outcome_count=1,
        script_arguments=[],
        undoable=False,
    )
    assert execute.status == ("skipped" if affected_count == 0 else "changed")
    assert execute.affected_count == affected_count
    assert execute.cascade_count == affected_count


@pytest.mark.anyio
async def test_absent_native_target_is_one_verified_skipped_outcome(
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

    def fake_run(_script_name: str, _arguments: list[str]) -> runner.NativeBackendResult:
        return runner.NativeBackendResult(
            status="skipped",
            affected_count=0,
            cascade_count=0,
            cascade_observed=True,
            target_state=["area-absent:area-1"],
            readback_verified=True,
            message_code="area_absent",
        )

    monkeypatch.setattr(mutations, "_safe_run", fake_run)
    preview_request = DeleteAreaRequest.model_validate({"mutationPhase": "preview", "areaId": "area-1"})
    preview = await mutations.call_mutating(
        "delete_area",
        "delete_area",
        preview_request,
        ctx=None,
        minimum_scope="things.admin",
        target_ids=("area-1",),
        outcome_count=1,
        script_arguments=["area-1"],
        undoable=False,
    )
    assert preview.status == "skipped"
    execute_request = DeleteAreaRequest.model_validate({
        "mutationPhase": "execute",
        "mutationReceipt": preview.mutation_receipt,
        "areaId": "area-1",
    })
    execute = await mutations.call_mutating(
        "delete_area",
        "delete_area",
        execute_request,
        ctx=None,
        minimum_scope="things.admin",
        target_ids=("area-1",),
        outcome_count=1,
        script_arguments=["area-1"],
        undoable=False,
    )
    assert execute.status == "skipped"
    assert execute.affected_count == 0
    assert execute.readback_verified is True


@pytest.mark.anyio
async def test_set_tag_parent_binds_both_references_to_one_changed_outcome(
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
    observed: list[tuple[str, ...]] = []

    def fake_run(_script_name: str, arguments: list[str]) -> runner.NativeBackendResult:
        observed.append(tuple(arguments))
        phase, child_id, parent_id = arguments
        if phase == "preview":
            return runner.NativeBackendResult(
                status="previewed",
                affected_count=1,
                cascade_count=0,
                cascade_observed=False,
                target_state=[
                    f"tag:{child_id}:parent:old-parent",
                    f"intended-parent:{parent_id}:stable",
                ],
                readback_verified=False,
                message_code="set_tag_parent_preview",
            )
        return runner.NativeBackendResult(
            status="changed",
            affected_count=1,
            cascade_count=0,
            cascade_observed=False,
            target_state=[
                f"tag:{child_id}:parent:{parent_id}",
                f"intended-parent:{parent_id}:stable",
            ],
            readback_verified=True,
            message_code="set_tag_parent_changed",
        )

    monkeypatch.setattr(mutations, "_safe_run", fake_run)
    preview_request = SetTagParentRequest.model_validate({
        "mutationPhase": "preview",
        "tagId": "tag-child",
        "parentTagId": "tag-parent",
    })
    preview = await mutations.call_mutating(
        "set_tag_parent",
        "set_tag_parent",
        preview_request,
        ctx=None,
        minimum_scope="things.write",
        target_ids=(preview_request.tag_id,),
        outcome_count=1,
        script_arguments=[preview_request.tag_id, preview_request.parent_tag_id],
        undoable=None,
    )
    wrong_parent_request = SetTagParentRequest.model_validate({
        "mutationPhase": "execute",
        "mutationReceipt": preview.mutation_receipt,
        "tagId": "tag-child",
        "parentTagId": "tag-other-parent",
    })
    with pytest.raises(Exception, match="things_mutation_receipt_invalid"):
        await mutations.call_mutating(
            "set_tag_parent",
            "set_tag_parent",
            wrong_parent_request,
            ctx=None,
            minimum_scope="things.write",
            target_ids=(wrong_parent_request.tag_id,),
            outcome_count=1,
            script_arguments=[
                wrong_parent_request.tag_id,
                wrong_parent_request.parent_tag_id,
            ],
            undoable=None,
        )
    assert observed == [("preview", "tag-child", "tag-parent")]

    execute_request = SetTagParentRequest.model_validate({
        "mutationPhase": "execute",
        "mutationReceipt": preview.mutation_receipt,
        "tagId": "tag-child",
        "parentTagId": "tag-parent",
    })
    execute = await mutations.call_mutating(
        "set_tag_parent",
        "set_tag_parent",
        execute_request,
        ctx=None,
        minimum_scope="things.write",
        target_ids=(execute_request.tag_id,),
        outcome_count=1,
        script_arguments=[execute_request.tag_id, execute_request.parent_tag_id],
        undoable=None,
    )
    assert execute.status == "changed"
    assert execute.affected_count == 1
    assert observed == [
        ("preview", "tag-child", "tag-parent"),
        ("preview", "tag-child", "tag-parent"),
        ("execute", "tag-child", "tag-parent"),
    ]


@pytest.mark.anyio
async def test_same_count_different_target_state_rejects_native_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir(mode=0o700)
    mutations._coordinator = MutationCoordinator(SecureRuntimePaths.create(runtime_root))
    monkeypatch.setenv("THINGS_MCP_ALLOW_LOCAL_IDENTITY_FALLBACK", "1")
    preview_reads = 0
    mutation_called = False

    def fake_run(_script_name: str, arguments: list[str]) -> runner.NativeBackendResult:
        nonlocal mutation_called, preview_reads
        if arguments[0] == "preview":
            preview_reads += 1
            child_state = "todo:child-before" if preview_reads == 1 else "todo:child-after"
            return runner.NativeBackendResult(
                status="previewed",
                affected_count=1,
                cascade_count=1,
                cascade_observed=True,
                target_state=["area:area-1", child_state],
                readback_verified=False,
                message_code="delete_area_preview",
            )
        mutation_called = True
        return runner.NativeBackendResult(
            status="changed",
            affected_count=1,
            cascade_count=1,
            cascade_observed=True,
            target_state=["area-absent:area-1"],
            readback_verified=True,
            message_code="delete_area_changed",
        )

    monkeypatch.setattr(mutations, "_safe_run", fake_run)
    preview_request = DeleteAreaRequest.model_validate({"mutationPhase": "preview", "areaId": "area-1"})
    preview = await mutations.call_mutating(
        "delete_area",
        "delete_area",
        preview_request,
        ctx=None,
        minimum_scope="things.admin",
        target_ids=("area-1",),
        outcome_count=1,
        script_arguments=["area-1"],
        undoable=False,
    )
    execute_request = DeleteAreaRequest.model_validate({
        "mutationPhase": "execute",
        "mutationReceipt": preview.mutation_receipt,
        "areaId": "area-1",
    })
    with pytest.raises(Exception, match="things_mutation_stale_state"):
        await mutations.call_mutating(
            "delete_area",
            "delete_area",
            execute_request,
            ctx=None,
            minimum_scope="things.admin",
            target_ids=("area-1",),
            outcome_count=1,
            script_arguments=["area-1"],
            undoable=False,
        )
    assert preview_reads == 2
    assert mutation_called is False
    mutations._coordinator = None
