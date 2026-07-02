# Skills & Plugins Review Swarm — Evidence

Plan: `skills-plugins-review-swarm`
Wave: **W5** (judge closeout)
Generated: 2026-07-01

## Gate matrix (G0–G5)

| Gate | Wave | Status | Notes |
| --- | --- | --- | --- |
| G0 | W0 | passed | Scaffold + baseline captured |
| G1 | W1 | passed | 7 repo skill shards resolved |
| G2 | W2 | passed | 3 plugin/hook lanes resolved |
| G3 | W3 | passed | 19 catalog shards resolved |
| G4 | W4 | passed | Security judge shard resolved |
| G5 | W5 | passed | Rollup + remediation emitted; 70 tracked findings closed by remediation refresh |

## Parallel groups (all resolved)

| Group | Dispatched | Resolved | Scope |
| --- | ---: | ---: | --- |
| PG-W0 | 6 | 6 | T-SP-001…006 baseline tasks |
| PG-W1 | 7 | 7 | `w1-findings-skill-shard-01`…`07` |
| PG-W2 | 3 | 3 | Plugin manifests, exposure dedupe, hook projection |
| PG-W3 | 19 | 19 | 5 custom + 13 external + design-ux catalog shards |
| PG-W4 | 1 | 1 | `w4-findings.json` security judge |
| PG-W5 | 3 | 3 | Findings merge, remediation queue, judge closeout |

## W0 baseline (G0)

| Task | Result |
| --- | --- |
| T-SP-001 shard manifest | `skills-plugins-review-shards.json`; 23 total shards |
| T-SP-002 repo skills | 51 repo-owned skills → 7 W1 shards (`8+8+7+7+7+7+7`) |
| T-SP-003 external catalog | 313 composed external entries → 13 W3 external shards |
| T-SP-004 plugin lanes | 3 W2 lanes: manifests, exposure-dedupe, hook-projection |
| T-SP-005 `wagents validate` | pass |
| T-SP-006 `wagents hooks validate --harness all` | pass |

## Repo skill audit baseline (W1 input)

| Metric | Value |
| --- | --- |
| Skills audited | 50 (51 repo-owned; `desktop-computer-use` out of scope) |
| Grade A | 30 |
| Grade B | 20 |
| Out of scope | `desktop-computer-use` |
| `check.py` failures (blocking) | `new-project` (exit 124 → P0 RV-SP-002) |

## Remediation refresh (2026-07-02)

| Finding set | Status | Evidence |
| --- | --- | --- |
| `RV-SP-001..003` | closed | Repo-skill timeout/eval coverage fixes validated. |
| `RV-SP-005..054` | closed | Custom catalog rows carry repo-owned trust/status metadata. |
| `RV-SP-055..065` | closed/accepted | External rows have explicit install/disposition metadata; `apm-cli` is an accepted external-tool exception. |
| `RV-SP-066..070` | closed | Security/eval-program findings are resolved for their original target skills. |
| `RV-SP-004` | accepted | W2 plugin-surface finding was a clean-surface record. |

Focused validation: `wagents validate`, `skills/new-project/scripts/check.py`,
catalog pytest shard, and eval pytest shard all passed in the remediation run.

## Severity summary (judge rollup)

| Severity | Count |
| --- | ---: |
| P0 | 1 |
| P1 | 53 |
| P2 | 13 |
| P3 | 3 |
| **Total** | **70** |

### By originating wave

| Wave | Findings | Primary themes |
| --- | ---: | --- |
| w1 | 3 | P0 `new-project` check timeout; thin eval coverage |
| w2 | 1 | P3 plugin surfaces clean |
| w3 | 61 | P1 catalog authoring frontmatter (`trust_tier`, `status`) |
| w4 | 5 | P1 security-judge thin evals; P2 eval depth gaps |

## Wave outcomes

- **W0**: Shard manifest, harness baselines, inventory fan-out.
- **W1**: Per-skill `check.py` / audit / package dry-run capture across 7 shards; meta records 50-skill audit scope.
- **W2**: Bundle + manifest + hook projection lanes; no blocking plugin regressions.
- **W3**: Custom + external catalog authoring review (313 external entries); design-ux cluster clean.
- **W4**: Cross-skill security judge and eval-program findings.
- **W5**: Merged `skills-plugins-review-findings.json`, remediation queue, orchestration/evidence closeout (`G5: passed_with_findings`).

