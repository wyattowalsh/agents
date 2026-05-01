# Harness Extension Surfaces

## Objective

Capture idiosyncratic extension models per AI tool/harness.

## Summary matrix

| Harness | Preferred lane | Secondary lane | Stable? | Notes |
|---|---|---|---|---|
| Claude Code | Agent Skills + plugin | MCP, hooks, subagents | Yes | Strong native skills/plugin surface; hooks need safety controls |
| Claude Desktop | Desktop Extension/MCP | Skills if exposed by client | Partial | Desktop packaging differs from Claude Code plugin model |
| ChatGPT | Custom GPT Actions/OpenAPI | Apps SDK/MCP preview | Mixed | Apps SDK is preview; Actions require OpenAPI/auth/privacy policy |
| Codex | AGENTS.md + local repo context | MCP docs/tools | Partial | Cloud sandbox tasks; human review required |
| GitHub Copilot Web | instructions + agents/skills | GitHub MCP/Actions | Yes/rolling | AGENTS.md precedence and `.github` instructions matter |
| GitHub Copilot CLI | skills/custom agents | MCP | Yes | Skills are first-class in CLI docs |
| OpenCode | skills/plugins/agents/config | MCP | Yes | Searches .opencode/.claude/.agents skill dirs |
| Gemini CLI | extensions/commands/context | MCP | Yes | Extension manifests can configure MCP servers |
| Cursor Editor | rules + AGENTS.md | MCP/background agents | Yes | .cursorrules deprecated; JSON/stream automation for CLI |
| Cursor Agent | CLI JSON/stream-json + MCP | rules/context | Yes | Good deterministic automation target |
| Cherry Studio | presets/assistants + MCP UI | built-in MCP env | Partial | Built-in uv/bun and auto-install flows need explicit policy |
| Perplexity Desktop | unverified | Perplexity MCP service | Unverified | Do not auto-write desktop configs without contract |
| Antigravity | rules only | TBD | Unverified | Official stable extension contracts not verified |

## Required follow-up

Each harness-specific doc in `planning/20-harness-registry/` must include:

- official docs sources;
- repo artifacts;
- support tier;
- preferred extension lane;
- config scopes;
- auth/secrets posture;
- automation affordances;
- known limitations;
- tasks and acceptance criteria.
