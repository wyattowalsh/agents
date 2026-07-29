from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "_rehearse_candidate_plugin_rollback",
        ROOT / "scripts" / "rehearse_candidate_plugin_rollback.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_content_digest_is_install_root_independent(tmp_path: Path) -> None:
    module = _module()
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "SKILL.md").write_text("same\n", encoding="utf-8")
    (second / "SKILL.md").write_text("same\n", encoding="utf-8")

    assert module.content_digest(first) == module.content_digest(second)


def test_content_digest_detects_plugin_byte_changes(tmp_path: Path) -> None:
    module = _module()
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    skill = plugin / "SKILL.md"
    skill.write_text("one\n", encoding="utf-8")
    before = module.content_digest(plugin)
    skill.write_text("two\n", encoding="utf-8")

    assert module.content_digest(plugin) != before


def test_content_digest_detects_mode_and_rejects_directory_symlinks(tmp_path: Path) -> None:
    module = _module()
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    executable = plugin / "probe.sh"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    first_target = plugin / "first"
    second_target = plugin / "second"
    first_target.mkdir()
    second_target.mkdir()
    before = module.content_digest(plugin)

    executable.chmod(0o755)
    after_mode = module.content_digest(plugin)
    assert after_mode != before

    link = plugin / "current"
    link.symlink_to(second_target.name, target_is_directory=True)
    with pytest.raises(ValueError, match="contains a symlink"):
        module.content_digest(plugin)


def test_content_digest_includes_runtime_cache(tmp_path: Path) -> None:
    module = _module()
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    (plugin / "SKILL.md").write_text("stable\n", encoding="utf-8")
    before = module.content_digest(plugin)
    cache = plugin / "__pycache__"
    cache.mkdir()
    (cache / "probe.pyc").write_bytes(b"runtime")

    assert module.content_digest(plugin) != before