## Artifact index (34 paths)

| Wave | Path | Role |
| --- | --- | --- |
| W0 | `planning/manifests/skills-plugins-review-shards.json` | Shard dispatch manifest (W1+W2+W3 lanes) |
| W0 | `planning/manifests/skills-plugins-review-orchestration.json` | Orchestration state (W0→W5 closeout) |
| W5 | `planning/manifests/skills-plugins-review-findings.json` | Merged findings rollup (70 items) |
| W5 | `planning/manifests/skills-plugins-review-remediation-queue.md` | Severity-sorted remediation queue |
| W5 | `planning/manifests/skills-plugins-review-evidence.md` | Evidence index (this file) |
| W1 | `planning/manifests/w1-findings-skill-shard-01.json` | Repo skill shard 01 audit entries |
| W1 | `planning/manifests/w1-findings-skill-shard-02.json` | Repo skill shard 02 audit entries |
| W1 | `planning/manifests/w1-findings-skill-shard-03.json` | Repo skill shard 03 audit entries |
| W1 | `planning/manifests/w1-findings-skill-shard-04.json` | Repo skill shard 04 audit entries |
| W1 | `planning/manifests/w1-findings-skill-shard-05.json` | Repo skill shard 05 audit entries |
| W1 | `planning/manifests/w1-findings-skill-shard-06.json` | Repo skill shard 06 audit entries |
| W1 | `planning/manifests/w1-findings-skill-shard-07.json` | Repo skill shard 07 audit entries |
| W1 | `planning/manifests/w1-findings-skill-shard-meta.json` | W1 rollup meta (50 audited skills) |
| W2 | `planning/manifests/w2-findings.json` | Plugin / bundle / hook projection lane findings |
| W3 | `planning/manifests/w3-findings-catalog-custom-01.json` | Catalog custom shard 01 |
| W3 | `planning/manifests/w3-findings-catalog-custom-02.json` | Catalog custom shard 02 |
| W3 | `planning/manifests/w3-findings-catalog-custom-03.json` | Catalog custom shard 03 |
| W3 | `planning/manifests/w3-findings-catalog-custom-04.json` | Catalog custom shard 04 |
| W3 | `planning/manifests/w3-findings-catalog-custom-05.json` | Catalog custom shard 05 |
| W3 | `planning/manifests/w3-findings-catalog-design-ux.json` | Catalog design-ux cluster (clean) |
| W3 | `planning/manifests/w3-findings-catalog-ext-01.json` | External catalog shard 01 |
| W3 | `planning/manifests/w3-findings-catalog-ext-02.json` | External catalog shard 02 |
| W3 | `planning/manifests/w3-findings-catalog-ext-03.json` | External catalog shard 03 |
| W3 | `planning/manifests/w3-findings-catalog-ext-04.json` | External catalog shard 04 |
| W3 | `planning/manifests/w3-findings-catalog-ext-05.json` | External catalog shard 05 |
| W3 | `planning/manifests/w3-findings-catalog-ext-06.json` | External catalog shard 06 |
| W3 | `planning/manifests/w3-findings-catalog-ext-07.json` | External catalog shard 07 |
| W3 | `planning/manifests/w3-findings-catalog-ext-08.json` | External catalog shard 08 |
| W3 | `planning/manifests/w3-findings-catalog-ext-09.json` | External catalog shard 09 |
| W3 | `planning/manifests/w3-findings-catalog-ext-10.json` | External catalog shard 10 |
| W3 | `planning/manifests/w3-findings-catalog-ext-11.json` | External catalog shard 11 |
| W3 | `planning/manifests/w3-findings-catalog-ext-12.json` | External catalog shard 12 |
| W3 | `planning/manifests/w3-findings-catalog-ext-13.json` | External catalog shard 13 |
| W4 | `planning/manifests/w4-findings.json` | Security judge + eval-program cross-cut |

## Shard coverage reference

| Lane | Shards | Coverage |
| --- | ---: | --- |
| W1-skills (repo) | 7 | 51 skills (50 audited) |
| W2-plugins | 3 | manifests + exposure + hooks |
| W3-catalog-custom | 5 | repo-owned catalog MDX rows |
| W3-catalog-external | 13 | 313 external catalog entries |
| W3-design-ux | 1 | design cluster spot-check |
| **Dispatch total** | **23** | per `skills-plugins-review-shards.json` |
