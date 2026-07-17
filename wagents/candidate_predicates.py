"""Fail-closed acceptance predicates for candidate-corpus activation receipts."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

JsonObject = Mapping[str, Any]
Predicate = Callable[[JsonObject, JsonObject], list[str]]

PASS = "passed"
ACCEPTED = "accepted"


def _missing(receipt: JsonObject, fields: Sequence[str]) -> list[str]:
    return [f"missing required field: {field}" for field in fields if receipt.get(field) in (None, "", [])]


def _status(receipt: JsonObject, field: str, expected: str = PASS) -> list[str]:
    value = receipt.get(field)
    return [] if value == expected else [f"{field} must be {expected!r}, found {value!r}"]


def raw_bijection_valid(receipt: JsonObject, context: JsonObject) -> list[str]:
    errors = _missing(receipt, ("raw_count", "unique_count", "duplicate_groups", "raw_indexes"))
    expected_raw = int(context.get("expected_raw_count", 293))
    expected_unique = int(context.get("expected_unique_count", 289))
    if receipt.get("raw_count") != expected_raw:
        errors.append(f"raw_count must be {expected_raw}")
    if receipt.get("unique_count") != expected_unique:
        errors.append(f"unique_count must be {expected_unique}")
    indexes = receipt.get("raw_indexes", [])
    if indexes != list(range(1, expected_raw + 1)):
        errors.append("raw indexes must cover the corpus exactly once and in order")
    if len(receipt.get("duplicate_groups", [])) != expected_raw - expected_unique:
        errors.append("duplicate group count does not reconcile raw and unique totals")
    return errors


def scoped_snapshot_valid(receipt: JsonObject, _context: JsonObject) -> list[str]:
    errors = _missing(receipt, ("normalized_url", "commit_sha", "tree_digest", "retrieved_at"))
    if receipt.get("tree_target") and receipt.get("scoped_path_status") != "exact-match":
        errors.append("tree target must resolve to the exact scoped path")
    if receipt.get("tree_target") and receipt.get("root_readme_fallback") is True:
        errors.append("tree target may not use a root README fallback")
    if receipt.get("tree_truncated") is True and receipt.get("scoped_refetch_status") != PASS:
        errors.append("truncated tree requires an exact scoped refetch")
    if receipt.get("fragment") and receipt.get("fragment_evidence_status") != PASS:
        errors.append("URL fragment requires explicit subresource evidence")
    return errors


def artifact_enumeration_closed(receipt: JsonObject, _context: JsonObject) -> list[str]:
    errors = _missing(receipt, ("source_id", "artifacts", "scan_digest"))
    if receipt.get("unclassified_executable_surfaces"):
        errors.append("unclassified executable surfaces remain")
    if receipt.get("classification_basis") in {"language-only", "substring-only", "topic-only"}:
        errors.append("artifact classification must bind an exact manifest or entrypoint")
    return errors


def independent_reviews_valid(receipt: JsonObject, _context: JsonObject) -> list[str]:
    errors = _missing(receipt, ("author_actor", "safety_reviewer_actor", "judge_actor"))
    actors = [receipt.get("author_actor"), receipt.get("safety_reviewer_actor"), receipt.get("judge_actor")]
    if None not in actors and len(set(actors)) != len(actors):
        errors.append("author, safety reviewer, and judge must be distinct actors")
    return errors


def package_identity_valid(receipt: JsonObject, context: JsonObject) -> list[str]:
    errors = _missing(
        receipt,
        ("artifact_id", "package_id", "source_commit_sha", "resolved_version", "integrity", "install_root"),
    )
    for field in ("package_id", "source_commit_sha", "resolved_version", "integrity"):
        expected = context.get(f"expected_{field}")
        if expected is not None and receipt.get(field) != expected:
            errors.append(f"{field} does not match the current activation target")
    return errors


def install_receipt_valid(receipt: JsonObject, _context: JsonObject) -> list[str]:
    errors = _missing(receipt, ("artifact_id", "package_id", "installed_digest", "installed_realpaths"))
    errors.extend(_status(receipt, "install_status"))
    if receipt.get("evidence_kind") in {"path", "config", "inventory", "dry-run"}:
        errors.append("path, config, inventory, or dry-run evidence cannot prove installation")
    return errors


def behavior_probe_valid(receipt: JsonObject, context: JsonObject) -> list[str]:
    errors = _missing(receipt, ("artifact_id", "fixture_id", "semantic_assertions", "installed_digest"))
    for field in ("happy_path_status", "failure_path_status", "denial_path_status"):
        errors.extend(_status(receipt, field))
    if receipt.get("probe_kind") in {"path", "config", "inventory", "help", "version", "import-only", "compile-only"}:
        errors.append("probe does not execute a source-specific semantic capability")
    if receipt.get("mock_only") is True:
        errors.append("mock-only execution cannot prove runtime usability")
    expected_digest = context.get("expected_installed_digest")
    if expected_digest is not None and receipt.get("installed_digest") != expected_digest:
        errors.append("behavior probe is not bound to the current installed digest")
    return errors


def fresh_process_valid(receipt: JsonObject, context: JsonObject) -> list[str]:
    errors = _missing(receipt, ("artifact_id", "initial_process_id", "fresh_process_id", "installed_digest"))
    if receipt.get("initial_process_id") == receipt.get("fresh_process_id"):
        errors.append("fresh-process proof reused the original process")
    errors.extend(_status(receipt, "fresh_discovery_status"))
    errors.extend(_status(receipt, "fresh_use_status"))
    expected_digest = context.get("expected_installed_digest")
    if expected_digest is not None and receipt.get("installed_digest") != expected_digest:
        errors.append("fresh-process probe is not bound to the current installed digest")
    return errors


def rollback_valid(receipt: JsonObject, context: JsonObject) -> list[str]:
    errors = _missing(receipt, ("artifact_id", "preimage_digest", "rollback_digest", "promoted_final_digest"))
    if receipt.get("preimage_digest") != receipt.get("rollback_digest"):
        errors.append("rollback did not restore the exact preimage")
    expected_digest = context.get("expected_promoted_final_digest")
    if expected_digest is not None and receipt.get("promoted_final_digest") != expected_digest:
        errors.append("rollback promotion digest does not match the current install receipt")
    errors.extend(_status(receipt, "fresh_absence_status"))
    errors.extend(_status(receipt, "promoted_final_status"))
    return errors


def binding_applicable(receipt: JsonObject, context: JsonObject) -> list[str]:
    errors = _missing(receipt, ("artifact_id", "harness_id", "surface", "applicability"))
    harnesses = context.get("harnesses", {})
    harness_id = receipt.get("harness_id")
    if harness_id not in harnesses:
        errors.append(f"unknown harness: {harness_id!r}")
    elif receipt.get("surface") not in harnesses[harness_id].get("projection_surfaces", []):
        errors.append("binding surface is not declared for the harness")
    if receipt.get("applicability") == "not-applicable-proven" and not receipt.get("independent_judge_actor"):
        errors.append("not-applicable requires an independent judge")
    return errors


def quarantine_valid(receipt: JsonObject, _context: JsonObject) -> list[str]:
    errors = _missing(receipt, ("artifact_id", "sandbox_profile", "fixture_id", "cleanup_digest"))
    for field in ("isolated_use_status", "global_rejection_status", "rollback_status", "global_absence_status"):
        errors.extend(_status(receipt, field))
    if receipt.get("inherited_secrets") is True:
        errors.append("quarantine execution inherited secrets")
    if receipt.get("lawful_owned_fixture") is not True:
        errors.append("quarantine execution requires a lawful, operator-owned fixture")
    return errors


def auth_valid(receipt: JsonObject, _context: JsonObject) -> list[str]:
    if receipt.get("auth_required") is not True:
        return []
    errors = _missing(receipt, ("artifact_id", "storage_backend", "minimum_scopes", "principal_fingerprint"))
    errors.extend(_status(receipt, "auth_negative_status"))
    errors.extend(_status(receipt, "auth_positive_status"))
    errors.extend(_status(receipt, "logout_or_revoke_status"))
    if receipt.get("secret_value_recorded") is True:
        errors.append("auth receipt must not record secret values")
    return errors


def docs_edges_valid(receipt: JsonObject, _context: JsonObject) -> list[str]:
    errors = _missing(receipt, ("source_paths", "generated_paths", "generator", "validator"))
    if receipt.get("generic_surface_only") is True:
        errors.append("docs receipt must bind exact source and generated paths")
    return errors


def dirty_ownership_valid(receipt: JsonObject, _context: JsonObject) -> list[str]:
    errors = _missing(receipt, ("declared_write_set", "preimage_digests", "postimage_digests"))
    unexpected = receipt.get("unexpected_writes", [])
    if unexpected:
        errors.append(f"unexpected writes detected: {unexpected!r}")
    if receipt.get("compare_and_swap_status") != PASS:
        errors.append("compare-and-swap preimage check did not pass")
    return errors


def receipt_fresh(receipt: JsonObject, context: JsonObject) -> list[str]:
    errors = _missing(receipt, ("source_commit_sha", "input_digest", "predicate_version", "recorded_at"))
    for field in ("source_commit_sha", "input_digest", "predicate_version"):
        current = context.get(field)
        if current is not None and receipt.get(field) != current:
            errors.append(f"receipt {field} is stale")
    try:
        recorded = datetime.fromisoformat(str(receipt.get("recorded_at"))).astimezone(UTC)
        now = datetime.fromisoformat(str(context.get("now"))).astimezone(UTC)
        ttl_seconds = int(context.get("ttl_seconds", 86_400))
        if (now - recorded).total_seconds() > ttl_seconds:
            errors.append("receipt exceeded its freshness TTL")
    except (TypeError, ValueError):
        errors.append("receipt timestamps are invalid")
    return errors


def global_closure_valid(receipt: JsonObject, _context: JsonObject) -> list[str]:
    errors = _missing(receipt, ("expected_leaf_ids", "leaf_receipts"))
    expected = set(receipt.get("expected_leaf_ids", []))
    leaf_receipts = receipt.get("leaf_receipts", [])
    accepted = {
        item.get("node_id")
        for item in leaf_receipts
        if isinstance(item, Mapping) and item.get("status") == ACCEPTED and item.get("predicate_errors") == []
    }
    missing = sorted(expected - accepted)
    if missing:
        errors.append(f"unaccepted leaf receipts remain: {missing!r}")
    if receipt.get("active_blockers"):
        errors.append("active blockers prevent requested full usability")
    if receipt.get("untested_capabilities"):
        errors.append("untested capabilities prevent requested full usability")
    return errors


PREDICATES: dict[str, Predicate] = {
    "raw-bijection": raw_bijection_valid,
    "scoped-snapshot": scoped_snapshot_valid,
    "artifact-enumeration": artifact_enumeration_closed,
    "independent-reviews": independent_reviews_valid,
    "package-identity": package_identity_valid,
    "install-receipt": install_receipt_valid,
    "behavior-probe": behavior_probe_valid,
    "fresh-process": fresh_process_valid,
    "rollback": rollback_valid,
    "binding-applicable": binding_applicable,
    "quarantine": quarantine_valid,
    "auth": auth_valid,
    "docs-edges": docs_edges_valid,
    "dirty-ownership": dirty_ownership_valid,
    "receipt-fresh": receipt_fresh,
    "global-closure": global_closure_valid,
}


def evaluate_predicate(predicate_id: str, receipt: JsonObject, context: JsonObject | None = None) -> list[str]:
    predicate = PREDICATES.get(predicate_id)
    if predicate is None:
        return [f"unknown predicate id: {predicate_id}"]
    return predicate(receipt, context or {})
