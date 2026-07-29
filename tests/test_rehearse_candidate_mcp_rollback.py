from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "_rehearse_candidate_mcp_rollback",
        ROOT / "scripts/rehearse_candidate_mcp_rollback.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_rollback_matrix_accounts_for_local_and_blocked_mcps() -> None:
    module = _module()
    artifacts = module.candidate_artifacts()
    plan = module.rollback_plan()

    assert len(artifacts) == module.EXPECTED_ARTIFACT_COUNT == 17
    assert len({artifact_id for artifact_id, _name, _seed in artifacts}) == 17
    assert sum(item["status"] == "ready" for item in plan) == module.EXPECTED_REHEARSABLE_ARTIFACT_COUNT == 15
    blockers = {item["mcp_server"]: item["blocker"] for item in plan if item["status"] == "blocked"}
    assert blockers == {
        "langfuse-mcp": "credentialed-runtime-probe-prohibited",
        "papersflow": "hosted-oauth-runtime-unavailable",
    }
    assert all(item["network_action_required"] for item in plan if item["status"] == "blocked")


def test_candidate_artifacts_reject_duplicate_runtime_ids(monkeypatch) -> None:
    module = _module()

    class Activation:
        @staticmethod
        def runtime_specs():
            return {
                "https://example.invalid/one": [{"kind": "mcp", "mcp_server": "one"}],
                "https://example.invalid/two": [{"kind": "mcp", "mcp_server": "two"}],
            }

        @staticmethod
        def artifact_id(_url, _seed):
            return "duplicate"

    monkeypatch.setattr(module, "EXPECTED_ARTIFACT_COUNT", 2)
    monkeypatch.setattr(module, "load_module", lambda *_args: Activation)

    with pytest.raises(ValueError, match="must be unique"):
        module.candidate_artifacts()


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


