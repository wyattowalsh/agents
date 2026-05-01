# MCP Replacement Candidates

## Replace with Agent Skills by default

Reasoning/prompt-structure MCPs should generally become skills because they primarily package procedural knowledge rather than dynamic external state.

Initial candidates from current `mcp.json`:

- `cascade-thinking`
- `sequential-thinking`
- `structured-thinking`
- `atom-of-thoughts`
- `creative-thinking`
- `lotus-wisdom-mcp`
- `shannon-thinking`
- `think-strategies`

## Convert to hybrid skill wrappers

Some tools can be presented as Agent Skills that call a CLI/MCP only when needed:

- `docling` → document-processing skill with `uvx` helper.
- `repomix` → repo-context-packaging skill with `npx repomix` helper.
- `ffmpeg` → media-processing skill with CLI wrapper and sandbox warnings.
- `trafilatura` → extraction skill using package/uvx instead of absolute path.

## Keep as MCP

Use MCP when dynamic state, auth, or live runtime interaction is central:

- `chrome-devtools`, Playwright/browser candidates.
- `context7`, `deepwiki`, OpenAI Docs MCP, docs/search servers.
- `brave-search`, `tavily`, `exa`, `duckduckgo-search` after dedupe.
- `gmail`, GitHub, CI, issue trackers, cloud services.
- database/vector/observability state servers.

## Acceptance criteria

Every replacement decision must include:

- equivalent skill package name;
- script/CLI contract if executable;
- deprecation path for the MCP entry;
- compatibility notes for harnesses that only support MCP;
- rollback path.
