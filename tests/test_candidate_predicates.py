from __future__ import annotations

from wagents.candidate_predicates import evaluate_predicate


def test_raw_bijection_accepts_293_289_four_duplicate_pairs() -> None:
    receipt = {
        "raw_count": 293,
        "unique_count": 289,
        "duplicate_groups": [[5, 56], [22, 86], [51, 284], [132, 175]],
        "raw_indexes": list(range(1, 294)),
    }
    assert evaluate_predicate("raw-bijection", receipt) == []


def test_install_receipt_rejects_path_only() -> None:
    receipt = {
        "artifact_id": "a",
        "package_id": "p",
        "installed_digest": "sha256:1",
        "installed_realpaths": ["~/.local/bin/a"],
        "install_status": "passed",
        "evidence_kind": "path",
    }
    assert "cannot prove installation" in " ".join(evaluate_predicate("install-receipt", receipt))


def test_behavior_probe_rejects_version_only() -> None:
    receipt = {
        "artifact_id": "a",
        "fixture_id": "f",
        "semantic_assertions": ["version printed"],
        "installed_digest": "sha256:1",
        "happy_path_status": "passed",
        "failure_path_status": "passed",
        "denial_path_status": "passed",
        "denial_path_encoding": "protocol-error",
        "probe_kind": "version",
    }
    assert evaluate_predicate("behavior-probe", receipt)


def test_fresh_process_rejects_reused_process() -> None:
    receipt = {
        "artifact_id": "a",
        "initial_process_id": "1",
        "fresh_process_id": "1",
        "installed_digest": "sha256:1",
        "fresh_discovery_status": "passed",
        "fresh_use_status": "passed",
    }
    assert evaluate_predicate("fresh-process", receipt)


def test_rollback_rejects_baseline_drift() -> None:
    receipt = {
        "artifact_id": "a",
        "preimage_digest": "before",
        "rollback_digest": "after",
        "promoted_final_digest": "final",
        "fresh_absence_status": "passed",
        "promoted_final_status": "passed",
    }
    assert evaluate_predicate("rollback", receipt)


def test_plugin_rollback_requires_transcript_bound_unique_launch_evidence() -> None:
    phases = (
        "marketplace",
        "initial_add",
        "initial_inventory",
        "remove",
        "fresh_absence",
        "restore",
        "restored_inventory",
        "restored_use_initial",
        "restored_use_fresh",
        "restored_use_discovery",
    )
    process_ids = {phase: 100 + index for index, phase in enumerate(phases)}
    launch_evidence = {
        phase: {
            "launch_id": f"{index + 1:032x}",
            "started_at_ns": 1_000 + index,
            "process_id": process_ids[phase],
        }
        for index, phase in enumerate(phases)
    }
    receipt = {
        "artifact_id": "a",
        "preimage_digest": "a" * 64,
        "rollback_digest": "a" * 64,
        "promoted_final_digest": "a" * 64,
        "fresh_absence_status": "passed",
        "promoted_final_status": "passed",
        "restored_use_process_id": process_ids["restored_use_fresh"],
        "fresh_absence_process_id": process_ids["fresh_absence"],
        "restored_use_output_sha256": "b" * 64,
        "restored_installed_digest": "a" * 64,
        "restored_use_status": "passed",
        "plugin_id": "plugin@marketplace",
        "plugin_scope": "user-global-codex",
        "rehearsal_kind": "isolated-plugin-root-detach",
        "live_install_unchanged": True,
        "transcript_path": "transcript.json",
        "transcript_sha256": "c" * 64,
        "journal_path": "/managed/plugin-journal.json",
        "journal_sha256": "d" * 64,
        "journal_transaction_id": "plugin-journal-transaction",
        "transaction_id": "plugin-transaction",
        "process_ids": process_ids,
        "launch_evidence": launch_evidence,
    }
    context = {
        "require_restored_use": True,
        "expected_promoted_final_digest": "a" * 64,
        "expected_plugin_id": "plugin@marketplace",
        "expected_plugin_scope": "user-global-codex",
        "expected_rehearsal_kind": "isolated-plugin-root-detach",
        "current_transcript_sha256": "c" * 64,
        "current_journal_sha256": "d" * 64,
    }

    assert evaluate_predicate("rollback", receipt, context) == []

    forged = {phase: dict(value) for phase, value in launch_evidence.items()}
    forged["restore"]["launch_id"] = forged["remove"]["launch_id"]
    errors = evaluate_predicate("rollback", {**receipt, "launch_evidence": forged}, context)

    assert any("launch identities were reused" in error for error in errors)

    without_journal = dict(receipt)
    without_journal.pop("journal_sha256")
    errors = evaluate_predicate("rollback", without_journal, context)
    assert any("missing required field: journal_sha256" in error for error in errors)


