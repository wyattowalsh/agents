# Wave 1 Tooling Report

Generated: 2026-06-15

## Executive summary
1. **sync_agent_stack.py (~2900 LOC)** duplicates wagents/platforms/base.py logic.
2. **Codex/Copilot/Gemini platform adapters are TODO stubs**.
3. **CLI --format json** missing on install, update, readme, skills sync, grok doctor.
4. **config-transaction-registry** rollback/redaction rules not fully implemented in sync paths.
5. **MCPHub** control plane is scripts/mcphub/* + npx @samanhappy/mcphub; mcp/mcphub is metadata-only.
6. **MCP registry clients matrix** extremely complex (projection_adapters, smart_routing, tunnel).
7. **Generated artifacts** (mcp.json, opencode.json) embed absolute paths.
8. **No wagents mcphub** top-level doctor command.

## Finding count: 25 (W1-T-01..25)

## Top 5 quick wins
1. Strip /Users/ww from sync-manifest + mcp-registry
2. Add --format json to imperative CLI commands
3. Thin sync script to call platform adapters
4. Standardize secret placeholders (env not file:)
5. Add wagents mcphub doctor wrapper
