# Affected Surfaces

## Source Of Truth

- `config/mcp-registry.json`
- `scripts/mcphub/qsv-stdio.sh`
- `docs/src/authoring/skills/{csv-query,csv-wrangling,data-clean,data-convert,data-describe,data-join,data-profile,data-quality,data-validate,data-viz,bls-query,genai-disclaimer,infer-ontology,qsv-performance,reproducible-analysis}.mdx`
- `docs/ai-tools/mcphub.md`
- `skills/mcphub-operator/references/group-picker.md`
- `openspec/changes/mcphub-qsv-data-group/*`
- `tests/test_qsv_mcp_registry.py`

## Generated Outputs

- `mcp/mcphub/mcp_settings.json`
- `docs/public/generated-registries/skills-catalog-index.json`
- generated catalog pages under `docs/src/content/docs/skills/catalog/`
- repo harness MCP projections via `scripts/sync_agent_stack.py`

## Machine-local (gitignored)

- `mcp/servers/qsv-agent-skills/` (sparse build of upstream 21.1.0 skills tree)

## Validation Commands

- `just mcphub-generate` / `just mcphub-generate-check` / `just mcphub-validate`
- `uv run pytest tests/test_qsv_mcp_registry.py`
- `uv run wagents validate`
- `uv run wagents docs generate --no-installed`
- `uv run wagents skills sync --dry-run --strict-pin`
- `uv run wagents openspec validate`
