# Tasks

## Implementation

- [x] Replace server in `config/mcp-registry.json` and update all group slugs
- [x] Add `scripts/mcphub/package-version-check-mcp.sh` launcher (upstream PyPI forward-ref patch)
- [x] Add `package-version-check-mcp` to `research` group
- [x] Regenerate `mcp/mcphub/mcp_settings.json`
- [x] Update sync constants, tests, collectors
- [x] Apply repo harness sync
- [x] Update skills and hand-maintained docs
- [x] Run authoring sync, docs generate/build, validation

## Verification

- [x] Targeted pytest (28 passed)
- [x] `just mcphub-smoke`
- [x] Zero-residual grep for legacy slug (only `REMOVED_MCP_SERVERS`)
- [x] `uv run wagents validate` (after RTK shared-include fix in separate commit)