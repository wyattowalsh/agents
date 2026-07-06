# Tasks

## Implementation

- [x] Capability matrix via manual maintainer pass (bypass documented; follow `openspec/schemas/mcp-server-change-tasks.md` on future MCP adds).
- [x] Add `scripts/mcphub/scrapling-stdio.sh` with pinned `scrapling[ai]==0.4.10`.
- [x] Add `scrapling` to `config/mcp-registry.json` with opt-in group memberships.
- [x] Add `tests/test_scrapling_registry.py`.
- [x] Update maintainer docs (mcphub.md, mcphub-operator, KB).
- [x] Regenerate `mcp/mcphub/mcp_settings.json` and repo MCP surfaces.
- [x] Run validation matrix.

## Documentation

- [x] Record audit evidence in `audit-bundle.json` and `tools-list.json`.
- [x] Refresh generated docs surfaces.

## Verification

- [x] Run registry, sync, validate, docs commands.
- [ ] Optional runtime mcphub-smoke after hub settings reload.