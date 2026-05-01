# MCP Index and Replacement Finalization

## Objective

Use Glama, MCP.so, PulseMCP, awesome MCP lists, and the official MCP Registry as discovery inputs while preserving a skill-first default.

## Registry/Index Policy

- MCP indexes are not trust roots.
- Each candidate must be traced back to upstream repo, official docs, license, maintainer, and release/version state.
- Promotion requires a smoke fixture and explicit secrets/sandbox model.

## Current Repo Risk

`mcp.json` includes strong npx/uvx candidates and local absolute-path entries. Absolute local paths are portability hazards and must be classified into:

1. replace with public `npx`/`uvx` invocation;
2. wrap as local-only optional profile;
3. promote into repo-owned MCP source under `mcp/`;
4. replace with Agent Skill;
5. remove from shared configs.

## Replace-with-Skill Heuristics

Replace MCP with a skill when the server only provides static instructions, deterministic code generation, local file analysis runnable as a CLI, template rendering, docs summarization from bundled references, checklist/decision-tree behavior, or non-live planning/thinking workflows.

Keep MCP when the server provides browser automation, authenticated SaaS API state, live search/current docs, database/vector DB/cloud state, filesystem server state that must remain interactive, telemetry streams, or remote tool/runtime sessions.
