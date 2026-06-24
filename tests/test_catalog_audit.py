"""Tests for read-only catalog audit reporting."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from wagents.catalog_audit import build_catalog_audit, render_catalog_audit_text
from wagents.cli import app

runner = CliRunner()


def _index_with(row: dict) -> dict:
    return {
        "allSkillIndex": [row],
        "customSkillIndex": [],
        "externalSkillIndex": [row],
    }


def _minimal_external_row(**overrides) -> dict:
    row = {
        "name": "demo-external",
        "sourceType": "curated-external",
        "sourcePath": "docs/src/authoring/skills/demo-external.mdx",
        "status": "install-now-after-trust-gate",
        "trustTier": "curated-trust-gated",
        "targetAgents": ["codex", "grok"],
        "installCommand": "npx skills add owner/repo --skill demo-external -y -g -a codex grok",
        "riskNotes": "Trust gated.",
        "promotionPolicy": "Install only after trust gate.",
        "provenanceEvidence": "Curated command.",
    }
    row.update(overrides)
    return row


def test_catalog_audit_reports_missing_external_evidence_fields():
    report = build_catalog_audit(index=_index_with(_minimal_external_row()))

    assert report["rows_examined"] == 1
    assert report["missing_field_counts"]["license"] == 1
    assert report["missing_field_counts"]["auditedHeadOrNoPinRationale"] == 1
    assert report["issue_counts"]["warning"] >= 1
    assert report["issue_code_counts"]["audit-license-missing"] == 1
    assert report["issue_code_counts"]["grok-target-needs-sync-mapping-review"] == 1


def test_catalog_audit_accepts_populated_external_evidence_fields():
    report = build_catalog_audit(
        index=_index_with(
            _minimal_external_row(
                license="MIT",
                licenseStatus="declared",
                auditDate="2026-06-23",
                auditedHead="abc123",
                pinPolicy="pin commit refs where source supports them",
                sourceListEvidence="npx skills add owner/repo --list",
                executableSurface="No hooks.",
                allowedTools="Read",
                hookSurface="none",
                scriptSurface="none",
                credentialBehavior="No credentials.",
                networkAccess="No network access.",
                fileAccess="Reads requested files.",
                liveActionRisk="No live actions.",
                riskCategory="low",
                dedupeNotes="No repo-owned overlap.",
                unsupportedTargetAgents=["grok"],
            )
        )
    )

    assert report["issue_counts"] == {}
    assert report["missing_field_counts"].get("license", 0) == 0
    assert "Issue counts: none" in render_catalog_audit_text(report)


def test_catalog_audit_cli_strict_fails_on_warning(monkeypatch):
    monkeypatch.setattr("wagents.catalog_audit.read_catalog_index", lambda: _index_with(_minimal_external_row()))

    result = runner.invoke(app, ["catalog", "audit", "--strict", "--format", "json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["strict"] is True
    assert payload["strict_failed"] is True
    assert payload["issue_code_counts"]["audit-license-missing"] == 1


def test_catalog_audit_cli_default_does_not_fail_on_issues(monkeypatch):
    monkeypatch.setattr("wagents.catalog_audit.read_catalog_index", lambda: _index_with(_minimal_external_row()))

    result = runner.invoke(app, ["catalog", "audit", "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["strict"] is False
    assert payload["strict_failed"] is False
    assert payload["issue_code_counts"]["audit-license-missing"] == 1


def test_catalog_audit_cli_status_filter(monkeypatch):
    rows = [
        _minimal_external_row(name="install-now", status="install-now-after-trust-gate"),
        _minimal_external_row(name="inspect-first", status="inspect-then-install"),
    ]
    monkeypatch.setattr(
        "wagents.catalog_audit.read_catalog_index",
        lambda: {"allSkillIndex": rows, "customSkillIndex": [], "externalSkillIndex": rows},
    )

    result = runner.invoke(app, ["catalog", "audit", "--status", "inspect-then-install", "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["rows_examined"] == 1
    assert payload["status_counts"] == {"inspect-then-install": 1}
