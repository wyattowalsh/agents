# MCP Registry Gap-Fill Watchlist

## Objective

Use MCP indexes to discover live-systems capabilities while preserving a skills-first strategy.

## Indexes to survey continuously

| Index | Use | Caveat |
|---|---|---|
| Glama MCP directory | Broad discovery, facets for browser automation, official/local/remote, TypeScript/Python | Directory presence is not a safety signal |
| PulseMCP | Large directory with trending domains and adoption signals | Directory metadata must be verified upstream |
| MCP.so | Discovery and comparison | Treat as lead generation only |
| Awesome MCP curated lists | Human-curated/ranked leads | Check upstream repo health and licenses |

## MCP candidates likely worth evaluating

| Candidate | Domain | Preferred install | Why MCP may be justified | Skill replacement posture |
|---|---|---|---|---|
| Playwright MCP | browser automation | `npx @playwright/mcp@latest` pinned in config after validation | Dynamic browser runtime, accessibility snapshots | Keep MCP |
| Chrome DevTools MCP | browser/devtools | npx or official package path | Live browser/devtools telemetry | Keep MCP |
| GitHub MCP Server | GitHub state | official server / Copilot default | Live repo/issues/PRs/actions state | Keep MCP for live state; skills for static GitHub playbooks |
| OpenAI Docs MCP | current docs | remote URL / `codex mcp add` | Live/current documentation | Keep as research/docs MCP |
| Context7 | documentation context | npx/remote depending harness | Current library docs | Keep as research/docs MCP; avoid static-doc duplication |
| Perplexity MCP | search/reasoning | official MCP config with API key | Current web/search/reasoning | Keep for research lane if policy allows |
| Qdrant MCP | vector DB | uvx/npx if official | Live vector DB operations | Keep only for actual vector DB state |
| Filesystem MCP | local FS | avoid unless harness needs MCP-only FS access | Often redundant and risky | Prefer skill/CLI or native harness tools |
| Git MCP | local git | avoid unless needed | Often redundant with CLI | Prefer skill/CLI wrappers |
| SQLite/Postgres MCP | DB state | uvx/npx/official | Live DB introspection | Keep only with strict auth/sandbox |

## Required MCP metadata

Every promoted MCP must include:

- upstream URL;
- package/install command;
- pinned version strategy;
- domain;
- transport;
- auth model;
- secret handling;
- sandbox policy;
- allowed tools/resources;
- smoke test;
- OWASP MCP Top 10 notes;
- skill replacement assessment;
- deprecation/rollback path.

## Rejection rules

Reject or quarantine MCPs that:

- require broad filesystem/network access without a narrow purpose;
- hide command execution behind vague descriptions;
- lack upstream repo/source transparency;
- are unmaintained or have unclear license;
- duplicate a deterministic CLI skill;
- fail mcp-scan or equivalent safety checks;
- include tool poisoning patterns or dynamic descriptions that cannot be pinned.
