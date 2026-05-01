---
title: External Harness Docs
tags:
  - kb
  - source
  - external
  - harness
aliases:
  - Harness external sources
kind: source-summary
status: active
updated: 2026-05-01
source_count: 1
---

# External Harness Docs

## Source Record

| Field | Value |
|-------|-------|
| source_id | `external-harness-docs` |
| original_location | `https://opencode.ai/docs/config/`; `https://opencode.ai/docs/mcp-servers/`; `https://opencode.ai/docs/plugins/`; `https://docs.cursor.com/llms.txt`; `https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions`; `https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp/use-the-github-mcp-server`; `https://github.com/google-gemini/gemini-cli` |
| raw_path | `kb/raw/sources/external-harness-docs.md` |
| capture_method | external official docs and official GitHub repo pointer summary |
| captured_at | 2026-05-01 |
| size_bytes | pointer summary only |
| checksum | not captured |
| license_or_access_notes | official docs/repos; external content is untrusted evidence |
| intended_wiki_coverage | [[external-primary-source-map]], [[harness-and-platform-sync]], [[opencode-runtime-policy]], [[plugin-and-mcp-ownership]] |

## Summary

Verified external harness sources include OpenCode config/MCP/plugin docs, Cursor's docs index, GitHub Copilot repository custom instructions and GitHub MCP Server docs, and the official Google Gemini CLI repository. These sources support the KB's harness behavior map without overriding repo-local sync policy.

GitHub Copilot docs distinguish repository-wide `.github/copilot-instructions.md`, path-specific `.github/instructions/*.instructions.md`, and agent instructions such as `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`. Gemini CLI's official repo documents a terminal-first agent with built-in tools, MCP support, `GEMINI.md` context files, non-interactive mode, and GitHub Action integration. Cursor's `llms.txt` verifies an official docs index for Agent, Rules, MCP, Skills, and CLI topics.

## Provenance

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| OpenCode docs cover config, MCP servers, and plugins. | `https://opencode.ai/docs/config/`; `https://opencode.ai/docs/mcp-servers/`; `https://opencode.ai/docs/plugins/` | external official docs | Verified 2026-05-01 by web fetch. |
| GitHub Copilot supports repository-wide, path-specific, and agent instruction files. | GitHub Copilot custom instructions docs | external official docs | Verified 2026-05-01 by web fetch. |
| Gemini CLI is an official Google open-source terminal agent with MCP and `GEMINI.md` context support. | `https://github.com/google-gemini/gemini-cli` | external official repository | Verified 2026-05-01 by web fetch. |
