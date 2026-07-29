from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "_candidate_final_closure",
        ROOT / "scripts" / "record_candidate_final_closure.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _configure(module, monkeypatch, tmp_path: Path) -> tuple[Path, Path]:
    docs = tmp_path / "docs-evidence.json"
    review = tmp_path / "review-evidence.json"
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "DOCS_EVIDENCE_RELATIVE", Path("docs-evidence.json"))
    monkeypatch.setattr(module, "REVIEW_EVIDENCE_RELATIVE", Path("review-evidence.json"))
    monkeypatch.setattr(module, "RECEIPTS_RELATIVE", Path("receipts.json"))
    monkeypatch.setattr(
        module,
        "REVIEW_OUTPUT_RELATIVES",
        frozenset({
            "review-outputs/author.txt",
            "review-outputs/safety.txt",
            "review-outputs/judge.txt",
        }),
    )
    monkeypatch.setattr(
        module,
        "REVIEW_OUTPUT_BY_ROLE",
        {
            "author": "review-outputs/author.txt",
            "safety-reviewer": "review-outputs/safety.txt",
            "judge": "review-outputs/judge.txt",
        },
    )
    monkeypatch.setattr(
        module,
        "WORKTREE_DIGEST_EXCLUDES",
        frozenset({"docs-evidence.json", "review-evidence.json", "receipts.json"}),
    )
    monkeypatch.setattr(module, "DOCS_SOURCE_PATHS", ("docs-generator.py",))
    return docs, review


def _docs_evidence(module, docs: Path, tmp_path: Path) -> None:
    generated = tmp_path / "README.md"
    source = tmp_path / "docs-generator.py"
    generated.write_text("generated\n", encoding="utf-8")
    source.write_text("source\n", encoding="utf-8")
    digest = module.sha256(generated)
    _write(
        docs,
        {
            "generation_status": "passed",
            "check_status": "passed",
            "build_status": "passed",
            "idempotence_status": "passed",
            "compare_and_swap_status": "passed",
            "complete": True,
            "changed_between_passes": [],
            "validation_writes": [],
            "unexpected_writes": [],
            "declared_write_set": ["README.md"],
            "preimage_digests": {"README.md": module.sha256_bytes(b"before\n")},
            "postimage_digests": {"README.md": digest},
            "second_pass_digests": {"README.md": digest},
            "final_digests": {"README.md": digest},
            "final_digest": module.canonical_sha256({"README.md": digest}),
            "version": 2,
            "assurance_kind": "candidate-docs-steward-closure",
            "commands": [
                {
                    "command": command,
                    "exit_code": 0,
                    "status": "passed",
                    "stdout_sha256": module.sha256_bytes(f"{command}:stdout".encode()),
                    "stderr_sha256": module.sha256_bytes(f"{command}:stderr".encode()),
                }
                for command in module.DOCS_EXPECTED_COMMANDS
            ],
        },
    )


def _review_evidence(module, review: Path, tmp_path: Path) -> dict[str, object]:
    reviewed = tmp_path / "implementation.py"
    reviewed.write_text("implemented = True\n", encoding="utf-8")
    reviewed_path_digests = {"implementation.py": module.sha256(reviewed)}
    reviewed_input_digest = module.canonical_sha256(reviewed_path_digests)
    completed_at = datetime.now(UTC).isoformat()
    output_dir = tmp_path / "review-outputs"
    output_dir.mkdir()
    output_values = {
        "author": b"author output",
        "safety": b"safety output",
        "judge": b"judge output",
    }
    for name, value in output_values.items():
        (output_dir / f"{name}.txt").write_bytes(value)
    findings = [
        {
            "finding_id": "SEC-001",
            "severity": "high",
            "status": "fixed",
            "resolution": "Replaced the permissive check with a fail-closed predicate.",
            "reviewer_actor": "safety",
        }
    ]
    runs = [
        {
            "actor": "integrator",
            "role": "author",
            "run_id": "run-author",
            "command": "pytest tests/test_candidate.py",
            "exit_code": 0,
            "output_path": "review-outputs/author.txt",
            "output_sha256": module.sha256_bytes(output_values["author"]),
            "findings": [],
            "reviewed_input_digest": reviewed_input_digest,
            "completed_at": completed_at,
        },
        {
            "actor": "safety",
            "role": "safety-reviewer",
            "run_id": "run-safety",
            "command": "ruff check scripts",
            "exit_code": 0,
            "output_path": "review-outputs/safety.txt",
            "output_sha256": module.sha256_bytes(output_values["safety"]),
            "findings": findings,
            "reviewed_input_digest": reviewed_input_digest,
            "completed_at": completed_at,
        },
        {
            "actor": "judge",
            "role": "judge",
            "run_id": "run-judge",
            "command": "ty check scripts",
            "exit_code": 0,
            "output_path": "review-outputs/judge.txt",
            "output_sha256": module.sha256_bytes(output_values["judge"]),
            "findings": [],
            "reviewed_input_digest": reviewed_input_digest,
            "completed_at": completed_at,
        },
    ]
    payload: dict[str, object] = {
        "version": 1,
        "assurance_kind": "candidate-independent-review-closure",
        "review_runs": runs,
        "reviewed_paths": ["implementation.py"],
        "reviewed_path_digests": reviewed_path_digests,
        "reviewed_input_digest": reviewed_input_digest,
        "worktree_digest": module.worktree_digest(),
        "findings_ledger_sha256": module.canonical_sha256(findings),
        "findings_fixed_status": "passed",
        "unresolved_actionable_findings": [],
    }
    _write(review, payload)
    return payload


