"""Fail-closed acceptance predicates for candidate-corpus activation receipts."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import PurePath
from typing import Any

from wagents.candidate_plugin_provenance import canonical_json_sha256

JsonObject = Mapping[str, Any]
Predicate = Callable[[JsonObject, JsonObject], list[str]]

PASS = "passed"
ACCEPTED = "accepted"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
LAUNCH_ID_RE = re.compile(r"^[0-9a-f]{32}$")
PLUGIN_ROLLBACK_LAUNCH_PHASES = (
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
PLUGIN_ROLLBACK_DISTINCT_PHASES = PLUGIN_ROLLBACK_LAUNCH_PHASES[:-1]
BINDING_PROOF_PHASES = (
    "discovery",
    "behavior",
    "fresh_process",
    "rollback",
    "promoted_final",
)


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


def independent_reviews_valid(receipt: JsonObject, context: JsonObject) -> list[str]:
    errors = _missing(
        receipt,
        (
            "author_actor",
            "safety_reviewer_actor",
            "judge_actor",
            "review_runs",
            "reviewed_paths",
            "reviewed_path_digests",
            "reviewed_input_digest",
            "worktree_digest",
        ),
    )
    actors = [receipt.get("author_actor"), receipt.get("safety_reviewer_actor"), receipt.get("judge_actor")]
    if None not in actors and len(set(actors)) != len(actors):
        errors.append("author, safety reviewer, and judge must be distinct actors")
    reviewed_input_digest = receipt.get("reviewed_input_digest")
    worktree_digest = receipt.get("worktree_digest")
    for field, value in (("reviewed_input_digest", reviewed_input_digest), ("worktree_digest", worktree_digest)):
        if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
            errors.append(f"{field} must be a sha256 digest")
        expected = context.get(f"expected_{field}")
        if expected is not None and value != expected:
            errors.append(f"{field} is stale")
    for field in ("reviewed_paths", "reviewed_path_digests"):
        expected = context.get(f"expected_{field}")
        if expected is not None and receipt.get(field) != expected:
            errors.append(f"{field} does not exactly match the current review input")
    runs = receipt.get("review_runs", [])
    if not isinstance(runs, list) or len(runs) != 3:
        errors.append("review_runs must contain exactly three independent runs")
        runs = []
    run_actors: list[str] = []
    run_ids: list[str] = []
    for run in runs:
        if not isinstance(run, Mapping):
            errors.append("review run must be an object")
            continue
        errors.extend(
            f"review run {error}"
            for error in _missing(
                run,
                ("actor", "role", "run_id", "command", "output_sha256", "reviewed_input_digest", "completed_at"),
            )
        )
        actor = run.get("actor")
        run_id = run.get("run_id")
        if isinstance(actor, str):
            run_actors.append(actor)
        if isinstance(run_id, str):
            run_ids.append(run_id)
        if run.get("exit_code") != 0:
            errors.append(f"review run {run_id!r} exit_code must be 0")
        if not isinstance(run.get("output_sha256"), str) or not SHA256_RE.fullmatch(str(run.get("output_sha256"))):
            errors.append(f"review run {run_id!r} output_sha256 must be a sha256 digest")
        if run.get("reviewed_input_digest") != reviewed_input_digest:
            errors.append(f"review run {run_id!r} is not bound to reviewed_input_digest")
        if not isinstance(run.get("findings"), list):
            errors.append(f"review run {run_id!r} findings must be a list")
    if runs and (sorted(run_actors) != sorted(str(actor) for actor in actors) or len(set(run_ids)) != 3):
        errors.append("review runs must bind the three distinct declared actors and run IDs")
    provenance_status = receipt.get("external_provenance_status")
    if provenance_status == "BLOCKED-EXTERNAL":
        errors.append("BLOCKED-EXTERNAL")
        return errors
    if provenance_status != PASS:
        errors.append("external_provenance_status must be 'passed' or 'BLOCKED-EXTERNAL'")
        return errors

    provenance = receipt.get("external_provenance")
    if not isinstance(provenance, Mapping):
        errors.append("external_provenance must be an object")
        return errors
    errors.extend(
        f"external provenance {error}"
        for error in _missing(
            provenance,
            (
                "issuer_id",
                "issuer_kind",
                "issuer_fingerprint",
                "issuer_evidence_sha256",
                "issuance_id",
                "session_id",
                "reviewed_input_digest",
                "worktree_digest",
                "task_bindings",
                "issuance_sha256",
            ),
        )
    )
    issuer_id = provenance.get("issuer_id")
    if issuer_id in actors:
        errors.append("external provenance issuer identity is self-authored by a review actor")
    if provenance.get("issuer_kind") != "trusted-harness":
        errors.append("external provenance issuer_kind must be 'trusted-harness'")
    for field in ("issuer_fingerprint", "issuer_evidence_sha256", "issuance_sha256"):
        value = provenance.get(field)
        if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
            errors.append(f"external provenance {field} must be a sha256 digest")
    if provenance.get("reviewed_input_digest") != reviewed_input_digest:
        errors.append("external provenance is not bound to reviewed_input_digest")
    if provenance.get("worktree_digest") != worktree_digest:
        errors.append("external provenance is not bound to worktree_digest")

    task_bindings = provenance.get("task_bindings")
    if not isinstance(task_bindings, list) or len(task_bindings) != len(runs):
        errors.append("external provenance task_bindings must cover all review runs")
        task_bindings = []
    expected_tasks = {
        (
            run.get("role"),
            run.get("actor"),
            run.get("run_id"),
            reviewed_input_digest,
        )
        for run in runs
        if isinstance(run, Mapping)
    }
    actual_tasks: set[tuple[object, object, object, object]] = set()
    task_ids: list[str] = []
    for task in task_bindings:
        if not isinstance(task, Mapping):
            errors.append("external provenance task binding must be an object")
            continue
        errors.extend(
            f"external provenance task binding {error}"
            for error in _missing(
                task,
                ("role", "actor", "run_id", "task_id", "reviewed_input_digest"),
            )
        )
        actual_tasks.add((
            task.get("role"),
            task.get("actor"),
            task.get("run_id"),
            task.get("reviewed_input_digest"),
        ))
        task_id = task.get("task_id")
        if isinstance(task_id, str):
            task_ids.append(task_id)
    if actual_tasks != expected_tasks:
        errors.append("external provenance task bindings do not match the review runs")
    if len(task_ids) != len(set(task_ids)):
        errors.append("external provenance task IDs must be distinct")
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
    if context.get("require_installed_package_origin") is True:
        errors.extend(_missing(receipt, ("audited_source_commit_sha", "installed_package_origin")))
        if receipt.get("audited_source_commit_sha") != receipt.get("source_commit_sha"):
            errors.append("audited source commit is not separated from and bound to the source audit")
        origin = receipt.get("installed_package_origin")
        if not isinstance(origin, Mapping):
            errors.append("installed_package_origin must be an object")
        elif origin.get("origin_digest") != context.get("expected_installed_package_origin"):
            errors.append("installed package origin does not match current package-manager evidence")
    if context.get("require_plugin_provenance") is True:
        fields = (
            "audited_source_commit_sha",
            "provenance_lock_entry_sha256",
            "approved_content_sha256",
            "source_content_sha256",
            "installed_content_sha256",
            "content_digest_algorithm",
            "content_digest_ignored_dirs",
        )
        errors.extend(_missing(receipt, fields))
        for field in fields:
            expected = context.get(f"expected_{field}")
            if expected is not None and receipt.get(field) != expected:
                errors.append(f"{field} does not match the immutable plugin provenance lock")
        if receipt.get("audited_source_commit_sha") != receipt.get("source_commit_sha"):
            errors.append("plugin audited source commit does not match the activation source commit")
        approved = receipt.get("approved_content_sha256")
        if approved != receipt.get("source_content_sha256") or approved != receipt.get("installed_content_sha256"):
            errors.append("plugin source and installed content must both match the approved digest")
        origin = receipt.get("installed_package_origin")
        if isinstance(origin, Mapping):
            origin_payload = dict(origin)
            origin_digest = origin_payload.pop("origin_digest", None)
            if origin_digest != canonical_json_sha256(origin_payload):
                errors.append("installed plugin package origin digest is not self-consistent")
            origin_fields = {
                "audited_source_commit_sha": receipt.get("audited_source_commit_sha"),
                "approved_content_sha256": receipt.get("approved_content_sha256"),
                "source_content_sha256": receipt.get("source_content_sha256"),
                "installed_content_sha256": receipt.get("installed_content_sha256"),
                "digest_algorithm": receipt.get("content_digest_algorithm"),
                "lock_entry_sha256": receipt.get("provenance_lock_entry_sha256"),
            }
            for field, expected in origin_fields.items():
                if origin.get(field) != expected:
                    errors.append(f"installed plugin package origin {field} drifted")
    return errors


def install_receipt_valid(receipt: JsonObject, context: JsonObject) -> list[str]:
    errors = _missing(
        receipt,
        ("artifact_id", "package_id", "installed_digest", "installed_realpaths", "digest_algorithm"),
    )
    errors.extend(_status(receipt, "install_status"))
    if receipt.get("evidence_kind") in {"path", "config", "inventory", "dry-run"}:
        errors.append("path, config, inventory, or dry-run evidence cannot prove installation")
    expected_digest = context.get("current_installed_digest")
    if expected_digest is not None and receipt.get("installed_digest") != expected_digest:
        errors.append("installed digest does not match the current filesystem")
    expected_algorithm = context.get("expected_digest_algorithm")
    if expected_algorithm is not None and receipt.get("digest_algorithm") != expected_algorithm:
        errors.append("install receipt uses an unexpected digest algorithm")
    expected_ignored = context.get("expected_digest_ignored_dirs")
    if expected_ignored is not None and sorted(receipt.get("digest_ignored_dirs", [])) != sorted(expected_ignored):
        errors.append("install receipt uses an unexpected digest ignore policy")
    if context.get("require_plugin_provenance") is True:
        fields = (
            "provenance_lock_entry_sha256",
            "approved_content_sha256",
            "installed_content_sha256",
            "content_digest_algorithm",
            "content_digest_ignored_dirs",
            "plugin_inventory_enabled",
            "plugin_inventory_plugin_id",
            "plugin_inventory_version",
        )
        errors.extend(_missing(receipt, fields))
        for field in fields:
            expected = context.get(f"expected_{field}")
            if expected is not None and receipt.get(field) != expected:
                errors.append(f"{field} does not match the immutable plugin provenance lock")
        current_content = context.get("current_installed_content_sha256")
        if current_content is None:
            errors.append("current installed plugin content digest is unavailable")
        elif receipt.get("installed_content_sha256") != current_content:
            errors.append("installed plugin content digest does not match the current filesystem")
        if receipt.get("installed_content_sha256") != receipt.get("approved_content_sha256"):
            errors.append("installed plugin content does not match the approved provenance digest")
        if receipt.get("plugin_inventory_enabled") is not True:
            errors.append("plugin install receipt does not prove live Codex activation")
        for field in ("plugin_inventory_enabled", "plugin_inventory_plugin_id", "plugin_inventory_version"):
            current = context.get(f"current_{field}")
            if current is None:
                errors.append(f"current {field} is unavailable")
            elif receipt.get(field) != current:
                errors.append(f"{field} does not match the current Codex activation state")
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
    if context.get("require_distinct_negative_evidence") is True:
        errors.extend(
            _missing(
                receipt,
                (
                    "failure_path_tool",
                    "failure_path_output_sha256",
                    "denial_path_tool",
                    "denial_path_output_sha256",
                    "denial_path_encoding",
                ),
            )
        )
        if receipt.get("failure_path_tool") == receipt.get("denial_path_tool"):
            errors.append("failure and denial paths must invoke distinct tools")
        for field in ("failure_path_output_sha256", "denial_path_output_sha256"):
            if not isinstance(receipt.get(field), str) or not SHA256_RE.fullmatch(str(receipt.get(field))):
                errors.append(f"{field} must be a sha256 digest")
        if receipt.get("denial_path_encoding") not in {
            "protocol-error",
            "tool-error",
            "content-marker",
            "dependency-gate",
        }:
            errors.append("denial_path_encoding must describe a verified denial representation")
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


def _lexical_absolute_path(value: Any, field: str, errors: list[str]) -> PurePath | None:
    if not isinstance(value, str) or not value:
        errors.append(f"{field} must be a non-empty absolute path")
        return None
    path = PurePath(value)
    if not path.is_absolute() or ".." in path.parts or str(path) != value:
        errors.append(f"{field} must be a canonical absolute lexical path")
        return None
    return path


def _isolated_bin_root(
    path: PurePath,
    *,
    artifact_id: str,
    runtime_kind: str,
    field: str,
    errors: list[str],
) -> PurePath | None:
    if path.parent.name != "bin":
        errors.append(f"{field} must be directly under the isolated rollback bin root")
        return None
    prefix = (
        f"wagents-mcp-entrypoint-rollback-{artifact_id}-"
        if runtime_kind == "mcp"
        else f"wagents-cli-rollback-{artifact_id}-"
    )
    root = path.parent.parent
    if not root.name.startswith(prefix):
        errors.append(f"{field} is outside the isolated {runtime_kind} rollback root")
        return None
    return path.parent


def _entrypoint_launch_evidence_valid(receipt: JsonObject, context: JsonObject) -> list[str]:
    errors: list[str] = []
    runtime_kind = context.get("expected_entrypoint_recovery_kind")
    if runtime_kind not in {"cli", "mcp"}:
        return ["current entrypoint recovery kind is unavailable"]

    expected_targets_raw = context.get("expected_live_entrypoint_targets")
    if (
        not isinstance(expected_targets_raw, Mapping)
        or not expected_targets_raw
        or not all(isinstance(name, str) and isinstance(target, str) for name, target in expected_targets_raw.items())
    ):
        return ["current live entrypoint targets are unavailable"]
    expected_targets = dict(expected_targets_raw)
    live_paths_raw = context.get("expected_live_entrypoint_paths")
    live_paths = (
        {value for value in live_paths_raw if isinstance(value, str)} if isinstance(live_paths_raw, list) else set()
    )
    artifact_id = str(receipt.get("artifact_id") or "")

    if runtime_kind == "mcp":
        errors.extend(_missing(receipt, ("restored_use_launch_path", "restored_use_launch_realpath")))
        launch_path = _lexical_absolute_path(
            receipt.get("restored_use_launch_path"),
            "restored_use_launch_path",
            errors,
        )
        launch_realpath = receipt.get("restored_use_launch_realpath")
        if not isinstance(launch_realpath, str) or not launch_realpath:
            errors.append("restored_use_launch_realpath must be a non-empty absolute path")
        if launch_path is None:
            return errors
        _isolated_bin_root(
            launch_path,
            artifact_id=artifact_id,
            runtime_kind="mcp",
            field="restored_use_launch_path",
            errors=errors,
        )
        if str(launch_path) in live_paths:
            errors.append("restored MCP use launched a live public entrypoint")
        expected_target = expected_targets.get(launch_path.name)
        if expected_target is None:
            errors.append("restored MCP launch does not name a current live entrypoint")
        elif launch_realpath != expected_target:
            errors.append("restored MCP launch realpath does not match the live entrypoint target")
        return errors

    errors.extend(
        _missing(
            receipt,
            (
                "restored_use_launch_paths",
                "restored_use_launch_realpaths",
                "restored_executable_map",
            ),
        )
    )
    launch_paths_raw = receipt.get("restored_use_launch_paths")
    launch_realpaths_raw = receipt.get("restored_use_launch_realpaths")
    executable_map_raw = receipt.get("restored_executable_map")
    valid_launch_paths = (
        isinstance(launch_paths_raw, list)
        and bool(launch_paths_raw)
        and all(isinstance(value, str) and value for value in launch_paths_raw)
    )
    valid_launch_realpaths = (
        isinstance(launch_realpaths_raw, list)
        and bool(launch_realpaths_raw)
        and all(isinstance(value, str) and value for value in launch_realpaths_raw)
    )
    if not valid_launch_paths:
        errors.append("restored_use_launch_paths must be a non-empty string list")
    if not valid_launch_realpaths:
        errors.append("restored_use_launch_realpaths must be a non-empty string list")
    if (
        isinstance(launch_paths_raw, list)
        and isinstance(launch_realpaths_raw, list)
        and len(launch_paths_raw) != len(launch_realpaths_raw)
    ):
        errors.append("restored CLI launch path and realpath cardinalities must match")

    expected_names = set(expected_targets)
    if not isinstance(executable_map_raw, Mapping) or not executable_map_raw:
        errors.append("restored_executable_map must be a non-empty object")
        executable_map: dict[str, Any] = {}
    else:
        executable_map = dict(executable_map_raw)
        if set(executable_map) != expected_names:
            errors.append("restored_executable_map must exactly cover current live entrypoints")

    map_paths: dict[str, str] = {}
    map_realpaths: dict[str, str] = {}
    isolated_bin: PurePath | None = None
    for name in sorted(expected_names & set(executable_map)):
        evidence = executable_map[name]
        if not isinstance(evidence, Mapping):
            errors.append(f"restored_executable_map[{name!r}] must be an object")
            continue
        launch_path = _lexical_absolute_path(
            evidence.get("launch_path"),
            f"restored_executable_map[{name!r}].launch_path",
            errors,
        )
        realpath = evidence.get("realpath")
        if not isinstance(realpath, str) or not realpath:
            errors.append(f"restored_executable_map[{name!r}].realpath must be a non-empty absolute path")
        elif realpath != expected_targets[name]:
            errors.append(f"restored_executable_map[{name!r}].realpath does not match the live entrypoint target")
        else:
            map_realpaths[name] = realpath
        if launch_path is None:
            continue
        if launch_path.name != name:
            errors.append(f"restored_executable_map[{name!r}].launch_path has the wrong executable basename")
        current_bin = _isolated_bin_root(
            launch_path,
            artifact_id=artifact_id,
            runtime_kind="cli",
            field=f"restored_executable_map[{name!r}].launch_path",
            errors=errors,
        )
        if current_bin is not None:
            if isolated_bin is None:
                isolated_bin = current_bin
            elif current_bin != isolated_bin:
                errors.append("restored_executable_map launch paths span multiple isolated rollback roots")
        if str(launch_path) in live_paths:
            errors.append(f"restored_executable_map[{name!r}] points at a live public entrypoint")
        map_paths[name] = str(launch_path)

    if valid_launch_paths and valid_launch_realpaths and len(launch_paths_raw) == len(launch_realpaths_raw):
        for index, (launch_value, realpath) in enumerate(zip(launch_paths_raw, launch_realpaths_raw, strict=True)):
            launch_path = _lexical_absolute_path(
                launch_value,
                f"restored_use_launch_paths[{index}]",
                errors,
            )
            if launch_path is None:
                continue
            if isolated_bin is not None and launch_path.parent != isolated_bin:
                errors.append(f"restored_use_launch_paths[{index}] is outside the isolated rollback root")
            if str(launch_path) in live_paths:
                errors.append(f"restored_use_launch_paths[{index}] launched a live public entrypoint")
            name = launch_path.name
            if map_paths.get(name) != str(launch_path):
                errors.append(f"restored_use_launch_paths[{index}] is not bound to restored_executable_map")
            if map_realpaths.get(name) != realpath:
                errors.append(f"restored_use_launch_realpaths[{index}] does not match the live entrypoint target")
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
    if context.get("require_entrypoint_recovery") is True:
        errors.extend(
            _missing(
                receipt,
                (
                    "fresh_absence_process_id",
                    "fresh_absence_output_sha256",
                    "restored_use_process_id",
                    "restored_use_output_sha256",
                    "rehearsal_kind",
                    "live_entrypoint_paths",
                    "live_entrypoint_digest",
                    "transcript_path",
                    "transcript_sha256",
                    "transaction_id",
                ),
            )
        )
        errors.extend(_status(receipt, "restored_use_status"))
        expected_rehearsal = context.get("expected_rehearsal_kind")
        if expected_rehearsal is not None and receipt.get("rehearsal_kind") != expected_rehearsal:
            errors.append("rehearsal_kind does not match the activated entrypoint")
        if receipt.get("live_entrypoint_unchanged") is not True:
            errors.append("rollback must prove the live entrypoint remained unchanged")
        expected_paths = context.get("expected_live_entrypoint_paths")
        if not isinstance(expected_paths, list) or not expected_paths:
            errors.append("current live entrypoint paths are unavailable")
        elif receipt.get("live_entrypoint_paths") != expected_paths:
            errors.append("live_entrypoint_paths do not match the current artifact entrypoints")
        current_live_digest = context.get("current_live_entrypoint_digest")
        if not isinstance(current_live_digest, str) or not SHA256_RE.fullmatch(current_live_digest):
            errors.append("current live entrypoint digest is unavailable")
        elif receipt.get("live_entrypoint_digest") != current_live_digest:
            errors.append("live entrypoint digest is stale")
        recovery_process_ids: list[int] = []
        for field in ("fresh_absence_process_id", "restored_use_process_id"):
            value = receipt.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                errors.append(f"{field} must be a positive process ID")
            else:
                recovery_process_ids.append(value)
        if len(recovery_process_ids) == 2 and len(set(recovery_process_ids)) != 2:
            errors.append("rollback absence and restored-use probes reused a process ID")
        for field in (
            "fresh_absence_output_sha256",
            "restored_use_output_sha256",
            "live_entrypoint_digest",
            "transcript_sha256",
        ):
            value = receipt.get(field)
            if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
                errors.append(f"{field} must be a sha256 digest")
        expected_transcript = context.get("current_transcript_sha256")
        if expected_transcript is not None and receipt.get("transcript_sha256") != expected_transcript:
            errors.append("rollback transcript digest is stale")
        errors.extend(_entrypoint_launch_evidence_valid(receipt, context))
    if context.get("require_restored_use") is True:
        errors.extend(
            _missing(
                receipt,
                ("restored_use_process_id", "restored_use_output_sha256", "restored_installed_digest"),
            )
        )
        errors.extend(_status(receipt, "restored_use_status"))
        if receipt.get("restored_installed_digest") != receipt.get("rollback_digest"):
            errors.append("restored-use proof is not bound to the restored plugin digest")
        for field in ("expected_plugin_id", "expected_plugin_scope", "expected_rehearsal_kind"):
            expected = context.get(field)
            receipt_field = field.removeprefix("expected_")
            if expected is not None and receipt.get(receipt_field) != expected:
                errors.append(f"{receipt_field} does not match the activated plugin")
        for field in ("fresh_absence_process_id", "restored_use_process_id"):
            try:
                if int(str(receipt.get(field))) <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append(f"{field} must be a nonzero process ID")
        process_ids = receipt.get("process_ids")
        launch_evidence = receipt.get("launch_evidence")
        if not isinstance(process_ids, Mapping) or set(process_ids) != set(PLUGIN_ROLLBACK_LAUNCH_PHASES):
            errors.append("rollback process_ids must exactly cover all plugin rollback phases")
            process_ids = {}
        if not isinstance(launch_evidence, Mapping) or set(launch_evidence) != set(PLUGIN_ROLLBACK_LAUNCH_PHASES):
            errors.append("rollback launch_evidence must exactly cover all plugin rollback phases")
            launch_evidence = {}
        launch_ids: dict[str, str] = {}
        for phase in PLUGIN_ROLLBACK_LAUNCH_PHASES:
            process_id = process_ids.get(phase)
            evidence = launch_evidence.get(phase)
            if not isinstance(process_id, int) or isinstance(process_id, bool) or process_id <= 0:
                errors.append(f"rollback process_ids[{phase!r}] must be a positive integer")
            if not isinstance(evidence, Mapping):
                errors.append(f"rollback launch_evidence[{phase!r}] must be an object")
                continue
            launch_id = evidence.get("launch_id")
            started_at_ns = evidence.get("started_at_ns")
            if not isinstance(launch_id, str) or not LAUNCH_ID_RE.fullmatch(launch_id):
                errors.append(f"rollback launch_evidence[{phase!r}] has an invalid launch_id")
            else:
                launch_ids[phase] = launch_id
            if not isinstance(started_at_ns, int) or isinstance(started_at_ns, bool) or started_at_ns <= 0:
                errors.append(f"rollback launch_evidence[{phase!r}] has an invalid started_at_ns")
            if evidence.get("process_id") != process_id:
                errors.append(f"rollback launch_evidence[{phase!r}] process_id drifted")
        distinct_ids = [launch_ids.get(phase) for phase in PLUGIN_ROLLBACK_DISTINCT_PHASES]
        if None not in distinct_ids and len(distinct_ids) != len(set(distinct_ids)):
            errors.append("rollback launch identities were reused across distinct phases")
        discovery = launch_evidence.get("restored_use_discovery")
        initial = launch_evidence.get("restored_use_initial")
        if isinstance(discovery, Mapping) and isinstance(initial, Mapping):
            if discovery.get("launch_id") == initial.get("launch_id"):
                if dict(discovery) != dict(initial):
                    errors.append("rollback discovery launch alias drifted from initial semantic use")
            elif discovery.get("launch_id") in set(distinct_ids):
                errors.append("rollback discovery reused an unrelated launch identity")
        output_digest = receipt.get("restored_use_output_sha256")
        if not isinstance(output_digest, str) or not SHA256_RE.fullmatch(output_digest):
            errors.append("restored_use_output_sha256 must be a sha256 digest")
        if receipt.get("live_install_unchanged") is not True:
            errors.append("rollback must prove the live install remained unchanged")
        errors.extend(_missing(receipt, ("transcript_path", "transcript_sha256")))
        expected_transcript = context.get("current_transcript_sha256")
        if expected_transcript is not None and receipt.get("transcript_sha256") != expected_transcript:
            errors.append("rollback transcript digest is stale")
    if context.get("require_entrypoint_recovery") is True or context.get("require_restored_use") is True:
        errors.extend(
            _missing(
                receipt,
                ("journal_path", "journal_sha256", "journal_transaction_id", "transaction_id"),
            )
        )
        journal_transaction_id = receipt.get("journal_transaction_id")
        if not isinstance(journal_transaction_id, str) or not journal_transaction_id:
            errors.append("journal_transaction_id must be a nonempty string")
        journal_sha256 = receipt.get("journal_sha256")
        if not isinstance(journal_sha256, str) or not SHA256_RE.fullmatch(journal_sha256):
            errors.append("journal_sha256 must be a sha256 digest")
        current_journal = context.get("current_journal_sha256")
        if not isinstance(current_journal, str) or not SHA256_RE.fullmatch(current_journal):
            errors.append("current rollback journal digest is unavailable")
        elif journal_sha256 != current_journal:
            errors.append("rollback journal digest is stale")
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


def auth_valid(receipt: JsonObject, context: JsonObject) -> list[str]:
    errors = _missing(receipt, ("auth_required",))
    expected_required = context.get("expected_auth_required")
    if expected_required is not None and receipt.get("auth_required") is not expected_required:
        errors.append("auth_required does not match the current auth contract")
    if receipt.get("auth_required") is not True and expected_required is not True:
        return errors
    errors.extend(
        _missing(
            receipt,
            ("artifact_id", "auth_mode", "auth_provider", "storage_backend", "minimum_scopes", "principal_fingerprint"),
        )
    )
    errors.extend(_status(receipt, "auth_negative_status"))
    errors.extend(_status(receipt, "auth_positive_status"))
    errors.extend(_status(receipt, "logout_or_revoke_status"))
    if receipt.get("secret_value_recorded") is not False:
        errors.append("auth receipt must explicitly prove secret_value_recorded is false")
    for field in ("auth_mode", "auth_provider", "storage_backend"):
        expected = context.get(f"expected_{field}")
        if expected is not None and receipt.get(field) != expected:
            errors.append(f"{field} does not match the current auth contract")
    for field in ("env_names", "minimum_scopes"):
        expected = context.get(f"expected_{field}")
        if expected is not None and sorted(receipt.get(field, [])) != sorted(expected):
            errors.append(f"{field} does not match the current auth contract")
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
        recorded_raw = datetime.fromisoformat(str(receipt.get("recorded_at")))
        now_raw = datetime.fromisoformat(str(context.get("now")))
        if recorded_raw.tzinfo is None or now_raw.tzinfo is None:
            raise ValueError("freshness timestamps require timezones")
        recorded = recorded_raw.astimezone(UTC)
        now = now_raw.astimezone(UTC)
        ttl_seconds = int(context.get("ttl_seconds", 86_400))
        clock_skew_seconds = int(context.get("clock_skew_seconds", 300))
        if ttl_seconds < 0 or clock_skew_seconds < 0:
            raise ValueError("freshness windows must be nonnegative")
        if (recorded - now).total_seconds() > clock_skew_seconds:
            errors.append("receipt timestamp is later than the allowed clock skew")
        if (now - recorded).total_seconds() > ttl_seconds:
            errors.append("receipt exceeded its freshness TTL")
    except (TypeError, ValueError):
        errors.append("receipt timestamps are invalid")
    return errors


def _string_set_field(
    receipt: JsonObject,
    field: str,
    *,
    allow_empty: bool = True,
) -> tuple[list[str], list[str]]:
    value = receipt.get(field)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        return [], [f"{field} must be a string list"]
    values = [str(item) for item in value]
    errors: list[str] = []
    if len(values) != len(set(values)):
        errors.append(f"{field} contains duplicates")
    if values != sorted(values):
        errors.append(f"{field} must be sorted")
    if not allow_empty and not values:
        errors.append(f"{field} must not be empty")
    return values, errors


def _capability_partition_valid(receipt: JsonObject, *, require_capabilities: bool) -> list[str]:
    required, errors = _string_set_field(
        receipt,
        "required_capabilities",
        allow_empty=not require_capabilities,
    )
    proved, proved_errors = _string_set_field(receipt, "proved_capabilities")
    untested, untested_errors = _string_set_field(receipt, "untested_capabilities")
    errors.extend(proved_errors)
    errors.extend(untested_errors)
    required_set = set(required)
    proved_set = set(proved)
    untested_set = set(untested)
    if proved_set - required_set:
        errors.append("proved_capabilities contains capabilities that are not required")
    if untested_set != required_set - proved_set:
        errors.append("untested_capabilities must equal required_capabilities - proved_capabilities")
    return errors


def harness_binding_phase_valid(receipt: JsonObject, context: JsonObject) -> list[str]:
    """Validate one content-addressed selector-to-harness phase receipt."""

    errors = _missing(
        receipt,
        (
            "artifact_id",
            "phase",
            "selector_id",
            "harness",
            "source_commit_sha",
            "input_digest",
            "installed_digest",
            "predicate_version",
            "recorded_at",
            "assertion_sha256",
        ),
    )
    expected = {
        "artifact_id": context.get("expected_artifact_id"),
        "phase": context.get("expected_phase"),
        "selector_id": context.get("expected_selector_id"),
        "harness": context.get("expected_harness"),
        "source_commit_sha": context.get("source_commit_sha"),
        "input_digest": context.get("input_digest"),
        "installed_digest": context.get("installed_digest"),
        "predicate_version": context.get("predicate_version"),
    }
    for field, expected_value in expected.items():
        if expected_value is not None and receipt.get(field) != expected_value:
            errors.append(f"{field} does not match the current binding")
    for field in ("input_digest", "installed_digest", "assertion_sha256"):
        value = receipt.get(field)
        if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
            errors.append(f"{field} must be a sha256 digest")

    assertion_payload = {
        str(key): value for key, value in receipt.items() if key not in {"assertion_sha256", "store_transaction_id"}
    }
    if receipt.get("assertion_sha256") != canonical_json_sha256(assertion_payload):
        errors.append("assertion_sha256 is not the canonical content digest of this binding phase")
    errors.extend(receipt_fresh(receipt, context))

    phase = receipt.get("phase")
    if phase == "discovery":
        errors.extend(_status(receipt, "discovery_status"))
        if receipt.get("sync_disposition") != "already-present":
            errors.append("discovery sync_disposition must be 'already-present'")
    elif phase == "behavior":
        errors.extend(_status(receipt, "positive_status"))
        errors.extend(_status(receipt, "negative_status"))
        for field in ("positive_assertions", "negative_assertions"):
            values, field_errors = _string_set_field(receipt, field, allow_empty=False)
            errors.extend(field_errors)
            if values and len(values) != len(set(values)):
                errors.append(f"{field} must contain distinct assertions")
        proved, proved_errors = _string_set_field(receipt, "proved_capabilities")
        errors.extend(proved_errors)
        required = context.get("required_capabilities", [])
        if not isinstance(required, list) or not all(isinstance(value, str) and value for value in required):
            errors.append("current required_capabilities must be a string list")
        elif set(proved) - set(required):
            errors.append("behavior receipt proves a capability that current portable metadata does not require")
    elif phase == "fresh_process":
        errors.extend(_status(receipt, "fresh_process_status"))
        errors.extend(_missing(receipt, ("initial_process_id", "fresh_process_id")))
        if receipt.get("initial_process_id") == receipt.get("fresh_process_id"):
            errors.append("fresh process proof must use a process distinct from initial discovery")
    elif phase == "rollback":
        for field in (
            "absence_status",
            "restore_status",
            "unchanged_state_status",
            "final_state_status",
        ):
            errors.extend(_status(receipt, field))
        if receipt.get("restored_installed_digest") != context.get("installed_digest"):
            errors.append("rollback restored_installed_digest does not match the current installed digest")
    elif phase == "promoted_final":
        errors.extend(_status(receipt, "promoted_final_status"))
        expected_phase_digests = context.get("expected_phase_receipt_digests")
        actual_phase_digests = receipt.get("phase_receipt_digests")
        if not isinstance(actual_phase_digests, Mapping):
            errors.append("promoted-final phase_receipt_digests must be an object")
        elif actual_phase_digests != expected_phase_digests:
            errors.append("promoted-final phase_receipt_digests do not bind the accepted proof chain")
    else:
        errors.append(f"unsupported harness-binding phase: {phase!r}")
    return errors


def _exact_leaf_closure_valid(
    receipt: JsonObject,
    context: JsonObject,
    *,
    metadata_fields: Sequence[str] = (),
) -> list[str]:
    errors = _missing(receipt, ("expected_leaf_ids", "leaf_receipts"))
    declared_values = receipt.get("expected_leaf_ids", [])
    current_values = context.get("expected_leaf_ids", declared_values)
    if not isinstance(declared_values, list) or not all(isinstance(value, str) and value for value in declared_values):
        errors.append("expected_leaf_ids must be a non-empty string list")
        declared_values = []
    if not isinstance(current_values, list) or not all(isinstance(value, str) and value for value in current_values):
        errors.append("current expected_leaf_ids must be a non-empty string list")
        current_values = []
    if len(declared_values) != len(set(declared_values)):
        errors.append("expected_leaf_ids contains duplicates")
    if set(declared_values) != set(current_values) or len(declared_values) != len(current_values):
        errors.append("expected_leaf_ids does not exactly match the current task graph")

    expected = set(current_values)
    leaf_receipts = receipt.get("leaf_receipts", [])
    if not isinstance(leaf_receipts, list):
        errors.append("leaf_receipts must be a list")
        leaf_receipts = []
    node_ids = [item.get("node_id") for item in leaf_receipts if isinstance(item, Mapping)]
    if len(node_ids) != len(leaf_receipts) or any(not isinstance(value, str) or not value for value in node_ids):
        errors.append("every leaf receipt must be an object with a non-empty node_id")
    valid_node_ids = [value for value in node_ids if isinstance(value, str) and value]
    if len(valid_node_ids) != len(set(valid_node_ids)):
        errors.append("leaf_receipts contains duplicate node IDs")
    actual = set(valid_node_ids)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append(f"missing leaf receipts remain: {missing!r}")
    if extra:
        errors.append(f"unexpected leaf receipts present: {extra!r}")

    expected_metadata = context.get("expected_leaf_metadata", {})
    if not isinstance(expected_metadata, Mapping):
        errors.append("current expected_leaf_metadata must be an object")
        expected_metadata = {}
    for item in leaf_receipts:
        if not isinstance(item, Mapping):
            continue
        node_id = item.get("node_id")
        if item.get("status") != ACCEPTED:
            errors.append(f"leaf {node_id!r} status must be {ACCEPTED!r}")
        if item.get("predicate_errors") != []:
            errors.append(f"leaf {node_id!r} predicate_errors must be []")
        metadata = expected_metadata.get(node_id, {})
        if node_id in expected and not isinstance(metadata, Mapping):
            errors.append(f"leaf {node_id!r} current metadata is invalid")
            continue
        for field in metadata_fields:
            if node_id in expected and field in metadata and item.get(field) != metadata.get(field):
                errors.append(f"leaf {node_id!r} {field} does not match the current task graph")
    errors.extend(_capability_partition_valid(receipt, require_capabilities=False))
    if receipt.get("active_blockers"):
        errors.append("active blockers prevent requested full usability")
    if receipt.get("untested_capabilities"):
        errors.append("untested capabilities prevent requested full usability")
    return errors


def selector_closure_valid(receipt: JsonObject, context: JsonObject) -> list[str]:
    errors = _exact_leaf_closure_valid(
        receipt,
        context,
        metadata_fields=("selector_id", "normalized_url", "skill_name", "path", "authoring_sha256"),
    )
    leaf_receipts = receipt.get("leaf_receipts", [])
    if not isinstance(leaf_receipts, list):
        return errors
    for item in leaf_receipts:
        if not isinstance(item, Mapping):
            continue
        errors.extend(
            f"selector leaf {item.get('node_id')!r} {error}"
            for error in _capability_partition_valid(item, require_capabilities=True)
        )
        selector_id = item.get("selector_id")
        reconstructed = f"selector:{str(item.get('normalized_url') or '').lower()}:{item.get('skill_name') or ''}"
        if selector_id != item.get("node_id") or selector_id != reconstructed:
            errors.append(f"selector leaf {item.get('node_id')!r} identity fields do not reconstruct its node ID")
        if item.get("source_evidence_status") != PASS:
            errors.append(f"selector leaf {item.get('node_id')!r} source evidence did not pass")
    return errors


def harness_binding_closure_valid(receipt: JsonObject, context: JsonObject) -> list[str]:
    errors = _exact_leaf_closure_valid(
        receipt,
        context,
        metadata_fields=(
            "selector_id",
            "normalized_url",
            "skill_name",
            "agent",
            "input_digest",
            "installed_digest",
            "required_capabilities",
        ),
    )
    expected_harnesses = context.get("target_harnesses", [])
    declared_harnesses = receipt.get("target_harnesses", [])
    if (
        not isinstance(declared_harnesses, list)
        or len(declared_harnesses) != len(set(declared_harnesses))
        or set(declared_harnesses) != set(expected_harnesses)
    ):
        errors.append("target_harnesses does not exactly match the current task graph")
    leaf_receipts = receipt.get("leaf_receipts", [])
    if not isinstance(leaf_receipts, list):
        return errors
    expected_sync_sha = context.get("expected_sync_report_sha256") or receipt.get("sync_report_sha256")
    if receipt.get("sync_report_sha256") != expected_sync_sha:
        errors.append("receipt sync_report_sha256 does not match current harness assurance")
    sanitized_sync_report = receipt.get("sanitized_sync_report")
    if not isinstance(sanitized_sync_report, Mapping):
        errors.append("sanitized_sync_report must be an object")
    else:
        sanitized_digest = canonical_json_sha256(sanitized_sync_report)
        for field in ("sanitized_sync_report_sha256", "source_report_evidence_sha256"):
            if receipt.get(field) != sanitized_digest:
                errors.append(f"{field} does not match sanitized_sync_report")
    assertion_owners: dict[str, list[str]] = {}
    for item in leaf_receipts:
        if not isinstance(item, Mapping):
            continue
        node_id = item.get("node_id")
        errors.extend(
            f"binding leaf {node_id!r} {error}"
            for error in _capability_partition_valid(item, require_capabilities=True)
        )
        reconstructed = f"binding:{item.get('selector_id') or ''}:{item.get('agent') or ''}"
        if node_id != reconstructed:
            errors.append(f"binding leaf {node_id!r} identity fields do not reconstruct its node ID")
        if item.get("sync_disposition") != "already-present":
            errors.append(f"binding leaf {node_id!r} is not already present")
        if item.get("sync_report_sha256") != expected_sync_sha:
            errors.append(f"binding leaf {node_id!r} is not bound to the current sync report")
        for field in ("input_digest", "installed_digest"):
            value = item.get(field)
            if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
                errors.append(f"binding leaf {node_id!r} {field} must be a sha256 digest")
        phase_evidence = item.get("phase_evidence")
        if not isinstance(phase_evidence, Mapping) or set(phase_evidence) != set(BINDING_PROOF_PHASES):
            errors.append(f"binding leaf {node_id!r} must bind exactly the five proof phases")
            continue
        for phase in BINDING_PROOF_PHASES:
            summary = phase_evidence.get(phase)
            if not isinstance(summary, Mapping):
                errors.append(f"binding leaf {node_id!r} phase {phase!r} summary must be an object")
                continue
            if summary.get("status") != ACCEPTED or summary.get("predicate_errors") != []:
                errors.append(f"binding leaf {node_id!r} phase {phase!r} is not accepted")
            for field in ("receipt_sha256", "assertion_sha256"):
                value = summary.get(field)
                if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
                    errors.append(f"binding leaf {node_id!r} phase {phase!r} {field} must be a sha256 digest")
            assertion_sha = summary.get("assertion_sha256")
            if isinstance(assertion_sha, str):
                assertion_owners.setdefault(assertion_sha, []).append(f"{node_id}:{phase}")
    for assertion_sha, owners in assertion_owners.items():
        if len(owners) > 1:
            errors.append(
                f"binding assertion digest {assertion_sha!r} is reused across proof edges: {sorted(owners)!r}"
            )
    return errors


def global_closure_valid(receipt: JsonObject, context: JsonObject) -> list[str]:
    return _exact_leaf_closure_valid(receipt, context)


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
    "harness-binding-phase": harness_binding_phase_valid,
    "selector-closure": selector_closure_valid,
    "harness-binding-closure": harness_binding_closure_valid,
    "global-closure": global_closure_valid,
}


def evaluate_predicate(predicate_id: str, receipt: JsonObject, context: JsonObject | None = None) -> list[str]:
    predicate = PREDICATES.get(predicate_id)
    if predicate is None:
        return [f"unknown predicate id: {predicate_id}"]
    return predicate(receipt, context or {})
