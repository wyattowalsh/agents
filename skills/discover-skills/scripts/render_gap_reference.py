#!/usr/bin/env python3
"""Render references/gap-analysis.md from discovery-taxonomy.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _paths import data_dir, skill_dir
from schemas import load_json


def render_markdown(taxonomy: dict) -> str:
    lines = [
        "# Gap Analysis Reference",
        "",
        "Generated from `data/discovery-taxonomy.json`. Do not edit the domain table by hand.",
        "",
        "## Domain Taxonomy",
        "",
        "| Domain | Existing Skills | Coverage |",
        "|--------|-----------------|----------|",
    ]
    for domain in taxonomy.get("domains", []):
        skills = ", ".join(domain.get("existing_skills", [])) or "—"
        lines.append(f"| {domain.get('name', '')} | {skills} | {domain.get('coverage', '')} |")

    lines.extend(
        [
            "",
            "## Priority Formula",
            "",
            "`priority = gap_severity × domain_relevance × solution_availability`",
            "",
            "See `data/discovery-taxonomy.json` for severity weights and scout queries.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render gap-analysis reference")
    parser.add_argument("--taxonomy", type=Path, default=None)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args(argv)

    taxonomy = load_json(args.taxonomy or data_dir() / "discovery-taxonomy.json")
    output = args.output or skill_dir() / "references" / "gap-analysis.md"
    output.write_text(render_markdown(taxonomy), encoding="utf-8")
    print(json.dumps({"output": str(output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())