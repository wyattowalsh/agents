# Tasks

Canonical task graph for the IDEAS Backlog Integration Program. Format:
`T-<wave><seq><sub> [P] — <lane> — <done_when>`. `[P]` marks tasks that may
run in parallel with sibling `[P]` tasks in the same wave once the wave's
serial prerequisites land. Status legend: `[x]` done, `[~]` blocked
(collision/dependency, not implemented), `[ ]` pending (not started).

Source plan (read-only reference):
`.cursor/plans/ideas_backlog_integration_364ceaf3.plan.md`.

## W0 — Program scaffold (gate: `uv run wagents openspec validate`)

- [x] T-000a — L0 — `proposal.md`
- [x] T-000b — L0 — `affected-surfaces.md`
- [x] T-000c — L0 — `design.md` (lane + collision map)
- [x] T-000d — L0 — `validation-matrix.md`
- [x] T-000e — L0 — `tasks.md` (this file)
- [x] T-000f — L0 — `specs/ideas-integration/spec.md`
- [x] T-000g — L0 — `planning/manifests/ideas-backlog-orchestration.json`
- [x] T-000h — L0 — dedup matrix vs in-flight OpenSpec changes (`design.md` + orchestration manifest `dedup_matrix`)
- [x] T-001a — L0 — research refresh evidence: verified `wagents eval validate`/`eval adequacy`/`hooks validate` exist in `wagents/cli.py`; verified `ci.yml` already SHA-pins actions; verified `justfile` already exists with `validate`/`lint`/`ci-check` recipes to extend
- [x] T-001b — L0 — `uv run wagents openspec validate` green after 3 requirement-wording fixes in `specs/ideas-integration/spec.md` (SHALL/MUST must appear before long backtick-path lists for the parser to detect the keyword); confirmed passing this session
- [x] T-001c — L0 — `coordinator/wave-w0-scaffold.json`

## W1 — Quick wins (gate: G1) — 12-way parallel dispatch

- [x] T-100a — CI — `wagents eval validate --format json` runs via standalone `.github/workflows/ideas-quality-gates.yml` (interim; `ci.yml` still blocked — see below)
- [x] T-100b — CI — `wagents eval adequacy --strict --format json` runs via `ideas-quality-gates.yml`
- [x] T-100c — CI — `wagents hooks validate --harness all --format json` runs via `ideas-quality-gates.yml`
- [x] T-110a — WF — `just verify-fast` recipe (validate + lint + key pytest subset)
- [x] T-110b — WF — `just verify-docs` recipe
- [x] T-110c — WF — `just verify-all` composes verify-fast + verify-docs + ci-check
- [x] T-120a [P] — WF — `docs/runbooks/pre-commit-optimization.md`
- [x] T-121a [P] — WF — `docs/runbooks/asset-authoring-workflow.md`
- [x] T-122a [P] — WF — `docs/runbooks/research-refresh-playbook.md`
- [x] T-130a [P] — WF — `.github/PULL_REQUEST_TEMPLATE/skill.md`
- [x] T-130b [P] — WF — `.github/PULL_REQUEST_TEMPLATE/agent.md`
- [x] T-130c [P] — WF — `.github/PULL_REQUEST_TEMPLATE/mcp.md`
- [x] T-130d [P] — WF — `.github/PULL_REQUEST_TEMPLATE/docs-infra.md`
- [x] T-140a — CI — standalone `dependency-review.yml` workflow (does not touch `ci.yml`)
- [x] T-101a — INT — non-`ci.yml` gate battery green (see final report)
- [x] T-101b — L0 — `coordinator/wave-w1-quick-wins.json`

## W2 — Docs + MCP foundation (gate: G2) — complete

- [x] T-200a — DOC — register `starlight-site-graph` in `docs/astro.config.mjs`
- [x] T-200b — DOC — `wagents/docs_reports.py` module scaffold (model on `write_harness_support_page()`)
- [x] T-200c — DOC — hook `write_reports_pages()` into `wagents/docs.py` `_docs_generate_impl`
- [x] T-200d — DOC — extend `_docs_generate_stale_reasons` for reports
- [x] T-210a [P] — DOC — collector: docs dependency drift
- [x] T-210b [P] — DOC — writer: `reports/docs-dependency-drift.mdx` + JSON
- [x] T-210c — DOC — collapsed Reports sidebar group in `render_sidebar_module()`
- [x] T-210d — DOC — register artifacts in `docs-artifact-registry.json`
- [x] T-220a — MCP0 — `wagents/mcp_shared/read_only_paths.py` (prefix allowlist)
- [x] T-220b — MCP0 — `wagents/mcp_shared/catalog_readers.py` (skills/agents)
- [x] T-220c — MCP0 — unit tests `tests/mcp_shared/`
- [x] T-221a — INT — V-010
- [x] T-221b — L0 — `coordinator/wave-w2-foundation.json`

## W3 — Reports parallel (gate: G3) — 4 agents [P] — complete

