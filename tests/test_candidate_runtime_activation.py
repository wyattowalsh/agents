from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import wagents.process_lifecycle as process_lifecycle

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "_candidate_runtime_activation",
        ROOT / "scripts" / "record_candidate_runtime_activation.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _script_module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_behavioral_receipt_regeneration_requires_lifecycle_gate(monkeypatch, tmp_path: Path) -> None:
    for index, (name, relative_path) in enumerate((
        ("_candidate_cli_lifecycle_gate", "scripts/run_candidate_cli_canaries.py"),
        ("_candidate_plugin_lifecycle_gate", "scripts/run_candidate_plugin_canaries.py"),
    )):
        module = _script_module(name, relative_path)
        receipt_root = tmp_path / str(index)
        receipt_root.mkdir()
        receipt_path = receipt_root / "receipts.json"
        receipt_path.write_text(
            json.dumps({
                "version": 2,
                "revision": 0,
                "receipts": [{"artifact_id": "existing", "phase": "behavior"}],
                "closure_receipts": [],
            })
            + "\n",
            encoding="utf-8",
        )
        before = receipt_path.read_bytes()
        monkeypatch.setattr(module, "RECEIPTS", receipt_path)
        monkeypatch.setattr(module, "RUNTIME_STATE", receipt_root / "state")
        monkeypatch.setattr(
            module,
            "run_after_process_lifecycle_gate",
            lambda _operation: (_ for _ in ()).throw(RuntimeError("fresh lifecycle proof failed")),
        )
        monkeypatch.setattr(
            module.ReceiptStore,
            "commit",
            lambda *_args, **_kwargs: pytest.fail("receipt commit ran after lifecycle proof failed"),
        )

        with pytest.raises(RuntimeError, match="fresh lifecycle proof failed"):
            module.write_receipts({
                ("new", "behavior"): {"artifact_id": "new", "phase": "behavior"},
            })
        assert receipt_path.read_bytes() == before


def test_process_lifecycle_gate_runs_exact_regressions_and_rejects_stale_proof(monkeypatch) -> None:
    captured_command: list[str] = []
    captured_kwargs: dict[str, object] = {}

    def run(command, **kwargs):
        captured_command.extend(command)
        captured_kwargs.update(kwargs)
        return subprocess.CompletedProcess(command, 0, "4 passed\n", "")

    monkeypatch.setattr(process_lifecycle.subprocess, "run", run)
    proof = process_lifecycle.require_process_lifecycle_gate()

    assert captured_command[-4:] == list(process_lifecycle.LIFECYCLE_GATE_NODE_IDS)
    assert captured_kwargs == {
        "cwd": process_lifecycle.ROOT,
        "text": True,
        "capture_output": True,
        "check": False,
        "timeout": process_lifecycle.LIFECYCLE_GATE_TIMEOUT_SECONDS,
    }
    process_lifecycle.validate_process_lifecycle_proof(proof)
    with pytest.raises(RuntimeError, match="sources changed after proof"):
        process_lifecycle.validate_process_lifecycle_proof(
            process_lifecycle.ProcessLifecycleProof(source_digests=(("stale", "0" * 64),))
        )


