"""Adversarial execution tests use disposable POSIX fixtures, never user files."""

from __future__ import annotations

import copy
import json
import multiprocessing
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import files_buddy_execution as execution  # noqa: E402


@pytest.fixture
def workspace(tmp_path):
    # Darwin's default temporary directory is under protected /private and may
    # contain symlinks. Native qualification uses an owned home fixture instead.
    with tempfile.TemporaryDirectory(
        prefix="files-buddy-test-", dir=Path.home() if platform.system() == "Darwin" else tmp_path
    ) as temporary:
        root = Path(temporary)
        source = root / "source"
        destination = root / "destination"
        source.mkdir()
        destination.mkdir()
        store = execution.StateStore(root / "state")
        yield source, destination, store


def create(workspace, kind="move", names=("sample.txt",)):
    source, destination, store = workspace
    mapping = []
    for name in names:
        (source / name).write_bytes(b"evidence-bound content\n")
        (source / name).chmod(0o640)
        mapping.append({"type": kind, "source": str(source / name), "destination": str(destination / name)})
    plan = execution.make_plan(mapping, [source], [destination], "Disposable test fixture", local_only=True)
    path, state = execution.create_state(store, plan)
    return path, state


def run_cli(store, *arguments):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "manifest-manager.py"), "--state-dir", str(store.root), *arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    return result, json.loads(result.stdout)


@pytest.mark.parametrize("kind", ["copy", "move", "rename"])
def test_round_trip_preserves_content_mode_and_mtime(workspace, kind):
    source, destination, store = workspace
    path, state = create(workspace, kind)
    before = state["plan"]["operations"][0]["before"]
    completed = execution.execute(store, str(path), state["plan_digest"])
    assert completed["status"] == "completed"
    assert execution.validate_outcomes(completed) == []
    result = destination / "sample.txt"
    assert result.read_bytes() == b"evidence-bound content\n"
    assert result.stat().st_mtime_ns == before["mtime_ns"]
    assert result.stat().st_mode == before["mode"]
    assert (source / "sample.txt").exists() == (kind == "copy")
    preview = execution.reverse_plan(store, str(path))
    assert result.exists()  # Preview records intent but never moves files.
    undone = execution.execute(store, str(path), preview["undo"]["plan_digest"], undo=True)
    assert undone["status"] == "undone"
    assert execution.validate_outcomes(undone) == []
    assert (source / "sample.txt").read_bytes() == b"evidence-bound content\n"
    assert not result.exists()
    if kind == "copy":
        quarantine = Path(undone["undo"]["plan"]["operations"][0]["destination"])
        assert quarantine.parent == destination
        assert quarantine.read_bytes() == (source / "sample.txt").read_bytes()
        assert quarantine.name.startswith(".files-buddy-undo-")
    else:
        assert (source / "sample.txt").stat().st_ino == before["inode"]


def test_approval_digest_is_exact_and_json_flag_is_not_authority(workspace):
    source, destination, store = workspace
    path, state = create(workspace)
    with pytest.raises(execution.ContractError, match="approval"):
        execution.execute(store, str(path), "0" * 64)
    state["approved"] = True
    with pytest.raises(execution.ContractError, match="exactly"):
        execution.validate_state(state)
    assert (source / "sample.txt").exists()
    assert not (destination / "sample.txt").exists()
    assert store.read(path)["approval"] is None


def test_new_files_never_join_a_reviewed_mapping(workspace):
    source, destination, store = workspace
    path, state = create(workspace)
    (source / "new.txt").write_text("arrived after approval")
    completed = execution.execute(store, str(path), state["plan_digest"])
    assert completed["status"] == "completed"
    assert (source / "new.txt").read_text() == "arrived after approval"
    assert not (destination / "new.txt").exists()
    assert len(completed["operations"]) == 1


def test_same_size_same_mtime_changed_source_blocks(workspace):
    source, destination, store = workspace
    path, state = create(workspace)
    target = source / "sample.txt"
    old = target.stat()
    target.write_bytes(b"changed content value\n!")
    # Preserve size as well as mtime to exercise hash/ctime identity evidence.
    target.write_bytes(b"x" * old.st_size)
    os.utime(target, ns=(old.st_atime_ns, old.st_mtime_ns))
    completed = execution.execute(store, str(path), state["plan_digest"])
    assert completed["status"] == "partial"
    assert completed["operations"][0]["status"] in {"uncertain", "conflict"}
    assert target.exists()
    assert not (destination / target.name).exists()
    with pytest.raises(execution.ContractError, match="replay"):
        execution.execute(store, str(path), state["plan_digest"])


