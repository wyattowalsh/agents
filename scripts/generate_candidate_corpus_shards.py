#!/usr/bin/env python3
"""Emit shard maps and coverage checks for candidate-corpus-jul2026 swarm."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
RAW_URLS = MANIFEST_DIR / "raw-urls.txt"
NORMALIZED = MANIFEST_DIR / "normalized-urls.json"
RECORDS_DIR = MANIFEST_DIR / "records"
MICRO_WAVE_SIZE = 49

CLUSTER_MAP = [
    {"id": "C01", "name": "swift-concurrency", "owners": ["twostraws/Swift-Concurrency-Agent-Skill", "AvdLee/Swift-Concurrency-Agent-Skill", "bocato/swift-testing-agent-skill"]},
    {"id": "C02", "name": "swift-testing", "owners": ["twostraws/Swift-Testing-Agent-Skill", "AvdLee/Swift-Testing-Agent-Skill", "bocato/swift-testing-agent-skill"]},
    {"id": "C03", "name": "terraform", "owners": ["antonbabenko/terraform-skill"]},
    {"id": "C04", "name": "solid-skills", "owners": ["ramziddin/solid-skills"]},
    {"id": "C05", "name": "unslop", "owners": ["MohamedAbdallah-14/unslop"]},
    {"id": "C06", "name": "ios-simulator", "owners": ["conorluddy/ios-simulator-skill"]},
    {"id": "C07", "name": "pm-skills", "owners": ["deanpeters/Product-Manager-Skills", "phuryn/pm-skills", "product-on-purpose/pm-skills"]},
]


def _load_normalized() -> dict:
    return json.loads(NORMALIZED.read_text(encoding="utf-8"))


def emit_all() -> None:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    if not NORMALIZED.exists():
        print("normalized-urls.json missing; run process_candidate_corpus.py --phase normalize first", file=sys.stderr)
        sys.exit(1)
    data = _load_normalized()
    entries = data["entries"]
    shard_map = {
        "version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "total": len(entries),
        "micro_wave_size": MICRO_WAVE_SIZE,
        "shards": [],
    }
    for i in range(0, len(entries), MICRO_WAVE_SIZE):
        chunk = entries[i : i + MICRO_WAVE_SIZE]
        shard_map["shards"].append(
            {
                "shard_id": f"MW-{i // MICRO_WAVE_SIZE + 1:02d}",
                "start_index": i,
                "count": len(chunk),
                "slugs": [e["slug"] for e in chunk],
            }
        )
    (MANIFEST_DIR / "shard-map-293.json").write_text(json.dumps(shard_map, indent=2) + "\n", encoding="utf-8")
    (MANIFEST_DIR / "cluster-map-18.json").write_text(json.dumps(CLUSTER_MAP, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote shard-map ({len(shard_map['shards'])} micro-waves) and cluster-map")


def check_coverage() -> int:
    if not RAW_URLS.exists() or not NORMALIZED.exists():
        print("Missing raw-urls or normalized-urls", file=sys.stderr)
        return 1
    raw_count = len([ln for ln in RAW_URLS.read_text(encoding="utf-8").splitlines() if ln.strip()])
    norm = _load_normalized()
    unique = len(norm.get("unique_targets", []))
    records = list(RECORDS_DIR.glob("*.json")) if RECORDS_DIR.exists() else []
    decisions_path = MANIFEST_DIR / "integration-decisions.json"
    decisions = 0
    if decisions_path.exists():
        decisions = len(json.loads(decisions_path.read_text(encoding="utf-8")).get("decisions", []))
    ok = raw_count == 293 and records and decisions >= unique - 5
    print(json.dumps({"raw": raw_count, "unique": unique, "records": len(records), "decisions": decisions, "ok": ok}, indent=2))
    return 0 if ok else 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit-all", action="store_true")
    parser.add_argument("--check-coverage", action="store_true")
    args = parser.parse_args()
    if args.emit_all:
        emit_all()
    elif args.check_coverage:
        sys.exit(check_coverage())
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()