def test_expected_binding_metadata_recomputes_content_addressed_fields(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _module()
    selector_id = "selector:https://example.invalid/repo:example"
    row = {
        "normalized_url": "https://example.invalid/repo",
        "skill_name": "example",
        "install_skill_name": "example",
        "target_agents": ["codex"],
        "installed_paths": ["~/.agents/skills/example"],
        "install_source": "example/repo",
        "install_command": "npx skills add example/repo --skill example",
        "status": "install-now",
        "trust_tier": "curated",
        "provenance_status": "verified",
        "selector_mode": "named",
        "sync_kind": "skills-cli",
        "audited_head": "a" * 40,
        "path": "docs/src/authoring/skills/example.mdx",
    }
    authoring = tmp_path / "docs/src/authoring/skills/example.mdx"
    authoring.parent.mkdir(parents=True)
    authoring.write_text("---\nname: example\n---\n", encoding="utf-8")
    sync_sha = "b" * 64
    catalog_row = {"name": "example", "useCommand": "/example"}
    captured: dict[str, object] = {}

    def binding_input_digest(_item, **kwargs):
        captured.update(kwargs)
        return "d" * 64

    closure_module = SimpleNamespace(
        selector_graph=lambda _rows: {
            selector_id: {
                **row,
                "selector_id": selector_id,
                "path": "docs/src/authoring/skills/example.mdx",
            }
        },
        catalog_rows_by_name=lambda: {"example": catalog_row},
        required_capabilities=lambda _item, _catalog: (["invoke:/example"], []),
        current_installed_digest=lambda _item: ("c" * 64, []),
        binding_input_digest=binding_input_digest,
    )

    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(
        module,
        "load_json",
        lambda path: {"overrides": [row]} if path.name == "promotion-overrides.json" else {"source_sha256": sync_sha},
    )
    monkeypatch.setattr(module, "load_catalog_closure_module", lambda: closure_module)

    metadata, harnesses = module.expected_binding_metadata({"gate_id": "harness-binding-closure"})

    assert harnesses == ["codex"]
    assert metadata[f"binding:{selector_id}:codex"] == {
        "selector_id": selector_id,
        "normalized_url": row["normalized_url"],
        "skill_name": "example",
        "agent": "codex",
        "input_digest": "d" * 64,
        "installed_digest": "c" * 64,
        "required_capabilities": ["invoke:/example"],
    }
    assert captured["sync_report_sha256"] == sync_sha


def test_runtime_activation_reopens_all_65_artifacts(monkeypatch) -> None:
    module = _module()
    monkeypatch.setattr(module, "load_receipt_document", lambda: {"receipts": [], "closure_receipts": []})

    payload = module.build_assurance()

    assert payload["source_target_count"] == 289
    assert payload["runtime_artifact_count"] == 65
    assert payload["minimum_runtime_artifact_count"] == 65
    assert payload["totals"]["kind_counts"] == {"cli": 30, "library": 1, "mcp": 17, "plugin": 17}
    assert payload["requested_full_usability"] is False
    assert payload["totals"]["active_blocker_count"] == 65


def test_runtime_activation_does_not_import_path_or_config_evidence(monkeypatch) -> None:
    module = _module()
    monkeypatch.setattr(module, "load_receipt_document", lambda: {"receipts": [], "closure_receipts": []})

    payload = module.build_assurance()

    assert all(item["status"] == "incomplete" for item in payload["artifacts"])
    assert all(any("missing behavior receipt" in error for error in item["errors"]) for item in payload["artifacts"])


def test_runtime_activation_structural_gate_rejects_false_complete() -> None:
    module = _module()
    payload = {
        "source_target_count": 289,
        "runtime_artifact_count": 65,
        "minimum_runtime_artifact_count": 65,
        "artifacts": [{"artifact_id": f"a-{index}", "status": "incomplete"} for index in range(65)],
        "requested_full_usability": True,
        "active_blockers": [],
        "closure_gates": {
            gate_id: {"status": "incomplete", "errors": ["missing"]} for gate_id in module.REQUIRED_CLOSURE_GATES
        },
    }

    assert "full usability cannot be true with incomplete artifacts" in module.structural_errors(payload)


def test_runtime_activation_rejects_complete_receipts_for_disabled_plugin(monkeypatch) -> None:
    module = _module()
    url = "https://github.com/charleswiltgen/axiom"
    seed = next(item for item in module.runtime_specs()[url] if item.get("kind") == "plugin")
    candidate_id = module.artifact_id(url, seed)
    monkeypatch.setattr(
        module,
        "load_receipts",
        lambda _payload=None: {candidate_id: {phase: {} for phase, _predicate in module.PHASE_PREDICATES}},
    )
    monkeypatch.setattr(module, "evaluate_predicate", lambda *args, **kwargs: [])

    payload = module.build_assurance()
    artifact = next(item for item in payload["artifacts"] if item["artifact_id"] == candidate_id)

    assert artifact["plugin_enabled"] is False
    assert artifact["status"] == "incomplete"
    assert "activation-policy: plugin is not enabled in the target harness" in artifact["errors"]


def test_mcp_activation_requires_registry_generated_live_and_reachability_evidence() -> None:
    module = _module()

    errors, reachable = module.mcp_activation_errors(
        "candidate",
        {"enabled": False},
        {"enabled": False},
        {"enabled": False},
        None,
    )

    assert reachable is False
    assert errors == [
        "MCP server is not enabled in config/mcp-registry.json",
        "MCP server is not enabled in generated MCPHub settings",
        "MCP server is not enabled in the live MCPHub settings",
    ]


def test_mcp_activation_treats_present_projected_entries_as_enabled_by_default() -> None:
    module = _module()
    registry = {"enabled": True, "command": "candidate", "tools": ["candidate_tool"]}
    generated = {"command": "candidate"}
    live = {"command": "candidate"}
    tools = ["candidate-candidate_tool"]
    projection = module.normalized_projection(registry, registry=True)
    configured_tools = ["candidate_tool"]
    receipt = {
        "phase": "activation",
        "status": "passed",
        "mcp_server": "candidate",
        "registry_enabled": True,
        "generated_enabled": True,
        "live_enabled": True,
        "mcphub_reachable": True,
        "endpoint": "http://127.0.0.1:46683/mcp/candidate",
        "registry_entry_sha256": module.canonical_json_sha256(registry),
        "generated_entry_sha256": module.canonical_json_sha256(generated),
        "live_entry_sha256": module.canonical_json_sha256(live),
        "registry_projection_sha256": module.canonical_json_sha256(projection),
        "generated_projection_sha256": module.canonical_json_sha256(projection),
        "live_projection_sha256": module.canonical_json_sha256(projection),
        "configured_tool_names": configured_tools,
        "configured_tool_names_sha256": module.canonical_json_sha256(configured_tools),
        "configured_tools_allow_all": False,
        "tool_count": len(tools),
        "tool_names": tools,
        "tool_names_sha256": module.canonical_json_sha256(tools),
        "bearer_auth_used": True,
        "mcphub_bearer_key_configured": True,
        "unauthenticated_denied": True,
        "unauthenticated_status_code": 401,
        "network_probe_performed": True,
        "secret_value_recorded": False,
    }

    errors, reachable = module.mcp_activation_errors(
        "candidate",
        registry,
        generated,
        live,
        receipt,
    )

    assert errors == []
    assert reachable is True
    assert module.projected_mcp_enabled(None) is False
    assert module.projected_mcp_enabled({"enabled": False}) is False


def test_mcp_activation_rejects_stale_config_and_tool_evidence() -> None:
    module = _module()
    registry = {"enabled": True}
    generated = {"command": "candidate"}
    live = {"command": "candidate"}
    receipt = {
        "phase": "activation",
        "status": "passed",
        "mcp_server": "candidate",
        "registry_enabled": True,
        "generated_enabled": True,
        "live_enabled": True,
        "mcphub_reachable": True,
        "endpoint": "http://127.0.0.1:46683/mcp/candidate",
        "registry_entry_sha256": module.canonical_json_sha256({"enabled": False}),
        "generated_entry_sha256": module.canonical_json_sha256(generated),
        "live_entry_sha256": module.canonical_json_sha256(live),
        "tool_count": 2,
        "tool_names": ["duplicate", "duplicate"],
        "tool_names_sha256": "0" * 64,
        "bearer_auth_used": True,
        "secret_value_recorded": False,
    }

    errors, reachable = module.mcp_activation_errors(
        "candidate",
        registry,
        generated,
        live,
        receipt,
    )

    assert reachable is False
    assert "MCPHub reachability receipt registry_entry_sha256 is stale" in errors
    assert "MCPHub reachability receipt tool_names must be a nonempty sorted unique list" in errors


@pytest.mark.parametrize(
    "observed_tools",
    (
        ["required_tool"],
        ["other-required_tool"],
        ["evil-candidate-required_tool"],
    ),
)
def test_mcp_activation_rejects_missing_configured_tool_and_auth_denial(
    observed_tools: list[str],
) -> None:
    module = _module()
    registry = {"enabled": True, "tools": ["required_tool"]}
    generated = {"enabled": True}
    live = {"enabled": True}
    projection = module.normalized_projection(registry, registry=True)
    configured_tools = ["required_tool"]
    receipt = {
        "phase": "activation",
        "status": "passed",
        "mcp_server": "candidate",
        "registry_enabled": True,
        "generated_enabled": True,
        "live_enabled": True,
        "mcphub_reachable": True,
        "endpoint": "http://127.0.0.1:46683/mcp/candidate",
        "registry_entry_sha256": module.canonical_json_sha256(registry),
        "generated_entry_sha256": module.canonical_json_sha256(generated),
        "live_entry_sha256": module.canonical_json_sha256(live),
        "registry_projection_sha256": module.canonical_json_sha256(projection),
        "generated_projection_sha256": module.canonical_json_sha256(projection),
        "live_projection_sha256": module.canonical_json_sha256(projection),
        "configured_tool_names": configured_tools,
        "configured_tool_names_sha256": module.canonical_json_sha256(configured_tools),
        "configured_tools_allow_all": False,
        "tool_count": len(observed_tools),
        "tool_names": observed_tools,
        "tool_names_sha256": module.canonical_json_sha256(observed_tools),
        "bearer_auth_used": True,
        "mcphub_bearer_key_configured": True,
        "unauthenticated_denied": False,
        "unauthenticated_status_code": 200,
        "network_probe_performed": True,
        "secret_value_recorded": False,
    }

    errors, reachable = module.mcp_activation_errors(
        "candidate",
        registry,
        generated,
        live,
        receipt,
    )

    assert reachable is False
    assert "MCPHub reachability receipt omits configured tools" in errors
    assert "MCPHub reachability receipt did not prove unauthenticated denial" in errors
    assert "MCPHub reachability receipt has an invalid unauthenticated status code" in errors


def test_runtime_specs_track_known_disabled_plugins() -> None:
    module = _module()
    expected_disabled = {
        "axiom@axiom-marketplace",
        "candidate-opencode-plugin-openspec",
        "designer-skill@awesome-codex-plugins",
        "prompt-to-asset@awesome-codex-plugins",
        "remotion@awesome-codex-plugins",
    }
    states = {
        str(item.get("plugin_id")): item.get("plugin_enabled")
        for rows in module.runtime_specs().values()
        for item in rows
        if item.get("kind") == "plugin"
    }

    assert expected_disabled <= states.keys()
    assert all(states[plugin_id] is False for plugin_id in expected_disabled)


def test_committed_runtime_receipts_remain_fail_closed() -> None:
    module = _module()
    payload = module.build_assurance()

    assert sum(payload["totals"]["status_counts"].values()) == 65
    assert payload["requested_full_usability"] is False
    assert set(payload["closure_gates"]) == set(module.REQUIRED_CLOSURE_GATES)
    assert payload["closure_gates"]["global-closure"]["status"] == "incomplete"
    enabled_plugins = [
        item for item in payload["artifacts"] if item["kind"] == "plugin" and item["plugin_enabled"] is True
    ]
    assert len(enabled_plugins) == 8
    receipts = module.load_receipts()
    for item in enabled_plugins:
        if item["status"] == "accepted":
            assert receipts[item["artifact_id"]]["rollback"]["restored_use_status"] == "passed"


def _synthetic_payload(module, *, generated_at: str = "2026-07-17T00:00:00+00:00") -> dict:
    specs = module.runtime_specs()
    artifacts = [
        {
            "artifact_id": module.artifact_id(url, seed),
            "kind": seed["kind"],
            "status": "incomplete",
        }
        for url, rows in sorted(specs.items())
        for seed in rows
    ]
    canonical_ids = sorted(item["artifact_id"] for item in artifacts)
    gates = {
        gate_id: {"predicate": "test", "status": "incomplete", "errors": ["missing"]}
        for gate_id in module.REQUIRED_CLOSURE_GATES
    }
    return {
        "version": 1,
        "generated_at": generated_at,
        "source_target_count": 289,
        "runtime_artifact_count": 65,
        "minimum_runtime_artifact_count": 65,
        "artifacts": artifacts,
        "canonical_runtime_artifact_ids": canonical_ids,
        "closure_gates": gates,
        "requested_full_usability": False,
        "active_blockers": [{"artifact_id": "a-0"}],
    }


def test_canonical_payload_ignores_only_top_level_generated_at() -> None:
    module = _module()
    first = _synthetic_payload(module, generated_at="one")
    second = _synthetic_payload(module, generated_at="two")

    assert module.canonical_payload(first) == module.canonical_payload(second)
    second["artifacts"][0]["recorded_at"] = "two"
    assert module.canonical_payload(first) != module.canonical_payload(second)


def test_check_recomputes_and_rejects_stale_stored_assurance(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    output = tmp_path / "assurance.json"
    current = _synthetic_payload(module)
    stale = _synthetic_payload(module)
    stale["active_blockers"] = [{"artifact_id": "different"}]
    output.write_text(json.dumps(stale), encoding="utf-8")
    monkeypatch.setattr(module, "OUTPUT", output)
    monkeypatch.setattr(module, "build_assurance", lambda: current)
    monkeypatch.setattr(sys, "argv", ["record_candidate_runtime_activation.py", "--check"])

    assert module.main() == 1


def test_check_accepts_generated_at_only_drift(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    output = tmp_path / "assurance.json"
    output.write_text(json.dumps(_synthetic_payload(module, generated_at="stored")), encoding="utf-8")
    monkeypatch.setattr(module, "OUTPUT", output)
    monkeypatch.setattr(module, "build_assurance", lambda: _synthetic_payload(module, generated_at="current"))
    monkeypatch.setattr(sys, "argv", ["record_candidate_runtime_activation.py", "--check"])

    assert module.main() == 0


def test_missing_closure_receipts_prevent_full_usability() -> None:
    module = _module()
    gates = module.build_closure_gates({}, [])

    assert set(gates) == set(module.REQUIRED_CLOSURE_GATES)
    assert all(gate["status"] == "incomplete" for gate in gates.values())


def test_journal_digest_rejects_paths_outside_managed_runtime(tmp_path: Path) -> None:
    module = _module()
    journal = tmp_path / "journal.json"
    journal.write_text('{"status":"passed"}\n', encoding="utf-8")

    digest, errors = module.journal_digest({"journal_path": str(journal)})

    assert digest is None
    assert errors == ["rollback journal must be inside the managed candidate receipt root"]


def test_transcript_digest_binds_cli_and_mcp_launch_evidence(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    receipt_root = tmp_path / "receipts"
    monkeypatch.setattr(module, "RUNTIME_RECEIPT_ROOT", receipt_root)
    cases = (
        (
            "candidate-non-node-cli-rollback",
            {
                "restored_use_launch_paths": ["/tmp/wagents-cli-rollback-artifact-fixture/bin/tool"],
                "restored_use_launch_realpaths": ["/managed/target"],
                "restored_executable_map": {
                    "tool": {
                        "launch_path": "/tmp/wagents-cli-rollback-artifact-fixture/bin/tool",
                        "realpath": "/managed/target",
                    }
                },
            },
        ),
        (
            "candidate-mcp-rollback",
            {
                "restored_use_launch_path": "/tmp/wagents-mcp-entrypoint-rollback-artifact-fixture/bin/tool",
                "restored_use_launch_realpath": "/managed/target",
            },
        ),
    )
    for transcript_kind, launch_evidence in cases:
        transcript = receipt_root / "transcripts" / transcript_kind / "artifact-transaction.json"
        transcript.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "artifact_id": "artifact",
            "transaction_id": "transaction",
            "rehearsal_kind": "isolated-entrypoint-root-detach",
            **launch_evidence,
        }
        transcript.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        receipt = {**payload, "transcript_path": str(transcript)}

        digest, errors = module.transcript_digest(receipt)
        assert digest == module.hashlib.sha256(transcript.read_bytes()).hexdigest()
        assert errors == []

        for field in launch_evidence:
            forged = dict(payload)
            forged[field] = "forged"
            transcript.write_text(json.dumps(forged) + "\n", encoding="utf-8")
            _, errors = module.transcript_digest(receipt)
            assert any(f"{field} does not match" in error for error in errors)


def test_transcript_digest_rejects_managed_path_symlinks(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    receipt_root = tmp_path / "receipts"
    monkeypatch.setattr(module, "RUNTIME_RECEIPT_ROOT", receipt_root)
    outside = tmp_path / "outside.json"
    payload = {
        "artifact_id": "artifact",
        "transaction_id": "transaction",
        "rehearsal_kind": "isolated-entrypoint-root-detach",
        "restored_use_launch_paths": ["/tmp/tool"],
    }
    outside.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    transcript = receipt_root / "transcripts" / "candidate-non-node-cli-rollback" / "artifact-transaction.json"
    transcript.parent.mkdir(parents=True)
    transcript.symlink_to(outside)

    digest, errors = module.transcript_digest({**payload, "transcript_path": str(transcript)})

    assert digest is None
    assert any("unavailable" in error for error in errors)


def test_journal_digest_binds_cli_mcp_and_plugin_records(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    monkeypatch.setattr(module, "RUNTIME_RECEIPT_ROOT", tmp_path)
    common_receipt = {
        "artifact_id": "artifact",
        "rehearsal_kind": "isolated-entrypoint-root-detach",
        "live_entrypoint_paths": ["/managed/tool"],
        "live_entrypoint_digest": "a" * 64,
        "live_entrypoint_unchanged": True,
        "preimage_digest": "b" * 64,
        "rollback_digest": "b" * 64,
        "fresh_absence_process_id": 101,
        "fresh_absence_output_sha256": "c" * 64,
        "restored_use_process_id": 202,
        "restored_use_output_sha256": "d" * 64,
        "transcript_path": "evidence.json",
        "transcript_sha256": "e" * 64,
        "transaction_id": "transaction",
        "journal_transaction_id": "journal-transaction",
        "store_transaction_id": "receipt-store-transaction",
    }
    common_record = {
        "artifact_id": "artifact",
        "rehearsal_kind": "isolated-entrypoint-root-detach",
        "live_entrypoints": ["/managed/tool"],
        "live_entrypoint_digest": "a" * 64,
        "live_entrypoint_unchanged": True,
        "preimage_digest": "b" * 64,
        "rollback_digest": "b" * 64,
        "fresh_absence_process_id": 101,
        "fresh_absence_output_sha256": "c" * 64,
        "transcript_path": "evidence.json",
        "transcript_sha256": "e" * 64,
        "status": "passed",
    }
    plugin_process_ids = {"fresh_absence": 303, "restored_use_fresh": 404}
    plugin_launch_evidence = {"fresh_absence": {"process_id": 303}, "restored_use_fresh": {"process_id": 404}}
    plugin_receipt = {
        "artifact_id": "plugin-artifact",
        "plugin_id": "plugin@marketplace",
        "plugin_scope": "user-global-codex",
        "scope": "isolated-codex-home",
        "rehearsal_kind": "isolated-plugin-root-detach",
        "preimage_digest": "f" * 64,
        "rollback_digest": "f" * 64,
        "promoted_final_digest": "1" * 64,
        "fresh_absence_process_id": 303,
        "restored_use_process_id": 404,
        "restored_use_output_sha256": "2" * 64,
        "restored_installed_digest": "f" * 64,
        "restored_use_status": "passed",
        "live_install_unchanged": True,
        "process_ids": plugin_process_ids,
        "launch_evidence": plugin_launch_evidence,
        "transcript_path": "plugin-evidence.json",
        "transcript_sha256": "3" * 64,
        "transaction_id": "plugin-transaction",
        "journal_transaction_id": "plugin-journal-transaction",
        "store_transaction_id": "plugin-receipt-store-transaction",
    }
    plugin_record = {**plugin_receipt, "status": "passed"}

    cases = [
        (
            "cli",
            "candidate-non-node-cli-rollback",
            {
                **common_receipt,
                "restored_use_launch_paths": ["/tmp/wagents-cli-rollback-artifact-fixture/bin/tool"],
                "restored_use_launch_realpaths": ["/managed/target"],
                "restored_executable_map": {
                    "tool": {
                        "launch_path": "/tmp/wagents-cli-rollback-artifact-fixture/bin/tool",
                        "realpath": "/managed/target",
                    }
                },
            },
            {
                **common_record,
                "transaction_id": "transaction",
                "restored_use_process_id": 202,
                "restored_use_output_sha256": "d" * 64,
                "restored_use_launch_paths": ["/tmp/wagents-cli-rollback-artifact-fixture/bin/tool"],
                "restored_use_launch_realpaths": ["/managed/target"],
                "restored_executable_map": {
                    "tool": {
                        "launch_path": "/tmp/wagents-cli-rollback-artifact-fixture/bin/tool",
                        "realpath": "/managed/target",
                    }
                },
            },
        ),
        (
            "mcp",
            "candidate-mcp-rollback",
            {
                **common_receipt,
                "restored_use_launch_path": "/tmp/wagents-mcp-entrypoint-rollback-artifact-fixture/bin/tool",
                "restored_use_launch_realpath": "/managed/target",
            },
            {
                **common_record,
                "transaction_id": "transaction",
                "restored_process_id": 202,
                "restored_output_sha256": "d" * 64,
                "restored_use_launch_path": "/tmp/wagents-mcp-entrypoint-rollback-artifact-fixture/bin/tool",
                "restored_use_launch_realpath": "/managed/target",
            },
        ),
        (
            "plugin",
            "candidate-plugin-rollback",
            plugin_receipt,
            plugin_record,
        ),
    ]
    for runtime_kind, journal_kind, receipt, record in cases:
        journal_transaction_id = receipt["journal_transaction_id"]
        path = tmp_path / "journals" / journal_kind / f"{journal_transaction_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 2,
            "transaction_id": journal_transaction_id,
            "kind": runtime_kind,
            "status": "commit-pending",
            "artifacts": [record],
        }
        path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        commit_path = tmp_path / "journals" / f"{journal_kind}-commit" / f"{journal_transaction_id}.json"
        commit_path.parent.mkdir(parents=True, exist_ok=True)
        commit_payload = {
            "version": 2,
            "transaction_id": journal_transaction_id,
            "status": "passed",
            "journal_path": str(path),
            "journal_sha256": module.hashlib.sha256(path.read_bytes()).hexdigest(),
            "artifact_ids": [str(receipt["artifact_id"])],
            "receipt_revision": 1,
            "receipt_store_transaction_id": receipt["store_transaction_id"],
            "receipt_document_sha256": "4" * 64,
        }
        commit_path.write_text(json.dumps(commit_payload) + "\n", encoding="utf-8")
        receipt["journal_path"] = str(path)
        digest, errors = module.journal_digest(receipt, runtime_kind=runtime_kind)
        assert digest == module.hashlib.sha256(path.read_bytes()).hexdigest()
        assert errors == []

        forged_marker = dict(commit_payload, version=1)
        commit_path.write_text(json.dumps(forged_marker) + "\n", encoding="utf-8")
        _, errors = module.journal_digest(receipt, runtime_kind=runtime_kind)
        assert any("marker version is not 2" in error for error in errors)

        forged_marker = dict(commit_payload, artifact_ids=["unrelated-artifact"])
        commit_path.write_text(json.dumps(forged_marker) + "\n", encoding="utf-8")
        _, errors = module.journal_digest(receipt, runtime_kind=runtime_kind)
        assert any("artifact ids do not match" in error for error in errors)
        assert any("omits the receipt artifact" in error for error in errors)

        forged_marker = dict(commit_payload, receipt_store_transaction_id="other-store-transaction")
        commit_path.write_text(json.dumps(forged_marker) + "\n", encoding="utf-8")
        _, errors = module.journal_digest(receipt, runtime_kind=runtime_kind)
        assert any("receipt-store transaction does not match" in error for error in errors)

        for field in ("receipt_revision", "receipt_store_transaction_id", "receipt_document_sha256"):
            forged_marker = dict(commit_payload)
            forged_marker.pop(field)
            commit_path.write_text(json.dumps(forged_marker) + "\n", encoding="utf-8")
            _, errors = module.journal_digest(receipt, runtime_kind=runtime_kind)
            assert any("marker fields do not match" in error for error in errors)

        receipt_without_store_transaction = dict(receipt)
        receipt_without_store_transaction.pop("store_transaction_id")
        commit_path.write_text(json.dumps(commit_payload) + "\n", encoding="utf-8")
        _, errors = module.journal_digest(receipt_without_store_transaction, runtime_kind=runtime_kind)
        assert any("receipt store transaction is missing" in error for error in errors)
        commit_path.write_text(json.dumps(commit_payload) + "\n", encoding="utf-8")

        forged = json.loads(json.dumps(payload))
        forged["artifacts"][0]["transaction_id"] = "other-transaction"
        path.write_text(json.dumps(forged) + "\n", encoding="utf-8")
        _, errors = module.journal_digest(receipt, runtime_kind=runtime_kind)
        assert any("transaction_id does not match" in error for error in errors)

        forged = json.loads(json.dumps(payload))
        forged["artifacts"][0]["transcript_sha256"] = "9" * 64
        path.write_text(json.dumps(forged) + "\n", encoding="utf-8")
        _, errors = module.journal_digest(receipt, runtime_kind=runtime_kind)
        assert any("transcript_sha256 does not match" in error for error in errors)

        if runtime_kind in {"cli", "mcp"}:
            fields = (
                ("restored_use_launch_path", "restored_use_launch_realpath")
                if runtime_kind == "mcp"
                else (
                    "restored_use_launch_paths",
                    "restored_use_launch_realpaths",
                    "restored_executable_map",
                )
            )
            for field in fields:
                forged = json.loads(json.dumps(payload))
                forged["artifacts"][0][field] = "forged"
                path.write_text(json.dumps(forged) + "\n", encoding="utf-8")
                _, errors = module.journal_digest(receipt, runtime_kind=runtime_kind)
                assert any(f"{field} does not match" in error for error in errors)

        forged = json.loads(json.dumps(payload))
        forged["artifacts"][0]["artifact_id"] = "unrelated-artifact"
        path.write_text(json.dumps(forged) + "\n", encoding="utf-8")
        _, errors = module.journal_digest(receipt, runtime_kind=runtime_kind)
        assert any("exactly one record" in error for error in errors)


def test_expected_selector_and_binding_graph_matches_current_overlay() -> None:
    module = _module()
    selectors = module.expected_selector_metadata()
    bindings, harnesses = module.expected_binding_metadata()

    assert len(selectors) == 1266
    assert len(bindings) == 7596
    assert len(harnesses) == 6


def test_global_closure_cannot_erase_declared_or_derived_blockers() -> None:
    module = _module()
    receipts = {
        "global-closure": {
            "gate_id": "global-closure",
            "expected_leaf_ids": list(module.NON_GLOBAL_CLOSURE_GATES),
            "active_blockers": ["declared blocker"],
        }
    }
    gates = module.build_closure_gates(receipts, [{"artifact_id": "runtime-blocker"}])

    assert gates["global-closure"]["status"] == "incomplete"
    assert any("active blockers" in error for error in gates["global-closure"]["errors"])


def test_review_closure_binds_the_canonical_full_worktree_digest(monkeypatch) -> None:
    module = _module()
    captured: dict[str, object] = {}
    canonical_worktree_digest = "f" * 64
    receipt = {
        "gate_id": "review-closure",
        "findings_fixed_status": "passed",
        "reviewed_path_digests": {"README.md": "a" * 64},
        "evidence_paths": ["README.md"],
        "evidence_digests": {"README.md": module.hashlib.sha256((module.ROOT / "README.md").read_bytes()).hexdigest()},
    }

    def evaluate(predicate: str, _receipt: object, context: dict[str, object]) -> list[str]:
        if predicate == "independent-reviews":
            captured.update(context)
        return []

    producer_receipt = dict(receipt)
    producer_receipt.update({
        "reviewed_paths": ["README.md"],
        "reviewed_input_digest": "b" * 64,
        "worktree_digest": canonical_worktree_digest,
    })
    receipt.update(producer_receipt)
    monkeypatch.setattr(module, "evaluate_predicate", evaluate)
    monkeypatch.setattr(module, "current_producer_closure_receipt", lambda _gate_id: producer_receipt)

    gates = module.build_closure_gates({"review-closure": receipt}, [])

    assert gates["review-closure"]["status"] == "accepted"
    assert captured["expected_worktree_digest"] == canonical_worktree_digest
    assert captured["expected_reviewed_input_digest"] != canonical_worktree_digest


def test_review_closure_rejects_receipt_that_omits_producer_paths(monkeypatch) -> None:
    module = _module()
    producer = {
        "gate_id": "review-closure",
        "findings_fixed_status": "passed",
        "reviewed_paths": ["README.md", "AGENTS.md"],
        "reviewed_path_digests": {"README.md": "a" * 64, "AGENTS.md": "b" * 64},
        "reviewed_input_digest": "c" * 64,
        "worktree_digest": "d" * 64,
        "evidence_paths": ["README.md"],
        "evidence_digests": {"README.md": module.hashlib.sha256((module.ROOT / "README.md").read_bytes()).hexdigest()},
    }
    truncated = dict(producer)
    truncated["reviewed_paths"] = ["README.md"]
    truncated["reviewed_path_digests"] = {"README.md": "a" * 64}
    monkeypatch.setattr(module, "current_producer_closure_receipt", lambda _gate_id: producer)
    monkeypatch.setattr(module, "evaluate_predicate", lambda *_args, **_kwargs: [])

    gates = module.build_closure_gates({"review-closure": truncated}, [])

    assert gates["review-closure"]["status"] == "incomplete"
    assert any("canonical producer evidence" in error for error in gates["review-closure"]["errors"])


def test_current_install_digest_detects_mutation_and_removal(tmp_path: Path) -> None:
    module = _module()
    installed = tmp_path / "tool"
    installed.write_text("one", encoding="utf-8")
    receipt = {
        "installed_realpaths": [str(installed)],
        "digest_algorithm": module.FILESYSTEM_DIGEST_ALGORITHM,
        "digest_ignored_dirs": sorted(module.RUNTIME_DIGEST_IGNORED_DIRS),
    }
    baseline, errors = module.current_install_digest(receipt)
    assert errors == []
    assert baseline

    installed.write_text("two", encoding="utf-8")
    changed, errors = module.current_install_digest(receipt)
    assert errors == []
    assert changed != baseline

    installed.unlink()
    missing, errors = module.current_install_digest(receipt)
    assert missing != baseline
    assert any("installed paths are missing" in error for error in errors)


def test_current_live_entrypoint_digest_detects_symlink_retarget(tmp_path: Path) -> None:
    module = _module()
    first = tmp_path / "first"
    second = tmp_path / "second"
    for target in (first, second):
        target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        target.chmod(0o755)
    entrypoint = tmp_path / "tool"
    entrypoint.symlink_to(first)
    receipt = {"live_entrypoint_paths": [str(entrypoint)]}

    baseline, errors = module.current_live_entrypoint_digest(receipt, [entrypoint])
    assert baseline
    assert errors == []
    assert module.current_live_entrypoint_targets([entrypoint]) == {"tool": str(first)}

    entrypoint.unlink()
    entrypoint.symlink_to(second)
    changed, errors = module.current_live_entrypoint_digest(receipt, [entrypoint])
    assert changed != baseline
    assert errors == []
    assert module.current_live_entrypoint_targets([entrypoint]) == {"tool": str(second)}