def test_isolated_env_uses_sanitized_temporary_homes(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    canaries = module.load_module("_candidate_plugin_canaries_env_test", module.CANARY_SCRIPT)
    monkeypatch.setenv("ROLLBACK_TEST_API_KEY", "do-not-copy")

    env = module.isolated_env(canaries, tmp_path)

    assert env["CODEX_HOME"] == str(tmp_path / "codex")
    assert env["HOME"] == str(tmp_path / "home")
    assert "ROLLBACK_TEST_API_KEY" not in env


def test_marketplace_roots_cover_every_enabled_plugin() -> None:
    module = _module()
    canaries = module.load_module("_candidate_plugin_canaries_marketplace_test", module.CANARY_SCRIPT)
    marketplaces = {plugin_id.rsplit("@", 1)[1] for plugin_id in canaries.EXPECTED_ENABLED_PLUGINS}

    assert marketplaces == set(module.MARKETPLACE_ROOTS)


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

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["closure_receipts"] == [{"gate_id": "docs-closure"}]


def test_apply_requires_explicit_model_execution_authorization(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _module()
    plugin_id = "unslop@awesome-codex-plugins"
    url = "https://example.invalid/unslop"
    seed = {
        "plugin_id": plugin_id,
        "plugin_enabled": True,
        "package_manager": "codex-plugin",
        "version": "1.0.0",
    }
    live_root = tmp_path / "plugin"
    live_root.mkdir()

    class Canaries:
        EXPECTED_ENABLED_PLUGINS = frozenset({plugin_id})

        @staticmethod
        def activation_module():
            return type("Activation", (), {"artifact_id": staticmethod(lambda _url, _seed: "artifact")})()

        @staticmethod
        def all_plugin_specs():
            return {plugin_id: (url, seed)}

        @staticmethod
        def enabled_plugin_specs(specs=None):
            return {plugin_id: (url, seed)}

        @staticmethod
        def verified_provenance_lock(_specs):
            return {plugin_id: {"plugin_id": plugin_id}}

        @staticmethod
        def marketplace_plugin_source(_plugin_id, _marketplace_root, _provenance):
            return live_root

        @staticmethod
        def verify_marketplace_checkout(_root, _provenance):
            return None

        @staticmethod
        def verify_plugin_content(_root, _provenance, *, label):
            assert label
            return "a" * 64

        @staticmethod
        def codex_plugin_live_state(*_args):
            return {
                "plugin_id": plugin_id,
                "version": "1.0.0",
                "enabled": True,
                "installed": True,
                "installed_path": str(live_root),
            }

        HOST_CODEX_HOME = tmp_path / "codex-home"
        CODEX_CACHE = tmp_path / "codex-cache"

        @staticmethod
        def plugin_root(_seed):
            return live_root

        @staticmethod
        def execution_requirements(_plugin_id):
            return {"model_execution": True, "audited_execution": True}

        @staticmethod
        def execution_authorized(
            _plugin_id,
            *,
            allow_model_execution,
            allow_audited_execution,
        ):
            return allow_model_execution and allow_audited_execution

    monkeypatch.setattr(module, "load_module", lambda *_args: Canaries)
    monkeypatch.setattr(module, "LOCK_PATH", tmp_path / "must-not-be-created.lock")
    monkeypatch.setattr(sys, "argv", ["rehearse_candidate_plugin_rollback.py", "--apply", "--plugin", plugin_id])

    assert module.main() == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["mode"] == "execution-required"
    assert payload["pending_execution"][0]["plugin_id"] == plugin_id
    assert not module.LOCK_PATH.exists()


def test_bind_final_journal_sha_updates_every_pending_receipt(tmp_path: Path) -> None:
    module = _module()
    journal = tmp_path / "journal.json"
    journal.write_text('{"status":"passed"}\n', encoding="utf-8")
    pending = {
        ("first", "rollback"): {"artifact_id": "first", "phase": "rollback"},
        ("second", "rollback"): {"artifact_id": "second", "phase": "rollback"},
    }

    digest = module.bind_final_journal_sha(pending, journal)

    assert digest == module.hashlib.sha256(journal.read_bytes()).hexdigest()
    assert {receipt["journal_sha256"] for receipt in pending.values()} == {digest}


def test_transaction_artifact_sets_reject_duplicates_and_drift() -> None:
    module = _module()

    assert module.require_exact_artifact_sets(
        ["second", "first"],
        ["first", "second"],
        ["second", "first"],
    ) == ["first", "second"]
    with pytest.raises(ValueError, match="must be unique"):
        module.require_exact_artifact_sets(["same", "same"], ["same", "same"], ["same", "same"])
    with pytest.raises(RuntimeError, match="sets do not match"):
        module.require_exact_artifact_sets(["first", "second"], ["first"], ["first", "second"])


def test_rollback_receipt_is_bound_to_identity_processes_and_transcript(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    state = tmp_path / "state"
    monkeypatch.setattr(module, "RUNTIME_STATE", state)
    transaction_id = "transaction1"
    transcript = state / "receipts" / "transcripts" / module.JOURNAL_KIND / f"artifact-{transaction_id}.json"
    process_ids = dict(zip(module.PROCESS_ID_FIELDS, range(100, 110), strict=True))
    process_ids["restore"] = process_ids["remove"]
    process_ids["restored_use_discovery"] = process_ids["restored_use_initial"]
    launch_evidence = {
        phase: {
            "launch_id": f"{index + 1:032x}",
            "started_at_ns": 1_000_000 + index,
            "process_id": process_ids[phase],
        }
        for index, phase in enumerate(module.PROCESS_ID_FIELDS)
    }
    launch_evidence["restored_use_discovery"] = dict(launch_evidence["restored_use_initial"])
    transcript_payload = {
        "artifact_id": "artifact",
        "plugin_id": "plugin@marketplace",
        "transaction_id": transaction_id,
        "process_ids": process_ids,
        "launch_evidence": launch_evidence,
        "live_install_unchanged": True,
    }
    module.atomic_json(transcript, transcript_payload)
    receipt: dict[str, Any] = {
        "artifact_id": "artifact",
        "phase": "rollback",
        "plugin_id": "plugin@marketplace",
        "plugin_scope": module.PLUGIN_SCOPE,
        "scope": module.ROLLBACK_SCOPE,
        "rehearsal_kind": module.REHEARSAL_KIND,
        "live_install_unchanged": True,
        "digest_algorithm": module.DIGEST_ALGORITHM,
        "digest_ignored_dirs": sorted(module.DIGEST_IGNORED_DIRS),
        "process_ids": process_ids,
        "launch_evidence": launch_evidence,
        "restored_use_output_sha256": "a" * 64,
        "preimage_digest": "before",
        "rollback_digest": "before",
        "restored_installed_digest": "before",
        "transaction_id": transaction_id,
        "transcript_path": str(transcript),
        "transcript_sha256": module.hashlib.sha256(transcript.read_bytes()).hexdigest(),
    }

    module.validate_rollback_receipt(
        receipt,
        expected_artifact_id="artifact",
        expected_plugin_id="plugin@marketplace",
    )

    wrong_plugin = dict(receipt, plugin_id="other@marketplace")
    with pytest.raises(RuntimeError, match="wrong plugin id"):
        module.validate_rollback_receipt(
            wrong_plugin,
            expected_artifact_id="artifact",
            expected_plugin_id="plugin@marketplace",
        )

    duplicate_launch_evidence = {phase: dict(value) for phase, value in launch_evidence.items()}
    duplicate_launch_evidence["restore"]["launch_id"] = duplicate_launch_evidence["remove"]["launch_id"]
    reused = dict(receipt, launch_evidence=duplicate_launch_evidence)
    with pytest.raises(RuntimeError, match="reused a launch identity"):
        module.validate_rollback_receipt(
            reused,
            expected_artifact_id="artifact",
            expected_plugin_id="plugin@marketplace",
        )

    transcript.write_text("{}\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="transcript digest is stale"):
        module.validate_rollback_receipt(
            receipt,
            expected_artifact_id="artifact",
            expected_plugin_id="plugin@marketplace",
        )
