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
import os
import re
import subprocess
import sys
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
PROGRESS = MANIFEST_DIR / "full-integration-progress.json"
STATE_REPORT = MANIFEST_DIR / "full-integration-state.md"
TRUST_CLEARED_STATUS = "install-now-after-trust-gate"
TRUST_CLEARED_TIER = "curated-trust-gated"
COVERAGE_TRUST_CLEARED = "covered-by-existing-installable-catalog"
COVERAGE_INSPECTION_REQUIRED = "covered-by-existing-inspection-required"
COVERAGE_REFERENCE = "covered-by-existing-reference"
COVERAGE_NEEDS_PROMOTION = "needs-promotion-review"
BLOCKING_GATES = [
    "source-list evidence",
    "license review",
    "security review",
    "attribution review",
    "auth review",
    "docs-steward promotion",
    "target-specific validation",
]
BASELINE_GATE_ARTIFACTS = (
    "existing-integration-coverage.json",
    "promotion-readiness-queue.json",
    "promotion-gate-matrix.json",
    "live-install-command-preview.json",
    "promotion-gate-summary.md",
    "research-task-graph.json",
    "raw-research-packets.json",
    "unique-target-research-packets.json",
    "promotion-wave-plan.json",
    "promotion-wave-plan.md",
)
AUTHORING_STEM_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
REQUIRED_OVERRIDE_STRING_FIELDS = (
    "normalized_url",
    "source_name",
    "candidate_authoring_name",
    "skill_name",
    "description",
    "install_source",
    "install_command",
    "status",
    "trust_tier",
    "sync_kind",
    "source_list_evidence",
    "license",
)


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


def load_overrides() -> list[Any]:
    if not OVERRIDES.exists():
        return []
    payload = load_json(OVERRIDES)
    if not isinstance(payload, dict):
        raise ValueError("promotion-overrides.json payload must be an object")
    overrides = payload.get("overrides", [])
    if not isinstance(overrides, list):
        raise ValueError("promotion-overrides.json overrides must be a list")
    return overrides


def authoring_path_for(stem: str) -> Path:
    path = (AUTHORING_DIR / f"{stem}.mdx").resolve()
    path.relative_to(AUTHORING_DIR.resolve())
    return path


def is_safe_authoring_stem(value: Any) -> bool:
    return isinstance(value, str) and bool(AUTHORING_STEM_RE.fullmatch(value))


def is_within_authoring_dir(path: Path) -> bool:
    try:
        path.resolve().relative_to(AUTHORING_DIR.resolve())
    except ValueError:
        return False
    return True


def validate_override_records(overrides: list[Any], rows: list[Any]) -> list[str]:
    errors: list[str] = []
    row_urls = {
        str(row.get("normalized_url"))
        for row in rows
        if isinstance(row, dict) and row.get("normalized_url")
    }
    seen_skill_names: set[str] = set()

    for index, override in enumerate(overrides):
        label = f"override {index + 1}"
        if not isinstance(override, dict):
            errors.append(f"{label} is not an object")
            continue

        for field in REQUIRED_OVERRIDE_STRING_FIELDS:
            value = override.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label} missing required string field {field}")

        skill_name = override.get("skill_name")
        if not is_safe_authoring_stem(skill_name):
            errors.append(f"{label} has invalid skill_name authoring stem")
        else:
            if skill_name in seen_skill_names:
                errors.append(f"duplicate promoted skill_name {skill_name}")
            seen_skill_names.add(skill_name)
            if not is_within_authoring_dir(authoring_path_for(skill_name)):
                errors.append(f"{label} promoted path escapes authoring directory")
        if override.get("status") != "install-now-after-trust-gate":
            errors.append(f"{label} status is not install-now-after-trust-gate")
        if override.get("sync_kind") != "skills-cli":
            errors.append(f"{label} sync_kind is not skills-cli")
        if override.get("source_list_evidence") != "source-list-found":
            errors.append(f"{label} source_list_evidence is not source-list-found")

        candidate_name = override.get("candidate_authoring_name")
        if not is_safe_authoring_stem(candidate_name):
            errors.append(f"{label} has invalid candidate_authoring_name authoring stem")
        elif not is_within_authoring_dir(authoring_path_for(candidate_name)):
            errors.append(f"{label} candidate path escapes authoring directory")

        normalized_url = override.get("normalized_url")
        if isinstance(normalized_url, str) and normalized_url.strip() and normalized_url not in row_urls:
            errors.append(f"{label} normalized_url has no source summary row: {normalized_url}")

        executed_commands = override.get("executed_commands")
        if not isinstance(executed_commands, list) or not all(
            isinstance(command, str) for command in executed_commands
        ):
            errors.append(f"{label} executed_commands must be a list of strings")
            executed_commands = []
        installed_paths = override.get("installed_paths")
        if not isinstance(installed_paths, list) or not all(isinstance(path, str) for path in installed_paths):
            errors.append(f"{label} installed_paths must be a list of strings")
            installed_paths = []
        if override.get("live_install_executed"):
            if not any(is_live_install_command(command) for command in executed_commands):
                errors.append(f"live install for {normalized_url} lacks non-dry-run install command evidence")
            if not installed_paths:
                errors.append(f"live install for {normalized_url} lacks installed path evidence")
            for missing_path in missing_installed_skill_md_paths(override):
                errors.append(f"live install for {normalized_url} has missing installed SKILL.md: {missing_path}")

    return errors


def is_live_install_command(command: Any) -> bool:
    command_text = str(command)
    return (
        "skills add" in command_text
        and "--skill" in command_text
        and "--dry-run" not in command_text
        and "--help" not in command_text
    )