def _attach_external_provenance(
    module,
    review: Path,
    tmp_path: Path,
    payload: dict[str, object],
    *,
    issuer_id: str = "codex-harness-issuer",
) -> Path:
    raw_runs = payload["review_runs"]
    assert isinstance(raw_runs, list)
    runs = [dict(row) for row in raw_runs if isinstance(row, dict)]
    issuance = {
        "issuance_id": "issuance-current-review",
        "session_id": "external-session-current-review",
        "issued_at": datetime.now(UTC).isoformat(),
        "reviewed_input_digest": payload["reviewed_input_digest"],
        "worktree_digest": payload["worktree_digest"],
        "task_bindings": [
            {
                "role": run["role"],
                "actor": run["actor"],
                "run_id": run["run_id"],
                "task_id": f"external-task-{run['role']}",
                "reviewed_input_digest": payload["reviewed_input_digest"],
            }
            for run in runs
        ],
    }
    issuer_path = tmp_path.parent / f"{tmp_path.name}-trusted-issuer.json"
    _write(
        issuer_path,
        {
            "version": 1,
            "issuer": {
                "issuer_id": issuer_id,
                "issuer_kind": "trusted-harness",
                "issuer_fingerprint": "d" * 64,
            },
            "issuances": [issuance],
        },
    )
    payload["external_provenance"] = {
        "issuer_id": issuer_id,
        "issuance_id": issuance["issuance_id"],
        "issuance_sha256": module.canonical_sha256(issuance),
    }
    _write(review, payload)
    return issuer_path


