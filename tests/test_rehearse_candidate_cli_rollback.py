from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from wagents.candidate_receipts import ReceiptConflictError

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "_rehearse_candidate_cli_rollback",
        ROOT / "scripts" / "rehearse_candidate_cli_rollback.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_snapshot_digest_covers_regular_file_bytes_mode_and_xattrs(tmp_path: Path) -> None:
    module = _module()
    executable = tmp_path / "tool"
    executable.write_text("one\n")
    executable.chmod(0o755)
    before = module.snapshot_digest(module.surface_snapshot([executable]))

    executable.write_text("two\n")
    after = module.snapshot_digest(module.surface_snapshot([executable]))

    assert before != after


def test_snapshot_digest_covers_symlink_target(tmp_path: Path) -> None:
    module = _module()
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.write_text("same\n")
    second.write_text("same\n")
    link = tmp_path / "tool"
    link.symlink_to(first)
    before = module.snapshot_digest(module.surface_snapshot([link]))

    link.unlink()
    link.symlink_to(second)
    after = module.snapshot_digest(module.surface_snapshot([link]))

    assert before != after


def test_atomic_detach_and_restore_preserves_exact_entrypoint(tmp_path: Path) -> None:
    module = _module()
    target = tmp_path / "target"
    target.write_text("tool\n")
    entrypoint = tmp_path / "tool"
    entrypoint.symlink_to(target)
    before = module.surface_snapshot([entrypoint])
    staged = tmp_path / ".wagents-rollback-test-tool"

    os.replace(entrypoint, staged)
    assert not entrypoint.exists()
    os.replace(staged, entrypoint)

    assert module.surface_snapshot([entrypoint]) == before


def test_public_entrypoints_deduplicates_lexically_equivalent_paths(monkeypatch) -> None:
    module = _module()
    canonical = Path.home() / ".local" / "bin" / "tool"
    lexical = Path.home() / ".local" / "share" / ".." / "bin" / "tool"
    monkeypatch.setattr(module.shutil, "which", lambda _name: str(lexical))
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            stdout=f"{lexical}\n{canonical}\n",
            returncode=0,
        ),
    )

    assert module.public_entrypoints({"package_manager": "uv-tool", "executables": ["tool"]}) == [canonical]


def test_isolated_interruption_never_mutates_live_entrypoint(tmp_path: Path) -> None:
    module = _module()
    live_root = tmp_path / "live"
    live_root.mkdir()
    target = live_root / "target"
    target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    target.chmod(0o755)
    entrypoint = live_root / "tool"
    entrypoint.symlink_to(target)
    before = module.surface_snapshot([entrypoint])
    isolated_bin = tmp_path / "isolated" / "bin"

    def interrupt_after_detach(_names: list[str], _isolated_bin: Path):
        assert not (isolated_bin / "tool").exists()
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        module.rehearse_isolated_surface(
            [entrypoint],
            ["tool"],
            isolated_bin,
            "interrupt",
            absence_probe=interrupt_after_detach,
        )

    assert module.surface_snapshot([entrypoint]) == before
    assert (isolated_bin / "tool").is_symlink()
    assert not list(isolated_bin.glob(".wagents-rollback-*"))


def test_isolated_rehearsal_binds_absence_process_and_output(tmp_path: Path) -> None:
    module = _module()
    live_root = tmp_path / "live"
    live_root.mkdir()
    target = live_root / "target"
    target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    target.chmod(0o755)
    entrypoint = live_root / "tool"
    entrypoint.symlink_to(target)
    isolated_bin = tmp_path / "isolated" / "bin"

    def prove_absence(names: list[str], root: Path):
        assert names == ["tool"]
        assert root == isolated_bin
        assert not (root / "tool").exists()
        return 1234, {"tool": None}, "a" * 64

    evidence = module.rehearse_isolated_surface(
        [entrypoint],
        ["tool"],
        isolated_bin,
        "success",
        absence_probe=prove_absence,
    )

    assert evidence["preimage_digest"] == evidence["rollback_digest"]
    assert evidence["fresh_absence_process_id"] == 1234
    assert evidence["fresh_absence_output_sha256"] == "a" * 64
    assert evidence["live_preimage"] == evidence["live_postimage"]
    assert (isolated_bin / "tool").resolve() == target


@pytest.mark.parametrize(
    ("absence_pid", "restored_pid", "absence_digest", "restored_digest"),
    [
        (0, 2, "a" * 64, "b" * 64),
        (2, 2, "a" * 64, "b" * 64),
        (1, 2, "not-a-digest", "b" * 64),
        (1, 2, "a" * 64, "z" * 64),
    ],
)
def test_process_evidence_fails_closed(
    absence_pid: int,
    restored_pid: int,
    absence_digest: str,
    restored_digest: str,
) -> None:
    module = _module()

    with pytest.raises(RuntimeError):
        module.validate_process_evidence(absence_pid, restored_pid, absence_digest, restored_digest)


