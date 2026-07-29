# Tasks: remediate-rv-skill-docs-contracts

## Foundation

- [ ] T-001 Re-prove the live branch, dirty owned-file preimages, applicable
  instructions, and current source/test behavior before implementation.
- [ ] T-002 Keep one writer per shared source/generated surface and preserve
  unrelated dirty changes.

## RV-003 Ordinary Process Lifecycle

- [ ] T-100 Identify every ordinary candidate CLI/plugin timeout path; exclude
  quarantine/sandbox scope from this lifecycle contract.
- [ ] T-110 Add or reuse one POSIX process-group helper implementing TERM →
  bounded wait → KILL when needed → reap/drain.
- [ ] T-120 [P] Add CLI timeout tests with a descendant process, retained
  stdout/stderr, and proof that the parent agent process group is untouched.
- [ ] T-130 [P] Add plugin timeout tests with the same descendant and pipe-drain
  assertions.
- [ ] T-140 Route the ordinary CLI/plugin timeout paths through the proved
  helper without broad signaling or sandbox claims.
- [ ] T-145 Add
  `test_behavioral_receipt_regeneration_requires_lifecycle_gate` to
  `tests/test_candidate_runtime_activation.py`.
- [ ] T-150 Run V-001 and V-002; keep candidate behavioral receipt regeneration
  blocked until both are green.

## RV-009 Portable Manifest Enricher

- [ ] T-200 [P] Replace line-oriented frontmatter parsing with a real YAML safe
  loader and declare the portable dependency/compatibility contract.
- [ ] T-210 [P] Add folded scalar, chomping, quoted, list, mapping, malformed
  YAML, preview, and explicit-apply fixtures.
- [ ] T-220 Derive harness targets from supplied portable catalog/sync metadata,
  bind the selected source and digest, and emit explicit unavailable state when
  neither source exists.
- [ ] T-230 Reject any repo `wagents` import and any hardcoded target list in the
  installed skill package.
- [ ] T-240 Run V-003 and V-004.

## RV-010 Pure Docs Graph Validation

- [ ] T-300 [P] Separate pure docs graph/report computation and validation from
  filesystem mutation and wall-clock access.
- [ ] T-310 Add optional `--snapshot-date YYYY-MM-DD`; when omitted in mutation
  mode, capture the current UTC date once at the CLI/generator boundary and
  pass it explicitly; reject invalid supplied dates before writes.
- [ ] T-320 [P] Add no-write/no-clock check-mode tests and byte-stability tests
  for equal inputs plus the same snapshot date.
- [ ] T-330 Thread one explicit snapshot date through the owning docs generator
  and every related report mutation.
- [ ] T-340 Run V-005 and V-006.

## RV-012 Taxonomy And Public Counts

- [ ] T-400 [P] Centralize the exact managed-six and Skills CLI-native-five
  categories while preserving separately typed MCP-only/hybrid surfaces.
- [ ] T-410 Make homepage rows/counts, install targets, support tables, and
  README grouping derive from the structured categories.
- [ ] T-420 [P] Add identity and count regressions for managed, Skills
  CLI-native, MCP-only, and hybrid rows.
- [ ] T-430 Run V-007.

## Proof-Only Review Gates

- [ ] T-500 Run RV-007 V-008 and verify AITK uses
  `render_flat_mcp(..., harness="crush")` with flat `type: stdio` entries.
- [ ] T-510 [P] Run RV-011 V-009 and verify exactly
  `browse_subreddit`, `search_reddit`, `get_post_details`, `user_analysis`, and
  `reddit_explain`, with no wildcard or `tools_allow_all`.
- [ ] T-520 [P] Run RV-013 V-010 and retain the bounded semantic-scan evidence
  and explicit keep-set classification.
- [ ] T-530 Re-run RV-010 V-005/V-006 as review proof after all docs graph
  implementation changes settle.

## Generated Surfaces And Closure

- [ ] T-600 Run source validation and all focused implementation tests.
- [ ] T-610 Serialize docs generation with `--snapshot-date`, README
  generation, MCPHub/sync reconciliation, and APM materialization; do not
  overlap an existing generator.
- [ ] T-620 Invoke `docs-steward` after source regeneration/build validation and
  record its finding or availability blocker.
- [ ] T-630 Run docs/readme check-mode validation against the settled generated
  snapshot.
- [ ] T-640 Run `uv run wagents apm refresh-lock --check` as final RV-008 proof
  only after every generator and materializer has finished.
- [ ] T-650 Run targeted strict and full OpenSpec validation; do not mark
  implementation complete while any task or external blocker remains.
