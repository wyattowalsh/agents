# Audit Checklist

## Purpose
Use this checklist for read-only diagnosis, post-change verification, and pre-`migration` reviews. Audit findings should lead to the next smallest safe batch, not a monolithic rewrite.

## Severity rubric
| Severity | Meaning | Typical response |
|----------|---------|------------------|
| Critical | `provenance` is broken, `canonical material` is at risk, or a path change could break consumers | Stop and plan a small corrective batch |
| Warning | Coverage, index freshness, `schema`, `config`, or `activity log` discipline is incomplete | Queue an additive repair batch |
| Suggestion | The KB works, but clarity, consistency, or reviewability can improve | Log it and bundle with the next safe batch |

## Audit report shape
| Severity | Path | Finding | Evidence | Safe next batch |
|----------|------|---------|----------|-----------------|
| Warning | `indexes/coverage.md` | Missing row for new `wiki` page | Page exists, index row absent | Add one coverage row and log the update |

## Structure and layer integrity
- [ ] The KB has clear `raw`, `wiki`, `schema`, `config`, `indexes`, and `activity log` surfaces.
- [ ] `raw` content is separate from `wiki` synthesis.
- [ ] `indexes/source-map.md` and `indexes/coverage.md` exist or there is an explicit approved alternative.
- [ ] `activity/log.md` exists and is append-only.
- [ ] `derived output` lives outside the canonical KB layers.
- [ ] If the repo is mixed or partial, it is explicitly treated as an `imperfect repo`.

### Common findings
- Critical: user-authored pages are being replaced by generated summaries.
- Warning: `raw` evidence is mixed into `wiki/` with no separation.
- Suggestion: add clearer links from `wiki/index.md` to current indexes.

## Provenance and canonical material
- [ ] Every maintained `wiki` page has a visible `Provenance` section or equivalent trace.
- [ ] Key claims link to `raw` or declared `canonical material`.
- [ ] Source summary pages identify the matching `raw` paths.
- [ ] `canonical material` is listed before recommending structural changes.
- [ ] No unsupported claims were introduced during enrichment.

### Provenance spot-check example
| Page | Claim | Backing source | Result |
|------|-------|----------------|--------|
| `wiki/topics/vendor-landscape.md` | "Vendor A supports offline mode" | `raw/extracts/vendor-demo.md#L44-L48` | Pass |

## Coverage and index freshness
- [ ] Every active source in `raw/` has a row in `indexes/source-map.md`.
- [ ] Every maintained `wiki` page has a row in `indexes/coverage.md`.
- [ ] Orphan `wiki` pages are called out explicitly.
- [ ] Gaps and unknowns are tracked instead of silently skipped.
- [ ] Index rows use current paths and stable naming.

### Coverage examples
- Warning: source exists in `raw/sources/` but has no planned `wiki` target.
- Suggestion: mark a page as `partial` instead of leaving coverage blank.

## Schema and config drift
- [ ] Observed page shapes still match `schema` guidance.
- [ ] `config` paths, slugs, and output targets still exist.
- [ ] Any `schema` or `config` change was deliberate and reviewable.
- [ ] No content change quietly introduced a new untracked field or status.

## Activity log continuity
- [ ] Every mutating batch has a corresponding `activity log` entry.
- [ ] Entries name changed files or file groups.
- [ ] Entries call out `canonical material`, `provenance`, and `derived output` decisions when relevant.
- [ ] Follow-up work is recorded instead of left implicit.

### Activity log example finding
| Severity | Finding | Safe next batch |
|----------|---------|-----------------|
| Warning | `wiki/` page changed with no matching log entry | Append a factual entry covering the completed batch |

## Derived output hygiene
- [ ] Every `derived output` lists its KB inputs or links to a logged recipe.
- [ ] The KB can stand on its own without the export.
- [ ] Old exports are preserved until the replacement is verified.
- [ ] Consumers can tell which file is canonical and which file is derived.

## Pre-migration checks
Run these before approving any `migration`:
- [ ] The `canonical material` inventory is complete.
- [ ] Path consumers are known.
- [ ] Rollback is documented.
- [ ] Additive repair was considered first.
- [ ] `provenance` will remain verifiable during and after the move.

## Audit exit checklist
- [ ] Findings are classified as critical, warning, or suggestion.
- [ ] Each finding cites a concrete path.
- [ ] The next recommendation is additive-first and reviewable.
- [ ] Destructive or high-impact work is deferred to an approved `migration` plan.
