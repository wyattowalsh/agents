#!/usr/bin/env python3
"""Record a compact, secret-free post-install harness reconciliation snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from wagents.site_model import SUPPORTED_AGENT_IDS

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026" / "harness-install-assurance.json"
CATALOG_INDEX = ROOT / "docs" / "public" / "generated-registries" / "skills-catalog-index.json"
PROMOTION_OVERRIDES = OUTPUT.parent / "promotion-overrides.json"
EXPECTED_AGENTS = SUPPORTED_AGENT_IDS


def now() -> str:
    return datetime.now(UTC).isoformat()


def _count(payload: dict[str, Any], field: str) -> int:
    value = payload.get(field, [])
    if not isinstance(value, list):
        raise ValueError(f"agent field {field} must be a list")
    return len(value)


def build_assurance(source: Path) -> dict[str, Any]:
    raw = source.read_bytes()
    report = json.loads(raw)
    if not isinstance(report, dict) or report.get("mode") not in {"dry-run", "apply"} or report.get("ok") is not True:
        raise ValueError("input must be a successful `wagents skills sync --dry-run|--apply --format json` report")
    report_mode = str(report["mode"])
    agents = report.get("agents")
    if not isinstance(agents, list):
        raise ValueError("input agents must be a list")

    summaries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in agents:
        if not isinstance(item, dict):
            raise ValueError("input agent rows must be objects")
        agent = str(item.get("agent") or "")
        if not agent or agent in seen:
            raise ValueError(f"invalid or duplicate agent row: {agent!r}")
        seen.add(agent)
        unresolved = item.get("unresolved", [])
        if not isinstance(unresolved, list) or any(" — " not in str(row) for row in unresolved):
            raise ValueError(f"agent {agent} has unresolved rows without provenance reasons")
        summaries.append({
            "agent": agent,
            "already_present": _count(item, "already_present"),
            "missing": _count(item, "missing"),
            "pin_blocked": _count(item, "pin_blocked") if "pin_blocked" in item else 0,
            "unresolved": _count(item, "unresolved"),
            "unresolved_reason_counts": dict(
                sorted(Counter(str(row).rsplit(" — ", 1)[-1] for row in unresolved).items())
            ),
            "commands": _count(item, "commands"),
            "inventory_fallback_used": bool(str(item.get("warning") or "")),
            "error": bool(str(item.get("error") or "")),
        })

    if seen != set(EXPECTED_AGENTS):
        raise ValueError(f"expected agents {EXPECTED_AGENTS}, found {tuple(sorted(seen))}")
    complete = all(
        not item["error"] and item["missing"] == 0 and item["pin_blocked"] == 0 and item["commands"] == 0
        for item in summaries
    )
    catalog_bytes = CATALOG_INDEX.read_bytes()
    overrides_bytes = PROMOTION_OVERRIDES.read_bytes()
    catalog = json.loads(catalog_bytes)
    overrides = json.loads(overrides_bytes)
    return {
        "version": 1,
        "generated_at": now(),
        "assurance_kind": f"post-install-{report_mode}",
        "command": f"uv run wagents skills sync --{report_mode} --format json",
        "source_mode": report_mode,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "catalog_index_sha256": hashlib.sha256(catalog_bytes).hexdigest(),
        "promotion_overrides_sha256": hashlib.sha256(overrides_bytes).hexdigest(),
        "catalog_entry_count": len(catalog.get("allSkillIndex", [])),
        "promotion_override_count": len(overrides.get("overrides", [])),
        "inventory_count": report.get("inventory_count"),
        "complete": complete,
        "target_harness_count": len(summaries),
        "agents": summaries,
        "totals": {
            field: sum(int(item[field]) for item in summaries)
            for field in ("already_present", "missing", "pin_blocked", "unresolved", "commands")
        },
        "notes": (
            "Unresolved rows are non-syncable inventory traceability rows; completion requires zero missing, "
            "pin-blocked, command, and agent-error rows for the desired installable set."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    payload = build_assurance(args.input)
    if args.apply:
        OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0 if payload["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