def test_entrypoint_rollback_requires_bound_recovery_evidence() -> None:
    isolated_launch = "/tmp/wagents-cli-rollback-a-fixture/bin/tool"
    receipt = {
        "artifact_id": "a",
        "preimage_digest": "a" * 64,
        "rollback_digest": "a" * 64,
        "promoted_final_digest": "b" * 64,
        "fresh_absence_status": "passed",
        "promoted_final_status": "passed",
        "fresh_absence_process_id": 101,
        "fresh_absence_output_sha256": "c" * 64,
        "restored_use_status": "passed",
        "restored_use_process_id": 202,
        "restored_use_output_sha256": "d" * 64,
        "rehearsal_kind": "isolated-entrypoint-root-detach",
        "live_entrypoint_paths": ["/managed/tool"],
        "live_entrypoint_digest": "e" * 64,
        "live_entrypoint_unchanged": True,
        "transcript_path": "transcript.json",
        "transcript_sha256": "f" * 64,
        "journal_path": "/tmp/journal.json",
        "journal_sha256": "1" * 64,
        "journal_transaction_id": "cli-journal-transaction",
        "transaction_id": "transaction",
        "restored_use_launch_paths": [isolated_launch, isolated_launch],
        "restored_use_launch_realpaths": ["/managed/target", "/managed/target"],
        "restored_executable_map": {"tool": {"launch_path": isolated_launch, "realpath": "/managed/target"}},
    }
    context = {
        "expected_promoted_final_digest": "b" * 64,
        "require_entrypoint_recovery": True,
        "expected_rehearsal_kind": "isolated-entrypoint-root-detach",
        "expected_live_entrypoint_paths": ["/managed/tool"],
        "expected_live_entrypoint_targets": {"tool": "/managed/target"},
        "expected_entrypoint_recovery_kind": "cli",
        "current_live_entrypoint_digest": "e" * 64,
        "current_transcript_sha256": "f" * 64,
        "current_journal_sha256": "1" * 64,
    }

    assert evaluate_predicate("rollback", receipt, context) == []

    forged = {**receipt, "restored_use_process_id": 101, "journal_sha256": "2" * 64}
    errors = evaluate_predicate("rollback", forged, context)
    assert any("reused a process ID" in error for error in errors)
    assert any("journal digest is stale" in error for error in errors)

    stale_entrypoint = {**receipt, "live_entrypoint_digest": "9" * 64}
    errors = evaluate_predicate("rollback", stale_entrypoint, context)
    assert any("live entrypoint digest is stale" in error for error in errors)

    wrong_paths = {**receipt, "live_entrypoint_paths": ["/managed/other"]}
    errors = evaluate_predicate("rollback", wrong_paths, context)
    assert any("live_entrypoint_paths do not match" in error for error in errors)

    wrong_cardinality = {**receipt, "restored_use_launch_realpaths": ["/managed/target"]}
    errors = evaluate_predicate("rollback", wrong_cardinality, context)
    assert any("cardinalities must match" in error for error in errors)

    escaped_launch = "/tmp/not-a-candidate-rollback/bin/tool"
    escaped_map = {"tool": {"launch_path": escaped_launch, "realpath": "/managed/target"}}
    escaped = {
        **receipt,
        "restored_use_launch_paths": [escaped_launch],
        "restored_use_launch_realpaths": ["/managed/target"],
        "restored_executable_map": escaped_map,
    }
    errors = evaluate_predicate("rollback", escaped, context)
    assert any("outside the isolated cli rollback root" in error for error in errors)

    stale_target = {
        **receipt,
        "restored_use_launch_realpaths": ["/managed/other", "/managed/other"],
        "restored_executable_map": {"tool": {"launch_path": isolated_launch, "realpath": "/managed/other"}},
    }
    errors = evaluate_predicate("rollback", stale_target, context)
    assert any("does not match the live entrypoint target" in error for error in errors)

    extra_map = {
        **receipt["restored_executable_map"],
        "other": {"launch_path": isolated_launch, "realpath": "/managed/target"},
    }
    errors = evaluate_predicate("rollback", {**receipt, "restored_executable_map": extra_map}, context)
    assert any("must exactly cover current live entrypoints" in error for error in errors)