def test_controlled_path_cannot_fall_through_to_live_entrypoint_dir(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    isolated_bin = tmp_path / "isolated"
    live_bin = tmp_path / "live"
    support_bin = tmp_path / "support"
    for path in (isolated_bin, live_bin, support_bin):
        path.mkdir()
    monkeypatch.setenv("PATH", os.pathsep.join([str(live_bin), str(support_bin)]))

    rendered = module.controlled_path(isolated_bin, {live_bin.resolve()}).split(os.pathsep)

    assert rendered == [str(isolated_bin), str(support_bin)]


def test_transcript_writer_hashes_exact_persisted_document(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    monkeypatch.setattr(module, "RUNTIME_STATE", tmp_path / "state")

    relative, digest = module.write_transcript(
        "artifact-1",
        {
            "artifact_id": "artifact-1",
            "status": "passed",
            "transaction_id": "transaction1",
        },
    )
    path = Path(relative)

    assert path.is_file()
    assert path == (
        tmp_path / "state" / "receipts" / "transcripts" / module.JOURNAL_KIND / "artifact-1-transaction1.json"
    )
    assert digest == module.sha256_file(path)
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "passed"


def test_receipt_writer_preserves_closure_receipts(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    output = tmp_path / "receipts.json"
    monkeypatch.setattr(module, "RECEIPTS", output)
    monkeypatch.setattr(module, "RUNTIME_STATE", tmp_path / "state")
    output.write_text(
        json.dumps({
            "version": 2,
            "revision": 0,
            "receipts": [],
            "closure_receipts": [{"gate_id": "docs-closure"}],
        })
        + "\n",
        encoding="utf-8",
    )

    module.write_receipts({("artifact", "rollback"): {"artifact_id": "artifact", "phase": "rollback"}})

    assert module.read_receipt_document()["closure_receipts"] == [{"gate_id": "docs-closure"}]


def test_rehearse_artifact_binds_installed_digest_and_semantic_use_to_explicit_maps(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _module()
    live_root = tmp_path / "live"
    live_root.mkdir()
    target = live_root / "tool-target"
    target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    target.chmod(0o755)
    entrypoint = live_root / "tool"
    entrypoint.symlink_to(target)
    install_root = tmp_path / "install"
    install_root.mkdir()
    installed_maps: list[dict[str, Path]] = []
    transcript_payloads: list[dict[str, object]] = []

    def installed_paths(_seed, executable_map):
        installed_maps.append(dict(executable_map))
        assert executable_map == {"tool": target}
        return [install_root]

    def repeat_probe(name, _body, executable_map):
        assert name == "tool-probe"
        assert set(executable_map) == {"tool"}
        clone = executable_map["tool"]
        assert clone.name == "tool"
        assert clone.parent.name == "bin"
        assert clone.is_symlink()
        assert clone.resolve() == target
        return SimpleNamespace(
            fresh_pid=222,
            output_sha256="b" * 64,
            launch_paths=(str(clone), str(clone)),
            launch_realpaths=(str(target), str(target)),
        )

    canaries = SimpleNamespace(
        PROBES={"tool-probe": object()},
        resolve_managed_executables=lambda _seeds: {"tool": target},
        installed_paths=installed_paths,
        file_digest=lambda _paths: "d" * 64,
        repeat_probe=repeat_probe,
    )
    monkeypatch.setattr(module, "load_module", lambda _name, path: canaries if path == module.CANARY_SCRIPT else None)
    monkeypatch.setattr(module, "public_entrypoints", lambda _seed: [entrypoint])
    journal_path = tmp_path / "journal.json"

    def write_transcript(_artifact_id, payload):
        transcript_payloads.append(payload)
        return "evidence.json", "c" * 64

    monkeypatch.setattr(module, "write_transcript", write_transcript)
    rows = {
        ("artifact", "install"): {
            "package_id": "standalone:tool",
            "installed_digest": "d" * 64,
        },
        ("artifact", "identity"): {
            "source_commit_sha": "1" * 40,
            "resolved_version": "1.0.0",
        },
    }
    journal = {"artifacts": []}

    receipt, record = module.rehearse_artifact(
        "artifact",
        {
            "package_manager": "standalone",
            "package_name": "tool",
            "executables": ["tool"],
            "source_commit_sha": "1" * 40,
            "version": "1.0.0",
        },
        "tool-probe",
        "https://example.invalid/tool",
        rows,
        journal,
        journal_path,
    )

    assert len(installed_maps) == 2
    assert all(mapping == {"tool": target} for mapping in installed_maps)
    assert receipt["restored_use_launch_paths"] == record["restored_use_launch_paths"]
    assert receipt["restored_use_launch_realpaths"] == [str(target), str(target)]
    assert receipt["restored_executable_map"]["tool"]["realpath"] == str(target)
    assert all(path != str(entrypoint) for path in receipt["restored_use_launch_paths"])
    assert transcript_payloads[0]["restored_use_launch_paths"] == receipt["restored_use_launch_paths"]
    assert receipt["transcript_sha256"] == "c" * 64


def _configure_main_transaction(monkeypatch, tmp_path: Path, module):
    receipts = tmp_path / "runtime-activation-receipts.json"
    state = tmp_path / "state"
    lock = state / "locks" / "cli-rollback.lock"
    entrypoint = tmp_path / "tool"
    entrypoint.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    entrypoint.chmod(0o755)
    seed = {"package_manager": "standalone", "package_name": "tool"}
    monkeypatch.setattr(module, "RECEIPTS", receipts)
    monkeypatch.setattr(module, "RUNTIME_STATE", state)
    monkeypatch.setattr(module, "LOCK_PATH", lock)
    monkeypatch.setattr(
        module,
        "candidate_artifacts",
        lambda: [("artifact", seed, "tool-probe", "https://example.invalid/tool")],
    )
    monkeypatch.setattr(module, "public_entrypoints", lambda _seed: [entrypoint])
    monkeypatch.setattr(sys, "argv", ["rehearse_candidate_cli_rollback.py", "--apply"])
    return receipts, state


def _fake_rehearsal_receipt(journal: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    record: dict[str, Any] = {
        "artifact_id": "artifact",
        "transaction_id": "artifact-transaction",
        "status": "passed",
    }
    artifacts = journal["artifacts"]
    assert isinstance(artifacts, list)
    artifacts.append(record)
    return (
        {
            "artifact_id": "artifact",
            "phase": "rollback",
            "transaction_id": "artifact-transaction",
        },
        record,
    )


def test_main_writes_success_marker_only_after_receipt_commit(monkeypatch, tmp_path: Path, capsys) -> None:
    module = _module()
    receipts, _state = _configure_main_transaction(monkeypatch, tmp_path, module)
    monkeypatch.setattr(
        module,
        "rehearse_artifact",
        lambda _artifact_id, _seed, _probe, _url, _rows, journal, _path: _fake_rehearsal_receipt(journal),
    )

    assert module.main() == 0

    output = json.loads(capsys.readouterr().out)
    marker = json.loads(Path(output["commit_marker"]).read_text(encoding="utf-8"))
    journal = json.loads(Path(output["journal_path"]).read_text(encoding="utf-8"))
    receipt_document = json.loads(receipts.read_text(encoding="utf-8"))
    rollback_receipt = next(row for row in receipt_document["receipts"] if row["phase"] == "rollback")
    assert journal["status"] == "commit-pending"
    assert marker["status"] == "passed"
    assert marker["artifact_ids"] == ["artifact"]
    assert marker["receipt_store_transaction_id"] == rollback_receipt["store_transaction_id"]
    assert marker["receipt_revision"] == receipt_document["revision"]


def test_main_cas_conflict_preserves_concurrent_row_and_writes_no_success_marker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _module()
    receipts, state = _configure_main_transaction(monkeypatch, tmp_path, module)

    def conflict_rehearsal(_artifact_id, _seed, _probe, _url, _rows, journal, _path):
        store = module.ReceiptStore(receipts, state)
        snapshot = store.snapshot(artifact_keys={("artifact", "rollback")})
        store.commit(
            snapshot,
            artifact_upserts={
                ("artifact", "rollback"): {
                    "artifact_id": "artifact",
                    "phase": "rollback",
                    "transaction_id": "concurrent-transaction",
                }
            },
        )
        return _fake_rehearsal_receipt(journal)

    monkeypatch.setattr(module, "rehearse_artifact", conflict_rehearsal)

    with pytest.raises(ReceiptConflictError):
        module.main()

    receipt_document = json.loads(receipts.read_text(encoding="utf-8"))
    rollback_receipt = next(row for row in receipt_document["receipts"] if row["phase"] == "rollback")
    assert rollback_receipt["transaction_id"] == "concurrent-transaction"
    assert not list((state / "receipts" / "journals" / f"{module.JOURNAL_KIND}-commit").glob("*.json"))
    assert len(list((state / "receipts" / "failures" / f"{module.JOURNAL_KIND}-commit").glob("*.json"))) == 1


def test_main_marker_write_failure_leaves_committed_receipt_fail_closed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _module()
    receipts, state = _configure_main_transaction(monkeypatch, tmp_path, module)
    monkeypatch.setattr(
        module,
        "rehearse_artifact",
        lambda _artifact_id, _seed, _probe, _url, _rows, journal, _path: _fake_rehearsal_receipt(journal),
    )
    original_write = module.ReceiptStore.write_immutable_json

    def fail_success_marker(self, *, kind, transaction_id, payload, failure=False, bucket=None):
        if kind == f"{module.JOURNAL_KIND}-commit" and not failure:
            raise OSError("simulated marker write failure")
        return original_write(
            self,
            kind=kind,
            transaction_id=transaction_id,
            payload=payload,
            failure=failure,
            bucket=bucket,
        )

    monkeypatch.setattr(module.ReceiptStore, "write_immutable_json", fail_success_marker)

    with pytest.raises(OSError, match="simulated marker write failure"):
        module.main()

    receipt_document = json.loads(receipts.read_text(encoding="utf-8"))
    assert any(row["phase"] == "rollback" for row in receipt_document["receipts"])
    assert not list((state / "receipts" / "journals" / f"{module.JOURNAL_KIND}-commit").glob("*.json"))
