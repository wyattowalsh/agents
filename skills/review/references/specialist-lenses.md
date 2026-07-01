# Specialist Review Lenses

Use specialist lenses as overlays on a concrete review scope. A lens changes what evidence to gather; it does not widen scope by itself.

## Lens Map

| Lens | Trigger | Focus |
| --- | --- | --- |
| `security` | auth, payments, secrets, input parsing, file/network I/O, policy boundaries | exploitability, privilege boundaries, data exposure, injection, authz/authn, crypto misuse |
| `supply-chain` | dependencies, installers, package managers, generated code, external skills | slopsquatting, provenance, pinned versions, lockfiles, postinstall hooks, typosquatting, SBOM/SARIF evidence |
| `ci` | GitHub Actions, workflows, release scripts, credentials | token permissions, untrusted checkout, pull_request_target, artifact poisoning, cache poisoning, secret exposure |
| `sql` | SQL strings, migrations, query builders, BI/analytics | injection, transactionality, indexes, query shape, row-level security, aggregation correctness |
| `data` | ETL, analytics, datasets, ML/AI pipelines | schema drift, null semantics, idempotency, sampling, leakage, reproducibility, denominator correctness |
| `frontend` | UI code, state, forms, rendering | user flows, state bugs, hydration, responsive behavior, error states, performance footguns |
| `a11y` | user-facing UI, forms, navigation, media | semantic structure, keyboard flow, focus, labels, contrast, motion, screen-reader behavior |
| `web-quality` | sites/apps, SEO/perf/PWA/content quality | Core Web Vitals, metadata, crawlability, accessibility, resilience, content trust |
| `mcp` | MCP servers, tools, schemas, auth | tool safety, prompt-injection boundaries, secret handling, schema clarity, side-effect gates |
| `agentic` | agents, skills, hooks, automation, tool policies | instruction hierarchy, tool permission boundaries, executable surfaces, memory, unsafe autonomy |
| `skill-assets` | `SKILL.md`, `skills/<name>/**`, skill evals, package output, skill catalog/research docs | skill-creator structural patterns, dispatch coverage, reference integrity, eval proof, package portability, generated-surface drift |
| `docs` | docs, README, generated sites, API references | accuracy, freshness, source of truth, generated/manual boundaries, examples, broken links |

## Evidence Prompts

| Lens | Gather before claiming a finding |
| --- | --- |
| `security` | Trace untrusted input to sinks; grep secrets/API keys; read authz checks on mutating paths |
| `supply-chain` | Read lockfiles, install scripts, `package.json`/`pyproject.toml` deps; run `scripts/check.py` or package dry-run when reviewing skills |
| `ci` | Read workflow YAML permissions, `pull_request_target`, artifact upload steps, cache keys, secret references |
| `sql` | Read migration files and raw query strings; check parameterization, transaction boundaries, index usage |
| `data` | Inspect schema contracts, null handling, idempotency keys, train/eval splits, aggregation denominators |
| `frontend` | Reproduce user flow; read state transitions, error boundaries, loading states; prefer browser snapshots when UI-dependent |
| `a11y` | Check semantic HTML, focus order, labels, contrast, keyboard traps; use Chrome DevTools a11y tree when available |
| `web-quality` | Check metadata, CWV signals, crawlability, PWA manifest, broken links, trust/content accuracy |
| `mcp` | Read tool schemas, auth config, side-effect gates; grep network/credential usage in server code |
| `agentic` | Read SKILL.md hooks, tool allowlists, memory paths, instruction hierarchy; inspect executable surfaces |
| `skill-assets` | Run `scripts/check.py`; read dispatch table, evals, reference index; compare generated catalog vs authoring source |
| `docs` | Diff docs against code/API; grep stale commands; verify generated vs hand-authored boundaries |

## Deep References

| Lens | Read for depth |
| --- | --- |
| `supply-chain` | `references/supply-chain-security.md` |
| `skill-assets` | `references/skill-asset-review.md` |
| `docs` | `references/checklists.md` |
| simplification | `references/simplification-lens.md`, `references/simplification-taxonomy.md` |
| source/provenance | `references/source-provenance-lens.md` |
| SARIF / Conventional Comments | `references/sarif-output.md`, `references/conventional-comments.md` |
| browser-grounded UI | Browser-Grounded Review section in `SKILL.md` |

## Lens Rules

1. Pick lenses from evidence: file types, changed paths, user request, public surfaces, and risk triggers.
2. Security-sensitive code always gets `security`; external skills always get `source/provenance` plus `agentic`; dependency changes usually get `supply-chain`; first-party skill assets get `skill-assets`.
3. A lens must produce evidence or a clear no-finding statement. Do not list unused lenses for theater.
4. When a specialist finding relies on a current standard or dependency behavior, validate with primary documentation or source.
5. Keep each finding in the main finding contract; do not invent lens-specific output shapes unless requested by `--format`.
