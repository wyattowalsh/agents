#!/usr/bin/env python3
"""Migrate curated external skills from config/external-skills.md into authoring mdx sources.

For each ExternalSkillEntry, writes docs/src/authoring/skills/{name}.mdx with:
- source_kind: curated-external
- projected frontmatter fields for ExternalSkillEntry reconstruction
- minimal body with a generated marker comment

Usage:
    uv run python scripts/migrate_external_skills_to_authoring_mdx.py [--dry-run]

One-time bootstrap from legacy config/external-skills.md. Ongoing curation edits
docs/src/authoring/skills/<id>.mdx directly; use emit_external_skills_projection.py
only if a legacy markdown projection is still needed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure repo root on path when run directly
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from wagents.external_skills import ExternalSkillEntry, read_external_skill_entries  # noqa: E402
from wagents.skill_index import AUTHORING_SKILLS_DIR  # noqa: E402

GENERATED_MARKER = (
    "{{/* GENERATED-AUTHORING: source=config/external-skills.md; entry={name}; re-run migration to refresh */}}"
)


def _render_frontmatter(entry: ExternalSkillEntry) -> str:
    lines: list[str] = ["---"]
    lines.append(f'name: "{entry.name}"')
    desc = (entry.notes or entry.description if hasattr(entry, "description") else entry.notes) or ""
    # Fallback description from notes
    if not desc:
        desc = f"Curated external skill from {entry.source or 'external source'}."
    d = str(desc).replace('"', '\\"')
    lines.append(f'description: "{d}"')
    lines.append(f'title: "{entry.name.replace("-", " ").title()}"')
    lines.append('source_kind: "curated-external"')
    if entry.source:
        lines.append(f'source: "{entry.source}"')
    if entry.install_source:
        lines.append(f'install_source: "{entry.install_source}"')
    if entry.status:
        lines.append(f'status: "{entry.status}"')
    if entry.trust_tier:
        lines.append(f'trust_tier: "{entry.trust_tier}"')
    if entry.provenance_status:
        lines.append(f'provenance_status: "{entry.provenance_status}"')
    if entry.install_command:
        lines.append(f'install_command: "{entry.install_command}"')
    if entry.target_agents:
        ta = ", ".join(entry.target_agents)
        lines.append(f"target_agents: [{ta}]")
    if entry.source_url:
        lines.append(f'source_url: "{entry.source_url}"')
    if entry.notes:
        n = str(entry.notes).replace('"', '\\"')
        lines.append(f'notes: "{n}"')
    if entry.risk_notes:
        r = str(entry.risk_notes).replace('"', '\\"')
        lines.append(f'risk_notes: "{r}"')
    if entry.promotion_policy:
        p = str(entry.promotion_policy).replace('"', '\\"')
        lines.append(f'promotion_policy: "{p}"')
    if entry.provenance_evidence:
        e = str(entry.provenance_evidence).replace('"', '\\"')
        lines.append(f'provenance_evidence: "{e}"')
    if entry.selector_mode and entry.selector_mode != "named":
        lines.append(f'selector_mode: "{entry.selector_mode}"')
    if entry.unresolved_reason:
        u = str(entry.unresolved_reason).replace('"', '\\"')
        lines.append(f'unresolved_reason: "{u}"')
    if entry.unsupported_target_agents:
        uta = ", ".join(entry.unsupported_target_agents)
        lines.append(f"unsupported_target_agents: [{uta}]")
    lines.append("---")
    return "\n".join(lines)


def _render_body(entry: ExternalSkillEntry) -> str:
    marker = GENERATED_MARKER.format(name=entry.name)
    # Keep body intentionally small; research can enrich later in docs pipeline
    parts = [marker, ""]
    if entry.notes:
        parts.append(str(entry.notes).strip())
    parts.append("")
    return "\n".join(parts)


def migrate_external_skills_to_authoring_mdx(
    *,
    dry_run: bool = False,
    authoring_dir: Path | None = None,
    entries: list[ExternalSkillEntry] | None = None,
) -> list[Path]:
    """Write one authoring mdx per curated external entry. Returns target paths."""
    base = authoring_dir or AUTHORING_SKILLS_DIR
    base.mkdir(parents=True, exist_ok=True)

    source_rows = read_external_skill_entries() if entries is None else entries
    rows = list(source_rows)
    written: list[Path] = []

    for entry in rows:
        front = _render_frontmatter(entry)
        body = _render_body(entry)
        content = f"{front}\n\n{body}"
        target = base / f"{entry.name}.mdx"
        if dry_run:
            written.append(target)
            continue
        target.write_text(content, encoding="utf-8")
        written.append(target)

    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate external-skills.md entries to authoring mdx")
    parser.add_argument("--dry-run", action="store_true", help="Print intended writes without touching disk")
    parser.add_argument("--count", action="store_true", help="Print number of entries and exit")
    args = parser.parse_args(argv)

    entries = read_external_skill_entries()
    if args.count:
        print(len(entries))
        return 0

    targets = migrate_external_skills_to_authoring_mdx(dry_run=args.dry_run)
    if args.dry_run:
        for t in targets:
            print(f"DRY: {t}")
    else:
        print(f"Wrote {len(targets)} authoring mdx files to {AUTHORING_SKILLS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
