# Proposal

## Problem

Agents need local, high-performance tabular data wrangling (CSV/Excel/JSONL/Parquet) without uploading data. Upstream [dathere/qsv](https://github.com/dathere/qsv) ships an MCP server and agent skills, but this repo has neither a registry entry, a capability group for tabular data, nor curated skill catalog rows.

## Intent

Integrate qsv as a full-stack surface:

1. MCPHub-managed stdio MCP server (`qsv`) via local sparse build + wrapper.
2. New public capability group `data` with qsv as primary member.
3. Opt-in membership on `coding` and `research` (not `harness`/`tunnel`).
4. Fifteen curated-external skill catalog rows for Skills CLI multi-harness sync.

## Scope

- `scripts/mcphub/qsv-stdio.sh`
- `config/mcp-registry.json` server + `data` group + coding/research membership
- `mcp/mcphub/mcp_settings.json` via generate
- Maintainer docs / group-picker for `data`
- Registry pytest
- Fifteen `docs/src/authoring/skills/*.mdx` curated-external rows (pin 21.1.0)
- Docs generate + skills sync apply after dry-run green (plan lock)

## Out Of Scope

- Vendoring qsv into repo `skills/`
- Default `harness` or `tunnel` attachment
- Homebrew packaging of `qsvmcp`
- Companion BLS/Census MCP servers
- Home stack sync unless separately requested
- Publishing `@qsv/agent-skills` to npm (upstream does not publish)

## Risks

- Filesystem read/write under allowed dirs (`REPO_ROOT` + `$HOME/dev`)
- ~23 tools at deferred startup (context cost if mis-grouped)
- Skills require MCP tools (`mcp__qsv__*`)
- Local build under gitignored `mcp/servers/qsv-agent-skills` must exist on machine
- Optional LLM path via `describegpt` (user-owned keys)