- [x] T-310a-e [P] — DOC — llms-txt-coverage report
- [x] T-311a-f [P] — DOC — site-graph-insights report
- [x] T-312a-d [P] — DOC — docs-link-check persisted snapshot
- [x] T-313a-d [P] — DOC — docs-graph-snapshot + trend storage
- [x] T-314a — INT — V-020
- [x] T-314b — L0 — `coordinator/wave-w3-reports.json`

## W4 — MCP Now fleet (gate: G4) — 6 agents [P] after T-220b — complete

Each server lane (a–f): scaffold → implement tools → registry row →
mcphub regen → tests → docs page.

- [x] T-400a-f — MCP-SC — `mcp/skill-catalog/`
- [x] T-401a-f — MCP-AC — `mcp/agent-catalog/`
- [x] T-402a-f — MCP-DI — `mcp/docs-index/`
- [x] T-403a-f — MCP-RO — `mcp/repo-readonly/`
- [x] T-404a-e — MCP-URL — `mcp/source-url-health/`
- [x] T-405a-e — MCP-EV — `mcp/eval-results/`
- [x] T-406a — MCP0 — batch register all W4 servers in `config/mcp-registry.json` (serial)
- [x] T-406b — INT — V-030 + Inspector smoke script
- [x] T-406c — L0 — `coordinator/wave-w4-mcp-now.json`

## W5 — Catalog discovery (gate: G5) — complete

