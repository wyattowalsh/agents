# Codex and `.agents` Plugin Package Plan

## Current repo signals

The repo includes `.codex-plugin/`, `.agents/`, and `agent-bundle.json`. The bundle advertises adapters for Codex and an Agent Skills CLI fallback.

## Plan

- Treat `.agents/plugins/marketplace.json` as a repo-local plugin marketplace candidate.
- Validate that Codex actually consumes the specified manifest before marking support validated.
- Keep AGENTS.md and OpenSpec status as primary Codex instruction surfaces.
- Use OpenAI Docs MCP as optional docs lookup.
- Add task nodes for Codex plugin manifest validation and installation smoke tests.
