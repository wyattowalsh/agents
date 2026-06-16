#!/usr/bin/env python3
"""Merge scout artifacts into ranked candidate lists."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from schemas import build_install_command, dedup_key, load_agent_targets, write_json

CONFIDENCE_HIGH_INSTALLS = 1000
CONFIDENCE_MEDIUM_INSTALLS = 100


def tier_from_installs(count: int | None) -> str:
    if count is None:
        return "investigate"
    if count >= CONFIDENCE_HIGH_INSTALLS:
        return "high"
    if count >= CONFIDENCE_MEDIUM_INSTALLS:
        return "medium"
    return "investigate"


def merge_candidates(
    artifacts_dir: Path,
    *,
    existing_names: set[str],
    agents: list[str],
) -> dict[str, Any]:
    merged: dict[str, dict[str, Any]] = {}
    errors: list[str] = []

    for path in sorted(artifacts_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append(f"{path.name}:invalid-json")
            continue

        for candidate in data.get("candidates", []):
            if not isinstance(candidate, dict):
                continue
            name = str(candidate.get("name", "")).strip()
            source = str(candidate.get("source", "")).strip()
            if not name or not source:
                continue
            if name in existing_names:
                continue
            key = dedup_key(name, source)
            installs = candidate.get("install_count")
            if isinstance(installs, str) and installs.isdigit():
                installs = int(installs)
            tier = tier_from_installs(installs if isinstance(installs, int) else None)
            entry = {
                "name": name,
                "source": source,
                "install_count": installs,
                "confidence": tier,
                "fills_gap": candidate.get("fills_gap", ""),
                "install_command": candidate.get("install_command")
                or build_install_command(source, name, agents=agents),
                "dedup_key": key,
                "from_task": data.get("task_id", path.stem),
            }
            prev = merged.get(key)
            if prev is None or (installs or 0) > (prev.get("install_count") or 0):
                merged[key] = entry

    by_tier: dict[str, list[dict[str, Any]]] = {"high": [], "medium": [], "investigate": []}
    for entry in merged.values():
        by_tier.setdefault(str(entry["confidence"]), []).append(entry)

    for tier in by_tier:
        by_tier[tier].sort(key=lambda e: (-(e.get("install_count") or 0), e["name"]))

    return {
        "version": 1,
        "total": len(merged),
        "tiers": by_tier,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Merge scout artifacts")
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--gap-report", type=Path, default=None)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args(argv)

    existing: set[str] = set()
    if args.gap_report and args.gap_report.is_file():
        gap = json.loads(args.gap_report.read_text(encoding="utf-8"))
        for domain in gap.get("domains", []):
            if isinstance(domain, dict):
                for name in domain.get("existing_skills", []):
                    existing.add(str(name))

    agents = load_agent_targets()
    result = merge_candidates(args.artifacts, existing_names=existing, agents=agents)
    write_json(args.output, result)
    print(json.dumps({"total": result["total"], "errors": result["errors"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())