def test_replaced_source_inode_blocks_even_equal_content(workspace):
    source, destination, store = workspace
    path, state = create(workspace)
    old = source / "sample.txt"
    old.rename(source / "retained.txt")
    old.write_bytes(b"evidence-bound content\n")
    completed = execution.execute(store, str(path), state["plan_digest"])
    assert completed["status"] == "partial"
    assert old.exists()
    assert not (destination / old.name).exists()


def test_destination_collision_never_overwrites(workspace):
    source, destination, store = workspace
    path, state = create(workspace)
    target = destination / "sample.txt"
    target.write_text("new user data")
    completed = execution.execute(store, str(path), state["plan_digest"])
    assert completed["status"] == "partial"
    assert target.read_text() == "new user data"
    assert (source / target.name).exists()


@pytest.mark.parametrize("kind", ["copy", "move"])
def test_collision_at_native_boundary_never_overwrites(workspace, kind):
    source, destination, store = workspace
    path, state = create(workspace, kind)
    target = destination / "sample.txt"

    def race(boundary):
        if boundary == "before-effect":
            target.write_text("racing application")

    completed = execution.execute(store, str(path), state["plan_digest"], fault=race)
    assert completed["status"] == "partial"
    assert target.read_text() == "racing application"
    assert (source / target.name).exists()


@pytest.mark.parametrize("boundary", ["prepared", "after-effect", "applied"])
def test_interruption_has_durable_intent_and_never_replays(workspace, boundary):
    source, destination, store = workspace
    path, state = create(workspace)

    def stop(point):
        if point == boundary:
            raise KeyboardInterrupt("synthetic process termination")

    with pytest.raises(KeyboardInterrupt):
        execution.execute(store, str(path), state["plan_digest"], fault=stop)
    saved = store.read(path)
    assert saved["operations"][0]["status"] in {"prepared", "applied"}
    assert saved["approval"]["plan_digest"] == state["plan_digest"]
    with pytest.raises(execution.ContractError, match="replay"):
        execution.execute(store, str(path), state["plan_digest"])
    reconciled = execution.reconcile(store, str(path))
    if boundary == "prepared":
        assert (source / "sample.txt").exists()
        assert not (destination / "sample.txt").exists()
        assert reconciled["status"] == "partial"
    else:
        assert reconciled["status"] == "completed"
        assert (destination / "sample.txt").exists()


def test_unrecorded_copy_identity_stays_uncertain(workspace):
    source, destination, store = workspace
    path, state = create(workspace, "copy")

    def stop(point):
        if point == "after-effect":
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        execution.execute(store, str(path), state["plan_digest"], fault=stop)
    reconciled = execution.reconcile(store, str(path))
    assert reconciled["status"] == "partial"
    assert reconciled["operations"][0]["status"] == "uncertain"
    assert "identity" in reconciled["operations"][0]["error"]
    assert (source / "sample.txt").exists()
    assert (destination / "sample.txt").exists()


def test_stop_policy_leaves_unstarted_operations_untouched(workspace):
    source, destination, store = workspace
    path, state = create(workspace, names=("first", "second"))
    (destination / "first").write_text("occupied")
    completed = execution.execute(store, str(path), state["plan_digest"])
    assert completed["status"] == "partial"
    assert completed["operations"][1]["status"] == "planned"
    assert (source / "second").exists()
    assert not (destination / "second").exists()


def test_undo_does_not_overwrite_new_original(workspace):
    source, destination, store = workspace
    path, state = create(workspace)
    execution.execute(store, str(path), state["plan_digest"])
    preview = execution.reverse_plan(store, str(path))
    (source / "sample.txt").write_text("new original")
    result = execution.execute(store, str(path), preview["undo"]["plan_digest"], undo=True)
    assert result["status"] == "partial"
    assert (source / "sample.txt").read_text() == "new original"
    assert (destination / "sample.txt").read_bytes() == b"evidence-bound content\n"


def test_reverse_plan_rejects_changed_destination(workspace):
    _source, destination, store = workspace
    path, state = create(workspace)
    execution.execute(store, str(path), state["plan_digest"])
    (destination / "sample.txt").write_text("edited after move")
    with pytest.raises(execution.ContractError, match="match"):
        execution.reverse_plan(store, str(path))


