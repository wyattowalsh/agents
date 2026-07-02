# Affected Surfaces

## This session (implemented)

- `openspec/changes/integrate-ideas-backlog/**` (this change)
- `planning/manifests/ideas-backlog-orchestration.json` (new)
- `justfile` (additive: `verify-fast`, `verify-docs`, `verify-all` recipes)
- `docs/runbooks/pre-commit-optimization.md` (new)
- `docs/runbooks/asset-authoring-workflow.md` (new)
- `docs/runbooks/research-refresh-playbook.md` (new)
- `.github/PULL_REQUEST_TEMPLATE/skill.md` (new)
- `.github/PULL_REQUEST_TEMPLATE/agent.md` (new)
- `.github/PULL_REQUEST_TEMPLATE/mcp.md` (new)
- `.github/PULL_REQUEST_TEMPLATE/docs-infra.md` (new)
- `.github/workflows/dependency-review.yml` (new, standalone — does not touch `ci.yml`)
- `.github/workflows/ideas-quality-gates.yml` (new, standalone — T-100a-c interim CI gates; does not touch `ci.yml`)
- `docs/astro.config.mjs` (register `starlight-site-graph` plugin — W2)
- `docs/src/components/starlight/PageSidebarComposed.astro` (wire graph/backlinks components — W2)
- `wagents/docs_reports.py` (new, W2/W3 reports pipeline)
- `wagents/mcp_shared/__init__.py`, `wagents/mcp_shared/read_only_paths.py`, `wagents/mcp_shared/catalog_readers.py` (new, W2)
- `wagents/docs.py` (`_docs_generate_impl`, `_docs_generate_stale_reasons`, `render_sidebar_module()` — W2/W3 report + catalog hooks)
- `config/mcp-registry.json`, `mcp/mcphub/mcp_settings.json` (W4 batch register 6 Now servers)
- `config/docs-artifact-registry.json` (W2/W3 report registrations)
- `mcp/skill-catalog/`, `mcp/agent-catalog/`, `mcp/docs-index/`, `mcp/repo-readonly/`, `mcp/source-url-health/`, `mcp/eval-results/` (new, W4)
- `tests/mcp_shared/**`, `tests/mcp/test_*` (new, W4)
- `docs/src/content/docs/reports/*.mdx` + `docs/public/generated-reports/*.json` (new, W2/W3)
- `docs/src/content/docs/architecture/*.mdx` (new, W5)
- `docs/src/content/docs/catalog/agents/`, `docs/src/content/docs/catalog/mcp/`, `docs/src/content/docs/catalog/tags/`, `docs/src/content/docs/catalog/platforms/`, `docs/src/content/docs/catalog/tooling/` (new, W5)

## Deferred — full scope for future wave sessions (see `tasks.md`, `design.md`)

### Source (wagents)

- `wagents/docs_reports.py` (new, W2)
- `wagents/mcp_shared/read_only_paths.py`, `wagents/mcp_shared/catalog_readers.py` (new, W2)
- `wagents/docs.py` (`_docs_generate_impl`, `_docs_generate_stale_reasons`, `render_sidebar_module()` — W2/W3)
- `wagents/cli.py` (SARIF, help regroup, exit-code audit, completion — W11; `wagents init` — W13)
- `config/mcp-registry.json`, `mcp/mcphub/mcp_settings.json` (W4/W10/W13 batch registers)
- `config/docs-artifact-registry.json` (W2/W3 report registrations)

### MCP servers (new directories)

- W4 (Now): `mcp/skill-catalog/`, `mcp/agent-catalog/`, `mcp/docs-index/`, `mcp/repo-readonly/`, `mcp/source-url-health/`, `mcp/eval-results/`
- W10 (Next): `mcp/template-smoke/`, `mcp/ci-artifacts/`, `mcp/release-provenance/`, `mcp/workflow-status/`, `mcp/docs-graph/`
- W13 (Later): `mcp/oauth-reference/`, `mcp/registry-publisher/`, `mcp/sandbox-profiles/`, `mcp/changelog-digest/`

### Skills / Agents (new)

- W7: `skills/skill-eval-scaffolder/`, `skills/skill-token-budget-linter/`, `skills/skill-compat-matrix/`, `skills/skill-package-manifest-enricher/` (+ extend `skills/skill-creator/` for example-blocks generation)
- W6/W7: `skills/cross-agent-install-smoke/`
- W8: `agents/skill-author.md`, `agents/mcp-template-maintainer.md`, `agents/agent-eval-runner.md`
- W12: `skills/skill-lifecycle-manager/`, `skills/skill-tag-taxonomist/`, `skills/skill-bundle-curator/`, `skills/skill-trace-debugger/` (+ extend skills-sync docs); `agents/triage-lead.md`, `agents/permission-policy-auditor.md`, `agents/agent-change-recorder.md`, `agents/mcp-capability-mapper.md`, `agents/bridge-consistency-checker.md`
- W13 (Later): `skills/skill-signing-verifier/`, `skills/skill-registry-lock/`, `skills/skill-localization-packager/`; `agents/agent-transpiler.md`, `agents/agent-permission-simulator.md`, `agents/agent-registry-publisher.md`, `agents/prompt-optimizer.md`
- W14: `skills/skill-quality-dashboard/`

### Docs / catalog

- `docs/astro.config.mjs` (register `starlight-site-graph` — W2)
- `docs/src/content/docs/reports/*.mdx` + `docs/public/generated-reports/*.json` (W2/W3/W14)
- `docs/src/content/docs/catalog/agents/`, `docs/src/content/docs/catalog/mcp/`, tag/platform/tooling index routes (W5)
- `docs/src/generated-sidebar.mjs` (regenerated only, via `render_sidebar_module()` — W2+)

### CI / Infra (deferred, blocked on ci.yml stabilization)

- `.github/workflows/ci.yml` — SA-CI sole owner; blocked in this session by
  the in-flight `fleet-hooks-performance` `hook-perf` job addition
  (uncommitted at scaffold time). Exact diff spec lives in `design.md`.
- `.github/workflows/maintenance-freshness.yml` (new, W11)
- `.github/actions/*` reusable workflow extraction (W11)
- Release artifact attestations in `release-skills.yml` (W11)

### Tests (deferred)

- `tests/mcp_shared/**`, `tests/mcp/test_*` per W4/W10 server
- `tests/test_new_mcp_scaffold.py` (W9)
- Golden snapshot tests for readme/docs/sidebar (W9)
- `tests/hooks/` pre-commit contract tests (W9)

## Notes

- The local research backlog source is never modified (gitignored, read-only
  per its own conventions); ship tracking is via this OpenSpec change plus
  optional local shipped markers in that source, not by tracking it in git.