def test_mcp_entrypoint_rollback_binds_launch_to_isolated_live_target() -> None:
    isolated_launch = "/tmp/wagents-mcp-entrypoint-rollback-a-fixture/bin/tool"
    receipt = {
        "artifact_id": "a",
        "preimage_digest": "a" * 64,
        "rollback_digest": "a" * 64,
        "promoted_final_digest": "b" * 64,
        "fresh_absence_status": "passed",
        "promoted_final_status": "passed",
        "fresh_absence_process_id": 101,
        "fresh_absence_output_sha256": "c" * 64,
        "restored_use_status": "passed",
        "restored_use_process_id": 202,
        "restored_use_output_sha256": "d" * 64,
        "rehearsal_kind": "isolated-entrypoint-root-detach",
        "live_entrypoint_paths": ["/managed/tool"],
        "live_entrypoint_digest": "e" * 64,
        "live_entrypoint_unchanged": True,
        "transcript_path": "transcript.json",
        "transcript_sha256": "f" * 64,
        "journal_path": "/tmp/journal.json",
        "journal_sha256": "1" * 64,
        "journal_transaction_id": "mcp-journal-transaction",
        "transaction_id": "transaction",
        "restored_use_launch_path": isolated_launch,
        "restored_use_launch_realpath": "/managed/target",
    }
    context = {
        "expected_promoted_final_digest": "b" * 64,
        "require_entrypoint_recovery": True,
        "expected_rehearsal_kind": "isolated-entrypoint-root-detach",
        "expected_live_entrypoint_paths": ["/managed/tool"],
        "expected_live_entrypoint_targets": {"tool": "/managed/target"},
        "expected_entrypoint_recovery_kind": "mcp",
        "current_live_entrypoint_digest": "e" * 64,
        "current_transcript_sha256": "f" * 64,
        "current_journal_sha256": "1" * 64,
    }

    assert evaluate_predicate("rollback", receipt, context) == []

    live_launch = {**receipt, "restored_use_launch_path": "/managed/tool"}
    errors = evaluate_predicate("rollback", live_launch, context)
    assert any("live public entrypoint" in error for error in errors)

    stale_target = {**receipt, "restored_use_launch_realpath": "/managed/other"}
    errors = evaluate_predicate("rollback", stale_target, context)
    assert any("does not match the live entrypoint target" in error for error in errors)


def test_independent_reviews_reject_same_actor() -> None:
    receipt = {"author_actor": "L1", "safety_reviewer_actor": "L1", "judge_actor": "L2"}
    assert evaluate_predicate("independent-reviews", receipt)


def test_auth_required_rejects_missing_positive_probe() -> None:
    receipt = {
        "artifact_id": "a",
        "auth_required": True,
        "storage_backend": "keychain",
        "minimum_scopes": ["read"],
        "principal_fingerprint": "sha256:redacted",
        "auth_negative_status": "passed",
        "auth_positive_status": "blocked",
        "logout_or_revoke_status": "passed",
        "secret_value_recorded": False,
    }
    assert evaluate_predicate("auth", receipt)


def test_quarantine_rejects_global_discovery() -> None:
    receipt = {
        "artifact_id": "a",
        "sandbox_profile": "deny-network",
        "fixture_id": "owned",
        "cleanup_digest": "sha256:cleanup",
        "isolated_use_status": "passed",
        "global_rejection_status": "failed",
        "rollback_status": "passed",
        "global_absence_status": "failed",
        "inherited_secrets": False,
        "lawful_owned_fixture": True,
    }
    assert evaluate_predicate("quarantine", receipt)