def test_copy_reverse_collision_preserves_both_files(workspace):
    source, destination, store = workspace
    path, state = create(workspace, "copy")
    execution.execute(store, str(path), state["plan_digest"])
    preview = execution.reverse_plan(store, str(path))
    quarantine = Path(preview["undo"]["plan"]["operations"][0]["destination"])
    quarantine.write_text("occupied")
    result = execution.execute(store, str(path), preview["undo"]["plan_digest"], undo=True)
    assert result["status"] == "partial"
    assert quarantine.read_text() == "occupied"
    assert (source / "sample.txt").read_bytes() == (destination / "sample.txt").read_bytes()


def test_symlink_and_parent_replacement_are_rejected(workspace):
    source, destination, store = workspace
    path, state = create(workspace)
    outside = source.parent / "outside"
    outside.mkdir()
    (outside / "sample.txt").write_text("do not move")
    source.rename(source.parent / "old-source")
    source.symlink_to(outside, target_is_directory=True)
    with pytest.raises(OSError, match=r"directory|symbolic|loop|levels"):
        execution.execute(store, str(path), state["plan_digest"])
    assert (outside / "sample.txt").read_text() == "do not move"
    assert not (destination / "sample.txt").exists()


def test_manifest_discovery_never_reads_outside_symlinks(workspace):
    _source, _destination, store = workspace
    path, state = create(workspace)
    outside = store.root.parent / "outside.json"
    outside.write_text(json.dumps({**state, "marker": "outside-secret"}))
    link = store.manifests / "outside.json"
    link.symlink_to(outside)
    assert store.discover() == ([path], [])
    result, payload = run_cli(store, "search", "outside-secret")
    assert result.returncode == 0
    assert payload == {"valid": True, "results": [], "errors": []}
    result, payload = run_cli(store, "show", str(link))
    assert result.returncode == 1
    assert payload["valid"] is False


@pytest.mark.parametrize("arguments", [("list",), ("search", "Disposable")])
def test_discovery_reports_corrupt_and_unknown_states_alongside_valid(workspace, arguments):
    _source, _destination, store = workspace
    path, _state = create(workspace)
    corrupt = store.manifests / "corrupt.json"
    corrupt.write_text("{invalid JSON")
    unknown = store.manifests / "unknown.json"
    unknown.write_text('{"schema_version": "999.0"}')
    result, payload = run_cli(store, *arguments)
    assert result.returncode == 1
    assert payload["valid"] is False
    assert [row["manifest"] for row in payload["results"]] == [str(path)]
    assert {row["manifest"] for row in payload["errors"]} == {str(corrupt), str(unknown)}
    assert all(row["error"] for row in payload["errors"])


def test_discovery_reports_rejected_regular_state_without_reading_it(workspace):
    _source, _destination, store = workspace
    path, _state = create(workspace)
    alias = store.manifests / "hardlink.json"
    os.link(path, alias)
    result, payload = run_cli(store, "list")
    assert result.returncode == 1
    assert payload["results"] == []
    assert {row["manifest"] for row in payload["errors"]} == {str(path), str(alias)}
    assert all("singly-linked" in row["error"] for row in payload["errors"])


def test_state_root_symlink_rejected_before_child_creation(workspace):
    root = workspace[0].parent
    external = root / "external"
    external.mkdir()
    link = root / "state"
    link.symlink_to(external, target_is_directory=True)
    store = execution.StateStore(link)
    with pytest.raises(OSError, match=r"directory|symbolic|loop|levels"), store.lock():
        pytest.fail("symlink state entered")
    assert list(external.iterdir()) == []


def test_manifest_identity_and_scope_prefix_are_not_aliases(workspace):
    source, destination, store = workspace
    _path, state = create(workspace)
    altered = copy.deepcopy(state)
    altered["plan"]["operations"][0]["destination"] = str(
        destination.with_name(destination.name + "-other") / "sample.txt"
    )
    altered["plan_digest"] = execution.canonical_digest(altered["plan"])
    with pytest.raises(execution.ContractError, match="outside"):
        execution.validate_state(altered)
    alias = store.manifests / "alias.json"
    alias.write_text(json.dumps(state))
    with pytest.raises(execution.ContractError, match="filename"):
        store.read(alias)
    assert (source / "sample.txt").exists()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda p: p.update(schema_version="99.0"),
        lambda p: p.update(failure_policy="continue"),
        lambda p: p.update(local_only_attested=False),
        lambda p: p["operations"][0].update(type="shell"),
        lambda p: p["operations"][0]["before"].update(size_bytes=-1),
        lambda p: p["operations"][0]["before"].update(size_bytes=1.5),
        lambda p: p["operations"][0]["before"].update(size_bytes=True),
        lambda p: p.update(created_at="not-a-time"),
        lambda p: p["operations"][0].update(unexpected=True),
    ],
)
def test_closed_plan_contract_rejects_malformed_values(workspace, mutation):
    _path, state = create(workspace)
    mutation(state["plan"])
    with pytest.raises(execution.ContractError):
        execution.validate_plan(state["plan"])


