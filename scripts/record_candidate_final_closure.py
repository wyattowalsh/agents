#!/usr/bin/env python3
"""Record docs, independent-review, and global closure receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
from collections.abc import Mapping
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from wagents.candidate_receipts import ReceiptStore

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_RELATIVE = Path("planning/manifests/candidate-corpus-jul2026")
DOCS_EVIDENCE_RELATIVE = MANIFEST_RELATIVE / "docs-closure-evidence.json"
REVIEW_EVIDENCE_RELATIVE = MANIFEST_RELATIVE / "review-closure-evidence.json"
RECEIPTS_RELATIVE = MANIFEST_RELATIVE / "runtime-activation-receipts.json"
RUNTIME_STATE = Path("~/.local/share/wagents/candidate-runtime").expanduser()
REVIEW_OUTPUT_BY_ROLE = {
    "author": (MANIFEST_RELATIVE / "review-evidence" / "author-validation.txt").as_posix(),
    "safety-reviewer": (MANIFEST_RELATIVE / "review-evidence" / "safety-review.md").as_posix(),
    "judge": (MANIFEST_RELATIVE / "review-evidence" / "judge-review.md").as_posix(),
}
REVIEW_OUTPUT_RELATIVES = frozenset(REVIEW_OUTPUT_BY_ROLE.values())
REVIEW_FINDING_SEVERITIES = frozenset({"critical", "high", "medium", "low", "info"})
DOCS_SOURCE_PATHS = (
    "scripts/run_candidate_docs_assurance.py",
    "wagents/docs.py",
    "planning/manifests/candidate-corpus-jul2026/docs-impact-matrix.json",
    "planning/manifests/candidate-corpus-jul2026/docs-steward-surface-map.json",
)
DOCS_EXPECTED_COMMANDS = (
    "uv run wagents readme",
    "uv run wagents docs generate --no-installed",
    "uv run wagents readme",
    "uv run wagents docs generate --no-installed",
    "uv run wagents readme --check",
    "uv run wagents docs generate --no-installed --check",
    "uv run wagents catalog index --check --format json",
    "uv run wagents docs lint",
    "uv run wagents docs build",
)
WORKTREE_DIGEST_EXCLUDES = frozenset({
    DOCS_EVIDENCE_RELATIVE.as_posix(),
    REVIEW_EVIDENCE_RELATIVE.as_posix(),
    RECEIPTS_RELATIVE.as_posix(),
    (MANIFEST_RELATIVE / "runtime-activation-assurance.json").as_posix(),
    *REVIEW_OUTPUT_RELATIVES,
})
FALLBACK_IGNORED_PARTS = frozenset({
    ".astro",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
})
REVIEW_ROLES = frozenset({"author", "safety-reviewer", "judge"})
RESOLVED_FINDING_STATUSES = frozenset({"fixed", "not-actionable"})
TRUSTED_ISSUER_EVIDENCE_ENV = "WAGENTS_CANDIDATE_TRUSTED_ISSUER_EVIDENCE"
BLOCKED_EXTERNAL = "BLOCKED-EXTERNAL"


def manifest_path(relative: Path) -> Path:
    return ROOT / relative


def load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain an object")
    return payload


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    if path.is_symlink():
        raise ValueError(f"evidence path must not be a symlink: {path}")
    return sha256_bytes(path.read_bytes())


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def comparable_receipt(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {key: item for key, item in value.items() if key != "store_transaction_id"}


def canonical_sha256(value: object) -> str:
    return sha256_bytes(canonical(value).encode())


def is_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def resolve_repo_file(value: str) -> Path:
    if not value or Path(value).is_absolute():
        raise ValueError(f"repository evidence path must be relative: {value!r}")
    raw_candidate = ROOT
    for part in Path(value).parts:
        raw_candidate /= part
        if raw_candidate.is_symlink():
            raise ValueError(f"repository evidence file is missing or a symlink: {value!r}")
    candidate = raw_candidate.resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"repository evidence path escapes root: {value!r}") from exc
    if not candidate.is_file():
        raise ValueError(f"repository evidence file is missing or a symlink: {value!r}")
    return candidate


def evidence(paths: list[Path]) -> tuple[list[str], dict[str, str]]:
    unique: dict[str, Path] = {}
    for path in paths:
        relative_path = relative(path)
        if relative_path in unique:
            continue
        unique[relative_path] = resolve_repo_file(relative_path)
    relative_paths = sorted(unique)
    return relative_paths, {value: sha256(unique[value]) for value in relative_paths}


def _repository_files_from_git() -> list[Path] | None:
    completed = subprocess.run(
        ("git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"),
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    paths: list[Path] = []
    for raw in completed.stdout.split(b"\0"):
        if not raw:
            continue
        path = ROOT / raw.decode("utf-8", errors="surrogateescape")
        if path.is_symlink() or path.is_file():
            paths.append(path)
    return sorted(set(paths), key=lambda path: path.relative_to(ROOT).as_posix())


def repository_files() -> list[Path]:
    from_git = _repository_files_from_git()
    if from_git is not None:
        return from_git
    paths: list[Path] = []
    for path in ROOT.rglob("*"):
        relative_path = path.relative_to(ROOT)
        if any(part in FALLBACK_IGNORED_PARTS for part in relative_path.parts):
            continue
        if path.is_symlink() or path.is_file():
            paths.append(path)
    return sorted(set(paths), key=lambda path: path.relative_to(ROOT).as_posix())


def _worktree_fingerprint(path: Path) -> str:
    metadata = path.lstat()
    mode = stat.S_IMODE(metadata.st_mode)
    if stat.S_ISLNK(metadata.st_mode):
        payload = f"symlink\0{mode:o}\0{os.readlink(path)}".encode()
    elif stat.S_ISREG(metadata.st_mode):
        payload = b"file\0" + f"{mode:o}".encode() + b"\0" + path.read_bytes()
    else:
        payload = f"other\0{mode:o}\0{metadata.st_mode}".encode()
    return sha256_bytes(payload)


def worktree_snapshot() -> dict[str, str]:
    return {
        relative(path): _worktree_fingerprint(path)
        for path in repository_files()
        if relative(path) not in WORKTREE_DIGEST_EXCLUDES
    }


def worktree_digest() -> str:
    return canonical_sha256(worktree_snapshot())


def candidate_review_paths() -> set[str]:
    """Return the minimum implementation, report, source-doc, and generated-doc review set."""
    required: set[str] = set(DOCS_SOURCE_PATHS)
    patterns = (
        "scripts/**/*candidate*",
        "tests/**/*candidate*",
        "wagents/candidate*.py",
        "openspec/changes/*candidate-corpus*/**/*",
        "openspec/changes/activate-candidate-corpus*/**/*",
        f"{MANIFEST_RELATIVE.as_posix()}/*",
    )
    for pattern in patterns:
        for path in ROOT.glob(pattern):
            relative_path = path.relative_to(ROOT)
            if (
                path.is_file()
                and not path.is_symlink()
                and not any(part in FALLBACK_IGNORED_PARTS for part in relative_path.parts)
            ):
                value = relative(path)
                if value not in WORKTREE_DIGEST_EXCLUDES:
                    required.add(value)

    records_path = manifest_path(MANIFEST_RELATIVE / "all-records.json")
    if records_path.is_file():
        records_payload = load_object(records_path)
        records = records_payload.get("records", [])
        if isinstance(records, list):
            for record in records:
                if not isinstance(record, dict):
                    continue
                for field in ("files_added", "files_modified"):
                    values = record.get(field, [])
                    if not isinstance(values, list):
                        continue
                    for value in values:
                        if not isinstance(value, str) or value in WORKTREE_DIGEST_EXCLUDES:
                            continue
                        path = ROOT / value
                        if path.is_file() and not path.is_symlink():
                            required.add(relative(resolve_repo_file(value)))

    promotion_path = manifest_path(MANIFEST_RELATIVE / "promotion-overrides.json")
    if promotion_path.is_file():
        promotion = load_object(promotion_path)
        rows = promotion.get("overrides", [])
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                skill_name = str(row.get("skill_name") or "")
                authoring_path = ROOT / "docs" / "src" / "authoring" / "skills" / f"{skill_name}.mdx"
                if skill_name and authoring_path.is_file() and not authoring_path.is_symlink():
                    required.add(relative(resolve_repo_file(relative(authoring_path))))

    docs_evidence = manifest_path(DOCS_EVIDENCE_RELATIVE)
    if docs_evidence.is_file():
        docs_payload = load_object(docs_evidence)
        declared = docs_payload.get("declared_write_set", [])
        if isinstance(declared, list):
            for value in declared:
                if not isinstance(value, str) or value in WORKTREE_DIGEST_EXCLUDES:
                    continue
                path = ROOT / value
                if path.is_file() and not path.is_symlink():
                    required.add(relative(resolve_repo_file(value)))
    return required


def review_input_summary(paths: list[str] | None = None) -> dict[str, Any]:
    reviewed_paths = sorted(paths if paths is not None else candidate_review_paths())
    reviewed_path_digests = {value: sha256(resolve_repo_file(value)) for value in reviewed_paths}
    return {
        "reviewed_paths": reviewed_paths,
        "reviewed_path_digests": reviewed_path_digests,
        "reviewed_input_digest": canonical_sha256(reviewed_path_digests),
        "worktree_digest": worktree_digest(),
    }


def _string_list(value: object, *, field: str, nonempty: bool = True) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{field} must be a string list")
    if nonempty and not value:
        raise ValueError(f"{field} must not be empty")
    if len(value) != len(set(value)):
        raise ValueError(f"{field} must not contain duplicates")
    return [str(item) for item in value]


def docs_receipt() -> dict[str, Any]:
    docs_evidence = manifest_path(DOCS_EVIDENCE_RELATIVE)
    payload = load_object(docs_evidence)
    if payload.get("version") != 2 or payload.get("assurance_kind") != "candidate-docs-steward-closure":
        raise ValueError("docs evidence version or assurance_kind is invalid")
    for field in (
        "generation_status",
        "check_status",
        "build_status",
        "idempotence_status",
        "compare_and_swap_status",
    ):
        if payload.get(field) != "passed":
            raise ValueError(f"docs evidence {field} is not passed")
    if (
        payload.get("complete") is not True
        or payload.get("changed_between_passes")
        or payload.get("validation_writes")
        or payload.get("unexpected_writes")
    ):
        raise ValueError("docs evidence is incomplete, unstable, or contains unexpected writes")

    generated_paths = _string_list(payload.get("declared_write_set"), field="declared_write_set")
    if generated_paths != sorted(generated_paths):
        raise ValueError("docs evidence declared_write_set must be sorted")
    final_digests = payload.get("final_digests")
    if not isinstance(final_digests, dict) or set(final_digests) != set(generated_paths):
        raise ValueError("docs evidence final_digests must exactly cover declared_write_set")
    if payload.get("second_pass_digests") != final_digests or payload.get("postimage_digests") != final_digests:
        raise ValueError("docs evidence final digests are not bound to the stable second pass")
    if payload.get("final_digest") != canonical_sha256(final_digests):
        raise ValueError("docs evidence final aggregate digest is stale")

    command_rows = payload.get("commands")
    if not isinstance(command_rows, list) or len(command_rows) != len(DOCS_EXPECTED_COMMANDS):
        raise ValueError("docs evidence requires the complete command sequence")
    for expected_command, row in zip(DOCS_EXPECTED_COMMANDS, command_rows, strict=True):
        if not isinstance(row, dict) or row.get("command") != expected_command:
            raise ValueError("docs evidence command sequence is malformed")
        exit_code = row.get("exit_code")
        if isinstance(exit_code, bool) or not isinstance(exit_code, int) or exit_code != 0:
            raise ValueError(f"docs evidence command did not exit zero: {expected_command}")
        if row.get("status") != "passed" or not all(
            is_sha256(row.get(field)) for field in ("stdout_sha256", "stderr_sha256")
        ):
            raise ValueError(f"docs evidence command output is malformed: {expected_command}")

    generated_files: list[Path] = []
    for value in generated_paths:
        path = resolve_repo_file(value)
        if not is_sha256(final_digests.get(value)) or sha256(path) != final_digests[value]:
            raise ValueError(f"docs generated-file digest is stale: {value}")
        generated_files.append(path)

    source_files = [resolve_repo_file(value) for value in DOCS_SOURCE_PATHS]
    paths, digests = evidence([docs_evidence, *source_files, *generated_files])
    preimage_digests = payload.get("preimage_digests")
    if not isinstance(preimage_digests, dict):
        raise ValueError("docs evidence preimage_digests must be an object")
    if not set(preimage_digests).issubset(generated_paths) or not all(
        is_sha256(value) for value in preimage_digests.values()
    ):
        raise ValueError("docs evidence preimage_digests is malformed")
    return {
        "gate_id": "docs-closure",
        "source_paths": list(DOCS_SOURCE_PATHS),
        "generated_paths": generated_paths,
        "generator": "uv run wagents readme && uv run wagents docs generate --no-installed",
        "validator": (
            "uv run wagents docs generate --no-installed --check && "
            "uv run wagents docs lint && uv run wagents docs build"
        ),
        "generation_status": "passed",
        "check_status": "passed",
        "build_status": "passed",
        "idempotence_status": "passed",
        "compare_and_swap_status": "passed",
        "generic_surface_only": False,
        "declared_write_set": generated_paths,
        "preimage_digests": preimage_digests,
        "postimage_digests": final_digests,
        "unexpected_writes": [],
        "final_digest": canonical_sha256(final_digests),
        "evidence_paths": paths,
        "evidence_digests": digests,
    }


def _validate_completed_at(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("review run completed_at must be a non-empty ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("review run completed_at must be an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("review run completed_at must include a timezone")
    current = datetime.now().astimezone()
    completed = parsed.astimezone()
    if completed < current - timedelta(days=1) or completed > current + timedelta(minutes=5):
        raise ValueError("review run completed_at is outside the accepted freshness window")
    return value


def _validate_findings(run: dict[str, Any], actors: set[str]) -> list[dict[str, Any]]:
    findings = run.get("findings")
    if not isinstance(findings, list):
        raise ValueError("review run findings must be a list")
    validated: list[dict[str, Any]] = []
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError("review finding rows must be objects")
        finding_id = finding.get("finding_id")
        severity = finding.get("severity")
        status_value = finding.get("status")
        resolution = finding.get("resolution")
        if not all(
            isinstance(value, str) and value.strip() for value in (finding_id, severity, status_value, resolution)
        ):
            raise ValueError("review findings require finding_id, severity, status, and resolution")
        if severity not in REVIEW_FINDING_SEVERITIES:
            raise ValueError(f"review finding has invalid severity: {finding_id}")
        if status_value not in RESOLVED_FINDING_STATUSES:
            raise ValueError(f"review finding is unresolved: {finding_id}")
        reviewer = finding.get("reviewer_actor", run.get("actor"))
        if reviewer not in actors or reviewer != run.get("actor"):
            raise ValueError(f"review finding reviewer does not match its review run: {finding_id}")
        validated.append(dict(finding))
    return validated


def _trusted_issuer_path(explicit: Path | None = None) -> Path | None:
    raw = explicit or (Path(value) if (value := os.environ.get(TRUSTED_ISSUER_EVIDENCE_ENV)) else None)
    if raw is None:
        return None
    candidate = raw.expanduser().absolute()
    if candidate.is_symlink() or not candidate.is_file():
        raise ValueError("trusted issuer evidence must be an existing regular non-symlink file")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        return resolved
    raise ValueError("trusted issuer evidence must be external to the repository")


def _validate_issued_at(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("external review issuance issued_at must be a non-empty ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("external review issuance issued_at must be an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("external review issuance issued_at must include a timezone")
    return value


def external_review_provenance(
    payload: dict[str, Any],
    runs: list[dict[str, Any]],
    actors: set[str],
    *,
    reviewed_input_digest: str,
    recorded_worktree_digest: str,
    trusted_issuer_evidence: Path | None = None,
) -> tuple[str, dict[str, Any] | None]:
    """Bind repo review evidence to one operator-supplied external harness issuance."""

    issuer_path = _trusted_issuer_path(trusted_issuer_evidence)
    if issuer_path is None:
        return BLOCKED_EXTERNAL, None

    trusted_bytes = issuer_path.read_bytes()
    trusted_payload = json.loads(trusted_bytes)
    if not isinstance(trusted_payload, dict):
        raise ValueError("trusted issuer evidence must contain an object")
    if trusted_payload.get("version") != 1:
        raise ValueError("trusted issuer evidence version must be 1")
    issuer = trusted_payload.get("issuer")
    if not isinstance(issuer, dict):
        raise ValueError("trusted issuer evidence requires an issuer object")
    issuer_id = issuer.get("issuer_id")
    if not isinstance(issuer_id, str) or not issuer_id:
        raise ValueError("trusted issuer evidence requires a non-empty issuer_id")
    if issuer_id in actors:
        raise ValueError("trusted issuer identity is self-authored by a review actor")
    if issuer.get("issuer_kind") != "trusted-harness":
        raise ValueError("trusted issuer evidence issuer_kind must be 'trusted-harness'")
    issuer_fingerprint = issuer.get("issuer_fingerprint")
    if not is_sha256(issuer_fingerprint):
        raise ValueError("trusted issuer fingerprint must be a lowercase SHA-256 digest")

    reference = payload.get("external_provenance")
    if not isinstance(reference, dict):
        raise ValueError("review evidence requires external_provenance when trusted issuer evidence is available")
    if reference.get("issuer_id") != issuer_id:
        raise ValueError("review external_provenance issuer_id does not match trusted issuer evidence")
    issuance_id = reference.get("issuance_id")
    if not isinstance(issuance_id, str) or not issuance_id:
        raise ValueError("review external_provenance requires a non-empty issuance_id")

    raw_issuances = trusted_payload.get("issuances")
    if not isinstance(raw_issuances, list) or not all(isinstance(row, dict) for row in raw_issuances):
        raise ValueError("trusted issuer evidence issuances must be an object list")
    matching = [dict(row) for row in raw_issuances if row.get("issuance_id") == issuance_id]
    if len(matching) != 1:
        raise ValueError("review external_provenance must select exactly one trusted issuance")
    issuance = matching[0]
    issuance_sha256 = canonical_sha256(issuance)
    if reference.get("issuance_sha256") != issuance_sha256:
        raise ValueError("review external_provenance issuance digest is stale")
    if issuance.get("reviewed_input_digest") != reviewed_input_digest:
        raise ValueError("external review issuance is not bound to reviewed_input_digest")
    if issuance.get("worktree_digest") != recorded_worktree_digest:
        raise ValueError("external review issuance is not bound to worktree_digest")
    session_id = issuance.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("external review issuance requires a non-empty session_id")
    _validate_issued_at(issuance.get("issued_at"))

    task_bindings = issuance.get("task_bindings")
    if not isinstance(task_bindings, list) or len(task_bindings) != len(runs):
        raise ValueError("external review issuance task_bindings must cover all review runs")
    expected = {
        (
            run["role"],
            run["actor"],
            run["run_id"],
            reviewed_input_digest,
        )
        for run in runs
    }
    actual: set[tuple[object, object, object, object]] = set()
    task_ids: list[str] = []
    for binding in task_bindings:
        if not isinstance(binding, Mapping):
            raise ValueError("external review issuance task binding must be an object")
        task_id = binding.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("external review issuance task binding requires a non-empty task_id")
        task_ids.append(task_id)
        actual.add(
            (
                binding.get("role"),
                binding.get("actor"),
                binding.get("run_id"),
                binding.get("reviewed_input_digest"),
            )
        )
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("external review issuance task IDs must be distinct")
    if actual != expected:
        raise ValueError("external review issuance task bindings do not match review runs")

    return "passed", {
        "issuer_id": issuer_id,
        "issuer_kind": issuer["issuer_kind"],
        "issuer_fingerprint": issuer_fingerprint,
        "issuer_evidence_sha256": sha256_bytes(trusted_bytes),
        "issuance_id": issuance_id,
        "session_id": session_id,
        "issued_at": issuance["issued_at"],
        "reviewed_input_digest": reviewed_input_digest,
        "worktree_digest": recorded_worktree_digest,
        "task_bindings": task_bindings,
        "issuance_sha256": issuance_sha256,
    }


def review_receipt(*, trusted_issuer_evidence: Path | None = None) -> dict[str, Any]:
    review_evidence = manifest_path(REVIEW_EVIDENCE_RELATIVE)
    payload = load_object(review_evidence)
    if payload.get("version") != 1 or payload.get("assurance_kind") != "candidate-independent-review-closure":
        raise ValueError("review evidence version or assurance_kind is invalid")
    runs = payload.get("review_runs")
    if not isinstance(runs, list) or len(runs) != 3 or not all(isinstance(row, dict) for row in runs):
        raise ValueError("review evidence requires exactly three review_runs")

    actors = {str(row.get("actor") or "").strip() for row in runs}
    roles = {str(row.get("role") or "").strip() for row in runs}
    run_ids = {str(row.get("run_id") or "").strip() for row in runs}
    if "" in actors or len(actors) != 3:
        raise ValueError("review evidence requires three distinct actors")
    if roles != REVIEW_ROLES:
        raise ValueError("review evidence requires author, safety-reviewer, and judge roles")
    if "" in run_ids or len(run_ids) != 3:
        raise ValueError("review evidence requires three distinct run IDs")

    reviewed_input_digest = payload.get("reviewed_input_digest")
    if not is_sha256(reviewed_input_digest):
        raise ValueError("reviewed_input_digest must be a lowercase SHA-256 digest")
    reviewed_input_digest_value = str(reviewed_input_digest)
    recorded_worktree_digest = payload.get("worktree_digest")
    if not is_sha256(recorded_worktree_digest) or recorded_worktree_digest != worktree_digest():
        raise ValueError("review worktree_digest is missing or stale")
    recorded_worktree_digest_value = str(recorded_worktree_digest)

    findings_ledger: list[dict[str, Any]] = []
    commands: set[str] = set()
    review_outputs: list[Path] = []
    output_paths: set[str] = set()
    for run in runs:
        command = run.get("command")
        exit_code = run.get("exit_code")
        if not isinstance(command, str) or not command.strip():
            raise ValueError("review run command must be non-empty")
        commands.add(command.strip())
        if isinstance(exit_code, bool) or not isinstance(exit_code, int) or exit_code != 0:
            raise ValueError("review run exit_code must be integer zero")
        output_sha256 = run.get("output_sha256")
        if not is_sha256(output_sha256):
            raise ValueError("review run output_sha256 must be a lowercase SHA-256 digest")
        output_path = run.get("output_path")
        if not isinstance(output_path, str) or not output_path:
            raise ValueError("review run output_path must be a repository-relative evidence file")
        if output_path not in REVIEW_OUTPUT_RELATIVES:
            raise ValueError("review run output_path is not an approved review evidence path")
        role = str(run.get("role") or "")
        if output_path != REVIEW_OUTPUT_BY_ROLE.get(role):
            raise ValueError("review run output_path does not match its review role")
        output_paths.add(output_path)
        resolved_output = resolve_repo_file(output_path)
        if resolved_output.stat().st_size == 0:
            raise ValueError("review run output_path must contain review evidence")
        if sha256(resolved_output) != output_sha256:
            raise ValueError("review run output_sha256 is not bound to output_path")
        review_outputs.append(resolved_output)
        if run.get("reviewed_input_digest") != reviewed_input_digest:
            raise ValueError("review runs must bind the same reviewed_input_digest")
        _validate_completed_at(run.get("completed_at"))
        findings_ledger.extend(_validate_findings(run, actors))
    if len(commands) != 3:
        raise ValueError("review evidence requires three distinct commands")
    if output_paths != set(REVIEW_OUTPUT_BY_ROLE.values()):
        raise ValueError("review evidence requires three distinct role-bound output paths")
    finding_ids = [str(row["finding_id"]) for row in findings_ledger]
    if len(finding_ids) != len(set(finding_ids)):
        raise ValueError("review findings ledger contains duplicate finding IDs")
    if payload.get("findings_ledger_sha256") != canonical_sha256(findings_ledger):
        raise ValueError("review findings ledger digest is missing or stale")

    reviewed_paths = _string_list(payload.get("reviewed_paths"), field="reviewed_paths")
    if reviewed_paths != sorted(reviewed_paths):
        raise ValueError("reviewed_paths must be sorted")
    excluded = set(reviewed_paths) & WORKTREE_DIGEST_EXCLUDES
    if excluded:
        raise ValueError(f"reviewed_paths contains self-referential closure evidence: {sorted(excluded)!r}")
    missing_required = candidate_review_paths() - set(reviewed_paths)
    if missing_required:
        preview = sorted(missing_required)[:10]
        raise ValueError(f"reviewed_paths omits required candidate paths: {preview!r}")
    reviewed_digests = payload.get("reviewed_path_digests")
    if not isinstance(reviewed_digests, dict) or set(reviewed_digests) != set(reviewed_paths):
        raise ValueError("reviewed_path_digests must exactly cover reviewed_paths")
    reviewed_files: list[Path] = []
    for value in reviewed_paths:
        path = resolve_repo_file(value)
        if not is_sha256(reviewed_digests.get(value)) or sha256(path) != reviewed_digests[value]:
            raise ValueError(f"reviewed input digest is stale: {value}")
        reviewed_files.append(path)
    if canonical_sha256(reviewed_digests) != reviewed_input_digest:
        raise ValueError("reviewed_input_digest does not match reviewed_path_digests")

    unresolved = payload.get("unresolved_actionable_findings")
    if not isinstance(unresolved, list) or unresolved:
        raise ValueError("review evidence contains unresolved actionable findings")
    if payload.get("findings_fixed_status") != "passed":
        raise ValueError("review findings are not fixed")

    provenance_status, provenance = external_review_provenance(
        payload,
        runs,
        actors,
        reviewed_input_digest=reviewed_input_digest_value,
        recorded_worktree_digest=recorded_worktree_digest_value,
        trusted_issuer_evidence=trusted_issuer_evidence,
    )
    paths, digests = evidence([review_evidence, *reviewed_files, *review_outputs])
    by_role = {str(row["role"]): row for row in runs}
    return {
        "gate_id": "review-closure",
        "author_actor": by_role["author"]["actor"],
        "safety_reviewer_actor": by_role["safety-reviewer"]["actor"],
        "judge_actor": by_role["judge"]["actor"],
        "review_runs": runs,
        "reviewed_paths": reviewed_paths,
        "reviewed_path_digests": reviewed_digests,
        "reviewed_input_digest": reviewed_input_digest,
        "worktree_digest": recorded_worktree_digest,
        "findings_ledger": findings_ledger,
        "findings_ledger_sha256": payload["findings_ledger_sha256"],
        "findings_fixed_status": "passed",
        "unresolved_actionable_findings": [],
        "source_validation_status": "passed",
        "external_provenance_status": provenance_status,
        "external_provenance": provenance,
        "active_blockers": [] if provenance_status == "passed" else [BLOCKED_EXTERNAL],
        "evidence_paths": paths,
        "evidence_digests": digests,
    }


def _closure_capabilities(rows: list[dict[str, Any]]) -> tuple[list[str], list[str], list[str]]:
    required: set[str] = set()
    proved: set[str] = set()
    for row in rows:
        for field, target in (("required_capabilities", required), ("proved_capabilities", proved)):
            values = row.get(field, [])
            if isinstance(values, list):
                target.update(str(value) for value in values if isinstance(value, str) and value)
    proved &= required
    return sorted(required), sorted(proved), sorted(required - proved)


def generated_receipts(
    existing_closures: dict[str, dict[str, Any]] | None = None,
    *,
    trusted_issuer_evidence: Path | None = None,
) -> dict[str, dict[str, Any]]:
    current = dict(existing_closures or {})
    docs = docs_receipt()
    review = review_receipt(trusted_issuer_evidence=trusted_issuer_evidence)
    prerequisites = {
        "selector-closure": current.get("selector-closure"),
        "harness-binding-closure": current.get("harness-binding-closure"),
        "docs-closure": docs,
        "review-closure": review,
    }
    capability_rows = [
        row
        for gate_id, row in prerequisites.items()
        if gate_id in {"selector-closure", "harness-binding-closure"} and isinstance(row, dict)
    ]
    required, proved, untested = _closure_capabilities(capability_rows)
    blockers: set[str] = set()
    for gate_id, row in prerequisites.items():
        if not isinstance(row, dict):
            blockers.add(f"missing:{gate_id}")
            continue
        if gate_id in {"selector-closure", "harness-binding-closure"} and row.get("verification_status") != "passed":
            blockers.add(f"incomplete:{gate_id}")
        values = row.get("active_blockers", [])
        if isinstance(values, list):
            blockers.update(str(value) for value in values if isinstance(value, str) and value)
    if review.get("external_provenance_status") == BLOCKED_EXTERNAL:
        blockers.add(BLOCKED_EXTERNAL)
    return {
        "docs-closure": docs,
        "review-closure": review,
        "global-closure": {
            "gate_id": "global-closure",
            "expected_leaf_ids": sorted(prerequisites),
            "active_blockers": sorted(blockers),
            "required_capabilities": required,
            "proved_capabilities": proved,
            "untested_capabilities": untested,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--print-worktree-digest", action="store_true")
    mode.add_argument("--print-review-input", action="store_true")
    parser.add_argument(
        "--trusted-issuer-evidence",
        type=Path,
        help=(
            "Operator-supplied external harness issuance document. "
            f"Defaults to ${TRUSTED_ISSUER_EVIDENCE_ENV}."
        ),
    )
    args = parser.parse_args()

    if args.print_worktree_digest:
        print(json.dumps({"worktree_digest": worktree_digest()}, indent=2))
        return 0
    if args.print_review_input:
        print(json.dumps(review_input_summary(), indent=2))
        return 0

    store = ReceiptStore(manifest_path(RECEIPTS_RELATIVE), RUNTIME_STATE)
    snapshot = store.snapshot(
        closure_keys={
            "selector-closure",
            "harness-binding-closure",
            "docs-closure",
            "review-closure",
            "global-closure",
        }
    )
    generated = generated_receipts(
        snapshot.closure_rows,
        trusted_issuer_evidence=args.trusted_issuer_evidence,
    )
    existing = snapshot.closure_rows
    errors: list[str] = []
    if args.check and any(
        canonical(comparable_receipt(existing.get(key))) != canonical(row) for key, row in generated.items()
    ):
        errors.append("stored final closure receipts are stale")
    if generated["review-closure"]["external_provenance_status"] == BLOCKED_EXTERNAL:
        errors.append(BLOCKED_EXTERNAL)
    global_blockers = generated["global-closure"]["active_blockers"]
    if global_blockers:
        errors.append(f"global closure has {len(global_blockers)} active blockers")
    applied = args.apply
    if applied:
        store.commit(snapshot, closure_upserts=generated)
    print(
        json.dumps(
            {
                "ok": not errors,
                "applied": applied,
                "closure_gate_ids": sorted({*existing, *generated}),
                "errors": errors,
            },
            indent=2,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
