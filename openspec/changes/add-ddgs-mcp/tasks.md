# Tasks

## Implementation

- [x] Wave 0: PyPI provenance audit (`ddgs-mcp-server` 0.5.1, MIT, stdio via uvx).
- [x] Add `ddgs` server and group membership in `config/mcp-registry.json`.
- [x] Regenerate `mcp/mcphub/mcp_settings.json`.
- [x] Update harness parity guards and tests.
- [x] Refresh docs and research references.
- [x] Run `sync_agent_stack.py --targets repo --apply`.

## Verification

- [x] `just mcphub-generate-check`, `just mcphub-validate`
- [x] `uv run wagents validate`, `uv run wagents openspec validate`
- [x] Pytest MCPHub subset
- [x] `uv run wagents docs generate --no-installed` and `uv run wagents docs build`