# Gemini, OpenCode, and Cursor Plugin Adjacency

## Gemini CLI

Gemini extensions can package context, MCP servers, and custom commands. Generate `gemini-extension.json` from canonical registry only after source-owned config is frozen.

## OpenCode

OpenCode can discover skills directly from `.opencode/skills`, `.claude/skills`, and `.agents/skills`. Prefer direct skills projection before creating complex plugin packages.

## Cursor

Cursor uses rules, MCP, CLI/background agents, and environment setup. Treat Cursor projection as rules + MCP + docs + optional CI/headless commands; do not assume a native skill/plugin package unless verified.
