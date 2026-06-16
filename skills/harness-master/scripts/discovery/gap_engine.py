#!/usr/bin/env python3
"""Compute GapReport from taxonomy + scan artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _paths import data_dir
from schemas import DomainGap, GapReport, load_json, utc_now_iso, validate_gap_report, write_json

CLASSIFICATION_HIGH = 9
CLASSIFICATION_MEDIUM = 4


def load_taxonomy(path: Path | None = None) -> dict[str, Any]:
    taxonomy_path = path or data_dir() / "discovery-taxonomy.json"
    return load_json(taxonomy_path)


def classify_priority(priority: int, *, high: int, medium: int) -> str:
    if priority >= high:
        return "high"
    if priority >= medium:
        return "medium"
    return "low"


def compute_domains(
    taxonomy: dict[str, Any],
    inventory: dict[str, Any] | None,
) -> list[DomainGap]:
    severity_map = taxonomy.get("coverage_severity", {})
    default_rel = int(taxonomy.get("default_domain_relevance", 2))
    default_avail = int(taxonomy.get("default_solution_availability", 2))
    high = int(taxonomy.get("priority_high", CLASSIFICATION_HIGH))
    medium = int(taxonomy.get("priority_medium", CLASSIFICATION_MEDIUM))

    skill_names: set[str] = set()
    if inventory:
        for item in inventory.get("skills", []):
            if isinstance(item, dict) and item.get("name"):
                skill_names.add(str(item["name"]))

    domains: list[DomainGap] = []
    for entry in taxonomy.get("domains", []):
        if not isinstance(entry, dict):
            continue
        coverage = str(entry.get("coverage", "none")).lower()
        severity = int(severity_map.get(coverage, 0))
        priority = severity * default_rel * default_avail
        existing = [str(s) for s in entry.get("existing_skills", [])]
        present = [name for name in existing if name in skill_names]
        gaps = [name for name in existing if name not in skill_names]
        if coverage in {"none", "low"} and not gaps:
            gaps = list(entry.get("scout_queries", []))[:3]

        domains.append(
            DomainGap(
                id=str(entry.get("id", "")),
                name=str(entry.get("name", "")),
                coverage=coverage,
                priority=priority,
                existing_skills=present or existing,
                gaps=gaps,
                scout_queries=[str(q) for q in entry.get("scout_queries", [])],
                classification=classify_priority(priority, high=high, medium=medium),
            )
        )

    domains.sort(key=lambda d: (-d.priority, d.name))
    return domains


def merge_asset_sections(
    *,
    mcp: dict[str, Any] | None,
    plugins: dict[str, Any] | None,
    harness: dict[str, Any] | None,
    hooks: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    mcp_out = mcp or {"present": [], "gaps": [], "blind_spots": []}
    plugins_out = plugins or {"stale_latest": [], "overlaps": []}
    harness_out = harness or {"blind_spots": [], "missing_surfaces": []}
    hooks_out = hooks or {"gaps": [], "blind_spots": [], "registry": {}}
    return mcp_out, plugins_out, harness_out, hooks_out


def build_gap_report(
    *,
    taxonomy: dict[str, Any],
    inventory: dict[str, Any] | None = None,
    mcp: dict[str, Any] | None = None,
    plugins: dict[str, Any] | None = None,
    harness: dict[str, Any] | None = None,
    hooks: dict[str, Any] | None = None,
) -> GapReport:
    domains = compute_domains(taxonomy, inventory)
    mcp_out, plugins_out, harness_out, hooks_out = merge_asset_sections(
        mcp=mcp, plugins=plugins, harness=harness, hooks=hooks
    )

    repo_count = int(inventory.get("repo_count", 0)) if inventory else 0
    installed_count = int(inventory.get("installed_count", 0)) if inventory else 0

    return GapReport(
        version=1,
        generated_at=utc_now_iso(),
        repo_skill_count=repo_count,
        installed_skill_count=installed_count,
        domains=domains,
        mcp=mcp_out,
        plugins=plugins_out,
        harness=harness_out,
        hooks=hooks_out,
        dedup_exclusions=[str(x) for x in taxonomy.get("dedup_exclusions", [])],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build GapReport JSON")
    parser.add_argument("--taxonomy", type=Path, default=None)
    parser.add_argument("--inventory", type=Path, default=None)
    parser.add_argument("--mcp", type=Path, default=None)
    parser.add_argument("--plugins", type=Path, default=None)
    parser.add_argument("--harness", type=Path, default=None)
    parser.add_argument("--hooks", type=Path, default=None)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args(argv)

    taxonomy = load_taxonomy(args.taxonomy)
    inventory = load_json(args.inventory) if args.inventory else None
    mcp = load_json(args.mcp) if args.mcp else None
    plugins = load_json(args.plugins) if args.plugins else None
    harness = load_json(args.harness) if args.harness else None
    hooks = load_json(args.hooks) if args.hooks else None

    report = build_gap_report(
        taxonomy=taxonomy,
        inventory=inventory,
        mcp=mcp,
        plugins=plugins,
        harness=harness,
        hooks=hooks,
    )
    payload = report.public_dict()
    errors = validate_gap_report(payload)
    if errors:
        print(json.dumps({"errors": errors}, indent=2), file=sys.stderr)
        return 1

    if args.output:
        write_json(args.output, payload)
    else:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())