def test_generated_receipts_bind_docs_and_three_actor_review(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    docs, review = _configure(module, monkeypatch, tmp_path)
    _docs_evidence(module, docs, tmp_path)
    payload = _review_evidence(module, review, tmp_path)
    monkeypatch.setattr(module, "candidate_review_paths", lambda: {"implementation.py"})

    receipts = module.generated_receipts()

    assert set(receipts) == {"docs-closure", "review-closure", "global-closure"}
    assert receipts["review-closure"]["author_actor"] == "integrator"
    assert receipts["review-closure"]["reviewed_input_digest"] == payload["reviewed_input_digest"]
    assert "README.md" in receipts["docs-closure"]["evidence_paths"]
    assert "docs-generator.py" in receipts["docs-closure"]["evidence_paths"]


def test_docs_receipt_rejects_stale_generated_file(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    docs, _ = _configure(module, monkeypatch, tmp_path)
    _docs_evidence(module, docs, tmp_path)
    (tmp_path / "README.md").write_text("later edit\n", encoding="utf-8")

    with pytest.raises(ValueError, match="digest is stale"):
        module.docs_receipt()


def test_docs_receipt_requires_complete_command_evidence(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    docs, _ = _configure(module, monkeypatch, tmp_path)
    _docs_evidence(module, docs, tmp_path)
    payload = json.loads(docs.read_text(encoding="utf-8"))
    payload["commands"] = payload["commands"][:-1]
    _write(docs, payload)

    with pytest.raises(ValueError, match="complete command sequence"):
        module.docs_receipt()


def test_review_receipt_rejects_reused_actor(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _, review = _configure(module, monkeypatch, tmp_path)
    payload = _review_evidence(module, review, tmp_path)
    raw_runs = payload["review_runs"]
    assert isinstance(raw_runs, list)
    runs = [dict(row) for row in raw_runs if isinstance(row, dict)]
    runs[1]["actor"] = "integrator"
    payload["review_runs"] = runs
    _write(review, payload)
    monkeypatch.setattr(module, "candidate_review_paths", lambda: {"implementation.py"})

    with pytest.raises(ValueError, match="distinct actors"):
        module.review_receipt()


def test_review_receipt_rejects_failed_or_unhashed_command(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _, review = _configure(module, monkeypatch, tmp_path)
    payload = _review_evidence(module, review, tmp_path)
    raw_runs = payload["review_runs"]
    assert isinstance(raw_runs, list)
    runs = [dict(row) for row in raw_runs if isinstance(row, dict)]
    runs[0]["exit_code"] = 1
    runs[0]["output_sha256"] = "not-a-digest"
    payload["review_runs"] = runs
    _write(review, payload)
    monkeypatch.setattr(module, "candidate_review_paths", lambda: {"implementation.py"})

    with pytest.raises(ValueError, match="exit_code"):
        module.review_receipt()


def test_review_receipt_binds_output_digest_to_persisted_evidence(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _, review = _configure(module, monkeypatch, tmp_path)
    payload = _review_evidence(module, review, tmp_path)
    (tmp_path / "review-outputs" / "safety.txt").write_text("tampered\n", encoding="utf-8")
    payload["worktree_digest"] = module.worktree_digest()
    _write(review, payload)
    monkeypatch.setattr(module, "candidate_review_paths", lambda: {"implementation.py"})

    with pytest.raises(ValueError, match="not bound to output_path"):
        module.review_receipt()


def test_review_receipt_allows_clean_three_review_outcome(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _, review = _configure(module, monkeypatch, tmp_path)
    payload = _review_evidence(module, review, tmp_path)
    raw_runs = payload["review_runs"]
    assert isinstance(raw_runs, list)
    runs = [dict(row) for row in raw_runs if isinstance(row, dict)]
    for run in runs:
        run["findings"] = []
    payload["review_runs"] = runs
    payload["findings_ledger_sha256"] = module.canonical_sha256([])
    _write(review, payload)
    monkeypatch.setattr(module, "candidate_review_paths", lambda: {"implementation.py"})

    receipt = module.review_receipt()

    assert receipt["findings_ledger"] == []


def test_review_receipt_accepts_trusted_external_harness_provenance(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _, review = _configure(module, monkeypatch, tmp_path)
    payload = _review_evidence(module, review, tmp_path)
    issuer_path = _attach_external_provenance(module, review, tmp_path, payload)
    monkeypatch.setattr(module, "candidate_review_paths", lambda: {"implementation.py"})

    receipt = module.review_receipt(trusted_issuer_evidence=issuer_path)

    assert receipt["source_validation_status"] == "passed"
    assert receipt["external_provenance_status"] == "passed"
    assert receipt["active_blockers"] == []
    assert receipt["external_provenance"]["issuer_id"] == "codex-harness-issuer"
    assert len(receipt["external_provenance"]["task_bindings"]) == 3


def test_review_receipt_without_trusted_issuer_is_blocked_external(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _, review = _configure(module, monkeypatch, tmp_path)
    _review_evidence(module, review, tmp_path)
    monkeypatch.delenv(module.TRUSTED_ISSUER_EVIDENCE_ENV, raising=False)
    monkeypatch.setattr(module, "candidate_review_paths", lambda: {"implementation.py"})

    receipt = module.review_receipt()

    assert receipt["source_validation_status"] == "passed"
    assert receipt["external_provenance_status"] == "BLOCKED-EXTERNAL"
    assert receipt["active_blockers"] == ["BLOCKED-EXTERNAL"]
    assert receipt["external_provenance"] is None


def test_review_receipt_rejects_self_authored_trusted_issuer(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _, review = _configure(module, monkeypatch, tmp_path)
    payload = _review_evidence(module, review, tmp_path)
    issuer_path = _attach_external_provenance(
        module,
        review,
        tmp_path,
        payload,
        issuer_id="integrator",
    )
    monkeypatch.setattr(module, "candidate_review_paths", lambda: {"implementation.py"})

    with pytest.raises(ValueError, match="self-authored"):
        module.review_receipt(trusted_issuer_evidence=issuer_path)


def test_generated_global_closure_exposes_external_blocker_and_derived_capabilities(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _module()
    docs, review = _configure(module, monkeypatch, tmp_path)
    _docs_evidence(module, docs, tmp_path)
    _review_evidence(module, review, tmp_path)
    monkeypatch.delenv(module.TRUSTED_ISSUER_EVIDENCE_ENV, raising=False)
    monkeypatch.setattr(module, "candidate_review_paths", lambda: {"implementation.py"})
    selector_capability = "selector:a::invoke:/example"
    binding_capability = "binding:a:codex::invoke:/example"
    existing = {
        "selector-closure": {
            "gate_id": "selector-closure",
            "verification_status": "passed",
            "active_blockers": [],
            "required_capabilities": [selector_capability],
            "proved_capabilities": [selector_capability],
            "untested_capabilities": [],
        },
        "harness-binding-closure": {
            "gate_id": "harness-binding-closure",
            "verification_status": "passed",
            "active_blockers": [],
            "required_capabilities": [binding_capability],
            "proved_capabilities": [],
            "untested_capabilities": [binding_capability],
        },
    }

    receipts = module.generated_receipts(existing)
    global_receipt = receipts["global-closure"]

    assert "BLOCKED-EXTERNAL" in global_receipt["active_blockers"]
    assert global_receipt["required_capabilities"] == [binding_capability, selector_capability]
    assert global_receipt["proved_capabilities"] == [selector_capability]
    assert global_receipt["untested_capabilities"] == [binding_capability]


def test_review_receipt_requires_distinct_commands(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _, review = _configure(module, monkeypatch, tmp_path)
    payload = _review_evidence(module, review, tmp_path)
    raw_runs = payload["review_runs"]
    assert isinstance(raw_runs, list)
    runs = [dict(row) for row in raw_runs if isinstance(row, dict)]
    runs[1]["command"] = runs[0]["command"]
    payload["review_runs"] = runs
    _write(review, payload)
    monkeypatch.setattr(module, "candidate_review_paths", lambda: {"implementation.py"})

    with pytest.raises(ValueError, match="three distinct commands"):
        module.review_receipt()


def test_review_receipt_rejects_output_reused_across_roles(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _, review = _configure(module, monkeypatch, tmp_path)
    payload = _review_evidence(module, review, tmp_path)
    raw_runs = payload["review_runs"]
    assert isinstance(raw_runs, list)
    runs = [dict(row) for row in raw_runs if isinstance(row, dict)]
    runs[1]["output_path"] = runs[0]["output_path"]
    runs[1]["output_sha256"] = runs[0]["output_sha256"]
    payload["review_runs"] = runs
    _write(review, payload)
    monkeypatch.setattr(module, "candidate_review_paths", lambda: {"implementation.py"})

    with pytest.raises(ValueError, match="does not match its review role"):
        module.review_receipt()


def test_review_receipt_rejects_role_output_swap(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _, review = _configure(module, monkeypatch, tmp_path)
    payload = _review_evidence(module, review, tmp_path)
    raw_runs = payload["review_runs"]
    assert isinstance(raw_runs, list)
    runs = [dict(row) for row in raw_runs if isinstance(row, dict)]
    author_path, author_digest = runs[0]["output_path"], runs[0]["output_sha256"]
    runs[0]["output_path"], runs[0]["output_sha256"] = runs[1]["output_path"], runs[1]["output_sha256"]
    runs[1]["output_path"], runs[1]["output_sha256"] = author_path, author_digest
    payload["review_runs"] = runs
    _write(review, payload)
    monkeypatch.setattr(module, "candidate_review_paths", lambda: {"implementation.py"})

    with pytest.raises(ValueError, match="does not match its review role"):
        module.review_receipt()


@pytest.mark.parametrize(
    ("field", "value"),
    (("version", 2), ("assurance_kind", "wrong-kind")),
)
def test_review_receipt_rejects_invalid_envelope(
    monkeypatch,
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    module = _module()
    _, review = _configure(module, monkeypatch, tmp_path)
    payload = _review_evidence(module, review, tmp_path)
    payload[field] = value
    _write(review, payload)
    monkeypatch.setattr(module, "candidate_review_paths", lambda: {"implementation.py"})

    with pytest.raises(ValueError, match="version or assurance_kind"):
        module.review_receipt()


def test_review_receipt_rejects_cross_run_finding_attribution(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _, review = _configure(module, monkeypatch, tmp_path)
    payload = _review_evidence(module, review, tmp_path)
    raw_runs = payload["review_runs"]
    assert isinstance(raw_runs, list)
    runs = [dict(row) for row in raw_runs if isinstance(row, dict)]
    findings = [dict(row) for row in runs[1]["findings"]]
    findings[0]["reviewer_actor"] = "judge"
    runs[1]["findings"] = findings
    payload["review_runs"] = runs
    payload["findings_ledger_sha256"] = module.canonical_sha256(findings)
    _write(review, payload)
    monkeypatch.setattr(module, "candidate_review_paths", lambda: {"implementation.py"})

    with pytest.raises(ValueError, match="reviewer does not match"):
        module.review_receipt()


def test_review_receipt_rejects_symlinked_output(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _, review = _configure(module, monkeypatch, tmp_path)
    payload = _review_evidence(module, review, tmp_path)
    safety = tmp_path / "review-outputs" / "safety.txt"
    safety.unlink()
    safety.symlink_to("author.txt")
    raw_runs = payload["review_runs"]
    assert isinstance(raw_runs, list)
    runs = [dict(row) for row in raw_runs if isinstance(row, dict)]
    runs[1]["output_sha256"] = module.sha256(tmp_path / "review-outputs" / "author.txt")
    payload["review_runs"] = runs
    payload["worktree_digest"] = module.worktree_digest()
    _write(review, payload)
    monkeypatch.setattr(module, "candidate_review_paths", lambda: {"implementation.py"})

    with pytest.raises(ValueError, match="symlink"):
        module.review_receipt()


def test_review_receipt_rejects_later_reviewed_input_edit(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _, review = _configure(module, monkeypatch, tmp_path)
    _review_evidence(module, review, tmp_path)
    monkeypatch.setattr(module, "candidate_review_paths", lambda: {"implementation.py"})
    (tmp_path / "implementation.py").write_text("implemented = False\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"worktree_digest.*stale"):
        module.review_receipt()


def test_review_receipt_requires_complete_candidate_path_set(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _, review = _configure(module, monkeypatch, tmp_path)
    _review_evidence(module, review, tmp_path)
    extra = tmp_path / "another-candidate-report.md"
    extra.write_text("review me\n", encoding="utf-8")
    payload = json.loads(review.read_text(encoding="utf-8"))
    payload["worktree_digest"] = module.worktree_digest()
    _write(review, payload)
    monkeypatch.setattr(
        module,
        "candidate_review_paths",
        lambda: {"implementation.py", "another-candidate-report.md"},
    )

    with pytest.raises(ValueError, match="omits required candidate paths"):
        module.review_receipt()


def test_review_input_summary_binds_paths_and_worktree(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _configure(module, monkeypatch, tmp_path)
    reviewed = tmp_path / "implementation.py"
    reviewed.write_text("implemented = True\n", encoding="utf-8")

    summary = module.review_input_summary(["implementation.py"])

    assert summary["reviewed_paths"] == ["implementation.py"]
    assert summary["reviewed_input_digest"] == module.canonical_sha256(summary["reviewed_path_digests"])
    assert summary["worktree_digest"] == module.worktree_digest()


def test_candidate_review_paths_include_all_records_file_ownership(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "MANIFEST_RELATIVE", Path("candidate-manifests"))
    monkeypatch.setattr(module, "DOCS_SOURCE_PATHS", ())
    monkeypatch.setattr(module, "WORKTREE_DIGEST_EXCLUDES", frozenset())
    config = tmp_path / "config" / "candidate-tool.json"
    report = tmp_path / "reports" / "candidate.md"
    config.parent.mkdir(parents=True)
    report.parent.mkdir(parents=True)
    config.write_text("{}\n", encoding="utf-8")
    report.write_text("review\n", encoding="utf-8")
    _write(
        tmp_path / "candidate-manifests" / "all-records.json",
        {
            "records": [
                {
                    "files_added": ["config/candidate-tool.json"],
                    "files_modified": ["reports/candidate.md"],
                }
            ]
        },
    )

    paths = module.candidate_review_paths()

    assert "config/candidate-tool.json" in paths
    assert "reports/candidate.md" in paths
