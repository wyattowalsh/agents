# Repo Cleanup Review Evidence

Generated: 2026-06-29

## W0 baseline (G-RC-0)

| Task | Result |
| --- | --- |
| T001 diff stat | 1384 files changed |
| T002 workstreams | docs=1216, skills=72, tests=23, wagents=16 |
| T004 bundles | A=1490 paths, B=9 paths |
| T005 legacy grep | Active: harness evals (fixed), spec/kb historical OK |
| T006 WAGENTS_CATALOG_LEGACY | 0 in production Python |
| T007 external_skills contract | index+authoring merge; path= for tests only |
| T009 pre-commit vs CI | Core parity; CI superset for portability/sync |
| T011 OpenSpec | 14 active changes (deferred archive) |

## W1 review lanes

| Lane | Key outcome |
| --- | --- |
| L-catalog | Legacy MD gone; transitional authoring+index merge (deferred) |
| L-validate | Extract complete; quarantine gap found → fixed |
| L-gates | Pre-commit/CI aligned on core; CI deeper |
| L-drift | harness-master evals stale → fixed |
| L-instructions | No legacy MD in live instructions |

## W3 fixes applied

- harness-master evals: authoring MDX + catalog index SSOT wording
- quarantine collector: authoring MDX scan + corrupt index error reporting
- authoring collector: removed stale noqa directives
- test: `test_quarantine_slug_in_authoring_mdx`

## Gate matrix (run 1 — post-fix)

| Check | Status |
| --- | --- |
| ruff check | pass |
| ty check | pass |
| wagents validate | pass |
| docs compose 100% | pass (397/397) |
| readme --check | pass |
| sync_agent_stack repo | pass |
| openspec validate | pass |
| catalog index --check | pass |
| skills sync --dry-run | pass |
| sync_skill_portability | pass |
| pytest targeted shards | pass (29+32+81) |
| pytest full | pass (1302) |
| SKILL_PORTABLE_CI | pass (150) |

## Gate matrix (run 2)

| Check | Status |
| --- | --- |
| ruff check | pass |
| ty check | pass |
| wagents validate | pass |
| docs compose 100% | pass |
| readme --check | pass |
| sync_agent_stack repo | pass |
| catalog index --check | pass |
| pytest full | pass (1302) |
