# Candidate Corpus July 2026 Final Review Report

- Total raw candidates processed: 293
- Total unique normalized targets: 289
- Added count: 1213
- Catalog authoring rows added: 1213
- Installable curated rows: 1038
- Live install additions: 1038
- Adapted count: 1038
- Reference-only count: 175
- Skipped count: 175 remaining gated rows plus selector collisions recorded separately
- Duplicates deduped: 4 raw duplicate URLs plus 0 selector-name collisions
- Auth requirements: 49 candidates require auth or credential-boundary review; promoted auth-bearing skills use placeholder-only credential guidance.
- Research task graph: 293 raw lanes, 289 synthesis lanes, 7879 leaf checks.
- Existing integration coverage: covered-by-existing-installable-catalog=14, covered-by-existing-reference=1, needs-promotion-review=274 before the live overlay.
- Full integration phase: `promotion-overlay-installed`; live install status: `live-installs-recorded`.
- Docs-steward surfaces updated: authoring catalog, generated external catalog pages, catalog indexes, install scripts, README, generated site data/sidebar, reports, and candidate-corpus manifests.
- Review findings addressed: source-list gates stayed separate from installs, duplicate names were repaired to canonical owners, repo-owned `research` and `design` were restored after external collisions, Grok was mirrored from Claude-compatible skill roots, and no third-party source trees were vendored into `skills/`.
- Unresolved risks: 175 reference-only rows are terminal skip/gate decisions for unclear license, inaccessible source, duplicate/canonical-source decisions, no safe install surface, or credential/destructive/abuse-risk gates. Credentialed MCP/plugin services remain disabled from default registry exposure.
- Final commit hash: recorded by the runner after this report is committed.

## Suggested PR Title

feat: install and catalog July 2026 candidate skills corpus

## Suggested PR Body

- Promotes reviewed July 2026 candidate corpus selectors into curated external catalog rows with license, provenance, install, and safety notes.
- Live-installs promoted Skills CLI assets across local harness roots and mirrors Claude-compatible skills into Grok discovery.
- Regenerates docs-steward catalog, install, generated registry, README, and report surfaces.
- Keeps unclear-license, inaccessible, duplicate, credentialed-service, and abuse-risk sources gated or disabled from default MCP/plugin exposure.
