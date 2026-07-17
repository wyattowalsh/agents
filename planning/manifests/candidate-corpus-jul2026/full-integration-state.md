# Candidate Corpus Full Integration State

- Phase: `corpus-integration-complete`
- Complete: `true`
- Completion scope: Complete for the July 2026 corpus: every normalized target maps to a permanent catalog integration and one runtime disposition; 1267 skill rows are reconciled across nine harnesses and 63/63 non-skill artifacts are verified, while candidate MCPs, broad-hook plugins, credentials, and quarantines retain their explicit activation gates.
- Raw research lanes: 293
- Unique target synthesis lanes: 289
- Live install eligible: 0
- New install command preview status: `no-live-install-commands-emitted`
- Recorded install evidence rows: 1267
- Installed path references verified: 4031/4031
- Missing installed `SKILL.md` files: 0
- Non-skill runtime artifacts verified: 63/63
- Non-skill normalized targets accounted for: 289/289
- Candidate MCP and broad-hook plugin activation remains explicit and disabled by default.
- Covered by existing installable catalog rows: 121
- Promoted installable catalog rows: 1267
- Integrated normalized targets: 289/289
- Unintegrated normalized targets: 0
- Integration classifications: {'inspection-existing': 6, 'installable-existing': 121, 'integrated-quarantine-reference': 4, 'integrated-reference': 158}
- Ready for repo promotion: 0
- Ready for live install: 0
- Terminal native or hard-blocked rows: 168
- Terminal non-install traceability rows: 162
- Promoted unique targets: 115
- Integrated quarantine reference targets: 4
- Active install blocks: 4

## Overlay Evidence

`live-install-command-preview.json` remains the no-new-live-install gate artifact. The reviewed catalog promotion overlay and install evidence are recorded in `promotion-overrides.json`, `applied-promotion-overrides.json`, `catalog-authoring-summary.json`, `harness-install-assurance.json`, `non-skill-install-assurance.json`, and this state report.

- Required closeout: `uv run python scripts/apply_candidate_corpus_promotions.py --check` for 1267 overrides.
- `uv run python scripts/promote_candidate_corpus.py --final-check` reconciles deep-source audit evidence, 1267 promoted overrides, 1267 install-evidence rows, and 289 terminal target decisions.
- Install-root verification found 0 missing `SKILL.md` files.
- Quarantined targets are integrated as non-installable reference rows. Their install blocks remain active until a separate reviewed decision changes the source evidence.
