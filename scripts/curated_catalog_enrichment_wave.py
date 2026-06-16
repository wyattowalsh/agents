#!/usr/bin/env python3
"""Orchestrate curated catalog enrichment waves.

W0: write curated inventory JSON (from external-skills config)
W1: call seed_curated_config_research (writes skill-research artifacts)
W2: partition via partition_skills_by_source (GROUP BY _skills_install_source), emit batch-*.md packets + batches.json
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Curated catalog enrichment wave orchestrator")
    parser.add_argument("--session", default="curated-catalog-enrichment-20260616")
    parser.add_argument("--dry-run", action="store_true", help="Do not call seed (write plan only)")
    parser.add_argument("--refresh", action="store_true", help="Force overwrite of research artifacts")
    parser.add_argument("--batch-max", type=int, default=8, help="Max skills per grouped batch")
    parser.add_argument(
        "--curated-status",
        default=None,
        help="Optional status filter (e.g. install-now-after-trust-gate)",
    )
    args = parser.parse_args()

    session = REPO / "artifacts" / args.session
    wave0 = session / "wave0"
    wave1 = session / "wave1"
    wave2 = session / "wave2"
    for d in (wave0, wave1, wave2):
        d.mkdir(parents=True, exist_ok=True)

    # W0: inventory JSON
    from wagents.external_skills import read_external_skill_entries

    entries = read_external_skill_entries()
    if args.curated_status:
        entries = [e for e in entries if e.status == args.curated_status]
    inv_rows = [e.public_dict() for e in entries]
    w0_payload = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "count": len(inv_rows),
        "rows": inv_rows,
        "curated_status_filter": args.curated_status,
    }
    (wave0 / "curated-inventory.json").write_text(json.dumps(w0_payload, indent=2, sort_keys=True), encoding="utf-8")

    # W1: seed curated research (uses build_curated... and write_artifact)
    from wagents.skill_research import seed_curated_config_research

    if args.dry_run:
        seeded = []
        (wave1 / "seed-plan.json").write_text(
            json.dumps({"dry_run": True, "would_seed": len(entries), "status": args.curated_status}, indent=2),
            encoding="utf-8",
        )
    else:
        seeded = seed_curated_config_research(curated_status=args.curated_status, overwrite=bool(args.refresh))
        (wave1 / "seeded.json").write_text(
            json.dumps({"written": [str(p) for p in seeded], "count": len(seeded)}, indent=2),
            encoding="utf-8",
        )

    # W2: use partition_skills_by_source (now groups by install_source) + emit packets + batches.json
    from wagents.skill_research import build_batch_prompt, partition_skills_by_source

    # collect and let partition do the grouping+chunking; we will post-select curated to keep packets focused
    all_batches = partition_skills_by_source(
        batch_max=args.batch_max,
        curated_status=args.curated_status,
        include_installed=False,
    )
    curated_batches: list[list[Any]] = []
    for b in all_batches:
        cb = [doc for doc in b if getattr(doc, "source_type", "") == "curated-external"]
        if cb:
            curated_batches.append(cb)

    batch_records: list[dict[str, Any]] = []
    for idx, batch in enumerate(curated_batches, start=1):
        names = [d.id for d in batch]
        sources = sorted({str((d.node.metadata or {}).get("_skills_install_source") or "unknown") for d in batch})
        prompt = build_batch_prompt(batch)
        rec = {
            "batch": idx,
            "skills": names,
            "count": len(names),
            "grouped_by_install_source": sources,
            "prompt_preview": prompt[:800] + ("..." if len(prompt) > 800 else ""),
        }
        batch_records.append(rec)
        pkt_path = wave2 / f"batch-{idx:02d}.md"
        lines = [
            f"# Curated Catalog Enrichment — Batch {idx}",
            "",
            f"**Skills ({len(names)}):** {', '.join(names)}",
            f"**Install sources (grouped):** {', '.join(sources)}",
            "",
            "## Research Prompt",
            "",
            prompt,
            "",
            "> Use for subagent batch research. Write resulting artifacts to docs/src/skill-research/<name>.md",
            "> Redact any local paths. Evidence only; not authority.",
        ]
        pkt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    batches_path = wave2 / "batches.json"
    batches_path.write_text(
        json.dumps(
            {
                "total_batches": len(curated_batches),
                "batch_max": args.batch_max,
                "curated_status": args.curated_status,
                "batches": batch_records,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    summary = {
        "session": str(session),
        "w0_curated": len(inv_rows),
        "w1_seeded": len(seeded) if not args.dry_run else 0,
        "w2_batches": len(curated_batches),
        "dry_run": args.dry_run,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