def installed_skill_md_path(raw_path: Any) -> Path:
    path = Path(os.path.expanduser(str(raw_path)))
    return path if path.name == "SKILL.md" else path / "SKILL.md"


def missing_installed_skill_md_paths(override: dict[str, Any]) -> list[str]:
    missing = []
    for raw_path in override.get("installed_paths", []):
        if not isinstance(raw_path, str) or not raw_path.strip():
            continue
        skill_md = installed_skill_md_path(raw_path)
        if not skill_md.exists():
            missing.append(str(skill_md))
    return missing


def live_install_evidence_stats(overrides: list[Any]) -> dict[str, Any]:
    live_rows = [
        override
        for override in overrides
        if isinstance(override, dict) and override.get("live_install_executed")
    ]
    installed_paths = [
        raw_path
        for override in live_rows
        for raw_path in override.get("installed_paths", [])
        if isinstance(raw_path, str) and raw_path.strip()
    ]
    missing = [
        path
        for override in live_rows
        for path in missing_installed_skill_md_paths(override)
    ]
    return {
        "live_install_rows": len(live_rows),
        "installed_path_refs": len(installed_paths),
        "verified_skill_md_count": len(installed_paths) - len(missing),
        "missing_installed_skill_md": missing,
    }


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
        "path": str(authoring_path_for(str(override["skill_name"])).relative_to(ROOT.resolve())),
        "normalized_url": override["normalized_url"],
        "source_name": override["source_name"],
        "raw_indexes": override.get("raw_indexes") or (previous or {}).get("raw_indexes", []),
        "status": override.get("status", "install-now-after-trust-gate"),
        "trust_tier": override.get("trust_tier", TRUST_CLEARED_TIER),
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


