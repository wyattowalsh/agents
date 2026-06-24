"""Read-only audit reporting for the generated skills catalog."""

from __future__ import annotations

from collections import Counter
from typing import Any

from wagents.skill_index import read_catalog_index

EXTERNAL_SOURCE_TYPES = {"curated-external", "external"}
PROMOTED_STATUS = "install-now-after-trust-gate"

AUDIT_FIELD_KEYS = (
    "license",
    "licenseStatus",
    "auditDate",
    "auditedHead",
    "pinPolicy",
    "sourceListEvidence",
    "executableSurface",
    "allowedTools",
    "hookSurface",
    "scriptSurface",
    "credentialBehavior",
    "networkAccess",
    "fileAccess",
    "liveActionRisk",
    "riskCategory",
    "dedupeNotes",
)

CORE_EXTERNAL_FIELDS = (
    "riskNotes",
    "promotionPolicy",
    "provenanceEvidence",
    "trustTier",
    "targetAgents",
)


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _targets_grok(row: dict[str, Any]) -> bool:
    target_agents = row.get("targetAgents") or row.get("target_agents") or ()
    if any(str(agent).strip() == "grok" for agent in target_agents):
        return True
    command = str(row.get("installCommand") or row.get("install_command") or "")
    return "grok" in command.split()


def _has_unsupported_target(row: dict[str, Any], agent: str) -> bool:
    unsupported = row.get("unsupportedTargetAgents") or row.get("unsupported_target_agents") or ()
    return any(str(item).strip() == agent for item in unsupported)


def _issue(
    *,
    severity: str,
    code: str,
    skill_id: str,
    status: str,
    message: str,
    field: str = "",
    source_path: str = "",
) -> dict[str, str]:
    return {
        "severity": severity,
        "code": code,
        "skill_id": skill_id,
        "status": status,
        "field": field,
        "source_path": source_path,
        "message": message,
    }


def _external_rows(index: dict[str, Any]) -> list[dict[str, Any]]:
    rows = index.get("externalSkillIndex") or []
    return [row for row in rows if str(row.get("sourceType") or row.get("source_kind") or "") in EXTERNAL_SOURCE_TYPES]


def build_catalog_audit(
    *,
    index: dict[str, Any] | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Build a non-mutating audit report for curated external catalog evidence."""
    payload = index if index is not None else (read_catalog_index() or {})
    rows = _external_rows(payload)
    if status:
        rows = [row for row in rows if str(row.get("status") or "") == status]

    issues: list[dict[str, str]] = []
    missing_field_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()

    for row in rows:
        skill_id = str(row.get("name") or "")
        row_status = str(row.get("status") or "unknown")
        source_path = str(row.get("sourcePath") or row.get("source_path") or "")
        status_counts[row_status] += 1

        if not skill_id:
            issues.append(
                _issue(
                    severity="error",
                    code="catalog-row-missing-name",
                    skill_id="",
                    status=row_status,
                    source_path=source_path,
                    message="External catalog row is missing a skill name.",
                )
            )

        for field in (*CORE_EXTERNAL_FIELDS, *AUDIT_FIELD_KEYS):
            if not _is_present(row.get(field)):
                missing_field_counts[field] += 1

        if not (_is_present(row.get("license")) or _is_present(row.get("licenseStatus"))):
            issues.append(
                _issue(
                    severity="warning",
                    code="audit-license-missing",
                    skill_id=skill_id,
                    status=row_status,
                    field="license",
                    source_path=source_path,
                    message="Record license or license gap before promotion.",
                )
            )

        if not (_is_present(row.get("auditedHead")) or _is_present(row.get("noPinRationale"))):
            issues.append(
                _issue(
                    severity="warning",
                    code="audit-pin-evidence-missing",
                    skill_id=skill_id,
                    status=row_status,
                    field="auditedHead",
                    source_path=source_path,
                    message="Record audited HEAD or explicit no-pin rationale.",
                )
            )
            missing_field_counts["auditedHeadOrNoPinRationale"] += 1

        for field, code, message in (
            ("sourceListEvidence", "audit-source-list-evidence-missing", "Record read-only source-list evidence."),
            ("executableSurface", "audit-executable-surface-missing", "Record hooks/scripts/command surface notes."),
            ("credentialBehavior", "audit-credential-behavior-missing", "Record credential behavior or absence."),
            ("liveActionRisk", "audit-live-action-risk-missing", "Record live-action risk or absence."),
            ("dedupeNotes", "audit-dedupe-notes-missing", "Record dedupe boundary against stronger local skills."),
        ):
            if not _is_present(row.get(field)):
                issues.append(
                    _issue(
                        severity="warning" if row_status == PROMOTED_STATUS else "info",
                        code=code,
                        skill_id=skill_id,
                        status=row_status,
                        field=field,
                        source_path=source_path,
                        message=message,
                    )
                )

        if _targets_grok(row) and not _has_unsupported_target(row, "grok"):
            issues.append(
                _issue(
                    severity="warning",
                    code="grok-target-needs-sync-mapping-review",
                    skill_id=skill_id,
                    status=row_status,
                    field="targetAgents",
                    source_path=source_path,
                    message=(
                        "Grok appears as a target; record unsupportedTargetAgents or verify local sync mapping "
                        "because Skills CLI does not have a native Grok adapter."
                    ),
                )
            )

    severity_counts = Counter(issue["severity"] for issue in issues)
    code_counts = Counter(issue["code"] for issue in issues)
    return {
        "ok": not severity_counts.get("error"),
        "rows_examined": len(rows),
        "status_filter": status or "",
        "status_counts": dict(sorted(status_counts.items())),
        "missing_field_counts": dict(sorted(missing_field_counts.items())),
        "issue_counts": dict(sorted(severity_counts.items())),
        "issue_code_counts": dict(sorted(code_counts.items())),
        "issues": issues,
    }


def render_catalog_audit_text(report: dict[str, Any], *, strict: bool = False, max_items: int = 12) -> list[str]:
    """Render a compact text summary for catalog audit output."""
    issue_counts = report.get("issue_counts") or {}
    missing_counts = report.get("missing_field_counts") or {}
    code_counts = report.get("issue_code_counts") or {}

    lines = [
        "Catalog audit",
        f"External rows examined: {report.get('rows_examined', 0)}",
        f"Status filter: {report.get('status_filter') or 'none'}",
        "Issue counts: "
        + ", ".join(f"{key}={value}" for key, value in sorted(issue_counts.items()))
        if issue_counts
        else "Issue counts: none",
        "Strict mode: " + ("enabled" if strict else "disabled"),
        "",
        "Status counts:",
    ]
    for status, count in (report.get("status_counts") or {}).items():
        lines.append(f"  - {status}: {count}")
    if not report.get("status_counts"):
        lines.append("  - none")

    lines.append("")
    lines.append("Top missing fields:")
    for field, count in sorted(missing_counts.items(), key=lambda item: (-int(item[1]), str(item[0])))[:max_items]:
        lines.append(f"  - {field}: {count}")
    if not missing_counts:
        lines.append("  - none")

    lines.append("")
    lines.append("Top issue codes:")
    for code, count in sorted(code_counts.items(), key=lambda item: (-int(item[1]), str(item[0])))[:max_items]:
        lines.append(f"  - {code}: {count}")
    if not code_counts:
        lines.append("  - none")
    return lines
