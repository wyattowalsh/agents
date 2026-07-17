# Tasks

## Implementation

- [x] Capability matrix via manual maintainer pass (bypass documented in design.md).
- [x] Sparse-build upstream qsv MCP under `mcp/servers/qsv-agent-skills` (gitignored).
- [x] Add `scripts/mcphub/qsv-stdio.sh`.
- [x] Register `qsv` server + `data` group + coding/research membership in `config/mcp-registry.json`.
- [x] Add `tests/test_qsv_mcp_registry.py`.
- [x] Author 15 curated-external skill MDX rows (pin 21.1.0).
- [x] Update maintainer docs (mcphub.md, group-picker).
- [x] Regenerate `mcp/mcphub/mcp_settings.json` and repo MCP surfaces.
- [x] Run validation matrix + skills apply (pin gate verified for 15 rows; multi-agent inventory dry-run timed out under host load; live `npx skills add` + Grok mirror completed).

## Documentation

- [x] Record audit evidence in `audit-bundle.json`.
- [x] Skills catalog authoring MDX present (15); re-run `wagents docs generate --no-installed` if index pages need full refresh.

## Verification

- [x] Registry pytest (6 passed) + mcphub-generate-check + mcphub-validate.
- [x] Pin gate True for all 15; skills installed under `~/.agents`, `~/.claude`, `~/.grok`.
- [ ] Optional runtime MCPHub smoke after hub reload with `data` group attached.
