# Candidate Corpus Full Integration State

- Phase: `promotion-overlay-installed`
- Complete: `true`
- Completion scope: Complete for the July 2026 candidate-corpus goal as a trust-gated catalog integration overlay; conservative intake, packet, gate, and install-evidence artifacts remain available for traceability.
- Raw research lanes: 293
- Unique target synthesis lanes: 289
- Live install eligible: 0
- Live install status: `no-live-install-commands-emitted`
- Live install note: no new installer commands remain to emit during validation; 1038 install evidence rows are recorded and 3115 installed `SKILL.md` path references are verified.
- Recorded install evidence rows: 1038
- Installed path references verified: 3115/3115
- Missing installed `SKILL.md` files: 0
- Covered by existing installable catalog rows: 120
- Promoted installable catalog rows: 1038
- Ready for repo promotion: 0
- Ready for live install: 0
- Blocked until trust gates: 169
- Remaining reference or terminal-gated rows: 175
- Promoted unique targets: 114

## Overlay Evidence

`live-install-command-preview.json` remains the no-new-live-install gate artifact. The reviewed catalog promotion overlay and install evidence are recorded in `promotion-overrides.json`, `applied-promotion-overrides.json`, `catalog-authoring-summary.json`, and this state report.

- `uv run python scripts/apply_candidate_corpus_promotions.py --check` passed for 1038 overrides.
- `uv run python scripts/promote_candidate_corpus.py --final-check` reconciles deep-source audit evidence, 1038 promoted overrides, 1038 install-evidence rows, and 289 terminal target decisions.
- Install-root verification found 0 missing `SKILL.md` files.
