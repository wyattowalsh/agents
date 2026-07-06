# Tasks

## Implementation

- [x] Add `scripts/mcphub/open-websearch-stdio.sh` with fleet-safe stdio defaults.
- [x] Add `open-websearch` to `config/mcp-registry.json` with opt-in group memberships.
- [x] Add `tests/test_open_websearch_registry.py`.
- [x] Author `docs/src/authoring/skills/open-websearch.mdx`.
- [x] Regenerate `mcp/mcphub/mcp_settings.json` and repo MCP surfaces.
- [x] Update maintainer docs (mcphub.md, mcphub-operator, review validation, KB).

## Documentation

- [x] Record audit evidence in `audit-bundle.json` and catalog MDX body.
- [x] Refresh generated docs surfaces.

## Verification

- [x] Run registry, sync, validate, docs, and catalog dry-run commands.
- [x] Runtime tools/list via direct stdio probe (`open-websearch@2.1.11`; bounded tool names verified).
- [ ] MCPHub endpoint smoke (`bash scripts/mcphub/smoke.sh`) — hub-wide init still degraded (context7 SSRF, /mcp 404 during partial startup).
- [x] Three atomic git commits C1→C2→C3 landed (`9f3c3246` package-version-check-mcp → `73eeb44b` ddgs → `0d934208` open-websearch; follow-ups `7157b329`, `d726a602`).