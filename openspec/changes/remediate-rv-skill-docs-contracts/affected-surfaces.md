# Affected Surfaces

## Source Of Truth

- `scripts/run_candidate_cli_canaries.py`
- `scripts/run_candidate_plugin_canaries.py`
- Any existing shared subprocess-lifecycle helper selected by implementation;
  no parallel sandbox abstraction is introduced.
- `skills/skill-package-manifest-enricher/SKILL.md`
- `skills/skill-package-manifest-enricher/scripts/enrich_manifest.py`
- `skills/skill-package-manifest-enricher/scripts/check.py`
- Portable catalog/sync metadata inputs consumed by the enricher.
- `wagents/docs_reports.py`
- `wagents/docs.py`
- `wagents/docs_catalog.py`
- `wagents/site_model.py`
- `wagents/cli.py` README generation.
- The retirement source and bounded semantic-scan policy owned by
  `remove-gemini-antigravity-copilot`.

## Generated Outputs

- `skills/*/manifest.enriched.json` only when an operator explicitly uses
  `--apply`; previews remain non-mutating.
- `docs/src/generated-site-data.mjs`
- `docs/public/generated-reports/docs-graph-snapshot.json`
- `docs/public/generated-reports/docs-link-check.json`
- `docs/public/generated-reports/site-graph-insights.json`
- `docs/public/generated-reports/maintainer-ops-dashboard.json`
- Generated homepage, support matrix, grouped catalog, and README surfaces.
- `.apm/` projections and `apm.lock.yaml`, generated and checked last.

## Downstream Agent Artifacts

- Managed harness taxonomy: exactly `claude-code`, `codex`, `crush`, `cursor`,
  `grok`, and `opencode`.
- Skills CLI-native taxonomy: exactly the managed set without `grok`.
- Cherry Studio, LM Studio, ChatGPT, Claude Desktop, and other applicable
  clients remain separately labeled MCP-only or hybrid surfaces.
- Generated `.claude`, `.cursor`, `.opencode`, `.agent`, `.crush`, and `.codex`
  OpenSpec artifacts remain local-only and are not edited by this change.

## Tests

- `tests/test_candidate_cli_canaries.py`
- `tests/test_candidate_plugin_canaries.py`
- `tests/test_candidate_runtime_activation.py` for the receipt-regeneration
  lifecycle precondition.
- Portable `skill-package-manifest-enricher` script/check fixtures.
- `tests/test_docs_reports.py`
- `tests/test_docs.py`
- `tests/test_docs_catalog.py`
- `tests/test_site_model.py`
- `tests/test_readme.py`
- `tests/test_sync_agent_stack.py` for RV-007 AITK/Crush proof only.
- `tests/test_reddit_mcp_buddy_registry.py` for RV-011 proof only.
- `tests/test_retire_harness_targets.py` for RV-013 proof only.
- `tests/test_apm_materialize.py` for APM lock regression support.

## Validation Commands

- Focused subprocess-lifecycle, manifest-enricher, docs-report, site-model,
  catalog, and README tests.
- `uv run pytest -q tests/test_sync_agent_stack.py -k 'crush or aitk'`
- `uv run pytest -q tests/test_reddit_mcp_buddy_registry.py`
- `uv run pytest -q tests/test_retire_harness_targets.py` plus the bounded
  source/generated retirement scan.
- `uv run wagents validate`
- `uv run wagents readme --check`
- `uv run wagents docs generate --no-installed` and docs checks/build scheduled
  by the owning generator lane.
- `uv run wagents apm refresh-lock --check` as the final post-generation gate.
- Targeted strict and full OpenSpec validation.
