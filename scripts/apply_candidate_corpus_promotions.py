#!/usr/bin/env python3
"""Apply reviewed candidate-corpus promotions after conservative generation.

The main candidate-corpus generator intentionally emits trust-gated intake rows.
This overlay converts explicitly reviewed overrides into normal installable
curated catalog rows and updates the generated authoring summary. It does not
fetch, install, execute, or vendor candidate code.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
AUTHORING_DIR = ROOT / "docs" / "src" / "authoring" / "skills"
OVERRIDES = MANIFEST_DIR / "promotion-overrides.json"
SUMMARY = MANIFEST_DIR / "catalog-authoring-summary.json"
REPORT = MANIFEST_DIR / "applied-promotion-overrides.json"


def now() -> str:
    return datetime.now(UTC).isoformat()


def yaml_string(value: Any) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def yaml_flow_list(values: list[Any]) -> str:
    return "[" + ", ".join(yaml_string(value) for value in values) + "]"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_overrides() -> list[dict[str, Any]]:
    if not OVERRIDES.exists():
        return []
    payload = load_json(OVERRIDES)
    overrides = payload.get("overrides", [])
    if not isinstance(overrides, list):
        raise ValueError("promotion-overrides.json overrides must be a list")
    return [override for override in overrides if isinstance(override, dict)]


def is_live_install_command(command: Any) -> bool:
    command_text = str(command)
    return (
        "skills add" in command_text
        and "--skill" in command_text
        and "--dry-run" not in command_text
        and "--help" not in command_text
    )


def render_promoted_row(override: dict[str, Any]) -> str:
    skill_name = str(override["skill_name"])
    install_skill_name = str(override.get("install_skill_name") or skill_name)
    raw_indexes = ", ".join(str(index) for index in override.get("raw_indexes", []))
    executed_commands = [str(command) for command in override.get("executed_commands", [])]
    installed_paths = [str(path) for path in override.get("installed_paths", [])]
    install_evidence_note = str(override.get("install_evidence_note", "")).strip()
    target_agents = list(override.get("target_agents", []))
    frontmatter = [
        "---",
        f"name: {yaml_string(skill_name)}",
        f"description: {yaml_string(override.get('description', ''))}",
        f"title: {yaml_string(override.get('title', skill_name.replace('-', ' ').title()))}",
        'source_kind: "curated-external"',
        f"source: {yaml_string(override.get('source_name', ''))}",
        f"install_source: {yaml_string(override.get('install_source', ''))}",
        f"install_command: {yaml_string(override.get('install_command', ''))}",
        f"install_skill_name: {yaml_string(install_skill_name)}",
        f"status: {yaml_string(override.get('status', 'install-now-after-trust-gate'))}",
        f"trust_tier: {yaml_string(override.get('trust_tier', 'curated-trust-gated'))}",
        f"provenance_status: {yaml_string(override.get('provenance_status', 'verified-install-command'))}",
        f"sync_kind: {yaml_string(override.get('sync_kind', 'skills-cli'))}",
        f"target_agents: {yaml_flow_list(target_agents)}",
        f"source_url: {yaml_string(override.get('normalized_url', ''))}",
        f"selector_mode: {yaml_string(override.get('selector_mode', 'named'))}",
        f"audit_date: {yaml_string(override.get('audit_date', '2026-07-07'))}",
        f"audited_head: {yaml_string(override.get('audited_head', ''))}",
        f"license: {yaml_string(override.get('license', ''))}",
        f"pin_policy: {yaml_string(override.get('pin_policy', 'pin-before-install'))}",
        f"no_pin_rationale: {yaml_string(override.get('no_pin_rationale', ''))}",
        f"source_list_evidence: {yaml_string(override.get('source_list_evidence', 'source-list-found'))}",
        f"executable_surface: {yaml_string(override.get('executable_surface', 'reviewed'))}",
        f"credential_behavior: {yaml_string(override.get('credential_behavior', ''))}",
        f"network_access: {yaml_string(override.get('network_access', ''))}",
        f"file_access: {yaml_string(override.get('file_access', ''))}",
        f"live_action_risk: {yaml_string(override.get('live_action_risk', ''))}",
        f"risk_category: {yaml_string(override.get('risk_category', 'standard-review'))}",
        f"dedupe_notes: {yaml_string('Raw indexes covered: ' + raw_indexes)}",
        f"notes: {yaml_string(override.get('description', ''))}",
        f"risk_notes: {yaml_string(override.get('live_action_risk', ''))}",
        f"promotion_policy: {yaml_string(override.get('promotion_policy', ''))}",
        f"provenance_evidence: {yaml_string(override.get('provenance_evidence', ''))}",
        "---",
        "",
    ]
    body = [
        f"# {skill_name.replace('-', ' ').title()}",
        "",
        (
            f"This row promotes `{override.get('source_name', '')}` from the July 2026 "
            "candidate corpus into an installable curated external skill."
        ),
        "",
        "## Reviewed Integration",
        "",
        f"- Raw indexes covered: {raw_indexes}",
        f"- Normalized URL: [{override.get('normalized_url', '')}]({override.get('normalized_url', '')})",
        f"- Catalog skill id: `{skill_name}`",
        f"- Upstream install selector: `{install_skill_name}`",
        f"- Install command: `{override.get('install_command', '')}`",
        f"- Inspected commit SHA: `{override.get('audited_head', 'unresolved')}`",
        f"- License status: `{override.get('license', 'unresolved')}`",
        f"- Source-list evidence: `{override.get('source_list_evidence', 'unknown')}`",
        f"- Live local install recorded: `{str(bool(override.get('live_install_executed'))).lower()}`",
        "",
        "## Local Install Evidence",
        "",
        *[f"- Executed command: `{command}`" for command in executed_commands],
        *[f"- Installed path: `{path}`" for path in installed_paths],
        *([f"- Install evidence note: {install_evidence_note}"] if install_evidence_note else []),
        "",
        "## Safety Notes",
        "",
        f"- Credential behavior: {override.get('credential_behavior', '')}",
        f"- Network access: {override.get('network_access', '')}",
        f"- File access: {override.get('file_access', '')}",
        f"- Live action risk: {override.get('live_action_risk', '')}",
        (
            "- MCP, background services, and external binaries remain opt-in; do not auto-start them from this "
            "catalog row."
        ),
        (
            "- Secrets, tokens, private keys, connection strings, cookies, OAuth grants, and account IDs must not "
            "be committed."
        ),
        "",
        "## Docs-Steward Notes",
        "",
        "- This row is the installable catalog promotion for the matching candidate-corpus intake row.",
        (
            "- Auth, install, validation, attribution, and promotion evidence remain visible in the candidate "
            "corpus manifests."
        ),
    ]
    return "\n".join(frontmatter + body) + "\n"


def promoted_summary_row(override: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "name": override["skill_name"],
        "path": str((AUTHORING_DIR / f"{override['skill_name']}.mdx").relative_to(ROOT)),
        "normalized_url": override["normalized_url"],
        "source_name": override["source_name"],
        "raw_indexes": override.get("raw_indexes") or (previous or {}).get("raw_indexes", []),
        "status": override.get("status", "install-now-after-trust-gate"),
        "sync_kind": override.get("sync_kind", "skills-cli"),
        "install_command": override.get("install_command", ""),
        "live_install_executed": bool(override.get("live_install_executed")),
        "risk_tier": override.get("risk_tier", (previous or {}).get("risk_tier", "standard-review")),
        "intake_decision": override.get("intake_decision", (previous or {}).get("intake_decision", "")),
        "source_list_evidence": override.get(
            "source_list_evidence",
            (previous or {}).get("source_list_evidence", "source-list-found"),
        ),
        "found_skill_count": int(override.get("found_skill_count", (previous or {}).get("found_skill_count", 0))),
        "install_evidence_note": override.get("install_evidence_note", ""),
        "remaining_blockers": override.get("remaining_blockers", []),
    }


def apply_overrides() -> dict[str, Any]:
    overrides = load_overrides()
    if not overrides:
        payload = {"version": 1, "generated_at": now(), "applied_count": 0, "items": []}
        write_json(REPORT, payload)
        return payload
    if not SUMMARY.exists():
        raise FileNotFoundError(f"Missing {SUMMARY.relative_to(ROOT)}")

    summary = load_json(SUMMARY)
    rows = summary.get("rows", [])
    if not isinstance(rows, list):
        raise ValueError("catalog-authoring-summary.json rows must be a list")
    overrides_by_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for override in overrides:
        overrides_by_url[str(override["normalized_url"])].append(override)

    applied = []
    for override in overrides:
        skill_name = str(override["skill_name"])
        candidate_name = str(override.get("candidate_authoring_name", ""))
        normalized_url = str(override["normalized_url"])
        promoted_path = AUTHORING_DIR / f"{skill_name}.mdx"
        promoted_path.write_text(render_promoted_row(override), encoding="utf-8")
        candidate_path = AUTHORING_DIR / f"{candidate_name}.mdx" if candidate_name else None
        if candidate_path and candidate_path.exists():
            candidate_path.unlink()
        applied.append(
            {
                "normalized_url": normalized_url,
                "skill_name": skill_name,
                "path": str(promoted_path.relative_to(ROOT)),
                "removed_candidate_row": str(candidate_path.relative_to(ROOT)) if candidate_path else "",
            }
        )

    updated_rows: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized_url = str(row.get("normalized_url", ""))
        if normalized_url in overrides_by_url:
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                for override in overrides_by_url[normalized_url]:
                    updated_rows.append(promoted_summary_row(override, row))
        else:
            updated_rows.append(row)
    for normalized_url, url_overrides in overrides_by_url.items():
        if normalized_url in seen_urls:
            continue
        for override in url_overrides:
            updated_rows.append(promoted_summary_row(override, None))
    status_counts = Counter(str(row.get("status", "")) for row in updated_rows)
    sync_kind_counts = Counter(str(row.get("sync_kind", "")) for row in updated_rows)
    summary["rows"] = updated_rows
    summary["generated_at"] = now()
    summary["rows_written"] = len(updated_rows)
    summary["status"] = "mixed" if len(status_counts) > 1 else next(iter(status_counts), "none")
    summary["status_counts"] = dict(sorted(status_counts.items()))
    summary["sync_kind"] = "mixed" if len(sync_kind_counts) > 1 else next(iter(sync_kind_counts), "none")
    summary["sync_kind_counts"] = dict(sorted(sync_kind_counts.items()))
    summary["install_commands_published"] = sum(1 for row in updated_rows if row.get("install_command"))
    summary["live_installs_recorded"] = sum(1 for row in updated_rows if row.get("live_install_executed"))
    write_json(SUMMARY, summary)

    payload = {
        "version": 1,
        "generated_at": now(),
        "applied_count": len(applied),
        "items": applied,
    }
    write_json(REPORT, payload)
    return payload


def validate() -> dict[str, Any]:
    overrides = load_overrides()
    summary = load_json(SUMMARY)
    rows = summary.get("rows", [])
    rows_by_key = {
        (row.get("normalized_url"), row.get("name")): row
        for row in rows
        if isinstance(row, dict) and row.get("normalized_url") and row.get("name")
    }
    errors = []
    for override in overrides:
        normalized_url = override["normalized_url"]
        skill_name = override["skill_name"]
        executed_commands = override.get("executed_commands", [])
        if override.get("live_install_executed") and not any(
            is_live_install_command(command) for command in executed_commands
        ):
            errors.append(f"live install for {normalized_url} lacks non-dry-run install command evidence")
        row = rows_by_key.get((normalized_url, skill_name))
        if not row:
            errors.append(f"missing summary row for {normalized_url} / {skill_name}")
            continue
        if not row.get("install_command"):
            errors.append(f"summary row for {normalized_url} has no install command")
        if not (AUTHORING_DIR / f"{skill_name}.mdx").exists():
            errors.append(f"missing promoted authoring row for {skill_name}")
        candidate_name = override.get("candidate_authoring_name")
        if candidate_name and (AUTHORING_DIR / f"{candidate_name}.mdx").exists():
            errors.append(f"stale candidate authoring row still exists for {candidate_name}")
    if summary.get("rows_written") != len(rows):
        errors.append("summary rows_written does not match row count")
    return {
        "ok": not errors,
        "overrides": len(overrides),
        "summary_rows": len(rows),
        "install_commands_published": summary.get("install_commands_published", 0),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="apply promotion overrides")
    parser.add_argument("--check", action="store_true", help="validate applied promotion overrides")
    args = parser.parse_args()

    if args.apply:
        payload = apply_overrides()
        print(json.dumps(payload, indent=2))
    if args.check:
        result = validate()
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1
    if not args.apply:
        parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
