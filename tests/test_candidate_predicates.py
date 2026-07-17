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


def test_unknown_predicate_fails_closed() -> None:
    assert evaluate_predicate("does-not-exist", {}) == ["unknown predicate id: does-not-exist"]


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