def test_global_closure_ignores_summary_complete_boolean() -> None:
    receipt = {
        "complete": True,
        "expected_leaf_ids": ["a", "b"],
        "leaf_receipts": [{"node_id": "a", "status": "accepted", "predicate_errors": []}],
        "active_blockers": [],
        "untested_capabilities": [],
    }
    assert evaluate_predicate("global-closure", receipt)


def test_selector_closure_requires_exact_current_leaf_set() -> None:
    selector_id = "selector:https://github.com/example/repo:example"
    metadata = {
        selector_id: {
            "selector_id": selector_id,
            "normalized_url": "https://github.com/Example/Repo",
            "skill_name": "example",
            "path": "docs/src/authoring/skills/example.mdx",
            "authoring_sha256": "a" * 64,
        }
    }
    receipt = {
        "expected_leaf_ids": [selector_id],
        "leaf_receipts": [
            {
                "node_id": selector_id,
                **metadata[selector_id],
                "status": "accepted",
                "predicate_errors": [],
                "source_evidence_status": "passed",
                "required_capabilities": ["invoke:/example"],
                "proved_capabilities": ["invoke:/example"],
                "untested_capabilities": [],
            }
        ],
        "active_blockers": [],
        "required_capabilities": [f"{selector_id}::invoke:/example"],
        "proved_capabilities": [f"{selector_id}::invoke:/example"],
        "untested_capabilities": [],
    }
    context = {"expected_leaf_ids": [selector_id], "expected_leaf_metadata": metadata}

    assert evaluate_predicate("selector-closure", receipt, context) == []
    receipt["leaf_receipts"].append(dict(receipt["leaf_receipts"][0]))
    assert "duplicate node IDs" in " ".join(evaluate_predicate("selector-closure", receipt, context))


def test_harness_binding_closure_rejects_wrong_agent_or_disposition() -> None:
    selector_id = "selector:https://github.com/example/repo:example"
    binding_id = f"binding:{selector_id}:codex"
    context = {
        "expected_leaf_ids": [binding_id],
        "expected_leaf_metadata": {
            binding_id: {
                "selector_id": selector_id,
                "normalized_url": "https://github.com/Example/Repo",
                "skill_name": "example",
                "agent": "codex",
            }
        },
        "target_harnesses": ["codex"],
        "expected_sync_report_sha256": "a" * 64,
    }
    receipt = {
        "expected_leaf_ids": [binding_id],
        "target_harnesses": ["codex"],
        "sync_report_sha256": "a" * 64,
        "leaf_receipts": [
            {
                "node_id": binding_id,
                "selector_id": selector_id,
                "normalized_url": "https://github.com/Example/Repo",
                "skill_name": "example",
                "agent": "cursor",
                "status": "accepted",
                "predicate_errors": [],
                "sync_disposition": "missing",
                "sync_report_sha256": "a" * 64,
                "input_digest": "b" * 64,
                "installed_digest": "c" * 64,
                "required_capabilities": ["invoke:/example"],
                "proved_capabilities": ["invoke:/example"],
                "untested_capabilities": [],
                "phase_evidence": {
                    phase: {
                        "status": "accepted",
                        "predicate_errors": [],
                        "receipt_sha256": f"{index + 1:064x}",
                        "assertion_sha256": f"{index + 101:064x}",
                    }
                    for index, phase in enumerate(
                        ("discovery", "behavior", "fresh_process", "rollback", "promoted_final")
                    )
                },
            }
        ],
        "active_blockers": [],
        "required_capabilities": [f"{binding_id}::invoke:/example"],
        "proved_capabilities": [f"{binding_id}::invoke:/example"],
        "untested_capabilities": [],
    }

    errors = evaluate_predicate("harness-binding-closure", receipt, context)
    assert any("agent does not match" in error for error in errors)
    assert any("not already present" in error for error in errors)


