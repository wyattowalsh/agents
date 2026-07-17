"""Shared renderers for candidate-corpus planning reports."""

from __future__ import annotations

from collections import Counter
from typing import Any, cast

TERMINAL_PROMOTION_WAVE_STATUS = "terminal-integration-wave-plan-generated"
TERMINAL_PROMOTION_POLICY = (
    "Terminal routing is generated from read-only evidence; live execution stays user-owned and "
    "hard-blocked rows remain non-installable."
)
TERMINAL_PROMOTION_ASSIGNMENT_RULE = (
    "Each normalized target is assigned to exactly one promotion wave by source URL, category, "
    "artifact type, and subresource text; Composio, Pedronauck, OpenSpec, and Obsidian sources "
    "are reserved for final reconciliation."
)
W00_MUTATION_POLICY = "no mutation; use existing catalog rows"
W99_MUTATION_POLICY = "authoring-only stable quarantine reference; no install"
STANDARD_MUTATION_POLICY = "single integrator only after read-only research packets pass"
RUNNER_CHECKLIST_HEADING = "## Runner-Owned Validation Checklist"
RUNNER_RESULTS_HEADING = "## Observed Closeout Results"

_REQUIRED_PLAN_FIELDS = (
    "status",
    "wave_count",
    "total_targets",
    "unique_targets_assigned",
    "raw_entries_covered",
    "live_install_eligible_count",
    "assignment_rule",
    "waves",
)
_REQUIRED_WAVE_FIELDS = (
    "wave_id",
    "name",
    "target_count",
    "promotion_policy",
    "mutation_policy",
    "targets",
)


def mutation_policy_for_wave(wave_id: str) -> str:
    """Return the canonical mutation policy for a promotion wave."""
    if wave_id == "W00":
        return W00_MUTATION_POLICY
    if wave_id == "W99":
        return W99_MUTATION_POLICY
    return STANDARD_MUTATION_POLICY


def validate_promotion_wave_plan(plan: Any) -> list[str]:
    """Return strict terminal promotion-plan contract errors."""
    if not isinstance(plan, dict):
        return ["promotion wave plan payload is not an object"]

    errors: list[str] = [
        f"promotion wave plan missing required field {field}" for field in _REQUIRED_PLAN_FIELDS if field not in plan
    ]
    if errors:
        return errors

    waves = plan["waves"]
    if not isinstance(waves, list):
        return ["promotion wave plan waves is not a list"]
    if plan["status"] != TERMINAL_PROMOTION_WAVE_STATUS:
        errors.append("promotion wave plan status is not terminal-integration-wave-plan-generated")
    if (
        not isinstance(plan["wave_count"], int)
        or isinstance(plan["wave_count"], bool)
        or plan["wave_count"] != len(waves)
    ):
        errors.append("promotion wave plan wave_count does not match waves")
    for field in ("total_targets", "unique_targets_assigned", "raw_entries_covered", "live_install_eligible_count"):
        value = plan[field]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"promotion wave plan {field} is not a non-negative integer")
    if plan["live_install_eligible_count"] != 0:
        errors.append("promotion wave plan live_install_eligible_count is not zero")
    if plan["unique_targets_assigned"] != plan["total_targets"]:
        errors.append("promotion wave plan unique target count does not match total_targets")
    if plan["assignment_rule"] != TERMINAL_PROMOTION_ASSIGNMENT_RULE:
        errors.append("promotion wave plan assignment_rule is not canonical")

    wave_ids: list[str] = []
    target_urls: list[str] = []
    raw_indexes: set[int] = set()
    target_total = 0
    for index, wave in enumerate(waves):
        if not isinstance(wave, dict):
            errors.append(f"promotion wave plan wave {index + 1} is not an object")
            continue
        wave_data = cast("dict[str, Any]", wave)
        for field in _REQUIRED_WAVE_FIELDS:
            if field not in wave_data:
                errors.append(f"promotion wave plan wave {index + 1} missing required field {field}")
        if any(field not in wave_data for field in _REQUIRED_WAVE_FIELDS):
            continue
        wave_id = wave_data["wave_id"]
        if not isinstance(wave_id, str) or not wave_id:
            errors.append(f"promotion wave plan wave {index + 1} has invalid wave_id")
            continue
        wave_ids.append(wave_id)
        if not isinstance(wave_data["name"], str) or not wave_data["name"].strip():
            errors.append(f"promotion wave {wave_id} has empty name")
        targets = wave_data["targets"]
        if not isinstance(targets, list):
            errors.append(f"promotion wave {wave_id} targets is not a list")
            continue
        target_count = wave_data["target_count"]
        if not isinstance(target_count, int) or isinstance(target_count, bool) or target_count != len(targets):
            errors.append(f"promotion wave {wave_id} target_count does not match targets")
        else:
            target_total += target_count
        if wave_data["promotion_policy"] != TERMINAL_PROMOTION_POLICY:
            errors.append(f"promotion wave {wave_id} promotion_policy is not canonical")
        if wave_data["mutation_policy"] != mutation_policy_for_wave(wave_id):
            errors.append(f"promotion wave {wave_id} mutation_policy is not canonical")
        for target_index, target in enumerate(targets):
            if not isinstance(target, dict):
                errors.append(f"promotion wave {wave_id} target {target_index + 1} is not an object")
                continue
            target_data = cast("dict[str, Any]", target)
            normalized_url = target_data.get("normalized_url")
            if not isinstance(normalized_url, str) or not normalized_url.strip():
                errors.append(f"promotion wave {wave_id} target {target_index + 1} has no normalized_url")
                continue
            target_urls.append(normalized_url)
            target_raw_indexes = target_data.get("raw_indexes")
            if isinstance(target_raw_indexes, list):
                for raw_index in target_raw_indexes:
                    if isinstance(raw_index, int) and not isinstance(raw_index, bool):
                        raw_indexes.add(raw_index)
                    elif isinstance(raw_index, str) and raw_index.isdigit():
                        raw_indexes.add(int(raw_index))

    if len(wave_ids) != len(set(wave_ids)):
        errors.append("promotion wave plan contains duplicate wave IDs")
    if "W00" not in wave_ids or "W99" not in wave_ids:
        errors.append("promotion wave plan must include W00 and W99")
    if target_total != plan["total_targets"]:
        errors.append("promotion wave plan target counts do not match total_targets")
    if len(target_urls) != len(set(target_urls)):
        errors.append("promotion wave plan assigns a normalized target more than once")
    if target_urls and len(target_urls) != plan["unique_targets_assigned"]:
        errors.append("promotion wave plan target identities do not match unique_targets_assigned")
    if raw_indexes and len(raw_indexes) != plan["raw_entries_covered"]:
        errors.append("promotion wave plan raw indexes do not match raw_entries_covered")
    return errors


