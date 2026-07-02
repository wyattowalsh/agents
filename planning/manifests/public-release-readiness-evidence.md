# Public Release Readiness Evidence

Generated: 2026-06-29; refreshed: 2026-07-02

## 2026-07-02 Refresh Gate Matrix

| Check | Result |
| --- | --- |
| `uv run ruff check` | pass |
| `uv run ty check` | pass |
| `uv run wagents validate --format json` | pass |
| `uv run wagents hooks validate --harness all` | pass |
| `uv run wagents openspec validate --format json` | current full run blocked by unrelated `fleet-hooks-promotion` no-delta change; `enforce-unique-eval-prompts` validates cleanly |
| `npx -y @fission-ai/openspec@latest validate enforce-unique-eval-prompts --type change --json --strict` | pass |
| `uv run wagents docs generate --no-installed --check` | pass |
| `uv run wagents docs build` | pass; internal links valid |
| `uv run wagents readme --check` | pass |
| `uv run python scripts/sync_agent_stack.py --check --targets repo --platforms opencode` | pass |
| `uv run python scripts/sync_agent_stack.py --apply --targets repo --platforms cursor` | pass; regenerated Cursor agent projections and repo skill symlinks |
| `uv run wagents skills sync --dry-run` | pass; inventory rows 499 |
| `uv run python skills/new-project/scripts/check.py` | pass |
| `uv run pytest tests/hooks -q` | 131 passed |
| `uv run pytest tests/hooks/test_bundle_dispatch.py tests/hooks/test_registry_perf_metadata.py tests/mcp tests/mcp_shared tests/test_installed_inventory.py tests/test_rtk_cli.py tests/test_sync_agent_stack.py tests/test_wagents_hook.py -q` | 306 passed |
| `uv run pytest tests/test_authoring_sync.py tests/test_skills_catalog_schemas.py tests/test_catalog_index_parity.py tests/test_external_skills.py tests/test_sync_desired_skills.py -q` | 53 passed |
| `uv run wagents eval validate --format json` | pass; canonical manifests reject duplicate stripped prompts |
| repo duplicate prompt scanner | pass; `duplicate_prompts 0` |
| bundled `validate_evals.py` parity check | pass; eligible bundled copies match canonical `skill-creator` source, with guarded `skills/research/scripts/asset_toolkit/validate_evals.py` intentionally excluded |
| `uv run pytest tests/test_eval_cli.py tests/test_skill_creator_audit.py tests/test_skill_bundled_toolkit.py -q` | 84 passed |
| `uv run pytest tests/test_eval_adequacy.py tests/test_eval_cli.py tests/test_eval_ci_flagship.py tests/mcp/test_eval_results.py -q` | 55 passed |

Refresh notes:

- `uv run wagents docs build` emitted Vite browser-compat externalization warnings and a Vercel local Node 26 warning; build output and internal link validation passed.
- `uv run wagents skills sync --dry-run` emitted an Antigravity fallback inventory timeout warning; the dry-run completed without applying installs.
- Grok Tier-T preflight was healthy. The bounded read-only dispatch completed and returned a result, but it emitted local MCPHub/GitHub MCP auth/tool-name errors during tool discovery; parent-side validation remains authoritative.
- `uv run wagents eval coverage --format json` exits 0 with 65/65 skills carrying eval manifests and zero skills below the five-case floor.
- `enforce-unique-eval-prompts` adds within-manifest duplicate stripped-prompt rejection, audit feedback, docs text, real-repo duplicate scanning, and bundled validator parity coverage for eligible non-guarded copies.

## 2026-06-29 Gate Matrix (Historical)

| Check | Run 1 | Run 2 |
| --- | --- | --- |
| `uv run ruff check` | pass | pass |
| `uv run ty check` | pass | pass |
| `uv run wagents validate` | pass | — |
| `uv run wagents docs compose --check-composed --min-pct 100` | pass (397/397) | — |
| `uv run wagents readme --check` | pass | — |
| `uv run python scripts/sync_agent_stack.py --check --targets repo` | pass | — |
| `uv run pytest -q` | 1268 passed | 1268 passed |

## Wave outcomes

- **W0**: Orchestration manifest + catalog shards + tmp-log cleanup.
- **W1**: Instructions/catalog SSOT alignment; OpenSpec archives (6 changes); ruff/ty/pytest green.
- **W2**: Pre-commit/CI parity (`readme-check`, `docs-generate-check`, `docs-compose-check`, `sync-stack-check`); CONTRIBUTING/START-HERE updated.
- **W3**: Authoring MDX + catalog index only; legacy `config/external-skills.md` removed.
- **W4**: 100% docs compose coverage (`planning/manifests/docs-composed-coverage.json`); skills registry validation updated.
- **W5**: `config/rtk-integration.json` tracked; remaining active OpenSpec changes (MCPHub, APM, RTK, Grok, public-release) left open for dedicated close-out.
- **W6**: Research skill `check.py` passes; journal export + verify tests present.
- **W7**: `wagents/commands/validate.py` extracted; collector tests added; validate uses `get_repo_root()`.
- **W8**: This evidence packet + consecutive gate matrix passes.

## Residual / follow-up

- Archive or close active OpenSpec changes under `openspec/changes/` when each change owner confirms completion.
- Consider consolidating duplicated `patched_repo` fixtures into `tests/conftest.py`.