def test_leaf_closure_rejects_malformed_ids_without_crashing() -> None:
    receipt = {
        "expected_leaf_ids": [["not-hashable"]],
        "leaf_receipts": {"not": "a-list"},
        "active_blockers": [],
        "untested_capabilities": [],
    }

    errors = evaluate_predicate("selector-closure", receipt)

    assert "expected_leaf_ids must be a non-empty string list" in errors
    assert "leaf_receipts must be a list" in errors


def test_install_receipt_rejects_live_digest_drift() -> None:
    receipt = {
        "artifact_id": "a",
        "package_id": "npm:a",
        "installed_digest": "a" * 64,
        "installed_realpaths": ["/tmp/a"],
        "install_status": "passed",
        "evidence_kind": "package-manager-live-install",
        "digest_algorithm": "lstat-tree-v1",
        "digest_ignored_dirs": [".git"],
    }
    errors = evaluate_predicate(
        "install-receipt",
        receipt,
        {
            "current_installed_digest": "b" * 64,
            "expected_digest_algorithm": "lstat-tree-v1",
            "expected_digest_ignored_dirs": [".git"],
        },
    )

    assert "installed digest does not match the current filesystem" in errors


def test_auth_receipt_requires_exact_contract_and_explicit_secret_absence() -> None:
    receipt = {
        "artifact_id": "a",
        "auth_required": True,
        "auth_mode": "oauth",
        "auth_provider": "wrong",
        "storage_backend": "oauth-session",
        "env_names": ["ACCOUNT"],
        "minimum_scopes": ["read"],
        "principal_fingerprint": "sha256:redacted",
        "auth_negative_status": "passed",
        "auth_positive_status": "passed",
        "logout_or_revoke_status": "passed",
    }
    errors = evaluate_predicate(
        "auth",
        receipt,
        {
            "expected_auth_mode": "oauth",
            "expected_auth_provider": "provider",
            "expected_storage_backend": "oauth-session",
            "expected_env_names": ["ACCOUNT"],
            "expected_minimum_scopes": ["read"],
        },
    )

    assert "auth_provider does not match the current auth contract" in errors
    assert "secret_value_recorded is false" in " ".join(errors)


def test_unknown_predicate_fails_closed() -> None:
    assert evaluate_predicate("does-not-exist", {}) == ["unknown predicate id: does-not-exist"]


def test_required_auth_contract_cannot_be_bypassed_with_false_flag() -> None:
    errors = evaluate_predicate(
        "auth",
        {"auth_required": False},
        {"expected_auth_required": True},
    )

    assert "auth_required does not match the current auth contract" in errors
    assert any("auth_positive_status" in error for error in errors)


def test_receipt_fresh_rejects_future_naive_and_negative_windows() -> None:
    base = {
        "source_commit_sha": "a" * 40,
        "input_digest": "b" * 64,
        "predicate_version": "v1",
    }
    context = {
        "source_commit_sha": "a" * 40,
        "input_digest": "b" * 64,
        "predicate_version": "v1",
        "now": "2026-07-17T00:00:00+00:00",
    }

    future = evaluate_predicate("receipt-fresh", {**base, "recorded_at": "2099-01-01T00:00:00+00:00"}, context)
    naive = evaluate_predicate("receipt-fresh", {**base, "recorded_at": "2026-07-17T00:00:00"}, context)
    negative = evaluate_predicate(
        "receipt-fresh",
        {**base, "recorded_at": "2026-07-17T00:00:00+00:00"},
        {**context, "ttl_seconds": -1},
    )

    assert any("clock skew" in error for error in future)
    assert "receipt timestamps are invalid" in naive
    assert "receipt timestamps are invalid" in negative


def test_package_identity_rejects_stale_version() -> None:
    receipt = {
        "artifact_id": "a",
        "package_id": "npm:tool",
        "source_commit_sha": "a" * 40,
        "resolved_version": "1.0.0",
        "integrity": "sha512:old",
        "install_root": "/tmp/tool",
    }
    errors = evaluate_predicate(
        "package-identity",
        receipt,
        {
            "expected_package_id": "npm:tool",
            "expected_source_commit_sha": "b" * 40,
            "expected_resolved_version": "2.0.0",
            "expected_integrity": "sha512:new",
        },
    )
    assert len(errors) == 3