def test_invalid_validation_returns_nonzero(workspace):
    _source, _destination, store = workspace
    path, _state = create(workspace)
    path.write_text('{"schema_version":"2.0"}')
    result, payload = run_cli(store, "validate", str(path))
    assert result.returncode == 1
    assert payload["valid"] is False


def test_stale_postcondition_validation_returns_nonzero(workspace):
    _source, destination, store = workspace
    path, state = create(workspace)
    execution.execute(store, str(path), state["plan_digest"])
    (destination / "sample.txt").rename(destination / "moved-elsewhere")
    result, payload = run_cli(store, "validate", str(path))
    assert result.returncode == 1
    assert payload["schema_valid"] is True
    assert payload["valid"] is False


def test_legacy_invalid_mkdir_and_unknown_operation_rejected(workspace):
    source, _destination, store = workspace
    _path, _state = create(workspace)
    value = {
        "version": "1.0",
        "created": execution.now(),
        "mode": "organize",
        "intent": "legacy fixture",
        "target_path": str(source),
        "status": "closed",
        "operations": [
            {
                "type": "mkdir",
                "status": "completed",
                "timestamp": "not-a-time",
                "destination": str(source / "sample.txt"),
            }
        ],
        "summary": {},
    }
    path = store.manifests / "legacy.json"
    path.write_text(json.dumps(value))
    result, payload = run_cli(store, "validate", str(path))
    assert result.returncode == 1
    assert payload["legacy"] is True
    value["operations"][0]["timestamp"] = execution.now()
    path.write_text(json.dumps(value))
    result, payload = run_cli(store, "validate", str(path))
    assert result.returncode == 1  # A regular file is never accepted as mkdir.
    value["operations"][0].update(type="unknown", status="failed", size_bytes=-1)
    assert execution.inspect_legacy(value)["valid"] is False
    assert execution.inspect_legacy(value)["hash_algorithm"] == "blake3"
    with pytest.raises(execution.ContractError, match="exactly"):
        execution.execute(store, str(path), "0" * 64)


def test_no_unsafe_legacy_append_or_close_route(workspace):
    _source, _destination, store = workspace
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "manifest-manager.py"), "--state-dir", str(store.root), "append", "untrusted"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "invalid choice" in result.stderr


def test_public_cli_refuses_non_mac_mutation(workspace):
    if platform.system() == "Darwin":
        pytest.skip("Non-macOS refusal fixture")
    source, destination, store = workspace
    path, state = create(workspace)
    result, payload = run_cli(store, "execute", str(path), "--approve", state["plan_digest"])
    assert result.returncode == 1
    assert "macOS-only" in payload["error"]
    assert (source / "sample.txt").exists()
    assert not (destination / "sample.txt").exists()


def test_mapping_rejects_hardlinks_and_unattested_cloud(workspace):
    source, destination, _store = workspace
    target = source / "sample"
    target.write_text("content")
    os.link(target, source / "alias")
    mapping = [{"type": "move", "source": str(target), "destination": str(destination / "sample")}]
    with pytest.raises(execution.ContractError, match="attest"):
        execution.make_plan(mapping, [source], [destination], "fixture", local_only=False)
    with pytest.raises(execution.ContractError, match="singly-linked"):
        execution.make_plan(mapping, [source], [destination], "fixture", local_only=True)


def test_project_and_known_cloud_paths_fail_before_content_access(workspace):
    source, destination, _store = workspace
    (source / ".git").mkdir()
    (source / "sample").write_text("project content")
    mapping = [{"type": "move", "source": str(source / "sample"), "destination": str(destination / "sample")}]
    with pytest.raises(execution.ContractError, match="dependency"):
        execution.make_plan(mapping, [source], [destination], "fixture", local_only=True)
    for path in [
        "/System",
        "/",
        "/Users/test/Library/CloudStorage",
        "/Users/test/Library/CloudStorage/Provider/a",
        "/Users/test/Dropbox/a",
        "/Users/test/Pictures/Library.photoslibrary/a",
    ]:
        with pytest.raises(execution.ContractError):
            execution._policy_path(Path(path))
    execution._policy_path(Path("/Users/test/Downloads"))  # Root '/' is exact-only.


