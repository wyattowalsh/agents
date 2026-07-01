# Public Release Readiness Evidence

Generated: 2026-06-29

## Gate matrix (2 consecutive runs)

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