# Proposal

## Why

`IDEAS/` (9 local, gitignored files — `SKILLS.md`, `AGENTS.md`, `MCP.md`, `CLI.md`,
`DOCS.md`, `TESTING.md`, `INFRA.md`, `WORKFLOWS.md`, `README.md`, research dated
2026-02-25) accumulated ~80 discrete, trend-backed backlog items across maintainer
observability, MCP-native catalog servers, unified discovery IA, install smoke,
eval CI gates, workflow artifacts, named skill/agent tooling, infra hardening, and
Later-tier reference implementations. Nothing in `IDEAS/` is tracked or gated, so
items risk staying permanently un-triaged or being re-implemented ad hoc without
lane ownership, collision control, or a shared validation bar.

## What Changes

- One umbrella OpenSpec change (this one) maps every `IDEAS/` item to a
  wave-gated (`W0`–`W15` + `RW0`–`RW3` review overlay), lane-partitioned task
  graph in `tasks.md`, mirroring the `fleet-hooks-performance` program pattern.
- `planning/manifests/ideas-backlog-orchestration.json` is the machine-readable
  wave/lane/task-id index; `coordinator/wave-*.json` manifests are the
  per-wave dispatch contracts.
- Ship in prioritized slices: **this session** delivers the full program
  scaffold (W0) plus the non-colliding subset of W1 quick wins (verify-\*
  recipes, runbooks, PR templates, a standalone dependency-review workflow).
  Remaining waves (W2–W15) are fully specified in `tasks.md` with `pending`
  status for follow-up execution sessions — see `## Non-Goals (this session)`.
- Reuse existing surfaces instead of rebuilding: `wagents/catalog.py`,
  `wagents/skill_index.py`, `write_harness_support_page()` in `wagents/docs.py`,
  `wagents/installed_inventory.py`, `wagents/eval_adequacy.py`. Extend-before-add
  for agents/skills (see IDEAS → task mapping in `design.md`).

## Non-Goals

- Live LLM eval execution in PR CI (structural/adequacy gates only; live evals
  stay `workflow_dispatch`/nightly).
- Replacing MCPHub with standalone server processes in default harness configs.
- Hand-editing generated `/reports/*`, catalog pages, or the skills catalog
  index.
- Promoting `IDEAS/` to tracked git (stays gitignored per `IDEAS/README.md`).

## Non-Goals (this session)

Full W0–W15 execution is a multi-week, ~140-task program by the source plan's
own estimate (`.cursor/plans/ideas_backlog_integration_364ceaf3.plan.md`,
read-only reference). This session does not implement:

- W2–W3: `wagents/docs_reports.py`, `wagents/mcp_shared/`, reports fan-out.
- W4/W10/W13: 15 new MCP servers.
- W5: catalog/architecture doc IA (coordinates with in-flight
  `compose-harness-catalog-pages`).
- W6–W8, W12–W13: install-smoke skill, 15 new skills, 15 new agent definitions.
- W9, W11: testing-depth expansion, CLI/infra Next (SARIF, attestations,
  reusable workflows, `maintenance-freshness.yml`).
- W14–W15: maintainer/skill-quality dashboards, final ship/docs regen, RW
  review-remediation overlay.

These remain fully scoped in `tasks.md` (status `pending`) with wave gates,
lane owners, and file allowlists so follow-up sessions can dispatch each wave
independently without re-deriving scope.

## Coordination With In-Flight Work

- `fleet-hooks-performance` has an **uncommitted, in-flight edit to
  `.github/workflows/ci.yml`** (adds the `hook-perf` job) at the time this
  change was scaffolded. Per the source plan's own collision rule, this
  program does **not** touch `.github/workflows/ci.yml` in W1; the exact CI
  gate additions (`wagents eval validate`, `wagents eval adequacy --strict`,
  `wagents hooks validate --harness all`) are fully specified in
  `design.md` for `SA-CI` to apply once `ci.yml` stabilizes.
- `compose-harness-catalog-pages` owns composed catalog page bodies; W5 must
  merge into its W2 agents/MCP composition rather than duplicate it.
- `public-release-prod-readiness` owns strict fail-closed validation parity;
  align W11 attestations/OIDC scope with it rather than duplicating gates.

## Validation

- `uv run wagents openspec validate`
- `uv run wagents validate`
- `uv run pytest tests/test_harness_config_docs.py tests/test_installed_inventory.py -q` (existing suites touched by evidence-gathering only; no source changes in those modules this session)
- `just verify-fast` (once defined by this change)
- `uv run ruff check`