def test_state_schema_assets_match_runtime(workspace):
    _path, state = create(workspace)
    assets = SCRIPTS.parent / "assets"
    plan_schema = json.loads((assets / "plan.schema.json").read_text())
    state_schema = json.loads((assets / "state.schema.json").read_text())
    registry = Registry().with_resources(
        [(schema["$id"], Resource.from_contents(schema)) for schema in [plan_schema, state_schema]]
    )
    Draft202012Validator.check_schema(plan_schema)
    Draft202012Validator.check_schema(state_schema)
    Draft202012Validator(plan_schema, registry=registry, format_checker=FormatChecker()).validate(state["plan"])
    Draft202012Validator(state_schema, registry=registry, format_checker=FormatChecker()).validate(state)


def _concurrent_execute(state_root, reference, digest, barrier, queue):
    try:
        barrier.wait(timeout=10)
        result = execution.execute(execution.StateStore(Path(state_root)), reference, digest)
        queue.put(result["status"])
    except execution.ContractError as exc:
        queue.put(str(exc))


def test_concurrent_same_plan_executes_once_and_retains_all_records(workspace):
    source, destination, store = workspace
    path, state = create(workspace, names=("a", "b", "c"))
    ctx = multiprocessing.get_context("fork")
    barrier, queue = ctx.Barrier(2), ctx.Queue()
    workers = [
        ctx.Process(target=_concurrent_execute, args=(str(store.root), str(path), state["plan_digest"], barrier, queue))
        for _ in range(2)
    ]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=20)
        assert not worker.is_alive()
        assert worker.exitcode == 0
    results = [queue.get(timeout=2), queue.get(timeout=2)]
    assert results.count("completed") == 1
    assert any("replay" in item for item in results)
    saved = store.read(path)
    assert len(saved["operations"]) == 3
    assert all(row["status"] == "verified" for row in saved["operations"])
    assert not list(source.iterdir())
    assert len(list(destination.iterdir())) == 3
    assert not list(store.manifests.glob("*.tmp"))


def test_private_lock_symlink_is_never_followed(workspace):
    _source, _destination, store = workspace
    _path, _state = create(workspace)
    outside = store.root.parent / "external-lock"
    outside.write_text("preserve")
    (store.root / "execution.lock").unlink()
    (store.root / "execution.lock").symlink_to(outside)
    with pytest.raises(OSError, match=r"directory|symbolic|loop|levels"), store.lock():
        pytest.fail("entered symlink lock")
    assert outside.read_text() == "preserve"


def test_duplicate_json_keys_and_nan_rejected():
    for payload in ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}']:
        with pytest.raises(execution.ContractError):
            execution.load_json(payload)


def test_plan_and_undo_cli_are_real_commands(workspace):
    source, destination, store = workspace
    item = source / "sample"
    item.write_text("content")
    mapping = source.parent / "mapping.json"
    mapping.write_text(json.dumps([{"type": "move", "source": str(item), "destination": str(destination / "sample")}]))
    result, payload = run_cli(
        store,
        "plan",
        "--mapping",
        str(mapping),
        "--source-root",
        str(source),
        "--destination-root",
        str(destination),
        "--intent",
        "fixture",
        "--local-only",
    )
    assert result.returncode == 0
    assert payload["approval_required"] is True
    assert item.exists()
    assert not (destination / "sample").exists()
    result, validation = run_cli(store, "validate", payload["manifest"])
    assert result.returncode == 0
    assert validation["valid"] is True
    result, _validation = run_cli(store, "undo", payload["manifest"])
    assert result.returncode == 1  # Requires real verified completion, not a made-up undo receipt.


def test_copy_growth_is_bounded_to_approved_bytes(workspace):
    source, destination, store = workspace
    path, state = create(workspace, "copy")
    approved_bytes = state["plan"]["operations"][0]["before"]["size_bytes"]

    def grow(point):
        if point == "copy-chunk":
            with (source / "sample.txt").open("ab") as stream:
                stream.write(b"unapproved growth")

    result = execution.execute(store, str(path), state["plan_digest"], fault=grow)
    assert result["status"] == "partial"
    assert result["operations"][0]["status"] == "uncertain"
    assert "grew" in result["operations"][0]["error"]
    assert (destination / "sample.txt").stat().st_size == approved_bytes
    assert (source / "sample.txt").stat().st_size > approved_bytes


