# Candidate Corpus Full Integration State

- Phase: `promotion-overlay-installed`
- Complete: `false` for all-source installation; the safe/relevant install wave is complete and the 175 remaining rows are terminal trust-gated skip/reference decisions.
- Raw research lanes: 293
- Unique target synthesis lanes: 289
- Raw leaf checks: 5567
- Unique synthesis leaf checks: 2312
- Total leaf checks: 7879
- Installable curated rows: 1038
- Live install rows recorded: 1038
- Live install unique skill names: 1038
- Live install unique upstream selectors: 1038
- Promoted unique targets: 114
- Remaining reference-only rows: 175
- Duplicate/blocked selectors recorded outside installable rows: 0

## Promotion Waves

- `W00`: 14 targets
- `W01`: 15 targets
- `W02`: 28 targets
- `W03`: 27 targets
- `W04`: 22 targets
- `W05`: 26 targets
- `W06`: 21 targets
- `W07`: 30 targets
- `W08`: 101 targets
- `W99`: 5 targets
- `W10-live-overlay`: 1038 installable curated rows across 114 unique targets

## Current Gate

Every raw candidate remains represented. The promotion overlay installed every license-cleared, non-quarantine Skills CLI selector that survived duplicate-name and repo-owned collision checks. Remaining reference-only rows are explicit terminal safety decisions because of unclear license, inaccessible source, quarantine risk, no safe install surface, or duplicate/canonical-source decisions.

## Assurance Evidence

- `uv run python scripts/apply_candidate_corpus_promotions.py --check` passed for 1038 overrides.
- `uv run wagents validate` passed after the promotion overlay.
- `uv run wagents docs generate --no-installed --check` passed after docs regeneration.
- `uv run wagents docs build` passed after cache cleanup; Astro generated `docs/dist/` and reported all internal links valid.
- Install-root verification found 0 missing `SKILL.md` files across `~/.agents/skills`, `~/.claude/skills`, `~/.config/crush/skills`, and `~/.grok/skills` for promoted live-install rows, with `opsx:tdd` normalized to `opsx-tdd` on disk.

## Ongoing Guardrails

- Keep credentialed, destructive, account-backed, or unclear-license sources disabled from default MCP/plugin exposure.
- Preserve unrelated dirty files outside this candidate-corpus wave.
