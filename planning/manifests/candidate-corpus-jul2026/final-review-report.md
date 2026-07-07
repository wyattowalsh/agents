# Candidate Corpus July 2026 Final Review Report

- Total raw candidates processed: 293
- Total unique normalized targets: 289
- Added count: 289
- Catalog authoring rows added: 289
- Live install additions: 0
- Adapted count: 0
- Reference-only count: 269
- Skipped count: 9
- Duplicates deduped: 4
- Auth requirements: 49 candidates require auth or credential-boundary review.
- Research task graph: 293 raw lanes, 289 synthesis lanes, 7879 leaf checks.
- GitHub metadata audit: ok=292, unavailable=1; license labels=9.
- Existing integration coverage: covered-by-existing-installable-catalog=14, covered-by-existing-reference=1, needs-promotion-review=274
- Covered by existing installable catalog rows: 14.
- Promotion waves: W00=14, W01=15, W02=28, W03=27, W04=22, W05=26, W06=21, W07=30, W08=101, W99=5
- Full integration phase: `research-graph-ready`; live install remains `no-new-live-installs-eligible`.
- Promotion packet outputs: 293 raw packets, 289 unique packets, 289 gate rows, 0 install commands.
- Source-list evidence: 289 list-only probes recorded (236 found, 53 blocked/error/no-skills), 0 installs
- Generator-owned docs-steward packets emitted: manifest surface map, auth matrix, decision log, catalog authoring summary, existing integration coverage, promotion wave plan, research task graph, research packet schema, raw/unique research packets, promotion gate matrix, live install command preview, GitHub metadata audit, subagent wave queue, promotion readiness queue, integration progress, changelog entry, validation report, and final review report.
- Covered docs-steward surfaces: `README`=289, `catalog-authoring`=289, `catalog-generated`=289, `skill-research`=289, `mcp-tools`=27, `auth-matrix`=293, `install-docs`=289, `openspec`=293, `runbooks`=49, `decision-log`=293, `changelog`=293, `reports`=293, `generated-drift`=293.
- Zero-count docs-steward surfaces omitted from covered lists: `agents-instructions`.
- Validation command checklist: see `validation-report.md`; execution results must be recorded by the runner.
- Review findings addressed in generator-owned outputs: coverage/schema gates are automated, catalog-only rows publish no install/use commands, and generated reports no longer imply unobserved validation passes.
- Unresolved risks: source-list, license, security, attribution, auth, and docs-steward trust gates remain required before live install, adaptation, or repo promotion for blocked targets.
- Final commit hash: no commit made by this script.

## Suggested PR Title

chore: add candidate corpus July 2026 intake manifests

## Suggested PR Body

- Adds deterministic candidate corpus normalization, sharding, coverage, generated catalog authoring rows, GitHub metadata audit, and manifest generation.
- Records public Git/GitHub metadata, source-support, security, license, compliance/auth, docs impact, dedupe, and decision outputs.
- Keeps newly reviewed third-party sources discovery-only pending source-list evidence, license review, security review, and docs-steward gates; credits existing installable catalog coverage.