def test_source_replacement_at_effect_boundary_is_rejected(workspace):
    source, destination, store = workspace
    path, state = create(workspace)

    def replace(point):
        if point == "before-effect":
            (source / "sample.txt").rename(source / "retained.txt")
            (source / "sample.txt").write_text("replacement belongs to another operation")

    result = execution.execute(store, str(path), state["plan_digest"], fault=replace)
    assert result["status"] == "partial"
    assert result["operations"][0]["status"] == "uncertain"
    assert (source / "retained.txt").read_bytes() == b"evidence-bound content\n"
    assert (source / "sample.txt").read_text() == "replacement belongs to another operation"
    assert not (destination / "sample.txt").exists()


def test_sparse_file_is_not_silently_expanded(workspace):
    source, destination, _store = workspace
    target = source / "sparse"
    with target.open("wb") as stream:
        stream.seek(8 * 1024 * 1024)
        stream.write(b"x")
    if target.stat().st_blocks * 512 >= target.stat().st_size:
        pytest.skip("Fixture filesystem does not expose sparse allocation")
    with pytest.raises(execution.ContractError, match="Sparse"):
        execution.make_plan(
            [{"type": "copy", "source": str(target), "destination": str(destination / "sparse")}],
            [source],
            [destination],
            "fixture",
            local_only=True,
        )


@pytest.mark.skipif(platform.system() != "Darwin", reason="Native macOS ACL API qualification")
def test_native_extended_acl_is_rejected(workspace):
    import getpass

    source, destination, _store = workspace
    target = source / "acl-file"
    target.write_text("owned native ACL fixture")
    subprocess.run(
        ["/bin/chmod", "+a", f"{getpass.getuser()} allow read", str(target)], check=True, capture_output=True
    )
    with pytest.raises(execution.ContractError, match="ACL"):
        execution.make_plan(
            [{"type": "move", "source": str(target), "destination": str(destination / "acl-file")}],
            [source],
            [destination],
            "native qualification",
            local_only=True,
        )


@pytest.mark.skipif(platform.system() != "Darwin", reason="Native macOS xattr/resource-fork qualification")
def test_native_extended_attribute_is_rejected(workspace):
    source, destination, _store = workspace
    target = source / "xattr-file"
    target.write_text("owned native xattr fixture")
    os.setxattr(target, "com.files-buddy.fixture", b"retained metadata")
    with pytest.raises(execution.ContractError, match="attributes"):
        execution.make_plan(
            [{"type": "copy", "source": str(target), "destination": str(destination / "xattr-file")}],
            [source],
            [destination],
            "native qualification",
            local_only=True,
        )
    assert os.getxattr(target, "com.files-buddy.fixture") == b"retained metadata"


@pytest.mark.skipif(platform.system() != "Darwin", reason="Native macOS no-clobber CLI and reverse qualification")
def test_native_cli_executes_and_reverses_exact_plan(workspace):
    source, destination, store = workspace
    path, state = create(workspace)
    result, complete = run_cli(store, "execute", str(path), "--approve", state["plan_digest"])
    assert result.returncode == 0
    assert complete["status"] == "completed"
    result, preview = run_cli(store, "undo", str(path))
    assert result.returncode == 0
    result, reversed_state = run_cli(store, "undo", str(path), "--approve", preview["reverse_plan"]["plan_digest"])
    assert result.returncode == 0
    assert reversed_state["status"] == "undone"
    assert (source / "sample.txt").exists()
    assert not (destination / "sample.txt").exists()


