# Proposal

## Problem

The managed MCP registry does not include `llms-txt-explorer`, so repo and home harness configs cannot discover or validate sites publishing `llms.txt` / `llms-full.txt` consistently across supported tools.

## Intent

Add `llms-txt-explorer` once to the normalized registry using an npx stdio launch wrapped by repo-managed fleet defaults, wire MCPHub groups (`harness`, `tunnel`, and relevant workflow groups), and update maintainer docs. No curated external skill catalog row (MCP-only).

## Scope

- Add `scripts/mcphub/llms-txt-explorer-stdio.sh` pinning `@thedaviddias/mcp-llms-txt-explorer@0.2.0`.
- Add `llms-txt-explorer` to `config/mcp-registry.json` with group memberships.
- Registry contract tests and mcphub settings regeneration.
- Maintainer docs (`docs/ai-tools/mcphub.md`, `kb/raw/sources/mcp-surfaces.md`).

## Out of scope

- Curated skill catalog authoring (`docs/src/authoring/skills/`).
- First-party MCP server code under `mcp/llms-txt-explorer/`.