def test_transcript_writer_uses_transaction_scoped_path(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    monkeypatch.setattr(module, "RUNTIME_STATE", tmp_path / "state")
    payload = {
        "artifact_id": "artifact",
        "transaction_id": "transaction1",
        "status": "passed",
    }

    relative, digest = module.write_transcript("artifact", payload)

    path = Path(relative)
    assert path.name == "artifact-transaction1.json"
    assert path.parent == tmp_path / "state" / "receipts" / "transcripts" / module.JOURNAL_KIND
    assert digest == module.hashlib.sha256(path.read_bytes()).hexdigest()


def test_stale_running_journal_is_recovered_as_immutable_failure(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    runtime_state = tmp_path / "state"
    receipts = tmp_path / "receipts.json"
    receipts.write_text(
        json.dumps({"version": 2, "revision": 0, "receipts": [], "closure_receipts": []}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "RUNTIME_STATE", runtime_state)
    staging = runtime_state / "receipts/.staging" / module.JOURNAL_KIND / "transaction1.json"
    staging.parent.mkdir(parents=True)
    staging.write_text(
        json.dumps({
            "version": 2,
            "transaction_id": "transaction1",
            "kind": "mcp",
            "status": "running",
            "artifacts": [
                {
                    "artifact_id": "artifact",
                    "mcp_server": "server",
                    "transaction_id": "artifacttransaction",
                    "status": "running",
                }
            ],
        })
        + "\n",
        encoding="utf-8",
    )

    recovered = module.recover_stale_staging(module.ReceiptStore(receipts, runtime_state))

    assert recovered == ["transaction1"]
    assert not staging.exists()
    failure = runtime_state / "receipts/failures" / module.JOURNAL_KIND / "transaction1.json"
    payload = json.loads(failure.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["error_type"] == "InterruptedRollback"
    assert payload["artifacts"][0]["status"] == "failed"
    assert payload["artifacts"][0]["error_type"] == "InterruptedRollback"


def test_failed_artifact_is_attributed_before_transaction_abort(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    staging = tmp_path / "staging.json"
    journal = {"artifacts": []}

    def fail(*_args):
        raise TimeoutError("probe timeout")

    monkeypatch.setattr(module, "rehearse_artifact", fail)

    with pytest.raises(TimeoutError, match="probe timeout"):
        module.rehearse_journaled_artifact(
            "artifact",
            "mcp-dashboards",
            {},
            {},
            "transaction1",
            journal,
            staging,
        )

    assert journal["artifacts"] == [
        {
            "artifact_id": "artifact",
            "mcp_server": "mcp-dashboards",
            "transaction_id": "transaction1",
            "status": "failed",
            "error_type": "TimeoutError",
        }
    ]
    assert json.loads(staging.read_text(encoding="utf-8"))["artifacts"] == journal["artifacts"]


def test_restored_canary_consumes_hardened_negative_and_shutdown_evidence(
    monkeypatch,
) -> None:
    module = _module()
    monkeypatch.setattr(
        module.anyio,
        "run",
        lambda *_args: (
            222,
            "a" * 64,
            "b" * 64,
            "c" * 64,
            "failure-tool",
            "denial-tool",
            "tool-error",
            "mcp-sdk-bounded-process-group-shutdown",
            "/tmp/isolated/server",
            "/tmp/isolated/server",
        ),
    )

    result = module.restored_canary(
        "server",
        SimpleNamespace(execute_once=object()),
        SimpleNamespace(),
    )

    assert result == (222, "a" * 64, "/tmp/isolated/server", "/tmp/isolated/server")


def test_mcp_receipt_binds_isolated_absence_restored_use_and_transcript(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    live_root = tmp_path / "live"
    live_root.mkdir()
    target = live_root / "server-target"
    target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    target.chmod(0o755)
    entrypoint = live_root / "server"
    entrypoint.symlink_to(target)
    install_root = tmp_path / "install"
    install_root.mkdir()

    @dataclass(frozen=True)
    class Probe:
        executable: Path

    cli_helpers = SimpleNamespace(file_digest=lambda _paths: "d" * 64)
    canaries = SimpleNamespace(
        PROBES={"server": Probe(entrypoint)},
        installed_paths=lambda _seed, _helpers: [install_root],
    )

    class RollbackHelpers:
        @staticmethod
        def public_entrypoints(_seed):
            return [entrypoint]

        @staticmethod
        def surface_snapshot(paths):
            return {str(path): {"kind": "symlink", "target": str(path.resolve())} for path in paths}

        @staticmethod
        def rehearse_isolated_surface(paths, names, isolated_bin, transaction_id):
            assert paths == [entrypoint]
            assert names == ["server"]
            assert transaction_id == "transaction"
            isolated_bin.mkdir(parents=True)
            clone = isolated_bin / "server"
            clone.symlink_to(target)
            live = RollbackHelpers.surface_snapshot(paths)
            return {
                "clones": [clone],
                "live_preimage": live,
                "live_entrypoint_digest": "e" * 64,
                "preimage_digest": "f" * 64,
                "rollback_digest": "f" * 64,
                "fresh_absence": {"server": None},
                "fresh_absence_process_id": 111,
                "fresh_absence_output_sha256": "a" * 64,
            }

        @staticmethod
        def validate_process_evidence(absence_pid, restored_pid, absence_digest, restored_digest):
            assert (absence_pid, restored_pid) == (111, 222)
            assert (absence_digest, restored_digest) == ("a" * 64, "b" * 64)

    def fake_load(_name, path):
        if path == module.CLI_CANARY_SCRIPT:
            return cli_helpers
        if path == module.MCP_CANARY_SCRIPT:
            return canaries
        if path == module.CLI_ROLLBACK_SCRIPT:
            return RollbackHelpers
        raise AssertionError(path)

    def fake_restored(_name, _canaries, probe):
        assert probe.executable.parent.name == "bin"
        assert probe.executable.resolve() == target
        return 222, "b" * 64, str(probe.executable), str(probe.executable.resolve())

    monkeypatch.setattr(module, "load_module", fake_load)
    monkeypatch.setattr(module, "restored_canary", fake_restored)
    monkeypatch.setattr(module, "write_transcript", lambda _artifact, _payload: ("evidence.json", "c" * 64))
    rows = {
        ("artifact", "install"): {
            "package_id": "uv-tool:server",
            "installed_digest": "d" * 64,
        },
        ("artifact", "identity"): {
            "source_commit_sha": "1" * 40,
            "resolved_version": "1.0.0",
        },
    }
    journal = {"artifacts": []}

    receipt = module.rehearse_artifact(
        "artifact",
        "server",
        {
            "executables": ["server"],
            "source_commit_sha": "1" * 40,
            "version": "1.0.0",
        },
        rows,
        "transaction",
        journal,
    )

    assert receipt["rehearsal_kind"] == module.REHEARSAL_KIND
    assert receipt["live_entrypoint_unchanged"] is True
    assert receipt["fresh_absence_process_id"] == 111
    assert receipt["fresh_absence_output_sha256"] == "a" * 64
    assert receipt["restored_use_process_id"] == 222
    assert receipt["restored_use_output_sha256"] == "b" * 64
    assert Path(receipt["restored_use_launch_path"]).parent.name == "bin"
    assert receipt["restored_use_launch_realpath"] == str(target)
    assert receipt["transcript_sha256"] == "c" * 64
    assert journal["artifacts"][0]["transaction_id"] == "transaction"
    assert journal["artifacts"][0]["restored_use_launch_path"] == receipt["restored_use_launch_path"]
    assert journal["artifacts"][0]["status"] == "passed"
