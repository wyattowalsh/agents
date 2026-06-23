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

## Lens Rules

1. Pick lenses from evidence: file types, changed paths, user request, public surfaces, and risk triggers.
2. Security-sensitive code always gets `security`; external skills always get `source/provenance` plus `agentic`; dependency changes usually get `supply-chain`; first-party skill assets get `skill-assets`.
3. A lens must produce evidence or a clear no-finding statement. Do not list unused lenses for theater.
4. When a specialist finding relies on a current standard or dependency behavior, validate with primary documentation or source.
5. Keep each finding in the main finding contract; do not invent lens-specific output shapes unless requested by `--format`.