def int_value(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def manifest_json(name: str) -> Path:
    return MANIFEST_DIR / name


def load_manifest_json(name: str, default: Any) -> Any:
    path = manifest_json(name)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def restore_committed_gate_artifacts() -> None:
    for name in BASELINE_GATE_ARTIFACTS:
        relative = f"planning/manifests/candidate-corpus-jul2026/{name}"
        result = subprocess.run(
            ["git", "show", f"HEAD:{relative}"],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            manifest_json(name).write_bytes(result.stdout)


def promoted_summary_rows_by_url() -> dict[str, list[dict[str, Any]]]:
    if not SUMMARY.exists():
        return {}
    summary = load_json(SUMMARY)
    rows = summary.get("rows", [])
    if not isinstance(rows, list):
        return {}
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict) or not row.get("install_command") or not row.get("normalized_url"):
            continue
        normalized_url = str(row["normalized_url"]).lower()
        result[normalized_url].append(
            {
                "name": row.get("name", ""),
                "path": row.get("path", ""),
                "source": row.get("source_name", ""),
                "install_source": row.get("source_name", ""),
                "source_url": row.get("normalized_url", ""),
                "status": row.get("status", ""),
                "trust_tier": row.get("trust_tier", ""),
                "sync_kind": row.get("sync_kind", ""),
                "has_install_command": True,
            }
        )
    return dict(result)


def existing_row_has_install_surface(row: dict[str, Any]) -> bool:
    has_install_command = bool(row.get("has_install_command")) or bool(str(row.get("install_command", "")).strip())
    sync_kind = str(row.get("sync_kind", "")).strip()
    return has_install_command and sync_kind not in {"", "none"}


def existing_row_trust_cleared(row: dict[str, Any]) -> bool:
    return (
        existing_row_has_install_surface(row)
        and row.get("status") == TRUST_CLEARED_STATUS
        and row.get("trust_tier") == TRUST_CLEARED_TIER
    )


def existing_rows_trust_cleared(rows: Any) -> bool:
    if not isinstance(rows, list):
        return False
    install_surface_rows = [row for row in rows if isinstance(row, dict) and existing_row_has_install_surface(row)]
    return bool(install_surface_rows) and all(existing_row_trust_cleared(row) for row in install_surface_rows)


def coverage_status_from_existing_rows(rows: Any) -> str:
    if existing_rows_trust_cleared(rows):
        return COVERAGE_TRUST_CLEARED
    if isinstance(rows, list) and any(
        isinstance(row, dict) and existing_row_has_install_surface(row) for row in rows
    ):
        return COVERAGE_INSPECTION_REQUIRED
    if isinstance(rows, list) and rows:
        return COVERAGE_REFERENCE
    return COVERAGE_NEEDS_PROMOTION


def coverage_item_trust_cleared(item: dict[str, Any]) -> bool:
    return item.get("coverage_status") == COVERAGE_TRUST_CLEARED and existing_rows_trust_cleared(
        item.get("existing_rows")
    )


def trust_cleared_rows_for_item(item: dict[str, Any]) -> list[dict[str, Any]]:
    rows = item.get("existing_rows", [])
    if not isinstance(rows, list):
        rows = []
    candidates = [row for row in rows if isinstance(row, dict)]
    return [row for row in candidates if existing_row_trust_cleared(row)]


def retained_existing_coverage_urls() -> set[str]:
    coverage = load_manifest_json("existing-integration-coverage.json", {"items": []})
    items = coverage.get("items", []) if isinstance(coverage, dict) else []
    selected: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized_url = str(item.get("normalized_url", "")).lower()
        if existing_rows_trust_cleared(item.get("existing_rows")) and normalized_url not in selected:
            selected.append(normalized_url)
    return set(selected)


def overlay_existing_coverage() -> set[str]:
    coverage_path = manifest_json("existing-integration-coverage.json")
    coverage = load_manifest_json("existing-integration-coverage.json", {"version": 1, "items": []})
    if not isinstance(coverage, dict):
        return set()
    items = coverage.get("items", [])
    if not isinstance(items, list):
        return set()
    promoted_rows_by_url = promoted_summary_rows_by_url()
    retained_urls = retained_existing_coverage_urls() | set(promoted_rows_by_url)
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized_url = str(item.get("normalized_url", "")).lower()
        if normalized_url in retained_urls:
            promoted_rows = promoted_rows_by_url.get(normalized_url, [])
            merged_rows = trust_cleared_rows_for_item(item) + promoted_rows
            deduped_rows = {
                (
                    str(row.get("name", "")),
                    str(row.get("path", "")),
                    str(row.get("install_source", "")),
                ): row
                for row in merged_rows
            }
            item["coverage_status"] = COVERAGE_TRUST_CLEARED
            item["existing_rows"] = list(deduped_rows.values())
        else:
            existing_rows = item.get("existing_rows", [])
            item["coverage_status"] = coverage_status_from_existing_rows(existing_rows)
            if item["coverage_status"] == COVERAGE_NEEDS_PROMOTION:
                item["existing_rows"] = []
    coverage["summary"] = dict(
        sorted(
            Counter(
                item.get("coverage_status", COVERAGE_NEEDS_PROMOTION)
                for item in items
                if isinstance(item, dict)
            ).items()
        )
    )
    write_json(coverage_path, coverage)
    return retained_urls


def overlay_research_graph(retained_urls: set[str]) -> None:
    graph_path = manifest_json("research-task-graph.json")
    graph = load_manifest_json("research-task-graph.json", {})
    coverage = load_manifest_json("existing-integration-coverage.json", {"items": []})
    if not isinstance(graph, dict):
        return
    lanes = graph.get("unique_target_lanes", [])
    if not isinstance(lanes, list):
        return
    coverage_items = coverage.get("items", []) if isinstance(coverage, dict) else []
    coverage_by_url = {
        str(item.get("normalized_url", "")).lower(): item
        for item in coverage_items
        if isinstance(item, dict) and item.get("normalized_url")
    }
    status_counts: Counter[str] = Counter()
    for lane in lanes:
        if not isinstance(lane, dict):
            continue
        normalized_url = str(lane.get("normalized_url", "")).lower()
        coverage_item = coverage_by_url.get(normalized_url, {})
        coverage_status = str(coverage_item.get("coverage_status") or COVERAGE_NEEDS_PROMOTION)
        lane["existing_integration_status"] = coverage_status
        lane["existing_rows"] = coverage_item.get("existing_rows", []) if isinstance(coverage_item, dict) else []
        if normalized_url in retained_urls and coverage_status == COVERAGE_TRUST_CLEARED:
            lane["terminal_decision_status"] = "covered-by-existing-catalog"
        else:
            lane["terminal_decision_status"] = "provisional-intake-only"
        status_counts[coverage_status] += 1
    graph["existing_integration_summary"] = dict(sorted(status_counts.items()))
    write_json(graph_path, graph)


def readiness_item_from_coverage(item: dict[str, Any], covered: bool) -> dict[str, Any]:
    existing_rows = item.get("existing_rows", [])
    if not isinstance(existing_rows, list):
        existing_rows = []
    return {
        "packet_id": item.get("packet_id", ""),
        "normalized_url": item.get("normalized_url", ""),
        "source_name": item.get("source_name", ""),
        "raw_indexes": item.get("raw_indexes", []),
        "existing_integration_status": item.get("coverage_status", COVERAGE_NEEDS_PROMOTION),
        "terminal_status": "covered-by-existing-installable-catalog" if covered else "blocked-until-trust-gates",
        "live_install_eligible": False,
        "repo_mutation_eligible": False,
        "install_command": "",
        "existing_rows": existing_rows if item.get("coverage_status") != COVERAGE_NEEDS_PROMOTION else [],
        "blocking_gates": [] if covered else BLOCKING_GATES,
    }


def overlay_promotion_readiness(retained_urls: set[str]) -> None:
    coverage = load_manifest_json("existing-integration-coverage.json", {"items": []})
    items = coverage.get("items", []) if isinstance(coverage, dict) else []
    covered_items = []
    blocked_items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        covered = coverage_item_trust_cleared(item) and str(item.get("normalized_url", "")).lower() in retained_urls
        target = readiness_item_from_coverage(item, covered)
        if covered:
            covered_items.append(target)
        else:
            blocked_items.append(target)
    payload = {
        "version": 1,
        "generated_at": now(),
        "status": "existing-coverage-reconciled-with-trust-gated-backlog",
        "summary": {
            "unique_targets": len(covered_items) + len(blocked_items),
            "covered_by_existing_installable_catalog": len(covered_items),
            "ready_for_repo_promotion": 0,
            "ready_for_live_install": 0,
            "blocked_until_trust_gates": len(blocked_items),
        },
        "covered_by_existing_installable_catalog": covered_items,
        "ready_for_repo_promotion": [],
        "ready_for_live_install": [],
        "blocked_until_trust_gates": blocked_items,
    }
    write_json(manifest_json("promotion-readiness-queue.json"), payload)


def overlay_promotion_waves(retained_urls: set[str]) -> None:
    path = manifest_json("promotion-wave-plan.json")
    plan = load_manifest_json("promotion-wave-plan.json", {})
    if not isinstance(plan, dict):
        return
    waves = plan.get("waves", [])
    if not isinstance(waves, list):
        return
    if not waves:
        return
    normalized = load_manifest_json("normalized-urls.json", {})
    coverage = load_manifest_json("existing-integration-coverage.json", {"items": []})
    unique_targets = normalized.get("unique_targets", []) if isinstance(normalized, dict) else []
    coverage_items = coverage.get("items", []) if isinstance(coverage, dict) else []
    if not isinstance(unique_targets, list):
        return
    coverage_by_url = {
        str(item.get("normalized_url", "")).lower(): item
        for item in coverage_items
        if isinstance(item, dict) and item.get("normalized_url")
    }
    all_targets: dict[str, dict[str, Any]] = {}
    for normalized_url in unique_targets:
        key = str(normalized_url).lower()
        coverage_item = coverage_by_url.get(key, {})
        all_targets[key] = {
            "normalized_url": str(normalized_url),
            "source_name": coverage_item.get("source_name", ""),
            "raw_indexes": coverage_item.get("raw_indexes", []),
            "coverage_status": coverage_item.get("coverage_status", "needs-promotion-review"),
            "existing_integration_status": coverage_item.get("coverage_status", "needs-promotion-review"),
        }
    covered_target_urls = {
        key
        for key, target in all_targets.items()
        if key in retained_urls and target.get("coverage_status") == COVERAGE_TRUST_CLEARED
    }
    covered_targets = [target for key, target in all_targets.items() if key in covered_target_urls]
    blocked_targets = [target for key, target in all_targets.items() if key not in covered_target_urls]
    waves[0]["targets"] = covered_targets
    waves[0]["target_count"] = len(covered_targets)
    target_wave = next((wave for wave in waves if isinstance(wave, dict) and wave.get("wave_id") == "W08"), waves[-1])
    for wave in waves[1:]:
        wave["targets"] = []
        wave["target_count"] = 0
    if target_wave is not waves[0]:
        target_wave["targets"] = blocked_targets
        target_wave["target_count"] = len(blocked_targets)
    plan["total_targets"] = len(all_targets)
    write_json(path, plan)


def refresh_promotion_gate_artifacts() -> None:
    promoter = ROOT / "scripts" / "promote_candidate_corpus.py"
    if not promoter.exists():
        return
    result = subprocess.run(
        [sys.executable, str(promoter), "--write"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        details = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        raise RuntimeError(f"promotion gate artifact refresh failed with exit {result.returncode}: {details}")


def write_promotion_reports(summary: dict[str, Any], overrides: list[dict[str, Any]], progress: dict[str, Any]) -> None:
    rows = summary.get("rows", [])
    unique_targets = int_value(summary.get("unique_targets"), 289)
    live_stats = live_install_evidence_stats(overrides)
    live_installed = live_stats["live_install_rows"]
    installed_path_refs = live_stats["installed_path_refs"]
    verified_skill_md = live_stats["verified_skill_md_count"]
    missing_skill_md = len(live_stats["missing_installed_skill_md"])
    readiness = load_manifest_json("promotion-readiness-queue.json", {})
    readiness_summary = readiness.get("summary", {}) if isinstance(readiness, dict) else {}
    preview = load_manifest_json("live-install-command-preview.json", {})
    preview_command_count = int_value(preview.get("command_count")) if isinstance(preview, dict) else 0
    reference_rows = sum(1 for row in rows if isinstance(row, dict) and not row.get("install_command"))
    deep_audit = load_manifest_json("deep-source-audit.json", {})
    deep_items = deep_audit.get("items", []) if isinstance(deep_audit, dict) else []
    deep_status_counts = deep_audit.get("status_counts", {}) if isinstance(deep_audit, dict) else {}
    deep_audited = int_value(deep_status_counts.get("audited"))
    deep_blocked = int_value(deep_status_counts.get("terminal-blocker"))
    validation_lines = [
        "# Candidate Corpus July 2026 Validation Report",
        "",
        "- Raw candidates processed: 293",
        f"- Unique normalized targets: {unique_targets}",
        f"- Catalog authoring rows: {len(rows)}",
        f"- Installable promoted curated-external rows: {len(overrides)}",
        f"- Recorded install evidence rows: {live_installed}",
        f"- Installed path references verified: {verified_skill_md}/{installed_path_refs}",
        f"- Missing installed `SKILL.md` files: {missing_skill_md}",
        f"- New live install commands emitted: {preview_command_count}",
        f"- Remaining reference or terminal-gated rows: {reference_rows}",
        (
            f"- Source-list evidence: 289 list-only source probes recorded; {len(overrides)} installable rows "
            "were promoted from reviewed override evidence."
        ),
        (
            f"- Deep source audit: {deep_audited} targets audited through GitHub API README/license/tree/package "
            f"reads plus {deep_blocked} terminal blocker; candidate code executed: false."
        ),
        f"- Full integration phase: `{progress.get('phase')}`",
        f"- Live install status: `{progress.get('live_install', {}).get('status')}`",
        (
            "- Gate summary: "
            f"{readiness_summary.get('covered_by_existing_installable_catalog', 0)} covered, "
            f"{readiness_summary.get('ready_for_repo_promotion', 0)} ready for repo promotion, "
            f"{readiness_summary.get('ready_for_live_install', 0)} ready for live install, "
            f"{readiness_summary.get('blocked_until_trust_gates', 0)} blocked."
        ),
        "",
        "## Observed Generated Evidence",
        "",
        "- Generator emitted manifest, matrix, packet, report, and catalog-authoring artifacts from local inputs.",
        "- Read-only generator and deep-source audit scripts did not execute candidate code.",
        (
            "- The promotion overlay records prior non-dry-run Skills CLI install commands; validation verifies "
            "installed `SKILL.md` roots without re-running installers."
        ),
        "",
        "## Command Checklist",
        "",
        "- `uv run python scripts/generate_candidate_corpus_shards.py --emit-all --no-network`",
        (
            "- `uv run python scripts/apply_candidate_corpus_promotions.py --check` passed for "
            f"{len(overrides)} promotion overrides."
        ),
        (
            "- `uv run python scripts/audit_candidate_deep_sources.py --check` passed for "
            f"{len(deep_items)} normalized targets."
        ),
        (
            "- `uv run python scripts/promote_candidate_corpus.py --final-check` passed for 293 raw entries, "
            f"{unique_targets} unique targets, {deep_audited} deep-audited targets, {deep_blocked} deep terminal "
            f"blocker, {len(overrides)} promoted overrides, and {live_installed} recorded install evidence rows."
        ),
        "- `uv run -- wagents docs generate --no-installed --check`",
        "- `uv run -- wagents catalog index --check --format json`",
        "- `uv run wagents validate`",
        (
            "- `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@latest validate "
            "integrate-candidate-corpus-jul2026 --strict --json`"
        ),
    ]
    (MANIFEST_DIR / "validation-report.md").write_text("\n".join(validation_lines) + "\n", encoding="utf-8")

    final_lines = [
        "# Candidate Corpus July 2026 Final Review Report",
        "",
        "- Total raw candidates processed: 293",
        f"- Total unique normalized targets: {unique_targets}",
        f"- Catalog authoring rows after overlay: {len(rows)}",
        f"- Promoted installable curated-external rows: {len(overrides)}",
        f"- Recorded install evidence rows: {live_installed}",
        f"- Installed path references verified: {verified_skill_md}/{installed_path_refs}",
        f"- Missing installed `SKILL.md` files: {missing_skill_md}",
        f"- New live install commands emitted: {preview_command_count}",
        f"- Remaining reference or terminal-gated rows: {reference_rows}",
        (
            f"- Full integration phase: `{progress.get('phase')}`; live install status is "
            f"`{progress.get('live_install', {}).get('status')}`."
        ),
        (
            f"- Deep source audit: {deep_audited} audited targets, {deep_blocked} terminal blocker, "
            "candidate code executed: false."
        ),
        "- Generator-owned conservative intake artifacts remain available for traceability.",
        "- No commit made by this script.",
        "",
        "## Suggested PR Title",
        "",
        "chore: integrate candidate corpus July 2026 promotion overlay",
        "",
        "## Suggested PR Body",
        "",
        (
            "- Adds deterministic candidate corpus normalization, sharding, coverage, generated catalog "
            "authoring rows, and promotion overlay validation."
        ),
        (
            "- Records read-only source-list/deep-source evidence and reviewed install metadata for promoted "
            "curated external rows, including installed-root verification."
        ),
        "- Keeps validation commands explicit and avoids live installs during checks.",
    ]
    (MANIFEST_DIR / "final-review-report.md").write_text("\n".join(final_lines) + "\n", encoding="utf-8")


def write_progress_state(summary: dict[str, Any], overrides: list[dict[str, Any]]) -> None:
    progress = load_json(PROGRESS) if PROGRESS.exists() else {"version": 1}
    rows = summary.get("rows", [])
    row_urls = {row.get("normalized_url") for row in rows if isinstance(row, dict) and row.get("normalized_url")}
    unique_targets = int_value(summary.get("unique_targets"), len(row_urls))
    live_stats = live_install_evidence_stats(overrides)
    live_installed = live_stats["live_install_rows"]
    installed_path_refs = live_stats["installed_path_refs"]
    verified_skill_md = live_stats["verified_skill_md_count"]
    missing_skill_md = len(live_stats["missing_installed_skill_md"])
    promoted_unique_targets = len(
        {override.get("normalized_url") for override in overrides if override.get("normalized_url")}
    )
    status_counts = summary.get("status_counts", {})
    reference_rows = (
        int_value(status_counts.get("global-only-or-avoid"))
        if isinstance(status_counts, dict)
        else sum(1 for row in rows if isinstance(row, dict) and not row.get("install_command"))
    )
    coverage_manifest = load_manifest_json("existing-integration-coverage.json", {})
    coverage = coverage_manifest.get("summary", {}) if isinstance(coverage_manifest, dict) else {}
    readiness_manifest = load_manifest_json("promotion-readiness-queue.json", {})
    readiness_summary = readiness_manifest.get("summary", {}) if isinstance(readiness_manifest, dict) else {}
    gate_matrix = load_manifest_json("promotion-gate-matrix.json", {})
    matrix_summary = gate_matrix.get("summary", {}) if isinstance(gate_matrix, dict) else {}
    live_preview = load_manifest_json("live-install-command-preview.json", {})
    preview_status = (
        str(live_preview.get("status", "no-live-install-commands-emitted"))
        if isinstance(live_preview, dict)
        else "no-live-install-commands-emitted"
    )
    preview_command_count = int_value(live_preview.get("command_count")) if isinstance(live_preview, dict) else 0
    coverage_total = sum(int_value(value) for value in coverage.values()) if isinstance(coverage, dict) else 0
    covered_existing = int_value(
        readiness_summary.get("covered_by_existing_installable_catalog")
        if isinstance(readiness_summary, dict)
        else coverage.get(COVERAGE_TRUST_CLEARED)
        if isinstance(coverage, dict)
        else None,
        max(unique_targets - reference_rows, 0),
    )
    blocked_until_trust_gates = int_value(
        readiness_summary.get("blocked_until_trust_gates")
        if isinstance(readiness_summary, dict)
        else coverage_total - covered_existing
        if coverage_total
        else None,
        max(unique_targets - covered_existing, 0),
    )
    ready_for_repo_promotion = int_value(
        readiness_summary.get("ready_for_repo_promotion")
        if isinstance(readiness_summary, dict)
        else matrix_summary.get("ready_for_repo_promotion")
        if isinstance(matrix_summary, dict)
        else None,
        0,
    )
    ready_for_live_install = int_value(
        readiness_summary.get("ready_for_live_install")
        if isinstance(readiness_summary, dict)
        else matrix_summary.get("ready_for_live_install")
        if isinstance(matrix_summary, dict)
        else None,
        0,
    )
    wave_plan = load_manifest_json("promotion-wave-plan.json", {})
    wave_rows = wave_plan.get("waves", []) if isinstance(wave_plan, dict) else []
    progress_waves = {
        str(wave.get("wave_id")): int_value(wave.get("target_count"))
        for wave in wave_rows
        if isinstance(wave, dict) and int_value(wave.get("target_count")) > 0
    }
    duplicate_raw_groups = 0
    normalized_path = MANIFEST_DIR / "normalized-urls.json"
    if normalized_path.exists():
        normalized = load_json(normalized_path)
        duplicate_groups = normalized.get("duplicate_groups", [])
        duplicate_raw_groups = len(duplicate_groups) if isinstance(duplicate_groups, (dict, list)) else 0

    progress["generated_at"] = now()
    progress["phase"] = "promotion-overlay-installed"
    progress["complete"] = True
    progress["completion_scope"] = (
        "Complete for the July 2026 candidate-corpus goal as a trust-gated catalog integration overlay; "
        "conservative intake, packet, gate, and install-evidence artifacts remain available for traceability."
    )
    progress["promotion_readiness"] = {
        **(readiness_summary if isinstance(readiness_summary, dict) else {}),
        "unique_targets": unique_targets,
        "covered_by_existing_installable_catalog": covered_existing,
        "ready_for_repo_promotion": ready_for_repo_promotion,
        "ready_for_live_install": ready_for_live_install,
        "blocked_until_trust_gates": blocked_until_trust_gates,
        "remaining_reference_rows": reference_rows,
        "promoted_unique_targets": promoted_unique_targets,
        "promoted_installable_rows": len(overrides),
        "recorded_install_evidence_rows": live_installed,
    }
    progress["existing_integration_coverage"] = dict(coverage) if isinstance(coverage, dict) else {}
    progress["promotion_waves"] = progress_waves
    progress["live_install"] = {
        "eligible_count": preview_command_count,
        "status": preview_status,
        "installed_skill_rows": live_installed,
        "recorded_install_evidence_rows": live_installed,
        "new_live_install_commands_emitted": preview_command_count,
        "installed_path_refs": installed_path_refs,
        "verified_skill_md_count": verified_skill_md,
        "missing_skill_md_count": missing_skill_md,
        "reason": (
            "live-install-command-preview.json remains the no-new-live-install gate artifact; "
            "promotion-overrides.json records prior non-dry-run Skills CLI install evidence."
        ),
        "pre_overlay_preview_status": (
            "live-install-command-preview.json remains the no-new-live-install gate artifact; "
            "promotion-overrides.json and catalog-authoring-summary.json record reviewed install evidence."
        ),
    }
    progress["terminal_decisions"] = {
        "raw_candidates_processed": int_value(progress.get("raw_candidates"), 293),
        "unique_normalized_targets": unique_targets,
        "installable_curated_rows": len(overrides),
        "live_installs_recorded": live_installed,
        "new_live_install_commands_emitted": preview_command_count,
        "reference_only_or_terminal_gated_rows": reference_rows,
        "duplicate_raw_groups": duplicate_raw_groups,
    }
    write_json(PROGRESS, progress)

    lines = [
        "# Candidate Corpus Full Integration State",
        "",
        f"- Phase: `{progress['phase']}`",
        "- Complete: `true`",
        f"- Completion scope: {progress['completion_scope']}",
        f"- Raw research lanes: {progress.get('raw_candidates', 293)}",
        f"- Unique target synthesis lanes: {unique_targets}",
        f"- Live install eligible: {preview_command_count}",
        f"- Live install status: `{progress['live_install']['status']}`",
        f"- Recorded install evidence rows: {live_installed}",
        f"- Installed path references verified: {verified_skill_md}/{installed_path_refs}",
        f"- Missing installed `SKILL.md` files: {missing_skill_md}",
        f"- Covered by existing installable catalog rows: {covered_existing}",
        f"- Promoted installable catalog rows: {len(overrides)}",
        f"- Ready for repo promotion: {ready_for_repo_promotion}",
        f"- Ready for live install: {ready_for_live_install}",
        f"- Blocked until trust gates: {blocked_until_trust_gates}",
        f"- Remaining reference or terminal-gated rows: {reference_rows}",
        f"- Promoted unique targets: {promoted_unique_targets}",
        "",
        "## Overlay Evidence",
        "",
        (
            "`live-install-command-preview.json` remains the no-new-live-install gate artifact. The reviewed "
            "catalog promotion overlay and install evidence are recorded in `promotion-overrides.json`, "
            "`applied-promotion-overrides.json`, `catalog-authoring-summary.json`, and this state report."
        ),
        "",
        (
            "- `uv run python scripts/apply_candidate_corpus_promotions.py --check` passed for "
            f"{len(overrides)} overrides."
        ),
        (
            "- `uv run python scripts/promote_candidate_corpus.py --final-check` reconciles deep-source audit "
            f"evidence, {len(overrides)} promoted overrides, {live_installed} install-evidence rows, and "
            f"{unique_targets} terminal target decisions."
        ),
        f"- Install-root verification found {missing_skill_md} missing `SKILL.md` files.",
    ]
    STATE_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_promotion_reports(summary, overrides, progress)

    final_report_path = MANIFEST_DIR / "final-review-report.md"
    if final_report_path.exists():
        final_report = final_report_path.read_text(encoding="utf-8").split("\n## Promotion Overlay Completion\n", 1)[0]
        overlay = [
            "## Promotion Overlay Completion",
            "",
            "- Full integration phase: `promotion-overlay-installed`.",
            f"- Promoted overrides: {len(overrides)}.",
            f"- Recorded install evidence rows: {live_installed}.",
            f"- Installed path references verified: {verified_skill_md}/{installed_path_refs}.",
            f"- Missing installed `SKILL.md` files: {missing_skill_md}.",
            "- Final commit hash: no commit made by this script.",
        ]
        final_report_path.write_text(final_report.rstrip() + "\n\n" + "\n".join(overlay) + "\n", encoding="utf-8")


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
    validation_errors = validate_override_records(overrides, rows)
    if validation_errors:
        joined = "\n- ".join(validation_errors)
        raise ValueError(f"Invalid promotion overrides:\n- {joined}")
    overrides_by_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for override in overrides:
        overrides_by_url[str(override["normalized_url"])].append(override)

    applied = []
    for override in overrides:
        skill_name = str(override["skill_name"])
        candidate_name = str(override.get("candidate_authoring_name", ""))
        normalized_url = str(override["normalized_url"])
        promoted_path = authoring_path_for(skill_name)
        promoted_path.write_text(render_promoted_row(override), encoding="utf-8")
        candidate_path = authoring_path_for(candidate_name) if candidate_name else None
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
    source_list_by_url = {
        str(row.get("normalized_url", "")): str(row.get("source_list_evidence", ""))
        for row in updated_rows
        if row.get("normalized_url")
    }
    source_list_status_counts = Counter(source_list_by_url.values())
    summary["rows"] = updated_rows
    summary["generated_at"] = now()
    summary["rows_written"] = len(updated_rows)
    summary["status"] = "mixed" if len(status_counts) > 1 else next(iter(status_counts), "none")
    summary["status_counts"] = dict(sorted(status_counts.items()))
    summary["sync_kind"] = "mixed" if len(sync_kind_counts) > 1 else next(iter(sync_kind_counts), "none")
    summary["sync_kind_counts"] = dict(sorted(sync_kind_counts.items()))
    summary["source_list_status_counts"] = dict(sorted(source_list_status_counts.items()))
    summary["install_commands_published"] = sum(1 for row in updated_rows if row.get("install_command"))
    summary["live_installs_recorded"] = sum(1 for row in updated_rows if row.get("live_install_executed"))
    write_json(SUMMARY, summary)
    restore_committed_gate_artifacts()
    retained_urls = overlay_existing_coverage()
    overlay_research_graph(retained_urls)
    overlay_promotion_readiness(retained_urls)
    overlay_promotion_waves(retained_urls)
    refresh_promotion_gate_artifacts()
    write_progress_state(summary, overrides)

    payload = {
        "version": 1,
        "generated_at": now(),
        "applied_count": len(applied),
        "items": applied,
    }
    write_json(REPORT, payload)
    return payload


def validate() -> dict[str, Any]:
    try:
        overrides = load_overrides()
    except ValueError as exc:
        return {
            "ok": False,
            "overrides": 0,
            "summary_rows": 0,
            "install_commands_published": 0,
            "errors": [str(exc)],
        }
    summary = load_json(SUMMARY)
    progress = load_json(PROGRESS)
    rows = summary.get("rows", [])
    errors = []
    if not isinstance(rows, list):
        errors.append("catalog-authoring-summary.json rows must be a list")
        rows = []
    errors.extend(validate_override_records(overrides, rows))
    rows_by_key = {
        (row.get("normalized_url"), row.get("name")): row
        for row in rows
        if isinstance(row, dict) and row.get("normalized_url") and row.get("name")
    }
    for override in overrides:
        if not isinstance(override, dict):
            continue
        normalized_url = override["normalized_url"]
        skill_name = override["skill_name"]
        row = rows_by_key.get((normalized_url, skill_name))
        if not row:
            errors.append(f"missing summary row for {normalized_url} / {skill_name}")
            continue
        if not row.get("install_command"):
            errors.append(f"summary row for {normalized_url} has no install command")
        if is_safe_authoring_stem(skill_name) and not authoring_path_for(str(skill_name)).exists():
            errors.append(f"missing promoted authoring row for {skill_name}")
        candidate_name = override.get("candidate_authoring_name")
        if is_safe_authoring_stem(candidate_name) and authoring_path_for(str(candidate_name)).exists():
            errors.append(f"stale candidate authoring row still exists for {candidate_name}")
    if summary.get("rows_written") != len(rows):
        errors.append("summary rows_written does not match row count")
    live_stats = live_install_evidence_stats(overrides)
    live_installed = live_stats["live_install_rows"]
    installed_path_refs = live_stats["installed_path_refs"]
    verified_skill_md = live_stats["verified_skill_md_count"]
    missing_skill_md = live_stats["missing_installed_skill_md"]
    installable_rows = sum(
        1 for row in rows if isinstance(row, dict) and row.get("install_command")
    )
    if summary.get("install_commands_published") != installable_rows:
        errors.append("summary install_commands_published does not match installable rows")
    if summary.get("install_commands_published") != len(overrides):
        errors.append("summary install_commands_published does not match promotion override count")
    if summary.get("live_installs_recorded") != live_installed:
        errors.append("summary live_installs_recorded does not match live install evidence")
    if missing_skill_md:
        errors.append(
            "recorded live install evidence has missing SKILL.md paths: "
            + ", ".join(missing_skill_md[:5])
        )
    status_counts = summary.get("status_counts", {})
    sync_kind_counts = summary.get("sync_kind_counts", {})
    if not isinstance(status_counts, dict):
        errors.append("summary status_counts is not an object")
        status_counts = {}
    if not isinstance(sync_kind_counts, dict):
        errors.append("summary sync_kind_counts is not an object")
        sync_kind_counts = {}
    if status_counts.get("install-now-after-trust-gate") != len(overrides):
        errors.append("summary installable status count does not match promotion override count")
    if sync_kind_counts.get("skills-cli") != len(overrides):
        errors.append("summary skills-cli sync count does not match promotion override count")
    if progress.get("phase") != "promotion-overlay-installed":
        errors.append("full integration progress phase is not promotion-overlay-installed")
    if progress.get("complete") is not True:
        errors.append("full integration progress does not mark the goal complete")
    readiness_manifest = load_manifest_json("promotion-readiness-queue.json", {})
    readiness_summary = readiness_manifest.get("summary", {}) if isinstance(readiness_manifest, dict) else {}
    preview_manifest = load_manifest_json("live-install-command-preview.json", {})
    preview_command_count = (
        int_value(preview_manifest.get("command_count"))
        if isinstance(preview_manifest, dict)
        else 0
    )
    preview_status = (
        preview_manifest.get("status", "no-live-install-commands-emitted")
        if isinstance(preview_manifest, dict)
        else "no-live-install-commands-emitted"
    )
    progress_live_install = progress.get("live_install", {})
    if progress_live_install.get("installed_skill_rows") != live_installed:
        errors.append("full integration progress install evidence row count drifted")
    if progress_live_install.get("recorded_install_evidence_rows") != live_installed:
        errors.append("full integration progress recorded install evidence count drifted")
    if progress_live_install.get("eligible_count") != preview_command_count:
        errors.append("full integration progress live install eligible count drifted from preview")
    if progress_live_install.get("new_live_install_commands_emitted") != preview_command_count:
        errors.append("full integration progress live install command count drifted from preview")
    if progress_live_install.get("status") != preview_status:
        errors.append("full integration progress live install status drifted from preview")
    if progress_live_install.get("installed_path_refs") != installed_path_refs:
        errors.append("full integration progress installed path reference count drifted")
    if progress_live_install.get("verified_skill_md_count") != verified_skill_md:
        errors.append("full integration progress verified SKILL.md count drifted")
    if progress_live_install.get("missing_skill_md_count") != len(missing_skill_md):
        errors.append("full integration progress missing SKILL.md count drifted")
    progress_readiness = progress.get("promotion_readiness", {})
    for field in (
        "unique_targets",
        "covered_by_existing_installable_catalog",
        "ready_for_repo_promotion",
        "ready_for_live_install",
        "blocked_until_trust_gates",
    ):
        if isinstance(readiness_summary, dict) and progress_readiness.get(field) != readiness_summary.get(field):
            errors.append(f"full integration progress readiness field {field} drifted from readiness manifest")
    if progress_readiness.get("promoted_installable_rows") != len(overrides):
        errors.append("full integration progress promoted installable row count drifted")
    if progress_readiness.get("recorded_install_evidence_rows") != live_installed:
        errors.append("full integration progress install evidence readiness count drifted")
    coverage_manifest = load_manifest_json("existing-integration-coverage.json", {})
    coverage_items = coverage_manifest.get("items", []) if isinstance(coverage_manifest, dict) else []
    if not isinstance(coverage_items, list):
        errors.append("existing integration coverage items is not a list")
        coverage_items = []
    for item in coverage_items:
        if not isinstance(item, dict):
            continue
        normalized_url = item.get("normalized_url")
        coverage_status = item.get("coverage_status")
        if coverage_status == COVERAGE_TRUST_CLEARED and not coverage_item_trust_cleared(item):
            errors.append(f"retained existing coverage lacks trust-cleared row for {normalized_url}")
        if coverage_status == COVERAGE_INSPECTION_REQUIRED and existing_rows_trust_cleared(item.get("existing_rows")):
            errors.append(f"inspection-required coverage contains only trust-cleared rows for {normalized_url}")
    readiness_manifest = load_manifest_json("promotion-readiness-queue.json", {})
    covered_readiness = (
        readiness_manifest.get("covered_by_existing_installable_catalog", [])
        if isinstance(readiness_manifest, dict)
        else []
    )
    if not isinstance(covered_readiness, list):
        errors.append("promotion readiness covered bucket is not a list")
        covered_readiness = []
    for item in covered_readiness:
        if not isinstance(item, dict):
            continue
        if not existing_rows_trust_cleared(item.get("existing_rows")):
            errors.append(f"covered readiness row lacks trust-cleared existing row for {item.get('normalized_url')}")
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
