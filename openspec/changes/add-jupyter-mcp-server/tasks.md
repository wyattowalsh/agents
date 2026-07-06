# Tasks

## Implementation

- [x] Capability matrix via manual maintainer pass (bypass documented; follow `openspec/schemas/mcp-server-change-tasks.md` on future MCP adds).
- [x] Add `scripts/mcphub/jupyter-mcp-server-stdio.sh` with pinned `jupyter-mcp-server==1.0.2`.
- [x] Add `jupyter-mcp-server` to `config/mcp-registry.json` with opt-in group memberships.
- [x] Add `tests/test_jupyter_mcp_server_registry.py`.
- [x] Update maintainer docs (mcphub.md, mcphub-operator, KB, instructions).
- [x] Regenerate `mcp/mcphub/mcp_settings.json` and repo MCP surfaces.
- [x] Run validation matrix.

## Documentation

- [x] Record audit evidence in `audit-bundle.json` and `tools-list.json`.
- [x] Refresh generated docs surfaces.

## Verification

- [x] Run registry, sync, validate, docs commands.
- [ ] Optional runtime mcphub-smoke after hub settings reload with JupyterLab running.