def test_execution_report_is_derived_and_does_not_authorize(workspace):
    source, destination, store = workspace
    path, state = create(workspace, "copy")
    before_report = path.read_bytes()
    result, planned = run_cli(store, "report", str(path))
    assert result.returncode == 0
    assert planned["status"] == "waiting-for-approval"
    assert planned["savings"]["selected_bytes"] is None
    assert planned["savings"]["verified_reclaimed_bytes"] is None
    assert path.read_bytes() == before_report
    with pytest.raises(execution.ContractError, match="exactly"):
        execution.validate_state(planned)
    completed = execution.execute(store, str(path), state["plan_digest"])
    result, report = run_cli(store, "report", str(path))
    assert result.returncode == 0
    byte_count = completed["plan"]["operations"][0]["before"]["size_bytes"]
    assert report["savings"]["selected_bytes"] == byte_count
    assert report["savings"]["acted_bytes"] == byte_count
    assert report["savings"]["verified_reclaimed_bytes"] is None
    assert report["savings"]["cloud_bytes_affected"] is None
    assert report["operations"][0]["source"] == str(source / "sample.txt")
    assert report["operations"][0]["destination"] == str(destination / "sample.txt")
    report_schema = json.loads((SCRIPTS.parent / "assets" / "report.schema.json").read_text())
    Draft202012Validator(report_schema, format_checker=FormatChecker()).validate(report)
    report_file = store.root / "report.json"
    report_file.write_text(json.dumps(report))
    rendered = store.root / "report.html"
    render = subprocess.run(
        [sys.executable, str(SCRIPTS / "dashboard-renderer.py"), "--data", str(report_file), "--output", str(rendered)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert render.returncode == 0, render.stdout
    assert rendered.is_file()
    assert "verified_reclaimed_bytes" in rendered.read_text()
    preview = execution.reverse_plan(store, str(path))
    execution.execute(store, str(path), preview["undo"]["plan_digest"], undo=True)
    result, reversed_report = run_cli(store, "report", str(path))
    assert result.returncode == 0
    assert reversed_report["savings"]["quarantined_bytes"] == byte_count
    assert reversed_report["savings"]["verified_reclaimed_bytes"] is None


def test_interrupted_execution_report_keeps_acted_bytes_unknown(workspace):
    _source, _destination, store = workspace
    path, state = create(workspace)

    def interrupt(boundary):
        if boundary == "prepared":
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        execution.execute(store, str(path), state["plan_digest"], fault=interrupt)
    result, report = run_cli(store, "report", str(path))
    assert result.returncode == 0
    assert report["savings"]["acted_bytes"] is None
    assert report["coverage"]["status"] == "partial"


@pytest.mark.parametrize("field", ["type", "status"])
def test_enum_containers_are_structured_errors(workspace, field):
    _source, _destination, store = workspace
    path, state = create(workspace)
    if field == "type":
        state["plan"]["operations"][0][field] = []
        state["plan_digest"] = execution.canonical_digest(state["plan"])
    else:
        state[field] = []
    path.write_text(json.dumps(state))
    result, payload = run_cli(store, "validate", str(path))
    assert result.returncode == 1
    assert payload["valid"] is False
    assert "Traceback" not in result.stderr


def test_zero_progress_copy_write_fails_without_looping(workspace, monkeypatch):
    source, destination, store = workspace
    path, state = create(workspace, "copy")
    monkeypatch.setattr(execution.os, "write", lambda *_args: 0)
    result = execution.execute(store, str(path), state["plan_digest"])
    assert result["status"] == "partial"
    assert "no progress" in result["operations"][0]["error"]
    assert (source / "sample.txt").exists()
    assert (destination / "sample.txt").stat().st_size == 0


def test_state_replacement_failure_preserves_previous_document(workspace, monkeypatch):
    _source, _destination, store = workspace
    path, state = create(workspace)
    original = path.read_bytes()

    def fail(*_args, **_kwargs):
        raise OSError("synthetic replace failure")

    monkeypatch.setattr(execution.os, "replace", fail)
    with store.lock(), pytest.raises(OSError, match="synthetic replace failure"):
        store.write(state)
    assert path.read_bytes() == original
    assert not list(store.manifests.glob("*.tmp"))


def _held_scope_execution(state_root, reference, digest, prepared, release, queue):
    def hold(boundary):
        if boundary == "prepared":
            prepared.set()
            if not release.wait(timeout=10):
                raise RuntimeError("Fixture release was not received")

    result = execution.execute(execution.StateStore(Path(state_root)), reference, digest, fault=hold)
    queue.put(result["status"])


def _observed_scope_execution(state_root, reference, digest, attempting, acquired, queue):
    import contextlib

    original = execution._scope_locks

    @contextlib.contextmanager
    def observed(plan):
        attempting.set()
        with original(plan):
            acquired.set()
            yield

    execution._scope_locks = observed
    result = execution.execute(execution.StateStore(Path(state_root)), reference, digest)
    queue.put(result["status"])


def test_overlapping_scopes_coordinate_across_distinct_state_directories(workspace):
    source, destination, first_store = workspace
    first_path, first_state = create(workspace)
    second_store = execution.StateStore(first_store.root.parent / "state-two")
    second_plan = execution.make_plan(
        [{"type": "move", "source": str(source / "sample.txt"), "destination": str(destination / "second.txt")}],
        [source],
        [destination],
        "Second independent fixture state",
        local_only=True,
    )
    second_path, second_state = execution.create_state(second_store, second_plan)
    ctx = multiprocessing.get_context("fork")
    prepared, release, attempting, acquired, queue = ctx.Event(), ctx.Event(), ctx.Event(), ctx.Event(), ctx.Queue()
    first = ctx.Process(
        target=_held_scope_execution,
        args=(str(first_store.root), str(first_path), first_state["plan_digest"], prepared, release, queue),
    )
    second = ctx.Process(
        target=_observed_scope_execution,
        args=(str(second_store.root), str(second_path), second_state["plan_digest"], attempting, acquired, queue),
    )
    first.start()
    try:
        assert prepared.wait(timeout=5)
        second.start()
        assert attempting.wait(timeout=5)
        assert not acquired.wait(timeout=0.2)
    finally:
        release.set()
        first.join(timeout=15)
        if second.pid is not None:
            second.join(timeout=15)
    assert not first.is_alive()
    assert not second.is_alive()
    assert first.exitcode == 0
    assert second.exitcode == 0
    assert sorted([queue.get(timeout=2), queue.get(timeout=2)]) == ["completed", "partial"]
    assert (destination / "sample.txt").exists()
    assert not (destination / "second.txt").exists()


def test_unprivate_state_root_fails_before_creating_children(workspace):
    root = workspace[0].parent / "unprivate-state"
    root.mkdir(mode=0o777)
    root.chmod(0o777)
    store = execution.StateStore(root)
    with pytest.raises(execution.ContractError, match="group/world writable"), store.lock():
        pytest.fail("entered unprivate state root")
    assert not (root / "manifests").exists()


@pytest.mark.parametrize(
    "path",
    [
        "/Users/test/.cache/huggingface/model.bin",
        "/Users/test/.ollama/models/blob",
        "/Users/test/.docker/image",
        "/Users/test/Library/Application Support/App/state.db",
        "/Users/test/Downloads/.env.production",
        "/Users/test/Downloads/active-vm.qcow2",
    ],
)
def test_owner_managed_data_cannot_use_generic_executor(path):
    with pytest.raises(execution.ContractError):
        execution._policy_path(Path(path))


@pytest.mark.parametrize(
    "path",
    [
        "/system/Volumes/Data/private",
        "/APPLICATIONS/Example.APP/data",
        "/Users/test/.SSH/id_ed25519",
        "/Users/test/.GnUpG/keyring",
        "/Users/test/.AWS/credentials",
        "/Users/test/Downloads/.ENV.production",
        "/Users/test/Downloads/.GITIGNORE",
        "/Users/test/OneDrive - Personal/a",
        "/Users/test/GOOGLEDRIVE-user/a",
        "/Users/test/dropbox/a",
    ],
)
def test_policy_rejects_case_aliases_portably(path):
    with pytest.raises(execution.ContractError):
        execution._policy_path(Path(path))
    execution._policy_path(Path("/Systemic/ordinary.txt"))


@pytest.mark.skipif(platform.system() != "Darwin", reason="Native case-insensitive volume alias qualification")
def test_native_case_aliases_do_not_bypass_protection_or_project_markers(workspace):
    source, destination, _store = workspace
    sensitive = source / ".ssh"
    sensitive.mkdir()
    secret = sensitive / "credential"
    secret.write_text("owned disposable secret fixture")
    alias = source / ".SSH" / "credential"
    if not alias.exists():
        pytest.skip("Fixture volume is case-sensitive; aliases do not identify the same file")
    with pytest.raises(execution.ContractError, match="Sensitive"):
        execution.make_plan(
            [{"type": "move", "source": str(alias), "destination": str(destination / "credential")}],
            [source],
            [destination],
            "native case alias fixture",
            local_only=True,
        )
    assert secret.read_text() == "owned disposable secret fixture"
    marker = source / "PACKAGE.JSON"
    marker.write_text("{}")
    target = source / "ordinary.txt"
    target.write_text("project-owned file")
    # Native lookups of the canonical marker spelling also find case aliases.
    with pytest.raises(execution.ContractError, match="dependency"):
        execution.make_plan(
            [{"type": "move", "source": str(target), "destination": str(destination / target.name)}],
            [source],
            [destination],
            "native project marker fixture",
            local_only=True,
        )
    assert target.read_text() == "project-owned file"
    assert list(destination.iterdir()) == []
