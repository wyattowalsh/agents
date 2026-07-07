# Candidate Corpus Full Integration State

- Phase: `research-graph-ready`
- Complete: `false`
- Raw research lanes: 293
- Unique target synthesis lanes: 289
- Raw leaf checks: 5567
- Unique synthesis leaf checks: 2312
- Total leaf checks: 7879
- Live install eligible: 0
- Existing integration coverage: covered-by-existing-installable-catalog=13, covered-by-existing-reference=1, needs-promotion-review=275
- Ready for repo promotion: 0
- Blocked until trust gates: 289

## Promotion Waves

- `W00`: 13 targets
- `W01`: 15 targets
- `W02`: 28 targets
- `W03`: 27 targets
- `W04`: 22 targets
- `W05`: 26 targets
- `W06`: 21 targets
- `W07`: 30 targets
- `W08`: 102 targets
- `W99`: 5 targets

## Current Gate

Every candidate is represented, but live install and repo-native promotion remain blocked until source-list, license, security, attribution, auth, and docs-steward gates pass.

## Next Actions

- Dispatch read-only source research packets for each U### lane.
- Promote only the N### targets whose raw lanes pass trust gates.
- Regenerate docs-steward surfaces after each promotion wave.
- Run focused validation and commit each validated wave if still authorized.