Coordinate with in-flight `compose-harness-catalog-pages` W2 (merge, don't duplicate).

- [x] T-520a-f — CAT — architecture pages + SkillTopology-style component (`wagents/docs_catalog.py`, `architecture/*`)
- [x] T-530a-f — CAT — `/catalog/agents/` generated route
- [x] T-531a-g — CAT — `/catalog/mcp/` auto-gen + empty-state
- [x] T-532a-h — CAT — tag/platform/tooling index routes
- [x] T-533a — INT — V-040 (`wagents docs generate` emits catalog routes)
- [x] T-533b — L0 — `coordinator/wave-w5-catalog.json`

## W6 — Install smoke (gate: G6) — complete

- [x] T-560a-c — SKL — `skills/cross-agent-install-smoke/` phase 1 dry-run assertions
- [x] T-560d-f — SKL — phase 2 local temp-home smoke script
- [x] T-561a — WF — `docs/runbooks/install-smoke.md`
- [x] T-562a — INT — V-050

## W7 — Skills Now (gate: G7) — 6 parallel [P] — complete

- [x] T-540a-f — SKL — skill-eval-scaffolder
- [x] T-541a-f — SKL — skill-token-budget-linter (+ optional CI comment)
- [x] T-542a-f — SKL — skill-compat-matrix
- [x] T-543a-d — SKL — skill-example-blocks-generator (extend `skill-creator`)
- [x] T-544a-e — SKL — skill-package-manifest-enricher
- [x] T-545a — INT — V-060

## W8 — Agents Now (gate: G8) — 4 parallel [P] — complete

- [x] T-580a-e — AGT — skill-author
- [x] T-581a-e — AGT — mcp-template-maintainer
- [x] T-582a-f — AGT — agent-eval-runner (+ evals/)
- [x] T-583a — INT — V-070

## W9 — Testing depth (gate: G9) — 6 parallel [P] — complete

- [x] T-570a-f — TST — parser edge fixtures
- [x] T-571a-g — TST — golden snapshots readme/docs/sidebar
- [x] T-572a-e — TST — CLI failure-path expansion
- [~] T-573a-f — TST — docs UI smoke in CI + artifact upload (blocked: no ci.yml edit; reusable-validate covers subset)
- [x] T-574a-d — TST — `planning/manifests/eval-ci-flagship-skills.json` + gate tests
- [x] T-575a-d — TST — `tests/test_new_mcp_scaffold.py`
- [x] T-576a-d — TST — pre-commit contract tests
- [x] T-577a — INT — V-080

## W10 — MCP Next (gate: G10) — 5 parallel [P] — complete

- [x] T-500a-g — MCP-TS — mcp-template-smoke
- [x] T-501a-f — MCP-CA — mcp-ci-artifacts
- [x] T-502a-f — MCP-RP — mcp-release-provenance
- [x] T-503a-f — MCP-WS — mcp-workflow-status
- [x] T-504a-f — MCP-DG — mcp-docs-graph
- [x] T-505a — MCP0 — registry batch
- [x] T-505b — INT — V-090

## W11 — CLI + Infra Next (gate: G11) — partial

- [~] T-750a-e — CLI — exit-code normalization audit (partial; SARIF + failure-path tests added)
- [~] T-751a-d — CLI — actionable error rendering (deferred; no broad cli.py refactor this wave)
- [x] T-752a-g — CLI — SARIF schema + `wagents validate --format sarif`
- [~] T-753a-e — CLI — help regroup by workflow (deferred)
- [x] T-754a-d — CLI — completion install docs + smoke test (`docs/runbooks/shell-completion.md`)
- [x] T-755a-f — TST — path-aware pytest selection script
- [~] T-780a-f — CI — release artifact attestations in release workflow (blocked: release-skills.yml collision policy)
- [x] T-782a-f — CI — reusable workflow extraction (`.github/workflows/reusable-validate.yml`)
- [x] T-783a-c — CI — cache strategy doc in KB wiki
- [x] T-784a-f — CI — `maintenance-freshness.yml`
- [~] T-790a — INT — V-100 (partial pending attestations + ci.yml rebase)

## W12 — Skills/Agents Next + workflows (gate: G12) — complete

- [x] T-710a-e — SKL — skill-lifecycle-manager
- [x] T-711a-e — SKL — skill-tag-taxonomist
- [x] T-712a-f — SKL — skill-bundle-curator
- [x] T-713a-e — SKL — skill-trace-debugger
- [x] T-714a-d — SKL — skill-install-dry-run-planner (extend skills sync docs)
- [x] T-720a-e — AGT — triage-lead
- [x] T-721a-e — AGT — permission-policy-auditor
- [x] T-722a-d — AGT — agent-change-recorder
- [x] T-723a-e — AGT — mcp-capability-mapper
- [x] T-724a-f — AGT — bridge-consistency-checker (extend sync check + agent)
- [x] T-700a-d — WF — worktree-parallel-agents runbook
- [x] T-701a-c — WF — ADR template convention
- [x] T-INT-12 — INT — V-110

## W13 — Later tier (gate: G13) — scaffolds shipped

- [x] T-600a-h — MCP — mcp-oauth-reference (reference scaffold)
- [x] T-601a-g — MCP — mcp-registry-publisher (stub)
- [x] T-602a-e — MCP — mcp-sandbox-profiles (stub)
- [x] T-603a-e — MCP — mcp-changelog-digest (stub)
- [~] T-760a-h — CLI — `wagents init` bootstrap workflow (runbook only; CLI command deferred)
- [~] T-761a-i — CLI — plugin architecture (deferred)
- [~] T-762a-e — CLI — CLI telemetry (deferred)
- [~] T-781a-e — INFRA — OIDC PyPI trusted-publisher scaffold (deferred)
- [~] T-785a-f — INFRA — workflow policy lint (deferred)
- [~] T-610a-f — DOCS — playground/wagents-command-examples (deferred)
- [~] T-611a-e — DOCS — docs-search-misses report (deferred)
- [~] T-770a-e — TST — trace grading experiments (deferred)
- [~] T-771a-e — TST — frontmatter fuzzing (deferred)
- [x] T-680a-d — WF — install-smoke workflow phase 3 (`workflow_dispatch` matrix)
- [x] T-730a-g — AGT — agent-transpiler (scaffold)
- [x] T-731a-f — AGT — agent-permission-simulator (scaffold)
- [x] T-732a-f — AGT — agent-registry-publisher (scaffold)
- [x] T-733a-f — AGT — prompt-optimizer (scaffold)
- [x] T-740a-f — SKL — skill-signing-verifier (scaffold)
- [x] T-741a-g — SKL — skill-registry-lock (scaffold)
- [x] T-742a-e — SKL — skill-localization-packager (scaffold)
- [~] T-INT-13 — INT — V-120 (partial — scaffolds only)

## W14 — Maintainer dashboard (gate: G14) — complete

- [x] T-800a-h — DOC — `/reports/maintainer-ops-dashboard` ingesting generated-reports JSON
- [x] T-801a-f — SKL — skill-quality-dashboard skill
- [~] T-802a-e — INFRA — provenance posture section (covered partially via release-provenance MCP + reports)
- [x] T-803a — INT — V-130

## W15 — Ship (gate: G15) — complete

- [x] T-900a — regenerate docs + readme
- [x] T-900b — update `kb/wiki/topics/ci-and-release-workflows.md`
- [~] T-900c — mark shipped items in the local research backlog source (local only, not tracked in git)
- [~] T-900d — full validation matrix V-001…V-130 (partial: openspec hooks-runtime-performance spec pre-existing failure)
- [x] T-900e — `coordinator/wave-w15-ship.json`

## Review overlay RW0–RW3 — pending

Post-W15 `/review` + security pass; findings get `RV-001…` IDs; remediation
waves mirror the `fleet-hooks-performance` RW pattern.

## SKIP list (evidence, not re-implemented)

- CLI `--format json` output modes, `doctor`, `--check`/`--dry-run` semantics — `wagents/cli.py` (verified: `eval_validate`, `eval_adequacy --strict`, `hooks_validate`, `docs generate --check`, `catalog index --check` all present and exercised locally this session).
- Docs: skills catalog generation, Starlight plugins wired — `docs/astro.config.mjs`, `wagents/catalog.py`.
- Infra: SHA-pinned actions — `.github/workflows/ci.yml` (verified: `actions/checkout@11bd719...`, `pnpm/action-setup@b906aff...`, `actions/setup-node@49933ea...` all commit-SHA pinned).
- Agent analogues: `code-reviewer`, `docs-writer`, `release-manager`, `orchestrator` cover `repo-reviewer`, `docs-curator`, `release-checker`.
