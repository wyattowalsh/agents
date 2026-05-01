# Idiosyncratic Extension Surfaces

## Purpose

Capture harness-specific primitives that do not map cleanly to skills/MCP/plugins.

## Surfaces

| Harness | Idiosyncratic surface | Planning use |
|---|---|---|
| Claude Code | hooks with command/http/mcp_tool/prompt/agent types | policy guardrails, validation hooks |
| Claude Code | subagents / agent teams | parallel execution UX inspiration |
| GitHub Copilot | `.github/agents/*.md` custom agent profiles | map local `agents/` to Copilot profiles |
| GitHub Copilot | `gh skill` preview/install/update/publish | skill provenance and audit lane |
| Cursor | background agents and `.cursor/environment.json` | async task execution and env bootstrap docs |
| Cursor | CLI `--output-format json` | automation and CI integration |
| Gemini CLI | extension command conflict prefixing | generated command naming policy |
| OpenCode | compatible discovery of `.agents/skills` | direct skills projection |
| Cherry Studio | bundled uv/bun path | install docs and config wizard caveat |
| Perplexity | macOS helper for local MCP | support caveat and setup doc |
| Antigravity | artifacts and Manager surface | UI/dashboard inspiration, not config contract |
| ChatGPT | Apps SDK UI inside chat | future app surface; preview only |
| Codex | cloud sandbox task execution | task graph parallelism and AGENTS.md focus |