def preserve_runner_owned_results(rendered: str, existing: str) -> str:
    """Append an existing runner-owned results section without synthesizing outcomes."""
    marker = f"\n{RUNNER_RESULTS_HEADING}\n"
    if marker not in existing:
        return rendered.rstrip() + "\n"
    runner_section = existing.split(marker, 1)[1].strip()
    if not runner_section:
        return rendered.rstrip() + "\n"
    return f"{rendered.rstrip()}\n\n{RUNNER_RESULTS_HEADING}\n\n{runner_section}\n"


def _sorted_count_text(counts: Counter[str] | dict[str, int]) -> str:
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "none"


def _wave_raw_indexes(wave: dict[str, Any]) -> list[int]:
    raw_indexes: set[int] = set()
    for target in wave.get("targets", []):
        if not isinstance(target, dict):
            continue
        for index in target.get("raw_indexes", []):
            if isinstance(index, int):
                raw_indexes.add(index)
            elif isinstance(index, str) and index.isdigit():
                raw_indexes.add(int(index))
    if raw_indexes:
        return sorted(raw_indexes)
    fallback_indexes: set[int] = set()
    for index in wave.get("raw_indexes", []):
        if isinstance(index, int):
            fallback_indexes.add(index)
        elif isinstance(index, str) and index.isdigit():
            fallback_indexes.add(int(index))
    return sorted(fallback_indexes)


def render_promotion_wave_report(plan: dict[str, Any]) -> str:
    """Render the human-facing promotion wave plan from the machine manifest."""
    errors = validate_promotion_wave_plan(plan)
    if errors:
        raise ValueError("Invalid promotion wave plan:\n- " + "\n- ".join(errors))
    status = plan["status"]
    waves = plan["waves"]
    wave_count = plan["wave_count"]
    assigned_count = plan["unique_targets_assigned"]
    raw_count = plan["raw_entries_covered"]
    live_install_eligible = plan["live_install_eligible_count"]
    lines = [
        "# Candidate Corpus Promotion Wave Plan",
        "",
        f"- Status: `{status}`",
        f"- Waves: {wave_count}",
        f"- Unique targets assigned: {assigned_count}",
        f"- Raw entries covered: {raw_count}",
        f"- Live install eligible: {live_install_eligible}",
        f"- Assignment rule: {plan['assignment_rule']}",
        "",
        "## Waves",
        "",
    ]
    for wave in waves:
        coverage_counts = wave.get("coverage_status_counts")
        if coverage_counts is None:
            coverage_counts = Counter(
                target.get("coverage_status", "unknown")
                for target in wave.get("targets", [])
                if isinstance(target, dict)
            )
        risk_counts = wave.get("risk_tier_counts")
        if risk_counts is None:
            risk_counts = Counter(
                target.get("risk_tier", "unclassified")
                for target in wave.get("targets", [])
                if isinstance(target, dict)
            )
        raw_indexes = _wave_raw_indexes(wave)
        coverage = _sorted_count_text(coverage_counts)
        risks = _sorted_count_text(risk_counts)
        lines.extend([
            f"### {wave['wave_id']} {wave['name']}",
            "",
            f"- Objective: {wave.get('objective', wave.get('description', 'Promotion wave'))}",
            f"- Unique targets: {wave.get('unique_target_count', wave['target_count'])}",
            f"- Raw entries: {wave.get('raw_entry_count', len(raw_indexes))}",
            f"- Coverage: {coverage}",
            f"- Risk tiers: {risks}",
            f"- Promotion policy: {wave['promotion_policy']}",
            f"- Mutation policy: {wave['mutation_policy']}",
            "",
        ])
    return "\n".join(lines) + "\n"
